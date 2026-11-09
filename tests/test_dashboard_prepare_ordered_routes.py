"""Dashboard ordered routes use only explicit owner configuration, offline."""
from __future__ import annotations

import copy
import json
import sys

import pytest

from scripts import dashboard_prepare as prepare


TARGETS = [
    {"provider": "provider-first", "model": "model-first", "route_id": "route-first",
     "provider_config_ref": "account-first", "quota_group": "quota-first"},
    {"provider": "provider-next", "model": "model-next", "route_id": "route-next",
     "provider_config_ref": "account-next", "quota_group": "quota-next"},
]


def policy(dialect="1.6.0"):
    value = {"protocol": "stockwiki.refresh_owner_policy/" + dialect,
             "provider": TARGETS[0]["provider"], "model": TARGETS[0]["model"],
             "qa": {"policy_id": "original-policy", "route_id": TARGETS[0]["route_id"],
                    "provider_config_ref": TARGETS[0]["provider_config_ref"]}}
    if dialect == "1.6.0":
        value["ordered_route_targets"] = copy.deepcopy(TARGETS)
    return value


def gateway(tmp_path, owner_policy):
    workspace = tmp_path / "owner"
    (workspace / "config").mkdir(parents=True)
    prepare._new(workspace / "config/quick_scan_refresh.json", owner_policy)
    code_root = tmp_path / "stockwiki-code"
    package = code_root / "stockwiki"
    package.mkdir(parents=True)
    (package / "quick_scan_prepare_cli.py").write_text('''
import hashlib, json, sys
from pathlib import Path
request = json.load(sys.stdin)
assert request == {'protocol': 'stockwiki.quick_scan_prepare_request/1.0.0', 'operation': 'policy', 'payload': {}}
path = Path(sys.argv[sys.argv.index('--root') + 1]) / 'config/quick_scan_refresh.json'
raw = path.read_bytes()
print(json.dumps({'protocol': 'stockwiki.quick_scan_prepare_reply/1.0.0', 'operation': 'policy', 'result': {
    'policy': json.loads(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'path': str(path)}}))
''', encoding="utf8")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    prepare._new(runtime / "llm_apis.json", {"synthetic": "no credentials"})
    qa = tmp_path / "qa"
    qa.mkdir()
    (qa / "main_with_llm.py").write_text("# never executed", encoding="utf8")
    for name in ("admission.json", "spend.json"):
        prepare._new(tmp_path / name, {})
    config = {"workspace_root": str(workspace), "stockwiki_root": str(code_root),
              "iqs_root": str(tmp_path), "stockwiki_python": sys.executable, "stockqa_root": str(qa),
              "prepare": {"admission_config": str(tmp_path / "admission.json"),
                          "runtime_dir": str(runtime), "spend_authorization": str(tmp_path / "spend.json"),
                          "producer": {"component_version": "test", "build_id": "offline"},
                          "authorization_reference": "synthetic-test-only",
                          "agent": {"profile_id": "test", "profile_sha256": "a" * 64, "harness_ref": "pytest"}}}
    return prepare.PrepareGateway(config)


def scope_inputs(tmp_path, monkeypatch, owner_policy):
    """Run real file/transport construction, replace only external owner calls."""
    directory = tmp_path / "scope"
    directory.mkdir()
    owner_config = tmp_path / "owner-config"
    owner_config.mkdir()
    captures = []

    def owner_prepare(config, operation, payload, *, iqs_release_root):
        assert operation == "refresh_record" and payload == {"preview_id": "original-preview"}
        assert iqs_release_root == str(tmp_path / "release")
        return {"preview_id": "original-preview", "record_sha256": "a" * 64,
                "owner_state": {"quote": {"max_http_requests": 1}}}

    def native(config, owner, module, arguments, *, input_value=None):
        captures.append((owner, module, list(arguments)))
        if module == "stockwiki.quick_scan_query_v2_cli":
            return {"result": {"status": "available", "missing_subject_refs": [],
                               "watermark": {"snapshot_id": "original-snapshot"}}}
        if module == "stockwiki.quick_scan_refresh_owner_cli":
            if "--install-delegation-stdin" in arguments:
                assert input_value["workspace_root"] == str((tmp_path / "owner").resolve())
                assert input_value["preview_record_sha256"] == "a" * 64
                assert input_value["preview_id"] == "original-preview"
                return {"grant_id": "original-grant"}
            if "--confirm-delegated" in arguments:
                return {"confirmation_id": "original-confirmation"}
            return {"preview_id": "original-preview", "status": "ready"}
        assert module == "src.utils.quick_scan_refresh_admission_cli"
        return {"registered_with_executor": True}

    monkeypatch.setattr(prepare, "_native_cli", native)
    monkeypatch.setattr(prepare, "_owner_prepare", owner_prepare)
    monkeypatch.setattr(prepare, "_cached_scope_result", lambda *args, **kwargs: None)
    config = {"workspace_root": str(tmp_path / "owner"), "iqs_root": str(tmp_path / "iqs"),
              "prepare": {"admission_config": str(tmp_path / "admission.json"),
                          "authorization_reference": "synthetic-test-only", "agent": {},
                          "runtime_dir": str(tmp_path / "runtime"), "spend_authorization": str(tmp_path / "spend.json")}}
    ref = {"entity_id": "ENT_SYNTHETIC", "scope": "entity", "scope_id": "ENT_SYNTHETIC", "security_id": None}
    target = {key: str(tmp_path / f"{key}.json") for key in
              ("questions", "manifest", "identity_snapshot", "c06_authority", "owner_config")}
    args = (config, directory,
            {"preview_id": "local-preview", "bank": {"entity_id": ref["entity_id"], "company": "Synthetic fixture",
                                                        "information_cutoff": "2026-11-01"}},
            {}, [{"id": "Q_GENERIC", "metric_id": "M_GENERIC"}], target, ref,
            owner_policy, {"consumer_id": "invest-quick-scan"},
            {"iqs_release_root": str(tmp_path / "release")}, "run-synthetic")
    return args, captures, directory, owner_config


