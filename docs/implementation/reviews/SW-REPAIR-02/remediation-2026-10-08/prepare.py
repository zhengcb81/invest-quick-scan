"""Read-only freeze of the second SW delivery; all executable bytes stay in IQS."""
import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

IQS = Path(__file__).resolve().parents[5]
SOURCE = Path("C:/Users/郑曾波/Projects/StockWiki")
RESULT = "c83c148af35407a5ae01072314ba9bd17e59b3d9"
RECEIVED = "1831a73b37a3ed1b67d3556f6425ed2b52594a24"
OWN = IQS / "runs/sw-repair-remediation-2026-10-08-01"
INTAKE = IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08-remediation"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args, stdin=None):
    return subprocess.run(["git", "-C", str(SOURCE), *args], input=stdin,
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
                          capture_output=True, check=True, timeout=60).stdout


def blobs(ref, paths):
    stream = io.BytesIO(git("cat-file", "--batch", stdin=("".join(ref + ":" + p + "\n" for p in paths)).encode("utf-8")))
    result = {}
    for path in paths:
        header = stream.readline().decode("utf-8").strip().split()
        if header[-1] == "missing":
            result[path] = None
        else:
            assert len(header) == 3 and header[1] == "blob"
            data = stream.read(int(header[2]))
            assert stream.read(1) == b"\n"
            result[path] = data
    assert not stream.read()
    return result


def main():
    assert git("rev-parse", "HEAD").decode().strip() == RECEIVED
    assert not git("status", "--porcelain=v1")
    post_paths = git("diff", "--name-only", RESULT, RECEIVED).decode().splitlines()
    assert all(p.startswith("docs/handoff/SW-REPAIR-02/") for p in post_paths), "Post-result runtime drift"
    OWN.mkdir(parents=True, exist_ok=False)
    INTAKE.mkdir(parents=True, exist_ok=False)
    save(INTAKE / "source-baseline.json", {"head": RECEIVED, "branch": "master", "status": "",
         "result_commit": RESULT, "post_result_paths": post_paths, "source_written": False})
    manifest_path = SOURCE / "docs/handoff/SW-REPAIR-02/artifacts.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    paths = [item["path"] for item in manifest["items"]]
    assert len(paths) == len(set(paths)) == 69
    received_blobs, result_blobs = blobs(RECEIVED, paths), blobs(RESULT, paths)
    checks = []
    for item in manifest["items"]:
        relative = PurePosixPath(item["path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        source = SOURCE.joinpath(*relative.parts)
        assert not source.is_symlink() and source.resolve().is_relative_to(SOURCE.resolve())
        raw = source.read_bytes()
        blob = received_blobs[item["path"]]
        old = result_blobs[item["path"]]
        assert blob is not None
        row = {"path": item["path"], "bytes": len(raw), "worktree_sha256": sha(raw),
               "raw_matched": len(raw) == item["bytes"] and sha(raw) == item["sha256"],
               "received_git_blob_sha256": sha(blob), "received_git_bytes": len(blob),
               "git_matched": sha(blob) == item["git_blob_sha256"] and len(blob) == item["git_blob_bytes"],
               "exact": raw == blob, "eol_equivalent": raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"),
               "result_commit_has_path": old is not None,
               "result_commit_blob_matches_declared": old is not None and sha(old) == item["git_blob_sha256"]}
        checks.append(row)
        if item["path"].startswith("docs/handoff/SW-REPAIR-02/"):
            target = INTAKE / "worker" / Path(*relative.parts[3:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    (INTAKE / "worker/artifacts.json").write_bytes(manifest_path.read_bytes())
    save(INTAKE / "artifact-verification.json", checks)
    assert all(row["raw_matched"] and row["git_matched"] and row["eol_equivalent"] for row in checks)
    entries = []
    with tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", RESULT, "stockwiki", "tests", "pyproject.toml")), mode="r:") as archive:
        for member in archive.getmembers():
            relative = PurePosixPath(member.name)
            assert not relative.is_absolute() and ".." not in relative.parts and (member.isfile() or member.isdir())
            if not member.isfile():
                continue
            raw = archive.extractfile(member).read()
            target = OWN / "runtime" / Path(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            entries.append({"path": str(relative), "bytes": len(raw), "sha256": sha(raw)})
    legacy = git("show", "9f552a67:stockwiki/quick_scan_query.py")
    (OWN / "runtime/legacy_quick_scan_query.py").write_bytes(legacy)
    entries.append({"path": "legacy_quick_scan_query.py", "bytes": len(legacy), "sha256": sha(legacy)})
    save(OWN / "export-manifest.json", entries)
    save(INTAKE / "verification/source-snapshot.json", entries)
    inert = (IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08/verification/llm_providers.inert.yaml").read_bytes()
    (OWN / "runtime/config").mkdir()
    (OWN / "runtime/config/llm_providers.yaml").write_bytes(inert)
    (INTAKE / "verification/llm_providers.inert.yaml").write_bytes(inert)
    save(INTAKE / "verification/environment-fixture.json", {"kind": "generated_inert_not_source", "keys": 0,
         "providers": [], "bytes": len(inert), "sha256": sha(inert)})
    for folder in ("temp", "logs", "guard", "browser-profile"):
        (OWN / folder).mkdir()
    original = IQS / "docs/implementation/reviews/SW-REPAIR-02/acceptance_cases.py"
    cases = OWN / "acceptance_cases.py"
    cases.write_bytes(original.read_bytes())
    (INTAKE / "verification/original-12-cases-executed.py").write_bytes(cases.read_bytes())
    frozen = IQS / "docs/implementation/reviews/SW-READY-01/acceptance_cases.py"
    (INTAKE / "verification/original-7-cases-executed.py").write_bytes(frozen.read_bytes())
    input_lock = IQS / "docs/implementation/parallel-lanes/packages/2026-10-07-wave2/inputs.lock.json"
    read_inputs = [input_lock, original, frozen, IQS / "docs/implementation/reviews/SW-REPAIR-02/remediation-2026-10-08.md"]
    lock = json.loads(input_lock.read_text("utf-8"))
    read_inputs += [IQS / row["path"] for group in ("iqs_inputs", "working_tree_snapshots") for row in lock[group]]
    save(INTAKE / "verification/iqs-input-before.json", {p.relative_to(IQS).as_posix(): sha(p.read_bytes()) for p in read_inputs})
    print(json.dumps({"artifacts": len(checks), "raw_and_received_blob_matched": True,
         "eol_differences": sum(not row["exact"] for row in checks), "source_snapshot_files": len(entries),
         "artifact_result_commit_missing": sum(not row["result_commit_has_path"] for row in checks),
         "artifact_result_commit_different": sum(row["result_commit_has_path"] and not row["result_commit_blob_matches_declared"] for row in checks)}))


if __name__ == "__main__":
    main()
