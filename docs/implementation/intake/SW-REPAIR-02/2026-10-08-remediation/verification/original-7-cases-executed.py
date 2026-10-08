"""Read-only producer intake counterexamples; all mutations use private fixtures.

Synthetic identity/subject records come from the producer's public-import test
helpers, never represent real StockWiki identity golden or production data.
"""

import importlib.util
import json
import os
import sqlite3
from pathlib import Path

import pytest

from stockwiki import quick_scan_backup as backup
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_backup_manifest import MANIFEST_NAME, manifest_digest

RUNTIME = Path(os.environ["IQS_SW_READY_WORK_ROOT"]) / "runtime"


def fixture_backup(tmp_path):
    paths = WorkspacePaths.from_root(tmp_path / "workspace")
    data = backup.quick_scan_data_dir(paths)
    data.mkdir(parents=True)
    (data / "marker.txt").write_text("owned fixture", encoding="utf-8")
    result = backup.create_backup(paths, name="owned_backup")
    return paths, result


def test_restore_accepts_already_existing_empty_target(tmp_path):
    paths, result = fixture_backup(tmp_path)
    (backup.quick_scan_data_dir(paths) / "marker.txt").unlink()
    assert backup.quick_scan_data_dir(paths).exists()
    receipt = backup.restore_backup(paths, "owned_backup")
    assert receipt["ok"]
    assert (backup.quick_scan_data_dir(paths) / "marker.txt").read_text() == "owned fixture"


def test_foreign_manifest_directory_is_never_pruned(tmp_path):
    paths, result = fixture_backup(tmp_path)
    foreign = backup.quick_scan_backup_root(paths) / "foreign_fixture"
    foreign.mkdir()
    body = {"format_version": "1.0.0", "files": [], "created_at_utc": "2000-01-01T00:00:00Z"}
    body["manifest_sha256"] = manifest_digest(body)
    (foreign / MANIFEST_NAME).write_text(json.dumps(body), encoding="utf-8")
    receipt = backup.prune_backups(paths, keep=1)
    assert foreign.exists(), "Foreign same-named manifest is not a StockWiki backup owner proof"
    assert "foreign_fixture" in receipt["skipped"]


def test_failed_final_rename_never_leaves_complete_partial_backup(monkeypatch, tmp_path):
    paths = WorkspacePaths.from_root(tmp_path / "workspace")
    data = backup.quick_scan_data_dir(paths)
    data.mkdir(parents=True)
    (data / "marker.txt").write_text("fixture", encoding="utf-8")
    original = Path.rename

    def fail_finalize(path, destination):
        if ".partial-" in path.name:
            raise OSError("synthetic final rename failure")
        return original(path, destination)

    monkeypatch.setattr(Path, "rename", fail_finalize)
    with pytest.raises((OSError, backup.QuickScanBackupError)):
        backup.create_backup(paths, name="must_not_finalize")
    assert not list(backup.quick_scan_backup_root(paths).glob("*.partial-*"))


def test_two_subjects_of_one_issuer_never_silently_collapse_into_one_score(tmp_path):
    import test_quick_scan_profiles as owner
    from test_quick_scan_observations import _observation, _package
    from stockwiki.quick_scan_import import import_package
    from stockwiki.quick_scan_observations import QuickScanObservationStore
    from stockwiki.quick_scan_profiles import build_entity_detail
    from stockwiki.quick_scan_store import QuickScanStore

    paths = owner._workspace(tmp_path / "workspace")
    observations = []
    for index, score in enumerate((2, 9), 1):
        subject = "ASJ_" + ("11111111-1111-4111-8111-111111111111" if index == 1 else "22222222-2222-4222-8222-222222222222")
        observations.append(_observation(
            "OBS_" + str(index) * 64, entity_id=owner.E01, score=score,
            request_id="request-" + str(index), attempt_id="attempt-" + str(index),
            extra={"analysis_subject": {"analysis_subject_id": subject,
                "analysis_subject_revision": 1, "entity_id": owner.E01, "primary_issuer_id": owner.E01}},
        ))
    receipt = import_package(QuickScanObservationStore(paths), _package(observations),
        frozen_release=owner._release(), identity_store=QuickScanStore(paths))
    assert len(receipt["acks"]) == 2 and all(item["status"] == "accepted" for item in receipt["acks"]), receipt
    detail = build_entity_detail(paths, owner.E01)
    fields = [field for group in detail["groups"] for field in group["fields"]
              if field["field_id"] == "score.iqs_01"]
    represented = {field["subject"]["analysis_subject_id"] for field in fields}
    explicitly_ambiguous = any(field.get("status") == "ambiguous" or field.get("ambiguous") for field in fields)
    assert len(represented) == 2 or explicitly_ambiguous, "Different reporting perimeters cannot become one unqualified latest score"


def test_real_legacy_public_snapshot_remains_readable():
    from stockwiki.quick_scan_query import search
    spec = importlib.util.spec_from_file_location("frozen_legacy_query", RUNTIME / "legacy_quick_scan_query.py")
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    profiles = [{"entity_id": "ENT_" + str(index).zfill(6), "canonical_name": "Fixture " + str(index)}
                for index in range(101)]
    old = legacy.search(profiles, page=1, page_size=50)
    current = search(profiles, page=2, page_size=50, snapshot=old["snapshot"])
    assert [row["entity_id"] for row in current["rows"]] == old["snapshot"]["ordered_ids"][50:100]


def test_ui_supports_multiple_conditions_instead_of_single_leaf_static_contract():
    # Static evidence only: this is not a real-browser E2E success claim.
    source = (RUNTIME / "stockwiki/ui_static/app.js").read_text(encoding="utf-8")
    payload = source[source.index("function qsPayload() {"):source.index("function qsSetStatus(")]
    assert "payload.conditions = [{ field: q.field, op: q.op, value: q.value }]" not in payload, "One hard-coded leaf makes AND/OR identical"


def test_sqlite_online_backup_preserves_committed_wal(tmp_path):
    paths = WorkspacePaths.from_root(tmp_path / "workspace")
    data = backup.quick_scan_data_dir(paths)
    data.mkdir(parents=True)
    with sqlite3.connect(data / "scan.sqlite") as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE fixture (value INTEGER)")
        connection.execute("INSERT INTO fixture VALUES (7)")
        connection.commit()
        result = backup.create_backup(paths, name="wal_positive")
        with sqlite3.connect(result.backup_dir / "scan.sqlite") as restored:
            assert restored.execute("SELECT value FROM fixture").fetchone()[0] == 7
            assert restored.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert backup.verify_backup(paths, "wal_positive")["ok"]
