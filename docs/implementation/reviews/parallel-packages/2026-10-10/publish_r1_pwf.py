"""Publish exactly four first-party Markdown documents from the approved seven."""
from pathlib import Path
import hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[5]
INTAKE=ROOT/'docs/implementation/intake/parallel-packages/2026-10-10/remediation-01'
RECEIPT=INTAKE/'documentation-publication.json'
PATHS=['task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md']
assert not RECEIPT.exists()
events=[]
def run(args):
    p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,timeout=120)
    events.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout.decode('utf-8',errors='replace'),
                   'stderr':p.stderr.decode('utf-8',errors='replace')})
    if p.returncode:raise RuntimeError(events[-1])
    return p.stdout
result={'scope':'four approved first-party Markdown; no private intake/source/database/golden export','paths':PATHS}
try:
    assert not run(['diff','--cached','--name-only']).strip()
    assert run(['rev-parse','HEAD']).decode().strip()=='9ccae89ead2cebd6e6fa93cc2316e4fd2fa623b0'
    assert run(['branch','--show-current']).decode().strip()=='master'
    assert run(['remote','get-url','origin']).decode().strip()=='https://github.com/zhengcb81/invest-quick-scan.git'
    result['working_tree_raw_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PATHS}
    run(['add','--',*PATHS])
    assert set(run(['diff','--cached','--name-only']).decode().splitlines())==set(PATHS)
    run(['diff','--cached','--check'])
    staged={p:hashlib.sha256(run(['show',':'+p])).hexdigest() for p in PATHS}
    run(['commit','-m','docs: record FACT R1 acceptance and pending EVID handoff'])
    assert not run(['diff','--cached','--name-only']).strip()
    commit=run(['rev-parse','HEAD']).decode().strip()
    assert set(run(['diff-tree','--no-commit-id','--name-only','-r',commit]).decode().splitlines())==set(PATHS)
    committed={p:hashlib.sha256(run(['show',commit+':'+p])).hexdigest() for p in PATHS}
    assert staged==committed
    run(['push','origin','HEAD:refs/heads/master'])
    remote=run(['ls-remote','--exit-code','origin','refs/heads/master']).decode().split()[0]
    assert remote==commit
    result.update(status='published',commit=commit,remote_commit=remote,staged_sha256=staged,committed_sha256=committed)
except Exception as exc:
    result.update(status='failed',error=str(exc))
    raise
finally:
    result['events']=events
    with RECEIPT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['events','staged_sha256','committed_sha256','working_tree_raw_sha256']},ensure_ascii=False))
