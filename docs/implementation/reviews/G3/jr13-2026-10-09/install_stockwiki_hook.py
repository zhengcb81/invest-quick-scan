"""Install the existing local static-only hook; no source/config edits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
SW = IQS.parent / "StockWiki"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13/stockwiki-publication"
OWN = IQS / "runs/s13p"
env = {k: v for k, v in os.environ.items() if k.upper() in {
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
    "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
env.update(GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
           PYTHONIOENCODING="utf-8", PRE_COMMIT_HOME=str(OWN / "pc"),
           RUFF_CACHE_DIR=str(OWN / "ruff"), TEMP=str(OWN / "tmp"),
           TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"))
assert OWN.is_dir() and not (OUT / "hook-install.process.json").exists()
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SW, env=env).decode().strip() == "c40de21403720306ba21edbf71b9634a40ee58f8"
hook_rel = subprocess.check_output(["git", "rev-parse", "--git-path", "hooks/pre-commit"], cwd=SW, env=env).decode().strip()
hook = (SW / hook_rel).resolve()
assert hook == SW / ".git/hooks/pre-commit" and not hook.exists()
start = time.monotonic()
proc = subprocess.Popen([sys.executable, "-B", "-m", "pre_commit", "install"], cwd=SW, env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
stdout, stderr = proc.communicate(timeout=60)
(OUT / "hook-install.stdout.log").write_bytes(stdout)
(OUT / "hook-install.stderr.log").write_bytes(stderr)
(OUT / "hook-install.process.json").write_text(json.dumps(dict(pid=proc.pid,
    argv=[sys.executable, "-B", "-m", "pre_commit", "install"], cwd=str(SW), returncode=proc.returncode,
    terminal_confirmed=True, wall_s=round(time.monotonic()-start, 3),
    stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest(),
    installed_hook=str(hook), source_or_config_changes=False), indent=2)+"\n", encoding="utf-8")
print(stdout.decode("utf-8", errors="replace")); print(stderr.decode("utf-8", errors="replace"))
assert proc.returncode == 0 and hook.is_file()
