"""Consumer-boundary counterexamples; all data are synthetic and privately owned."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pytest
from test_quick_scan_observations import _observation
from test_swr_profiles import E01, FIELD, _accepted, _bare_workspace, _hit, _score_fields

from stockwiki import quick_scan_backup as backup
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_backup_manifest import MANIFEST_NAME
from stockwiki.quick_scan_profiles import build_entity_detail


def two_backups(tmp_path):
    paths = WorkspacePaths.from_root(tmp_path / "workspace")
    data = backup.quick_scan_data_dir(paths)
    data.mkdir(parents=True)
    (data / "marker.txt").write_text("owned fixture", encoding="utf-8")
    backup.create_backup(paths, name="backup_a")
    backup.create_backup(paths, name="backup_z")
    return paths


@pytest.mark.parametrize("bad", [[], None, 0, {"files": None}])
def test_malformed_json_shape_is_skipped_without_stopping_retention(tmp_path, bad):
    paths = two_backups(tmp_path)
    root = backup.quick_scan_backup_root(paths)
    foreign = root / "foreign_shape"
    foreign.mkdir()
    (foreign / MANIFEST_NAME).write_text(json.dumps(bad), encoding="utf-8")
    receipt = backup.prune_backups(paths, keep=1)
    assert "foreign_shape" in receipt["skipped"]
    assert foreign.exists()
    assert receipt["removed"] == ["backup_a"] and receipt["kept"] == ["backup_z"]


@pytest.mark.parametrize("mutation", ["format_version", "owner_module", "workspace_root"])
def test_unknown_registry_version_or_foreign_owner_never_grants_delete(tmp_path, mutation):
    paths = two_backups(tmp_path)
    root = backup.quick_scan_backup_root(paths)
    registry_path = root / "owner_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if mutation == "format_version":
        registry[mutation] = "999.0.0"
    else:
        old = next(r for r in registry["records"] if r["name"] == "backup_a")
        old[mutation] = "foreign-module" if mutation == "owner_module" else str(tmp_path / "another-workspace")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    try:
        receipt = backup.prune_backups(paths, keep=1)
    except backup.QuickScanBackupError:
        receipt = None
    assert (root / "backup_a").exists(), "unknown registry/foreign record granted delete authority"
    if receipt is not None:
        assert "backup_a" in receipt["skipped"]


@pytest.mark.parametrize("dimension", ["segment", "period", "basis"])
def test_public_import_never_blends_incomparable_segments_periods_or_basis(tmp_path, dimension):
    paths = _bare_workspace(tmp_path / "workspace")
    observations = []
    for index, score in enumerate((2, 9)):
        extra, answer = {}, {}
        if dimension == "segment":
            extra = {"scope": "segment", "segment_id": "SEG_A" if index == 0 else "SEG_B"}
        elif dimension == "period":
            answer = {"period_start": "2025-01-01" if index == 0 else "2026-01-01", "period_end": "2025-12-31" if index == 0 else "2026-06-30", "basis": "current"}
        else:
            answer = {"period_start": "2026-01-01", "period_end": "2026-06-30", "basis": "current" if index == 0 else "normalized"}
        observations.append(_observation("OBS_BOUNDARY_" + dimension + str(index), entity_id=E01,
                                         question_id="IQS_LEG", field_id=FIELD, score=score,
                                         request_id="REQ_" + dimension + str(index), attempt_id="ATT_" + dimension + str(index),
                                         extra=extra, answer_extra=answer))
    _accepted(paths, observations)
    detail = build_entity_detail(paths, E01)
    profile = _score_fields(paths)[E01]
    result = _hit(paths, op=">=", value=8)
    (tmp_path / "boundary-result.json").write_text(json.dumps({"dimension": dimension, "accepted": 2,
                                                                  "input": observations, "detail": detail,
                                                                  "profile": profile, "query": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [f for group in detail["groups"] for f in group["fields"] if f["field_id"] == FIELD]
    assert {field["score"] for field in fields} == {2, 9}, "incomparable accepted values disappeared"
    judgment = profile["score_fields"][FIELD]
    assert judgment["score"] is None and judgment["status"] == "ambiguous"
    assert not result["rows"], "an unselected high-scoring variant entered the whitelist"


@pytest.mark.parametrize("kind", ["root", "parent"])
def test_backup_root_and_parent_junction_never_write_beyond_workspace(kind):
    fixture = Path(os.environ["IQS_SWR_WORK_ROOT"]) / "junction-fixtures" / kind
    paths = WorkspacePaths.from_root(fixture / "workspace")
    assert (fixture / "foreign/sentinel.txt").read_text() == "foreign-to-workspace but controller-owned"
    receipt, error = None, None
    try:
        receipt = backup.create_backup(paths, name="must_reject_junction_final")
    except backup.QuickScanBackupError as exc:
        error = str(exc)
    recorded = asdict(receipt) if is_dataclass(receipt) else receipt
    (fixture / "result.json").write_text(json.dumps({"kind": kind, "receipt": recorded, "error": error}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    assert receipt is None and error, "a workspace backup ancestor junction granted external write access"
    assert not list((fixture / "foreign").rglob(MANIFEST_NAME))
