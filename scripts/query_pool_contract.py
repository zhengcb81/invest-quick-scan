"""Named 2.1 pool wire; independent owner context, never financial certification."""
import copy
import json
import re
from datetime import date
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import query_contract as profiles
import module_contract

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/quick_scan/query-pool.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
SUBJECT=Draft202012Validator(profiles.SCHEMA['$defs']['SubjectRef'],format_checker=FormatChecker())
MAX_INDEX_BYTES=64*1024*1024
MAX_RESPONSE_BYTES=8*1024*1024
INDEX_KEYS={'protocol','universe_id','selection','owner_store_id','active_entity_count','rows','variants',
    'missing_entity_ids','missing_subject_refs','profile_batch_count','read_at','source_watermarks',
    'source_consistency','status','coverage','c06_envelope_validated','original_profile_envelopes_validated',
    'financial_accuracy_proven','facts_producer_ready','API_requests','content_sha256','snapshot_id'}
ROW_KEYS={'subject_ref','canonical_name','observation_refs','scope_kind','perimeter_coverage','scope_as_of',
    'identity_state','securities','scan_enabled','member_version'}
OBS_KEYS={'observation_id','payload_sha256','field_id','question_id','status','score','information_cutoff',
    'observed_at','provider','model_resolved','check_level','check_level_receipt_id','evidence_review_status',
    'qualification_status','variant_id','validity_status'}


def digest(value):return profiles._digest(value)


def validate_request(value):
    try:
        VALIDATOR.validate(value)
        if value['message_type']!='request':raise ValueError('pool_request_required')
        profiles._utc(value['requested_at'])
        if value['payload']['information_cutoff']>profiles._utc(value['requested_at']).date().isoformat():
            raise ValueError('pool_future_information_cutoff')
        payload=value['payload']
        if payload['cursor'] is not None and payload['snapshot_id'] is None:
            raise ValueError('pool_cursor_requires_snapshot')
        if value['operation']=='candidate_set':profiles._subject_map(payload['subject_refs'])
        policy=payload['filters']['score_policy']
        if policy is not None:
            fields=set(payload['field_ids'])
            def leaves(node,depth=0):
                if depth>20:raise ValueError('pool_rule_depth_limit')
                if 'condition' in node:return [node['condition']['field']]
                if 'not' in node:return leaves(node['not'],depth+1)
                return [f for part in node.get('all',node.get('any',[])) for f in leaves(part,depth+1)]
            selected=leaves(policy['root_rule'])+[g['field'] for g in policy.get('critical_gates',[])]
            if len(selected)>200 or not set(selected)<=fields:raise ValueError('pool_rule_fields_unrequested')
        if len(module_contract.canonical_bytes(value))>MAX_RESPONSE_BYTES:raise ValueError('pool_request_too_large')
    except (ValidationError,KeyError,TypeError,RecursionError) as exc:
        raise ValueError('pool_request_invalid') from exc
    return copy.deepcopy(value)


def query_sha256(request):
    validate_request(request)
    payload={k:v for k,v in request['payload'].items()
        if k not in {'snapshot_id','cursor','subject_refs','query_sha256','label'}}
    return digest(dict(consumer_id=request['consumer_id'],schema_version='2.1.0',
        operation='search',payload=payload))


def capture_id(index,query_hash):
    return 'psnap1_'+digest(dict(index_sha256=index['content_sha256'],query_sha256=query_hash))


