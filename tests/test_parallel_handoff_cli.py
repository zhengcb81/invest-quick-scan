"""Public, read-only intake checks for independent harness handoffs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "parallel_handoff_cli.py"


def _report(package_id: str = "QA-04", lane_id: str = "stockqa") -> dict:
    dirty = {"state": "dirty", "dirty_path_count": 55, "manifest_sha256": "a" * 64}
    return {
        "schema_version": "1.0.0",
        "lane_id": lane_id,
        "package_id": package_id,
        "status": "partial",
        "snapshot": {
            "repository": "C:/Users/郑曾波/Projects/StockQAbyLLM",
            "base_ref": "master",
            "base_commit": "a" * 40,
            "result_ref": "",
            "result_commit": None,
            "worktree_before": dirty,
            "worktree_after": dirty,
        },
        "scope": {
            "task_ids": ["Q04"],
            "authorization_scope_ref": "user_reported_stockqa_authorization",
            "owned_paths": ["C:/Users/郑曾波/Projects/StockQAbyLLM"],
            "authorized_paths": ["src/runners/llm_runner.py"],
            "changed_paths": [],
            "out_of_scope_writes": [],
        },
        "interfaces": [],
        "verification": {
            "checks": [],
            "external_writes": False,
            "network_calls": False,
            "paid_calls": False,
            "temporary_roots": [],
        },
        "review": {"status": "not_run", "snapshot_commit": None, "findings": []},
        "open_items": ["Q04 implementation pending"],
    }


class ParallelHandoffCliTests(unittest.TestCase):
    def setUp(self):
        # Keep test-created files in an owned, writable workspace, including
        # when a Windows sandbox advertises a non-writable system TEMP.
        self.temp_root = tempfile.TemporaryDirectory(prefix=".iqs-handoff-tests-", dir=ROOT)
        self.addCleanup(self.temp_root.cleanup)
        patch = mock.patch.object(tempfile, "tempdir", self.temp_root.name)
        patch.start()
        self.addCleanup(patch.stop)

    def run_cli(self, root: Path, payload: dict | str, *, package_id: str = "QA-04",
                catalog: Path | None = None):
        path = root / "handoff.json"
        path.write_text(
            payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        before = path.read_bytes()
        command = [sys.executable, "-B", "-X", "utf8", str(CLI), "--input", str(path),
                   "--package-id", package_id]
        if catalog is not None:
            command.extend(["--catalog", str(catalog)])
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            check=False,
        )
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        return result.returncode, json.loads(result.stdout)

    def test_valid_partial_handoff_is_format_only_and_read_only(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            code, answer = self.run_cli(Path(temp), _report())
        self.assertEqual(code, 0)
        self.assertEqual(answer, {
            "status": "valid",
            "package_id": "QA-04",
            "validation_scope": "handoff_shape_and_declared_scope_only",
            "errors": [],
        })

    def test_unknown_or_wrong_owner_package_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            unknown_code, unknown = self.run_cli(Path(temp), _report(), package_id="NO-SUCH-PACKAGE")
            report = _report()
            report["lane_id"] = "stockwiki"
            lane_code, lane = self.run_cli(Path(temp), report)
        self.assertEqual(unknown_code, 2)
        self.assertEqual(unknown["errors"][0]["code"], "unknown_package_id")
        self.assertEqual(lane_code, 2)
        self.assertEqual(lane["errors"][0]["code"], "lane_mismatch")

    def test_duplicate_json_key_and_sentinel_are_not_echoed(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            raw = '{"schema_version":"1.0.0","schema_version":"1.0.0",' \
                '"secret":"SENTINEL-DO-NOT-ECHO"}'
            code, answer = self.run_cli(Path(temp), raw)
        self.assertEqual(code, 2)
        self.assertEqual(answer["errors"][0]["code"], "duplicate_json_key")
        self.assertNotIn("SENTINEL", json.dumps(answer))

    def test_path_escape_and_unclean_temp_root_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            report = _report()
            report["scope"]["changed_paths"] = ["../StockWiki/stockwiki/quick_scan_store.py"]
            path_code, path_answer = self.run_cli(Path(temp), report)
            report = _report()
            report["verification"]["temporary_roots"] = [{
                "path_or_id": "temporary-test-root", "created": True, "cleaned": False,
            }]
            temp_code, temp_answer = self.run_cli(Path(temp), report)
        self.assertEqual(path_code, 2)
        self.assertEqual(path_answer["errors"][0]["code"], "changed_path_out_of_scope")
        self.assertEqual(temp_code, 2)
        self.assertEqual(temp_answer["errors"][0]["code"], "temporary_root_not_cleaned")

    def test_read_only_prestudy_cannot_claim_changed_files(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            report = _report("TH-01", "theme")
            report["scope"]["task_ids"] = ["T01"]
            report["scope"]["changed_paths"] = ["SKILL.md"]
            code, answer = self.run_cli(Path(temp), report, package_id="TH-01")
        self.assertEqual(code, 2)
        self.assertEqual(answer["errors"][0]["code"], "read_only_package_changed_files")

    def test_self_declared_authorization_cannot_escape_owner_repo(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            report = _report()
            outside = "C:/Users/郑曾波/Projects/StockWiki/stockwiki/quick_scan_store.py"
            report["scope"]["authorized_paths"] = [outside]
            report["scope"]["changed_paths"] = [outside]
            code, answer = self.run_cli(Path(temp), report)
        self.assertEqual(code, 2)
        self.assertEqual(answer["errors"][0]["code"], "changed_path_out_of_scope")

    def test_declared_authorized_file_inside_owner_repo_is_shape_valid(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-cli-") as temp:
            report = _report()
            report["scope"]["changed_paths"] = ["src/runners/llm_runner.py"]
            code, answer = self.run_cli(Path(temp), report)
        self.assertEqual(code, 0)
        self.assertEqual(answer["validation_scope"], "handoff_shape_and_declared_scope_only")

    def test_dated_catalog_intake_preserves_legacy_default(self):
        folder = ROOT / "docs/implementation/parallel-lanes/packages/2026-10-07"
        report = json.loads((folder / "QA-NET-01.handoff.template.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-catalog-") as temp:
            code, answer = self.run_cli(Path(temp), report, package_id="QA-NET-01",
                                        catalog=folder / "manifest.json")
            old_code, _ = self.run_cli(Path(temp), _report())
            wrong_code, wrong = self.run_cli(Path(temp), report, package_id="QA-NET-01")
        self.assertEqual(code, 0)
        self.assertEqual(answer["validation_scope"], "handoff_shape_and_declared_scope_only")
        self.assertEqual(old_code, 0)
        self.assertEqual(wrong_code, 2)
        self.assertEqual(wrong["errors"][0]["code"], "unknown_package_id")

    def test_dated_waiting_consumer_cannot_claim_writes(self):
        folder = ROOT / "docs/implementation/parallel-lanes/packages/2026-10-07"
        report = json.loads((folder / "TH-IMPL-01.handoff.template.json").read_text(encoding="utf-8"))
        report["scope"]["authorized_paths"] = ["SKILL.md"]
        report["scope"]["changed_paths"] = ["SKILL.md"]
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-catalog-") as temp:
            code, answer = self.run_cli(Path(temp), report, package_id="TH-IMPL-01",
                                        catalog=folder / "manifest.json")
        self.assertEqual(code, 2)
        self.assertEqual(answer["errors"][0]["code"], "read_only_package_changed_files")

    def test_catalog_outside_package_directory_is_refused_before_read(self):
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-catalog-") as temp:
            root = Path(temp)
            catalog = root / "private.json"
            catalog.write_text("SENTINEL-DO-NOT-ECHO", encoding="utf-8")
            code, answer = self.run_cli(root, _report(), catalog=catalog)
        self.assertEqual(code, 2)
        self.assertEqual(answer["errors"][0]["code"], "catalog_outside_package_directory")
        self.assertNotIn("SENTINEL", json.dumps(answer))

    def test_each_dated_package_template_is_shape_only(self):
        folder = ROOT / "docs/implementation/parallel-lanes/packages/2026-10-07"
        with tempfile.TemporaryDirectory(prefix="iqs-handoff-catalog-") as temp:
            for pid in ("QA-NET-01", "SW-READY-01", "TH-IMPL-01", "IN-IMPL-01"):
                with self.subTest(package=pid):
                    report = json.loads((folder / f"{pid}.handoff.template.json").read_text(encoding="utf-8"))
                    code, answer = self.run_cli(Path(temp), report, package_id=pid,
                                                catalog=folder / "manifest.json")
                    self.assertEqual(code, 0)
                    self.assertEqual(answer["validation_scope"], "handoff_shape_and_declared_scope_only")

    def test_malformed_local_catalog_does_not_emit_its_content(self):
        package_root = ROOT / "docs/implementation/parallel-lanes/packages"
        with tempfile.TemporaryDirectory(prefix=".iqs-catalog-test-", dir=package_root) as selected:
            catalog = Path(selected) / "manifest.json"
            for raw in ("SENTINEL-DO-NOT-ECHO", '{"packages":[],"packages":[]}',
                        '{"packages":[{"id":[] }]}'):
                with self.subTest(raw_type=raw[:12]):
                    catalog.write_text(raw, encoding="utf-8")
                    with tempfile.TemporaryDirectory(prefix="iqs-handoff-catalog-") as temp:
                        code, answer = self.run_cli(Path(temp), _report(), catalog=catalog)
                    self.assertEqual(code, 2)
                    self.assertEqual(answer["errors"][0]["code"], "catalog_invalid")
                    self.assertNotIn("SENTINEL", json.dumps(answer))


if __name__ == "__main__":
    unittest.main()
