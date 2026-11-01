"""B03: the company assessment projection over dispatch, HTTP and worker.

Covers the owner company result/history reads end to end on the IQS service
side: the extended company return-route boundary (hash company routes,
trusted-loopback absolute returns, cross-scope refusal, duplicate-key
refusal), the two new independent GET routes over a fake owner, and — when
the B03 StockWiki worktree is available — the real worker subprocess against
a real isolated owner workspace. GET reads perform no business write.
"""
from pathlib import Path
import copy
import http.client
import http.server
import json
import os
import subprocess
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import dashboard_company_projection as projection
import dashboard_iqs_link as link
from dashboard_http import product_handler
from dashboard_service import DashboardService, ProductError


RESULT_SNAPSHOT = {
    'result_id': 'cas_137748bc730fc0b965ea',
    'status': 'formal',
    'entity_id': 'ENT_A',
    'listing_id': 'LST_1',
    'analysis_subject_id': None,
    'information_cutoff': '2026-09-30',
    'registered_at': '2026-11-01T00:00:00Z',
    'questionnaire_version': '3.2.0',
    'scale_version': '2.0.0',
    'module_package_id': 'modpkg_1',
    'module_release_id': 'rel_1',
    'completeness': {'manifest_question_count': 3, 'observed_count': 3, 'missing_question_ids': []},
    'qualification': {'receipted_observation_count': 0, 'unreceipted_observation_count': 3, 'receipts': {}},
    'aggregate_score': None,
    'aggregate_score_reason': 'company_aggregate_authority_missing',
    'observation_refs': [
        {'observation_id': 'obs_a', 'question_id': 'IQS_A', 'field_id': 'score.iqs_a',
         'response_kind': 'score', 'payload_sha256': '0' * 64, 'question_version': '2.0.0'},
    ],
    'verification': {'observation_store': 'verified', 'mismatched_observation_ids': []},
    'honesty': {'financial_accuracy_proven': False, 'formal_research_accepted': False},
}


def _owner_result_payload(entity_id='ENT_A', result=None, reason=None):
    return {
        'protocol': projection.PROJECTION_PROTOCOL,
        'projection_version': projection.PROJECTION_VERSION,
        'entity_id': entity_id,
        'read': 'result',
        'owner_payload': {
            'protocol': 'stockwiki.company_assessment/1',
            'schema_version': '1.0.0',
            'store_id': 'qsobs_x',
            'registry_store_id': 'qsca_x',
            'result': result,
            'reason_code': reason,
            'network_calls': 0,
            'llm_calls': 0,
        },
        'network_calls': 0,
        'llm_calls': 0,
    }


class Owner:
    def __init__(self, config):
        self.config = config
        self.company_calls = []

    def status(self):
        return {'available': True, 'network_calls': 0}

    def history(self, entity_id):
        return {'observations': [
            {'observation_id': 'OBS_1', 'publication_status': 'published', 'analysis_subject_id': None},
        ], 'available': True}

    def company_result(self, entity_id, result_id=None):
        self.company_calls.append(('result', entity_id, result_id))
        if entity_id == 'ENT_MISSING':
            raise ProductError('entity_not_found', 'No registered entity has this ID', 404)
        return _owner_result_payload(entity_id, result=RESULT_SNAPSHOT)

    def company_history(self, entity_id, limit=20, offset=0):
        self.company_calls.append(('history', entity_id, limit, offset))
        return {
            'protocol': projection.PROJECTION_PROTOCOL,
            'projection_version': projection.PROJECTION_VERSION,
            'entity_id': entity_id,
            'read': 'history',
            'owner_payload': {
                'protocol': 'stockwiki.company_assessment/1',
                'schema_version': '1.0.0',
                'registry_store_id': 'qsca_x',
                'registry_state': 'available',
                'items': [{
                    'result_id': RESULT_SNAPSHOT['result_id'], 'status': 'formal',
                    'information_cutoff': '2026-09-30', 'registered_at': '2026-11-01T00:00:00Z',
                    'questionnaire_version': '3.2.0', 'scale_version': '2.0.0',
                    'manifest_question_count': 3, 'observed_count': 3,
                    'aggregate_score': None, 'aggregate_score_reason': 'company_aggregate_authority_missing',
                }],
                'page': {'limit': limit, 'offset': offset, 'total': 1},
                'network_calls': 0,
                'llm_calls': 0,
            },
            'network_calls': 0,
            'llm_calls': 0,
        }

    def search(self, *args, **kwargs):
        return {'rows': [], 'total': 0, 'snapshot': {'ordered_ids': []}}


