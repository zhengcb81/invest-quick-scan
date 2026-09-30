"""IQS consumer checks against frozen StockWiki public mapping DTO outputs."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.stockwiki_mapping_contract import MappingContractError, SCHEMA, validate_mapping_dto


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs/implementation/contracts/goldens/stockwiki-mapping-72531b5-four-state.json"
EXPECTED_SHA256 = "da3991c0d85ef9a0bce7c9152475b9184942df74c34fab4c5c935fb0e375a96f"


class StockWikiMappingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = GOLDEN.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
        cls.bundle = json.loads(raw)

    def test_schema_and_owner_generated_four_states(self):
        Draft202012Validator.check_schema(SCHEMA)
        cases = self.bundle["cases"]
        self.assertEqual([case["name"] for case in cases],
                         ["not_attempted", "unknown", "ambiguous", "mapped", "source_mismatch"])
        self.assertEqual([case["dto"]["mapping_status"] for case in cases],
                         [None, "unknown", "ambiguous", "mapped", "unknown"])
        self.assertEqual([case["dto"]["attempted"] for case in cases],
                         [False, True, True, True, True])
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(validate_mapping_dto(case["dto"], self.bundle["snapshot"],
                                                      case["query"]), case["dto"])
        self.assertTrue(cases[-1]["dto"]["binding_mismatch"])
        self.assertEqual(len(cases[2]["dto"]["candidates"]), 2)
        self.assertIsNone(cases[2]["dto"]["candidate"])

    def test_forged_candidate_and_state_fail_closed(self):
        snapshot = self.bundle["snapshot"]
        case = next(case for case in self.bundle["cases"] if case["name"] == "mapped")
        attacks = []
        fake_id = copy.deepcopy(case["dto"])
        fake_id["candidate"]["entity_id"] = "ENT_forged"
        attacks.append((fake_id, case["query"]))
        wrong_state = copy.deepcopy(case["dto"])
        wrong_state["mapping_status"] = "unknown"
        attacks.append((wrong_state, case["query"]))
        wrong_source = copy.deepcopy(case["dto"])
        wrong_source["candidate"]["source_binding"]["source_record_id"] = "urn:other"
        attacks.append((wrong_source, case["query"]))
        wrong_hash = copy.deepcopy(case["dto"])
        wrong_hash["snapshot_sha256"] = "0" * 64
        attacks.append((wrong_hash, case["query"]))
        attacks.append((case["dto"], {**case["query"], "as_of": "2026-09-30T00:00:00Z"}))
        for dto, query in attacks:
            with self.subTest(dto=dto["mapping_status"], query=query["as_of"]):
                with self.assertRaises(MappingContractError):
                    validate_mapping_dto(dto, snapshot, query)

    def test_missing_or_unsupported_dto_version_refused(self):
        case = self.bundle["cases"][0]
        for value in (None, "2.0.0"):
            mutated = copy.deepcopy(case["dto"])
            mutated["mapping_dto_schema_version"] = value
            with self.assertRaisesRegex(MappingContractError, "unsupported_mapping_dto_version"):
                validate_mapping_dto(mutated, self.bundle["snapshot"], case["query"])

    def test_rehashed_snapshot_with_wrong_source_binding_still_rejected(self):
        snapshot = copy.deepcopy(self.bundle["snapshot"])
        snapshot["source_bindings"][0]["ticker"] = "OTHER"
        payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        case = next(case for case in self.bundle["cases"] if case["name"] == "mapped")
        dto = copy.deepcopy(case["dto"])
        dto["snapshot_sha256"] = snapshot["snapshot_sha256"]
        with self.assertRaisesRegex(MappingContractError, "candidate_owner_join_mismatch"):
            validate_mapping_dto(dto, snapshot, case["query"])

    def test_rehashed_expired_listing_cannot_map_at_later_as_of(self):
        snapshot = copy.deepcopy(self.bundle["snapshot"])
        snapshot["entities"][0]["listings"][0]["valid_to"] = "2026-09-01T00:00:00Z"
        snapshot["source_bindings"][0]["valid_to"] = "2026-09-01T00:00:00Z"
        payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        case = next(case for case in self.bundle["cases"] if case["name"] == "mapped")
        dto = copy.deepcopy(case["dto"])
        dto["snapshot_sha256"] = snapshot["snapshot_sha256"]
        dto["candidate"]["source_binding"]["valid_to"] = "2026-09-01T00:00:00Z"
        dto["candidates"][0]["source_binding"]["valid_to"] = "2026-09-01T00:00:00Z"
        with self.assertRaises(MappingContractError):
            validate_mapping_dto(dto, snapshot, case["query"])

    def test_rehashed_unsupported_snapshot_package_version_refused(self):
        snapshot = copy.deepcopy(self.bundle["snapshot"])
        snapshot["identity_package_version"] = "9.9.9"
        payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        case = next(case for case in self.bundle["cases"] if case["name"] == "mapped")
        dto = copy.deepcopy(case["dto"])
        dto["snapshot_sha256"] = snapshot["snapshot_sha256"]
        with self.assertRaises(MappingContractError):
            validate_mapping_dto(dto, snapshot, case["query"])

    def test_retired_source_binding_cannot_map(self):
        snapshot = copy.deepcopy(self.bundle["snapshot"])
        snapshot["source_bindings"][0]["status"] = "retired"
        payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        case = next(case for case in self.bundle["cases"] if case["name"] == "mapped")
        dto = copy.deepcopy(case["dto"])
        dto["snapshot_sha256"] = snapshot["snapshot_sha256"]
        dto["candidate"]["source_binding"]["status"] = "retired"
        dto["candidates"][0]["source_binding"]["status"] = "retired"
        with self.assertRaises(MappingContractError):
            validate_mapping_dto(dto, snapshot, case["query"])


if __name__ == "__main__":
    unittest.main()
