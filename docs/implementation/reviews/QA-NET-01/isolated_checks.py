"""Run StockQA's existing full milestone checks in a private guarded export."""
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
OWN = Path(os.environ["IQS_QA_NET_WORK_ROOT"]).resolve()
if not OWN.is_relative_to(PROJECT / "runs") or not OWN.name.startswith("qa-net01-intake-"):
    raise ValueError("invalid_owned_root")
if not (OWN / "export-manifest.json").is_file():
    raise ValueError("missing_owned_export_manifest")
RUNTIME = OWN / "runtime"
GUARD = OWN / "guard"
GUARD.mkdir(exist_ok=True)
(OWN / "temp").mkdir(exist_ok=True)
source = r'''
import os, sys, hashlib, json, shutil, shlex, re
from pathlib import Path
OWN = Path(os.environ["IQS_QA_NET_WORK_ROOT"]).resolve()
GUARD = OWN / "guard"
RUNTIME = OWN / "runtime"
manifest = json.loads((OWN / "export-manifest.json").read_text(encoding="utf-8"))
wrapper_hashes = {row["path"]: row["sha256"] for row in manifest["export_allowlist"]}
shells = {Path(value).resolve(): suffix for value, suffix in
          ((shutil.which("bash"), "sh"), (os.environ.get("COMSPEC"), "bat")) if value}
# Nested pytest must never clean another live pytest process's basetemp.
os.environ["PYTEST_ADDOPTS"] = ('--basetemp "' + str(OWN / ("pytest-" + str(os.getpid())))
    + '" -o log_file="' + str(OWN / ("pytest-" + str(os.getpid()) + ".log")) + '"')
def path_ok(value):
    if isinstance(value, int): return
    raw = os.fsdecode(value)
    if raw.startswith("\\\\?\\") and len(raw) >= 7 and raw[4].isascii() and raw[4].isalpha() and raw[5:7] == ":\\":
        raw = raw[4:]
    if not Path(raw).resolve().is_relative_to(OWN):
        raise PermissionError("qa_net_full_guard_outside_write")
def audit(event, args):
    if event == "open":
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            path_ok(path)
    elif event in ("os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"):
        path_ok(args[0])
    elif event in ("os.rename", "os.replace", "os.link", "os.symlink"):
        path_ok(args[0]); path_ok(args[1])
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname"):
        # Windows asyncio's standard-library socketpair is a local self-pipe.
        # Permit that exact implementation, never HTTP/DNS or general loopback.
        frame = sys._getframe(1)
        if (event == "socket.connect" and frame.f_code.co_name == "_fallback_socketpair"
                and Path(frame.f_code.co_filename).resolve() == (Path(sys.base_prefix)/"Lib"/"socket.py").resolve()
                and isinstance(args[1], tuple) and args[1][0] in ("127.0.0.1", "::1")):
            return
        raise PermissionError("qa_net_full_guard_network")
    elif event.startswith("winreg.") or event == "os.system":
        raise PermissionError("qa_net_full_guard_registry_or_shell")
    elif event == "subprocess.Popen":
        executable, argv, cwd, env = args
        if executable is None:
            if isinstance(argv, str):
                for candidate in [Path(sys.executable).resolve(), *shells]:
                    if argv.lower().startswith(('"' + str(candidate) + '" ').lower()) or argv.lower().startswith((str(candidate) + ' ').lower()):
                        executable = candidate
                        break
            elif isinstance(argv, (list, tuple)) and argv:
                executable = argv[0]
        if executable is None:
            raise PermissionError("qa_net_full_guard_unidentified_executable")
        executable = Path(executable).resolve()
        if executable == Path(sys.executable).resolve():
            tokens = shlex.split(argv, posix=False) if isinstance(argv, str) else argv
            for token in tokens[1:]:
                token = str(token).strip('"')
                if token in ("-c", "-m"):
                    break
                if token in ("-S", "-I", "-E") or (re.fullmatch(r"-[A-Za-z]+", token) and set("SIE") & set(token[1:])):
                    raise PermissionError("qa_net_full_guard_disabled_by_python_flags")
        else:
            suffix = shells.get(executable)
            wrapper = RUNTIME / "scripts" / ("run_ci." + str(suffix))
            arguments = argv if isinstance(argv, str) else subprocess_arguments(argv)
            if (suffix is None or str(wrapper) not in arguments
                    or any(c in arguments for c in "&|<>`;\r\n")
                    or hashlib.sha256(wrapper.read_bytes()).hexdigest() != wrapper_hashes.get("scripts/run_ci." + suffix)):
                raise PermissionError("qa_net_full_guard_non_owned_wrapper")
        path_ok(cwd if cwd is not None else Path.cwd())
        if env is not None:
            env["IQS_QA_NET_WORK_ROOT"] = str(OWN)
            env["PYTHONPATH"] = os.pathsep.join((str(GUARD), env.get("PYTHONPATH", "")))
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHON"] = sys.executable
def subprocess_arguments(argv):
    return " ".join(str(value) for value in argv)
sys.addaudithook(audit)
'''
(GUARD / "sitecustomize.py").write_text(source, encoding="utf-8")
env = dict(os.environ)
for name in tuple(env):
    if name.endswith(("API_KEY", "API_TOKEN")):
        del env[name]
