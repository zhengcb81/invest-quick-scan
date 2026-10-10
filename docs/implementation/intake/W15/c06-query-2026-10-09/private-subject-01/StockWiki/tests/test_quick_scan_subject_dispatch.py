"""Synthetic two-phase dispatch and real owner transaction, no HTTP or gold."""
import copy
import hashlib
import json
import runpy
import sqlite3
from pathlib import Path

import pytest
import query_contract as qc
import subject_dispatch_contract as dc
import stockwiki.quick_scan_observations as original_store
from stockwiki.quick_scan_subject_dispatch import SubjectBoundObservationStore
from stockwiki.quick_scan_observations import ObservationImportError
from stockwiki.quick_scan_query_v2 import QueryReader


def workspace(tmp_path,monkeypatch):
    factory=runpy.run_path(str(Path(__file__).with_name('test_quick_scan_query_v2.py')))
    paths,identity,subjects,old,query,reader=factory['workspace'](tmp_path)
    obs=runpy.run_path(str(Path(__file__).resolve().parents[2]/'iqs/tests/test_query_contract_v2.py'))['observation']()
    obs['information_cutoff']='2026-10-09'
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    dispatch={'protocol':'stockwiki.subject_dispatch_request/1.0.0',
        'subject_ref':copy.deepcopy(query['payload']['subject_refs'][0]),
        'work_item_id':'WORK_SYNTHETIC','work_request_id':'REQ_LOCAL_SYNTHETIC',
        'execution_attempt_id':obs['execution']['attempt_id'],'provider':obs['execution']['provider'],
        'model_requested':obs['execution']['model_requested'],'identity_revision':1,
        'question_id':obs['question_id'],'field_id':obs['field_id'],
        'information_cutoff':obs['information_cutoff'],
        'dispatch_identity_snapshot_sha256':'a'*64,'dispatch_manifest_sha256':'b'*64,
        'dispatch_prompt_sha256':obs['execution']['prompt_sha256'],
        'question_definition_sha256':obs['question_definition_sha256'],
        'question_semantic_sha256':obs['question_semantic_sha256'],
        'question_contract':{'id':obs['question_id'],'response_kind':'score'},
        **{k:obs[k] for k in ('module_package_id','module_release_id','question_version','template_version','method_id')}}
    clock=['2026-10-09T19:59:00Z']
    store=SubjectBoundObservationStore(paths,contract=dc,clock=lambda:clock[0])
    store.migrate()
    monkeypatch.setattr(original_store,'_now',lambda:'2026-10-10T08:59:00Z')
    seed={'observation_id':obs['observation_id'],'payload_sha256':qc._digest(obs)}
    decision={'package_id':'pkg_'+'a'*64,'item_id':'itm_'+qc._digest(seed),**seed,
        'observation':obs,'status':'accepted','error_code':None,'exec_key':qc._digest(obs['execution'])}
    return paths,store,dispatch,decision,clock,old


def register(store,dispatch):
    # Independent expected metadata represents the trusted owner adapter;
    # public CLI must obtain it from actual current route, never request JSON.
    return store.register_dispatch(dispatch,expected_dispatch=copy.deepcopy(dispatch))


