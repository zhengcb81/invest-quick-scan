"""Concentrated adjacent boundaries from the single independent review.

SYNTHETIC ONLY. No source edits, live requests, owner golden or real database.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

QA=Path(os.environ['QA100_QA_ROOT'])
def fixture(name,path):
    spec=importlib.util.spec_from_file_location(name,QA/path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

f=fixture('qa104_complete','tests/unit/test_quick_scan_c06_complete_seal.py')
s=fixture('qa104_subprocess','tests/integration/test_qa_c06_02_subprocess_cli.py')
from src.utils.quick_scan_c06_authority import AuthorityUnavailable,load_c06_authority
from src.utils.quick_scan_delivery_seal import _send_intent_iso
from src.utils.quick_scan_observation_context import parse_standard_answer
from src.utils.quick_scan_result_outbox import canonical_sha256

def authority_file(tmp,document):
    document['observation_context_sha256']=canonical_sha256(document['observation_context'])
    path=tmp/'authority.json'
    path.write_text(json.dumps(document,ensure_ascii=False),encoding='utf-8')
    return path

def complete(store,item,checkpoint,body,context,authority):
    bound=f.bind_context_to_work_item(context,work_item=store.get_item(item['work_item_id']),
        question_id=item['question_id'])
    started=_send_intent_iso(store.get_attempt_transmission(checkpoint['attempt_id'])['send_intent_at'])
    return f.build_complete_c06_package(checkpoint['payload'],authority=f.authority_adapter_input(authority),
        context=bound,standard_answer=body,started_at=started)

def test_normal_standard_body_remains_parseable():
    assert parse_standard_answer(json.dumps(f._standard_body()))==f._standard_body()

def test_overflow_number_is_refused_at_standard_body_entry():
    raw=json.dumps(f._standard_body()).replace('"metrics": []','"metrics": [{"value": 1e400}]')
    with pytest.raises(ValueError):
        parse_standard_answer(raw)

def test_wrong_security_id_is_refused_by_authority_loader(tmp_path):
    doc=copy.deepcopy(f.AUTHORITY_V2)
    assert f.MANIFEST['profile']['security_id']=='SEC_CONTEXT_FIXTURE'
    doc['observation_context']['questions']['IQS_22']['metadata']['security_id']='SEC_FOREIGN'
    with pytest.raises(AuthorityUnavailable):
        load_c06_authority(authority_file(tmp_path,doc),manifest=f.MANIFEST,
            identity_snapshot_sha256=f.CONTEXT['identity_snapshot_sha256'])

def test_wrong_security_id_cli_is_refused_before_key_http_budget(tmp_path):
    files=s._prepare_root(tmp_path)
    document=json.loads(files['authority'].read_text('utf-8'))
    document['observation_context']['questions']['IQS_22']['metadata']['security_id']='SEC_FOREIGN'
    document['observation_context_sha256']=canonical_sha256(document['observation_context'])
    files['authority'].write_text(json.dumps(document,ensure_ascii=False),encoding='utf-8')
    result=s._spawn(tmp_path,s._cold_argv(files),stub=True)
    (tmp_path/'child.stdout.log').write_text(result.stdout,encoding='utf-8')
    (tmp_path/'child.stderr.log').write_text(result.stderr,encoding='utf-8')
    s._assert_rejected_before_key_http_budget(tmp_path,files,result)

@pytest.mark.parametrize('method',['prepare','supersede'])
def test_new_complete_write_requires_durable_complete_inputs(tmp_path,method):
    store,item,checkpoint,body=f._checkpointed(tmp_path,with_context=False)
    wid=item['work_item_id']
    assert store.get_observation_context(wid) is None and store.get_standard_answer(wid) is None
    if method=='supersede':
        assert f.seal_result_delivery(store,wid,authority=f.V1_AUTHORITY)['action']=='sealed'
    before=store.get_result_delivery(wid)
    revisions=store.list_delivery_revisions(wid)
    package=complete(store,item,checkpoint,body,f.CONTEXT,f._v2_authority(tmp_path))
    forged=f._forged_complete_package(package,lambda obs:f._mutate(obs,'claim_and_start'))
    with pytest.raises(ValueError):
        if method=='prepare': store.prepare_result_delivery(wid,forged)
        else: store.supersede_result_delivery(wid,forged)
    after=store.get_result_delivery(wid)
    assert (after['package_bytes'] if after else None)==(before['package_bytes'] if before else None)
    assert store.list_delivery_revisions(wid)==revisions

def test_prepare_cannot_bypass_a_run_scan_block(tmp_path):
    store,item,checkpoint,body=f._checkpointed(tmp_path,with_context=False)
    wid=item['work_item_id']
    doc=copy.deepcopy(f.AUTHORITY_V2)
    for question in doc['observation_context']['questions'].values():
        question['metadata']['run_id']='FOREIGN_RUN'
        question['metadata']['scan_id']='FOREIGN_SCAN'
    authority=load_c06_authority(authority_file(tmp_path,doc))
    store.attach_standard_inputs(wid,observation_context=doc['observation_context'],standard_answer=body)
    result=f.seal_result_delivery(store,wid,authority=authority)
    assert result['action']=='blocked' and result['block_code']=='c06_run_scan_unbound'
    before=store.get_result_delivery(wid)
    package=complete(store,item,checkpoint,body,doc['observation_context'],authority)
    with pytest.raises(ValueError): store.prepare_result_delivery(wid,package)
    assert store.get_result_delivery(wid)==before
    assert store.list_delivery_revisions(wid)==[]
