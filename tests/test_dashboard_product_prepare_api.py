"""Product composition tests; original SDK correctness lives in native tests."""
from pathlib import Path
import json
import sys
import threading
import time

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from dashboard_service import DashboardService, validate_config, ProductError


class Execution:
    def __init__(self, config):
        self.config, self.bundles, self.processes = config, config['bundles'], {'old':'preserved'}
    def status(self): return {'available':False}
    def active_references(self): return {'items':[]}
    def tasks(self, **kwargs): return {'tasks':[]}


class Prepare:
    def __init__(self, config):
        self.calls=0; self.release=threading.Event(); self.config=config
    def status(self): return {'available':True,'native_prepare_configured':True,'API_requests':0}
    def validate_selection(self,payload):
        if payload['preview_token'] != 'a'*64: raise ValueError('bad token')
    def bank_preview(self,payload): return {'questions':[{'id':'Q1'},{'id':'Q2'}],'question_count':2,'can_apply':True}
    def apply(self,payload):
        self.calls+=1
        assert self.release.wait(5)
        return {'status':'prepared','question_count_total':2,'execution_bundles':[
            {'bundle_id':'company-entity','execution_bundle':{'entity_id':'ENT_X','scope':'entity','scope_id':'ENT_X'}},
            {'bundle_id':'company-security','execution_bundle':{'entity_id':'ENT_X','scope':'security','scope_id':'SEC_X'}}]}


def wait_job(service, job_id):
    end=time.monotonic()+5
    while time.monotonic()<end:
        status, reply=service.dispatch('GET','/api/product/prepare/jobs/'+job_id)
        assert status==200, reply
        if reply['data']['state'] not in {'preparing','owner_prepared','registration_in_progress'}: return reply['data']
        time.sleep(.01)
    raise AssertionError('preparation failed to finish')


def test_async_preparation_registers_all_scopes_without_replacing_execution(tmp_path):
    service=DashboardService(tmp_path,execution_factory=Execution,prepare_factory=Prepare)
    execution=service._gateway('execution')
    selection={'preview_id':'prepare_'+'1'*32,'preview_token':'a'*64}
    started=time.monotonic()
    code, reply=service.dispatch('POST','/api/product/prepare/apply',selection)
    assert code==200 and time.monotonic()-started<1
    job_id=reply['data']['job']['job_id']
    assert service.dispatch('POST','/api/product/prepare/apply',selection)[1]['data']['attached'] is True
    assert service.dispatch('GET','/api/product/prepare/jobs')[0]==200
    preparer=service._preparer(); preparer.release.set()
    job=wait_job(service,job_id)
    assert job['state']=='registered', job
    assert service._gateway('execution') is execution
    assert execution.processes=={'old':'preserved'}
    assert set(execution.bundles)=={'company-entity','company-security'}
    assert preparer.calls==1 and job['allowed_actions']==[]
    saved=json.loads(service.config_path.read_text(encoding='utf8'))
    assert set(saved['execution_bundles'])==set(execution.bundles)
    assert service.dispatch('POST',f'/api/product/prepare/jobs/{job_id}/reconcile',{})[0]==200
    assert preparer.calls==1


def test_pending_job_blocks_workspace_switch_and_reads_do_not_start_work(tmp_path):
    service=DashboardService(tmp_path,execution_factory=Execution,prepare_factory=Prepare)
    assert service.dispatch('GET','/api/product/prepare/status')[1]['data']['API_requests']==0
    assert service.dispatch('GET','/api/product/prepare/jobs')[1]['data']['jobs']==[]
    assert not service.config_path.exists()
    payload={'preview_id':'prepare_'+'2'*32,'preview_token':'a'*64}
    job=service.dispatch('POST','/api/product/prepare/apply',payload)[1]['data']['job']
    config={**service.config,'workspace_label':'other'}
    assert service.dispatch('PUT','/api/product/setup',{'config':config,'revision_sha256':service._config_revision})[0]==409
    service._preparer().release.set()
    assert wait_job(service,job['job_id'])['state']=='registered'


