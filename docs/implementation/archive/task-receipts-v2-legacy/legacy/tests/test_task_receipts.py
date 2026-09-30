"""Hermetic regression coverage for the read-only task receipt verifier."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts import task_receipts as receipts


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class ReceiptFixture:
    def __init__(self, root: Path, *, historical: bool = False,
                 upstream_regression_reference: bool = False) -> None:
        self.root = root
        self.plan_path = root / "docs" / "implementation" / "tasks.json"
        self.catalog_path = root / "docs" / "implementation" / "acceptance-cases.json"
        self.receipt_path = root / "docs" / "implementation" / "receipt.json"
        self.schema_path = Path(__file__).resolve().parents[1] / "schemas" / "quick_scan" / "task-receipt.schema.json"
        self.plan_path.parent.mkdir(parents=True, exist_ok=True)
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "tests").mkdir(parents=True, exist_ok=True)
        (root / "evidence").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "implementation" / "contracts").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "implementation" / "reviews" / "T01").mkdir(parents=True, exist_ok=True)
        (root / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "tests" / "test_module.py").write_text("def test_value(): assert True\n", encoding="utf-8")
        (root / "schemas" / "sample.schema.json").parent.mkdir(parents=True, exist_ok=True)
        (root / "schemas" / "sample.schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
        (root / "docs" / "implementation" / "contracts" / "validation-T01-unit.log").write_text("3 tests passed\n", encoding="utf-8")

        task = {
            "id": "T01", "owner": "fixture", "kind": "implementation", "title": "Synthetic receipt task",
            "depends_on": ["P00"] if historical else [],
            "historical_context_dependencies": ["P00"] if historical else [],
            "case_ids": ["R01-C01", "R01-C02"] + (["P00-C01"] if upstream_regression_reference else []),
            "invariants": ["I01"],
            "allowed_changes": ["src/", "tests/", "schemas/"], "completion": ["All assertions pass."],
            "rollback": "Remove only the isolated fixture.",
        }
        self.plan = {"version": "test-1", "global_boundaries": ["read-only", "no network"], "tasks": [task],
                     "historical_context_edges": ([{"task_id": "T01", "dependency_task_id": "P00",
                                                    "manifest_path": "docs/implementation/baselines/P00-context-manifest.json"}] if historical else [])}
        if upstream_regression_reference:
            self.plan["tasks"].append({
                "id": "P00", "owner": "fixture-upstream", "kind": "implementation",
                "title": "Synthetic upstream owner", "depends_on": [], "case_ids": ["P00-C01"],
                "invariants": ["I01"], "allowed_changes": ["src/"],
                "completion": ["Upstream contract is sealed."], "rollback": "Remove fixture.",
            })
        case_list = [
            {"id": "R01-C01", "owner_task": "T01", "status": "specified_not_executed",
             "given": "valid fixture", "when": "verify", "then": ["pass"],
             "assertions": [{"id": "R01-C01.A01", "expected": "complete"}, {"id": "R01-C01.A02", "expected": "bound"}]},
            {"id": "R01-C02", "owner_task": "T01", "status": "specified_not_executed",
             "given": "implicit stable IDs", "when": "verify", "then": ["one", "two"]},
        ]
        if upstream_regression_reference:
            case_list.append({"id": "P00-C01", "owner_task": "P00", "status": "specified_not_executed",
                              "given": "upstream-owned contract", "when": "downstream regression check",
                              "then": ["result remains compatible"]})
        self.cases = {"cases": case_list}
        self.plan_path.write_bytes(_json_bytes(self.plan))
        self.catalog_path.write_bytes(_json_bytes(self.cases))
        self.roots = {"test": root.resolve()}
        self.plan_ref = self.ref(self.plan_path)
        self.catalog_ref = self.ref(self.catalog_path)
        self.core = self.make_core(task, historical=historical)
        self.receipt = self.seal(self.core)
        self.write_receipt()

    def ref(self, path: Path) -> dict[str, str]:
        rel = path.resolve().relative_to(self.root.resolve()).as_posix()
        return {"root_id": "test", "path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def make_core(self, task: dict, *, historical: bool = False) -> dict:
        snapshot = []
        for rel in ("src/module.py", "tests/test_module.py", "schemas/sample.schema.json"):
            p = self.root / rel
            snapshot.append({"root_id": "test", "path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        snapshot.sort(key=lambda x: (x["root_id"], x["path"]))
        snapshot_hash = receipts.canonical_sha256(snapshot)
        report = {
            "reviewer_id": "reviewer-fixture", "reviewer_role": "independent reviewer",
            "independent": True, "separation_basis": "different identity and no implementation access",
            "outcome": "approved", "implementation_snapshot_sha256": snapshot_hash,
            "open_findings": [],
        }
        review_path = self.root / "docs" / "implementation" / "reviews" / "T01" / "report.json"
        review_path.write_bytes(_json_bytes(report))
        review_ref = self.ref(review_path)
        case_results = []
        for case in self.cases["cases"]:
            ids = [a["id"] for a in case["assertions"]] if "assertions" in case else [f"{case['id']}.T{i:02d}" for i in range(1, len(case["then"]) + 1)]
            assertions = []
            for assertion_id in ids:
                assertions.append({
                    "assertion_id": assertion_id, "status": "passed", "test_stage": "unit",
                    "selector": f"tests/test_task_receipts.py::{assertion_id}",
                    "command": "python -X utf8 -m unittest tests.test_task_receipts", "exit_code": 0,
                    "log": self.ref(self.root / "docs" / "implementation" / "contracts" / "validation-T01-unit.log"), "skip_count": 0,
                    "isolation": {"isolated": True, "run_id": "fixture-run-001", "cleanup_verified": True,
                                  "cleanup_summary": "TemporaryDirectory removed after test."},
                    "network": {"mode": "none", "request_count": 0, "fees_usd": "0", "evidence": "No network adapter configured."},
                })
            case_results.append({"case_id": case["id"], "status": "passed", "assertions": assertions})
        dependencies = []
        if historical:
            baseline_dir = self.root / "docs/implementation/baselines"
            baseline_dir.mkdir(parents=True, exist_ok=True)
            report_input = baseline_dir / "baseline-report-2026-09-22.md"
            legacy_receipt = baseline_dir / "receipt-P00.json"
            report_input.write_text("synthetic historical baseline\n", encoding="utf-8")
            legacy_receipt.write_text('{"task_id":"P00","status":"implementation_complete"}\n', encoding="utf-8")
            manifest = {
                "manifest_version": "1.0", "dependency_task_id": "P00", "status": "context_only",
                "generated_at_utc": "2026-09-26T00:00:00Z", "eligibility_effect": "does_not_satisfy_current_dependency_or_close_gate",
                "files": [self.ref(report_input), self.ref(legacy_receipt)],
            }
            manifest_path = self.root / "docs/implementation/baselines/P00-context-manifest.json"
            manifest_path.write_bytes(_json_bytes(manifest))
            dependencies.append({"task_id": "P00", "kind": "historical_context", "evidence": self.ref(manifest_path), "status": "context_only"})
        return {
            "task_id": task["id"], "plan_version": self.plan["version"],
            "plan_sha256": hashlib.sha256(self.plan_path.read_bytes()).hexdigest(),
            "case_catalog_sha256": hashlib.sha256(self.catalog_path.read_bytes()).hexdigest(),
            "hash_algorithm": receipts.HASH_ALGORITHM,
            "task_spec_sha256": receipts.canonical_sha256(task),
            "owned_case_bundle_sha256": receipts.canonical_sha256(
                receipts._owned_case_bundle(task, self.cases, self.plan)),
            "referenced_case_bundle_sha256": receipts.canonical_sha256(
                receipts._referenced_case_bundle(task, self.cases, self.plan)),
            "global_boundaries_sha256": receipts.canonical_sha256(self.plan["global_boundaries"]),
            "implementation_author_id": "implementer-fixture", "case_results": case_results,
            "implementation_snapshot": snapshot, "implementation_snapshot_sha256": snapshot_hash,
            "independent_review": {**report, "report": review_ref}, "dependency_evidence": dependencies,
        }

    @staticmethod
    def seal(core: dict) -> dict:
        return {"schema_version": "2.0", "core": core, "core_sha256": receipts.canonical_sha256(core)}

    def write_receipt(self) -> None:
        self.receipt_path.write_bytes(_json_bytes(self.receipt))

    def verify(self) -> dict:
        return receipts.verify_receipt(self.ref(self.receipt_path), self.plan_ref, self.catalog_ref,
                                       self.roots, evaluated_at="2026-09-26T00:00:00Z")


class TaskReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="task-receipt-")
        self.root = Path(self.tmp.name)
        self.fx = ReceiptFixture(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def blockers(self, result: dict) -> set[str]:
        return {item["code"] for item in result.get("blockers", [])}

    def test_p00_p01_current_receipt_artifacts_are_allowlisted_without_replacing_legacy_baseline(self) -> None:
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root / "docs/implementation/tasks.json").read_text(encoding="utf-8"))
        tasks = {task["id"]: task for task in plan["tasks"]}
        p00_allowed = "\n".join(tasks["P00"]["allowed_changes"])
        p01_allowed = "\n".join(tasks["P01"]["allowed_changes"])
        legacy_receipt = root / "docs/implementation/baselines/receipt-P00.json"
        self.assertEqual(
            hashlib.sha256(legacy_receipt.read_bytes()).hexdigest(),
            "0d7cccbab76842ac7bd45e94e23242da88ff18a0c34b0910a310842ce0ee5983",
        )
        self.assertTrue(receipts._matches_task_change(
            "docs/implementation/baselines/baseline-report-2026-09-26.md", tasks["P00"]
        ))
        self.assertTrue(receipts._matches_task_change(
            "docs/implementation/contracts/validation-P00-current-r1.json", tasks["P00"]
        ))
        self.assertTrue(receipts._matches_task_change(
            "docs/implementation/contracts/validation-P00-current-r1.log", tasks["P00"]
        ))
        self.assertFalse(receipts._matches_task_change(
            "docs/implementation/baselines/receipt-P00.json", tasks["P00"]
        ))
        for task_id, allowed, artifacts in (
            ("P00", p00_allowed, (
                "docs/implementation/baselines/baseline-report-????-??-??.md",
                "docs/implementation/contracts/receipt-P00.json",
                "docs/implementation/contracts/validation-P00-*.json",
                "docs/implementation/contracts/validation-P00-*.log",
                "docs/implementation/reviews/P00/",
                "不修改legacy/、旧P00 v1或历史P01 manifest",
            )),
            ("P01", p01_allowed, (
                "docs/implementation/contracts/receipt-P01.json",
                "docs/implementation/contracts/validation-P01-*.log",
                "docs/implementation/contracts/validation-P01-current-*.json",
                "docs/implementation/contracts/validation-P01-self-check.json",
                "docs/implementation/reviews/P01/",
            )),
        ):
            for artifact in artifacts:
                with self.subTest(task_id=task_id, artifact=artifact):
                    self.assertIn(artifact, allowed)

    def test_canonical_hash_algorithm_is_utf8_compact_and_order_stable(self) -> None:
        value = {"z": 1, "你": "好", "a": [2, 1]}
        self.assertEqual(receipts.canonical_json_bytes(value), '{"a":[2,1],"z":1,"你":"好"}'.encode("utf-8"))
        with self.assertRaises(receipts.ReceiptError):
            receipts.canonical_json_bytes({"not_finite": float("nan")})

    def test_valid_receipt_and_schema_are_accepted(self) -> None:
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/quick_scan/task-receipt.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.fx.receipt)
        example = json.loads((Path(__file__).resolve().parents[1] / "examples/quick_scan/task-receipt-v2-example.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(example)
        self.assertEqual(example["core_sha256"], receipts.canonical_sha256(example["core"]))
        with patch.object(receipts, "read_ref", wraps=receipts.read_ref) as read_ref_spy:
            result = self.fx.verify()
        log_reads = [call for call in read_ref_spy.call_args_list
                     if isinstance(call.args[0], dict) and call.args[0].get("path") == "docs/implementation/contracts/validation-T01-unit.log"]
        self.assertEqual(len(log_reads), 4)
        self.assertTrue(result["eligible_to_close"], result)
        self.assertEqual(result["core_sha256"], self.fx.receipt["core_sha256"])
        self.assertRegex(result["validator_sha256"], r"^[a-f0-9]{64}$")
        assertion_schema = schema["$defs"]["assertion_result"]
        self.assertIn("test_stage", assertion_schema["required"])
        self.assertEqual(assertion_schema["properties"]["test_stage"]["enum"],
                         ["unit", "contract", "integration", "e2e", "review"])
        original_core = copy.deepcopy(self.fx.receipt["core"])
        for mutate in (
            lambda item: item.pop("test_stage"),
            lambda item: item.update(test_stage="manual_unknown"),
        ):
            with self.subTest(test_stage=mutate):
                core = copy.deepcopy(original_core)
                mutate(core["case_results"][0]["assertions"][0])
                self.fx.receipt = self.fx.seal(core)
                self.fx.write_receipt()
                self.assertIn("receipt_schema_invalid", self.blockers(self.fx.verify()))
        self.fx.receipt = self.fx.seal(original_core)
        self.fx.write_receipt()

    def test_case_and_assertion_sets_are_exact_and_derived_ids_are_stable(self) -> None:
        self.assertTrue(self.fx.verify()["eligible_to_close"])
        expected = ["R01-C02.T01", "R01-C02.T02"]
        got = [a["assertion_id"] for c in self.fx.receipt["core"]["case_results"] if c["case_id"] == "R01-C02" for a in c["assertions"]]
        self.assertEqual(got, expected)
        self.fx.receipt["core"]["case_results"].pop()
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        self.assertIn("case_result_set_mismatch", self.blockers(self.fx.verify()))

    def test_downstream_receipt_binds_upstream_regression_reference_separately_from_owned_cases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task-receipt-upstream-case-") as temp:
            fx = ReceiptFixture(Path(temp), historical=True, upstream_regression_reference=True)
            result = fx.verify()
            self.assertTrue(result["eligible_to_close"], result["blockers"])
            self.assertEqual(
                [case["id"] for case in receipts._owned_case_bundle(fx.plan["tasks"][0], fx.cases, fx.plan)],
                ["R01-C01", "R01-C02"],
            )
            self.assertEqual(
                sorted(case["case_id"] for case in fx.receipt["core"]["case_results"]),
                ["P00-C01", "R01-C01", "R01-C02"],
            )
            original_ref_hash = fx.receipt["core"]["referenced_case_bundle_sha256"]
            fx.cases["cases"][-1]["then"][0] = "upstream contract changed"
            fx.catalog_path.write_bytes(_json_bytes(fx.cases))
            fx.catalog_ref = fx.ref(fx.catalog_path)
            result = fx.verify()
            self.assertIn("referenced_case_bundle_sha256_stale", self.blockers(result))
            self.assertEqual(fx.receipt["core"]["referenced_case_bundle_sha256"], original_ref_hash)

    def test_referenced_case_requires_a_transitive_dependency_owner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task-receipt-unrelated-case-owner-") as temp:
            fx = ReceiptFixture(Path(temp), historical=True, upstream_regression_reference=True)
            task = fx.plan["tasks"][0]
            task["depends_on"] = []
            task["historical_context_dependencies"] = []
            fx.plan_path.write_bytes(_json_bytes(fx.plan))
            fx.plan_ref = fx.ref(fx.plan_path)
            self.assertIn("case_owner_not_dependency", self.blockers(fx.verify()))

    def test_referenced_case_requires_content_hash_for_new_receipts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task-receipt-missing-case-hash-") as temp:
            fx = ReceiptFixture(Path(temp), historical=True, upstream_regression_reference=True)
            fx.receipt["core"].pop("referenced_case_bundle_sha256")
            fx.receipt = fx.seal(fx.receipt["core"])
            fx.write_receipt()
            self.assertIn("referenced_case_bundle_sha256_missing", self.blockers(fx.verify()))

    def test_case_bundle_hash_failure_returns_blocked_sidecar_without_exception(self) -> None:
        self.fx.plan["tasks"][0]["case_ids"] = ["R01-C01"]
        self.fx.plan_path.write_bytes(_json_bytes(self.fx.plan))
        self.fx.plan_ref = self.fx.ref(self.fx.plan_path)
        result = self.fx.verify()
        self.assertFalse(result["eligible_to_close"])
        self.assertIn("owner_case_set_mismatch", self.blockers(result))

    def test_two_hop_dependency_owner_is_valid_and_deeper_cycles_fail_closed(self) -> None:
        task = {"id": "T01", "depends_on": ["MID"], "case_ids": ["P00-C01"]}
        middle = {"id": "MID", "depends_on": ["P00"], "case_ids": ["MID-C01"]}
        owner = {"id": "P00", "depends_on": [], "case_ids": ["P00-C01"]}
        plan = {"tasks": [task, middle, owner]}
        cases = {"cases": [{"id": "P00-C01", "owner_task": "P00", "status": "specified_not_executed",
                            "given": "ancestor-owned", "when": "two-hop regression", "then": ["compatible"]}]}
        self.assertEqual([item["id"] for item in receipts._task_case_bundle(task, cases, plan)], ["P00-C01"])
        owner["depends_on"] = ["MID"]
        with self.assertRaisesRegex(receipts.ReceiptError, "case_owner_dependency_invalid"):
            receipts._task_case_bundle(task, cases, plan)

    def test_owner_only_legacy_v2_receipt_remains_compatible_without_reference_hash(self) -> None:
        self.fx.receipt["core"].pop("referenced_case_bundle_sha256")
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        self.assertTrue(self.fx.verify()["eligible_to_close"])

    def test_unrelated_plan_and_catalog_additions_do_not_stale_owner_hashes(self) -> None:
        self.fx.plan["version"] = "test-2"
        self.fx.plan["tasks"].append({"id": "OTHER", "owner": "other", "depends_on": [], "case_ids": ["OTHER-C01"]})
        self.fx.cases["cases"].append({"id": "OTHER-C01", "owner_task": "OTHER", "status": "specified_not_executed", "given": "x", "when": "y", "then": ["z"]})
        self.fx.plan_path.write_bytes(_json_bytes(self.fx.plan))
        self.fx.catalog_path.write_bytes(_json_bytes(self.fx.cases))
        self.assertTrue(self.fx.verify()["eligible_to_close"])

    def test_task_case_and_global_boundary_changes_stale_receipt(self) -> None:
        for mutate, blocker in (
            (lambda: self.fx.plan["tasks"][0].update(title="changed"), "task_spec_sha256_stale"),
            (lambda: self.fx.cases["cases"][0]["then"].append("new assertion scope"), "owned_case_bundle_sha256_stale"),
            (lambda: self.fx.plan["global_boundaries"].append("new hard boundary"), "global_boundaries_sha256_stale"),
        ):
            with self.subTest(blocker=blocker):
                old_plan, old_cases = copy.deepcopy(self.fx.plan), copy.deepcopy(self.fx.cases)
                mutate()
                self.fx.plan_path.write_bytes(_json_bytes(self.fx.plan))
                self.fx.catalog_path.write_bytes(_json_bytes(self.fx.cases))
                self.assertIn(blocker, self.blockers(self.fx.verify()))
                self.fx.plan, self.fx.cases = old_plan, old_cases
                self.fx.plan_path.write_bytes(_json_bytes(old_plan))
                self.fx.catalog_path.write_bytes(_json_bytes(old_cases))

    def test_core_tamper_duplicate_and_unexpected_assertions_fail_closed(self) -> None:
        baseline = copy.deepcopy(self.fx.receipt["core"])
        mutations = (
            (lambda core: core["case_results"].append(copy.deepcopy(core["case_results"][0])), "case_result_set_mismatch"),
            (lambda core: core["case_results"].append({"case_id": "EXTRA", "status": "passed", "assertions": copy.deepcopy(core["case_results"][0]["assertions"])}), "case_result_set_mismatch"),
            (lambda core: core["case_results"][0]["assertions"].pop(), "assertion_result_set_mismatch"),
            (lambda core: core["case_results"][0]["assertions"].append(copy.deepcopy(core["case_results"][0]["assertions"][0])), "assertion_result_set_mismatch"),
        )
        for mutate, expected in mutations:
            with self.subTest(expected=expected):
                core = copy.deepcopy(baseline)
                mutate(core)
                self.fx.receipt = self.fx.seal(core)
                self.fx.write_receipt()
                self.assertIn(expected, self.blockers(self.fx.verify()))

    def test_failed_not_run_and_not_applicable_statuses_do_not_close(self) -> None:
        for status in ("failed", "not_run", "not_applicable"):
            with self.subTest(status=status):
                core = copy.deepcopy(self.fx.receipt["core"])
                core["case_results"][0]["assertions"][0]["status"] = status
                self.fx.receipt = self.fx.seal(core)
                self.fx.write_receipt()
                result = self.fx.verify()
                self.assertIn("assertion_not_passed", self.blockers(result))
                case_result = next(item for item in result["case_results"] if item["case_id"] == "R01-C01")
                assertion_result = next(item for item in case_result["assertions"] if item["assertion_id"] == "R01-C01.A01")
                self.assertEqual(case_result["reported_status"], "passed")
                self.assertEqual(case_result["status"], "blocked")
                self.assertEqual(assertion_result["reported_status"], status)
                self.assertEqual(assertion_result["status"], "blocked")

    def test_malformed_v2_fails_closed_without_echoing_extra_sensitive_fields(self) -> None:
        marker = "SECRET_PAYLOAD_SHOULD_NEVER_APPEAR_IN_OUTPUT_2048"
        core = copy.deepcopy(self.fx.receipt["core"])
        core["unexpected_secret_payload"] = marker
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        result = self.fx.verify()
        self.assertFalse(result["eligible_to_close"])
        self.assertIn("receipt_schema_invalid", self.blockers(result))
        self.assertNotIn(marker, json.dumps(result))

    def test_current_contract_hash_mismatch_fails_closed(self) -> None:
        self.fx.receipt["core"]["task_spec_sha256"] = "0" * 64
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        self.assertIn("task_spec_sha256_stale", self.blockers(self.fx.verify()))

    def test_snapshot_change_makes_preseal_review_stale(self) -> None:
        (self.root / "src/module.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.assertIn("evidence_hash_mismatch", self.blockers(self.fx.verify()))
        self.assertIn("review_stale", self.blockers(self.fx.verify()))

    def test_missing_empty_tampered_logs_exit_status_and_skips_block(self) -> None:
        log = self.fx.receipt["core"]["case_results"][0]["assertions"][0]["log"]
        path = self.root / log["path"]
        original = path.read_bytes()
        variants = [
            (lambda: path.unlink(), "evidence_file_missing"),
            (lambda: path.write_bytes(b" \n"), "test_log_empty"),
            (lambda: path.write_text("tampered\n", encoding="utf-8"), "evidence_hash_mismatch"),
            (lambda: self.fx.receipt["core"]["case_results"][0]["assertions"][0].update(exit_code=3), "test_exit_code_nonzero_or_missing"),
            (lambda: self.fx.receipt["core"]["case_results"][0]["assertions"][0].update(skip_count=1), "test_skipped_or_skip_count_invalid"),
        ]
        for change, expected in variants:
            with self.subTest(expected=expected):
                path.write_bytes(original)
                self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
                if expected == "test_log_empty":
                    self.fx.receipt["core"]["case_results"][0]["assertions"][0]["log"]["sha256"] = hashlib.sha256(b" \n").hexdigest()
                change()
                self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
                self.fx.write_receipt()
                self.assertIn(expected, self.blockers(self.fx.verify()))

    def test_review_forgery_self_review_and_review_cycle_are_rejected(self) -> None:
        core = copy.deepcopy(self.fx.receipt["core"])
        core["independent_review"]["reviewer_id"] = core["implementation_author_id"]
        review_path = self.root / "docs/implementation/reviews/T01/report.json"
        report = json.loads(review_path.read_text(encoding="utf-8"))
        report["reviewer_id"] = core["implementation_author_id"]
        review_path.write_bytes(_json_bytes(report))
        core["independent_review"]["report"] = self.fx.ref(review_path)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        self.assertIn("reviewer_not_independent", self.blockers(self.fx.verify()))

        core["independent_review"]["reviewer_id"] = "reviewer-fixture"
        report["reviewer_id"] = "reviewer-fixture"
        report["receipt_core_sha256"] = "f" * 64
        review_path.write_bytes(_json_bytes(report))
        core["independent_review"]["report"] = self.fx.ref(review_path)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        self.assertIn("review_cycle_reference_rejected", self.blockers(self.fx.verify()))

    def test_absolute_traversal_sensitive_and_symlink_escape_paths_are_rejected(self) -> None:
        assertion = self.fx.receipt["core"]["case_results"][0]["assertions"][0]
        log = assertion["log"]
        for path in ("../outside.log", "/outside.log", "secrets/key.txt"):
            with self.subTest(path=path):
                assertion["log"] = {**log, "path": path}
                self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
                self.fx.write_receipt()
                self.assertFalse(self.fx.verify()["eligible_to_close"])
        assertion["log"] = log

        outside_tmp = tempfile.TemporaryDirectory(prefix="task-receipt-outside-")
        self.addCleanup(outside_tmp.cleanup)
        outside = Path(outside_tmp.name) / "outside.log"
        outside.write_text("must not read\n", encoding="utf-8")
        escape = self.root / "docs" / "implementation" / "contracts" / "validation-T01-linked.log"
        escape.write_text("link placeholder\n", encoding="utf-8")
        original_resolve = Path.resolve
        def forged_resolve(path: Path, *args, **kwargs):
            if path == escape:
                return outside.resolve()
            return original_resolve(path, *args, **kwargs)
        assertion["log"] = {**log, "path": "docs/implementation/contracts/validation-T01-linked.log", "sha256": hashlib.sha256(escape.read_bytes()).hexdigest()}
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        with patch.object(Path, "resolve", autospec=True, side_effect=forged_resolve):
            self.assertIn("path_escape_rejected", self.blockers(self.fx.verify()))
        outside.unlink()

        protected = self.root / "company-wiki" / "companies" / "secret-company" / "summary.md"
        protected.parent.mkdir(parents=True, exist_ok=True)
        protected.write_text("must not be read\n", encoding="utf-8")
        hidden_alias = self.root / "docs" / "implementation" / "contracts" / "validation-T01-ordinary-name.log"
        hidden_alias.write_text("symlink placeholder\n", encoding="utf-8")
        assertion["log"] = {**log, "path": "docs/implementation/contracts/validation-T01-ordinary-name.log",
                            "sha256": hashlib.sha256(protected.read_bytes()).hexdigest()}
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        def sensitive_target_resolve(path: Path, *args, **kwargs):
            if path == hidden_alias:
                return protected.resolve()
            return original_resolve(path, *args, **kwargs)
        real_read_bytes = Path.read_bytes
        def guarded_read_bytes(path: Path):
            if path == protected:
                raise AssertionError("protected symlink target was read")
            return real_read_bytes(path)
        with patch.object(Path, "resolve", autospec=True, side_effect=sensitive_target_resolve), \
             patch.object(Path, "read_bytes", autospec=True, side_effect=guarded_read_bytes):
            self.assertIn("sensitive_path_rejected", self.blockers(self.fx.verify()))

        protected_root = self.root / "secrets"
        protected_root.mkdir()
        with self.assertRaisesRegex(receipts.ReceiptError, "sensitive_root_rejected"):
            receipts._root_map([f"private={protected_root}"])
        source_tmp = tempfile.TemporaryDirectory(prefix="receipt-hardlink-outside-")
        self.addCleanup(source_tmp.cleanup)
        source = Path(source_tmp.name) / "private.log"
        source.write_text("protected linked material\n", encoding="utf-8")
        alias = self.root / "evidence" / "linked-private.log"
        os.link(source, alias)
        ref = {"root_id": "test", "path": "evidence/linked-private.log",
               "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(receipts.ReceiptError, "hardlink_evidence_rejected"):
            receipts.resolve_ref(ref, self.fx.roots)

    def test_reference_purpose_and_task_scope_reject_unapproved_files_before_read(self) -> None:
        settings = self.root / "config" / "provider-settings.toml"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text("token = 'must not read'\n", encoding="utf-8")
        ordinary_config = self.root / "config" / "runtime.toml"
        ordinary_config.write_text("mode = 'fixture'\n", encoding="utf-8")
        original_read_bytes = Path.read_bytes

        def guarded_read_bytes(path: Path):
            if path in {settings, ordinary_config}:
                raise AssertionError(f"unapproved settings were read: {path.name}")
            return original_read_bytes(path)

        core = copy.deepcopy(self.fx.receipt["core"])
        core["implementation_snapshot"][0] = self.fx.ref(ordinary_config)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        with patch.object(Path, "read_bytes", autospec=True, side_effect=guarded_read_bytes):
            result = self.fx.verify()
        self.assertIn("snapshot_path_not_allowlisted", self.blockers(result))

        core = copy.deepcopy(self.fx.receipt["core"])
        core["implementation_snapshot"][0] = self.fx.ref(settings)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        with patch.object(Path, "read_bytes", autospec=True, side_effect=guarded_read_bytes):
            result = self.fx.verify()
        self.assertIn("sensitive_path_rejected", self.blockers(result))

        body = self.root / "evidence" / "body.log"
        body.write_text("full web page body must not be read\n", encoding="utf-8")
        body_ref = self.fx.ref(body)
        core = copy.deepcopy(self.fx.receipt["core"])
        assertion = core["case_results"][0]["assertions"][0]
        assertion["log"] = body_ref
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()

        def guard_settings_and_body(path: Path):
            if path in {settings, ordinary_config, body}:
                raise AssertionError(f"unapproved material was read: {path.name}")
            return original_read_bytes(path)

        with patch.object(Path, "read_bytes", autospec=True, side_effect=guard_settings_and_body):
            with self.assertRaisesRegex(receipts.ReceiptError, "review_report_path_rejected"):
                receipts.read_ref(body_ref, self.fx.roots, purpose="review_report", task_id="T01")
            with self.assertRaisesRegex(receipts.ReceiptError, "historical_context_path_not_allowlisted"):
                receipts.read_ref(body_ref, self.fx.roots, purpose="historical_manifest",
                                  allowed_paths={"docs/implementation/baselines/P00-context-manifest.json"})

        with patch.object(Path, "read_bytes", autospec=True, side_effect=guard_settings_and_body):
            result = self.fx.verify()
        self.assertIn("test_log_path_rejected", self.blockers(result))

        alias = self.root / "docs" / "implementation" / "contracts" / "validation-T01-linked-body.log"
        alias.write_text("symlink placeholder\n", encoding="utf-8")
        core = copy.deepcopy(self.fx.receipt["core"])
        core["case_results"][0]["assertions"][0]["log"] = self.fx.ref(alias)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()
        original_resolve = Path.resolve

        def redirect_allowed_alias(path: Path, *args, **kwargs):
            return body.resolve() if path == alias else original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", autospec=True, side_effect=redirect_allowed_alias), \
             patch.object(Path, "read_bytes", autospec=True, side_effect=guard_settings_and_body):
            result = self.fx.verify()
        self.assertIn("test_log_path_rejected", self.blockers(result))

        source_alias = self.root / "src" / "allowed-alias.py"
        source_alias.write_text("VALUE = 2\n", encoding="utf-8")
        core = copy.deepcopy(self.fx.receipt["core"])
        core["implementation_snapshot"][0] = self.fx.ref(source_alias)
        self.fx.receipt = self.fx.seal(core)
        self.fx.write_receipt()

        def redirect_source_alias(path: Path, *args, **kwargs):
            return ordinary_config.resolve() if path == source_alias else original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", autospec=True, side_effect=redirect_source_alias), \
             patch.object(Path, "read_bytes", autospec=True, side_effect=guard_settings_and_body):
            result = self.fx.verify()
        self.assertIn("snapshot_path_not_allowlisted", self.blockers(result))

        with self.assertRaisesRegex(receipts.ReceiptError, "sensitive_path_rejected"):
            receipts.read_ref(self.fx.ref(settings), self.fx.roots, purpose="control", expected_hash=False)

    def test_legacy_v1_remains_historical_and_unchanged(self) -> None:
        old = self.fx.receipt_path.read_bytes()
        legacy = self.root / "evidence/legacy-v1.json"
        legacy.write_text('{"task_id":"T01","status":"verified"}\n', encoding="utf-8")
        before = legacy.read_bytes()
        result = receipts.verify_receipt(self.fx.ref(legacy), self.fx.plan_ref, self.fx.catalog_ref,
                                         self.fx.roots, evaluated_at="2026-09-26T00:00:00Z")
        self.assertEqual(result["status"], "legacy_historical")
        self.assertFalse(result["eligible_to_close"])
        self.assertEqual(legacy.read_bytes(), before)
        self.assertEqual(self.fx.receipt_path.read_bytes(), old)

    def test_verifier_does_not_execute_recorded_commands_or_write_inputs_or_emit_secrets(self) -> None:
        marker = self.root / "command-ran.marker"
        secret = "TEST_ONLY_SECRET_VALUE_81927"
        assertion = self.fx.receipt["core"]["case_results"][0]["assertions"][0]
        assertion["command"] = f"python -c \"from pathlib import Path; Path('{marker}').write_text('{secret}')\""
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob("*") if p.is_file()}
        result = self.fx.verify()
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertFalse(marker.exists())
        self.assertEqual(before, after)
        self.assertNotIn(secret, json.dumps(result))
        repo = Path(__file__).resolve().parents[1]
        command = [
            sys.executable, str(repo / "scripts/task_receipts.py"), "verify",
            "--receipt", f"test:{self.fx.receipt_path.relative_to(self.root).as_posix()}",
            "--plan", f"test:{self.fx.plan_path.relative_to(self.root).as_posix()}",
            "--cases", f"test:{self.fx.catalog_path.relative_to(self.root).as_posix()}",
            "--root", f"test={self.root}",
        ]
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False,
                                   env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertFalse(marker.exists())
        self.assertNotIn(secret, completed.stdout)
        after_cli = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after_cli)

        selector_secret = "test_secret=TEST_ONLY_SELECTOR_SECRET_VALUE_0123456789"
        assertion["selector"] = selector_secret
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        before_unsafe_selector_cli = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in self.root.rglob("*") if p.is_file()}
        unsafe_selector_cli = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False,
                                             env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(unsafe_selector_cli.returncode, 1, unsafe_selector_cli.stderr + unsafe_selector_cli.stdout)
        self.assertNotIn(selector_secret, unsafe_selector_cli.stdout)
        unsafe_result = json.loads(unsafe_selector_cli.stdout)
        unsafe_assertion = unsafe_result["case_results"][0]["assertions"][0]
        self.assertIsNone(unsafe_assertion["selector"])
        self.assertFalse(unsafe_assertion["checks"]["selector_present"])
        self.assertIn("test_selector_unsafe", self.blockers(unsafe_result))
        after_unsafe_selector_cli = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before_unsafe_selector_cli, after_unsafe_selector_cli)

        path_secret = "sk-abcdefghijklmnopqrstuvwxyz"
        assertion["log"]["path"] = f"docs/implementation/contracts/validation-T01-{path_secret}.log"
        self.fx.receipt = self.fx.seal(self.fx.receipt["core"])
        self.fx.write_receipt()
        before_unsafe_path_cli = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in self.root.rglob("*") if p.is_file()}
        unsafe_path_cli = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False,
                                         env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(unsafe_path_cli.returncode, 1, unsafe_path_cli.stderr + unsafe_path_cli.stdout)
        self.assertNotIn(path_secret, unsafe_path_cli.stdout)
        unsafe_path_result = json.loads(unsafe_path_cli.stdout)
        unsafe_path_assertion = unsafe_path_result["case_results"][0]["assertions"][0]
        self.assertIsNone(unsafe_path_assertion["log_evidence"]["path"])
        self.assertEqual(unsafe_path_assertion["log_evidence"]["error_code"], "test_log_path_unsafe")
        self.assertIn("test_log_path_unsafe", self.blockers(unsafe_path_result))
        after_unsafe_path_cli = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before_unsafe_path_cli, after_unsafe_path_cli)

    def test_public_cli_is_read_only_and_returns_a_detached_sidecar(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        command = [
            sys.executable, str(repo / "scripts/task_receipts.py"), "verify",
            "--receipt", f"test:{self.fx.receipt_path.relative_to(self.root).as_posix()}",
            "--plan", f"test:{self.fx.plan_path.relative_to(self.root).as_posix()}",
            "--cases", f"test:{self.fx.catalog_path.relative_to(self.root).as_posix()}",
            "--root", f"test={self.root}",
        ]
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob("*") if p.is_file()}
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False,
                                   env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        result = json.loads(completed.stdout)
        self.assertTrue(result["eligible_to_close"])
        self.assertEqual(result["core_sha256"], self.fx.receipt["core_sha256"])
        self.assertRegex(result["validator_sha256"], r"^[a-f0-9]{64}$")
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(set(result), {"schema_version", "status", "eligible_to_close", "blockers",
                                       "core_sha256", "receipt_sha256", "validator_sha256", "evaluated_at_utc",
                                       "case_results"})
        assertion = result["case_results"][0]["assertions"][0]
        self.assertEqual(assertion["selector"], self.fx.receipt["core"]["case_results"][0]["assertions"][0]["selector"])
        self.assertEqual(assertion["log_evidence"]["path"], "docs/implementation/contracts/validation-T01-unit.log")
        self.assertTrue(assertion["log_evidence"]["hash_valid"])
        self.assertEqual(assertion["log_evidence"]["actual_sha256"], assertion["log_evidence"]["expected_sha256"])
        self.assertEqual(assertion["status"], "passed")
        self.assertEqual(assertion["reported_status"], "passed")
        self.assertEqual(assertion["validation_status"], "passed")
        self.assertNotIn('"command"', completed.stdout)

    def test_historical_p00_manifest_is_context_only_and_hash_locked(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="task-receipt-bootstrap-")
        self.addCleanup(temp.cleanup)
        fx = ReceiptFixture(Path(temp.name), historical=True)
        result = fx.verify()
        self.assertTrue(result["eligible_to_close"], result)
        self.assertEqual(fx.receipt["core"]["dependency_evidence"][0]["status"], "context_only")
        self.assertTrue(receipts._is_known_legacy_receipt({"task_id": "P00"}))
        self.assertTrue(receipts._is_known_legacy_receipt({"task_id": "P00", "schema_version": "1.0"}))
        for unknown in ("2.0", "3.0", "unknown", None):
            with self.subTest(unknown_schema_version=unknown):
                self.assertFalse(receipts._is_known_legacy_receipt({"task_id": "P00", "schema_version": unknown}))
        manifest_ref = fx.receipt["core"]["dependency_evidence"][0]["evidence"]
        manifest = json.loads((fx.root / manifest_ref["path"]).read_text(encoding="utf-8"))
        legacy_receipt = fx.root / manifest["files"][1]["path"]
        legacy_receipt.write_text('{"schema_version":"2.0","core":{},"core_sha256":"' + "0" * 64 + '"}\n', encoding="utf-8")
        self.assertIn("evidence_hash_mismatch", self.blockers(fx.verify()))

    def test_public_verifier_only_classifies_known_legacy_receipts_as_historical(self) -> None:
        old_receipt = self.fx.root / "evidence/receipt-pre-versioned.json"
        old_receipt.write_bytes(_json_bytes({"task_id": "P00", "status": "verified"}))
        old_result = receipts.verify_receipt(self.fx.ref(old_receipt), self.fx.plan_ref, self.fx.catalog_ref,
                                             self.fx.roots, evaluated_at="2026-09-26T00:00:00Z")
        self.assertEqual(old_result["status"], "legacy_historical")

        for version in ("3.0", "unknown", None):
            with self.subTest(schema_version=version):
                path = self.fx.root / f"evidence/unsupported-receipt-{version}.json"
                path.write_bytes(_json_bytes({"schema_version": version, "task_id": "P00", "status": "legacy"}))
                result = receipts.verify_receipt(self.fx.ref(path), self.fx.plan_ref, self.fx.catalog_ref,
                                                 self.fx.roots, evaluated_at="2026-09-26T00:00:00Z")
                self.assertEqual(result["status"], "blocked")
                self.assertFalse(result["eligible_to_close"])
                self.assertEqual(result["blockers"], [{"code": "receipt_schema_version_unsupported"}])

        malformed = self.fx.root / "evidence/non-object-receipt.json"
        malformed.write_bytes(_json_bytes(["not", "an", "envelope"]))
        result = receipts.verify_receipt(self.fx.ref(malformed), self.fx.plan_ref, self.fx.catalog_ref,
                                         self.fx.roots, evaluated_at="2026-09-26T00:00:00Z")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blockers"], [{"code": "receipt_invalid"}])

    def test_duplicate_json_keys_block_public_verifier_and_cli(self) -> None:
        raw = json.dumps(self.fx.receipt, ensure_ascii=False, indent=2) + "\n"
        marker = '"assertion_id": "R01-C01.A01",'
        marker_pos = raw.index(marker) + len(marker)
        status_pos = raw.index('"status": "passed"', marker_pos)
        raw = raw[:status_pos] + '"status": "failed",\n              "status": "passed"' + raw[status_pos + len('"status": "passed"'):]
        self.fx.receipt_path.write_text(raw, encoding="utf-8")
        result = self.fx.verify()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("json_duplicate_key", self.blockers(result))

        repo = Path(__file__).resolve().parents[1]
        command = [
            sys.executable, str(repo / "scripts/task_receipts.py"), "verify",
            "--receipt", f"test:{self.fx.receipt_path.relative_to(self.root).as_posix()}",
            "--plan", f"test:{self.fx.plan_path.relative_to(self.root).as_posix()}",
            "--cases", f"test:{self.fx.catalog_path.relative_to(self.root).as_posix()}",
            "--root", f"test={self.root}",
        ]
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False,
                                   env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
        cli_result = json.loads(completed.stdout)
        self.assertEqual(cli_result["status"], "blocked")
        self.assertIn("json_duplicate_key", self.blockers(cli_result))

    def test_historical_context_cannot_be_forged_into_a_current_v2_dependency(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="task-receipt-context-forgery-")
        self.addCleanup(temp.cleanup)
        fx = ReceiptFixture(Path(temp.name), historical=True)
        manifest_ref = fx.receipt["core"]["dependency_evidence"][0]["evidence"]
        manifest_path = fx.root / manifest_ref["path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        legacy_ref = manifest["files"][1]
        legacy_path = fx.root / legacy_ref["path"]
        legacy_path.write_text('{"schema_version":"2.0","core":{},"core_sha256":"' + "0" * 64 + '"}\n', encoding="utf-8")
        manifest["files"][1]["sha256"] = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
        manifest_path.write_bytes(_json_bytes(manifest))
        fx.receipt["core"]["dependency_evidence"][0]["evidence"] = fx.ref(manifest_path)
        fx.receipt = fx.seal(fx.receipt["core"])
        fx.write_receipt()
        self.assertIn("historical_dependency_receipt_not_legacy", self.blockers(fx.verify()))

        for version in ("3.0", "unknown", None):
            with self.subTest(unknown_schema_version=version):
                version_temp = tempfile.TemporaryDirectory(prefix="task-receipt-unknown-legacy-version-")
                self.addCleanup(version_temp.cleanup)
                version_fx = ReceiptFixture(Path(version_temp.name), historical=True)
                version_manifest_ref = version_fx.receipt["core"]["dependency_evidence"][0]["evidence"]
                version_manifest_path = version_fx.root / version_manifest_ref["path"]
                version_manifest = json.loads(version_manifest_path.read_text(encoding="utf-8"))
                version_legacy_path = version_fx.root / version_manifest["files"][1]["path"]
                version_legacy_path.write_bytes(_json_bytes({"schema_version": version, "task_id": "P00", "status": "legacy"}))
                version_manifest["files"][1]["sha256"] = hashlib.sha256(version_legacy_path.read_bytes()).hexdigest()
                version_manifest_path.write_bytes(_json_bytes(version_manifest))
                version_fx.receipt["core"]["dependency_evidence"][0]["evidence"] = version_fx.ref(version_manifest_path)
                version_fx.receipt = version_fx.seal(version_fx.receipt["core"])
                version_fx.write_receipt()
                self.assertIn("historical_dependency_receipt_not_legacy", self.blockers(version_fx.verify()))

        malformed_temp = tempfile.TemporaryDirectory(prefix="task-receipt-malformed-manifest-")
        self.addCleanup(malformed_temp.cleanup)
        malformed_fx = ReceiptFixture(Path(malformed_temp.name), historical=True)
        malformed_manifest_ref = malformed_fx.receipt["core"]["dependency_evidence"][0]["evidence"]
        malformed_manifest_path = malformed_fx.root / malformed_manifest_ref["path"]
        malformed_manifest = json.loads(malformed_manifest_path.read_text(encoding="utf-8"))
        malformed_manifest["files"][0]["path"] = {"unhashable": ["path"]}
        malformed_manifest_path.write_bytes(_json_bytes(malformed_manifest))
        malformed_fx.receipt["core"]["dependency_evidence"][0]["evidence"] = malformed_fx.ref(malformed_manifest_path)
        malformed_fx.receipt = malformed_fx.seal(malformed_fx.receipt["core"])
        malformed_fx.write_receipt()
        self.assertIn("historical_context_manifest_entry_invalid", self.blockers(malformed_fx.verify()))

    def test_legacy_or_missing_current_dependency_never_satisfies_close_gate(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="task-receipt-dependency-")
        self.addCleanup(temp.cleanup)
        fx = ReceiptFixture(Path(temp.name))
        task = fx.plan["tasks"][0]
        task["depends_on"] = ["P00"]
        task["historical_context_dependencies"] = []
        fx.plan_path.write_bytes(_json_bytes(fx.plan))
        fx.receipt["core"]["dependency_evidence"] = [{
            "task_id": "P00", "kind": "current_receipt", "status": "legacy_historical",
            "evidence": {"root_id": "test", "path": "evidence/legacy-v1.json", "sha256": "0" * 64},
        }]
        (fx.root / "evidence/legacy-v1.json").write_text('{"task_id":"P00","status":"verified"}\n', encoding="utf-8")
        fx.receipt["core"]["task_spec_sha256"] = receipts.canonical_sha256(task)
        fx.receipt = fx.seal(fx.receipt["core"])
        fx.write_receipt()
        self.assertIn("current_dependency_not_verified", self.blockers(fx.verify()))
        cycle = receipts._verify_loaded(fx.receipt, fx.plan, fx.cases, fx.roots,
                                        (fx.plan_path.read_bytes(), fx.catalog_path.read_bytes()), {"T01"})
        self.assertIn("dependency_cycle", self.blockers(cycle))

    def test_detached_sidecar_does_not_mutate_core_and_core_rejects_postseal_review(self) -> None:
        before = self.fx.receipt_path.read_bytes()
        sidecar = self.fx.verify()
        self.assertEqual(sidecar["core_sha256"], self.fx.receipt["core_sha256"])
        self.assertIn("validator_sha256", sidecar)
        self.assertEqual(self.fx.receipt_path.read_bytes(), before)
        core = copy.deepcopy(self.fx.receipt["core"])
        core["post_seal_review"] = {"report": "detached"}
        wrapper = self.fx.seal(core)
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/quick_scan/task-receipt.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(wrapper)))


if __name__ == "__main__":
    unittest.main()
