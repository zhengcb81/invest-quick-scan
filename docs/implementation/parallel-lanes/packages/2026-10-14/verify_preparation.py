"""One package preparation check. Does not execute worker products or APIs."""
from pathlib import Path
import hashlib, json, os, re, stat, subprocess, sys

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
catalog = json.loads((P / 'manifest.json').read_bytes())
lock = json.loads((P / 'inputs.lock.json').read_bytes())
assert catalog['workers_dispatched'] is False
seen = set()
for row in lock['files']:
    assert set(row) == {'repository', 'path', 'bytes', 'sha256'}
    key = row['repository'], row['path']
    assert key not in seen
    seen.add(key)
    rel = Path(row['path'])
    assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in row['path'] and ':' not in row['path']
    path = Path(lock['snapshot_root']) / row['repository'] / rel
    assert path.resolve().is_relative_to(Path(lock['snapshot_root']).resolve())
    info = path.lstat()
    assert not path.is_symlink() and not getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']

scopes = [Path(p['write_scope']).resolve() for p in catalog['packages']]
assert len(set(scopes)) == 3
for a in scopes:
    for b in scopes: assert a == b or not a.is_relative_to(b)

checks = []
env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC'}}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
for package in catalog['packages']:
    text = (P / package['document']).read_text('utf-8')
    for dependency in ('common-rules.md','integration-contract.md','manifest.json','inputs.lock.json',package['id']+'.targets.json',package['id']+'.handoff.template.json'):
        assert dependency in text
    assert set(package['input_repositories']).issubset(lock['repositories'])
    process = subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'scripts/parallel_handoff_cli.py'),'--catalog',str(P/'manifest.json'),'--package-id',package['id'],'--input',str(P/(package['id']+'.handoff.template.json'))],env=env,capture_output=True,timeout=30)
    assert process.returncode == 0, process.stdout.decode('utf-8') + process.stderr.decode('utf-8')
    checks.append({'package_id':package['id'],'template_shape_exit_code':0,'validation_scope':'handoff_shape_and_declared_scope_only'})
for path in P.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text('utf-8')):
        if ':' not in link and not link.startswith('#'): assert (P/link).is_file(), 'missing link:' + link

targets = {p['id']:json.loads((P/(p['id']+'.targets.json')).read_bytes()) for p in catalog['packages']}
assert len(targets['BLIND-INPUT-04']['records']) == 12
assert len(targets['FIN-PROVENANCE-03']['records']) == 90
chain = targets['CHAIN-VERIFY-04']
assert (len(chain['records']),len(chain['claim_ids']),len(chain['gap_ids'])) == (36,59,52)
assert len(set(chain['claim_ids'])) == 59 and len(set(chain['gap_ids'])) == 52
for company in ('alphabet','catl','cncb_h'):
    for name in ('manifest.json','questions.json'):
        assert ('fin',f'fixtures/locked-inputs/runs/c16b/formal-routes/{company}-questions/{name}') in seen
assert not any('runtime-reuse.json' in r['path'] and r['repository'] != 'iqs' for r in lock['files'])
print(json.dumps({'frozen_files':len(seen),'raw_bytes_verified':True,'nonoverlapping_roots':True,'local_links_valid':True,'targets':{'blind_scenarios':12,'financial_questions':90,'chain_slots':36,'chain_claims':59,'chain_gaps':52},'six_real_FIN_dependencies_included':True,'templates':checks,'worker_product_tests_run':False,'workers_dispatched':False,'API_calls':0},ensure_ascii=False))
