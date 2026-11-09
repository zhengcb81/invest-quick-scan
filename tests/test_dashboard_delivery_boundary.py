"""Exercise the delivery contract without a real owner or paid request."""

import hashlib
import json
from pathlib import Path
import sys

import pytest

from scripts import dashboard_delivery as delivery
from scripts.dashboard_execution import DashboardExecutionError, ExecutionGateway


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


def test_public_receiver_uses_original_scope_and_cleans_temporary_runtime(registered_delivery):
    gateway, bundle, request, ledger, _ = registered_delivery
    request['scope_bindings'] = {'Q2': {'scope': 'security', 'scope_id': 'SEC_TEST'}}
    Path(bundle['inspection_request']).write_text(json.dumps(request), encoding='utf-8')
    root = Path(gateway.config['stockqa_root'])
    owner_module = root / 'src/utils/quick_scan_refresh_inspect.py'
    owner_module.parent.mkdir(parents=True)
    owner_module.write_text(
        "def delivery_scope_projection(path, request):\n"
        "    return {'API_requests': 0, 'ledger': str(path), 'input': request}\n",
        encoding='utf-8',
    )
    expected = {
        'API_requests': 0, 'ledger': str(ledger),
        'input': {**request, 'confirmation_id': bundle['confirmation_id'], 'receiver_only': True},
    }
    assert delivery.read_delivery_receivers(bundle=bundle, config=gateway.config,
                                            state_root=gateway.state_root, call=gateway._call) == expected
    assert gateway.delivery_receivers('original') == expected
    assert ledger.read_bytes() == b'original outbox'
    assert list(gateway.state_root.iterdir()) == []
