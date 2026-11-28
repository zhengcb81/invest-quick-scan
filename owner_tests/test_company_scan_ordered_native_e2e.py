"""Original owner/SDK two-model continuation; only vendor wire is scripted."""
import copy
import json

import pytest

from test_company_scan_native_e2e import (
    actual, setup_admission, construct, SAFE_ENV, CODE, COMPANY, BRIDGE,
    _policy, RefreshAdmissionService,
)


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_original_ordered_shared_refusal_fallback_and_zero_send_resume(actual, tmp_path, monkeypatch):
    from src.core.models import Question
    from src.providers.llm_client import LLMClient
    from src.utils.quick_scan_shared_routes import run_ordered_company_scan
    from src.utils.http_client import http_client_manager
    from tests.unit.test_llm_client import _b01_thinking_response
    from iqs_company_agent_lab import synthfixtures as sf
    import requests

    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    policy["routes"] = policy["routes"][:2]
    policy["routes"][1]["model"] = "mimo-v2.6-flash"
    targets = [dict(provider="mimo", model=r["model"], route_id=r["id"],
        provider_config_ref=r["provider_config_ref"], quota_group=r["quota_group"])
        for r in policy["routes"]]
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo",
        selected_question_count=2, refresh_version="1.6.0", ordered_route_targets=targets)
    from datetime import datetime, timedelta, timezone

    consent_expiry = datetime.fromisoformat(
        prepared["consent"]["delegation"]["expires_at"].replace("Z", "+00:00")
    )
    assert consent_expiry > datetime.now(timezone.utc) + timedelta(hours=12)
    accepted = RefreshAdmissionService(prepared["deployment_file"], process_env=dict(SAFE_ENV)).admit(
        prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    llm_config = tmp_path / "model-config.json"
    llm_config.write_text(json.dumps({"providers": {t["provider_config_ref"]:
        {"base_url": "https://api.xiaomimimo.com/v1/chat/completions"} for t in targets}}), encoding="utf8")
    settings = dict(root=str(tmp_path), deployment=str(prepared["deployment_file"]),
        confirmation_id=prepared["consent"]["confirmation_id"], bundle=str(prepared["bundle"]),
        policy=policy, llm_config_file=str(llm_config))
    task, services = construct(settings)
    config = dict(schema_version="1.0.0", iqs_root=str(CODE), company_agent_root=str(COMPANY),
        runtime_bridge_root=str(BRIDGE), state_root=str(tmp_path / "shared"),
        limits={"max_model_requests_per_session": 2})
    clients = [(r, LLMClient("SCRIPTED-NOT-A-SECRET", r["model"],
        "https://api.xiaomimimo.com/v1/chat/completions", provider_name="mimo", timeout=10))
        for r in policy["routes"]]
    sent = []

    class Wire:
        def post(self, *args, **kwargs):
            body = kwargs["json"]
            sent.append(copy.deepcopy(body))
            assert body["thinking"] == {"type": "enabled"}
            assert body["max_completion_tokens"] == 32768
            if len(sent) == 1:
                assert body["model"] == targets[0]["model"]
                response = requests.Response()
                response.status_code = 401
                response.headers = {"x-request-id": "scripted-primary-explicit-refusal"}
                response._content = json.dumps({"error": {"code": "invalid_api_key",
                    "message": "synthetic explicit refusal"}}).encode()
                return response
            assert len(sent) == 2 and body["model"] == targets[1]["model"]
            selected = json.loads(body["messages"][-1]["content"].splitlines()[-1])["requested_question_ids"]
            assert set(selected) == set(task_contract["question_ids"])
            answers = [sf.gen_insufficient(row["question"]) for row in task_contract["questions"]]
            for answer in answers:
                answer.update(status="not_applicable", information_as_of=task_contract["raw"]["information_cutoff"],
                    summary="[Synthetic software fixture] No real company finding or financial rating.")
            response = _b01_thinking_response("mimo_chat_completions", targets[1]["model"],
                final=json.dumps({"answers": answers, "declared_question_ids": selected}))
            response.content = json.dumps(response.json.return_value).encode()
            return response

    monkeypatch.setattr(http_client_manager, "get_sync_session", lambda: Wire())
    # Native tasks are opaque owner handles. The coordinator uses the detached
    # JSON contract projection instead of reaching into LoadedTask internals.
    from iqs_company_agent_lab.api import task_snapshot
    task_contract = task_snapshot(task)
    questions = [Question(row["question"]["prompt"], question_id=row["question_id"])
        for row in task_contract["questions"]]
    import importlib
    # Resolve the configured engine by its public module name; tests should not
    # depend on the coordinator's private loader helper or tuple shape.
    shared_engine = importlib.import_module("shared_company_engine")
    def interrupt_publication(*args, **kwargs):
        raise RuntimeError("scripted_publication_interrupt_after_paid_response")
    with monkeypatch.context() as interrupted:
        interrupted.setattr(shared_engine, "finalize_shared_engine", interrupt_publication)
        # This injected publication hook is called by the public coordinator
        # after the engine returns, so the test-owned interruption propagates.
        with pytest.raises(
            RuntimeError, match="scripted_publication_interrupt_after_paid_response"
        ):
            run_ordered_company_scan(services.lifecycle, clients, config=config, questions=questions,
                cost_resolver=services.cost_resolver, question_pack_size=2, max_output_tokens=32768,
                transport_origin="scripted_wire")
    assert len(sent) == 2
    work_ids = [services.owner.existing_work(q)["work_item_id"] for q in task_contract["question_ids"]]
    assert all(services.store.get_answer_checkpoint(wid) is None for wid in work_ids)
    assert services.store.company_scan_progress(work_ids)["model_requests"] == 2
    monkeypatch.setattr(http_client_manager, "get_sync_session",
                        lambda: pytest.fail("paid fallback response must not be requested again"))
    original_config = llm_config.read_bytes()
    llm_config.unlink()  # Paid-only recovery must not require today's key/endpoint file.
    _, paid = construct(dict(settings, recovery_only=True))
    # Mirror the production recovery runner: the owner returns only routes
    # bound to received responses, explicitly marked response-only. The
    # coordinator still selects the original route from durable progress.
    recovery_routes = paid.owner.execution_routes(None)
    assert [route["id"] for route in recovery_routes] == [targets[1]["route_id"]]
    recovery_clients = [
        (
            route,
            LLMClient("", route["model"], "", provider_name=route["provider"]),
        )
        for route in recovery_routes
    ]
    assert all(route["eligible"] is False for route, _ in recovery_clients)
    run_ordered_company_scan(paid.lifecycle, recovery_clients, config=config, questions=questions,
        cost_resolver=paid.cost_resolver, question_pack_size=2, max_output_tokens=32768,
        transport_origin="scripted_wire", recovery_only=True)
    llm_config.write_bytes(original_config)
    original_checkpoints = []
    for wid in work_ids:
        checkpoint = services.store.get_answer_checkpoint(wid)
        assert checkpoint is not None
        original_checkpoints.append(checkpoint)
        assert [a["phase"] for a in services.store.list_attempts(wid)] == ["confirmed_failure", "response_available"]
        assert [a["model_requested"] for a in services.store.list_attempts(wid)] == [t["model"] for t in targets]
        assert services.store.get_owner_refresh_binding(wid)["binding"]["model"] == targets[0]["model"]
        assert services.store.get_result_delivery(wid)["state"] == "ready"
    assert paid.lifecycle.hydrate_question(questions[0]) is not None
    assert services.store.company_scan_progress(work_ids)["model_requests"] == 2
    assert len(list((tmp_path / "shared").glob("scan-*"))) == 2
    monkeypatch.setattr(http_client_manager, "get_sync_session",
                        lambda: pytest.fail("original completed scope must not send"))
    # Reconstruct the original owner/lifecycle, preserving the same two tasks.
    _, restored = construct(settings)
    run_ordered_company_scan(restored.lifecycle, clients, config=config, questions=list(reversed(questions)),
        cost_resolver=restored.cost_resolver, question_pack_size=2, max_output_tokens=32768,
        transport_origin="scripted_wire")
    assert [restored.store.get_answer_checkpoint(wid) for wid in work_ids] == original_checkpoints
    assert restored.lifecycle.hydrate_question(questions[0]) is not None
    assert restored.store.company_scan_progress(work_ids)["model_requests"] == 2 and len(sent) == 2
