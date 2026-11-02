"""Original SQLite ACK application, with independently scoped invalid members."""
import copy
import json
import subprocess
import sys

import pytest

from test_dashboard_delivery import delivery, TARGET, SOURCE
from scripts.dashboard_owner import _env


def _delivery_rows(bundle):
    script = r'''
import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from src.utils.quick_scan_refresh_inspect import ReadOnlyWorkView
request=json.load(sys.stdin)
view=ReadOnlyWorkView(pathlib.Path(request['work_store']))
print(json.dumps({w:view.get_result_delivery(w) for w in request['work_item_ids'].values()},
                 sort_keys=True,default=lambda v:v.hex()))
'''
    result = subprocess.run([sys.executable, '-B', '-c', script, str(SOURCE)],
        input=json.dumps(bundle), capture_output=True, text=True, encoding='utf8',
        timeout=30, env=_env())
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('mutation', ['hash', 'store'])
@pytest.mark.parametrize('bad_index', [0, 1])
def test_invalid_ack_does_not_block_other_original_ack(delivery, mutation, bad_index):
    gateway, bundle, receipt = delivery
    gateway.bind_delivery_consumer(bundle, TARGET, 'isolated-test')
    wrong = copy.deepcopy(receipt)
    bad = wrong['acks'][bad_index]
    if mutation == 'hash':
        bad['payload_sha256'] = '0' * 64
    else:
        bad['consumer']['store_id'] = 'DIFFERENT_STORE'
    before = _delivery_rows(bundle)
    result = gateway.acknowledge_delivery(bundle, wrong)
    states = {r['observation_id']: r['state'] for r in result['items']}
    assert result['status'] == 'owner_rejected'
    assert states[bad['observation_id']] == 'ack_rejected'
    good = receipt['acks'][1 - bad_index]
    assert states[good['observation_id']] == 'delivered'
    after = _delivery_rows(bundle)
    bad_work = bundle['work_item_ids'][bad['observation_id']]
    assert after[bad_work] == before[bad_work]
    assert gateway.acknowledge_delivery(bundle, receipt)['status'] == 'delivered'
    settled = _delivery_rows(bundle)
    assert gateway.acknowledge_delivery(bundle, receipt)['status'] == 'delivered'
    assert _delivery_rows(bundle) == settled
    assert result['API_requests'] == result['network_calls'] == 0


@pytest.mark.parametrize('received_index', [0, 1])
def test_available_ack_subset_is_applied_and_missing_ack_remains_pending(delivery, received_index):
    gateway, bundle, receipt = delivery
    gateway.bind_delivery_consumer(bundle, TARGET, 'isolated-test')
    partial = copy.deepcopy(receipt)
    partial['acks'] = [partial['acks'][received_index]]
    result = gateway.acknowledge_delivery(bundle, partial)
    states = {row['observation_id']: row['state'] for row in result['items']}
    assert result['status'] == 'owner_rejected'
    assert states[receipt['acks'][received_index]['observation_id']] == 'delivered'
    assert states[receipt['acks'][1-received_index]['observation_id']] == 'ack_missing'
    completed = gateway.acknowledge_delivery(bundle, receipt)
    assert completed['status'] == 'delivered'
    before = _delivery_rows(bundle)
    assert gateway.acknowledge_delivery(bundle, receipt)['status'] == 'delivered'
    assert _delivery_rows(bundle) == before
