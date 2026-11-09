"""Preparation must work against a deployed owner command without owner source APIs."""

import ast
import sys
from pathlib import Path

import pytest

from scripts import contract_validation, dashboard_prepare


def test_snapshot_uses_the_public_owner_command(tmp_path, monkeypatch):
    code = tmp_path / "owner-code"
    package = code / "stockwiki"
    package.mkdir(parents=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (package / "quick_scan_prepare_cli.py").write_text(
        """
import json, sys
request = json.load(sys.stdin)
assert request['protocol'] == 'stockwiki.quick_scan_prepare_request/1.0.0'
assert request['operation'] == 'snapshot'
assert request['payload']['entity_id'] == 'ENT_EXACT'
assert sys.argv[sys.argv.index('--root') + 1]
listing = {'entity_id': 'ENT_EXACT', 'security_id': 'SEC_EXACT', 'listing_id': 'LISTING_EXACT'}
identity = {'payload': {'entity_id': 'ENT_EXACT', 'listings': [listing]}, 'trusted_context': {
    'identity_receipts': {}, 'source_bindings': {}, 'market_registry': {}}}
data = {'identity': identity, 'selection': {'subject_gap': 'subject_authority_missing',
    'subjects': [], 'binding': None, 'anchor': None, 'bootstrap': None, 'scope_as_of': None,
    'owner_snapshot_as_of': request['payload']['owner_snapshot_as_of'],
    'selected_listing': listing, 'listing_binding': None}}
print(json.dumps({'protocol': 'stockwiki.quick_scan_prepare_reply/1.0.0',
    'operation': 'snapshot', 'result': data}))
""",
        encoding="utf-8",
    )
    seen = []
    monkeypatch.setattr(contract_validation, "validate_entity", lambda entity, **_: seen.append(entity))
    config = {"stockwiki_root": str(code), "stockwiki_python": sys.executable,
              "workspace_root": str(workspace), "iqs_root": str(tmp_path)}
    result = dashboard_prepare._snapshot(config, {"entity_id": "ENT_EXACT",
        "owner_snapshot_as_of": "2026-11-09T07:00:00Z"})
    assert result["identity"]["payload"]["entity_id"] == "ENT_EXACT"
    assert result["subject_gap"] == "subject_authority_missing"
    assert seen == [result["identity"]["payload"]]
    assert list(workspace.iterdir()) == []


def test_prepare_does_not_import_or_insert_stockwiki_implementation():
    tree = ast.parse(Path(dashboard_prepare.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("stockwiki"), node.lineno
        if isinstance(node, ast.Import):
            assert not any(alias.name.startswith("stockwiki") for alias in node.names), node.lineno
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and ast.unparse(node.func) == "sys.path.insert"):
            assert "stockwiki_root" not in ast.unparse(node), node.lineno


def test_status_does_not_advertise_preview_when_owner_has_no_public_command(tmp_path):
    config = {"stockwiki_root":str(tmp_path), "workspace_root":str(tmp_path), "iqs_root":str(tmp_path),
              "stockwiki_python":sys.executable}
    status = dashboard_prepare.PrepareGateway(config).status()
    assert status["available"] is False and status["bank_preview_available"] is False
    assert status["API_requests"] == 0 and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("same_bank", [False, True])
def test_cache_plan_refusal_applies_only_to_the_same_frozen_bank(monkeypatch, same_bank):
    error = {"code": "query_store_unavailable", "message": "No source snapshot", "status": 409, "details": {}}
    snapshot = {"manifest_raw": "{}", "route_raw": "{}", "manifest_raw_sha256": "a" * 64}
    monkeypatch.setattr(dashboard_prepare, "_owner_prepare", lambda *args, **kwargs: {
        "snapshot": snapshot, "plan_error": error})

    def compare(*_):
        if not same_bank:
            raise dashboard_prepare.DashboardPrepareError("existing_work_bank_changed", "Another frozen bank", 409)

    monkeypatch.setattr(dashboard_prepare, "_equivalent_frozen_bank", compare)
    payload = {"native": {"binding": {"entity_id": "ENT_EXACT"}}, "manifest": {"questions": []},
               "route": {}, "question_ids": []}
    if not same_bank:
        assert dashboard_prepare._cache_preview({}, payload) is None
    else:
        with pytest.raises(dashboard_prepare.DashboardPrepareError) as failure:
            dashboard_prepare._cache_preview({}, payload)
        assert failure.value.code == "query_store_unavailable"


@pytest.mark.parametrize("change", [None, "security_id", "listing_id", "primary_issuer_id", "unknown_question"])
def test_cache_returns_only_exact_native_subject_reference(monkeypatch, change):
    binding = {"entity_id": "ENT_A", "analysis_subject_id": "ASJ_A", "analysis_subject_revision": 1,
               "subject_key": "ASJ_A@1", "identity_revision": 1, "perimeter_sha256": "a" * 64}
    ref = {**{key: binding[key] for key in ("entity_id", "analysis_subject_id", "analysis_subject_revision", "perimeter_sha256")},
           "primary_issuer_id": "ENT_A", "security_id": "SEC_A", "listing_id": "LIST_A",
           "segment_id": None, "scope": "security", "scope_id": "SEC_A"}
    if change in {"security_id", "listing_id", "primary_issuer_id"}:
        ref[change] = "FOREIGN"
    plan = {"snapshot": {"manifest_raw": "{}", "route_raw": "{}", "manifest_raw_sha256": "a" * 64},
            "rows": [{"question_id": "Q1", "subject_ref": ref,
                      "field": {"field_id": "Q1", "decision": "reuse", "reuse_observation_id": "obs_a"}}],
            "work_store": "ledger.sqlite"}
    monkeypatch.setattr(dashboard_prepare, "_owner_prepare", lambda *args, **kwargs: plan)
    monkeypatch.setattr(dashboard_prepare, "_equivalent_frozen_bank", lambda *_: None)
    calls = []
    monkeypatch.setattr(dashboard_prepare, "_read_continuation_bank", lambda *args, **kwargs: calls.append(args[1]) or [])
    payload = {"native": {"binding": binding, "selected_listing": {"security_id": "SEC_A", "listing_id": "LIST_A"}},
               "manifest": {"questions": [{"id": "Q1", "scope": "security"}]},
               "route": {"as_of": "2026-11-09"}, "question_ids": ["Q1"]}
    if change == "unknown_question":
        payload["question_ids"].append("UNKNOWN")
    if change is None:
        result = dashboard_prepare._cache_preview({}, payload)
        assert result["cached_scopes"][0]["subject_ref"] == ref and result["cached_question_count"] == 1
        assert calls[0]["scope_bindings"] == {"Q1": {"scope": "security", "scope_id": "SEC_A"}}
    else:
        with pytest.raises(dashboard_prepare.DashboardPrepareError) as failure:
            dashboard_prepare._cache_preview({}, payload)
        assert failure.value.code == ("question_subset_invalid" if change == "unknown_question" else "native_response_invalid")
        assert calls == []
