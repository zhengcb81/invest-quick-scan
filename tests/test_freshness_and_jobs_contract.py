"""C04 contract tests. Exercise the repository's reference rules, not copied test lambdas."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft7Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import contract_validation as cv
import work_contract as wc

SCHEMA = json.loads((ROOT / "schemas/quick_scan/work.schema.json").read_text(encoding="utf-8"))


def validate_definition(name, value):
    wrapper = {"$schema": SCHEMA["$schema"], "definitions": SCHEMA["definitions"],
               "$ref": f"#/definitions/{name}"}
    Draft7Validator(wrapper, format_checker=FormatChecker()).validate(value)


def meta(**updates):
    value = {
        "information_as_of": "2026-09-20",
        "published_at": "2026-09-21T10:00:00Z",
        "valid_until": "2026-10-01T00:00:00Z",
        "answer_started_at": "2026-09-22T10:00:00Z",
        "answered_at": "2026-09-22T10:01:00Z",
        "imported_at": "2026-09-22T10:02:00Z",
        "checked_at": None,
        "event_invalidated_at": None,
        "response_status": "scored",
        "check_level": "screening_audited",
    }
    value.update(updates)
    return value


def expected(**updates):
    value = {"question_fingerprint": "qhash", "routing_fingerprint": "rhash", "generation":1,
             "scope": "entity", "scope_id": "ENT_A", "minimum_check_level": "execution_verified"}
    value.update(updates)
    return value


def observation(**updates):
    value = {**meta(), **expected(), "response_status": "scored"}
    value.update(updates)
    return value


class FreshnessAndJobsContractTests(unittest.TestCase):
    def test_schema_itself_is_valid_and_fresh_observation_has_separate_times(self):
        Draft7Validator.check_schema(SCHEMA)
        validate_definition("ObservationTimeMeta", meta())
        self.assertEqual(wc.freshness_status(meta(), "2026-09-22T12:00:00Z"), "fresh")
        wc.validate_temporal_order(meta())
        with self.assertRaises(ValueError):
            wc.validate_temporal_order(meta(answered_at="2026-09-22T09:59:00Z"))
        with self.assertRaises(ValueError):
            wc.validate_temporal_order(meta(imported_at="2026-09-22T10:00:00Z"))

    def test_time_01_reuses_compatible_fresh_observation_without_creating_work(self):
        delivered = {"status":"delivered", "generation":1}
        self.assertEqual(wc.reuse_decision(observation(), expected(), "2026-09-22T12:00:00Z", delivered), "reuse")

    def test_time_02_expiry_is_strict_at_the_boundary_and_all_datetime_is_utc(self):
        value = meta(valid_until="2026-09-22T00:00:00Z")
        self.assertEqual(wc.freshness_status(value, "2026-09-21T23:59:59Z"), "fresh")
        self.assertEqual(wc.freshness_status(value, "2026-09-22T00:00:00Z"), "stale")
        self.assertEqual(wc.freshness_status(value, "2026-09-22T00:00:01Z"), "stale")
        with self.assertRaises(ValueError):
            wc.freshness_status(meta(information_as_of="2026-09-22T12:00:01Z"), "2026-09-22T12:00:00Z")
        for invalid in ("2026-09-22T00:00:00", "2026-09-22T01:00:00+01:00", "not-a-date"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                wc.parse_utc(invalid)

    def test_time_03_reimport_never_renews_expired_observation(self):
        value = observation(valid_until="2026-06-01T00:00:00Z", information_as_of="2026-03-01")
        original = deepcopy(value)
        original_hash = __import__("hashlib").sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        # A retry decision cannot mutate or freshen the old immutable observation.
        self.assertEqual(wc.reuse_decision(value, expected(), "2026-09-22T22:00:00Z", {"status":"delivered","generation":1}), "dispatch")
        self.assertEqual(value, original)
        self.assertEqual(__import__("hashlib").sha256(json.dumps(value, sort_keys=True).encode()).hexdigest(), original_hash)
        self.assertEqual(wc.freshness_status(value, "2026-09-22T22:00:00Z"), "stale")

    def test_time_04_unknown_is_deferred_during_cooldown_then_dispatched(self):
        value = observation(response_status="insufficient_evidence", information_as_of=None, valid_until=None)
        work = {"status":"delivered", "generation":1, "next_retry_at":"2026-09-25T00:00:00Z"}
        self.assertEqual(wc.reuse_decision(value, expected(), "2026-09-24T23:59:59Z", work), "deferred_unknown")
        self.assertEqual(wc.reuse_decision(value, expected(), "2026-09-25T00:00:00Z", work), "dispatch_new_generation")
        delivered_unknown = {"work_item_id":"WORK_1","entity_id":"ENT_A","question_id":"IQS_01","generation":1,
            "scope":"entity","scope_id":"ENT_A","question_fingerprint":"a"*64,"routing_fingerprint":"b"*64,
            "request_cache_key":None,"response_status":"insufficient_evidence","status":"delivered",
            "observation_ref":"OBS_A","observation_hash":"c"*64,"next_retry_at":"2026-09-25T00:00:00Z",
            "run_ids":["RUN_1"],"scan_ids":["SCAN_1"],"attempts":[],
            "created_at":"2026-09-22T00:00:00Z","updated_at":"2026-09-22T00:01:00Z"}
        validate_definition("WorkItem", delivered_unknown)
        self.assertEqual(wc.freshness_status(value, "2026-09-24T00:00:00Z"), "missing_date")

    def test_time_05_screening_threshold_is_not_part_of_logical_work_identity(self):
        before = wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        after = wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        self.assertEqual(before, after)
        # The work contract has no score threshold input; screening is a local query.

    def test_time_06_semantic_or_route_change_invalidates_only_that_observation(self):
        prior = observation()
        wanted = expected(question_fingerprint="new-question-hash")
        self.assertFalse(wc.observation_compatible(prior, wanted))
        self.assertEqual(wc.reuse_decision(prior, wanted, "2026-09-22T12:00:00Z"), "dispatch")
        self.assertTrue(wc.observation_compatible(prior, expected()))
        self.assertTrue(wc.observation_compatible(prior, expected(generation=2)))
        self.assertEqual(wc.reuse_decision(prior, expected(generation=2), "2026-09-22T12:00:00Z",
                                           {"status":"delivered","generation":1}), "dispatch")

    def test_time_07_historical_cutoff_requires_source_published_by_cutoff(self):
        self.assertTrue(wc.source_available_as_of("2026-06-30T23:59:59Z", "2026-06-30"))
        self.assertFalse(wc.source_available_as_of("2026-07-01T00:00:00Z", "2026-06-30"))
        self.assertFalse(wc.source_available_as_of(None, "2026-06-30"))

    def test_time_08_event_invalidation_overrides_ttl_and_missing_date_is_never_fresh(self):
        value = meta(event_invalidated_at="2026-09-20T00:00:00Z")
        self.assertEqual(wc.freshness_status(value, "2026-09-22T00:00:00Z"), "event_invalidated")
        self.assertEqual(wc.freshness_status(meta(information_as_of=None), "2026-09-22T00:00:00Z"), "missing_date")

    def test_time_09_field_freshness_preview_is_stable_and_never_dispatches(self):
        fields = {
            "revenue": meta(valid_until="2026-10-01T00:00:00Z"),
            "capital_structure": meta(valid_until="2026-09-21T00:00:00Z"),
            "backlog": meta(information_as_of=None, valid_until=None),
        }
        original = deepcopy(fields)

        first = wc.field_freshness_preview(fields, "2026-09-22T00:00:00Z")
        second = wc.field_freshness_preview(fields, "2026-09-22T00:00:00Z")

        self.assertEqual(first, second)
        self.assertEqual(first["fields"]["revenue"], {"freshness_status": "fresh", "refresh_needed": False})
        self.assertEqual(first["fields"]["capital_structure"], {"freshness_status": "stale", "refresh_needed": True})
        self.assertEqual(first["fields"]["backlog"], {"freshness_status": "missing_date", "refresh_needed": True})
        self.assertEqual(first["refresh_needed_fields"], ["backlog", "capital_structure"])
        self.assertFalse(first["dispatch_started"])
        self.assertEqual(fields, original)

    def test_job_01_key_deduplicates_across_runs_but_distinguishes_security_and_segment(self):
        entity = wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        same_entity_another_run = wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        security = wc.logical_work_key("ENT_A", "IQS_01", 1, "security", "SEC_HK")
        segment = wc.logical_work_key("ENT_A", "IQS_01", 1, "segment", "SEG_CLOUD")
        forced_refresh = wc.logical_work_key("ENT_A", "IQS_01", 2, "entity", "ENT_A")
        self.assertEqual(entity, same_entity_another_run)
        self.assertEqual(len({entity, security, segment, forced_refresh}), 4)
        with self.assertRaises(ValueError):
            wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "SEC_HK")

    def test_request_cache_key_is_separate_and_changes_for_exact_model_request(self):
        key = wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        args = dict(provider="provider-a", model="model-a", input_hash="input-hash",
                    question_fingerprint="qhash", routing_fingerprint="rhash",
                    information_cutoff="2026-09-22", search_enabled=True)
        first = wc.request_cache_key(key, **args)
        self.assertEqual(first, wc.request_cache_key(key, **args))
        changed_model = {**args, "model": "model-b"}
        self.assertNotEqual(first, wc.request_cache_key(key, **changed_model))
        self.assertEqual(key, wc.logical_work_key("ENT_A", "IQS_01", 1, "entity", "ENT_A"))

    def test_job_08_state_machine_rejects_illegal_jumps_and_checks_proofs(self):
        self.assertEqual({k:set(v) for k,v in SCHEMA["x-allowed-transitions"].items()}, wc._ALLOWED_TRANSITIONS)
        self.assertFalse(wc.transition_allowed("pending", "delivered"))
        self.assertFalse(wc.transition_allowed("leased", "pending"))
        self.assertTrue(wc.transition_allowed("leased", "pending", confirmed_not_sent=True))
        self.assertFalse(wc.transition_allowed("uncertain", "pending", confirmed_not_sent=True,
                                                uncertain_attempt_id="A1", reconciled_attempt_id="A1"))
        self.assertTrue(wc.transition_allowed("uncertain", "pending", confirmed_not_sent=True,
                                               attempt_ids=["A1"], uncertain_attempt_id="A1", reconciled_attempt_id="A1",
                                               reconciliation_outcome="not_sent"))
        # An uncertain network result needs reconciliation of the same attempt.
        self.assertFalse(wc.transition_allowed("uncertain", "result_ready", uncertain_attempt_id="A1",
                                                attempt_ids=["A1"], reconciled_attempt_id="A2", reconciliation_outcome="response_available"))
        self.assertTrue(wc.transition_allowed("uncertain", "result_ready", uncertain_attempt_id="A1",
                                               attempt_ids=["A1"], reconciled_attempt_id="A1", reconciliation_outcome="response_available"))
        # Unknown answer cooldown is a scheduling decision, not a mutable work status.
        self.assertNotIn("deferred_unknown", SCHEMA["definitions"]["WorkItemStatus"]["enum"])

    def test_job_08_uncertain_attempt_must_exist_once_and_transition_uses_work_item(self):
        base = {
            "work_item_id": "WORK_1", "entity_id": "ENT_A", "question_id": "IQS_01", "generation": 1,
            "scope": "entity", "scope_id": "ENT_A", "question_fingerprint": "a" * 64,
            "routing_fingerprint": "b" * 64, "request_cache_key": "REQ_" + "d" * 64,
            "status": "uncertain", "uncertain_attempt_id": "ATTEMPT_1",
            "run_ids": ["RUN_1"], "scan_ids": ["SCAN_1"],
            "attempts": [{"attempt_id": "ATTEMPT_1", "provider": "fixture",
                           "model_requested": "fixture-model", "started_at": "2026-09-22T00:00:00Z"}],
            "created_at": "2026-09-22T00:00:00Z", "updated_at": "2026-09-22T00:01:00Z"
        }
        cv.validate_work_item(base)
        self.assertTrue(wc.transition_work_item(
            base, "pending", confirmed_not_sent=True,
            reconciled_attempt_id="ATTEMPT_1", reconciliation_outcome="not_sent"))

        missing = {**base, "uncertain_attempt_id": "ATTEMPT_MISSING"}
        duplicate = {**base, "attempts": base["attempts"] * 2}
        for invalid in (missing, duplicate):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                cv.validate_work_item(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                wc.transition_work_item(
                    invalid, "pending", confirmed_not_sent=True,
                    reconciled_attempt_id="ATTEMPT_1", reconciliation_outcome="not_sent")
        self.assertFalse(wc.transition_allowed(
            "uncertain", "pending", uncertain_attempt_id="ATTEMPT_1",
            attempt_ids=["ATTEMPT_OTHER"], confirmed_not_sent=True,
            reconciled_attempt_id="ATTEMPT_1", reconciliation_outcome="not_sent"))

    def test_job_08_only_matching_accepted_ack_delivers_and_rejection_keeps_result_ready(self):
        args = dict(expected_item_id="WORK_A", expected_hash="a"*64, ack_item_id="WORK_A",
                    ack_hash="a"*64, ack_status="accepted")
        self.assertTrue(wc.transition_allowed("result_ready", "delivered", **args))
        self.assertFalse(wc.transition_allowed("result_ready", "delivered", **{**args, "ack_hash":"b"*64}))
        self.assertFalse(wc.transition_allowed("result_ready", "delivered", **{**args, "ack_item_id":"WORK_B"}))
        self.assertFalse(wc.transition_allowed("result_ready", "delivered", **{**args, "ack_status":"rejected_hash_mismatch"}))
        self.assertEqual(SCHEMA["x-allowed-transitions"]["result_ready"], ["delivered"])

    def test_work_schema_encodes_scope_and_status_requirements(self):
        base = {
            "work_item_id":"WORK_1", "entity_id":"ENT_A", "question_id":"IQS_01", "generation":1,
            "scope":"entity", "scope_id":"ENT_A", "question_fingerprint":"a"*64,
            "routing_fingerprint":"b"*64, "request_cache_key":None, "status":"pending",
            "run_ids":["RUN_1"], "scan_ids":["SCAN_1"], "attempts":[],
            "created_at":"2026-09-22T00:00:00Z", "updated_at":"2026-09-22T00:00:00Z"
        }
        validate_definition("WorkItem", base)
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", {**base,"status":"leased"})
        valid_leased = {**base,"status":"leased","lease_token":"LEASE_1","lease_expires_at":"2026-09-22T01:00:00Z"}
        validate_definition("WorkItem", valid_leased)
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", {**base,"status":"uncertain"})
        uncertain = {**base,"status":"uncertain","uncertain_attempt_id":"ATTEMPT_1",
                     "request_cache_key":"REQ_"+"d"*64,
                     "attempts":[{"attempt_id":"ATTEMPT_1","provider":"fixture",
                                  "model_requested":"fixture-model","started_at":"2026-09-22T00:00:00Z"}]}
        validate_definition("WorkItem", uncertain)
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", {**base,"scope":"listing"})
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", {**base,"scope":"security","scope_id":"ENT_A"})
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", {**base,"response_status":"insufficient_evidence"})
        invalid_time = {**base,"created_at":"2026-09-22T01:00:00+01:00"}
        with self.assertRaises(ValidationError):
            validate_definition("WorkItem", invalid_time)

    def test_ack_schema_rejects_bad_timestamp_and_unknown_fields(self):
        valid = {"work_item_id":"WORK_1","observation_hash":"c"*64,
                 "ack_status":"accepted","received_at":"2026-09-22T21:00:00Z"}
        validate_definition("ImportAck", valid)
        for invalid in ({**valid,"extra":"not-allowed"}, {**valid,"received_at":"2026-09-22T21:00:00"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                validate_definition("ImportAck", invalid)


if __name__ == "__main__":
    unittest.main()
