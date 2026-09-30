"""The old recursive receipt CLI now has only a retirement notice."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RetiredTaskReceiptCliTests(unittest.TestCase):
    def test_cli_reports_retired_without_reading_or_mutating_a_receipt(self):
        with tempfile.TemporaryDirectory(prefix="iqs-retired-receipt-") as temp:
            root = Path(temp)
            input_path = root / "historical-receipt.json"
            input_path.write_text('{"synthetic":"must stay unchanged"}\n', encoding="utf-8")
            before = input_path.read_bytes()
            result = subprocess.run(
                [sys.executable, "-B", "scripts/task_receipts.py", "--retire-check", str(input_path)],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stderr, "")
            self.assertEqual(len(result.stdout.splitlines()), 1)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "retired")
            self.assertEqual(response["code"], "task_receipt_workflow_retired")
            self.assertEqual(input_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
