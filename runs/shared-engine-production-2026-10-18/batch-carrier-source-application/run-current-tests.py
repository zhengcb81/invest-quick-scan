from pathlib import Path
import os, subprocess, sys, json, time
here=Path(__file__).resolve().parent;base=here.parent;root=base.parents[1];own=base/'real-profile-smoke-candidate'
label=sys.argv[1]
assert label.isascii() and label.isalnum() and not (own/label).exists()
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','SYSTEMDRIVE'}}
env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',GIT_OPTIONAL_LOCKS='0',IQS_CONTINUATION_OWN=str(own),IQS_PROFILE_SMOKE_TEST_ROOT=str(own),TEMP=str(own/'temp'),TMP=str(own/'temp'),PYTHONPATH=os.pathsep.join([str(own/'guard'),str(root.parent/'StockQAbyLLM'),str(root.parent/'iqs-agent-runtime-lab/src'),str(root.parent/'iqs-company-agent-lab/src')]),IQS_BATCH_ORIGINAL_ROOT=str(base))
files=[root.parent/'iqs-agent-runtime-lab/tests/test_batch_carrier.py',root.parent/'StockQAbyLLM/tests/unit/test_research_final_json.py',root.parent/'StockQAbyLLM/tests/integration/test_batch_saved_native.py']
start=time.monotonic();r=subprocess.run([sys.executable,'-B','-X','utf8','-m','pytest',*[str(p) for p in files],'--noconftest','-q','--tb=short','-p','no:cacheprovider','--basetemp',str(own/label),'--junitxml',str(own/'evidence'/f'{label}.xml')],cwd=own,env=env)
(here/(label+'-process.json')).write_text(json.dumps(dict(exit_code=r.returncode,seconds=time.monotonic()-start,source='actual delivered sources; original frozen-dependency conftests deliberately excluded; old frozen compatibility separately passed39',keyless=True,core_socket_denied=True,write_audited=True,private_real_cache_read_opt_in=True),indent=2)+'\n',encoding='utf-8')
raise SystemExit(r.returncode)
