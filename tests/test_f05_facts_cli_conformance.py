"""Public CLI conformance for the IQS facts wire.

This suite drives scripts/query_contract_cli.py as an external caller would:
temporary JSON input, one subprocess per operation, and asserted exit code and
canonical output. Cross-repository producer/consumer behavior is exercised by
StockWiki's C06 integration tests through the public CLI; IQS tests do not
import StockWiki implementation modules or depend on its Git object store.
Everything here is synthetic; no owner store, production path, or network.
"""
import ast
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import module_contract
import query_facts_contract as fc
from test_query_facts_contract import (digest, fact_request, fact_observation,
                                       fact_pair, strict_pair,
                                       three_counterparty_pair)
from test_query_capabilities_facts_wire import build_11, capabilities_request, owner_context

LAB_ROOT = Path(__file__).resolve().parents[1]
CLI = LAB_ROOT / 'scripts' / 'query_contract_cli.py'
OUTPUT_FIELDS = {'protocol', 'operation', 'status', 'input_sha256', 'result',
                 'API_requests', 'database_writes', 'identity_attested'}


def run_cli(operation, value=None, *, raw=None):
    """One real subprocess against the public CLI; returns (code, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'input.json'
        path.write_bytes(raw if raw is not None
                         else module_contract.canonical_bytes(value))
        env = {key: os.environ[key] for key in
               ('SYSTEMROOT', 'WINDIR', 'PATH', 'PATHEXT', 'COMSPEC', 'USERPROFILE',
                'APPDATA', 'LOCALAPPDATA', 'SYSTEMDRIVE') if key in os.environ}
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                   PYTHONIOENCODING='utf-8')
        proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(CLI),
                               '--operation', operation, '--input', str(path)],
                              cwd=str(LAB_ROOT / 'scripts'), env=env,
                              capture_output=True, timeout=180)
    return proc.returncode, proc.stdout, proc.stderr


def valid_output(operation, envelope):
    return {'protocol': 'iqs.query_validation/1.0.0', 'operation': operation,
            'status': 'validated', 'input_sha256': digest(envelope),
            'API_requests': 0, 'database_writes': 0, 'identity_attested': False}


def rejected_output(operation):
    return {'protocol': 'iqs.query_validation/1.0.0', 'operation': operation,
            'status': 'rejected', 'error_code': 'query_contract_rejected',
            'API_requests': 0, 'database_writes': 0, 'identity_attested': False}


# ----------------------------------------------------------------- Part A: CLI

def test_cli_facts_request_accepts_and_echoes():
    request, _, _, _ = strict_pair()
    code, out, err = run_cli('facts-request', {'request': request})
    assert code == 0, err
    output = json.loads(out)
    assert set(output) == OUTPUT_FIELDS
    expected = valid_output('facts-request', {'request': request})
    expected['result'] = request
    assert output == expected


def test_cli_facts_capabilities_advertises_semantic_projection_support():
    code, out, err = run_cli('facts-capabilities', {})
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == {
        'protocol':'iqs.facts_contract_capabilities/1.0.0',
        'wire_version':'2.7.0',
        'features':['full_response_validation_v1',
                    'paged_response_projection_v1',
                    'export_response_validation_v1'],
    }


def test_cli_facts_request_rejects_duplicate_json_key():
    request, _, _, _ = strict_pair()
    body = module_contract.canonical_bytes({'request': request})
    raw = body[:-1] + b',"request":{}}'
    code, out, err = run_cli('facts-request', raw=raw)
    assert code == 2
    assert json.loads(out) == rejected_output('facts-request')


def test_cli_facts_request_rejects_wrong_version_extra_field_and_bad_wire():
    request, _, _, _ = strict_pair()
    old = dict(request, schema_version='2.6.0')
    code, out, _ = run_cli('facts-request', {'request': old})
    assert code == 2 and json.loads(out) == rejected_output('facts-request')
    code, out, _ = run_cli('facts-request', {'request': request, 'extra': True})
    assert code == 2 and json.loads(out) == rejected_output('facts-request')
    code, out, _ = run_cli('facts-request', {'request': dict(request, operation='search')})
    assert code == 2 and json.loads(out) == rejected_output('facts-request')


def test_cli_facts_query_hash_matches_contract():
    request, _, _, _ = strict_pair()
    code, out, err = run_cli('facts-query-hash', {'request': request})
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == fc.query_sha256(request)
    # independent derivation, not the contract's own helper
    payload = copy.deepcopy(request['payload'])
    payload.pop('snapshot_id', None)
    payload.pop('page', None)
    if payload['information_cutoff'] is None:
        payload['information_cutoff'] = request['requested_at'][:10]
    independent = digest({'consumer_id': request['consumer_id'],
                          'schema_version': '2.7.0', 'operation': 'query_facts',
                          'payload': payload})
    assert output['result'] == independent


def test_cli_facts_build_then_response_round_trip():
    request, profile, owner, read_at = strict_pair()
    envelope = {'profile_result': profile, 'request': request,
                'owner': owner, 'read_at': read_at}
    code, out, err = run_cli('facts-build', envelope)
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    expected = fc.build_response(profile_result=profile, request=request,
                                 owner=owner, read_at=read_at)
    assert output['result'] == expected
    response_envelope = {'response': expected, 'request': request, 'owner': owner}
    code, out, err = run_cli('facts-response', response_envelope)
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == expected


def test_cli_facts_response_accepts_and_binds_public_page_projection():
    request, profile, owner = three_counterparty_pair()
    request['payload']['page'] = {'page_size': 1, 'cursor': None}
    full = fc.build_response(profile_result=profile, request=request,
                             owner=owner, read_at='2026-10-09T15:00:00Z')
    response = copy.deepcopy(full)
    response['result'] = fc.present_result(full['result'], request['payload'])
    envelope = {'response': response, 'request': request, 'owner': owner}

    code, out, err = run_cli('facts-response', envelope)
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == response

    tampered = copy.deepcopy(envelope)
    tampered['response']['result']['page_facts'][0]['counterparty']['name'] = 'Unrelated'
    code, out, _ = run_cli('facts-response', tampered)
    assert code == 2 and json.loads(out) == rejected_output('facts-response')


def test_cli_facts_response_accepts_strict_page_with_no_strict_rows():
    request, profile, owner, read_at = fact_pair(
        fact_observation(review='unreviewed'),
        overrides={'mode':'strict','direction':'outgoing',
                   'page':{'page_size':1,'cursor':None}})
    full = fc.build_response(profile_result=profile, request=request,
                             owner=owner, read_at=read_at)
    assert len(full['result']['facts']) == 1
    assert full['result']['candidate_total'] == 1
    response = copy.deepcopy(full)
    response['result'] = fc.present_result(full['result'], request['payload'])
    assert response['result']['total'] == 0
    assert response['result']['page_facts'] == []

    code, out, err = run_cli('facts-response',
        {'response':response,'request':request,'owner':owner})
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == response

    tampered = copy.deepcopy(response)
    tampered['result']['candidate_total'] = 0
    code, out, _ = run_cli('facts-response',
        {'response':tampered,'request':request,'owner':owner})
    assert code == 2 and json.loads(out) == rejected_output('facts-response')


def test_cli_facts_response_rejects_tampered_and_missing_fields():
    request, profile, owner, read_at = strict_pair()
    response = fc.build_response(profile_result=profile, request=request,
                                 owner=owner, read_at=read_at)
    tampered = copy.deepcopy(response)
    tampered['result']['watermark']['observation_sequence'] = 99
    code, out, _ = run_cli('facts-response',
                           {'response': tampered, 'request': request,
                            'owner': owner})
    assert code == 2 and json.loads(out) == rejected_output('facts-response')
    code, out, _ = run_cli('facts-build',
                           {'profile_result': profile, 'request': request,
                            'owner': owner})
    assert code == 2 and json.loads(out) == rejected_output('facts-build')


def test_cli_facts_export_response_validates_public_owner_projection():
    request, profile, owner, read_at = fact_pair(
        fact_observation(), overrides=dict(operation='export_facts',
                                            label='synthetic export'))
    internal = fc.build_response(profile_result=profile, request=request,
                                 owner=owner, read_at=read_at)
    body = fc.build_export_body(internal['result'], request,
                                generated_at=read_at)
    result = copy.deepcopy(internal['result'])
    result.update(operation='export_facts', facts=[], page_facts=[],
                  total=len(body['candidates']), next_cursor=None, export=body)
    response = dict(message_type='response', schema_version='2.7.0',
                    request_id=request['request_id'], operation='export_facts',
                    response_at=read_at, result=result)
    envelope = {'response': response, 'request': request, 'owner': owner}

    code, out, err = run_cli('facts-export-response', envelope)
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    assert output['result'] == response

    # Recompute both self-hash fields after mutation. The CLI must still reject
    # because the candidates no longer match the request-bound owner projection.
    changed = copy.deepcopy(envelope)
    changed_body = changed['response']['result']['export']
    changed_body['candidates'] = []
    content = {key: value for key, value in changed_body.items()
               if key not in {'dataset_sha256', 'candidate_set_id'}}
    digest_value = digest(content)
    changed_body['dataset_sha256'] = digest_value
    changed_body['candidate_set_id'] = 'fexp1_' + digest_value
    code, out, _ = run_cli('facts-export-response', changed)
    assert code == 2
    assert json.loads(out) == rejected_output('facts-export-response')


def test_cli_facts_build_rejects_unverified_profile_rows():
    request, profile, owner, read_at = strict_pair()
    profile['profiles'][0]['observations'][0]['payload_sha256'] = '0' * 64
    code, out, _ = run_cli('facts-build',
                           {'profile_result': profile, 'request': request,
                            'owner': owner, 'read_at': read_at})
    assert code == 2 and json.loads(out) == rejected_output('facts-build')


def test_cli_capabilities_wire_declaration_is_routed():
    context = owner_context()
    request = capabilities_request()
    response = build_11(request=request, context=context)
    envelope = {'request': request, 'source_context': context,
                'index': None, 'scope_context': None}
    code, out, err = run_cli('capabilities-build', envelope)
    assert code == 0, err
    output = json.loads(out)
    assert output['status'] == 'validated'
    # the CLI result is the full built response envelope
    wires = output['result']['result']['supported_query_wires']
    assert len(wires) == 7 and wires[-1] == {
        'schema_version': '2.7.0', 'operations': ['query_facts', 'export_facts']}
    code, out, err = run_cli('capabilities-response',
                             {'response': response, 'request': request,
                              'source_context': context, 'index': None,
                              'scope_context': None})
    assert code == 0, err


def test_cli_legacy_query_operations_still_route():
    from test_query_contract_v2 import pair
    request, response, owner = pair()
    code, out, err = run_cli('request', {'request': request})
    assert code == 0, err
    assert json.loads(out)['status'] == 'validated'
    code, out, err = run_cli('response',
                             {'response': response, 'request': request,
                              'owner': owner})
    assert code == 0, err
    assert json.loads(out)['status'] == 'validated'


def test_cli_output_is_canonical_json():
    request, _, _, _ = strict_pair()
    _, out, _ = run_cli('facts-query-hash', {'request': request})
    # the payload itself is canonical; the trailing newline is an OS detail
    assert out.rstrip(b'\r\n') == module_contract.canonical_bytes(json.loads(out))


def test_facts_consumer_cli_does_not_import_stockwiki_implementation():
    """IQS talks to the owner via the versioned public JSON CLI, not imports."""
    paths = (LAB_ROOT / 'scripts' / 'query_facts_contract.py',
             LAB_ROOT / 'scripts' / 'query_contract_cli.py')
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'stockwiki' or alias.name.startswith('stockwiki.'):
                        violations.append(f'{path.name}:{node.lineno}: import {alias.name}')
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'stockwiki' or (node.module or '').startswith('stockwiki.'):
                    violations.append(f'{path.name}:{node.lineno}: from {node.module} import ...')
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == '__import__' and node.args \
                    and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str) \
                    and node.args[0].value.startswith('stockwiki.'):
                violations.append(f'{path.name}:{node.lineno}: dynamic import {node.args[0].value}')
    assert not violations, 'F05 consumer crossed the public CLI boundary:\n' + '\n'.join(violations)
