"""Finalization composition units; synthetic ports are not production evidence.

The original owner software / SQLite / SDK positive lives in the opt-in native
E2E. These fast units test the glue's all-before-write guards and idempotence.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "StockQAbyLLM"))
sys.path.insert(0, str(ROOT.parent / "iqs-company-agent-lab/src"))
sys.path.insert(0, str(ROOT.parent / "iqs-agent-runtime-lab/src"))
spec = importlib.util.spec_from_file_location("finalization_engine", ROOT / "scripts/shared_company_engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
from src.utils.quick_scan_owner_research import OwnerResearchServices


class MapperOnlyServices(OwnerResearchServices):
    """Contract-only double: never admitted and never calls a network client."""
    def __init__(self, task, *, expired=False, proof_bad=False):
        self.task, self.saves, self.restores = task, [], []
        self.expired, self.proof_bad = expired, proof_bad
        self.owner = SimpleNamespace(entries={q: {"kind": "work", "work_item_id": "WORK_" + q} for q in task.question_ids})
        self.rows, self.checkpoints, self.standards = {}, {}, {}
        for q in task.question_ids:
            self.rows["WORK_" + q] = {"work_item_id": "WORK_" + q, "question_id": q, "status": "leased"}
        self.store = SimpleNamespace(
            get_item=lambda w: copy.deepcopy(self.rows[w]),
            list_attempts=lambda w: [{"attempt_id": "ATTEMPT_" + self.rows[w]["question_id"]}],
            get_attempt_response=self._response,
            get_answer_checkpoint=lambda w: copy.deepcopy(self.checkpoints.get(w)),
            get_standard_answer=lambda w: copy.deepcopy(self.standards.get(w)),
            get_result_delivery=lambda w: {"state": "ready"} if w in self.checkpoints and not getattr(self, "delivery_pending", False) else None,
            get_external_context_use=lambda a: {"proof": {"use_id": "tampered"}} if self.proof_bad else None,
        )
    def _assert_registered_inputs(self):
        pass
    def _response(self, attempt_id):
        q = attempt_id.removeprefix("ATTEMPT_")
        return {"receipt": {"attempt_id": "native_" + q, "search_status": "executed", "source_urls": ["https://example.invalid/" + q]}}
    def inspect_attempt(self, ref):
        q = ref.removeprefix("stockqa:native_")
        if q not in self.task.question_ids:
            return {"known": False, "response_saved": None}
        return {"known": True, "native_receipt": self._response("ATTEMPT_" + q)["receipt"],
                "response_saved": {"final_content": json.dumps({"answers": [answer(q)], "declared_question_ids": [q]}), "tool_calls": None}}
    def restore_finalization_handle(self, question_id, *, native_reference):
        if self.expired:
            raise ValueError("original lease expired")
        self.restores.append(question_id)
        return {"work_item_id": "WORK_" + question_id}
    def commit_standard_answers(self, answers, *, native_reference):
        for body in answers:
            q = body["question_id"]
            if "WORK_" + q in self.checkpoints:
                continue  # Existing same-native standard answer only needs native resealing.
            if getattr(self, "fail_on", None) == q:
                raise RuntimeError("synthetic storage failure after earlier member committed")
            if self.proof_bad:
                raise ValueError("original external proof mismatch")
            self.saves.append(q)
            w = "WORK_" + q
            self.checkpoints[w] = {"checkpoint_id": "CHECKPOINT_" + q, "attempt_id": "ATTEMPT_" + q,
                "payload_sha256": "a" * 64, "payload": {"provenance": {"provider_attempt_id": "native_" + q}}}
            self.standards[w] = {"answer": copy.deepcopy(body)}
            self.rows[w]["status"] = "result_ready"


def answer(q):
    return {"question_id": q, "status": "insufficient_evidence", "score": None, "summary": "synthetic test only"}


@pytest.fixture
def bound(monkeypatch):
    task = SimpleNamespace(question_ids=["IQS_05", "IQS_06"], raw={"run_id": "synthetic-finalize"})
    run = {"run_id": task.raw["run_id"], "slots": [{"question_id": q, "execution_status": "completed", "answer": answer(q), "attempt_refs": ["stockqa:native_" + q]} for q in task.question_ids]}
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: copy.deepcopy(run))
    return task, MapperOnlyServices(task), run


def test_explicit_finalizer_calls_original_seam_and_reuses_completed_checkpoints(bound):
    task, services, _ = bound
    first = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert first["status"] == "completed" and services.saves == task.question_ids
    assert first["new_model_http"] == 0 and first["financial_accuracy_assessed"] is False
    assert len(first["checkpoints"]) == 2
    # A fresh service carrier can inspect existing checkpoints without a lease or HTTP.
    services.expired = True
    again = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert again["reused_question_ids"] == task.question_ids
    assert services.saves == task.question_ids


def test_finalizer_refuses_arbitrary_service_before_export_read():
    with pytest.raises(engine.SharedEngineRejected, match="original_owner"):
        engine.finalize_shared_engine(object(), object(), Path("never-read"))


@pytest.mark.parametrize("change", ["wrong_ref", "foreign_member", "changed_answer", "partial"])
def test_finalizer_preflights_all_slots_before_any_native_save(bound, monkeypatch, change):
    task, services, run = bound
    if change == "wrong_ref":
        run["slots"][1]["attempt_refs"] = ["stockqa:foreign"]
    elif change == "foreign_member":
        run["slots"][1]["attempt_refs"] = ["stockqa:native_IQS_05"]
    elif change == "changed_answer":
        run["slots"][1]["answer"]["summary"] = "changed after native output"
    else:
        run["slots"][1]["execution_status"] = "not_attempted"
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: copy.deepcopy(run))
    with pytest.raises(engine.SharedEngineRejected):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert services.saves == []


def test_expired_original_lease_is_not_renewed_or_resent(bound):
    task, services, _ = bound
    services.expired = True
    with pytest.raises(ValueError, match="lease expired"):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert services.saves == []


def test_native_external_proof_mismatch_cannot_be_replaced_with_caller_data(bound):
    task, services, _ = bound
    services.proof_bad = True
    with pytest.raises(ValueError, match="external proof"):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert services.saves == [] and services.checkpoints == {}


def test_existing_checkpoint_for_different_standard_answer_is_not_reused(bound):
    task, services, _ = bound
    engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    services.standards["WORK_IQS_06"]["answer"]["summary"] = "conflicting existing answer"
    with pytest.raises(engine.SharedEngineRejected, match="existing_checkpoint"):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert services.saves == task.question_ids


def test_partial_native_publication_resumes_only_unsaved_member_without_resend(bound):
    task, services, _ = bound
    services.fail_on = "IQS_06"
    with pytest.raises(RuntimeError, match="storage failure"):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert services.saves == ["IQS_05"]
    assert set(services.checkpoints) == {"WORK_IQS_05"}
    services.fail_on = None
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert result["reused_question_ids"] == ["IQS_05"]
    assert result["new_model_http"] == 0
    assert services.saves == task.question_ids and len(services.checkpoints) == 2


def test_saved_checkpoints_with_failed_seal_do_not_claim_finalization_complete(bound):
    task, services, _ = bound
    services.delivery_pending = True
    pending = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert pending["status"] == "checkpointed_delivery_pending"
    assert pending["checkpoint_status"] == "completed"
    assert pending["pending_delivery_question_ids"] == task.question_ids
    assert services.saves == task.question_ids
    services.delivery_pending = False
    completed = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert completed["status"] == "completed" and completed["pending_delivery_question_ids"] == []
    assert completed["reused_question_ids"] == task.question_ids
    assert completed["new_model_http"] == 0 and services.saves == task.question_ids
