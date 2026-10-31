from pathlib import Path
import json,os,sys,subprocess,hashlib,uuid,shutil,time
root=Path.cwd();out=root/'runs/close-support31/test-entry-independent';tmp=root/('.techeck-'+uuid.uuid4().hex[:6]);tmp.mkdir()
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(tmp),TMP=str(tmp));env.pop('PYTHONPATH',None)
argv=[sys.executable,'-B','-m','pytest','tests/test_test_suites.py','tests/test_test_runner_cli.py','tests/test_dashboard_entity_view_http.py','tests/test_dashboard_temporal.py::test_pure_shadow_calls_real_engine_without_mutation_or_current_context_claim','-q','-p','no:cacheprovider','--basetemp',str(tmp/'pytest')]
try:
 start=time.perf_counter();p=subprocess.run(argv,cwd=root,env=env,capture_output=True,timeout=90);log=out/'target-tests.log';log.write_bytes(p.stdout+p.stderr)
 plan=subprocess.run([sys.executable,'-B','scripts/run_tests.py','fast','--plan'],cwd=root,env=env,capture_output=True,timeout=10);assert plan.returncode==0,plan.stderr
 x=json.loads(plan.stdout)
 obj={'argv':argv,'PYTHONPATH_absent':True,'exit_code':p.returncode,'wall_seconds':time.perf_counter()-start,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'output_tail':log.read_text(encoding='utf8',errors='replace')[-1400:],'plain_fast_plan':{'exit_code':plan.returncode,'fast_files':x['file_count'],'total_files':x['all_file_count']},'source_hashes':{str(v):hashlib.sha256((root/v).read_bytes()).hexdigest() for v in ['scripts/run_tests.py','tests/test_test_suites.py','tests/test_dashboard_temporal.py','tests/suites.json']}}
finally:
 assert tmp.resolve().parent==root.resolve() and tmp.name.startswith('.techeck-');shutil.rmtree(tmp)
obj['cleanup']={'owned_short_TEMP_absent':not tmp.exists(),'no_production_workspace_or_service_write':True,'paid_api_calls':0};(out/'target-tests.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(obj,ensure_ascii=True))
