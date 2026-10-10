"""Private C06 v2 get_profiles boundary; production capability is not published."""
import base64
import copy
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import module_contract
import standard_answers
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/quick_scan/query-v2.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
MAX_INPUT_BYTES=8*1024*1024
MAX_OBSERVATION_BYTES=512*1024
ANSWER_SCHEMA=json.loads((ROOT/'schemas/answer-content.schema.json').read_bytes())
PORTABLE_SCHEMA=copy.deepcopy(json.loads((ROOT/'schemas/observation.schema.json').read_bytes()))
# A named read-only dialect, not an in-place change to the frozen v1 contract.
PORTABLE_SCHEMA['$id']='urn:iqs:stockwiki-portable-observation:1'
PORTABLE_SCHEMA['properties']['entity_id']={'type':'string','minLength':1,'maxLength':160}
ANSWER_REGISTRY=Registry().with_resource(ANSWER_SCHEMA['$id'],Resource.from_contents(ANSWER_SCHEMA))
ORIGINAL_VALIDATOR=Draft202012Validator(PORTABLE_SCHEMA,registry=ANSWER_REGISTRY,format_checker=FormatChecker())


def _validate_shape(value,kind):
    try:
        if len(module_contract.canonical_bytes(value))>MAX_INPUT_BYTES:
            raise ValueError('query_input_too_large')
        VALIDATOR.validate(value)
    except (ValidationError,TypeError,ValueError,RecursionError) as exc:
        raise ValueError('query_document_invalid') from exc
    if value['message_type']!=kind:
        raise ValueError('query_message_type_mismatch')


def load_document(path):
    try:
        with Path(path).open('rb') as handle:
            raw=handle.read(MAX_INPUT_BYTES+1)
        if len(raw)>MAX_INPUT_BYTES:
            raise ValueError('query_input_too_large')
        value=json.loads(raw.decode('utf-8-sig'),object_pairs_hook=module_contract._unique_object)
        if not isinstance(value,dict):
            raise ValueError('query_object_required')
        module_contract.canonical_bytes(value)
        return value
    except (OSError,UnicodeDecodeError,TypeError,ValueError,RecursionError) as exc:
        raise ValueError('query_json_invalid') from exc


def _subject_key(ref):
    return tuple(ref[name] for name in ('entity_id','analysis_subject_id','analysis_subject_revision',
                  'scope','scope_id','security_id','listing_id','segment_id'))


def _subject_map(refs):
    mapped={}
    for ref in refs:
        key=_subject_key(ref)
        if key in mapped:
            raise ValueError('query_duplicate_subject_scope')
        scope=ref['scope']
        if scope=='entity':
            if ref['scope_id']!=ref['entity_id'] or any(ref[n] is not None for n in ('security_id','listing_id','segment_id')):
                raise ValueError('query_entity_scope_mismatch')
        elif scope=='security':
            if not ref['security_id'] or ref['scope_id']!=ref['security_id'] or ref['segment_id'] is not None:
                raise ValueError('query_security_scope_mismatch')
        elif not ref['segment_id'] or ref['scope_id']!=ref['segment_id'] or any(ref[n] is not None for n in ('security_id','listing_id')):
            raise ValueError('query_segment_scope_mismatch')
        mapped[key]=ref
    return mapped


def validate_request(value):
    _validate_shape(value,'request')
    _subject_map(value['payload']['subject_refs'])
    _utc(value['requested_at'])
    if value['payload']['information_cutoff']>_utc(value['requested_at']).date().isoformat():
        raise ValueError('query_future_information_cutoff')


def _digest(value):
    return hashlib.sha256(module_contract.canonical_bytes(value)).hexdigest()


def _utc(value):
    if not isinstance(value,str) or not value.endswith('Z'):
        raise ValueError('query_timestamp_must_be_utc')
    try:
        return datetime.fromisoformat(value[:-1]+'+00:00')
    except ValueError as exc:
        raise ValueError('query_timestamp_invalid') from exc


def query_sha256(request):
    payload={k:v for k,v in request['payload'].items() if k!='snapshot_id'}
    return _digest({'consumer_id':request['consumer_id'],'operation':request['operation'],'payload':payload})