class Execution:
    def __init__(self, config):
        self.config = config

    def status(self):
        return {'available': False, 'blocked_reasons': ['not_configured']}

    def tasks(self, **kwargs):
        return {'tasks': []}


def service_for(tmp_path, owner=Owner, **config):
    path = tmp_path / 'config' / 'dashboard.local.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding='utf8')
    return DashboardService(tmp_path, owner_factory=owner, execution_factory=Execution)


# -- company return-route boundary --------------------------------------------


def test_company_hash_routes_are_accepted_with_bounded_params():
    assert link.safe_return_to('#/company/ENT_A') == '#/company/ENT_A'
    assert link.safe_return_to('#/company/ENT_A/quickscan?listing_id=LST_1') == \
        '#/company/ENT_A/quickscan?listing_id=LST_1'
    assert link.safe_return_to('#/company/ENT_A/documents?analysis_subject_id=SUBJ_1') == \
        '#/company/ENT_A/documents?analysis_subject_id=SUBJ_1'
    for tab in ('overview', 'research', 'forecast'):
        assert link.safe_return_to(f'#/company/ENT_A/{tab}') != link.FALLBACK_RETURN


def test_company_routes_reject_ambiguous_or_foreign_values():
    # duplicated key: ambiguous scope injection
    assert link.safe_return_to('#/company/ENT_A/quickscan?listing_id=A&listing_id=B') == \
        link.FALLBACK_RETURN
    # unknown query key on a company route
    assert link.safe_return_to('#/company/ENT_A?observation=x') == link.FALLBACK_RETURN
    # unknown tab (not a Dashboard router tab)
    assert link.safe_return_to('#/company/ENT_A/notatab') == link.FALLBACK_RETURN
    # malformed entity segment
    assert link.safe_return_to('#/company/../escape') == link.FALLBACK_RETURN
    assert link.safe_return_to('#/company/ENT%5FA') == link.FALLBACK_RETURN
    # second fragment splice
    assert link.safe_return_to('#/company/ENT_A#x') == link.FALLBACK_RETURN
    # encoded control characters
    assert link.safe_return_to('#/company/ENT_A%0d') == link.FALLBACK_RETURN


def test_absolute_company_returns_accept_only_trusted_loopback():
    good = 'http://127.0.0.1:43210/company/ENT_A/quickscan?listing_id=LST_1'
    assert link.safe_return_to(good) == good
    localhost = 'http://localhost:8080/company/ENT_A'
    assert link.safe_return_to(localhost) == localhost
    foreign = 'http://evil.example/company/ENT_A/quickscan'
    assert link.safe_return_to(foreign) == link.FALLBACK_RETURN
    protocol_relative = '//evil.example/company/ENT_A'
    assert link.safe_return_to(protocol_relative) == link.FALLBACK_RETURN
    non_company = 'http://127.0.0.1:43210/results'
    assert link.safe_return_to(non_company) == link.FALLBACK_RETURN
    fragment = 'http://127.0.0.1:43210/company/ENT_A#/results'
    assert link.safe_return_to(fragment) == link.FALLBACK_RETURN
    dup = 'http://127.0.0.1:43210/company/ENT_A?listing_id=A&listing_id=B'
    assert link.safe_return_to(dup) == link.FALLBACK_RETURN
    dead_port = 'http://127.0.0.1:0/company/ENT_A'
    assert link.safe_return_to(dead_port) == link.FALLBACK_RETURN


def test_company_return_entity_extraction_and_scope_match():
    assert link.company_return_entity('#/company/ENT_A/quickscan?listing_id=L') == 'ENT_A'
    assert link.company_return_entity('http://127.0.0.1:1/company/ENT_B') == 'ENT_B'
    assert link.company_return_entity('#/results') is None
    assert link.company_return_entity('http://127.0.0.1:1/results') is None


