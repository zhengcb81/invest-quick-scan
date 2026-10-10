"""Private two-phase dispatch contract, reusing the query/answer validators."""
import copy
import base64
import hashlib
import re

import query_contract as qc
import module_contract

PROTOCOL='stockwiki.subject_dispatch_request/1.0.0'
FIELDS={'protocol','subject_ref','work_item_id','work_request_id','execution_attempt_id',
        'provider','model_requested','identity_revision','question_id','field_id',
        'information_cutoff','dispatch_identity_snapshot_sha256','dispatch_manifest_sha256',
        'dispatch_prompt_sha256','question_definition_sha256','question_semantic_sha256','question_contract',
        'module_package_id','module_release_id','question_version','template_version','method_id'}
HASHES={'dispatch_identity_snapshot_sha256','dispatch_manifest_sha256','dispatch_prompt_sha256',
        'question_definition_sha256','question_semantic_sha256'}


def digest(value):
    return hashlib.sha256(module_contract.canonical_bytes(value)).hexdigest()


def query_request(dispatch,now):
    return {'message_type':'request','schema_version':'2.0.0','request_id':dispatch['work_request_id'],
            # Internal semantic-validation envelope only; no query is sent.
            'consumer_id':'invest-quick-scan','operation':'get_profiles','requested_at':now,
            'payload':{'subject_refs':[dispatch['subject_ref']],'field_ids':[dispatch['field_id']],
                'information_cutoff':dispatch['information_cutoff'],'include_history':True,
                'model_filter':None,'snapshot_id':None}}


def validate_dispatch_request(value,*,registered_at):
    if (not isinstance(value,dict) or set(value)!=FIELDS or value['protocol']!=PROTOCOL
        or len(module_contract.canonical_bytes(value))>128*1024):
        raise ValueError('subject_dispatch_request_invalid')
    for field in HASHES:
        if not isinstance(value[field],str) or re.fullmatch('[a-f0-9]{64}',value[field]) is None:
            raise ValueError('subject_dispatch_hash_invalid')
    for field in FIELDS-HASHES-{'protocol','subject_ref','identity_revision','question_contract'}:
        if not isinstance(value[field],str) or not value[field].strip() or len(value[field])>160:
            raise ValueError('subject_dispatch_string_invalid')
    if type(value['identity_revision']) is not int or value['identity_revision']<1:
        raise ValueError('subject_dispatch_revision_invalid')
    question=value['question_contract']
    if (not isinstance(question,dict) or question.get('id')!=value['question_id']
        or question.get('response_kind') not in {'score','fact'}):
        raise ValueError('subject_dispatch_question_contract_invalid')
    qc.validate_request(query_request(value,registered_at))
    return copy.deepcopy(value)


def validate_receipt(receipt,*,store_id):
    if (not isinstance(receipt,dict) or set(receipt)!={'protocol','receipt_id','store_id',
        'dispatch_request','request_sha256','registered_at'}
        or receipt['protocol']!='stockwiki.subject_dispatch_receipt/1.0.0'
        or receipt['store_id']!=store_id):
        raise ValueError('subject_dispatch_receipt_invalid')
    validate_dispatch_request(receipt['dispatch_request'],registered_at=receipt['registered_at'])
    if (receipt['request_sha256']!=digest(receipt['dispatch_request'])
        or receipt['receipt_id']!='sdr_'+digest({k:v for k,v in receipt.items() if k!='receipt_id'})):
        raise ValueError('subject_dispatch_receipt_hash_invalid')
    return copy.deepcopy(receipt)


def bind_original(receipt,observation,*,payload_sha256,observation_sequence,ack_sequence,bound_at):
    """Post-answer binding references a real PREVIOUS owner registration."""
    d=receipt['dispatch_request']
    raw=module_contract.canonical_bytes(observation)
    original=qc._original({'original_json_base64':base64.b64encode(raw).decode('ascii'),
        'raw_sha256':hashlib.sha256(raw).hexdigest(),'payload_sha256':payload_sha256,
        'observation_id':observation['observation_id']})
    execution=original['execution']
    ref=d['subject_ref']
    if (any(original.get(k)!=ref[k] for k in ('entity_id','security_id','segment_id','scope'))
        # Standard1.1 has no identity_revision/listing/analysis_subject fields.
        # Those remain independent PRE-dispatch owner facts, never backfilled
        # into the original or demanded from a schema that forbids them.
        or any(original.get(k)!=d[k] for k in ('question_id','field_id',
              'information_cutoff','question_definition_sha256','question_semantic_sha256',
              'module_package_id','module_release_id','question_version','template_version','method_id'))
        or any(execution[k]!=d[k] for k in ('provider','model_requested'))
        or execution['attempt_id']!=d['execution_attempt_id']
        or execution['prompt_sha256']!=d['dispatch_prompt_sha256']):
        raise ValueError('subject_dispatch_original_mismatch')
    binding={'protocol':'stockwiki.observation_subject_binding/1.0.0',
        'subject_ref':copy.deepcopy(ref),'observation_id':original['observation_id'],
        'payload_sha256':payload_sha256,'execution_request_id':execution['request_id'],
        'execution_attempt_id':execution['attempt_id'],
        'dispatch_identity_snapshot_sha256':d['dispatch_identity_snapshot_sha256'],
        'dispatch_manifest_sha256':d['dispatch_manifest_sha256'],
        'recorded_before_send_at':receipt['registered_at']}
    # This binding ID is produced AFTER the response. The event referenced by
    # recorded_before_send_at is the distinct immutable dispatch receipt.
    binding['receipt_id']='sbr_'+digest({'dispatch_receipt_id':receipt['receipt_id'],
        'dispatch_receipt_sha256':digest(receipt),'binding':binding})
    qc._validate_original_semantics(original,row={'binding_status':'bound','subject_binding':binding,
        'payload_sha256':payload_sha256,
        'observation_sequence':observation_sequence,'ack_sequence':ack_sequence},
        owner_ref={'question_contract':d['question_contract']},request=query_request(d,bound_at),
        watermark={'read_at':bound_at,'observation_sequence':observation_sequence,'ack_sequence':ack_sequence},
        subject_ref=ref)
    return binding
