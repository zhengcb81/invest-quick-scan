"""Versioned pure preview contract. Content integrity never grants permission.

Query v2 and legacy refresh remain unchanged. The owner independently supplies
the current W15 plan, membership, policy and original QA budget quote. This
module has no databases, authentication, queue, model client or HTTP execution.
"""
import copy
import json
from datetime import timedelta
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
import module_contract
import query_contract as query

SCHEMA=json.loads((Path(__file__).resolve().parents[1]/'schemas/quick_scan/refresh-v1.schema.json').read_bytes())
CURRENCY_SCHEMA=json.loads((Path(__file__).resolve().parents[1]/'schemas/quick_scan/refresh-v1.1.schema.json').read_bytes())
from query_vendor_contract import SCHEMA as VENDOR_QUERY_SCHEMA
REGISTRY=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in
    (SCHEMA,CURRENCY_SCHEMA,query.SCHEMA,VENDOR_QUERY_SCHEMA)])
MAX_BYTES=8*1024*1024
DISPATCH={'dispatch_new_work','dispatch_new_generation','resume_existing_work'}
HELD={'deferred_unknown','deferred_scope_unbound','manual_refresh_required'}


def paid_work_count(items):
    # An already durable answer only needs delivery. This does not decide
    # retries: uncertain attempts remain governed by the original executor.
    return sum(i['decision'] in DISPATCH and not (
        i['decision']=='resume_existing_work' and i['existing_work_status']=='result_ready') for i in items)


def digest(value):return query._digest(value)


def _shape(value,kind,*,currency_dialect=False):
    if kind!='OwnerState':
        currency_dialect = isinstance(value,dict) and value.get('protocol') in {
            'iqs.refresh_request/1.1.0','stockwiki.refresh_preview/1.1.0','stockwiki.refresh_owner_policy/1.1.0'}
    schema=CURRENCY_SCHEMA if currency_dialect else SCHEMA
    try:
        if len(module_contract.canonical_bytes(value))>MAX_BYTES:
            raise ValueError('refresh_input_too_large')
        Draft202012Validator({'$ref':schema['$id']+'#/$defs/'+kind},
            registry=REGISTRY,format_checker=FormatChecker()).validate(value)
    except (ValidationError,TypeError,ValueError,RecursionError) as error:
        raise ValueError('refresh_document_invalid') from error


def validate_request(request):
    _shape(request,'Request')
    source=request['source_query']
    selected=query
    if request['protocol']=='iqs.refresh_request/1.1.0' and source.get('schema_version')=='2.6.0':
        import query_vendor_contract as selected
    selected.validate_request(source)
    if source['payload']['snapshot_id'] is None:
        raise ValueError('refresh_frozen_snapshot_required')
    if request['consumer_id']!=source['consumer_id']:
        raise ValueError('refresh_consumer_mismatch')
    query._subject_map(request['subject_refs'])
    captured={digest(r) for r in source['payload']['subject_refs']}
    if any(digest(r) not in captured for r in request['subject_refs']):
        raise ValueError('refresh_subject_outside_snapshot')
    if set(request['field_ids'])-set(source['payload']['field_ids']):
        raise ValueError('refresh_field_outside_snapshot')
    if query._utc(request['requested_at'])<query._utc(source['requested_at']):
        raise ValueError('refresh_request_before_query')


def validate_policy(policy):
    """Validate owner-configured structure, never a consumer permission claim."""
    _shape(policy,'OwnerPolicy')
    if type(policy['policy_version']) is not int or type(policy['ttl_hours']) is not int:
        raise ValueError('refresh_integer_required')
    dynamic_routes=policy.get('route_resolution','explicit_routes')=='current_owner_members'
    dynamic_fields=policy.get('field_permission','explicit_fields')=='current_manifest'
    if (dynamic_routes and policy['routes']) or (not dynamic_routes and not policy['routes']):
        raise ValueError('refresh_policy_route_permission_ambiguous')
    if (dynamic_fields and policy['field_ids']) or (not dynamic_fields and not policy['field_ids']):
        raise ValueError('refresh_policy_field_permission_ambiguous')
    seen=set()
    for row in policy['routes']:
        ref=row['subject_ref'];query._subject_map([ref])
        key=digest(ref)
        if key in seen:raise ValueError('refresh_policy_duplicate_subject')
        seen.add(key)
        if row['subject_key']!=ref['analysis_subject_id']+'@'+str(ref['analysis_subject_revision']):
            raise ValueError('refresh_policy_subject_key_mismatch')
        scope='segment' if ref['scope']=='segment' else 'entity'
        scope_id=ref['segment_id'] if scope=='segment' else ref['entity_id']
        if row['scope']!=scope or row['scope_id']!=scope_id:
            raise ValueError('refresh_policy_route_scope_mismatch')
    for key in ('code_root','work_store','budget_policy_file'):
        if not Path(policy['qa'][key]).is_absolute():raise ValueError('refresh_policy_absolute_path_required')
    return copy.deepcopy(policy)


