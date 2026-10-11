"""Pure scoped research lead projection; missing provenance never proves independence."""
import copy
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
import query_contract as core
import module_contract
from exchange_contract import independent_support

SCHEMA=json.loads((Path(__file__).resolve().parents[1]/'schemas/quick_scan/query-research.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
MAX_BYTES=16*1024*1024
MAX_CLOSURE_DEPTH=256
MAX_CLOSURE_NODES=1000
PROFILE_FIELDS=('subject_refs','field_ids','information_cutoff','include_history','model_filter','snapshot_id')


def _shape(value,kind):
    try:
        if len(module_contract.canonical_bytes(value))>MAX_BYTES:raise ValueError('research_document_too_large')
        VALIDATOR.validate(value)
        if value['message_type']!=kind:raise ValueError('research_message_type')
    except (ValidationError,TypeError,ValueError,RecursionError) as error:
        raise ValueError('research_document_invalid') from error


def validate_request(request):
    _shape(request,'request')
    if not request['payload']['origin_task_id'].strip() or not request['payload']['purpose'].strip():
        raise ValueError('research_blank_origin_or_purpose')
    core.validate_request(base_request(request))
    return copy.deepcopy(request)


def base_request(request,*,profile_snapshot_id=None):
    payload={key:copy.deepcopy(request['payload'][key]) for key in PROFILE_FIELDS}
    payload['snapshot_id']=profile_snapshot_id
    return dict(message_type='request',schema_version='2.0.0',operation='get_profiles',
        **{key:request[key] for key in ('request_id','consumer_id','requested_at')},payload=payload)


def query_sha256(request):
    validate_request(request)
    semantic=dict(consumer_id=request['consumer_id'],operation=request['operation'],
        payload={k:v for k,v in request['payload'].items() if k!='snapshot_id'})
    return core._digest(semantic)


def _owner(owner):
    if (not isinstance(owner,dict) or set(owner)!={'store_id','observation_refs','lineage_source_status','lineage_by_observation'}
        or not isinstance(owner['observation_refs'],dict)
        or owner['lineage_source_status'] not in {'not_recorded','recorded'}):
        raise ValueError('research_independent_owner_required')
    graph=owner['lineage_by_observation']
    spec=SCHEMA['$defs']['Response']['properties']['result']['properties']['lineage_by_observation']
    try:Draft202012Validator(spec).validate(graph)
    except ValidationError as error:raise ValueError('research_owner_lineage_invalid') from error
    if owner['lineage_source_status']=='not_recorded' and graph:
        raise ValueError('research_unrecorded_lineage_not_empty')
    return {key:copy.deepcopy(owner[key]) for key in ('store_id','observation_refs')}


def _closure(candidate,graph):
    if candidate not in graph:return [],'unknown'
    visited=set();active=set();upstream=set();stack=[(candidate,0,False)]
    while stack:
        node,depth,exit_node=stack.pop()
        if exit_node:active.remove(node);visited.add(node);continue
        if depth>MAX_CLOSURE_DEPTH or len(visited)+len(active)>=MAX_CLOSURE_NODES:
            return sorted(upstream),'limit_exceeded'
        if node in active:return sorted(upstream),'cycle'
        if node in visited:continue
        if node not in graph:return sorted(upstream),'missing_ancestor'
        active.add(node);stack.append((node,depth,True))
        for parent in reversed(graph[node]):
            if parent!=candidate:upstream.add(parent)
            stack.append((parent,depth+1,False))
    return sorted(upstream),'complete'


def _project(profile,request,owner):
    graph=owner['lineage_by_observation'];wanted=set(request['payload']['observation_ids'])
    seen=set();leads=[]
    for company in profile['profiles']:
        for row in company['observations']:
            oid=row['observation_id']
            if wanted and oid not in wanted:continue
            if oid in seen:raise ValueError('research_duplicate_original')
            seen.add(oid);original=core._original(row)
            upstream,status=_closure(oid,graph)
            by_target={}
            for target in request['payload']['target_observation_ids']:
                # Original algorithm, only after a complete bounded closure;
                # this boolean describes graph dependence, not source truth.
                by_target[target]=(status=='complete' and independent_support(target,oid,graph))
            urls=sorted({v['url'] for v in original['answer']['evidence']})
            for url in urls:
                parsed=urlsplit(url)
                if parsed.scheme not in {'http','https'} or not parsed.hostname or any(c.isspace() for c in url):
                    raise ValueError('research_original_url_invalid')
            leads.append(dict(schema_version='2.0.0',origin_task_id=request['payload']['origin_task_id'],
                subject_ref=copy.deepcopy(company['subject_ref']),observation_ids=[oid],
                upstream_observation_ids=upstream,upstream_closure_status=status,evidence_urls=urls,
                handoff_reason=request['payload']['purpose'],formal_evidence_accepted=False,
                independent_support_by_target=by_target))
            if len(leads)>1000:raise ValueError('research_lead_limit_exceeded')
    missing=sorted(wanted-seen)
    status=profile['status']
    if status!='unavailable':
        status=('partial' if leads else 'coverage_gap') if missing else (status if leads else 'coverage_gap')
    return leads,missing,status


def seal_response(response,*,request):
    result=copy.deepcopy(response['result']);result['query_sha256']=query_sha256(request)
    result.pop('snapshot_id',None);result['snapshot_id']='rsnap1_'+core._digest(result)
    return dict(response,result=result)


def build_response(*,profile_response,request,owner):
    validate_request(request);native=_owner(owner)
    core.validate_response(profile_response,expected_request=base_request(request),expected_owner=native)
    profile=copy.deepcopy(profile_response['result']);leads,missing,status=_project(profile,request,owner)
    response=dict(message_type='response',schema_version='2.4.0',request_id=request['request_id'],
        operation='research_context',response_at=profile_response['response_at'],
        result=dict(status=status,profile_result=profile,leads=leads,missing_observation_ids=missing,
            lineage_source_status=owner['lineage_source_status'],lineage_by_observation=copy.deepcopy(owner['lineage_by_observation']),
            formal_evidence_accepted=False,financial_accuracy_proven=False))
    response=seal_response(response,request=request)
    validate_response(response,request=request,owner=owner)
    return response


def validate_response(response,*,request,owner):
    validate_request(request);_shape(response,'response');native=_owner(owner)
    result=response['result'];profile=result['profile_result']
    if (response['request_id']!=request['request_id'] or result['query_sha256']!=query_sha256(request)
        or result['lineage_source_status']!=owner['lineage_source_status']
        or result['lineage_by_observation']!=owner['lineage_by_observation']):
        raise ValueError('research_owner_or_query_mismatch')
    sealed=seal_response(response,request=request)
    if sealed!=response:raise ValueError('research_snapshot_content_mismatch')
    if request['payload']['snapshot_id'] is not None and request['payload']['snapshot_id']!=result['snapshot_id']:
        raise ValueError('research_snapshot_id_mismatch')
    base=base_request(request,profile_snapshot_id=(profile['watermark']['snapshot_id']
        if request['payload']['snapshot_id'] is not None else None))
    packet=dict(message_type='response',schema_version='2.0.0',request_id=request['request_id'],
        operation='get_profiles',response_at=response['response_at'],result=profile)
    core.validate_response(packet,expected_request=base,expected_owner=native)
    leads,missing,status=_project(profile,request,owner)
    if result['leads']!=leads or result['missing_observation_ids']!=missing or result['status']!=status:
        raise ValueError('research_original_projection_mismatch')
    return copy.deepcopy(response)