def test_explicit_ordered_policy_is_available_without_recovery_refs(tmp_path):
    product = gateway(tmp_path, policy())
    assert product._execution_gaps() == []
    assert prepare._recovery_subset(product.config, tmp_path, {}, {}, policy()) is None


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "primary", "qa-primary"])
def test_invalid_ordered_targets_are_a_preapply_configuration_gap(tmp_path, mutation):
    owner_policy = policy()
    if mutation == "missing":
        del owner_policy["ordered_route_targets"]
    elif mutation == "duplicate":
        owner_policy["ordered_route_targets"].append(copy.deepcopy(TARGETS[0]))
    elif mutation == "primary":
        owner_policy["model"] = "unapproved-primary"
    else:
        owner_policy["qa"]["route_id"] = "unapproved-route"
    assert "native_prepare_owner_policy_invalid" in gateway(tmp_path, owner_policy)._execution_gaps()


def test_ordered_scope_preserves_exact_sequence_in_inspection_and_broad_snapshot(tmp_path, monkeypatch):
    args, captures, directory, owner_config = scope_inputs(tmp_path, monkeypatch, policy())
    result = prepare._prepare_scope(*args)
    query = json.loads((directory / "query.json").read_text(encoding="utf8"))
    refresh = json.loads((directory / "refresh.json").read_text(encoding="utf8"))
    inspect = json.loads((directory / "inspection-request.json").read_text(encoding="utf8"))
    assert query["schema_version"] == "2.6.0"
    assert query["payload"]["model_filter"] is None
    assert refresh["source_query"]["payload"]["snapshot_id"] == "original-snapshot"
    assert refresh["protocol"] == "iqs.refresh_request/1.6.0"
    assert inspect["ordered_route_targets"] == TARGETS
    assert inspect["model"] == TARGETS[0]["model"]
    assert result["execution_bundle"]["inspection_schema_version"] == "1.6.0"
    assert len(captures) == 5
    assert not list(owner_config.iterdir())


def test_invalid_ordered_scope_stops_before_native_calls(tmp_path, monkeypatch):
    owner_policy = policy()
    owner_policy["ordered_route_targets"] = []
    args, captures, directory, _ = scope_inputs(tmp_path, monkeypatch, owner_policy)
    with pytest.raises(prepare.DashboardPrepareError, match="owner"):
        prepare._prepare_scope(*args)
    assert captures == [] and not list(directory.iterdir())


@pytest.mark.parametrize("dialect", ["1.0.0", "1.1.0", "1.2.0", "1.3.0"])
def test_old_scope_does_not_expand_to_ordered_models(tmp_path, monkeypatch, dialect):
    owner_policy = policy(dialect)
    # Even an accidental extra key in an older config cannot opt it into 1.6.
    owner_policy["ordered_route_targets"] = copy.deepcopy(TARGETS)
    args, _, directory, _ = scope_inputs(tmp_path, monkeypatch, owner_policy)
    result = prepare._prepare_scope(*args)
    inspect = json.loads((directory / "inspection-request.json").read_text(encoding="utf8"))
    query = json.loads((directory / "query.json").read_text(encoding="utf8"))
    assert "ordered_route_targets" not in inspect
    assert inspect["model"] == TARGETS[0]["model"]
    assert query["schema_version"] == ("2.0.0" if dialect == "1.0.0" else "2.6.0")
    assert result["execution_bundle"]["inspection_schema_version"] == dialect


@pytest.mark.parametrize("dialect", ["1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0"])
def test_recovery_refs_remain_explicit_and_old_unsupported_dialects_stay_unsupported(tmp_path, dialect):
    product = gateway(tmp_path, policy(dialect))
    if dialect in {"1.2.0", "1.3.0"}:
        assert "recovery_policy_refs_required" in product._execution_gaps()
    elif dialect in {"1.4.0", "1.5.0"}:
        assert "native_prepare_owner_dialect_not_supported" in product._execution_gaps()
    else:
        product.config["prepare"]["recovery_work_decision_refs"] = [
            {"work_item_id": "WORK_" + "a" * 32, "decision_id": "owd1_" + "b" * 64}]
        assert "recovery_policy_refs_required" in product._execution_gaps()
        with pytest.raises(prepare.DashboardPrepareError, match="controlled policy"):
            prepare._recovery_subset(product.config, tmp_path, {}, {}, policy(dialect))
