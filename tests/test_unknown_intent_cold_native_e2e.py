"""Cold unknown-intent recovery through the original cross-repository owner.

The company, approval, SQLite and task are synthetic; StockQA's actual native
owner, SDK and the original Company Agent Runner are used. The vendor wire is
scripted and no external API is called.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import hashlib

import pytest
from unknown_intent_diagnostics import exception_cause_chain, write_child_diagnostic

from test_company_scan_native_e2e import (
    actual,
    construct,
    SAFE_ENV,
    CODE,
    COMPANY,
    BRIDGE,
    _policy,
    RefreshAdmissionService,
    setup_admission,
    _task_snapshot,
    load,
)


def _append_post(path, phase):
    with open(path, "a", encoding="utf8") as stream:
        stream.write(json.dumps({"phase": phase}, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _session(model):
    return dict(
        protocol="iqs.agent-runtime-lab.session-config/1.0.0",
        planned_model=model,
        endpoint_profile_id=f"{model}@https://api.xiaomimimo.com/v1/chat/completions",
        max_output_tokens=4096,
        session_input_tokens=240000,
        session_output_tokens=48000,
        wall_seconds=900,
        logical_clock=False,
    )


def _read_post_count(path, phase):
    path = Path(path)
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf8").splitlines():
        try:
            count += json.loads(line).get("phase") == phase
        except (TypeError, ValueError):
            continue
    return count


def _safe_result_summary(result):
    if not isinstance(result, dict):
        return None
    summary = result.get("runtime_summary")
    safe = {
        "status": result.get("status") if isinstance(result.get("status"), str) else None,
        "all_slots_completed": result.get("all_slots_completed")
        if isinstance(result.get("all_slots_completed"), bool) else None,
        "runtime_summary_present": isinstance(summary, dict),
    }
    if isinstance(summary, dict):
        for name in ("new_model_http", "replayed_native_attempts"):
            value = summary.get(name)
            if isinstance(value, int) and not isinstance(value, bool):
                safe[name] = value
    return safe


def _exception_roots():
    own = Path(SAFE_ENV["IQS_C06_OWN"]).resolve()
    return (
        ("qa", own / "qa"),
        ("sw", own / "sw"),
        ("company", Path(SAFE_ENV["IQS_C06_COMPANY_ROOT"])),
        ("runtime", Path(SAFE_ENV["IQS_C06_BRIDGE_ROOT"])),
        ("iqs", Path(SAFE_ENV["IQS_C06_COMPOSITION_CODE_ROOT"])),
        ("repo", Path(__file__).resolve().parents[1]),
    )


def _child_run(config_path, phase, diagnostic_path):
    diagnostic = {
        "phase": phase,
        "execute_returned": False,
        "execute_exception_type": None,
        "execute_cause_chain": [],
        "summary": None,
        "checkpoint_exists": False,
        "checkpoint_sha256": None,
        "pending_intent_present": False,
        "pending_intent_kind": None,
        "pending_receipt_present": False,
        "pending_receipt_outcome": None,
        "pending_receipt_reason_code": None,
        "pending_receipt_final_content_present": None,
        "pending_receipt_tool_calls_present": None,
        "export_exists": False,
        "recovery_decision": None,
        "recovery_reason": None,
        "saved_receipt_present": None,
        "resume_returned": False,
        "resume_exception_type": None,
        "resume_cause_chain": [],
        "resume_reason_code": None,
        "recovered_session_exists": False,
        "recovered_export_exists": False,
        "wire_post_count": 0,
    }
    settings = None
    try:
        settings = json.loads(Path(config_path).read_text(encoding="utf8"))
        task, services = construct(settings["settings"])
        contract = _task_snapshot(task)
        from iqs_scan.execution import api as engine
        from src.providers import llm_research_client as sdk
        from src.utils.quick_scan_company_api import create_company_research_runtime
        import requests

        class Wire:
            def post(self, *args, **kwargs):
                _append_post(settings["post_log"], phase)
                if phase == "send-unknown":
                    raise requests.Timeout("scripted provider outcome is unknown")
                raise AssertionError("unknown native intent must never be posted again")

        sdk.http_client_manager.get_metered_sync_session = lambda: Wire()
        checkpoint = Path(settings["session_dir"]) / "checkpoint.json"
        if phase == "send-unknown":
            try:
                result = engine.execute_shared_engine(
                    task,
                    services,
                    settings["session_config"],
                    settings["unused_export"],
                    session_dir=settings["session_dir"],
                    transport_origin="scripted_wire",
                )
                diagnostic["execute_returned"] = True
                diagnostic["summary"] = _safe_result_summary(result)
            except Exception as error:
                diagnostic["execute_exception_type"] = type(error).__name__
                diagnostic["execute_cause_chain"] = exception_cause_chain(error, _exception_roots())
            diagnostic["export_exists"] = Path(settings["unused_export"]).exists()
        elif phase == "cold-recovery":
            pass
        else:
            raise ValueError("unknown diagnostic phase")

        if checkpoint.is_file():
            raw_checkpoint = checkpoint.read_bytes()
            diagnostic["checkpoint_exists"] = True
            diagnostic["checkpoint_sha256"] = hashlib.sha256(raw_checkpoint).hexdigest()
            saved = json.loads(raw_checkpoint.decode("utf8"))
            intent = saved.get("pending_intent")
            receipt = saved.get("pending_receipt")
            diagnostic["pending_intent_present"] = isinstance(intent, dict)
            diagnostic["pending_intent_kind"] = (
                intent.get("kind") if isinstance(intent, dict) and isinstance(intent.get("kind"), str) else None
            )
            diagnostic["pending_receipt_present"] = receipt is not None
            if isinstance(receipt, dict):
                outcome = receipt.get("outcome")
                if outcome in {"response_available", "rejected", "outcome_unknown"}:
                    diagnostic["pending_receipt_outcome"] = outcome
                reason_code = receipt.get("reason_code")
                if isinstance(reason_code, str):
                    diagnostic["pending_receipt_reason_code"] = reason_code
                diagnostic["pending_receipt_final_content_present"] = (
                    receipt.get("final_content") is not None
                )
                diagnostic["pending_receipt_tool_calls_present"] = (
                    receipt.get("tool_calls") is not None
                )
            if isinstance(intent, dict):
                runtime = create_company_research_runtime(services, task_contract=contract)
                proof = runtime.recover_intent(intent)
                diagnostic["recovery_decision"] = proof.get("decision")
                diagnostic["recovery_reason"] = proof.get("reason")
                diagnostic["saved_receipt_present"] = proof.get("saved_receipt") is not None

                if phase == "cold-recovery":
                    try:
                        result = engine.resume_shared_engine(
                            task,
                            services,
                            settings["session_config"],
                            checkpoint,
                            settings["recovered_export"],
                            session_dir=settings["recovered_session"],
                            transport_origin="scripted_wire",
                        )
                        diagnostic["resume_returned"] = True
                        diagnostic["summary"] = _safe_result_summary(result)
                    except Exception as error:
                        diagnostic["resume_exception_type"] = type(error).__name__
                        diagnostic["resume_cause_chain"] = exception_cause_chain(error, _exception_roots())
                        if "native_safe_output_required_never_resend_unknown" in str(error):
                            diagnostic["resume_reason_code"] = "native_safe_output_required_never_resend_unknown"
        diagnostic["recovered_session_exists"] = Path(settings["recovered_session"]).exists()
        diagnostic["recovered_export_exists"] = Path(settings["recovered_export"]).exists()
    except Exception as error:
        diagnostic["child_exception_type"] = type(error).__name__
        diagnostic["child_cause_chain"] = exception_cause_chain(error, _exception_roots())
    finally:
        if settings is not None:
            diagnostic["wire_post_count"] = _read_post_count(settings["post_log"], phase)
        write_child_diagnostic(diagnostic_path, diagnostic)


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_original_unknown_intent_cold_recovery_refuses_without_second_http(
    actual, tmp_path
):
    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    policy["routes"] = policy["routes"][:1]
    targets = [
        dict(
            provider="mimo",
            model=route["model"],
            route_id=route["id"],
            provider_config_ref=route["provider_config_ref"],
            quota_group=route["quota_group"],
        )
        for route in policy["routes"]
    ]
    prepared = setup_admission(
        actual,
        tmp_path,
        policy=policy,
        provider="mimo",
        selected_question_count=1,
        refresh_version="1.6.0",
        ordered_route_targets=targets,
    )
    accepted = RefreshAdmissionService(
        prepared["deployment_file"], process_env=dict(SAFE_ENV)
    ).admit(prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"

    # The original task/client route is valid; only its transport is replaced
    # by a deterministic timeout after the send-intent has been recorded.
    model_file = tmp_path / "model-config.json"
    model_file.write_text(
        json.dumps(
            {
                "providers": {
                    target["provider_config_ref"]: {
                        "base_url": "https://api.xiaomimimo.com/v1/chat/completions"
                    }
                    for target in targets
                }
            }
        ),
        encoding="utf8",
    )
    settings = dict(
        root=str(tmp_path),
        deployment=str(prepared["deployment_file"]),
        confirmation_id=prepared["consent"]["confirmation_id"],
        bundle=str(prepared["bundle"]),
        policy=policy,
        llm_config_file=str(model_file),
    )
    session_config = _session(targets[0]["model"])
    session_dir = tmp_path / "original-session"
    config_path = tmp_path / "unknown-native-run.json"
    post_log = tmp_path / "provider-posts.jsonl"
    # This path is in the explicitly owned outer runtime so the run_group
    # tempfile cleanup cannot erase evidence before the wrapper archives it.
    diagnostic_dir = Path(SAFE_ENV["IQS_C06_OWN"]) / "diagnostics"
    diagnostic_dir.mkdir()
    config_path.write_text(
        json.dumps(
            {
                "settings": settings,
                "session_config": session_config,
                "session_dir": str(session_dir),
                "unused_export": str(tmp_path / "unused-export"),
                "recovered_session": str(tmp_path / "recovered-session"),
                "recovered_export": str(tmp_path / "recovered-export"),
                "post_log": str(post_log),
                "diagnostic_dir": str(diagnostic_dir),
            }
        ),
        encoding="utf8",
    )

    expected_diagnostics = {
        "send-unknown": {
            "wire_post_count": 1,
            "checkpoint_exists": True,
            "pending_intent_present": True,
            "pending_intent_kind": "model_step",
            "pending_receipt_present": True,
            "pending_receipt_outcome": "outcome_unknown",
            "pending_receipt_reason_code": "transport_outcome_uncertain",
            "pending_receipt_final_content_present": False,
            "pending_receipt_tool_calls_present": False,
            "recovery_decision": "pause_for_inspection",
            "saved_receipt_present": False,
            "summary": {
                "status": None,
                "all_slots_completed": False,
                "runtime_summary_present": True,
                "new_model_http": 1,
                "replayed_native_attempts": 0,
            },
        },
        "cold-recovery": {
            "wire_post_count": 0,
            "checkpoint_exists": True,
            "pending_intent_present": True,
            "pending_intent_kind": "model_step",
            "pending_receipt_present": True,
            "pending_receipt_outcome": "outcome_unknown",
            "pending_receipt_reason_code": "transport_outcome_uncertain",
            "pending_receipt_final_content_present": False,
            "pending_receipt_tool_calls_present": False,
            "recovery_decision": "pause_for_inspection",
            "saved_receipt_present": False,
            "resume_returned": False,
            "resume_reason_code": "native_safe_output_required_never_resend_unknown",
            "recovered_session_exists": False,
            "recovered_export_exists": False,
        },
    }
    for phase in ("send-unknown", "cold-recovery"):
        diagnostic_path = diagnostic_dir / f"{phase}.json"
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(Path(__file__)), phase, str(config_path), str(diagnostic_path)],
            cwd=Path(SAFE_ENV["IQS_C06_OWN"]) / "qa",
            env=dict(SAFE_ENV, PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True,
            timeout=900,
        )
        (tmp_path / (phase + ".stdout.log")).write_bytes(result.stdout[-16000:])
        (tmp_path / (phase + ".stderr.log")).write_bytes(result.stderr[-16000:])
        diagnostic = json.loads(diagnostic_path.read_text(encoding="utf8")) if diagnostic_path.is_file() else None
        post_count = len(post_log.read_text(encoding="utf8").splitlines()) if post_log.is_file() else 0
        assert result.returncode == 0, (
            f"phase={phase}, returncode={result.returncode}, diagnostic={diagnostic}, "
            f"post_log_lines={post_count}, stderr={result.stderr[-5000:].decode(errors='replace')}"
        )
        assert diagnostic is not None, f"phase={phase}, diagnostic missing, post_log_lines={post_count}"
        assert diagnostic.get("child_exception_type") is None, (
            f"phase={phase}, diagnostic={diagnostic}, post_log_lines={post_count}"
        )
        for field, expected in expected_diagnostics[phase].items():
            assert diagnostic.get(field) == expected, (
                f"phase={phase}, field={field}, expected={expected}, diagnostic={diagnostic}, "
                f"post_log_lines={post_count}"
            )
    assert json.loads(post_log.read_text(encoding="utf8").splitlines()[0]) == {"phase": "send-unknown"}
    assert len(post_log.read_text(encoding="utf8").splitlines()) == 1


if __name__ == "__main__":
    _child_run(sys.argv[2], sys.argv[1], sys.argv[3])