def validate_index(index,*,store_id):
    try:
        if not isinstance(index,dict) or set(index)!=INDEX_KEYS:raise ValueError('pool_index_shape')
        core={k:v for k,v in index.items() if k not in {'content_sha256','snapshot_id'}}
        if index['content_sha256']!=digest(core) or index['snapshot_id']!='pool1_'+index['content_sha256']:
            raise ValueError('pool_index_integrity_mismatch')
        if (index['protocol'] not in {'stockwiki.c06_pool_index/1.0.0','stockwiki.c06_pool_index/1.1.0'} or index['owner_store_id']!=store_id
            or index['source_consistency']!='sequential_owner_reads'
            or index['c06_envelope_validated'] is not False or index['original_profile_envelopes_validated'] is not True
            or index['financial_accuracy_proven'] is not False or index['facts_producer_ready'] is not False
            or type(index['API_requests']) is not int or index['API_requests']!=0):
            raise ValueError('pool_index_owner_or_claim_mismatch')
        read_at=profiles._utc(index['read_at'])
        marks=index['source_watermarks']
        if len(marks)!=4 or {m['namespace'] for m in marks}!={'universe','identity','analysis_subjects','observations'}:
            raise ValueError('pool_source_watermarks_invalid')
        for mark in marks:
            if (mark['status'] not in {'available','missing','read_error','schema_unavailable'}
                or type(mark['sequence']) is not int or mark['sequence']<0
                or profiles._utc(mark['read_at'])>read_at):raise ValueError('pool_source_watermarks_invalid')
        if len(module_contract.canonical_bytes(index))>MAX_INDEX_BYTES:raise ValueError('pool_index_retention_limit')
        refs=profiles._subject_map([row['subject_ref'] for row in index['rows']])
        seen=set();fields=[];found=set()
        for row in index['rows']:
            if set(row)!=ROW_KEYS:raise ValueError('pool_index_row_shape')
            SUBJECT.validate(row['subject_ref'])
            if not isinstance(row['canonical_name'],str) or not 1<=len(row['canonical_name'])<=200:
                raise ValueError('pool_index_name_invalid')
            if type(row['scan_enabled']) is not bool or type(row['member_version']) is not int or row['member_version']<1:
                raise ValueError('pool_index_membership_invalid')
            found.add(row['subject_ref']['entity_id']);available=set()
            for obs in row['observation_refs']:
                if set(obs)!=OBS_KEYS:raise ValueError('pool_index_observation_shape')
                if obs['observation_id'] in seen:raise ValueError('pool_index_duplicate_observation')
                seen.add(obs['observation_id'])
                if (not re.fullmatch('obs_[a-f0-9]{64}',obs['observation_id'])
                    or not re.fullmatch('[a-f0-9]{64}',obs['payload_sha256'])
                    or any(not isinstance(obs[k],str) or not 1<=len(obs[k])<=160
                        for k in ('field_id','question_id','provider','model_resolved'))
                    or date.fromisoformat(obs['information_cutoff']).isoformat()!=obs['information_cutoff']):
                    raise ValueError('pool_observation_reference_invalid')
                if (obs['variant_id'] not in index['variants'] or obs['field_id'] not in index['selection']['field_ids']
                    or obs['information_cutoff']>index['selection']['information_cutoff']
                    or profiles._utc(obs['observed_at'])>read_at):raise ValueError('pool_index_observation_binding_invalid')
                if obs['check_level']!='unverified_model_output' or obs['check_level_receipt_id'] is not None:
                    raise ValueError('pool_independent_qualification_required')
                if obs['validity_status']!='not_assessed':raise ValueError('pool_independent_validity_required')
                definition=index['variants'][obs['variant_id']];key=definition['variant_key'];ref=row['subject_ref']
                if index['protocol']=='stockwiki.c06_pool_index/1.1.0':
                    if len(key)!=19:raise ValueError('pool_variant_integrity_mismatch')
                    key=[ref['entity_id'],*key[:11],ref['security_id'],ref['listing_id'],ref['segment_id'],*key[11:]]
                if (len(key)!=23 or key[0:3]!=[ref['entity_id'],obs['field_id'],obs['question_id']]
                    or key[11:15]!=[ref['scope'],ref['security_id'],ref['listing_id'],ref['segment_id']]
                    or key[17]!=obs['provider'] or key[19]!=obs['model_resolved']
                    or key[21]!=module_contract.canonical_bytes(definition['cohort']).decode('utf-8')):
                    raise ValueError('pool_variant_original_axis_mismatch')
                score=obs['score']
                if obs['status']=='scored':
                    if type(score) is not int or not 1<=score<=10:raise ValueError('pool_score_invalid')
                elif score is not None:raise ValueError('pool_null_score_required')
                if obs['qualification_status'] not in {'rejected','conflict'} and obs['status'] in {'scored','answered'}:
                    available.add(obs['field_id'])
            fields.append(available)
        for key,variant in index['variants'].items():
            shared=index['protocol']=='stockwiki.c06_pool_index/1.1.0'
            keys={'protocol','cohort','variant_key'} if shared else {'cohort','variant_key'}
            if key!=digest(variant) or set(variant)!=keys or len(variant['variant_key'])!=(19 if shared else 23):
                raise ValueError('pool_variant_integrity_mismatch')
            if shared and variant['protocol']!='stockwiki.c06_shared_caliber/1.0.0':raise ValueError('pool_variant_protocol_invalid')
        if type(index['active_entity_count']) is not int or index['active_entity_count']!=len(found|set(index['missing_entity_ids'])):
            raise ValueError('pool_member_count_mismatch')
        expected=set.intersection(*fields) if fields and not index['missing_entity_ids'] and not index['missing_subject_refs'] else set()
        coverage=index['coverage'];requested=set(index['selection']['field_ids'])
        if (set(coverage['requested_field_ids'])!=requested or set(coverage['covered_field_ids'])!=expected
            or set(coverage['missing_field_ids'])!=requested-expected):raise ValueError('pool_coverage_mismatch')
        failed=any(mark['status']!='available' for mark in marks)
        complete=expected==requested and not index['missing_entity_ids'] and not index['missing_subject_refs'] and not failed
        partial=any(fields) and not complete and not failed
        expected_coverage='unknown' if failed else 'complete' if complete else 'partial' if partial else 'not_covered'
        expected_status='unavailable' if failed else 'ok' if complete else 'partial' if partial else 'coverage_gap'
        if coverage['status']!=expected_coverage or index['status']!=expected_status or (failed and seen):
            raise ValueError('pool_source_failure_hidden_as_coverage')
    except (ValidationError,KeyError,TypeError,RecursionError) as exc:
        raise ValueError('pool_index_invalid') from exc
    return copy.deepcopy(index)


