"""Concentrated synthetic boundary tests against frozen QA-C06-02 source."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

import pytest

QA=Path(os.environ['QA100_QA_ROOT'])
OWN=Path(os.environ['E97_OWNED_ROOT'])
spec=importlib.util.spec_from_file_location('complete_fixture',QA/'tests/unit/test_quick_scan_c06_complete_seal.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from src.utils.quick_scan_c06_authority import load_c06_authority, AuthorityUnavailable
from src.utils.quick_scan_observation_context import parse_standard_answer
from src.utils.quick_scan_result_outbox import canonical_sha256,canonical_bytes
from src.utils.quick_scan_work_store import QuickScanWorkStore

def resign(doc):
    doc['observation_context_sha256']=canonical_sha256(doc['observation_context'])
    return doc
def write(tmp,doc):
    p=tmp/'authority.json';p.write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8');return p

@pytest.mark.parametrize('field,value',[
    ('question_definition_sha256','0'*64),('question_semantic_sha256','1'*64),('template_version','99.0.0')])
def test_metadata_is_bound_to_real_frozen_manifest(tmp_path,field,value):
    doc=copy.deepcopy(f.AUTHORITY_V2)
    doc['observation_context']['questions'][f.QID]['metadata'][field]=value
    with pytest.raises(AuthorityUnavailable):
        load_c06_authority(write(tmp_path,resign(doc)),manifest=f.MANIFEST,
            identity_snapshot_sha256=f.CONTEXT['identity_snapshot_sha256'])

def test_authority_duplicate_json_key_is_rejected(tmp_path):
    path=write(tmp_path,f.AUTHORITY_V2)
    raw=path.read_text('utf-8')
    path.write_text(raw.replace('"schema_version": "2.0.0"',
        '"schema_version": "1.0.0", "schema_version": "2.0.0"',1),encoding='utf-8')
    with pytest.raises(AuthorityUnavailable): load_c06_authority(path)

def test_standard_body_duplicate_score_is_rejected():
    raw=json.dumps(f._standard_body())
    raw=raw.replace('"score": 8','"score": 1, "score": 8',1)
    try:
        parsed=parse_standard_answer(raw)
    except ValueError:
        return
    assert parsed is None,'Duplicate score silently chose the last value'

def test_foreign_run_and_scan_cannot_seal_this_checkpoint(tmp_path):
    store,item,_,body=f._checkpointed(tmp_path,with_context=False)
    doc=copy.deepcopy(f.AUTHORITY_V2)
    for q in doc['observation_context']['questions'].values():
        q['metadata']['run_id']='FOREIGN_RUN';q['metadata']['scan_id']='FOREIGN_SCAN'
    authority=load_c06_authority(write(tmp_path,resign(doc)))
    store.attach_standard_inputs(item['work_item_id'],observation_context=doc['observation_context'],standard_answer=body)
    result=f.seal_result_delivery(store,item['work_item_id'],authority=authority)
    assert result['action']=='blocked','Foreign run/scan became a sealed complete observation'

def test_supersede_cannot_change_full_claim_or_original_start(tmp_path):
    store,item,_,body=f._checkpointed(tmp_path)
    wid=item['work_item_id']
    f.seal_result_delivery(store,wid,authority=f._v2_authority(tmp_path))
    before=store.get_result_delivery(wid)
    forged=copy.deepcopy(before['package']);entry=forged['items'][0];obs=entry['observation']
    obs['answer']['evidence'][0]['claim']='Changed claim not from durable standard body'
    obs['execution']['started_at']='2026-09-27T10:00:00Z'
    del obs['observation_id'];obs['observation_id']='obs_'+canonical_sha256(obs)
    entry['observation_id']=obs['observation_id']
    entry['payload_sha256']=canonical_sha256(obs)
    entry['item_id']='itm_'+canonical_sha256({'observation_id':obs['observation_id'],
        'payload_sha256':entry['payload_sha256']})
    del forged['package_id'];del forged['package_sha256']
    digest=canonical_sha256(forged);forged['package_id']='pkg_'+digest;forged['package_sha256']=digest
    with pytest.raises(ValueError): store.supersede_result_delivery(wid,forged)
    assert store.get_standard_answer(wid)['answer']==body
    assert store.get_result_delivery(wid)['package_bytes']==before['package_bytes']

def legacy_store(tmp_path,monkeypatch):
    name='src.utils.qa100_legacy_work_store'
    spec=importlib.util.spec_from_file_location(name,OWN/'legacy_work_store.py')
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    assert m.SCHEMA_VERSION==5
    class Old(m.QuickScanWorkStore):
        def save_answer_checkpoint(self,*args,**kwargs):
            kwargs.pop('observation_context',None);kwargs.pop('standard_answer',None)
            return super().save_answer_checkpoint(*args,**kwargs)
    monkeypatch.setattr(f,'QuickScanWorkStore',Old)
    store,item,_,_=f._checkpointed(tmp_path,with_context=False,with_answer=False)
    wid=item['work_item_id'];f.seal_result_delivery(store,wid,authority=copy.deepcopy(f.V1_AUTHORITY))
    delivery=store.get_result_delivery(wid);store.begin_result_delivery(wid)
    store.apply_result_delivery_ack(wid,f._ack(delivery,ack_id='ack_true_v5_00001'))
    return tmp_path/'quick_scan_work.sqlite',wid,delivery

def db_snapshot(path):
    with sqlite3.connect(path) as db:
        names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return dict(version=db.execute('PRAGMA user_version').fetchone()[0],
            schema=list(db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name')),
            tables={n:list(db.execute('SELECT * FROM "'+n+'"')) for n in names})

def test_true_v5_delivered_package_ack_preserved_by_v6(tmp_path,monkeypatch):
    path,wid,old=legacy_store(tmp_path,monkeypatch);before=db_snapshot(path)
    new=QuickScanWorkStore(path);after=db_snapshot(path)
    assert before['version']==5 and after['version']==6
    assert all(after['tables'][k]==v for k,v in before['tables'].items())
    assert new.get_result_delivery(wid)['package_bytes']==old['package_bytes']
    assert new.get_item(wid)['status']=='delivered'
    assert len(new.list_delivery_revisions(wid))==1

def test_v5_to_v6_mid_migration_failure_rolls_back_every_change(tmp_path,monkeypatch):
    path,_,_=legacy_store(tmp_path,monkeypatch);before=db_snapshot(path)
    original=QuickScanWorkStore._apply_v6_migration
    def fail(connection):
        original(connection)
        raise RuntimeError('Controller injected failure before COMMIT')
    monkeypatch.setattr(QuickScanWorkStore,'_apply_v6_migration',staticmethod(fail))
    with pytest.raises(RuntimeError): QuickScanWorkStore(path)
    assert db_snapshot(path)==before
