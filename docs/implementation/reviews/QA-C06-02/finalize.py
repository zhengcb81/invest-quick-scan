"""Record final read-only source facts and a reproducible evidence index."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare import BASE, HEAD, RESULT, SOURCE, IQS, OWN, INTAKE, git, sha, save
from run import OUT, execute

def main():
    baseline=json.loads((INTAKE/'source-baseline.json').read_text('utf-8'))
    head=git('rev-parse','HEAD').decode().strip();status=git('status','--porcelain=v1').decode('utf-8')
    artifacts=json.loads((INTAKE/'worker/artifacts.json').read_text('utf-8'))['artifacts']
    matched=[dict(path=x['path'],matched=sha((SOURCE/x['path']).read_bytes())==x['sha256']) for x in artifacts]
    assert head==HEAD and status==baseline['status'] and all(x['matched'] for x in matched)
    changed=[x['path'] for x in json.loads((OWN/'snapshot.json').read_text('utf-8'))
       if sha((OWN/'qa'/x['path']).read_bytes())!=x['sha256']]
    assert not changed
    # A diagnostic only; never replace the worker's delivered handoff.
    document=json.loads((INTAKE/'worker/handoff.json').read_text('utf-8'))
    document['scope']['changed_paths']=baseline['changed_paths']
    document['scope']['authorized_paths']=[
        '.secrets.baseline' if x.startswith('.secrets.baseline ') else
        'tests/integration/' if x.startswith('tests/integration/ ') else
        'tests/unit/' if x.startswith('tests/unit/ ') else x
        for x in document['scope']['authorized_paths']]
    diagnosis=OWN/'handoff-scope-diagnostic.json';save(diagnosis,document)
    (OUT/'handoff-scope-diagnostic.json').write_bytes(diagnosis.read_bytes())
    row=execute('public-handoff-scope-diagnostic',[str(IQS/'scripts/parallel_handoff_cli.py'),
       '--input',str(diagnosis),'--package-id','QA-C06-02',
       '--catalog',str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json')])
    save(OUT/'final-verification.json',dict(source_head_before=HEAD,source_head_after=head,
       source_status_before=baseline['status'],source_status_after=status,
       source_artifacts=matched,snapshot_files=133,snapshot_changed_after_all_cases=changed,
       worker_repository_written=False,source_database_copied=False,paid_calls=0,external_http=0,
       diagnostic_check=row,known_sessions_exited={'67027':0,'13502':1,'76942':0},
       controller_timeout=dict(command='focused.py controller-setup-retest (4 selectors)',timeout_s=180,
           result='controller timeout: process killed and waited by subprocess.run; no product RED claimed',
           original_stdout_not_archived='execute did not catch TimeoutExpired; bounded stdout was not retained'),
       unique_worker_methods_verified=200,worker_async_case='guard initially rejected Windows asyncio socketpair; corrected retest timed out; unverified by coordinator',
       new_boundaries=dict(failed=7,passed=2),cleanup_pending=True))
    print(json.dumps(dict(source_unchanged=True,artifacts=len(matched),snapshot_files=133)))

if __name__=='__main__':main()
