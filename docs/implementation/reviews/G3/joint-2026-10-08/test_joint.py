"""Concentrated J01-J12 assertions; real owner code, synthetic protocol data."""
import copy
import hashlib
import json
import stat
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run as h

BASE = h.OUT
h.OUT = h.OWN / 'logs'
QA = h.OWN / 'cases/a-selected'
SW = h.OWN / 'cases/sw-corrected'
RELEASE = h.OWN / 'independent-release.json'
PRODUCED = json.loads((BASE / 'producer-summary.json').read_text('utf-8'))
INITIAL = json.loads((BASE / 'initial-imports.json').read_text('utf-8'))
ACKS = {row['question_id']: row['result']['receipt']['acks'][0] for row in INITIAL}


def package(qid):
    return json.loads(Path(PRODUCED['packages'][qid]['path']).read_text('utf-8'))


def save(name, value):
    path = h.OWN / 'cases' / name
    h.save(path, value)
    return path


def consumer(label, path, root=SW, release=RELEASE):
    return h.actor('sw', label, dict(op='import', root=str(root), package=str(path), release=str(release)))


@pytest.fixture(scope='module')
def all_imported():
    for qid in PRODUCED['packages']:
        if qid in ACKS:
            continue
        result = consumer('all-' + qid, PRODUCED['packages'][qid]['path'])
        assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'accepted': 1}
        ACKS[qid] = result['receipt']['acks'][0]
    return h.actor('sw', 'all-rows', dict(op='observations', root=str(SW)))


def test_j01_status_low_cycle_and_full_body(all_imported):
    assert all_imported['counts']['observations'] == 31
    rows = {row['question_id']: row['payload'] for row in all_imported['observations']}
    assert rows['IQS_01']['answer']['score'] == 2
    assert rows['IQS_01']['cycle_sensitive'] is True
    assert len(rows['IQS_01']['answer']['evidence']) == 18
    assert rows['IQS_01']['answer']['watch_triggers'] == ['Synthetic watch trigger']
    assert rows['IQS_02']['answer']['status'] == 'insufficient_evidence'
    assert rows['IQS_02']['answer']['score'] is None
    assert rows['IQS_04']['answer']['status'] == 'not_applicable'
    assert rows['IQS_04']['answer']['score'] is None


def test_j02_entry_and_independent_release(all_imported):
    bad = h.actor('qa', 'j02-wrong-entry', dict(op='produce', root=str(h.OWN / 'cases/entrybad'),
                                           wrong_security=True))
    assert bad['cli_exit'] != 0 and bad['key_opens'] == bad['http_sends'] == 0
    assert not bad['database_created']
    root = h.OWN / 'cases/releasebad'
    h.actor('sw', 'j02-seed', dict(op='seed', root=str(root)))
    release = json.loads(RELEASE.read_text('utf-8'))
    release['questions']['IQS_01']['definition_sha256'] = '0' * 64
    path = save('wrong-release.json', release)
    result = consumer('j02-release', PRODUCED['packages']['IQS_01']['path'], root=root, release=path)
    assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'rejected': 1}
    rows = h.actor('sw', 'j02-rows', dict(op='observations', root=str(root)))
    assert rows['counts']['observations'] == 0


def test_j03_independent_execution_and_stable_replay(all_imported):
    second = h.actor('qa', 'j03-independent-cold', dict(op='produce', root=str(h.OWN / 'cases/b'),
             run_label='J108_B', model_resolved='actual-fixture-model-B',
             answers={'IQS_01': dict(score=9, basis='normalized')}))
    assert second['cli_exit'] == 0 and second['http_sends'] == 31
    a = package('IQS_01')['items'][0]['observation']
    b = json.loads(Path(second['packages']['IQS_01']['path']).read_text('utf-8'))['items'][0]['observation']
    assert a['observation_id'] != b['observation_id']
    assert a['execution']['attempt_id'] != b['execution']['attempt_id']
    assert (a['run_id'], a['scan_id']) != (b['run_id'], b['scan_id'])
    save('second-producer.json', second)
    replay = consumer('j03-replay', PRODUCED['packages']['IQS_01']['path'])
    assert replay['receipt']['acks'][0] == ACKS['IQS_01']


