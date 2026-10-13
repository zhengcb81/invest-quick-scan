"""Receipt-backed field assessment over unchanged original C06 rows.

This pure validator accepts an independently captured OWNER receipt mapping,
never receipts or TTL selected by a query consumer. It does not issue receipts,
authenticate an operator, persist a qualification, or certify financial truth.
The native owner adapter must establish receipt provenance before calling it.
"""
import copy
import re
from datetime import timedelta
from jsonschema import ValidationError
import query_contract as originals
from contract_validation import validate_parsed_answer
from work_contract import parse_utc,freshness_status

LEVELS=('unverified_model_output','execution_verified','screening_audited','formal_research_accepted')
RECEIPT_KEYS={'receipt_id','entity_id','question_id','observation_id','authorized_check_level',
    'issuer','status','receipt_sha256','store_id','payload_sha256','subject_ref','issued_at'}
POLICY_KEYS={'protocol','policy_id','version','fields','valid_from_utc','valid_to_utc','policy_sha256'}


def digest(value):return originals._digest(value)


def validate_policy(value,at_utc):
    now=parse_utc(at_utc)
    if value is None:return None
    if (not isinstance(value,dict) or set(value)!=POLICY_KEYS
        or value['protocol']!='iqs.query_field_policy/1.0.0'
        or not isinstance(value['policy_id'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',value['policy_id'])
        or not isinstance(value['version'],str) or not re.fullmatch(r'\d+\.\d+\.\d+',value['version'])
        or value['policy_sha256']!=digest({k:v for k,v in value.items() if k!='policy_sha256'})):
        raise ValueError('field_policy_invalid')
    if (parse_utc(value['valid_from_utc'])>now
        or (value['valid_to_utc'] is not None and now>=parse_utc(value['valid_to_utc']))):
        raise ValueError('field_policy_not_current')
    fields=value['fields']
    if not isinstance(fields,dict) or not 1<=len(fields)<=2000:raise ValueError('field_policy_fields_invalid')
    for field,row in fields.items():
        if (not isinstance(field,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',field)
            or not isinstance(row,dict) or set(row)!={'ttl_hours','minimum_check_level'}
            or type(row['ttl_hours']) is not int or not 1<=row['ttl_hours']<=87600
            or row['minimum_check_level'] not in LEVELS[1:]):
            raise ValueError('field_policy_fields_invalid')
    return copy.deepcopy(value)


def _bound(row, original_reader=originals._original):
    original=original_reader(row)
    binding=row.get('subject_binding')
    if (not isinstance(binding,dict) or binding.get('observation_id')!=original['observation_id']
        or binding.get('payload_sha256')!=row['payload_sha256']):
        raise ValueError('field_assessment_bound_original_required')
    ref=binding['subject_ref']
    originals._subject_map([ref])
    # Standard originals keep listing authority in the independently captured
    # subject sidecar. Do not demand a listing field forbidden by their schema;
    # an original that actually carries it must still match exactly.
    if (ref['entity_id']!=original['entity_id'] or ref['scope']!=original['scope']
        or any(ref[k]!=original.get(k) for k in ('security_id','segment_id'))
        or ('listing_id' in original and ref['listing_id']!=original['listing_id'])):
        raise ValueError('field_assessment_original_scope_mismatch')
    return original,ref


def _receipt(record,key,row,original,ref,store_id,now):
    if (not isinstance(record,dict) or set(record)!=RECEIPT_KEYS or record['receipt_id']!=key
        or not re.fullmatch(r'RCP_[A-Za-z0-9_.-]+',key)
        or record['receipt_sha256']!=digest({k:v for k,v in record.items() if k!='receipt_sha256'})
        or record['store_id']!=store_id or record['entity_id']!=original['entity_id']
        or record['question_id']!=original['question_id'] or record['observation_id']!=original['observation_id']
        or record['payload_sha256']!=row['payload_sha256'] or record['subject_ref']!=ref
        or record['status'] not in {'active','revoked'}):raise ValueError('field_receipt_binding_invalid')
    level=record['authorized_check_level']
    allowed={'execution_verified':{'stockqa'},'screening_audited':{'iqs','stockwiki'},
        'formal_research_accepted':{'stockwiki','invest-core'}}
    if level not in allowed or record['issuer'] not in allowed[level]:raise ValueError('field_receipt_issuer_invalid')
    if not parse_utc(original['observed_at'])<=parse_utc(record['issued_at'])<=now:
        raise ValueError('field_receipt_time_invalid')
    if record['status']=='active':
        status=original['answer']['status']
        # Fact answers have no numeric score. The scoring contract's unknown
        # null branch validates their receipt without inventing a score.
        parsed=dict(question_id=original['question_id'],status='unknown' if status=='answered' else status,
            score=original['answer']['score'],description='Original C06 field assessment',
            check_level=level,check_level_receipt_id=key)
        validate_parsed_answer(parsed,trusted_check_level_receipts={key:record},
            expected_entity_id=original['entity_id'],expected_observation_id=original['observation_id'])
    return record


def _assess(rows,*,store_id,at_utc,trusted_check_level_receipts,field_policy,bound_original):
    """Independent grade and information-age TTL; no upgrade of raw originals."""
    try:
        now=parse_utc(at_utc);policy=validate_policy(field_policy,at_utc)
        if (not isinstance(store_id,str) or not store_id or not isinstance(rows,list) or len(rows)>5000
            or not isinstance(trusted_check_level_receipts,dict)):
            raise ValueError('field_assessment_inputs_invalid')
        records={};by_id={}
        for row in rows:
            original,ref=bound_original(row);oid=original['observation_id']
            if oid in by_id:raise ValueError('field_assessment_duplicate_original')
            if parse_utc(original['observed_at'])>now:raise ValueError('field_assessment_future_original')
            by_id[oid]=(row,original,ref)
        for key,record in trusted_check_level_receipts.items():
            if not isinstance(record,dict) or record.get('observation_id') not in by_id:
                raise ValueError('field_receipt_unrequested_original')
            row,original,ref=by_id[record['observation_id']]
            checked=_receipt(record,key,row,original,ref,store_id,now)
            records.setdefault(original['observation_id'],[]).append(checked)
        result={}
        for oid,(row,original,ref) in by_id.items():
            candidates=records.get(oid,[])
            # A revoked record cannot be bypassed with another active receipt.
            # The native owner must explicitly select its current event state.
            if len(candidates)>1:raise ValueError('field_receipt_current_state_ambiguous')
            record=candidates[0] if candidates else None
            active=record is not None and record['status']=='active'
            level=record['authorized_check_level'] if active else LEVELS[0]
            fid=original['field_id'];settings=(policy or {}).get('fields',{}).get(fid)
            info=original['answer'].get('information_as_of');until=None
            validity='policy_unavailable' if policy is None else 'field_policy_missing'
            if settings is not None:
                if info is not None:
                    stamp=info if 'T' in info else info+'T00:00:00Z'
                    start=min(parse_utc(stamp),parse_utc(original['observed_at']))
                    until=(start+timedelta(hours=settings['ttl_hours'])).isoformat().replace('+00:00','Z')
                validity=freshness_status(dict(information_as_of=info,valid_until=until),at_utc)
            minimum=settings['minimum_check_level'] if settings is not None else None
            enough=minimum is not None and LEVELS.index(level)>=LEVELS.index(minimum)
            usable=row['qualification_status'] not in {'rejected','conflict'}
            result[oid]=dict(payload_sha256=row['payload_sha256'],subject_ref=copy.deepcopy(ref),
                field_id=fid,question_id=original['question_id'],information_as_of=info,valid_until=until,
                validity_status=validity,minimum_check_level=minimum,check_level=level,
                check_level_receipt_id=record['receipt_id'] if active else None,
                qualification_status='verified' if active else 'revoked' if record else 'receipt_missing',
                screening_eligible=usable and enough and validity=='fresh' and original['answer']['status']=='scored')
        body=dict(protocol='iqs.query_field_assessment/1.0.0',store_id=store_id,assessed_at=at_utc,
            field_policy_sha256=policy['policy_sha256'] if policy else None,observations=result,
            financial_accuracy_proven=False,formal_research_accepted=False,API_requests=0,database_writes=0)
        return dict(body,assessment_sha256=digest(body))
    except (KeyError,TypeError,ValidationError,OverflowError,RecursionError) as exc:
        raise ValueError('field_assessment_invalid') from exc


def assess_originals(rows,*,store_id,at_utc,trusted_check_level_receipts,field_policy):
    return _assess(rows,store_id=store_id,at_utc=at_utc,trusted_check_level_receipts=trusted_check_level_receipts,
        field_policy=field_policy,bound_original=_bound)


def assess_vendor_originals(rows,*,store_id,at_utc,trusted_check_level_receipts,field_policy):
    import query_vendor_contract as vendor
    return _assess(rows,store_id=store_id,at_utc=at_utc,
        trusted_check_level_receipts=trusted_check_level_receipts,field_policy=field_policy,
        bound_original=lambda row:_bound(row, vendor._original))


def _pool_original(value):
    # Only the trusted native owner obtains these metadata from exact original
    # bytes and binding in one readonly transaction. Never a consumer request.
    keys={'observation_id','payload_sha256','subject_ref','field_id','question_id','observed_at',
        'status','score','information_as_of','qualification_status'}
    if not isinstance(value,dict) or set(value)!=keys:raise ValueError('field_pool_input_invalid')
    ref=value['subject_ref'];originals._subject_map([ref])
    if (not re.fullmatch('obs_[a-f0-9]{64}',value['observation_id'])
        or not re.fullmatch('[a-f0-9]{64}',value['payload_sha256'])
        or any(not isinstance(value[k],str) or not 1<=len(value[k])<=160 for k in ('field_id','question_id','status'))
        or (value['status']=='scored' and (type(value['score']) is not int or not 1<=value['score']<=10))
        or (value['status']!='scored' and value['score'] is not None)):
        raise ValueError('field_pool_input_invalid')
    parse_utc(value['observed_at'])
    original=dict(observation_id=value['observation_id'],entity_id=ref['entity_id'],
        question_id=value['question_id'],field_id=value['field_id'],observed_at=value['observed_at'],
        answer=dict(status=value['status'],score=value['score'],information_as_of=value['information_as_of']))
    return original,ref


def assess_pool_inputs(inputs,*,store_id,at_utc,trusted_check_level_receipts,field_policy):
    """Same C03/C04 algorithms; native exact-byte metadata, no answer copies."""
    return _assess(inputs,store_id=store_id,at_utc=at_utc,trusted_check_level_receipts=trusted_check_level_receipts,
        field_policy=field_policy,bound_original=_pool_original)
