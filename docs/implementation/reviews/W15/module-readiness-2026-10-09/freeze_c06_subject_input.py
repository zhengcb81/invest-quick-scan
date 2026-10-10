"""Explicitly admit ONE private additive reader hunk; old freeze stays intact."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
OWN=ROOT/'runs/c15a'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    name='stockwiki/quick_scan_observations.py'
    baseline=json.loads((OUT/'stockwiki-inputs-01.json').read_bytes())['files']
    original=next(row['execution_sha256'] for row in baseline if row['path']==name)
    raw=(OWN/'sw'/name).read_bytes()
    candidate=sha(raw)
    # Original source remains the exact baseline outside the owned candidate.
    assert sha((Path('C:/Users/郑曾波/Projects/StockWiki')/name).read_bytes())==original
    for row in baseline:
        if row['path']!=name:
            assert sha((OWN/'sw'/row['path']).read_bytes())==row['execution_sha256']
    target=OUT/'subject-candidate-inputs-01.json'
    assert not target.exists()
    target.write_text(json.dumps({'StockWiki':{name:{'original_sha256':original,
        'candidate_sha256':candidate,'change':'READ_SCHEMA_VERSION extension point only; legacy migration stays2'}},
        'unmodified_baseline_files':177,'production_source_changed':False,
        'private_schema3_not_published':True},indent=2)+'\n','utf-8')
    print(json.dumps({'declared_candidate':name,'unchanged_baseline':177,'source_written':False}))


if __name__=='__main__':
    main()
