"""Same SR02-4 damaged-input boundary, exercised through public backup functions."""
import json

import pytest
from acceptance_cases import two_backups
from stockwiki import quick_scan_backup as backup
from stockwiki.quick_scan_backup_manifest import MANIFEST_NAME


@pytest.mark.parametrize("operation", ["list", "prune"])
def test_non_utf8_foreign_manifest_is_invalid_and_does_not_stop_retention(tmp_path, operation):
    paths = two_backups(tmp_path)
    root = backup.quick_scan_backup_root(paths)
    foreign = root / "foreign_corrupt_bytes"
    foreign.mkdir()
    manifest = foreign / MANIFEST_NAME
    manifest.write_bytes(b"\xff")
    try:
        if operation == "list":
            result = backup.list_quick_scan_backups(paths)
        else:
            result = backup.prune_backups(paths, keep=1)
    except Exception as exc:
        (tmp_path / "corrupt-manifest-result.json").write_text(json.dumps({
            "operation": operation, "exception": type(exc).__name__, "message": str(exc),
            "foreign_unchanged": manifest.read_bytes() == b"\xff",
            "backup_a_exists": (root / "backup_a").exists(),
            "backup_z_exists": (root / "backup_z").exists()}, indent=2) + "\n", encoding="utf-8")
        raise
    (tmp_path / "corrupt-manifest-result.json").write_text(json.dumps({
        "operation": operation, "result": result, "foreign_unchanged": manifest.read_bytes() == b"\xff"},
        indent=2) + "\n", encoding="utf-8")
    assert manifest.read_bytes() == b"\xff"
    if operation == "list":
        row = next(row for row in result if row["name"] == foreign.name)
        assert row["manifest_shape"] == "invalid" and not row["complete"]
        assert (root / "backup_a").exists() and (root / "backup_z").exists()
    else:
        assert foreign.name in result["skipped"]
        assert result["removed"] == ["backup_a"] and result["kept"] == ["backup_z"]