env.update(TMP=str(OWN / "temp"), TEMP=str(OWN / "temp"), TMPDIR=str(OWN / "temp"),
           PYTHONPATH=os.pathsep.join((str(GUARD), str(RUNTIME))),
           PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
           PYTEST_PLUGINS="pytest_asyncio.plugin", STOCKQA_RUN_LIVE_E2E="0",
           PYTEST_ADDOPTS='--basetemp "' + str(OWN / "pytest-root") + '" -o log_file="' + str(OWN / "pytest-session.log") + '"',
           BLACK_CACHE_DIR=str(OWN / "black-cache"), BLACK_NUM_WORKERS="1",
           XDG_CACHE_HOME=str(OWN / "cache"))
env["PYTHON"] = sys.executable
probe = '''import os, sys, socket
import subprocess
from pathlib import Path
assert "sitecustomize" in sys.modules
own = Path(os.environ["IQS_QA_NET_WORK_ROOT"]).resolve()
assert sys.modules["sitecustomize"].OWN == own
target = own.parent / "qa_net_full_guard_canary.txt"
assert not target.exists()
try:
    target.write_text("must never be written")
    raise AssertionError("outside write allowed")
except PermissionError:
    pass
try:
    socket.getaddrinfo("example.com", 443)
    raise AssertionError("DNS allowed")
except PermissionError:
    pass
assert not target.exists()
for flag in ("-S", "-I", "-E", "-BIS"):
    try:
        subprocess.run([sys.executable, flag, "-c", "pass"], check=True)
        raise AssertionError("guard-disabling Python flag allowed")
    except PermissionError:
        pass
print("inherited_guard_canaries_passed")
'''
result = subprocess.run([sys.executable, "-B", "-c", probe], cwd=RUNTIME, env=env,
                        capture_output=True, text=True, encoding="utf-8")
(OWN / "guard-canary.log").write_text(result.stdout + result.stderr, encoding="utf-8")
if result.returncode != 0:
    raise RuntimeError("inherited guard preflight failed; public checks not launched")
command = [sys.executable, "-B", "scripts/checks.py", "--full", "--timeout", "180"]
if sys.argv[1:]:
    command = [sys.executable, "-B", *sys.argv[1:]]
with (OWN / "full-check-output.log").open("w", encoding="utf-8") as log:
    process = subprocess.Popen(command, cwd=RUNTIME, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in process.stdout:
        log.write(line)
        log.flush()
        if (line.startswith("checks:") or "passed" in line or "error:" in line
                or "PermissionError:" in line or "would reformat" in line):
            print(line.rstrip()[:600], flush=True)
    code = process.wait()
print(json.dumps({"public_check_exit_code": code, "work_root": str(OWN), "live_enabled": False}))
raise SystemExit(code)