def test_j04_duplicate_json_is_refused_before_write(all_imported):
    root = h.OWN / 'cases/duplicate'
    h.actor('sw', 'j04-seed', dict(op='seed', root=str(root)))
    raw = Path(PRODUCED['packages']['IQS_01']['path']).read_text('utf-8')
    original = '"summary":' + json.dumps(package('IQS_01')['items'][0]['observation']['answer']['summary'])
    assert raw.count(original) == 1
    changed = raw.replace(original, '"summary":"Contradictory first value",' + original, 1)
    path = h.OWN / 'cases/duplicate.package.json'
    path.write_text(changed, encoding='utf-8')
    result = consumer('j04-duplicate', path, root=root)
    rows = h.actor('sw', 'j04-rows', dict(op='observations', root=str(root)))
    assert result['cli_exit'] != 0 and rows['counts']['observations'] == 0


def test_j05_package_hash_and_missing_entity(all_imported):
    changed = package('IQS_01')
    changed['items'][0]['observation']['answer']['score'] = 9
    result = consumer('j05-hash', save('bad-hash.json', changed))
    assert result['cli_exit'] == 2 and result['receipt']['error_code'] == 'package_hash_mismatch'
    result = consumer('j05-entity', PRODUCED['packages']['IQS_01']['path'], root=h.OWN / 'cases/noentity')
    assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'rejected': 1}
    assert result['receipt']['acks'][0]['error_code'] == 'missing_entity'


def test_j06_real_ack_roundtrip_and_duplicate_settlement(all_imported):
    begin = h.actor('qa', 'j06-begin', dict(op='begin', root=str(QA)))
    assert begin['state'] == 'send_uncertain'
    package_doc = package('IQS_01')
    # Lost return: read the SAME committed receiver's public durable ACK.
    recovered = h.actor('sw', 'j06-ack-read', dict(op='ack', root=str(SW),
        package_id=package_doc['package_id'], item_id=package_doc['items'][0]['item_id']))
    assert recovered == ACKS['IQS_01']
    path = save('actual-recovered-ack.json', recovered)
    first = h.actor('qa', 'j06-ack-apply', dict(op='ack', root=str(QA), ack=str(path)))
    assert first['accepted'] and first['state'] == 'delivered'
    again = h.actor('qa', 'j06-ack-again', dict(op='ack', root=str(QA), ack=str(path)))
    assert again['accepted'] and again['after'] == first['after']


