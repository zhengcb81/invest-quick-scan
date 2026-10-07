"""Read-only shape and declared-scope check for parallel harness handoffs.

This cannot authenticate claims in a handoff. The coordinator must compare
commits, hashes, authorization, test output, and owner-produced artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
LANE_DIR = ROOT / "docs" / "implementation" / "parallel-lanes"
MAX_INPUT_BYTES = 1_048_576
SCOPE = "handoff_shape_and_declared_scope_only"


class DuplicateKeyError(ValueError):
    pass


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _outcome(package_id: str, code: str | None = None) -> tuple[int, dict]:
    if code is None:
        return 0, {"status": "valid", "package_id": package_id,
                   "validation_scope": SCOPE, "errors": []}
    return 2, {"status": "invalid", "package_id": package_id,
               "validation_scope": SCOPE, "errors": [{"code": code}]}


def _normal_path(value: str) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if ".." in path.parts or "." in path.parts or normalized.startswith("//"):
        return None
    # Drive-relative paths (C:foo) are ambiguous on Windows.
    if len(normalized) >= 2 and normalized[1] == ":" and not normalized[2:3] == "/":
        return None
    return path.as_posix().casefold().rstrip("/")


def _within(path: str, scope: str) -> bool:
    return path == scope or path.startswith(scope + "/")


def validate_handoff(input_path: Path, package_id: str,
                     catalog_path: Path | None = None) -> tuple[int, dict]:
    package_dir = (LANE_DIR / "packages").resolve()
    selected = catalog_path if catalog_path is not None else package_dir / "manifest.json"
    try:
        selected = selected.resolve()
    except (OSError, RuntimeError):
        return _outcome(package_id, "catalog_unreadable")
    # A catalog selects known local package instructions, never an arbitrary
    # private file supplied in a handoff. This remains a shape-only check.
    if not selected.is_relative_to(package_dir):
        return _outcome(package_id, "catalog_outside_package_directory")
    try:
        with selected.open("rb") as handle:
            raw_catalog = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        return _outcome(package_id, "catalog_unreadable")
    if len(raw_catalog) > MAX_INPUT_BYTES:
        return _outcome(package_id, "catalog_too_large")
    try:
        catalog = json.loads(raw_catalog.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError):
        return _outcome(package_id, "catalog_invalid")
    entries = catalog.get("packages") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        return _outcome(package_id, "catalog_invalid")
    packages = {}
    for entry in entries:
        if not isinstance(entry, dict) or any(
            not isinstance(entry.get(key), str) or not entry[key]
            for key in ("id", "lane_id", "write_scope", "readiness")
        ):
            return _outcome(package_id, "catalog_invalid")
        ids = entry.get("task_ids")
        if not isinstance(ids, list) or any(not isinstance(value, str) or not value for value in ids):
            return _outcome(package_id, "catalog_invalid")
        if entry["id"] in packages:
            return _outcome(package_id, "catalog_invalid")
        packages[entry["id"]] = entry
    package = packages.get(package_id)
    if package is None:
        return _outcome(package_id, "unknown_package_id")

    try:
        raw = input_path.read_bytes()
    except OSError:
        return _outcome(package_id, "input_unreadable")
    if len(raw) > MAX_INPUT_BYTES:
        return _outcome(package_id, "input_too_large")
    try:
        report = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except DuplicateKeyError:
        return _outcome(package_id, "duplicate_json_key")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _outcome(package_id, "invalid_json")

    schema = json.loads((LANE_DIR / "handoff.schema.json").read_text(encoding="utf-8"))
    if not Draft202012Validator(schema).is_valid(report):
        return _outcome(package_id, "schema_invalid")
    if report["package_id"] != package_id:
        return _outcome(package_id, "package_mismatch")
    if report["lane_id"] != package["lane_id"]:
        return _outcome(package_id, "lane_mismatch")
    if set(report["scope"]["task_ids"]) != set(package["task_ids"]):
        return _outcome(package_id, "task_scope_mismatch")

    scope = report["scope"]
    changed = scope["changed_paths"]
    if package["readiness"].startswith("read_only") and (changed or report["verification"]["external_writes"]):
        return _outcome(package_id, "read_only_package_changed_files")
    if scope["out_of_scope_writes"]:
        return _outcome(package_id, "out_of_scope_writes_reported")

    owner_root = _normal_path(package["write_scope"])
    authorized = [_normal_path(path) for path in scope["authorized_paths"]]
    if owner_root is None or any(path is None for path in authorized):
        return _outcome(package_id, "declared_scope_invalid")
    for value in changed:
        path = _normal_path(value)
        if path is None:
            return _outcome(package_id, "changed_path_out_of_scope")
        if ":" in path[:3]:
            if not _within(path, owner_root):
                return _outcome(package_id, "changed_path_out_of_scope")
            rel = path[len(owner_root):].lstrip("/")
        else:
            rel = path
        if not any(_within(rel, allowed) or _within(path, allowed) for allowed in authorized):
            return _outcome(package_id, "changed_path_out_of_scope")

    if any(root["created"] and not root["cleaned"] for root in report["verification"]["temporary_roots"]):
        return _outcome(package_id, "temporary_root_not_cleaned")
    return _outcome(package_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--catalog", type=Path,
                        help="Package catalog under this repository's parallel-lanes/packages directory.")
    args = parser.parse_args(argv)
    code, result = validate_handoff(args.input, args.package_id, args.catalog)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
