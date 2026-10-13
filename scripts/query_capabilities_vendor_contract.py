"""Capabilities1.2 adds explicit execution support, never financial coverage."""
import copy,json
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
import query_capabilities_contract as base
import observation_profiles
from module_contract import canonical_bytes
SCHEMA=json.loads((base.scoped.raw.ROOT/'schemas/quick_scan/query-capabilities-v1.2.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())

def _shape(value):
    try:VALIDATOR.validate(value)
    except (ValidationError,TypeError,KeyError) as error:raise ValueError('capabilities_document_invalid') from error

def validate_request(request):
    _shape(request)
    if request.get('message_type')!='request':raise ValueError('capabilities_request_required')
    # Exactly the legacy selectors and owner-only context checks, with a named envelope version.
    legacy=copy.deepcopy(request);legacy['schema_version']='1.1.0';base.validate_request(legacy)
    if len(canonical_bytes(request))>base.MAX_BYTES:raise ValueError('capabilities_request_too_large')
    return copy.deepcopy(request)

def _result(request,source_context,index,scope_context):
    result=base._result(request,source_context,index,scope_context)
    wires=result['supported_query_wires']+[dict(schema_version='2.6.0',operations=['get_profiles'])]
    result['supported_query_wires']=wires
    requirement=result['capability_requirements'];supported={row['schema_version'] for row in wires}
    requirement['missing_query_versions']=[v for v in request['payload']['required_query_versions'] if v not in supported]
    requirement['status']='missing' if any(v for k,v in requirement.items() if k.startswith('missing_')) else 'satisfied'
    result.update(execution_profiles=[observation_profiles.profile_descriptor()],
        supported_subject_dispatch_versions=['1.0.0','1.1.0','1.2.0'],supported_subject_binding_versions=['1.0.0','1.1.0'])
    return result

def build_response(*,request,source_context,index,scope_context):
    validate_request(request)
    response=dict(protocol='stockwiki.c06_query_capabilities/1.2.0',schema_version='1.2.0',message_type='response',operation='capabilities',
        request_id=request['request_id'],response_at=source_context['read_at'],result=_result(request,source_context,index,scope_context))
    return validate_response(response=response,request=request,source_context=source_context,index=index,scope_context=scope_context)

def validate_response(*,response,request,source_context,index,scope_context):
    validate_request(request);_shape(response)
    if (response['message_type']!='response' or response['request_id']!=request['request_id']
        or base.profiles._utc(response['response_at'])<base.profiles._utc(source_context['read_at'])
        or canonical_bytes(response['result'])!=canonical_bytes(_result(request,source_context,index,scope_context))):
        raise ValueError('capabilities_response_owner_mismatch')
    if len(canonical_bytes(response))>base.MAX_BYTES:raise ValueError('capabilities_response_too_large')
    return copy.deepcopy(response)
