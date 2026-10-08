"""Inspect only this batch's synthetic owned databases and preserved ledgers."""
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import IQS,OWN,QA,OUT,save

def ledger(root,name):
    path=root/name
    return path.read_text('utf-8').splitlines() if path.exists() else []

def inspect_database(root):
    path=root/'quick_scan_work.sqlite'
    if not path.exists(): return None
    connection=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    connection.row_factory=sqlite3.Row
    try:
        deliveries=[dict(row) for row in connection.execute(
            'SELECT work_item_id,state,block_code,package_json FROM quick_scan_result_delivery')]
        observations=[]
        for row in deliveries:
            if row['package_json']:
                observation=json.loads(row['package_json'])['items'][0]['observation']
                observations.append(dict(question_id=observation['question_id'],
                    run_id=observation.get('run_id'),scan_id=observation.get('scan_id'),
                    claim=observation['answer']['evidence'][0].get('claim'),
                    started_at=observation['execution'].get('started_at'),state=row['state'],
                    durable_contexts=connection.execute('SELECT COUNT(*) FROM quick_scan_work_context WHERE work_item_id=?',(row['work_item_id'],)).fetchone()[0],
                    durable_answers=connection.execute('SELECT COUNT(*) FROM quick_scan_standard_answer WHERE work_item_id=?',(row['work_item_id'],)).fetchone()[0],
                    run_refs=[dict(x) for x in connection.execute('SELECT run_id,scan_id FROM work_run_ref WHERE work_item_id=?',(row['work_item_id'],))]))
        return dict(delivery_count=len(deliveries),states=[row['state'] for row in deliveries],observations=observations)
    finally: connection.close()

def main():
    root=OWN/'tmp/remaining-seven-and-mirrors'
    records=[]
    for case in sorted(root.iterdir()):
        if not case.is_dir() or case.is_symlink(): continue
        if case.name.endswith('current'): continue
        entry=dict(case=case.name,database=inspect_database(case))
        if 'security_id_cli' in case.name:
            entry.update(http_stub_sends=len(ledger(case,'http-stub-sends.jsonl')),
                key_opens=len(ledger(case,'key-opens.jsonl')),
                network_attempts=len(ledger(case,'network-attempts.jsonl')),
                work_database_created=(case/'quick_scan_work.sqlite').exists(),
                result_written=(case/'result.json').exists())
            for name in ('child.stdout.log','child.stderr.log','http-stub-sends.jsonl','key-opens.jsonl'):
                path=case/name
                if path.exists(): (OUT/('remaining-security-cli-'+name)).write_bytes(path.read_bytes())
        records.append(entry)
    save(OUT/'remaining-observed-state.json',dict(synthetic_only=True,external_http=0,records=records))
    sys.path.insert(0,str(IQS/'scripts'))
    from standard_answers import validate_observation
    selected=[]
    for case in (OWN/'tmp/affected-regression').glob('test_real_subprocess_cold_warm*'):
        if case.is_symlink() or case.name.endswith('current'): continue
        database=inspect_database(case)
        connection=sqlite3.connect((case/'quick_scan_work.sqlite').as_uri()+'?mode=ro',uri=True)
        try:
            for (raw,) in connection.execute('SELECT package_json FROM quick_scan_result_delivery'):
                package=json.loads(raw)
                observation=package['items'][0]['observation']
                validate_observation(observation,require_published=True,expected_observation_id=observation['observation_id'])
                if not selected:
                    (OUT/'normal-cli-selected-package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                selected.append(observation['question_id'])
        finally: connection.close()
        assert len(selected)==31
        assert all(any(ref['run_id']==obs['run_id'] and ref['scan_id']==obs['scan_id']
            for ref in obs['run_refs']) for obs in database['observations'])
        save(OUT/'normal-cli-iqs-validation.json',dict(synthetic_only=True,observations=len(selected),
            iqs_public_validate_passed=len(selected),all_observation_runs_durably_mapped=True,
            http_stub_sends=len(ledger(case,'http-stub-sends.jsonl')),
            network_attempts=len(ledger(case,'network-attempts.jsonl')),
            real_stockwiki_import_ack_ui='not_run'))
    assert len(selected)==31
    print(json.dumps(dict(remaining_owned_cases=len(records),normal_iqs_validated=len(selected))))

if __name__=='__main__': main()
