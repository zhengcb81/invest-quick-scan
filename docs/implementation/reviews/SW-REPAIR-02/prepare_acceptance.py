"""Freeze this intake without executing or modifying the source repository."""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

IQS = Path(__file__).resolve().parents[4]
SOURCE = Path("C:/Users/郑曾波/Projects/StockWiki")
COMMIT = "9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f"
OWN = IQS / "runs/sw-repair-2026-10-08-01"
INTAKE = IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, body) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(SOURCE), *args], check=True,
                          capture_output=True).stdout


def main() -> None:
    OWN.mkdir(parents=True, exist_ok=False)
    INTAKE.mkdir(parents=True, exist_ok=False)
    before = {"head": git("rev-parse", "HEAD").decode().strip(),
              "status": git("status", "--porcelain=v1").decode(),
              "branch": git("branch", "--show-current").decode().strip(),
              "result_commit": COMMIT}
    save(INTAKE / "source-baseline.json", before)
    manifest_path = SOURCE / "docs/handoff/SW-REPAIR-02/artifacts.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verified = []
    for item in manifest["items"]:
        relative = PurePosixPath(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe artifact path")
        source = SOURCE.joinpath(*relative.parts)
        if not source.resolve().is_relative_to(SOURCE.resolve()):
            raise ValueError("artifact leaves source")
        data = source.read_bytes()
        match = len(data) == item["bytes"] and sha(data) == item["sha256"]
        verified.append({**item, "actual_bytes": len(data), "actual_sha256": sha(data),
                         "matched": match})
        if str(relative).startswith("docs/handoff/SW-REPAIR-02/"):
            target = INTAKE / "worker" / Path(*relative.parts[3:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    (INTAKE / "worker/artifacts.json").write_bytes(manifest_path.read_bytes())
    save(INTAKE / "artifact-verification.json", verified)
    if not all(item["matched"] for item in verified):
        raise ValueError("artifact mismatches: see saved verification")
    archive = git("archive", "--format=tar", COMMIT, "stockwiki", "tests", "pyproject.toml")
    entries = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        for member in bundle.getmembers():
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or not (member.isdir() or member.isfile()):
                raise ValueError("unsafe Git archive entry")
            if member.isdir():
                continue
            payload = bundle.extractfile(member).read()
            target = OWN / "runtime" / Path(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            entries.append({"path": str(relative), "bytes": len(payload), "sha256": sha(payload)})
    legacy = git("show", "9f552a67:stockwiki/quick_scan_query.py")
    (OWN / "runtime/legacy_quick_scan_query.py").write_bytes(legacy)
    entries.append({"path": "legacy_quick_scan_query.py", "bytes": len(legacy), "sha256": sha(legacy)})
    save(OWN / "export-manifest.json", entries)
    save(INTAKE / "verification/source-snapshot.json", entries)
    inert = (IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08/verification/llm_providers.inert.yaml").read_bytes()
    (OWN / "runtime/config").mkdir()
    (OWN / "runtime/config/llm_providers.yaml").write_bytes(inert)
    save(INTAKE / "verification/environment-fixture.json", {
        "path": "config/llm_providers.yaml", "kind": "generated_inert_environment_not_git_source",
        "bytes": len(inert), "sha256": sha(inert), "providers": [], "keys": 0})
    boundaries = []
    for item in verified:
        if not item["path"].startswith("docs/handoff/"):
            blob = git("show", COMMIT + ":" + item["path"])
            actual = (SOURCE / item["path"]).read_bytes()
            boundaries.append({"path": item["path"], "git_sha256": sha(blob),
                               "worktree_sha256": sha(actual), "exact": blob == actual,
                               "eol_equivalent": blob.replace(b"\r\n", b"\n") == actual.replace(b"\r\n", b"\n")})
    save(INTAKE / "git-byte-boundary.json", boundaries)
    if not all(item["eol_equivalent"] for item in boundaries):
        raise ValueError("result source differs beyond EOL")
    for name in ("temp", "logs", "guard", "browser-profile"):
        (OWN / name).mkdir()
    print(json.dumps({"artifact_count": len(verified), "artifact_matches": sum(x["matched"] for x in verified),
                      "source_file_count": len(entries), "eol_differences": sum(not x["exact"] for x in boundaries),
                      "head": before["head"], "source_clean": before["status"] == "", "own_root": str(OWN)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
