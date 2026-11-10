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
from iqs_company_agent_lab.evidence import EvidenceBoard
from iqs_company_agent_lab.api import create_owner_task, task_snapshot


class MapperOnlyServices(OwnerResearchServices):
    """Contract-only double: never admitted and never calls a network client."""
    def __init__(self, task, *, expired=False, proof_bad=False):
        self.task, self.saves, self.restores = task, [], []
        self.expired, self.proof_bad = expired, proof_bad
        self.owner = SimpleNamespace(bundle={"authority": {}}, entries={q: {"kind": "work", "work_item_id": "WORK_" + q} for q in task_snapshot(task)["question_ids"]})
        self.rows, self.checkpoints, self.standards = {}, {}, {}
        for q in task_snapshot(task)["question_ids"]:
            self.rows["WORK_" + q] = {"work_item_id": "WORK_" + q, "question_id": q, "status": "leased"}
        self.store = SimpleNamespace(
            get_item=lambda w: copy.deepcopy(self.rows[w]),
            list_attempts=lambda w: [{"attempt_id": "ATTEMPT_" + self.rows[w]["question_id"]}],
            get_attempt_response=self._response,
            get_answer_checkpoint=lambda w: copy.deepcopy(self.checkpoints.get(w)),
            get_standard_answer=lambda w: copy.deepcopy(self.standards.get(w)),
            get_result_delivery=lambda w: {"state": "ready"} if w in self.checkpoints and not getattr(self, "delivery_pending", False) and w not in getattr(self, "delivery_pending_work_ids", set()) else None,
            get_external_context_use=lambda a: {"proof": {"use_id": "tampered"}} if self.proof_bad else None,
        )
    def _assert_registered_inputs(self, *, check_current=True):
        pass
    def bind_task_owner_binding(self, binding):
        contract = task_snapshot(self.task)
        subject = contract["company_doc"]["subject"]["subject_ref"]
        if binding.get("subject_ref") != subject:
            raise ValueError("native_task_owner_binding_mismatch")
        self._task_binding = copy.deepcopy(binding)
    def _response(self, attempt_id):
        q = attempt_id.removeprefix("ATTEMPT_")
        return {"receipt": {"attempt_id": "native_" + q, "search_status": "executed", "source_urls": ["https://example.invalid/" + q]}}
    def inspect_attempt(self, ref):
        q = ref.removeprefix("stockqa:native_")
        if q not in task_snapshot(self.task)["question_ids"]:
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


def finalization_task(question_ids):
    subject_ref = {"entity_id": "SYNTHETIC_FINALIZE", "scope": "entity", "scope_id": "SYNTHETIC_FINALIZE"}
    raw = {
        "protocol": "iqs.company-scan-task/1.0.0",
        "run_id": "synthetic-finalize",
        "company_ref": {"path": "company.json", "bytes": 1, "sha256": "a" * 64},
        "information_cutoff": "2026-10-15",
        "limits": {},
        "strategy_id": "free_agent",
        "question_refs": [],
    }
    return create_owner_task(
        raw,
        [{"question_id": qid, "question": {"id": qid}} for qid in question_ids],
        {"origin": "owner_public", "subject": {"subject_ref": subject_ref}},
        {"records": []},
        {"provider": "synthetic-test", "model": "synthetic-test"},
        {},
        owner_binding={
            "protocol": "iqs.native-company-owner-binding/1.0.0",
            "synthetic": False,
            "subject_ref": subject_ref,
            "authority_ref": {"id": "synthetic-authority"},
        },
    )


@pytest.fixture
def bound(monkeypatch):
    from src.utils import quick_scan_delivery_seal
    # The native helper's actual SQLite/authority match is tested in StockQA.
    # This fixture isolates composition only, never grants native authority.
    monkeypatch.setattr(quick_scan_delivery_seal, "get_matching_sealed_delivery",
                        lambda store, wid, *, authority: store.get_result_delivery(wid))
    question_ids = ["IQS_05", "IQS_06"]
    task = finalization_task(question_ids)
    run = {"run_id": task_snapshot(task)["raw"]["run_id"], "slots": [{"question_id": q, "execution_status": "completed", "answer": answer(q), "attempt_refs": ["stockqa:native_" + q]} for q in task_snapshot(task)["question_ids"]]}
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: (copy.deepcopy(run), EvidenceBoard(2000)))
    # Glue-only double; the dedicated semantic suite exercises the original rule.
    monkeypatch.setattr(engine, "_production_answer_semantics", lambda *args, **kwargs: lambda body, qid: None)
    return task, MapperOnlyServices(task), run


