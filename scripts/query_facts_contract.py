"""Native IQS contract for the F05 facts wire 2.7.0 (stockwiki.c06_facts_query/1.0.0).

The frozen StockWiki F05 candidate (owner commit 63a6ffcf) declares this wire
and calls the four `facts-*` operations of the public query contract CLI.
Schema and semantics are the frozen owner declaration, not an IQS invention:
the schema file is a byte copy of the owner schema (SHA-256 pinned in tests)
and the projection below follows the frozen wire item by item.

Strict/explore split, frozen status vocabulary, direction convention,
period/quality/evidence gates and the no_cross_fact_join policy all come from
that wire; an unknown protocol state never reads as "no facts". The base
profile rows are validated natively (original hashes, ACK, subject binding,
answer semantics) before projection; no second fact store, no network, no
owner store access.
"""
import base64
import copy
import json
import math
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import query_contract as core
import module_contract

SCHEMA=json.loads((Path(__file__).resolve().parents[1]/'schemas/quick_scan/query-facts-v2.7.schema.json').read_bytes())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
PROTOCOL='stockwiki.c06_facts_query/1.0.0'
EXPORT_PROTOCOL='stockwiki.c06_facts_export/1.0.0'
WIRE_VERSION='2.7.0'
DIRECTION_CONVENTION_VERSION='stockwiki.facts_direction_convention/1.0.0'
CAPABILITIES_PROTOCOL='iqs.facts_contract_capabilities/1.0.0'
CAPABILITIES_FEATURES=('full_response_validation_v1',
    'paged_response_projection_v1','export_response_validation_v1')
MAX_BYTES=16*1024*1024
MAX_OBSERVATION_BYTES=512*1024
PAGE_SIZE_DEFAULT=50
PAGE_SIZE_MAX=100
FACTS_MAX=5000
CONFIDENCE_RANK={'low':1,'medium':2,'high':3}
# Declared (relation, role) -> direction, frozen by the owner wire. Anything
# outside the table resolves to `unresolved` and can never enter a strict
# from/to result; the `uses` family stays incoming so an equipment user can
# never read as a supplier.
DIRECTION_CONVENTION={
    'sells_to':{'outgoing':{'customer','channel'}},
    'supplies':{'outgoing':{'customer','channel'}},
    'supplies_to':{'outgoing':{'customer','channel'}},
    'provides':{'outgoing':{'customer','channel'}},
    'serves':{'outgoing':{'customer','industry','user'}},
    'sells':{'outgoing':{'customer','channel','industry','user','other'}},
    'buys_equipment_from':{'incoming':{'supplier','producer'}},
    'buys_input_from':{'incoming':{'supplier','producer'}},
    'procures_from':{'incoming':{'supplier','producer'}},
    'uses_equipment':{'incoming':{'supplier','producer'}},
    'uses_input':{'incoming':{'supplier','producer'}},
    'competes_with':{'symmetric':{'peer','other'}},
    'denies_supply_to':{'denial':{'customer','channel','other'}},
    'denies_partnership_with':{'denial':{'peer','other'}},
}


def _digest(value):
    return module_contract.digest(value)


def _fail(code):
    raise ValueError(code)


def capabilities():
    """Public semantic features of this facts contract implementation."""
    return {'protocol':CAPABILITIES_PROTOCOL,'wire_version':WIRE_VERSION,
        'features':list(CAPABILITIES_FEATURES)}


def _shape(value,kind):
    try:
        if len(module_contract.canonical_bytes(value))>MAX_BYTES:
            _fail('facts_document_too_large')
        VALIDATOR.validate(value)
    except (ValidationError,TypeError,ValueError,KeyError,RecursionError) as error:
        raise ValueError('facts_document_invalid') from error
    if value['message_type']!=kind:
        _fail('facts_message_type_invalid')


def validate_envelope(value):
    """Public schema validation for any facts wire document (request or response)."""
    _shape(value,value.get('message_type','request'))
    return value


def materialize(request,*,information_cutoff=None):
    """Bind the effective information cutoff once, before hashing.

    A missing cutoff defaults to the query date (requested_at); the value is
    materialized ONCE and travels in the request, the hash and the watermark,
    so a replay with the same snapshot reproduces the identical query identity.
    """
    body=copy.deepcopy(request)
    if body['payload']['information_cutoff'] is None:
        body['payload']['information_cutoff']=information_cutoff or body['requested_at'][:10]
    return body


def _materialize_for_response(request,response):
    """Use the stored cutoff when a snapshot replay omits it in the request."""
    payload=request['payload']
    if payload['information_cutoff'] is None and payload['snapshot_id'] is not None:
        cutoff=response['result']['watermark']['information_cutoff']
        return materialize(request,information_cutoff=cutoff)
    return materialize(request)


def normalize_payload(request):
    """Hash echo: snapshot id, paging and label never split one snapshot.

    The snapshot stores the FULL ordered row set; page_size/cursor only slice
    it, so they are presentation, not query identity. The first page omitted
    and an explicit page are the same query.
    """
    payload=copy.deepcopy(materialize(request)['payload'])
    payload.pop('snapshot_id',None)
    payload.pop('page',None)
    return payload


