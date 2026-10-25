"""Slow original delivery never holds the UI lock or repeats paid work."""
import hashlib
import threading
import time

import pytest

from scripts.dashboard_delivery_jobs import DeliveryJobs, DeliveryJobError


class Execution:
    def __init__(self): self.revision='original'
    def bundle_registration(self,bundle_id):
        return {'bundle_id':bundle_id,'entity_id':'ENT_'+bundle_id,
            'bundle_fingerprint':hashlib.sha256((bundle_id+self.revision).encode()).hexdigest()}


def settled(jobs,job_id):
    deadline=time.monotonic()+5
    while jobs._threads and time.monotonic()<deadline: time.sleep(.01)
    assert not jobs._threads
    return jobs.get(job_id)


def test_duplicate_delivery_attaches_and_reads_remain_available_during_native_io(tmp_path):
    entered,release=threading.Event(),threading.Event();calls=[]
    def deliver(bundle):
        calls.append(bundle);entered.set();assert release.wait(5);return {'status':'delivered'}
    jobs=DeliveryJobs(Execution(),tmp_path,'a'*64,deliver,lambda _:None)
    first=jobs.submit({'bundle_id':'A'});job_id=first['job']['job_id']
    assert entered.wait(2)
    try:
        assert jobs.list()['jobs'][0]['state']=='running'
        assert jobs.submit({'bundle_id':'A'})['attached'] is True
        with pytest.raises(DeliveryJobError):jobs.control(job_id,'resume')
        with pytest.raises(DeliveryJobError):jobs.control(job_id,'abandon')
    finally:release.set()
    result=settled(jobs,job_id)
    assert result['state']=='completed' and calls==['A']
    assert result['counts']=={'scopes':1,'delivered_scopes':1}
    assert result['financial_accuracy_proven'] is False


def test_partial_batch_resume_only_retries_pending_exact_original_packages(tmp_path):
    execution=Execution();calls=[];retry=False
    def deliver(bundle):
        calls.append(bundle)
        return {'status':'delivered' if bundle=='A' or retry else 'partial'}
    def batch(_):return {'entries':[{**execution.bundle_registration(key),'state':state} for key,state in [('A','owner_ready'),('B','owner_ready'),('C','selected')]]}
    jobs=DeliveryJobs(execution,tmp_path,'b'*64,deliver,batch)
    job_id=jobs.submit({'batch_id':'batch-original'})['job']['job_id']
    first=settled(jobs,job_id)
    assert first['state']=='partial' and first['partial_batch_selection'] is True
    assert first['counts']['delivered_scopes']==1
    retry=True;jobs.control(job_id,'resume')
    assert settled(jobs,job_id)['state']=='completed' and calls==['A','B','B']


def test_restart_never_automatically_resends_and_original_fingerprint_drift_blocks(tmp_path):
    execution=Execution();calls=[]
    jobs=DeliveryJobs(execution,tmp_path,'c'*64,lambda bundle:calls.append(bundle) or {'status':'partial'},lambda _:None)
    job_id=jobs.submit({'bundle_id':'A'})['job']['job_id'];settled(jobs,job_id)
    restarted=DeliveryJobs(execution,tmp_path,'c'*64,lambda _:None,lambda _:None)
    assert restarted.list()['jobs'][0]['state']=='partial' and calls==['A']
    execution.revision='changed'
    with pytest.raises(DeliveryJobError,match='范围已变'):restarted.control(job_id,'resume')
    assert calls==['A']
    assert restarted.control(job_id,'abandon')['state']=='abandoned' and not restarted.active()


def test_unready_batch_and_unknown_selection_do_not_create_a_job(tmp_path):
    jobs=DeliveryJobs(Execution(),tmp_path,'d'*64,lambda _:None,lambda _:{'entries':[]})
    with pytest.raises(DeliveryJobError):jobs.submit({'batch_id':'not-ready'})
    with pytest.raises(DeliveryJobError):jobs.submit({'command':'no'})
    assert jobs.list()['jobs']==[]


def test_same_session_orphan_has_explicit_recovery_without_a_new_model_call(tmp_path):
    execution=Execution();jobs=DeliveryJobs(execution,tmp_path,'e'*64,lambda _:{'status':'delivered'},lambda _:None)
    job_id='deliveryjob_'+'1'*32
    jobs._write(jobs._path(job_id),{'protocol':'iqs.delivery_job/1.0.0','job_id':job_id,
        'deployment_sha256':'e'*64,'state':'running','session':jobs.session,
        'entries':[{**execution.bundle_registration('A'),'state':'importing'}]})
    assert jobs.get(job_id)['state']=='needs_original_inspection'
    jobs.control(job_id,'resume')
    assert settled(jobs,job_id)['state']=='completed'


def test_delivery_stores_only_counts_not_all_original_ack_details(tmp_path):
    outcome={'status':'delivered','items':[{'bundle_id':f'package-{index}',
        'ack_reconciliation':{'status':'delivered','items':[{'observation_id':'not-copied'}]}} for index in range(36)]}
    jobs=DeliveryJobs(Execution(),tmp_path,'f'*64,lambda _:outcome,lambda _:None)
    job_id=jobs.submit({'bundle_id':'A'})['job']['job_id']
    record=settled(jobs,job_id)
    summary=record['entries'][0]['outcome']
    assert summary['package_count']==summary['delivered_packages']==36
    assert 'items' not in summary
    assert 'not-copied' not in jobs._path(job_id).read_text(encoding='utf8')


def test_maximum_reference_count_is_readable_and_oversized_write_preserves_old_record(tmp_path):
    jobs=DeliveryJobs(Execution(),tmp_path,'1'*64,lambda _:None,lambda _:None)
    job_id='deliveryjob_'+'2'*32
    entries=[{'bundle_id':f'B{index}','entity_id':'ENT_'+str(index//2),'scope':'entity' if index%2==0 else 'security',
        'scope_id':('ENT_' if index%2==0 else 'SEC_')+str(index//2),
        'bundle_fingerprint':'a'*64,'state':'delivered','company_preparation_id':'prepare_'+'a'*32,
        'expected_scope_bindings':[{'scope':'entity','scope_id':'ENT_'+str(index//2)},{'scope':'security','scope_id':'SEC_'+str(index//2)}],
        'outcome':{'status':'delivered','package_count':33,'delivered_packages':33,'error_codes':[]}} for index in range(5000)]
    record={'protocol':'iqs.delivery_job/1.0.0','job_id':job_id,'deployment_sha256':'1'*64,
        'state':'completed','session':jobs.session,'entries':entries}
    path=jobs._path(job_id);jobs._write(path,record)
    before=path.read_bytes()
    assert len(before)<16*1024*1024 and jobs.get(job_id)['counts']['delivered_scopes']==5000
    with pytest.raises(DeliveryJobError):jobs._write(path,{**record,'invalid_blob':'x'*(16*1024*1024)})
    assert path.read_bytes()==before
