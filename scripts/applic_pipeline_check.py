"""Cross-check a composed bank manifest against the applicability snapshot.

The composition pipeline (question_sets compose) picks modules from a
hand-written profile; the applicability snapshot (APPLIC-RESOLVE-14) holds the
machine-judged four-state cell per (entity, module). These two have never been
reconciled. This tool reports where they disagree, classified, without changing
either side.

Exit codes: 0 all agree, 2 disagreements found, 3 data error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

APPLICABLE = "applicable"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fail(message: str) -> tuple[int, dict]:
    """Data errors return (3, report) so tests and main share one path."""
    return 3, {"status": "data_error", "error": message}


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise SystemExit(_fail(f"unreadable or invalid JSON: {path} ({error})")[0])


def compare(manifest_path: Path, snapshot_path: Path) -> tuple[int, dict]:
    manifest = _load(manifest_path)
    snapshot = _load(snapshot_path)

    questions = manifest.get("questions")
    modules = manifest.get("modules")
    profile = manifest.get("profile") or {}
    entity_id = profile.get("entity_id")
    if not isinstance(questions, list) or not questions:
        return _fail(f"manifest has no questions: {manifest_path}")
    if not isinstance(modules, list) or not modules:
        return _fail(f"manifest has no modules: {manifest_path}")
    if not isinstance(entity_id, str) or not entity_id:
        return _fail(f"manifest profile has no entity_id: {manifest_path}")

    cells = snapshot.get("cells")
    inputs = snapshot.get("inputs") or {}
    if not isinstance(cells, list):
        return _fail(f"snapshot has no cells: {snapshot_path}")

    entity_cells = {}
    for cell in cells:
        cid = cell.get("entity_id")
        mid = cell.get("module_id")
        if not isinstance(cid, str) or not isinstance(mid, str):
            return _fail(f"snapshot cell missing entity_id/module_id: {snapshot_path}")
        if cid == entity_id:
            entity_cells[mid] = cell
    if not entity_cells:
        return _fail(
            f"snapshot has no cells for entity {entity_id} — manifest and snapshot "
            f"cover different entities ({manifest_path} vs {snapshot_path})"
        )

    composed = set(modules)
    snap_modules = set(entity_cells)
    rows_checked = len(composed | snap_modules)

    disagreements = []
    unaligned = []
    agree = 0
    for module_id in sorted(composed | snap_modules):
        cell = entity_cells.get(module_id)
        in_composed = module_id in composed
        if cell is None:
            unaligned.append({
                "module_id": module_id,
                "category": "composed_module_missing_in_snapshot",
                "detail": "manifest selects a module the snapshot has no axis for",
            })
            continue
        if not in_composed:
            if cell.get("state") == APPLICABLE:
                disagreements.append({
                    "module_id": module_id,
                    "category": "snapshot_applicable_not_composed",
                    "snapshot_state": cell.get("state"),
                    "basis_kind": (cell.get("basis") or {}).get("kind"),
                    "reason": (cell.get("basis") or {}).get("reason"),
                })
            else:
                # Not composed and not applicable: both sides effectively
                # exclude it — counted as agreement.
                agree += 1
            continue
        if cell.get("state") == APPLICABLE:
            agree += 1
        else:
            disagreements.append({
                "module_id": module_id,
                "category": "composed_but_not_applicable",
                "snapshot_state": cell.get("state"),
                "basis_kind": (cell.get("basis") or {}).get("kind"),
                "reason": (cell.get("basis") or {}).get("reason"),
            })

    categories = {}
    for item in disagreements:
        categories[item["category"]] = categories.get(item["category"], 0) + 1

    result = {
        "status": "ok" if not disagreements and not unaligned else "disagreement",
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "snapshot_path": str(snapshot_path),
        "snapshot_sha256": _sha256(snapshot_path),
        "manifest_identity": {
            "package_id": manifest.get("module_package_id"),
            "release_id": manifest.get("module_release_id"),
            "mode": manifest.get("mode"),
            "template_version": manifest.get("template_version"),
            "entity_id": entity_id,
            "company": profile.get("company"),
            "as_of": profile.get("as_of"),
            "profile_fields": {
                "company_type": profile.get("company_type"),
                "industry_modules": profile.get("industry_modules"),
                "stage": profile.get("stage"),
                "overlays": profile.get("overlays"),
                "diagnostic_modules": profile.get("diagnostic_modules"),
            },
        },
        "snapshot_identity": {
            "snapshot_id": snapshot.get("snapshot_id"),
            "inputs": inputs,
        },
        "rows_checked": rows_checked,
        "summary": {
            "agree": agree,
            "snapshot_only": categories.get("snapshot_applicable_not_composed", 0),
            "composed_not_applicable": categories.get("composed_but_not_applicable", 0),
            **categories,
        },
        "disagreements": disagreements,
        "unaligned": unaligned,
    }
    code = 2 if disagreements or unaligned else 0
    return code, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args(argv)
    code, result = compare(args.manifest, args.snapshot)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
