"""Cold public CLI preserves paid work, then resumes the never-sent member.

Original native owner/SDK/Runner/SQLite; synthetic issuer and scripted wire.
Recovery subprocesses receive no credential or sending configuration, assert
zero API calls, and use only temporary business data. A later run restores the
original authorized route and proves the remaining question is sent once.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_company_scan_native_e2e import (
    actual, setup_admission, construct, SAFE_ENV, CODE, COMPANY, BRIDGE,
    _policy, RefreshAdmissionService, _task_snapshot,
)


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_paid_partial_cold_cli_without_current_sending_configuration(actual, tmp_path, monkeypatch):
    from src.core.models import Question
    from src.providers.llm_client import LLMClient
    from src.utils.quick_scan_shared_routes import run_ordered_company_scan
    import importlib
    from src.utils.http_client import http_client_manager
    from tests.unit.test_llm_client import _b01_thinking_response
    from iqs_company_agent_lab import synthfixtures as sf
    from iqs_company_agent_lab.runner import Runner

    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    policy["routes"] = policy["routes"][:1]
    targets = [dict(provider="mimo", model=r["model"], route_id=r["id"],
        provider_config_ref=r["provider_config_ref"], quota_group=r["quota_group"])
        for r in policy["routes"]]
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo",
        selected_question_count=2, refresh_version="1.6.0", ordered_route_targets=targets)
    accepted = RefreshAdmissionService(prepared["deployment_file"], process_env=dict(SAFE_ENV)).admit(
        prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    model_file = tmp_path / "model-config.json"
    model_file.write_text(json.dumps({"providers": {t["provider_config_ref"]:
        {"base_url": "https://api.xiaomimimo.com/v1/chat/completions"} for t in targets}}), encoding="utf8")
    model_config_bytes = model_file.read_bytes()
    settings = dict(root=str(tmp_path), deployment=str(prepared["deployment_file"]),
        confirmation_id=prepared["consent"]["confirmation_id"], bundle=str(prepared["bundle"]),
        policy=policy, llm_config_file=str(model_file))
    task, services = construct(settings)
    task_contract = _task_snapshot(task)
    config = dict(schema_version="1.0.0", iqs_root=str(CODE), company_agent_root=str(COMPANY),
        runtime_bridge_root=str(BRIDGE), state_root=str(tmp_path / "shared"),
        limits={"max_model_requests_per_session": 2})
    config_file = tmp_path / "shared.json"
    config_file.write_text(json.dumps(config), encoding="utf8")
    budget_policy_file = Path(json.loads(prepared["deployment_file"].read_text(encoding="utf8"))["budget_policy_file"])
    budget_policy_bytes = budget_policy_file.read_bytes()
    clients = [(r, LLMClient("SCRIPTED-NOT-A-SECRET", r["model"],
        "https://api.xiaomimimo.com/v1/chat/completions", provider_name="mimo"))
        for r in policy["routes"]]
    sent = []
    sent_question_ids = []
    continuation_question_id = None

    class Wire:
        def post(self, *args, **kwargs):
            body = kwargs["json"]
            sent.append(copy.deepcopy(body))
            selected = json.loads(body["messages"][-1]["content"].splitlines()[-1])["requested_question_ids"]
            assert len(selected) == 1
            sent_question_ids.append(selected)
            if len(sent) == 2:
                assert selected == [continuation_question_id]
            else:
                assert len(sent) == 1, "the scenario permits one paid attempt and one authorized continuation"
            answer = sf.gen_insufficient(next(row["question"] for row in task_contract["questions"]
                                             if row["question_id"] == selected[0]))
            answer.update(status="not_applicable", information_as_of=task_contract["raw"]["information_cutoff"],
                summary="[Synthetic software fixture] Normal answer retained; no financial finding.")
            response = _b01_thinking_response("mimo_chat_completions", targets[0]["model"],
                final=json.dumps({"answers": [answer], "declared_question_ids": selected}))
            response.content = json.dumps(response.json.return_value).encode()
            return response

    monkeypatch.setattr(http_client_manager, "get_sync_session", lambda: Wire())
    questions = [Question(row["question"]["prompt"], question_id=row["question_id"]) for row in task_contract["questions"]]
    shared_engine = importlib.import_module("shared_company_engine")
    with monkeypatch.context() as interrupted:
        def stop_before_answer_commit(*args, **kwargs):
            raise RuntimeError("scripted_process_death_after_paid_safe_capture")
        interrupted.setattr(Runner, "_process_response", stop_before_answer_commit)
        with pytest.raises(shared_engine.SharedEngineInterrupted):
            run_ordered_company_scan(services.lifecycle, clients, config=config, questions=questions,
                cost_resolver=services.cost_resolver, question_pack_size=1, max_output_tokens=32768,
                transport_origin="scripted_wire")
    assert len(sent) == 1
    work_ids = [services.owner.existing_work(q)["work_item_id"] for q in task_contract["question_ids"]]
    assert all(services.store.get_answer_checkpoint(wid) is None for wid in work_ids)
    attempts_before = [services.store.list_attempts(wid) for wid in work_ids]
    assert sorted(len(rows) for rows in attempts_before) == [0, 1]
    paid_index = next(i for i, rows in enumerate(attempts_before) if rows)
    question_ids = task_contract["question_ids"]
    paid_question_id = question_ids[paid_index]
    continuation_question_id = question_ids[1 - paid_index]
    assert sent_question_ids == [[paid_question_id]]
    paid_response = services.store.get_attempt_response(attempts_before[paid_index][0]["attempt_id"])
    budget_requests_before_recovery = services.store.get_quick_scan_budget_status(
        policy["policy_id"]
    )["requests"]
    assert budget_requests_before_recovery == 1
    budget_policy_file.unlink()
    model_file.unlink()
    # These are future sending controls, not locations or original inputs.
    config.update(limits={"max_model_requests_per_session": 0}, pack_by="obsolete-unused-setting")
    config_file.write_text(json.dumps(config), encoding="utf8")
    assert not (tmp_path / "llm_apis.json").exists()
    output = tmp_path / "paid-output.json"
    ref = task_contract["raw"]["owner_binding"]["subject_ref"]
    qa_root = Path(sys.modules["src"].__file__).resolve().parent.parent
    command = [sys.executable, "-B", "-X", "utf8", str(qa_root / "main_with_llm.py"),
        "--company", "Synthetic issuer", "--entity-id", ref["entity_id"], "--require-search",
        "--seal-deliveries", "--recover-checkpoints", "--shared-company-config", str(config_file),
        "--refresh-admission-config", str(prepared["deployment_file"]),
        "--refresh-confirmation-id", prepared["consent"]["confirmation_id"], "--output", str(output)]
    for filename, flag in (("questions.json", "config"), ("manifest.json", "question-manifest"),
        ("identity.json", "identity-snapshot"), ("authority.json", "c06-authority"),
        ("owner-config.json", "quick-scan-owner-config")):
        command += ["--" + flag, str(prepared["bundle"] / filename)]
    env = dict(SAFE_ENV)
    for iteration in range(2):
        result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True,
                                encoding="utf8", timeout=240)
        assert result.returncode == 0, result.stdout[-5000:] + result.stderr[-5000:]
        scope = json.loads(output.with_suffix(".json.scope.json").read_text(encoding="utf8"))
        assert scope["status"] == "partial" and scope["original_question_count"] == 2
        assert scope["saved_question_ids"] == [paid_question_id]
        assert scope["restored_question_count"] == 1
        assert scope["remaining_question_ids"] == [continuation_question_id]
        assert scope["API_requests"] == 0 and scope["dispatch_started"] is False
        checkpoint = services.store.get_answer_checkpoint(work_ids[paid_index])
        assert checkpoint is not None
        assert services.store.get_answer_checkpoint(work_ids[1-paid_index]) is None
        assert services.store.get_result_delivery(work_ids[paid_index])["state"] == "ready"
        assert services.store.get_attempt_response(attempts_before[paid_index][0]["attempt_id"]) == paid_response
        assert [services.store.list_attempts(wid) for wid in work_ids] == attempts_before
        assert services.store.get_quick_scan_budget_status(policy["policy_id"])["requests"] == budget_requests_before_recovery
        if iteration == 0:
            first_checkpoint = checkpoint
        else:
            assert checkpoint == first_checkpoint
    assert len(sent) == 1

    # The prior two cold recoveries were read/replay-only. Restore the exact
    # original current controls, construct a fresh owner port over the same
    # durable action, and prove the never-sent member can be dispatched once.
    budget_policy_file.write_bytes(budget_policy_bytes)
    model_file.write_bytes(model_config_bytes)
    config.update(limits={"max_model_requests_per_session": 2})
    config.pop("pack_by", None)
    continuation_task, continuation_services = construct(settings)
    continuation_contract = _task_snapshot(continuation_task)
    assert continuation_contract["question_ids"] == question_ids
    result = run_ordered_company_scan(
        continuation_services.lifecycle,
        clients,
        config=config,
        questions=questions,
        cost_resolver=continuation_services.cost_resolver,
        question_pack_size=1,
        max_output_tokens=32768,
        transport_origin="scripted_wire",
    )
    assert sent_question_ids == [[paid_question_id], [continuation_question_id]]
    assert len(sent) == 2
    # The ordered coordinator returns no summary on the fully checkpointed path;
    # durable owner state below is the completion contract.
    assert result is None
    assert all(continuation_services.store.get_answer_checkpoint(wid) is not None for wid in work_ids)
    assert all(continuation_services.store.get_result_delivery(wid)["state"] == "ready" for wid in work_ids)
    assert continuation_services.store.get_quick_scan_budget_status(policy["policy_id"])["requests"] == 2
