"""One owned original delegated/SDK/Runner case, no live API or credentials."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

c = Path(__file__).resolve().parent
for source in (c / "qa/src/utils").glob("*.py"):
    shutil.copy2(source, c / "runtime/qa/src/utils" / source.name)
for source in (c / "sw/stockwiki").glob("*.py"):
    shutil.copy2(source, c / "runtime/sw/stockwiki" / source.name)
for source in (c / "iqs").rglob("*"):
    if source.is_file():
        target = c / "runtime/iqs" / source.relative_to(c / "iqs")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
shutil.copy2(c / "qa/tests/continuation_fixture.py", c / "runtime/qa/tests/continuation_fixture.py")
shutil.copy2(c / "qa/tests/unit/test_quick_scan_work_store.py", c / "runtime/qa/tests/unit/test_quick_scan_work_store.py")
shutil.copytree(c / "guard", c / "runtime/guard", dirs_exist_ok=True)
env = {k: os.environ[k] for k in ("SystemRoot", "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT") if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(c / "runtime/guard"), str(c / "runtime/qa"), str(c / "runtime/sw"),
    str(c / "runtime/company/src"), str(c / "runtime/bridge/src")]),
    PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", TEMP=str(c / "runtime/tmp"), TMP=str(c / "runtime/tmp"),
    IQS_C06_RUN_INTEGRATION="1", IQS_C06_OWN=str(c / "runtime"), IQS_CONTINUATION_OWN=str(c),
    IQS_C06_COMPOSITION_CODE_ROOT=str(c / "runtime/iqs"),
    IQS_C06_COMPANY_ROOT=str(c / "runtime/company"), IQS_C06_BRIDGE_ROOT=str(c / "runtime/bridge"))
label = sys.argv[1] if len(sys.argv) > 1 else "public01"
if not label.isascii() or not label.replace("-", "").isalnum():
    raise SystemExit("simple owned evidence label required")
env["IQS_CONTINUATION_METRICS"] = str(c / "evidence" / (label + "-metrics"))
cmd = [sys.executable, "-B", "-m", "pytest", str(c / "qa/tests/integration/test_owner_continuation_public.py"),
    "-q", "--tb=short", "-p", "no:cacheprovider", "--basetemp", str(c / label),
    "--junitxml", str(c / "evidence" / (label + ".xml"))]
raise SystemExit(subprocess.run(cmd, cwd=c, env=env).returncode)