def snapshot_content_sha256(result):
    core=copy.deepcopy(result)
    for key in ('snapshot_id','snapshot_content_sha256'):
        core['watermark'].pop(key,None)
    return _digest(core)


def seal_response(value,*,request):
    """Content-address a captured owner result; this is NOT authentication."""
    value=copy.deepcopy(value)
    w=value['result']['watermark']
    w['query_sha256']=query_sha256(request)
    w['snapshot_content_sha256']=snapshot_content_sha256(value['result'])
    w['snapshot_id']='snap2_'+w['snapshot_content_sha256']
    return value


def _original(row):
    try:
        raw=base64.b64decode(row['original_json_base64'],validate=True)
        if len(raw)>MAX_OBSERVATION_BYTES or hashlib.sha256(raw).hexdigest()!=row['raw_sha256']:
            raise ValueError('query_original_bytes_mismatch')
        obs=json.loads(raw.decode('utf-8'),object_pairs_hook=module_contract._unique_object)
        module_contract.canonical_bytes(obs)
        ORIGINAL_VALIDATOR.validate(obs)
        if row['payload_sha256']!=_digest(obs) or row['observation_id']!=obs['observation_id']:
            raise ValueError('query_original_reference_mismatch')
        if obs['observation_id']!='obs_'+_digest({k:v for k,v in obs.items() if k!='observation_id'}):
            raise ValueError('query_original_immutable_hash_mismatch')
        return obs
    except (ValueError,TypeError,UnicodeError,ValidationError,RecursionError) as exc:
        raise ValueError('query_original_observation_invalid') from exc


def _reference(row,expected_owner):
    refs=expected_owner.get('observation_refs')
    if not isinstance(refs,dict) or row['observation_id'] not in refs:
        raise ValueError('query_independent_observation_reference_required')
    ref=refs[row['observation_id']]
    if not isinstance(ref,dict):
        raise ValueError('query_owner_observation_reference_invalid')
    expected={k:row[k] for k in ('payload_sha256','observation_sequence','ack_sequence',
                                  'ingest_status','qualification_status')}
    expected['binding_sha256']=_digest(row['subject_binding']) if row['subject_binding'] is not None else None
    if set(ref)-{'question_contract'}!=set(expected) or any(ref.get(k)!=v for k,v in expected.items()):
        raise ValueError('query_owner_observation_reference_mismatch')
    # bool == 1 is not a valid sequence attestation.
    if any(type(ref[k]) is not int for k in ('observation_sequence','ack_sequence')):
        raise ValueError('query_owner_observation_sequence_invalid')
    return ref


