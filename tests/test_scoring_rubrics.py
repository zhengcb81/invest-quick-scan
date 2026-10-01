"""V02/EVO-05--07: release, raw-answer preservation and comparison oracles."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc  # noqa: E402
import module_registry  # noqa: E402
import question_sets as qs  # noqa: E402
import scoring_rubrics as sr  # noqa: E402

AT = "2026-10-01T12:00:00Z"


def rubric_body():
    _, modules, _, _ = module_registry.load_current()
    return {
        "schema_version": "1.0.0", "version": "1.0.0",
        "method_id": "core-constructs-v1-operating", "owner": "iqs",
        "cohort": "operating", "valid_from_utc": "2026-09-30T00:00:00Z",
        "valid_until_utc": None, "calibration_sample_refs": [],
        "minimum_check_level": "execution_verified",
        "dimension_min_coverage": 0.7, "quality_min_coverage": 0.8,
        "quality_weights": dict(qs.QUALITY_WEIGHTS), "supersedes": None,
        "core_basket": [{"construct_id": q["construct_id"], "question_id": q["id"],
                         "question_definition_sha256": mc.digest(q),
                         "dimension": q["dimension"], "scope": q["scope"],
                         "rubric_version": q["rubric_version"]}
                        for q in modules["common"]["questions"]],
        "critical_extensions": [],
    }


def snapshot(body=None, score=8):
    body = body or rubric_body()
    records = []
    for q in body["core_basket"]:
        records.append({
            "id": q["question_id"], "construct_id": q["construct_id"],
            "dimension": q["dimension"],
            "aggregation_role": ("growth_core" if q["dimension"] == "growth" else
                                 "valuation_core" if q["dimension"] == "valuation" else
                                 "quality_core"),
            "question_definition_sha256": q["question_definition_sha256"],
            "question_semantic_sha256": mc.digest({"definition": q, "contexts": []}),
            "scope": q["scope"],
            "scope_id": "E1" if q["scope"] == "entity" else "SEC1",
            "scope_basis": "consolidated" if q["scope"] == "entity" else "ordinary-equity",
            "period_start": "2025-01-01", "period_end": "2025-12-31", "period_basis": "FY",
            "provider": "fixture", "model": "fixture-model", "model_config_sha256": "a" * 64,
            "status": "scored", "score": score, "confidence": "high",
            "check_level": "execution_verified", "check_level_receipt_id": "RCP_" + q["question_id"],
            "is_audited_na": False, "critical": q["construct_id"] in {"IQS_12", "IQS_13", "IQS_16"},
            "freshness": "fresh", "observation_id": "OBS_" + q["question_id"],
            "observation_sha256": mc.digest({"original": q["question_id"], "score": score}),
        })
    return {"schema_version": "1.0.0", "entity_id": "E1", "cohort": "operating",
            "information_as_of": "2026-09-30", "records": records}


class ScoringRubricTests(unittest.TestCase):
    def setUp(self):
        self.body = rubric_body()
        self.raw = snapshot(self.body)

    def aggregate(self, raw=None, body=None, at=AT):
        raw = self.raw if raw is None else raw
        return sr.aggregate(sr.seal_rubric(body or self.body), raw,
                            expected_snapshot_sha256=mc.digest(raw), at=at)

    def test_evo05_weight_only_release_keeps_originals_and_parallel_scores(self):
        raw = snapshot(self.body, score=5)
        for row in raw["records"]:
            if row["dimension"] == "moat":
                row["score"] = 8
        before = copy.deepcopy(raw)
        old = sr.seal_rubric(self.body)
        body = copy.deepcopy(self.body)
        body.update(method_id="moat-weighted-v1", supersedes=old["rubric_release_id"])
        body["quality_weights"] = dict(zip(qs.QUALITY_WEIGHTS, [10, 50, 10, 15, 10, 5]))
        new = sr.seal_rubric(body)
        first = sr.aggregate(old, raw, expected_snapshot_sha256=mc.digest(raw), at=AT)
        second = sr.aggregate(new, raw, expected_snapshot_sha256=mc.digest(raw), at=AT)
        self.assertEqual((first["quality_score"], second["quality_score"]), (5.6, 6.5))
        self.assertEqual(raw, before)
        self.assertEqual(first["source_observations"], second["source_observations"])
        self.assertEqual(first["source_snapshot_sha256"], second["source_snapshot_sha256"])
        self.assertEqual(first["denominator"]["expected_core"], 24)
        self.assertEqual(first["denominator"]["quality_applicable"], 18)
        self.assertNotEqual(first["derived_id"], second["derived_id"])
        self.assertEqual(first["new_llm_calls"], 0)
        self.assertEqual(second["new_llm_calls"], 0)

    def test_evo07_unknown_eight_and_diagnostic_ten_never_raise_core_five(self):
        raw = snapshot(self.body, score=5)
        row = copy.deepcopy(raw["records"][0])
        row.update(id="DIAG_01", construct_id=None, aggregation_role="diagnostic_only",
                   score=10, critical=False, observation_id="OBS_DIAG_01")
        raw["records"].append(row)
        self.assertEqual(self.aggregate(raw)["quality_score"], 5)
        raw["records"][11].update(status="insufficient_evidence", score=8)
        derived = self.aggregate(raw)
        self.assertIsNone(derived["quality_score"])
        self.assertIn({"id": "IQS_12", "kind": "unresolved"}, derived["critical_issues"])
        self.assertIsNone(derived["comparison_inputs"][11]["effective_score"])

    def test_evo06_axes_and_missing_critical_cannot_create_false_zero_trend(self):
        rubric = sr.seal_rubric(self.body)
        for key, value in [("question_definition_sha256", "b" * 64),
                           ("question_semantic_sha256", "c" * 64),
                           ("scope_basis", "different-perimeter"),
                           ("period_end", "2026-06-30"), ("model", "another-model")]:
            with self.subTest(key=key):
                right = copy.deepcopy(self.raw)
                right["records"][0][key] = value
                if key == "scope_basis":
                    for row in right["records"]:
                        if row["scope"] == "entity":
                            row[key] = value
                result = sr.compare(rubric, self.raw, rubric, right,
                                    left_sha256=mc.digest(self.raw), right_sha256=mc.digest(right), at=AT)
                self.assertEqual(result["status"], "incomparable")
                self.assertIsNone(result["quality_delta"])
                self.assertTrue(result["reasons"])
        right = copy.deepcopy(self.raw)
        del right["records"][11]
        result = sr.compare(rubric, self.raw, rubric, right,
                            left_sha256=mc.digest(self.raw), right_sha256=mc.digest(right), at=AT)
        self.assertEqual(result["status"], "incomparable")
        self.assertIsNone(result["quality_delta"])

    def test_same_aligned_method_compares_and_new_method_requires_own_rule_binding(self):
        rubric = sr.seal_rubric(self.body)
        result = sr.compare(rubric, self.raw, rubric, self.raw,
                            left_sha256=mc.digest(self.raw), right_sha256=mc.digest(self.raw), at=AT)
        self.assertEqual((result["status"], result["quality_delta"]), ("comparable", 0))
        derived = self.aggregate()
        self.assertEqual(sr.rule_input(derived, expected_method_id=rubric["method_id"],
                                       expected_release_id=rubric["rubric_release_id"])["score"], 8)
        wrong = sr.rule_input(derived, expected_method_id="new-method",
                              expected_release_id=rubric["rubric_release_id"])
        self.assertIsNone(wrong["score"])
        self.assertEqual(wrong["status"], "unavailable")

    def test_release_integrity_invalid_weight_denominator_and_immutable_method(self):
        rubric = sr.seal_rubric(self.body)
        changed = copy.deepcopy(self.body)
        changed.update(version="1.1.0", supersedes=rubric["rubric_release_id"])
        changed["quality_weights"]["business"] = 25
        changed["quality_weights"]["moat"] = 15
        with self.assertRaises(ValueError):
            sr.validate_upgrade(rubric, sr.seal_rubric(changed))
        for field, value in [("quality_min_coverage", 0.7), ("dimension_min_coverage", 0.6),
                             ("core_basket", self.body["core_basket"][:-1])]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.body)
                bad[field] = value
                with self.assertRaises(ValueError):
                    sr.seal_rubric(bad)
        tampered = copy.deepcopy(rubric)
        tampered["method_id"] = "forged"
        with self.assertRaises(ValueError):
            sr.aggregate(tampered, self.raw, expected_snapshot_sha256=mc.digest(self.raw), at=AT)

    def test_coverage_audited_na_grade_and_critical_are_not_averaged_away(self):
        for qid, changes in [("IQS_12", {"status": "not_applicable", "score": None, "is_audited_na": True}),
                             ("IQS_13", {"check_level": "unverified_model_output", "check_level_receipt_id": None}),
                             ("IQS_16", {"confidence": "low"}),
                             ("IQS_16", {"score": 3}), ("IQS_12", {"freshness": "stale"})]:
            with self.subTest(qid=qid, changes=changes):
                raw = copy.deepcopy(self.raw)
                next(r for r in raw["records"] if r["id"] == qid).update(changes)
                self.assertIsNone(self.aggregate(raw)["quality_score"])
        raw = copy.deepcopy(self.raw)
        raw["records"][0].update(status="not_applicable", score=None)
        self.assertEqual(self.aggregate(raw)["denominator"]["quality_applicable"], 18)
        raw["records"][0]["is_audited_na"] = True
        self.assertEqual(self.aggregate(raw)["denominator"]["quality_applicable"], 18)
        raw["records"][0]["check_level"] = "screening_audited"
        self.assertEqual(self.aggregate(raw)["denominator"]["quality_applicable"], 17)
        self.assertEqual(self.aggregate(raw)["quality_score"], 8)

    def test_duplicate_core_or_source_and_snapshot_hash_conflicts_reject(self):
        raw = copy.deepcopy(self.raw)
        raw["records"].append(copy.deepcopy(raw["records"][0]))
        with self.assertRaises(ValueError):
            self.aggregate(raw)
        with self.assertRaises(ValueError):
            sr.aggregate(sr.seal_rubric(self.body), self.raw,
                         expected_snapshot_sha256="0" * 64, at=AT)
        bad = copy.deepcopy(self.raw)
        bad["records"][0]["score"] = True
        with self.assertRaises(ValueError):
            self.aggregate(bad)
        for score in (8.0, 1.0):
            with self.subTest(score=score):
                bad["records"][0]["score"] = score
                with self.assertRaises(ValueError):
                    self.aggregate(bad)
        weights = copy.deepcopy(self.body)
        weights["quality_weights"]["business"] = 20.0
        with self.assertRaises(ValueError):
            sr.seal_rubric(weights)

    def test_release_effective_window_is_half_open_and_historical_reader_is_independent(self):
        body = copy.deepcopy(self.body)
        body["valid_until_utc"] = AT
        self.assertEqual(self.aggregate(body=body, at="2026-10-01T11:59:59Z")["quality_score"], 8)
        for at in [AT, "2026-10-01T12:00:01Z", "2026-09-29T12:00:00Z", "2026-10-01T11:00:00"]:
            with self.subTest(at=at):
                with self.assertRaises(ValueError):
                    self.aggregate(body=body, at=at)
        rubric = sr.seal_rubric(body)
        with tempfile.TemporaryDirectory(prefix="iqs-v02-reader-") as temp:
            path = Path(temp) / "historic.json"
            data = mc.canonical_bytes(rubric)
            path.write_bytes(data)
            self.assertEqual(sr.load_rubric(path, expected_sha256=hashlib.sha256(data).hexdigest(),
                                            expected_release_id=rubric["rubric_release_id"]), rubric)
            with self.assertRaises(ValueError):
                sr.load_rubric(path, expected_sha256="0" * 64,
                               expected_release_id=rubric["rubric_release_id"])
        self.assertFalse(Path(temp).exists())

    def test_type_replacement_is_bound_to_one_construct_and_cannot_double_count(self):
        body = copy.deepcopy(self.body)
        body["cohort"] = "bank"
        body["method_id"] = "core-bank-v1"
        body["core_basket"][10]["question_id"] = "BANK_11"
        body["core_basket"][10]["question_definition_sha256"] = "d" * 64
        raw = snapshot(body)
        raw["cohort"] = "bank"
        self.assertEqual(self.aggregate(raw, body)["quality_score"], 8)
        wrong = copy.deepcopy(raw)
        wrong["records"][10]["id"] = "IQS_11"
        self.assertIn({"id": "BANK_11", "code": "missing_question"},
                      self.aggregate(wrong, body)["unavailable_reasons"])

    def test_default_method_matches_actual_existing_core_summary(self):
        raw = copy.deepcopy(self.raw)
        for index, row in enumerate(raw["records"]):
            row["score"] = 4 + index % 7
        old_rows = [{"id": r["id"], "construct_id": r["construct_id"],
                     "comparison_role": "core", "dimension": r["dimension"],
                     "score": r["score"], "status": r["status"], "critical": r["critical"]}
                    for r in raw["records"]]
        old = qs.summarize(old_rows, policy="core-constructs-v1")
        new = self.aggregate(raw)
        self.assertEqual(new["quality_score"], old["quality_score"])
        for dimension in qs.DIMENSIONS:
            self.assertEqual(new["dimensions"][dimension]["score"], old["dimensions"][dimension]["score"])

    def test_required_extra_risk_and_fixed_critical_flags_cannot_be_bypassed(self):
        body = copy.deepcopy(self.body)
        question = copy.deepcopy(body["core_basket"][0])
        question.update(question_id="RISK_01", construct_id=None)
        body["critical_extensions"] = [question]
        self.assertIsNone(self.aggregate(body=body)["quality_score"])
        raw = copy.deepcopy(self.raw)
        raw["records"][11].update(critical=False, score=3)
        self.assertIsNone(self.aggregate(raw)["quality_score"])
        for changes in ({"critical": True, "score": 3},
                        {"critical": True, "status": "unknown", "score": 8}):
            with self.subTest(changes=changes):
                core_risk = copy.deepcopy(self.raw)
                core_risk["records"][0].update(changes)
                self.assertIsNone(self.aggregate(core_risk)["quality_score"])
        raw = copy.deepcopy(self.raw)
        row = copy.deepcopy(raw["records"][0])
        row.update(id="RISK_01", construct_id=None, critical=True, score=3,
                   observation_id="OBS_RISK_01")
        raw["records"].append(row)
        self.assertIsNone(self.aggregate(raw)["quality_score"])
        row.update(score=8)
        self.assertEqual(self.aggregate(raw, body)["quality_score"], 8)
        for field in ("provider", "model", "model_config_sha256", "period_start", "period_end", "period_basis"):
            with self.subTest(field=field):
                broken = copy.deepcopy(raw)
                broken["records"][-1][field] = None
                self.assertIsNone(self.aggregate(broken)["quality_score"])

    def test_new_method_scores_are_parallel_but_not_automatically_comparable(self):
        old = sr.seal_rubric(self.body)
        body = copy.deepcopy(self.body)
        body.update(method_id="alternative-v1", supersedes=old["rubric_release_id"])
        body["quality_weights"]["business"] = 25
        body["quality_weights"]["moat"] = 15
        new = sr.seal_rubric(body)
        sr.validate_upgrade(old, new)
        compared = sr.compare(old, self.raw, new, self.raw, left_sha256=mc.digest(self.raw),
                              right_sha256=mc.digest(self.raw), at=AT)
        self.assertEqual(compared["status"], "incomparable")
        self.assertIsNone(compared["quality_delta"])
        denied = sr.rule_input(compared["right"], expected_method_id=old["method_id"],
                               expected_release_id=old["rubric_release_id"])
        self.assertIsNone(denied["score"])

    def test_cli_pinned_bytes_and_duplicate_key_fail_closed_in_clean_temp_workspace(self):
        rubric = sr.seal_rubric(self.body)
        with tempfile.TemporaryDirectory(prefix="iqs-v02-cli-") as temp:
            root = Path(temp)
            rubric_path, snapshot_path = root / "rubric.json", root / "snapshot.json"
            rubric_data, snapshot_data = mc.canonical_bytes(rubric), mc.canonical_bytes(self.raw)
            rubric_path.write_bytes(rubric_data)
            snapshot_path.write_bytes(snapshot_data)
            environment = {k: v for k, v in os.environ.items()
                           if not any(token in k.upper() for token in ("API_KEY", "LIVE_E2E"))}
            command = [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/scoring_rubrics.py"),
                       "aggregate", "--rubric", str(rubric_path), "--rubric-sha256",
                       hashlib.sha256(rubric_data).hexdigest(), "--release-id", rubric["rubric_release_id"],
                       "--snapshot", str(snapshot_path), "--snapshot-sha256",
                       hashlib.sha256(snapshot_data).hexdigest(), "--at", AT]
            passed = subprocess.run(command, cwd=temp, env=environment, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertEqual(json.loads(passed.stdout)["quality_score"], 8)
            duplicate = snapshot_data[:-1] + b',"entity_id":"E1"}'
            snapshot_path.write_bytes(duplicate)
            command[command.index("--snapshot-sha256") + 1] = hashlib.sha256(duplicate).hexdigest()
            failed = subprocess.run(command, cwd=temp, env=environment, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(failed.returncode, 2)
            self.assertEqual(json.loads(failed.stdout)["error_code"], "scoring_rubric_input_invalid")
            self.assertEqual({p.name for p in root.iterdir()}, {"rubric.json", "snapshot.json"})
            self.assertEqual(rubric_path.read_bytes(), rubric_data)
        self.assertFalse(Path(temp).exists())

    def test_committed_candidate_matches_frozen_core_and_exact_pinned_loader(self):
        release_id = "rubrel_1ae5bfbf4c63bb197bde53d9058ca50ff631aae1a9525e0ec8578f4495379d02"
        path = ROOT / "questions/scoring-rubrics" / (release_id + ".json")
        loaded = sr.load_rubric(path, expected_release_id=release_id,
                               expected_sha256="88af96451741a8fcdd1b69d07d4de21c665c549c2d077aa6866f2d74fa9909ae")
        self.assertEqual(loaded, sr.seal_rubric(self.body))
        self.assertEqual(loaded["calibration_sample_refs"], [])

    def test_pinned_archive_bytes_survive_windows_git_checkout(self):
        folder = ROOT / "questions/scoring-rubrics"
        source = next(folder.glob("rubrel_*.json"))
        with tempfile.TemporaryDirectory(prefix="iqs-v02-git-") as temp:
            root = Path(temp)
            destination = root / source.name
            destination.write_bytes(source.read_bytes())
            (root / ".gitattributes").write_bytes((folder / ".gitattributes").read_bytes())
            environment = {k: v for k, v in os.environ.items()
                           if not any(token in k.upper() for token in ("API_KEY", "LIVE_E2E", "GIT_"))}
            for arguments in (["init", "-q"], ["config", "core.autocrlf", "true"],
                              ["add", "--", ".gitattributes", source.name]):
                result = subprocess.run(["git", *arguments], cwd=temp, env=environment,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
            destination.unlink()
            result = subprocess.run(["git", "checkout-index", "--all", "--force"], cwd=temp,
                                    env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(destination.read_bytes(), source.read_bytes())
        self.assertFalse(Path(temp).exists())


if __name__ == "__main__":
    unittest.main()
