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
