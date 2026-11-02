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


def journal_read_port(work_id, fault=None):
    """Mock only a native reader, never generate owner/admission authority."""
    return r'''
import sys
sys.path.insert(0,sys.argv[1])
from src.utils import quick_scan_refresh_admission_journal as journal
def original_action(connection, confirmation_id):
    if confirmation_id != 'rc2_'+'1'*64 or FAULT == 'missing': return None
    original=store.get_item(ORIGINAL_ID)
    row={key:original[key] for key in ('work_item_id','entity_id','question_id','generation','scope','scope_id')}
    if FAULT == 'entity': row['entity_id']='ENT_OTHER'
    if FAULT == 'question': row['question_id']='OTHER_Q'
    if FAULT == 'scope': row['scope']='security';row['scope_id']='SEC_OTHER'
    if FAULT == 'generation': row['generation']+=1
    if FAULT == 'work_id': row['work_item_id']='WORK_MISSING'
    return {'receipt':{'confirmation_id': 'rc2_'+('2' if FAULT=='confirmation' else '1')*64,
        'items':[row]},'inputs':{'references':[]}}
journal.read_record=original_action
'''.replace('ORIGINAL_ID', repr(work_id)).replace('FAULT', repr(fault))


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


def test_same_native_receiver_reuses_original_binding_when_locator_label_changes(delivery):
    gateway, bundle, receipt = delivery
    gateway.bind_delivery_consumer(bundle, TARGET, 'dashboard-owner-status:original-workspace-path')
    before = Path(bundle['work_store']).read_bytes()
    result = gateway.bind_delivery_consumer(bundle, TARGET, 'dashboard-owner-status:moved-same-data-store')
    assert result['status'] == 'bound' and result['API_requests'] == 0
    assert Path(bundle['work_store']).read_bytes() == before
    assert gateway.acknowledge_delivery(bundle, receipt)['status'] == 'delivered'


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
    bundle = {'entity_id': 'ENT_TEST', 'admission_config': str(tmp_path/'admission'), 'confirmation_id': 'rc2_'+'1'*64,
              'inspection_request': str(tmp_path/'request'), 'manifest': str(tmp_path/'manifest')}
    gateway = ExecutionGateway({'stockqa_root': str(SOURCE), 'iqs_release_root': str(ROOT),
                                'state_root': str(tmp_path/'state'), 'bundles': {'B': bundle}})
    calls = []
    def native(command, root, runtime, *, input_value=None):
        calls.append(command)
        assert '-c' in command and '--policy' not in command
        assert input_value['question_ids'] == ['Q1', 'Q2'] + (['Q3'] if missing_work in {'row', 'omitted'} else [])
        rows = []
        for i in range(0 if missing_work=='all' else 2):
            if i >= ready_count:
                rows.append({'work_item_id': f'WORK_{i}', 'status': 'not_exportable', 'reason': None})
            else:
                raw = json.dumps({'fixture': i})
                rows.append({'work_item_id': f'WORK_{i}', 'status': 'exportable', 'observation_id': f'obs_{i}',
                             'package_json': raw, 'package_bytes_sha256': hashlib.sha256(raw.encode()).hexdigest()})
        if missing_work in {'row', 'omitted'}:
            rows.append({'question_id': 'Q3', 'work_item_id': None, 'status': 'not_exportable', 'reason': 'missing'})
        if missing_work == 'all':
            rows.extend({'question_id': qid, 'work_item_id': None, 'status': 'not_exportable', 'reason': 'missing'}
                        for qid in input_value['question_ids'])
        return {'items': rows, 'API_requests': 0, 'network_calls': 0}
    monkeypatch.setattr(gateway, '_call', native)  # Native process boundary; SQL/package validation is tested separately.
    _, selected = gateway._select({'bundle_id': 'B'})
    result = export_deliveries(bundle_id='B', bundle=selected, config=gateway.config,
        state_root=gateway.state_root, call=gateway._call, inspection_work_items=gateway.inspection_work_items)
    assert result['status'] == ('exported' if ready_count == 2 and not missing_work else 'partial')
    extra = int(missing_work in {'row','omitted'})
    assert len(result['items']) == 2+extra and len(result['import_bundles']) == ready_count
    assert sum(row['status'] == 'not_exportable' for row in result['items']) == 2-ready_count+extra
    assert result['API_requests'] == result['model_calls'] == 0 and len(calls) == 1
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


