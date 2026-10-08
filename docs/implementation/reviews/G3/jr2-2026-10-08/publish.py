"""Explicit --apply guarded publish after the concentrated review; no Git writes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")
ALLOWED = {
    "src/utils/quick_scan_result_outbox.py",
    "src/utils/quick_scan_work_store.py",
    "tests/unit/test_quick_scan_result_outbox.py",
    "tests/unit/test_q10_delivery.py",
    "tests/unit/test_quick_scan_work_store.py",
    "tests/unit/test_quick_scan_c06_complete_seal.py",
    "tests/integration/test_qa_c06_02_e2e.py",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    review = json.loads((OUT / "approval-for-publish.json").read_text("utf-8"))
    label = review["snapshot_label"]
    assert label.replace("-", "").replace("_", "").isalnum()
    snapshot = OUT / "snapshots" / label
    frozen = json.loads((snapshot / "source.json").read_text("utf-8"))
    rows = frozen["changed_files"]
    assert {row["path"] for row in rows} == ALLOWED and len(rows) == 7
    assert review["approved_for_seven_file_jr2_publish"] is True
    assert review["reviewed_source_sha256"] == sha((snapshot / "source.json").read_bytes())
    baseline = frozen["source_baseline"]
    assert git("rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert git("status", "--porcelain=v1").decode() == baseline["status"], "Reconcile concurrent edits before publishing"
    prepared = []
    for row in rows:
        path = (SOURCE / row["path"]).resolve()
        assert path == SOURCE / row["path"] and path.is_relative_to(SOURCE) and path.is_file() and not path.is_symlink()
        assert sha(path.read_bytes()) == row["before_sha256"], "External file changed"
        raw = (snapshot / "source" / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Reviewed bytes changed"
        prepared.append((path, raw))
    if args.apply:
        for path, raw in prepared:
            # Recheck each file immediately before its exact approved replacement.
            row = next(row for row in rows if SOURCE / row["path"] == path)
            assert sha(path.read_bytes()) == row["before_sha256"], "Pre-write drift"
            path.write_bytes(raw)
        for path, raw in prepared:
            assert path.read_bytes() == raw
    receipt = dict(schema="jr2_publish_receipt/1", applied=args.apply,
                   published_files=7 if args.apply else 0, expected_files=7,
                   baseline_head=baseline["head"], network_calls=0,
                   exact_reviewed_sha256=review["reviewed_source_sha256"])
    target = OUT / ("publish-receipt.json" if args.apply else "publish-dry-run.json")
    with target.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
