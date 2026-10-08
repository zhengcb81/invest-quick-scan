"""Execute a bounded acceptance batch against the frozen source export."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

IQS = Path(__file__).resolve().parents[4]
OWN = IQS / "runs/sw-repair-2026-10-08-01"
RUNTIME = OWN / "runtime"
SOURCE = Path("C:/Users/郑曾波/Projects/StockWiki")
mode = sys.argv[1]
if mode not in {"core", "extra", "browser"} or not (OWN / "export-manifest.json").is_file():
    raise ValueError("unknown batch or missing frozen export")
sys.dont_write_bytecode = True
safe_names = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "LOCALAPPDATA",
              "APPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA"}
safe_env = {key: value for key, value in os.environ.items() if key.upper() in safe_names}
os.environ.clear()
os.environ.update(safe_env)
os.environ.update({"TMP": str(OWN / "temp"), "TEMP": str(OWN / "temp"), "TMPDIR": str(OWN / "temp"),
                   "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1",
                   "IQS_SW_READY_WORK_ROOT": str(OWN), "IQS_SWR_WORK_ROOT": str(OWN),
                   "GIT_DIR": str(SOURCE / ".git"), "GIT_WORK_TREE": str(RUNTIME),
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
if mode == "browser":
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "C:/Users/郑曾波/AppData/Local/ms-playwright"
sys.path[:0] = [str(RUNTIME), str(RUNTIME / "tests")]
os.chdir(RUNTIME)
node_driver = None
if mode == "browser":
    from playwright._impl._driver import compute_driver_executable
    node, driver = compute_driver_executable()
    node_driver = [str(node), str(driver), "run-driver"]


def path_ok(value) -> None:
    if isinstance(value, int):
        return
    raw = os.fsdecode(value)
    if raw.casefold() in {"nul", "nul:", os.devnull.casefold()}:
        return
    path = Path(raw).resolve()
    if not path.is_relative_to(OWN.resolve()):
        raise PermissionError("swr_intake_outside_write")


def allowed_process(args) -> bool:
    commands = [["git", "show", "9f552a67:stockwiki/quick_scan_query.py"]]
    if node_driver:
        commands.append(node_driver)
    if isinstance(args, (list, tuple)):
        return [os.fsdecode(x) for x in args] in commands
    return isinstance(args, str) and args in [subprocess.list2cmdline(c) for c in commands]


def audit(event, args) -> None:
    if event == "open":
        path, access, flags = args
        if (isinstance(access, str) and any(c in access for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        ):
            path_ok(path)
    elif event in {"os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"}:
        path_ok(args[0])
    elif event in {"os.rename", "os.replace", "os.link", "os.symlink"}:
        path_ok(args[0]); path_ok(args[1])
    elif event in {"socket.connect", "socket.bind", "socket.sendto"}:
        address = args[1] if event != "socket.sendto" else args[-1]
        if not isinstance(address, tuple) or str(address[0]) not in {"127.0.0.1", "::1"}:
            raise PermissionError("swr_intake_nonloopback_socket")
    elif event == "socket.getaddrinfo":
        if str(args[0]) not in {"127.0.0.1", "::1", "localhost"}:
            raise PermissionError("swr_intake_external_dns")
    elif event == "subprocess.Popen":
        if not allowed_process(args[1]):
            raise PermissionError("swr_intake_process_not_allowlisted")
    elif event == "os.system" or event.startswith("winreg."):
        raise PermissionError("swr_intake_shell_or_registry")


sys.addaudithook(audit)
canary = IQS / "swr-intake-must-not-write.txt"
if canary.exists():
    raise ValueError("canary already exists")
try:
    canary.write_text("must be blocked", encoding="utf-8")
    raise AssertionError("outside write allowed")
except PermissionError:
    pass
try:
    socket.getaddrinfo("example.invalid", 443)
    raise AssertionError("external DNS allowed")
except PermissionError:
    pass
print(json.dumps({"mode": mode, "canaries": "passed", "keys_provided": 0,
                  "source_commit": "9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f"}), flush=True)

if mode == "browser":
    from playwright.sync_api import BrowserType
    original_launch = BrowserType.launch

    def isolated_launch(self, **kwargs):
        kwargs["args"] = [*kwargs.get("args", []), "--disable-background-networking",
                          "--disable-component-update", "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"]
        return original_launch(self, **kwargs)

    BrowserType.launch = isolated_launch

import pytest
if mode == "core":
    selected = ["tests/" + p for p in ["test_swr_cases.py", "test_swr_backup.py", "test_swr_profiles.py",
                                      "test_swr_query.py", "test_quick_scan_backup.py", "test_quick_scan_profiles.py",
                                      "test_quick_scan_query.py", "test_ui_quick_scan.py"]]
    selected.append(str(IQS / "docs/implementation/reviews/SW-READY-01/acceptance_cases.py"))
elif mode == "extra":
    selected = [str(Path(__file__).with_name("acceptance_cases.py"))]
else:
    selected = ["tests/test_e2e_quick_scan_ui.py"]
raise SystemExit(pytest.main(["-q", "-s", *selected, "--rootdir", str(OWN), "--basetemp", str(OWN / ("pytest-" + mode)),
                              "--override-ini", "cache_dir=" + str(OWN / ("cache-" + mode)),
                              "--override-ini", "log_file=" + str(OWN / ("pytest-" + mode + ".log")), "--tb=short"]))