def _validate_original_semantics(obs,*,row,owner_ref,request,watermark,subject_ref):
    execution=obs['execution']
    answer=obs['answer']
    start,end=_utc(execution['started_at']),_utc(execution['answered_at'])
    if end<start or _utc(obs['observed_at'])!=end or end>_utc(watermark['read_at']):
        raise ValueError('query_original_time_mismatch')
    if obs['information_cutoff']>request['payload']['information_cutoff'] or obs['information_cutoff']>end.date().isoformat():
        raise ValueError('query_original_after_information_cutoff')
    if answer['question_id']!=obs['question_id']:
        raise ValueError('query_original_question_mismatch')
    # Reuse the answer owner's semantic validator. Fact contracts must come
    # from the independently retained frozen question, never the answer.
    contract=owner_ref.get('question_contract')
    if answer['response_kind']=='fact':
        if not isinstance(contract,dict) or contract.get('response_kind')!='fact':
            raise ValueError('query_fact_question_contract_required')
        question=contract
    else:
        question={'id':obs['question_id'],'response_kind':'score'}
    registry=json.loads((ROOT/'questions/metric-registry.json').read_bytes())
    try:
        standard_answers.validate_content(answer,question,obs['information_cutoff'],
            answer_schema=ANSWER_SCHEMA,metric_registry=registry)
    except (ValueError,ValidationError,TypeError,KeyError) as exc:
        raise ValueError('query_original_answer_semantics_invalid') from exc
    if execution['search_status']=='executed' and not execution['search_receipt_id']:
        raise ValueError('query_original_search_reference_missing')
    if answer['status'] in ('scored','answered') and execution['search_status']!='executed':
        raise ValueError('query_original_success_without_search')
    if obs['task_mode']=='comparison' and not obs['comparison_group_id']:
        raise ValueError('query_original_comparison_group_missing')
    if row['observation_sequence']>watermark['observation_sequence'] or row['ack_sequence']>watermark['ack_sequence']:
        raise ValueError('query_original_beyond_watermark')
    if obs['field_id'] not in request['payload']['field_ids']:
        raise ValueError('query_unrequested_observation_field')
    model_filter=request['payload']['model_filter']
    if model_filter is not None and any(execution[k]!=model_filter[k] for k in ('provider','model_resolved')):
        raise ValueError('query_original_model_filter_mismatch')
    if subject_ref is not None:
        if row['binding_status']!='bound' or row['subject_binding'] is None:
            raise ValueError('query_unbound_history_in_current_profile')
        binding=row['subject_binding']
        if binding['subject_ref']!=subject_ref:
            raise ValueError('query_original_subject_binding_mismatch')
        if (binding['observation_id']!=obs['observation_id'] or binding['payload_sha256']!=row['payload_sha256']
            or binding['execution_request_id']!=execution['request_id']
            or binding['execution_attempt_id']!=execution['attempt_id']
            or _utc(binding['recorded_before_send_at'])>start):
            raise ValueError('query_original_dispatch_binding_mismatch')
        if any(obs[k]!=subject_ref[k] for k in ('entity_id','security_id','segment_id','scope')):
            raise ValueError('query_original_scope_mismatch')
        if not isinstance(execution['model_resolved'],str) or not execution['model_resolved'].strip():
            raise ValueError('query_original_actual_model_required')
    else:
        if row['binding_status']!='legacy_unbound' or row['subject_binding'] is not None:
            raise ValueError('query_bound_answer_in_unbound_history')
        candidates=request['payload']['subject_refs']
        if not any(all(obs[k]==s[k] for k in ('entity_id','security_id','segment_id','scope')) for s in candidates):
            raise ValueError('query_foreign_unbound_history')
        if not request['payload']['include_history']:
            raise ValueError('query_unrequested_unbound_history')


def _watermark(value,request):
    result=value['result']
    w=result['watermark']
    # A named frozen capture retains its original read time. Fresh queries
    # still require a capture at or after this request; content/query/id checks
    # below apply equally to the explicit replay and never allow live fallback.
    frozen=request['payload']['snapshot_id'] is not None
    if (not frozen and _utc(w['read_at'])<_utc(request['requested_at'])) or _utc(w['read_at'])>_utc(value['response_at']):
        raise ValueError('query_watermark_time_mismatch')
    if _utc(value['response_at'])<_utc(request['requested_at']):
        raise ValueError('query_response_before_request')
    if w['query_sha256']!=query_sha256(request) or w['snapshot_content_sha256']!=snapshot_content_sha256(result):
        raise ValueError('query_snapshot_content_mismatch')
    if w['snapshot_id']!='snap2_'+w['snapshot_content_sha256']:
        raise ValueError('query_snapshot_id_mismatch')
    if request['payload']['snapshot_id'] is not None and request['payload']['snapshot_id']!=w['snapshot_id']:
        raise ValueError('query_requested_snapshot_unavailable')
    source_names=[s['namespace'] for s in w['source_watermarks']]
    if len(source_names)!=len(set(source_names)) or not {'identity','observations'}<=set(source_names):
        raise ValueError('query_source_watermarks_incomplete')
    for source in w['source_watermarks']:
        if _utc(source['read_at'])>_utc(w['read_at']):
            raise ValueError('query_source_watermark_after_capture')
        if source['status']=='available':
            if source['content_sha256'] is None or source['schema_version'] is None:
                raise ValueError('query_available_source_without_watermark')
        elif source['content_sha256'] is not None:
            raise ValueError('query_failed_source_with_content_claim')
    return any(s['status']!='available' for s in w['source_watermarks'])


