"""Rebuild only the frozen public StockWiki intake files into a new IQS root."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[4]
    work = args.work_root.resolve()
    if work.exists() or not work.is_relative_to(project / "runs") or not work.name.startswith("sw-ready01-intake-"):
        raise ValueError("new exclusive IQS/runs/sw-ready01-intake-* root required")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    base, legacy = manifest["freeze_commit"], manifest["legacy_query_commit"]
    if not all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in (base, legacy)):
        raise ValueError("exact base and legacy commit IDs required")
    payloads = {}
    for row in manifest["export_allowlist"]:
        name = row["path"]
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or name in payloads:
            raise ValueError("unsafe or duplicate export path")
        revision, source = (legacy, "stockwiki/quick_scan_query.py") if name == "legacy_quick_scan_query.py" else (base, name)
        data = subprocess.run(["git", "show", revision + ":" + source], cwd=args.repo.resolve(),
                              check=True, capture_output=True).stdout
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("frozen Git file differs: " + name)
        payloads[name] = data
    for fixture in manifest.get("generated_inert_fixtures", []):
        if fixture["path"] != "config/llm_providers.yaml":
            raise ValueError("unknown fixture; no private config allowed")
        data = b"providers: []\n"
        if hashlib.sha256(data).hexdigest() != fixture["sha256"]:
            data = b"providers: []\r\n"
        if len(data) != fixture["bytes"] or hashlib.sha256(data).hexdigest() != fixture["sha256"]:
            raise ValueError("inert fixture hash mismatch")
        payloads[fixture["path"]] = data
    work.mkdir()
    for name, data in payloads.items():
        destination = work / "runtime" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (work / "export-manifest.json").write_bytes(args.manifest.read_bytes())
    print(json.dumps({"reconstructed_public_files_and_inert_fixture": len(payloads), "live": False}))


if __name__ == "__main__":
    main()
