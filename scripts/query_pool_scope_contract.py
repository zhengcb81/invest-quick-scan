"""Closed 2.5 scope selection over original rows and current owner assessment.

Scope selection is a consumer request, never a claim of field applicability.
Distinct company/subject/scope counts and field denominators remain explicit.
"""
import copy
import json
import re
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import query_pool_contract as raw
import query_pool_assessment_contract as assessed
from module_contract import canonical_bytes

SCHEMA = json.loads((raw.ROOT / 'schemas/quick_scan/query-pool-scoped.schema.json').read_bytes())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
SELECTION_KEYS = ('field_ids', 'information_cutoff', 'model_filter', 'field_scope_selection')
SCOPE_KEYS = {'scope_counts', 'field_scope_coverage', 'scope_inventory_sha256'}
SCOPE_RESULT_KEYS = {'scope_counts', 'field_scope_coverage'}
digest = raw.digest


def _selection(fields, selection):
    if (not isinstance(selection, dict) or set(selection) != set(fields)
        or any(not isinstance(values, list) or not values
            or any(not isinstance(value, str) or value not in {'entity', 'security', 'segment'} for value in values)
            or len(values) != len(set(values)) for values in selection.values())):
        raise ValueError('pool_field_scope_selection_invalid')


def validate_request(value):
    try:
        VALIDATOR.validate(value)
        _selection(value['payload']['field_ids'], value['payload']['field_scope_selection'])
        legacy = copy.deepcopy(value)
        legacy['schema_version'] = '2.2.0'
        legacy['payload'].pop('field_scope_selection')
        assessed.validate_request(legacy)
    except (ValidationError, TypeError, KeyError, RecursionError) as exc:
        raise ValueError('scoped_pool_request_invalid') from exc
    return copy.deepcopy(value)


def query_sha256(request):
    validate_request(request)
    payload = {key: value for key, value in request['payload'].items()
        if key not in {'snapshot_id', 'cursor', 'subject_refs', 'query_sha256', 'label'}}
    return digest(dict(consumer_id=request['consumer_id'], schema_version='2.5.0', operation='search', payload=payload))


def _coverage(index):
    """Independently recompute every denominator from original selected rows."""
    rows = index['rows']; selected_scopes = index['selection']['field_scope_selection']
    failed = any(mark['status'] != 'available' for mark in index['source_watermarks'])
    counts = dict(active_company_count=index['active_entity_count'],
        profiled_company_count=len({row['subject_ref']['entity_id'] for row in rows}),
        profiled_analysis_subject_count=len({(row['subject_ref']['analysis_subject_id'],
            row['subject_ref']['analysis_subject_revision'], row['subject_ref']['perimeter_sha256']) for row in rows}),
        profile_scope_row_count=len(rows))
    by_field = {}
    for field in index['selection']['field_ids']:
        wanted, missing = {}, {}
        for row in rows:
            ref = row['subject_ref']
            if ref['scope'] not in selected_scopes[field]:
                continue
            key = digest(ref); wanted[key] = ref
            present = any(item['field_id'] == field and item['status'] in {'scored', 'answered'}
                and item['qualification_status'] not in {'rejected', 'conflict'} for item in row['observation_refs'])
            if not present or failed:
                missing[key] = ref
        for ref in index['missing_subject_refs']:
            if ref['scope'] in selected_scopes[field]:
                key = digest(ref); wanted[key] = ref; missing[key] = ref
        covered = len(wanted) - len(missing)
        denominators = {scope: dict(requested_scope_row_count=sum(ref['scope'] == scope for ref in wanted.values()),
            covered_scope_row_count=sum(ref['scope'] == scope and key not in missing for key, ref in wanted.items()))
            for scope in selected_scopes[field]}
        absent = [scope for scope in selected_scopes[field] if denominators[scope]['requested_scope_row_count'] == 0]
        full = bool(wanted) and not missing and not absent and not index['missing_entity_ids'] and not failed
        by_field[field] = dict(requested_scopes=selected_scopes[field], requested_scope_row_count=len(wanted),
            covered_scope_row_count=covered, missing_subject_refs=[missing[key] for key in sorted(missing)],
            scope_denominators=denominators, absent_requested_scopes=absent,
            unresolved_company_count=len(index['missing_entity_ids']),
            status='unknown' if failed else 'complete' if full else 'partial' if covered else 'not_covered')
    fields = index['selection']['field_ids']
    covered = [field for field in fields if by_field[field]['status'] == 'complete']
    full = len(covered) == len(fields) and not failed
    partial = any(value['covered_scope_row_count'] for value in by_field.values()) and not failed and not full
    coverage = dict(status='unknown' if failed else 'complete' if full else 'partial' if partial else 'not_covered',
        requested_field_ids=fields, covered_field_ids=covered, missing_field_ids=[field for field in fields if field not in covered])
    status = 'unavailable' if failed else 'ok' if full else 'partial' if partial else 'coverage_gap'
    return counts, by_field, coverage, status


