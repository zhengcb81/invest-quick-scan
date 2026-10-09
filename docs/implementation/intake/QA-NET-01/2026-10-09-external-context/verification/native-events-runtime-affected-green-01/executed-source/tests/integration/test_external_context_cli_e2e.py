"""Actual public main() with synthetic identity/manifest/pricing and HTTP only.

These are software integration fixtures, never StockWiki owner goldens or
financial correctness evidence. Every file and database stays in tmp_path.
"""
import hashlib
import json
from contextlib import closing
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
import requests

from tests.integration.test_quick_scan_cli import _http_failure, _invoke, _ordered_policy, _response
from tests.unit.test_quick_scan_external_context import _execution_policy_document
from tests.unit.test_external_search_provider import _response as search_response
from src.utils.quick_scan_work_store import QuickScanWorkStore


def _inputs(tmp_path, monkeypatch, *, hybrid=False):
    # Independently freeze inputs before constructing any model answer.
    prompt = "公司的第1项核心优势是否持久？"
    identity = {"object_type": "entity", "schema_version": "2.2.0", "payload": {
        "entity_id": "ENT_SYNTHETIC", "identity_revision": 1, "identity_state": "verified",
        "listings": [{"source_binding_ref": "BND_SYNTHETIC_ONLY"}]},
        "fixture_notice": "synthetic identity, not a StockWiki verified issuer golden"}
    identity_path = tmp_path / "identity-synthetic.json"
    identity_path.write_text(json.dumps(identity), encoding="utf-8")
    digest = lambda data: hashlib.sha256(data).hexdigest()
    manifest = {"schema_version": "1.0.0", "template_version": "synthetic/1", "question_count": 1,
        "modules": ["synthetic/core"], "module_locks": {}, "replacements": {}, "questions": [{
        "id": "IQS_05", "module_id": "synthetic/core", "scope": "entity", "prompt": prompt,
        "prompt_sha256": digest(prompt.encode()), "semantic_sha256": digest(b"synthetic-semantic"),
        "definition_sha256": digest(b"synthetic-definition")}]}
    manifest_path = tmp_path / "manifest-synthetic.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    search = _execution_policy_document()
    search["external_routes"][0]["credential_env"] = "IQS_SYNTHETIC_SEARCH_TOKEN"
    search["external_routes"][0]["endpoint"] = "https://api.search.brave.com/res/v1/web/search"
    plan = search["execution_plan"]
    plan["entity_id"] = "ENT_SYNTHETIC"
    plan["identity_snapshot_sha256"] = digest(identity_path.read_bytes())
    plan["question_manifest_sha256"] = digest(manifest_path.read_bytes())
    for origin in plan["entity_domain_bindings"]:
        origin["identity_snapshot_sha256"] = plan["identity_snapshot_sha256"]
    if hybrid:
        search["selection"].update(mode="explicit_hybrid", hybrid_plan_reference="synthetic-hybrid/1")
        plan["answer_search_mode"] = "native_with_external_context"
    search_path = tmp_path / "search-synthetic.json"
    search_path.write_text(json.dumps(search), encoding="utf-8")
    model = _ordered_policy(max_attempts=1)
    model["models"] = [{**model["models"][0], "provider_config_ref": "openai", "model": "gpt-4.1"}]
    model["budget"]["max_cost"] = 25
    providers = {"openai": {"enabled": True, "api_key": "synthetic-only", "model": "gpt-4.1",
        "base_url": "https://api.openai.com/v1/responses", "max_retries": 1}}
    monkeypatch.setenv("IQS_SYNTHETIC_SEARCH_TOKEN", "synthetic-only")
    session = Mock()
    session.request.return_value = search_response(json.dumps({"web": {"results": [{
        "title": "Synthetic issuer", "url": "https://fixture.example/ir",
        "description": "Synthetic margin disclosure", "page_age": "2026-10-01"}]}}).encode())
    monkeypatch.setattr("src.utils.http_client.http_client_manager.get_metered_sync_session", lambda: session)
    response = _response(searched=hybrid, content=json.dumps({"entity_id": "ENT_SYNTHETIC", "company_name": "Fixture Corp",
        "question_id": "IQS_05", "status": "scored", "score": 6, "description": "Synthetic supported answer"}))
    response.json.return_value["model"] = "gpt-4.1"
    response.json.return_value["output"][-1]["role"] = "assistant"
    response.content = json.dumps(response.json.return_value).encode()
    response.text = response.content.decode()
    kwargs = dict(entity_id="ENT_SYNTHETIC", model_policy=model, provider_configs=providers, responses=[response], extra_argv=[
        "--identity-snapshot", str(identity_path), "--question-manifest", str(manifest_path), "--search-policy", str(search_path)])
    return kwargs, session, search_path


