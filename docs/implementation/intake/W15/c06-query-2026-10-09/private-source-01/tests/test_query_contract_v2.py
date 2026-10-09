"""Synthetic scope/coverage boundary fixtures; never a real owner golden."""
import copy

import pytest

import query_contract as qc


SUBJECT = {
    'entity_id': 'ENT_11111111-1111-4111-8111-111111111111',
    'analysis_subject_id': 'ASJ_22222222-2222-4222-8222-222222222222',
    'analysis_subject_revision': 1,
    'primary_issuer_id': 'ENT_33333333-3333-4333-8333-333333333333',
    'perimeter_sha256': 'a'*64,
    'scope': 'entity',
    'scope_id': 'ENT_11111111-1111-4111-8111-111111111111',
    'security_id': None, 'listing_id': None, 'segment_id': None,
}


def pair():
    request = {'message_type':'request','schema_version':'2.0.0','request_id':'REQ_SYNTHETIC_C06',
               'consumer_id':'invest-quick-scan','operation':'get_profiles',
               'requested_at':'2026-10-09T21:00:00Z',
               'payload':{'subject_refs':[copy.deepcopy(SUBJECT)],'field_ids':['IQS_01'],
                          'information_cutoff':'2026-10-09','include_history':True,
                          'model_filter':None,'snapshot_id':None}}
    coverage = {'status':'not_covered','requested_markets':['US'],'covered_markets':[],
                'requested_field_ids':['IQS_01'],'covered_field_ids':[],
                'missing_field_ids':['IQS_01'],'scores_available':False,'facts_available':False,
                'reason':'synthetic no observation coverage'}
    watermark = {'store_id':'STORE_SYNTHETIC_C06','snapshot_id':'SNAP_SYNTHETIC_C06',
                 'member_sequence':0,'observation_sequence':0,'ack_sequence':0,
                 'read_at':'2026-10-09T21:01:00Z'}
    response = {'message_type':'response','schema_version':'2.0.0','request_id':request['request_id'],
                'operation':'get_profiles','response_at':'2026-10-09T21:01:00Z',
                'result':{'status':'coverage_gap','profiles':[{'subject_ref':copy.deepcopy(SUBJECT),
                           'canonical_name':'Synthetic C06','observations':[]}],
                          'missing_subject_refs':[],'coverage':coverage,'watermark':watermark}}
    owner = {'store_id':'STORE_SYNTHETIC_C06'}
    return request, response, owner


def validate(request, response, owner):
    qc.validate_request(request)
    qc.validate_response(response,expected_request=request,expected_owner=owner)


def test_real_uuid_spelling_and_distinct_scan_entity_vs_legal_issuer():
    validate(*pair())


def test_two_reporting_subjects_for_one_entity_are_two_profiles():
    request, response, owner = pair()
    other = copy.deepcopy(SUBJECT)
    other['analysis_subject_id']='ASJ_44444444-4444-4444-8444-444444444444'
    other['perimeter_sha256']='b'*64
    request['payload']['subject_refs'].append(other)
    response['result']['profiles'].append({'subject_ref':copy.deepcopy(other),
                                           'canonical_name':'Synthetic C06','observations':[]})
    validate(request,response,owner)


@pytest.mark.parametrize('field,new',[
    ('analysis_subject_revision',2), ('perimeter_sha256','b'*64),
    ('primary_issuer_id','ENT_55555555-5555-4555-8555-555555555555'),
    ('entity_id','ENT_66666666-6666-4666-8666-666666666666'),
    ('scope_id','ENT_66666666-6666-4666-8666-666666666666'),
])
def test_profile_cannot_drift_from_requested_subject(field,new):
    request,response,owner=pair()
    response['result']['profiles'][0]['subject_ref'][field]=new
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_conflicting_perimeters_for_same_subject_are_not_two_requests():
    request,response,owner=pair()
    other=copy.deepcopy(SUBJECT)
    other['perimeter_sha256']='b'*64
    request['payload']['subject_refs'].append(other)
    with pytest.raises(ValueError):
        qc.validate_request(request)


def test_response_cannot_return_same_profile_twice():
    request,response,owner=pair()
    response['result']['profiles']*=2
    with pytest.raises(ValueError):
        validate(request,response,owner)


@pytest.mark.parametrize('kind',['complete','overlap','unrequested'])
def test_field_coverage_is_an_exact_partition_of_request(kind):
    request,response,owner=pair()
    coverage=response['result']['coverage']
    if kind=='complete': coverage['status']='complete'
    elif kind=='overlap': coverage['covered_field_ids']=['IQS_01']
    else: coverage['missing_field_ids']=['IQS_02']
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_response_store_must_match_independent_owner():
    request,response,owner=pair()
    response['result']['watermark']['store_id']='STORE_FOREIGN'
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_response_requires_explicit_independent_owner():
    request,response,_=pair()
    with pytest.raises(ValueError):
        qc.validate_response(response,expected_request=request,expected_owner=None)


@pytest.mark.parametrize('field,value',[('request_id','REQ_FOREIGN'),('schema_version','1.0.0'),('operation','search')])
def test_response_does_not_silently_change_request_or_protocol(field,value):
    request,response,owner=pair()
    response[field]=value
    with pytest.raises(ValueError):
        validate(request,response,owner)


@pytest.mark.parametrize('raw',[b'{"request_id":"one","request_id":"two"}',b'{"x":NaN}',b'{"x":1e400}',b'{"truncated":'])
def test_strict_input_rejects_duplicate_nonfinite_and_truncated_json(tmp_path,raw):
    path=tmp_path/'input.json'
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        qc.load_document(path)
