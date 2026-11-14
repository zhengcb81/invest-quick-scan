"""Continue the same FACT milestone in a byte-frozen, offline owned copy."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("intake_helpers", HERE / "acceptance_run.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
ROOT = old.ROOT
SOURCE = ROOT.parent / "iqs-fact-content-lab"
EXPECTED = "1ece6b2b49195dc5a4514c8b263192cb017eed55"
PRODUCT = "fb187d92a5b267f8ec7bcbef10bfc8b396f4bb8e"
WORK = ROOT / "runs/fc2a"
LAB = WORK / "fact"
INTAKE = ROOT / "docs/implementation/intake/parallel-packages/2026-10-10/fact-remediation-02"
HANDOFF = Path("docs/handoff/FACT-CONTENT-01/remediation-02")


def git_state():
    result = []
    for args in [["rev-parse", "HEAD"], ["branch", "--show-current"],
                 ["status", "--porcelain=v1", "-uall"], ["ls-files", "-z"],
                 ["merge-base", "--is-ancestor", PRODUCT, "HEAD"],
                 ["diff", "--name-only", PRODUCT, "HEAD"]]:
        p = subprocess.run(["git", "--no-optional-locks", "-C", str(SOURCE), *args],
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        if p.returncode:
            raise RuntimeError(f"read-only git failed: {args}: {p.stderr}")
        result.append({"args": args, "stdout": p.stdout, "exit_code": p.returncode})
    return result


def freeze():
    assert not WORK.exists() and not (INTAKE / "source-freeze-01.json").exists()
    state = git_state()
    assert state[0]["stdout"].strip() == EXPECTED
    assert not state[2]["stdout"].strip(), "external writer or unowned dirty paths"
    assert all(p.startswith(HANDOFF.as_posix() + "/")
               for p in state[5]["stdout"].splitlines())
    inputs = old.inspect_inputs()
    files = state[3]["stdout"].split("\0")[:-1]
    WORK.mkdir(parents=True)
    LAB.mkdir()
    for leaf in ["guard", "guard-logs", "temp"]:
        (WORK / leaf).mkdir()
    rows = []
    for rel in files:
        part = Path(rel)
        assert not part.is_absolute() and ".." not in part.parts
        assert not any(p.lower() in {".git", ".codegraph", ".env", "secrets", "credentials"}
                       for p in part.parts)
        src, dst = SOURCE / part, LAB / part
        old.safe(src)
        blob = src.read_bytes()
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("xb") as f:
            f.write(blob)
        assert old.digest(src) == old.digest(dst)
        rows.append({"path": rel, "bytes": len(blob), "sha256": old.digest(dst)})
    artifacts = json.loads((LAB / HANDOFF / "artifacts.json").read_text(encoding="utf-8"))
    checks = []
    for entry in artifacts["artifacts"]:
        part = Path(entry["path"])
        assert not part.is_absolute() and ".." not in part.parts
        p = LAB / part
        old.safe(p)
        checks.append({**entry, "actual_bytes": p.stat().st_size,
                       "actual_sha256": old.digest(p),
                       "matches": old.digest(p) == entry["sha256"]
                       and p.stat().st_size == entry["bytes"]})
    mismatched = [r["path"] for r in checks if not r["matches"]]
    assert set(mismatched) == {str(HANDOFF / "planning/progress.md").replace("\\", "/"),
                               str(HANDOFF / "planning/task_plan.md").replace("\\", "/")}
    old.write(INTAKE / "source-git-before-01.json", state)
    old.write(INTAKE / "source-freeze-01.json", {"at": old.now(), "head": EXPECTED,
        "product_commit": PRODUCT, "files": rows, "inputs": inputs, "artifacts": checks,
        "handoff_state": "present_manifest_inconsistent", "source_written": False})
    old.write(WORK / "ownership.json", {"root": str(WORK), "controller": str(Path(__file__)),
                                        "at": old.now(), "source_head": EXPECTED})
    guard = '''import os, socket, sys
from pathlib import Path
OWN = Path(__OWN__).resolve()
JUNIT = Path(__JUNIT__).resolve()
def inside(path):
    if isinstance(path, int) or path is None: return
    p = Path(os.fsdecode(path)).resolve()
    if p == JUNIT or p.is_relative_to(OWN): return
    raise OSError('FACT R2 acceptance forbids writes outside owned root')
def audit(event, args):
    if event == 'open':
        mode = args[1] or ''
        flags = args[2] or 0
        if any(c in mode for c in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND): inside(args[0])
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime'):
        inside(args[0])
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        inside(args[0]); inside(args[1])
    elif event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto'):
        raise OSError('FACT R2 acceptance is offline')
sys.addaudithook(audit)
def deny(*a, **k):
    with (OWN/'guard-logs'/('blocked-'+str(os.getpid())+'.log')).open('a',encoding='utf-8') as f: f.write('blocked network attempt\\n')
    raise OSError('FACT R2 acceptance is offline')
socket.socket.connect=deny
socket.socket.connect_ex=deny
socket.create_connection=deny
socket.getaddrinfo=deny
'''.replace("__OWN__", repr(str(WORK))).replace("__JUNIT__", repr(str(INTAKE / "fact-r2-regression-01.xml")))
    # Native test subprocesses explicitly use src-only PYTHONPATH. Install the
    # same owned test instrumentation there; never alter the source repository.
    for p in [WORK / "guard/sitecustomize.py", LAB / "src/sitecustomize.py"]:
        assert not p.exists()
        p.write_text(guard, encoding="utf-8")
    print(json.dumps({"files": len(rows), "artifacts": len(checks),
                      "mismatched": mismatched, "inputs": inputs}, ensure_ascii=False))


def environment():
    keep = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "SYSTEMDRIVE"}
    e = {k: v for k, v in os.environ.items() if k.upper() in keep}
    e.update(TEMP=str(WORK / "temp"), TMP=str(WORK / "temp"), TMPDIR=str(WORK / "temp"),
             PYTHONPATH=os.pathsep.join([str(WORK / "guard"), str(LAB / "src")]),
             PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
             PYTHONIOENCODING="utf-8", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", IQS_ROOT=str(ROOT))
    return e


def run(label, args, timeout=600):
    assert WORK.is_dir()
    dest = INTAKE / "logs"
    dest.mkdir(exist_ok=True)
    paths = [dest / f"{label}.{suffix}" for suffix in ["stdout.log", "stderr.log", "result.json"]]
    assert not any(p.exists() for p in paths)
    command = [sys.executable, "-B", "-X", "utf8", *args]
    start = time.monotonic()
    with paths[0].open("xb") as out, paths[1].open("xb") as err:
        proc = subprocess.Popen(command, cwd=LAB, env=environment(), stdout=out, stderr=err)
        print(json.dumps({"started": label, "pid": proc.pid}, ensure_ascii=False), flush=True)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Do not pretend a killed parent guarantees its children terminal.
            old.write(paths[2], {"at": old.now(), "pid": proc.pid, "timed_out": True,
                                "terminal": False, "command": command})
            raise
    result = {"at": old.now(), "pid": proc.pid, "command": command, "cwd": str(LAB),
              "exit_code": rc, "terminal": proc.poll() is not None, "timed_out": False,
              "seconds": time.monotonic() - start, "sanitized_environment": True,
              "source_written": False, "paid_api_requests": 0,
              "stdout_sha256": old.digest(paths[0]), "stderr_sha256": old.digest(paths[1])}
    old.write(paths[2], result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    print(paths[0].read_text(encoding="utf-8", errors="replace")[-2200:], flush=True)
    print(paths[1].read_text(encoding="utf-8", errors="replace")[-1300:], flush=True)
    return result


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "freeze":
        freeze()
    elif action == "regress-fixed-device":
        run("fact-r2-regression-02", ["-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
            "--basetemp=" + (WORK / "pt").as_posix(),
            "--junitxml=" + (INTAKE / "fact-r2-regression-02.xml").as_posix()])
    elif action == "handoff":
        run("fact-r2-handoff-01", [str(ROOT / "scripts/parallel_handoff_cli.py"), "--catalog",
            str(ROOT / "docs/implementation/parallel-lanes/packages/2026-10-10/manifest.json"),
            "--package-id", "FACT-CONTENT-01", "--input", str(LAB / HANDOFF / "handoff.json")])
    elif action == "counterexamples":
        run("fact-r2-counterexamples-01", [str(HERE / "fact_r2_counterexamples.py")])
    elif action == "counterexamples-fixed-controller":
        run("fact-r2-counterexamples-02", [str(HERE / "fact_r2_counterexamples.py")])
    else:
        raise SystemExit("unknown action")