def validate_request(request):
    _shape(request,'request')
    payload=request['payload']
    period=payload['period']
    if period is not None and 'start' in period and period['start']>period['end']:
        _fail('facts_period_reversed')
    if payload['mode']=='strict':
        if payload['direction'] is None:
            _fail('facts_direction_required_in_strict')
        if payload['evidence']!='require_resolved':
            _fail('facts_evidence_any_invalid_in_strict')
    if request['operation']=='export_facts' and not request.get('label'):
        _fail('facts_export_label_required')
    if (payload['page'] is not None and payload['page']['cursor'] is not None
        and payload['snapshot_id'] is None):
        _fail('facts_cursor_requires_snapshot')
    if (payload['information_cutoff'] is not None
        and payload['information_cutoff']>request['requested_at'][:10]):
        _fail('facts_future_information_cutoff')
    if len(module_contract.canonical_bytes(request))>MAX_BYTES:
        _fail('facts_request_too_large')
    return copy.deepcopy(request)


def query_sha256(request):
    validate_request(request)
    semantic=dict(consumer_id=request['consumer_id'],schema_version=WIRE_VERSION,
        operation='query_facts',payload=normalize_payload(request))
    return _digest(semantic)


def resolve_direction(relation,role):
    entry=DIRECTION_CONVENTION.get(relation)
    if entry is None:
        return 'unresolved'
    for direction,roles in entry.items():
        if role in roles:
            return direction
    return 'unresolved'


def _fact_id(observation_id,item_index):
    return 'fact_'+_digest({'observation_id':observation_id,'item_index':item_index})[:24]


def _hit_paths(item,payload):
    paths=[]
    counterparty=payload.get('counterparty') or {}
    text=counterparty.get('text')
    if text:
        needle=text.casefold()
        if needle in item['name'].casefold():
            paths.append({'attribute':'counterparty_name','value':item['name']})
        for alias in item.get('aliases') or []:
            if needle in alias.casefold():
                paths.append({'attribute':'counterparty_alias','value':alias})
        canonical=item.get('canonical_entity_id')
        if canonical and needle in canonical.casefold():
            paths.append({'attribute':'counterparty_entity_id','value':canonical})
        if item.get('segment') and needle in item['segment'].casefold():
            paths.append({'attribute':'item_segment','value':item['segment']})
        if item.get('description') and needle in item['description'].casefold():
            paths.append({'attribute':'item_description','value':item['description']})
        if needle in item['relation'].casefold():
            paths.append({'attribute':'relation','value':item['relation']})
    if payload.get('relation_types') and item['relation'] in payload['relation_types']:
        paths.append({'attribute':'relation','value':item['relation']})
    wanted=counterparty.get('entity_ids')
    canonical=item.get('canonical_entity_id')
    if wanted and canonical and canonical in wanted:
        paths.append({'attribute':'counterparty_entity_id','value':canonical})
    return paths


def _period_view(payload):
    period=payload['period']
    if period is not None and 'as_of' in period:
        return 'as_of',period['as_of']
    if period is not None:
        return 'range',(period['start'],period['end'])
    return 'as_of',payload['information_cutoff']


def _apply_period(row,payload):
    """Set period_qualification; None means the row does not match the window."""
    kind,window=_period_view(payload)
    valid_from,valid_to=row['valid_from'],row['valid_to']
    if valid_from is None and valid_to is None:
        row['period_qualification']='period_unknown'
        return 'period_unknown'
    if kind=='range':
        start,end=window
        if (valid_from is None or valid_from<=end) and (valid_to is None or valid_to>=start):
            row['period_qualification']='overlaps_requested_period'
            return 'ok'
        return None
    as_of=window
    if valid_from is not None and valid_from>as_of:
        return None
    if valid_to is not None and valid_to<as_of:
        row['period_qualification']='expired'
        return 'expired'
    row['period_qualification']='active_at_as_of'
    return 'ok'


def _matches_filters(row,payload):
    if payload['relation_types'] and row['relation'] not in payload['relation_types']:
        return None
    if payload['direction'] is not None and row['direction']!=payload['direction']:
        return None
    if payload['commercial_stages'] and row['commercial_stage'] not in payload['commercial_stages']:
        return None
    counterparty=payload.get('counterparty')
    if counterparty:
        if counterparty.get('text') and not row['hit_paths']:
            return None
        wanted=counterparty.get('entity_ids')
        if wanted and row['counterparty']['canonical_entity_id'] not in wanted:
            return None
    return _apply_period(row,payload)


def _quality_context(row):
    # Fixed quality context of the frozen wire: answered, fresh, unverified
    # model output with no minimum check level and no comparability binding.
    def entry(value):
        return {'value':value,'status':'answered','fresh':True,
            'check_level':'unverified_model_output','minimum_check_level':None,
            'comparability_scope':None}
    return {'confidence_rank':entry(row['confidence_rank']),
        'evidence_count':entry(len(row['evidence_ids'])),
        'observation_sequence':entry(row['observation_sequence'])}


