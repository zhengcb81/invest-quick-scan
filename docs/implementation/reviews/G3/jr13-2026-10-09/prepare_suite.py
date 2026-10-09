"""Adapt the historical joint assertions without editing frozen evidence."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
IQS = HERE.parents[4]
OWN = IQS / "runs/r13a"

def main():
    source = (HERE.parent / "joint-2026-10-08/test_joint.py").read_text("utf-8")
    assert not (HERE / "test_joint.py").exists()
    source = source.replace("import run as h", "import joint_harness as h\nfrom jsonschema import Draft202012Validator, FormatChecker")
    begin = source.index("BASE = h.OUT")
    end = source.index("\n\ndef package(qid)")
    source = source[:begin] + '''QA = h.OWN / 'cases/a-selected'
SW = h.OWN / 'cases/sw-corrected'
RELEASE = h.OWN / 'independent-release.json'
PRODUCED = {}
ACKS = {}
ACK_SCHEMA = json.loads((h.IQS / 'schemas/quick_scan/exchange.schema.json').read_bytes())
ACK_VALIDATOR = Draft202012Validator({'$ref':'#/$defs/ImportAck','$defs':ACK_SCHEMA['$defs']},format_checker=FormatChecker())
''' + source[end:]
    begin = source.index("@pytest.fixture(scope='module')")
    end = source.index("\n\ndef test_j01", begin)
    source = source[:begin] + '''@pytest.fixture(scope='module')
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
            receiver_descriptor=str(h.OWN/'cases/jr13-receiver.response.json')))
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
''' + source[end:]
    source = source.replace("    begin = h.actor('qa', 'j06-begin', dict(op='begin', root=str(QA)))\n    assert begin['state'] == 'send_uncertain'", "    begin = h.actor('qa', 'j06-before', dict(op='snapshot', root=str(QA)))\n    assert begin['delivery']['state'] == 'send_uncertain'")
    # The valid receiver wire is used unchanged; no field-stripping projection.
    source = source.replace("{k: copy.deepcopy(v) for k, v in ACKS['IQS_06'].items() if k not in {'ack_sequence', 'original_import'}}", "copy.deepcopy(ACKS['IQS_06'])")
    source = source.replace("    # Contract-shaped NEGATIVE only; the actual unprojected ACK fails J06.", "    # Deliberately wrong target negative; no projected positive ACK.")
    source = source.replace("    # J06 commits send-intent before its failing raw-ACK application.", "    # IQS_06 has a committed send-intent, deliberately no returned ACK.")
    source = source.replace("dict(op='snapshot', root=str(QA)))\n    assert before['delivery']['state'] == 'send_uncertain'", "dict(op='snapshot', root=str(QA),question_id='IQS_06'))\n    assert before['delivery']['state'] == 'send_uncertain'")
    source = source.replace("dict(op=op, root=str(QA)))", "dict(op=op, root=str(QA),question_id='IQS_06'))")
    source += '''

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
'''
    (HERE / "test_joint.py").write_text(source,encoding="utf-8")
    # Pytest guard forbids writing outside OWN; tests and controller are copied here.
    (OWN / "joint_harness.py").write_bytes((HERE / "joint_harness.py").read_bytes())
    (OWN / "test_joint.py").write_bytes((HERE / "test_joint.py").read_bytes())
    print('Joint tests copied; original historical files retained unchanged.')

if __name__=='__main__':main()
