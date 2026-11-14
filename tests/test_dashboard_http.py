"""Product HTTP boundary; ephemeral listener, no model calls or production writes."""
from pathlib import Path
import hashlib
import http.client
import http.server
import json
import socketserver
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dashboard_http import product_handler
from dashboard_service import DashboardService


class LoopbackServer(http.server.ThreadingHTTPServer):
    def server_bind(self):
        # Keep the literal loopback fixture independent of DNS and OS settings.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address


class Owner:
    def __init__(self, config): self.config = config; self.requests = {}; self.history = []
    def status(self): return {'available': True, 'network_calls': 0}
    def search(self, *args, **kwargs): return {'args': args, 'selection': kwargs, 'snapshot': {'ordered_ids':['e1','e2']}}
    def coverage(self): return {'field_catalog': []}
    def universe_apply(self, body): return {'applied': True, 'payload': body}
    def universe_preview(self, body):
        return {'status': 'preview', 'can_apply': True, 'preview_token': 'preview-1',
                'member': {'version': 0}, 'entity': {'identity_revision': 2}}
    def membership_request_read(self, body):
        key = body.get('idempotency_key')
        value = self.requests.get((body.get('universe_id'), key)) if key else None
        if body.get('request_id'):
            value = next((row for row in self.requests.values()
                          if row['request']['request_id'] == body['request_id']), None)
        return value or {'status': 'not_found'}
    def membership_request_apply(self, body):
        canonical = {key: body[key] for key in ('action', 'universe_id', 'entity_id', 'reason',
                                                 'priority', 'pin', 'expected_member_version',
                                                 'expected_identity_revision')}
        receipt = {'protocol': 'stockwiki.membership_request/1.0.0', 'status': 'applied',
                   'request_id': 'REQ_HTTP', 'request_scope': 'ws:default', 'workspace_scope': 'ws',
                   'universe_id': body['universe_id'], 'entity_id': body['entity_id'],
                   'action': body['action'], 'idempotency_key': body['idempotency_key'],
                   'payload_sha256': 'sha-http', 'canonical_payload': canonical,
                   'member_version': 1, 'created_at': '2026-11-12T00:00:00Z',
                   'member': {'entity_id': body['entity_id'], 'version': 1}}
        request = {**receipt, 'receipt': receipt}
        self.requests[(body['universe_id'], body['idempotency_key'])] = {
            'status': 'found', 'request': request}
        self.history = [{'version': 1, 'snapshot': receipt['member']}]
        return receipt
    def membership_history(self, body):
        return {'universe_id': body['universe_id'], 'entity_id': body['entity_id'],
                'items': self.history[:body['limit']], 'total': len(self.history),
                'limit': body['limit'], 'after_version': body['after_version'],
                'version_pin': body['version_pin'] or len(self.history), 'has_more': False,
                'next_after_version': self.history[-1]['version'] if self.history else None}


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
    with LoopbackServer(('127.0.0.1', 0), handler) as server:
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


def test_membership_request_public_routes_replay_and_history_over_http(product):
    semantic = {'action': 'add', 'universe_id': 'default', 'entity_id': 'ENT_HTTP',
                'reason': 'http test', 'priority': 0, 'pin': False}
    status, preview = call(product, 'POST', '/api/product/universe/preview',
                           json.dumps(semantic), write_headers(product))
    assert status == 200 and preview['data']['status'] == 'preview'
    request = {**semantic, 'idempotency_key': 'HTTP-1',
               'preview_token': preview['data']['preview_token']}
    status, applied = call(product, 'POST', '/api/product/universe/apply',
                           json.dumps(request), write_headers(product))
    assert status == 200 and applied['data']['status'] == 'applied'
    assert applied['data']['request_protocol'] == 'iqs.dashboard.member_request/1.0.0'

    # A lost-response retry needs no still-current preview token.
    retry = {**semantic, 'idempotency_key': 'HTTP-1'}
    status, replay = call(product, 'POST', '/api/product/universe/apply',
                          json.dumps(retry), write_headers(product))
    assert status == 200 and replay['data']['status'] == 'replayed'
    assert replay['data']['request_id'] == applied['data']['request_id']

    status, receipt = call(product, path='/api/product/universe/request?universe_id=default&idempotency_key=HTTP-1')
    assert status == 200 and receipt['data']['status'] == 'found'
    assert receipt['data']['request']['request_id'] == applied['data']['request_id']
    status, history = call(product, path='/api/product/universe/history?universe_id=default&entity_id=ENT_HTTP')
    assert status == 200 and [row['version'] for row in history['data']['items']] == [1]


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