def _compare(op,actual,threshold):
    if op=='>':return actual>threshold
    if op=='>=':return actual>=threshold
    if op=='<':return actual<threshold
    if op=='<=':return actual<=threshold
    if op=='==':return actual==threshold
    return actual!=threshold


def _quality_leaf(leaf,context):
    """One leaf of the frozen quality evaluator over its fixed context.

    Reproduces the owner rules engine exactly for the schema-allowed domain
    (integer thresholds, six operators, the three declared fields): unknown on
    a null/non-numeric value, native comparison otherwise; explanations carry
    field/op/threshold/outcome/actual/reason.
    """
    entry=context.get(leaf['field'])
    base={'field':leaf['field'],'op':leaf['op'],'threshold':leaf['value'],
        'critical_risk_gate':False}
    actual=entry.get('value') if isinstance(entry,dict) else None
    if actual is None:
        base.update(outcome='unknown',actual=None,reason='value_null')
        return base
    if isinstance(actual,bool) or not isinstance(actual,(int,float)):
        base.update(outcome='unknown',actual=actual,reason='value_not_numeric')
        return base
    if isinstance(actual,float) and not math.isfinite(actual):
        base.update(outcome='unknown',actual=None,reason='value_not_numeric',
            detail='non-finite')
        return base
    base.update(outcome='pass' if _compare(leaf['op'],actual,leaf['value']) else 'fail',
        actual=actual,reason='compared')
    return base


def _fold(combine,outcomes):
    if combine=='all':
        return 'fail' if 'fail' in outcomes else 'unknown' if 'unknown' in outcomes else 'pass'
    return 'pass' if 'pass' in outcomes else 'unknown' if 'unknown' in outcomes else 'fail'


def _quality_outcome(row,conditions):
    if conditions is None:
        return 'not_requested',[]
    context=_quality_context(row)
    try:
        explanations=[_quality_leaf(leaf,context) for leaf in conditions['leaves']]
        outcome=_fold(conditions['combine'],[leaf['outcome'] for leaf in explanations])
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError('facts_quality_condition_invalid') from error
    return outcome,explanations


def _strict_gate(row,payload,evidence_map):
    """First failed gate wins; only filter-passing rows reach this check."""
    if row['binding_status']!='bound':
        return 'unverified_provenance'
    if row['qualification_status'] in {'rejected','conflict'}:
        return 'qualification_'+row['qualification_status']
    if row['answer_status']!='answered':
        return 'answer_status_'+str(row['answer_status'])
    if row['direction']=='unresolved':
        return 'unknown_direction'
    if row['commercial_stage']=='unknown':
        return 'unknown_commercial_stage'
    if row['period_qualification']=='period_unknown':
        return 'period_unknown'
    if row['period_qualification']=='expired':
        return 'expired'
    if payload['evidence']=='require_resolved' and (
        not row['evidence_ids'] or any(eid not in evidence_map for eid in row['evidence_ids'])
    ):
        return 'evidence_unresolved'
    if row['evidence_review_status']!='reviewed':
        return 'evidence_unreviewed'
    return 'strict'


def _assertion_group(row):
    counterparty=row['counterparty']
    key=counterparty['canonical_entity_id'] or counterparty['name'].casefold()
    ref=row['subject_ref']
    return (ref['entity_id'],ref['scope'],ref['scope_id'],row['field_id'],
        row['relation'],row['role'],key)


def _mark_assertions(rows):
    """Newest-cutoff assertion wins per group; same-cutoff divergence conflicts.

    Owner profiles convention: inside one comparable group rows at the newest
    information_cutoff are candidates for current; ties resolve by
    (observed_at, sequence, observation_id) and older cutoffs are superseded
    history. When the newest-cutoff rows disagree on the declared claim, the
    owner answered the same information date two ways and nothing in the group
    can be a strict fact until review resolves it.
    """
    groups={}
    for row in rows:
        groups.setdefault(_assertion_group(row),[]).append(row)
    for members in groups.values():
        newest_cutoff=max(row['information_cutoff'] for row in members)
        current_generation=[row for row in members
            if row['information_cutoff']==newest_cutoff]
        claims={row['_claim'] for row in current_generation}
        if len(claims)>1:
            for row in members:
                row['status_detail']='assertion_conflict_pending_review'
            continue
        current=max(current_generation,
            key=lambda row:(_stamp_order(row),row['observation_id']))
        for row in members:
            if row is not current:
                row['status_detail']='superseded'


def _stamp_order(row):
    return (row['observed_at'],row['observation_sequence'])


