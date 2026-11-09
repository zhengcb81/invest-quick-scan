"""Capabilities wire declarations for the 2.7.0 facts wire; old wires stay frozen.

All fixtures are synthetic; the capability source context is a synthetic owner
capture, never a real store. The declared 2.7.0 wire must match the four
facts-* operations the public CLI actually routes, and every 2.0.0-2.6.0 wire
entry must survive byte-identical.
"""
import copy

import pytest

import query_contract as core
import query_capabilities_contract as caps
import query_capabilities_vendor_contract as vendor

READ_AT = '2026-10-09T21:01:00Z'
STORE = 'STORE_SYNTHETIC_C06'

LEGACY_WIRES = [
    {'schema_version': '2.0.0', 'operations': ['get_profiles']},
    {'schema_version': '2.1.0', 'operations': ['search', 'candidate_set']},
    {'schema_version': '2.2.0', 'operations': ['search', 'candidate_set']},
    {'schema_version': '2.3.0', 'operations': ['nominate', 'report_conflict']},
    {'schema_version': '2.4.0', 'operations': ['research_context']},
    {'schema_version': '2.5.0', 'operations': ['search', 'candidate_set']},
]
FACTS_WIRE = {'schema_version': '2.7.0', 'operations': ['query_facts', 'export_facts']}
FACTS_WIRE_28 = {'schema_version': '2.8.0', 'operations': ['query_facts', 'export_facts']}
VENDOR_WIRE = {'schema_version': '2.6.0', 'operations': ['get_profiles']}
LEGACY_OPERATIONS = ['get_profiles', 'search', 'candidate_set', 'nominate',
                     'report_conflict', 'research_context']


def owner_context(*, read_at=READ_AT, domains=('US',), capture_error=None,
                  sequence=0):
    marks = [{'namespace': namespace, 'schema_version': version,
              'status': 'available', 'sequence': 0, 'read_at': read_at,
              'content_sha256': str(index + 2) * 64}
             for index, (namespace, version) in enumerate(
                 [('universe', 6), ('identity', 6), ('analysis_subjects', 1),
                  ('observations', 3)])]
    ctx = {'protocol': 'stockwiki.capabilities_owner_context/1.0.0',
           'store_id': STORE, 'read_at': read_at, 'source_watermarks': marks,
           'identity_market_domains': list(domains),
           'identity_market_scan_status': 'available',
           'identity_market_scope': 'selected_universe',
           'unmapped_identity_market_labels': [],
           'observation_sequence': sequence, 'capture_error': capture_error}
    ctx['context_sha256'] = core._digest(
        {key: value for key, value in ctx.items() if key != 'context_sha256'})
    return ctx


def capabilities_request(*, versions=(), operations=(), schema_version='1.1.0'):
    return {'message_type': 'request', 'schema_version': schema_version,
            'request_id': 'REQ_SYNTHETIC_CAPS', 'consumer_id': 'invest-quick-scan',
            'operation': 'capabilities', 'requested_at': '2026-10-09T21:00:00Z',
            'payload': {'required_operations': list(operations),
                        'required_query_versions': list(versions),
                        'required_market_filters': [],
                        'required_native_purposes': [], 'selection': None}}


def build_11(**kwargs):
    return caps.build_response(request=kwargs.pop('request'),
                               source_context=kwargs.pop('context'),
                               index=None, scope_context=None)


def build_12(**kwargs):
    return vendor.build_response(request=kwargs.pop('request'),
                                 source_context=kwargs.pop('context'),
                                 index=None, scope_context=None)


def test_capabilities_1_1_declares_the_facts_wire_after_the_legacy_six():
    response = build_11(request=capabilities_request(), context=owner_context())
    wires = response['result']['supported_query_wires']
    assert wires == LEGACY_WIRES + [FACTS_WIRE, FACTS_WIRE_28]
    assert len(wires) == 8
    assert response['result']['supported_operations'] == (
        LEGACY_OPERATIONS + ['query_facts', 'export_facts'])


def test_capabilities_1_2_keeps_vendor_wire_and_adds_facts_wire():
    response = build_12(request=capabilities_request(schema_version='1.2.0'),
                        context=owner_context())
    wires = response['result']['supported_query_wires']
    assert len(wires) == 9
    assert LEGACY_WIRES == wires[:6]
    assert wires == LEGACY_WIRES + [VENDOR_WIRE, FACTS_WIRE, FACTS_WIRE_28]
    assert response['schema_version'] == '1.2.0'
    assert response['protocol'] == 'stockwiki.c06_query_capabilities/1.2.0'
    assert response['result']['supported_operations'] == (
        LEGACY_OPERATIONS + ['query_facts', 'export_facts'])


