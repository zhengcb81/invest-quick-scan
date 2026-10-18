"""Different-agent, wire-free probes. All artifacts remain under this review dir."""
import copy
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1] / "company-candidate"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from test_runtime_provenance import executed, observed, export
from iqs_company_agent_lab.canonical import sha256_hex
from iqs_company_agent_lab.provenance import summarize_runtime_evidence
from iqs_company_agent_lab.reporter import generate_report
from iqs_company_agent_lab.evidence import EvidenceBoard
from iqs_company_agent_lab.errors import ProtocolIllegalError
from conftest import make_task
from test_runtime_provenance import OwnerShapedTestPort
from iqs_company_agent_lab.runner import Runner
from iqs_company_agent_lab.checkpoint import build_checkpoint
from iqs_company_agent_lab.task import task_from_bundle


def persist(path, value):
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf8"))


@pytest.mark.parametrize("rewrite_run_epoch", [False, True])
def test_rehashed_board_cannot_relabel_original_synthetic_sources(tmp_path, rewrite_run_epoch):
    runner = executed()
    doc = observed(runner)
    export(tmp_path, runner, doc)
    folder = tmp_path / "run"
    board = json.loads((folder / "evidence-board.json").read_bytes())
    assert board["records"]
    for record in board["records"]:
        record["source_url"] = "https://public.example.org/rewritten-source/" + record["evidence_id"]
    persist(folder / "evidence-board.json", board)
    run = json.loads((folder / "research-run.json").read_bytes())
    raw = (folder / "evidence-board.json").read_bytes()
    run["evidence_board_ref"].update(bytes=len(raw), sha256=sha256_hex(raw))
    # Deliberately keep the original journal and original evidence_epoch_sha256.
    assert EvidenceBoard.from_snapshot(board).epoch_sha256() != run["evidence_epoch_sha256"]
    if rewrite_run_epoch:
        run["evidence_epoch_sha256"] = EvidenceBoard.from_snapshot(board).epoch_sha256()
    persist(folder / "research-run.json", run)
    doc["evidence_origin"] = "fixed_public_context"
    persist(folder / "runtime-evidence.json", doc)
    try:
        summary = summarize_runtime_evidence(doc, run=run, events=runner.journal.events,
            run_raw=(folder / "research-run.json").read_bytes(), board_doc={}, board_snapshot=board)
        persist(folder / "runtime-summary.json", summary)
        generate_report(folder, tmp_path / "report")
    except ProtocolIllegalError:
        return
    raise AssertionError("Original synthetic source URLs were replaced and relabeled public without changing original journal")


def test_private_native_metadata_refused_before_export(tmp_path):
    runner = executed()
    doc = observed(runner)
    doc["attempts"][0]["native_receipt"]["request_id"] = "reasoning_content SECRET THOUGHT"
    doc["attempts"][0]["native_receipt_sha256"] = sha256_hex(doc["attempts"][0]["native_receipt"])
    try:
        export(tmp_path, runner, doc)
    except ProtocolIllegalError:
        assert not (tmp_path / "run").exists()
        return
    raise AssertionError("Private content accepted in bounded native metadata")


def test_unknown_partial_native_usage_does_not_claim_total(tmp_path):
    runner = executed()
    doc = observed(runner)
    doc["attempts"] = doc["attempts"][:1]
    result = export(tmp_path, runner, doc)["runtime_summary"]
    assert result["native_observation_complete"] is False
    assert result["new_model_http"] is None
    assert result["cash_cost"] is None


def test_conflicting_provider_same_physical_id_not_double_counted(tmp_path):
    runner = executed()
    doc = observed(runner)
    doc["attempts"][1]["native_receipt"] = copy.deepcopy(doc["attempts"][0]["native_receipt"])
    doc["attempts"][1]["native_receipt"]["provider"] = "different-provider"
    doc["attempts"][1]["native_receipt_sha256"] = sha256_hex(doc["attempts"][1]["native_receipt"])
    try:
        export(tmp_path, runner, doc)
    except ProtocolIllegalError:
        return
    raise AssertionError("Conflicting native identity was merged")


def test_boolean_usage_does_not_count_as_integer(tmp_path):
    runner = executed()
    doc = observed(runner)
    doc["attempts"][0]["native_receipt"]["usage"]["input_tokens"] = True
    doc["attempts"][0]["native_receipt_sha256"] = sha256_hex(doc["attempts"][0]["native_receipt"])
    try:
        export(tmp_path, runner, doc)
    except ProtocolIllegalError:
        return
    raise AssertionError("Boolean native usage accepted as integer")


def test_zero_evidence_run_still_exports_honest_unobserved_summary(tmp_path):
    task = copy.deepcopy(make_task("fixed3", "independent-empty-board"))
    task.evidence_board_doc["records"] = []
    runner = Runner(task, OwnerShapedTestPort(task.raw["run_id"]))
    runner.run()
    doc = observed(runner)
    doc["evidence_origin"] = "unobserved"
    result = export(tmp_path, runner, doc)
    assert result["runtime_summary"]["evidence_origin"] == "unobserved"
    assert result["runtime_summary"]["financial_qualification_granted"] is False


def test_checkpoint_owns_task_bundle_after_creation():
    runner = executed()
    checkpoint = build_checkpoint(runner.state, runner.journal)
    original = copy.deepcopy(checkpoint)
    runner.task.runtime_profile["independent_mutable_source_probe"] = "later task edit"
    runner.task.questions[0]["question"]["question"] = "later source object edit"
    assert checkpoint == original, "snapshot task bundle aliases later mutable task state"


def test_restored_task_does_not_alias_original_checkpoint():
    runner = executed()
    checkpoint = build_checkpoint(runner.state, runner.journal)
    original = copy.deepcopy(checkpoint)
    task = task_from_bundle(checkpoint["task_bundle"])
    task.runtime_profile["independent_resumed_task_probe"] = "new process configuration"
    assert checkpoint == original, "restored task aliases original checkpoint task bundle"
