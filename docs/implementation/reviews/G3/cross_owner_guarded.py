"""Run the public-interface preflight in two exact, private owner exports."""
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
OWN = Path(os.environ["IQS_CROSS_OWNER_ROOT"]).resolve()
if not OWN.is_relative_to(PROJECT / "runs") or not OWN.name.startswith("cross-owner-"):
    raise ValueError("new exclusive IQS cross-owner root required")
for child in ("qa-net01-intake-runtime", "sw-ready01-intake-runtime"):
    if not (OWN / child / "export-manifest.json").is_file():
        raise ValueError("exact owner export manifest missing")
for name in tuple(os.environ):
    if name.endswith(("API_KEY", "API_TOKEN")) or "RUN_LIVE" in name:
        del os.environ[name]
(OWN / "temp").mkdir(exist_ok=True)
os.environ.update(TMP=str(OWN / "temp"), TEMP=str(OWN / "temp"), TMPDIR=str(OWN / "temp"),
                  PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
sys.dont_write_bytecode = True
sys.path[:0] = [str(OWN / "qa-net01-intake-runtime/runtime"),
                str(OWN / "sw-ready01-intake-runtime/runtime")]
os.chdir(OWN / "sw-ready01-intake-runtime/runtime")


def path_ok(value):
    if isinstance(value, int):
        return
    raw = os.fsdecode(value)
    if raw.startswith("\\\\?\\") and len(raw) >= 7 and raw[5:7] == ":\\":
        raw = raw[4:]
    if not Path(raw).resolve().is_relative_to(OWN):
        raise PermissionError("cross_owner_write_outside_run")


def audit(event, args):
    if event == "open":
        path, mode, flags = args
        if ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
                (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))):
            path_ok(path)
    elif event in ("os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"):
        path_ok(args[0])
    elif event in ("os.rename", "os.replace", "os.link", "os.symlink"):
        path_ok(args[0]); path_ok(args[1])
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto"):
        # The standard-library Windows asyncio self-pipe is not HTTP.
        frame = sys._getframe(1)
        if (event == "socket.connect" and frame.f_code.co_name == "_fallback_socketpair"
                and Path(frame.f_code.co_filename).resolve() == (Path(sys.base_prefix) / "Lib/socket.py").resolve()
                and isinstance(args[1], tuple) and args[1][0] in ("127.0.0.1", "::1")):
            return
        raise PermissionError("cross_owner_network_forbidden")
    elif event == "subprocess.Popen" or event == "os.system" or event.startswith("winreg."):
        raise PermissionError("cross_owner_network_process_registry_forbidden")


sys.addaudithook(audit)
import socket
for action in (lambda: (OWN.parent / "cross-owner-canary.txt").write_text("forbidden"),
               lambda: socket.getaddrinfo("example.com", 443)):
    try:
        action()
        raise AssertionError("guard canary unexpectedly permitted")
    except PermissionError:
        pass
print("cross_owner_guard_canaries_passed", flush=True)
import pytest
raise SystemExit(pytest.main([
    "-q", str(PROJECT / "docs/implementation/reviews/G3/cross_owner_cases.py"),
    "--rootdir", str(OWN), "--basetemp", str(OWN / "pytest"),
    "-o", "cache_dir=" + str(OWN / "cache"),
    "-o", "log_file=" + str(OWN / "pytest.log"), "--tb=short",
]))
