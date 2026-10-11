"""Closed read-only capabilities 1.1; support never implies answer coverage."""
import copy
import json
import re
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import query_contract as profiles
import query_pool_scope_contract as scoped
from module_contract import canonical_bytes

SCHEMA = json.loads((scoped.raw.ROOT / 'schemas/quick_scan/query-capabilities.schema.json').read_bytes())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
MAX_BYTES = 8 * 1024 * 1024
WIRES = [dict(schema_version='2.0.0', operations=['get_profiles']),
    dict(schema_version='2.1.0', operations=['search', 'candidate_set']),
    dict(schema_version='2.2.0', operations=['search', 'candidate_set']),
    dict(schema_version='2.3.0', operations=['nominate', 'report_conflict']),
    dict(schema_version='2.4.0', operations=['research_context']),
    dict(schema_version='2.5.0', operations=['search', 'candidate_set'])]
OPERATIONS = ['get_profiles', 'search', 'candidate_set', 'nominate', 'report_conflict', 'research_context']
MARKETS = ['CN', 'HK', 'US']
INTERFACES = [
    dict(component='StockWiki', entry_type='module', entry_point='stockwiki.quick_scan_refresh_owner_cli',
        purpose='refresh_preview', selectors=['--root', '--iqs-code-root', '--request'], permission_boundary='fixed_owner_configuration_readonly_preview'),
    dict(component='StockWiki', entry_type='module', entry_point='stockwiki.quick_scan_refresh_owner_cli',
        purpose='native_confirmation', selectors=['--root', '--iqs-code-root', '--confirm', '--idempotency-key'],
        permission_boundary='interactive_challenge_real_OS_principal_and_current_scope'),
    dict(component='StockQA', entry_type='module', entry_point='src.utils.quick_scan_refresh_admission_cli',
        purpose='qa_admission', selectors=['--config', '--confirmation-id'], permission_boundary='fixed_native_confirmation_and_executor_configuration'),
    dict(component='StockQA', entry_type='script', entry_point='main_with_llm.py', purpose='qa_execution',
        selectors=['--require-search', '--identity-snapshot', '--question-manifest', '--c06-authority', '--spend-authorization',
            '--quick-scan-owner-config', '--refresh-admission-config', '--refresh-confirmation-id'],
        permission_boundary='durable_admission_current_owner_permission_and_original_Q13_budget'),
    dict(component='StockWiki', entry_type='module', entry_point='stockwiki.quick_scan_subject_dispatch_cli',
        purpose='pre_send_subject_registration', selectors=['--root', '--iqs-code-root', '--iqs-release-root', '--operation', '--request',
            '--subject-key', '--scope', '--scope-id', '--expected-decision-id', '--expected-anchor-version'],
        permission_boundary='independent_current_route_manifest_owner_anchor_before_send'),
    dict(component='StockWiki', entry_type='module', entry_point='stockwiki.quick_scan_qualification_cli',
        purpose='operator_review', selectors=['--root', '--iqs-code-root', '--request'],
        permission_boundary='fixed_review_authority_real_OS_principal_and_original_payload'),
    dict(component='StockQA', entry_type='module', entry_point='src.utils.quick_scan_execution_inspect_cli',
        purpose='execution_inspection', selectors=['--ledger', '--request'], permission_boundary='fixed_owner_executor_readonly_original_ledger'),
    dict(component='StockWiki', entry_type='module', entry_point='stockwiki.quick_scan_execution_qualification_cli',
        purpose='execution_qualification', selectors=['--root', '--iqs-code-root', '--request'],
        permission_boundary='fixed_execution_policy_real_OS_principal_and_native_execution_proof')]


def market_domain(value):
    return ('CN' if value in {'A', 'CN', 'SSE', 'SZSE', 'BSE'} else 'HK' if value in {'HK', 'HKEX'}
        else 'US' if value in {'US', 'NASDAQ', 'NYSE', 'NYSE_AMERICAN'} else None)


def validate_request(request):
    try:
        VALIDATOR.validate(request)
        if request['message_type'] != 'request':
            raise ValueError('capabilities_request_required')
        profiles._utc(request['requested_at'])
        selection = request['payload']['selection']
        if selection is not None:
            payload = dict(selection, filters=dict(text='', markets=[], industries=[], stages=[], company_types=[], score_policy=None),
                view='all_relevant', page_size=100, snapshot_id=None, cursor=None)
            scoped.validate_request(dict(message_type='request', schema_version='2.5.0', operation='search',
                request_id=request['request_id'], consumer_id=request['consumer_id'], requested_at=request['requested_at'], payload=payload))
        if len(canonical_bytes(request)) > MAX_BYTES:
            raise ValueError('capabilities_request_too_large')
    except (ValidationError, KeyError, TypeError, RecursionError) as exc:
        raise ValueError('capabilities_request_invalid') from exc
    return copy.deepcopy(request)


