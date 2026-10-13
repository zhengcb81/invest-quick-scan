"""Read-only check of cards, locks, scopes and handoff templates; no worker tests."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
P=Path(__file__).resolve().parent
catalog=json.loads((P/'manifest.json').read_bytes());lock=json.loads((P/'inputs.lock.json').read_bytes())
seen=set()
for row in lock['files']:
    key=(row['repository'],row['path']);assert key not in seen;seen.add(key)
    assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts
    raw=(Path(lock['snapshot_root'])/row['repository']/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
scopes=[Path(e['write_scope']).resolve() for e in catalog['packages']]
assert len(set(scopes))==3
for a in scopes:
    for b in scopes:
        assert a==b or not a.is_relative_to(b)
checks=[]
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC'}}
env['PYTHONDONTWRITEBYTECODE']='1'
for e in catalog['packages']:
    assert (P/e['document']).is_file() and all(repo in lock['repositories'] for repo in e['input_repositories'])
    for dep in ('common-rules.md','integration-contract.md','inputs.lock.json','manifest.json',e['id']+'.handoff.template.json'):
        assert dep in (P/e['document']).read_text('utf-8')
    result=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(lock['repositories']['iqs']['source_root'])/'scripts/parallel_handoff_cli.py'),'--catalog',str(P/'manifest.json'),'--package-id',e['id'],'--input',str(P/(e['id']+'.handoff.template.json'))],env=env,capture_output=True,timeout=30)
    assert result.returncode==0,result.stdout.decode('utf-8')+result.stderr.decode('utf-8')
    checks.append(dict(package_id=e['id'],template_shape_exit_code=0,validation_scope='handoff_shape_and_declared_scope_only'))
for path in P.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text('utf-8')):
        if ':' not in link and not link.startswith('#'):assert (P/link).is_file(), 'missing_link:'+link
route=json.loads((P/'ROUTE-E2E-03.targets.json').read_bytes())['records']
chain=json.loads((P/'CHAIN-SOURCE-03.targets.json').read_bytes())['records']
assert len(route)==47 and len({r['case_id'] for r in route})==47
assert len(chain)==36 and len({r['record_id'] for r in chain})==36
print(json.dumps(dict(frozen_files=len(seen),nonoverlapping_roots=True,local_links_valid=True,route_baseline_cases=47,chain_baseline_slots=36,templates=checks,worker_product_tests_run=False,workers_dispatched=False,API_calls=0),ensure_ascii=False))
