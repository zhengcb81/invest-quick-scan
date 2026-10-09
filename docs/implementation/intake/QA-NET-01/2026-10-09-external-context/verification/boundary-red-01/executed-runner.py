"""One guarded affected batch; keep original RED and exact execution bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--select")
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args()
    assert args.label.replace("-", "").isalnum()
    assert OWN.is_dir() and not OWN.is_symlink()
    for name in args.tests:
        path = (OWN / "qa" / name).resolve()
        assert path.is_relative_to(OWN / "qa/tests") and path.is_file()
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(OWN / "qa"), str(OWN / "qa/src")]), E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", STOCKQA_RUN_LIVE_E2E="0")
    names = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))["files"]
    watched = {name: (OWN / "qa" / name).read_bytes() for name in names if (OWN / "qa" / name).is_file()}
    frozen = {name: hashlib.sha256(raw).hexdigest() for name, raw in watched.items()}
    dest = OUT / "verification" / args.label
    dest.mkdir(parents=True, exist_ok=False)
    for name, raw in watched.items():
        path = dest / "executed-source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (dest / "executed-runner.py").write_bytes(Path(__file__).read_bytes())
    (dest / "executed-guard.py").write_bytes((OWN / "guard/sitecustomize.py").read_bytes())
    command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", *args.tests, "-q", "-o", "addopts=", "-p", "no:cacheprovider", "-p", "pytest_asyncio.plugin", "--basetemp=" + str(OWN / "tmp" / args.label), "--junitxml=" + str(dest / "junit.xml")]
    if args.select:
        command += ["-k", args.select]
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=OWN / "qa", env=env, capture_output=True, timeout=300)
        stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
    (dest / "stdout.log").write_bytes(stdout)
    (dest / "stderr.log").write_bytes(stderr)
    receipt = dict(command=command, returncode=code, timeout=timed_out, wall_s=round(time.monotonic() - start, 3), key_environment_removed=True, executed_source_hashes=frozen, executed_source_unchanged=all(hashlib.sha256((OWN / "qa" / n).read_bytes()).hexdigest() == sha for n, sha in frozen.items()), owner_files_written=False)
    (dest / "process.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("returncode", "timeout", "wall_s", "executed_source_unchanged")}))
    sys.exit(code if code is not None else 124)


if __name__ == "__main__":
    main()
