"""Public CLI conformance for the facts wire and the frozen F05 owner wrappers.

Part A drives scripts/query_contract_cli.py exactly like a caller would: a
temporary JSON input file, one subprocess per call, exit code and canonical
output asserted. Part B restores the tracked StockWiki code of the frozen F05
candidate (owner commit 63a6ffcf) into this lab's own temporary directory and
drives the public CLI through the candidate's IqsQueryContract wrappers and
FactsContractAdapter. The candidate repository is only read via git archive;
the restored copy is cleaned up; a native rejection must propagate without
triggering the StockWiki local fallback. Everything is synthetic; no owner
store, no production path, no network.
"""
import copy
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import pytest

import module_contract
import query_facts_contract as fc
from test_query_facts_contract import (digest, fact_request, fact_observation,
                                       fact_owner, fact_pair, fact_profile_result,
                                       projection, strict_pair, three_counterparty_pair)
from test_query_capabilities_facts_wire import build_11, capabilities_request, owner_context

LAB_ROOT = Path(__file__).resolve().parents[1]
CLI = LAB_ROOT / 'scripts' / 'query_contract_cli.py'
OWNER_REPO = Path(os.environ.get(
    'F05_OWNER_LAB_REPO', r'C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab'))
OWNER_COMMIT = '63a6ffcf23f8d16f47acf44bdbcf3e567a85458e'
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


# --------------------------------------------------- Part B: frozen F05 owner

class _OwnerRestore:
    """Tracked code of the frozen F05 candidate restored into a lab temp dir."""

    def __init__(self):
        if not OWNER_REPO.exists():
            pytest.fail(f'frozen F05 owner repository missing: {OWNER_REPO}')
        probe = subprocess.run(['git', '-C', str(OWNER_REPO), 'cat-file', '-t',
                                OWNER_COMMIT], capture_output=True)
        if probe.returncode != 0:
            pytest.fail(f'frozen F05 owner commit missing: {OWNER_COMMIT}')
        archive = subprocess.run(
            ['git', '-C', str(OWNER_REPO), 'archive', '--format=tar', OWNER_COMMIT,
             '--', 'stockwiki', 'config/quick_scan_facts_query.schema.json'],
            check=True, capture_output=True).stdout
        self._temp = tempfile.TemporaryDirectory(prefix='f05-owner-restore-')
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self._temp.name, filter='data')
        self.root = Path(self._temp.name)
        self.scripts = str(LAB_ROOT / 'scripts')
        self._added_scripts = self.scripts not in sys.path
        sys.path.insert(0, str(self.root))
        if self._added_scripts:
            sys.path.insert(0, self.scripts)
        import stockwiki.quick_scan_query_contract as query_contract
        import stockwiki.quick_scan_facts_contract as facts_contract
        import stockwiki.quick_scan_observations as observations
        self.query_contract = query_contract
        self.facts_contract = facts_contract
        self.observations = observations

    def cleanup(self):
        if self._added_scripts and self.scripts in sys.path:
            sys.path.remove(self.scripts)
        sys.path.remove(str(self.root))
        for name in list(sys.modules):
            if name == 'stockwiki' or name.startswith('stockwiki.'):
                del sys.modules[name]
        self._temp.cleanup()


@pytest.fixture()
def owner_env():
    restored = _OwnerRestore()
    try:
        yield restored
    finally:
        restored.cleanup()


def test_frozen_owner_wrappers_drive_the_native_cli(owner_env):
    contract = owner_env.query_contract.IqsQueryContract(
        LAB_ROOT, runs_dir=owner_env.root / 'runs')
    adapter = owner_env.facts_contract.FactsContractAdapter(native=contract)
    request, profile, owner, read_at = strict_pair()
    validated = adapter.validate_facts_request(request)
    assert validated == request
    assert adapter.native_supported is True
    native_hash = adapter.facts_query_sha256(request)
    assert native_hash == owner_env.facts_contract.query_sha256(request)
    assert native_hash == fc.query_sha256(request)
    assert adapter.native_supported is True
    response = adapter.build_facts_response(profile_result=profile,
                                            request=request, owner=owner,
                                            read_at=read_at)
    assert adapter.native_supported is True
    # the IQS native build and the frozen owner local build agree exactly
    assert response == owner_env.facts_contract.build_response(
        profile_result=profile, request=request, owner=owner, read_at=read_at)
    checked = adapter.validate_facts_response(response, request=request,
                                              owner=owner)
    assert checked == response
    assert adapter.native_supported is True


