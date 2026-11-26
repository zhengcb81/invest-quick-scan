import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from iqs_scan.workbench.dashboard_locks import control_lock  # noqa: E402
from iqs_scan.workbench.dashboard_service import DashboardService  # noqa: E402


PREVIEW = "prepare_" + "a" * 32
PAYLOAD = {"preview_id": PREVIEW, "preview_token": "1" * 64}
JOB = "/api/product/prepare/jobs/prepjob_" + "a" * 32


def _wait_for(check):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        try:
            found = check()
        except PermissionError:
            found = None  # Windows can transiently share-deny the atomic record replacement.
        if found:
            return found
        time.sleep(0.01)
    raise AssertionError("the fixture did not reach the requested checkpoint")


class _Preparer:
    def __init__(self, state, mode):
        self.state = state
        self.mode = mode

    def validate_selection(self, payload):
        assert self.mode == "submit" and payload == PAYLOAD

    def apply(self, payload):
        assert self.mode == "submit" and payload == PAYLOAD
        with (self.state / "fixture-calls").open("a", encoding="utf-8") as stream:
            print("prepare", file=stream)
        _wait_for((self.state / "fixture-fail").exists)
        try:
            raise ValueError("fixture-raw-private-inner")
        except ValueError as cause:
            raise PermissionError(13, "fixture-raw-private-outer") from cause

    def preparation(self, preview):
        assert preview == PREVIEW
        return {"status": "in_progress"}


def _entry(mode, root):
    service = DashboardService(root, prepare_factory=lambda _: _Preparer(Path(root), mode))
    if mode == "submit":
        status, result = service.dispatch("POST", "/api/product/prepare/apply", PAYLOAD)
        print(json.dumps({"status": status, "result": result}), flush=True)
        while True:
            time.sleep(1)
    else:
        observations = [service.dispatch("GET", JOB) for _ in range(2)]
        attached = service.dispatch("POST", "/api/product/prepare/apply", PAYLOAD)
        print(json.dumps([*observations, attached]), flush=True)


def _subprocess(mode, root):
    env = {**os.environ, "RESEARCH_FEEDBACK_RUN_ID": f"fixture-{mode}",
           "RESEARCH_FEEDBACK_ATTEMPT_ID": f"fixture-attempt-{mode}", "PYTHONPATH": str(REPO / "scripts")}
    for key in ("RESEARCH_FEEDBACK_DIR", "RESEARCH_FEEDBACK_OUT"):
        env.pop(key, None)
    # run_path preserves the repository working directory for normal imports.
    args = [sys.executable, "-B", "-c", "import runpy,sys; runpy.run_path(sys.argv.pop(1),run_name='__main__')",
            str(Path(__file__).resolve()), mode, str(root)]
    return args, env


def _snapshot(state):
    return {path.relative_to(state): path.read_bytes() for path in state.rglob("*") if path.is_file()}