def test_saving_identical_persisted_setup_does_not_check_or_interrupt_active_work(tmp_path):
    class Busy(Execution):
        def active_references(self):
            raise AssertionError('an unchanged save must not inspect running work')
    service = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Busy)
    service.config_path.parent.mkdir(parents=True, exist_ok=True)
    service.config_path.write_text(json.dumps(service.config), encoding='utf8')
    service._load()
    execution = service._gateway('execution')
    before = service.config_path.read_bytes(), service.config_path.stat().st_mtime_ns
    body = {'config': service.config, 'revision_sha256': service._config_revision}
    status, reply = service.dispatch('PUT', '/api/product/setup', body)
    assert status == 200, reply
    assert (service.config_path.read_bytes(), service.config_path.stat().st_mtime_ns) == before
    assert service._gateway('execution') is execution
    body['revision_sha256'] = 'stale'
    assert service.dispatch('PUT', '/api/product/setup', body)[1]['error']['code'] == 'stale_setup'


def test_changed_setup_checks_running_references_once_and_keeps_active_guard(tmp_path):
    calls = []
    class Tracked(Execution):
        def active_references(self):
            calls.append('check')
            return {'items': [{'process_state': 'running'}] if len(calls) > 1 else []}
    service = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Tracked)
    body = {'config': {**service.config, 'workspace_label': 'changed'}, 'revision_sha256': service._config_revision}
    assert service.dispatch('PUT', '/api/product/setup', body)[0] == 200
    assert calls == ['check']
    body = {'config': {**service.config, 'workspace_label': 'another'}, 'revision_sha256': service._config_revision}
    assert service.dispatch('PUT', '/api/product/setup', body)[1]['error']['code'] == 'execution_active'
    assert service.config['workspace_label'] == 'changed'


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


def test_old_unbound_snapshot_is_rejected_as_stale_instead_of_crashing(tmp_path):
    service = DashboardService(tmp_path, owner_factory=Owner)
    status, reply = service.dispatch('GET', '/api/product/results')
    assert status == 200
    token = reply['data']['snapshot_token']
    service._snapshots[token].pop('config_revision')
    status, reply = service.dispatch('GET', f'/api/product/results?offset=1&snapshot_token={token}')
    assert status == 409 and reply['error']['code'] == 'snapshot_expired'


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
    body={'config':{**unknown.config,'workspace_label':'actual-change'},'revision_sha256':unknown._config_revision}
    assert unknown.dispatch('PUT','/api/product/setup',body)[0] == 409


@pytest.mark.parametrize('mapping', [False, True])
@pytest.mark.parametrize('can_apply', [True, False])
def test_import_reconciles_exact_receipt_and_declares_missing_mapping(tmp_path, mapping, can_apply):
    events=[]
    class ImportOwner(Owner):
        def status(self): return {'available':True,'store_id':'independent-owner-store'}
        def import_preview(self, body): return {'can_apply':can_apply,'preview_token':'bound-preview'}
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
def test_existing_seal_control_route_forwards_only_empty_explicit_request(product,monkeypatch):
    service,_,_=product
    forwarded=[]
    execution=service._gateway('execution')
    monkeypatch.setattr(execution,'control',lambda run_id,action:forwarded.append((run_id,action)) or {'status':'started','API_requests':0},raising=False)
    status,reply=call(product,'POST','/api/product/tasks/run-original/seal','{}',write_headers(product))
    assert status==200 and reply['data']['status']=='started'
    assert forwarded==[('run-original','seal')]
    assert call(product,'POST','/api/product/tasks/run-original/seal','{"command":"forbidden"}',write_headers(product))[0]==400
    assert len(forwarded)==1