def test_explicit_finalizer_calls_original_seam_and_reuses_completed_checkpoints(bound):
    task, services, _ = bound
    first = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert first["status"] == "completed" and services.saves == task_snapshot(task)["question_ids"]
    assert first["new_model_http"] == 0 and first["financial_accuracy_assessed"] is False
    assert len(first["checkpoints"]) == 2
    # A fresh service carrier can inspect existing checkpoints without a lease or HTTP.
    services.expired = True
    again = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert again["reused_question_ids"] == task_snapshot(task)["question_ids"]
    assert services.saves == task_snapshot(task)["question_ids"]


def test_finalization_summary_uses_verified_task_id_when_slot_projection_has_no_id(bound, monkeypatch):
    task, services, run = bound
    monkeypatch.setattr(engine, "_verified_finalization_export",
                        lambda *args: ({"slots": copy.deepcopy(run["slots"])}, EvidenceBoard(2000)))
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert result["run_id"] == task_snapshot(task)["raw"]["run_id"]
    assert result["status"] == "completed"


def test_finalizer_refuses_arbitrary_service_before_export_read():
    with pytest.raises(engine.SharedEngineRejected, match="original_company_task_contract_required"):
        engine.finalize_shared_engine(object(), object(), Path("never-read"))


def test_finalizer_normalizes_invalid_owner_runtime_before_export_read(tmp_path):
    task = finalization_task(["IQS_INVALID_RUNTIME"])
    export = tmp_path / "must-not-read-or-create"
    with pytest.raises(engine.SharedEngineRejected, match="original_owner_research_services"):
        engine.finalize_shared_engine(task, object(), export)
    assert not export.exists()


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
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: (copy.deepcopy(run), EvidenceBoard(2000)))
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
    assert services.saves == task_snapshot(task)["question_ids"]


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
    assert services.saves == task_snapshot(task)["question_ids"] and len(services.checkpoints) == 2


def test_saved_checkpoints_with_failed_seal_do_not_claim_finalization_complete(bound):
    task, services, _ = bound
    services.delivery_pending = True
    pending = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert pending["status"] == "checkpointed_delivery_pending"
    assert pending["checkpoint_status"] == "completed"
    assert pending["pending_delivery_question_ids"] == task_snapshot(task)["question_ids"]
    assert services.saves == task_snapshot(task)["question_ids"]
    services.delivery_pending = False
    completed = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert completed["status"] == "completed" and completed["pending_delivery_question_ids"] == []
    assert completed["reused_question_ids"] == task_snapshot(task)["question_ids"]
    assert completed["new_model_http"] == 0 and services.saves == task_snapshot(task)["question_ids"]


def test_old_ready_package_is_not_current_authority_completion(bound, monkeypatch):
    from src.utils import quick_scan_delivery_seal
    task, services, _ = bound
    current = {"matched": False}
    monkeypatch.setattr(quick_scan_delivery_seal, "get_matching_sealed_delivery",
        lambda store, wid, *, authority: store.get_result_delivery(wid) if current["matched"] else None)
    first = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert first["checkpoint_status"] == "completed"
    assert first["status"] == "checkpointed_delivery_pending"
    assert all(row["delivery_state"] == "ready" and not row["delivery_matches_authority"] for row in first["checkpoints"])
    assert first["pending_delivery_question_ids"] == task_snapshot(task)["question_ids"]
    before = copy.deepcopy(services.checkpoints)
    current["matched"] = True
    again = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert again["status"] == "completed" and again["whole_task_finalized"]
    assert services.checkpoints == before and again["new_model_http"] == 0


