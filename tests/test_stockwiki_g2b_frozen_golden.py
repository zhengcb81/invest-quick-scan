"""Consumer regression against a frozen public StockWiki G2b export."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs/implementation/contracts/goldens/stockwiki-g2b-72531b5-provisional.json"
EXPECTED_SHA256 = "0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f"

MAPPING_GOLDEN = GOLDEN.with_name("stockwiki-mapping-72531b5-four-state.json")


def _cli(path: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "scripts/identity_contract_cli.py",
         "--input", str(path), "--schema-version", "2.2.0"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, timeout=30,
    )
    assert result.stderr == ""
    assert len(result.stdout.splitlines()) == 1
    return result.returncode, json.loads(result.stdout)


class StockWikiG2bFrozenGoldenTests(unittest.TestCase):
    def test_frozen_bytes_match_owner_export_hash_and_pass_public_cli(self):
        raw = GOLDEN.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_SHA256)
        request = json.loads(raw)
        self.assertEqual(set(request), {"schema_version", "object_type", "payload", "trusted_context"})
        self.assertEqual(request["payload"]["identity_state"], "provisional")
        code, result = _cli(GOLDEN)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])

    def test_missing_owner_receipt_is_rejected_without_payload_echo(self):
        request = json.loads(GOLDEN.read_text(encoding="utf-8"))
        request["trusted_context"]["identity_receipts"].clear()
        with tempfile.TemporaryDirectory(prefix="iqs-g2b-frozen-") as temp:
            path = Path(temp) / "mutated.json"
            path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            code, result = _cli(path)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["errors"])
        self.assertNotIn("ACME", json.dumps(result))


def _acceptance(*extra: str):
    return subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "scripts/stockwiki_g2b_acceptance.py",
         "--golden", str(GOLDEN), "--mapping-golden", str(MAPPING_GOLDEN), *extra],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, timeout=75,
    )


def test_acceptance_replays_both_frozen_owner_contracts_without_a_checkout():
    result = _acceptance()
    assert result.returncode == 0, result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["proof_mode"] == "frozen_owner_exports"
    assert outcome["live_owner_export"] is None
    assert set(outcome["negative_codes"]) == {
        "entity_id", "receipt_removed", "binding_source", "mic_removed", "revision",
    }
    assert outcome["owner_mapping_probe"]["mapping_negative_count"] == 4
    assert outcome["temporary_roots_cleaned"] is True


def test_acceptance_does_not_use_an_implicit_stockwiki_data_root(tmp_path):
    result = _acceptance("--owner-root", str(tmp_path))
    assert result.returncode == 2
    assert "requires --stockwiki-root, --owner-root, --entity-id and --as-of" in result.stderr


def test_acceptance_never_rewrites_the_owner_golden():
    before = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()
    result = _acceptance("--capture-golden")
    assert result.returncode == 2
    assert "StockWiki owns golden export" in result.stderr
    assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == before


def test_fresh_export_uses_public_cli_with_explicit_data_root(monkeypatch, tmp_path):
    from scripts import stockwiki_g2b_acceptance as acceptance

    code_root = tmp_path / "checkout with no tests"
    package = code_root / "stockwiki"
    package.mkdir(parents=True)
    (package / "cli.py").touch()
    data_root = tmp_path / "explicit isolated data"
    data_root.mkdir()
    query = acceptance.OwnerQuery(code_root, data_root, "ENT_fixture", "2026-09-29T00:00:00Z")
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs["cwd"]))
        return subprocess.CompletedProcess(argv, 0, GOLDEN.read_bytes() + b"\r\n", b"diagnostic warning")

    monkeypatch.setattr(acceptance.subprocess, "run", run)
    assert acceptance._export(query) == GOLDEN.read_bytes()
    assert calls == [([sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli",
                      "--root", str(data_root), "identity-export-g2b",
                      "--entity-id", query.entity_id, "--as-of", query.as_of], code_root)]

    def failure(argv, **kwargs):
        data = b'{"error_code":"entity_not_found","detail":"secret example"}'
        return subprocess.CompletedProcess(argv, 2, b"", data)

    monkeypatch.setattr(acceptance.subprocess, "run", failure)
    with pytest.raises(ValueError, match="entity_not_found") as caught:
        acceptance._export(query)
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("bad_payload", [[], {"entity_id": "another entity"}])
def test_fresh_export_binds_requested_entity_before_consumer(monkeypatch, tmp_path, bad_payload):
    from scripts import stockwiki_g2b_acceptance as acceptance

    query = acceptance.OwnerQuery(tmp_path, tmp_path, "ENT_fixture", "2026-09-29T00:00:00Z")
    monkeypatch.setattr(acceptance, "_export", lambda _: json.dumps({"payload": bad_payload}).encode())
    monkeypatch.setattr(acceptance, "_iqs_validate", lambda _: pytest.fail("invalid source sent to IQS"))
    with pytest.raises(ValueError, match="did not bind the requested entity"):
        acceptance._verify_live_query(query, tmp_path / "fresh.json")


if __name__ == "__main__":
    unittest.main()
