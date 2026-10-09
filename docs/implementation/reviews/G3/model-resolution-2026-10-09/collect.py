"""Freeze one reviewed iteration and verify source drift and write ownership."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/model-resolution-2026-10-09-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_once(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def git(source, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", source, *args])


def collect_published_eol(args, snapshot):
    # Importing this local controller must not create an extra unscoped file.
    sys.dont_write_bytecode = True
    import reconcile_eol as eol

    context = eol.verify_published_eol()
    original = context["manifest"]
    eol.require(args.label != eol.ORIGINAL_LABEL and args.test_label != original["test_label"],
                "Published EOL evidence requires new snapshot and test labels")
    names = {row["path"] for row in context["rows"]}
    verification = OUT / "verification" / args.test_label
    receipt_raw = eol.read(verification, "process.json")
    receipt = eol.decode(receipt_raw)
    eol.require(receipt["returncode"] == 0 and receipt["timeout"] is False
                and receipt["executed_source_unchanged"] is True
                and receipt["key_environment_removed"] is True
                and receipt["external_source_written"] is False,
                "New guarded execution was not successful and unchanged")
    eol.require(set(receipt["executed_source_hashes"]) == names,
                "New execution did not freeze exactly all 24 scoped source paths")
    old_verification = OUT / "verification" / original["test_label"]
    old_receipt = eol.decode(eol.read(old_verification, "process.json"))
    expected_command = []
    for token in old_receipt["command"]:
        if token.startswith("--basetemp="):
            token = "--basetemp=" + str(OWN / "tmp" / args.test_label)
        elif token.startswith("--junitxml="):
            token = "--junitxml=" + str(OWN / "logs/worker" / args.test_label / "junit.xml")
        expected_command.append(token)
    expected_tests = {
        "tests/unit/test_model_resolution.py", "tests/unit/test_llm_config.py",
        "tests/unit/test_llm_client.py", "tests/unit/test_llm_provider.py",
        "tests/unit/test_async_llm_provider.py", "tests/unit/test_llm_integration.py",
        "tests/unit/test_quick_scan_work_transport.py", "tests/unit/test_quick_scan_work_store.py",
        "tests/unit/test_quick_scan_cost_resolver.py", "tests/unit/test_quick_scan_c06_complete_seal.py",
        "tests/unit/test_quick_scan_result_outbox.py", "tests/unit/test_q10_delivery.py",
        "tests/integration/test_qa_c06_02_e2e.py", "tests/integration/test_qa_c06_02_subprocess_cli.py",
    }
    command_tests = [token for token in expected_command if token.startswith("tests/")]
    eol.require(len(command_tests) == 14 and set(command_tests) == expected_tests
                and "-k" not in expected_command
                and "pytest_asyncio.plugin" in expected_command
                and receipt["command"] == expected_command,
                "New execution is not the complete original affected 14-file command")
    changed = []
    for previous in context["rows"]:
        name = previous["path"]
        raw = context["source_raw"][name]
        executed = eol.read(verification, "executed-source/" + name)
        eol.require(raw == eol.read(OWN / "qa", name) == executed
                    and sha(raw) == receipt["executed_source_hashes"][name]
                    and sha(eol.normalized(raw)) == previous["normalized_lf_sha256"],
                    "New GREEN does not bind current published raw bytes: " + name)
        changed.append(dict(path=name, bytes=len(raw), sha256=sha(raw),
                            before_sha256=previous["before_sha256"],
                            normalized_lf_sha256=previous["normalized_lf_sha256"],
                            original_reviewed_sha256=previous["sha256"]))
    guard_raw = eol.read(OWN, "guard/sitecustomize.py")
    runner_raw = eol.read(Path(__file__).parent, "run_tests.py")
    eol.require(guard_raw == eol.read(verification, "executed-guard.py")
                == eol.read(old_verification, "executed-guard.py")
                and sha(guard_raw) == receipt["executed_guard_sha256"]
                == old_receipt["executed_guard_sha256"], "Execution guard changed")
    eol.require(runner_raw == eol.read(verification, "executed-runner.py")
                == eol.read(old_verification, "executed-runner.py"), "Guarded runner changed")
    evidence_files = []
    raw_evidence = {}
    classifications = {
        "process.json": "Guarded subprocess outcome and immutable 24-path execution SHA map",
        "junit.xml": "Complete affected 14-file test result; no selected subset",
        "stdout.log": "Raw pytest standard output; preserved without rewriting",
        "stderr.log": "Raw pytest standard error; preserved without rewriting",
        "executed-guard.py": "Exact executed audit guard; unchanged from original approved run",
        "executed-runner.py": "Exact executed isolated runner; unchanged from original approved run",
    }
    for name, classification in classifications.items():
        raw = eol.read(verification, name)
        raw_evidence[name] = raw
        evidence_files.append(dict(path="verification/" + args.test_label + "/" + name,
                                   bytes=len(raw), sha256=sha(raw), classification=classification))
    eol.require(raw_evidence["process.json"] == receipt_raw, "Execution receipt changed during collection")
    suites = ET.fromstring(raw_evidence["junit.xml"])
    totals = {key: sum(int(s.get(key, "0")) for s in suites.iter("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    eol.require(totals == context["approval"]["approved_junit_totals"]
                and totals == dict(tests=606, failures=0, errors=0, skipped=0),
                "New execution is not the complete 606-test GREEN")
    eol.require(b"606 passed" in raw_evidence["stdout.log"], "Raw stdout does not confirm full GREEN")
    network_path = eol.safe_path(OWN, "network-attempts.jsonl")
    network_raw = eol.read(OWN, "network-attempts.jsonl") if network_path.exists() else b""
    eol.require(not network_raw, "Network attempt recorded")
    ledger_path = eol.safe_path(OWN, "key-opens-v2.jsonl")
    ledger_raw = eol.read(OWN, "key-opens-v2.jsonl") if ledger_path.exists() else b""
    reads = [eol.decode(line) for line in ledger_raw.splitlines()]
    for row in reads:
        path = Path(row["path"])
        eol.require(row["inside_owned_root"] is True and path.is_absolute()
                    and path.is_relative_to(OWN) and path.resolve().is_relative_to(OWN),
                    "Configuration read is not classified inside the owned root")
        eol.safe_path(OWN, path.relative_to(OWN).as_posix())
    # Recheck current inputs before creating the new immutable snapshot.
    rechecked = eol.verify_published_eol()
    eol.require(rechecked["checkout"] == context["checkout"]
                and rechecked["source_raw"] == context["source_raw"]
                and rechecked["generated"] == context["generated"],
                "Source or logger changed during collection")
    eol.require(eol.read(OWN, "guard/sitecustomize.py") == guard_raw
                and (eol.read(OWN, "key-opens-v2.jsonl") if ledger_path.exists() else b"") == ledger_raw
                and (eol.read(OWN, "network-attempts.jsonl") if network_path.exists() else b"") == network_raw,
                "Guard ledger changed during collection")
    for name, raw in raw_evidence.items():
        eol.require(eol.read(verification, name) == raw, "Execution evidence changed: " + name)
    evidence = dict(schema="model_resolution_reviewed_source/1", source_baseline=context["baseline"],
                    published_eol=True, original_snapshot_label=eol.ORIGINAL_LABEL,
                    original_manifest_sha256=context["hashes"]["original_manifest_sha256"],
                    original_reviewed_source_sha256=context["hashes"]["original_manifest_sha256"],
                    original_approval_sha256=context["hashes"]["original_approval_sha256"],
                    original_publish_receipt_sha256=context["hashes"]["original_publish_receipt_sha256"],
                    eol_source_proof_sha256=context["proof_sha256"],
                    eol_copy_intent_sha256=context["copy_intent_sha256"],
                    original_evidence=context["hashes"],
                    changed_files=changed, unchanged_isolated_files=117,
                    original_external_source_unchanged_files=117,
                    protected_original_files=context["checkout"]["protected_files"],
                    published_source_state=context["checkout"], eol_changed_files=11,
                    test_label=args.test_label, verified_junit_totals=totals,
                    execution_evidence=evidence_files,
                    excluded_generated_test_output=context["generated"],
                    guard=dict(network_attempts=0, network_ledger_sha256=sha(network_raw),
                               key_environment_removed=True, synthetic_owned_config_reads=len(reads),
                               key_opens_ledger_sha256=sha(ledger_raw), executed_guard_sha256=sha(guard_raw),
                               executed_runner_sha256=sha(runner_raw),
                               proof_limit="Python audit guard, not a complete OS read sandbox"))
    for row in changed:
        eol.write_once(snapshot, "source/" + row["path"], context["source_raw"][row["path"]])
    eol.write_once(snapshot, "source.json", eol.json_bytes(evidence))
    eol.write_once(snapshot, "executed-guard.py", guard_raw)
    if ledger_path.exists():
        eol.write_once(snapshot, "key-opens-v2.jsonl", ledger_raw)
    print(json.dumps(dict(published_eol=True, changed=24, unchanged=117, source_files=137,
                          new_files=4, eol_changed_files=11, network_attempts=0,
                          synthetic_owned_config_reads=len(reads), junit_totals=totals)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--test-label", required=True)
    parser.add_argument("--published-eol", action="store_true")
    args = parser.parse_args()
    assert all(label.replace("-", "").replace("_", "").isalnum() for label in (args.label, args.test_label))
    snapshot = OUT / "snapshots" / args.label
    assert not snapshot.exists()
    if args.published_eol:
        collect_published_eol(args, snapshot)
        return
    scope = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))
    baseline = json.loads((OUT / "source-baseline.json").read_text("utf-8"))
    source = baseline["source"]
    assert git(source, "rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert git(source, "status", "--porcelain=v1").decode() == baseline["status"]
    before = {row["path"]: row for row in json.loads((OUT / "source-snapshot.json").read_text("utf-8"))}
    extra = json.loads((OUT / "extra-baseline.json").read_text("utf-8"))[0]
    extra_raw = (Path(source) / extra["path"]).read_bytes()
    assert sha(extra_raw.replace(b"\r\n", b"\n")) == sha(git(source, "show", baseline["head"] + ":" + extra["path"]).replace(b"\r\n", b"\n"))
    before[extra["path"]] = dict(extra, bytes=len(extra_raw), sha256=sha(extra_raw))
    allowed = set(scope["files"])
    actual_paths = {p.relative_to(OWN / "qa").as_posix() for p in (OWN / "qa").rglob("*") if p.is_file()}
    # The unchanged owner logger creates this single dated diagnostic file when
    # the isolated tests import it. It is test output, never publishable source.
    generated = actual_paths - (set(before) | allowed)
    assert generated <= {"logs/stock_qa_20261009.log"}, "Unclassified isolated files"
    generated_rows = []
    for name in sorted(generated):
        path = OWN / "qa" / name
        assert not path.is_symlink() and path.stat().st_nlink == 1
        raw = path.read_bytes()
        generated_rows.append(dict(path=name, bytes=len(raw), sha256=sha(raw),
                                   classification="Owner logger output from isolated tests; only deleted with exact OWN cleanup"))
    actual_paths -= generated
    assert set(before) <= actual_paths, "Protected source file missing"
    assert actual_paths <= set(before) | allowed, "Undeclared isolated source files"
    changed = []
    unchanged = 0
    for name in sorted(actual_paths):
        raw = (OWN / "qa" / name).read_bytes()
        previous = before.get(name)
        if previous and name != extra["path"]:
            assert sha((Path(source) / name).read_bytes()) == previous["sha256"], "External drift: " + name
        if previous and (sha(raw) == previous["sha256"] or
                         (name == ".gitignore" and raw.replace(b"\r\n", b"\n") == extra_raw.replace(b"\r\n", b"\n"))):
            unchanged += 1
            continue
        assert name in allowed, "Undeclared isolated edit: " + name
        if previous is None:
            assert not (Path(source) / name).exists(), "New source path already exists"
        write_once(snapshot / "source" / name, raw)
        changed.append(dict(path=name, bytes=len(raw), sha256=sha(raw),
                            before_sha256=previous["sha256"] if previous else None,
                            normalized_lf_sha256=sha(raw.replace(b"\r\n", b"\n"))))
    network = OWN / "network-attempts.jsonl"
    assert not network.exists() or not network.read_bytes(), "Network attempt recorded"
    ledger = OWN / "key-opens-v2.jsonl"
    reads = [json.loads(line) for line in ledger.read_text("utf-8").splitlines()] if ledger.exists() else []
    assert all(row["inside_owned_root"] and Path(row["path"]).is_relative_to(OWN) for row in reads)
    receipt = json.loads((OUT / "verification" / args.test_label / "process.json").read_text("utf-8"))
    assert receipt["returncode"] == 0 and not receipt["timeout"] and receipt["executed_source_unchanged"]
    assert all(sha((OWN / "qa" / name).read_bytes()) == digest for name, digest in receipt["executed_source_hashes"].items())
    evidence = dict(schema="model_resolution_reviewed_source/1", source_baseline=baseline,
                    changed_files=changed, unchanged_isolated_files=unchanged,
                    original_external_source_unchanged_files=len(before), test_label=args.test_label,
                    excluded_generated_test_output=generated_rows,
                    guard=dict(network_attempts=0, key_environment_removed=True,
                               synthetic_owned_config_reads=len(reads), proof_limit="Python audit guard, not a complete OS read sandbox"))
    write_once(snapshot / "source.json", (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode())
    write_once(snapshot / "executed-guard.py", (OWN / "guard/sitecustomize.py").read_bytes())
    if ledger.exists():
        write_once(snapshot / "key-opens-v2.jsonl", ledger.read_bytes())
    print(json.dumps(dict(changed=len(changed), unchanged=unchanged, source_files=len(before), network_attempts=0,
                          synthetic_owned_config_reads=len(reads))))


if __name__ == "__main__":
    main()
