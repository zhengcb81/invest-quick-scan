"""Preparation timeouts and registration recovery never repeat original apply."""
import json
from pathlib import Path
import threading
import time

import pytest

from scripts.dashboard_jobs import PreparationJobs, DashboardJobError

SELECTION={'preview_id':'prepare_'+'1'*32,'preview_token':'a'*64}


class Preparer:
    def __init__(self):
        self.entered,self.release=threading.Event(),threading.Event()
        self.apply_count=0;self.result=None
    def validate_selection(self,payload):
        if payload!=SELECTION:raise DashboardJobError('preview_stale','Wrong original preview',409)
    def apply(self,payload):
        self.apply_count+=1;self.entered.set()
        assert self.release.wait(5)
        self.result={'execution_bundles':[{'bundle_id':'original','execution_bundle':{'entity_id':'ENT_TEST'}}]}
        return self.result
    def preparation(self,preview_id):
        assert preview_id==SELECTION['preview_id']
        return {'status':'prepared','result':self.result} if self.result else {'status':'partial'}


@pytest.fixture
def setup(tmp_path):
    preparer=Preparer();registered=[]
    jobs=PreparationJobs(preparer,tmp_path/'jobs',lambda result: registered.append(result) or {'registered':True})
    yield jobs,preparer,registered
    preparer.release.set()
    for thread in list(jobs._threads.values()):thread.join(timeout=5)
    assert not any(thread.is_alive() for thread in jobs._threads.values())


def finish(jobs,job_id):
    deadline=time.monotonic()+5
    while job_id in jobs._threads and time.monotonic()<deadline:time.sleep(.01)
    assert job_id not in jobs._threads
    return jobs.get(job_id)


def test_async_duplicate_click_only_applies_once(setup):
    jobs,preparer,registered=setup
    first=jobs.submit(SELECTION);job_id=first['job']['job_id']
    assert preparer.entered.wait(2) and first['job']['state']=='preparing'
    assert jobs.submit(SELECTION)['attached'] is True
    assert preparer.apply_count==1 and registered==[]
    preparer.release.set()
    assert finish(jobs,job_id)['state']=='registered'
    assert len(registered)==1


def test_read_after_restart_never_reapplies_unknown_preparation(setup):
    jobs,preparer,registered=setup
    job_id=jobs.submit(SELECTION)['job']['job_id'];assert preparer.entered.wait(2)
    restarted=PreparationJobs(preparer,jobs.state_root,lambda result: registered.append(result))
    assert restarted.get(job_id)['state']=='needs_original_inspection'
    assert restarted.reconcile(job_id)['original_preparation']['status']=='partial'
    assert preparer.apply_count==1


def test_registration_failure_reconciles_without_original_apply_again(setup):
    jobs,preparer,_=setup
    def fail(result):raise DashboardJobError('config_changed','Original configuration changed',409)
    jobs.on_prepared=fail
    job_id=jobs.submit(SELECTION)['job']['job_id'];preparer.release.set()
    assert finish(jobs,job_id)['state']=='registration_pending'
    jobs.on_prepared=lambda result:{'registered':True}
    assert jobs.reconcile(job_id)['state']=='registered'
    assert preparer.apply_count==1


def test_wrong_token_does_not_consume_legal_job_id(setup):
    jobs,preparer,_=setup
    with pytest.raises(DashboardJobError):jobs.submit({**SELECTION,'preview_token':'b'*64})
    assert not jobs.state_root.exists() and preparer.apply_count==0
    jobs.submit(SELECTION)


def test_corrupt_reference_is_not_empty_success_or_new_apply(setup):
    jobs,preparer,_=setup;jobs.state_root.mkdir()
    path=jobs._path('prepjob_'+'1'*32);path.write_text('{',encoding='utf8')
    with pytest.raises(DashboardJobError,match='损坏'):jobs.submit(SELECTION)
    assert preparer.apply_count==0


def test_explicit_abandon_preserves_partial_owner_records_and_does_not_register(setup):
    jobs,preparer,registered=setup
    job_id=jobs.submit(SELECTION)['job']['job_id'];assert preparer.entered.wait(2)
    with pytest.raises(DashboardJobError):jobs.abandon(job_id)
    # A different session can only stop waiting; it cannot roll back or cancel the old owner call.
    restarted=PreparationJobs(preparer,jobs.state_root,lambda result: registered.append(result))
    assert restarted.abandon(job_id)['state']=='abandoned'
    preparer.release.set();finish(jobs,job_id)
    assert restarted.get(job_id)['state']=='abandoned'
    assert registered==[] and not restarted.active()


def test_foreign_abandon_cannot_race_a_live_registration_callback(setup):
    jobs,preparer,registered=setup
    entered,release=threading.Event(),threading.Event()
    def register(result):
        entered.set()
        assert release.wait(5)
        registered.append(result)
        return {'registered':True}
    jobs.on_prepared=register
    job_id=jobs.submit(SELECTION)['job']['job_id'];preparer.release.set()
    assert entered.wait(2)
    restarted=PreparationJobs(preparer,jobs.state_root,lambda result: None)
    try:
        with pytest.raises(DashboardJobError) as error: restarted.abandon(job_id)
        assert error.value.code=='preparation_control_busy'
        with pytest.raises(DashboardJobError): restarted.reconcile(job_id)
    finally:
        release.set()
    assert finish(jobs,job_id)['state']=='registered'
    assert len(registered)==1 and preparer.apply_count==1


def test_same_session_orphan_is_reconcilable_without_reapplying(setup):
    jobs,preparer,registered=setup
    jobs.state_root.mkdir()
    job_id='prepjob_'+'1'*32
    preparer.result={'execution_bundles':[]}
    jobs._write(jobs._path(job_id),{'protocol':'iqs.preparation_job/1.0.0','job_id':job_id,
        **SELECTION,'state':'preparing','session':jobs.session})
    assert jobs.get(job_id)['state']=='needs_original_inspection'
    assert 'reconcile' in jobs.get(job_id)['allowed_actions']
    assert jobs.reconcile(job_id)['state']=='registered'
    assert preparer.apply_count==0 and len(registered)==1
