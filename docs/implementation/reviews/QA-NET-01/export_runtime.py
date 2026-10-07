"""Rebuild this acceptance export from exact Git revisions; never copy local secrets."""

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
    if not work.is_relative_to(project / "runs") or not work.name.startswith("qa-net01-intake-"):
        raise ValueError("work root must be a new private qa-net01-intake-* directory")
    if work.exists():
        raise ValueError("refusing an existing work root")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    base = manifest["freeze_commit"]
    final = manifest.get("remediation_code_commit")
    if not re.fullmatch(r"[0-9a-f]{40}", base) or not re.fullmatch(r"[0-9a-f]{40}", final or ""):
        raise ValueError("both exact commit revisions are required")
    entries = {row["path"]: (base, row) for row in manifest["export_allowlist"]}
    entries.update({name: (final, row) for name, row in manifest["overlay"].items()})
    # Validate and hash every read before creating the destination.
    payloads = {}
    for name, (revision, row) in entries.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise ValueError("unsafe manifest path")
        result = subprocess.run(
            ["git", "show", revision + ":" + name], cwd=args.repo.resolve(),
            check=True, capture_output=True,
        )
        data = result.stdout
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            # Git may normalize tracked CRLF source. Accept only the exact
            # byte spelling whose previously archived SHA proves equivalence.
            candidate = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if hashlib.sha256(candidate).hexdigest() != row["sha256"]:
                raise ValueError("Git content differs from executed export: " + name)
            data = candidate
        if len(data) != row["bytes"]:
            raise ValueError("byte length mismatch: " + name)
        payloads[name] = data
    work.mkdir()
    runtime = work / "runtime"
    for name, data in payloads.items():
        destination = runtime / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (work / "export-manifest.json").write_bytes(args.manifest.read_bytes())
    print(json.dumps({"exported_files": len(payloads), "private_work_root": str(work), "live": False}))


if __name__ == "__main__":
    main()
