"""Automated tests for Scoring, Availability Levels and Three-Valued Rules Contract (Task C03).
Covers scenarios: SC-02, SC-03, SC-04, SC-05, SC-06, SC-07, SC-16, SC-09, RULE-01, RULE-02, RULE-03.
"""
import json
from pathlib import Path
import sys
import unittest
import jsonschema
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import contract_validation as cv
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
                "check_level": "execution_verified",
                "check_level_receipt_id": "RCP_EXECUTION_FIXTURE"
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
                    "check_level": "execution_verified",
                    "check_level_receipt_id": "RCP_EXECUTION_FIXTURE"
                }
                self.validate_score_type("ParsedAnswer", answer)

    def test_sc_04_mismatched_outer_inner_scores_and_id_mismatch(self):
        """SC-04: Mismatched outer vs inner scores or wrong question ID must raise error."""
        with self.assertRaises(ValueError) as cm1:
            cv.reconcile_answer_score(expected_question_id="IQS_05", actual_question_id="IQS_06", outer_score=8, inner_score=8)
        self.assertIn("question_id mismatch", str(cm1.exception))

        with self.assertRaises(ValueError) as cm2:
            cv.reconcile_answer_score(expected_question_id="IQS_05", actual_question_id="IQS_05", outer_score=5, inner_score=8)
        self.assertIn("score mismatch", str(cm2.exception))

    def test_sc_16_legacy_score_and_nullable_statuses_stay_distinct(self):
        """SC-16: Legacy transport values cannot replace formal score or collapse unknown/N/A/error states."""
        for status in ("unknown", "not_applicable", "insufficient_evidence", "error"):
            with self.subTest(status=status):
                answer = {
                    "question_id": "IQS_01",
                    "status": status,
                    "score": None,
                    "legacy_transport_score": 5,
                    "description": "结构化测试样例",
                    "check_level": "unverified_model_output",
                    "check_level_receipt_id": None,
                }
                cv.validate_parsed_answer(answer)
                self.assertEqual(answer["status"], status)
                self.assertIsNone(answer["score"])
                self.assertEqual(answer["legacy_transport_score"], 5)

        explicit_low_score = {
            "question_id": "IQS_01",
            "status": "scored",
            "score": 3,
            "legacy_transport_score": 5,
            "description": "明确低分，与未知状态不同",
            "check_level": "unverified_model_output",
            "check_level_receipt_id": None,
        }
        cv.validate_parsed_answer(explicit_low_score)
        self.assertEqual(explicit_low_score["status"], "scored")
        self.assertEqual(explicit_low_score["score"], 3)

    def test_sc_05_and_sc_06_model_cannot_self_grant_check_level(self):
        """SC-05 & SC-06: Model raw response claiming accepted_ids cannot self-upgrade check_level."""
        raw_model_claim = {
            "accepted_ids": ["IQS_01", "IQS_02"],
            "search_verified": True,
            "check_level": "formal_research_accepted"
        }
        parsed = {"question_id":"IQS_01", "status":"scored", "score":8,
                  "description":"claim", "check_level":raw_model_claim["check_level"],
                  "check_level_receipt_id":"RCP_FORGED"}
        with self.assertRaises(ValueError):
            cv.validate_parsed_answer(parsed)

    def test_sc_07_coverage_rate_with_audited_na(self):
        """SC-07: Audited N/A excluded from denominator (7/9), unchecked N/A remains in denominator (7/10)."""
        self.assertAlmostEqual(cv.coverage_rate(selected_count=10, valid_scored_count=7, na_count=1, na_is_audited=True), 7 / 9)
        self.assertAlmostEqual(cv.coverage_rate(selected_count=10, valid_scored_count=7, na_count=1, na_is_audited=False), 7 / 10)

    def test_rule_01_field_threshold_conditions(self):
        """RULE-01: Score 8 evaluated against >8 yields fail, >=8 yields pass."""
        cond_gt = {"field": "score", "op": ">", "value": 8}
        cond_gte = {"field": "score", "op": ">=", "value": 8}
        self.validate_rule_type("FieldThresholdCondition", cond_gt)
        self.validate_rule_type("FieldThresholdCondition", cond_gte)

        self.assertEqual(cv.evaluate_rule({"condition":cond_gt}, {"score":8}), "fail")
        self.assertEqual(cv.evaluate_rule({"condition":cond_gte}, {"score":8}), "pass")

    def test_rule_02_three_valued_logic_and_critical_gate(self):
        """RULE-02: Three-valued logic truth table for ALL and ANY, plus critical risk gate override."""
        states = ["pass", "fail", "unknown"]
        state_value = {"pass": 1, "fail": 0, "unknown": None}
        leaf_a = {"condition":{"field":"a","op":">=","value":1}}
        leaf_b = {"condition":{"field":"b","op":">=","value":1}}
        for s1 in states:
            for s2 in states:
                fields = {key:value for key,value in {"a":state_value[s1],"b":state_value[s2]}.items() if value is not None}
                res_all = cv.evaluate_rule({"all":[leaf_a, leaf_b]}, fields)
                res_any = cv.evaluate_rule({"any":[leaf_a, leaf_b]}, fields)
                if "fail" in (s1, s2):
                    self.assertEqual(res_all, "fail")
                if "pass" in (s1, s2):
                    self.assertEqual(res_any, "pass")

        root = {"any":[{"condition":{"field":"quality","op":">=","value":8}}]}
        gate = {"field":"critical","op":">=","value":5,"critical_risk_gate":True}
        self.assertEqual(cv.evaluate_policy(root, {"quality":10,"critical":3}, [gate]), "fail")
        self.assertEqual(cv.evaluate_policy(root, {"quality":10,"critical":8}, [gate]), "pass")

    def test_rule_03_missing_fields_and_invalid_empty_rules(self):
        """RULE-03: Missing fields return unknown; empty all/any raises ValueError."""
        res = cv.evaluate_rule({"condition": {"field": "missing_metric", "op": ">=", "value": 8}}, {})
        self.assertEqual(res, "unknown")

        with self.assertRaises(ValidationError):
            cv.evaluate_rule({"all": []}, {"score": 8})


if __name__ == "__main__":
    unittest.main()
