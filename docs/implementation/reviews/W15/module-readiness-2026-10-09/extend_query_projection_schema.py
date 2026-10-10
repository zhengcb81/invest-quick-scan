"""One-time private C06 projection schema extension, never touches frozen v1."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
path=ROOT/'runs/c15a/iqs/schemas/quick_scan/query-v2.schema.json'
schema=json.loads(path.read_bytes())
assert 'ObservationProjection' not in schema['$defs']


def obj(properties,required=None):
    return {'type':'object','properties':properties,
            'required':list(properties) if required is None else required,'additionalProperties':False}


text={'type':'string','minLength':1,'maxLength':160}
sha={'type':'string','pattern':'^[a-f0-9]{64}$'}
utc={'type':'string','format':'date-time','pattern':'Z$'}
sequence={'type':'integer','minimum':0}
subject={'$ref':'#/$defs/SubjectRef'}
binding=obj({'protocol':{'const':'stockwiki.observation_subject_binding/1.0.0'},
    'receipt_id':text,'subject_ref':subject,
    'observation_id':{'type':'string','pattern':'^obs_[a-f0-9]{64}$'},
    'payload_sha256':sha,'execution_request_id':text,'execution_attempt_id':text,
    'dispatch_identity_snapshot_sha256':sha,'dispatch_manifest_sha256':sha,
    'recorded_before_send_at':utc})
schema['$defs']['SubjectBinding']=binding
schema['$defs']['ObservationProjection']=obj({
    'observation_id':{'type':'string','pattern':'^obs_[a-f0-9]{64}$'},
    'payload_sha256':sha,'raw_sha256':sha,
    'original_json_base64':{'type':'string','minLength':4,'maxLength':699052},
    'observation_wire_profile':{'const':'stockwiki-portable-observation/1.0.0'},
    'binding_status':{'enum':['bound','legacy_unbound']},
    'subject_binding':{'anyOf':[{'$ref':'#/$defs/SubjectBinding'},{'type':'null'}]},
    'observation_sequence':{'type':'integer','minimum':1},
    'ack_sequence':{'type':'integer','minimum':1},
    'ingest_status':{'enum':['accepted','already_present']},
    'qualification_status':{'enum':['review_pending','independently_checked','rejected','conflict']}})
result=schema['$defs']['Response']['properties']['result']
result['properties']['profiles']['items']['properties']['observations']={
    'type':'array','maxItems':1000,'items':{'$ref':'#/$defs/ObservationProjection'}}
result['properties']['legacy_unbound_observations']={
    'type':'array','maxItems':1000,'items':{'$ref':'#/$defs/ObservationProjection'}}
result['required'].append('legacy_unbound_observations')
result['properties']['status']['enum'].append('unavailable')
watermark=result['properties']['watermark']
watermark['properties'].update({'query_sha256':sha,'snapshot_content_sha256':sha,
    'read_consistency':{'const':'sequential_owner_reads'},
    'source_watermarks':{'type':'array','minItems':1,'maxItems':12,'items':obj({
        'namespace':{'enum':['identity','analysis_subjects','observations','evidence','universe']},
        'schema_version':{'type':['integer','null'],'minimum':0},
        'status':{'enum':['available','missing','schema_unavailable','read_error']},
        'sequence':sequence,'read_at':utc,
        'content_sha256':{'anyOf':[sha,{'type':'null'}]}})}})
watermark['required'].extend(['query_sha256','snapshot_content_sha256','read_consistency','source_watermarks'])
schema['title']='QuickScanQueryV2 private original-observation projection stage'
path.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'private_schema_extended':True,'legacy_schema_unchanged':True,'production_published':False}))