def _validate_response(response,*,request,index,selected_rows,store_id,request_validator,index_validator,
        query_hasher,validator,row_extra=frozenset(),watermark_extra=None,qualification_available=False,
        candidate_protocol='stockwiki.c06_candidate_set/2.1.0',candidate_prefix='cset2_',candidate_qualified=False,
        selection_keys=('field_ids','information_cutoff','model_filter'),result_extra=None):
    request_validator(request);index_validator(index,store_id=store_id)
    if len(module_contract.canonical_bytes(response))>MAX_RESPONSE_BYTES:raise ValueError('pool_response_too_large')
    try:validator.validate(response)
    except ValidationError as error:raise ValueError('pool_response_invalid') from error
    if response['message_type']!='response' or any(response[k]!=request[k] for k in ('schema_version','operation','request_id')):
        raise ValueError('pool_response_binding_mismatch')
    if profiles._utc(response['response_at'])<profiles._utc(request['requested_at']):
        raise ValueError('pool_response_before_request')
    if (profiles._utc(index['read_at'])>profiles._utc(response['response_at'])
        or (request['payload']['snapshot_id'] is None
            and profiles._utc(index['read_at'])<profiles._utc(request['requested_at']))):
        raise ValueError('pool_response_read_time_invalid')
    result=response['result'];mark=result['watermark'];qhash=query_hasher(request)
    expected=dict(store_id=store_id,snapshot_id=capture_id(index,qhash),query_sha256=qhash,
        pool_index_sha256=index['content_sha256'],read_at=index['read_at'],
        source_watermarks=index['source_watermarks'],source_consistency=index['source_consistency'],**(watermark_extra or {}))
    if mark!=expected or (request['payload']['snapshot_id'] is not None and mark['snapshot_id']!=request['payload']['snapshot_id']):
        raise ValueError('pool_response_watermark_mismatch')
    payload=request['payload']
    if (index['universe_id']!=payload['universe_id'] or index['selection']!={k:payload[k]
        for k in selection_keys}):raise ValueError('pool_response_selection_mismatch')
    if any(module_contract.canonical_bytes(result.get(k))!=module_contract.canonical_bytes(value)
        for k,value in (result_extra or {}).items()):raise ValueError('pool_response_scope_projection_mismatch')
    original={digest(row['subject_ref']):row for row in index['rows']}
    all_refs=profiles._subject_map([row['subject_ref'] for row in selected_rows])
    for row in selected_rows:
        if set(row)!=ROW_KEYS|{'selection_outcome','selection_explanations'}|row_extra:
            raise ValueError('pool_selected_row_shape')
        if {k:row[k] for k in ROW_KEYS}!=original.get(digest(row['subject_ref'])):
            raise ValueError('pool_response_original_changed')
        if row['selection_outcome'] not in {'pass','fail','unknown','not_requested'}:
            raise ValueError('pool_selection_outcome_invalid')
        if row['selection_outcome']=='pass' and request['payload']['filters']['score_policy'] is not None and not qualification_available:
            raise ValueError('pool_independent_qualification_required')
    if result['rows']!=selected_rows:raise ValueError('pool_response_row_mismatch')
    needed={obs['variant_id'] for row in selected_rows for obs in row['observation_refs']}
    if result['calibers']!={key:index['variants'][key] for key in needed}:
        raise ValueError('pool_response_caliber_mismatch')
    if result['coverage']!=index['coverage'] or result['total_subject_count']!=len(index['rows']):
        raise ValueError('pool_response_coverage_mismatch')
    counts=result['condition_counts']
    if (sum(counts.values())>len(index['rows']) or result['matched_subject_count']>len(index['rows'])
        or len(selected_rows)>result['matched_subject_count']):raise ValueError('pool_response_counts_invalid')
    if index['status']=='unavailable' and result['status']!='unavailable':raise ValueError('pool_response_failure_hidden')
    if result['status'] in {'ok','empty'} and (index['coverage']['status']!='complete'
        or (payload['filters']['score_policy'] is not None
            and (not qualification_available or result['screening_coverage_status']!='complete'))):raise ValueError('pool_response_false_complete')
    if (result['status']=='ok' and not result['matched_subject_count']) or (result['status']=='empty' and result['matched_subject_count']):
        raise ValueError('pool_response_empty_mismatch')
    if (result['financial_accuracy_proven'] is not False or result['full_C06_milestone_accepted'] is not False
        or result['facts_producer_ready'] is not False or result['API_requests']!=0):raise ValueError('pool_response_false_claim')
    candidate=result['candidate_set']
    if request['operation']=='candidate_set':
        if candidate is None:raise ValueError('pool_candidate_set_required')
        candidate_keys={'protocol','store_id','snapshot_id','query_sha256','label','rule','members',
            'read_at','screening_qualified','candidate_set_id','content_sha256'}
        if set(candidate)!=candidate_keys:raise ValueError('pool_candidate_shape_invalid')
        body={k:v for k,v in candidate.items() if k not in {'candidate_set_id','content_sha256'}}
        if candidate['content_sha256']!=digest(body) or candidate['candidate_set_id']!=candidate_prefix+digest(body):
            raise ValueError('pool_candidate_integrity_mismatch')
        if [row['subject_ref'] for row in candidate['members']]!=request['payload']['subject_refs']:
            raise ValueError('pool_candidate_subject_mismatch')
        if candidate['members']!=selected_rows or candidate['screening_qualified'] is not candidate_qualified:
            raise ValueError('pool_candidate_original_changed')
        if any(candidate[k]!=v for k,v in dict(protocol=candidate_protocol,
            store_id=store_id,snapshot_id=mark['snapshot_id'],query_sha256=qhash,
            label=payload['label'],rule=payload['filters']['score_policy'],read_at=index['read_at']).items()):
            raise ValueError('pool_candidate_query_metadata_mismatch')
    elif candidate is not None:raise ValueError('pool_unrequested_candidate_set')
    return copy.deepcopy(response)


def validate_response(response,*,request,index,selected_rows,store_id):
    return _validate_response(response,request=request,index=index,selected_rows=selected_rows,store_id=store_id,
        request_validator=validate_request,index_validator=validate_index,query_hasher=query_sha256,validator=VALIDATOR)


validate_pool_request=validate_request
pool_query_sha256=query_sha256
validate_pool_index=validate_index
finish_pool_response=validate_response
