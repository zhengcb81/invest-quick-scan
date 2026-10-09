"""Write the same-review final record from independently checked local evidence."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
INTAKE = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


verification = json.loads((OUT / "frozen-candidate-02-verification.json").read_bytes())
probe = json.loads((OUT / "capacity-anchor-02.process.json").read_bytes())
probe_stdout = (OUT / "capacity-anchor-02.stdout.log").read_text(encoding="utf-8")
facts = json.loads(probe_stdout.splitlines()[0])
assert verification["all_36_current_and_snapshot_bytes_match"]
assert probe["returncode"] == 0 and probe["terminal_confirmed"] and probe["source_unchanged"]
assert facts["rejection"] == "owner_refresh_guard_rejected" and not facts["permit_returned"]
assert facts["attempt_phases"] == ["prepared"]
assert verification["probe_attempt_rows"] == [["prepared", None]]
assert not verification["denied_owner_drift_created_new_budget_reservation"]
assert "1 passed in 1.28s" in probe_stdout
eight_cases = next(row for row in verification["process_checks"]
                   if row["label"] == "executor-final-affected-04")["capacity_and_guard_cases"]
assert len(eight_cases) == 8 and all(row["passed"] for row in eight_cases)

records = []
terminal_facts = {
    "storage-final-09": dict(passed=91, failed=0, pytest_wall_s=59.41),
    "storage-profiles-final-11": dict(passed=90, failed=0, pytest_wall_s=16.73),
    "executor-final-affected-04": dict(passed=307, failed=1, pytest_wall_s=72.30),
    "executor-checkpoint-final-05": dict(passed=8, failed=0, pytest_wall_s=3.44),
    "handoff-final-01": dict(passed=18, failed=0, pytest_wall_s=103.01),
}
for check in verification["process_checks"]:
    row = dict(check)
    row.update(terminal_facts[row["label"]])
    records.append(row)

result = {
    "review_date": "2026-10-09",
    "review_identity": "same_W15_concentrated_review_final_addendum",
    "outcome": "limited_foundation_signed_off",
    "software_open_findings": 0,
    "candidate_index_sha256": verification["candidate_index_sha256"],
    "candidate_index": "docs/implementation/intake/W15/module-readiness-2026-10-09/candidate-index-02.json",
    "candidate_counts": verification["candidate_counts"],
    "all_36_current_and_frozen_snapshot_bytes_match": True,
    "software_scope": ["IQS producer handoff", "StockWiki route and original Observation storage/refresh",
                       "QA original work/budget/send transaction integration"],
    "closed_findings": [{
        "id": "F1", "priority": "P1", "kind": "product",
        "description": "Owner current drift during capacity wait must reject before every fee admission retry",
        "resolution": "Named owner guard at entry and both work/budget-only retry loops",
        "final_transport_sha256": "69ec8dce71337a9c359a49302e2739cb217e60371b964907ae1843a6d70b1fc4",
        "final_locations": ["src/utils/quick_scan_work_transport.py:651", "src/utils/quick_scan_work_transport.py:665",
                            "src/utils/quick_scan_work_transport.py:770", "src/utils/quick_scan_work_transport.py:797"],
        "original_RED_preserved": True,
        "independent_recheck": {
            "label": "capacity-anchor-02", "pid": probe["pid"], "returncode": probe["returncode"],
            "terminal_confirmed": probe["terminal_confirmed"], "passed": 1,
            "pytest_wall_s": 1.28, "controller_wall_s": probe["wall_s"],
            "source_unchanged": probe["source_unchanged"], "executed_product_schema_hashes": 19,
            "facts": facts, "budget_rows": verification["probe_budget_rows"],
            "attempt_rows": verification["probe_attempt_rows"],
            "new_work_budget_reservations": 0, "send_intent_rows": 0,
            "process_sha256": digest(OUT / "capacity-anchor-02.process.json"),
            "probe_source_sha256": digest(OUT / "test_capacity_anchor.py"),
            "boundary_substitutes": ["IQS UnitValidator", "typed CLI transport"],
            "real_storage": ["StockWiki SQLite current anchor", "QA SQLite fee admission and settlement", "QA attempt/send-intent ledger"],
        },
        "formal_F1_cases_passed": eight_cases[:4],
    }],
    "existing_terminal_records": records,
    "counts_aggregated": False,
    "executor_307P_1F_preserved": True,
    "Q07_failure_classification": "fixture requested model default was inconsistent with model-a response; product rejected durable response mismatch",
    "Q07_fixture_followup": "executor-checkpoint-final-05: independent 8P, products unchanged; no claim of 308P suite",
    "static_QA_05": {
        "all_four_terminal_zero": True, "tools": ["Black", "isort", "mypy", "Bandit"], "mypy_source_files": 63,
        "product_python_sha_matches_final": True,
        "later_fixture_not_attested_by_this_old_static_record": verification["static_qa_05_candidate_python_paths_with_different_or_missing_sha"],
    },
    "static_SW_01": {
        "terminal_zero": True, "all_eight_product_SHA_match_final": True,
        "later_fixture_SHA_not_retroactively_attested": True,
    },
    "publication_hooks": "controller will run normal source hooks; no success predicted by reviewer",
    "isolation": {
        "guard_sha256": probe["guard_sha256"], "guard_revision": "v3",
        "stdlib_socketpair_allowance": "only exact fallback_socketpair frame local csock to its own listening lsock",
        "ordinary_loopback_and_remote_denied": True, "foreign_SQLite_denied": True,
        "four_actual_guard_cases_passed": eight_cases[4:],
        "guard_is_private_support_not_product": True, "whole_OS_guard_claim": False, "v2_original_preserved": True,
    },
    "before_publication_preflight_sha256": verification["before_publication_preflight_sha256"],
    "source_preflight_heads": verification["source_preflight_heads"],
    "preflight_review_scope": "read existing controller evidence and match candidate index; no new whole external-source inventory run",
    "full_non_green_preserved": True,
    "full_SW_original_terminal": {
        "label": "full-sw-support-fixed", "pid": 5808, "returncode": 1,
        "passed": 1063, "failed": 64, "skipped": 18, "errors": 21, "pytest_wall_s": 225.22,
        "coverage_80_percent_is_diagnostic": True,
    },
    "full_classification_reference": "full-sw-classification-01.md",
    "c06_envelope_validated": False,
    "uncompleted_original_evidence": ["real C06/query serializer/envelope", "actual owner query golden", "financial facts and accuracy"],
    "original_gates_not_closed": ["G3/L03", "F05", "B01", "TH-IN", "whole W15"],
    "real_owner_input_is_not_query_or_financial_golden": True,
    "historical_router_2_1_2_2_is_unit_storage_boundary_only": True,
    "review_product_source_PWF_writes": 0, "review_full_reruns": 0,
    "review_model_API_HTTP_calls": 0,
    "evidence": {
        "verification_sha256": digest(OUT / "frozen-candidate-02-verification.json"),
        "markdown_sha256": digest(OUT / "concentrated-recheck-02.md"),
        "initial_review_sha256": digest(OUT / "concentrated-review-01.md"),
        "full_classification_sha256": digest(OUT / "full-sw-classification-01.md"),
        "published_profiles_readonly_comparison_sha256": digest(OUT / "published-profile-baseline-01.json"),
    },
}
(OUT / "concentrated-recheck-02.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"outcome": result["outcome"], "software_open_findings": result["software_open_findings"],
                  "candidate_index_sha256": result["candidate_index_sha256"],
                  "report_sha256": digest(OUT / "concentrated-recheck-02.json")}, ensure_ascii=False))
