"""Freeze the final reviewed seven-file QA patch and guard receipts, never keys."""
import hashlib
import json
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/jr2-2026-10-08-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")
CHANGED = (
    "src/utils/quick_scan_result_outbox.py",
    "src/utils/quick_scan_work_store.py",
    "tests/unit/test_quick_scan_result_outbox.py",
    "tests/unit/test_q10_delivery.py",
    "tests/unit/test_quick_scan_work_store.py",
    "tests/unit/test_quick_scan_c06_complete_seal.py",
    "tests/integration/test_qa_c06_02_e2e.py",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def write_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main():
    baseline = json.loads((OUT / "source-baseline.json").read_text("utf-8"))
    assert git("rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert git("status", "--porcelain=v1").decode() == baseline["status"]
    original = json.loads((OUT / "source-snapshot.json").read_text("utf-8"))
    before = {row["path"]: row for row in original}
    assert len(before) == 136 and set(CHANGED) <= before.keys()
    actual = []
    for name, row in before.items():
        source_raw = (SOURCE / name).read_bytes()
        assert sha(source_raw) == row["sha256"], "Current external source drifted: " + name
        raw = (OWN / "qa" / name).read_bytes()
        if name not in CHANGED:
            assert sha(raw) == row["sha256"], "Undeclared isolated edit: " + name
            continue
        assert sha(raw) != row["sha256"], "Expected a concrete change: " + name
        write_once(OUT / "reviewed-source" / name, raw)
        actual.append(dict(path=name, bytes=len(raw), sha256=sha(raw),
                           before_sha256=row["sha256"], normalized_lf_sha256=sha(raw.replace(b"\r\n", b"\n"))))
    evidence = dict(schema="jr2_reviewed_source/1", source_baseline=baseline,
                    changed_files=actual, unchanged_isolated_files=129,
                    original_external_source_unchanged_files=136)
    write_once(OUT / "reviewed-source.json", (json.dumps(evidence, ensure_ascii=False, indent=2)+"\n").encode())
    for filename in ("network-attempts.jsonl", "key-opens.jsonl"):
        path = OWN / filename
        data = path.read_bytes() if path.exists() else b""
        assert not data, "Unexpected network/key-read audit: " + filename
    print(json.dumps(dict(reviewed_changes=len(actual), external_unchanged=136,
                          isolated_unchanged=129, network_attempts=0, configured_key_reads=0)))


if __name__ == "__main__":
    main()