def test_old_logical_routes_keep_their_original_semantics():
    assert link.safe_return_to('#/results?offset=50') == '#/results?offset=50'
    assert link.safe_return_to('#/universe') == '#/universe'
    assert link.safe_return_to('#//evil.example') == link.FALLBACK_RETURN


# -- projection shaping --------------------------------------------------------


def test_project_result_passes_the_owner_snapshot_through_verbatim():
    response = projection.project_result(_owner_result_payload(result=RESULT_SNAPSHOT))
    assert response['company_result'] == RESULT_SNAPSHOT
    assert response['reason_code'] is None
    assert response['protocol'] == projection.PROJECTION_PROTOCOL


def test_project_result_keeps_honest_absence_instead_of_zero():
    for reason in ('company_result_not_registered', 'company_assessment_registry_absent',
                   'observation_store_missing', 'observation_store_unavailable'):
        response = projection.project_result(_owner_result_payload(result=None, reason=reason))
        assert response['company_result'] is None
        assert response['reason_code'] == reason


def test_project_result_refuses_an_owner_aggregate_score():
    forged = dict(RESULT_SNAPSHOT, aggregate_score=88)
    with pytest.raises(projection.ProjectionError) as error:
        projection.project_result(_owner_result_payload(result=forged))
    assert error.value.code == 'owner_projection_invalid'


def test_project_result_refuses_a_reasonless_absence():
    with pytest.raises(projection.ProjectionError):
        projection.project_result(_owner_result_payload(result=None, reason=None))


def test_project_history_shapes_items_and_page():
    payload = Owner(None).company_history('ENT_A', limit=20, offset=0)
    response = projection.project_history(payload, limit=20, offset=0)
    assert response['page'] == {'limit': 20, 'offset': 0, 'total': 1}
    assert response['items'][0]['aggregate_score'] is None


def test_project_history_refuses_a_page_that_ignores_the_request():
    payload = Owner(None).company_history('ENT_A', limit=20, offset=0)
    with pytest.raises(projection.ProjectionError) as error:
        projection.project_history(payload, limit=5, offset=0)
    assert error.value.code == 'owner_projection_invalid'
    forged = copy.deepcopy(payload)
    forged['owner_payload']['items'] = forged['owner_payload']['items'] * 30
    with pytest.raises(projection.ProjectionError):
        projection.project_history(forged, limit=20, offset=0)


def test_project_history_allows_a_valid_past_end_empty_page():
    # `offset > total` is a legitimate empty page (the owner answers exactly
    # that); only a page that carries rows beyond the total is malformed.
    payload = Owner(None).company_history('ENT_A', limit=1, offset=2)
    payload['owner_payload']['items'] = []
    payload['owner_payload']['page'] = {'limit': 1, 'offset': 2, 'total': 1}
    response = projection.project_history(payload, limit=1, offset=2)
    assert response['items'] == [] and response['page']['total'] == 1
    empty = Owner(None).company_history('ENT_A', limit=1, offset=1)
    empty['owner_payload']['items'] = []
    empty['owner_payload']['page'] = {'limit': 1, 'offset': 1, 'total': 0}
    assert projection.project_history(empty, limit=1, offset=1)['items'] == []
    # rows beyond the total stay refused
    over = Owner(None).company_history('ENT_A', limit=1, offset=1)
    over['owner_payload']['page'] = {'limit': 1, 'offset': 1, 'total': 1}
    over['owner_payload']['items'] = over['owner_payload']['items'][:1]
    with pytest.raises(projection.ProjectionError):
        projection.project_history(over, limit=1, offset=1)


def test_project_result_refuses_a_mismatched_entity():
    item = dict(RESULT_SNAPSHOT, entity_id='ENT_OTHER')
    with pytest.raises(projection.ProjectionError) as error:
        projection.project_result(_owner_result_payload(result=item))
    assert error.value.code == 'owner_projection_invalid'