@pytest.mark.parametrize("hybrid", [False, True])
def test_public_external_main_cold_and_warm_keep_receipt_and_avoid_http(tmp_path, monkeypatch, hybrid):
    kwargs, search, _ = _inputs(tmp_path, monkeypatch, hybrid=hybrid)
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0
    first = json.loads(output.read_text("utf-8"))
    assert first["schema_version"] == "stockqa.quick_scan_result/1.1.0"
    receipt = first["execution_receipts"]["IQS_05"]
    assert receipt["search_status"] == "executed" and "search_binding" in receipt
    assert first["answers"]["IQS_05"]["score"] == 6
    assert search.request.call_count == 1 and models.post.call_count == 1
    proof = receipt["search_binding"]["external_context_use"]
    # Consumer's public temporal contract: persistence/use occurs after the
    # original HTTP completion and no later than the durable answer time.
    assert datetime.fromisoformat(receipt["completed_at"].replace("Z", "+00:00")) <= datetime.fromtimestamp(proof["used_at"], timezone.utc)
    assert datetime.fromtimestamp(proof["used_at"], timezone.utc) <= datetime.fromisoformat(receipt["answered_at"].replace("Z", "+00:00"))
    store = QuickScanWorkStore(tmp_path / "quick_scan_work.sqlite")
    assert store.get_answer_checkpoint(proof["work_item_id"])["checkpoint_schema_version"] == 2
    before = store.get_quick_scan_budget_status("quick-scan-test-policy")
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0
    second = json.loads(output.read_text("utf-8"))
    assert second["execution_receipts"]["IQS_05"]["answered_at"] == receipt["answered_at"]
    assert second["execution_receipts"]["IQS_05"] == receipt
    assert search.request.call_count == 1 and models.post.call_count == 0
    assert store.get_quick_scan_budget_status("quick-scan-test-policy") == before


def test_public_external_main_wrong_manifest_fails_before_store_or_http(tmp_path, monkeypatch, caplog):
    kwargs, search, path = _inputs(tmp_path, monkeypatch)
    document = json.loads(path.read_text("utf-8"))
    document["execution_plan"]["question_manifest_sha256"] = "e" * 64
    path.write_text(json.dumps(document), encoding="utf-8")
    code, _, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code != 0
    assert "external_policy_manifest_mismatch" in caplog.text
    assert search.request.call_count == 0 and models.post.call_count == 0
    assert not (tmp_path / "quick_scan_work.sqlite").exists()


def test_public_external_main_uncertain_search_preserves_reservation_and_stops_model(tmp_path, monkeypatch):
    kwargs, search, _ = _inputs(tmp_path, monkeypatch)
    search.request.side_effect = requests.Timeout("synthetic timeout")
    code, _, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code != 0
    assert search.request.call_count == 1 and models.post.call_count == 0
    store = QuickScanWorkStore(tmp_path / "quick_scan_work.sqlite")
    budget = store.get_quick_scan_budget_status("quick-scan-test-policy")
    assert budget["requests"] == 1 and budget["reserved_micros"] > 0


@pytest.mark.parametrize("hybrid", [False, True])
@pytest.mark.parametrize("status", [401, 429])
def test_public_external_main_fallback_reuses_context_and_recovers_all_actual_attempts(tmp_path, monkeypatch, hybrid, status):
    kwargs, search, _ = _inputs(tmp_path, monkeypatch, hybrid=hybrid)
    model = _ordered_policy(max_attempts=2)
    model["models"][0]["model"] = "gpt-4.1"
    model["models"][1]["model"] = "gpt-4.1-mini"
    model["budget"]["max_cost"] = 25
    primary = dict(kwargs["provider_configs"]["openai"])
    backup = {**primary, "model": "gpt-4.1-mini"}
    response = kwargs["responses"][0]
    response.json.return_value["model"] = "gpt-4.1-mini"
    response.content = json.dumps(response.json.return_value).encode()
    response.text = response.content.decode()
    rejection = _http_failure(status, error_code="insufficient_quota" if status == 429 else None)
    rejection.content = json.dumps(rejection.json.return_value).encode()
    rejection.text = rejection.content.decode()
    kwargs.update(model_policy=model, provider_name="primary", provider_configs={"primary": primary, "backup": backup},
                  responses=[rejection, response])
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0
    receipt = json.loads(output.read_text("utf-8"))["execution_receipts"]["IQS_05"]
    assert receipt["requested_model"] == receipt["actual_model"] == "gpt-4.1-mini"
    assert [attempt["http_status_code"] for attempt in receipt["attempts"]] == [status, 200]
    assert [attempt["requested_model"] for attempt in receipt["attempts"]] == ["gpt-4.1", "gpt-4.1-mini"]
    assert search.request.call_count == 1 and models.post.call_count == 2
    payloads = [call.kwargs["json"] for call in models.post.call_args_list]
    assert payloads[0]["input"] == payloads[1]["input"]
    proof = receipt["search_binding"]["external_context_use"]
    store = QuickScanWorkStore(tmp_path / "quick_scan_work.sqlite")
    attempts = store.list_attempts(proof["work_item_id"])
    assert [attempt["route_id"] for attempt in attempts] == ["primary-route", "backup-route"]
    contexts = [store.get_external_context_use(attempt["attempt_id"])["intent"] for attempt in attempts]
    assert contexts[0]["context_sha256"] == contexts[1]["context_sha256"]
    before = store.get_quick_scan_budget_status("quick-scan-test-policy")
    assert before["requests"] == 3 and before["spent_micros"] == 23000
    assert before["reserved_micros"] == 0
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0 and models.post.call_count == 0 and search.request.call_count == 1
    assert json.loads(output.read_text("utf-8"))["execution_receipts"]["IQS_05"] == receipt
    assert store.get_quick_scan_budget_status("quick-scan-test-policy") == before


