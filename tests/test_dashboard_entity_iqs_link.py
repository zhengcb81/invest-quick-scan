"""B03 LIVE-OWNER-VERIFY-REPAIR-01: the entity route must carry the IQSLink.

RED (before the fix): `/api/product/entity` answered with the owner entity
payload only. The frozen G-IQS-01 `IQSLink` declaration never travelled with
the entity, so the Dashboard `get_result` composition
fell back to the legacy partial declaration: the composed `routes.results`
lost the latest company result's `result_id` pin, the first-observation
anchor and the return context.

GREEN (after the fix): the entity response carries a valid `iqs_link`
declaration for THAT entity (entity-scoped by construction), the return
context is honoured and cross-scope returns still collapse to the plain
fallback, and no owner write is performed.
"""
from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import dashboard_iqs_link as link
from dashboard_service import DashboardService, ProductError


ENTITY_PAYLOAD = {
    'entity': {
        'entity_id': 'ENT_A',
        'canonical_name': '受控实体A',
        'identity_state': 'verified',
        'securities': [],
        'segments': [],
    },
    'observations': [],
}


class Owner:
    """A fake owner that can serve the entity, history and company reads."""

    def __init__(self, config):
        self.config = config
        self.entity_calls = []
        self.company_calls = []

    def status(self):
        return {'available': True, 'network_calls': 0}

    def entity(self, entity_id):
        self.entity_calls.append(entity_id)
        if entity_id == 'ENT_MISSING':
            raise ProductError('entity_not_found', 'No registered entity has this ID', 404)
        return dict(ENTITY_PAYLOAD)

    def entity_view(self, entity_id):
        return {'protocol': 'iqs.company_research_view/1.0.0', 'entity': dict(ENTITY_PAYLOAD),
                'temporal_shadow': {'reuse_authorized': False}}

    def history(self, entity_id):
        return {'observations': [
            {'observation_id': 'OBS_1', 'publication_status': 'published',
             'analysis_subject_id': None, 'answer_status': 'scored',
             'qualification_status': 'receipted'},
        ], 'available': True}

    def company_result(self, entity_id, result_id=None):
        self.company_calls.append(('result', entity_id, result_id))
        return {'protocol': 'iqs.dashboard.company_assessment/1',
                'projection_version': 'company_assessment/1.1.0',
                'entity_id': entity_id, 'read': 'result', 'owner_payload': {}}

    def company_history(self, entity_id, limit=20, offset=0):
        self.company_calls.append(('history', entity_id, limit, offset))
        return {'protocol': 'iqs.dashboard.company_assessment/1',
                'projection_version': 'company_assessment/1.1.0',
                'entity_id': entity_id, 'read': 'history', 'owner_payload': {}}


class Execution:
    def __init__(self, config):
        self.config = config

    def active_references(self):
        return []


def service_for(tmp_path, owner=Owner, **config):
    path = tmp_path / 'config' / 'dashboard.local.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding='utf8')
    return DashboardService(tmp_path, owner_factory=owner, execution_factory=Execution)


def test_entity_route_carries_the_iqs_link_declaration(tmp_path):
    """RED: the entity response must publish the frozen IQSLink."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_A')
    assert code == 200, reply
    data = reply['data']
    assert 'iqs_link' in data, (
        'the entity route must carry the frozen IQSLink declaration; '
        'without it the Dashboard composes a legacy link without the '
        'company result_id pin or the return context')
    declaration = data['iqs_link']
    assert declaration['service_id'] == link.SERVICE_ID
    assert declaration['base_origin'] == 'http://127.0.0.1:43219'
    assert declaration['route_template_version'] == link.ROUTE_TEMPLATE_VERSION
    assert declaration['routes']['results'].startswith('http://127.0.0.1:43219/#/results')


def test_entity_route_iqs_link_is_entity_scoped(tmp_path):
    """The declaration is built for THIS entity (never a cached one)."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_A')
    assert code == 200, reply
    declaration = reply['data']['iqs_link']
    assert declaration['status'] in {'available', 'partial', 'unreadable', 'unconfigured'}
    # the observation context is only advertised when the owner can address
    # a formal observation for this entity
    assert declaration.get('supported_context')