def project_fact_rows(profile_result,payload):
    """Project sealed fact answers into filtered, gated, stably ordered rows.

    Returns ``(rows, stats)``; ``stats['fact_observations']`` counts fact-kind
    originals seen before filtering so coverage_gap and empty stay distinct.
    """
    rows=[]
    stats={'fact_observations':0}
    for profile in profile_result['profiles']:
        for record in profile['observations']:
            obs=core.original_observation(record)
            answer=obs['answer']
            if answer.get('response_kind')!='fact':
                continue
            stats['fact_observations']+=1
            if record['binding_status']!='bound':
                # A legacy unbound answer cannot carry a fact row past the
                # native seal (no dispatch question contract); refuse loudly.
                _fail('facts_legacy_unbound_answer')
            evidence_map={entry['id']:entry for entry in answer.get('evidence') or []}
            for index,item in enumerate(answer.get('items') or []):
                evidence_refs=[
                    {'id':evidence_map[eid]['id'],'title':evidence_map[eid]['title'],
                     'url':evidence_map[eid]['url'],
                     'published_at':evidence_map[eid].get('published_at')}
                    for eid in item.get('evidence_ids') or [] if eid in evidence_map]
                ref=profile['subject_ref']
                direction=resolve_direction(item['relation'],item['role'])
                rows.append({
                    'fact_id':_fact_id(obs['observation_id'],index),
                    'qualification':'candidate',
                    'status_detail':'strict',
                    'subject_ref':{'entity_id':ref['entity_id'],'scope':ref['scope'],
                        'scope_id':ref['scope_id'],'security_id':ref.get('security_id'),
                        'listing_id':ref.get('listing_id'),'segment_id':ref.get('segment_id')},
                    'canonical_name':profile['canonical_name'],
                    'matched_listings':copy.deepcopy(profile.get('matched_listings') or []),
                    'observation_id':obs['observation_id'],
                    'payload_sha256':record['payload_sha256'],
                    'observation_sequence':record['observation_sequence'],
                    'ack_sequence':record['ack_sequence'],
                    'binding_status':record['binding_status'],
                    'qualification_status':record['qualification_status'],
                    'field_id':obs['field_id'],
                    'question_id':obs['question_id'],
                    'answer_status':answer['status'],
                    'information_cutoff':obs['information_cutoff'],
                    'observed_at':obs['observed_at'],
                    'item_index':index,
                    'counterparty':{'name':item['name'],
                        'canonical_entity_id':item.get('canonical_entity_id'),
                        'aliases':list(item.get('aliases') or [])},
                    'relation':item['relation'],
                    'role':item['role'],
                    'direction':direction,
                    'direction_convention_version':DIRECTION_CONVENTION_VERSION,
                    'commercial_stage':item['commercial_stage'],
                    'valid_from':item.get('valid_from'),
                    'valid_to':item.get('valid_to'),
                    'period_qualification':'period_unknown',
                    'answer_period':{'start':answer.get('period_start'),
                        'end':answer.get('period_end'),'basis':answer.get('basis'),
                        'information_as_of':answer.get('information_as_of')},
                    'item_segment':item.get('segment'),
                    'evidence_ids':list(item.get('evidence_ids') or []),
                    'evidence':evidence_refs,
                    'confidence':item.get('confidence'),
                    'confidence_rank':CONFIDENCE_RANK.get(item.get('confidence')),
                    'quality_outcome':'not_requested',
                    'quality_explanations':[],
                    'hit_paths':_hit_paths(item,payload),
                    'evidence_review_status':obs.get('evidence_review_status','unreviewed'),
                    '_claim':(item['relation'],item['role'],item['commercial_stage'],
                        item.get('valid_from'),item.get('valid_to'),direction),
                })
    # Assertion supersession/conflict marking runs on the FULL projected set:
    # a recall filter must never erase a conflicting claim and revive the
    # filtered-out row as an unconflicted current fact.
    _mark_assertions(rows)
    kept=[row for row in rows if _matches_filters(row,payload) is not None]
    if len(kept)>FACTS_MAX:
        _fail('facts_result_limit_exceeded')
    for row in kept:
        row['quality_outcome'],row['quality_explanations']=_quality_outcome(
            row,payload['quality_conditions'])
    # A row is a hit only on `pass`; unknown never qualifies.
    if payload['quality_conditions'] is not None:
        kept=[row for row in kept if row['quality_outcome']=='pass']
    for row in kept:
        row['quality_outcome'],row['quality_explanations']=_quality_outcome(
            row,payload['quality_conditions'])
        detail=_strict_gate(row,payload,{entry['id']:entry for entry in row['evidence']})
        if row['status_detail']=='strict':
            row['status_detail']=detail
        row['qualification']='strict' if row['status_detail']=='strict' else 'candidate'
    ordered=sorted(kept,key=lambda row:(
        row['subject_ref']['entity_id'],row['subject_ref']['scope'],
        row['subject_ref']['scope_id'] or '',row['observation_sequence'],
        row['observation_id'],row['item_index']))
    return [_strip(row) for row in ordered],stats


def _strip(row):
    return {k:v for k,v in row.items() if not k.startswith('_')}