def _legacy_projection(index):
    """Apply unchanged original-axis checks; derive its conservative coverage.

This projection is validation input only. It is never returned, retained or
presented as an owner snapshot, new original or evidence authority.
"""
    legacy = {key: copy.deepcopy(index[key]) for key in raw.INDEX_KEYS}
    legacy['protocol'] = 'stockwiki.c06_pool_index/1.1.0'
    legacy['selection'].pop('field_scope_selection')
    field_sets = [{item['field_id'] for item in row['observation_refs']
        if item['status'] in {'scored', 'answered'} and item['qualification_status'] not in {'rejected', 'conflict'}}
        for row in legacy['rows']]
    requested = set(legacy['selection']['field_ids'])
    covered = set.intersection(*field_sets) if field_sets and not legacy['missing_entity_ids'] and not legacy['missing_subject_refs'] else set()
    failed = any(mark['status'] != 'available' for mark in legacy['source_watermarks'])
    full = covered == requested and not legacy['missing_entity_ids'] and not legacy['missing_subject_refs'] and not failed
    partial = any(field_sets) and not full and not failed
    legacy['coverage'] = dict(status='unknown' if failed else 'complete' if full else 'partial' if partial else 'not_covered',
        requested_field_ids=legacy['selection']['field_ids'], covered_field_ids=sorted(covered),
        missing_field_ids=sorted(requested - covered))
    legacy['status'] = 'unavailable' if failed else 'ok' if full else 'partial' if partial else 'coverage_gap'
    legacy['content_sha256'] = digest({key: value for key, value in legacy.items() if key not in {'content_sha256', 'snapshot_id'}})
    legacy['snapshot_id'] = 'pool1_' + legacy['content_sha256']
    return legacy


def _scope_context(index, context, store_id):
    inventory_keys = {'store_id', 'universe_id', 'selection', 'active_entity_count', 'missing_entity_ids', 'scope_rows'}
    keys = inventory_keys | {'protocol', 'read_at', 'source_watermarks', 'inventory_sha256', 'context_sha256'}
    if (not isinstance(context, dict) or set(context) != keys or context['protocol'] != 'stockwiki.pool_scope_context/1.0.0'
        or context['store_id'] != store_id or context['context_sha256'] != digest({k: v for k, v in context.items() if k != 'context_sha256'})
        or context['inventory_sha256'] != digest({k: context[k] for k in inventory_keys})
        or index['scope_inventory_sha256'] != context['inventory_sha256']):
        raise ValueError('pool_independent_scope_inventory_required')
    raw.profiles._utc(context['read_at'])
    if len(canonical_bytes(context)) > raw.MAX_INDEX_BYTES or len(context['scope_rows']) > 60000:
        raise ValueError('pool_scope_inventory_capacity_limit')
    for key, value in context['scope_rows'].items():
        if not re.fullmatch('[a-f0-9]{64}', key) or not re.fullmatch('[a-f0-9]{64}', value):
            raise ValueError('pool_scope_inventory_invalid')
    if (len(context['source_watermarks']) != 3
        or {mark['namespace'] for mark in context['source_watermarks']} != {'universe', 'identity', 'analysis_subjects'}
        or any(mark['status'] != 'available' or raw.profiles._utc(mark['read_at']) > raw.profiles._utc(context['read_at'])
            for mark in context['source_watermarks'])):
        raise ValueError('pool_scope_inventory_source_unavailable')
    actual_rows = {digest(row['subject_ref']): digest({key: value for key, value in row.items() if key != 'observation_refs'})
        for row in index['rows']}
    if (actual_rows != context['scope_rows'] or index['universe_id'] != context['universe_id']
        or index['selection'] != context['selection'] or index['active_entity_count'] != context['active_entity_count']
        or index['missing_entity_ids'] != context['missing_entity_ids']):
        raise ValueError('pool_scope_inventory_mismatch')
    if any(digest(ref) not in actual_rows for ref in index['missing_subject_refs']):
        raise ValueError('pool_scope_inventory_mismatch')


