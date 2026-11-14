"""One concentrated EVID R1 acceptance in an owned, offline copy.

Never run in the source repository. Each action/result name is single-use.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("acceptance_helpers", HERE / "acceptance_run.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
ROOT = helper.ROOT
SOURCE = ROOT.parent / "iqs-evidence-lab"
WORK = ROOT / "runs/p114er1a"
LAB = WORK / "evid"
INTAKE = ROOT / "docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01"
EXPECTED = "70498e40918ea28476b8d0185a0294be7bbb6e0e"
PRODUCT = "44aa20402125b23de151e2c7c0f4abff7082a7cb"


def git_state():
    results = []
    for args in (["rev-parse", "HEAD"], ["branch", "--show-current"],
                 ["status", "--porcelain=v1", "-uall"], ["ls-files", "-z"],
                 ["remote", "-v"], ["diff", "--name-only", PRODUCT, "HEAD"]):
        proc = subprocess.run(["git", "-C", str(SOURCE), *args], capture_output=True,
                              text=True, encoding="utf-8", timeout=30)
        if proc.returncode:
            raise RuntimeError(proc.stderr)
        results.append({"args": args, "stdout": proc.stdout, "exit_code": proc.returncode})
    return results


def freeze():
    assert not WORK.exists() and not INTAKE.exists()
    state = git_state()
    assert state[0]["stdout"].strip() == EXPECTED
    assert all(line.startswith("?? .codegraph/") for line in state[2]["stdout"].splitlines())
    # Handoff-only commits do not silently select a new product version.
    assert all(p.startswith("docs/handoff/") or p in {"task_plan.md", "progress.md", "findings.md"}
               for p in state[5]["stdout"].splitlines())
    inputs = helper.inspect_inputs()
    files = state[3]["stdout"].split("\0")[:-1]
    for rel in files:
        part = Path(rel)
        assert not part.is_absolute() and ".." not in part.parts
        assert not any(s.lower() in {".git", ".codegraph", ".env", "secrets", "credentials"}
                       for s in part.parts)
        helper.safe(SOURCE / part)
    WORK.mkdir(parents=True)
    INTAKE.mkdir(parents=True)
    LAB.mkdir()
    helper.write(INTAKE / "source-git-before.json", state)
    rows = []
    for rel in files:
        src, dst = SOURCE / rel, LAB / rel
        blob = src.read_bytes()
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("xb") as stream:
            stream.write(blob)
        sha = helper.digest(src)
        assert helper.digest(dst) == sha
        rows.append({"path": rel, "bytes": len(blob), "sha256": sha})
    artifacts = json.loads((LAB / "docs/handoff/EVID-REF-02/remediation-01/artifacts.json").read_text(encoding="utf-8"))
    checks = []
    for item in artifacts["artifacts"]:
        part = Path(item["path"])
        assert not part.is_absolute() and ".." not in part.parts
        helper.safe(SOURCE / part)
        checks.append({"path": item["path"], "matches": helper.digest(SOURCE / part) == item["sha256"]
                       and (SOURCE / part).stat().st_size == item["bytes"]})
    helper.write(INTAKE / "source-freeze.json", {"at": helper.now(), "head": EXPECTED,
                 "product_commit": PRODUCT, "files": rows, "artifacts": checks, "inputs": inputs,
                 "external_source_written": False})
    for name in ("guard", "guard-logs", "temp"):
        (WORK / name).mkdir()
    (WORK / "guard/sitecustomize.py").write_text('''import os, socket, json
from pathlib import Path
def deny(*a, **k):
    p = Path(os.environ['IQS_ACCEPT_GUARD_LOG']) / ('attempt-' + str(os.getpid()) + '.jsonl')
    with p.open('a', encoding='utf-8') as f: f.write(json.dumps({'pid':os.getpid(),'event':'blocked_socket_attempt'})+'\\n')
    raise OSError('IQS EVID R1 acceptance: offline')
socket.socket.connect=deny
socket.socket.connect_ex=deny
socket.create_connection=deny
socket.getaddrinfo=deny
''', encoding="utf-8")
    helper.write(WORK / "ownership.json", {"root": str(WORK), "controller": str(Path(__file__).resolve()), "at": helper.now()})
    print(json.dumps({"files": len(rows), "artifacts": len(checks), "bad_artifacts": [x for x in checks if not x["matches"]], "inputs": inputs}))


def environment():
    keep = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "SYSTEMDRIVE"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update(TEMP=str(WORK / "temp"), TMP=str(WORK / "temp"), TMPDIR=str(WORK / "temp"),
               PYTHONPATH=os.pathsep.join([str(WORK / "guard"), str(LAB / "src")]),
               PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", IQS_ACCEPT_GUARD_LOG=str(WORK / "guard-logs"),
               IQS_ROOT=str(ROOT), IQS_EVIDENCE_LAB_IQS_ROOT=str(ROOT),
               IQS_EVIDENCE_LAB_RECEIPT_DIR=str(LAB / ".acceptance-receipts"))
    return env


def prepare_relocated_inputs():
    """Synthetic relocation fixture; originals/locks are never edited.

    Native CLI rejects the unmodified pack after relocation. To discriminate
    other defects, copy verified input bytes and rewrite ONLY root locations
    in a separately labelled lock; update its dependent pack digest.
    """
    import copy
    mirror = WORK / "iqs"
    cases = LAB / ".acceptance-cases"
    assert not mirror.exists() and not cases.exists()
    helper.inspect_inputs()
    original = json.loads(helper.LOCK.read_text(encoding="utf-8"))
    lock = copy.deepcopy(original)
    roots = {str(ROOT).replace("\\", "/"): mirror, str(SOURCE).replace("\\", "/"): LAB}
    copied = []
    for entry in original["files"]:
        source = Path(entry["source_root"]) / entry["path"]
        target = roots[entry["source_root"]] / entry["path"]
        helper.safe(source)
        blob = source.read_bytes()
        assert len(blob) == entry["bytes"] and helper.digest(source) == entry["sha256"]
        if target.exists():
            assert helper.digest(target) == entry["sha256"]
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(blob)
        assert helper.digest(target) == entry["sha256"]
        copied.append({"source": str(source), "target": str(target), "sha256": entry["sha256"], "bytes": entry["bytes"]})
    for repo in lock["repositories"]:
        repo["root"] = roots[repo["root"]].as_posix()
    for entry in lock["files"]:
        entry["source_root"] = roots[entry["source_root"]].as_posix()
    rel = helper.LOCK.relative_to(ROOT)
    (mirror / rel).parent.mkdir(parents=True, exist_ok=True)
    helper.write(mirror / rel, lock)
    cases.mkdir()
    p = json.loads((LAB / "fixtures/reference/reference-pack-1.1.json").read_text(encoding="utf-8"))
    ref = next(r for r in p["input_refs"] if r["role"] == "batch_input_lock")
    ref["bytes"], ref["sha256"] = (mirror / rel).stat().st_size, helper.digest(mirror / rel)
    body = {k: v for k, v in p.items() if k != "pack_id"}
    import hashlib
    p["pack_id"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
    helper.write(cases / "reference-pack-relocated-1.1.json", p)
    legacy = SOURCE / "reports/evid-ref-02-run-01/evaluation.json"
    helper.safe(legacy)
    summary = json.loads((LAB / "docs/handoff/EVID-REF-02/remediation-01/generated/summary-legacy-1.0.0/evaluation-summary.json").read_text(encoding="utf-8"))
    assert helper.digest(legacy) == summary["source"]["evaluation_raw_sha256"]
    blob = legacy.read_bytes()
    with (cases / "legacy-evaluation.json").open("xb") as stream:
        stream.write(blob)
    helper.write(INTAKE / "relocated-input-fixture.json", {"at": helper.now(), "synthetic_relocation_only": True,
                 "copied_original_bytes": copied, "original_lock_sha256": helper.digest(helper.LOCK),
                 "derived_lock_sha256": helper.digest(mirror / rel),
                 "changes": "repository.root and files.source_root only; file bytes/SHA and all other lock metadata unchanged; dependent pack lock-ref and pack_id recomputed",
                 "legacy_original": {"path": str(legacy), "sha256": helper.digest(legacy), "bytes": len(blob)},
                 "does_not_prove_original_public_cli_portability": True})
    print(json.dumps({"verified_input_copies": len(copied), "synthetic_relocation": True}))


def run(label, args, timeout=300):
    dest = INTAKE / "logs"
    dest.mkdir(exist_ok=True)
    paths = [dest / f"{label}.{suffix}" for suffix in ("stdout.log", "stderr.log", "result.json")]
    assert not any(p.exists() for p in paths)
    command = [sys.executable, "-B", "-X", "utf8", *args]
    start = time.monotonic()
    timed_out = False
    with paths[0].open("xb") as out, paths[1].open("xb") as err:
        proc = subprocess.Popen(command, cwd=LAB, env=environment(), stdout=out, stderr=err)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            rc = proc.wait(timeout=30)
    result = {"at": helper.now(), "pid": proc.pid, "command": command, "cwd": str(LAB),
              "exit_code": rc, "timed_out": timed_out, "terminal": proc.poll() is not None,
              "seconds": time.monotonic() - start, "sanitized_environment": True,
              "stdout_sha256": helper.digest(paths[0]), "stderr_sha256": helper.digest(paths[1])}
    helper.write(paths[2], result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    for p in paths[:2]:
        print(p.read_text(encoding="utf-8", errors="replace")[-1700:], flush=True)
    return rc


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "freeze":
        freeze()
    elif action == "regress":
        sys.exit(run("evid-r1-regression-01", ["-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
                 "--basetemp=" + str(WORK / "pytest-temp"), "--junitxml=" + str(INTAKE / "evid-r1-regression.xml")]))
    elif action == "regress-corrected":
        # The package owns tmp_path through conftest; do not override its
        # session-specific .temp-roots base with a different controller path.
        sys.exit(run("evid-r1-regression-02", ["-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
                 "--junitxml=" + str(INTAKE / "evid-r1-regression-02.xml")]))
    elif action == "handoff":
        sys.exit(run("evid-r1-handoff-01", [str(ROOT / "scripts/parallel_handoff_cli.py"),
                 "--catalog", str(ROOT / "docs/implementation/parallel-lanes/packages/2026-10-10/manifest.json"),
                 "--package-id", "EVID-REF-02", "--input", str(LAB / "docs/handoff/EVID-REF-02/remediation-01/handoff.json")]))
    elif action == "counterexamples":
        sys.exit(run("evid-r1-counterexamples-01", [str(HERE / "evid_r1_counterexamples.py")]))
    elif action == "counterexamples-corrected":
        import ast
        ast.parse((HERE / "evid_r1_counterexamples.py").read_text(encoding="utf-8"))
        sys.exit(run("evid-r1-counterexamples-02", [str(HERE / "evid_r1_counterexamples.py")]))
    elif action == "prepare-relocation":
        prepare_relocated_inputs()
    elif action == "junction":
        sys.exit(run("evid-r1-junction-02", [str(HERE / "evid_r1_junction_case.py")]))
    else:
        raise SystemExit("unknown action")