def test_pre_receipt_exists_before_answer_and_after_binding_does_not_rewrite_original(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    pre=register(store,dispatch)
    assert 'observation_id' not in pre and 'execution_request_id' not in pre
    assert store.counts()['observations']==0
    clock[0]='2026-10-10T08:59:00Z'
    ack=store.apply_decisions([decision])[0]
    post=store.binding_for_observation(decision['observation_id'])
    assert ack['status']=='accepted'
    assert post['dispatch_receipt_id']==pre['receipt_id']
    assert post['dispatch_receipt_sha256']==qc._digest(pre)
    assert post['bound_at']==clock[0]
    assert post['binding']['recorded_before_send_at']==pre['registered_at']
    assert post['binding']['execution_request_id']==decision['observation']['execution']['request_id']
    original=store.get_observation(decision['observation_id'])
    assert original['payload']==decision['observation'] and original['payload_sha256']==decision['payload_sha256']
    assert original['payload'].get('analysis_subject') is None


def test_registration_and_package_restart_replay_preserve_both_original_receipts(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    pre=register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    first=store.apply_decisions([decision])[0]
    post=store.binding_for_observation(decision['observation_id'])
    reopened=SubjectBoundObservationStore(paths,contract=dc,clock=lambda:'2026-10-10T09:00:00Z')
    assert register(reopened,dispatch)==pre
    assert reopened.apply_decisions([decision])[0]==first
    assert reopened.binding_for_observation(decision['observation_id'])==post
    assert reopened.counts()['observations']==reopened.counts()['acked_items']==1


@pytest.mark.parametrize('field,value',[
    ('subject_ref',{'entity_id':'foreign'}),('question_id','IQS_02'),
    ('provider','foreign'),('model_requested','foreign'),('dispatch_prompt_sha256','9'*64)])
def test_request_cannot_replace_independent_owner_expected_dispatch(tmp_path,monkeypatch,field,value):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    changed=copy.deepcopy(dispatch)
    changed[field]=value
    with pytest.raises(ObservationImportError,match='subject_dispatch_authority_mismatch'):
        store.register_dispatch(changed,expected_dispatch=dispatch)
    assert store.dispatch_count()==0 and store.counts()['observations']==0


def test_old_import_cannot_be_retroactively_registered_or_bound(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    with pytest.raises(ObservationImportError,match='subject_dispatch_answer_already_exists'):
        register(store,dispatch)
    assert store.binding_for_observation(decision['observation_id']) is None


def test_registration_after_actual_send_time_rolls_back_answer_and_ack(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    clock[0]='2026-10-10T08:58:00Z'
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    with pytest.raises(ObservationImportError,match='subject_dispatch_original_mismatch'):
        store.apply_decisions([decision])
    assert store.counts()['observations']==store.counts()['acked_items']==0
    assert store.dispatch_count()==1


def test_same_attempt_question_cannot_register_two_subject_revisions(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    changed=copy.deepcopy(dispatch)
    changed['subject_ref']['analysis_subject_revision']=2
    with pytest.raises(ObservationImportError,match='subject_dispatch_immutable_conflict'):
        register(store,changed)


def test_sidecars_are_sqlite_immutable_and_old_writer_refuses_schema3(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    with sqlite3.connect(store.database_path) as con:
        for sql in ('UPDATE quick_scan_subject_dispatch SET receipt_json=receipt_json',
                    'DELETE FROM quick_scan_subject_dispatch',
                    'UPDATE quick_scan_subject_binding SET binding_json=binding_json',
                    'DELETE FROM quick_scan_subject_binding'):
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(sql)
    with pytest.raises(ObservationImportError,match='observation_store_newer_schema'):
        old.migrate()


def test_atomic_batch_does_not_keep_first_answer_when_second_binding_is_wrong(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    other_dispatch=copy.deepcopy(dispatch)
    other_dispatch['execution_attempt_id']='SYN_ATT_2'
    register(store,other_dispatch)
    other=copy.deepcopy(decision)
    other['observation']['execution']['attempt_id']='SYN_ATT_2'
    other['observation']['execution']['model_requested']='foreign'
    obs=other['observation']
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    other['observation_id']=obs['observation_id']
    other['payload_sha256']=qc._digest(obs)
    other['item_id']='itm_'+qc._digest({k:other[k] for k in ('observation_id','payload_sha256')})
    other['exec_key']=qc._digest(obs['execution'])
    clock[0]='2026-10-10T08:59:00Z'
    with pytest.raises(ObservationImportError,match='subject_dispatch_original_mismatch'):
        store.apply_decisions([decision,other])
    assert store.counts()['observations']==store.counts()['acked_items']==0
    assert store.binding_for_observation(decision['observation_id']) is None


def query(paths,dispatch,*,history=True):
    reader=QueryReader(paths,contract=qc,clock=lambda:'2026-10-10T09:00:00Z')
    request=dc.query_request(dispatch,'2026-10-10T09:00:00Z')
    request['payload']['include_history']=history
    return reader,request


def test_actual_pre_and_post_owner_records_produce_bound_original_current_projection(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    pre=register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    reader,request=query(paths,dispatch,history=False)
    response=reader.get_profiles(request)
    assert response['result']['status']=='ok'
    row=response['result']['profiles'][0]['observations'][0]
    assert row['binding_status']=='bound'
    assert row['subject_binding']['recorded_before_send_at']==pre['registered_at']
    assert reader.owner_context['observation_refs'][row['observation_id']]['binding_sha256']==qc._digest(row['subject_binding'])
    assert response['result']['legacy_unbound_observations']==[]
    qc.validate_response(response,expected_request=request,expected_owner=reader.owner_context)


def test_bound_original_is_never_reassigned_to_requested_later_subject_revision(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    reader,request=query(paths,dispatch)
    request['payload']['subject_refs'][0]['analysis_subject_revision']=2
    response=reader.get_profiles(request)
    assert response['result']['status']=='coverage_gap'
    assert response['result']['profiles']==[]
    assert response['result']['legacy_unbound_observations']==[]


def test_bound_and_unbound_originals_remain_separate_in_the_same_schema3_store(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    legacy=copy.deepcopy(decision)
    obs=legacy['observation']
    obs['execution']['attempt_id']='LEGACY_ATT'
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    legacy['observation_id']=obs['observation_id']
    legacy['payload_sha256']=qc._digest(obs)
    legacy['item_id']='itm_'+qc._digest({k:legacy[k] for k in ('observation_id','payload_sha256')})
    legacy['exec_key']=qc._digest(obs['execution'])
    store.apply_decisions([legacy])
    reader,request=query(paths,dispatch)
    response=reader.get_profiles(request)
    assert response['result']['status']=='ok'
    assert [r['observation_id'] for r in response['result']['profiles'][0]['observations']]==[decision['observation_id']]
    assert [r['observation_id'] for r in response['result']['legacy_unbound_observations']]==[legacy['observation_id']]
    request['payload']['include_history']=False
    assert reader.get_profiles(request)['result']['legacy_unbound_observations']==[]


@pytest.mark.parametrize('field,value',[
    ('provider','foreign'),('model_requested','foreign'),('prompt_sha256','f'*64),
    ('question_id','IQS_02'),('question_semantic_sha256','f'*64),('module_release_id','modrel_'+'f'*64)])
def test_changed_answer_cannot_escape_binding_check_by_becoming_legacy(tmp_path,monkeypatch,field,value):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    obs=decision['observation']
    if field in {'provider','model_requested','prompt_sha256'}:
        obs['execution'][field]=value
    else:
        obs[field]=value
        if field=='question_id': obs['answer']['question_id']=value
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    decision['observation_id']=obs['observation_id']
    decision['payload_sha256']=qc._digest(obs)
    decision['item_id']='itm_'+qc._digest({k:decision[k] for k in ('observation_id','payload_sha256')})
    decision['exec_key']=qc._digest(obs['execution'])
    with pytest.raises(ObservationImportError,match='subject_dispatch_original_mismatch'):
        store.apply_decisions([decision])
    assert store.counts()['observations']==store.counts()['acked_items']==0


def test_reader_refuses_removed_schema3_immutability_trigger_as_read_failure(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-10T08:59:00Z'
    store.apply_decisions([decision])
    with sqlite3.connect(store.database_path) as con:
        con.execute('DROP TRIGGER quick_scan_subject_binding_no_update')
    reader,request=query(paths,dispatch)
    response=reader.get_profiles(request)
    assert response['result']['status']=='unavailable'
    assert response['result']['profiles'][0]['observations']==[]
    assert response['result']['coverage']['scores_available'] is False


def test_binding_clock_cannot_claim_post_import_before_the_original_ack(tmp_path,monkeypatch):
    paths,store,dispatch,decision,clock,old=workspace(tmp_path,monkeypatch)
    register(store,dispatch)
    clock[0]='2026-10-09T20:02:00Z'  # after answer, but before actual ACK next day
    with pytest.raises(ObservationImportError,match='subject_dispatch_original_mismatch'):
        store.apply_decisions([decision])
    assert store.counts()['observations']==store.counts()['acked_items']==0
