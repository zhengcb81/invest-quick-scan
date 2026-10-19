"""Lint module files against the catalog and published artifacts.

Catches drift that scripts/question_sets.py validate does not currently check:
catalog applies_when vs module text, module/catalog question counts, rubric
version mixing, redundant type critical flags, and missing/current artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "questions/catalog.json"
ARTIFACTS = ROOT / "questions/releases/artifacts"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def lint(root: Path = ROOT) -> dict:
    catalog = _load(root / "questions/catalog.json")
    errors, warnings = [], []
    for entry in catalog["modules"]:
        path = root / entry["path"]
        if not path.is_file():
            errors.append(f"{entry['id']}: module file missing: {entry['path']}")
            continue
        module = _load(path)
        if module.get("module_id") != entry.get("id"):
            errors.append(f"{entry['id']}: module_id mismatch ({module.get('module_id')})")
        if module.get("kind") != entry.get("kind"):
            errors.append(f"{entry['id']}: kind mismatch ({module.get('kind')})")
        if module.get("applies_when") != entry.get("applies_when"):
            errors.append(f"{entry['id']}: catalog applies_when drifted from module")
        count = len(module.get("questions") or [])
        if count != entry.get("question_count"):
            errors.append(f"{entry['id']}: question_count {count} != catalog {entry.get('question_count')}")
        versions = {q.get("rubric_version") for q in module.get("questions") or []}
        if len(versions) > 1:
            warnings.append(f"{entry['id']}: mixed rubric_version {sorted(versions)}")
        if module.get("kind") != "common":
            critical = [q["id"] for q in module.get("questions") or [] if q.get("critical")]
            if critical:
                warnings.append(f"{entry['id']}: explicit critical on non-common questions {critical}")
        artifact_dir = root / "questions/releases/artifacts" / entry["id"]
        current = [p for p in artifact_dir.glob(module["version"].replace(".", "_") + "-*.json")] if artifact_dir.is_dir() else []
        if not current:
            warnings.append(f"{entry['id']}: no published artifact for version {module['version']}")
        else:
            published = _load(current[0])
            if published != module:
                errors.append(f"{entry['id']}: module differs from published artifact {current[0].name}")
    return {"modules": len(catalog["modules"]), "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = lint(args.root)
    if args.json:
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for error in result["errors"]:
        print("ERROR", error)
    for warning in result["warnings"]:
        print("WARN", warning)
    print(json.dumps({"modules": result["modules"], "errors": len(result["errors"]),
                      "warnings": len(result["warnings"])}, ensure_ascii=False))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
