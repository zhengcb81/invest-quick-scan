"""Add the one missing frozen registry and preserve the failed preparation."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/"runs/r13a"
OUT=IQS/"docs/implementation/intake/G3/2026-10-09-jr13"

def main():
    name="src/config/quick_scan_metric_registry.json"
    path=OWN/"qa"/name
    assert not path.exists() and not (OUT/"joint-dependency-02.json").exists()
    env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env["GIT_OPTIONAL_LOCKS"]="0"
    sha="bc41908e4cdc44c13fefda97f3118e5434aed5f8"
    raw=subprocess.check_output(["git","show",sha+":"+name],cwd=IQS.parent/"StockQAbyLLM",env=env)
    path.write_bytes(raw)
    record={"path":name,"source_commit":sha,"sha256":hashlib.sha256(raw).hexdigest(),
        "reason":"joint-01 CLI rejected before HTTP because this registry was omitted from the isolated export",
        "product_failure":False,"real_API_calls":0}
    (OUT/"joint-dependency-02.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    for folder in [OWN/"logs/joint",OWN/"cases/a-selected"]:
        for item in folder.rglob("*"):
            if item.is_file() and item.suffix in {".log", ".jsonl"} or item.is_file() and item.name.endswith((".response.json",".process.json")):
                target=OUT/"joint-01-detail"/item.relative_to(OWN)
                assert not target.exists()
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(item.read_bytes())
    suite=IQS/"docs/implementation/reviews/G3/jr13-2026-10-09/test_joint.py"
    text=suite.read_text("utf-8").replace("h.OWN / 'cases/", "h.CASES / '").replace("h.OWN/'cases/", "h.CASES/'").replace("h.OWN / 'cases'", "h.CASES").replace("h.OWN/'cases'", "h.CASES")
    suite.write_text(text,encoding="utf-8")
    (OWN/"test_joint.py").write_bytes(suite.read_bytes())
    (OWN/"joint_harness.py").write_bytes((suite.parent/"joint_harness.py").read_bytes())
    print(json.dumps(record))

if __name__=='__main__':main()
