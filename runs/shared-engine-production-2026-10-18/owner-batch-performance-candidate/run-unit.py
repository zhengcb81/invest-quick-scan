from pathlib import Path
import os,sys,subprocess
r=Path(__file__).resolve().parent
label=sys.argv[1]
assert label.isascii() and label.replace("-","").isalnum()
if (r/label).exists() or (r/"evidence"/(label+".xml")).exists():
    raise SystemExit("Fresh owned evidence label required; existing test data is retained")
env={k:os.environ[k] for k in ("SystemRoot","SYSTEMROOT","WINDIR","PATH","PATHEXT") if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(r/"guard"),str(r/"runtime/qa")]),IQS_CONTINUATION_OWN=str(r),PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1",TEMP=str(r/"temp"),TMP=str(r/"temp"))
cmd=[sys.executable,"-B","-m","pytest",str(r/"runtime/qa/tests/unit/test_owner_batch_claim.py"),str(r/"runtime/qa/tests/unit/test_owner_batch_adapters.py"),"-q","--tb=short","-p","no:cacheprovider","--basetemp",str(r/label),"--junitxml",str(r/"evidence"/(label+".xml"))]
raise SystemExit(subprocess.run(cmd,cwd=r,env=env).returncode)