@pytest.mark.parametrize("scenario", ["retained", "retained_undelivered", "unconfirmed", "normal"])
def test_prepare_post_recovers_one_original_outcome_after_process_stop(tmp_path, scenario):
    state = Path(DashboardService(tmp_path).config["state_root"])
    args, env = _subprocess("submit", tmp_path)
    process = subprocess.Popen(args, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    diagnostic = None
    try:
        _wait_for((tmp_path / "fixture-calls").exists)
        submitted = json.loads(process.stdout.readline())
        assert submitted["status"] == 200 and not submitted["result"]["data"]["attached"]
        assert submitted["result"]["data"]["API_requests"] == 0

        if scenario == "retained_undelivered":
            (state / "observations").write_text("delivery unavailable", encoding="utf-8")

        def original_diagnostic():
            ready = list((state / "observations").glob("*.ready"))
            logs = list(state.rglob("runtime-failures.jsonl"))
            if (ready or scenario == "retained_undelivered") and logs:
                return json.loads(next((state / "diagnostics").glob("*.jsonl")).read_text(encoding="utf-8"))

        if scenario in {"retained", "retained_undelivered"}:
            with control_lock(state / "preparation-jobs" / "jobs.lock"):
                (tmp_path / "fixture-fail").touch()
                diagnostic = _wait_for(original_diagnostic)
                process.kill()
                process.wait(timeout=10)
        elif scenario == "normal":
            (tmp_path / "fixture-fail").touch()
            diagnostic = _wait_for(original_diagnostic)
            record = next((state / "preparation-jobs").glob("prepjob_*.json"))
            _wait_for(lambda: json.loads(record.read_text(encoding="utf-8"))["state"] == "needs_original_inspection")
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    before = _snapshot(state)
    if scenario != "normal":
        job = next(path for path in before if path.name.startswith("prepjob_") and path.suffix == ".json")
        assert json.loads(before[job])["state"] == "preparing"

    args, env = _subprocess("inspect", tmp_path)
    inspected = subprocess.run(args, env=env, cwd=REPO, capture_output=True, text=True, timeout=25, check=True)
    first, second, attached = json.loads(inspected.stdout)
    assert first[0] == second[0] == 200
    job = first[1]["data"]
    assert job == second[1]["data"]
    assert attached[0] == 200 and attached[1]["data"]["attached"]
    assert attached[1]["data"]["job"] == job and attached[1]["data"]["API_requests"] == 0
    assert job["state"] == "needs_original_inspection"
    assert job["model_dispatch_started"] is False

    if diagnostic:
        assert job["error_code"] == "preparation_interrupted"
        reference = job["failure_diagnostic"]["details_ref"]
        assert diagnostic["details_ref"] == reference
        assert job["failure_diagnostic"]["feedback_recorded"] is (scenario != "retained_undelivered")
        read = subprocess.run(
            [sys.executable, "-B", str(REPO / "scripts" / "iqs_feedback_owner.py"), "get-diagnostic",
             reference, "--state-root", str(state)], env=env, cwd=REPO, capture_output=True,
            text=True, timeout=25, check=True,
        )
        cold = json.loads(read.stdout)["diagnostic"]
        assert cold["observation"]["step_id"].split("/")[0] == "prepare.apply"
        assert cold["observation"]["run_id"] == "fixture-submit"
        assert {entry["type"] for entry in cold["chain"]} == {"PermissionError", "ValueError"}
        if scenario == "retained":
            trace = _cli("iqs_feedback_owner.py", ("get-run-trace", job["job_id"], job["session"],
                                                    "--state-root", state), env)
            assert trace.returncode == 0, trace.stderr
            timeline = json.loads(trace.stdout)["events"]
            assert timeline[0]["step_id"] == "prepare.job" and timeline[0]["state"] == "started"
            assert timeline[-1]["details_ref"] == reference
    else:
        assert job["error_code"] == "worker_state_unknown"
        assert "failure_diagnostic" not in job

    assert before == _snapshot(state)
    assert (tmp_path / "fixture-calls").read_text(encoding="utf-8").splitlines() == ["prepare"]
    assert b"fixture-raw-private" not in b"\n".join(before.values())


def _cli(script, args, env):
    return subprocess.run([sys.executable, "-B", str(REPO / "scripts" / script), *map(str, args)],
                          env=env, cwd=REPO, capture_output=True, text=True, timeout=25)


@pytest.mark.parametrize("scenario", ["absent", "invalid_arguments", "valid"])
def test_plan_cli_keeps_business_exit_and_original_runtime_trace(tmp_path, scenario):
    runs = tmp_path / "runs"
    state = runs / "dashboard-runtime"
    _, env = _subprocess("plan", tmp_path)
    env["IQS_FEEDBACK_RUNS_ROOT"] = str(runs)
    if scenario == "absent":
        plan_args = ("--plan-dir", tmp_path / "fixture-raw-private-plan", "validate")
    elif scenario == "invalid_arguments":
        plan_args = ("fixture-raw-private-option",)
    else:
        plan_args = ("--plan-dir", REPO / "docs" / "implementation", "validate")
    result = _cli("implementation_plan.py", plan_args, env)
    if scenario == "valid":
        assert result.returncode == 0 and not result.stderr
        data = json.loads(result.stdout)
        assert data["planning_valid"] and data["product_tests_executed"] is False
        assert not (state / "observations").exists()
    else:
        assert result.returncode == 2 and not result.stdout
        if scenario == "absent":
            assert result.stderr.startswith("Cannot read/validate implementation plan:")
        record, = (state / "diagnostics").glob("*.jsonl")
        failure = json.loads(record.read_text(encoding="utf-8"))
        assert failure["observation"]["refusal_code"] == (
            "plan_input_unavailable" if scenario == "absent" else "invalid_arguments")
        assert failure["observation"]["run_id"] == "fixture-plan"
        assert failure["observation"]["attempt_id"] == "fixture-attempt-plan"
        assert failure["feedback_recorded"]

    reply = _cli("iqs_feedback_owner.py", ("get-run-trace", "fixture-plan", "fixture-attempt-plan",
                                            "--state-root", state), env)
    assert reply.returncode == 0, reply.stderr
    trace = json.loads(reply.stdout)["events"]
    assert all(row["timestamp_utc"].endswith("Z") for row in trace)
    assert [(row["step_id"], row["state"]) for row in trace if row["state"] != "failed"] == (
        [("plan.cli", "started"), ("plan.load", "completed"), ("plan.validate", "completed"),
         ("plan.cli", "completed")] if scenario == "valid" else
        [("plan.cli", "started"), ("plan.cli", "refused")]
    )
    assert trace[-1]["elapsed_ms"] >= 0
    assert b"fixture-raw-private" not in b"\n".join(_snapshot(state).values())


def test_production_answer_adapter_keeps_process_import_paths(tmp_path, monkeypatch):
    from iqs_scan.execution import shared_company_engine as engine

    calls = []
    context, resources = object(), object()

    def owner_resources():
        calls.append("owner")
        return resources

    runtime = SimpleNamespace(original_scan_context=lambda: SimpleNamespace(observation_context=context),
                              original_semantic_resources=owner_resources)
    contract = {"company_doc": {"origin": "owner_public"}}
    monkeypatch.setattr(engine, "_task_contract", lambda task: contract)
    monkeypatch.setattr(engine, "_company_runtime", lambda services, task: runtime)
    monkeypatch.setattr(engine, "REPO_ROOT", tmp_path / "unrelated-checkout", raising=False)
    validator = SimpleNamespace(prompt_rules=object(), legacy_prompt_rules=object())

    def frozen(task, observed_context, *, semantic_resources):
        assert (task, observed_context, semantic_resources) == (contract, context, resources)
        calls.append("validator")
        return validator

    monkeypatch.setattr(engine, "_frozen_answer_semantics", frozen)
    original_paths = list(sys.path)
    monkeypatch.setattr(sys, "path", original_paths.copy())
    callback = engine._production_answer_semantics(object(), object())
    assert callback.base_semantic_validator is validator
    assert calls == ["owner", "validator"]
    assert sys.path == original_paths


def test_saved_scan_keeps_read_only_success_and_joinable_trace(tmp_path):
    _, env = _subprocess("scan", tmp_path)
    runs = tmp_path / "runs"
    env["IQS_FEEDBACK_RUNS_ROOT"] = str(runs)
    run = runs / "fixture-original-run"
    run.mkdir(parents=True)
    answers = {"bank": {"question_count": 1}, "meta": {"calls": 0, "searches": 0}, "answers": [{
        "question_id": "fixture-question", "status": "scored", "score": 7,
        "evidence": [{"url": "https://example.invalid/source"}],
    }]}
    (run / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
    (run / "run-log.json").write_text("[]", encoding="utf-8")
    (run / "index.html").write_text("<html></html>", encoding="utf-8")
    before = _snapshot(run)
    result = _cli("scan_result_check.py", ("--run", run), env)
    assert result.returncode == 0 and not result.stderr
    data = json.loads(result.stdout)
    assert (data["ok"], data["usable"], data["coverage"], data["scored"]) == (True, True, "complete", 1)
    assert before == _snapshot(run)

    state = runs / "dashboard-runtime"
    reply = _cli("iqs_feedback_owner.py", ("get-run-trace", "fixture-scan", "fixture-attempt-scan",
                                            "--state-root", state), env)
    assert reply.returncode == 0, reply.stderr
    trace = json.loads(reply.stdout)["events"]
    assert [(row["step_id"], row["state"]) for row in trace] == [
        ("scan.check", "started"), ("scan.inspect", "completed"), ("scan.check", "completed"),
    ]
    assert trace[-1]["elapsed_ms"] >= 0
    assert trace[1]["evidence_ref"].startswith("iqs:scan/runs/fixture-original-run@")
    assert not (state / "observations").exists()


def test_preparation_same_owner_worker_retains_native_job_attempt(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import child_feedback_environment, operation_scope, read_owned_operation_failure

    monkeypatch.setenv("RESEARCH_FEEDBACK_RUN_ID", "whole-audit-run")
    monkeypatch.setenv("RESEARCH_FEEDBACK_ATTEMPT_ID", "audit-attempt")
    for key in ("RESEARCH_FEEDBACK_DIR", "RESEARCH_FEEDBACK_OUT"):
        monkeypatch.delenv(key, raising=False)
    job, attempt = "prepjob_" + "b" * 32, "1" * 32
    state = tmp_path / "diagnostics"
    with operation_scope(job, attempt, recoverable=True):
        remote = child_feedback_environment()
        own_worker = child_feedback_environment(same_owner=True)
    assert not set(own_worker).difference(remote).intersection(os.environ)
    env = {**os.environ, **own_worker, "PYTHONUTF8": "1"}
    request = {"operation": "apply", "config": {"state_root": str(state), "prepare": {}},
               "payload": {"directory": str(tmp_path / "fixture-raw-private-candidate")}}
    command = [sys.executable, "-B", str(REPO / "scripts" / "dashboard_prepare.py"), "--worker"]
    result = subprocess.run(command, input=json.dumps(request), env=env, cwd=REPO, capture_output=True,
                            text=True, timeout=25)
    reply = json.loads(result.stdout)
    assert result.returncode == 2 and not reply["ok"]
    original = read_owned_operation_failure(state, job, attempt, "prepare.worker")
    assert original is not None
    assert original["details_ref"] == reply["error"]["details"]["failure_diagnostic"]["details_ref"]
    assert original["observation"]["run_id"] == "whole-audit-run"
    assert original["chain"][0]["type"] == "FileNotFoundError"
    assert b"fixture-raw-private" not in b"\n".join(_snapshot(state).values())


def test_initial_config_refusal_is_visible_before_any_owner_is_wired(tmp_path, monkeypatch):
    from iqs_scan.workbench.dashboard_service import ProductError

    config = tmp_path / "config.json"
    config.write_text('{"fixture-raw-private-unparsed"', encoding="utf-8")
    monkeypatch.setenv("RESEARCH_FEEDBACK_RUN_ID", "fixture-invalid-config")
    monkeypatch.setenv("RESEARCH_FEEDBACK_ATTEMPT_ID", "fixture-invalid-attempt")
    for key in ("RESEARCH_FEEDBACK_DIR", "RESEARCH_FEEDBACK_OUT"):
        monkeypatch.delenv(key, raising=False)

    def unexpected(_):
        pytest.fail("configuration refusal must not call a downstream owner")

    with pytest.raises(ProductError) as failed:
        DashboardService(tmp_path, config_path=config, prepare_factory=unexpected, execution_factory=unexpected)
    assert failed.value.code == "config_invalid_json"
    state = tmp_path / "runs" / "dashboard-runtime"
    record, = (state / "diagnostics").glob("*.jsonl")
    diagnostic = json.loads(record.read_text(encoding="utf-8"))
    assert diagnostic["observation"]["step_id"] == "dashboard.config"
    assert diagnostic["observation"]["refusal_code"] == "config_invalid_json"
    assert {cause["type"] for cause in diagnostic["chain"]} == {"ProductError", "JSONDecodeError"}
    assert b"fixture-raw-private" not in b"\n".join(_snapshot(state).values())


if __name__ == "__main__":
    _entry(*sys.argv[1:])