@pytest.mark.parametrize("stage", ["restore", "commit", "seal", "after_success"])
@pytest.mark.parametrize("error_name", ["WorkConflictError", "LeaseFencedError"])
def test_work_local_finalization_conflict_preserves_other_members(bound, stage, error_name):
    from src.utils import quick_scan_work_store as native_store
    _, _, run = bound
    task = finalization_task(["IQS_05", "IQS_06", "IQS_07"])
    run["slots"].append(dict(question_id="IQS_07", execution_status="completed",
        answer=answer("IQS_07"), attempt_refs=["stockqa:native_IQS_07"]))
    services = MapperOnlyServices(task)
    restore, commit = services.restore_finalization_handle, services.commit_standard_answers
    fault = {"enabled": True}
    error_type = getattr(native_store, error_name)

    def restore_member(qid, **kwargs):
        if fault["enabled"] and stage == "restore" and qid == "IQS_06":
            raise error_type("synthetic member changed")
        return restore(qid, **kwargs)

    def commit_member(bodies, **kwargs):
        if fault["enabled"] and stage in {"commit", "seal", "after_success"} and bodies[0]["question_id"] == "IQS_06":
            if stage in {"seal", "after_success"}:
                commit(bodies, **kwargs)
                services.delivery_pending_work_ids = {"WORK_IQS_06"} if stage == "seal" else set()
            raise error_type("synthetic member changed")
        return commit(bodies, **kwargs)

    services.restore_finalization_handle, services.commit_standard_answers = restore_member, commit_member
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert {"IQS_05", "IQS_07"} <= set(services.saves)
    assert result["finalization_errors"][0]["question_id"] == "IQS_06"
    assert (result["status"] == "completed") == (stage == "after_success")
    assert result["whole_task_finalized"] == (stage == "after_success")
    assert result["unfinalized_question_ids"] == ([] if stage in {"seal", "after_success"} else ["IQS_06"])
    assert result["pending_delivery_question_ids"] == (["IQS_06"] if stage == "seal" else [])
    assert result["new_model_http"] == 0
    before = copy.deepcopy(services.checkpoints)
    fault["enabled"], services.delivery_pending_work_ids = False, set()
    again = engine.finalize_shared_engine(task, services, Path("unused-unit-export"))
    assert again["status"] == "completed" and again["whole_task_finalized"]
    assert all(services.checkpoints[k] == v for k, v in before.items())
    assert services.saves.count("IQS_05") == services.saves.count("IQS_07") == 1


def test_native_bare_single_answer_preserves_all_fields():
    body = answer("IQS_05")
    engine._native_final_answer({"final_content": json.dumps(body), "tool_calls": None}, "IQS_05", body)


@pytest.mark.parametrize("case", ["wrong_qid", "changed_field", "trailing_json", "duplicate_pack"])
def test_native_bare_or_pack_rejects_conflicting_originals(case):
    expected = answer("IQS_05")
    body = copy.deepcopy(expected)
    if case == "wrong_qid":
        body["question_id"] = "IQS_06"
    elif case == "changed_field":
        body["summary"] = "different native field"
    if case == "duplicate_pack":
        content = json.dumps({"answers": [body, body], "declared_question_ids": ["IQS_05"]})
    else:
        content = json.dumps(body) + (" {}" if case == "trailing_json" else "")
    with pytest.raises(engine.SharedEngineRejected):
        engine._native_final_answer({"final_content": content, "tool_calls": None}, "IQS_05", expected)


def test_native_answer_replays_original_citation_ids_without_mutating_inputs():
    from iqs_company_agent_lab.answers import check_citation_closure
    from iqs_company_agent_lab.evidence import EvidenceBoard
    body = dict(answer("IQS_05"), evidence=[{"id": "model-local-id", "url": "https://example.invalid/original", "claim": "Synthetic original source."}],
                metrics=[{"evidence_ids": ["model-local-id"]}], items=[{"evidence_ids": ["model-local-id"]}])
    board = EvidenceBoard(2000)
    board_before = copy.deepcopy(board.snapshot())
    native_before = copy.deepcopy(body)
    expected = copy.deepcopy(body)
    check_citation_closure(expected, board, board.publication_exclusive_date)
    engine._native_final_answer({"final_content": json.dumps(body), "tool_calls": None}, "IQS_05", expected, evidence_board=board)
    assert body == native_before and board.snapshot() == board_before
    for key in ("summary", "score"):
        changed = copy.deepcopy(expected)
        changed[key] = "modified" if key == "summary" else 9
        with pytest.raises(engine.SharedEngineRejected):
            engine._native_final_answer({"final_content": json.dumps(body), "tool_calls": None}, "IQS_05", changed, evidence_board=board)
    wrong_id = copy.deepcopy(expected)
    wrong_id["metrics"][0]["evidence_ids"] = ["foreign-id"]
    with pytest.raises(engine.SharedEngineRejected):
        engine._native_final_answer({"final_content": json.dumps(body), "tool_calls": None}, "IQS_05", wrong_id, evidence_board=board)


