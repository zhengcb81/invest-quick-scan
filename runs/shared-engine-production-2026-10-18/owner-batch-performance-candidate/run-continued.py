from pathlib import Path
import os,subprocess,sys,json,hashlib
r=Path(__file__).resolve().parent
label=sys.argv[1] if len(sys.argv)>1 else 'c01'
assert label.isascii() and label.isalnum()
if (r/label).exists() or (r/"evidence"/(label+".xml")).exists():
    raise SystemExit("Fresh owned evidence label required; existing test data is retained")
env={k:os.environ[k] for k in ('SystemRoot','SYSTEMROOT','WINDIR','PATH','PATHEXT') if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(r/'runtime/guard'),str(r/'runtime/qa'),str(r/'runtime/sw'),str(r/'runtime/company/src'),str(r/'runtime/bridge/src')]),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TEMP=str(r/'runtime/tmp'),TMP=str(r/'runtime/tmp'),IQS_C06_RUN_INTEGRATION='1',IQS_BATCH_CONTINUE_B02='1',IQS_C06_OWN=str(r/'runtime'),IQS_CONTINUATION_OWN=str(r),IQS_C06_COMPOSITION_CODE_ROOT=str(r/'runtime/iqs'),IQS_C06_COMPANY_ROOT=str(r/'runtime/company'),IQS_C06_BRIDGE_ROOT=str(r/'runtime/bridge'),IQS_CONTINUATION_METRICS=str(r/'evidence'/(label+'-metrics')))
probe='from iqs_company_agent_lab.scan_profile import task_validation_context;from iqs_company_agent_lab.runner import Runner;from iqs_agent_runtime_lab.port import RuntimeBridgePort;from src.utils.quick_scan_owner_research import OwnerResearchServices;print("original import closure passed")'
subprocess.run([sys.executable,'-B','-c',probe],env=env,cwd=r,check=True)
cmd=[sys.executable,'-B','-m','pytest',str(r/'qa/tests/integration/test_owner_batch_public.py')+'::test_continue_native_batch','-q','--tb=short','-p','no:cacheprovider','--basetemp',str(r/label),'--junitxml',str(r/'evidence'/(label+'.xml'))]
raise SystemExit(subprocess.run(cmd,cwd=r,env=env).returncode)
