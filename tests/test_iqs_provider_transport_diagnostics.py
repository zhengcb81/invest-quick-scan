"""Provider transport failures are safe to return and readable after exit."""

from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from iqs_scan.providers.api import ask_model, post_json  # noqa: E402


CANARY = "synthetic-provider-value-do-not-copy"
URL = "https://provider.invalid/?private=" + CANARY


def owner(args, request=None):
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts" / "iqs_feedback_owner.py"),
                             *map(str, args)], env=dict(os.environ), input=request, capture_output=True,
                            text=True, encoding="utf8", timeout=20, check=True)
    return json.loads(result.stdout)


def scoped_outbox(tmp_path, monkeypatch):
    runs, out = tmp_path / "runs", tmp_path / "outbox"
    monkeypatch.setenv("IQS_FEEDBACK_RUNS_ROOT", str(runs))
    monkeypatch.setenv("RESEARCH_FEEDBACK_DIR", str(out))
    monkeypatch.setenv("RESEARCH_FEEDBACK_RUN_ID", "provider-fixture-run")
    monkeypatch.setenv("RESEARCH_FEEDBACK_ATTEMPT_ID", "provider-fixture-attempt")
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    return runs, out


def rows(out):
    return [json.loads(marker.with_suffix(".jsonl").read_bytes()) for marker in out.glob("feedback-*.ready")]


def digest(value):
    data = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(data.encode("ascii")).hexdigest()


def reconcile(runs, row):
    fields = ("owner", "origin_owner", "run_id", "attempt_id", "step_id", "check_id")
    occurrence = digest([row[field] for field in fields])
    module = row["owner"]
    action = digest(["reconcile", module, occurrence])
    payload = {"occurrence_id": occurrence, "observation": row}
    request = {"schema_version": "feedback-action/1", "owner": module, "kind": "reconcile",
               "method": "lookup", "action_id": action, "payload": payload,
               "request_digest": digest([module, "reconcile", action, payload])}
    return owner(["--db", runs / "uncreated.sqlite", "--runs-root", runs, "reconcile"], json.dumps(request))


@pytest.mark.parametrize(("scenario", "status", "marker", "code", "error_type"), [
    ("http-text", 503, "http_error", "provider_http_503", "HTTPError"),
    ("http-json", 429, "http_error", "provider_http_429", "HTTPError"),
    ("url", 0, "transport", "provider_transport_error", "ConnectionRefusedError"),
    ("timeout", 0, "timeout", "provider_transport_timeout", "TimeoutError"),
    ("invalid-response", 0, "transport", "provider_invalid_response", "JSONDecodeError"),
])
def test_provider_failure_returns_safe_fact_and_survives_cold_read(tmp_path, monkeypatch, capsys,
                                                                scenario, status, marker, code, error_type):
    runs, out = scoped_outbox(tmp_path, monkeypatch)
    calls = []

    class Response(io.BytesIO):
        status = 200

    def offline(request, timeout):
        calls.append(timeout)
        if scenario in {"http-text", "http-json"}:
            body = json.dumps({"error": CANARY}) if scenario == "http-json" else CANARY
            raise urllib.error.HTTPError(URL, status, CANARY, None, io.BytesIO(body.encode()))
        if scenario == "url":
            raise urllib.error.URLError(ConnectionRefusedError(111, URL))
        if scenario == "timeout":
            raise TimeoutError(CANARY)
        return Response(CANARY.encode())

    monkeypatch.setattr(urllib.request, "urlopen", offline)
    actual_status, payload = post_json(URL, CANARY, {"prompt": CANARY}, 4)
    assert actual_status == status
    assert CANARY not in json.dumps(payload)
    assert payload == {"error": marker}
    row, = rows(out)
    assert (row["actual"], row["run_id"], row["attempt_id"]) == (code, "provider-fixture-run", "provider-fixture-attempt")
    ref = row["details_ref"]
    cold = ["--runs-root", runs, "get-diagnostic", ref]
    saved = owner(cold)
    assert owner(cold) == saved
    assert saved["diagnostic"]["observation"] == row
    chain = saved["diagnostic"]["chain"]
    assert any(cause["type"] == error_type for cause in chain)
    if scenario == "url":
        assert any(cause.get("errno") == 111 for cause in chain)
    usage = reconcile(runs, row)["result"]
    assert (usage["job_status"], usage["status"], usage["cost_state"]) == ("unconfirmed", "cost_unknown", "unknown")
    assert usage["recorded_search_cost_micros"] is None
    assert usage["new_model_calls"] == usage["new_searches"] == usage["new_cost_micros"] == 0
    assert not (runs / "uncreated.sqlite").exists()
    assert calls == [4]

    console = capsys.readouterr()
    persisted = b"".join(path.read_bytes() for folder in (runs, out) for path in folder.rglob("*") if path.is_file())
    assert CANARY not in console.err + console.out + json.dumps(saved)
    assert CANARY.encode() not in persisted


def test_original_attempt_groups_matching_failures_and_keeps_different_classes(tmp_path, monkeypatch):
    _, out = scoped_outbox(tmp_path, monkeypatch)
    failed = [urllib.error.HTTPError(URL, 503, CANARY, None, io.BytesIO()) for _ in range(2)]
    failed.append(TimeoutError(CANARY))

    def offline(*_args, **_kwargs):
        raise failed.pop(0)

    monkeypatch.setattr(urllib.request, "urlopen", offline)
    provider = {"endpoint": URL, "key_env": "IQS_PROVIDER_FIXTURE_KEY", "model": "offline"}
    monkeypatch.setenv(provider["key_env"], CANARY)
    assert ask_model(provider, "placeholder") == {"error": "model_http_503"}
    assert ask_model(provider, "placeholder") == {"error": "model_http_503"}
    assert ask_model(provider, "placeholder") == {"error": "model_timeout"}
    observations = rows(out)
    assert len(observations) == 2
    assert len({row["details_ref"] for row in observations}) == 2
    assert {row["actual"] for row in observations} == {"provider_http_503", "provider_transport_timeout"}
    assert {row["step_id"] for row in observations} == {"provider.http/http_503", "provider.http/transport_timeout"}
    assert {row["attempt_id"] for row in observations} == {"provider-fixture-attempt"}


def test_success_keeps_original_model_usage_and_does_not_log_failure(tmp_path, monkeypatch):
    _, out = scoped_outbox(tmp_path, monkeypatch)

    class Response(io.BytesIO):
        status = 200

    result = {"choices": [{"message": {"content": "{\"score\": 3}"}}],
              "usage": {"prompt_tokens": 11, "completion_tokens": 7}}
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response(json.dumps(result).encode()))
    provider = {"endpoint": URL, "key_env": "IQS_PROVIDER_FIXTURE_KEY", "model": "offline"}
    monkeypatch.setenv(provider["key_env"], CANARY)
    assert ask_model(provider, "placeholder") == {"score": 3, "_usage": {"prompt_tokens": 11, "completion_tokens": 7}}
    assert rows(out) == []
