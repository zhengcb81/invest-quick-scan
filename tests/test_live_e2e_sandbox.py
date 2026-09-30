"""Offline regression tests for live-test isolation and guarded cleanup."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from live_e2e_sandbox import IsolationError, LiveE2ESandbox


class LiveE2ESandboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iqs-live-sandbox-test-")
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_run_directories_are_unique_and_all_paths_stay_under_system_temp(self):
        first = LiveE2ESandbox(base_dir=self.base)
        second = LiveE2ESandbox(base_dir=self.base)
        try:
            self.assertNotEqual(first.run_id, second.run_id)
            self.assertNotEqual(first.root, second.root)
            self.assertTrue(first.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            self.assertEqual(set(first.paths), set(first.DIRECTORY_NAMES))
            for path in first.paths.values():
                self.assertEqual(path.parent, first.root)
            self.assertEqual(first.assert_run_path(first.path("downloads") / "sample.bin"),
                             first.path("downloads") / "sample.bin")
            with self.assertRaisesRegex(IsolationError, "dedicated run subdirectory"):
                first.assert_run_path(first.root / "unclassified-output.json")
        finally:
            first.cleanup()
            second.cleanup()

    def test_success_removes_only_registered_run_files_and_keeps_preexisting_sibling(self):
        sentinel = self.base / "preexisting-user-file.bin"
        sentinel.write_bytes(b"must survive")
        before = sentinel.read_bytes()
        sandbox = LiveE2ESandbox(base_dir=self.base)
        root = sandbox.root
        downloaded = sandbox.path("downloads") / "public-sample.bin"
        downloaded.write_bytes(b"real test download fixture bytes")
        record = sandbox.register_artifact(
            downloaded, action="downloaded_fixture", component_owner="stockqa"
        )
        manifest = json.loads((root / sandbox.MANIFEST_FILE).read_text(encoding="utf-8"))
        self.assertEqual(record["sha256"], manifest["artifacts"][0]["sha256"])
        self.assertEqual(record["run_id"], sandbox.run_id)
        self.assertEqual(record["owner_id"], sandbox.owner_id)

        sandbox.cleanup()
        self.assertFalse(root.exists())
        self.assertEqual(sentinel.read_bytes(), before)

    def test_path_traversal_and_external_artifact_registration_fail_closed(self):
        outside = self.base / "outside.txt"
        outside.write_text("keep", encoding="utf-8")
        sandbox = LiveE2ESandbox(base_dir=self.base)
        with self.assertRaises(IsolationError):
            sandbox.assert_run_path(sandbox.root / ".." / outside.name)
        with self.assertRaises(IsolationError):
            sandbox.register_artifact(
                outside, action="must_not_delete", component_owner="stockqa"
            )
        sandbox.cleanup()
        self.assertTrue(outside.exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_hard_link_to_external_file_is_not_accepted_as_owned_artifact(self):
        outside = self.base / "external-source.txt"
        outside.write_bytes(b"outside-owned data")
        sandbox = LiveE2ESandbox(base_dir=self.base)
        link = sandbox.path("downloads") / "unsafe-hard-link.txt"
        try:
            os.link(outside, link)
        except (AttributeError, OSError, NotImplementedError) as exc:
            sandbox.cleanup()
            self.skipTest(f"filesystem does not support hard links here: {exc}")

        with self.assertRaisesRegex(IsolationError, "hard-linked"):
            sandbox.register_artifact(link, action="download", component_owner="stockqa")
        self.assertEqual(outside.read_bytes(), b"outside-owned data")
        link.unlink()
        sandbox.cleanup()

    def test_modified_registered_download_is_preserved_for_investigation(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        artifact = sandbox.path("downloads") / "report.bin"
        original = b"provider response body"
        artifact.write_bytes(original)
        sandbox.register_artifact(artifact, action="download", component_owner="stockqa")
        artifact.write_bytes(b"changed after the recorded hash")

        with self.assertRaisesRegex(IsolationError, "changed since registration"):
            sandbox.cleanup()
        self.assertTrue(sandbox.root.exists())
        self.assertEqual(artifact.read_bytes(), b"changed after the recorded hash")

        artifact.write_bytes(original)
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_unregistered_partial_download_blocks_cleanup_until_registered(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        partial = sandbox.path("downloads") / "interrupted-download.part"
        partial.write_bytes(b"partial response")

        with self.assertRaisesRegex(IsolationError, "unregistered"):
            sandbox.cleanup()
        self.assertTrue(partial.exists())
        self.assertTrue(sandbox.root.exists())

        records = sandbox.register_existing_files(
            action="partial_download_after_failure", component_owner="stockqa"
        )
        self.assertEqual(len(records), 1)
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_real_temporary_sqlite_and_component_output_files_are_registered_then_removed(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        database = sandbox.path("sqlite") / "quick_scan_test.sqlite3"
        connection = sqlite3.connect(database)
        try:
            connection.execute("CREATE TABLE probe (value TEXT NOT NULL)")
            connection.execute("INSERT INTO probe(value) VALUES (?)", ("temporary",))
            connection.commit()
        finally:
            connection.close()
        (sandbox.path("workspace") / "state.json").write_text("{}", encoding="utf-8")
        (sandbox.path("downloads") / "search-cache.json").write_text("{}", encoding="utf-8")
        (sandbox.path("exchange") / "result.json").write_text("{}", encoding="utf-8")
        (sandbox.path("logs") / "worker.log").write_text("done", encoding="utf-8")

        records = sandbox.register_existing_files(
            action="component_output", component_owner="stockwiki"
        )
        self.assertEqual(len(records), 5)
        self.assertEqual({Path(item["path"]).parts[0] for item in records},
                         set(sandbox.DIRECTORY_NAMES))
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())
        self.assertFalse(database.exists())

    def test_external_state_drift_preserves_run_directory_until_state_is_restored(self):
        protected = self.base / "protected-profile.json"
        protected.write_text("before", encoding="utf-8")
        observer = lambda: {"sha256": hashlib.sha256(protected.read_bytes()).hexdigest()}
        sandbox = LiveE2ESandbox(base_dir=self.base, state_observer=observer)
        marker = sandbox.path("logs") / "run.log"
        marker.write_text("test log", encoding="utf-8")
        sandbox.register_artifact(marker, action="log", component_owner="stockwiki")
        protected.write_text("unexpected external mutation", encoding="utf-8")

        with self.assertRaisesRegex(IsolationError, "protected external state drifted"):
            sandbox.cleanup()
        self.assertTrue(sandbox.root.exists())
        self.assertTrue(marker.exists())

        protected.write_text("before", encoding="utf-8")
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_manifest_tampering_never_expands_the_cleanup_allowlist(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        artifact = sandbox.path("exchange") / "result.json"
        artifact.write_text("{}", encoding="utf-8")
        sandbox.register_artifact(artifact, action="exchange", component_owner="stockwiki")
        manifest = sandbox.root / sandbox.MANIFEST_FILE
        original = manifest.read_bytes()
        manifest.write_bytes(original + b" ")

        with self.assertRaisesRegex(IsolationError, "manifest changed"):
            sandbox.cleanup()
        self.assertTrue(sandbox.root.exists())
        self.assertTrue(artifact.exists())

        manifest.write_bytes(original)
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_hardlinked_manifest_is_rejected_without_writing_through_to_target(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        external = self.base / "external-manifest-target.json"
        external.write_bytes(b"user-owned bytes")
        manifest = sandbox.root / sandbox.MANIFEST_FILE
        original_manifest = manifest.read_bytes()
        manifest.unlink()
        try:
            os.link(external, manifest)
        except OSError as exc:
            sandbox.cleanup()
            self.skipTest(f"filesystem does not support hard links here: {exc}")

        artifact = sandbox.path("downloads") / "download.bin"
        artifact.write_bytes(b"temporary")
        with self.assertRaisesRegex(IsolationError, "unique regular file"):
            sandbox.register_artifact(artifact, action="download", component_owner="stockqa")
        self.assertEqual(external.read_bytes(), b"user-owned bytes")
        self.assertEqual(manifest.read_bytes(), b"user-owned bytes")
        with self.assertRaisesRegex(IsolationError, "unique regular file"):
            sandbox.cleanup()
        self.assertTrue(artifact.exists())

        manifest.unlink()
        manifest.write_bytes(original_manifest)
        artifact.unlink()
        sandbox.cleanup()

    @unittest.skipUnless(os.name == "nt", "Windows open-file sharing is the target case")
    def test_open_sqlite_handle_fails_cleanup_preflight_before_any_file_is_removed(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        database = sandbox.path("sqlite") / "locked.sqlite3"
        connection = sqlite3.connect(database)
        connection.execute("CREATE TABLE probe (value TEXT NOT NULL)")
        connection.commit()
        log = sandbox.path("logs") / "must-survive.log"
        log.write_text("keep until SQLite is closed", encoding="utf-8")
        sandbox.register_existing_files(action="test_output", component_owner="stockwiki")

        try:
            with self.assertRaisesRegex(IsolationError, "no files were deleted"):
                sandbox.cleanup()
            self.assertTrue(database.exists())
            self.assertTrue(log.exists())
            self.assertEqual(log.read_text(encoding="utf-8"), "keep until SQLite is closed")
        finally:
            connection.close()
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_failed_file_staging_rolls_back_every_prior_artifact(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        download = sandbox.path("downloads") / "source.bin"
        download.write_bytes(b"download stays")
        database = sandbox.path("sqlite") / "locked.sqlite3"
        database.write_bytes(b"database stays")
        log = sandbox.path("logs") / "worker.log"
        log.write_bytes(b"log stays")
        sandbox.register_existing_files(action="test_output", component_owner="stockwiki")
        real_replace = os.replace

        def fail_on_locked_db(source, destination):
            if Path(source).name == database.name:
                raise PermissionError("simulated open SQLite handle")
            return real_replace(source, destination)

        with patch("live_e2e_sandbox.os.replace", side_effect=fail_on_locked_db):
            with self.assertRaisesRegex(IsolationError, "no files were deleted"):
                sandbox.cleanup()
        self.assertEqual(download.read_bytes(), b"download stays")
        self.assertEqual(database.read_bytes(), b"database stays")
        self.assertEqual(log.read_bytes(), b"log stays")
        self.assertFalse(list(sandbox.root.rglob(".cleanup-*")))
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_empty_directory_junction_or_symlink_blocks_cleanup(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        outside = self.base / "outside-target"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("not part of the run", encoding="utf-8")
        link = sandbox.path("workspace") / "empty-link"
        if os.name == "nt":
            result = subprocess.run(["cmd.exe", "/c", "mklink", "/J",
                                     str(link), str(outside)],
                                    capture_output=True, text=True, check=False)
            if result.returncode != 0:
                sandbox.cleanup()
                self.skipTest(f"could not create a temporary junction: {result.stderr}")
        else:
            link.symlink_to(outside, target_is_directory=True)
        self.assertTrue(link.exists())

        log = sandbox.path("logs") / "evidence.log"
        log.write_text("must remain on guard failure", encoding="utf-8")
        sandbox.register_artifact(log, action="log", component_owner="stockwiki")
        with self.assertRaisesRegex(IsolationError, "link or reparse point"):
            sandbox.cleanup()
        self.assertTrue(log.exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "not part of the run")

        if os.name == "nt":
            os.rmdir(link)
        else:
            link.unlink()
        sandbox.cleanup()
        self.assertTrue(sentinel.exists())

    def test_context_manager_cleans_on_test_exception_without_suppressing_it(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        root = sandbox.root
        artifact = sandbox.path("logs") / "failure.log"
        with self.assertRaisesRegex(RuntimeError, "simulated provider failure"):
            with sandbox:
                artifact.write_text("provider failed after writing", encoding="utf-8")
                sandbox.register_artifact(
                    artifact, action="failure_log", component_owner="stockqa"
                )
                raise RuntimeError("simulated provider failure")
        self.assertFalse(root.exists())

    def test_cleanup_stops_only_children_started_by_this_sandbox(self):
        command = [sys.executable, "-c", "import time; time.sleep(60)"]
        sandbox = LiveE2ESandbox(base_dir=self.base)
        owned = sandbox.start_process(command, component_owner="stockqa")
        unrelated = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        try:
            sandbox.cleanup()
            self.assertIsNotNone(owned.poll())
            self.assertIsNone(unrelated.poll())
        finally:
            for process in (owned, unrelated):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)

    def test_child_default_working_directory_routes_relative_output_to_run_workspace(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        code = (
            "from pathlib import Path; "
            "Path('relative-output.txt').write_text('isolated', encoding='utf-8')"
        )
        child = sandbox.start_process(
            [sys.executable, "-c", code], component_owner="stockqa"
        )
        self.assertEqual(child.wait(timeout=5), 0)
        output = sandbox.path("workspace") / "relative-output.txt"
        self.assertEqual(output.read_text(encoding="utf-8"), "isolated")
        sandbox.register_artifact(output, action="child_relative_output",
                                  component_owner="stockqa")
        sandbox.cleanup()
        self.assertFalse(sandbox.root.exists())

    def test_child_process_external_working_directory_is_rejected_before_spawn(self):
        sandbox = LiveE2ESandbox(base_dir=self.base)
        external = self.base / "outside-cwd"
        external.mkdir()
        with patch("live_e2e_sandbox.subprocess.Popen") as popen:
            with self.assertRaisesRegex(IsolationError, "outside this run"):
                sandbox.start_process(
                    [sys.executable, "-c", "pass"],
                    component_owner="stockqa", cwd=external,
                )
            popen.assert_not_called()
        sandbox.cleanup()


if __name__ == "__main__":
    unittest.main()
