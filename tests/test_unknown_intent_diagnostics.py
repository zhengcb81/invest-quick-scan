import json
import runpy

from unknown_intent_diagnostics import exception_cause_chain, write_child_diagnostic


def test_child_diagnostic_is_atomic_json_and_drops_request_material(tmp_path):
    destination = tmp_path / "diagnostics" / "send-unknown.json"
    write_child_diagnostic(
        destination,
        {
            "phase": "send-unknown",
            "execute_returned": False,
            "execute_exception_type": "SharedEngineInterrupted",
            "checkpoint_exists": True,
            "pending_intent_present": True,
            "pending_intent_kind": "model_step",
            "pending_receipt_present": False,
            "pending_receipt_outcome": "outcome_unknown",
            "pending_receipt_reason_code": "transport_outcome_uncertain",
            "pending_receipt_final_content_present": False,
            "pending_receipt_tool_calls_present": False,
            "wire_post_count": 1,
            "summary": {"runtime_summary_present": False, "new_model_http": 0},
            "execute_cause_chain": [
                {
                    "module": "builtins",
                    "class": "RuntimeError",
                    "stable_error_code": "offline_test_network_forbidden",
                    "frames": [{"path": "qa/src/example.py", "function": "send", "line": 12}],
                    "exception_message": "must not be persisted",
                }
            ],
            "prompt": "must not be persisted",
            "api_key": "must not be persisted",
        },
    )

    loaded = json.loads(destination.read_text(encoding="utf8"))
    assert loaded["wire_post_count"] == 1
    assert loaded["pending_intent_kind"] == "model_step"
    assert loaded["pending_receipt_outcome"] == "outcome_unknown"
    assert loaded["pending_receipt_reason_code"] == "transport_outcome_uncertain"
    assert loaded["pending_receipt_final_content_present"] is False
    assert loaded["pending_receipt_tool_calls_present"] is False
    assert loaded["summary"] == {"new_model_http": 0, "runtime_summary_present": False}
    assert loaded["execute_cause_chain"] == [
        {
            "module": "builtins",
            "class": "RuntimeError",
            "stable_error_code": "offline_test_network_forbidden",
            "frames": [{"path": "qa/src/example.py", "function": "send", "line": 12}],
        }
    ]
    assert "prompt" not in loaded and "api_key" not in loaded
    assert not destination.with_name(destination.name + ".tmp").exists()


def test_child_diagnostic_rejects_unstable_receipt_details(tmp_path):
    destination = tmp_path / "diagnostics" / "bad-receipt.json"
    write_child_diagnostic(
        destination,
        {
            "pending_receipt_outcome": "provider said secret-key-value",
            "pending_receipt_reason_code": "timeout: secret-key-value",
            "pending_receipt_final_content_present": "yes",
            "pending_receipt_tool_calls_present": 1,
        },
    )

    loaded = json.loads(destination.read_text(encoding="utf8"))
    assert "pending_receipt_outcome" not in loaded
    assert "pending_receipt_reason_code" not in loaded
    assert "pending_receipt_final_content_present" not in loaded
    assert "pending_receipt_tool_calls_present" not in loaded
    assert "secret-key-value" not in destination.read_text(encoding="utf8")


def test_shared_engine_interrupted_cause_has_only_stable_code_and_repo_frames(tmp_path):
    root = tmp_path / "qa"
    root.mkdir()
    script = root / "synthetic_runner.py"
    script.write_text(
        """
class SharedEngineInterrupted(Exception):
    pass

def execute():
    try:
        raise RuntimeError('offline_test_network_forbidden')
    except RuntimeError as cause:
        raise SharedEngineInterrupted('do not expose provider payload') from cause
""",
        encoding="utf8",
    )
    namespace = runpy.run_path(str(script))
    try:
        namespace["execute"]()
    except Exception as error:
        chain = exception_cause_chain(error, [("qa", root)])
    else:
        raise AssertionError("synthetic interruption was not raised")

    assert [entry["class"] for entry in chain] == ["SharedEngineInterrupted", "RuntimeError"]
    assert "stable_error_code" not in chain[0]
    assert chain[1]["stable_error_code"] == "offline_test_network_forbidden"
    assert any(frame["path"] == "qa/synthetic_runner.py" for entry in chain for frame in entry["frames"])
    assert "do not expose" not in json.dumps(chain)
