import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm.kpi_matcher import match_kpi
from app.llm.planner import plan_query


"""
Purpose:
- Offline regression harness for planner + KPI matcher routing behavior.
- Validates that representative questions map to expected intent/time grain/KPI IDs.

Why this exists:
- KPI catalog defines business semantics; this harness verifies runtime routing behavior.
- Prevents silent regressions when planner or matcher heuristics are tuned.
- Ensures optional KPI layer remains optional by checking schema fallback cases.
"""


def _load_cases(path: Path) -> list[dict]:
    """
    Load JSON eval definitions.

    Supports:
    - legacy list format: [ ...cases... ]
    - metadata format: { "purpose": ..., "cases": [ ... ] }
    """
    with path.open("r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        return data["cases"]
    raise ValueError("Eval cases file must be a JSON list or an object with a 'cases' list.")


def _load_metadata(path: Path) -> tuple[str, list[str]]:
    """Load optional purpose/why metadata for human-readable eval output."""
    with path.open("r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return "", []
    purpose = str(data.get("purpose", "")).strip()
    why = data.get("why_this_exists", [])
    why_list = [str(x) for x in why] if isinstance(why, list) else []
    return purpose, why_list


def _assert_case(case: dict) -> tuple[bool, list[str]]:
    """Run one planner+KPI assertion case and return pass/fail details."""
    failures: list[str] = []
    question = case["question"]
    plan = plan_query(question)
    decision = match_kpi(question, plan)

    expected_intent = case.get("expected_intent")
    if expected_intent and plan.intent != expected_intent:
        failures.append(f"intent expected={expected_intent} actual={plan.intent}")

    expected_time_grain = case.get("expected_time_grain")
    if expected_time_grain and plan.time_grain != expected_time_grain:
        failures.append(
            f"time_grain expected={expected_time_grain} actual={plan.time_grain}"
        )

    expected_kpi_id = case.get("expected_kpi_id")
    actual_kpi_id = decision.kpi_id if decision.matched else None
    if actual_kpi_id != expected_kpi_id:
        failures.append(f"kpi_id expected={expected_kpi_id} actual={actual_kpi_id}")

    expected_status = case.get("expected_kpi_status")
    if expected_status is not None:
        actual_status = decision.status if decision.matched else None
        if actual_status != expected_status:
            failures.append(f"kpi_status expected={expected_status} actual={actual_status}")

    return (len(failures) == 0, failures)


def run_eval(cases_path: Path) -> int:
    """Execute eval suite and print a compact pass/fail report."""
    cases = _load_cases(cases_path)
    purpose, why = _load_metadata(cases_path)

    if purpose:
        print("Eval Purpose:")
        print(f"- {purpose}")
    if why:
        print("Why This Exists:")
        for line in why:
            print(f"- {line}")
    if purpose or why:
        print("")

    passed = 0
    failed = 0

    for case in cases:
        ok, failures = _assert_case(case)
        if ok:
            passed += 1
            print(f"[PASS] {case.get('id', '<no-id>')}")
            continue

        failed += 1
        print(f"[FAIL] {case.get('id', '<no-id>')}")
        for failure in failures:
            print(f"  - {failure}")

    total = passed + failed
    print("\n--- Eval Summary ---")
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    default_path = Path("app/eval/planner_kpi_cases.json")
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    raise SystemExit(run_eval(path))
