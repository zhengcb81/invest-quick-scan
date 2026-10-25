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


def test_scope_delivery_uses_original_outbox_without_growing_an_all_company_registry(tmp_path):
    events=[]
    class Outbox(Execution):
        def export_delivery(self,payload):
            return {'status':'exported','items':[{'status':'exportable'}],
                'import_bundles':{'original-package':{'work_store':'original','work_item_ids':{'obs':'WORK'}}}}
        def bind_delivery_consumer(self,bundle,target,source):
            assert target['store_id']=='independent-owner'
            events.append('bind')
        def acknowledge_delivery(self,bundle,receipt):
            events.append('ack');return {'status':'delivered'}
    class Receiver:
        def __init__(self,config): assert set(config['bundles'])=={'original-package'}
        def status(self): return {'available':True,'store_id':'independent-owner'}
        def import_preview(self,body): return {'can_apply':True,'preview_token':'original-preview'}
        def import_apply(self,body):
            assert body['preview_token']=='original-preview'
            events.append('import');return {'receipt':{'acks':[]}}
    service=DashboardService(tmp_path,execution_factory=Outbox,owner_factory=Receiver)
    for _ in range(2):
        reply=service._deliver_scope('scope')
        assert reply['status']=='delivered'
    assert events==['bind','import','ack']*2
    assert service.config['import_bundles']=={} and not service.config_path.exists()
