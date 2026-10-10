"""One-time documentation input freeze. No producer implementation or API calls."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
LAB = ROOT.parent / "iqs-evidence-lab"
FACT = ROOT.parent / "iqs-fact-content-lab"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], encoding="utf-8", errors="strict"
    ).strip()


def record(root: Path, relative: str, consumers: list[str]) -> dict:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Invalid fixed input: {path}")
    raw = path.read_bytes()
    return {
        "source_root": root.as_posix(), "path": relative,
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "hash_domain": "working_tree_raw_bytes", "consumers": consumers,
    }


def write(name: str, value: dict) -> None:
    path = HERE / name
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> None:
    expected = {
        ROOT: "8d57f2ae1855d8105fa8abaccfef13ed2ff090ce",
        LAB: "2c0efb6370e401ca84d5f23cd5047de2bbfdec0a",
    }
    before = {}
    for root, head in expected.items():
        actual = git(root, "rev-parse", "HEAD")
        if actual != head:
            raise RuntimeError(f"Source HEAD drift: {root}")
        before[root] = {
            "root": root.as_posix(), "head": actual,
            "branch": git(root, "branch", "--show-current"),
            "status_porcelain": git(root, "status", "--porcelain=v1", "-uall").splitlines(),
        }
    if FACT.exists():
        raise RuntimeError("New FACT directory already exists; do not overwrite")
    common = [
        "questions/facts.json", "questions/common.json", "questions/catalog.json",
        "questions/metric-registry.json", "schemas/answer-content.schema.json",
        "schemas/observation.schema.json", "schemas/quick_scan/question-module.schema.json",
        "schemas/quick_scan/module-release.schema.json", "references/standard-output.md",
        "references/accuracy-first-operations.md", "docs/implementation/composable-evolution-plan.md",
        "docs/implementation/tasks.json",
    ]
    evidence = [
        "docs/implementation/experiments/accuracy-first-results-2026-10-07.md",
        "docs/implementation/experiments/accuracy-pricing-2026-10-07.json",
    ]
    archive = "docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/"
    evidence.extend(git(ROOT, "ls-tree", "-r", "--name-only", "HEAD", "--", archive).splitlines())
    lab_inputs = [
        "README.md", "src/iqs_evidence_lab/hashing.py", "src/iqs_evidence_lab/guards.py",
        "src/iqs_evidence_lab/errors.py", "src/iqs_evidence_lab/semantic.py",
        "docs/handoff/EVID-LAB-01/experiment-proposal.md",
        "docs/handoff/EVID-LAB-01/experiment-proposal.config.json",
    ]
    files = [record(ROOT, p, ["EVID-REF-02", "FACT-CONTENT-01"]) for p in common]
    files.extend(record(ROOT, p, ["EVID-REF-02"]) for p in evidence)
    files.extend(record(LAB, p, ["EVID-REF-02"]) for p in lab_inputs)
    facts = json.loads((ROOT / "questions/facts.json").read_text(encoding="utf-8"))
    proposal = json.loads((LAB / lab_inputs[-1]).read_text(encoding="utf-8"))
    questions = facts["questions"]
    if len(questions) != 61 or len({q["id"] for q in questions}) != 61:
        raise RuntimeError("Fact baseline is not the fixed unique 61")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lock = {
        "format_version": "1.0.0", "observed_at_utc": now,
        "source_written": False, "api_requests": 0,
        "coordinator_reserved_roots": [ROOT.as_posix(), (ROOT.parent / "StockQAbyLLM").as_posix(), (ROOT.parent / "StockWiki").as_posix()],
        "repositories": list(before.values()),
        "new_repository": {"root": FACT.as_posix(), "exists": False},
        "files": files,
        "fact_baseline": {"version": facts["version"], "question_count": 61,
                          "question_ids": [q["id"] for q in questions],
                          "field_ids": [q["field_id"] for q in questions]},
        "reference_sample": proposal["sample"]["companies"],
        "reference_question_ids": proposal["sample"]["question_ids"],
        "private_query_v2_consumed": False,
        "note": "Observations, not repository locks; preserve CodeGraph infrastructure and unrelated changes. Local candidate delivery does not close original G3/F05 or complete task IDs.",
    }
    definitions = [
        {"id": "EVID-REF-02", "root": LAB, "tasks": ["L02", "B01"],
         "head": expected[LAB], "branch": before[LAB]["branch"],
         "paths": ["src/iqs_evidence_lab/reference", "schemas/reference-pack-v1.schema.json", "schemas/reference-evaluation-v1.schema.json", "tests/reference", "fixtures/reference", "tools/reference_entry.py", "docs/handoff/EVID-REF-02"],
         "scope": "reference_candidate_and_offline_evaluation_only", "network": "harness_public_read_only_evidence_collection_only"},
        {"id": "FACT-CONTENT-01", "root": FACT, "tasks": ["F01", "F03", "F04", "F05", "F06", "V03", "V07"],
         "head": "NEW_REPOSITORY_TEMPLATE_ONLY", "branch": "NEW_REPOSITORY_TEMPLATE_ONLY",
         "paths": ["README.md", ".gitignore", "pyproject.toml", "src/iqs_fact_content_lab", "schemas", "content", "tests", "fixtures", "tools", "docs/handoff/FACT-CONTENT-01"],
         "scope": "fact_content_candidate_and_semantic_acceptance_data_only", "network": "none"},
    ]
    manifest = {
        "format_version": "1.0.0", "observed_at_utc": now,
        "task_source": "../../../tasks.json", "coordinator_write_scope": ROOT.as_posix(),
        "workers_dispatched": False, "default_live_enabled": False,
        "packages": [], "held_packages": ["TH-IMPL-01", "IN-IMPL-01"],
        "previous_deliveries_preserved": True,
    }
    for d in definitions:
        manifest["packages"].append({
            "id": d["id"], "lane_id": "iqs", "document": d["id"] + ".md",
            "task_ids": d["tasks"], "write_scope": d["root"].as_posix(),
            "authorized_relative_paths": d["paths"],
            "readiness": "ready_for_scoped_support_after_unique_writer_preflight",
            "authorization": "human_all_followup_authorized; human_dispatch_selects_worker; card_path_scope_only",
            "delivery_scope": d["scope"], "full_task_completion_delegated": False,
            "model_api_enabled": False, "paid_search_enabled": False,
            "network_scope": d["network"],
        })
        current = before.get(d["root"], {"status_porcelain": []})
        dirty = len(current["status_porcelain"])
        template = {
            "schema_version": "1.0.0", "lane_id": "iqs", "package_id": d["id"], "status": "partial",
            "snapshot": {"repository": d["root"].as_posix(), "base_ref": d["branch"], "base_commit": d["head"],
                         "result_ref": "", "result_commit": None,
                         "worktree_before": {"state": "dirty" if dirty else "clean", "dirty_path_count": dirty, "manifest_sha256": None},
                         "worktree_after": {"state": "dirty" if dirty else "clean", "dirty_path_count": dirty, "manifest_sha256": None}},
            "scope": {"task_ids": d["tasks"], "authorization_scope_ref": "human_all_followup_grant; TEMPLATE_ONLY_NOT_DISPATCHED",
                      "owned_paths": [d["root"].as_posix()], "authorized_paths": [], "changed_paths": [], "out_of_scope_writes": []},
            "interfaces": [], "verification": {"checks": [], "external_writes": False, "network_calls": False,
                                                  "paid_calls": False, "temporary_roots": []},
            "review": {"status": "not_run", "snapshot_commit": None, "findings": []},
            "open_items": ["TEMPLATE ONLY, not executed; replace every before/after and result field with actual worker evidence.",
                           "lane_id=iqs does not grant IQS repository write access; only the package directory is owned.",
                           "No full task completion or G3/F05/TH-IN/live approval delegated.",
                           "Human reference qualification and source evidence are separate from software tests."],
            "next_action": "Read this card and common handoff rules; sole-writer preflight, input SHA check, then independent scoped implementation.",
        }
        write(d["id"] + ".handoff.template.json", template)
    write("inputs.lock.json", lock)
    write("manifest.json", manifest)
    for item in files:
        if record(Path(item["source_root"]), item["path"], item["consumers"]) != item:
            raise RuntimeError("Input byte drift during freeze")
    for root, head in expected.items():
        if git(root, "rev-parse", "HEAD") != head:
            raise RuntimeError("HEAD drift during freeze")
    if git(LAB, "status", "--porcelain=v1", "-uall").splitlines() != before[LAB]["status_porcelain"]:
        raise RuntimeError("Lab working tree drift during freeze")
    print(json.dumps({"inputs": len(files), "packages": 2, "fact_questions": 61,
                      "reference_slots": len(proposal["sample"]["companies"]) * len(proposal["sample"]["question_ids"]),
                      "api_requests": 0, "external_source_written": False}))


if __name__ == "__main__":
    main()