def test_entity_route_honours_the_return_context(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_A%2Fquickscan')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == \
        'http://127.0.0.1:43210/company/ENT_A/quickscan'


def test_entity_route_collapses_a_cross_scope_return(tmp_path):
    """A return naming another company is never echoed back."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN


def test_entity_route_does_not_depend_on_ui_generated_answers(tmp_path):
    """Entity reads are owner-owned; the UI repository is not a data source."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_A')
    assert code == 200, reply
    data = reply['data']
    assert 'draft_runs' not in data
    assert 'draft_source_status' not in data
    assert 'iqs_link' in data


def test_entity_route_reads_only_never_writes(tmp_path):
    """The entity read performs no owner write."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    owner = service._gateway('owner')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_A')
    assert code == 200, reply
    assert owner.entity_calls == ['ENT_A']
    assert owner.company_calls == []


def test_entity_route_still_refuses_an_unknown_entity(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_MISSING')
    assert code == 404
    assert reply['error']['code'] == 'entity_not_found'


# ---------------------------------------------------------------------------
# CROSS-ID-DASHBOARD-RETURN: a cross-scope company return naming the
# Dashboard's business entity is confirmed only through a StockWiki-verified
# dual-workspace mapping; everything else keeps the B03 fallback while the
# entity payload stays readable.
# ---------------------------------------------------------------------------

CROSS_RETURN = ('http://127.0.0.1:43210/company/ENT_OTHER/quickscan'
                '?listing_id=LST_OTHER')


class RecordingBridge:
    """A fake mapping verifier whose verdict the test pins."""

    instances = []

    def __init__(self, config):
        self.config = config
        self.calls = []
        self.verdict = {'confirmed': True, 'reason': None, 'detail': {}}
        RecordingBridge.instances.append(self)

    def verify(self, r25_entity_id, return_to):
        self.calls.append((r25_entity_id, return_to))
        return dict(self.verdict)


def service_with_bridge(tmp_path, bridge_factory, **config):
    path = tmp_path / 'config' / 'dashboard.local.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding='utf8')
    return DashboardService(tmp_path, owner_factory=Owner, execution_factory=Execution,
                            return_bridge_factory=bridge_factory)


def test_entity_route_confirms_a_verified_cross_id_return(tmp_path):
    """The exact original-business address is echoed once StockWiki confirms."""
    bridge = RecordingBridge
    service = service_with_bridge(tmp_path, bridge, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan%3Flisting_id%3DLST_OTHER')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == CROSS_RETURN
    # the verdict is about THIS entity and THIS exact return text
    assert bridge.instances[-1].calls == [
        ('ENT_A', 'http://127.0.0.1:43210/company/ENT_OTHER/quickscan?listing_id=LST_OTHER')]
    # the entity payload itself is untouched by the confirmation
    assert reply['data']['entity']['entity_id'] == 'ENT_A'


def test_link_route_confirms_a_verified_cross_id_return(tmp_path):
    """`/api/product/link` funnels through the same confirmation."""
    origin = 'http://127.0.0.1:43219'
    service = service_with_bridge(tmp_path, RecordingBridge, dashboard_origin=origin)
    code, reply = service.dispatch(
        'GET', '/api/product/link?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan%3Flisting_id%3DLST_OTHER')
    assert code == 200 and reply['data']['return_to'] == CROSS_RETURN
    # company/result composes its iqs_link through the identical
    # `_iqs_link` call (after the owner projection read), so this route
    # covers the shared confirmation; the projection fixtures live in
    # test_dashboard_company_result.py.


def test_entity_route_degrades_a_refused_cross_id_return(tmp_path):
    """Wrong listing / unverified mapping: fallback echo, payload readable."""

    class RefusingBridge(RecordingBridge):
        def __init__(self, config):
            super().__init__(config)
            self.verdict = {'confirmed': False,
                            'reason': 'listing_coordinates_mismatch', 'detail': {}}

    service = service_with_bridge(tmp_path, RefusingBridge,
                                  dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan%3Flisting_id%3DLST_OTHER')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN
    assert reply['data']['entity']['entity_id'] == 'ENT_A'
    assert reply['data']['observations'] == []


def test_entity_route_degrades_when_the_bridge_raises(tmp_path):
    """An unusable verifier is a degraded return, never a broken entity read."""
    def exploding_factory(config):
        raise RuntimeError('bridge construction failed')
    service = service_with_bridge(tmp_path, exploding_factory,
                                  dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan%3Flisting_id%3DLST_OTHER')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN


def test_entity_route_does_not_call_the_bridge_for_same_id_returns(tmp_path):
    """The B03 same-entity echo keeps working with zero identity-bridge cost."""
    before = len(RecordingBridge.instances)
    service = service_with_bridge(tmp_path, RecordingBridge, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_A%2Fquickscan%3Flisting_id%3DLST_A')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == \
        'http://127.0.0.1:43210/company/ENT_A/quickscan?listing_id=LST_A'
    assert len(RecordingBridge.instances) == before, 'no verifier may be constructed'


def test_entity_route_never_verifies_a_foreign_or_hash_return(tmp_path):
    """External hosts and hash-form cross-scope returns collapse untouched."""
    before = len(RecordingBridge.instances)
    service = service_with_bridge(tmp_path, RecordingBridge, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2Fevil.example%2Fcompany%2FENT_OTHER%2Fquickscan')
    assert code == 200
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return=%23%2Fcompany%2FENT_OTHER%2Fquickscan')
    assert code == 200
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN
    assert len(RecordingBridge.instances) == before, 'no verifier may be constructed' 


def test_entity_route_collapses_a_cross_scope_return_without_a_bridge(tmp_path):
    """No bridge configured: the historical B03 behaviour is byte-identical."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN


def test_entity_view_route_carries_the_same_declaration_top_level(tmp_path):
    """The UI's primary read confirms a cross-workspace return identically.

    The declaration rides at the TOP level of the entity-view payload so the
    projected `entity` stays byte-identical to the plain entity route.
    """
    service = service_with_bridge(tmp_path, RecordingBridge,
                                  dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch(
        'GET', '/api/product/entity-view?id=ENT_A&return='
        'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan%3Flisting_id%3DLST_OTHER')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == CROSS_RETURN
    assert 'iqs_link' not in reply['data']['entity'], 'the entity payload stays pure'
    code, reply = service.dispatch('GET', '/api/product/entity-view?id=ENT_A')
    assert code == 200, reply
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN
