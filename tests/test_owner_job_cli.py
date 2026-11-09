"""Public job façade over the real product transport (loopback HTTP) + CLI.

The service runs with FAKE owner/execution gateways (no model, no network, no
production state); the transport guards, envelope and routing are the real
ones. CLI invocations run against this live origin and their exit codes and
``iqs-job/1`` envelopes are asserted verbatim.
"""
from pathlib import Path
import http.client
import http.server
import json
import socketserver
import subprocess
import sys
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dashboard_http import product_handler
from dashboard_service import DashboardService


class Owner:
    def __init__(self, config):
        self.config = config

    def status(self):
        return {'available': True, 'network_calls': 0}


class Execution:
    started = []
    controls = []
    counter = 0
    runs = {}

    def __init__(self, config):
        self.config = config

    def status(self):
        return {'available': True, 'bundles': [], 'API_requests': 0}

    def start(self, payload):
        Execution.started.append(dict(payload))
        Execution.counter += 1
        run_id = 'run-' + f'{Execution.counter:032x}'
        record = {'run_id': run_id, 'bundle_id': 'b1', 'bundle_fingerprint': 'f' * 64,
                  'entity_id': payload.get('entity_id'), 'started_at': '2026-11-07T00:00:00Z',
                  'process_state': 'running', 'launcher_state': 'running'}
        Execution.runs[run_id] = record
        return {'status': 'started', 'run': record, 'process_started': True,
                'paid_dispatch_started': None}

    def resolve_job_bundle(self, *, bundle_id, entity_id, listing_id, analysis_subject_id, as_of):
        return {'bundle_id': bundle_id or 'b1', 'entity_id': entity_id, 'bundle_fingerprint': 'f' * 64}

    def control(self, run_id, action):
        Execution.controls.append((run_id, action))
        return {'run': {'run_id': run_id}, 'preview': {'inspection_sha256': 'a' * 64,
                'inspection': {'work_items': [{'question_id': 'q1', 'status': 'delivered'}]}}}

    def tasks(self, *, bundle_ids=None, run_ids=None, inspect_owner=True, limit=50, offset=0):
        rows = [dict(row, run_id=run_id) for run_id, row in sorted(Execution.runs.items())
                if run_ids is None or run_id in run_ids]
        return {'tasks': rows[offset:offset + limit], 'total': len(rows), 'offset': offset,
                'limit': limit,
                'next_offset': offset + limit if offset + limit < len(rows) else None,
                'API_requests': 0}