def test_slow_owner_read_does_not_block_setup_or_pause(tmp_path):
    entered, release = threading.Event(), threading.Event()
    replies = []
    class SlowOwner(Owner):
        def coverage(self):
            entered.set()
            assert release.wait(3)
            return {'workspace': self.config['workspace_root']}
    class Controls(Execution):
        def control(self, run_id, action):
            return {'run_id': run_id, 'action': action}
    service = DashboardService(tmp_path, owner_factory=SlowOwner, execution_factory=Controls)
    reader = threading.Thread(target=lambda: replies.append(service.dispatch('GET', '/api/product/coverage')))
    reader.start()
    try:
        assert entered.wait(2)
        finished = threading.Event()
        def unrelated():
            replies.append(service.dispatch('GET', '/api/product/setup'))
            replies.append(service.dispatch('POST', '/api/product/tasks/run-existing/pause'))
            finished.set()
        other = threading.Thread(target=unrelated)
        other.start()
        try:
            assert finished.wait(1), 'slow read held the entire service lock'
        finally:
            release.set()
            other.join(3)
        assert not other.is_alive()
    finally:
        release.set()
        reader.join(3)
    assert not reader.is_alive()
    assert all(status == 200 for status, _ in replies)


@pytest.mark.parametrize('action', ['preview', 'start'])
def test_slow_execution_leaves_reads_available_and_protects_mutation_target(tmp_path, action):
    entered, release, read_done = threading.Event(), threading.Event(), threading.Event()
    replies = {}

    class SlowExecution(Execution):
        def active_references(self):
            return {'items': []}

        def preview(self, body):
            entered.set()
            assert release.wait(5)
            return {'workspace': self.config['workspace_root']}

        start = preview

    service = DashboardService(tmp_path, owner_factory=Owner, execution_factory=SlowExecution)
    original = service.config['workspace_root']
    replacement = str(tmp_path / 'replacement')
    setup_body = {'config': {**service.config, 'workspace_root': replacement},
                  'revision_sha256': service._config_revision}

    def command():
        replies['command'] = service.dispatch('POST', '/api/product/tasks/' + action)

    def read_and_switch():
        replies['read'] = service.dispatch('GET', '/api/product/setup')
        replies['results'] = service.dispatch('GET', '/api/product/results')
        replies['switch'] = service.dispatch('PUT', '/api/product/setup', setup_body)
        read_done.set()

    worker = threading.Thread(target=command)
    reader = threading.Thread(target=read_and_switch)
    worker.start()
    try:
        assert entered.wait(2)
        reader.start()
        assert read_done.wait(2), 'slow execution blocked unrelated reads or configuration handling'
        assert replies['read'][0] == replies['results'][0] == 200
        assert replies['read'][1]['data']['config']['workspace_root'] == original
        if action == 'start':
            assert replies['switch'][0] == 409
            assert replies['switch'][1]['error']['code'] == 'execution_active'
        else:
            assert replies['switch'][0] == 200
    finally:
        release.set()
        worker.join(6)
        if reader.ident is not None:
            reader.join(6)
    assert not worker.is_alive() and not reader.is_alive()
    assert replies['command'][0] == 200
    assert replies['command'][1]['data']['workspace'] == original
    if action == 'start':
        assert service.dispatch('PUT', '/api/product/setup', setup_body)[0] == 200