def test_export_existing_outbox_needs_no_current_budget_or_new_send_controls(delivery, tmp_path, monkeypatch):
    import hashlib
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    import frozen_release_projection
    monkeypatch.setattr(frozen_release_projection, 'create_projection', lambda *a, **kw: {'fixture': 'release'})
    gateway, original, _ = delivery
    original_ids = list(original['work_item_ids'].values())
    # Mock only the native journal read port. The two real SQLite checkpoints,
    # sealed bytes and their integrity reader remain ORIGINAL code. This is no
    # owner/admission qualification or producer-positive receipt fixture.
    call = gateway._call
    from scripts.dashboard_delivery import _EXPORT
    journal_port = journal_read_port(original_ids[0])
    def recorded_action(command, *args, **kwargs):
        command = list(command)
        if '-c' in command and command[command.index('-c')+1] == _EXPORT:
            command[command.index('-c')+1] = journal_port + _EXPORT
        return call(command, *args, **kwargs)
    monkeypatch.setattr(gateway, '_call', recorded_action)
    ledger = Path(original['work_store'])
    admission = tmp_path/'admission.json'
    admission.write_text(json.dumps({'work_store': str(ledger),
                                    'budget_policy_file': str(tmp_path/'removed-policy.json')}), encoding='utf8')
    request = tmp_path/'request.json'
    request.write_text(json.dumps({'entity_id': 'ENT_BYD', 'question_ids': ['IQS_05'],
        'scope_bindings': {'IQS_05': {'scope': 'entity', 'scope_id': 'ENT_BYD'}}}), encoding='utf8')
    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}', encoding='utf8')
    bundle = {'entity_id': 'ENT_BYD', 'admission_config': str(admission),
              'inspection_request': str(request), 'manifest': str(manifest), 'work_lease_seconds': -1,
              'confirmation_id': 'rc2_'+'1'*64}
    gateway.config.update(iqs_release_root=str(ROOT), runtime_dir=str(tmp_path))
    gateway.bundles['ORIGINAL'] = bundle
    gateway.state_root = tmp_path/'state'
    before = ledger.read_bytes()
    result = gateway.export_delivery({'bundle_id': 'ORIGINAL'})
    assert result['status'] == 'exported' and result['API_requests'] == 0
    assert len(result['import_bundles']) == 1
    for registration in result['import_bundles'].values():
        raw = Path(registration['package']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == registration['package_sha256']
        assert set(registration['work_item_ids'].values()) == {original_ids[0]}
        assert original_ids[1] not in registration['work_item_ids'].values()
    assert ledger.read_bytes() == before and not (tmp_path/'removed-policy.json').exists()
    read = gateway.preview({'bundle_id': 'ORIGINAL'}, read_only=True)
    assert read['status'] == 'inspected' and read['API_requests'] == 0
    assert read['inspection']['work_items'][0]['status'] == 'result_ready'
    assert ledger.read_bytes() == before


@pytest.mark.parametrize('fault', ['missing', 'confirmation', 'entity', 'question', 'scope', 'generation', 'work_id'])
def test_original_action_scope_cannot_select_foreign_or_later_work(delivery, tmp_path, fault):
    """Actual readonly SQLite/outbox, explicit mock of immutable journal port."""
    from scripts.dashboard_delivery import _EXPORT
    gateway, original, _ = delivery
    ledger = Path(original['work_store'])
    ids = list(original['work_item_ids'].values())
    request = {'entity_id': 'ENT_BYD', 'question_ids': ['IQS_05'],
               'scope_bindings': {'IQS_05': {'scope': 'entity', 'scope_id': 'ENT_BYD'}},
               'confirmation_id': 'rc2_'+'1'*64,
               'work_ids': [ids[1]]}  # Cannot override the original action with today's ID.
    before = ledger.read_bytes()
    with pytest.raises(DashboardExecutionError):
        gateway._call([sys.executable, '-B', '-X', 'utf8', '-c', journal_read_port(ids[0], fault)+_EXPORT,
                       str(SOURCE), str(ledger)], SOURCE, tmp_path, input_value=request)
    assert ledger.read_bytes() == before


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
