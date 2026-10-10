"""Real owner SQLite and serializers with synthetic identities, never real gold."""
import copy
import hashlib
import json
import sqlite3
import base64
import runpy
from pathlib import Path

import pytest

import query_contract as qc
import stockwiki.quick_scan_observations as observation_module
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_analysis import AnalysisSubjectStore, perimeter_sha256
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.quick_scan_query_v2 import QueryReader, QueryReadError

NOW='2026-10-10T09:00:00Z'
ENTITY='ENT_11111111-1111-4111-8111-111111111111'
ASJ='ASJ_22222222-2222-4222-8222-222222222222'


def snapshot(root):
    return {str(p.relative_to(root)):(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob('*') if p.is_file()}


def workspace(tmp_path):
    paths=WorkspacePaths.from_root(tmp_path/'workspace')
    identity=QuickScanStore(paths)
    identity.migrate()
    entity={'identity_schema_version':'2.0.0','identity_state':'verified','identity_revision':1,
        'entity_id':ENTITY,'canonical_name':'Synthetic query company','incorporation_country':'US',
        'scope_attestation_id':'ATT_SYNTHETIC','verified_issuer_receipt_id':'VIR_SYNTHETIC',
        'company_wiki_ref':None,'formal_stockwiki_profile':None,'securities':[],'segments':[]}
    identity.save_entity(entity,source_bindings=[])
    subject={'analysis_subject_schema_version':'1.0.0','analysis_subject_id':ASJ,
        'analysis_subject_revision':1,'display_name':'Synthetic reporting scope',
        'primary_issuer_id':ENTITY,'anchor_listing_id':None,'scope_kind':'standalone_issuer',
        'scope_as_of':'2026-10-09T00:00:00Z','perimeter_coverage':'not_applicable',
        'memberships':[{'entity_id':ENTITY,'role':'primary_issuer','valid_from':None,
            'valid_to':None,'evidence_ref':'https://example.com/synthetic-subject'}]}
    receipt={'receipt_id':'PRC_SYNTHETIC','status':'verified','analysis_subject_id':ASJ,
        'analysis_subject_revision':1,'primary_issuer_id':ENTITY,
        'evidence_ref':'https://example.com/synthetic-perimeter',
        'perimeter_sha256':perimeter_sha256(subject)}
    subjects=AnalysisSubjectStore(paths)
    subjects.migrate()
    subjects.import_subject(identity,{'analysis_subject':subject,'perimeter_receipt':receipt},at=NOW)
    observations=QuickScanObservationStore(paths)
    observations.migrate()
    ref={'entity_id':ENTITY,'analysis_subject_id':ASJ,'analysis_subject_revision':1,
        'primary_issuer_id':ENTITY,'perimeter_sha256':perimeter_sha256(subject),
        'scope':'entity','scope_id':ENTITY,'security_id':None,'listing_id':None,'segment_id':None}
    request={'message_type':'request','schema_version':'2.0.0','request_id':'REQ_SYNTHETIC_OWNER',
        'consumer_id':'invest-quick-scan','operation':'get_profiles','requested_at':NOW,
        'payload':{'subject_refs':[ref],'field_ids':['IQS_01'],'information_cutoff':'2026-10-09',
                   'include_history':True,'model_filter':None,'snapshot_id':None}}
    reader=QueryReader(paths,contract=qc,clock=lambda:NOW)
    return paths,identity,subjects,observations,request,reader


def test_existing_owner_databases_return_true_empty_coverage_without_any_file_change(tmp_path):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    assert response['result']['status']=='coverage_gap'
    assert response['result']['profiles'][0]['canonical_name']=='Synthetic query company'
    assert response['result']['profiles'][0]['subject_ref']==request['payload']['subject_refs'][0]
    assert response['result']['coverage']['missing_field_ids']==['IQS_01']
    assert all(s['status']=='available' for s in response['result']['watermark']['source_watermarks'])
    assert before==snapshot(paths.root)
    qc.validate_response(response,expected_request=request,expected_owner=reader.owner_context)


def test_missing_observation_database_is_not_created_or_laundered_as_empty(tmp_path):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    observations.database_path.unlink()  # Only this test-owned fixture.
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    assert response['result']['status']=='unavailable'
    assert response['result']['coverage']['status']=='unknown'
    assert next(s for s in response['result']['watermark']['source_watermarks']
                if s['namespace']=='observations')['status']=='missing'
    assert not observations.database_path.exists()
    assert before==snapshot(paths.root)


@pytest.mark.parametrize('kind',['unknown_schema','missing_table','bad_bytes'])
def test_owner_read_failure_is_explicit_and_never_triggers_migration(tmp_path,kind):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    if kind=='bad_bytes': observations.database_path.write_bytes(b'not a SQLite database')
    else:
        with sqlite3.connect(observations.database_path) as con:
            con.execute('PRAGMA user_version=99' if kind=='unknown_schema'
                        else 'DROP TABLE quick_scan_import_item')
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    assert response['result']['status']=='unavailable'
    expected='schema_unavailable' if kind=='unknown_schema' else 'read_error'
    assert next(s for s in response['result']['watermark']['source_watermarks']
                if s['namespace']=='observations')['status']==expected
    assert before==snapshot(paths.root)


@pytest.mark.parametrize('field,value',[
    ('analysis_subject_revision',2),('perimeter_sha256','9'*64),
    ('primary_issuer_id','ENT_33333333-3333-4333-8333-333333333333')])
def test_request_does_not_assign_an_existing_company_to_a_different_subject(tmp_path,field,value):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    request['payload']['subject_refs'][0][field]=value
    response=reader.get_profiles(request)
    assert response['result']['profiles']==[]
    assert response['result']['missing_subject_refs']==request['payload']['subject_refs']
    assert response['result']['status']=='coverage_gap'


def test_owner_serializer_is_content_addressed_and_returns_independent_copies(tmp_path):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    response=reader.get_profiles(request)
    original=copy.deepcopy(response)
    response['result']['profiles'][0]['canonical_name']='caller mutation'
    again=reader.get_profiles(request)
    assert again==original
    assert again['result']['watermark']['read_consistency']=='sequential_owner_reads'
    assert again['result']['watermark']['snapshot_id'].startswith('snap2_')


def test_an_unknown_snapshot_is_rejected_before_database_access(tmp_path,monkeypatch):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    request['payload']['snapshot_id']='SNAP_UNKNOWN'
    def forbidden(*args,**kwargs):
        raise AssertionError('must not fall back to live SQLite for an unknown snapshot')
    monkeypatch.setattr(sqlite3,'connect',forbidden)
    with pytest.raises(QueryReadError,match='snapshot_unavailable'):
        reader.get_profiles(request)


@pytest.mark.parametrize('namespace',['identity','analysis_subjects'])
def test_missing_other_owner_namespace_returns_named_unavailable_not_a_crash(tmp_path,namespace):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    database=identity.database_path if namespace=='identity' else subjects.database_path
    database.unlink()  # Only the explicit owned fixture.
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    assert response['result']['status']=='unavailable'
    assert response['result']['coverage']['status']=='unknown'
    assert response['result']['profiles']==[]
    assert response['result']['missing_subject_refs']==request['payload']['subject_refs']
    assert next(s for s in response['result']['watermark']['source_watermarks']
                if s['namespace']==namespace)['status']=='missing'
    assert not database.exists()
    assert before==snapshot(paths.root)
    qc.validate_response(response,expected_request=request,expected_owner=reader.owner_context)


def test_active_wal_is_not_ignored_or_mutated_to_claim_an_empty_database(tmp_path):
    paths,identity,subjects,observations,request,reader=workspace(tmp_path)
    con=sqlite3.connect(observations.database_path)
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('CREATE TABLE synthetic_wal_marker(value INTEGER)')
        con.commit()
        assert observations.database_path.with_name(observations.database_path.name+'-wal').exists()
        before=snapshot(paths.root)
        response=reader.get_profiles(request)
        assert response['result']['status']=='unavailable'
        assert next(s for s in response['result']['watermark']['source_watermarks']
                    if s['namespace']=='observations')['status']=='read_error'
        assert before==snapshot(paths.root)
    finally:
        con.close()


def imported_observation(store,monkeypatch,*,model='actual-a',status='scored',field_id='IQS_01',package_digit='4'):
    # Reuse the complete synthetic wire fixture; no second maintained answer builder.
    factory=runpy.run_path(str(Path(__file__).resolve().parents[2]/'iqs/tests/test_query_contract_v2.py'))
    obs=factory['observation'](model=model,status=status)
    obs['field_id']=obs['question_id']=obs['answer']['question_id']=field_id
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    monkeypatch.setattr(observation_module,'_now',lambda:'2026-10-10T08:59:00Z')
    decision={'package_id':'pkg_'+package_digit*64,'item_id':'itm_'+qc._digest(obs),
              'observation_id':obs['observation_id'],'payload_sha256':qc._digest(obs),
              'observation':obs,'status':'accepted','error_code':None,
              'exec_key':qc._digest({'execution':obs['execution'],'field':field_id})}
    ack=store.apply_decisions([decision])[0]
    return obs,ack


def test_actual_store_original_unbound_answer_is_separate_history_not_current_coverage(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    obs,ack=imported_observation(store,monkeypatch)
    with sqlite3.connect(store.database_path) as con:
        raw=con.execute('SELECT payload_json FROM quick_scan_observation').fetchone()[0].encode()
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    result=response['result']
    assert result['profiles'][0]['observations']==[]
    assert result['status']=='coverage_gap' and result['coverage']['scores_available'] is False
    row=result['legacy_unbound_observations'][0]
    assert row['binding_status']=='legacy_unbound' and row['subject_binding'] is None
    assert row['ack_sequence']==row['observation_sequence']==1 and row['ingest_status']=='accepted'
    assert base64.b64decode(row['original_json_base64'])==raw
    assert json.loads(raw)==obs and obs['execution']['model_requested']=='requested-a'
    assert obs['execution']['model_resolved']=='actual-a'
    assert reader.owner_context['observation_refs'][obs['observation_id']]['binding_sha256'] is None
    assert before==snapshot(paths.root)
    qc.validate_response(response,expected_request=request,expected_owner=reader.owner_context)


def test_history_off_does_not_reassign_legacy_rows_to_current_subject(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch)
    request['payload']['include_history']=False
    response=reader.get_profiles(request)
    assert response['result']['legacy_unbound_observations']==[]
    assert response['result']['profiles'][0]['observations']==[]
    assert response['result']['coverage']['scores_available'] is False


def test_legacy_model_filter_uses_actual_model_and_field_filter_excludes_other_answers(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch,model='actual-a')
    selected,_=imported_observation(store,monkeypatch,model='actual-b',package_digit='5')
    imported_observation(store,monkeypatch,model='actual-b',field_id='IQS_02',package_digit='6')
    request['payload']['model_filter']={'provider':'synthetic-provider','model_resolved':'actual-b'}
    response=reader.get_profiles(request)
    assert [r['observation_id'] for r in response['result']['legacy_unbound_observations']]==[selected['observation_id']]
    request['payload']['model_filter']['model_resolved']='requested-a'
    assert reader.get_profiles(request)['result']['legacy_unbound_observations']==[]


def test_duplicate_delivery_keeps_original_ack_and_observation_sequence(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    obs,first=imported_observation(store,monkeypatch)
    same,again=imported_observation(store,monkeypatch,package_digit='5')
    assert again['status']=='already_present' and same==obs
    response=reader.get_profiles(request)
    row=response['result']['legacy_unbound_observations'][0]
    assert row['ack_sequence']==row['observation_sequence']==1
    assert response['result']['watermark']['ack_sequence']==2
    assert response['result']['watermark']['observation_sequence']==1


def test_existing_subject_columns_are_not_a_before_send_binding_receipt(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch)
    with sqlite3.connect(store.database_path) as con:
        con.execute('UPDATE quick_scan_observation SET analysis_subject_id=?,analysis_subject_revision=1,primary_issuer_id=?',(ASJ,ENTITY))
    response=reader.get_profiles(request)
    assert response['result']['profiles'][0]['observations']==[]
    assert response['result']['legacy_unbound_observations'][0]['subject_binding'] is None


def test_captured_snapshot_replay_uses_original_data_even_when_request_time_and_store_change(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch)
    original=reader.get_profiles(request)
    original_owner=reader.owner_context
    with sqlite3.connect(identity.database_path) as con:
        con.execute('UPDATE quick_scan_entity SET canonical_name=?',('Changed after capture',))
    replay=copy.deepcopy(request)
    replay['request_id']='REQ_REPLAY'
    replay['requested_at']='2026-10-10T09:10:00Z'
    replay['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    reader.clock=lambda:'2026-10-10T09:11:00Z'
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no live fallback')))
    response=reader.get_profiles(replay)
    assert response['result']==original['result']
    assert response['request_id']=='REQ_REPLAY' and response['response_at']=='2026-10-10T09:11:00Z'
    assert reader.owner_context==original_owner
    qc.validate_response(response,expected_request=replay,expected_owner=original_owner)


def test_snapshot_for_a_different_query_is_rejected_before_any_database_read(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    original=reader.get_profiles(request)
    request['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    request['payload']['field_ids']=['IQS_02']
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no live fallback')))
    with pytest.raises(QueryReadError,match='snapshot_query_mismatch'):
        reader.get_profiles(request)


def test_owner_subject_columns_and_original_json_must_have_the_same_subject_id(tmp_path):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    foreign='ASJ_44444444-4444-4444-8444-444444444444'
    with sqlite3.connect(subjects.database_path) as con:
        con.execute('UPDATE analysis_subject SET analysis_subject_id=?',(foreign,))
    request['payload']['subject_refs'][0]['analysis_subject_id']=foreign
    with pytest.raises(QueryReadError,match='owner_subject_read_error'):
        reader.get_profiles(request)


@pytest.mark.parametrize('damage',[
    'missing_ack','foreign_store','ack_sequence','duplicate_ack_key',
    'payload_hash','metadata_model','observation_sequence'])
def test_damaged_owner_receipt_or_original_is_not_returned_as_trusted_history(tmp_path,monkeypatch,damage):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch)
    with sqlite3.connect(store.database_path) as con:
        if damage=='missing_ack':
            con.execute('DELETE FROM quick_scan_import_item')
        elif damage=='foreign_store':
            con.execute("UPDATE quick_scan_import_item SET store_id='foreign'")
        elif damage=='ack_sequence':
            con.execute('UPDATE quick_scan_import_item SET ack_sequence=2')
        elif damage=='duplicate_ack_key':
            raw=con.execute('SELECT ack_json FROM quick_scan_import_item').fetchone()[0]
            con.execute('UPDATE quick_scan_import_item SET ack_json=?',
                        ('{"status":"rejected",'+raw[1:],))
        elif damage=='payload_hash':
            con.execute('UPDATE quick_scan_observation SET payload_sha256=?',('0'*64,))
        elif damage=='metadata_model':
            con.execute("UPDATE quick_scan_observation SET model_resolved='foreign'")
        else:
            con.execute('UPDATE quick_scan_observation SET import_sequence=2')
    before=snapshot(paths.root)
    with pytest.raises(QueryReadError,match='owner_observation_read_error'):
        reader.get_profiles(request)
    assert before==snapshot(paths.root)


def test_expired_snapshot_fails_without_reading_current_store(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    elapsed=[0.0]
    reader.elapsed_clock=lambda:elapsed[0]
    original=reader.get_profiles(request)
    elapsed[0]=3601
    request['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no live fallback')))
    with pytest.raises(QueryReadError,match='snapshot_expired'):
        reader.get_profiles(request)


def test_a_new_reader_does_not_pretend_to_have_durable_capture_storage(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    original=reader.get_profiles(request)
    request['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    new=QueryReader(paths,contract=qc,clock=lambda:NOW)
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no live fallback')))
    with pytest.raises(QueryReadError,match='snapshot_unavailable'):
        new.get_profiles(request)


def test_capture_retention_is_bounded_and_does_not_change_remaining_snapshots(tmp_path,monkeypatch):
    import stockwiki.quick_scan_query_v2 as owner_module
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    monkeypatch.setattr(owner_module,'MAX_SNAPSHOTS',2)
    original=reader.get_profiles(request)
    request['payload']['field_ids']=['IQS_02']
    second=reader.get_profiles(request)
    request['payload']['field_ids']=['IQS_03']
    third=reader.get_profiles(request)
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no live fallback')))
    request['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    with pytest.raises(QueryReadError,match='snapshot_unavailable'):
        reader.get_profiles(request)
    request['payload']['snapshot_id']=third['result']['watermark']['snapshot_id']
    assert reader.get_profiles(request)['result']==third['result']
    assert second['result']['watermark']['snapshot_id']!=third['result']['watermark']['snapshot_id']


def test_many_real_duplicate_deliveries_do_not_exhaust_requested_original_query(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    obs,first=imported_observation(store,monkeypatch)
    # All duplicate ACKs are produced by the actual owner transaction, not
    # hand-written ledger rows. Selection should only need original receipt1.
    decisions=[{'package_id':'pkg_'+hashlib.sha256(str(n).encode()).hexdigest(),
                'item_id':first['item_id'],'observation_id':obs['observation_id'],
                'payload_sha256':qc._digest(obs),'observation':obs,'status':'accepted',
                'error_code':None,'exec_key':qc._digest({'execution':obs['execution'],'field':'IQS_01'})}
               for n in range(5001)]
    acks=store.apply_decisions(decisions)
    assert len(acks)==5001 and all(a['status']=='already_present' for a in acks)
    before=snapshot(paths.root)
    response=reader.get_profiles(request)
    result=response['result']
    assert len(result['legacy_unbound_observations'])==1
    assert result['legacy_unbound_observations'][0]['ack_sequence']==1
    assert result['watermark']['ack_sequence']==5002
    assert result['watermark']['observation_sequence']==1
    assert before==snapshot(paths.root)


def test_information_cutoff_does_not_return_later_originals(tmp_path,monkeypatch):
    paths,identity,subjects,store,request,reader=workspace(tmp_path)
    imported_observation(store,monkeypatch)
    request['payload']['information_cutoff']='2026-10-07'
    response=reader.get_profiles(request)
    assert response['result']['legacy_unbound_observations']==[]
    assert response['result']['missing_subject_refs']==request['payload']['subject_refs']
    assert response['result']['watermark']['observation_sequence']==1