def _profile_watermark(value,owner):
    """Frozen producer shape of the bare profile capture watermark."""
    if (not isinstance(value,dict) or set(value)!={'store_id','observation_sequence',
        'source_watermarks','read_at'} or value['store_id']!=owner['store_id']
        or type(value['observation_sequence']) is not int or value['observation_sequence']<0):
        _fail('facts_profile_watermark_invalid')
    read_at=core.parse_utc_timestamp(value['read_at'])
    marks=value['source_watermarks']
    if not isinstance(marks,list) or len({mark.get('namespace') for mark in marks})!=len(marks):
        _fail('facts_profile_source_watermarks_invalid')
    if not {'identity','observations'}<={mark.get('namespace') for mark in marks}:
        _fail('facts_profile_source_watermarks_invalid')
    for mark in marks:
        if (not isinstance(mark,dict) or set(mark)!={'namespace','schema_version','status',
            'sequence','read_at','content_sha256'} or type(mark['sequence']) is not int
            or mark['sequence']<0 or mark['status'] not in
            {'available','missing','read_error','schema_unavailable'}
            or core.parse_utc_timestamp(mark['read_at'])>read_at):
            _fail('facts_profile_source_watermarks_invalid')
        if mark['status']=='available':
            if (type(mark['schema_version']) is not int or not isinstance(mark['content_sha256'],str)
                or not re.fullmatch('[a-f0-9]{64}',mark['content_sha256'])):
                _fail('facts_profile_source_watermarks_invalid')
        elif mark['content_sha256'] is not None:
            _fail('facts_profile_source_watermarks_invalid')
    return value


def _matched_listings(value):
    if not isinstance(value,list):
        _fail('facts_profile_matched_listings_invalid')
    for listing in value:
        if (not isinstance(listing,dict) or set(listing)!={'market','ticker','listing_id'}
            or any(listing[k] is not None and not isinstance(listing[k],str)
                   for k in ('market','ticker','listing_id'))):
            _fail('facts_profile_matched_listings_invalid')
    return value


def _scope_key(ref):
    """Facts SubjectScope identity, comparable across profile and missing refs."""
    return (ref['entity_id'],ref['scope'],ref['scope_id'],ref['security_id'],
        ref['listing_id'],ref['segment_id'])


def _subject_scope(ref):
    """Facts wire SubjectScope shape with the core scope consistency rules."""
    if (not isinstance(ref,dict) or set(ref)!={'entity_id','scope','scope_id',
        'security_id','listing_id','segment_id'} or not isinstance(ref['entity_id'],str)
        or not ref['entity_id'] or ref['scope'] not in {'entity','security','segment'}):
        _fail('facts_subject_scope_invalid')
    scope=ref['scope']
    if scope=='entity':
        if (ref['scope_id']!=ref['entity_id']
            or any(ref[n] is not None for n in ('security_id','listing_id','segment_id'))):
            _fail('facts_subject_scope_invalid')
    elif scope=='security':
        if (not ref['security_id'] or ref['scope_id']!=ref['security_id']
            or ref['segment_id'] is not None):
            _fail('facts_subject_scope_invalid')
    else:
        if (not ref['segment_id'] or ref['scope_id']!=ref['segment_id']
            or any(ref[n] is not None for n in ('security_id','listing_id'))):
            _fail('facts_subject_scope_invalid')
    return ref


ROW_FIELDS={'observation_id','payload_sha256','raw_sha256','original_json_base64',
    'observation_wire_profile','binding_status','subject_binding','observation_sequence',
    'ack_sequence','ingest_status','qualification_status'}


