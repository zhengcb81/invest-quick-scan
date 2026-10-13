"""Explicit query2.6 dialect, reuses old scope/watermark/content checks."""
import copy,json,base64
from jsonschema import Draft202012Validator,FormatChecker
import query_contract as base
import observation_profiles as profiles
SCHEMA=json.loads((base.ROOT/'schemas/quick_scan/query-v2.6.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())

def shape(value,kind):return base._validate_shape(value,kind,validator=VALIDATOR)
def validate_request(value):
    shape(value,'request');base._subject_map(value['payload']['subject_refs']);base._utc(value['requested_at'])
    if value['payload']['information_cutoff']>base._utc(value['requested_at']).date().isoformat():
        raise ValueError('query_future_information_cutoff')
    return copy.deepcopy(value)
def _original(row):
    # First decode is bounded, then base reader authenticates bytes/hash and parses strict JSON.
    if not isinstance(row.get('original_json_base64'),str) or len(row['original_json_base64'])>4*((base.MAX_OBSERVATION_BYTES+2)//3):raise ValueError('query_original_bytes_mismatch')
    raw=base64.b64decode(row['original_json_base64'],validate=True)
    if len(raw)>base.MAX_OBSERVATION_BYTES:raise ValueError('query_original_bytes_mismatch')
    header=json.loads(raw.decode('utf-8'),object_pairs_hook=base.module_contract._unique_object)
    if header.get('schema_version')=='1.1.0':
        if row.get('observation_wire_profile')!='stockwiki-portable-observation/1.0.0':raise ValueError('query_original_wire_profile_mismatch')
        return base._original(row)
    if header.get('schema_version')!='1.2.0':raise ValueError('query_observation_profile_unavailable')
    if row.get('observation_wire_profile')!='stockwiki-portable-observation/1.1.0':raise ValueError('query_original_wire_profile_mismatch')
    resources={path:profiles._read(path) for path in profiles._BASE_RESOURCES}
    schema=profiles.schema_for('1.2.0',resources)
    schema['$id']='urn:iqs:stockwiki-portable-observation:1.2'
    schema['properties']['entity_id']={'type':'string','minLength':1,'maxLength':160}
    validator=Draft202012Validator(schema,registry=base.ANSWER_REGISTRY,format_checker=FormatChecker())
    return base._original(row,validator=validator)
def validate_response(value,*,expected_request,expected_owner):
    return base._validate_response(value,expected_request=expected_request,expected_owner=expected_owner,
        request_validator=validate_request,shape_validator=shape,original_reader=_original)
query_sha256=base.query_sha256
seal_response=base.seal_response
