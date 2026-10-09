"""Archive the public-boundary slice without publishing the private producer."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import checkpoint_05 as previous

IQS, CONTROL, OUT, OWN = previous.IQS, previous.CONTROL, previous.OUT, previous.OWN
BASELINE = "033d77a53a3c9a9596b7f73a53e2af2a42bb3aa3"
INDEX = OUT / "checkpoint-index-06.json"
MANIFEST = OWN / "checkpoint-paths-06.nul"
LABELS = ("public-result-red-01", "public-result-green-01", "public-consumer-red-01", "public-consumer-green-01",
    "public-binding-red-01", "public-binding-green-01", "public-route-adjacent-red-01", "public-route-adjacent-red-02",
    "public-consumer-affected-green-01", "public-producer-affected-green-01", "public-consumer-collection-01",
    "public-consumer-affected-green-02", "native-cli-diagnostic-01", "native-cli-fixture-green-01")
ROOT_PATHS = (*previous.ROOT_PATHS, "scripts/stockqa_adapter.py", "scripts/routing.py",
    "schemas/quick_scan/route-decision.schema.json", "tests/test_external_search_result_contract.py",
    "tests/test_question_sets.py")


def sha(raw): return hashlib.sha256(raw).hexdigest()


def immutable_previous():
    previous.source_unchanged()
    previous.previous_unchanged()
    path = OUT / "checkpoint-index-05.json"
    assert previous.git("show", "HEAD:" + path.relative_to(IQS).as_posix()) == path.read_bytes()
    for record in json.loads(path.read_text("utf-8"))["records"]:
        assert sha((IQS / record["path"]).read_bytes()) == record["sha256"], record["path"]


def freeze_matches(label, field, root):
    process = json.loads((OUT / "verification" / label / "process.json").read_text("utf-8"))
    assert process["executed_source_unchanged"]
    for name, digest in process[field].items(): assert sha((root / name).read_bytes()) == digest, name
    return process


def fixture_only_change():
    old = (OUT / "verification/public-consumer-affected-green-02/executed-iqs-source/tests/test_question_sets.py").read_text("utf-8")
    new = (IQS / "tests/test_question_sets.py").read_text("utf-8")
    before, after = ast.parse(old), ast.parse(new)
    name = "test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline"
    original = [n for n in ast.walk(before) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(original) == 1
    replaced = 0
    for node in ast.walk(after):
        if isinstance(node, ast.ClassDef):
            for position, item in enumerate(node.body):
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    node.body[position] = copy.deepcopy(original[0]); replaced += 1
    assert replaced == 1 and ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False)


def prepare():
    assert previous.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not previous.git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    immutable_previous()
    freeze_matches("public-producer-affected-green-01", "executed_source_hashes", OWN / "qa")
    freeze_matches("native-cli-fixture-green-01", "executed_iqs_source_hashes", IQS)
    old = json.loads((OUT / "verification/public-consumer-affected-green-02/process.json").read_text("utf-8"))
    for name, digest in old["executed_iqs_source_hashes"].items():
        if name != "tests/test_question_sets.py": assert sha((IQS / name).read_bytes()) == digest, name
    fixture_only_change()
    scope = set(json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"])
    support = 0
    for record in json.loads((OUT / "source-snapshot.json").read_text("utf-8")):
        if record["path"] not in scope:
            assert sha((OWN / "qa" / record["path"]).read_bytes()) == record["sha256"]
            support += 1
    paths, batches = [], []
    for label in LABELS:
        root = OUT / "verification" / label
        process = json.loads((root / "process.json").read_text("utf-8"))
        assert process["executed_source_unchanged"]
        counts = None
        if (root / "junit.xml").is_file():
            suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
            assert suite is not None
            counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
        batches.append({"label": label, "returncode": process["returncode"], "timeout": process["timeout"],
            "wall_s": process["wall_s"], "diagnostic_only": process.get("diagnostic_only", False), "junit": counts})
        paths.extend(p for p in root.rglob("*") if p.is_file())
    indexed = {b["label"]: b for b in batches}
    assert indexed["public-producer-affected-green-01"]["junit"] == dict(tests=682, failures=0, errors=0, skipped=0)
    # pytest-subtests writes the 216 successful subtests as additional JUnit
    # cases: 111 collected methods + 216 subtests, while stdout keeps both counts.
    assert indexed["public-consumer-affected-green-02"]["junit"] == dict(tests=327, failures=1, errors=0, skipped=0)
    assert indexed["native-cli-fixture-green-01"]["junit"] == dict(tests=1, failures=0, errors=0, skipped=0)
    assert indexed["public-consumer-affected-green-01"]["timeout"] and indexed["public-consumer-affected-green-01"]["junit"] is None
    paths += [Path(__file__).resolve(), CONTROL / "run_consumer_tests.py", CONTROL / "public-result-interface.md"]
    records = []
    for path in sorted(paths):
        name, raw = path.relative_to(IQS).as_posix(), path.read_bytes()
        assert not path.is_symlink() and not previous.git("ls-files", "--", name).strip()
        if path.suffix == ".json": json.loads(raw)
        elif path.suffix == ".py": ast.parse(raw.decode("utf-8"), filename=name)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {"phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": previous.SOURCE, "production_schema_version": 8, "private_schema_version": 11,
        "public_result_version_private_producer": "1.1.0", "support_files_unchanged": support,
        "test_batches": batches, "consumer_targeted_fixture_only_change": True,
        "consumer_validation": "110 passed / 1 failed, followed by the corrected failed case passing; not one 111-pass run",
        "records": records, "pending": ["runner_cascade_dispatch", "async_projection", "two_stage_cross_lease",
            "mcp_each_http", "public_cli", "concentrated_review", "source_publish", "strict_cleanup"], "whole_project_gates_closed": False}
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    selected = [*ROOT_PATHS, *(r["path"] for r in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"".join(n.encode()+b"\0" for n in selected))
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches), "support": support}))


def publish():
    assert previous.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not previous.git("diff", "--cached", "--name-only").strip()
    immutable_previous()
    document = json.loads(INDEX.read_text("utf-8"))
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert all(b"opencode" not in n and not n.startswith(b"runs/") for n in selected)
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"]
    previous.git("add", "-f", "--pathspec-from-file="+str(MANIFEST), "--pathspec-file-nul")
    assert set(previous.git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1]) == set(selected)
    for record in document["records"]: assert sha(previous.git("show", ":"+record["path"])) == record["sha256"]
    assert previous.git("show", ":"+INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    previous.git("diff", "--cached", "--check")
    previous.git("commit", "-m", "feat: accept versioned external search result bindings")
    previous.git("push", "origin", "HEAD:master")
    assert previous.git("rev-parse", "HEAD") == previous.git("rev-parse", "origin/master")
    for record in document["records"]: assert sha(previous.git("show", "HEAD:"+record["path"])) == record["sha256"]
    previous.source_unchanged()
    print(json.dumps({"commit": previous.git("rev-parse", "HEAD").decode().strip(), "artifacts": len(document["records"]),
        "selected": len(selected), "status": previous.git("status", "--porcelain=v1").decode(), "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
