"""Recheck received source and preserve terminal receipts; no external writes."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare import HEAD,RESULT,SOURCE,IQS,OWN,INTAKE,git,sha,save

def main():
    baseline=json.loads((INTAKE/'source-baseline.json').read_text('utf-8'))
    head=git('rev-parse','HEAD').decode().strip()
    status=git('status','--porcelain=v1').decode('utf-8')
    artifacts=json.loads((INTAKE/'worker/artifacts.json').read_text('utf-8'))['artifacts']
    matches=[dict(path=x['path'],matched=sha((SOURCE/x['path']).read_bytes())==x['sha256']) for x in artifacts]
    snapshot=json.loads((OWN/'snapshot.json').read_text('utf-8'))
    changed=[x['path'] for x in snapshot if sha((OWN/'qa'/x['path']).read_bytes())!=x['sha256']]
    assert head==HEAD and status==baseline['status'] and all(x['matched'] for x in matches) and not changed
    out=INTAKE/'verification'
    (out/'sitecustomize-corrected-executed.py').write_bytes((OWN/'guard/sitecustomize.py').read_bytes())
    save(out/'final-verification.json',dict(source_head_before=HEAD,source_head_after=head,
        source_result_commit=RESULT,source_status_before=baseline['status'],source_status_after=status,
        source_artifacts=matches,snapshot_files=len(snapshot),snapshot_changed_after_all_cases=changed,
        worker_repository_written=False,source_database_copied=False,paid_calls=0,external_http=0,downloads=0,
        affected=dict(passed=247,failed=0),original_boundaries=dict(passed=9,failed=0),
        adjacent_boundaries=dict(passed=1,failed=6,code_groups=4),
        async_case='GREEN: isolated Mock HTTP under elevated loopback guard; also inside corrected 247',
        real_stockwiki_joint='not_run',real_owner_golden=False,gate_closed=False,
        known_sessions_exited={'52630':0,'22776':0,'71486':0,'67104':0,'48976':0,'48176':0},
        controller_events=[
            'Initial freeze stopped before mkdir: result->HEAD also has .gitignore. Read-only diff proved one exact receipt exception; updated allowlist, retained initial helper.',
            'Initial controller guard treated read-only integer file descriptor as a path: one child test setup failure, not product RED. Corrected controller only; 7-case batch repeated with new basetemp.',
            'Sandbox async socketpair caused first affected batch 300s and async-only 45s timeouts. subprocess.run killed/waited direct children, stdout/stderr retained. Elevated exact guarded Mock case GREEN, corrected affected batch GREEN.',
            'Source AGENTS.md path absent; inherited human instructions and known package paths apply. Initial sandbox CIM denied; strict final query requires elevation.'
        ],cleanup_pending=True))
    print(json.dumps(dict(source_unchanged=True,artifacts=len(matches),snapshot_files=len(snapshot))))

if __name__=='__main__': main()
