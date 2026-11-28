"""Production C06 owner composition, native response capture, and cold recovery.

The original synthetic admission fixture provisions a temporary authority only.
The test drives the public StockQA CLI and real IQS/owner/SDK/Runner stores.
The sole provider wire is a literal loopback HTTP service with no keys.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import threading

import pytest

if os.environ.get("IQS_C06_RUN_INTEGRATION") != "1":
    raise RuntimeError("Configure the explicit owned C06 fixture runtime before collection")

_ENV_NAMES = (
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP", "PYTHONUTF8",
    "PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "IQS_C06_RUN_INTEGRATION", "IQS_C06_OWN",
    "IQS_C06_COMPOSITION_CODE_ROOT", "IQS_C06_COMPANY_ROOT", "IQS_C06_BRIDGE_ROOT",
)
SAFE_ENV = {name: os.environ[name] for name in _ENV_NAMES if name in os.environ}
OWN = Path(SAFE_ENV["IQS_C06_OWN"]).resolve()
CODE = Path(SAFE_ENV["IQS_C06_COMPOSITION_CODE_ROOT"]).resolve()
MODEL = "mimo-v2.6-pro"
PROVIDER_ENDPOINT = "https://api.xiaomimimo.com/v1/chat/completions"
CUTOFF = "2026-10-13"
CRASH_EXIT = 86

# The pinned C06 infrastructure supplies these setup-only synthetic fixtures.
from tests.integration.test_c06_refresh_admission import setup_admission
from tests.integration.test_c06_subject_public_e2e import actual
from src.config.llm_config import LLMConfig


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf8")


def _read(path):
    return json.loads(path.read_text(encoding="utf8"))


def _model_configuration():
    """Synthetic policy with one route, resolved by the public owner config."""
    route = dict(
        id="c06-loopback", enabled=True, provider_config_ref="mimo", model=MODEL,
        quota_group="fixture-account", max_in_flight=1,
    )
    caps = ["web_search", "structured_output"]
    return {
        "default_provider": "mimo",
        "providers": {"mimo": {
            "enabled": True, "api_key": "C06-LOOPBACK-FIXTURE-NOT-A-KEY",
            "provider_type": "mimo", "base_url": PROVIDER_ENDPOINT, "model": MODEL,
        }},
        "quick_scan_model_policy": {
            "schema_version": "2.0.0", "policy_id": "c06-native-pack-fixture",
            "configured": True, "execution_owner": "StockQAbyLLM",
            "dispatch": {
                "max_in_flight_total": 1, "max_questions_per_pack": 12,
                "one_entity_per_pack": True, "separate_score_and_fact_packs": True,
                "required_capabilities": caps, "on_preferred_capacity_full": "wait",
                "speculative_racing": False,
            },
            "budget": {
                "currency": "USD", "max_cost": 25, "max_requests": 20,
                "max_cost_per_attempt": 1, "reset_on_restart": False,
            },
            "cost_policy": {
                "pricing_basis": "verified_rate_card", "pricing_ref": "c06-loopback-rates",
                "include_search_charges": True, "include_failed_attempts": True,
                "reserve_before_dispatch": True,
                "unknown_actual_cost_action": "retain_reservation_and_pause",
            },
            "quota_groups": [{
                "id": route["quota_group"], "max_in_flight": 1, "window_seconds_hint": None,
                "unknown_reset_cooldown_seconds": 60, "half_open_probe_limit": 1,
            }],
            "models": [route],
            "fallback": {
                "on_quota_exhausted": "cooldown_group_then_next",
                "on_rate_limit": "respect_retry_after_then_next",
                "on_server_error": "bounded_retry_then_next",
                "on_auth_error": "disable_route_then_next",
                "on_invalid_request": "stop_without_fallback",
                "on_malformed_response": "bounded_retry_then_next",
                "on_missing_capability": "skip_before_dispatch",
                "on_timeout": "reconcile_receipt_before_retry",
                "on_low_score": "accept",
                "on_unknown_answer": "accept_with_gap",
                "on_fallback_success": "stop_dispatch_keep_primary_health",
                "max_attempts_per_dispatch_round": 1,
            },
            "comparison": {
                "enabled": False, "max_models_per_question": 2, "max_cost": 0, "max_requests": 0,
                "same_input_and_cutoff_required": True, "separate_from_primary_fallback": True,
            },
            "resume": {
                "success_checkpoint": "per_question", "replay_outbox_before_dispatch": True,
                "preserve_uncertain_requests": True, "persist_cooldowns_and_budget": True,
            },
        },
    }


def _capture_provider(tmp_path):
    _write(tmp_path / "llm_apis.json", _model_configuration())
    _write(tmp_path / "spend_authorization.json", {
        "schema_version": "1.0.0", "currency": "USD", "hard_cap": 25,
        "pricing_snapshot_ref": "c06-loopback-rates",
        "authorized_at": datetime.now(timezone.utc).isoformat(),
    })
    _write(tmp_path / "quick_scan_rate_cards.json", {
        "schema_version": "1.0.0",
        "rate_cards": [{
            "pricing_ref": "c06-loopback-rates", "provider": "mimo", "model": MODEL,
            "currency": "USD", "source_ref": "synthetic-c06-loopback",
            "source_checked_at": datetime.now(timezone.utc).date().isoformat(),
            "rates": {
                "input_per_million_tokens": 1, "cached_input_per_million_tokens": 0,
                "cache_creation_input_per_million_tokens": 1, "output_per_million_tokens": 1,
                "search_tool_call": 0,
            },
        }],
    })
    return LLMConfig(str(tmp_path / "llm_apis.json")).get_quick_scan_model_policy(default_provider="mimo")


def _answer(question_id):
    return {
        "question_id": question_id, "response_kind": "score", "status": "not_applicable",
        "score": None, "summary": "[Synthetic C06 fixture] No company finding.",
        "information_as_of": CUTOFF, "period_start": "2025-01-01", "period_end": "2025-12-31",
        "basis": "trailing", "trend": "stable", "confidence": "medium",
        "metrics": [], "items": [], "evidence": [], "counterevidence": "Synthetic only.",
        "watch_triggers": [], "missing_fields": ["Synthetic evidence only"],
        "coverage": {"status": "partial", "reason": "Synthetic test data only"},
    }


@contextmanager
def _loopback_provider(profile):
    """Accept only the native chat-completions POST on the test socket."""
    posts, errors = [], []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                assert self.path == "/v1/chat/completions"
                assert self.headers.get("Authorization") is None
                assert self.client_address[0] == "127.0.0.1"
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                assert request["model"] == MODEL
                assert request["thinking"] == {"type": "enabled"}
                assert any(tool.get("type") == "web_search" for tool in request["tools"])
                context = json.loads(request["messages"][-1]["content"].splitlines()[-1])
                selected = context["requested_question_ids"]
                assert selected == _read(profile)["packs"][len(posts)]
                posts.append(selected)
                final = {"answers": [_answer(qid) for qid in selected], "declared_question_ids": selected}
                response = {
                    "id": "synthetic-c06-native-" + str(len(posts)), "model": MODEL,
                    "choices": [{"message": {
                        "role": "assistant", "content": json.dumps(final),
                        "reasoning_content": "PRIVATE-NATIVE-REASONING",
                        "annotations": [{"type": "url_citation", "url": "https://example.invalid/c06-synthetic"}],
                    }, "finish_reason": "stop"}],
                    "usage": {
                        "prompt_tokens": 1200, "prompt_tokens_details": {"cached_tokens": 400},
                        "completion_tokens": 1200, "completion_tokens_details": {"reasoning_tokens": 200},
                        "web_search_usage": {"tool_usage": 1},
                    },
                }
                raw = json.dumps(response).encode("utf8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("x-request-id", response["id"])
                self.end_headers()
                self.wfile.write(raw)
            except Exception as error:
                errors.append(type(error).__name__)
                self.send_error(500, "C06 test server rejected the request")

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", posts, errors
        finally:
            server.shutdown()
            thread.join()


def _route_fixture_wire(loopback):
    """Route only transport to the real local socket after native endpoint validation."""
    from requests.adapters import HTTPAdapter

    original = HTTPAdapter.send

    def send(adapter, request, **options):
        if request.method != "POST" or request.url != PROVIDER_ENDPOINT:
            raise AssertionError("C06 attempted a request outside its fixture")
        if not loopback:
            raise AssertionError("C06 cold recovery attempted transport")
        projected = request.copy()
        projected.url = loopback + "/v1/chat/completions"
        projected.headers.pop("Authorization", None)
        options["proxies"] = {}
        return original(adapter, projected, **options)

    HTTPAdapter.send = send


def _observe_engine(root, phase):
    from iqs_company_agent_lab.api import task_snapshot
    sys.path.insert(0, str(CODE / "scripts"))
    import shared_company_engine as engine

    if phase == "recovery":
        resume = engine.resume_shared_engine

        def resume_fixture(*args, **kwargs):
            return resume(*args, **{**kwargs, "transport_origin": "scripted_wire"})

        engine.resume_shared_engine = resume_fixture
        return
    execute = engine.execute_shared_engine
    checkpoint_wrapper = engine._pending_port
    sent_packs = []

    def record_profile(task, *args, **kwargs):
        snapshot = task_snapshot(task)
        profile = snapshot["raw"]["execution_profile"]
        _write(root / "approved-pack-profile.json", {
            "packs": profile["packs"], "question_ids": snapshot["question_ids"],
            "input_token_cap": snapshot["limits"]["session_input_tokens"],
        })
        return execute(task, *args, **{**kwargs, "transport_origin": "scripted_wire"})

    class ResponseBoundary:
        def __init__(self, port):
            self.port = port

        def __getattr__(self, name):
            return getattr(self.port, name)

        def model_step(self, envelope):
            receipt = self.port.model_step(envelope)
            if receipt.get("outcome") != "response_available":
                _write(root / "native-refusal.json", {
                    "outcome": receipt.get("outcome"), "reason_code": receipt.get("reason_code"),
                })
                return receipt
            selected = envelope["intent"]["question_ids"]
            sent_packs.append(selected)
            if phase == "crash" and sent_packs == _read(root / "approved-pack-profile.json")["packs"]:
                _write(root / "crash-native-proof.json", {
                    "native_reference": receipt["runtime_attempt_ref"], "packs": sent_packs,
                })
                # The owner port returned only after the native SDK and owner
                # stores committed. IQS has saved just the pending intent here.
                os._exit(CRASH_EXIT)
            return receipt

    def wrap_checkpoint_port(port, *args, **kwargs):
        return checkpoint_wrapper(ResponseBoundary(port), *args, **kwargs)

    engine.execute_shared_engine = record_profile
    engine._pending_port = wrap_checkpoint_port


def _cli_args(config, phase):
    bundle = Path(config["bundle"])
    args = [
        str(OWN / "qa/main_with_llm.py"), "--company", "Synthetic C06 issuer",
        "--entity-id", config["entity_id"], "--require-search",
        "--refresh-admission-config", config["deployment"],
        "--refresh-confirmation-id", config["confirmation_id"],
        "--shared-company-config", config["shared"], "--output", config["output"],
    ]
    if phase == "recovery":
        args += ["--seal-deliveries", "--recover-checkpoints"]
    else:
        args += ["--provider", "mimo", "--question-pack-size", "12", "--max-output-tokens", "4096"]
    for name, flag in (
        ("manifest.json", "question-manifest"), ("identity.json", "identity-snapshot"),
        ("authority.json", "c06-authority"), ("questions.json", "config"),
        ("owner-config.json", "quick-scan-owner-config"),
    ):
        args += ["--" + flag, str(bundle / name)]
    return args


def _child(phase, config_path):
    config = _read(Path(config_path))
    _route_fixture_wire(config["loopback"] if phase == "crash" else None)
    _observe_engine(Path(config["root"]), phase)
    sys.path.insert(0, str(OWN / "qa"))
    sys.argv = _cli_args(config, phase)
    runpy.run_path(sys.argv[0], run_name="__main__")


def _run_child(root, config_path, phase):
    with (root / f"{phase}.out").open("wb") as out, (root / f"{phase}.err").open("wb") as err:
        return subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), phase, str(config_path)],
            cwd=root, env={**SAFE_ENV, "PYTHONDONTWRITEBYTECODE": "1"}, stdin=subprocess.DEVNULL,
            stdout=out, stderr=err, timeout=600,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).returncode


def _diagnostic(root, phase):
    return "\n".join(
        line for suffix in ("out", "err")
        for line in (root / f"{phase}.{suffix}").read_text(encoding="utf8").splitlines()
        if len(line) < 700
    )[-2400:]


_PARAMS = [{"observation_version": "1.2.0", "information_cutoff": CUTOFF}]


@pytest.mark.parametrize("actual", _PARAMS, indirect=True)
@pytest.mark.parametrize("case", ["crash", "oversize"])
def test_original_twelve_owner_sdk_runner_and_process_resume_zero_new_http(actual, tmp_path, case):
    policy = _capture_provider(tmp_path)
    prepared = setup_admission(
        actual, tmp_path, policy=policy, provider="mimo", selected_question_count=12,
        information_cutoff=CUTOFF,
    )
    confirmation_id = prepared["consent"]["confirmation_id"]
    admitted = subprocess.run(
        [
            sys.executable, "-B", "-m", "src.utils.quick_scan_refresh_admission_cli",
            "--config", str(prepared["deployment_file"]), "--confirmation-id", confirmation_id,
        ],
        cwd=tmp_path, env=SAFE_ENV, stdin=subprocess.DEVNULL, capture_output=True,
        encoding="utf8", timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert admitted.returncode == 0, admitted.stderr[-2000:]
    admission = json.loads(admitted.stdout)
    assert admission["status"] == "accepted" and admission["API_requests"] == 0
    shared = tmp_path / "shared.json"
    settings = {
        "schema_version": "1.0.0", "iqs_root": str(CODE), "state_root": str(tmp_path / "shared"),
        "company_agent_root": SAFE_ENV["IQS_C06_COMPANY_ROOT"],
        "runtime_bridge_root": SAFE_ENV["IQS_C06_BRIDGE_ROOT"],
    }
    if case == "oversize":
        settings["limits"] = {"session_input_tokens": 1024}
    _write(shared, settings)

    output = tmp_path / "result.json"
    config_path = tmp_path / "owned-native-test.json"
    profile_path = tmp_path / "approved-pack-profile.json"
    with _loopback_provider(profile_path) as (origin, posts, errors):
        config = {
            "root": str(tmp_path), "confirmation_id": confirmation_id,
            "entity_id": prepared["ref"]["entity_id"], "loopback": origin,
            "bundle": str(prepared["bundle"]), "deployment": str(prepared["deployment_file"]),
            "output": str(output), "shared": str(shared),
        }
        _write(config_path, config)
        result = _run_child(tmp_path, config_path, case)
        if case == "oversize":
            assert result != 0
            assert _read(tmp_path / "native-refusal.json") == {
                "outcome": "rejected", "reason_code": "research_session_resource_limit",
            }
            assert not posts and not errors
            assert prepared["ledger"].get_quick_scan_budget_status(policy["policy_id"])["requests"] == 0
            assert not output.exists()
            return

        assert result == CRASH_EXIT, _diagnostic(tmp_path, "crash")
        profile = _read(profile_path)
        selected = [row["id"] for row in prepared["selected_questions"]]
        assert profile["packs"] == [selected]
        assert len(selected) == 12 and len(set(selected)) == 12
        assert posts == profile["packs"] and not errors
        assert profile["input_token_cap"] == 240000
        crash = _read(tmp_path / "crash-native-proof.json")
        assert crash["native_reference"] and crash["packs"] == profile["packs"]
        checkpoint, = (tmp_path / "shared").glob("*/session-*/checkpoint.json")
        before = checkpoint.read_bytes()
        assert _read(checkpoint).get("pending_receipt") is None
        assert _read(checkpoint).get("pending_intent")
        assert not output.exists()

        paid = prepared["ledger"].get_quick_scan_budget_status(policy["policy_id"])
        assert paid["requests"] == 1
        (tmp_path / "llm_apis.json").unlink()
        (tmp_path / "quick_scan_rate_cards.json").unlink()
        (tmp_path / "spend_authorization.json").unlink()
        result = _run_child(tmp_path, config_path, "recovery")
        assert result == 0, _diagnostic(tmp_path, "recovery")
        scope = _read(output.with_suffix(".json.scope.json"))
        assert scope["status"] == "completed" and scope["recovery_mode"] == "received_original_response", scope
        assert scope["original_question_count"] == scope["restored_question_count"] == 12
        assert set(scope["saved_question_ids"]) == set(selected)
        assert scope["remaining_question_ids"] == []
        assert scope["API_requests"] == 0 and scope["dispatch_started"] is False
        assert checkpoint.read_bytes() == before
        assert posts == profile["packs"] and not errors
        assert prepared["ledger"].get_quick_scan_budget_status(policy["policy_id"]) == paid
        summary_file, = (tmp_path / "shared").glob("*/export/runtime-summary.json")
        summary = _read(summary_file)
        assert summary["runtime_origin"] == "scripted_wire"
        assert summary["new_model_http"] == 0 and summary["replayed_native_attempts"] == 1
        assert not summary["owner_authority_verified"] and not summary["financial_qualification_granted"]
        assert b"PRIVATE-NATIVE-REASONING" not in output.read_bytes()
        for path in summary_file.parent.iterdir():
            if path.is_file():
                assert b"PRIVATE-NATIVE-REASONING" not in path.read_bytes()


if __name__ == "__main__":
    _child(sys.argv[1], sys.argv[2])
