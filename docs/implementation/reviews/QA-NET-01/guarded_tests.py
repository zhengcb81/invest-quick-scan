"""Run frozen owner tests in this intake's private writable root only."""
import os
import sys
import socket
import contextlib
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
OWN = Path(os.environ["IQS_QA_NET_WORK_ROOT"]).resolve()
if not OWN.is_relative_to(PROJECT / "runs") or not OWN.name.startswith("qa-net01-intake-"):
    raise ValueError("intake_work_root_outside_owned_scope")
if not (OWN / "export-manifest.json").is_file():
    raise ValueError("missing_owned_export_manifest")
RUNTIME = OWN / "runtime"
TEMP = OWN / "temp"
TEMP.mkdir(exist_ok=True)
for name in tuple(os.environ):
    if name.endswith(("API_KEY", "API_TOKEN")) or name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        del os.environ[name]
os.environ.update(TMP=str(TEMP), TEMP=str(TEMP), TMPDIR=str(TEMP),
                  PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
os.environ["IQS_QA_NET_RUNTIME"] = str(RUNTIME)
sys.dont_write_bytecode = True
os.chdir(RUNTIME)
sys.path.insert(0, str(RUNTIME))
COUNTS = {"outside_write_blocked": 0, "network_blocked": 0}

def own_path(value):
    if isinstance(value, int):
        return
    raw = os.fsdecode(value)
    # Windows pytest uses the equivalent extended drive spelling for cleanup.
    # Normalize only drive-qualified paths; devices/UNC remain outside scope.
    if raw.startswith("\\\\?\\") and len(raw) >= 7 and raw[4].isascii() and raw[4].isalpha() and raw[5:7] == ":\\":
        raw = raw[4:]
    path = Path(raw).resolve()
    if not path.is_relative_to(OWN):
        COUNTS["outside_write_blocked"] += 1
        raise PermissionError("intake_guard_root_escape")

def audit(event, args):
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing:
            own_path(path)
    elif event in ("os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"):
        own_path(args[0])
    elif event in ("os.rename", "os.replace", "os.link", "os.symlink"):
        own_path(args[0]); own_path(args[1])
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname"):
        COUNTS["network_blocked"] += 1
        raise PermissionError("intake_guard_network_forbidden")
    elif event in ("subprocess.Popen", "os.system", "winreg.OpenKey", "winreg.QueryValue", "winreg.QueryValueEx"):
        raise PermissionError("intake_guard_subprocess_or_registry_forbidden")

sys.addaudithook(audit)
canary = OWN.parent / "qa_net01_guard_canary.txt"
assert not canary.exists()
try:
    canary.write_text("must never be created", encoding="utf-8")
    raise AssertionError("outside write guard not active")
except PermissionError:
    pass
try:
    socket.getaddrinfo("example.com", 443)
    raise AssertionError("network guard not active")
except PermissionError:
    pass
assert not canary.exists()
import pytest

args = sys.argv[1:] or [
    "tests/unit/test_qa_net01_c06_seal.py",
    "tests/unit/test_qa_net01_question_manifest.py",
    "tests/unit/test_qa_net01_search_boundary.py",
    "tests/integration/test_qa_net01_cli_e2e.py",
]
class Tee:
    def __init__(self, target, log):
        self.target, self.log = target, log
    def write(self, value):
        self.target.write(value); self.log.write(value)
    def flush(self):
        self.target.flush(); self.log.flush()
    def __getattr__(self, name):
        return getattr(self.target, name)

with (OWN / "guarded-test-output.log").open("w", encoding="utf-8") as log:
    with contextlib.redirect_stdout(Tee(sys.stdout, log)), contextlib.redirect_stderr(Tee(sys.stderr, log)):
        result = pytest.main(args + ["-q", "--rootdir", str(RUNTIME), "--basetemp", str(OWN / "pytest-root"),
                                     "-o", "log_file=" + str(OWN / "pytest-session.log"),
                                     "-o", "cache_dir=" + str(OWN / "pytest-cache")])
        print("INTAKE_GUARD_COUNTS=" + str(COUNTS))
raise SystemExit(result)