def test_read_keeps_original_deployment_during_config_change_and_snapshot_cannot_cross(tmp_path):
    entered, release = threading.Event(), threading.Event()
    replies = []
    class SlowOwner(Owner):
        def search(self, *args, **kwargs):
            if not kwargs.get('snapshot'):
                entered.set()
                assert release.wait(3)
            return {'workspace': self.config['workspace_root'], 'snapshot': {'ordered_ids': ['original']}}
    class Idle(Execution):
        def active_references(self): return {'items': []}
    service = DashboardService(tmp_path, owner_factory=SlowOwner, execution_factory=Idle)
    service.config['workspace_root'] = str(tmp_path / 'original')
    reader = threading.Thread(target=lambda: replies.append(service.dispatch('GET', '/api/product/results')))
    reader.start()
    try:
        assert entered.wait(2)
        finished = threading.Event()
        config_replies = []
        def change():
            config_replies.append(service.dispatch('PUT', '/api/product/setup', {
                'config': {**service.config, 'workspace_root': str(tmp_path / 'replacement')},
                'revision_sha256': service._config_revision}))
            finished.set()
        writer = threading.Thread(target=change)
        writer.start()
        try:
            assert finished.wait(1), 'read must not hold the setup lock during owner I/O'
        finally:
            release.set()
            writer.join(3)
        assert config_replies[0][0] == 200, config_replies
    finally:
        release.set()
        reader.join(3)
    assert not reader.is_alive()
    status, result = replies[0]
    assert status == 200 and result['data']['workspace'] == str(tmp_path / 'original')
    token = result['data']['snapshot_token']
    status, result = service.dispatch('GET', f'/api/product/results?offset=50&snapshot_token={token}')
    assert status == 409 and result['error']['code'] == 'snapshot_expired'


@pytest.mark.parametrize('document', ['{', '[]', '{"runs":{}}', '{"runs":["bad-row"]}'])
def test_entity_reads_ignore_ui_generated_answers(tmp_path, monkeypatch, document):
    class FormalOwner(Owner):
        def entity(self, entity_id): return {'entity': {'entity_id': entity_id}, 'groups': ['formal']}
        def entity_view(self, entity_id): return {'entity': self.entity(entity_id), 'temporal_shadow': {}}
    service = DashboardService(tmp_path, owner_factory=FormalOwner)
    source = tmp_path/'ui/src/generated/answers.json'
    source.parent.mkdir(parents=True)
    source.write_text(document, encoding='utf8')
    original = Path.read_text
    def read(path, *args, **kwargs):
        if path == source:
            raise AssertionError('IQS product route read a UI-owned answer file')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    for endpoint in ('entity', 'entity-view'):
        status, reply = service.dispatch('GET', f'/api/product/{endpoint}?id=ENT_FORMAL')
        assert status == 200, reply
        formal = reply['data']['entity'] if endpoint == 'entity-view' else reply['data']
        assert formal['groups'] == ['formal']
        assert 'draft_runs' not in formal and 'draft_source_status' not in formal


def test_new_deployment_defaults_and_template_do_not_select_a_historical_experiment(tmp_path):
    from dashboard_service import defaults, validate_config
    for historical in ('runs/r25-live/owner-workspace', 'runs/c16b/native-owner-alphabet-01/owner-workspace'):
        (tmp_path / historical).mkdir(parents=True)
    value = defaults(tmp_path)
    assert value['workspace_root'] == '' and value['iqs_release_root'] == ''
    template = json.loads((Path(__file__).resolve().parents[1]/'examples/dashboard.config.template.json').read_text(encoding='utf8'))
    assert template['workspace_root'] == '' and template['iqs_release_root'] == ''
    explicit = {**value, 'workspace_root': str(tmp_path/'existing'), 'iqs_release_root': str(tmp_path/'existing-release')}
    assert validate_config(explicit, tmp_path)['workspace_root'] == explicit['workspace_root']
