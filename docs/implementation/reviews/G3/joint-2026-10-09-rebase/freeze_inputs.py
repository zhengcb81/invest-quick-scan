"""Read-only source inspection, record current integration inputs in IQS.

This is preparation, not a test, permission, new gate or producer golden.
No source imports/runtime copies/API calls/real DB access are performed.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OWNERS = {
    "StockQAbyLLM": {"commit": "bc41908e4cdc44c13fefda97f3118e5434aed5f8", "paths": [
        "src/utils/quick_scan_work_store.py", "src/utils/quick_scan_result_outbox.py",
        "src/utils/quick_scan_delivery_seal.py", "src/utils/quick_scan_observation_context.py",
        "tests/integration/test_qa_c06_02_subprocess_cli.py", "tests/fixtures/quick_scan_c06_manifest_v2_fixture.json"]},
    "StockWiki": {"commit": "c40de21403720306ba21edbf71b9634a40ee58f8", "paths": [
        "stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py",
        "tests/test_quick_scan_observations.py", "tests/test_quick_scan_delivery.py",
        "stockwiki/cli.py", "stockwiki/paths.py"]},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    env = {key: value for key, value in os.environ.items() if not key.upper().endswith("_API_KEY")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.check_output(["git", *args], cwd=repo, env=env)


def state(repo):
    return {"head": git(repo, "rev-parse", "HEAD").decode().strip(),
            "branch": git(repo, "branch", "--show-current").decode().strip(),
            "status": git(repo, "status", "--porcelain=v1").decode().replace("\r\n", "\n")}


def main():
    target = HERE / "inputs-01.json"
    assert not target.exists(), "Do not replace a previous preparation observation"
    observations = {}
    for name, spec in OWNERS.items():
        repo = Path("C:/Users/郑曾波/Projects") / name
        before = state(repo)
        assert before["head"] == spec["commit"] and before["branch"] == "master", name
        assert not before["status"] if name == "StockWiki" else (
            len(before["status"].splitlines()) == 7 and all(row.startswith("?? ") for row in before["status"].splitlines()))
        rows = []
        for path in spec["paths"]:
            raw = git(repo, "show", before["head"] + ":" + path)
            row = {"path": path, "git_blob_bytes": len(raw), "git_blob_sha256": sha(raw)}
            if path.endswith(".py"):
                tree = ast.parse(raw.decode("utf-8"))
                row["current_public_signatures"] = {node.name: ast.unparse(node.args) for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name in {
                        "bind_result_delivery_consumer", "begin_result_delivery", "apply_result_delivery_ack", "store_id", "ack_for"}}
            else:
                json.loads(raw)
            if name == "StockWiki" and path in spec["paths"][:4]:
                old = git(repo, "show", "d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff:" + path)
                row["unchanged_from_previous_joint_baseline"] = raw == old
            rows.append(row)
        assert state(repo) == before, "Dynamic source drift; reconcile before using preparation"
        observations[name] = {**before, "files": rows, "source_written": False}
    internal_paths = ["schemas/quick_scan/exchange.schema.json",
        "docs/implementation/reviews/G3/joint-2026-10-08/qa_driver.py",
        "docs/implementation/reviews/G3/joint-2026-10-08/sw_driver.py",
        "docs/implementation/reviews/G3/joint-2026-10-08/remediation.md",
        "docs/implementation/reviews/QA-C06-02/second-remediation-2026-10-08/sitecustomize.py",
        "docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/llm_providers.inert.yaml"]
    internal = []
    for name in internal_paths:
        path = IQS / name
        raw = path.read_bytes()
        assert raw == git(IQS, "show", "HEAD:" + name), name
        internal.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    adapters = []
    for name in ("qa_actor.py", "sw_actor.py", "freeze_inputs.py", "README.md"):
        raw = (HERE / name).read_bytes()
        if name.endswith(".py"):
            ast.parse(raw.decode("utf-8"))
        adapters.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {"schema": "joint-rebase-preparation/1.0.0", "observed_on": "2026-10-09",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "iqs_observed_head": git(IQS, "rev-parse", "HEAD").decode().strip(), "owners": observations,
        "fixed_internal_dependencies": internal, "new_test_adapters": adapters,
        "execution_status": "prepared_not_executed", "StockWiki_write_authorization": "pending_human_answer",
        "fixture_is_real_owner_golden": False, "new_public_CLI_capability": False,
        "tests_passed": None, "joint_ACK_closed": False, "whole_project_gates_closed": False,
        "production_DBs_read_or_written": False, "real_API_calls": 0,
        "next": "After exact StockWiki authorization/fix, create a NEW input lock and guarded runtime; never run old fixed-root helpers"}
    target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"prepared_owner_paths": sum(len(owner["files"]) for owner in observations.values()),
        "new_adapters_AST_valid": True, "tests_executed": 0, "source_writes": 0, "real_API_calls": 0,
        "StockWiki_authorization": "pending_human_answer"}))


if __name__ == "__main__":
    main()