def validate_response(value,*,expected_request,expected_owner):
    validate_request(expected_request)
    _validate_shape(value,'response')
    if (not isinstance(expected_owner,dict) or not {'store_id'}<=set(expected_owner)
        or set(expected_owner)-{'store_id','observation_refs'}
        or not isinstance(expected_owner['store_id'],str) or not expected_owner['store_id'].strip()):
        raise ValueError('query_independent_owner_required')
    if any(value[n]!=expected_request[n] for n in ('schema_version','request_id','operation')):
        raise ValueError('query_request_binding_mismatch')
    result=value['result']
    if result['watermark']['store_id']!=expected_owner['store_id']:
        raise ValueError('query_owner_binding_mismatch')
    requested=_subject_map(expected_request['payload']['subject_refs'])
    profiles=_subject_map([p['subject_ref'] for p in result['profiles']])
    missing=_subject_map(result['missing_subject_refs'])
    if set(profiles)&set(missing) or set(profiles)|set(missing)!=set(requested):
        raise ValueError('query_subject_coverage_mismatch')
    for key,ref in {**profiles,**missing}.items():
        if ref!=requested[key]:
            raise ValueError('query_subject_binding_mismatch')
    source_failed=_watermark(value,expected_request)
    coverage=result['coverage']
    fields=set(expected_request['payload']['field_ids'])
    covered=set(coverage['covered_field_ids'])
    gaps=set(coverage['missing_field_ids'])
    if set(coverage['requested_field_ids'])!=fields or covered&gaps or covered|gaps!=fields:
        raise ValueError('query_field_coverage_mismatch')
    if coverage['status']=='complete' and (gaps or missing):
        raise ValueError('query_false_complete_coverage')
    if coverage['status']=='not_covered' and covered:
        raise ValueError('query_false_uncovered_fields')
    if not set(coverage['covered_markets'])<=set(coverage['requested_markets']):
        raise ValueError('query_unrequested_market_coverage')
    seen=set()
    field_sets=[]
    scores=facts=False
    for profile in result['profiles']:
        available=set()
        latest_keys=set()
        for row in profile['observations']:
            if row['observation_id'] in seen:
                raise ValueError('query_duplicate_original_observation')
            seen.add(row['observation_id'])
            obs=_original(row)
            owner_ref=_reference(row,expected_owner)
            _validate_original_semantics(obs,row=row,owner_ref=owner_ref,request=expected_request,
                watermark=result['watermark'],subject_ref=profile['subject_ref'])
            if not expected_request['payload']['include_history']:
                key=tuple(obs[k] for k in ('field_id','method_id','question_version'))+tuple(
                    obs['execution'][k] for k in ('provider','model_requested','model_resolved','model_revision'))
                if key in latest_keys:
                    raise ValueError('query_multiple_latest_answers_for_one_model')
                latest_keys.add(key)
            if row['qualification_status'] not in ('rejected','conflict') and obs['answer']['status'] in ('scored','answered'):
                available.add(obs['field_id'])
                scores|=obs['answer']['response_kind']=='score'
                facts|=obs['answer']['response_kind']=='fact'
        field_sets.append(available)
    for row in result['legacy_unbound_observations']:
        if row['observation_id'] in seen:
            raise ValueError('query_duplicate_original_observation')
        seen.add(row['observation_id'])
        obs=_original(row)
        _validate_original_semantics(obs,row=row,owner_ref=_reference(row,expected_owner),
            request=expected_request,watermark=result['watermark'],subject_ref=None)
    actual_covered=set.intersection(*field_sets) if field_sets and not missing else set()
    if covered!=actual_covered or coverage['scores_available']!=scores or coverage['facts_available']!=facts:
        raise ValueError('query_false_observation_coverage')
    if source_failed:
        if result['status']!='unavailable' or coverage['status']!='unknown' or scores or facts or seen:
            raise ValueError('query_read_failure_hidden_as_coverage')
    elif result['status']=='unavailable' or coverage['status']=='unknown':
        raise ValueError('query_unexplained_read_failure')
    elif covered==fields and not missing:
        if coverage['status']!='complete' or result['status']!='ok':
            raise ValueError('query_complete_result_status_mismatch')
    elif scores or facts:
        if coverage['status']!='partial' or result['status']!='partial':
            raise ValueError('query_partial_result_status_mismatch')
    elif coverage['status']!='not_covered' or result['status']!='coverage_gap':
        raise ValueError('query_empty_coverage_status_mismatch')
