"""Extend the owned JR13 runtime with a frozen non-secret QA export."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
QA = IQS.parent / "StockQAbyLLM"
COMMIT = "bc41908e4cdc44c13fefda97f3118e5434aed5f8"

def main():
    destination = OUT / "joint-input-01.json"
    assert OWN.is_dir() and not (OWN / "qa").exists() and not destination.exists()
    env = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=QA, env=env)
    assert git("rev-parse", "HEAD").decode().strip() == COMMIT
    status = git("status", "--porcelain=v1").decode()
    assert not any(line[:2].strip() != "??" for line in status.splitlines())
    names = git("ls-tree", "-r", "--name-only", COMMIT).decode().splitlines()
    selected = [n for n in names if (
        n.startswith(("src/", "tests/")) and n.endswith(".py")
        or n.startswith("src/") and n.endswith(".schema.json")
        or n.startswith("tests/fixtures/quick_scan") and n.endswith(".json")
        or n in {"main_with_llm.py", "main.py", "pyproject.toml"})]
    rows = []
    for name in selected:
        raw = git("show", COMMIT + ":" + name)
        target = OWN / "qa" / name
        assert target.resolve().is_relative_to(OWN.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    adapters = {}
    for owner in ("qa", "sw"):
        for kind, directory, source in (
            ("legacy", "joint-2026-10-08", owner + "_driver.py"),
            ("current", "joint-2026-10-09-rebase", owner + "_actor.py")):
            path = IQS / "docs/implementation/reviews/G3" / directory / source
            raw = path.read_bytes()
            filename = "legacy_" + owner + "_actor.py" if kind == "legacy" else owner + "_actor.py"
            (OWN / filename).write_bytes(raw)
            adapters[path.relative_to(IQS).as_posix()] = hashlib.sha256(raw).hexdigest()
    manifest = OWN / "qa/tests/fixtures/quick_scan_c06_manifest_v2_fixture.json"
    raw = manifest.read_bytes()
    doc = json.loads(raw)
    locks = []
    for lock in doc["module_locks"]:
        data = (IQS / lock["artifact_ref"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == lock["artifact_sha256"]
        locks.append({"path": lock["artifact_ref"], "sha256": lock["artifact_sha256"]})
    release = {"module_package_id": doc["module_package_id"], "release_id": doc["module_release_id"],
        "catalog_version": doc["template_version"], "semantic_fingerprint_version": "2.0.0",
        "questions": {q["id"]: {"field_id":q["metric_id"], "scope":q["scope"], "response_kind":"score",
            "rubric_version":q["rubric_version"], "construct_id":q["construct_id"],
            "definition_sha256":q["definition_sha256"], "semantic_sha256":q["semantic_sha256"]} for q in doc["questions"]}}
    release_raw = (json.dumps(release, ensure_ascii=False, indent=2)+"\n").encode()
    (OWN / "independent-release.json").write_bytes(release_raw)
    (OUT / "independent-release.json").write_bytes(release_raw)
    sw_rows = {p.relative_to(OWN/"sw").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (OWN/"sw").rglob("*") if p.is_file()}
    assert git("rev-parse", "HEAD").decode().strip() == COMMIT
    assert git("status", "--porcelain=v1").decode() == status
    record = {"schema":"jr13-joint-source-lock/1", "QA_head":COMMIT, "QA_source_files":rows,
        "SW_base":"c40de21403720306ba21edbf71b9634a40ee58f8", "SW_candidate_files":sw_rows,
        "adapters":adapters, "manifest_sha256":hashlib.sha256(raw).hexdigest(), "module_locks":locks,
        "release_sha256":hashlib.sha256(release_raw).hexdigest(), "release_basis":"pre-dispatch synthetic manifest, independent of observation",
        "schema_sha256":hashlib.sha256((IQS/"schemas/quick_scan/exchange.schema.json").read_bytes()).hexdigest(),
        "guard_sha256":hashlib.sha256((OWN/"guard/sitecustomize.py").read_bytes()).hexdigest(),
        "synthetic_only":True, "real_owner_golden":False, "real_API_calls":0, "source_written":False}
    destination.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"QA_source_files":len(rows),"SW_files":len(sw_rows),"source_written":False}))

if __name__ == "__main__":main()
