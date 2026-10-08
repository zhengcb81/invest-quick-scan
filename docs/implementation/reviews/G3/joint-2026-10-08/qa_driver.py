"""Test-only adapter: real QA CLI subprocess and public work-store APIs."""
import hashlib
import json
import os
from pathlib import Path
import sys

from src.utils.quick_scan_result_outbox import canonical_bytes
from src.utils.quick_scan_work_store import QuickScanWorkStore
from tests.integration import test_qa_c06_02_subprocess_cli as fixture


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def snapshot(store, item):
    wid = item['work_item_id']
    delivery = store.get_result_delivery(wid)
    return dict(work_item=store.get_item(wid), delivery=delivery, attempts=store.list_attempts(wid),
                revisions=store.list_delivery_revisions(wid),
                events=store.list_result_delivery_events(wid),
                checkpoint=store.get_answer_checkpoint(wid))


def main(request):
    root = Path(request['root'])
    root.mkdir(parents=True, exist_ok=True)
    op = request['op']
    if op == 'produce':
        files = fixture._prepare_root(root)
        responses = json.loads((root / 'stub-responses.json').read_text('utf-8'))
        for qid, changes in request.get('answers', {}).items():
            response = json.loads(responses[qid])
            outer = json.loads(response['output'][1]['content'][0]['text'])
            body = fixture.base._standard_answer(qid, large=changes.get('large', False))
            body.update({k: v for k, v in changes.items() if k != 'large'})
            outer.update(status=body['status'], score=body['score'],
                         description=json.dumps(body, ensure_ascii=False))
            response['output'][1]['content'][0]['text'] = json.dumps(outer, ensure_ascii=False)
            responses[qid] = json.dumps(response, ensure_ascii=False)
        (root / 'stub-responses.json').write_text(json.dumps(responses), encoding='utf-8')
        if request.get('model_resolved'):
            responses = json.loads((root / 'stub-responses.json').read_text('utf-8'))
            for qid, text in responses.items():
                response = json.loads(text)
                response['model'] = request['model_resolved']
                responses[qid] = json.dumps(response)
            (root / 'stub-responses.json').write_text(json.dumps(responses), encoding='utf-8')
        if request.get('wrong_security'):
            from src.utils.quick_scan_result_outbox import canonical_sha256
            document = json.loads(files['authority'].read_text('utf-8'))
            document['observation_context']['questions']['IQS_22']['metadata']['security_id'] = 'SEC_FOREIGN'
            document['observation_context_sha256'] = canonical_sha256(document['observation_context'])
            files['authority'].write_text(json.dumps(document), encoding='utf-8')
        if request.get('run_label'):
            from src.utils.quick_scan_result_outbox import canonical_sha256
            document = json.loads(files['authority'].read_text('utf-8'))
            for selected in document['observation_context']['questions'].values():
                selected['metadata']['run_id'] = 'RUN_' + request['run_label']
                selected['metadata']['scan_id'] = 'SCAN_' + request['run_label']
            document['observation_context_sha256'] = canonical_sha256(document['observation_context'])
            files['authority'].write_text(json.dumps(document), encoding='utf-8')
        child = fixture._spawn(root, fixture._cold_argv(files), stub=True)
        (root / 'cold.stdout.log').write_text(child.stdout, encoding='utf-8')
        (root / 'cold.stderr.log').write_text(child.stderr, encoding='utf-8')
        if child.returncode:
            return dict(cli_exit=child.returncode,
                        key_opens=len((root / 'key-opens.jsonl').read_text('utf-8').splitlines()) if (root / 'key-opens.jsonl').exists() else 0,
                        http_sends=len((root / 'http-stub-sends.jsonl').read_text('utf-8').splitlines()) if (root / 'http-stub-sends.jsonl').exists() else 0,
                        database_created=(root / 'quick_scan_work.sqlite').exists())
    if op == 'legacy-upgrade':
        from tests.unit import test_quick_scan_c06_complete_seal as complete
        from src.utils.quick_scan_delivery_seal import seal_result_delivery
        store, item, _, _ = complete._checkpointed(root)
        wid = item['work_item_id']
        first = seal_result_delivery(store, wid, authority=complete.V1_AUTHORITY)
        old = store.get_result_delivery(wid)
        second = seal_result_delivery(store, wid, authority=complete._v2_authority(root))
        new = store.get_result_delivery(wid)
        (root / 'old.package.json').write_bytes(old['package_bytes'])
        (root / 'new.package.json').write_bytes(new['package_bytes'])
        return dict(first=first, second=second, old=old, new=new,
                    revisions=store.list_delivery_revisions(wid),
                    attempts=store.list_attempts(wid), work_item_id=wid)
    store = QuickScanWorkStore(root / 'quick_scan_work.sqlite')
    items = store.find_work_items(entity_id=fixture.base.ENTITY_ID,
                                 question_ids=fixture.QUESTIONS)
    if op == 'produce':
        paths = {}
        for qid, values in items.items():
            item = values[0]
            delivery = store.get_result_delivery(item['work_item_id'])
            if delivery and delivery['package']:
                path = root / (qid + '.package.json')
                path.write_bytes(delivery['package_bytes'])
                paths[qid] = dict(path=str(path), work_item_id=item['work_item_id'],
                                  state=delivery['state'], package_sha256=digest(delivery['package']))
        return dict(cli_exit=0, packages=paths,
                    http_sends=len((root / 'http-stub-sends.jsonl').read_text('utf-8').splitlines()))
    qid = request.get('question_id', 'IQS_01')
    item = items[qid][0]
    if op == 'snapshot':
        return snapshot(store, item)
    if op == 'begin':
        result = store.begin_result_delivery(item['work_item_id'])
        return dict(state=result['state'], request_sha256=hashlib.sha256(result['request_bytes']).hexdigest())
    if op == 'ack':
        ack = json.loads(Path(request['ack']).read_text('utf-8'))
        before = snapshot(store, item)
        try:
            result = store.apply_result_delivery_ack(item['work_item_id'], ack)
            return dict(accepted=True, state=result['state'], before=before,
                        after=snapshot(store, store.get_item(item['work_item_id'])))
        except ValueError as error:
            return dict(accepted=False, error=str(error), before=before,
                        after=snapshot(store, store.get_item(item['work_item_id'])))
    if op in {'warm', 'seal'}:
        files = {k: root / v for k, v in dict(questions='questions.json', manifest='manifest.json',
                    identity='identity.json', spend='spend_authorization.json',
                    authority='quick_scan_c06_authority.json', output='warm-result.json').items()}
        argv = fixture._cold_argv(files) if op == 'warm' else ['--seal-deliveries',
                '--entity-id', fixture.base.ENTITY_ID, '--c06-authority', str(files['authority'])]
        sends_before = (root / 'http-stub-sends.jsonl').read_bytes()
        before = snapshot(store, item)
        child = fixture._spawn(root, argv, stub=False)
        (root / (op + '.stdout.log')).write_text(child.stdout, encoding='utf-8')
        (root / (op + '.stderr.log')).write_text(child.stderr, encoding='utf-8')
        return dict(cli_exit=child.returncode, extra_http=0 if sends_before == (root / 'http-stub-sends.jsonl').read_bytes() else None,
                    before=before, after=snapshot(store, store.get_item(item['work_item_id'])))
    raise ValueError('Unsupported test adapter op: ' + op)


if __name__ == '__main__':
    request = json.loads(Path(sys.argv[1]).read_text('utf-8'))
    result = main(request)
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False, default=lambda x:
        x.decode('utf-8') if isinstance(x, bytes) else str(x)), encoding='utf-8')
