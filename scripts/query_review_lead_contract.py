"""Pure named review intake validation; claims are never verified identity."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
import query_contract as core
import module_contract

SCHEMA=json.loads((Path(__file__).resolve().parents[1]/'schemas/quick_scan/query-review-lead.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
MAX_BYTES=64*1024


def _shape(value,kind):
    try:
        if len(module_contract.canonical_bytes(value))>MAX_BYTES:raise ValueError('review_lead_too_large')
        VALIDATOR.validate(value)
        if value['message_type']!=kind:raise ValueError('review_lead_message_type')
    except (ValidationError,TypeError,ValueError,RecursionError) as exc:
        raise ValueError('review_lead_document_invalid') from exc


def _strings(value):
    if isinstance(value,str) and not value.strip():raise ValueError('review_lead_blank_field')
    if isinstance(value,dict):
        for item in value.values():_strings(item)
    elif isinstance(value,list):
        for item in value:_strings(item)


def validate_request(value):
    _shape(value,'request');_strings(value);core._utc(value['requested_at'])
    return copy.deepcopy(value)


def claim(request):
    validate_request(request)
    return dict(consumer_id=request['consumer_id'],operation=request['operation'],payload=copy.deepcopy(request['payload']))


def claim_sha256(request):return core._digest(claim(request))


def validate_response(response,*,request,owner):
    validate_request(request);_shape(response,'response')
    if (set(owner)!={'store_id','intake_id','claim_sha256','recorded_at','owner_principal_bound'}
        or type(owner['intake_id']) is not int or owner['owner_principal_bound'] is not True):
        raise ValueError('review_lead_independent_owner_required')
    result=response['result'];payload=request['payload']
    if (response['request_id']!=request['request_id'] or response['operation']!=request['operation']
        or result['claim_sha256']!=claim_sha256(request)
        or any(result[key]!=value for key,value in owner.items())):
        raise ValueError('review_lead_owner_reference_mismatch')
    if request['operation']=='nominate':
        if result['nomination_id']!=payload['nomination_id'] or result['candidate_id']!='nomination:'+str(owner['intake_id']):
            raise ValueError('review_lead_nomination_mismatch')
    elif result['conflict_id']!=payload['conflict_id'] or result['entity_ids']!=payload['entity_ids']:
        raise ValueError('review_lead_conflict_mismatch')
    if (core._utc(response['response_at'])<core._utc(request['requested_at'])
        or core._utc(response['response_at'])<core._utc(result['recorded_at'])):
        raise ValueError('review_lead_time_mismatch')
    return copy.deepcopy(response)