def test_native_answer_rejects_unsupported_external_citation():
    from iqs_company_agent_lab.evidence import EvidenceBoard
    body = dict(answer("IQS_05"), evidence=[{"id": "missing", "url": "http://example.invalid/not-https"}])
    with pytest.raises(engine.SharedEngineRejected):
        engine._native_final_answer({"final_content": json.dumps(body), "tool_calls": None}, "IQS_05", body, evidence_board=EvidenceBoard(2000))


@pytest.mark.parametrize("remaining_status", ["not_attempted", "paused", "failed"])
def test_partial_finalizer_saves_only_original_completed_selection(bound, remaining_status):
    task, services, run = bound
    run["slots"][1].update(execution_status=remaining_status, answer=None, attempt_refs=[])
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"),
                                           question_ids=["IQS_05"])
    assert result["status"] == "partial"
    assert result["checkpoint_status"] == "partial"
    assert result["selected_question_ids"] == ["IQS_05"]
    assert result["unfinalized_question_ids"] == ["IQS_06"]
    assert result["original_question_count"] == 2
    assert result["selected_question_count"] == 1
    assert result["whole_task_finalized"] is False
    assert services.saves == services.restores == ["IQS_05"]
    assert set(services.checkpoints) == {"WORK_IQS_05"}
    assert result["new_model_http"] == 0 and result["financial_accuracy_assessed"] is False
    # Existing matching first-member CP is reused without touching the other member.
    services.expired = True
    again = engine.finalize_shared_engine(task, services, Path("unused-unit-export"),
                                          question_ids=["IQS_05"])
    assert again["status"] == "partial" and again["reused_question_ids"] == ["IQS_05"]
    assert services.saves == services.restores == ["IQS_05"]


@pytest.mark.parametrize("selection", [[], ["IQS_05", "IQS_05"], ["foreign"], "IQS_05", [None], True])
def test_partial_selection_cannot_grant_foreign_or_ambiguous_scope(bound, selection):
    task, services, _ = bound
    with pytest.raises(engine.SharedEngineRejected, match="selection"):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"), question_ids=selection)
    assert services.saves == services.restores == []


@pytest.mark.parametrize("fault", ["not_completed", "wrong_native", "changed_answer", "foreign_member"])
def test_partial_selection_retains_all_native_preflight_guards(bound, fault):
    task, services, run = bound
    selected = run["slots"][0]
    if fault == "not_completed":
        selected["execution_status"] = "not_attempted"
    elif fault == "wrong_native":
        selected["attempt_refs"] = ["stockqa:foreign"]
    elif fault == "changed_answer":
        selected["answer"]["summary"] = "modified paid output"
    else:
        services.owner.entries["IQS_05"]["work_item_id"] = "WORK_IQS_06"
    with pytest.raises(engine.SharedEngineRejected):
        engine.finalize_shared_engine(task, services, Path("unused-unit-export"), question_ids=["IQS_05"])
    assert services.saves == services.restores == []


def test_explicit_all_selection_uses_original_task_order_and_retains_complete_semantics(bound):
    task, services, _ = bound
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"),
                                           question_ids=list(reversed(task_snapshot(task)["question_ids"])))
    assert result["status"] == "completed" and result["whole_task_finalized"] is True
    assert services.saves == task_snapshot(task)["question_ids"]
    assert result["selected_question_ids"] == task_snapshot(task)["question_ids"]
    assert result["unfinalized_question_ids"] == []


def test_explicit_full_scope_with_pending_delivery_is_not_whole_task_finalized(bound):
    task, services, _ = bound
    services.delivery_pending = True
    result = engine.finalize_shared_engine(task, services, Path("unused-unit-export"),
                                           question_ids=task_snapshot(task)["question_ids"])
    assert result["status"] == "checkpointed_delivery_pending"
    assert result["whole_task_finalized"] is False
    assert result["pending_delivery_question_ids"] == task_snapshot(task)["question_ids"]
