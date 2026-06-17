"""
SQL-correctness eval harness.

For each active KPI, take a representative NL question and run the real pipeline
(plan -> match -> generate SQL), then make *semantic* assertions derived directly
from the catalog so the eval can never drift from the KPI definitions:

  - required_tables          every required table is referenced
  - completed-status filter  the lowercase 'completed' filter is applied correctly
                             (catches the 'COMPLETED' uppercase zero-rows trap)
  - aggregation pattern      sql_recipe.pattern maps to the expected aggregate
  - required_joins           join column references appear (secondary)
  - time grain               date bucketing when the question implies a grain (secondary)

Cases are generated FROM the catalog (not a hand-list), honoring "never drift".

Usage:
  python app/eval/run_sql_correctness_eval.py                 # full run (calls the LLM)
  python app/eval/run_sql_correctness_eval.py --limit 5       # first 5 KPIs
  python app/eval/run_sql_correctness_eval.py --kpi total_token_revenue
  python app/eval/run_sql_correctness_eval.py --section A
  python app/eval/run_sql_correctness_eval.py --offline       # print cases, no LLM
  python app/eval/run_sql_correctness_eval.py --json out.json # write machine-readable results
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env before any app import that constructs an OpenAI client at module load.
from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from app.rag.catalog.kpi_catalog import load_kpi_catalog


# ---------------------------------------------------------------------------
# Context: full schema (isolates KPI->SQL correctness from retrieval quality)
# ---------------------------------------------------------------------------
def build_full_schema_context() -> str:
    """Concatenate all formatted schema docs so generation is not retrieval-limited."""
    from app.rag.embeddings import load_schema_docs, format_doc

    docs = load_schema_docs()
    parts = ["Relevant Database Schema:"]
    for doc in docs:
        parts.append(format_doc(doc).strip())
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Case generation (from the catalog)
# ---------------------------------------------------------------------------
@dataclass
class EvalCase:
    kpi_id: str
    section: str
    question: str
    required_tables: list[str]
    required_joins: list[str]
    filters_defaults: list[str]
    pattern: str
    numerator: str | None


def build_cases(catalog: dict) -> list[EvalCase]:
    cases = []
    for k in catalog["kpis"]:
        if k.get("status") != "active":
            continue
        examples = k.get("example_questions") or []
        if not examples:
            continue
        recipe = k.get("sql_recipe", {})
        cases.append(
            EvalCase(
                kpi_id=k["kpi_id"],
                section=k.get("section", "?"),
                question=examples[0],
                required_tables=k.get("required_tables", []),
                required_joins=k.get("required_joins", []),
                filters_defaults=k.get("filters_defaults", []),
                pattern=str(recipe.get("pattern", "")),
                numerator=recipe.get("numerator"),
            )
        )
    return cases


# ---------------------------------------------------------------------------
# Assertions (semantic, on generated SQL text)
# ---------------------------------------------------------------------------
def _norm(sql: str) -> str:
    return " ".join(sql.lower().split())


_AGG_FOR_PATTERN = {
    "sum_grouped": "sum(",
    "count_grouped": "count(",
    "average": "avg(",
}


def _lead_func(expr: str | None) -> str | None:
    """Extract the leading aggregate function name from a recipe numerator."""
    if not expr:
        return None
    m = re.match(r"\s*([a-zA-Z_]+)\s*\(", expr)
    return m.group(1).lower() + "(" if m else None


def assert_tables(case: EvalCase, sql_n: str) -> tuple[bool, str]:
    missing = [t for t in case.required_tables if t.lower() not in sql_n]
    return (not missing, f"missing tables: {missing}" if missing else "tables ok")


def assert_completed_filter(case: EvalCase, raw_sql: str) -> tuple[bool, str] | None:
    """Only applies when the KPI declares a status = 'completed' default.

    Must match a status-to-completed comparison, not merely the substring
    "completed" (e.g. a `completed_at IS NOT NULL` column filter does not count).
    """
    needs = any("status" in f.lower() and "completed" in f.lower()
                for f in case.filters_defaults)
    if not needs:
        return None  # not applicable
    low = raw_sql.lower()
    # correct: lower(...status...) = 'completed'  OR  status = 'completed' (lowercase literal)
    correct = re.search(r"lower\s*\([^)]*status[^)]*\)\s*=\s*'completed'", low) or \
        re.search(r"status\s*=\s*'completed'", raw_sql)  # raw: lowercase literal only
    # trap: uppercase literal without a lower()/upper() wrap
    trap = re.search(r"=\s*'COMPLETED'", raw_sql) and not re.search(r"lower\s*\([^)]*status", low)
    if correct and not trap:
        return (True, "completed filter ok")
    if trap:
        return (False, "UPPERCASE 'COMPLETED' trap (returns 0 rows)")
    return (False, "completed-status filter missing")


def assert_aggregation(case: EvalCase, sql_n: str) -> tuple[bool, str] | None:
    if case.pattern == "raw_sql":
        return None  # freeform recipe, skip strict aggregation check
    if case.pattern == "average":
        # an average is valid as AVG(...) or as an explicit SUM(...)/COUNT(...) division
        ok = "avg(" in sql_n or ("sum(" in sql_n and "count(" in sql_n and "/" in sql_n)
        return (ok, "expected avg( or sum()/count() for average")
    if case.pattern in _AGG_FOR_PATTERN:
        agg = _AGG_FOR_PATTERN[case.pattern]
        return (agg in sql_n, f"expected {agg} for {case.pattern}")
    if case.pattern == "ratio":
        lead = _lead_func(case.numerator)
        # ratio should aggregate; accept the numerator's function, or any count/sum, or a division
        ok = (lead and lead in sql_n) or "count(" in sql_n or "sum(" in sql_n or "/" in sql_n
        return (ok, "expected ratio aggregation (count/sum/division)")
    return None


def assert_joins(case: EvalCase, sql_n: str) -> tuple[bool, str] | None:
    if not case.required_joins:
        return None
    missing = []
    for j in case.required_joins:
        cols = re.findall(r"[a-z_]+\.[a-z_]+", j.lower())
        if not all(c in sql_n for c in cols):
            missing.append(j)
    return (not missing, f"missing join refs: {missing}" if missing else "joins ok")


def assert_time_grain(question: str, sql_n: str) -> tuple[bool, str] | None:
    from app.llm.planner import plan_query

    grain = plan_query(question).time_grain
    if grain == "all_time":
        return None
    bucketed = "date_trunc" in sql_n or "date(" in sql_n or "to_char(" in sql_n or \
        re.search(r"extract\s*\(", sql_n)
    return (bool(bucketed), f"expected date bucketing for grain={grain}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
@dataclass
class CaseResult:
    kpi_id: str
    section: str
    question: str
    sql: str = ""
    checks: dict = field(default_factory=dict)   # name -> {passed, detail}
    core_passed: bool = False
    error: str | None = None


CORE_CHECKS = {"tables", "completed_filter", "aggregation"}


def run_case(case: EvalCase, context: str) -> CaseResult:
    import contextlib
    import io
    from app.llm.generate_sql import build_sql_planning_context, generate_sql

    res = CaseResult(kpi_id=case.kpi_id, section=case.section, question=case.question)
    try:
        # Silence generate_sql's debug prints (context dump, KPI-match log).
        with contextlib.redirect_stdout(io.StringIO()):
            pc = build_sql_planning_context(case.question)
            sql = generate_sql(case.question, context, planning_context=pc)
        res.sql = sql
    except Exception as exc:  # pragma: no cover - network/env dependent
        res.error = str(exc)
        return res

    sql_n = _norm(sql)
    raw = sql
    checks: dict[str, tuple[bool, str] | None] = {
        "tables": assert_tables(case, sql_n),
        "completed_filter": assert_completed_filter(case, raw),
        "aggregation": assert_aggregation(case, sql_n),
        "joins": assert_joins(case, sql_n),
        "time_grain": assert_time_grain(case.question, sql_n),
    }
    for name, out in checks.items():
        if out is None:
            continue
        res.checks[name] = {"passed": out[0], "detail": out[1]}

    res.core_passed = all(
        res.checks[c]["passed"] for c in CORE_CHECKS if c in res.checks
    )
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="SQL-correctness eval (catalog-driven)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kpi", type=str, default=None)
    ap.add_argument("--section", type=str, default=None, choices=list("ABCDE"))
    ap.add_argument("--offline", action="store_true", help="print cases + assertions, no LLM")
    ap.add_argument("--json", dest="json_out", type=str, default=None)
    args = ap.parse_args(argv)

    catalog = load_kpi_catalog()
    cases = build_cases(catalog)
    if args.section:
        cases = [c for c in cases if c.section == args.section]
    if args.kpi:
        cases = [c for c in cases if c.kpi_id == args.kpi]
    if args.limit:
        cases = cases[: args.limit]

    print(f"SQL-correctness eval — {len(cases)} cases\n")

    if args.offline:
        for c in cases:
            needs_completed = any("completed" in f.lower() for f in c.filters_defaults)
            print(f"[{c.section}] {c.kpi_id}")
            print(f"    q: {c.question}")
            print(f"    tables={c.required_tables} pattern={c.pattern} "
                  f"completed_filter={'yes' if needs_completed else 'no'} "
                  f"joins={len(c.required_joins)}")
        return 0

    context = build_full_schema_context()
    results = [run_case(c, context) for c in cases]

    passed = sum(1 for r in results if r.core_passed and not r.error)
    errored = [r for r in results if r.error]

    for r in results:
        if r.error:
            print(f"ERROR  [{r.section}] {r.kpi_id}: {r.error}")
            continue
        flag = "PASS" if r.core_passed else "FAIL"
        print(f"{flag}  [{r.section}] {r.kpi_id}")
        if not r.core_passed:
            for name, c in r.checks.items():
                if name in CORE_CHECKS and not c["passed"]:
                    print(f"        - {name}: {c['detail']}")

    print(f"\n--- Summary ---")
    print(f"Core pass: {passed}/{len(results)}   errors: {len(errored)}")
    # secondary signal
    for name in ("joins", "time_grain"):
        applicable = [r for r in results if name in r.checks]
        ok = sum(1 for r in applicable if r.checks[name]["passed"])
        if applicable:
            print(f"  ({name}: {ok}/{len(applicable)} applicable)")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"\nWrote {args.json_out}")

    return 0 if passed == len(results) and not errored else 1


if __name__ == "__main__":
    sys.exit(main())
