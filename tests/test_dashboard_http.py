"""Product HTTP boundary; ephemeral listener, no model calls or production writes."""
from pathlib import Path
import hashlib
import http.client
import http.server
import json
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dashboard_http import product_handler
from dashboard_service import DashboardService


class Owner:
    def __init__(self, config): self.config = config
    def status(self): return {'available': True, 'network_calls': 0}
    def search(self, *args, **kwargs): return {'args': args, 'selection': kwargs, 'snapshot': {'ordered_ids':['e1','e2']}}
    def coverage(self): return {'field_catalog': []}
    def universe_apply(self, body): return {'applied': True, 'payload': body}


class Execution:
    def __init__(self, config): self.config = config
    def status(self): return {'available': False, 'blocked_reasons': ['not_configured']}
    def tasks(self, **kwargs): return {'tasks': [{'process_state': 'running', 'launcher_state': 'draining'}]}


@pytest.fixture
def product(tmp_path):
    service = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Execution)
    class Static(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b'static')
        def log_message(self, *args): pass
    handler = product_handler(Static, service)
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        yield service, server.server_address[1], tmp_path
        server.shutdown(); thread.join(timeout=5)
        assert not thread.is_alive()


def call(product, method='GET', path='/api/product/status', body=None, headers=None):
    _, port, _ = product
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw) if raw.startswith(b'{') else raw
    finally: connection.close()


def write_headers(product):
    service, port, _ = product
    return {'Content-Type': 'application/json', 'X-IQS-CSRF': service.csrf_token, 'Origin': f'http://127.0.0.1:{port}'}


def test_status_get_is_readonly_and_returns_token(product):
    _, _, root = product
    before = list(root.rglob('*'))
    status, reply = call(product)
    assert status == 200 and reply['data']['csrf_token']
    assert reply['data']['read_has_model_calls'] is False
    assert list(root.rglob('*')) == before
    assert call(product, path='/app.js') == (200, b'static')


@pytest.mark.parametrize('headers,code', [({'Host':'evil.example'},'invalid_host'),
    ({'Origin':'https://evil.example'},'invalid_origin'), ({'Origin':'null'},'invalid_origin'),
    ({'Sec-Fetch-Site':'cross-site'},'cross_site_request')])
def test_reject_cross_site_and_rebinding(product, headers, code):
    status, reply = call(product, headers=headers)
    assert status == 403 and reply['error']['code'] == code


def test_mutation_requires_token_and_original_route(product):
    status, reply = call(product, 'POST', '/api/product/universe/apply', '{}', {'Content-Type':'application/json'})
    assert status == 403 and reply['error']['code'] == 'csrf_required'
    status, reply = call(product, 'POST', '/api/product/universe/apply', '{"entity_id":"e1"}', write_headers(product))
    assert status == 200 and reply['data']['payload'] == {'entity_id':'e1'}
    assert call(product, 'POST', '/app.js', '{}', write_headers(product))[0] == 405


@pytest.mark.parametrize('body', ['[]', '{"x":NaN}', '{"x":1,"x":2}', '{', '{"x":'+ '['*1100 + '0' + ']'*1100 + '}'])
def test_malformed_json_never_reaches_owner(product, body):
    status, reply = call(product, 'POST', '/api/product/universe/apply', body, write_headers(product))
    assert status == 400 and reply['error']['code'] == 'invalid_json'


def test_setup_revision_credential_and_active_guard(product):
    service, _, root = product
    status, setup = call(product, path='/api/product/setup')
    assert status == 200
    body = {'config': setup['data']['config'], 'revision_sha256': 'stale'}
    assert call(product, 'PUT', '/api/product/setup', json.dumps(body), write_headers(product))[0] == 409
    body['revision_sha256'] = hashlib.sha256(b'').hexdigest()
    body['config']['api_key'] = 'forbidden-test'
    assert call(product, 'PUT', '/api/product/setup', json.dumps(body), write_headers(product))[0] == 400
    del body['config']['api_key']
    service._gateway('execution')
    assert call(product, 'PUT', '/api/product/setup', json.dumps(body), write_headers(product))[1]['error']['code'] == 'execution_active'
    assert not (root/'config/dashboard.local.json').exists()


