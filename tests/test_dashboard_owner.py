"""Dashboard/real owner subprocess boundary; every writable path is temporary.

StockWiki's existing storage-boundary fixtures seed synthetic answers through
its public APIs. These are engineering tests, not financial-accuracy goldens.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.dashboard_owner import DashboardOwnerError, OwnerGateway, _env, _original_error

ROOT = Path(__file__).resolve().parents[1]
STOCKWIKI = ROOT.parent / "StockWiki"
ENTITY = "ENT_11111111-1111-4111-8111-111111111111"
SECOND = "ENT_22222222-2222-4222-8222-222222222222"


def _tree(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


@pytest.fixture()
def owner(tmp_path):
    if not (STOCKWIKI / "stockwiki" / "quick_scan_store.py").is_file():
        pytest.skip("Explicit integration dependency: sibling StockWiki owner source")
    workspace = tmp_path / "owner"
    bundle = tmp_path / "registered"
    bundle.mkdir()
    script = r'''
import json, sys
from pathlib import Path
sys.path[:0]=[sys.argv[1], str(Path(sys.argv[1])/'tests')]
from test_quick_scan_profiles import _workspace, _release, E01
from test_quick_scan_observations import _observation, _package
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.quick_scan_import import import_package
from stockwiki.quick_scan_observations import QuickScanObservationStore
paths=_workspace(Path(sys.argv[2]))
identity=QuickScanStore(paths)
identity.create_universe('TEST','Isolated dashboard test universe')
package=_package([_observation('dashboard-import-score',entity_id=E01,request_id='DASHBOARD_REQ',attempt_id='DASHBOARD_ATT')])
target=Path(sys.argv[3]);(target/'package.json').write_text(json.dumps(package),encoding='utf-8')
(target/'release.json').write_text(json.dumps(_release()),encoding='utf-8')
facts=_package([_observation('dashboard-original-fact',entity_id=E01,question_id='FACT_10',field_id='facts.customers',response_kind='fact',score=None,status='answered',request_id='DASH_FACT_REQ',attempt_id='DASH_FACT_ATT',answer_extra={'items':[{'name':'Synthetic customer','value':'Stored fact only'}]})])
result=import_package(QuickScanObservationStore(paths),facts,frozen_release=_release(),identity_store=identity)
assert result['summary']=={'accepted':1},result
'''
    result = subprocess.run([sys.executable, "-B", "-c", script, str(STOCKWIKI), str(workspace), str(bundle)],
                            capture_output=True, text=True, encoding="utf-8", timeout=40, env=_env())
    assert result.returncode == 0, result.stderr
    config = {"stockwiki_root": str(STOCKWIKI), "workspace_root": str(workspace),
              "stockwiki_python": sys.executable, "iqs_root": str(ROOT), "universe_id": "TEST", "scratch_root": str(tmp_path),
              "bundles": {"TEST_BUNDLE": {"package": str(bundle / "package.json"),
                                           "release": str(bundle / "release.json")}}}
    return OwnerGateway(config), workspace, bundle


def test_missing_deployment_and_database_are_honest_and_do_not_create(tmp_path):
    result = OwnerGateway({}).status()
    assert result["available"] is False
    assert result["error"]["code"] == "owner_not_configured"
    if not STOCKWIKI.is_dir():
        return
    config = {"stockwiki_root": str(STOCKWIKI), "workspace_root": str(tmp_path),
              "stockwiki_python": sys.executable, "iqs_root": str(ROOT)}
    result = OwnerGateway(config).status()
    assert result["error"]["code"] == "owner_database_missing"
    assert not (tmp_path / "data").exists()


def test_real_owner_reads_keep_original_model_versions_missingness_and_no_writes(owner):
    gateway, workspace, _ = owner
    before = _tree(workspace)
    assert gateway.status()["entity_count"] == 2
    result = gateway.search(limit=1)
    assert result["protocol"] == "stockwiki_w09_read_primitives"
    assert result["c06_envelope_validated"] is False
    assert result["total"] == 2 and len(result["rows"]) == 1
    assert gateway.search(limit=1, offset=1, snapshot=result["snapshot"])["rows"][0]["entity_id"] != result["rows"][0]["entity_id"]
    detail = gateway.entity(ENTITY)
    fields = [field for group in detail["groups"] for field in group["fields"]]
    stored = next(field for field in fields if field["question_id"] == "IQS_LEG")
    assert stored["model_resolved"] == "fixture-model"
    assert stored["versions"]["question_version"] == "1.0.0"
    assert stored["observed_at"] == "2026-10-01T09:01:00Z"
    assert detail["quality"]["quality_verified"] is False
    history = gateway.history(ENTITY)
    assert history["complete"] and history["count"] >= len(fields)
    assert history["observations"][0]["payload"]["execution"]["model_resolved"] == "fixture-model"
    facts = gateway.facts(ENTITY)
    assert facts["count"] == 1 and facts["relations_supported"] is False
    assert facts["observations"][0]["payload"]["answer"]["items"][0]["name"] == "Synthetic customer"
    assert gateway.universe_list()["member_count"] == 0
    assert gateway.delivery_status()["distinct_companies"] == 2
    assert _tree(workspace) == before


def test_unknown_entity_or_universe_is_named_not_empty(owner):
    gateway, _, _ = owner
    with pytest.raises(DashboardOwnerError) as error:
        gateway.entity("ENT_NOT_REGISTERED")
    assert error.value.code == "entity_not_found" and error.value.status == 404
    with pytest.raises(DashboardOwnerError) as error:
        gateway.universe_list("MISSING")
    assert error.value.code == "universe_not_found"


def test_name_preview_never_activates_and_id_required_for_apply(owner):
    gateway, workspace, _ = owner
    before = _tree(workspace)
    result = gateway.universe_preview({"query": "fixture", "reason": "test"})
    assert result["can_apply"] is False and result["identity_changed"] is False
    with pytest.raises(DashboardOwnerError):
        gateway.universe_apply({"query": "fixture", "reason": "test"})
    assert _tree(workspace) == before


def test_universe_original_add_remove_restore_and_stale_preview(owner):
    gateway, _, _ = owner
    request = {"action": "add", "entity_id": ENTITY, "reason": "User selected this existing issuer"}
    first = gateway.universe_preview(request)
    assert first["can_apply"] and first["member"] is None
    added = gateway.universe_apply({**request, "preview_token": first["preview_token"]})
    assert added["member"]["version"] == 1
    with pytest.raises(DashboardOwnerError) as error:
        gateway.universe_apply({**request, "preview_token": first["preview_token"]})
    assert error.value.code == "preview_stale"
    current = gateway.universe_preview(request)
    repeat = gateway.universe_apply({**request, "preview_token": current["preview_token"]})
    assert repeat["member"]["version"] == 1
    for action, version in (("remove", 2), ("restore", 3)):
        command = {**request, "action": action}
        preview = gateway.universe_preview(command)
        result = gateway.universe_apply({**command, "preview_token": preview["preview_token"]})
        assert result["member"]["version"] == version
    assert gateway.universe_list()["member_count"] == 1


def test_bundle_import_uses_original_ack_and_idempotent_replay(owner):
    gateway, workspace, _ = owner
    before = _tree(workspace)
    preview = gateway.import_preview({"bundle_id": "TEST_BUNDLE"})
    assert preview["can_apply"] and preview["item_count"] == 1
    assert _tree(workspace) == before
    result = gateway.import_apply({"bundle_id": "TEST_BUNDLE", "preview_token": preview["preview_token"]})
    receipt = result["receipt"]
    assert receipt["summary"] == {"accepted": 1}
    ack = gateway.delivery_status(receipt["package_id"])
    assert ack["count"] == 1 and ack["receipts"][0]["ack"] == receipt["acks"][0]
    snapshot = _tree(workspace)
    replay = gateway.import_apply({"bundle_id": "TEST_BUNDLE", "preview_token": preview["preview_token"]})
    assert replay["receipt"] == receipt
    assert _tree(workspace) == snapshot
    assert gateway.import_preview({"bundle_id": "TEST_BUNDLE"})["replay"] is True


def test_bundle_preview_token_binds_bytes_and_browser_paths_are_rejected(owner):
    gateway, workspace, bundle = owner
    initial = gateway.import_preview({"bundle_id": "TEST_BUNDLE"})
    package = bundle / "package.json"
    package.write_text(package.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    before = _tree(workspace)
    with pytest.raises(DashboardOwnerError) as error:
        gateway.import_apply({"bundle_id": "TEST_BUNDLE", "preview_token": initial["preview_token"]})
    assert error.value.code == "preview_stale"
    with pytest.raises(DashboardOwnerError) as error:
        gateway.import_preview({"bundle_id": "TEST_BUNDLE", "path": str(package)})
    assert error.value.code == "unknown_field"
    with pytest.raises(DashboardOwnerError) as error:
        gateway.import_preview({"bundle_id": "UNREGISTERED"})
    assert error.value.code == "bundle_not_registered"
    assert _tree(workspace) == before


def test_input_validation_and_secret_free_child(monkeypatch):
    gateway = OwnerGateway({})
    for options in ({"limit": True}, {"limit": 101}, {"offset": -1}, {"query": []}):
        with pytest.raises(DashboardOwnerError):
            gateway.search(**options)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret-never-a-real-key")
    monkeypatch.setenv("PYTHONPATH", "untrusted-extra-import-root")
    assert "DEEPSEEK_API_KEY" not in _env() and "PYTHONPATH" not in _env()
    with pytest.raises(DashboardOwnerError):
        gateway.entity("../../somewhere")


def test_owner_corrupt_database_is_unavailable_not_zero(owner):
    gateway, workspace, _ = owner
    database = workspace / "data" / "quick_scan" / "scan_observations.sqlite"
    database.write_bytes(b"Not a database: isolated corruption regression")
    result = gateway.status()
    assert result["available"] is False
    assert result["error"]["code"] in {"owner_store_unreadable", "observation_read_unavailable"}
    assert "entity_count" not in result


def test_original_busy_and_transport_timeout_remain_distinct(monkeypatch, tmp_path):
    import sqlite3
    assert _original_error(sqlite3.OperationalError("database is locked")).code == "owner_busy"
    assert _original_error(sqlite3.DatabaseError("file is not a database")).code == "owner_store_unreadable"
    gateway = OwnerGateway({})
    monkeypatch.setattr(gateway, "_deployment", lambda: {"stockwiki_python": sys.executable,
                                                       "stockwiki_root": str(tmp_path)})
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("isolated owner", 1)
    monkeypatch.setattr(subprocess, "run", timeout)
    assert gateway.status()["error"]["code"] == "owner_timeout"


def test_score_conditions_use_original_three_valued_owner_grammar(owner):
    gateway, workspace, _ = owner
    before = _tree(workspace)
    conditions = [{"field": "score.iqs_01", "op": ">=", "value": 8}]
    result = gateway.search(conditions=conditions, condition_combine="all")
    assert [row["entity_id"] for row in result["rows"]] == [ENTITY]
    assert result["condition_rules"]["outcome_counts"] == {"pass": 1, "fail": 0, "unknown": 1}
    coverage = gateway.coverage()
    assert coverage["by_field"]["score.iqs_01"]["entities"] == 2
    with pytest.raises(DashboardOwnerError) as error:
        gateway.search(conditions=[{"field": "score.iqs_01", "op": "~", "value": 8}])
    assert error.value.code == "condition_unknown_operator"
    with pytest.raises(DashboardOwnerError) as error:
        gateway.search(view="unrecognized_view")
    assert error.value.code == "view_invalid"
    assert _tree(workspace) == before