def validate_raw_index(index, *, store_id, scope_context, qualified=False):
    try:
        expected_keys = raw.INDEX_KEYS | SCOPE_KEYS | ({'field_assessments', 'qualification_watermark'} if qualified else set())
        protocol = 'stockwiki.c06_pool_index/1.4.0' if qualified else 'stockwiki.c06_pool_index/1.3.0'
        if set(index) != expected_keys or index['protocol'] != protocol or set(index['selection']) != set(SELECTION_KEYS):
            raise ValueError('pool_scoped_index_shape')
        _selection(index['selection']['field_ids'], index['selection']['field_scope_selection'])
        if (index['content_sha256'] != digest({key: value for key, value in index.items() if key not in {'content_sha256', 'snapshot_id'}})
            or index['snapshot_id'] != 'pool1_' + index['content_sha256']):
            raise ValueError('pool_scoped_index_integrity_mismatch')
        if len(canonical_bytes(index)) > raw.MAX_INDEX_BYTES:
            raise ValueError('pool_index_retention_limit')
        # Reuse original SubjectRef, original variant, time/model, immutable
        # score, unavailable-source and membership invariants unchanged.
        raw.validate_index(_legacy_projection(index), store_id=store_id)
        _scope_context(index, scope_context, store_id)
        scopes = set().union(*map(set, index['selection']['field_scope_selection'].values()))
        for row in index['rows']:
            ref = row['subject_ref']
            if ref['scope'] not in scopes:
                raise ValueError('pool_unrequested_scope')
            if any(ref['scope'] not in index['selection']['field_scope_selection'][item['field_id']]
                for item in row['observation_refs']):
                raise ValueError('pool_observation_scope_selection_mismatch')
            if ref['scope'] == 'security' and (ref['listing_id'] is None or len(row['securities']) != 1
                or row['securities'][0]['security_id'] != ref['security_id']
                or row['securities'][0]['listing_id'] != ref['listing_id']):
                raise ValueError('pool_security_market_scope_mismatch')
        expected = _coverage(index)
        actual = (index['scope_counts'], index['field_scope_coverage'], index['coverage'], index['status'])
        if canonical_bytes(actual) != canonical_bytes(expected):
            raise ValueError('pool_scope_denominator_mismatch')
    except (ValidationError, TypeError, KeyError, RecursionError) as exc:
        raise ValueError('pool_scoped_index_invalid') from exc
    return copy.deepcopy(index)


def validate_index(index, *, store_id, assessment_context, scope_context):
    validate_raw_index(index, store_id=store_id, scope_context=scope_context, qualified=True)
    context = assessed._context(assessment_context, store_id, index['field_assessments'])
    if index['qualification_watermark'] != context['qualification_watermark']:
        raise ValueError('pool_independent_assessment_mismatch')
    if set(index['field_assessments']) != {item['observation_id'] for row in index['rows'] for item in row['observation_refs']}:
        raise ValueError('pool_assessment_original_set_mismatch')
    if raw.profiles._utc(context['read_at']) < raw.profiles._utc(index['read_at']):
        raise ValueError('pool_assessment_before_capture')
    return copy.deepcopy(index)


def validate_response(response, *, request, index, selected_rows, store_id, assessment_context, scope_context):
    validate_index(index, store_id=store_id, assessment_context=assessment_context, scope_context=scope_context)
    for row in selected_rows:
        expected = {item['observation_id']: index['field_assessments'][item['observation_id']] for item in row['observation_refs']}
        if row.get('field_assessments') != expected:
            raise ValueError('pool_response_owner_assessment_changed')
    qualified = (bool(selected_rows) and request['payload']['filters']['score_policy'] is not None
        and request['payload']['view'] == 'qualified' and all(row['selection_outcome'] == 'pass' for row in selected_rows))
    return raw._validate_response(response, request=request, index=index, selected_rows=selected_rows, store_id=store_id,
        request_validator=validate_request,
        index_validator=lambda value, store_id: validate_index(value, store_id=store_id,
            assessment_context=assessment_context, scope_context=scope_context),
        query_hasher=query_sha256, validator=VALIDATOR, row_extra={'field_assessments'},
        selection_keys=SELECTION_KEYS, result_extra={key: index[key] for key in SCOPE_RESULT_KEYS},
        watermark_extra={'qualification_watermark': index['qualification_watermark']}, qualification_available=True,
        candidate_protocol='stockwiki.c06_candidate_set/2.5.0', candidate_prefix='cset4_', candidate_qualified=qualified)


validate_pool_request = validate_request
pool_query_sha256 = query_sha256
validate_scoped_pool_index = validate_index
finish_scoped_pool_response = validate_response
