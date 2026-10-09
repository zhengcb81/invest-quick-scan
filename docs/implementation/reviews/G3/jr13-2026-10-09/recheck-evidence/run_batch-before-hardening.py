"""One guarded affected batch; every output is retained under a unique label."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"

def validate_synthetic_config(line):
    raw=Path(line)
    assert raw.is_absolute() and raw.is_relative_to(OWN) and ".." not in raw.parts
    path=raw.resolve()
    assert path.is_relative_to(OWN.resolve()) and path.name=="llm_apis.json"
    for component in [raw,*raw.parents]:
        stat=component.lstat()
        assert not getattr(stat,"st_file_attributes",0)&0x400 and not component.is_symlink()
        if component==OWN:break
    assert raw.lstat().st_nlink==1
    value=json.loads(path.read_bytes())
    assert set(value)=={"default_provider","providers"} and value["default_provider"]=="openai"
    assert set(value["providers"])=={"openai"}
    provider=value["providers"]["openai"]
    assert set(provider)=={"enabled","api_key","model","base_url","max_retries","format_repair_budget"}
    assert provider["enabled"] is True and provider["api_key"]=="offline-fixture-key"
    assert provider["model"] in {"actual-fixture-model","actual-fixture-model-B"}
    assert provider["base_url"]=="https://api.openai.com/v1/chat/completions"
    assert type(provider["max_retries"]) is int and provider["max_retries"]==1
    assert type(provider["format_repair_budget"]) is int and provider["format_repair_budget"]==0
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"synthetic_only":True}

def main():
    label = sys.argv[1]
    assert label.replace("-", "").isalnum()
    destination = OUT / label
    assert not destination.exists()
    destination.mkdir()
    env = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(E97_OWNED_ROOT=str(OWN), PYTHONPATH=os.pathsep.join([str(OWN/"guard"),str(OWN/"sw"),str(OWN/"sw/tests")]),
        PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        STOCKQA_RUN_LIVE_E2E="0", STOCKWIKI_PROJECT_PARENT=str(OWN), TEMP=str(OWN/"tmp"), TMP=str(OWN/"tmp"), TMPDIR=str(OWN/"tmp"), IQS_JR13_SCHEMA=str(IQS/"schemas/quick_scan/exchange.schema.json"))
    env["JR13_JOINT_TAG"] = label
    files = sys.argv[2:] or ["tests/test_quick_scan_observations.py", "tests/test_quick_scan_delivery.py"]
    command = [sys.executable,"-B","-X","utf8","-m","pytest",*files,"-q","-o","addopts=","-p","no:cacheprovider","--basetemp",str(OWN/"tmp"/label),"--junitxml="+str(OWN/"logs"/(label+".xml"))]
    source = {n:hashlib.sha256((OWN/"sw"/n).read_bytes()).hexdigest() for n in ["stockwiki/quick_scan_import.py","stockwiki/quick_scan_observations.py","stockwiki/quick_scan_backup_manifest.py","tests/test_quick_scan_observations.py","tests/test_quick_scan_delivery.py"]}
    (destination/"source-before.json").write_text(json.dumps(source,indent=2)+"\n",encoding="utf-8")
    started=time.monotonic()
    proc=subprocess.run(command,cwd=OWN/"sw",env=env,capture_output=True,timeout=180)
    for name,raw in [("stdout.log",proc.stdout),("stderr.log",proc.stderr)]: (destination/name).write_bytes(raw)
    (destination/"junit.xml").write_bytes((OWN/"logs"/(label+".xml")).read_bytes())
    changed = [n for n,sha in source.items() if hashlib.sha256((OWN/"sw"/n).read_bytes()).hexdigest()!=sha]
    synthetic=[]
    key_ledger=OWN/"key-opens.jsonl"
    if key_ledger.exists():
        (destination/"key-opens.jsonl").write_bytes(key_ledger.read_bytes())
        for line in key_ledger.read_text("utf-8").splitlines():
            synthetic.append(validate_synthetic_config(line))
    network=OWN/"network-attempts.jsonl"
    if network.exists():(destination/"network-attempts.jsonl").write_bytes(network.read_bytes())
    (destination/"process.json").write_text(json.dumps({"argv":command,"cwd":str(OWN/"sw"),"returncode":proc.returncode,"wall_s":round(time.monotonic()-started,3),"source_sha256":source,"source_changed_during_test":changed,"synthetic_config_reads":synthetic,"real_API_calls":0,"production_DB_access":False},indent=2)+"\n",encoding="utf-8")
    for folder in [OWN/"logs"/label,OWN/"cases"/label]:
        if folder.exists():
            for item in folder.rglob("*"):
                if item.is_file() and (item.suffix in {".log", ".jsonl"} or item.name.endswith((".request.json",".response.json",".process.json"))):
                    target=destination/"actors"/item.relative_to(OWN)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(item.read_bytes())
    assert not network.exists() or not network.read_bytes(), "Unexpected network access"
    assert not changed, "Test source changed: batch invalidated"
    print(proc.stdout.decode("utf-8")[-5500:])
    print(proc.stderr.decode("utf-8")[-1500:])
    print(json.dumps({"returncode":proc.returncode,"label":label}))
    sys.exit(proc.returncode)

if __name__ == "__main__":main()
