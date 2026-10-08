"""Collect actual CLI/store consistency without production data or source writes."""
import copy
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import IQS,OWN,QA,OUT,execute,save

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    checks=[]
    # Show the pre-key/pre-send semantic binding defect through the actual CLI,
    # not only the loader. New isolated company fixture, same frozen input set.
    bad=OWN/'public-cli-wrong-metadata';bad.mkdir()
    checks.append(execute('bad-metadata-inputs',[str(OWN/'setup_cli.py')],cwd=bad))
    path=bad/'quick_scan_c06_authority.json';doc=json.loads(path.read_text('utf-8'))
    qid=next(iter(doc['observation_context']['questions']))
    doc['observation_context']['questions'][qid]['metadata']['template_version']='99.0.0'
    context_raw=json.dumps(doc['observation_context'],sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    doc['observation_context_sha256']=sha(context_raw)
    path.write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
    checks.append(execute('cli-bad-metadata',[str(QA/'main_with_llm.py'),'--company','Fixture Corp',
       '--entity-id','ENT_CONTEXT_FIXTURE','--provider','openai','--config',str(bad/'questions.json'),
       '--output',str(bad/'result.json'),'--require-search','--identity-snapshot',str(bad/'identity.json'),
       '--spend-authorization',str(bad/'spend_authorization.json'),'--question-manifest',str(bad/'manifest.json'),
       '--security-scope-id','SEC_CONTEXT_FIXTURE','--c06-authority',str(path)],cwd=bad,extra={'QA100_STUB_HTTP':'1'}))
    records=[]
    for tag in ('public-cli','public-cli-wrong-metadata'):
        case=OWN/tag
        with sqlite3.connect(case/'quick_scan_work.sqlite') as db:
            db.row_factory=sqlite3.Row
            deliveries=list(db.execute('SELECT work_item_id,package_json,state FROM quick_scan_result_delivery'))
            mismatched=[]
            schema_results=[]
            for d in deliveries:
                package=json.loads(d['package_json']);obs=package['items'][0]['observation']
                refs=[dict(r) for r in db.execute('SELECT run_id,scan_id FROM work_run_ref WHERE work_item_id=?',(d['work_item_id'],))]
                match=any(r['run_id']==obs['run_id'] and r['scan_id']==obs['scan_id'] for r in refs)
                if not match:mismatched.append(dict(work_item_id=d['work_item_id'],question_id=obs['question_id'],
                    observation_run_id=obs['run_id'],observation_scan_id=obs['scan_id'],actual_refs=refs))
                # IQS public validate API uses its real published release.
                sys.path.insert(0,str(IQS/'scripts'))
                from standard_answers import validate_observation
                try:
                    validate_observation(obs,require_published=True,expected_observation_id=obs['observation_id'])
                    schema_results.append(dict(question_id=obs['question_id'],valid=True))
                except Exception as e:
                    schema_results.append(dict(question_id=obs['question_id'],valid=False,error=type(e).__name__,reason=str(e)))
                if obs['question_id']==qid:
                    (OUT/(tag+'-selected-package.json')).write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            sends=(case/'http-stub-sends.jsonl').read_text('utf-8').splitlines()
            records.append(dict(case=tag,synthetic_only=True,deliveries=len(deliveries),stub_sends=len(sends),
               run_mismatch_count=len(mismatched),run_mismatches=mismatched,iqs_public_validation=schema_results))
    # Check the worker golden through this same public validator.
    golden=json.loads((OUT.parent/'worker/golden/complete_c06_package.json').read_text('utf-8'))
    obs=golden['items'][0]['observation']
    try:
        validate_observation(obs,require_published=True,expected_observation_id=obs['observation_id'])
        result=dict(valid=True)
    except Exception as e:result=dict(valid=False,error=type(e).__name__,reason=str(e))
    changed=[]
    for x in json.loads((OWN/'snapshot.json').read_text('utf-8')):
        if sha((QA/x['path']).read_bytes())!=x['sha256']:changed.append(x['path'])
    save(OUT/'cli-consistency-result.json',dict(checks=checks,records=records,worker_golden_iqs_validation=result,
       snapshot_files=133,snapshot_changed=changed,source_written=False,paid_calls=0,external_http=0,
       real_stockwiki_joint='not_run: producer binding defects + existing SW changes_requested',cleanup_pending=True))
    assert not changed

if __name__=='__main__':main()
