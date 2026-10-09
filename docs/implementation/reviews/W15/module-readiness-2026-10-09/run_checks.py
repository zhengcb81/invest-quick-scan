"""Bounded, credential-free W15 checks in one exclusively owned runtime."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
OWN = ROOT / "runs/w15a"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
GUARD = '''import os, socket, sqlite3, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
OWN=Path(os.environ["IQS_W15_OWN"]).resolve()
def denied(*args, **kwargs): raise RuntimeError("W15 offline: network denied")
_socket_connect=socket.socket.connect
_pair_code=socket._fallback_socketpair.__code__
def guarded_connect(self, address):
    # Windows asyncio's stdlib socketpair needs exactly its own local listener.
    # Ordinary localhost HTTP and every non-loopback connection remain denied.
    frame=sys._getframe(1)
    if frame.f_code is _pair_code and frame.f_locals.get("csock") is self:
        listener=frame.f_locals.get("lsock")
        if (listener is not None and isinstance(address, tuple) and len(address)==2
                and address[0] in {"127.0.0.1", "::1"}
                and listener.getsockname()[:2]==address
                and listener.getsockopt(socket.SOL_SOCKET,socket.SO_ACCEPTCONN)==1):
            return _socket_connect(self,address)
    return denied(self,address)
socket.socket.connect=guarded_connect
socket.socket.connect_ex=denied
socket.socket.sendto=denied
_connect=sqlite3.connect
def connect(database, *args, **kwargs):
    if database != ":memory:":
        text=str(database)
        if text.startswith("file:"):
            parsed=urlsplit(text)
            if parsed.netloc or parsed.fragment: raise RuntimeError("W15 offline: URI authority denied")
            text=unquote(parsed.path)
            if len(text)>3 and text[0]=="/" and text[2]==":": text=text[1:]
        if not Path(text).resolve().is_relative_to(OWN): raise RuntimeError("W15 offline: foreign database denied")
    return _connect(database, *args, **kwargs)
sqlite3.connect=connect
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    label = sys.argv[1]
    assert re.fullmatch(r"(?:handoff|storage|executor|baseline)-[a-z][a-z0-9-]{1,60}", label)
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / (label + ".process.json")).exists()
    if not OWN.exists():
        OWN.mkdir()
        for name in ("guard", "tmp"):
            (OWN / name).mkdir()
        (OWN / "guard/sitecustomize.py").write_text(GUARD, encoding="utf-8")
        (OWN / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    assert OWN.resolve() == ROOT / "runs/w15a"
    assert (OWN / "guard/sitecustomize.py").read_text(encoding="utf-8") == GUARD
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", IQS_W15_OWN=str(OWN),
               PYTHONPATH=os.pathsep.join((str(OWN / "guard"), str(ROOT / "scripts"))),
               TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"))
    target = OWN / "sw" if label.startswith("storage-") else OWN / "qa" if label.startswith("executor-") else OWN / "qa_baseline" if label.startswith("baseline-") else ROOT
    if target != ROOT:
        assert target.is_dir() and target.resolve().is_relative_to(OWN)
        env["PYTHONPATH"] = os.pathsep.join((str(OWN / "guard"), str(target), str(target / "tests")))
        env["STOCKWIKI_PROJECT_PARENT"] = str(OWN / "no-production-workspaces")
        env["IQS_ROUTE_TEST_CODE_ROOT"] = str(ROOT)
        env["IQS_W15_QA_CODE_ROOT"] = str(OWN / "qa")
    refs = ["tests/test_route_store_handoff.py", "scripts/route_store_handoff.py", "scripts/routing.py",
            "scripts/question_manifest.py", "scripts/question_sets.py", "scripts/module_contract.py",
            "scripts/module_registry.py", "scripts/question_fingerprints.py",
            "schemas/quick_scan/route-store-validation.schema.json",
            "schemas/quick_scan/module-refresh.schema.json", "schemas/quick_scan/route-store-cli.schema.json"]
    before = {p: sha((ROOT / p).read_bytes()) if (ROOT / p).exists() else None for p in refs}
    if target != ROOT:
        for directory in dict.fromkeys((target, OWN / "sw", OWN / "qa")):
            for path in sorted(directory.rglob("*.py")):
                before[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
            for path in sorted(directory.rglob("*.schema.json")):
                before[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", "-c", str(OWN / "pytest.ini"),
               "-p", "no:cacheprovider", "--basetemp", str(OWN / label), "-q",
               "--junitxml", str(OUT / (label + ".junit.xml")), *sys.argv[2:]]
    started = time.monotonic()
    proc = subprocess.Popen(command, cwd=target, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps(dict(label=label, pid=proc.pid)), flush=True)
    stdout, stderr = proc.communicate(timeout=900)
    (OUT / (label + ".stdout.log")).write_bytes(stdout)
    (OUT / (label + ".stderr.log")).write_bytes(stderr)
    after = {p: sha((ROOT / p).read_bytes()) if (ROOT / p).exists() else None for p in refs}
    if target != ROOT:
        for directory in dict.fromkeys((target, OWN / "sw", OWN / "qa")):
            for path in sorted(directory.rglob("*.py")):
                after[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
            for path in sorted(directory.rglob("*.schema.json")):
                after[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    assert after == before, "source changed during execution"
    report = dict(label=label, pid=proc.pid, command=command, returncode=proc.returncode,
                  terminal_confirmed=True, wall_s=round(time.monotonic() - started, 3),
                  execution_sha256=before, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr),
                  credentials_inherited=False, Python_network_guard=True, foreign_SQLite_guard=True,
                  whole_OS_guard_claim=False, model_API_requests=0, production_DB_migrations=0,
                  synthetic_company_data=True, owned_runtime=str(OWN),
                  guard_sha256=sha((OWN / "guard/sitecustomize.py").read_bytes()))
    (OUT / (label + ".process.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(stdout.decode("utf-8", errors="replace")[-3500:])
    print(stderr.decode("utf-8", errors="replace")[-1200:])
    print(json.dumps(dict(label=label, returncode=proc.returncode, terminal_confirmed=True)))


if __name__ == "__main__":
    main()