def _check_state(request,state):
    _shape(state,'OwnerState',currency_dialect=request['protocol']=='iqs.refresh_request/1.1.0')
    numbers=[state['policy_version'],state['ttl_hours'],*state['member_versions'].values(),
        *[a[k] for a in state['anchors'] for k in ('anchor_version','identity_revision')],
        state['quote']['max_cost_micros'],state['quote']['max_http_requests'],
        *[i['generation'] for i in state['items'] if i['generation'] is not None]]
    if any(type(n) is not int for n in numbers):raise ValueError('refresh_integer_required')
    refs={digest(r):r for r in request['subject_refs']}
    if set(state['member_versions'])!={r['entity_id'] for r in refs.values()}:
        raise ValueError('refresh_owner_roster_scope_mismatch')
    if {digest(a['subject_ref']) for a in state['anchors']}!=set(refs):
        raise ValueError('refresh_owner_anchor_scope_mismatch')
    if len(state['anchors'])!=len(refs):raise ValueError('refresh_duplicate_anchor')
    seen=set(); covered=set()
    expected={(key,field) for key in refs for field in request['field_ids']}
    for item in state['items']:
        key=digest(item['subject_ref'])
        pair=(key,item['field_id'])
        unique=(*pair,item['question_id'])
        if pair not in expected or unique in seen:
            raise ValueError('refresh_owner_plan_scope_mismatch')
        seen.add(unique);covered.add(pair)
        if (item['decision']=='reuse')!=(item['reuse_observation_id'] is not None):
            raise ValueError('refresh_original_reference_required')
        if item['decision'] in DISPATCH and item['generation'] is None:
            raise ValueError('refresh_work_generation_required')
        if item['decision']=='resume_existing_work' and item['existing_work_status'] is None:
            raise ValueError('refresh_existing_work_status_required')
    if covered!=expected:raise ValueError('refresh_owner_plan_incomplete')
    source_filter=request['source_query']['payload']['model_filter']
    if source_filter is not None and source_filter!={'provider':state['provider'],'model_resolved':state['model']}:
        raise ValueError('refresh_selected_model_outside_snapshot_filter')
    tasks=paid_work_count(state['items'])
    quote=state['quote']
    if tasks and quote['budget_available'] and quote['max_http_requests']<tasks:
        raise ValueError('refresh_quote_request_bound_insufficient')
    if not tasks and (quote['max_http_requests'] or quote['max_cost_micros']):
        raise ValueError('refresh_no_work_must_be_zero_cost')


def create_preview(request,owner_state,*,created_at,expires_at):
    validate_request(request);_check_state(request,owner_state)
    created,end=query._utc(created_at),query._utc(expires_at)
    if created<query._utc(request['requested_at']) or not created<end<=created+timedelta(hours=1):
        raise ValueError('refresh_preview_time_invalid')
    state=copy.deepcopy(owner_state)
    tasks=any(i['decision'] in DISPATCH for i in state['items'])
    paid_tasks=paid_work_count(state['items'])
    held=any(i['decision'] in HELD for i in state['items'])
    status=('blocked' if held or (paid_tasks and not state['quote']['budget_available'])
        else 'ready' if tasks else 'noop')
    scope=dict(source_snapshot_id=request['source_query']['payload']['snapshot_id'],
        subject_refs=request['subject_refs'],field_ids=request['field_ids'],
        consumer_id=request['consumer_id'],origin_task_id=request['origin_task_id'])
    result=dict(protocol='stockwiki.refresh_preview/'+('1.1.0' if request['protocol']=='iqs.refresh_request/1.1.0' else '1.0.0'),operation='request_refresh',
        request_sha256=digest(request),scope_sha256=digest(scope),owner_state_sha256=digest(state),
        source_snapshot_id=scope['source_snapshot_id'],
        **{k:state[k] for k in ('store_id','policy_id','policy_version','policy_sha256','provider','model','items','quote')},
        created_at=created_at,expires_at=expires_at,status=status,
        requires_user_confirmation=status=='ready',dispatch_started=False,API_requests=0)
    result['preview_id']='rv1_'+digest(result)
    _shape(result,'Preview')
    return result


def validate_preview(preview,*,request,owner_state,now=None):
    _shape(preview,'Preview')
    if type(preview['API_requests']) is not int or type(preview['policy_version']) is not int:
        raise ValueError('refresh_integer_required')
    expected=create_preview(request,owner_state,created_at=preview['created_at'],expires_at=preview['expires_at'])
    if preview!=expected:raise ValueError('refresh_preview_owner_mismatch')
    if now is not None and not query._utc(preview['created_at'])<=query._utc(now)<query._utc(preview['expires_at']):
        raise ValueError('refresh_preview_expired')
    return copy.deepcopy(preview)
