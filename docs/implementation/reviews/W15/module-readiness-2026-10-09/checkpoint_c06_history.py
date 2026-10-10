"""One-time raw private checkpoint of actual owner-history test execution."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    owner=json.loads((OUT/'owner-history-fault-01.process.json').read_bytes())
    pure=json.loads((OUT/'contract-snapshot-01.process.json').read_bytes())
    for result in (owner,pure):
        assert result['returncode']==0 and result['terminal_confirmed'] and result['source_unchanged']
        assert result['API_requests']==0 and not result['real_company_golden']
    executed=json.loads((OUT/'owner-history-fault-01.sources.json').read_bytes())
    contract=json.loads((OUT/'contract-snapshot-01.sources.json').read_bytes())
    for row in json.loads((OUT/'inputs-01.json').read_bytes())['IQS_nonsecret_inputs']:
        assert sha((ROOT/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    for row in json.loads((OUT/'stockwiki-inputs-01.json').read_bytes())['files']:
        assert sha((OWN/'sw'/row['path']).read_bytes())==row['execution_sha256']
    target=OUT/'private-owner-reader-02'
    record=OUT/'owner-reader-checkpoint-02.json'
    assert not target.exists() and not record.exists()
    paths={'StockWiki':('stockwiki/quick_scan_query_v2.py','tests/test_quick_scan_query_v2.py'),
           'IQS':('scripts/query_contract.py','tests/test_query_contract_v2.py',
                  'schemas/quick_scan/query-v2.schema.json','questions/metric-registry.json')}
    frozen=[]
    for namespace,names in paths.items():
        root=OWN/('sw' if namespace=='StockWiki' else 'iqs')
        for name in names:
            raw=(root/name).read_bytes()
            assert sha(raw)==executed[namespace][name]
            if namespace=='IQS':
                assert sha(raw)==contract[str(Path(name))]
            dest=target/namespace/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
            frozen.append({'source_namespace':namespace,'source_path':name,
                'snapshot_path':dest.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    guard=(OWN/'guard/sitecustomize.py').read_bytes()
    assert sha(guard)==owner['actual_guard_raw_sha256']==pure['actual_guard_raw_sha256']
    (target/'isolation-guard.py').write_bytes(guard)
    record.write_text(json.dumps({'state':'private_not_reviewed_not_published',
        'scope':'actual_component_synthetic_unbound_history_and_process_retained_snapshot',
        'source_candidates':frozen,'tests':[
            {'label':'owner-history-fault-01','pytest_passed':33,'pytest_wall_s':20.22,
             'child_pid':owner['pid'],'child_returncode':owner['returncode'],
             'process_sha256':sha((OUT/'owner-history-fault-01.process.json').read_bytes()),
             'sources_sha256':owner['sources_sha256']},
            {'label':'contract-snapshot-01','pytest_passed':65,'pytest_wall_s':0.89,
             'child_pid':pure['pid'],'child_returncode':pure['returncode'],
             'process_sha256':sha((OUT/'contract-snapshot-01.process.json').read_bytes()),
             'sources_sha256':pure['sources_sha256']}],
        'counts_not_a_combined_accuracy_rate':True,'guard_raw_sha256':sha(guard),
        'original_StockWiki_files_unchanged':178,'original_IQS_files_unchanged':64,
        'nonempty_legacy_original_history':True,'current_bound_observation_projection':False,
        'before_send_subject_sidecar_implemented':False,'snapshot_scope':'bounded_process_only',
        'durable_public_snapshot_supported':False,'public_c06_envelope_validated':False,
        'source_published':False,'real_company_golden':False,'API_requests':0,
        'temporary_root_retained_for_same_node':'runs/c15a'},indent=2)+'\n','utf-8')
    print(json.dumps({'private_checkpoint':True,'published':False,
                      'owner_passed':33,'contract_passed':65,'owned_runtime_keep':'runs/c15a'}))


if __name__=='__main__':
    main()