def _validate_profile_result(profile_result,*,request,owner):
    """Native verification of the consumed profile: no unverified row survives.

    Checks the frozen producer shape (classification_gap optional), subject
    coverage against the requested entity_ids, the bare capture watermark, and
    every observation row through the core seal: original bytes/hash/schema,
    owner reference and full answer semantics. The bare profile watermark does
    not carry the capture ack watermark, so the core ack bound is derived from
    the owner-attested ack values (every row's ack_sequence must equal its
    owner reference anyway); rows beyond the attested bound do not exist.
    """
    if (not isinstance(profile_result,dict)
        or set(profile_result)-{'classification_gap'}!={'profiles','legacy_unbound_observations',
            'missing_subject_refs','watermark'}
        or not isinstance(profile_result.get('classification_gap'),bool)):
        _fail('facts_profile_result_invalid')
    profiles=profile_result['profiles']
    legacy=profile_result['legacy_unbound_observations']
    missing=profile_result['missing_subject_refs']
    if (not isinstance(profiles,list) or not isinstance(legacy,list)
        or not isinstance(missing,list)):
        _fail('facts_profile_result_invalid')
    requested=set(request['payload']['entity_ids'])
    try:
        profile_refs=core.index_subject_refs([profile['subject_ref'] for profile in profiles])
    except (TypeError,KeyError) as error:
        raise ValueError('facts_profile_result_invalid') from error
    missing_refs={}
    for ref in missing:
        _subject_scope(ref)
        key=_scope_key(ref)
        if key in missing_refs:
            _fail('facts_duplicate_subject_scope')
        missing_refs[key]=ref
    if {_scope_key(profile['subject_ref']) for profile in profiles}&set(missing_refs):
        _fail('facts_subject_coverage_mismatch')
    for ref in list(profile_refs.values())+list(missing_refs.values()):
        if ref['entity_id'] not in requested:
            _fail('facts_unrequested_subject')
    _profile_watermark(profile_result['watermark'],owner)
    rows=[row for profile in profiles for row in profile.get('observations',[])]
    rows+=list(legacy)
    for row in rows:
        if not isinstance(row,dict) or set(row)!=ROW_FIELDS:
            _fail('facts_profile_row_invalid')
    watermark=dict(profile_result['watermark'],
        ack_sequence=max([row['ack_sequence'] for row in rows]+[0]))
    candidates=[profile['subject_ref'] for profile in profiles]+list(missing)
    base=dict(payload=dict(subject_refs=copy.deepcopy(candidates),
        field_ids=list(request['payload']['field_ids']),
        information_cutoff=request['payload']['information_cutoff'],
        include_history=True,model_filter=copy.deepcopy(request['payload']['model_filter'])))
    seen=set()
    for profile in profiles:
        if (not isinstance(profile,dict) or set(profile)-{'matched_listings'}
            !={'subject_ref','canonical_name','observations'}
            or not isinstance(profile['canonical_name'],str)
            or not profile['canonical_name'].strip()
            or not isinstance(profile['observations'],list)):
            _fail('facts_profile_result_invalid')
        if 'matched_listings' in profile:
            _matched_listings(profile['matched_listings'])
        for row in profile['observations']:
            if row['observation_id'] in seen:
                _fail('facts_duplicate_original_observation')
            seen.add(row['observation_id'])
            obs=core.original_observation(row)
            owner_ref=core.validate_owner_observation_reference(row,owner)
            if obs['answer'].get('response_kind')=='fact' and row['binding_status']!='bound':
                # Frozen wire parity: a legacy unbound answer cannot carry a
                # fact row past the native seal; refuse with the wire's code
                # before the generic unbound-history check.
                _fail('facts_legacy_unbound_answer')
            core.validate_original_semantics(obs,row=row,owner_ref=owner_ref,request=base,
                watermark=watermark,subject_ref=profile['subject_ref'])
    for row in legacy:
        if row['observation_id'] in seen:
            _fail('facts_duplicate_original_observation')
        seen.add(row['observation_id'])
        obs=core.original_observation(row)
        owner_ref=core.validate_owner_observation_reference(row,owner)
        core.validate_original_semantics(obs,row=row,owner_ref=owner_ref,request=base,
            watermark=watermark,subject_ref=None)
    return copy.deepcopy(profile_result)


def build_result(*,profile_result,request,owner,read_at):
    """Sealed FULL result (both qualifications); the service pages afterwards."""
    payload=request['payload']
    facts,stats=project_fact_rows(profile_result,payload)
    query_hash=query_sha256(request)
    missing=profile_result.get('missing_subject_refs') or []
    marks=profile_result['watermark']['source_watermarks']
    failed=any(mark['status']!='available' for mark in marks)
    strict_count=sum(1 for row in facts if row['qualification']=='strict')
    candidate_count=len(facts)-strict_count
    explore=payload['mode']=='explore'
    found=len(facts)>0 if explore else strict_count>0
    reasons=[]
    if missing:
        reasons.append('subject_unavailable')
    if profile_result.get('classification_gap'):
        reasons.append('identity_market_unmapped')
    reasons.extend(mark['namespace']+'_'+mark['status'] for mark in marks
        if mark['status']!='available')
    if failed:
        status,coverage_status,empty_reason='unavailable','unknown','source_unavailable'
    elif not stats['fact_observations']:
        status='coverage_gap'
        empty_reason='subject_unavailable' if (missing or not profile_result['profiles']) \
            else 'no_bound_fact_observations'
        coverage_status='not_covered'
    elif found:
        status='partial' if missing else 'ok'
        empty_reason=None
        coverage_status='partial' if missing else 'complete'
    else:
        status,coverage_status,empty_reason='empty','partial','no_fact_match'
    result={
        'protocol':PROTOCOL,
        'status':status,
        'mode':payload['mode'],
        'operation':request['operation'],
        'store_id':owner['store_id'],
        'facts':facts,
        'page_facts':[],
        'total':len(facts) if explore else strict_count,
        'candidate_total':candidate_count,
        'next_cursor':None,
        'missing_subject_ids':sorted({ref['entity_id'] for ref in missing}),
        'missing_subject_refs':copy.deepcopy(missing),
        'coverage':{'status':coverage_status,'reason_codes':sorted(set(reasons)),
            'inference_policy':'no_cross_fact_join','market_wide_claim':False,
            'fact_relation_available':bool(facts),'empty_reason':empty_reason},
        'export':None,
        'query_sha256':query_hash,
        'profile_result':copy.deepcopy(profile_result),
        'watermark':{'store_id':owner['store_id'],'snapshot_id':'PENDING',
            'query_sha256':query_hash,
            'information_cutoff':payload['information_cutoff'],
            'observation_sequence':profile_result['watermark']['observation_sequence'],
            'read_at':read_at,'source_consistency':'sequential_owner_reads',
            'source_watermarks':copy.deepcopy(marks)},
    }
    return seal_response({'message_type':'response','schema_version':WIRE_VERSION,
        'request_id':request['request_id'],'operation':request['operation'],
        'response_at':read_at,'result':result},request=request)


