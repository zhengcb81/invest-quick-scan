"""Exercise the delivery contract without a real owner or paid request."""

import hashlib
import json
from pathlib import Path
import sys

import pytest

from scripts import dashboard_delivery as delivery
from scripts.dashboard_execution import DashboardExecutionError, ExecutionGateway

REQUEST = 'stockqa.delivery_scope_request/1.0.0'
RESPONSE = 'stockqa.delivery_scope_response/1.0.0'


@pytest.fixture
def registered_delivery(tmp_path):
    ledger = tmp_path / 'ledger.sqlite'
    ledger.write_bytes(b'original outbox')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text('{}', encoding='utf-8')
    request = {'entity_id': 'ENT_TEST', 'question_ids': ['Q2', 'Q1']}
    admission = tmp_path / 'admission.json'
    admission.write_text(json.dumps({'work_store': str(ledger)}), encoding='utf-8')
    inspection = tmp_path / 'inspection.json'
    inspection.write_text(json.dumps(request), encoding='utf-8')
    bundle = {
        'entity_id': 'ENT_TEST', 'company_preparation_id': 'prepared-test',
        'confirmation_id': 'rc2_' + 'a' * 64, 'manifest': str(manifest),
        'admission_config': str(admission), 'inspection_request': str(inspection),
    }
    gateway = ExecutionGateway({
        'bundles': {'original': bundle}, 'state_root': str(tmp_path / 'state'),
        'stockqa_root': str(tmp_path / 'owner'), 'stockqa_python': sys.executable,
    })
    return gateway, bundle, request, ledger, manifest


def test_delivery_owns_scope_and_registration_retains_its_fingerprint(registered_delivery):
    gateway, bundle, _, ledger, manifest = registered_delivery
    expected = {
        'entity_id': 'ENT_TEST', 'work_store': str(ledger.resolve()),
        'manifest': str(manifest.resolve()), 'question_ids': ['Q1', 'Q2'],
        'confirmation_id': bundle['confirmation_id'],
        'scope_bindings': {qid: {'scope': 'entity', 'scope_id': 'ENT_TEST'} for qid in ('Q1', 'Q2')},
    }
    assert delivery.describe_delivery_scope(bundle) == expected
    encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    assert gateway.delivery_registration('original') == {
        'company_preparation_id': 'prepared-test', 'bundle_id': 'original', 'entity_id': 'ENT_TEST',
        'delivery_scope': expected, 'bundle_fingerprint': hashlib.sha256(encoded).hexdigest(),
        'API_requests': 0,
    }
    assert not gateway.state_root.exists()


def test_delivery_rejects_bad_scope_and_missing_confirmation_before_transport(registered_delivery):
    gateway, bundle, request, _, _ = registered_delivery
    del bundle['confirmation_id']
    with pytest.raises(DashboardExecutionError) as exc:
        delivery.read_delivery_receivers(bundle=bundle, config=gateway.config,
                                         state_root=gateway.state_root, call=lambda *a, **k: pytest.fail('owner call'))
    assert exc.value.code == 'delivery_original_scope_unavailable'
    assert not gateway.state_root.exists()

    request['question_ids'] = ['Q1', 'Q1']
    Path(bundle['inspection_request']).write_text(json.dumps(request), encoding='utf-8')
    with pytest.raises(DashboardExecutionError) as exc:
        delivery.describe_delivery_scope(bundle)
    assert exc.value.code == 'delivery_work_mapping_missing'


def test_public_receiver_uses_original_scope_without_creating_runtime(registered_delivery):
    gateway, bundle, request, ledger, _ = registered_delivery
    request['scope_bindings'] = {'Q2': {'scope': 'security', 'scope_id': 'SEC_TEST'}}
    Path(bundle['inspection_request']).write_text(json.dumps(request), encoding='utf-8')
    root = Path(gateway.config['stockqa_root'])
    owner_module = root / 'src/utils/quick_scan_delivery_scope_cli.py'
    owner_module.parent.mkdir(parents=True)
    owner_module.write_text(
        "import json, sys\n"
        "from pathlib import Path\n"
        "assert Path.cwd() == Path(__file__).resolve().parents[2]\n"
        "assert len(sys.argv) == 3 and sys.argv[1] == '--ledger'\n"
        "request = json.load(sys.stdin)\n"
        f"assert request['protocol'] == {REQUEST!r}\n"
        "assert request['operation'] == 'receivers'\n"
        "assert request['scope']['question_ids'] == ['Q2', 'Q1']\n"
        "assert request['scope']['confirmation_id'] == 'rc2_' + 'a' * 64\n"
        "assert request['scope']['scope_bindings'] == {'Q2': {'scope': 'security', 'scope_id': 'SEC_TEST'}}\n"
        f"print(json.dumps(dict(protocol={RESPONSE!r}, operation='receivers', status='ok',\n"
        "    result=dict(items=[], work_items=[], consumers=[{'work_store':sys.argv[2]}]),\n"
        "    API_requests=0, network_calls=0)))\n",
        encoding='utf-8',
    )
    expected = {
        'API_requests': 0, 'network_calls': 0,
        'items': [], 'work_items': [], 'consumers': [{'work_store': str(ledger)}],
    }
    assert delivery.read_delivery_receivers(bundle=bundle, config=gateway.config,
                                            state_root=gateway.state_root, call=gateway._call) == expected
    assert gateway.delivery_receivers('original') == expected
    assert ledger.read_bytes() == b'original outbox'
    assert not gateway.state_root.exists()


