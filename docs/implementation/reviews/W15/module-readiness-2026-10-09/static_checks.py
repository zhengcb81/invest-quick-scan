"""Format only W15 candidate changes, or check them without source publication."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
OWN = ROOT / "runs/w15a"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"


def changed(project):
    index = json.loads((OUT/("stockwiki-input-01.json" if project=="sw" else "executor-input-01.json")).read_bytes())
    rows = index["nonsecret_files"] if project=="sw" else index["artifacts"]
    baseline = {r["path"]: r.get("execution_sha256", r.get("sha256")) for r in rows}
    return [p.relative_to(OWN/project).as_posix() for p in sorted((OWN/project).rglob("*.py"))
            if hashlib.sha256(p.read_bytes()).hexdigest()!=baseline.get(p.relative_to(OWN/project).as_posix())]


def main():
    label, project, mode = sys.argv[1:]
    assert project in {"sw", "qa"} and mode in {"format", "static", "full"}
    assert mode != "full" or project == "sw"
    assert label.replace("-", "").isalnum() and not (OUT/(label+".process.json")).exists()
    paths = changed(project)
    assert paths
    env = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC",
                 "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", IQS_W15_OWN=str(OWN),
               PYTHONPATH=str(OWN/project),
               TEMP=str(OWN/"tmp"), TMP=str(OWN/"tmp"), TMPDIR=str(OWN/"tmp"),
               MYPY_CACHE_DIR=str(OWN/"mypy-cache"), RUFF_CACHE_DIR=str(OWN/"ruff-cache"), STOCKQA_RUN_LIVE_E2E="0")
    if mode=="format":
        commands = [[sys.executable,"-B","-m","ruff","check","--fix",*paths],
                    [sys.executable,"-B","-m","ruff","format",*paths]] if project=="sw" else [
                    [sys.executable,"-B","-m","isort","--profile","black",*paths],
                    *[[sys.executable,"-B","-m","black",path] for path in paths]]
    elif project=="sw":
        commands = [[sys.executable,"-B","scripts/checks.py","--full" if mode=="full" else "--static-only"]]
        if mode=="full":
            assert (OWN/"StockWiki/config/evidence_topics.yaml").is_file()
            assert (OWN/"sw/sitecustomize.py").read_bytes()==(OWN/"guard/sitecustomize.py").read_bytes()
            env["PYTEST_ADDOPTS"] = "-p no:cacheprovider --basetemp="+str(OWN/"sw-full-test-tmp")
            env["IQS_ROUTE_TEST_CODE_ROOT"] = str(ROOT)
            env["IQS_W15_QA_CODE_ROOT"] = str(OWN/"qa")
            env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    else:
        # Exact canonical owner static tool scope, without its optional reports.
        commands = [[sys.executable,"-B","-m","black","--workers","1","--check","src","tests","main_with_llm.py"],
                    [sys.executable,"-B","-m","isort","--check-only","--profile","black","src","tests","main_with_llm.py"],
                    [sys.executable,"-B","-m","mypy","src"],
                    [sys.executable,"-B","-m","bandit","-r","src","-q","-f","screen"]]
    baseline = {p.relative_to(OWN/project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((OWN/project).rglob("*.py"))}
    records = []
    for i, command in enumerate(commands):
        start = time.monotonic()
        proc = subprocess.Popen(command,cwd=OWN/project,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        print(json.dumps(dict(label=label,step=i,pid=proc.pid)),flush=True)
        stdout,stderr = proc.communicate(timeout=1800 if mode=="full" else 600)
        (OUT/f"{label}-{i}.stdout.log").write_bytes(stdout)
        (OUT/f"{label}-{i}.stderr.log").write_bytes(stderr)
        records.append(dict(pid=proc.pid,terminal_confirmed=True,command=command,returncode=proc.returncode,wall_s=round(time.monotonic()-start,3)))
        print((stdout+stderr).decode("utf-8",errors="replace")[-2500:])
        if proc.returncode: break
    after = {p.relative_to(OWN/project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((OWN/project).rglob("*.py"))}
    changed_after = [p for p in baseline if baseline[p]!=after[p]]
    assert not changed_after if mode!="format" else set(changed_after)<=set(paths)
    report = dict(project=project,mode=mode,steps=records,source_before=baseline,source_after=after,
                  changed_allowlist=paths,changed_after=changed_after,credentials_inherited=False,model_API_requests=0,
                  production_DB_migrations=0,whole_OS_guard_claim=False,Python_network_guard=mode=="full",
                  guard_note="Canonical static tools need local IPC; full SW children load an owned identical sitecustomize guard after PYTHONPATH reset.",
                  real_data_scope="26 actual metadata files and four read-only native backups in an isolated clone; no company documents or actual observations fabricated" if mode=="full" else None)
    (OUT/(label+".process.json")).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
