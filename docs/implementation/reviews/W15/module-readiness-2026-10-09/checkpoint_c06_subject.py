"""Freeze actual private two-phase primitive execution, not production release."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    labels=('owner-subject-final-01','owner-history-regression-01','contract-subject-01')
    actual=[json.loads((OUT/(label+'.process.json')).read_bytes()) for label in labels]
    for result in actual:
        assert result['returncode']==0 and result['terminal_confirmed'] and result['source_unchanged']
        assert result['API_requests']==0 and not result['real_company_golden']
    executed=json.loads((OUT/'owner-subject-final-01.sources.json').read_bytes())
    regression=json.loads((OUT/'owner-history-regression-01.sources.json').read_bytes())
    assert executed==regression
    pure=json.loads((OUT/'contract-subject-01.sources.json').read_bytes())
    admitted=json.loads((OUT/'subject-candidate-inputs-01.json').read_bytes())
    for row in json.loads((OUT/'stockwiki-inputs-01.json').read_bytes())['files']:
        candidate=admitted['StockWiki'].get(row['path'])
        expected=row['execution_sha256'] if candidate is None else candidate['candidate_sha256']
        assert sha((OWN/'sw'/row['path']).read_bytes())==expected
    for row in json.loads((OUT/'inputs-01.json').read_bytes())['IQS_nonsecret_inputs']:
        assert sha((ROOT/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    paths={'StockWiki':('stockwiki/quick_scan_observations.py','stockwiki/quick_scan_subject_dispatch.py',
        'stockwiki/quick_scan_query_v2.py','tests/test_quick_scan_subject_dispatch.py',
        'tests/test_quick_scan_query_v2.py'),
        'IQS':('scripts/query_contract.py','scripts/subject_dispatch_contract.py',
        'tests/test_query_contract_v2.py','schemas/quick_scan/query-v2.schema.json','questions/metric-registry.json')}
    snapshot=OUT/'private-subject-01'
    record=OUT/'subject-checkpoint-01.json'
    assert not snapshot.exists() and not record.exists()
    frozen=[]
    for namespace,names in paths.items():
        root=OWN/('sw' if namespace=='StockWiki' else 'iqs')
        for name in names:
            raw=(root/name).read_bytes()
            assert sha(raw)==executed[namespace][name]
            if namespace=='IQS': assert sha(raw)==pure[str(Path(name))]
            dest=snapshot/namespace/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
            frozen.append({'source_namespace':namespace,'source_path':name,
                'snapshot_path':dest.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    name='stockwiki/quick_scan_observations.py'
    original=(Path('C:/Users/郑曾波/Projects/StockWiki')/name).read_bytes()
    assert sha(original)==admitted['StockWiki'][name]['original_sha256']
    dest=snapshot/'StockWiki-original'/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(original)
    guard=(OWN/'guard/sitecustomize.py').read_bytes()
    assert all(sha(guard)==result['actual_guard_raw_sha256'] for result in actual)
    (snapshot/'isolation-guard.py').write_bytes(guard)
    record.write_text(json.dumps({'state':'private_not_reviewed_not_published',
        'scope':'two_phase_owner_dispatch_primitive_atomic_import_and_read_projection',
        'source_candidates':frozen,'tests':[{'label':label,'pytest_passed':count,'pytest_wall_s':wall,
            'child_pid':result['pid'],'child_returncode':result['returncode'],
            'process_sha256':sha((OUT/(label+'.process.json')).read_bytes()),
            'sources_sha256':result['sources_sha256']}
            for label,count,wall,result in zip(labels,(23,33,65),(6.62,45.93,1.49),actual)],
        'counts_are_separate_software_batches_not_accuracy_rate':True,
        'guard_raw_sha256':sha(guard),'original_StockWiki_inputs':178,
        'unchanged_original_StockWiki_inputs':177,'declared_original_candidate_paths':list(admitted['StockWiki']),
        'original_IQS_inputs_unchanged':64,'schema_version':3,
        'actual_owner_transaction_bound_projection':True,
        'before_send_HTTP_producer_integrated':False,'public_expected_authority_adapter_integrated':False,
        'public_C06_validated':False,'source_published':False,'real_company_golden':False,
        'API_requests':0,'owned_runtime_keep':'runs/c15a'},indent=2)+'\n','utf-8')
    print(json.dumps({'private_checkpoint':True,'owner_binding':23,'legacy_reader':33,
        'contract':65,'published':False,'owned_runtime_keep':'runs/c15a'}))


if __name__=='__main__':
    main()
