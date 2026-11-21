"""Daily execution failures and native IQS F4 outboxes share the original run scope."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def call(script, args, env):
    return subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts" / script), *map(str, args)],
        env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=20,
    )


def read_owner_outbox(folder):
    rows = []
    for ready in folder.glob("feedback-*.ready"):
        metadata = json.loads(ready.read_text(encoding="utf8"))
        raw = ready.with_suffix(".jsonl").read_text(encoding="utf8").splitlines()
        assert len(raw) == 1
        row = json.loads(raw[0])
        assert all(row[k] == metadata[k] for k in ("owner", "run_id", "attempt_id", "step_id"))
        rows.append(row)
    return rows


@pytest.mark.parametrize("scenario", ["missing", "corrupt", "execution"])
def test_scan_failure_uses_the_native_outbox_without_a_launcher(tmp_path, scenario):
    run = tmp_path / "runs" / "arbitrary-run"
    run.mkdir(parents=True)
    out = tmp_path / "outbox"
    env = {**os.environ, "RESEARCH_FEEDBACK_DIR": str(out), "IQS_FEEDBACK_RUNS_ROOT": str(run.parent)}
    env.pop("RESEARCH_FEEDBACK_OUT", None)
    if scenario != "missing":
        doc = {"bank": {"question_count": 1}, "meta": {"calls": 0, "searches": 1}, "answers": [
            {"question_id": "Q", "status": "insufficient_evidence", "problems": ["offline"]}]}
        (run / "answers.json").write_text("{" if scenario == "corrupt" else json.dumps(doc))
        (run / "run-log.json").write_text("[]")
        (run / "index.html").write_text("")
    result = call("scan_result_check.py", ["--run", run], env)
    assert result.returncode != 0
    rows = read_owner_outbox(out)
    failed = [r for r in rows if r["check_id"] == "operation-outcome"]
    assert len(failed) == 1 and failed[0]["disposition"] == "deviation"
    assert failed[0]["details_ref"].startswith("iqs:diagnostic/")
    ref = failed[0]["details_ref"]
    look = call("iqs_feedback_owner.py", ["--db", tmp_path / "empty.sqlite", "--runs-root", run.parent,
                "get-diagnostic", ref, "--state-root", run.parent], env)
    assert look.returncode == 0, look.stderr
    entry = json.loads(look.stdout)["diagnostic"]
    assert entry["observation"]["details_ref"] == ref
    assert not (tmp_path / "empty.sqlite").exists()


def test_configured_sidecar_and_default_job_restart_report_once(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import record_operation_failure
    monkeypatch.delenv("RESEARCH_FEEDBACK_DIR", raising=False)
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    marker = tmp_path / "input-must-stay-private"
    marker.write_text("never log this value")
    diagnostic = record_operation_failure(PermissionError(13, str(marker)), "fixture.read",
                                          directory=tmp_path, run_id="run-one", attempt_id="attempt-one")
    assert diagnostic["recorded"]
    decision = read_owner_outbox(tmp_path / "observations")
    assert len(decision) == 1 and decision[0]["run_id"] == "run-one"
    ready = next((tmp_path / "observations").glob("*.ready"))
    ready.unlink()   # native public intake has consumed the committed marker
    record_operation_failure(PermissionError(13, str(marker)), "fixture.read",
                             directory=tmp_path, run_id="run-one", attempt_id="attempt-one")
    assert not list((tmp_path / "observations").glob("*.ready"))
    assert str(marker) not in next((tmp_path / "diagnostics").glob("*.jsonl")).read_text()


def test_hostile_exception_cannot_replace_a_business_failure(tmp_path):
    from iqs_scan.foundation.api import record_operation_failure

    class OpaqueError(RuntimeError):
        def __getattribute__(self, key):
            if key in {"__dict__", "__cause__", "__context__", "__traceback__"}:
                raise RuntimeError("introspection refused")
            return super().__getattribute__(key)

    try:
        try:
            raise OSError("private input")
        except OSError as exc:
            raise OpaqueError("private input") from exc
    except OpaqueError as exc:
        record = record_operation_failure(exc, "fixture", directory=tmp_path)
    assert record["recorded"] is True
    assert "OpaqueError" in json.dumps(record) and "OSError" in json.dumps(record)
    assert "private input" not in json.dumps(record)


def test_public_republish_after_sink_recovery_resolves_original_without_business_work(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import record_operation_failure
    out = tmp_path / "bad-outbox"
    out.write_text("occupied", encoding="utf8")
    monkeypatch.setenv("RESEARCH_FEEDBACK_DIR", str(out))
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    initial = record_operation_failure(PermissionError(13, "private-value"), "fixture.read",
                                       directory=tmp_path, run_id="r", attempt_id="a")
    assert initial["recorded"] and not initial["feedback_recorded"]
    out.unlink()
    args = ["republish-diagnostic", initial["details_ref"], "--state-root", tmp_path]
    for _ in range(2):
        republished = call("iqs_feedback_owner.py", args, os.environ.copy())
        assert republished.returncode == 0, republished.stderr
    rows = read_owner_outbox(out)
    assert len(rows) == 1
    assert rows[0]["details_ref"] == initial["details_ref"] and rows[0]["attempt_id"] == "a"


def test_plain_cli_argument_refusal_is_observed_without_raw_argv(tmp_path):
    out = tmp_path / "observation.jsonl"
    env = {**os.environ, "RESEARCH_FEEDBACK_OUT": str(out), "IQS_FEEDBACK_RUNS_ROOT": str(tmp_path)}
    result = call("scan_result_check.py", ["--unknown-synthetic-do-not-log"], env)
    assert result.returncode == 2
    row = json.loads(out.read_text(encoding="utf8"))
    assert row["refusal_code"] == "invalid_arguments"
    assert "do-not-log" not in json.dumps(row)


def test_bootstrap_diagnostics_do_not_require_the_business_schema_stack():
    program = "import sys; sys.path.insert(0,'scripts'); from iqs_scan.foundation.api import record_operation_failure"
    outcome = subprocess.run([sys.executable, "-S", "-B", "-c", program], cwd=ROOT, capture_output=True)
    assert outcome.returncode == 0, outcome.stderr


def test_all_different_execution_errors_are_not_a_successful_bank(tmp_path):
    from iqs_scan.tools.scan_result_check import inspect_run

    answers = [{"question_id": f"Q{i}", "status": "insufficient_evidence", "problems": [failure]}
               for i, failure in enumerate(["timeout: operator", "receipt_missing: operator"])]
    record = {"bank": {"question_count": 2}, "meta": {"calls": 2}, "answers": answers}
    (tmp_path / "answers.json").write_text(json.dumps(record), encoding="utf8")
    (tmp_path / "run-log.json").write_text("[]", encoding="utf8")
    (tmp_path / "index.html").write_text("", encoding="utf8")
    report = inspect_run(tmp_path).report
    assert report["coverage"] == "complete"
    assert report["ok"] is False and report["usable"] is False


def test_independent_outbox_can_report_when_native_diagnostic_store_is_unwritable(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import record_operation_failure

    out = tmp_path / "out"
    monkeypatch.setenv("RESEARCH_FEEDBACK_DIR", str(out))
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    (tmp_path / "diagnostics").write_text("occupied")
    result = record_operation_failure(OSError("private cause"), "offline.failure", directory=tmp_path,
                                      evidence_ref="iqs:scan/runs/test")
    assert result["recorded"] is False and result["feedback_recorded"] is True
    row, = read_owner_outbox(out)
    assert "details_ref" not in row
    assert row["evidence_ref"] == "iqs:scan/runs/test"