@pytest.fixture
def product(tmp_path):
    service = DashboardService(tmp_path, owner_factory=Owner, execution_factory=Execution)
    Execution.started.clear()
    Execution.controls.clear()
    Execution.counter = 0
    Execution.runs.clear()

    class Static(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'static')

        def log_message(self, *args):
            pass

    handler = product_handler(Static, service)

    class LoopbackServer(http.server.ThreadingHTTPServer):
        def server_bind(self):
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = self.server_address

    with LoopbackServer(('127.0.0.1', 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield service, server.server_address[1], tmp_path
        server.shutdown()
        thread.join(timeout=5)
        assert not thread.is_alive()


def call(product, method='GET', path='/api/product/status', body=None, headers=None):
    _, port, _ = product
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw) if raw.startswith(b'{') else raw
    finally:
        connection.close()


def write_headers(product):
    service, port, _ = product
    return {'Content-Type': 'application/json', 'X-IQS-CSRF': service.csrf_token,
            'Origin': f'http://127.0.0.1:{port}'}


COMMAND = {'command_id': 'dash-cmd-1', 'idempotency_key': 'dash-idem-1',
           'owner': 'invest-quick-scan',
           'company': {'entity_id': 'ENT_HTTP', 'listing_id': None,
                       'analysis_subject_id': None, 'resolution_status': 'resolved',
                       'display_name': 'HTTP Company'},
           'requested_action': 'run_scan',
           'explicit_scope': {'scope_version': '1', 'scan_kind': 'formal',
                              'universe_id': None, 'questionnaire_version': None},
           'as_of': None, 'limits_ref': None}


def test_status_declares_job_facade_routes(product):
    status, reply = call(product)
    assert status == 200
    facade = reply['data']['owner_job_facade']
    assert facade['wire_protocol'] == 'iqs-job/1'
    assert facade['mapping_version'] == 'iqs.owner_job_actions/1.0.0'
    assert facade['routes']['submit'] == 'POST jobs/submit'
    assert 'iqs.bundle.spend_authorization' in facade['limits_ref_registry']


def test_submit_requires_csrf_like_every_write(product):
    status, reply = call(product, 'POST', '/api/product/jobs/submit',
                         json.dumps({'command_request': COMMAND}),
                         {'Content-Type': 'application/json'})
    assert status == 403 and reply['error']['code'] == 'csrf_required'
    assert Execution.started == []


def test_submit_get_status_act_list_over_http(product):
    status, reply = call(product, 'POST', '/api/product/jobs/submit',
                         json.dumps({'command_request': COMMAND}), write_headers(product))
    assert status == 200
    data = reply['data']
    run_id = data['command']['owner_job_id']
    assert run_id.startswith('run-')
    assert Execution.started == [{'entity_id': 'ENT_HTTP', 'bundle_id': 'b1', 'bundle_fingerprint': 'f' * 64}]
    view = data['job_view']
    assert view['owner_job_id'] == run_id and view['cost_state'] == 'unknown'

    # Same key over HTTP replays the same job without a second dispatch.
    status, replay = call(product, 'POST', '/api/product/jobs/submit',
                          json.dumps({'command_request': COMMAND}), write_headers(product))
    assert status == 200 and replay['data']['attached'] is True
    assert replay['data']['command']['owner_job_id'] == run_id
    assert len(Execution.started) == 1

    status, fetched = call(product, path=f'/api/product/jobs/{run_id}')
    assert status == 200
    assert fetched['data']['job_view']['status'] == 'running'
    assert fetched['data']['annotation']['work_completion_authoritative'] is False

    status, binding = call(product, path='/api/product/jobs/commands/dash-cmd-1')
    assert status == 200
    assert binding['data']['command']['owner_job_id'] == run_id
    assert binding['data']['command']['return_to'] is None

    status, listing = call(product, path='/api/product/jobs?limit=10')
    assert status == 200
    assert listing['data']['page']['total'] >= 1
    assert listing['data']['work_completion_authoritative_default'] is False

    status, acted = call(product, 'POST', f'/api/product/jobs/{run_id}/reconcile',
                         json.dumps({'idempotency_key': 'dash-act-1'}), write_headers(product))
    assert status == 200
    assert acted['data']['action_result']['outcome'] == 'inspected'
    assert Execution.controls == [(run_id, 'inspect')]
    status, replayed = call(product, 'POST', f'/api/product/jobs/{run_id}/reconcile',
                            json.dumps({'idempotency_key': 'dash-act-1'}), write_headers(product))
    assert status == 200 and replayed['data']['replayed'] is True
    assert Execution.controls == [(run_id, 'inspect')]


def test_submit_draft_scope_refused_over_http(product):
    draft = {**COMMAND, 'command_id': 'dash-draft', 'idempotency_key': 'dash-draft-1',
             'explicit_scope': {'scope_version': '1', 'scan_kind': 'draft',
                                'universe_id': None, 'questionnaire_version': None}}
    status, reply = call(product, 'POST', '/api/product/jobs/submit',
                         json.dumps({'command_request': draft}), write_headers(product))
    assert status == 409 and reply['error']['code'] == 'draft_scan_not_exposable'
    assert Execution.started == []


def test_invalid_job_ids_rejected_at_boundary(product):
    status, reply = call(product, path='/api/product/jobs/evil-id')
    assert status in (404, 405) and reply['ok'] is False
    status, reply = call(product, 'POST', '/api/product/jobs/run-11111111111111111111111111111111/retry',
                         json.dumps({'idempotency_key': 'k'}), write_headers(product))
    # Unknown run reaches the facade and fails honestly as an owner-side refusal.
    assert status in (404, 409) and reply['ok'] is False


def run_cli(port, *argv, request=None, stdin_text=None):
    import os
    command = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'scripts' / 'owner_job_cli.py'),
               '--origin', f'http://127.0.0.1:{port}', *argv]
    input_text = stdin_text
    if request is not None:
        input_text = json.dumps(request)
    return subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                          input=input_text, timeout=30,
                          env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'})


