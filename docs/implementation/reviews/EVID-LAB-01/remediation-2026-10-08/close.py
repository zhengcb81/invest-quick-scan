"""Read-only recheck of delivered worker bytes and private cleanup; final evidence index."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

IQS=Path(__file__).resolve().parents[5]
INTAKE=IQS/'docs/implementation/intake/EVID-LAB-01/2026-10-08-remediation'
REVIEWS=Path(__file__).parent
SOURCE=Path('C:/Users/郑曾波/Projects/iqs-evidence-lab')
OWN=IQS/'runs/evid-lab-remediation-2026-10-08-01'
INDEX=INTAKE/'delivery-index.json'

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text('utf-8-sig'))
def save(path,body): path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args): return subprocess.run(['git','-C',str(SOURCE),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True,check=True).stdout.decode('utf-8').strip()

if sys.argv[1:]==['--check-staged']:
    index=read(INDEX)
    for item in index['items']:
        data=subprocess.run(['git','show',':'+item['path']],cwd=IQS,capture_output=True,check=True).stdout
        assert len(data)==item['bytes'] and sha(data)==item['sha256'], 'staged byte drift: '+item['path']
    assert subprocess.run(['git','show',':'+INDEX.relative_to(IQS).as_posix()],cwd=IQS,capture_output=True,check=True).stdout==INDEX.read_bytes()
    print(json.dumps({'staged_exact_files':len(index['items']),'index_exact':True}))
    raise SystemExit(0)
if sys.argv[1:]==['--index']:
    items=[]
    for base in (INTAKE,REVIEWS):
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path==INDEX: continue
            assert not path.is_symlink() and path.resolve().is_relative_to(IQS.resolve())
            data=path.read_bytes()
            if path.suffix=='.json': json.loads(data.decode('utf-8-sig'))
            items.append({'path':path.relative_to(IQS).as_posix(),'bytes':len(data),'sha256':sha(data)})
    save(INDEX,{'schema':'iqs_evid_lab_remediation_index/1','status':'changes_requested',
        'source_result_commit':'62fe8b2f51bf498d0925b65e998c7b0a4dba7192',
        'source_received_head':'380cb496f30c72128c2cc8e3c88e36924f3c4f2c','byte_domain':'exact archived bytes, -text attributes',
        'exclusions':['this index','mutable root PWF/handoff-for-new-agent.md','.gitattributes'],'count':len(items),'items':items})
    print(json.dumps({'files_bound':len(items),'bytes':sum(i['bytes'] for i in items)}))
    raise SystemExit(0)
assert not sys.argv[1:]
cleanup=read(INTAKE/'cleanup-receipt.json')
assert cleanup['applied'] and cleanup['files_deleted']==266 and not OWN.exists()
manifest=read(INTAKE/'worker/artifacts.json')
checks=[]
for item in manifest['files']:
    data=(SOURCE/item['path']).read_bytes()
    checks.append({'path':item['path'],'bytes':len(data),'worktree_sha256':sha(data),
        'matched':len(data)==item['bytes'] and sha(data)==item['worktree_sha256']})
assert len(checks)==104 and all(c['matched'] for c in checks)
save(INTAKE/'artifact-verification-after.json',checks)
after={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'status':git('status','--porcelain=v1'),
       'artifact_matches':104,'source_written':False,
       'source_temp_root_children':len(list((SOURCE/'.temp-roots').iterdir())) if (SOURCE/'.temp-roots').exists() else 0}
assert after['head']=='380cb496f30c72128c2cc8e3c88e36924f3c4f2c' and not after['status']
save(INTAKE/'source-after.json',after)
result=read(INTAKE/'verification/result.json')
result.update(cleanup_pending=False,cleanup={'applied':True,'files_deleted':266,'directories_deleted':67,'root_absent':True},source_after=after)
save(INTAKE/'verification/result.json',result)
print(json.dumps({'source_clean':True,'source_head':after['head'],'artifact_matches':104,'private_root_absent':True,'status':result['status']}))
