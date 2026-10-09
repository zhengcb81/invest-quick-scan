"""Resume frozen checkpoint07 after Windows argv-length failure before staging.

Keep the original helper/index immutable; use the NUL manifest for writes and
batch blob reads for exact byte verification. No tests or external publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import checkpoint_07 as original

IQS, OUT, OWN = original.IQS, original.OUT, original.OWN
EXTRA = OUT / "checkpoint-07-resume.json"
MANIFEST = OWN / "checkpoint-paths-07-resume.nul"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_original():
    assert original.earlier.git("rev-parse", "HEAD").decode().strip() == original.BASELINE
    original.immutable_inputs()
    document = json.loads(original.INDEX.read_text("utf-8"))
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"], record["path"]
    return document


def prepare():
    validate_original()
    assert not original.earlier.git("diff", "--cached", "--name-only").strip()
    assert not EXTRA.exists() and not MANIFEST.exists()
    path = Path(__file__).resolve()
    raw = path.read_bytes()
    document = {
        "original_index_sha256": sha(original.INDEX.read_bytes()),
        "reason": "WinError206 in read-only diff argv before staging; frozen original helper/index unchanged",
        "records": [{"path": path.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)}],
        "whole_project_gates_closed": False, "source_published": False,
    }
    EXTRA.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = original.MANIFEST.read_bytes().split(b"\0")[:-1]
    selected += [path.relative_to(IQS).as_posix().encode(), EXTRA.relative_to(IQS).as_posix().encode()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"\0".join(selected) + b"\0")
    print(json.dumps({"selected": len(selected), "original_index_unchanged": True}))


def verify_blobs(ref, records):
    """Read exact Git blob bytes in one bounded process, without shell argv."""
    queries = [(ref + record["path"]).encode("utf-8") for record in records]
    assert all(b"\n" not in query and b"\r" not in query for query in queries)
    result = subprocess.run(["git", "cat-file", "--batch"], cwd=IQS,
        input=b"\n".join(queries) + b"\n", capture_output=True, check=True)
    cursor = 0
    for record in records:
        end = result.stdout.index(b"\n", cursor)
        header = result.stdout[cursor:end].split()
        assert len(header) == 3 and header[1] == b"blob", record["path"]
        size = int(header[2])
        raw = result.stdout[end + 1:end + 1 + size]
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"], record["path"]
        cursor = end + 1 + size
        assert result.stdout[cursor:cursor + 1] == b"\n"
        cursor += 1
    assert cursor == len(result.stdout)


def publish():
    original_doc = validate_original()
    assert not original.earlier.git("diff", "--cached", "--name-only").strip()
    extra = json.loads(EXTRA.read_text("utf-8"))
    assert sha(original.INDEX.read_bytes()) == extra["original_index_sha256"]
    for record in extra["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"]
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert len(selected) == len(set(selected))
    assert all(b"opencode" not in name and not name.startswith(b"runs/") for name in selected)
    tracked = set(original.earlier.git("ls-files", "-z").split(b"\0"))
    changed = set(original.earlier.git("diff", "--name-only", "-z").split(b"\0")) - {b""}
    assert changed <= set(selected), changed - set(selected)
    expected = (changed & set(selected)) | (set(selected) - tracked)
    original.earlier.git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    actual = set(original.earlier.git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1])
    assert actual == expected, (actual - expected, expected - actual)
    records = original_doc["records"] + extra["records"]
    for path in (original.INDEX, EXTRA):
        raw = path.read_bytes()
        records.append({"path": path.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    verify_blobs(":", records)
    original.earlier.git("diff", "--cached", "--check")
    original.earlier.git("commit", "-m", "feat: freeze external dispatch and native event recovery progress")
    original.earlier.git("push", "origin", "HEAD:master")
    assert original.earlier.git("rev-parse", "HEAD") == original.earlier.git("rev-parse", "origin/master")
    verify_blobs("HEAD:", records)
    original.earlier.source_unchanged()
    print(json.dumps({"commit": original.earlier.git("rev-parse", "HEAD").decode().strip(),
        "original_artifacts": len(original_doc["records"]), "selected": len(selected), "changed": len(actual),
        "verified_git_blobs": len(records), "status": original.earlier.git("status", "--porcelain=v1").decode("utf-8"),
        "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
