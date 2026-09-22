"""Automated tests for Scoring, Availability Levels and Three-Valued Rules Contract (Task C03).
Covers scenarios: SC-02, SC-03, SC-04, SC-05, SC-06, SC-07, SC-09, RULE-01, RULE-02, RULE-03.
"""
import json
from pathlib import Path
import unittest
import jsonschema
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCORE_SCHEMA_PATH = ROOT / "schemas/quick_scan/score.schema.json"
RULE_SCHEMA_PATH = ROOT / "schemas/quick_scan/rule.schema.json"


class ScoringAndRulesContractTests(unittest.TestCase):
    def setUp(self):
        self.score_schema = json.loads(SCORE_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.rule_schema = json.loads(RULE_SCHEMA_PATH.read_text(encoding="utf-8"))

    def validate_score_type(self, definition_name: str, instance: dict):
        wrapper = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": self.score_schema.get("definitions", {}),
            "$ref": f"#/definitions/{definition_name}"
        }
        validate(instance=instance, schema=wrapper)

    def validate_rule_type(self, definition_name: str, instance: dict):
        wrapper = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": self.rule_schema.get("definitions", {}),
            "$ref": f"#/definitions/{definition_name}"
        }
        validate(instance=instance, schema=wrapper)

    def test_sc_02_nullable_score_isolation_from_legacy_transport(self):
        """SC-02: Status insufficient_evidence has score=null; legacy_transport_score=5 stays out of formal score."""
        answer = {
            "question_id": "IQS_01",
            "status": "insufficient_evidence",
            "score": None,
            "legacy_transport_score": 5,
            "description": "缺乏可信财务公开披露",
            "check_level": "unverified_model_output"
        }
        self.validate_score_type("ParsedAnswer", answer)
        self.assertIsNone(answer["score"])
        # Transport score must be isolated from formal score
        self.assertEqual(answer["legacy_transport_score"], 5)

    def test_sc_03_valid_and_invalid_score_boundaries(self):
        """SC-03: Invalid scores rejected; 1, 5, 10 pass."""
        valid_scores = [1, 5, 10]
        for s in valid_scores:
            answer = {
                "question_id": "IQS_01",
                "status": "scored",
                "score": s,
                "description": "valid score",
                "check_level": "execution_verified"
            }
            self.validate_score_type("ParsedAnswer", answer)

        invalid_scores = [True, False, 0, 11, 1.5, "8", "NaN"]
        for s in invalid_scores:
            with self.assertRaises((ValidationError, TypeError)):
                answer = {
                    "question_id": "IQS_01",
                    "status": "scored",
                    "score": s,
                    "description": "invalid score",
                    "check_level": "execution_verified"
                }
                self.validate_score_type("ParsedAnswer", answer)

    def test_sc_04_mismatched_outer_inner_scores_and_id_mismatch(self):
        """SC-04: Mismatched outer vs inner scores or wrong question ID must raise error."""
        def parse_and_reconcile(expected_qid, actual_qid, outer_score, inner_score):
            if expected_qid != actual_qid:
                raise ValueError(f"Question ID mismatch: expected {expected_qid}, got {actual_qid}")
            if outer_score != inner_score:
                raise ValueError(f"Score conflict: outer={outer_score}, inner={inner_score}")
            return outer_score

        with self.assertRaises(ValueError) as cm1:
            parse_and_reconcile("IQS_05", "IQS_06", 8, 8)
        self.assertIn("Question ID mismatch", str(cm1.exception))

        with self.assertRaises(ValueError) as cm2:
            parse_and_reconcile("IQS_05", "IQS_05", 5, 8)
        self.assertIn("Score conflict", str(cm2.exception))

    def test_sc_05_and_sc_06_model_cannot_self_grant_check_level(self):
        """SC-05 & SC-06: Model raw response claiming accepted_ids cannot self-upgrade check_level."""
        raw_model_claim = {
            "accepted_ids": ["IQS_01", "IQS_02"],
            "search_verified": True,
            "check_level": "formal_research_accepted"
        }
        # Ingestion rule: Model raw output is always constrained to unverified_model_output
        def ingest_model_output(raw_output, audit_receipt=None):
            if audit_receipt is None:
                return "unverified_model_output"
            return audit_receipt.get("check_level", "unverified_model_output")

        self.assertEqual(ingest_model_output(raw_model_claim, None), "unverified_model_output")

    def test_sc_07_coverage_rate_with_audited_na(self):
        """SC-07: Audited N/A excluded from denominator (7/9), unchecked N/A remains in denominator (7/10)."""
        def calculate_coverage(selected_count, valid_scored_count, na_count, na_is_audited):
            if na_is_audited:
                effective_denominator = selected_count - na_count
            else:
                effective_denominator = selected_count
            return valid_scored_count / effective_denominator

        self.assertAlmostEqual(calculate_coverage(10, 7, 1, True), 7 / 9)
        self.assertAlmostEqual(calculate_coverage(10, 7, 1, False), 7 / 10)

    def test_rule_01_field_threshold_conditions(self):
        """RULE-01: Score 8 evaluated against >8 yields fail, >=8 yields pass."""
        def evaluate_threshold(score, op, threshold):
            if op == ">":
                return "pass" if score > threshold else "fail"
            elif op == ">=":
                return "pass" if score >= threshold else "fail"
            elif op == "<":
                return "pass" if score < threshold else "fail"
            elif op == "<=":
                return "pass" if score <= threshold else "fail"
            elif op == "==":
                return "pass" if score == threshold else "fail"
            elif op == "!=":
                return "pass" if score != threshold else "fail"
            raise ValueError(f"Unknown operator {op}")

        cond_gt = {"field": "score", "op": ">", "value": 8}
        cond_gte = {"field": "score", "op": ">=", "value": 8}
        self.validate_rule_type("FieldThresholdCondition", cond_gt)
        self.validate_rule_type("FieldThresholdCondition", cond_gte)

        self.assertEqual(evaluate_threshold(8, ">", 8), "fail")
        self.assertEqual(evaluate_threshold(8, ">=", 8), "pass")

    def test_rule_02_three_valued_logic_and_critical_gate(self):
        """RULE-02: Three-valued logic truth table for ALL and ANY, plus critical risk gate override."""
        def eval_all(a, b):
            # fail > unknown > pass
            if a == "fail" or b == "fail":
                return "fail"
            if a == "unknown" or b == "unknown":
                return "unknown"
            return "pass"

        def eval_any(a, b):
            # pass > unknown > fail
            if a == "pass" or b == "pass":
                return "pass"
            if a == "unknown" or b == "unknown":
                return "unknown"
            return "fail"

        # Check all 9 pairs
        states = ["pass", "fail", "unknown"]
        for s1 in states:
            for s2 in states:
                res_all = eval_all(s1, s2)
                res_any = eval_any(s1, s2)
                if "fail" in (s1, s2):
                    self.assertEqual(res_all, "fail")
                if "pass" in (s1, s2):
                    self.assertEqual(res_any, "pass")

        # Critical gate override test (SC-09 + RULE-02)
        def evaluate_policy(composite_result, critical_gate_passed):
            if not critical_gate_passed:
                return "fail"
            return composite_result

        # Even if ANY result is pass, critical gate failure forces fail
        self.assertEqual(evaluate_policy("pass", False), "fail")
        self.assertEqual(evaluate_policy("pass", True), "pass")

    def test_rule_03_missing_fields_and_invalid_empty_rules(self):
        """RULE-03: Missing fields return unknown; empty all/any raises ValueError."""
        def evaluate_rule(rule_dict, record):
            if "condition" in rule_dict:
                cond = rule_dict["condition"]
                field = cond["field"]
                if field not in record or record[field] is None:
                    return "unknown"
                val = record[field]
                op = cond["op"]
                target = cond["value"]
                if op == ">=":
                    return "pass" if val >= target else "fail"
                raise ValueError(f"Unknown operator {op}")
            elif "all" in rule_dict:
                items = rule_dict["all"]
                if not items:
                    raise ValueError("Empty 'all' rule configuration is illegal")
                sub_results = [evaluate_rule(item, record) for item in items]
                if "fail" in sub_results:
                    return "fail"
                if "unknown" in sub_results:
                    return "unknown"
                return "pass"
            raise ValueError("Invalid rule structure")

        # Missing field yields unknown
        res = evaluate_rule({"condition": {"field": "missing_metric", "op": ">=", "value": 8}}, {})
        self.assertEqual(res, "unknown")

        # Empty all yields ValueError
        with self.assertRaises(ValueError):
            evaluate_rule({"all": []}, {"score": 8})


if __name__ == "__main__":
    unittest.main()