def test_owner_read_envelope_protocol_is_checked():
    # A future owner shape must not be relabelled under this projection
    # version: the owner's own protocol/schema declaration is checked.
    good = {'protocol': projection.OWNER_PROTOCOL,
            'schema_version': projection.OWNER_SCHEMA_VERSION,
            'network_calls': 0, 'llm_calls': 0}
    assert projection._checked_owner_read(dict(good)) == good
    with pytest.raises(projection.ProjectionError) as error:
        projection._checked_owner_read({**good, 'protocol': 'stockwiki.company_assessment/9'})
    assert error.value.code == 'owner_protocol_unsupported'
    with pytest.raises(projection.ProjectionError) as error:
        projection._checked_owner_read({**good, 'schema_version': '9.9.9'})
    assert error.value.code == 'owner_protocol_unsupported'
    with pytest.raises(projection.ProjectionError):
        projection._checked_owner_read({**good, 'network_calls': 3})


# -- dispatch level ------------------------------------------------------------


def test_company_result_route_returns_snapshot_with_entity_scoped_link(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/result?id=ENT_A&return='
                                   'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_A%2Fquickscan%3Flisting_id%3DLST_1')
    assert code == 200, reply
    data = reply['data']
    assert data['company_result']['result_id'] == RESULT_SNAPSHOT['result_id']
    assert data['company_result']['aggregate_score'] is None
    assert data['iqs_link']['return_to'] == 'http://127.0.0.1:43210/company/ENT_A/quickscan?listing_id=LST_1'
    assert data['iqs_link']['base_origin'] == 'http://127.0.0.1:43219'



@pytest.mark.parametrize('suffix', [
    '&result_id=',
    '&result_id=cas_first&result_id=cas_second',
])
def test_company_result_route_rejects_empty_or_repeated_result_id_without_owner_read(tmp_path, suffix):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    owner = service._gateway('owner')
    code, reply = service.dispatch('GET', '/api/product/company/result?id=ENT_A' + suffix)
    assert code == 400
    assert reply['error']['code'] == 'invalid_query'
    assert owner.company_calls == []


