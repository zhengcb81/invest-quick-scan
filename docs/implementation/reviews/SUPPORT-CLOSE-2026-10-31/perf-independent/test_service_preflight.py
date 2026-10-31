"""Actual service seam: mutable bundle after first preview must not bind consumer."""
import hashlib,importlib.util,inspect,json,sys
from pathlib import Path
import pytest

LAB=Path(__file__).resolve().parent/'snapshot'
sys.path.insert(0,str(LAB/'src'))
spec=importlib.util.spec_from_file_location('fault_helpers',LAB/'tests/integration/test_native_fault_parity.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
fault_variants=helpers.fault_variants
from iqs_import_perf import fixtures

@pytest.mark.parametrize('variant',['baseline','candidate'])
def test_service_preflight_revalidates_before_native_consumer_bind(fault_variants,tmp_path,variant):
 root,owner_module=fault_variants[variant]
 built=fixtures.build_stockqa_ledger(tmp_path/'work.sqlite',fixtures.question_plan(1))
 wid=built['sealed'][0]['work_item_id'];store=built['store'];delivery=store.get_result_delivery(wid)
 assert delivery['consumer_binding'] is None
 ws=fixtures.build_stockwiki_workspace(tmp_path/'ws',vendor=root)
 package=tmp_path/'package.json';package.write_text(delivery['package_json'],encoding='utf8')
 release=tmp_path/'release.json';release.write_text(json.dumps(fixtures.release_projection()),encoding='utf8')
 scratch=tmp_path/'scratch';scratch.mkdir()
 config={'stockwiki_root':str(root/'stockwiki'),'iqs_root':str(root/'iqs'),'iqs_release_root':str(root/'iqs'),'workspace_root':str(tmp_path/'ws'),'scratch_root':str(scratch),'stockwiki_python':sys.executable,'timeout_seconds':120,'bundles':{'one':{'package':str(package),'release':str(release),'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'release_sha256':hashlib.sha256(release.read_bytes()).hexdigest()}}}
 class OriginalOwner:
  def import_preview(self,payload):return owner_module._owner_worker(config,'import_preview',payload)
  def status(self):return owner_module._owner_worker(config,'status',{})
  def import_apply(self,payload):return owner_module._owner_worker(config,'import_apply',payload)
  def call_batch(self,operations):return owner_module._owner_worker(config,'operations',{'operations':operations})
 original=OriginalOwner()
 if variant=='candidate':
  result=owner_module._owner_worker(config,'operations',{'operations':[{'operation':'import_preview','payload':{'bundle_id':'one'}},{'operation':'status'}]})
  preview=owner_module.OwnerGateway.unwrap_batch(result[0]);status=owner_module.OwnerGateway.unwrap_batch(result[1])
 else:preview=original.import_preview({'bundle_id':'one'});status=original.status()
 assert preview['can_apply'] and status['available']
 # The only fault injection: mutate a synthetic file after real prechecks.
 package.write_bytes(package.read_bytes()+b' ')
 bundle={'work_store':str(store.path),'work_item_ids':[wid]}
 class NativeExecution:
  bind_calls=0
  def bind_delivery_consumer(self,bundle,target,source_ref):
   assert bundle['work_item_ids']==[wid] and Path(bundle['work_store'])==store.path
   self.bind_calls+=1
   return store.bind_result_delivery_consumer(wid,target,source_ref=source_ref)
  def acknowledge_delivery(self,*args):raise AssertionError('tampered package must never reach ACK')
 scripts=str(root/'iqs/scripts');sys.path.insert(0,scripts)
 spec=importlib.util.spec_from_file_location('preflight_service_'+variant,root/'iqs/scripts/dashboard_service.py')
 service_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(service_module)
 service=object.__new__(service_module.DashboardService);service.config={'workspace_root':str(tmp_path/'ws')}
 execution=NativeExecution()
 kwargs={'execution':execution,'workspace':str(tmp_path/'ws')}
 if variant=='candidate' and 'preview' in inspect.signature(service._apply_import).parameters:
  kwargs.update(preview=preview,status_result=status)
 with pytest.raises(Exception) as error:
  service._apply_import(original,bundle,{'bundle_id':'one','preview_token':preview['preview_token']},**kwargs)
 assert getattr(error.value,'code',None)=='bundle_hash_mismatch',str(error.value)
 after=store.get_result_delivery(wid)
 print(json.dumps({'variant':variant,'native_bind_calls':execution.bind_calls,'consumer_before':delivery['consumer_binding'],'consumer_after':after['consumer_binding'],'delivery_state':after['state']},sort_keys=True))
 assert after['state']=='ready'
 assert after['consumer_binding']==delivery['consumer_binding'], 'preflight caching persisted consumer binding before rejecting mutable package'
