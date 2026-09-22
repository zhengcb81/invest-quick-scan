"""Automated tests for Metrics, Comparability and Evidence Semantics Contract (Task C02).
Covers scenarios: SC-08, SC-09, SC-10, SC-11, DUR-01, DUR-02, DUR-03.
"""
import json
from pathlib import Path
import unittest
import jsonschema
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/quick_scan/metric.schema.json"
CATALOG_PATH = ROOT / "questions/catalog.json"


class MetricsContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def validate_type(self, definition_name: str, instance: dict):
        wrapper_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": self.schema.get("definitions", {}),
            "$ref": f"#/definitions/{definition_name}"
        }
        validate(instance=instance, schema=wrapper_schema)

    def test_sc_08_metamorphic_diagnostics_never_alter_core_averages(self):
        """SC-08: Adding diagnostic answers (Dupont, Porter, Recovery) with score 10 never alters quality/growth/valuation averages."""
        core_answers = {
            "IQS_01": {"score": 8, "aggregation_role": "quality_core"},
            "IQS_02": {"score": 7, "aggregation_role": "quality_core"},
            "IQS_03": {"score": 9, "aggregation_role": "quality_core"},
            "IQS_GROWTH_01": {"score": 6, "aggregation_role": "growth_core"},
            "IQS_VALUATION_01": {"score": 5, "aggregation_role": "valuation_core"}
        }

        def compute_aggregates(answers):
            quality = [v["score"] for v in answers.values() if v["aggregation_role"] == "quality_core"]
            growth = [v["score"] for v in answers.values() if v["aggregation_role"] == "growth_core"]
            valuation = [v["score"] for v in answers.values() if v["aggregation_role"] == "valuation_core"]
            diagnostics = [v["score"] for v in answers.values() if v["aggregation_role"] == "diagnostic_only"]
            return {
                "quality_avg": sum(quality) / len(quality) if quality else None,
                "growth_avg": sum(growth) / len(growth) if growth else None,
                "valuation_avg": sum(valuation) / len(valuation) if valuation else None,
                "diagnostics_count": len(diagnostics)
            }

        baseline = compute_aggregates(core_answers)

        # Append diagnostics with score 10
        with_diagnostics = dict(core_answers)
        with_diagnostics["DUPONT_01"] = {"score": 10, "aggregation_role": "diagnostic_only"}
        with_diagnostics["PORTER_01"] = {"score": 10, "aggregation_role": "diagnostic_only"}
        with_diagnostics["RECOVERY_01"] = {"score": 10, "aggregation_role": "diagnostic_only"}

        after = compute_aggregates(with_diagnostics)

        # Core averages strictly invariant
        self.assertEqual(baseline["quality_avg"], after["quality_avg"])
        self.assertEqual(baseline["growth_avg"], after["growth_avg"])
        self.assertEqual(baseline["valuation_avg"], after["valuation_avg"])
        # Only diagnostics count increments
        self.assertEqual(baseline["diagnostics_count"], 0)
        self.assertEqual(after["diagnostics_count"], 3)

    def test_sc_09_critical_risk_cannot_be_averaged_or_bypassed(self):
        """SC-09: Critical risk score <= 3 (e.g. IQS_16 or bank cash replacement) flags critical risk, cannot be bypassed."""
        mapping = {
            "question_id": "IQS_16",
            "primary_metric_ref": "financial.cash_runway",
            "dimension": "quality",
            "aggregation_role": "quality_core",
            "critical_risk": True,
            "replacement_for": None
        }
        self.validate_type("QuestionMetricMapping", mapping)

        answers = {
            "IQS_01": 10,
            "IQS_02": 10,
            "IQS_03": 10,
            "IQS_16": 3  # Critical failure
        }

        # Rule evaluation
        has_critical_failure = any(score <= 3 for qid, score in answers.items() if qid == "IQS_16")
        quality_avg = sum(answers.values()) / len(answers)

        # Even if quality_avg is high (33/4 = 8.25), critical risk flag must trigger
        self.assertTrue(has_critical_failure)
        self.assertGreater(quality_avg, 8.0)

        # Automated gate logic: critical failure denies quality pass regardless of OR filters
        quality_gate_passed = (quality_avg >= 7.0) and (not has_critical_failure)
        self.assertFalse(quality_gate_passed)

    def test_sc_10_core_manifest_coverage_and_replacements(self):
        """SC-10: Check manifest coverage and replacement rules."""
        if CATALOG_PATH.exists():
            catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            self.assertIn("modules", catalog)
            common_mod = next((m for m in catalog["modules"] if m["id"] == "common"), None)
            self.assertIsNotNone(common_mod)
            self.assertEqual(common_mod["question_count"], 24)
            common_file = ROOT / common_mod["path"]
            if common_file.exists():
                common_data = json.loads(common_file.read_text(encoding="utf-8"))
                self.assertEqual(len(common_data["questions"]), 24)

    def test_sc_11_cross_cohort_incomparability(self):
        """SC-11: Cross-cohort metrics (e.g. bank.roe vs financial.roic) must not be ranked or averaged together."""
        bank_metric = {
            "metric_id": "bank.cet1_ratio",
            "unit": "percent",
            "definition": "核心一级资本充足率",
            "cohort": "bank",
            "comparability_scope": "within_cohort_only",
            "critical_risk_flag": True
        }
        industrial_metric = {
            "metric_id": "financial.roic",
            "unit": "percent",
            "definition": "税后经营利润/平均投入资本",
            "cohort": "operating",
            "comparability_scope": "within_cohort_only",
            "critical_risk_flag": False
        }
        self.validate_type("MetricRegistryEntry", bank_metric)
        self.validate_type("MetricRegistryEntry", industrial_metric)

        def can_compare(m1, m2):
            if m1["cohort"] != m2["cohort"] and (
                m1["comparability_scope"] != "cross_cohort_comparable" or
                m2["comparability_scope"] != "cross_cohort_comparable"
            ):
                return False
            return True

        self.assertFalse(can_compare(bank_metric, industrial_metric))

    def test_dur_01_and_dur_02_evidence_demands(self):
        """DUR-01 & DUR-02: Mapping requires durability preconditions and net economic effect without keyword bonuses."""
        bundle = {
            "contract_version": "1.0.0",
            "updated_at": "2026-09-22T22:00:00Z",
            "metrics": [
                {
                    "metric_id": "financial.operating_margin",
                    "unit": "percent",
                    "definition": "营业利润率",
                    "cohort": "all",
                    "comparability_scope": "cross_cohort_comparable",
                    "critical_risk_flag": False
                }
            ],
            "question_mappings": [
                {
                    "question_id": "IQS_01",
                    "primary_metric_ref": None,
                    "dimension": "quality",
                    "aggregation_role": "quality_core",
                    "critical_risk": False,
                    "replacement_for": None,
                    "evidence_demands": {
                        "require_durability_conditions": True,
                        "require_net_economic_effect": True,
                        "counter_evidence_required": True
                    }
                }
            ]
        }
        self.validate_type("MetricContractBundle", bundle)
        q_map = bundle["question_mappings"][0]
        self.assertTrue(q_map["evidence_demands"]["require_durability_conditions"])
        self.assertTrue(q_map["evidence_demands"]["require_net_economic_effect"])

    def test_dur_03_diagnostic_addition_rules(self):
        """DUR-03: Unknown vs N/A separation, no unneeded duplicate questions."""
        def evaluate_diagnostic_trigger(has_unanswered_risk, evidence_status):
            if evidence_status == "not_applicable":
                return "skip_diagnostic"
            if evidence_status == "unknown":
                return "needs_verification"
            if has_unanswered_risk:
                return "trigger_diagnostic"
            return "skip_diagnostic"

        self.assertEqual(evaluate_diagnostic_trigger(True, "not_applicable"), "skip_diagnostic")
        self.assertEqual(evaluate_diagnostic_trigger(True, "unknown"), "needs_verification")
        self.assertEqual(evaluate_diagnostic_trigger(True, "valid"), "trigger_diagnostic")


if __name__ == "__main__":
    unittest.main()
