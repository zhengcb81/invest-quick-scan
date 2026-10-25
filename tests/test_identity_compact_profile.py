"""Synthetic lexical/join tests only; these are not owner producer goldens."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import contract_validation as cv
from identity_contract_cli import validate_file
from test_identity_contract_cli import _entity_request

PROFILE = "stockwiki-g2b/1.1.0"
OLD = "stockwiki-g2b/1.0.0"
COMPACT = "BIND_0123456789abcdef0123456789abcdef"


def request_with_ref(ref):
    request = _entity_request()
    listing = request["payload"]["listings"][0]
    old = listing["source_binding_ref"]
    listing["source_binding_ref"] = ref
    binding = request["trusted_context"]["source_bindings"].pop(old)
    binding["binding_ref"] = ref
    request["trusted_context"]["source_bindings"][ref] = binding
    next(iter(request["trusted_context"]["identity_receipts"].values()))["source_binding_ref"] = ref
    return request


class CompactIdentityProfileTests(unittest.TestCase):
    def validate(self, request, profile=PROFILE):
        with tempfile.TemporaryDirectory(prefix=".iqs-compact-", dir=ROOT) as temp:
            path = Path(temp) / "input.json"
            raw = json.dumps(request).encode("utf-8")
            path.write_bytes(raw)
            result, status = validate_file(str(path), "2.2.0", wire_profile=profile)
            self.assertEqual(path.read_bytes(), raw)
            return result, status

    def test_explicit_minor_profile_supports_compact_and_existing_spelling(self):
        for ref in (COMPACT, "BND_SYNTHETIC_01", "BIND_11111111-1111-4111-8111-111111111111"):
            result, status = self.validate(request_with_ref(ref))
            self.assertEqual(status, 0, result)
            self.assertEqual(result["validation_scope"], "contract_consistency_only")

    def test_old_profile_and_frozen_schema_do_not_gain_compact_support(self):
        original = copy.deepcopy(cv.IDENTITY_SCHEMA)
        old = cv.identity_schema_for_wire_profile(OLD)
        result, status = self.validate(request_with_ref(COMPACT), OLD)
        self.assertEqual(status, 2, result)
        result, status = self.validate(request_with_ref(COMPACT))
        self.assertEqual(status, 0, result)
        self.assertEqual(cv.IDENTITY_SCHEMA, original)
        self.assertEqual(cv.identity_schema_for_wire_profile(OLD), old)

    def test_malformed_refs_and_wrong_binding_join_still_fail(self):
        for ref in ("BIND_" + "a" * 31, "BIND_" + "a" * 33, "BIND_" + "g" * 32,
                    "BIND_" + "A" * 32, COMPACT + "\n", "BIND_../" + "a" * 32):
            result, status = self.validate(request_with_ref(ref))
            self.assertEqual(status, 2, result)
        request = request_with_ref(COMPACT)
        request["trusted_context"]["source_bindings"][COMPACT]["ticker"] = "OTHER"
        result, status = self.validate(request)
        self.assertEqual(status, 2, result)

    def test_verified_country_requirement_is_not_relaxed_by_reader_profile(self):
        # A deliberately mutated archived DTO is a negative fixture, not a
        # replacement owner golden or evidence for changing an entity.
        original = json.loads((ROOT / "docs/implementation/contracts/goldens/stockwiki-real-alphabet-2026-10-07.json").read_bytes())
        result, status = self.validate(original)
        self.assertEqual(status, 0, result)
        request = copy.deepcopy(original)
        request["payload"]["incorporation_country"] = None
        for receipt in request["trusted_context"]["identity_receipts"].values():
            receipt["incorporation_country"] = None
        result, status = self.validate(request)
        self.assertEqual(status, 2, result)

    def test_original_owner_receipt_aliases_and_lifecycle_are_preserved(self):
        directory = ROOT / "docs/implementation/contracts/goldens"
        manifest = json.loads((directory / "stockwiki-real-identity-2026-10-07.manifest.json").read_bytes())
        for entry in manifest["cases"]:
            original = json.loads((directory / entry["path"]).read_bytes())
            result, status = self.validate(original)
            self.assertEqual(status, 0, result)
            for state in (None, "revoked", "superseded"):
                negative = copy.deepcopy(original)
                next(iter(negative["trusted_context"]["identity_receipts"].values()))["effective_status"] = state
                result, status = self.validate(negative)
                self.assertEqual(status, 2, result)


if __name__ == "__main__":
    unittest.main()
