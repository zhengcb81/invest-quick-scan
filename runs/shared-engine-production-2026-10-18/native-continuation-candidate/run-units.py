from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parent
label=sys.argv[1]
if not label.isascii() or not label.replace("-","").isalnum(): raise SystemExit("owned label required")
env={k:os.environ[k] for k in ("SystemRoot","SYSTEMROOT","WINDIR","PATH","PATHEXT") if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(root/"unit-guard"),str(root/"runtime/qa"),str(root/"runtime/sw")]),PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1",IQS_CONTINUATION_OWN=str(root),TEMP=str(root/"temp"),TMP=str(root/"temp"))
command=[sys.executable,"-B","-m","pytest",str(root/"qa/tests/unit/test_owner_budget_continuation.py"),str(root/"qa/tests/unit/test_owner_exposure_real_migration.py"),"-q","--tb=short","-p","no:cacheprovider","--basetemp",str(root/label),"--junitxml",str(root/"evidence"/(label+".xml"))]
raise SystemExit(subprocess.run(command,cwd=root,env=env).returncode)