def _context(value):
    keys = {'protocol', 'store_id', 'read_at', 'source_watermarks', 'identity_market_domains',
        'identity_market_scan_status', 'identity_market_scope', 'unmapped_identity_market_labels',
        'observation_sequence', 'capture_error', 'context_sha256'}
    if (not isinstance(value, dict) or set(value) != keys or value['protocol'] != 'stockwiki.capabilities_owner_context/1.0.0'
        or value['context_sha256'] != profiles._digest({key: item for key, item in value.items() if key != 'context_sha256'})
        or not isinstance(value['store_id'], str) or not 1 <= len(value['store_id']) <= 160):
        raise ValueError('capabilities_owner_context_required')
    at = profiles._utc(value['read_at'])
    marks = value['source_watermarks']
    if (not isinstance(marks, list) or len(marks) != 4
        or {mark['namespace'] for mark in marks} != {'universe', 'identity', 'analysis_subjects', 'observations'}):
        raise ValueError('capabilities_sources_invalid')
    for mark in marks:
        if (set(mark) != {'namespace', 'schema_version', 'status', 'sequence', 'read_at', 'content_sha256'}
            or mark['status'] not in {'available', 'missing', 'read_error', 'schema_unavailable'}
            or type(mark['sequence']) is not int or mark['sequence'] < 0 or profiles._utc(mark['read_at']) > at):
            raise ValueError('capabilities_source_invalid')
        versions = {'universe': {5, 6}, 'identity': {5, 6}, 'analysis_subjects': {1}, 'observations': {2, 3, 4}}
        if mark['status'] == 'available' and (type(mark['schema_version']) is not int
            or mark['schema_version'] not in versions[mark['namespace']]
            or not isinstance(mark['content_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', mark['content_sha256'])):
            raise ValueError('capabilities_available_source_invalid')
    identity = next(mark for mark in marks if mark['namespace'] == 'identity')
    expected = 'available' if identity['status'] == 'available' else 'unavailable'
    if (value['identity_market_scan_status'] != expected
        or value['identity_market_scope'] not in {'owner_namespace', 'selected_universe'}
        or not isinstance(value['identity_market_domains'], list)
        or value['identity_market_domains'] != sorted(set(value['identity_market_domains']))
        or not set(value['identity_market_domains']) <= set(MARKETS)
        or (expected != 'available' and (value['identity_market_domains'] or value['unmapped_identity_market_labels']))
        or type(value['observation_sequence']) is not int or value['observation_sequence'] < 0):
        raise ValueError('capabilities_identity_or_sequence_invalid')
    if value['capture_error'] is not None and (not isinstance(value['capture_error'], str)
        or not re.fullmatch('[a-z][a-z0-9_]{0,159}', value['capture_error'])):
        raise ValueError('capabilities_capture_reason_invalid')
    return value


def _result(request, source_context, index, scope_context):
    ctx = _context(source_context); selection = request['payload']['selection']
    if profiles._utc(request['requested_at']) > profiles._utc(ctx['read_at']):
        raise ValueError('capabilities_read_before_request')
    if (selection is None and (index is not None or scope_context is not None or ctx['capture_error'] is not None)):
        raise ValueError('capabilities_unrequested_selection')
    if index is not None:
        scoped.validate_raw_index(index, store_id=ctx['store_id'], scope_context=scope_context)
        if (ctx['capture_error'] is not None or index['universe_id'] != selection['universe_id']
            or index['selection'] != {key: selection[key] for key in scoped.SELECTION_KEYS}
            or profiles._utc(index['read_at']) > profiles._utc(ctx['read_at'])):
            raise ValueError('capabilities_selection_mismatch')
        native_marks = {mark['namespace']: mark for mark in ctx['source_watermarks']}
        if any(any(mark[key] != native_marks[mark['namespace']][key] for key in ('schema_version', 'status', 'sequence'))
            for mark in index['source_watermarks']):
            raise ValueError('capabilities_source_changed_during_preflight')
    elif scope_context is not None or (selection is not None and ctx['capture_error'] is None):
        raise ValueError('capabilities_missing_selection_result')
    reasons = [mark['namespace'] + '_' + mark['status'] for mark in ctx['source_watermarks'] if mark['status'] != 'available']
    markets, unmapped = set(), set()
    if index is None:
        status = 'unknown' if reasons or selection is not None else 'not_requested'
        reasons.append(ctx['capture_error'] or 'selection_not_requested')
        counts, fields = None, {}
    else:
        status = index['coverage']['status']
        if status != 'complete':
            reasons.append('selected_fields_not_covered')
        counts = copy.deepcopy(index['scope_counts'])
        # Preflight is compact: exact missing SubjectRefs remain in the query
        # index, rather than repeating the whole issuer pool for every field.
        fields = {field: {key: copy.deepcopy(item) for key, item in value.items() if key != 'missing_subject_refs'}
            for field, value in index['field_scope_coverage'].items()}
        for field, value in index['field_scope_coverage'].items():
            fields[field]['missing_scope_row_count'] = len(value['missing_subject_refs'])
        for row in index['rows']:
            if not any(item['status'] in {'scored', 'answered'} and item['qualification_status'] not in {'rejected', 'conflict'}
                for item in row['observation_refs']):
                continue
            for security in row['securities']:
                label = security.get('market'); domain = market_domain(label)
                if domain:
                    markets.add(domain)
                elif isinstance(label, str) and label:
                    unmapped.add(label)
    payload = request['payload']
    available = dict(required_operations=OPERATIONS, required_query_versions=[wire['schema_version'] for wire in WIRES],
        required_market_filters=MARKETS, required_native_purposes=[entry['purpose'] for entry in INTERFACES])
    missing = {key.replace('required_', 'missing_'): [item for item in payload[key] if item not in supported]
        for key, supported in available.items()}
    required = dict(status='missing' if any(missing.values()) else 'satisfied', **missing)
    return dict(store_id=ctx['store_id'], supported_operations=copy.deepcopy(OPERATIONS), supported_query_wires=copy.deepcopy(WIRES),
        market_support=dict(profile_listing_scope='any_owner_attested_listing', market_filter_domains=copy.deepcopy(MARKETS)),
        identity_market_domains=copy.deepcopy(ctx['identity_market_domains']), identity_market_scan_status=ctx['identity_market_scan_status'],
        identity_market_scope=ctx['identity_market_scope'], unmapped_identity_market_labels=copy.deepcopy(ctx['unmapped_identity_market_labels']),
        capability_requirements=required, native_interfaces=copy.deepcopy(INTERFACES),
        coverage=dict(selection=copy.deepcopy(selection), status=status, reason_codes=sorted(set(reasons)),
            covered_market_domains=sorted(markets), unmapped_covered_market_labels=sorted(unmapped), scope_counts=counts,
            field_scope_coverage=fields, basis='availability_of_scope_bound_originals_not_accuracy_or_screening_qualification'),
        watermark=dict(store_id=ctx['store_id'], read_at=ctx['read_at'], source_watermarks=copy.deepcopy(ctx['source_watermarks']),
            source_consistency='sequential_owner_reads', observation_sequence=ctx['observation_sequence'],
            selected_index_sha256=index['content_sha256'] if index is not None else None,
            scope_inventory_sha256=index['scope_inventory_sha256'] if index is not None else None,
            owner_context_sha256=ctx['context_sha256']),
        limits=dict(source_max_bytes=8*1024*1024, source_max_rows=5000, pool_index_max_bytes=64*1024*1024, page_size_max=100,
            snapshot_ttl_seconds=3600, snapshot_max_count=32, snapshot_max_bytes=16*1024*1024, snapshot_total_max_bytes=64*1024*1024),
        answer_qualification_assessed=False, facts_producer_ready=False, financial_accuracy_proven=False,
        full_C06_milestone_accepted=False, dispatch_started=False, API_requests=0, database_writes=0)


def build_response(*, request, source_context, index, scope_context):
    validate_request(request)
    response = dict(protocol='stockwiki.c06_query_capabilities/1.1.0', schema_version='1.1.0', message_type='response',
        operation='capabilities', request_id=request['request_id'], response_at=source_context['read_at'],
        result=_result(request, source_context, index, scope_context))
    return validate_response(response=response, request=request, source_context=source_context, index=index, scope_context=scope_context)


def validate_response(*, response, request, source_context, index, scope_context):
    validate_request(request)
    try:
        VALIDATOR.validate(response)
        if (response['message_type'] != 'response' or response['request_id'] != request['request_id']
            or profiles._utc(response['response_at']) < profiles._utc(source_context['read_at'])
            or canonical_bytes(response['result']) != canonical_bytes(_result(request, source_context, index, scope_context))):
            raise ValueError('capabilities_response_owner_mismatch')
        if len(canonical_bytes(response)) > MAX_BYTES:
            raise ValueError('capabilities_response_too_large')
    except (ValidationError, KeyError, TypeError, RecursionError) as exc:
        raise ValueError('capabilities_response_invalid') from exc
    return copy.deepcopy(response)


validate_capabilities_request = validate_request
build_capabilities_response = build_response
validate_capabilities_response = validate_response
