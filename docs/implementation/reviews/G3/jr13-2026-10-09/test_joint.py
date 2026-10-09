"""Concentrated J01-J12 assertions; real owner code, synthetic protocol data."""
import copy
import hashlib
import json
import stat
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import joint_harness as h
from jsonschema import Draft202012Validator, FormatChecker

QA = h.CASES / 'a-selected'
SW = h.CASES / 'sw-corrected'
RELEASE = h.OWN / 'independent-release.json'
PRODUCED = {}
ACKS = {}
ACK_SCHEMA = json.loads((h.IQS / 'schemas/quick_scan/exchange.schema.json').read_bytes())
ACK_VALIDATOR = Draft202012Validator({'$ref':'#/$defs/ImportAck','$defs':ACK_SCHEMA['$defs']},format_checker=FormatChecker())


def package(qid):
    return json.loads(Path(PRODUCED['packages'][qid]['path']).read_text('utf-8'))


def save(name, value):
    path = h.CASES / name
    h.save(path, value)
    return path


def consumer(label, path, root=SW, release=RELEASE):
    return h.actor('sw', label, dict(op='import', root=str(root), package=str(path), release=str(release)))


@pytest.fixture(scope='module')
def all_imported():
    seed = h.actor('sw', 'jr13-seed', dict(op='seed',root=str(SW)))
    assert seed['identity_state']=='provisional'
    owner = h.actor('sw','jr13-receiver',dict(op='receiver-owner',root=str(SW)))
    assert owner['synthetic_only'] and not ACKS
    PRODUCED.update(h.actor('qa','jr13-cold',dict(op='produce',root=str(QA),run_label='JR13',answers={
        'IQS_01':dict(score=2,large=True),
        'IQS_02':dict(status='insufficient_evidence',score=None),
        'IQS_04':dict(status='not_applicable',score=None,basis='not_applicable')})))
    assert PRODUCED['cli_exit']==0 and len(PRODUCED['packages'])==PRODUCED['http_sends']==31
    before = h.actor('qa','jr13-unbound-before',dict(op='snapshot',root=str(QA)))
    refused = h.actor('qa','jr13-unbound-begin',dict(op='begin',root=str(QA)),expected_code=1)
    assert 'consumer' in refused['stderr']
    after = h.actor('qa','jr13-unbound-after',dict(op='snapshot',root=str(QA)))
    assert before==after
    for qid in ['IQS_01','IQS_06']:
        binding = h.actor('qa','jr13-bind-'+qid,dict(op='bind-consumer',root=str(QA),question_id=qid,
            receiver_descriptor=str(h.CASES/'jr13-receiver.response.json')))
        assert binding['incoming_ack_used_as_authority'] is False
        started = h.actor('qa','jr13-begin-'+qid,dict(op='begin',root=str(QA),question_id=qid))
        assert started['state']=='send_uncertain'
    for qid in PRODUCED['packages']:
        result = consumer('jr13-all-'+qid, PRODUCED['packages'][qid]['path'])
        assert result['cli_exit']==0 and result['receipt']['summary']=={'accepted':1}
        ack=result['receipt']['acks'][0]
        ACK_VALIDATOR.validate(ack)
        assert ack['consumer']==owner['consumer']
        ACKS[qid]=ack
    return h.actor('sw','jr13-all-rows',dict(op='observations',root=str(SW)))


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
    bad = h.actor('qa', 'j02-wrong-entry', dict(op='produce', root=str(h.CASES / 'entrybad'),
                                           wrong_security=True))
    assert bad['cli_exit'] != 0 and bad['key_opens'] == bad['http_sends'] == 0
    assert not bad['database_created']
    root = h.CASES / 'releasebad'
    h.actor('sw', 'j02-seed', dict(op='seed', root=str(root)))
    release = json.loads(RELEASE.read_text('utf-8'))
    release['questions']['IQS_01']['definition_sha256'] = '0' * 64
    path = save('wrong-release.json', release)
    result = consumer('j02-release', PRODUCED['packages']['IQS_01']['path'], root=root, release=path)
    assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'rejected': 1}
    rows = h.actor('sw', 'j02-rows', dict(op='observations', root=str(root)))
    assert rows['counts']['observations'] == 0


