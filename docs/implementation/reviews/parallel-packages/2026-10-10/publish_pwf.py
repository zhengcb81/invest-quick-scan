"""Only four first-party files in the user's explicit seven-document allowlist."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'docs/implementation/intake/parallel-packages/2026-10-10'
FILES=['task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md']
ORIGIN='https://github.com/zhengcb81/invest-quick-scan.git'
assert not (OUT/'documentation-publication-03.json').exists()
LOG=OUT/'publication-logs';LOG.mkdir()
steps=[]

def run(name,args,expect=0):
    p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True)
    (LOG/(name+'.stdout.log')).write_bytes(p.stdout)
    (LOG/(name+'.stderr.log')).write_bytes(p.stderr)
    steps.append({'name':name,'args':args,'exit_code':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()})
    if p.returncode!=expect: raise RuntimeError(f'{name} git exit {p.returncode}')
    return p.stdout.decode('utf-8').strip()

try:
    origin=run('origin',['remote','get-url','origin'])
    assert origin in [ORIGIN,'git@github.com:zhengcb81/invest-quick-scan.git'],origin
    assert not run('initial-index',['diff','--cached','--name-only'])
    assert run('branch',['branch','--show-current'])=='master'
    before=run('head-before',['rev-parse','HEAD'])
    sha={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in FILES}
    run('docs-diff-check',['diff','--check','--',*FILES])
    run('stage',['add','--',*FILES])
    staged=run('staged-paths',['diff','--cached','--name-only']).splitlines()
    assert sorted(staged)==sorted(FILES),staged
    run('staged-diff-check',['diff','--cached','--check'])
    run('commit',['commit','-m','docs: record concentrated acceptance of two delivered lab packages'])
    head=run('head-after',['rev-parse','HEAD'])
    changed=run('committed-paths',['diff-tree','--no-commit-id','--name-only','-r',head]).splitlines()
    assert sorted(changed)==sorted(FILES),changed
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value for path,value in sha.items())
    run('push',['push','origin','master'])
    remote=run('remote-head',['ls-remote','origin','refs/heads/master']).split()[0]
    assert remote==head
    assert not run('final-index',['diff','--cached','--name-only'])
    result={'status':'four_explicitly_authorized_first_party_documents_committed_and_pushed',
            'before':before,'commit':head,'remote_head':remote,'origin':origin,'paths':FILES,
            'source_exported':False,'databases_or_real_golden_exported':False,
            'new_repair_cards_and_received_source_handoffs_exported':False,'steps':steps}
except Exception as exc:
    result={'status':'publication_failed','exception':type(exc).__name__,'message':str(exc),'steps':steps}
    raise
finally:
    (OUT/'documentation-publication-03.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='steps'},ensure_ascii=False))