def test_company_result_route_passes_explicit_result_id_without_latest_fallback(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    owner = service._gateway('owner')
    result_id = RESULT_SNAPSHOT['result_id']
    code, reply = service.dispatch(
        'GET', f'/api/product/company/result?id=ENT_A&result_id={result_id}')
    assert code == 200, reply
    assert owner.company_calls == [('result', 'ENT_A', result_id)]

def test_company_result_route_refuses_cross_scope_return(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/result?id=ENT_A&return='
                                   'http%3A%2F%2F127.0.0.1%3A43210%2Fcompany%2FENT_OTHER%2Fquickscan')
    assert code == 200
    # A return naming another company collapses to the plain fallback.
    assert reply['data']['iqs_link']['return_to'] == link.FALLBACK_RETURN


def test_company_history_route_bounds_and_paging(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/history?id=ENT_A&limit=1&offset=0')
    assert code == 200
    assert reply['data']['page'] == {'limit': 1, 'offset': 0, 'total': 1}
    code, reply = service.dispatch('GET', '/api/product/company/history?id=ENT_A&limit=0')
    assert code == 400
    code, reply = service.dispatch('GET', '/api/product/company/history?id=ENT_A&limit=51')
    assert code == 400
    code, reply = service.dispatch('GET', '/api/product/company/history?id=ENT_A&limit=bogus')
    assert code == 400


def test_company_routes_require_an_entity(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/result')
    assert code == 400
    assert reply['error']['code'] == 'entity_required'


def test_company_result_unknown_entity_is_a_404(tmp_path):
    service = service_for(tmp_path, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/result?id=ENT_MISSING')
    assert code == 404
    assert reply['error']['code'] == 'entity_not_found'


def test_company_absence_is_returned_as_a_named_reason_not_zero(tmp_path):
    class EmptyOwner(Owner):
        def company_result(self, entity_id, result_id=None):
            return _owner_result_payload(entity_id, result=None,
                                         reason='company_result_not_registered')

    service = service_for(tmp_path, owner=EmptyOwner, dashboard_origin='http://127.0.0.1:43219')
    code, reply = service.dispatch('GET', '/api/product/company/result?id=ENT_A')
    assert code == 200
    data = reply['data']
    assert data['company_result'] is None
    assert data['reason_code'] == 'company_result_not_registered'


# -- real HTTP boundary ---------------------------------------------------------


def _serve(tmp_path, owner=Owner):
    service = service_for(tmp_path, owner=owner, dashboard_origin='http://127.0.0.1:43219')

    class Static(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), product_handler(Static, service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def test_company_routes_over_real_http(tmp_path):
    server, port = _serve(tmp_path)
    try:
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        connection.request('GET', '/api/product/company/history?id=ENT_A&limit=5',
                           headers={'Host': f'127.0.0.1:{port}'})
        response = connection.getresponse()
        assert response.status == 200
        body = json.loads(response.read().decode('utf-8'))
        assert body['ok'] is True
        assert body['data']['items'][0]['result_id'] == RESULT_SNAPSHOT['result_id']
        # cross-site origin stays refused on the new GET route too
        connection.request('GET', '/api/product/company/history?id=ENT_A', headers={
            'Host': f'127.0.0.1:{port}', 'Origin': 'http://evil.example',
            'Sec-Fetch-Site': 'cross-site'})
        assert connection.getresponse().status == 403
    finally:
        server.shutdown()
        server.server_close()


# -- real worker subprocess (needs the B03 StockWiki worktree) ------------------

B03_STOCKWIKI_ROOT = Path(os.environ.get(
    'B03_STOCKWIKI_ROOT',
    str(Path(__file__).resolve().parents[2] / 'dashboard-owner-sw-b03-assessments')))


def _seed_workspace(root: Path) -> None:
    """Seed an isolated owner workspace through public entry points only."""
    script = f'''
import sys
sys.path.insert(0, r"{B03_STOCKWIKI_ROOT}")
from pathlib import Path
sys.path.insert(0, r"{B03_STOCKWIKI_ROOT / 'tests'}")
from test_public_company_assessments import (
    _workspace, _manifest, _published_observation, _import_observations,
    _register_request, E01,
)
from stockwiki.public_company_assessments import register_company_assessment
paths = _workspace(Path(r"{root}"))
manifest = _manifest()
_import_observations(paths, manifest, [
    _published_observation(E01, qid, f"obs_{{qid.lower()}}", manifest=manifest)
    for qid in manifest["questions"]
])
outcome = register_company_assessment(paths, _register_request(E01, manifest))
print(outcome["result_id"])
'''
    done = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, timeout=300)
    assert done.returncode == 0, done.stderr.decode('utf-8', 'replace')
    return done.stdout.decode('utf-8').strip()


@pytest.mark.skipif(not (B03_STOCKWIKI_ROOT / 'stockwiki' / 'public_company_assessments.py').is_file(),
                    reason='B03 StockWiki worktree is not available next to this service tree')
def test_company_reads_through_the_real_owner_worker(tmp_path):
    from dashboard_owner import OwnerGateway

    root = tmp_path / 'owner-workspace'
    root.mkdir(parents=True, exist_ok=True)
    result_id = _seed_workspace(root)
    config = {
        'stockwiki_root': str(B03_STOCKWIKI_ROOT),
        'stockwiki_python': sys.executable,
        'workspace_root': str(root),
        'iqs_root': str(Path(__file__).resolve().parents[1]),
        'timeout_seconds': 120,
        'bundles': {},
    }
    gateway = OwnerGateway(config)
    answer = gateway.company_result('ENT_11111111-1111-4111-8111-111111111111')
    assert answer['protocol'] == projection.PROJECTION_PROTOCOL
    snapshot = answer['owner_payload']['result']
    assert snapshot['result_id'] == result_id
    assert snapshot['aggregate_score'] is None
    assert snapshot['status'] == 'reference'
    history = gateway.company_history('ENT_11111111-1111-4111-8111-111111111111', limit=5, offset=0)
    assert history['owner_payload']['page']['total'] == 1
    absent = gateway.company_result('ENT_11111111-1111-4111-8111-111111111111',
                                    result_id='cas_00000000000000000000')
    assert absent['owner_payload']['result'] is None
    assert absent['owner_payload']['reason_code'] == 'company_result_not_registered'
    with pytest.raises(Exception):
        gateway.company_history('ENT_11111111-1111-4111-8111-111111111111', limit=0)
