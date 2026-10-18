from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parent
label=sys.argv[1]
if not label.isascii() or not label.replace("-","").isalnum(): raise SystemExit("owned label required")
env={k:os.environ[k] for k in ("SystemRoot","SYSTEMROOT","WINDIR","PATH","PATHEXT") if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(root/"unit-guard"),str(root/"qa"),str(root/"runtime/qa"),str(root/"runtime/sw")]),PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1",IQS_CONTINUATION_OWN=str(root),TEMP=str(root/"temp"),TMP=str(root/"temp"))
results=[]
for index,name in enumerate(("test_quick_scan_budget.py","test_q09_budget_concurrency.py","test_quick_scan_uncertain_seal.py")):
    command=[sys.executable,"-B","-m","pytest",str(root/("qa/tests/unit" if name=="test_quick_scan_uncertain_seal.py" else "qa/tests/original_regression")/name),"-k","not async_search","-q","--tb=short","-p","no:cacheprovider","--basetemp",str(root/(label+"-"+str(index))),"--junitxml",str(root/"evidence"/(label+"-"+str(index)+".xml"))]
    results.append(subprocess.run(command,cwd=root,env=env).returncode)
raise SystemExit(max(results))
