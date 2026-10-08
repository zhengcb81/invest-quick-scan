"""A single bounded affected batch; raw output and timeouts are retained."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/sw-repair-remediation-2026-10-08-01"
INTAKE = IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08-remediation"
OUT = INTAKE / "verification"
HELPER = Path(__file__).with_name("guarded_run.py")


def main():
    safe = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "LOCALAPPDATA",
            "APPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA", "SYSTEMDRIVE"}
    env = {key: value for key, value in os.environ.items() if key.upper() in safe}
    env.update(TMP=str(OWN / "temp"), TEMP=str(OWN / "temp"), TMPDIR=str(OWN / "temp"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    checks = []

    def run(name, arguments):
        command = [sys.executable, "-B", "-X", "utf8", *arguments]
        started = time.monotonic()
        try:
            process = subprocess.run(command, cwd=IQS, env=env, capture_output=True, timeout=180)
        except subprocess.TimeoutExpired as exc:
            process = subprocess.CompletedProcess(command, 124, exc.stdout or b"", exc.stderr or b"")
        (OUT / (name + ".stdout.log")).write_bytes(process.stdout)
        (OUT / (name + ".stderr.log")).write_bytes(process.stderr)
        row = {"name": name, "command": command, "returncode": process.returncode,
               "wall_s": round(time.monotonic() - started, 3),
               "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(process.stderr).hexdigest()}
        checks.append(row)
        print(json.dumps({k: row[k] for k in ("name", "returncode", "wall_s")}), flush=True)

    run("public-handoff", [str(IQS / "scripts/parallel_handoff_cli.py"), "--catalog",
                           str(IQS / "docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json"),
                           "--package-id", "SW-REPAIR-02", "--input", str(INTAKE / "worker/handoff.json")])
    for mode in ("core", "extra", "utf8", "browser"):
        run(mode, [str(HELPER), mode])
    (OUT / "commands.json").write_text(json.dumps({"schema": "iqs_sw_remediation_commands/1", "checks": checks,
        "paid_calls": 0, "keys_in_child_environment": 0, "source_written": False,
        "cleanup_pending": True}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
