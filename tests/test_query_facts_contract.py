"""Synthetic F05 facts wire 2.7.0 contract tests; never a real owner golden.

Every fixture below is a synthetic protocol sample built against the frozen
owner schema (schemas/quick_scan/query-facts-v2.7.schema.json, SHA-256 pinned
to the package card). No production path, no network, no real owner store.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest

import query_contract as qc
import query_facts_contract as fc


SCHEMA_SHA256 = 'cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad'
OWNER_RELATIONS = ['sells_to', 'supplies', 'buys_input_from', 'partners_with']
READ_AT = '2026-10-09T21:01:00Z'
STORE = 'STORE_SYNTHETIC_C06'

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


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                    ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def test_schema_is_byte_copy_of_frozen_owner_schema():
    path = Path(fc.__file__).resolve().parents[1]/'schemas/quick_scan/query-facts-v2.7.schema.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SCHEMA_SHA256


def fact_observation(*, cutoff='2026-10-08', relation='sells_to', role='customer',
                     stage='commercial', valid_from='2026-01-01', valid_to=None,
                     review='reviewed', cp_name='Synthetic Counterparty Co',
                     canonical='ENT_CP_0001', confidence='high',
                     observed_at='2026-10-09T20:01:00Z'):
    """Complete but deliberately synthetic portable fact Observation."""
    answer = {'question_id':'facts.test_chain','response_kind':'fact','status':'answered',
        'score':None,'summary':'synthetic facts answer','information_as_of':cutoff,
        'period_start':'2026-01-01','period_end':'2026-06-30','basis':'current',
        'trend':'stable','confidence':'medium','metrics':[],
        'items':[{'name':cp_name,'canonical_entity_id':canonical,
                  'aliases':['Synthetic CP'],'relation':relation,'segment':None,
                  'role':role,'commercial_stage':stage,
                  'description':'synthetic supply relation','valid_from':valid_from,
                  'valid_to':valid_to,'taxonomy_id':None,'metrics':[],
                  'evidence_ids':['E1'],'confidence':confidence}],
        'evidence':[{'id':'E1','title':'synthetic pointer','url':'https://example.com/evidence',
                     'published_at':cutoff,'claim':'synthetic claim'}],
        'counterevidence':'synthetic uncertainty','watch_triggers':[],'missing_fields':[],
        'coverage':{'status':'partial','reason':'synthetic scope'}}
    obs = {'schema_version':'1.1.0','entity_id':SUBJECT['entity_id'],'security_id':None,
        'segment_id':None,'field_id':'facts.test_chain','construct_id':None,
        'question_id':'facts.test_chain','question_version':'1.0',
        'template_version':'synthetic-v1','method_id':'synthetic-method',
        'scope':'entity','cohort':{'company_type':'unclassified','industries':[],
                                  'stage':'unclassified','subtype':None},
        'information_cutoff':cutoff,'run_id':'SYN_RUN','scan_id':'SYN_SCAN',
        'inputset_id':'SYN_INPUT','task_mode':'primary','comparison_group_id':None,
        'observed_at':observed_at,
        'execution':{'provider':'synthetic-provider','model_requested':'requested-a',
            'model_resolved':'actual-a','model_revision':None,'request_id':'SYN_REQ',
            'attempt_id':'SYN_ATT','started_at':'2026-10-09T20:00:00Z',
            'answered_at':observed_at,'search_status':'executed',
            'search_receipt_id':'SYN_SEARCH','prompt_sha256':'c'*64},
        'answer':answer,'evidence_review_status':review,'module_package_id':'pkg_'+'4'*64,
        'module_release_id':'modrel_'+'5'*64,'question_definition_sha256':'d'*64,
        'question_semantic_sha256':'e'*64,'cycle_sensitive':False}
    obs['observation_id']='obs_'+digest(obs)
    return obs


def score_observation(*, cutoff='2026-10-08'):
    """One scored non-fact observation: validated but never projected as a fact."""
    answer = {'question_id':'IQS_01','response_kind':'score','status':'scored',
        'score':8,'summary':'synthetic answer','information_as_of':cutoff,
        'period_start':None,'period_end':None,'basis':'current','trend':'stable',
        'confidence':'low','metrics':[],'items':[],
        'evidence':[{'id':'E1','title':'synthetic pointer','url':'https://example.com/evidence',
                     'published_at':cutoff,'claim':'synthetic claim'}],
        'counterevidence':'synthetic uncertainty','watch_triggers':[],'missing_fields':[],
        'coverage':{'status':'partial','reason':'synthetic scope'}}
    obs = {'schema_version':'1.1.0','entity_id':SUBJECT['entity_id'],'security_id':None,
        'segment_id':None,'field_id':'IQS_01','construct_id':None,'question_id':'IQS_01',
        'question_version':'1.0','template_version':'synthetic-v1',
        'method_id':'synthetic-method','scope':'entity',
        'cohort':{'company_type':'unclassified','industries':[],'stage':'unclassified',
                  'subtype':None},
        'information_cutoff':cutoff,'run_id':'SYN_RUN','scan_id':'SYN_SCAN',
        'inputset_id':'SYN_INPUT','task_mode':'primary','comparison_group_id':None,
        'observed_at':'2026-10-09T20:01:00Z',
        'execution':{'provider':'synthetic-provider','model_requested':'requested-a',
            'model_resolved':'actual-a','model_revision':None,'request_id':'SYN_REQ',
            'attempt_id':'SYN_ATT','started_at':'2026-10-09T20:00:00Z',
            'answered_at':'2026-10-09T20:01:00Z','search_status':'executed',
            'search_receipt_id':'SYN_SEARCH','prompt_sha256':'c'*64},
        'answer':answer,'evidence_review_status':'unreviewed',
        'module_package_id':'pkg_'+'4'*64,'module_release_id':'modrel_'+'5'*64,
        'question_definition_sha256':'d'*64,'question_semantic_sha256':'e'*64,
        'cycle_sensitive':False}
    obs['observation_id']='obs_'+digest(obs)
    return obs


def projection(obs,*,bound=True,sequence=1,qualification='review_pending',
               ingest='accepted'):
    raw=json.dumps(obs,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    binding={'protocol':'stockwiki.observation_subject_binding/1.0.0',
             'receipt_id':'SYN_BINDING','subject_ref':copy.deepcopy(SUBJECT),
             'observation_id':obs['observation_id'],'payload_sha256':digest(obs),
             'execution_request_id':obs['execution']['request_id'],
             'execution_attempt_id':obs['execution']['attempt_id'],
             'dispatch_identity_snapshot_sha256':'f'*64,'dispatch_manifest_sha256':'1'*64,
             'recorded_before_send_at':'2026-10-09T19:59:00Z'} if bound else None
    return {'observation_id':obs['observation_id'],'payload_sha256':digest(obs),
            'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'original_json_base64':base64.b64encode(raw).decode(),
            'observation_wire_profile':'stockwiki-portable-observation/1.0.0',
            'binding_status':'bound' if bound else 'legacy_unbound',
            'subject_binding':binding,'observation_sequence':sequence,'ack_sequence':sequence,
            'ingest_status':ingest,'qualification_status':qualification}


def fact_request(**overrides):
    payload = dict(mode='explore',entity_ids=[SUBJECT['entity_id']],markets=[],
        listing_ids=[],field_ids=['facts.test_chain'],information_cutoff='2026-10-09',
        model_filter=None,relation_types=[],direction=None,counterparty=None,
        commercial_stages=[],segment_ids=[],period=None,evidence='require_resolved',
        quality_conditions=None,page=None,snapshot_id=None)
    payload.update({k:v for k,v in overrides.items() if k in payload})
    request = dict(message_type='request',schema_version='2.7.0',
        request_id='REQ_SYNTHETIC_FACTS',consumer_id='invest-quick-scan',
        operation='query_facts',requested_at='2026-10-09T21:00:00Z',label=None,
        payload=payload)
    request.update({k:v for k,v in overrides.items() if k not in payload})
    return request


def default_marks(*, read_at=READ_AT, failed=None):
    marks = [{'namespace':'identity','schema_version':6,'status':'available',
              'sequence':0,'read_at':read_at,'content_sha256':'2'*64},
             {'namespace':'observations','schema_version':3,'status':'available',
              'sequence':0,'read_at':read_at,'content_sha256':'3'*64}]
    if failed is not None:
        marks[-1] = dict(marks[-1],status=failed,content_sha256=None)
    return marks


def fact_profile_result(rows=(),*,missing=(),classification_gap=False,
                        sequence=None,marks=None):
    rows=list(rows)
    return {'profiles':[{'subject_ref':copy.deepcopy(SUBJECT),
                         'canonical_name':'Synthetic C06','observations':rows,
                         'matched_listings':[{'market':'US','ticker':'SYN',
                                              'listing_id':'L1'}]}],
            'legacy_unbound_observations':[],
            'missing_subject_refs':list(missing),
            'classification_gap':classification_gap,
            'watermark':{'store_id':STORE,
                'observation_sequence':sequence if sequence is not None
                    else max([row['observation_sequence'] for row in rows]+[0]),
                'source_watermarks':default_marks() if marks is None else marks,
                'read_at':READ_AT}}


def fact_owner(rows):
    refs={}
    for row in rows:
        refs[row['observation_id']]={'payload_sha256':row['payload_sha256'],
            'binding_sha256':digest(row['subject_binding'])
                if row['subject_binding'] is not None else None,
            'observation_sequence':row['observation_sequence'],
            'ack_sequence':row['ack_sequence'],
            'ingest_status':row['ingest_status'],
            'qualification_status':row['qualification_status'],
            'question_contract':{'id':'facts.test_chain','response_kind':'fact',
                                 'relations':list(OWNER_RELATIONS)}}
    return {'store_id':STORE,'observation_refs':refs}


def fact_pair(*observations,overrides=None,owner_over=None,profile_over=None):
    rows=[projection(obs,sequence=i+1) for i,obs in enumerate(observations)]
    request=fact_request(**(overrides or {}))
    profile=fact_profile_result(rows,**(profile_over or {}))
    owner=fact_owner(rows)
    owner.update(owner_over or {})
    return request,profile,owner,READ_AT


def strict_pair(**kw):
    return fact_pair(fact_observation(),
                     overrides=dict(mode='strict',direction='outgoing'),**kw)


def build(request,profile,owner,read_at=READ_AT):
    return fc.build_response(profile_result=profile,request=request,owner=owner,
        read_at=read_at)


def validate(request,response,owner):
    return fc.validate_response(response,request=request,owner=owner)


# ---------------------------------------------------------------- schema edge

@pytest.mark.parametrize('mutation',[
    ('schema_version','2.6.0'),('operation','search'),
    ('requested_at','2026-10-09'),])
def test_request_rejects_wrong_wire_fields(mutation):
    request,profile,owner,_=fact_pair(fact_observation())
    request[mutation[0]]=mutation[1]
    with pytest.raises(ValueError,match='facts_'):
        fc.validate_request(request)


def test_request_rejects_missing_and_extra_payload_fields():
    request,_,_,_=fact_pair(fact_observation())
    missing=copy.deepcopy(request);missing['payload'].pop('direction')
    with pytest.raises(ValueError,match='facts_document_invalid'):
        fc.validate_request(missing)
    extra=copy.deepcopy(request);extra['payload']['languages']=[]
    with pytest.raises(ValueError,match='facts_document_invalid'):
        fc.validate_request(extra)


def test_envelope_rejects_wrong_message_type_and_unknown_document():
    request,_,_,_=fact_pair(fact_observation())
    with pytest.raises(ValueError,match='facts_document_invalid'):
        fc.validate_request(dict(request,message_type='response'))
    with pytest.raises(ValueError,match='facts_document_invalid'):
        fc.validate_envelope({'unrelated':'document'})


def test_response_position_rejects_request_shaped_document():
    request,profile,owner,_=fact_pair(fact_observation())
    with pytest.raises(ValueError,match='facts_message_type_invalid'):
        validate(request,request,owner)


@pytest.mark.parametrize('payload,error',[
    (dict(mode='strict',direction=None),'facts_direction_required_in_strict'),
    (dict(mode='strict',direction='outgoing',evidence='any'),
     'facts_evidence_any_invalid_in_strict'),
    (dict(period={'start':'2026-06-01','end':'2026-01-01'}),'facts_period_reversed'),
    (dict(information_cutoff='2026-10-10'),'facts_future_information_cutoff'),
    (dict(page={'page_size':10,'cursor':'tok.abc'}),'facts_cursor_requires_snapshot'),
])
def test_request_semantic_rejections(payload,error):
    request,_,_,_=fact_pair(fact_observation())
    request['payload'].update(payload)
    with pytest.raises(ValueError,match=error):
        fc.validate_request(request)


def test_export_request_requires_label():
    request,profile,owner,_=fact_pair(fact_observation(),
                                      overrides=dict(operation='export_facts'))
    with pytest.raises(ValueError,match='facts_export_label_required'):
        fc.validate_request(request)
    request['label']='synthetic export'
    fc.validate_request(request)


# ------------------------------------------------------------------ hash rules

def test_query_hash_stable_across_presentation_parameters():
    base,_,_,_=fact_pair(fact_observation())
    variants=[fact_pair(fact_observation(),overrides=dict(page={'page_size':50,'cursor':None}))[0],
              fact_pair(fact_observation(),overrides=dict(snapshot_id='fsnap1_'+'a'*64))[0],
              fact_pair(fact_observation(),overrides=dict(label='page two'))[0],
              fact_pair(fact_observation(),overrides=dict(requested_at='2026-10-09T23:30:00Z'))[0],
              fact_pair(fact_observation(),overrides=dict(information_cutoff=None))[0]]
    assert {fc.query_sha256(request) for request in variants}=={fc.query_sha256(base)}


def test_query_hash_binds_the_facts_wire_version():
    request27,_,_,_=fact_pair(fact_observation())
    request28=copy.deepcopy(request27)
    request28['schema_version']='2.8.0'
    assert fc.query_sha256(request27)!=fc.query_sha256(request28)


def test_query_hash_sensitive_to_real_selection_changes():
    base,_,_,_=fact_pair(fact_observation())
    deltas=[dict(mode='strict',direction='outgoing'),
            dict(entity_ids=[SUBJECT['entity_id'],'ENT_OTHER']),
            dict(information_cutoff='2026-10-05'),dict(relation_types=['sells_to']),
            dict(direction='outgoing'),dict(commercial_stages=['commercial']),
            dict(markets=['US']),dict(segment_ids=['SEG_1']),
            dict(evidence='any'),dict(counterparty={'text':'counter'}),
            dict(quality_conditions={'leaves':[{'field':'evidence_count','op':'>=',
                'value':1}],'combine':'all'}),
            dict(period={'as_of':'2026-09-30'})]
    for delta in deltas:
        other,_,_,_=fact_pair(fact_observation(),overrides=dict(delta))
        assert fc.query_sha256(other)!=fc.query_sha256(base),delta


def test_export_facts_request_shares_query_identity_with_query_facts():
    query,_,_,_=fact_pair(fact_observation())
    export,_,_,_=fact_pair(fact_observation(),overrides=dict(operation='export_facts',
                                                             label='synthetic export'))
    assert fc.query_sha256(export)==fc.query_sha256(query)


def test_information_cutoff_replay_binds_to_snapshot_identity():
    stored,_,_,_=fact_pair(fact_observation())
    replay,_,_,_=fact_pair(fact_observation(),
                           overrides=dict(information_cutoff=None,
                                          requested_at='2026-10-15T08:00:00Z'))
    materialized=fc.materialize(replay,information_cutoff='2026-10-09')
    assert fc.query_sha256(materialized)==fc.query_sha256(stored)


# --------------------------------------------------------------- build & states

def test_strict_candidate_and_explore_rows_stay_distinct():
    obs=fact_observation(stage='unknown')  # candidate-only: unknown stage
    request,profile,owner,_=fact_pair(obs)
    result=build(request,profile,owner)['result']
    # explore keeps the candidate with its real status_detail, never upgrades it
    assert result['status']=='ok' and result['total']==1
    assert result['candidate_total']==1
    row=result['facts'][0]
    assert row['qualification']=='candidate'
    assert row['status_detail']=='unknown_commercial_stage'
    assert result['coverage']['empty_reason'] is None
    assert result['coverage']['fact_relation_available'] is True
    strict,_,_,_=fact_pair(obs,overrides=dict(mode='strict',direction='outgoing'))
    strict_result=build(strict,profile,owner)['result']
    assert strict_result['status']=='empty' and strict_result['total']==0
    assert strict_result['candidate_total']==1
    assert strict_result['coverage']['status']=='partial'
    assert strict_result['coverage']['empty_reason']=='no_fact_match'
    assert strict_result['facts'][0]['status_detail']=='unknown_commercial_stage'


def test_strict_happy_path_resolves_direction_and_gates():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    result=response['result']
    assert response['schema_version']=='2.7.0'
    assert result['protocol']=='stockwiki.c06_facts_query/1.0.0'
    assert result['status']=='ok' and result['total']==1
    row=result['facts'][0]
    assert row['qualification']=='strict' and row['status_detail']=='strict'
    assert row['direction']=='outgoing'
    assert row['direction_convention_version']==fc.DIRECTION_CONVENTION_VERSION
    assert row['period_qualification']=='active_at_as_of'
    assert row['subject_ref']['entity_id']==SUBJECT['entity_id']
    assert row['matched_listings']==[{'market':'US','ticker':'SYN','listing_id':'L1'}]
    assert result['coverage']['status']=='complete'
    assert result['coverage']['inference_policy']=='no_cross_fact_join'
    assert result['coverage']['market_wide_claim'] is False
    assert result['watermark']['snapshot_id'].startswith('fsnap1_')
    assert result['watermark']['information_cutoff']=='2026-10-09'
    assert result['export'] is None
    validate(request,response,owner)


def test_score_only_profile_is_coverage_gap_never_empty():
    request,profile,owner,_=fact_pair(score_observation(),
                                      overrides=dict(field_ids=['facts.test_chain','IQS_01']))
    response=build(request,profile,owner)
    result=response['result']
    assert result['status']=='coverage_gap'
    assert result['coverage']['status']=='not_covered'
    assert result['coverage']['empty_reason']=='no_bound_fact_observations'
    assert result['coverage']['fact_relation_available'] is False
    assert result['facts']==[]


def test_missing_subject_is_partial_with_subject_unavailable_reason():
    request,profile,owner,_=fact_pair(fact_observation(),
        profile_over=dict(missing=[{'entity_id':'ENT_77777777-7777-4777-8777-777777777777',
            'scope':'entity','scope_id':'ENT_77777777-7777-4777-8777-777777777777',
            'security_id':None,'listing_id':None,'segment_id':None}]))
    request['payload']['entity_ids'].append('ENT_77777777-7777-4777-8777-777777777777')
    response=build(request,profile,owner)
    result=response['result']
    assert result['status']=='partial'
    assert result['coverage']['status']=='partial'
    assert 'subject_unavailable' in result['coverage']['reason_codes']
    assert result['missing_subject_ids']==['ENT_77777777-7777-4777-8777-777777777777']


def test_v28_listing_missing_scope_does_not_collide_with_entity_profile():
    """An unresolved listing remains distinct from a valid issuer-level profile."""
    request,profile,owner,read_at=fact_pair(fact_observation(),
        overrides={'schema_version':'2.8.0'})
    listing={'entity_id':SUBJECT['entity_id'],'scope':'listing',
        'scope_id':'LST_UNRESOLVED_SYNTHETIC','security_id':None,
        'listing_id':'LST_UNRESOLVED_SYNTHETIC','segment_id':None}
    profile['missing_subject_refs']=[listing]

    response=build(request,profile,owner,read_at)

    assert response['schema_version']=='2.8.0'
    assert response['result']['status']=='partial'
    assert response['result']['coverage']['status']=='partial'
    assert response['result']['missing_subject_ids']==[SUBJECT['entity_id']]
    assert response['result']['missing_subject_refs']==[listing]
    assert fc.validate_response(response,request=request,owner=owner)==response


def test_v28_rejects_missing_listing_outside_the_requested_listing_filter():
    request,profile,owner,read_at=fact_pair(fact_observation(),
        overrides={'schema_version':'2.8.0'})
    request['payload']['listing_ids']=['LST_SELECTED']
    profile['missing_subject_refs']=[{'entity_id':SUBJECT['entity_id'],'scope':'listing',
        'scope_id':'LST_NOT_SELECTED','security_id':None,
        'listing_id':'LST_NOT_SELECTED','segment_id':None}]
    with pytest.raises(ValueError,match='facts_unrequested_subject'):
        build(request,profile,owner,read_at)


def test_v28_rejects_a_listing_reported_both_present_and_missing():
    request,profile,owner,read_at=fact_pair(fact_observation(),
        overrides={'schema_version':'2.8.0'})
    listing_id='LST_CONTRADICTORY'
    security=copy.deepcopy(SUBJECT)
    security.update(scope='security',scope_id='SEC_SYNTHETIC',
        security_id='SEC_SYNTHETIC',listing_id=listing_id,segment_id=None)
    profile['profiles'][0]['subject_ref']=security
    profile['profiles'][0]['observations']=[]
    profile['missing_subject_refs']=[{'entity_id':SUBJECT['entity_id'],'scope':'listing',
        'scope_id':listing_id,'security_id':None,'listing_id':listing_id,'segment_id':None}]
    with pytest.raises(ValueError,match='facts_subject_coverage_mismatch'):
        build(request,profile,owner,read_at)


def test_v27_does_not_silently_accept_the_new_listing_missing_scope():
    request,profile,owner,read_at=fact_pair(fact_observation())
    profile['missing_subject_refs']=[{'entity_id':SUBJECT['entity_id'],
        'scope':'listing','scope_id':'LST_UNRESOLVED_SYNTHETIC',
        'security_id':None,'listing_id':'LST_UNRESOLVED_SYNTHETIC','segment_id':None}]
    with pytest.raises(ValueError,match='facts_subject_scope_invalid'):
        build(request,profile,owner,read_at)


def test_source_failure_is_unavailable_and_never_reads_as_no_facts():
    request,profile,owner,_=fact_pair(fact_observation(),
        profile_over=dict(marks=default_marks(failed='read_error')))
    response=build(request,profile,owner)
    result=response['result']
    assert result['status']=='unavailable'
    assert result['coverage']['status']=='unknown'
    assert result['coverage']['empty_reason']=='source_unavailable'
    assert 'observations_read_error' in result['coverage']['reason_codes']


def test_filters_drop_rows_but_keep_fact_relation_available():
    request,profile,owner,_=fact_pair(fact_observation(),
        overrides=dict(relation_types=['supplies']))
    response=build(request,profile,owner)
    result=response['result']
    assert result['status']=='empty' and result['facts']==[]
    assert result['coverage']['empty_reason']=='no_fact_match'
    # frozen semantics: fact_relation_available tracks the kept row set
    assert result['coverage']['fact_relation_available'] is False


def test_expired_period_is_candidate_in_explore_and_absent_in_strict():
    obs=fact_observation(valid_from='2025-01-01',valid_to='2026-01-31')
    request,profile,owner,_=fact_pair(obs)
    row=build(request,profile,owner)['result']['facts'][0]
    assert row['status_detail']=='expired' and row['period_qualification']=='expired'
    strict,_,_,_=fact_pair(obs,overrides=dict(mode='strict',direction='outgoing'))
    strict_result=build(strict,profile,owner)['result']
    assert strict_result['total']==0
    assert strict_result['facts'][0]['status_detail']=='expired'


def test_period_range_overlap_and_unknown_period_handling():
    obs=fact_observation(valid_to='2026-01-31')
    request,profile,owner,_=fact_pair(obs,
        overrides=dict(period={'start':'2025-06-01','end':'2026-06-01'}))
    row=build(request,profile,owner)['result']['facts'][0]
    assert row['period_qualification']=='overlaps_requested_period'
    unknown=fact_observation(valid_from=None,valid_to=None)
    request2,profile2,owner2,_=fact_pair(unknown)
    row2=build(request2,profile2,owner2)['result']['facts'][0]
    assert row2['period_qualification']=='period_unknown'
    assert row2['status_detail']=='period_unknown'
    not_started=fact_observation(valid_from='2026-11-01')
    request3,profile3,owner3,_=fact_pair(not_started)
    result3=build(request3,profile3,owner3)['result']
    assert result3['status']=='empty' and result3['facts']==[]


def test_unresolved_direction_never_enters_strict():
    obs=fact_observation(relation='partners_with',role='peer')
    request,profile,owner,_=fact_pair(obs)
    row=build(request,profile,owner)['result']['facts'][0]
    assert row['direction']=='unresolved'
    assert row['status_detail']=='unknown_direction'
    strict,_,_,_=fact_pair(obs,overrides=dict(mode='strict',direction='outgoing'))
    assert build(strict,profile,owner)['result']['total']==0


@pytest.mark.parametrize('qualification,detail',[
    ('rejected','qualification_rejected'),('conflict','qualification_conflict')])
def test_owner_qualification_rejection_is_preserved_not_silently_accepted(
        qualification,detail):
    obs=fact_observation()
    rows=[projection(obs,qualification=qualification)]
    profile=fact_profile_result(rows)
    owner=fact_owner(rows)
    request=fact_request()
    row=build(request,profile,owner)['result']['facts'][0]
    assert row['status_detail']==detail and row['qualification']=='candidate'


def test_unreviewed_evidence_keeps_row_out_of_strict():
    obs=fact_observation(review='unreviewed')
    request,profile,owner,_=fact_pair(obs)
    row=build(request,profile,owner)['result']['facts'][0]
    assert row['evidence_review_status']=='unreviewed'
    assert row['status_detail']=='evidence_unreviewed'


def test_legacy_unbound_fact_answer_is_refused_loudly():
    obs=fact_observation()
    row=projection(obs,bound=False)
    # an unbound answer cannot be a current profile row: the native seal
    # refuses it with the frozen wire's own code before projection
    profile=fact_profile_result([row])
    owner=fact_owner([row])
    request=fact_request()
    with pytest.raises(ValueError,match='facts_legacy_unbound_answer'):
        build(request,profile,owner)
    # in the legacy unbound history the row is simply not projected; the
    # store then reads as a coverage gap, never as asserted facts
    legacy=fact_profile_result()
    legacy['legacy_unbound_observations']=[row]
    legacy['watermark']['observation_sequence']=1
    result=build(request,legacy,owner)['result']
    assert result['status']=='coverage_gap'
    assert result['facts']==[]


# ------------------------------------------------------------ assertion marking

def test_newer_cutoff_supersedes_older_assertion():
    old=fact_observation(cutoff='2026-10-01')
    new=fact_observation()
    request,profile,owner,_=fact_pair(old,new)
    rows=build(request,profile,owner)['result']['facts']
    assert len(rows)==2
    by_seq={row['observation_sequence']:row['status_detail'] for row in rows}
    assert by_seq[1]=='superseded' and by_seq[2]=='strict'
    assert rows[0]['qualification']=='candidate'


def test_same_cutoff_divergent_claims_conflict_whole_group():
    a=fact_observation(stage='commercial')
    b=fact_observation(stage='pilot')
    request,profile,owner,_=fact_pair(a,b)
    rows=build(request,profile,owner)['result']['facts']
    assert [row['status_detail'] for row in rows]==[
        'assertion_conflict_pending_review']*2
    assert all(row['qualification']=='candidate' for row in rows)


# -------------------------------------------------------------------- quality

def test_quality_conditions_gate_rows_and_explanations_shape():
    passing=fact_observation(cp_name='CP Alpha Co',confidence='high')
    failing=fact_observation(cp_name='CP Beta Co',confidence='medium')
    conditions={'leaves':[{'field':'confidence_rank','op':'>=','value':3}],
                'combine':'all'}
    request,profile,owner,_=fact_pair(passing,failing,
        overrides=dict(quality_conditions=conditions))
    result=build(request,profile,owner)['result']
    assert result['total']==1
    row=result['facts'][0]
    assert row['quality_outcome']=='pass'
    assert row['quality_explanations']==[{'field':'confidence_rank','op':'>=',
        'threshold':3,'critical_risk_gate':False,'outcome':'pass','actual':3,
        'reason':'compared'}]
    # the failing row is dropped by the quality gate and never qualifies
    assert row['counterparty']['name']=='CP Alpha Co'


def test_quality_unknown_outcome_never_reads_as_pass():
    # A null quality value is unknown, not a pass and not a fail (unit level:
    # schema-valid fact answers always rank their confidence, so the null path
    # is defensive).
    row={'confidence_rank':None,'evidence_ids':['E1'],'observation_sequence':1}
    outcome,explanations=fc._quality_outcome(row,{'leaves':[
        {'field':'confidence_rank','op':'>=','value':1}],'combine':'all'})
    assert outcome=='unknown'
    assert explanations==[{'field':'confidence_rank','op':'>=','threshold':1,
        'critical_risk_gate':False,'outcome':'unknown','actual':None,
        'reason':'value_null'}]
    outcome2,_=fc._quality_outcome(row,None)
    assert outcome2=='not_requested'


def test_quality_any_combination_passes_on_single_passing_leaf():
    obs=fact_observation()
    conditions={'leaves':[{'field':'confidence_rank','op':'>=','value':2},
                          {'field':'evidence_count','op':'<','value':1}],
                'combine':'any'}
    request,profile,owner,_=fact_pair(obs,overrides=dict(quality_conditions=conditions))
    result=build(request,profile,owner)['result']
    assert result['total']==1
    row=result['facts'][0]
    assert row['quality_outcome']=='pass'
    assert [entry['outcome'] for entry in row['quality_explanations']]==['pass','fail']


# -------------------------------------------------------- reference integrity

def test_owner_observation_reference_is_required_and_binding_checked():
    obs=fact_observation()
    request,profile,owner,_=fact_pair()
    profile['profiles'][0]['observations']=[projection(obs)]
    with pytest.raises(ValueError,match='query_independent_observation_reference_required'):
        build(request,profile,owner)
    bad=dict(fact_owner([]))
    bad['observation_refs']={projection(obs)['observation_id']:
        dict(fact_owner([projection(obs)])['observation_refs'][projection(obs)['observation_id']],
             payload_sha256='0'*64)}
    with pytest.raises(ValueError,match='query_owner_observation_reference_mismatch'):
        build(request,profile,bad)


def test_unrequested_subject_reference_is_rejected():
    request,profile,owner,_=fact_pair(fact_observation())
    profile['profiles'][0]['subject_ref']=dict(SUBJECT,
        entity_id='ENT_88888888-8888-4888-8888-888888888888',
        scope_id='ENT_88888888-8888-4888-8888-888888888888')
    with pytest.raises(ValueError,match='facts_unrequested_subject'):
        build(request,profile,owner)


def test_duplicate_subject_scope_is_rejected():
    request,profile,owner,_=fact_pair(fact_observation())
    other=dict(copy.deepcopy(profile['profiles'][0]),
               canonical_name='Synthetic C06 Two')
    profile['profiles'].append(other)
    with pytest.raises(ValueError,match='query_duplicate_subject_scope'):
        build(request,profile,owner)


def test_forged_observation_identity_is_rejected():
    obs=fact_observation()
    row=projection(obs)
    row['payload_sha256']='0'*64
    request,profile,owner,_=fact_pair()
    profile['profiles'][0]['observations']=[row]
    owner=fact_owner([row])
    with pytest.raises(ValueError,match='query_original_observation_invalid'):
        build(request,profile,owner)


def test_profile_watermark_and_source_marks_are_verified():
    request,profile,owner,_=fact_pair(fact_observation())
    profile['watermark']['store_id']='STORE_FOREIGN'
    with pytest.raises(ValueError,match='facts_profile_watermark_invalid'):
        build(request,profile,owner)
    _,profile2,owner2,_=fact_pair(fact_observation())
    profile2['watermark']['source_watermarks']=[
        {'namespace':'observations','schema_version':3,'status':'available',
         'sequence':0,'read_at':READ_AT,'content_sha256':'3'*64}]
    with pytest.raises(ValueError,match='facts_profile_source_watermarks_invalid'):
        build(request,profile2,owner2)
    _,profile3,owner3,_=fact_pair(fact_observation())
    profile3['watermark']['source_watermarks'][0]['status']='read_error'
    profile3['watermark']['source_watermarks'][0]['content_sha256']='3'*64
    with pytest.raises(ValueError,match='facts_profile_source_watermarks_invalid'):
        build(request,profile3,owner3)


def test_classification_gap_is_reported_not_hidden():
    request,profile,owner,_=fact_pair(fact_observation(),
        profile_over=dict(classification_gap=True))
    result=build(request,profile,owner)['result']
    assert 'identity_market_unmapped' in result['coverage']['reason_codes']


# ------------------------------------------------------------------ pagination

def three_counterparty_pair():
    rows=[projection(fact_observation(cp_name=name,canonical=canonical),sequence=i+1)
          for i,(name,canonical) in enumerate([('CP Alpha Co','ENT_CP_0001'),
                                               ('CP Beta Co','ENT_CP_0002'),
                                               ('CP Gamma Co','ENT_CP_0003')])]
    request=fact_request()
    profile=fact_profile_result(rows,sequence=3)
    owner=fact_owner(rows)
    return request,profile,owner


def test_paging_slices_without_refiltering_and_binds_cursor():
    request,profile,owner=three_counterparty_pair()
    request['payload']['page']={'page_size':2,'cursor':None}
    result=build(request,profile,owner)['result']
    # the sealed FULL result carries every row; paging is presentation only
    assert result['total']==3 and len(result['facts'])==3
    assert result['page_facts']==[] and result['next_cursor'] is None
    presented=fc.present_result(result,request['payload'])
    assert presented['total']==3 and len(presented['page_facts'])==2
    assert presented['facts']==[] and presented['next_cursor']
    second=dict(request['payload'],page={'page_size':2,
        'cursor':presented['next_cursor']})
    page2=fc.present_result(result,second)
    assert len(page2['page_facts'])==1 and page2['next_cursor'] is None
    names={row['counterparty']['name'] for row in presented['page_facts']+page2['page_facts']}
    assert names=={'CP Alpha Co','CP Beta Co','CP Gamma Co'}


def test_cursor_rejects_cross_query_cross_snapshot_and_bad_offset():
    request,profile,owner=three_counterparty_pair()
    result=build(request,profile,owner)['result']
    payload=dict(request['payload'],page={'page_size':2,'cursor':None})
    first=fc.present_result(result,payload)
    good=fc.present_result(result,dict(payload,page={'page_size':2,
        'cursor':first['next_cursor']}))
    assert good['page_facts']
    # cross-query: same cursor against a different query identity
    other_rows=[projection(fact_observation(cp_name='CP Alpha Co'))]
    other=fact_request(relation_types=['sells_to'])
    other_result=build(other,fact_profile_result(other_rows),
                       fact_owner(other_rows))['result']
    with pytest.raises(ValueError,match='facts_cursor_invalid'):
        fc.present_result(other_result,dict(payload,page={'page_size':2,
            'cursor':first['next_cursor']}))
    # cross-snapshot: cursor bound to another snapshot id
    with pytest.raises(ValueError,match='facts_cursor_invalid'):
        fc._offset(first['next_cursor'],query_hash=result['query_sha256'],
            snapshot_id='fsnap1_'+'b'*64,page_size=2,total=3)
    # offsets must align with the page size and stay inside the result
    token,_,_=first['next_cursor'].partition('.')
    import base64 as b64
    value={'offset':1,'query_sha256':result['query_sha256'],
           'snapshot_id':result['watermark']['snapshot_id']}
    raw=b64.urlsafe_b64encode(json.dumps(value,sort_keys=True,separators=(',',':'),
        ensure_ascii=False).encode()).decode().rstrip('=')
    forged=raw+'.'+digest(value)
    with pytest.raises(ValueError,match='facts_cursor_invalid'):
        fc.present_result(result,dict(payload,page={'page_size':2,'cursor':forged}))


def test_strict_paging_counts_only_strict_rows():
    request,profile,owner=three_counterparty_pair()
    request['payload']['mode']='strict'
    request['payload']['direction']='outgoing'
    request['payload']['page']={'page_size':2,'cursor':None}
    result=build(request,profile,owner)['result']
    assert result['total']==3 and result['candidate_total']==0
    assert result['page_facts']==[]
    presented=fc.present_result(result,request['payload'])
    assert presented['total']==3 and len(presented['page_facts'])==2
    assert presented['next_cursor'] is not None


def test_default_page_size_and_bounds():
    request,profile,owner=three_counterparty_pair()
    result=build(request,profile,owner)['result']
    presented=fc.present_result(result,request['payload'])
    assert presented['total']==3 and len(presented['page_facts'])==3
    with pytest.raises(ValueError,match='facts_page_size_invalid'):
        fc.present_result(result,dict(request['payload'],
            page={'page_size':101,'cursor':None}))


# --------------------------------------------------------------------- export

def public_export_response(request,profile,owner,read_at):
    """Mirror the frozen owner presenter using only a synthetic response."""
    internal=fc.build_response(profile_result=profile,request=request,
        owner=owner,read_at=read_at)
    body=fc.build_export_body(internal['result'],request,generated_at=read_at)
    result=copy.deepcopy(internal['result'])
    result['operation']='export_facts'
    result['facts']=[]
    result['page_facts']=[]
    result['total']=len(body['candidates'])
    result['next_cursor']=None
    result['export']=body
    return dict(message_type='response',schema_version='2.7.0',
        request_id=request['request_id'],operation='export_facts',
        response_at=read_at,result=result)


def reseal_export_body(body):
    content={k:v for k,v in body.items()
        if k not in {'dataset_sha256','candidate_set_id'}}
    digest_value=digest(content)
    body['dataset_sha256']=digest_value
    body['candidate_set_id']='fexp1_'+digest_value
    return body

def test_export_body_verifies_and_binds_to_query():
    request,profile,owner,_=fact_pair(fact_observation(),
        overrides=dict(operation='export_facts',label='synthetic export'))
    response=build(request,profile,owner)
    result=response['result']
    assert result['operation']=='export_facts'
    body=fc.build_export_body(result,request,generated_at=READ_AT)
    assert body['protocol']=='stockwiki.c06_facts_export/1.0.0'
    assert body['candidate_set_id']=='fexp1_'+body['dataset_sha256']
    assert body['query_sha256']==result['query_sha256']
    assert body['information_cutoff']=='2026-10-09'
    assert body['query']==fc.normalize_payload(request)
    assert [row['fact_id'] for row in body['candidates']]==[
        row['fact_id'] for row in result['facts']]
    public=public_export_response(request,profile,owner,READ_AT)
    verified=fc.verify_export(body,response=public,request=request,owner=owner)
    assert verified['verified'] is True
    tampered=copy.deepcopy(body);tampered['candidates']=[]
    with pytest.raises(ValueError,match='facts_export_hash_mismatch'):
        fc.verify_export(tampered,response=public,request=request,owner=owner)
    retyped=copy.deepcopy(body);retyped['protocol']='other.protocol/1.0.0'
    with pytest.raises(ValueError,match='facts_export_shape'):
        fc.verify_export(retyped,response=public,request=request,owner=owner)


def test_public_export_response_binds_candidates_query_snapshot_and_owner():
    request,profile,owner,_=fact_pair(fact_observation(),
        overrides=dict(operation='export_facts',label='synthetic export'))
    public=public_export_response(request,profile,owner,READ_AT)
    assert fc.validate_export_response(response=public,request=request,
                                       owner=owner)==public

    # A self-consistent hash is not proof that these are the owner's rows.
    changed=copy.deepcopy(public)
    changed['result']['export']['candidates']=[]
    reseal_export_body(changed['result']['export'])
    with pytest.raises(ValueError,match='facts_export_binding_mismatch'):
        fc.validate_export_response(response=changed,request=request,owner=owner)

    # The exported label and snapshot must agree with the original request and
    # the sealed query result, even though the dataset hash is recomputed.
    changed=copy.deepcopy(public)
    changed['result']['export']['label']='different export label'
    reseal_export_body(changed['result']['export'])
    with pytest.raises(ValueError,match='facts_export_binding_mismatch'):
        fc.validate_export_response(response=changed,request=request,owner=owner)

    changed=copy.deepcopy(public)
    changed['result']['export']['query']['field_ids']=['facts.different_query']
    changed['result']['export']['query_sha256']='0'*64
    reseal_export_body(changed['result']['export'])
    with pytest.raises(ValueError,match='facts_export_binding_mismatch'):
        fc.validate_export_response(response=changed,request=request,owner=owner)

    changed=copy.deepcopy(public)
    changed['result']['watermark']['snapshot_id']='fsnap1_'+'0'*64
    changed['result']['export']['watermark']['snapshot_id']='fsnap1_'+'0'*64
    reseal_export_body(changed['result']['export'])
    with pytest.raises(ValueError,match='facts_export_binding_mismatch'):
        fc.validate_export_response(response=changed,request=request,owner=owner)

    other_owner=copy.deepcopy(owner)
    other_owner['store_id']='STORE_OTHER_SYNTHETIC'
    with pytest.raises(ValueError):
        fc.validate_export_response(response=public,request=request,owner=other_owner)


def test_public_export_snapshot_replay_reuses_stored_cutoff_across_days():
    request,profile,owner,_=fact_pair(fact_observation(),
        overrides=dict(operation='export_facts',label='synthetic export'))
    original=public_export_response(request,profile,owner,READ_AT)
    replay=copy.deepcopy(request)
    replay['request_id']='REQ_CROSS_DAY_EXPORT_REPLAY'
    replay['requested_at']='2026-10-15T08:00:00Z'
    replay['payload']['information_cutoff']=None
    replay['payload']['snapshot_id']=original['result']['watermark']['snapshot_id']
    effective=fc.materialize(replay,
        information_cutoff=original['result']['watermark']['information_cutoff'])
    presented=public_export_response(effective,profile,owner,READ_AT)
    presented['response_at']='2026-10-15T08:01:00Z'

    assert presented['result']['watermark']['snapshot_id']==replay['payload']['snapshot_id']
    assert fc.validate_export_response(response=presented,request=replay,
                                       owner=owner)==presented

    # Changing the echoed cutoff and every related self-hash still cannot
    # reuse the original snapshot ID for a different logical query.
    changed=copy.deepcopy(presented)
    wrong_cutoff='2026-10-10'
    changed_request=fc.materialize(replay,information_cutoff=wrong_cutoff)
    wrong_hash=fc.query_sha256(changed_request)
    changed['result']['query_sha256']=wrong_hash
    changed['result']['watermark']['query_sha256']=wrong_hash
    changed['result']['watermark']['information_cutoff']=wrong_cutoff
    changed_export=changed['result']['export']
    changed_export['query']=fc.normalize_payload(changed_request)
    changed_export['query_sha256']=wrong_hash
    changed_export['information_cutoff']=wrong_cutoff
    changed_export['watermark']['query_sha256']=wrong_hash
    changed_export['watermark']['information_cutoff']=wrong_cutoff
    reseal_export_body(changed_export)
    with pytest.raises(ValueError):
        fc.validate_export_response(response=changed,request=replay,owner=owner)


def test_strict_export_keeps_only_strict_candidates():
    rows=[projection(fact_observation(cp_name='CP Alpha Co',canonical='ENT_CP_0001')),
          projection(fact_observation(cp_name='CP Beta Co',canonical='ENT_CP_0002',
                                      stage='unknown'))]
    request=fact_request(mode='strict',direction='outgoing',
                         operation='export_facts',label='synthetic export')
    profile=fact_profile_result(rows,sequence=2)
    owner=fact_owner(rows)
    result=build(request,profile,owner)['result']
    body=fc.build_export_body(result,request,generated_at=READ_AT)
    assert len(body['candidates'])==1
    assert body['candidates'][0]['qualification']=='strict'
    assert body['candidate_entity_ids']==[SUBJECT['entity_id']]


def test_response_snapshot_replay_accepts_either_operation():
    obs=fact_observation()
    request,profile,owner,_=fact_pair(obs)
    response=build(request,profile,owner)
    snapshot=response['result']['watermark']['snapshot_id']
    # a replay presents the stored sealed result under the replaying request's
    # envelope (the owner capture path), keeping the stored result unchanged
    replay=fact_request(snapshot_id=snapshot,requested_at='2026-10-15T08:00:00Z',
                        information_cutoff=None)
    envelope=dict(message_type='response',schema_version='2.7.0',
        request_id=replay['request_id'],operation=replay['operation'],
        response_at='2026-10-15T08:01:00Z',
        result=copy.deepcopy(response['result']))
    validate(replay,envelope,owner)
    export_replay=dict(replay,operation='export_facts',label='synthetic export')
    export_envelope=dict(envelope,operation='export_facts')
    validate(export_replay,export_envelope,owner)
    wrong=fact_request(snapshot_id='fsnap1_'+'e'*64)
    with pytest.raises(ValueError,match='facts_snapshot_id_mismatch'):
        validate(wrong,envelope,owner)


def test_tampered_projection_is_rejected():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    tampered=copy.deepcopy(response)
    tampered['result']['facts'][0]['commercial_stage']='pilot'
    # re-seal the tampered content so the snapshot check passes and the
    # projection rebuild itself is what rejects the mutation
    resealed=fc.seal_response({'message_type':tampered['message_type'],
        'schema_version':tampered['schema_version'],
        'request_id':tampered['request_id'],'operation':tampered['operation'],
        'response_at':tampered['response_at'],
        'result':tampered['result']},request=request)
    with pytest.raises(ValueError,match='facts_projection_mismatch'):
        validate(request,resealed,owner)
    raw=copy.deepcopy(response)
    raw['result']['facts'][0]['commercial_stage']='pilot'
    with pytest.raises(ValueError,match='facts_snapshot_content_mismatch'):
        validate(request,raw,owner)


def test_owner_store_and_request_binding_are_enforced():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    # a foreign independent owner is rejected (profile watermark store fires first)
    foreign=dict(owner,store_id='STORE_OTHER')
    with pytest.raises(ValueError):
        validate(request,response,foreign)
    with pytest.raises(ValueError,match='facts_request_binding_mismatch'):
        validate(dict(request,request_id='REQ_OTHER'),response,owner)
    early=dict(response,response_at='2026-10-09T20:30:00Z')
    with pytest.raises(ValueError,match='facts_response_before_read'):
        validate(request,early,owner)


def test_seal_recomputation_rejects_snapshot_edits():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    tampered=copy.deepcopy(response)
    tampered['result']['watermark']['observation_sequence']=99
    with pytest.raises(ValueError,match='facts_snapshot_content_mismatch'):
        validate(request,tampered,owner)


def test_model_filter_rejects_mismatched_original():
    obs=fact_observation()
    request=fact_request(model_filter={'provider':'synthetic-provider',
                                       'model_resolved':'other-model'})
    rows=[projection(obs)]
    profile=fact_profile_result(rows)
    owner=fact_owner(rows)
    with pytest.raises(ValueError,match='query_original_model_filter_mismatch'):
        build(request,profile,owner)


def test_unrequested_field_in_original_is_rejected():
    obs=fact_observation()
    request=fact_request(field_ids=['facts.other_field'])
    rows=[projection(obs)]
    profile=fact_profile_result(rows)
    owner=fact_owner(rows)
    with pytest.raises(ValueError,match='query_unrequested_observation_field'):
        build(request,profile,owner)


def test_validate_response_requires_schema_valid_response():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    bad=copy.deepcopy(response);bad['result'].pop('coverage')
    with pytest.raises(ValueError,match='facts_document_invalid'):
        validate(request,bad,owner)


def test_owner_shape_is_enforced():
    request,profile,owner,_=strict_pair()
    response=build(request,profile,owner)
    with pytest.raises(ValueError,match='facts_independent_owner_required'):
        validate(request,response,{'store_id':STORE})
    with pytest.raises(ValueError,match='facts_independent_owner_required'):
        validate(request,response,dict(owner,store_id='  '))
