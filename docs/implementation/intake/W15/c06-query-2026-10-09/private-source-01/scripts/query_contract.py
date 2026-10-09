"""Private C06 v2 get_profiles boundary; production capability is not published."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import module_contract

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/'schemas/quick_scan/query-v2.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
MAX_INPUT_BYTES=8*1024*1024


def _validate_shape(value,kind):
    try:
        module_contract.canonical_bytes(value)
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


def validate_response(value,*,expected_request,expected_owner):
    validate_request(expected_request)
    _validate_shape(value,'response')
    if not isinstance(expected_owner,dict) or set(expected_owner)!={'store_id'} or not isinstance(expected_owner['store_id'],str) or not expected_owner['store_id'].strip():
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
    # Current private stage permits no observation output, so it cannot claim
    # covered fields or a successful scoring result without actual lineage.
    if covered or coverage['scores_available'] or coverage['facts_available'] or result['status']=='ok':
        raise ValueError('query_observation_projection_pending')
