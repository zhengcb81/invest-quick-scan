"""Real owner SQLite and serializers with synthetic identities, never real gold."""
import copy
import hashlib
import json
import sqlite3

import pytest

import query_contract as qc
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
