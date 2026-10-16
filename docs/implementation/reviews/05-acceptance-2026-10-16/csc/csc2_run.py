"""Launch auditable tests in a small explicit environment."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LAB = ROOT / "csc2"
PY = "C:/Miniconda/python.exe"
TMP = ROOT / "tmp"
TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

def run(name, args):
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if k in os.environ}
    env.update(PATH="C:/Miniconda;C:/Windows/System32", TEMP=str(TMP), TMP=str(TMP),
               PYTHONPATH=os.pathsep.join((str(ROOT), str(LAB))), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    argv = [PY, "-B", "-X", "utf8", *args]
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=LAB, env=env, capture_output=True, timeout=180)
    end = dt.datetime.now(dt.timezone.utc).isoformat()
    row = dict(name=name, argv=argv, cwd=str(LAB), started_utc=start, ended_utc=end,
               exit_code=p.returncode, environment_keys=sorted(env))
    for suffix, raw in (("out", p.stdout), ("err", p.stderr)):
        path = LOGS / f"{name}.{suffix}.log"
        path.write_bytes(raw)
        row[suffix] = dict(path=str(path.relative_to(ROOT)), bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest())
    (LOGS / f"{name}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(row, ensure_ascii=False))
    print(p.stdout.decode("utf8", "replace")[-1600:])
    print(p.stderr.decode("utf8", "replace")[-800:])
    return p.returncode

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2:]))
