"""Offline DeepSeek Search client tests; transport is injected."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "deepseek_search_client", ROOT / "scripts/deepseek_search_client.py"
)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


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


def transport_for(body, status=200, seen=None):
    def transport(endpoint, payload, headers, timeout):
        if seen is not None:
            seen.update(endpoint=endpoint, payload=payload, headers=headers)
        return status, body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    return transport


def test_ok_receipt_and_payload():
    seen = {}
    body = {"results": [
        {"title": "t", "url": "https://example.com/a", "snippet": "s", "rerank_score": 1.6}
    ]}
    receipt = client.search(
        "宁德时代 2025 年报", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
        api_key="k", transport=transport_for(body, seen=seen), count=3, ori_question="问题",
    )
    assert receipt["status"] == "ok"
    assert receipt["cost_micros"] == 5000
    assert receipt["currency"] == "CNY"
    assert seen["payload"] == {"query": "宁德时代 2025 年报", "count": 3,
                               "need_content": True, "ori_question": "问题"}
    assert seen["headers"]["Authorization"] == "Bearer k"


def test_empty_results():
    receipt = client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                            api_key="k", transport=transport_for({"results": []}))
    assert receipt["status"] == "empty"
    assert receipt["result_count"] == 0


def test_http_error_is_unavailable_without_cost():
    receipt = client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                            api_key="k", transport=transport_for(b"{}", status=503))
    assert receipt["status"] == "unavailable"
    assert receipt["cost_micros"] == 0
    assert receipt["error_reason"] == "http_503"


def test_missing_key_rejected():
    try:
        client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"], api_key="")
    except ValueError as error:
        assert "api_key_required" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_count_bounds():
    for count in (0, 51):
        try:
            client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                          api_key="k", transport=transport_for({"results": []}), count=count)
        except ValueError as error:
            assert "count_invalid" in str(error)
        else:
            raise AssertionError("expected rejection")


def test_missing_deepseek_route_rejected():
    exp = exposure()
    exp["routes"] = [{"route_id": "brave-primary", "provider": "brave",
                      "credential_env": "BRAVE_API_KEY", "enabled": True, "max_queries": 2}]
    try:
        client.search("q", exposure=exp, policy_sha256=exposure()["search_policy_sha256"], api_key="k",
                      transport=transport_for({"results": []}))
    except ValueError as error:
        assert "deepseek_route_not_in_exposure" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_endpoint_override_rejected():
    try:
        client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                      api_key="k", transport=transport_for({"results": []}),
                      endpoint="https://evil.example.com/search")
    except ValueError as error:
        assert "endpoint_not_allowed" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_need_content_must_be_bool():
    try:
        client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                      api_key="k", transport=transport_for({"results": []}), need_content="false")
    except ValueError as error:
        assert "need_content_bool_required" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_zero_cost_rejected():
    try:
        client.search("q", exposure=exposure(), policy_sha256=exposure()["search_policy_sha256"],
                      api_key="k", transport=transport_for({"results": []}), cost_micros=0)
    except ValueError as error:
        assert "cost_micros_required" in str(error)
    else:
        raise AssertionError("expected rejection")
