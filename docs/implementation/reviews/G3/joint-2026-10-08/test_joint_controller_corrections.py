"""Only unexecuted paths/controller corrections; original product REDs retained."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run as h

BASE = h.OUT
h.OUT = h.OWN / 'logs/corrections'
QA = h.OWN / 'cases/a-selected'
SW = h.OWN / 'cases/sw-corrected'
RELEASE = h.OWN / 'independent-release.json'
PRODUCED = json.loads((BASE / 'producer-summary.json').read_text('utf-8'))
ACK = json.loads((BASE / 'suite-actors/all-IQS_07.response.json').read_text('utf-8'))['receipt']['acks'][0]


def save(name, value):
    path = h.OWN / 'cases' / name
    h.save(path, value)
    return path


def test_j03_direct_second_execution_and_replay():
    # Independent successful same-model run. Does NOT repair or mask the
    # earlier actual-model != requested-model checkpoint failure.
    second = h.actor('qa', 'c-j03-direct-cold', dict(op='produce', root=str(h.OWN / 'cases/b-direct'),
                  run_label='J108_B_DIRECT', answers={'IQS_01': dict(score=9, basis='normalized')}))
    assert second['cli_exit'] == 0 and second['http_sends'] == 31
    a = json.loads(Path(PRODUCED['packages']['IQS_01']['path']).read_text('utf-8'))['items'][0]['observation']
    b = json.loads(Path(second['packages']['IQS_01']['path']).read_text('utf-8'))['items'][0]['observation']
    assert a['observation_id'] != b['observation_id']
    assert a['execution']['attempt_id'] != b['execution']['attempt_id']
    assert (a['run_id'], a['scan_id']) != (b['run_id'], b['scan_id'])
    save('direct-second-producer.json', second)
    replay = h.actor('sw', 'c-j03-replay', dict(op='import', root=str(SW),
                  package=PRODUCED['packages']['IQS_01']['path'], release=str(RELEASE)))
    first = json.loads((BASE / 'initial-imports.json').read_text('utf-8'))[0]['result']['receipt']['acks'][0]
    assert replay['receipt']['acks'][0] == first


def test_j05_missing_entity_in_migrated_empty_store():
    root = h.OWN / 'cases/emptyentity'
    h.actor('sw', 'c-j05-empty', dict(op='empty', root=str(root)))
    result = h.actor('sw', 'c-j05-import', dict(op='import', root=str(root),
                     package=PRODUCED['packages']['IQS_01']['path'], release=str(RELEASE)))
    assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'rejected': 1}
    assert result['receipt']['acks'][0]['error_code'] == 'missing_entity'
    rows = h.actor('sw', 'c-j05-rows', dict(op='observations', root=str(root)))
    assert rows['counts']['observations'] == 0


@pytest.fixture(scope='module')
def uncertain_item():
    result = h.actor('qa', 'c-j07-begin', dict(op='begin', root=str(QA), question_id='IQS_07'))
    assert result['state'] == 'send_uncertain'


@pytest.mark.parametrize('field', ['package_id', 'item_id', 'observation_id', 'payload_sha256', 'namespace'])
def test_j07_negative_keys_preserve_full_snapshot(uncertain_item, field):
    # Explicit contract-shaped NEGATIVE only; no stripping for positive ACKs.
    ack = {k: copy.deepcopy(v) for k, v in ACK.items() if k not in {'ack_sequence', 'original_import'}}
    if field == 'namespace':
        ack['consumer']['namespace'] = 'foreign_namespace'
    else:
        ack[field] = 'f' * 64
    result = h.actor('qa', 'c-j07-key-' + field, dict(op='ack', root=str(QA), question_id='IQS_07',
               ack=str(save('c-ack-bad-' + field + '.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j07_wrong_store_cannot_settle_after_send_intent(uncertain_item):
    ack = {k: copy.deepcopy(v) for k, v in ACK.items() if k not in {'ack_sequence', 'original_import'}}
    ack['consumer']['store_id'] = 'qsobs_unrelated_target'
    result = h.actor('qa', 'c-j07-wrong-store', dict(op='ack', root=str(QA), question_id='IQS_07',
                ack=str(save('c-ack-wrong-store.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j11_incomparable_basis_keeps_both_values():
    second = json.loads((h.OWN / 'cases/direct-second-producer.json').read_text('utf-8'))
    imported = h.actor('sw', 'c-j11-import', dict(op='import', root=str(SW),
                     package=second['packages']['IQS_01']['path'], release=str(RELEASE)))
    assert imported['receipt']['summary'] == {'accepted': 1}
    result = h.actor('sw', 'c-j11-query', dict(op='query', root=str(SW),
                     query={'conditions': [{'field': 'score.iqs_01', 'op': '>=', 'value': 8}]}))
    assert result['search']['total'] == 0
    fields = [field for group in result['entity']['groups'] for field in group['fields'] if field['question_id'] == 'IQS_01']
    assert {field['score'] for field in fields} == {2, 9}
    assert all(field['ambiguous'] is True and len(field['variants']) == 2 for field in fields)
    assert 'score.iqs_01' in result['entity']['score_summary']['ambiguous_fields']
    assert result['capabilities']['llm_calls'] == result['capabilities']['network_calls'] == 0
