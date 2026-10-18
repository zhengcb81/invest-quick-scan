"""Offline binding tests: exposure document <-> owner policy cell."""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT / "scripts")
import sys

sys.path.insert(0, sys_path)
SPEC = importlib.util.spec_from_file_location(
    "search_exposure_binding", ROOT / "scripts/search_exposure_binding.py"
)
binding = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(binding)


def exposure(tmp_path, **overrides):
    policy = tmp_path / "search-policy.json"
    policy.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")
    value = {
        "protocol": "iqs.search_exposure/1.0.0",
        "consumer_id": "invest-quick-scan",
        "search_policy_ref": "search-policy.json",
        "search_policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
        "max_search_queries_per_session": 2,
        "max_search_cost_micros": 50000,
        "currency": "USD",
        "routes": [
            {"route_id": "brave-primary", "provider": "brave", "credential_env": "BRAVE_API_KEY",
             "enabled": True, "max_queries": 2},
        ],
        "storage_rights": {"confirmed": True, "entitlement_ref": "owner-terms"},
        "approved_by": "owner",
        "approved_at": "2026-10-18T12:00:00Z",
    }
    value.update(overrides)
    return value


def policy(tmp_path, document_sha256, consumer="invest-quick-scan"):
    return {
        "policy_id": "POLICY_TEST",
        "allowed_consumer_ids": [consumer],
        "budget_exposure_acceptance": {
            "control": {
                "cells": [
                    {
                        "cell_id": "CELL1",
                        "controls": {"search_policy_sha256": document_sha256},
                    }
                ]
            }
        },
    }


def test_binding_matches_cell(tmp_path):
    env = {"BRAVE_API_KEY": "x"}
    doc = exposure(tmp_path)
    result = binding.bind(policy(tmp_path, binding.canonical_sha256(doc)), doc,
                          base_dir=tmp_path, environ=env)
    assert result["status"] == "bound", result
    assert result["matched_cells"] == ["CELL1"]
    assert result["exposure_sha256"] == binding.canonical_sha256(doc)


def test_binding_rejects_hash_mismatch(tmp_path):
    env = {"BRAVE_API_KEY": "x"}
    doc = exposure(tmp_path)
    result = binding.bind(policy(tmp_path, "0" * 64), doc, base_dir=tmp_path, environ=env)
    assert result["status"] == "rejected"
    assert "cell_search_exposure_binding_missing" in result["errors"]


def test_binding_rejects_invalid_exposure(tmp_path):
    env = {}
    doc = exposure(tmp_path)
    result = binding.bind(policy(tmp_path, binding.canonical_sha256(doc)), doc,
                          base_dir=tmp_path, environ=env)
    assert result["status"] == "rejected"
    assert any(error.startswith("credential_env_absent") for error in result["errors"])


def test_binding_rejects_consumer_not_allowed(tmp_path):
    env = {"BRAVE_API_KEY": "x"}
    doc = exposure(tmp_path)
    result = binding.bind(policy(tmp_path, binding.canonical_sha256(doc), consumer="other"),
                          doc, base_dir=tmp_path, environ=env)
    assert result["status"] == "rejected"
    assert "consumer_not_allowed_by_owner_policy" in result["errors"]
