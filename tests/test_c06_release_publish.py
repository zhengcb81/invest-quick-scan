"""Actual owned filesystem publication: Windows long paths and writer races.

No company documents/LLM or production release catalog is modified.
"""
import json
import os
from pathlib import Path
import shutil
import pytest
import module_registry as registry
import question_sets as qs


def native(path):
    value=os.path.abspath(path)
    if os.name!='nt' or value.startswith('\\\\?\\'):return value
    return '\\\\?\\UNC\\'+value[2:] if value.startswith('\\\\') else '\\\\?\\'+value


def long_target(tmp_path,name):
    directory=tmp_path
    while len(str(directory))<285:directory=directory/'owned-long-目录-123456'
    return directory/name


def test_actual_long_immutable_path_is_idempotent_and_refuses_different_bytes(tmp_path):
    path=long_target(tmp_path,'pkg_'+'a'*64+'.json')
    assert len(str(path))>260
    registry._write_immutable(path,b'SYNTHETIC immutable bytes')
    before=os.stat(native(path)).st_ino
    registry._write_immutable(path,b'SYNTHETIC immutable bytes')
    with pytest.raises(ValueError,match='immutable release artifact changed'):
        registry._write_immutable(path,b'different bytes')
    assert Path(native(path)).read_bytes()==b'SYNTHETIC immutable bytes'
    assert os.stat(native(path)).st_ino==before
    assert not list(Path(native(path.parent)).glob('.publish-*'))


def test_actual_long_mutable_pointer_publication_is_atomic_and_cleans_temp(tmp_path):
    path=long_target(tmp_path,'current.json')
    registry._atomic_json(path,{'package_id':'SYNTHETIC first'})
    registry._atomic_json(path,{'package_id':'SYNTHETIC second'})
    assert json.loads(Path(native(path)).read_bytes())=={'package_id':'SYNTHETIC second'}
    assert not list(Path(native(path.parent)).glob('.publish-*'))


@pytest.mark.parametrize('same_bytes',[False,True])
def test_another_writer_winning_between_probe_and_publish_is_not_overwritten(tmp_path,monkeypatch,same_bytes):
    path=tmp_path/'owned-immutable.json';raw=b'SYNTHETIC requested bytes'
    winner=raw if same_bytes else b'SYNTHETIC other writer bytes';seen={}
    original_replace=registry.os.replace;original_link=registry.os.link
    def before_publish(operation,source,destination,*args,**kwargs):
        if os.path.normcase(str(destination).removeprefix('\\\\?\\'))==os.path.normcase(str(path)):
            assert not path.exists();path.write_bytes(winner);seen['inode']=path.stat().st_ino
        return operation(source,destination,*args,**kwargs)
    monkeypatch.setattr(registry.os,'replace',lambda s,d,*a,**k:before_publish(original_replace,s,d,*a,**k))
    monkeypatch.setattr(registry.os,'link',lambda s,d,*a,**k:before_publish(original_link,s,d,*a,**k))
    if same_bytes:registry._write_immutable(path,raw)
    else:
        with pytest.raises(ValueError,match='immutable release artifact changed concurrently'):
            registry._write_immutable(path,raw)
    assert path.read_bytes()==winner and path.stat().st_ino==seen['inode']
    assert not list(tmp_path.glob('.publish-*'))


def test_actual_catalog_publication_at_long_root_replays_and_keeps_logical_references(tmp_path):
    source=Path(os.environ['IQS_ROUTE_TEST_CODE_ROOT']);root=tmp_path/'owned-bank'
    # Keep source inputs readable with ordinary deployment paths, while
    # content-addressed artifact names exceed the old Windows rename limit.
    while len(str(root))<215:root=root/'owned-bank-目录-123'
    assert root.resolve().is_relative_to(tmp_path.resolve())
    for folder in ('questions','schemas'):
        shutil.copytree(source/folder,Path(native(root/folder)),ignore=shutil.ignore_patterns('releases'))
    first=registry.publish(root=root,renderer_version=qs.RENDERER_VERSION,router_version='1.0.0',
        renderer_rules_sha256=qs.renderer_rules_sha256())
    second=registry.publish(root=root,renderer_version=qs.RENDERER_VERSION,router_version='1.0.0',
        renderer_rules_sha256=qs.renderer_rules_sha256())
    assert first==second and first['modules']==48 and first['questions']==222
    assert '\\\\?\\' not in json.dumps(first)
    pointer=Path(native(root/'questions/releases/current.json'))
    assert json.loads(pointer.read_bytes())['package_id']==first['package_id']
    assert not list(Path(native(root/'questions/releases')).rglob('.publish-*'))
