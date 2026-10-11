"""Named 2.2 pool projection: independent current owner assessment is mandatory.

Reuses the original raw index/response invariants. Consumer requests contain
neither audit receipts nor field TTL/policy. No financial truth certification.
"""
import copy
import json
import re
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
import query_pool_contract as raw
import query_contract as profiles
from query_field_assessment import LEVELS
from module_contract import canonical_bytes

SCHEMA=json.loads((raw.ROOT/'schemas/quick_scan/query-pool-qualified.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
FIELDS={'information_as_of','valid_until','validity_status','minimum_check_level',
    'check_level','check_level_receipt_id','qualification_status','screening_eligible'}
MARK_KEYS={'protocol','store_id','source_status','qualification_sequence','field_policy_sha256',
    'field_policy_valid_until','input_set_sha256','receipt_set_sha256','source_consistency'}
CONTEXT_KEYS={'protocol','store_id','read_at','qualification_watermark','field_assessments','context_sha256'}
DIGEST_CONTEXT_KEYS=(CONTEXT_KEYS-{'field_assessments'})|{'field_assessments_sha256'}
digest=raw.digest


def validate_request(value):
    try:VALIDATOR.validate(value)
    except ValidationError as exc:raise ValueError('qualified_pool_request_invalid') from exc
    legacy=copy.deepcopy(value);legacy['schema_version']='2.1.0'
    raw.validate_request(legacy)
    return copy.deepcopy(value)


def query_sha256(request):
    validate_request(request)
    payload={k:v for k,v in request['payload'].items()
        if k not in {'snapshot_id','cursor','subject_refs','query_sha256','label'}}
    return digest(dict(consumer_id=request['consumer_id'],schema_version='2.2.0',operation='search',payload=payload))


def _context(context,store_id,assessment_values):
    try:
        compact=context.get('protocol')=='stockwiki.pool_field_assessment_digest/1.0.0' if isinstance(context,dict) else False
        if (not isinstance(context,dict) or set(context)!=(DIGEST_CONTEXT_KEYS if compact else CONTEXT_KEYS)
            or context['protocol']!=('stockwiki.pool_field_assessment_digest/1.0.0' if compact else 'stockwiki.pool_field_assessment/1.0.0')
            or context['store_id']!=store_id
            or context['context_sha256']!=digest({k:v for k,v in context.items() if k!='context_sha256'})):
            raise ValueError('pool_independent_assessment_required')
        if compact:
            if digest(assessment_values)!=context['field_assessments_sha256']:
                raise ValueError('pool_independent_assessment_mismatch')
        elif assessment_values!=context['field_assessments']:
            raise ValueError('pool_independent_assessment_mismatch')
        profiles._utc(context['read_at']);mark=context['qualification_watermark']
        if (set(mark)!=MARK_KEYS or mark['protocol']!='stockwiki.pool_qualification_watermark/1.0.0'
            or mark['store_id']!=store_id or mark['source_status'] not in {'available','not_initialized'}
            or type(mark['qualification_sequence']) is not int or mark['qualification_sequence']<0
            or mark['source_consistency']!='one_native_read_transaction'
            or any(not isinstance(mark[k],str) or not re.fullmatch('[a-f0-9]{64}',mark[k])
                for k in ('input_set_sha256','receipt_set_sha256'))
            or (mark['field_policy_sha256'] is not None and not re.fullmatch('[a-f0-9]{64}',mark['field_policy_sha256']))):
            raise ValueError('pool_independent_assessment_watermark_invalid')
        values=assessment_values
        if mark['field_policy_valid_until'] is not None:
            if profiles._utc(context['read_at'])>=profiles._utc(mark['field_policy_valid_until']):
                raise ValueError('pool_assessment_policy_expired')
        if not isinstance(values,dict) or len(values)>60000:raise ValueError('pool_assessment_capacity_limit')
        for key,value in values.items():
            if (not re.fullmatch('obs_[a-f0-9]{64}',key) or set(value)!=FIELDS
                or value['check_level'] not in LEVELS
                or value['minimum_check_level'] not in (None,*LEVELS[1:])
                or type(value['screening_eligible']) is not bool
                or value['qualification_status'] not in {'verified','revoked','receipt_missing'}
                or value['validity_status'] not in {'fresh','stale','unknown','policy_unavailable','field_policy_missing'}):
                raise ValueError('pool_assessment_projection_invalid')
            if value['valid_until'] is not None:profiles._utc(value['valid_until'])
            if value['validity_status']=='fresh' and (value['valid_until'] is None
                or profiles._utc(context['read_at'])>=profiles._utc(value['valid_until'])):
                raise ValueError('pool_assessment_expired')
            if value['screening_eligible'] and (value['minimum_check_level'] is None
                or LEVELS.index(value['check_level'])<LEVELS.index(value['minimum_check_level'])
                or value['qualification_status']!='verified' or value['validity_status']!='fresh'):
                raise ValueError('pool_assessment_false_eligibility')
        return context
    except (KeyError,TypeError,RecursionError) as exc:raise ValueError('pool_assessment_context_invalid') from exc


def validate_index(index,*,store_id,assessment_context):
    context=_context(assessment_context,store_id,index['field_assessments'])
    if (set(index)!=raw.INDEX_KEYS|{'field_assessments','qualification_watermark'}
        or index['protocol']!='stockwiki.c06_pool_index/1.2.0'
        or index['qualification_watermark']!=context['qualification_watermark']):
        raise ValueError('pool_independent_assessment_mismatch')
    if (index['content_sha256']!=digest({k:v for k,v in index.items() if k not in {'content_sha256','snapshot_id'}})
        or index['snapshot_id']!='pool1_'+index['content_sha256']):raise ValueError('pool_qualified_index_integrity_mismatch')
    if len(canonical_bytes(index))>raw.MAX_INDEX_BYTES:raise ValueError('pool_index_retention_limit')
    legacy={k:copy.deepcopy(index[k]) for k in raw.INDEX_KEYS}
    legacy['protocol']='stockwiki.c06_pool_index/1.1.0'
    legacy['content_sha256']=digest({k:v for k,v in legacy.items() if k not in {'content_sha256','snapshot_id'}})
    legacy['snapshot_id']='pool1_'+legacy['content_sha256']
    raw.validate_index(legacy,store_id=store_id)
    if set(index['field_assessments'])!={o['observation_id'] for row in index['rows'] for o in row['observation_refs']}:
        raise ValueError('pool_assessment_original_set_mismatch')
    if profiles._utc(context['read_at'])<profiles._utc(index['read_at']):raise ValueError('pool_assessment_before_capture')
    return copy.deepcopy(index)


def validate_response(response,*,request,index,selected_rows,store_id,assessment_context):
    validate_index(index,store_id=store_id,assessment_context=assessment_context)
    for row in selected_rows:
        expected={o['observation_id']:index['field_assessments'][o['observation_id']] for o in row['observation_refs']}
        if row.get('field_assessments')!=expected:raise ValueError('pool_response_owner_assessment_changed')
    candidate_qualified=(bool(selected_rows) and request['payload']['filters']['score_policy'] is not None
        and request['payload']['view']=='qualified' and all(row['selection_outcome']=='pass' for row in selected_rows))
    return raw._validate_response(response,request=request,index=index,selected_rows=selected_rows,store_id=store_id,
        request_validator=validate_request,index_validator=lambda value,store_id:validate_index(value,
            store_id=store_id,assessment_context=assessment_context),query_hasher=query_sha256,validator=VALIDATOR,
        row_extra={'field_assessments'},watermark_extra={'qualification_watermark':index['qualification_watermark']},
        qualification_available=True,candidate_protocol='stockwiki.c06_candidate_set/2.2.0',
        candidate_prefix='cset3_',candidate_qualified=candidate_qualified)


validate_pool_request=validate_request
pool_query_sha256=query_sha256
validate_qualified_pool_index=validate_index
finish_qualified_pool_response=validate_response
