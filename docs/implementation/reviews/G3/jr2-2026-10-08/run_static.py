"""Run owner-configured static checks with one-file Black and private caches."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/jr2-2026-10-08-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
FILES = (
    "src/utils/quick_scan_result_outbox.py", "src/utils/quick_scan_work_store.py",
    "tests/unit/test_quick_scan_result_outbox.py", "tests/unit/test_q10_delivery.py",
    "tests/unit/test_quick_scan_work_store.py", "tests/unit/test_quick_scan_c06_complete_seal.py",
    "tests/integration/test_qa_c06_02_e2e.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--format", action="store_true")
    parser.add_argument("--mypy", action="store_true")
    args = parser.parse_args()
    assert args.label.replace("-", "").replace("_", "").isalnum()
    log = OUT / "verification" / args.label
    log.mkdir(parents=True, exist_ok=False)
    qa = OWN / "qa"
    paths = [str(qa / name) for name in FILES]
    env = {key: value for key, value in os.environ.items() if key.upper() in
           {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(qa), str(qa / "src")]),
        E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
        PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        BLACK_CACHE_DIR=str(OWN / "tmp/black-cache"), MYPY_CACHE_DIR=str(OWN / "tmp/mypy-cache"))
    commands = [[sys.executable, "-B", "-m", "isort", "--profile", "black",
                 "--settings-path", str(qa / "pyproject.toml"), *([] if args.format else ["--check-only"]), *paths]]
    # A single file per invocation avoids Black's multi-file process pool.
    commands.extend([sys.executable, "-B", "-m", "black", "--workers", "1",
                     "--config", str(qa / "pyproject.toml"), *([] if args.format else ["--check"]), path]
                    for path in paths)
    if args.mypy:
        commands.append([sys.executable, "-B", "-m", "mypy", "--config-file", str(qa / "pyproject.toml"), "src/"])
    records = []
    for index, command in enumerate(commands):
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=qa, env=env, capture_output=True, timeout=90)
            code, stdout, stderr, timed_out = result.returncode, result.stdout, result.stderr, False
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr, timed_out = None, error.stdout or b"", error.stderr or b"", True
        (log / f"{index:02}.stdout.log").write_bytes(stdout)
        (log / f"{index:02}.stderr.log").write_bytes(stderr)
        records.append(dict(command=command, returncode=code, timeout=timed_out, wall_s=round(time.monotonic()-started, 3)))
    payload = dict(schema="jr2_static/1", format_applied=args.format, commands=records,
        failed_commands=sum(row["returncode"] != 0 for row in records),
        final_file_sha256={name: hashlib.sha256((qa / name).read_bytes()).hexdigest() for name in FILES},
        key_environment_removed=True, network_enabled=False, cache_scope=str(OWN / "tmp"))
    (log / "process.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", "utf-8")
    print(json.dumps(dict(label=args.label, failed_commands=payload["failed_commands"],
                         returncodes=[row["returncode"] for row in records],
                         wall_s=round(sum(row["wall_s"] for row in records), 3))))


if __name__ == "__main__":
    main()