@pytest.mark.parametrize('field', ['package_id', 'item_id', 'observation_id', 'payload_sha256', 'namespace'])
def test_j07_wrong_ack_keys_leave_state(all_imported, field):
    # Explicit manipulated negative fixture. This is NOT the normal owner ACK
    # and is never counted as a successful production serializer/roundtrip.
    ack = {k: copy.deepcopy(v) for k, v in ACKS['IQS_06'].items() if k not in {'ack_sequence', 'original_import'}}
    if field == 'namespace':
        ack['consumer']['namespace'] = 'foreign_namespace'
    else:
        ack[field] = 'f' * 64
    result = h.actor('qa', 'j07-key-' + field, dict(op='ack', root=str(QA), question_id='IQS_06',
             ack=str(save('ack-bad-' + field + '.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j07_first_wrong_store_is_refused(all_imported):
    # Contract-shaped NEGATIVE only; the actual unprojected ACK fails J06.
    ack = {k: copy.deepcopy(v) for k, v in ACKS['IQS_06'].items() if k not in {'ack_sequence', 'original_import'}}
    ack['consumer']['store_id'] = 'qsobs_unrelated_target'
    result = h.actor('qa', 'j07-wrong-store', dict(op='ack', root=str(QA), question_id='IQS_06',
             ack=str(save('ack-wrong-store.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j08_legacy_additive_upgrade():
    result = h.actor('qa', 'j08-upgrade', dict(op='legacy-upgrade', root=str(h.OWN / 'cases/legacy')))
    assert result['first']['action'] == 'sealed' and result['second']['action'] == 'superseded'
    assert result['old']['package_bytes'] != result['new']['package_bytes']
    assert len(result['revisions']) == 2
    assert len(result['attempts']) == 1


def test_j09_uncertain_restart_never_reasks(all_imported):
    # J06 commits send-intent before its failing raw-ACK application.
    before = h.actor('qa', 'j09-before', dict(op='snapshot', root=str(QA)))
    assert before['delivery']['state'] == 'send_uncertain'
    for op in ['warm', 'seal']:
        result = h.actor('qa', 'j09-' + op, dict(op=op, root=str(QA)))
        assert result['cli_exit'] == 0 and result['extra_http'] == 0
        assert result['before']['attempts'] == result['after']['attempts']
        assert result['after']['delivery']['state'] == 'send_uncertain'
        assert result['before']['delivery']['package_bytes'] == result['after']['delivery']['package_bytes']


def test_j10_stockwiki_backup_watermarks(all_imported):
    before = h.actor('sw', 'j10-before', dict(op='observations', root=str(SW)))
    backup = h.actor('sw', 'j10-backup', dict(op='backup', root=str(SW), action='create', name='joint_before'))
    assert backup['cli_exit'] == 0
    verified = h.actor('sw', 'j10-verify', dict(op='backup', root=str(SW), action='verify', name='joint_before'))
    assert verified['cli_exit'] == 0
    refused = h.actor('sw', 'j10-nonempty-refused', dict(op='backup', root=str(SW), action='restore', name='joint_before'))
    assert refused['cli_exit'] == 2
    assert 'restore_target_not_empty' in refused['stderr']
    target_root = h.OWN / 'cases/restored'
    source = SW / 'backups/quick_scan/joint_before'
    target = target_root / 'backups/quick_scan/joint_before'
    assert not target_root.exists()
    for path in sorted(source.rglob('*')):
        mode = path.lstat()
        assert not path.is_symlink() and not getattr(mode, 'st_file_attributes', 0) & 0x400
        destination = target / path.relative_to(source)
        if stat.S_ISDIR(mode.st_mode):
            destination.mkdir(parents=True, exist_ok=True)
        else:
            assert stat.S_ISREG(mode.st_mode) and mode.st_nlink == 1
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
    restored = h.actor('sw', 'j10-restore', dict(op='backup', root=str(target_root), action='restore', name='joint_before'))
    assert restored['cli_exit'] == 0
    after = h.actor('sw', 'j10-after', dict(op='observations', root=str(target_root)))
    assert before == after
    unchanged = h.actor('sw', 'j10-source-unchanged', dict(op='observations', root=str(SW)))
    assert before == unchanged
    # This assertion does not certify an executor backup or paired recovery.


def test_j11_variants_never_promote_a_high_score(all_imported):
    second = json.loads((h.OWN / 'cases/second-producer.json').read_text('utf-8'))
    imported = consumer('j11-import-second', second['packages']['IQS_01']['path'])
    assert imported['receipt']['summary'] == {'accepted': 1}
    result = h.actor('sw', 'j11-query', dict(op='query', root=str(SW),
             query={'conditions': [{'field': 'score.iqs_01', 'op': '>=', 'value': 8}]}))
    assert result['search']['total'] == 0
    assert result['coverage']['llm_calls'] == result['coverage']['network_calls'] == 0
    fields = [field for group in result['entity']['groups'] for field in group['fields'] if field['question_id'] == 'IQS_01']
    assert fields and all(len(field['variants']) == 2 for field in fields)
    assert {field['score'] for field in fields} == {2, 9}
    assert all(field['ambiguous'] is True for field in fields)
    assert 'score.iqs_01' in result['entity']['score_summary']['ambiguous_fields']


def test_j12_capabilities_keep_fact_and_c06_gaps(all_imported):
    result = h.actor('sw', 'j12-query', dict(op='query', root=str(SW)))
    caps = result['capabilities']
    assert caps['protocol'] == 'stockwiki_w09_read_primitives'
    assert caps['c06_envelope_validated'] is False
    assert caps['facts_available'] is False and caps['fact_relations_available'] is False
    assert caps['llm_calls'] == caps['network_calls'] == 0