@pytest.mark.parametrize("mutation", ["missing_use", "corrupt_use"])
def test_public_external_main_corrupt_saved_evidence_never_reasks_or_overwrites_answer(tmp_path, monkeypatch, mutation):
    kwargs, search, _ = _inputs(tmp_path, monkeypatch)
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0 and models.post.call_count == 1
    original_output = output.read_bytes()
    receipt = json.loads(original_output)["execution_receipts"]["IQS_05"]
    proof = receipt["search_binding"]["external_context_use"]
    store = QuickScanWorkStore(tmp_path / "quick_scan_work.sqlite")
    before = store.get_quick_scan_budget_status("quick-scan-test-policy")
    # Deliberately corrupt only this disposable SQLite fixture behind its
    # immutable triggers, as a damaged-restore test; never production data.
    with closing(store._connect()) as connection, connection:
        if mutation == "missing_use":
            connection.execute("DROP TRIGGER quick_scan_external_use_no_delete")
            connection.execute("DELETE FROM quick_scan_external_use_intent WHERE attempt_id=?", (proof["work_attempt_id"],))
        else:
            connection.execute("DROP TRIGGER quick_scan_external_use_no_update")
            connection.execute("UPDATE quick_scan_external_use_intent SET metadata_sha256=? WHERE attempt_id=?", ("e" * 64, proof["work_attempt_id"]))
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code != 0
    assert models.post.call_count == 0 and search.request.call_count == 1
    assert output.read_bytes() == original_output
    assert store.get_quick_scan_budget_status("quick-scan-test-policy") == before


def test_public_external_main_deepseek_text_endpoint_keeps_thinking_out_of_output_and_restores(tmp_path, monkeypatch):
    kwargs, search, _ = _inputs(tmp_path, monkeypatch)
    kwargs["model_policy"]["models"][0].update(provider_config_ref="deepseek", model="deepseek-flash")
    kwargs.update(provider_name="deepseek", provider_configs={"deepseek": {
        "enabled": True, "api_key": "synthetic-only", "model": "deepseek-flash",
        "base_url": "https://api.deepseek.com/responses", "max_retries": 1}})
    response = kwargs["responses"][0]
    response.json.return_value["model"] = "deepseek-flash"
    response.json.return_value["output"].insert(0, {"type": "reasoning", "content": [
        {"type": "reasoning_text", "text": "synthetic-thinking-MUST-NOT-LEAK"}]})
    response.content = json.dumps(response.json.return_value).encode()
    response.text = response.content.decode()
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0 and models.post.call_count == 1 and search.request.call_count == 1
    assert models.post.call_args.args[0] == "https://api.deepseek.com/responses"
    payload = models.post.call_args.kwargs["json"]
    assert payload["reasoning"] == {"effort": "high"}
    assert not ({"tools", "tool_choice", "include"} & set(payload))
    first = json.loads(output.read_text("utf-8"))
    receipt = first["execution_receipts"]["IQS_05"]
    assert first["provider"]["name"] == receipt["provider"] == "deepseek"
    assert receipt["actual_model"] == receipt["requested_model"] == "deepseek-flash"
    assert receipt["search_binding"]["native_receipt"]["search_status"] == "unverified"
    assert receipt["search_status"] == "executed" and receipt["web_search_calls"] == []
    assert "synthetic-thinking-MUST-NOT-LEAK" not in output.read_text("utf-8")
    proof = receipt["search_binding"]["external_context_use"]
    store = QuickScanWorkStore(tmp_path / "quick_scan_work.sqlite")
    checkpoint = store.get_answer_checkpoint(proof["work_item_id"])
    assert checkpoint["payload"]["provenance"]["actual_provider"] == "deepseek"
    assert "synthetic-thinking-MUST-NOT-LEAK".encode() not in store.path.read_bytes()
    before = store.get_quick_scan_budget_status("quick-scan-test-policy")
    code, output, models = _invoke(monkeypatch, tmp_path, **kwargs)
    assert code == 0 and models.post.call_count == 0 and search.request.call_count == 1
    assert json.loads(output.read_text("utf-8"))["execution_receipts"]["IQS_05"] == receipt
    assert store.get_quick_scan_budget_status("quick-scan-test-policy") == before
