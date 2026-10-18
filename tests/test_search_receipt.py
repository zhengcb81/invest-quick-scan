"""Offline search receipt tests bound to an owner search exposure."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("search_receipt", ROOT / "scripts/search_receipt.py")
receipt_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(receipt_module)


def exposure():
    return {
        "protocol": "iqs.search_exposure/1.0.0",
        "consumer_id": "invest-quick-scan",
        "search_policy_ref": "policy.json",
        "search_policy_sha256": "a" * 64,
        "max_search_queries_per_session": 2,
        "max_search_cost_micros": 10000,
        "currency": "CNY",
        "routes": [
            {"route_id": "deepseek-primary", "provider": "deepseek",
             "credential_env": "DEEPSEEK_API_KEY", "enabled": True, "max_queries": 2}
        ],
        "storage_rights": {"confirmed": True, "entitlement_ref": "owner-terms"},
        "approved_by": "owner",
        "approved_at": "2026-10-18T12:00:00Z",
    }


def response(results):
    return json.dumps({"results": results}, ensure_ascii=False).encode("utf-8")


def build(raw, **kw):
    return receipt_module.from_response(
        raw,
        exposure=exposure(),
        policy_sha256=exposure()["search_policy_sha256"],
        provider="deepseek",
        route_id="deepseek-primary",
        query="宁德时代 2025 年报 营收",
        requested_at="2026-10-18T12:00:00Z",
        completed_at="2026-10-18T12:00:02Z",
        cost_micros=kw.pop("cost_micros", 5000),
        **kw,
    )


def test_receipt_from_deepseek_response():
    raw = response([
        {"title": "CATL annual report", "url": "https://example.com/a",
         "snippet": "snippet", "summary": "summary", "rerank_score": 1.7},
        {"title": "CATL filing", "url": "https://example.com/b",
         "snippet": "snippet", "rerank_score": 0.9},
    ])
    receipt = build(raw)
    assert receipt["status"] == "ok"
    assert receipt["result_count"] == 2
    assert receipt["exposure_sha256"] == receipt_module.canonical_sha256(exposure())
    assert receipt["results"][1]["rerank_score"] == 0.9
    assert receipt["response_sha256"] == receipt_module.hashlib.sha256(raw).hexdigest()


def test_empty_results_status_empty():
    receipt = build(response([]))
    assert receipt["status"] == "empty"
    assert receipt["result_count"] == 0


def test_cost_above_exposure_rejected():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}])
    try:
        build(raw, cost_micros=20000)
    except ValueError as error:
        assert "cost_exceeds_exposure" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_route_not_in_exposure_rejected():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}])
    try:
        receipt_module.from_response(
            raw, exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"], provider="brave",
            route_id="brave-primary", query="q",
            requested_at="2026-10-18T12:00:00Z", completed_at="2026-10-18T12:00:01Z",
            cost_micros=1000,
        )
    except ValueError as error:
        assert "route_not_in_exposure" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_result_count_mismatch_rejected():
    receipt = build(response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}]))
    receipt["result_count"] = 0
    try:
        receipt_module.validate(receipt)
    except Exception as error:
        assert "result_count" in str(error) or "minimum" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_ok_receipt_requires_positive_cost():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}])
    try:
        build(raw, cost_micros=0)
    except ValueError as error:
        assert "cost_required" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_policy_hash_must_match_exposure():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}])
    try:
        receipt_module.from_response(
            raw, exposure=exposure(), policy_sha256="c" * 64, provider="deepseek",
            route_id="deepseek-primary", query="q",
            requested_at="2026-10-18T12:00:00Z", completed_at="2026-10-18T12:00:01Z",
            cost_micros=5000,
        )
    except ValueError as error:
        assert "policy_mismatch" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_raw_dict_rejected():
    try:
        build({"results": []})
    except ValueError as error:
        assert "must_be_bytes_or_text" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_non_numeric_rerank_rejected():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": None}])
    try:
        build(raw)
    except ValueError as error:
        assert "rerank_score_invalid" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_time_order_enforced():
    raw = response([{"title": "t", "url": "https://example.com", "snippet": "", "rerank_score": 1}])
    try:
        receipt_module.from_response(
            raw, exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
            provider="deepseek", route_id="deepseek-primary", query="q",
            requested_at="2026-10-18T12:00:05Z", completed_at="2026-10-18T12:00:01Z",
            cost_micros=5000,
        )
    except ValueError as error:
        assert "time_order" in str(error)
    else:
        raise AssertionError("expected rejection")