def seal_response(response,*,request):
    result=copy.deepcopy(response['result'])
    result['watermark'].pop('snapshot_id',None)
    result['watermark']['snapshot_id']='fsnap1_'+_digest(result)
    return dict(response,result=result)


def _owner(owner):
    if (not isinstance(owner,dict) or set(owner)!={'store_id','observation_refs'}
        or not isinstance(owner['store_id'],str) or not owner['store_id'].strip()
        or not isinstance(owner['observation_refs'],dict)):
        _fail('facts_independent_owner_required')
    return copy.deepcopy(owner)


def build_response(*,profile_result,request,owner,read_at):
    validate_request(request)
    request=materialize(request)
    native=_owner(owner)
    _validate_profile_result(profile_result,request=request,owner=native)
    response=build_result(profile_result=profile_result,request=request,
        owner=native,read_at=read_at)
    validate_response(response,request=request,owner=native)
    return response


def build_export_body(result,request,*,generated_at):
    """Frozen candidate set from the SAME rows and order as the public query."""
    payload=request['payload']
    candidates=copy.deepcopy(result['facts'])
    if payload['mode']=='strict':
        candidates=[row for row in candidates if row['qualification']=='strict']
    body={
        'protocol':EXPORT_PROTOCOL,
        'export_version':'1.0.0',
        'candidate_set_id':'PENDING',
        'dataset_sha256':'PENDING',
        'operation':'export_facts',
        'mode':payload['mode'],
        'label':request.get('label'),
        'query':normalize_payload(request),
        'query_sha256':result['query_sha256'],
        'information_cutoff':payload['information_cutoff'],
        'watermark':copy.deepcopy(result['watermark']),
        'candidates':candidates,
        'candidate_entity_ids':sorted({row['subject_ref']['entity_id'] for row in candidates}),
        'coverage':copy.deepcopy(result['coverage']),
        'generated_at':generated_at,
        'direction_convention_version':DIRECTION_CONVENTION_VERSION,
    }
    core_content={k:v for k,v in body.items() if k not in {'dataset_sha256','candidate_set_id'}}
    body['dataset_sha256']=_digest(core_content)
    body['candidate_set_id']='fexp1_'+body['dataset_sha256']
    return body


def _verify_export_hash(dataset):
    """Verify only the export body's self-hash; this does not bind its source."""
    if not isinstance(dataset,dict) or dataset.get('protocol')!=EXPORT_PROTOCOL:
        _fail('facts_export_shape')
    body={k:v for k,v in dataset.items() if k not in {'dataset_sha256','candidate_set_id'}}
    digest=_digest(body)
    if (dataset.get('dataset_sha256')!=digest
        or dataset.get('candidate_set_id')!='fexp1_'+digest):
        _fail('facts_export_hash_mismatch')
    return copy.deepcopy(dataset)


def verify_export(dataset,*,response,request,owner):
    """Verify an export body and bind it to the public response that carries it."""
    _verify_export_hash(dataset)
    validated=validate_export_response(response=response,request=request,owner=owner)
    if dataset!=validated['result']['export']:
        _fail('facts_export_binding_mismatch')
    return dict(copy.deepcopy(dataset),verified=True)


def validate_export_response(*,response,request,owner):
    """Validate the owner-presented export against its query and sealed source.

    An export's self-hash only detects accidental changes. Rebuild the normal
    facts projection from the original profile result and owner provenance,
    then rebuild the export body and compare the complete public envelope. This
    binds candidates, query, snapshot, coverage and provenance to the request.
    """
    validate_request(request)
    if request['operation']!='export_facts':
        _fail('facts_export_request_required')
    _shape(response,'response')
    request=_materialize_for_response(request,response)
    native=_owner(owner)
    result=response['result']
    export=result['export']
    _verify_export_hash(export)
    if (response['request_id']!=request['request_id']
        or response['operation']!='export_facts'
        or result['operation']!='export_facts'):
        _fail('facts_request_binding_mismatch')

    read_at=result['watermark']['read_at']
    if core.parse_utc_timestamp(response['response_at'])<core.parse_utc_timestamp(read_at):
        _fail('facts_response_before_read')
    internal=build_response(profile_result=result['profile_result'],request=request,
        owner=native,read_at=read_at)
    expected_result=copy.deepcopy(internal['result'])
    expected_export=build_export_body(expected_result,request,
        generated_at=export['generated_at'])
    expected_result.update(operation='export_facts',facts=[],page_facts=[],
        total=len(expected_export['candidates']),next_cursor=None,export=expected_export)
    expected={'message_type':'response','schema_version':WIRE_VERSION,
        'request_id':request['request_id'],'operation':'export_facts',
        'response_at':response['response_at'],'result':expected_result}
    if module_contract.canonical_bytes(response)!=module_contract.canonical_bytes(expected):
        _fail('facts_export_binding_mismatch')
    return copy.deepcopy(response)


