"""W03 identity-bound v2 envelopes; all fixtures are offline and disposable."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import contract_validation as cv
import standard_answers as sa
import work_contract as wc
from test_standard_answers import published_fixture, rehash


def owner_context(**updates):
    context = {
        "entity_id": "ENT_A", "identity_state": "provisional", "identity_revision": 1,
        "source_binding_version": 1, "scan_eligibility": "eligible_provisional",
        "active_source_binding_refs": ["BND_A"],
        "security_binding_refs": {"SEC_A": "BND_A"}, "segment_ids": [],
    }
    context.update(updates)
    return context


def work_item(**updates):
    item = {
        "schema_version": "2.0.0", "work_item_id": "WORK_A", "entity_id": "ENT_A",
        "question_id": "IQS_01", "generation": 1, "scope": "entity", "scope_id": "ENT_A",
        "question_fingerprint": "a" * 64, "routing_fingerprint": "b" * 64,
        "request_cache_key": None, "status": "pending", "run_ids": ["RUN_A"],
        "scan_ids": ["SCAN_A"], "attempts": [],
        "created_at": "2026-09-22T00:00:00Z", "updated_at": "2026-09-22T00:00:00Z",
        "identity_state": "provisional", "identity_revision": 1,
        "source_binding_version": 1, "source_binding_refs": ["BND_A"],
    }
    item.update(updates)
    return item


def v2_observation(work, **updates):
    record = sa.build_observations(*published_fixture(entity_id="ENT_A"))['observations'][0]
    record.update(
        schema_version="2.0.0", entity_id=work["entity_id"],
        question_id=work["question_id"], work_item_id=work["work_item_id"],
        work_generation=work["generation"], scope_id=work["scope_id"],
        question_fingerprint=work["question_fingerprint"],
        routing_fingerprint=work["routing_fingerprint"],
        identity_state_at_answer=work["identity_state"],
        identity_revision=work["identity_revision"],
        source_binding_version=work["source_binding_version"],
        source_binding_refs=work["source_binding_refs"],
    )
    record.update(updates)
    return rehash(record)


def completed_work_item(work, record, *, status="result_ready"):
    execution = record["execution"]
    item = {**work, "status": status, "request_cache_key": "REQ_" + "d" * 64,
            "observation_ref": record["observation_id"],
            "observation_hash": hashlib.sha256(json.dumps(
                record, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
            "response_status": record["answer"]["status"],
            "run_ids": [record["run_id"]], "scan_ids": [record["scan_id"]],
            "attempts": [{"attempt_id": execution["attempt_id"],
                          "provider": execution["provider"],
                          "model_requested": execution["model_requested"],
                          "model_resolved": execution["model_resolved"],
                          "started_at": execution["started_at"],
                          "answered_at": execution["answered_at"],
                          "request_id": execution["request_id"],
                          "prompt_hash": execution["prompt_sha256"]}]}
    return item


def current_proofs(work, record):
    persisted = completed_work_item(work, record, status="delivered")
    execution = record["execution"]
    return dict(
        trusted_dispatch_identity_context=owner_context(), persisted_work_item=persisted,
        persisted_attempt={**persisted["attempts"][0], "work_item_id": work["work_item_id"],
                           "status": "completed"},
        trusted_search_receipt={"receipt_id": execution["search_receipt_id"],
                                "work_item_id": work["work_item_id"],
                                "attempt_id": execution["attempt_id"],
                                "request_id": execution["request_id"],
                                "search_status": "executed"},
        trusted_ingest_receipt={"consumer": "stockwiki", "ack_status": "accepted",
                                "work_item_id": work["work_item_id"],
                                "observation_id": record["observation_id"],
                                "observation_hash": persisted["observation_hash"]},
        trusted_content_receipt={"issuer": "stockwiki", "status": "validated",
                                 "validation_scope": "frozen_package_and_answer_semantics",
                                 "schema_version": "2.0.0",
                                 "observation_id": record["observation_id"],
                                 "observation_hash": persisted["observation_hash"],
                                 "module_package_id": record["module_package_id"],
                                 "question_id": record["question_id"]},
        expected_observation_id=record["observation_id"],
    )


class IdentityBoundWorkObservationTests(unittest.TestCase):
    def test_v2_work_requires_complete_owner_bound_identity_and_legacy_entry_rejects_it(self):
        item, owner = work_item(), owner_context()
        self.assertIsNone(cv.validate_work_item_v2(item, trusted_identity_context=owner))
        legacy = {k: v for k, v in item.items() if k not in (
            "identity_revision", "source_binding_version", "identity_state", "source_binding_refs")}
        legacy["schema_version"] = "1.0.0"
        cv.validate_work_item(legacy)
        with self.assertRaisesRegex(ValueError, "v2 work"):
            cv.validate_work_item_v2(legacy, trusted_identity_context=owner)
        with self.assertRaises(ValidationError):
            cv.validate_work_item({**legacy, "identity_revision": 1})
        with self.assertRaisesRegex(ValueError, "trusted identity"):
            cv.validate_work_item_v2(item, trusted_identity_context=None)
        with self.assertRaisesRegex(ValueError, "legacy"):
            cv.validate_work_item(item)
        with self.assertRaisesRegex(ValueError, "legacy"):
            wc.transition_work_item(item, "leased")
        work_schema = json.loads((ROOT / "schemas/quick_scan/work.schema.json").read_text(encoding="utf-8"))
        Draft7Validator.check_schema(work_schema)
        work_definition = {"$schema": work_schema["$schema"],
                           "definitions": work_schema["definitions"],
                           "$ref": "#/definitions/WorkItem"}
        for removed in ("identity_revision", "source_binding_version", "source_binding_refs", "identity_state"):
            with self.subTest(removed=removed):
                bad = {k: v for k, v in item.items() if k != removed}
                with self.assertRaises(ValidationError):
                    Draft7Validator(work_definition,
                                    format_checker=FormatChecker()).validate(bad)

    def test_v2_work_rejects_stale_revision_binding_refs_and_ineligible_owner(self):
        item, owner = work_item(), owner_context()
        for changed in (
            {"identity_revision": 2}, {"source_binding_version": 2},
            {"identity_state": "verified"}, {"source_binding_refs": ["BND_OTHER"]},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                cv.validate_work_item_v2({**item, **changed}, trusted_identity_context=owner)
        for changed in (
            {"scan_eligibility": "candidate"}, {"active_source_binding_refs": ["BND_OTHER"]},
            {"source_binding_version": 2}, {"security_binding_refs": {}},
            {"active_source_binding_refs": ["BND_A", "BND_B"]},
        ):
            with self.subTest(owner=changed), self.assertRaises(ValueError):
                cv.validate_work_item_v2(item, trusted_identity_context=owner_context(**changed))
        security_item = work_item(scope="security", scope_id="SEC_A")
        cv.validate_work_item_v2(security_item, trusted_identity_context=owner)
        with self.assertRaises(ValueError):
            cv.validate_work_item_v2(work_item(scope="security", scope_id="SEC_OTHER"),
                                     trusted_identity_context=owner)

    def test_identity_and_binding_versions_partition_work_and_request_keys(self):
        args = ("ENT_A", "IQS_01", 1, "entity", "ENT_A")
        old = wc.logical_work_key(*args)
        first = wc.logical_work_key_v2(*args, identity_revision=1,
                                       source_binding_version=1, identity_state="provisional",
                                       source_binding_refs=["BND_A"])
        changed_identity = wc.logical_work_key_v2(*args, identity_revision=2,
                                                   source_binding_version=1, identity_state="verified",
                                                   source_binding_refs=["BND_A"])
        changed_binding = wc.logical_work_key_v2(*args, identity_revision=1,
                                                  source_binding_version=2, identity_state="provisional",
                                                  source_binding_refs=["BND_A"])
        self.assertEqual(len(old), 5)
        self.assertEqual(len({old, first, changed_identity, changed_binding}), 4)
        cache_args = dict(provider="fixture", model="fixture-model", input_hash="input",
                          question_fingerprint="qhash", routing_fingerprint="rhash",
                          information_cutoff="2026-09-22", search_enabled=True)
        self.assertNotEqual(wc.request_cache_key(first, **cache_args),
                            wc.request_cache_key(changed_binding, **cache_args))

    def test_v2_observation_has_separate_schema_and_exact_dispatch_lineage(self):
        item, owner = work_item(), owner_context()
        record = v2_observation(item)
        schema = json.loads((ROOT / "schemas/observation-v2.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertIsNone(cv.validate_observation_identity_v2(
            record, completed_work_item(item, record), trusted_dispatch_identity_context=owner,
            expected_observation_id=record["observation_id"]))
        with self.assertRaisesRegex(ValueError, "v2 identity"):
            sa.validate_observation(record)
        with self.assertRaisesRegex(ValueError, "v2 identity"):
            sa.validate_observation(record, require_published=True,
                                    expected_observation_id=record["observation_id"])
        with self.assertRaises(ValidationError):
            cv._validate_202012(cv.OBSERVATION_SCHEMA, record)
        for removed in ("work_item_id", "work_generation", "scope_id", "identity_revision",
                        "source_binding_version", "source_binding_refs", "identity_state_at_answer"):
            with self.subTest(removed=removed):
                bad = {k: v for k, v in record.items() if k != removed}
                with self.assertRaises(ValidationError):
                    cv._validate_202012(schema, bad)
        for changed in (
            {"work_item_id": "WORK_OTHER"}, {"work_generation": 2},
            {"source_binding_version": 2}, {"identity_revision": 2},
            {"source_binding_refs": ["BND_OTHER"]},
            {"identity_state_at_answer": "verified"},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                changed_record = v2_observation(item, **changed)
                cv.validate_observation_identity_v2(
                    changed_record, completed_work_item(item, changed_record),
                    trusted_dispatch_identity_context=owner,
                    expected_observation_id=changed_record["observation_id"])
        with self.assertRaisesRegex(ValueError, "independently stored ID"):
            cv.validate_observation_identity_v2(
                v2_observation(item, identity_revision=2),
                completed_work_item(item, record),
                trusted_dispatch_identity_context=owner,
                expected_observation_id=record["observation_id"])

    def test_late_old_identity_answer_is_historical_not_current_reuse(self):
        dispatched = work_item()
        record = v2_observation(dispatched)
        current = owner_context(identity_revision=2, source_binding_version=2)
        proofs = current_proofs(dispatched, record)
        self.assertFalse(cv.observation_identity_is_current(record, current, **proofs))
        self.assertTrue(cv.observation_identity_is_current(record, owner_context(), **proofs))
        self.assertIsNone(cv.validate_observation_identity_v2(
            record, completed_work_item(dispatched, record),
            trusted_dispatch_identity_context=owner_context(),
            expected_observation_id=record["observation_id"]))
        expected = dict(schema_version="2.0.0", entity_id="ENT_A", generation=1,
                        question_fingerprint="a" * 64, routing_fingerprint="b" * 64,
                        scope="entity", scope_id="ENT_A", minimum_check_level="execution_verified",
                        identity_state="provisional", identity_revision=2,
                        source_binding_version=2, source_binding_refs=["BND_A"])
        reuse_record = {**record, "check_level": "screening_audited",
                        "response_status": "scored", "information_as_of": "2026-09-20",
                        "valid_until": "2026-10-01T00:00:00Z"}
        self.assertEqual(wc.reuse_decision(reuse_record, expected, "2026-09-22T12:00:00Z",
                                           {"status": "delivered", "generation": 1,
                                            "schema_version": "2.0.0", "identity_revision": 1,
                                            "source_binding_version": 1}), "dispatch")
        for changed in (
            {"identity_revision": 2, "source_binding_version": 1},
            {"identity_revision": 1, "source_binding_version": 2},
            {"identity_revision": 1, "source_binding_version": 1,
             "identity_state": "verified"},
        ):
            with self.subTest(changed=changed):
                wanted = {**expected, **changed}
                self.assertFalse(wc.observation_compatible(reuse_record, wanted))
                self.assertEqual(wc.reuse_decision(reuse_record, wanted,
                                                   "2026-09-22T12:00:00Z"), "dispatch")
        self.assertFalse(wc.observation_compatible(
            {**reuse_record, "schema_version": "1.1.0"}, expected))
        self.assertFalse(cv.observation_identity_is_current(
            sa.build_observations(*published_fixture())['observations'][0], owner_context()))

    def test_verified_multi_listing_security_scope_uses_its_own_binding(self):
        current = owner_context(identity_state="verified", scan_eligibility="eligible_verified",
                                active_source_binding_refs=["BND_A", "BND_B"],
                                security_binding_refs={"SEC_A": "BND_A", "SEC_B": "BND_B"})
        security_work = work_item(identity_state="verified", scope="security", scope_id="SEC_B",
                                  source_binding_refs=["BND_B"])
        cv.validate_work_item_v2(security_work, trusted_identity_context=current)
        record = v2_observation(security_work, scope="security", security_id="SEC_B")
        cv.validate_observation_identity_v2(
            record, completed_work_item(security_work, record),
            trusted_dispatch_identity_context=current,
            expected_observation_id=record["observation_id"])
        proofs = current_proofs(security_work, record)
        proofs["trusted_dispatch_identity_context"] = current
        self.assertTrue(cv.observation_identity_is_current(record, current, **proofs))
        changed = owner_context(identity_state="verified", scan_eligibility="eligible_verified",
                                active_source_binding_refs=["BND_A", "BND_C"],
                                security_binding_refs={"SEC_A": "BND_A", "SEC_B": "BND_C"},
                                source_binding_version=2)
        self.assertFalse(cv.observation_identity_is_current(record, changed, **proofs))
        self.assertFalse(cv.observation_identity_is_current(
            {**record, "security_id": "SEC_OTHER"}, current, **proofs))

    def test_identity_envelope_rejects_pending_and_mismatched_dispatch_attempt(self):
        work = work_item()
        record = v2_observation(work)
        with self.assertRaises(ValueError):
            cv.validate_observation_identity_v2(
                record, work, trusted_dispatch_identity_context=owner_context(),
                expected_observation_id=record["observation_id"])
        completed = completed_work_item(work, record)
        cv.validate_observation_identity_v2(
            record, completed, trusted_dispatch_identity_context=owner_context(),
            expected_observation_id=record["observation_id"])
        for changed in (
            {"attempts": [{**completed["attempts"][0], "attempt_id": "ATTEMPT_OTHER"}]},
            {"attempts": [{**completed["attempts"][0], "provider": "OTHER"}]},
            {"attempts": [{**completed["attempts"][0], "model_requested": "OTHER"}]},
            {"attempts": [{**completed["attempts"][0], "prompt_hash": "f" * 64}]},
            {"run_ids": ["RUN_OTHER"]}, {"scan_ids": ["SCAN_OTHER"]},
            {"observation_hash": "f" * 64},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                cv.validate_observation_identity_v2(
                    record, {**completed, **changed},
                    trusted_dispatch_identity_context=owner_context(),
                    expected_observation_id=record["observation_id"])
        unavailable = v2_observation(work, execution={
            **record["execution"], "search_status": "unavailable", "search_receipt_id": None,
        })
        with self.assertRaises(ValueError):
            cv.validate_observation_identity_v2(
                unavailable, completed_work_item(work, unavailable),
                trusted_dispatch_identity_context=owner_context(),
                expected_observation_id=unavailable["observation_id"])

    def test_current_score_gate_rejects_self_claimed_or_corrupt_observation(self):
        work = work_item()
        record = v2_observation(work)
        self.assertFalse(cv.observation_identity_is_current(record, owner_context()))
        corrupted = {**record, "observation_id": "obs_" + "f" * 64}
        self.assertFalse(cv.observation_identity_is_current(corrupted, owner_context()))
        proofs = current_proofs(work, record)
        self.assertTrue(cv.observation_identity_is_current(record, owner_context(), **proofs))
        self.assertFalse(cv.observation_identity_is_current(corrupted, owner_context(), **proofs))
        self.assertFalse(cv.observation_identity_is_current(
            record, owner_context(), **{**proofs, "trusted_search_receipt": None}))
        self.assertFalse(cv.observation_identity_is_current(
            record, owner_context(), **{**proofs, "trusted_ingest_receipt": None}))
        self.assertFalse(cv.observation_identity_is_current(
            record, owner_context(), **{**proofs, "trusted_content_receipt": None}))
        self.assertFalse(cv.observation_identity_is_current(
            record, owner_context(), **{**proofs, "persisted_work_item": work}))

    def test_current_score_gate_binds_each_persisted_owner_record(self):
        work = work_item()
        record = v2_observation(work)
        proofs = current_proofs(work, record)
        forged = []
        for name, changes in (
            ("trusted_search_receipt", {"request_id": "REQ_OTHER"}),
            ("trusted_search_receipt", {"attempt_id": "ATTEMPT_OTHER"}),
            ("trusted_search_receipt", {"search_status": "failed"}),
            ("trusted_ingest_receipt", {"consumer": "untrusted"}),
            ("trusted_ingest_receipt", {"ack_status": "rejected"}),
            ("trusted_ingest_receipt", {"observation_hash": "f" * 64}),
            ("trusted_content_receipt", {"issuer": "untrusted"}),
            ("trusted_content_receipt", {"status": "rejected"}),
            ("trusted_content_receipt", {"schema_version": "9.9.9"}),
            ("trusted_content_receipt", {"observation_hash": "f" * 64}),
            ("trusted_content_receipt", {"module_package_id": "PACKAGE_OTHER"}),
            ("trusted_content_receipt", {"question_id": "QUESTION_OTHER"}),
            ("persisted_attempt", {"status": "unknown"}),
            ("persisted_attempt", {"work_item_id": "WORK_OTHER"}),
            ("persisted_attempt", {"prompt_hash": "f" * 64}),
            ("trusted_dispatch_identity_context", owner_context(entity_id="ENT_OTHER")),
            ("expected_observation_id", "obs_" + "f" * 64),
        ):
            altered = dict(proofs)
            if name == "expected_observation_id":
                altered[name] = changes
            elif name == "trusted_dispatch_identity_context":
                altered[name] = changes
            else:
                altered[name] = {**proofs[name], **changes}
            forged.append((name, altered))
        for name, altered in forged:
            with self.subTest(proof=name, altered=altered[name]):
                self.assertFalse(cv.observation_identity_is_current(record, owner_context(), **altered))

    def test_unknown_answer_with_numeric_score_is_history_only_not_current_score(self):
        work = work_item()
        scored = v2_observation(work)
        unknown = v2_observation(work, answer={
            **scored["answer"], "status": "insufficient_evidence", "score": 8,
        })
        persisted = completed_work_item(work, unknown, status="delivered")
        persisted["next_retry_at"] = "2026-09-25T00:00:00Z"
        cv.validate_observation_identity_v2(
            unknown, persisted, trusted_dispatch_identity_context=owner_context(),
            expected_observation_id=unknown["observation_id"])
        proofs = current_proofs(work, unknown)
        proofs["persisted_work_item"] = persisted
        self.assertFalse(cv.observation_identity_is_current(unknown, owner_context(), **proofs))

    def test_schema_valid_but_semantically_invalid_scored_content_needs_owner_receipt(self):
        work = work_item()
        scored = v2_observation(work)
        invalid = v2_observation(work, answer={**scored["answer"], "evidence": []})
        persisted = completed_work_item(work, invalid, status="delivered")
        cv.validate_observation_identity_v2(
            invalid, persisted, trusted_dispatch_identity_context=owner_context(),
            expected_observation_id=invalid["observation_id"])
        question = published_fixture(entity_id="ENT_A")[0]["questions"][0]
        with self.assertRaisesRegex(ValueError, "evidence"):
            sa.validate_content(invalid["answer"], question, invalid["information_cutoff"])
        proofs = current_proofs(work, invalid)
        self.assertFalse(cv.observation_identity_is_current(
            invalid, owner_context(), **{**proofs, "trusted_content_receipt": None}))


if __name__ == "__main__":
    unittest.main()
