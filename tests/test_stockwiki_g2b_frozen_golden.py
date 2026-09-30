"""Consumer regression against a frozen public StockWiki G2b export."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs/implementation/contracts/goldens/stockwiki-g2b-72531b5-provisional.json"
EXPECTED_SHA256 = "0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f"


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


if __name__ == "__main__":
    unittest.main()