def test_j03_independent_execution_and_stable_replay(all_imported):
    second = h.actor('qa', 'j03-independent-cold', dict(op='produce', root=str(h.CASES / 'b'),
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
    root = h.CASES / 'duplicate'
    h.actor('sw', 'j04-seed', dict(op='seed', root=str(root)))
    raw = Path(PRODUCED['packages']['IQS_01']['path']).read_text('utf-8')
    original = '"summary":' + json.dumps(package('IQS_01')['items'][0]['observation']['answer']['summary'])
    assert raw.count(original) == 1
    changed = raw.replace(original, '"summary":"Contradictory first value",' + original, 1)
    path = h.CASES / 'duplicate.package.json'
    path.write_text(changed, encoding='utf-8')
    result = consumer('j04-duplicate', path, root=root)
    rows = h.actor('sw', 'j04-rows', dict(op='observations', root=str(root)))
    assert result['cli_exit'] != 0 and rows['counts']['observations'] == 0


def test_j05_package_hash_and_missing_entity(all_imported):
    changed = package('IQS_01')
    changed['items'][0]['observation']['answer']['score'] = 9
    result = consumer('j05-hash', save('bad-hash.json', changed))
    assert result['cli_exit'] == 2 and result['receipt']['error_code'] == 'package_hash_mismatch'
    empty = h.actor('sw', 'j05-empty-identity', dict(op='empty', root=str(h.CASES / 'noentity')))
    assert empty['empty_identity_store'] is True
    result = consumer('j05-entity', PRODUCED['packages']['IQS_01']['path'], root=h.CASES / 'noentity')
    assert result['cli_exit'] == 0 and result['receipt']['summary'] == {'rejected': 1}
    assert result['receipt']['acks'][0]['error_code'] == 'missing_entity'


def test_j06_real_ack_roundtrip_and_duplicate_settlement(all_imported):
    begin = h.actor('qa', 'j06-before', dict(op='snapshot', root=str(QA)))
    assert begin['delivery']['state'] == 'send_uncertain'
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
    ack = copy.deepcopy(ACKS['IQS_06'])
    if field == 'namespace':
        ack['consumer']['namespace'] = 'foreign_namespace'
    else:
        ack[field] = 'f' * 64
    result = h.actor('qa', 'j07-key-' + field, dict(op='ack', root=str(QA), question_id='IQS_06',
             ack=str(save('ack-bad-' + field + '.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j07_first_wrong_store_is_refused(all_imported):
    # Deliberately wrong target negative; no projected positive ACK.
    ack = copy.deepcopy(ACKS['IQS_06'])
    ack['consumer']['store_id'] = 'qsobs_unrelated_target'
    result = h.actor('qa', 'j07-wrong-store', dict(op='ack', root=str(QA), question_id='IQS_06',
             ack=str(save('ack-wrong-store.json', ack))))
    assert not result['accepted'] and result['before'] == result['after']


def test_j08_legacy_additive_upgrade():
    result = h.actor('qa', 'j08-upgrade', dict(op='legacy-upgrade', root=str(h.CASES / 'legacy')))
    assert result['first']['action'] == 'sealed' and result['second']['action'] == 'superseded'
    assert result['old']['package_bytes'] != result['new']['package_bytes']
    assert len(result['revisions']) == 2
    assert len(result['attempts']) == 1


def test_j09_uncertain_restart_never_reasks(all_imported):
    # IQS_06 has a committed send-intent, deliberately no returned ACK.
    before = h.actor('qa', 'j09-before', dict(op='snapshot', root=str(QA),question_id='IQS_06'))
    assert before['delivery']['state'] == 'send_uncertain'
    for op in ['warm', 'seal']:
        result = h.actor('qa', 'j09-' + op, dict(op=op, root=str(QA),question_id='IQS_06'))
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
    target_root = h.CASES / 'restored'
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
    second = json.loads((h.CASES / 'second-producer.json').read_text('utf-8'))
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


def test_j13_delivered_restart_preserves_originals_at_zero_http(all_imported):
    before=h.actor('qa','j13-before',dict(op='snapshot',root=str(QA)))
    assert before['delivery']['state']=='delivered'
    for op in ['warm','seal']:
        result=h.actor('qa','j13-'+op,dict(op=op,root=str(QA)))
        assert result['cli_exit']==0 and result['extra_http']==0
        assert result['after']['delivery']['state']=='delivered'
        for key in ['attempts','checkpoint','revisions']:
            assert result['before'][key]==result['after'][key]
        assert result['before']['delivery']['package_bytes']==result['after']['delivery']['package_bytes']
