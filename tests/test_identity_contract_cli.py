"""Subprocess contract tests for the public identity JSON validation CLI.

Fixtures in this module are deliberately synthetic. They test only the IQS
schema/reference contract and are not StockWiki producer goldens.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "identity_contract_cli.py"
PACKAGE_VERSION = "2.2.0"
MAX_INPUT_BYTES = 1_048_576
ENTITY_ID = "ENT_11111111-1111-4111-8111-111111111111"
SECURITY_ID = "SEC_22222222-2222-4222-8222-222222222222"
LISTING_ID = "LST_33333333-3333-4333-8333-333333333333"


def _entity_request() -> dict:
    entity = {
        "identity_schema_version": "2.1.0",
        "identity_state": "provisional",
        "identity_revision": 1,
        "entity_id": ENTITY_ID,
        "canonical_name": "Synthetic example issuer",
        "incorporation_country": None,
        "scope_attestation_id": "ATT_SYNTHETIC_01",
        "company_wiki_ref": None,
        "formal_stockwiki_profile": None,
        "securities": [{
            "security_id": SECURITY_ID,
            "entity_id": ENTITY_ID,
            "security_type": None,
            "share_class": None,
            "adr_ratio": None,
            "ordinary_security_ref": None,
        }],
        "listings": [{
            "listing_id": LISTING_ID,
            "entity_id": ENTITY_ID,
            "security_id": SECURITY_ID,
            "market": "US",
            "exchange_raw": "Synthetic venue",
            "exchange_mic": None,
            "ticker_raw": "SYNTH",
            "ticker": "SYNTH",
            "currency": None,
            "listing_status": None,
            "source_binding_ref": "BND_SYNTHETIC_01",
            "valid_from": None,
            "valid_to": None,
        }],
        "segments": [],
    }
    listing = entity["listings"][0]
    binding = {
        "binding_ref": listing["source_binding_ref"],
        "source_namespace": "synthetic-test-only",
        "source_record_id": "fixture:synthetic-issuer-01",
        "source_canonical_name": entity["canonical_name"],
        "entity_id": ENTITY_ID,
        "security_id": SECURITY_ID,
        "listing_id": LISTING_ID,
        "market": "US",
        "exchange_raw": listing["exchange_raw"],
        "exchange_mic": None,
        "ticker_raw": listing["ticker_raw"],
        "ticker": listing["ticker"],
        "valid_from": None,
        "valid_to": None,
        "status": "active",
    }
    scope_receipt = {
        "receipt_id": entity["scope_attestation_id"],
        "kind": "provisional_scope",
        "entity_id": ENTITY_ID,
        "identity_revision": 1,
        "status": "active",
        "security_id": SECURITY_ID,
        "listing_id": LISTING_ID,
        "source_binding_ref": binding["binding_ref"],
        "source_namespace": binding["source_namespace"],
        "source_record_id": binding["source_record_id"],
        "source_listing": {
            "listing_id": LISTING_ID,
            "security_id": SECURITY_ID,
            "market": "US",
            "exchange_raw": listing["exchange_raw"],
            "exchange_mic": None,
            "ticker_raw": listing["ticker_raw"],
            "ticker": listing["ticker"],
            "valid_from": None,
            "valid_to": None,
            "canonical_name": entity["canonical_name"],
        },
        "known_attributes": {
            "incorporation_country": None,
            "security_type": None,
            "share_class": None,
            "currency": None,
            "listing_status": None,
        },
        "scope": "listed_operating_company",
        "basis": "user_exact_security_attestation",
        "negative_scope_flag": False,
        "evidence_ref": "synthetic-test-only",
        "actor_id": "synthetic-test-only",
        "recorded_at": "2026-09-28T00:00:00Z",
    }
    return {
        "schema_version": PACKAGE_VERSION,
        "object_type": "entity",
        "payload": entity,
        "trusted_context": {
            "market_registry": {"US": ["XNAS", "XNYS"]},
            "identity_receipts": {entity["scope_attestation_id"]: scope_receipt},
            "source_bindings": {binding["binding_ref"]: binding},
        },
    }


def _analysis_subject_request() -> dict:
    subject = {
        "analysis_subject_schema_version": "1.0.0",
        "analysis_subject_id": "ASJ_99999999-9999-4999-8999-999999999999",
        "analysis_subject_revision": 1,
        "display_name": "Synthetic standalone issuer",
        "primary_issuer_id": ENTITY_ID,
        "anchor_listing_id": None,
        "scope_kind": "standalone_issuer",
        "scope_as_of": "2026-06-30T00:00:00Z",
        "perimeter_coverage": "not_applicable",
        "memberships": [{
            "entity_id": ENTITY_ID,
            "role": "primary_issuer",
            "valid_from": None,
            "valid_to": None,
            "evidence_ref": "https://example.invalid/synthetic-test-only",
        }],
    }
    return {
        "schema_version": PACKAGE_VERSION,
        "object_type": "analysis_subject",
        "payload": subject,
        "trusted_context": {
            "issuer_states": {ENTITY_ID: "verified"},
            "listing_to_issuer": {},
            "reporting_perimeter_receipts": {},
        },
    }


class IdentityContractCliTests(unittest.TestCase):
    def run_cli(self, input_path: Path, schema_version: str = PACKAGE_VERSION):
        return subprocess.run(
            [sys.executable, "-B", str(CLI), "--input", str(input_path),
             "--schema-version", schema_version],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )

    def write_request(self, root: Path, value: dict, name: str = "request.json") -> Path:
        path = root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def output_object(self, result: subprocess.CompletedProcess[str]) -> dict:
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        return json.loads(result.stdout)

    def test_valid_entity_request_returns_one_line_json_exit_zero_and_does_not_modify_input(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            path = self.write_request(Path(temp), _entity_request())
            before = path.read_bytes()
            result = self.run_cli(path)
            response = self.output_object(result)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(response["status"], "valid")
            self.assertEqual(response["schema_version"], PACKAGE_VERSION)
            self.assertEqual(response["validation_scope"], "contract_consistency_only")
            self.assertEqual(response["errors"], [])
            self.assertEqual(path.read_bytes(), before)

    def test_valid_analysis_subject_request_is_contract_only_and_read_only(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            path = self.write_request(Path(temp), _analysis_subject_request())
            before = path.read_bytes()
            result = self.run_cli(path)
            response = self.output_object(result)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(response["status"], "valid")
            self.assertEqual(response["validation_scope"], "contract_consistency_only")
            self.assertEqual(path.read_bytes(), before)

    def test_semantic_identity_mismatch_returns_stable_pointer_without_echoing_input(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            request = _entity_request()
            request["payload"]["canonical_name"] = "SYNTHETIC-PRIVATE-SENTINEL"
            request["trusted_context"]["source_bindings"]["BND_SYNTHETIC_01"]["security_id"] = (
                "SEC_44444444-4444-4444-8444-444444444444"
            )
            path = self.write_request(Path(temp), request)
            result = self.run_cli(path)
            response = self.output_object(result)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(response["status"], "invalid")
            self.assertEqual(response["errors"][0]["code"], "semantic_validation_failed")
            self.assertEqual(response["errors"][0]["pointer"], "/payload")
            self.assertNotIn("SYNTHETIC-PRIVATE-SENTINEL", result.stdout)
            self.assertNotIn("SEC_FOREIGN", result.stdout)

    def test_unknown_schema_version_exits_three_without_reading_input(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            missing = Path(temp) / "must-not-be-opened.json"
            result = self.run_cli(missing, "99.0.0")
            response = self.output_object(result)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(response["status"], "invalid")
            self.assertEqual(response["errors"], [{
                "code": "unknown_schema_version", "pointer": "/schema_version"
            }])

    def test_duplicate_json_keys_fail_closed_without_echo(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text(
                '{"schema_version":"2.2.0","schema_version":"2.2.0",'
                '"object_type":"entity","payload":{},"trusted_context":{},'
                '"sentinel":"SYNTHETIC-DUPLICATE-INPUT-SENTINEL"}',
                encoding="utf-8",
            )
            before = path.read_bytes()
            result = self.run_cli(path)
            response = self.output_object(result)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(response["errors"][0]["code"], "duplicate_json_key")
            self.assertEqual(path.read_bytes(), before)
            self.assertNotIn("SYNTHETIC-DUPLICATE-INPUT-SENTINEL", result.stdout)

    def test_oversized_input_is_rejected_before_full_read(self):
        with tempfile.TemporaryDirectory(prefix="iqs-identity-cli-") as temp:
            path = Path(temp) / "oversized.json"
            path.write_bytes(b" " * (MAX_INPUT_BYTES + 1))
            before_size = path.stat().st_size
            result = self.run_cli(path)
            response = self.output_object(result)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(response["errors"][0]["code"], "input_too_large")
            self.assertEqual(path.stat().st_size, before_size)


if __name__ == "__main__":
    unittest.main()