@pytest.mark.parametrize('patch', [
    {'protocol': 'stockqa.delivery_scope_response/2.0.0'},
    {'operation': 'export'},
    {'status': 'rejected'},
    {'API_requests': False},
    {'network_calls': 1},
    {'result': {'items': [], 'work_items': [], 'consumers': [None]}},
])
def test_receiver_refuses_an_incompatible_owner_response(registered_delivery, patch):
    gateway, _, _, ledger, _ = registered_delivery
    Path(gateway.config['stockqa_root']).mkdir()

    def owner_call(command, root, cwd, *, input_value):
        assert root == cwd
        assert command[-4:] == ['-m', 'src.utils.quick_scan_delivery_scope_cli', '--ledger', str(ledger)]
        assert input_value['protocol'] == REQUEST and input_value['operation'] == 'receivers'
        return {
            'protocol': RESPONSE, 'operation': 'receivers', 'status': 'ok',
            'result': {'items': [], 'work_items': [], 'consumers': []},
            'API_requests': 0, 'network_calls': 0, **patch,
        }

    gateway._call = owner_call
    with pytest.raises(DashboardExecutionError) as exc:
        gateway.delivery_receivers('original')
    assert exc.value.code == 'owner_delivery_contract_invalid'
    assert ledger.read_bytes() == b'original outbox'


@pytest.mark.parametrize(('operation', 'status', 'rows'), [
    ('bind', 'bound', []),
    ('bind', 'bound', [{'work_item_id': 'work-A', 'binding_sha256': 'short'},
                      {'work_item_id': 'work-B', 'binding_sha256': 'b' * 64}]),
    ('bind', 'bound', [{'work_item_id': 'work-A', 'binding_sha256': 'a' * 64}] * 2),
    ('acknowledge', 'delivered', [{'observation_id': 'foreign', 'work_item_id': 'work-A', 'state': 'delivered'},
                                  {'observation_id': 'obs-B', 'work_item_id': 'work-B', 'state': 'ack_missing'}]),
    ('acknowledge', 'delivered', [{'observation_id': 'obs-A', 'work_item_id': 'work-A', 'state': 'delivered'},
                                  {'observation_id': 'obs-B', 'work_item_id': 'work-B', 'state': 'ack_missing'}]),
    ('acknowledge', 'owner_rejected', [{'observation_id': 'obs-A', 'work_item_id': 'work-B', 'state': 'ack_rejected'},
                                      {'observation_id': 'obs-B', 'work_item_id': 'work-B', 'state': 'ack_missing'}]),
    ('acknowledge', 'owner_rejected', [{'observation_id': 'obs-A', 'work_item_id': 'work-A', 'state': 'ack_missing'},
                                      {'observation_id': 'obs-B', 'work_item_id': 'work-B', 'state': 'ack_missing'}]),
])
def test_delivery_control_rejects_inexact_owner_row_binding(registered_delivery, operation, status, rows):
    gateway, bundle, _, ledger, _ = registered_delivery
    Path(gateway.config['stockqa_root']).mkdir()
    bundle.update(work_store=str(ledger), work_item_ids={'obs-A': 'work-A', 'obs-B': 'work-B'})
    gateway._call = lambda *args, **kwargs: {
        'protocol': 'stockqa.delivery_control_response/1.0.0', 'operation': operation,
        'status': status, 'items': rows, 'API_requests': 0, 'network_calls': 0,
    }
    with pytest.raises(DashboardExecutionError) as exc:
        if operation == 'bind':
            gateway.bind_delivery_consumer(bundle, {'store_id': 'receiver'}, 'isolated-ref')
        else:
            gateway.acknowledge_delivery(bundle, {'acks': [{'observation_id': 'obs-A', 'status': 'accepted'}]})
    assert exc.value.code == 'owner_delivery_control_invalid'
    assert ledger.read_bytes() == b'original outbox'


@pytest.mark.parametrize('invalid', ['"status":"rejected",', '"duration":1e999,'])
def test_stockqa_projection_rejects_ambiguous_owner_json(registered_delivery, invalid):
    gateway, _, _, ledger, _ = registered_delivery
    root = Path(gateway.config['stockqa_root'])
    command = root / 'src/utils/quick_scan_delivery_scope_cli.py'
    command.parent.mkdir(parents=True)
    valid = json.dumps({'protocol': RESPONSE, 'operation': 'receivers', 'status': 'ok',
                        'result': {'items': [], 'work_items': [], 'consumers': []},
                        'API_requests': 0, 'network_calls': 0})
    command.write_text(f'print({("{" + invalid + valid[1:])!r})', encoding='utf-8')
    with pytest.raises(DashboardExecutionError) as exc:
        gateway.delivery_receivers('original')
    assert exc.value.code == 'owner_transport_unavailable'
    assert ledger.read_bytes() == b'original outbox'
