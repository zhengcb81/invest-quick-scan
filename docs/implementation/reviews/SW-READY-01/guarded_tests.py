"""Run SW intake cases against a read-only frozen export, private writes only."""

import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
OWN = Path(os.environ["IQS_SW_READY_WORK_ROOT"]).resolve()
if not OWN.is_relative_to(PROJECT / "runs") or not OWN.name.startswith("sw-ready01-intake-"):
    raise ValueError("invalid owned root")
if not (OWN / "export-manifest.json").is_file():
    raise ValueError("missing export manifest")
for name in tuple(os.environ):
    if name.endswith(("API_KEY", "API_TOKEN")):
        del os.environ[name]
for name in ("TMP", "TEMP", "TMPDIR"):
    os.environ[name] = str(OWN / "temp")
(OWN / "temp").mkdir(exist_ok=True)
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.dont_write_bytecode = True
sys.path[:0] = [str(OWN / "runtime"), str(OWN / "runtime/tests")]


def path_ok(value):
    if isinstance(value, int):
        return
    raw = os.fsdecode(value)
    if raw.startswith("\\\\?\\"):
        raw = raw[4:]
    if not Path(raw).resolve().is_relative_to(OWN):
        raise PermissionError("sw_ready_guard_outside_write")


def audit(event, args):
    if event == "open":
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            path_ok(path)
    elif event in ("os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"):
        path_ok(args[0])
    elif event in ("os.rename", "os.replace", "os.link", "os.symlink"):
        path_ok(args[0]); path_ok(args[1])
    elif event.startswith("socket.") or event == "subprocess.Popen" or event == "os.system" or event.startswith("winreg."):
        raise PermissionError("sw_ready_guard_network_process_registry")


sys.addaudithook(audit)
outside = OWN.parent / "sw-ready-guard-canary.txt"
assert not outside.exists()
try:
    outside.write_text("must not write")
    raise AssertionError("outside write allowed")
except PermissionError:
    pass
import socket
try:
    socket.getaddrinfo("example.com", 443)
    raise AssertionError("DNS allowed")
except PermissionError:
    pass
print("sw_ready_guard_canaries_passed", flush=True)
os.chdir(OWN / "runtime")
import pytest
raise SystemExit(pytest.main([
    "-q", str(PROJECT / "docs/implementation/reviews/SW-READY-01/acceptance_cases.py"),
    "--rootdir", str(OWN), "--basetemp", str(OWN / "pytest"),
    "--override-ini", "cache_dir=" + str(OWN / "cache"),
    "--override-ini", "log_file=" + str(OWN / "pytest.log"), "--tb=short",
]))
