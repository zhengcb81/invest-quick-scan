"""Search failure must be observable, not silently downgraded to "no results".

Regression context (2026-10-22): with no DEEPSEEK_API_KEY present, search()
normalized every non-200 response to an empty list. The scan then recorded all
questions as insufficient_evidence with reason "检索无可用来源" and exited 0, so a
credential outage looked identical to a genuinely empty search. These tests pin
the distinction between "the provider answered, but had nothing" and "the call
failed".
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import thin_scan  # noqa: E402


def _provider():
    return {"id": "stub", "endpoint": "https://example.invalid/search",
            "key_env": "STUB_KEY", "cost_micros": 700, "priority": 1}


def test_empty_successful_response_is_not_a_failure(monkeypatch):
    """A 200 with zero results is a legitimate empty search, not an error."""
    monkeypatch.setenv("STUB_KEY", "test-key")
    monkeypatch.setattr(thin_scan, "post_json", lambda *a, **k: (200, {"results": []}))

    results, error = thin_scan.search_with_status(_provider(), "q", 5)

    assert results == []
    assert error is None


def test_missing_credentials_are_reported_as_an_error(monkeypatch):
    """No key means the request cannot be authenticated: that is a failure."""
    monkeypatch.delenv("STUB_KEY", raising=False)
    monkeypatch.setattr(thin_scan, "post_json", lambda *a, **k: (200, {"results": []}))

    results, error = thin_scan.search_with_status(_provider(), "q", 5)

    assert results == []
    assert error == "search_missing_credentials:STUB_KEY"


def test_non_200_response_is_reported_with_its_status(monkeypatch):
    monkeypatch.setenv("STUB_KEY", "test-key")
    monkeypatch.setattr(thin_scan, "post_json", lambda *a, **k: (401, {"error": "bad key"}))

    results, error = thin_scan.search_with_status(_provider(), "q", 5)

    assert results == []
    assert error == "search_http_401"


def test_malformed_payload_is_reported(monkeypatch):
    monkeypatch.setenv("STUB_KEY", "test-key")
    monkeypatch.setattr(thin_scan, "post_json", lambda *a, **k: (200, ["not", "a", "dict"]))

    results, error = thin_scan.search_with_status(_provider(), "q", 5)

    assert results == []
    assert error == "search_bad_payload"


def test_legacy_search_still_returns_a_plain_list(monkeypatch):
    """Existing callers keep the list-shaped contract."""
    monkeypatch.setenv("STUB_KEY", "test-key")
    monkeypatch.setattr(thin_scan, "post_json", lambda *a, **k: (
        200, {"results": [{"url": "https://example.com/a", "title": "t"}]}))

    assert thin_scan.search(_provider(), "q", 5) == [
        {"url": "https://example.com/a", "title": "t", "summary": "", "date": "", "site": ""}]


def test_search_failure_is_recorded_in_the_question_problems(monkeypatch):
    """A failed search must land in problems, not masquerade as an empty result."""
    provider = _provider()
    monkeypatch.delenv("STUB_KEY", raising=False)

    record = {"problems": [], "searches": 0}
    results, error = thin_scan.search_with_status(provider, "q", 5)
    thin_scan._record_search_outcome(record, results, error)

    assert results == []
    assert record["problems"] == ["search_missing_credentials:STUB_KEY"]
    assert record["searches"] == 1


def test_model_call_reads_the_mapped_key_env(monkeypatch):
    """RED regression: ask_model() indexed provider['key_env'] and raised KeyError.

    model_config.models() returns raw config entries keyed `api_key_env`, exactly
    like the search provider did. Fixing only the search path left every model
    call crashing the moment a real key was present.
    """
    monkeypatch.setenv("STUB_KEY", "test-key")
    captured = {}

    def fake_post(url, key, body, timeout):
        captured["key"] = key
        captured["model"] = body.get("model")
        return 200, {"choices": [{"message": {"content": '{"status":"insufficient_evidence","summary":"s"}'}}],
                     "usage": {"prompt_tokens": 1, "completion_tokens": 2}}

    monkeypatch.setattr(thin_scan, "post_json", fake_post)
    provider = {"id": "stub", "model": "stub-model", "endpoint": "https://example.invalid/chat",
                "key_env": "STUB_KEY"}

    answer = thin_scan.ask_model(provider, "prompt")

    assert captured["key"] == "test-key", "credentials must be resolved through key_env"
    assert captured["model"] == "stub-model"
    assert "error" not in answer


def test_model_config_models_expose_key_env():
    """model_config.models() feeds ask_model(); it must expose the mapped field."""
    import model_config

    for provider in model_config.models():
        assert "key_env" in provider, f"model {provider.get('id')} lacks key_env"
        assert "api_key_env" not in provider, "consumers read key_env; do not leak the raw field"
