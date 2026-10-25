"""Independent original StockQA ACK boundary probe, fully temporary/offline."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STOCKQA = ROOT.parent / 'StockQAbyLLM'
sys.path.insert(0, str(STOCKQA))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fixture = load('review_native_q10_fixture', STOCKQA / 'tests/unit/test_q10_delivery.py')
product = load('review_product_execution', ROOT / 'scripts/dashboard_execution.py')
report = {'paid_API_calls': 0, 'real_owner': 'StockQAbyLLM', 'financial_qualification': False}

with tempfile.TemporaryDirectory(prefix='native-ack-', dir=Path(__file__).parent) as temporary:
    folder = Path(temporary)
    store = fixture._store(folder)
    lifecycle = fixture._lifecycle(store)
    records, mapping, acks = [], {}, []
    for qid in ('IQS_05', 'IQS_06'):
        seeded = fixture._seed_checkpoint(store, lifecycle, qid)
        work = seeded['handle']['work_item_id']
        package = fixture._build_package(fixture._checkpoint_payload(store, work), fixture._c06_authority())
        record = store.prepare_result_delivery(work, package)
        records.append((work, record))
        mapping[record['observation_id']] = work
        acks.append(fixture._ack_for(record, ack_id='ack_review_' + qid))
    bundle = {'work_store': str(store.path), 'work_item_ids': mapping}
    gateway = product.ExecutionGateway({'stockqa_root': str(STOCKQA), 'stockqa_python': sys.executable,
        'state_root': str(folder / 'references')})
    bound = gateway.bind_delivery_consumer(bundle, fixture.JR2_CONSUMER,
                                          'operator-config:review-ui-product27')
    assert bound['status'] == 'bound'
    report['consumer_binding'] = bound['status']

    for label, field, value in [('foreign_store', 'consumer', {**fixture.JR2_CONSUMER, 'store_id': 'foreign-store'}),
                                ('wrong_hash', 'payload_sha256', '0' * 64)]:
        wrong = copy.deepcopy(acks)
        wrong[0][field] = value
        try:
            gateway.acknowledge_delivery(bundle, {'acks': wrong})
            raise AssertionError(label + '_accepted')
        except product.DashboardExecutionError as error:
            report[label] = error.code
        assert all(store.get_result_delivery(work)['state'] == 'ready' for work, _ in records)
    try:
        gateway.bind_delivery_consumer({**bundle, 'work_item_ids': {'not_the_original_observation': records[0][0]}},
                                       fixture.JR2_CONSUMER, 'operator-config:review-ui-product27')
        raise AssertionError('wrong_observation_accepted')
    except product.DashboardExecutionError as error:
        report['wrong_observation_mapping'] = error.code
    try:
        gateway.acknowledge_delivery({}, {'acks': acks})
        raise AssertionError('unregistered_owner_accepted')
    except product.DashboardExecutionError as error:
        report['missing_registration'] = error.code

    # A partial native outcome is retained, then exact replay settles only the
    # remaining original work. This exercises crash/retry semantics, not a DB copy.
    partly_wrong = copy.deepcopy(acks)
    partly_wrong[1]['payload_sha256'] = '0' * 64
    try:
        gateway.acknowledge_delivery(bundle, {'acks': partly_wrong})
        raise AssertionError('partial_wrong_ack_accepted')
    except product.DashboardExecutionError as error:
        report['partial_batch_error'] = error.code
    assert [store.get_result_delivery(work)['state'] for work, _ in records] == ['delivered', 'ready']
    report['partial_states'] = ['delivered', 'ready']
    result = gateway.acknowledge_delivery(bundle, {'acks': acks})
    assert result['status'] == 'delivered'
    replay = gateway.acknowledge_delivery(bundle, {'acks': acks})
    assert replay == result
    report['exact_retry'] = result['status']
    report['exact_replay_unchanged'] = replay == result

report['temporary_directory_removed'] = not folder.exists()
print(json.dumps(report))