def test_condition_and_query_validation(product):
    assert call(product, path='/api/product/results?limit=nope')[0] == 400
    assert call(product, path='/api/product/results?filters=%5B%5D')[0] == 400
    status, reply = call(product, path='/api/product/results?conditions=%5B%7B%22field%22%3A%22IQS_01%22%2C%22op%22%3A%22gte%22%2C%22value%22%3A8%7D%5D&condition_combine=any')
    assert status == 200 and reply['data']['selection']['conditions'][0]['value'] == 8
    assert reply['data']['selection']['condition_combine'] == 'any'


def test_original_snapshot_is_bound_to_filters_and_config(product):
    status, reply = call(product, path='/api/product/results?view=quality')
    token = reply['data']['snapshot_token']
    assert status == 200
    status, page = call(product, path=f'/api/product/results?view=quality&offset=50&snapshot_token={token}')
    assert status == 200 and page['data']['selection']['snapshot'] == {'ordered_ids':['e1','e2']}
    assert page['data']['selection']['view'] == 'quality'
    assert call(product, path=f'/api/product/results?view=recovery&offset=50&snapshot_token={token}')[0] == 409
    assert call(product, path='/api/product/results?offset=50')[0] == 409


def test_finished_process_allows_setup_and_unknown_process_blocks_even_on_first_access(tmp_path):
    class Finished(Execution):
        def tasks(self, **kwargs): return {'tasks':[{'process_state':'process_exited','launcher_state':'running'}]}
    finished = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Finished)
    body = {'config': finished.config, 'revision_sha256': hashlib.sha256(b'').hexdigest()}
    assert finished.dispatch('PUT','/api/product/setup',body)[0] == 200
    class Unknown(Execution):
        def tasks(self, **kwargs): return {'tasks':[{'process_state':'needs_original_inspection'}]}
    unknown = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Unknown)
    assert unknown._execution is None
    body={'config':unknown.config,'revision_sha256':unknown._config_revision}
    assert unknown.dispatch('PUT','/api/product/setup',body)[0] == 409


@pytest.mark.parametrize('mapping', [False, True])
def test_import_reconciles_exact_receipt_and_declares_missing_mapping(tmp_path, mapping):
    events=[]
    class ImportOwner(Owner):
        def status(self): return {'available':True,'store_id':'independent-owner-store'}
        def import_preview(self, body): return {'can_apply':True,'preview_token':'bound-preview'}
        def import_apply(self, body):
            events.append('import')
            return {'status':'rejected_or_conflict','receipt':{'acks':[{'status':'rejected'}]}}
    class AckExecution(Execution):
        def tasks(self, **kwargs): return {'tasks':[]}
        def bind_delivery_consumer(self, bundle, target, source):
            events.append('bind')
            assert target['store_id']=='independent-owner-store' and source.startswith('dashboard-owner-status:')
        def acknowledge_delivery(self, bundle, receipt):
            events.append('ack')
            assert receipt=={'acks':[{'status':'rejected'}]}
            return {'status':'owner_rejected','items':[{'state':'rejected'}],'API_requests':0}
    service=DashboardService(tmp_path,owner_factory=ImportOwner,execution_factory=AckExecution)
    service.config['import_bundles']={'B':{'work_store':str(tmp_path/'registered.sqlite'),'work_item_ids':{'obs':'WORK'}} if mapping else {}}
    status,reply=service.dispatch('POST','/api/product/import/apply',{'bundle_id':'B','preview_token':'bound-preview'})
    assert status==200
    assert events==(['bind','import','ack'] if mapping else ['import'])
    assert reply['data']['ack_reconciliation']['status']==('owner_rejected' if mapping else 'not_configured')