def test_facts_requirements_are_satisfied_once_declared():
    request = capabilities_request(operations=['query_facts', 'export_facts'],
                                   versions=['2.7.0', '2.8.0'])
    response = build_11(request=request, context=owner_context())
    required = response['result']['capability_requirements']
    assert required['status'] == 'satisfied'
    assert required['missing_operations'] == []
    assert required['missing_query_versions'] == []
    vendor_response = build_12(request=capabilities_request(
        schema_version='1.2.0', operations=['query_facts'], versions=['2.7.0', '2.8.0']),
        context=owner_context())
    vendor_required = vendor_response['result']['capability_requirements']
    assert vendor_required['status'] == 'satisfied'
    assert vendor_required['missing_operations'] == []
    assert vendor_required['missing_query_versions'] == []


def test_legacy_requirements_keep_their_old_answers():
    # 1.1.0 never declared the vendor wire, so requiring it still reports missing
    legacy_request = capabilities_request(versions=['2.6.0'])
    legacy = build_11(request=legacy_request, context=owner_context())
    assert legacy['result']['capability_requirements']['missing_query_versions'] == ['2.6.0']
    # 1.2.0 declares it
    current = build_12(request=capabilities_request(
        schema_version='1.2.0', versions=['2.6.0']), context=owner_context())
    assert current['result']['capability_requirements']['missing_query_versions'] == []
    # an old-only requirement stays satisfied on both envelope versions
    old_only = capabilities_request(operations=['get_profiles'], versions=['2.0.0'])
    assert build_11(request=old_only, context=owner_context())[
        'result']['capability_requirements']['status'] == 'satisfied'
    assert build_12(request=dict(old_only, schema_version='1.2.0'),
                    context=owner_context())[
        'result']['capability_requirements']['status'] == 'satisfied'


def test_honesty_constants_are_unchanged():
    for response in (build_11(request=capabilities_request(), context=owner_context()),
                     build_12(request=capabilities_request(schema_version='1.2.0'),
                              context=owner_context())):
        result = response['result']
        assert result['facts_producer_ready'] is False
        assert result['financial_accuracy_proven'] is False
        assert result['full_C06_milestone_accepted'] is False


def test_wire_count_bounds_are_closed_in_both_schemas():
    context = owner_context()
    response = build_11(request=capabilities_request(), context=context)
    wires = response['result']['supported_query_wires']
    for broken_wires in (wires + [VENDOR_WIRE], wires[:6]):
        broken = copy.deepcopy(response)
        broken['result']['supported_query_wires'] = broken_wires
        with pytest.raises(ValueError, match='capabilities_response_invalid'):
            caps.validate_response(response=broken, request=capabilities_request(),
                                   source_context=context, index=None,
                                   scope_context=None)
    vendor_response = build_12(request=capabilities_request(schema_version='1.2.0'),
                               context=context)
    vendor_wires = vendor_response['result']['supported_query_wires']
    for broken_wires in (vendor_wires + [VENDOR_WIRE], vendor_wires[:7]):
        broken = copy.deepcopy(vendor_response)
        broken['result']['supported_query_wires'] = broken_wires
        with pytest.raises(ValueError, match='capabilities_document_invalid'):
            vendor.validate_response(response=broken, request=capabilities_request(
                schema_version='1.2.0'), source_context=context, index=None,
                scope_context=None)


def test_1_1_wire_entry_cannot_gain_undeclared_operations():
    context = owner_context()
    response = build_11(request=capabilities_request(), context=context)
    broken = copy.deepcopy(response)
    broken['result']['supported_query_wires'][-1]['operations'] = ['query_facts']
    with pytest.raises(ValueError, match='capabilities_response_'):
        caps.validate_response(response=broken, request=capabilities_request(),
                               source_context=context, index=None, scope_context=None)


def test_request_validation_round_trip_is_unchanged_for_old_payloads():
    request = capabilities_request(operations=['get_profiles'],
                                   versions=['2.0.0', '2.5.0'])
    caps.validate_request(request)
    with pytest.raises(ValueError, match='capabilities_request_invalid'):
        caps.validate_request(dict(request, message_type='response'))
    with pytest.raises(ValueError, match='capabilities_request_invalid'):
        caps.validate_request(dict(request, schema_version='9.9.9'))
