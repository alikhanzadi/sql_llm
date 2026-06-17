"""
Paraphrase-robustness eval — measures TRUE KPI-matcher precision.

The planner+matcher routing eval (run_planner_kpi_eval.py) uses the catalog's own
example questions, which the matcher is effectively tuned on. This harness instead
uses held-out paraphrases that avoid each KPI's name and alias phrases, so the score
reflects how the matcher handles language it was NOT tuned on.

This is a measurement report, not a hard pass/fail gate. Misses are expected and
show where lexical matching breaks (e.g. "earnings" vs "revenue").

Usage:
  python app/eval/run_paraphrase_eval.py
  python app/eval/run_paraphrase_eval.py --show-contaminated   # list leaks only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm.planner import plan_query
from app.llm.kpi_matcher import match_kpi
from app.rag.catalog.kpi_catalog import load_kpi_catalog

CASES_PATH = Path("app/eval/paraphrase_cases.json")


def _contaminated(question: str, kpi: dict) -> str | None:
    """Return the leaked name/alias phrase if the question contains one verbatim."""
    q = question.lower()
    candidates = [kpi.get("name", "")] + list(kpi.get("aliases", []))
    for c in candidates:
        c = (c or "").lower().strip()
        if len(c) >= 4 and c in q:
            return c
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-contaminated", action="store_true")
    args = ap.parse_args(argv)

    cases = json.load(open(CASES_PATH))["cases"]
    kpis = {k["kpi_id"]: k for k in load_kpi_catalog()["kpis"]}

    hits = 0
    misses_none = []   # routed to schema fallback (below threshold / guardrail)
    misses_wrong = []  # routed to a different KPI
    contaminated = []

    for case in cases:
        expected = case["kpi_id"]
        q = case["question"]
        kpi = kpis.get(expected, {})

        leak = _contaminated(q, kpi)
        if leak:
            contaminated.append((expected, leak, q))

        plan = plan_query(q)
        decision = match_kpi(q, plan)
        got = decision.kpi_id if decision.matched else None

        if got == expected:
            hits += 1
        elif got is None:
            misses_none.append((expected, q))
        else:
            misses_wrong.append((expected, got, q))

    total = len(cases)
    print(f"Paraphrase robustness — {total} held-out questions\n")

    if args.show_contaminated:
        if contaminated:
            print("Contaminated (paraphrase leaked a name/alias — rewrite these):")
            for exp, leak, q in contaminated:
                print(f"  {exp}: leaked '{leak}'  | {q}")
        else:
            print("No contaminated cases.")
        return 0

    if misses_wrong:
        print("WRONG-KPI misses (routed to a different KPI):")
        for exp, got, q in misses_wrong:
            print(f"  {exp:<38} -> {got:<34} | {q}")
        print()
    if misses_none:
        print("FALLBACK misses (below threshold -> schema-only):")
        for exp, q in misses_none:
            print(f"  {exp:<38} -> NONE | {q}")
        print()

    print("--- Summary ---")
    print(f"Precision: {hits}/{total} = {hits/total*100:.1f}%")
    print(f"  wrong-KPI: {len(misses_wrong)}   fallback: {len(misses_none)}")
    if contaminated:
        print(f"  ! {len(contaminated)} contaminated paraphrase(s) — run --show-contaminated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
