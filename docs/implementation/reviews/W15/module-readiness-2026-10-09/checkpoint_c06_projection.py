"""One-time exact-byte private progress archive, not a production release."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    process=OUT/'contract-projection-green-03.process.json'
    result=json.loads(process.read_bytes())
    assert result['returncode']==0 and result['terminal_confirmed'] and result['source_unchanged']
    executed=json.loads((OUT/'contract-projection-green-03.sources.json').read_bytes())
    baseline=json.loads((OUT/'inputs-01.json').read_bytes())
    for row in baseline['IQS_nonsecret_inputs']:
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
        assert sha((ROOT/row['path']).read_bytes())==row['execution_sha256']
    snapshot=OUT/'private-source-02'
    record=OUT/'checkpoint-02.json'
    assert not snapshot.exists() and not record.exists()
    names=('scripts/query_contract.py','schemas/quick_scan/query-v2.schema.json',
           'tests/test_query_contract_v2.py','questions/metric-registry.json')
    frozen=[]
    for name in names:
        raw=(OWN/'iqs'/name).read_bytes()
        assert sha(raw)==executed[str(Path(name))]
        target=snapshot/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        frozen.append({'path':name,'bytes':len(raw),'execution_sha256':sha(raw)})
    guard=(OWN/'guard/sitecustomize.py').read_bytes()
    assert sha(guard)==result['actual_guard_raw_sha256']
    (snapshot/'isolation-guard.py').write_bytes(guard)
    record.write_text(json.dumps({'state':'private_in_progress_not_reviewed_not_published',
        'snapshot':frozen,'guard_raw_sha256':sha(guard),'pytest_passed':62,'pytest_wall_s':0.66,
        'actual_pid':result['pid'],'process_sha256':sha(process.read_bytes()),
        'original_public_IQS_inputs_unchanged':True,'source_written':False,'API_requests':0,
        'real_company_golden':False,'synthetic_nonempty_projection_verified':True,
        'production_subject_sidecar_implemented':False,'full_C06_validated':False,
        'whole_W15_complete':False,'owned_runtime_keep':str(OWN)},indent=2)+'\n','utf-8')
    print(json.dumps({'private_checkpoint':True,'published':False,'passed':62,'owned_runtime_keep':str(OWN)}))


if __name__=='__main__':
    main()
