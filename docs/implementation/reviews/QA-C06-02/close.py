"""Close cleaned evidence and verify exact staged bytes; never stage all files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

IQS=Path(__file__).resolve().parents[4]
REVIEW=Path(__file__).resolve().parent
INTAKE=IQS/'docs/implementation/intake/QA-C06-02/2026-10-08'
OWN=IQS/'runs/qa-c06-02-2026-10-08-01'
INDEX=REVIEW/'artifacts.json'
def sha(x):return hashlib.sha256(x).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    cleanup=json.loads((INTAKE/'cleanup-receipt.json').read_text('utf-8-sig'))
    assert cleanup['applied'] and not OWN.exists() and cleanup['files_deleted']==518
    proof=json.loads((INTAKE/'verification/final-verification.json').read_text('utf-8'))
    assert not proof['snapshot_changed_after_all_cases'] and all(x['matched'] for x in proof['source_artifacts'])
    if '--index' in sys.argv:
        save(INTAKE/'acceptance-receipt.json',dict(schema='iqs_qa_c06_02_acceptance/1',
           verdict='partial_verified/changes_requested',source_result_commit='7e71b2cd8bbb042a72b282e83cb361a1ddcbb8b7',
           source_received_head='a12bc29bf20f5fc48df69236f2e07c3c2472bacd',
           source_written=False,cleanup_applied=True,owned_root_absent=True,owned_files_deleted=518,
           original_snapshot_files=133,original_artifacts=36,original_bytes_unchanged=True,
           worker_test_items_verified=200,worker_async_case='unverified: controller guard/time-out',
           new_boundary_test_items=dict(passed=2,failed=7),code_repair_groups=4,handoff_repair_groups=1,
           cold_stub_sends=31,bad_metadata_stub_sends=31,restart_warm_seal_extra_sends=0,
           external_http=0,paid_calls=0,downloads=0,real_identity_golden=False,real_stockwiki_joint='not_run',
           gate_closed=False,original_phase92_shared_temp_opencode_preserved=True))
        paths=sorted(p for root in (REVIEW,INTAKE) for p in root.rglob('*') if p.is_file() and p!=INDEX)
        rows=[dict(path=p.relative_to(IQS).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in paths]
        save(INDEX,dict(schema='iqs_acceptance_artifact_index/1',scope='QA-C06-02 read-only acceptance; original byte hashes',
            files=rows,excludes=['this index','root PWF files','.gitattributes','new-agent handoff'],
            worker_secrets_baseline='hash metadata only; never copied'))
        print(json.dumps(dict(indexed_files=len(rows),cleanup_applied=True)))
    if '--check-staged' in sys.argv:
        body=json.loads(INDEX.read_text('utf-8'))
        for x in body['files']:
            data=subprocess.run(['git','show',':'+x['path']],cwd=IQS,capture_output=True,check=True).stdout
            assert len(data)==x['bytes'] and sha(data)==x['sha256'],x['path']
        raw=subprocess.run(['git','show',':'+INDEX.relative_to(IQS).as_posix()],cwd=IQS,capture_output=True,check=True).stdout
        assert raw==INDEX.read_bytes()
        print(json.dumps(dict(staged_byte_hashes_matched=len(body['files']),index_exact=True)))

if __name__=='__main__':main()
