"""Original native ACK boundary, seeded by isolated owner fixtures; no model I/O."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.dashboard_execution import ExecutionGateway, DashboardExecutionError

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent/'StockQAbyLLM'
TARGET = {'component':'StockWiki','namespace':'quick_scan','store_id':'stockwiki-test-store'}


@pytest.fixture
def delivery(tmp_path):
    if not (SOURCE/'tests/unit/test_quick_scan_work_store.py').is_file():
        pytest.skip('Explicit original StockQA fixture dependency')
    script = r'''
import hashlib,json,sys
from pathlib import Path
sys.path[:0]=[sys.argv[1],str(Path(sys.argv[1])/'tests/unit')]
from test_quick_scan_work_store import (_checkpointed_work_item,_c06_package_for_checkpoint,_ack_for_package,
 _created,_successful_search_attempt,_answer_for,_readdress_c06_package)
base=Path(sys.argv[2]);store,item,cp,clock=_checkpointed_work_item(base)
items=[(item,cp)]
other=_created(store,generation=2)
lease,attempt,receipt=_successful_search_attempt(store,other['work_item_id'])
cp2=store.save_answer_checkpoint(other['work_item_id'],lease,attempt['attempt_id'],answer=_answer_for(other),execution_receipt=receipt)
items.append((other,cp2));mapping={};acks=[]
for item,checkpoint in items:
 package=_c06_package_for_checkpoint(checkpoint)
 observation='obs_'+hashlib.sha256(item['work_item_id'].encode()).hexdigest()
 package['items'][0]['observation_id']=observation
 package['items'][0]['observation']['observation_id']=observation
 _readdress_c06_package(package)
 store.prepare_result_delivery(item['work_item_id'],package)
 mapping[package['items'][0]['observation_id']]=item['work_item_id'];acks.append(_ack_for_package(package))
print(json.dumps({'work_store':str(store.path),'work_item_ids':mapping,'receipt':{'acks':acks}}))
'''
    from scripts.dashboard_owner import _env
    done = subprocess.run([sys.executable,'-B','-c',script,str(SOURCE),str(tmp_path)],
        capture_output=True,text=True,encoding='utf8',timeout=40,env=_env())
    assert done.returncode == 0, done.stderr
    data = json.loads(done.stdout)
    gateway = ExecutionGateway({'stockqa_root':str(SOURCE),'stockqa_python':sys.executable})
    bundle = {k:v for k,v in data.items() if k!='receipt'}
    return gateway,bundle,data['receipt']


def test_original_target_binding_and_exact_ack_replay(delivery):
    gateway,bundle,receipt=delivery
    assert gateway.bind_delivery_consumer(bundle,TARGET,'operator-config:isolated-dashboard-test')['status']=='bound'
    assert gateway.acknowledge_delivery(bundle,receipt)['status']=='delivered'
    before=Path(bundle['work_store']).read_bytes()
    assert gateway.acknowledge_delivery(bundle,receipt)['status']=='delivered'
    assert Path(bundle['work_store']).read_bytes()==before


@pytest.mark.parametrize('ready_count,missing_work', [(n, missing) for n in [0, 1, 2]
                                                    for missing in [False, 'row', 'omitted']] + [(0, 'all')])
def test_scope_export_keeps_unfinished_questions_without_blocking_sealed_answers(tmp_path, monkeypatch, ready_count, missing_work):
    import hashlib
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    import frozen_release_projection
    from scripts.dashboard_delivery import export_deliveries
    monkeypatch.setattr(frozen_release_projection, 'create_projection', lambda manifest, **kwargs: {'fixture': 'release'})
    for name, value in {'admission': {'work_store': str(tmp_path/'ledger'), 'budget_policy_file': str(tmp_path/'policy')},
                        'request': {'entity_id': 'ENT_TEST', 'question_ids': ['Q1', 'Q2'] + (['Q3'] if missing_work in {'row','omitted'} else [])}, 'manifest': {}}.items():
        (tmp_path/name).write_text(json.dumps(value), encoding='utf8')
    (tmp_path/'ledger').write_bytes(b'test boundary')
    (tmp_path/'policy').write_text('{}', encoding='utf8')
    bundle = {'entity_id': 'ENT_TEST', 'admission_config': str(tmp_path/'admission'),
              'inspection_request': str(tmp_path/'request'), 'manifest': str(tmp_path/'manifest')}
    gateway = ExecutionGateway({'stockqa_root': str(SOURCE), 'iqs_release_root': str(ROOT),
                                'state_root': str(tmp_path/'state'), 'bundles': {'B': bundle}})
    calls = []
    def native(command, root, runtime, *, input_value=None):
        calls.append(command)
        if len(calls) == 1:
            return {'protocol': 'stockqa.refresh_inspection/1.0.0', 'reservation_created': False,
                    'API_requests': 0, 'work_items': [] if missing_work=='all' else [{'question_id': f'Q{i+1}', 'work_item_id': f'WORK_{i}',
                        'status': 'result_ready' if i < ready_count else 'pending'} for i in range(2)] +
                        ([{'question_id':'Q3','status':'missing','work_item_id':None}] if missing_work=='row' else [])}
        assert input_value['work_ids'] == ([] if missing_work=='all' else ['WORK_0', 'WORK_1'])
        rows = []
        for i in range(0 if missing_work=='all' else 2):
            if i >= ready_count:
                rows.append({'work_item_id': f'WORK_{i}', 'status': 'not_exportable', 'reason': None})
            else:
                raw = json.dumps({'fixture': i})
                rows.append({'work_item_id': f'WORK_{i}', 'status': 'exportable', 'observation_id': f'obs_{i}',
                             'package_json': raw, 'package_bytes_sha256': hashlib.sha256(raw.encode()).hexdigest()})
        return {'items': rows, 'API_requests': 0, 'network_calls': 0}
    monkeypatch.setattr(gateway, '_call', native)  # Native process boundary; SQL/package validation is tested separately.
    result = export_deliveries(gateway, {'bundle_id': 'B'})
    assert result['status'] == ('exported' if ready_count == 2 and not missing_work else 'partial')
    extra = int(missing_work in {'row','omitted'})
    assert len(result['items']) == 2+extra and len(result['import_bundles']) == ready_count
    assert sum(row['status'] == 'not_exportable' for row in result['items']) == 2-ready_count+extra
    assert result['API_requests'] == result['model_calls'] == 0 and len(calls) == 2
    for registration in result['import_bundles'].values():
        raw = Path(registration['package']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == registration['package_sha256']


@pytest.mark.parametrize('mutation', ['store','hash'])
def test_original_owner_rejects_foreign_store_or_hash_without_mutation(delivery,mutation):
    gateway,bundle,receipt=delivery
    gateway.bind_delivery_consumer(bundle,TARGET,'operator-config:isolated-dashboard-test')
    wrong=copy.deepcopy(receipt)
    if mutation=='store':wrong['acks'][0]['consumer']['store_id']='other-store'
    else:wrong['acks'][0]['payload_sha256']='0'*64
    before=Path(bundle['work_store']).read_bytes()
    with pytest.raises(DashboardExecutionError):gateway.acknowledge_delivery(bundle,wrong)
    assert Path(bundle['work_store']).read_bytes()==before


def test_observation_mapping_cannot_retarget_original_work(delivery):
    gateway,bundle,receipt=delivery
    mapping=list(bundle['work_item_ids'])
    bundle['work_item_ids'][mapping[0]]=bundle['work_item_ids'][mapping[1]]
    before=Path(bundle['work_store']).read_bytes()
    with pytest.raises(DashboardExecutionError):gateway.bind_delivery_consumer(bundle,TARGET,'operator-config:isolated-dashboard-test')
    assert Path(bundle['work_store']).read_bytes()==before


def test_partial_ack_batch_is_retriable_without_reapplying_completed_work(delivery):
    gateway,bundle,receipt=delivery
    gateway.bind_delivery_consumer(bundle,TARGET,'operator-config:isolated-dashboard-test')
    wrong=copy.deepcopy(receipt);wrong['acks'][1]['payload_sha256']='0'*64
    with pytest.raises(DashboardExecutionError):gateway.acknowledge_delivery(bundle,wrong)
    assert gateway.acknowledge_delivery(bundle,receipt)['status']=='delivered'


def test_missing_ledger_never_creates_empty_native_database(tmp_path):
    gateway=ExecutionGateway({'stockqa_root':str(SOURCE)})
    bundle={'work_store':str(tmp_path/'missing.sqlite'),'work_item_ids':{'obs':'WORK'}}
    with pytest.raises(DashboardExecutionError):gateway.acknowledge_delivery(bundle,{'acks':[]})
    assert not (tmp_path/'missing.sqlite').exists()


def test_original_rejection_is_recorded_without_claiming_delivered(delivery):
    gateway,bundle,receipt=delivery
    gateway.bind_delivery_consumer(bundle,TARGET,'operator-config:isolated-dashboard-test')
    rejected=copy.deepcopy(receipt)
    for ack in rejected['acks']:
        ack.update(status='rejected',error_code='invalid_payload')
    result=gateway.acknowledge_delivery(bundle,rejected)
    assert result['status']=='owner_rejected'
    assert {row['state'] for row in result['items']}=={'rejected'}


def test_export_reads_exact_original_outbox_bytes_and_rejects_foreign_entity(delivery, tmp_path):
    import hashlib
    from scripts.dashboard_delivery import _EXPORT
    gateway,bundle,receipt=delivery
    ledger=Path(bundle['work_store'])
    request={'entity_id':'ENT_BYD','question_ids':['IQS_05'],'work_ids':list(bundle['work_item_ids'].values())}
    command=[sys.executable,'-B','-X','utf8','-c',_EXPORT,str(SOURCE),str(ledger)]
    before=ledger.read_bytes()
    response=gateway._call(command,SOURCE,tmp_path,input_value=request)
    assert response['API_requests']==0 and len(response['items'])==2
    for row in response['items']:
        assert row['status']=='exportable'
        assert hashlib.sha256(row['package_json'].encode('utf8')).hexdigest()==row['package_bytes_sha256']
        assert row['work_item_id']==bundle['work_item_ids'][row['observation_id']]
    assert ledger.read_bytes()==before
    with pytest.raises(DashboardExecutionError):
        gateway._call(command,SOURCE,tmp_path,input_value={**request,'entity_id':'ENT_FOREIGN'})
    assert ledger.read_bytes()==before


def test_export_uses_layout_checked_read_only_view_without_history_audit(delivery, tmp_path):
    from scripts.dashboard_delivery import _EXPORT
    gateway,bundle,receipt=delivery
    ledger=Path(bundle['work_store'])
    request={'entity_id':'ENT_BYD','question_ids':['IQS_05'],'work_ids':list(bundle['work_item_ids'].values())}
    # Original layout validation must still run, while a scan of every unrelated
    # historical answer/package is deliberately rejected in this child.
    guard=r'''
import sys
sys.path.insert(0,sys.argv[1])
from src.utils.quick_scan_work_store import QuickScanWorkStore
original=QuickScanWorkStore._validate_schema.__func__
def layout_only(cls,connection,**kwargs):
    if kwargs.get('audit_records',True):
        print('HISTORY_AUDIT_FORBIDDEN',file=sys.stderr)
        raise AssertionError('export must not audit unrelated history')
    return original(cls,connection,**kwargs)
QuickScanWorkStore._validate_schema=classmethod(layout_only)
'''
    before=ledger.read_bytes()
    response=gateway._call([sys.executable,'-B','-X','utf8','-c',guard+_EXPORT,
        str(SOURCE),str(ledger)],SOURCE,tmp_path,input_value=request)
    assert response['API_requests']==0 and response['network_calls']==0
    assert len(response['items'])==2 and all(r['status']=='exportable' for r in response['items'])
    assert ledger.read_bytes()==before


@pytest.mark.parametrize('fault',['layout','current_package'])
def test_read_only_export_keeps_layout_and_current_package_validation(delivery,tmp_path,fault):
    import sqlite3
    from scripts.dashboard_delivery import _EXPORT
    gateway,bundle,receipt=delivery
    ledger=Path(bundle['work_store'])
    work_ids=list(bundle['work_item_ids'].values())
    # Corrupt only this disposable test database. Restore the exact trigger
    # definition after changing the selected payload, so that case reaches
    # current-object validation rather than merely the layout check.
    with sqlite3.connect(ledger) as connection:
        if fault=='layout':
            connection.execute('DROP TRIGGER answer_checkpoint_no_update')
        else:
            trigger=connection.execute("SELECT sql FROM sqlite_master WHERE name='quick_scan_delivery_package_immutable'").fetchone()[0]
            connection.execute('DROP TRIGGER quick_scan_delivery_package_immutable')
            connection.execute('UPDATE quick_scan_result_delivery SET package_json=? WHERE work_item_id=?',('{}',work_ids[0]))
            connection.execute(trigger)
    before=ledger.read_bytes()
    request={'entity_id':'ENT_BYD','question_ids':['IQS_05'],'work_ids':work_ids}
    with pytest.raises(DashboardExecutionError):
        gateway._call([sys.executable,'-B','-X','utf8','-c',_EXPORT,str(SOURCE),str(ledger)],
            SOURCE,tmp_path,input_value=request)
    assert ledger.read_bytes()==before
