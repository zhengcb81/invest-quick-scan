"""Freeze one reviewed iteration and verify source drift and write ownership."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--test-label", required=True)
    args = parser.parse_args()
    assert all(label.replace("-", "").replace("_", "").isalnum() for label in (args.label, args.test_label))
    snapshot = OUT / "snapshots" / args.label
    assert not snapshot.exists()
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
