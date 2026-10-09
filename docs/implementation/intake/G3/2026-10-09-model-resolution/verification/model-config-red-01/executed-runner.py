"""Guarded affected tests; labels never overwrite previous raw results."""
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
    parser.add_argument("--select")
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args()
    assert args.label.replace("-", "").replace("_", "").isalnum()
    assert OWN.is_dir() and not OWN.is_symlink()
    log = OWN / "logs/worker" / args.label
    log.mkdir(parents=True, exist_ok=False)
    for name in args.tests:
        path = (OWN / "qa" / name).resolve()
        assert path.is_relative_to(OWN / "qa/tests") and path.is_file()
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(OWN / "qa"), str(OWN / "qa/src")]),
               E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"),
               TMPDIR=str(OWN / "tmp"), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", STOCKQA_RUN_LIVE_E2E="0")
    scope = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))
    watched = [name for name in scope["files"] if (OWN / "qa" / name).is_file()]
    hashes = {name: hashlib.sha256((OWN / "qa" / name).read_bytes()).hexdigest() for name in watched}
    guard_sha = hashlib.sha256((OWN / "guard/sitecustomize.py").read_bytes()).hexdigest()
    command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", *args.tests,
               "-q", "-o", "addopts=", "-p", "no:cacheprovider", "-p", "pytest_asyncio.plugin",
               "--basetemp=" + str(OWN / "tmp" / args.label), "--junitxml=" + str(log / "junit.xml")]
    if args.select:
        command += ["-k", args.select]
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=OWN / "qa", env=env, capture_output=True, timeout=300)
        stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
    (log / "stdout.log").write_bytes(stdout)
    (log / "stderr.log").write_bytes(stderr)
    receipt = dict(command=command, returncode=code, timeout=timed_out,
                   wall_s=round(time.monotonic() - start, 3), key_environment_removed=True,
                   external_source_written=False, executed_source_hashes=hashes,
                   executed_guard_sha256=guard_sha,
                   executed_source_unchanged=all(hashlib.sha256((OWN / "qa" / name).read_bytes()).hexdigest() == value
                                                 for name, value in hashes.items()))
    (log / "process.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archived = OUT / "verification" / args.label
    archived.mkdir(parents=True, exist_ok=False)
    (archived / "executed-runner.py").write_bytes(Path(__file__).read_bytes())
    for path in log.iterdir():
        assert path.is_file() and not path.is_symlink()
        (archived / path.name).write_bytes(path.read_bytes())
    print(json.dumps({key: receipt[key] for key in ("returncode", "timeout", "wall_s", "executed_source_unchanged")}))
    sys.exit(code if code is not None else 124)


if __name__ == "__main__":
    main()
