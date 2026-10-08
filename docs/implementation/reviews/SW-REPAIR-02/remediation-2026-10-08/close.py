"""Verify the source and completed cleanup; bind final raw IQS acceptance artifacts."""
import json
import subprocess
import sys
from pathlib import Path

from prepare import INTAKE, IQS, OWN, RECEIVED, RESULT, SOURCE, git, save, sha

REVIEWS = Path(__file__).parent
INDEX = INTAKE / "delivery-index.json"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def main():
    if sys.argv[1:] == ["--index"]:
        rows = []
        for base in (INTAKE, REVIEWS):
            for path in sorted(base.rglob("*")):
                if not path.is_file() or path == INDEX:
                    continue
                assert not path.is_symlink() and path.resolve().is_relative_to(IQS.resolve())
                raw = path.read_bytes()
                if path.suffix == ".json":
                    json.loads(raw.decode("utf-8-sig"))
                rows.append({"path": path.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
        save(INDEX, {"schema": "iqs_sw_remediation_delivery_index/1", "status": "partial_verified_changes_requested",
             "result_commit": RESULT, "received_head": RECEIVED, "byte_domain": "exact archived raw bytes",
             "exclusions": ["this index", "mutable PWF/handoff-for-new-agent.md", ".gitattributes"],
             "count": len(rows), "items": rows})
        print(json.dumps({"files_bound": len(rows), "bytes": sum(row["bytes"] for row in rows)}))
        return
    if sys.argv[1:] == ["--check-staged"]:
        index = read(INDEX)
        for row in index["items"]:
            raw = subprocess.run(["git", "show", ":" + row["path"]], cwd=IQS, capture_output=True, check=True).stdout
            assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], row["path"]
        assert subprocess.run(["git", "show", ":" + INDEX.relative_to(IQS).as_posix()], cwd=IQS,
                              capture_output=True, check=True).stdout == INDEX.read_bytes()
        print(json.dumps({"staged_exact_files": index["count"], "index_exact": True}))
        return
    assert not sys.argv[1:]
    receipt = read(INTAKE / "cleanup-receipt.json")
    baseline = read(INTAKE / "cleanup-baseline.json")
    assert receipt["applied"] and receipt["files_deleted"] == 814 and len(baseline["directories"]) == 654
    assert not OWN.exists()
    rows = []
    for item in read(INTAKE / "worker/artifacts.json")["items"]:
        raw = (SOURCE / item["path"]).read_bytes()
        rows.append({"path": item["path"], "bytes": len(raw), "sha256": sha(raw),
                     "matched": len(raw) == item["bytes"] and sha(raw) == item["sha256"]})
    assert len(rows) == 69 and all(row["matched"] for row in rows)
    save(INTAKE / "artifact-verification-after.json", rows)
    after = {"head": git("rev-parse", "HEAD").decode().strip(),
             "branch": git("branch", "--show-current").decode().strip(),
             "status": git("status", "--porcelain=v1").decode().strip(),
             "artifact_matches": len(rows), "source_written_by_controller": False}
    assert after["head"] == RECEIVED and after["branch"] == "master" and after["status"] == ""
    save(INTAKE / "source-after.json", after)
    result = read(INTAKE / "verification/result.json")
    before = read(INTAKE / "verification/iqs-input-before.json")
    hashes = {relative: sha((IQS / relative).read_bytes()) for relative in before}
    assert before == hashes and result["snapshot_changes_after_tests"] == []
    result.update(cleanup_pending=False, cleanup={"applied": True, "files_deleted": 814,
                  "directories_deleted": 654, "junction_nodes_unlinked": 8, "root_absent": True},
                  source_after=after, iqs_inputs_after=hashes,
                  review="one_concentrated_independent_review_completed", no_gate_closed=True)
    save(INTAKE / "verification/result.json", result)
    print(json.dumps({"source_head_unchanged": True, "source_clean": True, "raw_artifacts_matched": 69,
                      "locked_iqs_input_files_unchanged": len(hashes), "private_root_absent": True,
                      "status": result["status"]}))


if __name__ == "__main__":
    main()
