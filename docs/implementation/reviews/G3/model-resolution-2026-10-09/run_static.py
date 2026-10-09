"""Affected-file formatting and owner mypy using only private caches."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/model-resolution-2026-10-09-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--format", action="store_true")
    parser.add_argument("--mypy", action="store_true")
    args = parser.parse_args()
    assert args.label.replace("-", "").replace("_", "").isalnum()
    scope = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))
    before = {r["path"]: r for r in json.loads((OUT / "source-snapshot.json").read_text("utf-8"))}
    qa = OWN / "qa"
    files = [name for name in scope["files"] if name.endswith(".py") and (qa / name).is_file()
             and (name not in before or hashlib.sha256((qa / name).read_bytes()).hexdigest() != before[name]["sha256"])]
    assert files
    pre_hashes = {name: hashlib.sha256((qa / name).read_bytes()).hexdigest() for name in files}
    log = OUT / "verification" / args.label
    log.mkdir(parents=True, exist_ok=False)
    (log / "executed-runner.py").write_bytes(Path(__file__).read_bytes())
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(qa), str(qa / "src")]),
               E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               BLACK_CACHE_DIR=str(OWN / "tmp/black-cache"), MYPY_CACHE_DIR=str(OWN / "tmp/mypy-cache"))
    paths = [str(qa / name) for name in files]
    commands = [[sys.executable, "-B", "-m", "isort", "--profile", "black",
                 "--settings-path", str(qa / "pyproject.toml"), *([] if args.format else ["--check-only"]), *paths]]
    # Use one file per invocation to avoid a Windows process-pool hang.
    commands += [[sys.executable, "-B", "-m", "black", "--workers", "1", "--config", str(qa / "pyproject.toml"),
                  *([] if args.format else ["--check"]), path] for path in paths]
    if args.mypy:
        commands.append([sys.executable, "-B", "-m", "mypy", "--config-file", str(qa / "pyproject.toml"), "src/"])
    records = []
    for index, command in enumerate(commands):
        start = time.monotonic()
        try:
            result = subprocess.run(command, cwd=qa, env=env, capture_output=True, timeout=120)
            stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
        (log / f"{index:02}.stdout.log").write_bytes(stdout)
        (log / f"{index:02}.stderr.log").write_bytes(stderr)
        records.append(dict(command=command, returncode=code, timeout=timed_out, wall_s=round(time.monotonic() - start, 3)))
        if timed_out:
            break  # Do not launch more checks after an unconfirmed descendant state.
    payload = dict(schema="model_resolution_static/1", format_applied=args.format,
                   commands=records, failed_commands=sum(row["returncode"] != 0 for row in records),
                   pre_file_sha256=pre_hashes,
                   final_file_sha256={name: hashlib.sha256((qa / name).read_bytes()).hexdigest() for name in files},
                   key_environment_removed=True, cache_scope=str(OWN / "tmp"))
    (log / "process.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(label=args.label, failed_commands=payload["failed_commands"],
                          returncodes=[row["returncode"] for row in records],
                          wall_s=round(sum(row["wall_s"] for row in records), 3))))
    sys.exit(1 if payload["failed_commands"] else 0)


if __name__ == "__main__":
    main()
