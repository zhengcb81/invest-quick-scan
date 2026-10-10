"""Freeze one nonsecret canonical metric resource for the existing validator."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
source=ROOT/'questions/metric-registry.json'
target=ROOT/'runs/c15a/iqs/questions/metric-registry.json'
out=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09/metric-input-01.json'
assert not target.exists() and not out.exists()
raw=source.read_bytes()
target.parent.mkdir(exist_ok=True)
target.write_bytes(raw)
out.write_text(json.dumps({'owner':'invest-quick-scan','source_path':'questions/metric-registry.json',
    'execution_path':str(target.relative_to(ROOT)),
    'source_and_execution_sha256':hashlib.sha256(raw).hexdigest(),
    'source_written':False,'production_database_access':False,'API_requests':0},indent=2)+'\n','utf-8')
print(out)
