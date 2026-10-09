"""Read-only, exact known-file comparison to the already published SW commit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
SOURCE = Path('C:/Users/郑曾波/Projects/StockWiki')
COMMIT = '6c46f03b486d215d696d32bee618793bc7fcb410'
PATHS = (
    'tests/test_quick_scan_profiles.py', 'tests/test_swr_profiles.py',
    'tests/test_quick_scan_observations.py', 'tests/test_quick_scan_issuer_bridge.py',
    'stockwiki/quick_scan_profiles.py', 'stockwiki/quick_scan_import.py',
    'stockwiki/quick_scan_observations.py', 'stockwiki/quick_scan_store.py',
    'stockwiki/quick_scan_schema.py', 'stockwiki/quick_scan_query.py',
    'stockwiki/quick_scan_freshness.py',
)
env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
records = []
for relative in PATHS:
    command = ['git', '--git-dir=' + str(SOURCE / '.git'), '--work-tree=' + str(SOURCE),
               'show', COMMIT + ':' + relative]
    process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                             timeout=30, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if process.returncode:
        raise RuntimeError('read-only Git show failed for ' + relative)
    baseline, candidate = process.stdout, (ROOT / 'runs/w15a/sw' / relative).read_bytes()
    working = (SOURCE / relative).read_bytes()
    records.append(dict(path=relative, baseline_blob_sha256=hashlib.sha256(baseline).hexdigest(),
                        candidate_execution_sha256=hashlib.sha256(candidate).hexdigest(),
                        source_working_sha256=hashlib.sha256(working).hexdigest(),
                        blob_raw_equal=baseline == candidate,
                        blob_LF_equal=baseline.replace(b'\r\n', b'\n') == candidate.replace(b'\r\n', b'\n'),
                        source_working_raw_equal=working == candidate))
result = dict(source_commit=COMMIT, read_only=True, baseline_test_execution=False,
              secret_files_read=False, records=records)
(OUT / 'published-profile-baseline-01.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
