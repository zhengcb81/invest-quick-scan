"""Read-only candidate execution; artifacts only in own review roots."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[6]
OWN = ROOT / 'runs/w15a'
OUT = Path(__file__).resolve().parent
PROBE = OWN / 'review-owned/test_capacity_anchor.py'
PATHS = [
    ROOT / 'scripts/route_store_handoff.py',
    *[ROOT / ('schemas/quick_scan/' + x) for x in ('route-store-validation.schema.json', 'module-refresh.schema.json', 'route-store-cli.schema.json')],
    *[OWN / ('sw/stockwiki/' + x) for x in ('quick_scan_store.py', 'quick_scan_schema.py', 'quick_scan_backup_manifest.py', 'quick_scan_route_validation.py', 'quick_scan_routes.py', 'quick_scan_module_refresh.py', 'quick_scan_routes_cli.py', 'cli_parsers/quick_scan.py')],
    *[OWN / ('qa/' + x) for x in ('src/utils/quick_scan_owner_refresh.py', 'src/utils/quick_scan_owner_refresh_journal.py', 'src/utils/quick_scan_work_store.py', 'src/utils/quick_scan_work_transport.py', 'src/runners/llm_runner.py', 'src/core/qa_engine.py', 'main_with_llm.py')],
]
def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in PATHS}
before = hashes()
env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
temp = OWN / 'review-owned/tmp'
temp.mkdir(parents=True, exist_ok=True)
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', IQS_W15_OWN=str(OWN),
           PYTHONPATH=os.pathsep.join(map(str, (OWN / 'guard', OWN / 'qa', OWN / 'sw'))),
           TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
command = [sys.executable, '-B', '-X', 'utf8', '-m', 'pytest', '-c', str(OWN / 'pytest.ini'),
           '-p', 'no:cacheprovider', '--basetemp', str(OWN / 'review-owned/capacity-anchor-02'),
           '-q', '-s', str(PROBE)]
start = time.monotonic()
process = subprocess.Popen(command, cwd=OWN / 'qa', env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
stdout, stderr = process.communicate(timeout=90)
after = hashes()
(OUT / 'capacity-anchor-02.stdout.log').write_bytes(stdout)
(OUT / 'capacity-anchor-02.stderr.log').write_bytes(stderr)
result = dict(returncode=process.returncode, pid=process.pid, terminal_confirmed=True,
              wall_s=round(time.monotonic()-start, 3), command=command,
              execution_sha256=before, source_unchanged=before == after,
              credentials_inherited=False, Python_network_guard=True, foreign_SQLite_guard=True,
              whole_OS_guard_claim=False, HTTP_calls=0,
              guard_sha256=hashlib.sha256((OWN / 'guard/sitecustomize.py').read_bytes()).hexdigest())
(OUT / 'capacity-anchor-02.process.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(stdout.decode('utf-8', errors='replace')[-6500:])
print(stderr.decode('utf-8', errors='replace')[-1000:])
print(json.dumps(result, ensure_ascii=False))
