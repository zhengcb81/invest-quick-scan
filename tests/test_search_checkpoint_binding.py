"""Offline binding tests between receipts, task exposure and checkpoint."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "search_checkpoint_binding", ROOT / "scripts/search_checkpoint_binding.py"
)
binding = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(binding)

SPEC2 = importlib.util.spec_from_file_location("search_receipt", ROOT / "scripts/search_receipt.py")
receipts = importlib.util.module_from_spec(SPEC2)
SPEC2.loader.exec_module(receipts)


def exposure():
    return {
        "protocol": "iqs.search_exposure/1.0.0",
        "consumer_id": "invest-quick-scan",
        "search_policy_ref": "policy.json",
        "search_policy_sha256": "a" * 64,
        "max_search_queries_per_session": 2,
        "max_search_cost_micros": 10000,
        "currency": "CNY",
        "routes": [{"route_id": "deepseek-primary", "provider": "deepseek",
                    "credential_env": "DEEPSEEK_API_KEY", "enabled": True, "max_queries": 2}],
        "storage_rights": {"confirmed": True, "entitlement_ref": "owner-terms"},
        "approved_by": "owner",
        "approved_at": "2026-10-18T12:00:00Z",
    }


def receipt(cost=5000):
    return {
        "protocol": "iqs.search_receipt/1.0.0",
        "exposure_sha256": receipts.canonical_sha256(exposure()),
        "policy_sha256": exposure()["search_policy_sha256"],
        "provider": "deepseek",
        "route_id": "deepseek-primary",
        "query": "q",
        "requested_at": "2026-10-18T12:00:00Z",
        "completed_at": "2026-10-18T12:00:01Z",
        "status": "ok",
        "results": [{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1.0}],
        "result_count": 1,
        "cost_micros": cost,
        "currency": "CNY",
        "response_sha256": "c" * 64,
    }


def test_bind_one_receipt():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [receipt()])
    assert result["status"] == "bound", result
    assert result["receipt_count"] == 1
    assert result["total_cost_micros"] == 5000


def test_count_over_limit_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [receipt(), receipt(), receipt()])
    assert result["status"] == "rejected"
    assert "receipt_count_exceeds_exposure" in result["errors"]


def test_cost_over_limit_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [receipt(20000)])
    assert result["status"] == "rejected"


def test_checkpoint_hash_mismatch_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [receipt()], checkpoint={"search_receipts_sha256": "0" * 64})
    assert result["status"] == "rejected"
    assert "checkpoint_receipts_hash_mismatch" in result["errors"]


def test_missing_exposure_rejected():
    result = binding.bind({"execution_profile": {}}, [receipt()])
    assert result["status"] == "rejected"
    assert "task_search_exposure_missing" in result["errors"]


def test_empty_receipts_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [])
    assert result["status"] == "rejected"
    assert "receipts_required" in result["errors"]


def test_all_unavailable_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    row = receipt()
    row["status"] = "unavailable"
    row["results"] = []
    row["result_count"] = 0
    row["cost_micros"] = 0
    row["error_reason"] = "http_503"
    result = binding.bind(profile, [row])
    assert result["status"] == "rejected"
    assert "receipts_without_ok_result" in result["errors"]


def test_checkpoint_without_hash_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    result = binding.bind(profile, [receipt()], checkpoint={})
    assert result["status"] == "rejected"
    assert "checkpoint_receipts_sha256_required" in result["errors"]


def test_duplicate_receipts_rejected():
    profile = {"execution_profile": {"search_exposure": exposure()}}
    row = receipt()
    result = binding.bind(profile, [row, row])
    assert result["status"] == "rejected"
    assert "duplicate_receipts" in result["errors"]
