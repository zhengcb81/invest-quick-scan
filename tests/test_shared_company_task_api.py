"""Synthetic contract tests for the IQS-to-owner task factory boundary."""
import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _owner_inputs():
    question = {"id": "Q1", "module_id": "base", "prompt": "Synthetic public API contract"}
    subject = {
        "entity_id": "ENT_TEST",
        "scope": "entity",
        "scope_id": "ENT_TEST",
        "primary_issuer_id": "ISS_TEST",
    }
    manifest = {
        "questions": [question],
        "module_locks": [{"module_id": "base", "version": "1.0.0"}],
    }
    identity = {
        "payload": {
            "entity_id": "ENT_TEST",
            "canonical_name": "Synthetic issuer",
            "listings": [{"market": "US", "ticker": "SYN"}],
        }
    }
    return SimpleNamespace(
        requested_question_ids=["Q1"],
        entries={"Q1": {"kind": "work"}},
        observation_context={
            "questions": {
                "Q1": {"subject_binding": {"question_contract": question, "subject_ref": subject}}
            }
        },
        bundle={"manifest": manifest},
        input_raw={
            "manifest.json": json.dumps(manifest).encode(),
            "identity.json": json.dumps(identity).encode(),
            "authority.json": b"{}",
            "owner-config.json": b"{}",
            "questions.json": b"[]",
        },
        plan={"information_cutoff": "2026-11-10", "provider": "synthetic", "model": "unit"},
        route_provider="synthetic",
        route_model="unit",
        route_id="route-test",
    )


def _install_owner_apis(monkeypatch, *, company_agent_protocol="iqs.company-agent-public-api/2.3.0"):
    events = []
    created = []
    task = SimpleNamespace(protocol="iqs.company-agent-task/3.0.0")
    limits = {"max_search_queries_per_session": 0, "max_model_requests_per_session": 1}

    def canonical_json(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def sha256_hex(value):
        if isinstance(value, bytes):
            payload = value
        elif isinstance(value, str):
            payload = value.encode()
        else:
            payload = canonical_json(value).encode()
        return hashlib.sha256(payload).hexdigest()

    def create_owner_task(raw, questions, company, board, profile, targets, *, owner_binding):
        events.append("create_owner_task")
        created.append((raw, questions, company, board, profile, targets, owner_binding))
        task.raw = raw
        return task

    company_api = ModuleType("iqs_company_agent_lab.api")
    company_api.PUBLIC_API_PROTOCOL = company_agent_protocol
    company_api.canonical_json = canonical_json
    company_api.sha256_hex = sha256_hex
    company_api.create_owner_task = create_owner_task
    company_api.build_scan_profile = lambda questions, **kwargs: {
        "resource_limits": dict(limits),
        "question_count": len(questions),
    }
    company_api.validate_scan_task = lambda value: events.append(("validate_scan_task", value))
    company_api.native_company_projection = lambda identity, subject: {
        "entity_id": identity["entity_id"],
        "subject_ref": subject,
    }
    company_api.scan_limits = lambda value, search_exposure=None: dict(limits)
    company_package = ModuleType("iqs_company_agent_lab")
    company_package.__path__ = []
    monkeypatch.setitem(sys.modules, "iqs_company_agent_lab", company_package)
    monkeypatch.setitem(sys.modules, "iqs_company_agent_lab.api", company_api)

    runtime_package = ModuleType("iqs_agent_runtime_lab")
    runtime_package.__path__ = []
    runtime_api = ModuleType("iqs_agent_runtime_lab.api")
    runtime_api.PUBLIC_API_PROTOCOL = "iqs.agent-runtime-public-api/1.4.0"
    monkeypatch.setitem(sys.modules, "iqs_agent_runtime_lab", runtime_package)
    monkeypatch.setitem(sys.modules, "iqs_agent_runtime_lab.api", runtime_api)

    stockqa_package = ModuleType("src")
    stockqa_package.__path__ = []
    utils_package = ModuleType("src.utils")
    utils_package.__path__ = []
    stockqa_api = ModuleType("src.utils.quick_scan_company_api")
    stockqa_api.PUBLIC_API_PROTOCOL = "stockqa.company-scan-public-api/1.5.0"
    owner = _owner_inputs()
    stockqa_api.company_scan_inputs = lambda lifecycle: owner
    stockqa_api.company_scan_pack_group_key = lambda lifecycle, qid, prompt: "base"
    stockqa_api.validate_company_scan_task = lambda lifecycle, value: events.append(
        ("validate_company_scan_task", value)
    )
    monkeypatch.setitem(sys.modules, "src", stockqa_package)
    monkeypatch.setitem(sys.modules, "src.utils", utils_package)
    monkeypatch.setitem(sys.modules, "src.utils.quick_scan_company_api", stockqa_api)

    return events, created, task


def _task_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("shared_company_task")


def test_company_task_factory_checks_versions_then_uses_public_owner_factories(monkeypatch):
    events, created, expected_task = _install_owner_apis(monkeypatch)
    task_module = _task_module(monkeypatch)
    import shared_company_ports

    current = shared_company_ports.current_owner_api_protocols

    def audited_current_protocols():
        events.append("owner_api_preflight")
        return current()

    monkeypatch.setattr(shared_company_ports, "current_owner_api_protocols", audited_current_protocols)
    result = task_module.create_company_scan_task(
        object(), experiment_id="synthetic", run_id="run-1"
    )

    assert result is expected_task
    assert result.raw["protocol"] == "iqs.company-scan-task/1.0.0"
    assert created and created[0][0]["question_refs"][0]["question_id"] == "Q1"
    assert events[0] == "owner_api_preflight"
    assert any(isinstance(event, tuple) and event[0] == "validate_scan_task" for event in events)
    assert any(
        isinstance(event, tuple) and event == ("validate_company_scan_task", expected_task)
        for event in events
    )


def test_company_task_factory_rejects_provider_version_before_building_task(monkeypatch):
    events, created, _ = _install_owner_apis(
        monkeypatch, company_agent_protocol="iqs.company-agent-public-api/2.2.0"
    )
    task_module = _task_module(monkeypatch)
    from shared_company_ports import OwnerApiProtocolError

    with pytest.raises(OwnerApiProtocolError, match="company_scan_owner_api_version_unsupported"):
        task_module.create_company_scan_task(
            object(), experiment_id="synthetic", run_id="run-1"
        )

    assert created == []
    assert events == []
