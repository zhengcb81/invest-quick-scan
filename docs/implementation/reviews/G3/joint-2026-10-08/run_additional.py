"""Finish evidence gaps: independent uncertain restart and public ACK schema."""
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run as h


def main():
    root = h.OWN / 'cases/a-selected'
    before = h.actor('qa', 'independent-j09-before', dict(op='snapshot', root=str(root), question_id='IQS_08'))
    assert before['delivery']['state'] == 'ready'
    begun = h.actor('qa', 'independent-j09-begin', dict(op='begin', root=str(root), question_id='IQS_08'))
    assert begun['state'] == 'send_uncertain'
    outcomes = []
    for op in ['warm', 'seal']:
        result = h.actor('qa', 'independent-j09-' + op, dict(op=op, root=str(root), question_id='IQS_08'))
        assert result['cli_exit'] == 0 and result['extra_http'] == 0
        assert result['before']['attempts'] == result['after']['attempts'] == before['attempts']
        assert result['after']['delivery']['state'] == 'send_uncertain'
        assert result['before']['delivery']['package_bytes'] == result['after']['delivery']['package_bytes']
        outcomes.append(dict(op=op, cli_exit=result['cli_exit'], extra_http=result['extra_http']))
    missing = h.actor('sw', 'independent-j05-no-observations', dict(op='observations', root=str(h.OWN / 'cases/emptyentity')))
    assert missing['counts']['observations'] == 0
    schema = json.loads((h.IQS / 'schemas/quick_scan/exchange.schema.json').read_text('utf-8'))
    validator = Draft202012Validator({'$schema': schema['$schema'], '$defs': schema['$defs'], '$ref': '#/$defs/ImportAck'})
    accepted = json.loads((h.OUT / 'initial-imports.json').read_text('utf-8'))[0]['result']['receipt']['acks'][0]
    rejected = json.loads((h.OUT / 'correction-actors/c-j05-import.response.json').read_text('utf-8'))['receipt']['acks'][0]
    checks = []
    for kind, ack in [('accepted', accepted), ('rejected', rejected)]:
        errors = sorted(validator.iter_errors(ack), key=lambda e: (str(list(e.path)), e.message))
        assert errors, 'Both actual owner ACKs must expose the observed 1.0 compatibility failure'
        checks.append(dict(kind=kind, actual_ack=ack, schema_valid=False,
                     errors=[dict(path=list(e.path), message=e.message) for e in errors]))
    h.save(h.OUT / 'additional-results.json', dict(independent_uncertain_restart=outcomes,
         missing_entity_observations=0, ack_schema_checks=checks,
         no_actual_model_alias_fix=True, synthetic_only=True, paid_calls=0, network_calls=0))
    for name in ['joint-junit.xml', 'corrections-junit.xml']:
        (h.OUT / name).write_bytes((h.OWN / 'logs' / name).read_bytes())
    print(json.dumps(dict(independent_restart='passed', missing_entity_observations=0,
               actual_public_ack_schema=['accepted-invalid', 'rejected-invalid'], paid_calls=0)))


if __name__ == '__main__':
    main()
