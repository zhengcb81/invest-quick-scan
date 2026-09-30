"""Regression checks for retiring the engineering receipt workflow."""
from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/implementation/archive/task-receipts-v2-legacy"


class TaskReceiptRetirementTests(unittest.TestCase):
    def test_preservation_manifest_is_complete_and_pinned(self):
        manifest_path = ARCHIVE / "preservation-manifest.json"
        self.assertEqual(
            hashlib.sha256(manifest_path.read_bytes()).hexdigest().upper(),
            "562FE14079642F7EB0FE728DF69355226D6F584E9BB1ED574E1AD656FD5CED1A",
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["entries"]), 186)
        self.assertEqual(
            Counter(entry["kind"] for entry in manifest["entries"]),
            {
                "retired_tool_source": 5,
                "retired_plan_snapshot": 1,
                "preserved_historical_evidence": 180,
            },
        )

    def test_historical_receipts_reviews_and_archived_sources_keep_their_hashes(self):
        manifest = json.loads(
            (ARCHIVE / "preservation-manifest.json").read_text(encoding="utf-8")
        )
        entries = manifest["entries"]
        self.assertTrue(any(entry["kind"] == "preserved_historical_evidence" for entry in entries))
        self.assertTrue(any(entry["kind"] == "retired_tool_source" for entry in entries))
        for entry in entries:
            with self.subTest(path=entry["path"]):
                content = (ROOT / entry["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), entry["sha256"])
                self.assertEqual(len(content), entry["bytes"])

    def test_active_plan_has_no_task_receipt_engine_or_p01_closure_gate(self):
        plan = json.loads((ROOT / "docs/implementation/tasks.json").read_text(encoding="utf-8"))
        cases = json.loads(
            (ROOT / "docs/implementation/acceptance-cases.json").read_text(encoding="utf-8")
        )
        task_ids = {task["id"] for task in plan["tasks"]}
        self.assertNotIn("P01", task_ids)
        self.assertTrue(all("P01" not in task.get("depends_on", []) for task in plan["tasks"]))
        self.assertTrue(all("historical_context_dependencies" not in task for task in plan["tasks"]))
        self.assertNotIn("historical_context_edges", plan)
        self.assertTrue(all(case.get("owner_task") != "P01" for case in cases["cases"]))
        self.assertTrue(all(not case["id"].startswith("RCPT-") for case in cases["cases"]))
        self.assertFalse(any("Receipt dependency rule:" in boundary for boundary in plan["global_boundaries"]))


if __name__ == "__main__":
    unittest.main()
