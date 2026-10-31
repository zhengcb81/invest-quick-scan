"""Native row binding and honest TIME shadow; all data here are synthetic."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
# Explicit test-only dependency, matching the original owner's sibling fixture.
# Production workers still use only the configured native StockWiki path.
sys.path.insert(0,str(ROOT.parent/'StockWiki'))
import dashboard_temporal as temporal

NOW='2026-10-31T12:00:00Z'
ENTITY='ENT_SYNTHETIC_TIME'


def specimen():
    policies,bindings=temporal._policies()
    qid='IQS_01';binding=bindings[qid]
    payload={'observation_id':'OBS_TIME_SYNTHETIC','entity_id':ENTITY,'identity_revision':1,
      'field_id':policies[qid]['field_id'],'question_id':qid,'scope':'entity',
      'question_version':'1.0.0','question_semantic_sha256':'a'*64,
      'question_definition_sha256':binding['definition_sha256'],
      'module_package_id':'synthetic_package','module_release_id':binding['module_release_id'],
      'template_version':'1.0.0','observed_at':'2026-10-31T11:00:00Z',
      'information_cutoff':'2026-10-31','execution':{'provider':'synthetic','model_resolved':'synthetic'},
      'answer':{'status':'scored','score':7,'information_as_of':'2026-10-30',
                'evidence':[{'url':'https://example.invalid/','published_at':'2026-10-30'}]}}
    raw={k:deepcopy(v) for k,v in payload.items() if k in ['observation_id','entity_id','identity_revision','field_id','question_id','scope','observed_at','information_cutoff']}
    raw.update(payload=payload,payload_sha256=temporal._sha(payload))
    row={k:deepcopy(v) for k,v in raw.items() if k!='payload'};row.pop('entity_id')
    detail={'entity':{'entity_id':ENTITY},'groups':[{'fields':[row]}]}
    return detail,raw


def view(detail,raw):
    return temporal.build_entity_view(detail,lambda oid:raw,entity_id=ENTITY,now_utc=NOW)


def result(detail,raw):
    return view(detail,raw)['temporal_shadow']['records'][0]


def test_pure_shadow_calls_real_engine_without_mutation_or_current_context_claim():
    detail,raw=specimen();before=deepcopy((detail,raw));paths=list(sys.path)
    actual=view(detail,raw);record=actual['temporal_shadow']['records'][0]
    assert actual['entity'] is detail
    assert (detail,raw)==before and sys.path==paths
    assert record['knowledge_kind']=='structural'
    assert record['decision']=='not_assessable' and record['reuse_authorized'] is False
    assert record['current_context_verified'] is False
    saved=record['captured_context_assessment']
    assert 'verification_missing' in saved['reason_codes']
    assert saved['actual_source_dates']['verified_at'] is None
    assert saved['legacy_equivalent']['authoritative'] is False


@pytest.mark.parametrize('target',['payload','projection'])
def test_hash_drift_is_named_and_never_assessed(target):
    detail,raw=specimen()
    if target=='payload':raw['payload']['answer']['score']=10
    else:detail['groups'][0]['fields'][0]['payload_sha256']='f'*64
    assert 'hash_mismatch' in result(detail,raw)['reason_codes'][0]
    assert 'captured_context_assessment' not in result(detail,raw)


@pytest.mark.parametrize('key,value',[('question_id','OTHER'),('field_id','score.other'),('scope','security'),('security_id','SEC_OTHER')])
def test_projection_or_scope_drift_refused(key,value):
    detail,raw=specimen();detail['groups'][0]['fields'][0][key]=value
    assert 'binding_mismatch' in result(detail,raw)['reason_codes'][0]


@pytest.mark.parametrize('key',['observed_at','information_cutoff'])
def test_projection_clock_cannot_disagree_with_native_payload(key):
    detail,raw=specimen();detail['groups'][0]['fields'][0][key]='2026-01-01'
    assert result(detail,raw)['reason_codes']==['native_clock_binding_mismatch']


@pytest.mark.parametrize('key,value',[('question_definition_sha256','f'*64),('module_release_id','modrel_future')])
def test_catalog_cannot_attach_to_new_meaning_or_release(key,value):
    detail,raw=specimen();raw['payload'][key]=value;raw['payload_sha256']=temporal._sha(raw['payload'])
    detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    assert result(detail,raw)['reason_codes']==['time_policy_definition_unbound']


@pytest.mark.parametrize('child',[None,'ENT_FOREIGN',17])
def test_explicit_unknown_or_foreign_child_never_inherits(child):
    detail,raw=specimen();detail['groups'][0]['fields'][0]['entity_id']=child
    assert result(detail,raw)['reason_codes']==['child_identity_unknown_or_foreign']


def test_missing_or_foreign_parent_does_not_read_native_store():
    for parent in [{},{'entity_id':'ENT_FOREIGN'}]:
        detail,_=specimen();detail['entity']=parent
        def forbidden(oid):raise AssertionError('must not read cross-entity observations')
        actual=temporal.build_entity_view(detail,forbidden,entity_id=ENTITY,now_utc=NOW)
        assert not actual['temporal_shadow']['records']


def test_model_self_verification_never_becomes_receipt():
    detail,raw=specimen();raw['payload']['verified_at']=NOW
    raw['payload']['evidence_review_status']='formal_research_accepted'
    raw['payload_sha256']=temporal._sha(raw['payload']);detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    actual=result(detail,raw)
    assert not actual['verification_receipt_available']
    assert actual['captured_context_assessment']['actual_source_dates']['verified_at'] is None


def test_unbound_legacy_and_unknown_question_remain_readable():
    detail,raw=specimen();raw['payload'].pop('question_definition_sha256')
    raw['payload_sha256']=temporal._sha(raw['payload']);detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    actual=view(detail,raw)
    assert actual['entity'] is detail
    assert actual['temporal_shadow']['records'][0]['decision']=='not_assessable'


@pytest.mark.parametrize('revision',[None,'legacy'])
def test_absent_native_revision_can_explain_clocks_but_never_create_identity_context(revision):
    detail,raw=specimen();raw['identity_revision']=revision;raw['payload'].pop('identity_revision')
    raw['payload_sha256']=temporal._sha(raw['payload']);detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    before=deepcopy(raw);actual=result(detail,raw)
    assert actual['knowledge_kind']=='structural'
    assert actual['decision']=='not_assessable' and not actual['current_context_verified']
    assert 'captured_context_assessment' not in actual
    clocks=actual['clock_only_assessment']
    assert clocks['context_assessed'] is False and clocks['reuse_authorized'] is False
    assert clocks['actual_source_dates']['verified_at'] is None
    assert [r['clock'] for r in clocks['clock_assessments']]==['fact_valid_clock','verification_clock']
    assert clocks['clock_assessments'][1]['status']=='missing'
    assert raw==before


@pytest.mark.parametrize('info,cutoff,code',[('2027-01-01','2027-01-01','information_date_in_future'),
    ('2026-10-30','2026-10-29','information_after_cutoff')])
def test_clock_only_path_preserves_global_information_constraints(info,cutoff,code):
    detail,raw=specimen();raw['identity_revision']=None;raw['payload'].pop('identity_revision')
    raw['payload']['answer']['information_as_of']=info;raw['payload']['information_cutoff']=cutoff;raw['information_cutoff']=cutoff
    raw['payload_sha256']=temporal._sha(raw['payload']);row=detail['groups'][0]['fields'][0]
    row.update(payload_sha256=raw['payload_sha256'],information_cutoff=cutoff)
    actual=result(detail,raw)
    assert code in actual['reason_codes'] and 'clock_only_assessment' not in actual
    assert not actual['reuse_authorized']


def test_clock_only_path_keeps_unknown_publication_explicit_even_for_structural_question():
    detail,raw=specimen();raw['identity_revision']=None;raw['payload'].pop('identity_revision')
    raw['payload']['answer']['evidence'][0].pop('published_at');raw['payload_sha256']=temporal._sha(raw['payload'])
    detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    actual=result(detail,raw)
    assert actual['clock_only_assessment']['source_constraints']['status']=='not_assessable'
    assert 'publication_unknown' in actual['reason_codes']


@pytest.mark.parametrize('event,code',[('2026-10-30T12:00:00Z','event_invalidated'),('not-a-date','event_invalidated_at_invalid'),('2026-11-01T12:00:00Z',None)])
def test_clock_only_path_keeps_event_invalidation_and_bad_event_explicit(event,code):
    detail,raw=specimen();raw['identity_revision']=None;raw['payload'].pop('identity_revision')
    raw['payload']['event_invalidated_at']=event;raw['payload_sha256']=temporal._sha(raw['payload'])
    detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256'];actual=result(detail,raw)
    if code:assert code in actual['reason_codes']
    if code!='event_invalidated_at_invalid':
        assert actual['clock_only_assessment']['actual_source_dates']['event_invalidated_at']==event
        if code is None:assert actual['clock_only_assessment']['source_constraints']['event_status']=='scheduled'
    assert actual['reuse_authorized'] is False


@pytest.mark.parametrize('groups',[None,[{'fields':None}],[None]])
def test_malformed_legacy_groups_keep_original_detail(groups):
    detail,raw=specimen();detail['groups']=groups;actual=view(detail,raw)
    assert actual['entity'] is detail
    assert actual['temporal_shadow']['reason_codes']
    assert actual['temporal_shadow']['records']==[]


def test_malformed_legacy_execution_is_unknown_not_whole_company_failure():
    detail,raw=specimen();raw['payload']['execution']='legacy-unknown'
    raw['payload_sha256']=temporal._sha(raw['payload']);detail['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
    assert result(detail,raw)['reason_codes']==['native_execution_unreadable']


def test_native_subprocess_view_is_readonly_and_old_entity_unchanged(owner):
    # Reuse the existing original-owner isolated fixture; no hand-made owner success.
    from test_dashboard_owner import _tree,ENTITY as native_entity
    gateway,workspace,_=owner
    before=_tree(workspace);legacy=gateway.entity(native_entity)
    actual=gateway.entity_view(native_entity)
    # Projection generation time varies between genuine reads, never the stored rows.
    assert actual['protocol']==temporal.VIEW_PROTOCOL
    copied=deepcopy(actual['entity']);copied.pop('generated_at_utc',None);legacy.pop('generated_at_utc',None)
    assert copied==legacy
    assert actual['temporal_shadow']['production_reuse_applied'] is False
    assert actual['temporal_shadow']['records']
    assert _tree(workspace)==before


from test_dashboard_owner import owner
