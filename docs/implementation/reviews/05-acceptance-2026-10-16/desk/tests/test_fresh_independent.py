import json,hashlib,copy
import pytest
from tests.test_review_regressions import dataset
from iqs_experiment_desk import build_bundle
from iqs_experiment_desk.server import load_bundle
from iqs_experiment_desk.view import derive_view_and_details
from iqs_experiment_desk.canonical import content_sha256,canonical_json
from iqs_experiment_desk.errors import DeskError

@pytest.mark.parametrize('case', ['invalid_commit','null_commit_without_reason','non_utc_clock','unknown_consumer','windows_reserved_source_path','trailing_dot_source_path'])
def test_shared_lock_contract(dataset,case):
 _,lock,_,finalize=dataset
 root=next(iter(lock['source_roots'].values()))
 if case=='invalid_commit': root['commit']='not-a-git-sha'
 elif case=='null_commit_without_reason':
  for key in list(root):
   if key not in ('root','commit'):root.pop(key)
  root['commit']=None
 elif case=='non_utc_clock':lock['prepared_at']='2026-10-16T12:00:00+08:00'
 elif case=='unknown_consumer':lock['files'][-1]['consumers'].append('UNREGISTERED-PACKAGE')
 elif case=='windows_reserved_source_path':lock['files'][-1]['source_path']='AUX.json'
 elif case=='trailing_dot_source_path':lock['files'][-1]['source_path']='folder./x.json'
 with pytest.raises(DeskError):derive_view_and_details(**finalize())

@pytest.mark.parametrize('core',['view','manifest','details'])
@pytest.mark.parametrize('mode',['protocol','structure'])
def test_serve_rejects_unknown_core_protocol(dataset,scratch,core,mode):
 output=scratch/'bundle';build_bundle(output_root=str(output),**dataset[3]())
 path=output/(core+'.json');obj=json.loads(path.read_text(encoding='utf-8'))
 if mode=='protocol':obj['protocol']='iqs.unknown/9.9.9'
 elif core=='view':obj['rows']='not-an-array'
 elif core=='manifest':obj['registrations']='not-an-array'
 elif core=='details':obj.pop('rows',None)
 if 'content_sha256' in obj:obj['content_sha256']=content_sha256(obj)
 if core=='view':
  dpath=output/'details.json';details=json.loads(dpath.read_text(encoding='utf-8'));details['view_content_sha256']=obj['content_sha256'];dpath.write_text(canonical_json(details),encoding='utf-8')
 path.write_text(canonical_json(obj),encoding='utf-8')
 bundle=json.loads((output/'bundle.json').read_text(encoding='utf-8'))
 if core=='view':bundle['view_content_sha256']=obj['content_sha256']
 if core=='manifest':
  bundle['source_manifest_sha256']=obj['content_sha256']
  vp=output/'view.json';view=json.loads(vp.read_text(encoding='utf-8'));view['source_manifest_sha256']=obj['content_sha256'];view['content_sha256']=content_sha256(view);vp.write_text(canonical_json(view),encoding='utf-8');bundle['view_content_sha256']=view['content_sha256']
  dp=output/'details.json';details=json.loads(dp.read_text(encoding='utf-8'));details['view_content_sha256']=view['content_sha256'];dp.write_text(canonical_json(details),encoding='utf-8')
 for ref in bundle['files']:
  b=(output/ref['path']).read_bytes();ref.update(bytes=len(b),raw_sha256=hashlib.sha256(b).hexdigest())
 for name in ('manifest','view','details'):bundle[name]=next(x for x in bundle['files'] if x['path']==name+'.json')
 bundle['content_sha256']=content_sha256(bundle);(output/'bundle.json').write_text(canonical_json(bundle),encoding='utf-8')
 with pytest.raises(DeskError):load_bundle(output)
