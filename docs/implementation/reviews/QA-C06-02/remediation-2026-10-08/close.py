"""Index this finite acceptance only and verify exact staged evidence bytes."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

IQS=Path(__file__).resolve().parents[5]
REVIEW=Path(__file__).resolve().parent
INTAKE=IQS/'docs/implementation/intake/QA-C06-02/2026-10-08-remediation'
OWN=IQS/'runs/qa-c06-remediation-2026-10-08-01'
INDEX=REVIEW/'artifacts.json'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):
    return subprocess.run(['git',*args],cwd=IQS,capture_output=True,check=True).stdout

def main():
    cleanup=json.loads((INTAKE/'cleanup-receipt.json').read_text('utf-8-sig'))
    assert cleanup['applied'] and cleanup['files_deleted']==743 and not OWN.exists()
    proof=json.loads((INTAKE/'verification/final-verification.json').read_text('utf-8'))
    assert not proof['snapshot_changed_after_all_cases'] and all(x['matched'] for x in proof['source_artifacts'])
    if '--index' in sys.argv:
        links=0
        for path in REVIEW.glob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)',path.read_text('utf-8')):
                assert (path.parent/target).resolve().exists(),target
                links+=1
        for path in REVIEW.glob('*.py'): ast.parse(path.read_text('utf-8'))
        save(INTAKE/'acceptance-receipt.json',dict(schema='iqs_qa_c06_02_remediation_acceptance/1',
            verdict='partial_verified/changes_requested',source_result_commit=proof['source_result_commit'],
            source_received_head=proof['source_head_after'],source_written=False,
            source_snapshot_files=135,worker_artifacts=47,original_bytes_unchanged=True,
            affected_passed=247,original_boundaries_passed=9,
            worker_async_confirmed=True,worker_1083_full_gate='received_only_not_reexecuted',
            adjacent_boundaries=dict(passed=1,failed=6,code_groups=4),
            normal_cli_iqs_validated=31,wrong_security_cli_stub_sends=31,wrong_security_cli_key_opens=2,
            cleanup_applied=True,owned_root_absent=True,owned_files_deleted=743,
            worker_shared_temp='historical_ownership_unproved_not_deleted',
            external_http=0,paid_calls=0,downloads=0,real_owner_golden=False,real_stockwiki_joint='not_run',
            gate_closed=False,old_roots_shared_temp_opencode_preserved=True))
        save(INTAKE/'verification/document-check.json',dict(helper_ast_valid=True,local_links_valid=links,
            cleanup_applied=True,gate_closed=False,product_tests_reexecuted_for_document_check=False))
        paths=sorted(path for root in (REVIEW,INTAKE) for path in root.rglob('*') if path.is_file() and path!=INDEX)
        rows=[dict(path=path.relative_to(IQS).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for path in paths]
        save(INDEX,dict(schema='iqs_acceptance_artifact_index/1',scope='QA-C06-02 second acceptance; received/controller bytes',
            files=rows,excludes=['this index','root PWF files','.gitattributes','new-agent handoff'],
            secrets_baseline='opaque metadata only; content never copied'))
        print(json.dumps(dict(indexed_files=len(rows),local_links_valid=links,cleanup_applied=True)))
    if '--check-staged' in sys.argv:
        document=json.loads(INDEX.read_text('utf-8'))
        for entry in document['files']:
            raw=git('show',':'+entry['path'])
            assert len(raw)==entry['bytes'] and sha(raw)==entry['sha256'],entry['path']
        assert git('show',':'+INDEX.relative_to(IQS).as_posix())==INDEX.read_bytes()
        allowed={entry['path'] for entry in document['files']}|{INDEX.relative_to(IQS).as_posix(),
            '.gitattributes','task_plan.md','findings.md','progress.md','docs/implementation/handoff-for-new-agent.md'}
        staged=set(git('diff','--cached','--name-only').decode('utf-8').splitlines())
        assert staged==allowed,(staged-allowed,allowed-staged)
        print(json.dumps(dict(staged_byte_hashes_matched=len(document['files']),index_exact=True,staged_files=len(staged))))

if __name__=='__main__': main()
