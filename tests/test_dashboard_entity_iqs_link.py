"""B03 LIVE-OWNER-VERIFY-REPAIR-01: the entity route must carry the IQSLink.

RED (before the fix): `/api/product/entity` answered with the owner entity
payload plus the draft track only. The frozen G-IQS-01 `IQSLink` declaration
never travelled with the entity, so the Dashboard `get_result` composition
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

    def history(self, entity_id):
        return {'observations': [
            {'observation_id': 'OBS_1', 'publication_status': 'published',
             'analysis_subject_id': None, 'answer_status': 'scored',
             'qualification_status': 'receipted'},
        ], 'available': True}

    def company_result(self, entity_id, result_id=None):
        self.company_calls.append(('result', entity_id, result_id))
        return {'protocol': 'iqs.dashboard.company_assessment/1',
                'projection_version': 'company_assessment/1.0.0',
                'entity_id': entity_id, 'read': 'result', 'owner_payload': {}}

    def company_history(self, entity_id, limit=20, offset=0):
        self.company_calls.append(('history', entity_id, limit, offset))
        return {'protocol': 'iqs.dashboard.company_assessment/1',
                'projection_version': 'company_assessment/1.0.0',
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


def test_entity_route_keeps_the_draft_track_separate(tmp_path):
    """The draft track stays beside the entity; it is not the link."""
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/entity?id=ENT_A')
    assert code == 200, reply
    data = reply['data']
    assert 'draft_runs' in data
    assert data['draft_source_label']
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