def test_completed_registration_conflict_preserves_native_result_for_reconcile(tmp_path):
    service=DashboardService(tmp_path,execution_factory=Execution,prepare_factory=Prepare)
    service.config['execution_bundles']['company-entity']={'entity_id':'ENT_OTHER'}
    selection={'preview_id':'prepare_'+'3'*32,'preview_token':'a'*64}
    job=service.dispatch('POST','/api/product/prepare/apply',selection)[1]['data']['job']
    service._preparer().release.set()
    result=wait_job(service,job['job_id'])
    assert result['state']=='registration_pending' and result['result']['status']=='prepared'
    assert result['registration_error']=='prepared_bundle_conflict'
    assert set(result['allowed_actions'])=={'reconcile','abandon'}
    assert not service.config_path.exists()


@pytest.mark.parametrize('addition', [{'prepare':{'command':'bad'}},{'batch':{'max_concurrency':0}},{'prepare':{'api_key':'do-not-store'}}])
def test_prepare_config_rejects_unknown_commands_credentials_and_concurrency(tmp_path,addition):
    with pytest.raises(ProductError): validate_config(addition,tmp_path)


def test_shared_company_config_can_be_selected_in_original_settings_and_registered_bundle(tmp_path):
    value = validate_config({'prepare':{'shared_company_config':'config/shared-company.json'},
                             'execution_bundles':{'B':{'shared_company_config':'frozen/shared-company.json'}}},tmp_path)
    assert value['prepare']['shared_company_config'] == str(tmp_path/'config/shared-company.json')
    assert value['execution_bundles']['B']['shared_company_config'] == str(tmp_path/'frozen/shared-company.json')
    with pytest.raises(ProductError):
        validate_config({'prepare':{'shared_company_config':'https://example.invalid/config.json'}},tmp_path)


@pytest.mark.parametrize('references', ['none','mixed','only','missing'])
def test_scope_delivery_uses_original_outbox_without_growing_an_all_company_registry(tmp_path, references):
    events=[]
    class Outbox(Execution):
        def export_delivery(self,payload):
            items=[] if references=='only' else [{'status':'exportable'}]
            if references in {'mixed','only','missing'}:
                items.append({'status':'not_exportable' if references=='missing' else 'referenced', 'question_id':'CACHED'})
            return {'status':'partial' if references=='missing' else 'exported','items':items,
                'referenced_question_ids':['CACHED'] if references in {'mixed','only'} else [],
                'import_bundles':{} if references=='only' else {'original-package':{'work_store':'original','work_item_ids':{'obs':'WORK'}}}}
        def bind_delivery_consumer(self,bundle,target,source):
            assert target['store_id']=='independent-owner'
            events.append('bind')
        def acknowledge_delivery(self,bundle,receipt):
            events.append('ack');return {'status':'delivered'}
    class Receiver:
        def __init__(self,config): assert set(config['bundles'])=={'original-package'}
        def status(self): return {'available':True,'store_id':'independent-owner'}
        def import_preview(self,body):
            events.append('preview')
            return {'can_apply':True,'preview_token':'original-preview'}
        def import_apply(self,body):
            assert body['preview_token']=='original-preview'
            events.append('import');return {'receipt':{'acks':[]}}
    service=DashboardService(tmp_path,execution_factory=Outbox,owner_factory=Receiver)
    for _ in range(2):
        reply=service._deliver_scope('scope')
        assert reply['status']==('partial' if references=='missing' else 'delivered')
        if references=='only':
            assert reply['items']==[] and reply['referenced_question_ids']==['CACHED']
    assert events==([] if references=='only' else ['preview','bind','import','ack']*2)
    assert service.config['import_bundles']=={} and not service.config_path.exists()


def test_setup_can_change_future_scan_settings_while_exact_delivery_waits(tmp_path):
    class Registered(Execution):
        def bundle_registration(self,bundle_id):
            return {'bundle_id':bundle_id,'entity_id':'ENT_X','bundle_fingerprint':'a'*64}
    service=DashboardService(tmp_path,execution_factory=Registered)
    service.config['execution_bundles']['original']={'entity_id':'ENT_X'}
    jobs=service._delivery_jobs();jobs.deliver_scope=lambda _: {'status':'partial'}
    jid=jobs.submit({'bundle_id':'original'})['job']['job_id']
    deadline=time.monotonic()+5
    while jobs._threads and time.monotonic()<deadline:time.sleep(.01)
    assert jobs.get(jid)['state']=='partial'
    before=jobs._path(jid).read_bytes()
    config={**service.config,'prepare':{'pack_size':1,'thinking':True},'workspace_label':'new label'}
    status,reply=service.dispatch('PUT','/api/product/setup',{'config':config,'revision_sha256':service._config_revision})
    assert status==200,reply
    assert service._delivery_jobs().get(jid)['state']=='partial'
    assert jobs._path(jid).read_bytes()==before
    for key,value in [('workspace_root',str(tmp_path/'other-owner')),('state_root',str(tmp_path/'other-jobs')),
                      ('execution_bundles',{'unrelated':{'entity_id':'ENT_OTHER'}})]:
        changed={**service.config,key:value}
        status,reply=service.dispatch('PUT','/api/product/setup',{'config':changed,'revision_sha256':service._config_revision})
        assert status==409 and reply['error']['code']=='delivery_active',reply


@pytest.mark.parametrize('remaining', [False, True])
def test_stored_ack_recovers_before_release_export_and_keeps_partial_progress(tmp_path, remaining):
    events=[]
    target={'component':'StockWiki','namespace':'quick_scan','store_id':'original-owner'}
    class Outbox(Execution):
        def delivery_receivers(self, bundle_id):
            return {'items':[{'status':'referenced','question_id':'CACHED'}],
                'consumers':[{'work_item_id':'W1','consumer':target,'work_store':'original-ledger',
                    'package_id':'P1','observation_id':'O1'}] + ([{'work_item_id':'W2','consumer':None,
                        'work_store':'original-ledger','package_id':'P2','observation_id':'O2'}] if remaining else [])}
        def export_delivery(self,payload):
            events.append('export')
            raise OSError('Original release archive missing after remote acceptance')
        def acknowledge_delivery(self,bundle,receipt):
            assert bundle['work_store']=='original-ledger' and bundle['work_item_ids']=={'O1':'W1'}
            assert receipt=={'acks':[{'package_id':'P1','observation_id':'O1','consumer':target,'status':'accepted'}]}
            events.append('native-ack')
            return {'status':'delivered','items':[{'work_item_id':'W1','state':'delivered'}]}
    class Receiver:
        def __init__(self,config): pass
        def status(self): return {'available':True,'store_id':'original-owner'}
        def delivery_status(self,package_id):
            assert package_id=='P1';events.append('stored-ack')
            return {'receipts':[{'ack':{'package_id':'P1','observation_id':'O1','consumer':target,'status':'accepted'}}]}
        def import_preview(self,body): pytest.fail('Existing accepted ACK must not preview/import again')
        def import_apply(self,body): pytest.fail('Existing accepted ACK must not import again')
    service=DashboardService(tmp_path,execution_factory=Outbox,owner_factory=Receiver)
    result=service._deliver_scope('scope')
    assert result['status']==('partial' if remaining else 'delivered')
    assert result['items'][0]['ack_reconciliation']['status']=='delivered'
    assert result['referenced_question_ids']==['CACHED'] and result['API_requests']==0
    assert events==['stored-ack','native-ack']+(['export'] if remaining else [])


def test_mixed_stored_ack_and_missing_ack_import_only_remaining_original_package(tmp_path):
    events=[]
    target={'component':'StockWiki','namespace':'quick_scan','store_id':'original-owner'}
    bundles={f'P{i}':{'work_store':'original-ledger','work_item_ids':{f'O{i}':f'W{i}'}} for i in (1,2)}
    class Outbox(Execution):
        def delivery_receivers(self, bundle_id):
            return {'items':[], 'consumers':[{'work_item_id':f'W{i}','consumer':target,
                'work_store':'original-ledger','package_id':f'P{i}','observation_id':f'O{i}'} for i in (1,2)]}
        def export_delivery(self,payload):
            return {'status':'exported','items':[{'status':'exportable'}]*2,'import_bundles':bundles}
        def acknowledge_delivery(self,bundle,receipt):
            work=next(iter(bundle['work_item_ids'].values()));events.append(('ack',work))
            return {'status':'delivered','items':[{'work_item_id':work,'state':'delivered'}]}
        def bind_delivery_consumer(self,*args): events.append(('bind','W2'))
    class Receiver:
        def __init__(self,config): self.bundles=config['bundles']
        def status(self): return {'available':True,'store_id':'original-owner'}
        def delivery_status(self,package_id):
            return {'receipts':[{'ack':{'status':'accepted','package_id':'P1','observation_id':'O1'}}] if package_id=='P1' else []}
        def import_preview(self,payload):
            assert payload['bundle_id']=='P2' and set(self.bundles)=={'P2'}
            events.append(('preview','W2'));return {'preview_token':'original'}
        def import_apply(self,payload):
            assert payload['bundle_id']=='P2'
            events.append(('import','W2'));return {'status':'imported','receipt':{'package_id':'P2','acks':[]}}
    result=DashboardService(tmp_path,execution_factory=Outbox,owner_factory=Receiver)._deliver_scope('scope')
    assert result['status']=='delivered' and len(result['items'])==2
    assert events==[('ack','W1'),('preview','W2'),('bind','W2'),('import','W2'),('ack','W2')]


def test_cache_only_preparation_finishes_without_execution_registration_or_config_write(tmp_path):
    class Cached(Prepare):
        def apply(self,payload):
            self.calls+=1
            return {'status':'cached','question_count_total':1,'cached_question_count':1,
                'execution_bundles':[],'cached_scopes':[{'subject_ref':{'scope':'entity','scope_id':'ENT_X'},
                'question_count':1,'items':[{'question_id':'Q1','observation_id':'OBS_original'}]}]}
    def no_executor(config):
        raise AssertionError('Pure cache must not create an executor')
    service=DashboardService(tmp_path,execution_factory=no_executor,prepare_factory=Cached)
    selection={'preview_id':'prepare_'+'4'*32,'preview_token':'a'*64}
    job=service.dispatch('POST','/api/product/prepare/apply',selection)[1]['data']['job']
    result=wait_job(service,job['job_id'])
    assert result['state']=='registered',result
    assert result['registration']=={'bundle_ids':[],'question_count_total':1,'cached_question_count':1,'API_requests':0}
    assert service.config['execution_bundles']=={} and not service.config_path.exists()


@pytest.mark.parametrize('payload',[
    {'status':'cached','execution_bundles':[],'cached_scopes':[],'cached_question_count':0,'question_count_total':0},
    {'status':'prepared','execution_bundles':[],'cached_scopes':[]},
    {'status':'cached','execution_bundles':[],'cached_scopes':[{'items':[{'question_id':'Q','observation_id':None}]}],
        'cached_question_count':1,'question_count_total':1},
])
def test_empty_or_unbound_cache_result_is_not_a_successful_preparation(tmp_path,payload):
    service=DashboardService(tmp_path)
    deployment={k:v for k,v in service.config.items() if k not in {'execution_bundles','import_bundles'}}
    with pytest.raises(ProductError):service._register_prepared(payload,deployment)
    assert not service.config_path.exists()
