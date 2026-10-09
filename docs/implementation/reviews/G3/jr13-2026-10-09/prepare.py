"""Export only non-secret tracked code/assets into a new IQS-owned runtime."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
SW = IQS.parent / "StockWiki"
COMMIT = "c40de21403720306ba21edbf71b9634a40ee58f8"
ENV = {k:v for k,v in os.environ.items() if not k.upper().endswith("_API_KEY")}
ENV["GIT_OPTIONAL_LOCKS"] = "0"

def git(*args):
    return subprocess.check_output(["git", *args], cwd=SW, env=ENV)

def main():
    assert not OWN.exists() and not OUT.exists(), "Fresh runtime and intake required"
    assert git("rev-parse", "HEAD").decode().strip() == COMMIT
    assert not git("status", "--porcelain=v1").strip(), "Owner source drift"
    names = git("ls-tree", "-r", "--name-only", COMMIT).decode().splitlines()
    excluded = {"config/companies.yaml", "config/workspace.yaml", "config/integrations.yaml", "config/llm_providers.yaml"}
    selected = [n for n in names if (
        n.startswith(("stockwiki/", "tests/", "scripts/")) and n.endswith(".py")
        or n.startswith("tests/fixtures/") and Path(n).suffix in {".json", ".csv", ".md"}
        or n.startswith("framework/") and Path(n).suffix in {".yaml", ".md"}
        or n.startswith("config/") and n.endswith(".yaml") and n not in excluded
        or n in {"pyproject.toml", "pytest.ini"})]
    (OWN / "sw").mkdir(parents=True)
    OUT.mkdir(parents=True)
    rows = []
    for name in selected:
        raw = git("show", COMMIT + ":" + name)
        target = OWN / "sw" / name
        assert target.resolve().is_relative_to(OWN.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        rows.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    for name in ("guard", "tmp", "logs", "cases"):
        (OWN / name).mkdir()
    guard = IQS / "docs/implementation/reviews/QA-C06-02/second-remediation-2026-10-08/sitecustomize.py"
    (OWN / "guard/sitecustomize.py").write_bytes(guard.read_bytes())
    (OWN / "sw/config/companies.yaml").write_text("companies: []\n", encoding="utf-8")
    (OWN / "sw/config/llm_providers.yaml").write_bytes((IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/llm_providers.inert.yaml").read_bytes())
    for name in ("workspace.yaml", "integrations.yaml"):
        (OWN / "sw/config" / name).write_text("{}\n", encoding="utf-8")
    assert git("rev-parse", "HEAD").decode().strip() == COMMIT
    assert not git("status", "--porcelain=v1").strip()
    record = {"schema": "jr13-source-input/1", "source_head": COMMIT,
        "authorization": "User: 授权这4个文件，由你接管。", "owned_root": str(OWN),
        "source_files": rows, "guard_sha256": hashlib.sha256(guard.read_bytes()).hexdigest(),
        "real_API_calls": 0, "production_DB_access": False, "source_written": False}
    (OUT / "input-01.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"exported_source_files": len(rows), "source_written": False, "real_API_calls": 0}))

if __name__ == "__main__":
    main()
