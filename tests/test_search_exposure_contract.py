"""Offline contract tests for owner-approved bounded search exposure."""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "search_exposure_contract", ROOT / "scripts/search_exposure_contract.py"
)
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def document(tmp_path, **overrides):
    policy = tmp_path / "search-policy.json"
    policy.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")
    value = {
        "protocol": "iqs.search_exposure/1.0.0",
        "consumer_id": "invest-quick-scan",
        "search_policy_ref": "search-policy.json",
        "search_policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
        "max_search_queries_per_session": 2,
        "max_search_cost_micros": 50000,
        "routes": [
            {"route_id": "brave-primary", "provider": "brave", "credential_env": "BRAVE_API_KEY",
             "enabled": True, "max_queries": 1},
            {"route_id": "tavily-primary", "provider": "tavily", "credential_env": "TAVILY_API_KEY",
             "enabled": True, "max_queries": 1},
        ],
        "storage_rights": {"confirmed": True, "entitlement_ref": "owner-terms-2026-10-18"},
        "approved_by": "owner",
        "approved_at": "2026-10-18T12:00:00Z",
    }
    value.update(overrides)
    return value


def test_valid_search_exposure(tmp_path):
    env = {"BRAVE_API_KEY": "x", "TAVILY_API_KEY": "y"}
    result = contract.validate(document(tmp_path), base_dir=tmp_path, environ=env)
    assert result["status"] == "valid", result
    assert result["enabled_routes"] == ["brave-primary", "tavily-primary"]
    assert result["credential_presence"] == {"BRAVE_API_KEY": True, "TAVILY_API_KEY": True}


def test_policy_hash_mismatch_rejected(tmp_path):
    env = {"BRAVE_API_KEY": "x", "TAVILY_API_KEY": "y"}
    result = contract.validate(
        document(tmp_path, search_policy_sha256="0" * 64), base_dir=tmp_path, environ=env
    )
    assert result["status"] == "rejected"
    assert "search_policy_sha256_mismatch" in result["errors"]


def test_missing_credential_env_rejected(tmp_path):
    result = contract.validate(document(tmp_path), base_dir=tmp_path, environ={})
    assert result["status"] == "rejected"
    assert "credential_env_absent:BRAVE_API_KEY" in result["errors"]


def test_storage_rights_must_be_confirmed(tmp_path):
    env = {"BRAVE_API_KEY": "x", "TAVILY_API_KEY": "y"}
    doc = document(tmp_path, storage_rights={"confirmed": False, "entitlement_ref": "x"})
    result = contract.validate(doc, base_dir=tmp_path, environ=env)
    assert result["status"] == "rejected"


def test_zero_queries_rejected(tmp_path):
    env = {"BRAVE_API_KEY": "x", "TAVILY_API_KEY": "y"}
    result = contract.validate(
        document(tmp_path, max_search_queries_per_session=0), base_dir=tmp_path, environ=env
    )
    assert result["status"] == "rejected"


def test_route_budget_must_cover_session_cap(tmp_path):
    env = {"BRAVE_API_KEY": "x", "TAVILY_API_KEY": "y"}
    result = contract.validate(
        document(tmp_path, max_search_queries_per_session=5), base_dir=tmp_path, environ=env
    )
    assert result["status"] == "rejected"
    assert "route_query_budget_below_session_cap" in result["errors"]