def validate_response(response,*,request,owner):
    validate_request(request)
    _shape(response,'response')
    request=_materialize_for_response(request,response)
    native=_owner(owner)
    _validate_profile_result(response['result']['profile_result'],request=request,owner=native)
    result=response['result']
    if (response['request_id']!=request['request_id']
        or response['operation']!=request['operation']
        or result['query_sha256']!=query_sha256(request)
        or result['store_id']!=native['store_id']
        or result['watermark']['store_id']!=native['store_id']):
        _fail('facts_request_binding_mismatch')
    if core.parse_utc_timestamp(response['response_at'])<core.parse_utc_timestamp(result['watermark']['read_at']):
        _fail('facts_response_before_read')
    # A snapshot can be replayed by either operation; the projection is
    # rebuilt under the operation that produced the stored sealed result.
    # The public owner query returns a page projection (`facts=[]`,
    # `page_facts=...`) while the immutable snapshot id is bound to the FULL
    # result. Recompute that full result from the owner-bound profile, then
    # compare either the full build response or its exact requested page.
    build_request=dict(copy.deepcopy(request),operation=result['operation'])
    rebuilt=build_result(profile_result=result['profile_result'],request=build_request,
        owner=native,read_at=result['watermark']['read_at'])['result']
    presented=present_result(rebuilt,request['payload'])
    is_page=(bool(rebuilt['facts']) and result.get('facts')==[]
        and isinstance(result.get('page_facts'),list))
    if is_page:
        if result['watermark']['snapshot_id']!=rebuilt['watermark']['snapshot_id']:
            _fail('facts_snapshot_content_mismatch')
        if result!=presented:
            _fail('facts_projection_mismatch')
    else:
        sealed=seal_response({'message_type':response['message_type'],
            'schema_version':response['schema_version'],'request_id':response['request_id'],
            'operation':response['operation'],'response_at':response['response_at'],
            'result':copy.deepcopy(result)},request=request)
        if sealed['result']!=result:
            _fail('facts_snapshot_content_mismatch')
        if result!=rebuilt:
            _fail('facts_projection_mismatch')
    if (request['payload']['snapshot_id'] is not None
        and request['payload']['snapshot_id']!=result['watermark']['snapshot_id']):
        _fail('facts_snapshot_id_mismatch')
    return copy.deepcopy(response)


def _reject_constant(token):
    raise ValueError('facts_cursor_invalid')


def _json(raw):
    return json.loads(raw.decode('utf-8'),object_pairs_hook=module_contract.unique_json_object,
        parse_constant=_reject_constant)


def _cursor(offset,query_hash,snapshot_id):
    value={'offset':offset,'query_sha256':query_hash,'snapshot_id':snapshot_id}
    token=base64.urlsafe_b64encode(module_contract.canonical_bytes(value)).decode().rstrip('=')
    return token+'.'+_digest(value)


def _offset(cursor,*,query_hash,snapshot_id,page_size,total):
    if cursor is None:
        return 0
    try:
        token,digest=cursor.split('.')
        value=_json(base64.b64decode(token+'='*(-len(token)%4),altchars=b'-_',validate=True))
        if (set(value)!={'offset','query_sha256','snapshot_id'}
            or _digest(value)!=digest or value['query_sha256']!=query_hash
            or value['snapshot_id']!=snapshot_id or type(value['offset']) is not int
            or not 0<value['offset']<total or value['offset']%page_size):
            raise ValueError('invalid cursor')
        return value['offset']
    except (ValueError,TypeError,KeyError) as error:
        raise ValueError('facts_cursor_invalid') from error


def present_result(result,payload):
    """One shared projection of the sealed full result onto a page; no re-filter.

    Presentation layer of the frozen wire (service side): the sealed FULL
    result stays authoritative, the page only slices it, and cursors are bound
    to the query hash and snapshot so cross-query or cross-snapshot replay is
    rejected.
    """
    page=payload['page']
    size=PAGE_SIZE_DEFAULT if page is None else page['page_size']
    if size<1 or size>PAGE_SIZE_MAX:
        _fail('facts_page_size_invalid')
    ordered=result['facts']
    if payload['mode']=='strict':
        ordered=[row for row in ordered if row['qualification']=='strict']
    offset=_offset(page['cursor'] if page else None,query_hash=result['query_sha256'],
        snapshot_id=result['watermark']['snapshot_id'],page_size=size,total=len(ordered))
    window=ordered[offset:offset+size]
    next_cursor=None
    if offset+len(window)<len(ordered):
        next_cursor=_cursor(offset+len(window),result['query_sha256'],
            result['watermark']['snapshot_id'])
    presented=copy.deepcopy(result)
    presented['facts']=[]
    presented['page_facts']=window
    presented['total']=len(ordered)
    presented['next_cursor']=next_cursor
    return presented