def test_cli_help_and_protocol(product):
    _, port, _ = product
    done = subprocess.run([sys.executable, '-B', '-X', 'utf8',
                           str(ROOT / 'scripts' / 'owner_job_cli.py'), '--help'],
                          capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert done.returncode == 0
    assert 'iqs-job/1' in done.stdout
    for operation in ('submit', 'get-status', 'allowed-actions', 'act', 'list-jobs', 'get-command'):
        assert operation in done.stdout


def test_cli_rejects_non_loopback_origin(product):
    _, port, _ = product
    done = subprocess.run([sys.executable, '-B', '-X', 'utf8',
                           str(ROOT / 'scripts' / 'owner_job_cli.py'),
                           '--origin', 'http://evil.example:1', '--operation', 'list-jobs'],
                          capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert done.returncode == 2
    envelope = json.loads(done.stdout)
    assert envelope['protocol'] == 'iqs-job/1' and envelope['ok'] is False
    assert envelope['error']['code'] == 'origin_invalid'


def test_cli_submit_status_act_list_end_to_end(product):
    _, port, _ = product
    done = run_cli(port, '--operation', 'submit', request={'command_request': COMMAND})
    assert done.returncode == 0, done.stderr
    envelope = json.loads(done.stdout)
    assert envelope['protocol'] == 'iqs-job/1' and envelope['ok'] is True
    run_id = envelope['data']['command']['owner_job_id']
    assert run_id.startswith('run-')
    assert len(Execution.started) == 1

    done = run_cli(port, '--operation', 'get-status', '--owner-job-id', run_id)
    assert done.returncode == 0
    status_envelope = json.loads(done.stdout)
    assert status_envelope['data']['job_view']['status'] == 'running'

    done = run_cli(port, '--operation', 'allowed-actions', '--owner-job-id', run_id)
    assert done.returncode == 0
    actions = json.loads(done.stdout)['data']
    assert actions['allowed_actions'] == []  # known-running: no cancel/retry, no pending need
    assert actions['mapping_version'] == 'iqs.owner_job_actions/1.0.0'

    done = run_cli(port, '--operation', 'act', '--owner-job-id', run_id,
                   '--action', 'reconcile', '--idempotency-key', 'cli-act-1')
    assert done.returncode == 0
    acted = json.loads(done.stdout)
    assert acted['data']['action_result']['outcome'] == 'inspected'
    done = run_cli(port, '--operation', 'act', '--owner-job-id', run_id,
                   '--action', 'reconcile', '--idempotency-key', 'cli-act-1')
    assert done.returncode == 0
    assert json.loads(done.stdout)['data']['replayed'] is True
    assert Execution.controls == [(run_id, 'inspect')]

    done = run_cli(port, '--operation', 'list-jobs', '--limit', '10')
    assert done.returncode == 0
    page = json.loads(done.stdout)['data']
    assert page['page']['total'] >= 1
    assert page['protocol'] == 'iqs-job/1'

    done = run_cli(port, '--operation', 'get-command', '--command-id', 'dash-cmd-1')
    assert done.returncode == 0
    assert json.loads(done.stdout)['data']['command']['owner_job_id'] == run_id


def test_cli_maps_owner_business_refusal_to_exit_2(product):
    _, port, _ = product
    done = run_cli(port, '--operation', 'act', '--owner-job-id', 'run-' + '9' * 32,
                   '--action', 'retry', '--idempotency-key', 'cli-retry')
    assert done.returncode == 2
    envelope = json.loads(done.stdout)
    assert envelope['ok'] is False
    assert envelope['error']['code'] == 'retry_forbidden'


def test_cli_transport_failure_is_exit_1(product):
    done = subprocess.run([sys.executable, '-B', '-X', 'utf8',
                           str(ROOT / 'scripts' / 'owner_job_cli.py'),
                           '--origin', 'http://127.0.0.1:9', '--operation', 'list-jobs',
                           '--timeout-seconds', '2'],
                          capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert done.returncode == 1
    envelope = json.loads(done.stdout)
    assert envelope['error']['code'] == 'transport_error'
