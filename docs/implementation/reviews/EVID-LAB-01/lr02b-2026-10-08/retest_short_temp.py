"""Rerun only ten setup-blocked tests; preserve the first batch's raw evidence."""
import os
import subprocess
import sys
import time
from pathlib import Path

from prepare import INTAKE, IQS, OWN, save, sha
from run import inputs

LAB = OWN / "lab"
OUT = INTAKE / "verification"
before = inputs()
plugin = Path(__file__).with_name("short_temp_plugin.py").read_bytes()
(OWN / "short_temp_plugin.py").write_bytes(plugin)
(OUT / "short-temp-plugin-executed.py").write_bytes(plugin)
safe = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA",
        "LOCALAPPDATA", "PROGRAMDATA", "SYSTEMDRIVE"}
env = {key: value for key, value in os.environ.items() if key.upper() in safe}
env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(OWN), str(LAB / "src")]),
           PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
           TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
           E97_OWNED_ROOT=str(OWN.resolve()), E97_LAB_ROOT=str(LAB),
           IQS_EVIDENCE_LAB_IQS_ROOT=str(IQS))
command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest",
           "tests/controller/test_archive_binding.py", "-o", "addopts=", "-q",
           "-p", "no:cacheprovider", "-p", "short_temp_plugin"]
started = time.monotonic()
process = subprocess.run(command, cwd=LAB, env=env, capture_output=True, timeout=180)
for kind, raw in (("stdout", process.stdout), ("stderr", process.stderr)):
    (OUT / ("archive-binding-tests-short-temp." + kind + ".log")).write_bytes(raw)
row = {"name": "archive-binding-tests-short-temp", "command": command,
       "returncode": process.returncode, "wall_s": round(time.monotonic() - started, 3),
       "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
       "controller_correction": "Only conftest TEMP_ROOT/ENV/pytest basetemp overridden in memory to OWN/t; delivered source bytes and all ten assertions unchanged",
       "original_inputs_unchanged": inputs() == before}
save(OUT / "archive-binding-tests-short-temp.result.json", row)
print(row)
assert row["original_inputs_unchanged"] and process.returncode == 0