def test_frozen_owner_replay_wrapper_uses_native_response(owner_env):
    contract = owner_env.query_contract.IqsQueryContract(
        LAB_ROOT, runs_dir=owner_env.root / 'runs')
    adapter = owner_env.facts_contract.FactsContractAdapter(native=contract)
    request, profile, owner, read_at = strict_pair()
    response = adapter.build_facts_response(profile_result=profile,
                                            request=request, owner=owner,
                                            read_at=read_at)
    snapshot = response['result']['watermark']['snapshot_id']
    # the replay keeps the original query identity, binds the stored snapshot
    # and may arrive later with a changed request timestamp
    replay = copy.deepcopy(request)
    replay['payload']['snapshot_id'] = snapshot
    replay['requested_at'] = '2026-10-15T08:00:00Z'
    envelope = dict(message_type='response', schema_version='2.7.0',
                    request_id=replay['request_id'],
                    operation=replay['operation'],
                    response_at='2026-10-15T08:01:00Z',
                    result=copy.deepcopy(response['result']))
    assert adapter.validate_facts_response(envelope, request=replay,
                                           owner=owner) == envelope
    assert adapter.native_supported is True


def test_native_rejection_propagates_and_never_triggers_local_fallback(owner_env,
                                                                       monkeypatch):
    contract = owner_env.query_contract.IqsQueryContract(
        LAB_ROOT, runs_dir=owner_env.root / 'runs')
    adapter = owner_env.facts_contract.FactsContractAdapter(native=contract)
    request, _, _, _ = strict_pair()
    invalid = fact_request(mode='strict')  # strict without a declared direction
    calls = []
    monkeypatch.setattr(owner_env.facts_contract, 'validate_request',
                        lambda value: calls.append(value))
    with pytest.raises(owner_env.observations.ObservationImportError) as error:
        adapter.validate_facts_request(invalid)
    assert error.value.error_code == 'subject_contract_output_invalid'
    assert calls == []  # the StockWiki local fallback never executed
    assert adapter.native_supported is None
    # the same native instance still validates the good request afterwards
    assert adapter.validate_facts_request(request) == request
    assert adapter.native_supported is True


def test_unsupported_operation_falls_back_but_rejection_still_propagates(owner_env):
    class Stub:
        def __init__(self, code):
            self.code = code

        def validate_facts_request(self, request):
            raise owner_env.observations.ObservationImportError(self.code)

    request, _, _, _ = strict_pair()
    absent = owner_env.facts_contract.FactsContractAdapter(
        native=Stub('subject_contract_operation_unsupported'))
    assert absent.validate_facts_request(request) == request
    assert absent.native_supported is False
    rejected = owner_env.facts_contract.FactsContractAdapter(
        native=Stub('subject_contract_output_invalid'))
    with pytest.raises(owner_env.observations.ObservationImportError) as error:
        rejected.validate_facts_request(request)
    assert error.value.error_code == 'subject_contract_output_invalid'


def test_real_unsupported_operation_triggers_the_fallback(owner_env):
    # the base IQS commit (aca0f4be) has no facts-* operations: its real
    # argparse 'invalid choice' refusal must surface as an ABSENT capability
    # (subject_contract_operation_unsupported) and fall back to the owner
    # local contract — never as a request rejection.
    base_commit = 'aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981'
    archive = subprocess.run(
        ['git', '-C', str(LAB_ROOT), 'archive', '--format=tar', base_commit,
         '--', 'scripts', 'schemas'], check=True, capture_output=True).stdout
    with tempfile.TemporaryDirectory(prefix='f05-base-cli-') as base:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(base, filter='data')
        contract = owner_env.query_contract.IqsQueryContract(
            Path(base), runs_dir=owner_env.root / 'runs')
        adapter = owner_env.facts_contract.FactsContractAdapter(native=contract)
        request, _, _, _ = strict_pair()
        assert adapter.validate_facts_request(request) == request
        assert adapter.native_supported is False
        # the same absent CLI must still reject a genuinely invalid request
        # through the owner local contract
        invalid = fact_request(mode='strict')  # strict without a direction
        with pytest.raises(ValueError, match='facts_direction_required_in_strict'):
            adapter.validate_facts_request(invalid)


def test_frozen_owner_hash_and_cli_hash_are_identical(owner_env):
    contract = owner_env.query_contract.IqsQueryContract(
        LAB_ROOT, runs_dir=owner_env.root / 'runs')
    request, _, _, _ = strict_pair()
    code, out, err = run_cli('facts-query-hash', {'request': request})
    assert code == 0, err
    assert json.loads(out)['result'] == contract.facts_query_sha256(request)
    assert json.loads(out)['result'] == owner_env.facts_contract.query_sha256(request)
