"""Real archived owner DTOs and adversarial public-CLI wire compatibility.

These are existing W04 exports, not invented StockWiki positives. No producer
store, network, credentials, or documents are accessed by the test suite.
"""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import contract_validation as cv
from test_identity_contract_cli import _entity_request

CLI = ROOT / "scripts/identity_contract_cli.py"
PROFILE = "stockwiki-g2b/1.0.0"
GOLDENS = ROOT / "docs/implementation/contracts/goldens"
MANIFEST = GOLDENS / "stockwiki-real-identity-2026-10-07.manifest.json"
FROZEN_SCHEMAS = {
    # Frozen Git blob (LF); the existing Windows worktree uses CRLF, whose
    # separate raw SHA is recorded in the review. Ignore only Git EOL conversion.
    "identity.schema.json": "4924b5e3bc641dd060f6f748c2fff8a9166d76a7d123c591838fa4c3018282f3",
    "identity-cli-request.schema.json": "d63afdf4420d1432fc3cb0be2f6f27c3ff3d1524e17a6fbffd1a3a3c2a51effc",
}

# A Python startup audit hook guards the real child CLI, including any future
# dependency: network attempts and writes outside this test's root fail.
AUDIT_GUARD = '''
import os, pathlib, sys
root = pathlib.Path(os.environ["IQS_TEST_OWNED_ROOT"]).resolve()
def audit(event, args):
    if event.startswith("socket."):
        raise RuntimeError("network forbidden in identity offline E2E")
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing and not isinstance(path, int):
            if not pathlib.Path(path).resolve().is_relative_to(root):
                raise RuntimeError("write outside test root")
    if event in ("os.remove", "os.rmdir", "os.mkdir", "os.rename"):
        for path in args[:2] if event == "os.rename" else args[:1]:
            if not pathlib.Path(path).resolve().is_relative_to(root):
                raise RuntimeError("mutation outside test root")
sys.addaudithook(audit)
(root / "guard-active").write_text("active", encoding="utf-8")
'''


class IdentityWireProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_bytes())
        cls.raw = {}
        cls.data = {}
        for entry in cls.manifest["cases"]:
            raw = (GOLDENS / entry["path"]).read_bytes()
            assert len(raw) == entry["bytes"]
            assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
            cls.raw[entry["name"]] = raw
            cls.data[entry["name"]] = json.loads(raw)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".iqs-wire-tests-", dir=ROOT)
        self.root = Path(self.temp.name)
        (self.root / "sitecustomize.py").write_text(AUDIT_GUARD, encoding="utf-8")
        self.env = dict(os.environ, PYTHONPATH=str(self.root),
                        IQS_TEST_OWNED_ROOT=str(self.root), PYTHONDONTWRITEBYTECODE="1")

    def tearDown(self):
        self.temp.cleanup()
        self.assertFalse(self.root.exists())

    def invoke(self, request: dict | bytes, *extra: str):
        raw = request if isinstance(request, bytes) else json.dumps(request).encode("utf-8")
        path = self.root / "input.json"
        path.write_bytes(raw)
        (self.root / "guard-active").unlink(missing_ok=True)
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(CLI), "--input", str(path),
             "--schema-version", "2.2.0", *extra],
            cwd=self.root, env=self.env, capture_output=True,
            text=True, encoding="utf-8", timeout=15, check=False,
        )
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual((self.root / "guard-active").read_text(encoding="utf-8"), "active")
        self.assertEqual(result.stderr, "", result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        return result.returncode, json.loads(result.stdout)

    def reject(self, request: dict, code: str | None = None):
        exit_code, response = self.invoke(request)
        self.assertEqual(exit_code, 2, response)
        self.assertEqual(response["status"], "invalid")
        if code:
            self.assertEqual(response["errors"][0]["code"], code)
        self.assertNotIn("PRIVATE-PAYLOAD-SENTINEL", json.dumps(response))

    @staticmethod
    def receipt(request: dict):
        return next(iter(request["trusted_context"]["identity_receipts"].values()))

    @staticmethod
    def validate(request: dict, **kwargs):
        trusted = request["trusted_context"]
        return cv.validate_entity(
            request["payload"], trusted_identity_receipts=trusted["identity_receipts"],
            trusted_source_bindings=trusted["source_bindings"],
            trusted_market_registry=trusted["market_registry"], **kwargs,
        )

    def test_real_three_market_exports_pass_without_rewriting_or_upgrading(self):
        self.assertEqual(set(self.data), {"catl", "cncb_h", "alphabet"})
        for name, raw in self.raw.items():
            with self.subTest(company=name):
                before = copy.deepcopy(self.data[name])
                exit_code, response = self.invoke(raw)
                self.assertEqual(exit_code, 0, response)
                self.assertEqual(response["status"], "valid")
                self.assertEqual(response["wire_profile"], PROFILE)
                self.assertEqual(response["validation_scope"], "contract_consistency_only")
                self.assertEqual(self.data[name], before)
        self.assertEqual(self.data["catl"]["payload"]["identity_state"], "provisional")
        self.assertEqual(len(self.data["alphabet"]["payload"]["listings"]), 4)

    def test_original_schemas_and_legacy_validator_are_unchanged(self):
        for name, digest in FROZEN_SCHEMAS.items():
            raw = (ROOT / "schemas/quick_scan" / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), digest)
        original = copy.deepcopy(cv.IDENTITY_SCHEMA)
        with self.assertRaises((ValueError, cv.JsonSchemaValidationError)):
            self.validate(self.data["catl"])
        self.validate(self.data["catl"], wire_profile=PROFILE)
        self.assertEqual(cv.IDENTITY_SCHEMA, original)
        with self.assertRaises((ValueError, cv.JsonSchemaValidationError)):
            self.validate(self.data["catl"])
        self.validate(_entity_request())

    def test_legacy_bnd_and_status_and_consistent_dual_status_still_pass(self):
        for effective in (None, "active"):
            request = _entity_request()
            if effective:
                self.receipt(request)["effective_status"] = effective
            exit_code, response = self.invoke(request)
            self.assertEqual(exit_code, 0, response)

    def test_inactive_conflicting_missing_and_nonstring_receipt_statuses_fail(self):
        for field in ("status", "effective_status"):
            for value in ("revoked", "superseded", "retired", "unknown", None, True, [], ""):
                with self.subTest(field=field, value=value):
                    request = copy.deepcopy(self.data["catl"])
                    self.receipt(request)[field] = value
                    self.reject(request, "semantic_validation_failed")
        request = copy.deepcopy(self.data["catl"])
        self.receipt(request).pop("effective_status")
        self.reject(request, "semantic_validation_failed")
        request = _entity_request()
        self.receipt(request)["effective_status"] = "revoked"
        with self.assertRaises(ValueError):
            self.validate(request)  # legacy cannot bypass an explicit lifecycle event

    def test_manual_null_evidence_needs_actor_and_exact_source_qualification(self):
        for actor in (None, "", "   ", False, []):
            request = copy.deepcopy(self.data["catl"])
            self.receipt(request)["actor_id"] = actor
            self.reject(request, "semantic_validation_failed")
        for evidence in (False, {}, [], ""):
            request = copy.deepcopy(self.data["catl"])
            self.receipt(request)["evidence_ref"] = evidence
            self.reject(request, "semantic_validation_failed")
        request = copy.deepcopy(self.data["catl"])
        self.receipt(request).pop("evidence_ref")
        self.reject(request, "semantic_validation_failed")

    def test_official_and_verified_evidence_require_https(self):
        for name in ("catl", "alphabet"):
            for evidence in (None, "", "http://example.invalid", False):
                request = copy.deepcopy(self.data[name])
                receipt = self.receipt(request)
                if name == "catl":
                    receipt["basis"] = "official_equity_category"
                receipt["evidence_ref"] = evidence
                self.reject(request, "semantic_validation_failed")

    def test_receipt_revision_requires_exact_positive_integer_not_bool_or_float(self):
        for value in (1, 3, True, 2.0, "2", None):
            request = copy.deepcopy(self.data["catl"])
            self.receipt(request)["identity_revision"] = value
            self.reject(request, "semantic_validation_failed")
        request = _entity_request()
        self.receipt(request)["identity_revision"] = True
        with self.assertRaises(ValueError):
            self.validate(request)

    def test_exact_binding_joins_and_registry_remain_required(self):
        for field in ("entity_id", "security_id", "listing_id", "ticker", "market", "source_record_id"):
            request = copy.deepcopy(self.data["catl"])
            binding = next(iter(request["trusted_context"]["source_bindings"].values()))
            binding[field] = ("US" if field == "market" else "000001" if field == "ticker"
                              else "PRIVATE-PAYLOAD-SENTINEL" if field == "source_record_id"
                              else {"entity_id": "ENT_11111111-1111-4111-8111-111111111111",
                                    "security_id": "SEC_22222222-2222-4222-8222-222222222222",
                                    "listing_id": "LST_33333333-3333-4333-8333-333333333333"}[field])
            self.reject(request)
        for key in ("source_bindings", "identity_receipts", "market_registry"):
            request = copy.deepcopy(self.data["catl"])
            request["trusted_context"][key] = {}
            self.reject(request)

    def test_only_precise_new_binding_uuid_ids_are_admitted(self):
        for ref in ("BIND_SYNTHETIC", "BIND_11111111-1111-1111-8111-111111111111",
                    "BIND_11111111-1111-4111-7111-111111111111", "BIND_", "BIND_a/b",
                    "BIND_11111111-1111-4111-8111-111111111111\n", "BND_OK\n"):
            request = copy.deepcopy(self.data["catl"])
            listing = request["payload"]["listings"][0]
            old = listing["source_binding_ref"]
            listing["source_binding_ref"] = ref
            binding = request["trusted_context"]["source_bindings"].pop(old)
            binding["binding_ref"] = ref
            request["trusted_context"]["source_bindings"][ref] = binding
            self.receipt(request)["source_binding_ref"] = ref
            self.reject(request, "request_schema_invalid")

    def test_verified_multi_listing_exact_coverage_and_attributes_remain_required(self):
        for field in ("listing_ids", "security_ids", "listing_attributes", "security_attributes"):
            request = copy.deepcopy(self.data["alphabet"])
            item = self.receipt(request)[field]
            if isinstance(item, list):
                item.pop()
            else:
                item.pop(next(iter(item)))
            self.reject(request, "semantic_validation_failed")
        request = copy.deepcopy(self.data["alphabet"])
        self.receipt(request)["same_legal_issuer"] = False
        self.reject(request, "semantic_validation_failed")

    def test_unknown_wire_profile_is_rejected_before_reading_missing_input(self):
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), "--input", str(self.root / "missing.json"),
             "--schema-version", "2.2.0", "--wire-profile", "unrecognized/9.9.9"],
            cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8",
            timeout=15, check=False,
        )
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "unknown_wire_profile")

    def test_explicit_legacy_cli_profile_keeps_original_input_boundary(self):
        self.assertEqual(self.invoke(_entity_request(), "--wire-profile", "legacy")[0], 0)
        self.assertEqual(self.invoke(self.raw["catl"], "--wire-profile", "legacy")[0], 2)

    def test_child_guard_blocks_network_and_writes_before_side_effects(self):
        forbidden = ROOT / (self.root.name + "-forbidden.json")
        code = (
            "import pathlib,socket; blocked=0\n"
            "try: socket.socket()\n"
            "except RuntimeError: blocked+=1\n"
            f"try: pathlib.Path({str(forbidden)!r}).write_text('forbidden')\n"
            "except RuntimeError: blocked+=1\n"
            "assert blocked==2\nprint('guard_canaries_passed')"
        )
        result = subprocess.run([sys.executable, "-B", "-c", code], cwd=self.root,
                                env=self.env, capture_output=True, text=True,
                                encoding="utf-8", timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "guard_canaries_passed")
        self.assertFalse(forbidden.exists())

    def test_profile_schema_copy_and_unknown_internal_profile_do_not_leak(self):
        legacy = copy.deepcopy(cv.IDENTITY_SCHEMA)
        derived = cv.identity_schema_for_wire_profile(PROFILE)
        changed = []
        for name, definition in legacy["definitions"].items():
            if definition != derived["definitions"][name]:
                changed.append(name)
        self.assertEqual(changed, ["ListingV21", "SourceBindingV21"])
        derived["definitions"].clear()
        self.assertEqual(cv.IDENTITY_SCHEMA, legacy)
        self.assertTrue(cv.identity_schema_for_wire_profile(PROFILE)["definitions"])
        with self.assertRaises(ValueError):
            self.validate(_entity_request(), wire_profile="made_up/1.0.0")


if __name__ == "__main__":
    unittest.main()
