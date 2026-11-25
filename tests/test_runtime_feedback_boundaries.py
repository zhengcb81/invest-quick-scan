"""Daily execution failures and native IQS F4 outboxes share the original run scope."""
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Event, Thread

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
                "get-diagnostic", ref], env)
    assert look.returncode == 0, look.stderr
    entry = json.loads(look.stdout)["diagnostic"]
    assert entry["observation"]["details_ref"] == ref
    assert not (tmp_path / "empty.sqlite").exists()
    log = run.parent / "dashboard-runtime" / "runtime-failures.jsonl"
    local, = (json.loads(line) for line in log.read_bytes().splitlines())
    assert local["run_id"] == failed[0]["run_id"]
    assert local["step_id"] == failed[0]["step_id"]
    assert local["chain"] == entry["chain"]
    assert local["timestamp_utc"].endswith("Z")


def test_local_log_records_failures_when_outbox_is_unavailable(tmp_path, monkeypatch, capsys):
    from iqs_scan.foundation.api import record_operation_failure

    sidecar = tmp_path / "blocked"
    sidecar.mkdir()
    monkeypatch.setenv("RESEARCH_FEEDBACK_OUT", str(sidecar))
    failure = ValueError("Bearer synthetic-secret-value")
    result = record_operation_failure(failure, "fixture.publish", directory=tmp_path,
                                      run_id="same-run", attempt_id="same-attempt")
    assert result["recorded"] and not result["feedback_recorded"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "tracking incomplete" in captured.err
    raw = (tmp_path / "runtime-failures.jsonl").read_text(encoding="utf8")
    assert "synthetic-secret-value" not in raw
    record = json.loads(raw)
    assert record["run_id"] == "same-run"
    assert record["chain"][0]["type"] == "ValueError"


def test_local_log_rotates_without_losing_concurrent_process_failures(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import record_operation_failure

    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    monkeypatch.delenv("RESEARCH_FEEDBACK_DIR", raising=False)
    monkeypatch.delenv("RESEARCH_FEEDBACK_RUN_ID", raising=False)
    monkeypatch.delenv("RESEARCH_FEEDBACK_ATTEMPT_ID", raising=False)
    root = tmp_path / "parallel"
    root.mkdir()
    logfile = root / "runtime-failures.jsonl"
    logfile.write_bytes(b"x" * (2 * 1024 * 1024 - 1) + b"\n")
    script = ("from iqs_scan.foundation.api import record_operation_failure; "
              "from pathlib import Path; import sys; "
              "record_operation_failure(ValueError('fixture'), 'fixture.worker', directory=Path(sys.argv[1]), "
              "run_id=sys.argv[2], attempt_id='one')")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
    processes = [subprocess.Popen([sys.executable, "-B", "-c", script, str(root), f"worker-{i}"],
                                  env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(4)]
    try:
        for process in processes:
            out, err = process.communicate(timeout=20)
            assert (process.returncode, out, err) == (0, b"", b"")
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    result = record_operation_failure(RuntimeError("fixture"), "fixture.worker", directory=root,
                                      run_id="parent", attempt_id="one")
    assert result["recorded"]
    assert logfile.with_suffix(".jsonl.1").stat().st_size == 2 * 1024 * 1024
    rows = [json.loads(line) for line in logfile.read_bytes().splitlines()]
    assert sorted(row["run_id"] for row in rows) == ["parent", "worker-0", "worker-1", "worker-2", "worker-3"]


def test_local_log_keeps_new_record_after_an_interrupted_line(tmp_path, monkeypatch):
    from iqs_scan.foundation.api import record_operation_failure

    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    monkeypatch.delenv("RESEARCH_FEEDBACK_DIR", raising=False)
    log = tmp_path / "runtime-failures.jsonl"
    log.write_bytes(b'{"previous":"incomplete')
    result = record_operation_failure(RuntimeError("next entry"), "fixture.recovered", directory=tmp_path)
    assert result["recorded"] and result["feedback_recorded"]
    interrupted, current = log.read_bytes().splitlines()
    assert interrupted == b'{"previous":"incomplete'
    assert json.loads(current)["chain"][0]["type"] == "RuntimeError"


def test_original_preparation_failure_survives_a_busy_job_control_lock(tmp_path, monkeypatch):
    from iqs_scan.workbench.dashboard_jobs import PreparationJobs
    from iqs_scan.workbench.dashboard_locks import control_lock

    diagnostics = tmp_path / "state"
    outbox = tmp_path / "outbox"
    monkeypatch.setenv("RESEARCH_FEEDBACK_DIR", str(outbox))
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)

    class Preparer:
        calls = 0

        def apply(self, payload):
            self.calls += 1
            raise PermissionError(13, "secret value")

    preparer = Preparer()
    jobs = PreparationJobs(preparer, tmp_path / "jobs", lambda result: pytest.fail("unexpected registration"),
                           diagnostic_root=diagnostics)
    record = {"job_id": "prepjob_" + "a" * 32, "session": "fixture-session", "state": "preparing"}
    with control_lock(jobs.state_root / "jobs.lock"):
        worker = Thread(target=jobs._run, args=(jobs.state_root / "original.json", record, {}))
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive()
    item, = read_owner_outbox(outbox)
    assert (item["step_id"], item["run_id"]) == ("prepare.apply", record["job_id"])
    saved = call("iqs_feedback_owner.py", ["get-diagnostic", item["details_ref"], "--state-root", diagnostics], os.environ)
    assert saved.returncode == 0
    assert json.loads(saved.stdout)["diagnostic"]["chain"][0]["type"] == "PermissionError"
    assert b"secret value" not in saved.stdout
    assert preparer.calls == 1 and not (jobs.state_root / "original.json").exists()


def test_stopped_batch_coordinator_failure_is_visible_after_worker_exits(tmp_path, monkeypatch):
    from iqs_scan.workbench.dashboard_batches import BatchGateway

    diagnostics = tmp_path / "state"
    outbox = tmp_path / "outbox"
    monkeypatch.setenv("RESEARCH_FEEDBACK_DIR", str(outbox))
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT", raising=False)
    gateway = BatchGateway(None, diagnostics)
    entered, finish = Event(), Event()
    steps = []

    def fail_step(batch_id):
        steps.append(batch_id)
        entered.set()
        assert finish.wait(timeout=5)
        raise OSError(13, "private error detail")

    monkeypatch.setattr(gateway, "_step", fail_step)
    gateway._launch_worker("fixture-batch")
    assert entered.wait(timeout=5)
    worker = gateway._threads["fixture-batch"]
    finish.set()
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert gateway._worker_errors["fixture-batch"]["code"] == "batch_coordinator_io_failed"
    item, = read_owner_outbox(outbox)
    assert (item["step_id"], item["run_id"]) == ("batch.coordinator", "fixture-batch")
    saved = call("iqs_feedback_owner.py", ["get-diagnostic", item["details_ref"], "--state-root", diagnostics], os.environ)
    assert saved.returncode == 0
    assert json.loads(saved.stdout)["diagnostic"]["chain"][0]["type"] == "PermissionError"
    assert b"private error detail" not in saved.stdout
    assert steps == ["fixture-batch"]


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


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "utf-32"])
def test_long_real_child_error_is_available_via_cold_log_pages(tmp_path, monkeypatch, encoding):
    from iqs_scan.workbench.dashboard_execution import ExecutionGateway

    monkeypatch.setenv("IQS_TEST_SECRET", "provider-secret-fixture-only")
    state = tmp_path / "state"
    run_id = "run-" + "2" * 32
    folder = state / run_id
    folder.mkdir(parents=True)
    record = {"run_id": run_id, "launch_attempt": 1, "process_state": "running", "launcher_state": "running",
              "log_path": str(folder / "process.log")}
    job_path = state / (run_id + ".json")
    job_path.write_text(json.dumps(record), encoding="utf8")
    gateway = ExecutionGateway({"state_root": str(state)})
    child_code = (
        "import os,sys; msg='x'*1070000+'\\n原因：原写入失败 '+os.environ['IQS_TEST_SECRET']+' password=unknown-synthetic-value Authorization: Bearer unknown-synthetic-bearer\\n';"
        "sys.stdout.buffer.write(msg.encode(sys.argv[1])); sys.exit(29)"
    )
    with subprocess.Popen([sys.executable, "-B", "-c", child_code, encoding], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT) as child:
        gateway._processes[run_id] = child
        gateway._finish(child, job_path, record)
    final = json.loads(job_path.read_bytes())
    assert final["exit_code"] == 29
    row = final["failure_diagnostic"]["observation"]
    assert row["evidence_ref"] == final["process_log_ref"]
    owner_args = ["get-process-log", row["evidence_ref"], "--state-root", state, "--tail-bytes", 120]
    page = call("iqs_feedback_owner.py", owner_args, os.environ.copy())
    assert page.returncode == 0, page.stderr
    view = json.loads(page.stdout)["log"]
    assert view["total_bytes"] > 1048576 and view["eof"] is True
    assert "原因：原写入失败 [REDACTED]" in view["text"]
    saved = (folder / "process.log").read_bytes()
    assert b"provider-secret-fixture-only" not in saved
    assert b"unknown-synthetic-value" not in saved and b"unknown-synthetic-bearer" not in saved
    start = view["offset"]
    restored = ""
    while len(restored.encode("utf8")) < view["total_bytes"] - start:
        part = call("iqs_feedback_owner.py", ["get-process-log", row["evidence_ref"], "--state-root", state,
                    "--offset", start + len(restored.encode("utf8")), "--limit", 57], os.environ.copy())
        assert part.returncode == 0, part.stderr
        restored += json.loads(part.stdout)["log"]["text"]
    assert restored == view["text"]


def test_redact_named_credentials_even_when_no_environment_variable_contains_them():
    from iqs_scan.foundation.api import redacted_output_lines

    lines = [
        "password=unconfigured-value https://example.invalid/?api_key=query-value&format=json\n",
        '{"access_token":"json-value","message":"keep me"}\n',
        "Authorization: Basic basic-value\n",
        "secret_key='phrase with blanks' stage=keep\n",
        "X-Api-Key: header-value\n",
        "https://user:pass@example.invalid/safe\n",
        "-----BEGIN PRIVATE KEY-----\nbase64-unconfigured\n-----END PRIVATE KEY-----\n",
    ]
    result = "".join(redacted_output_lines(iter(lines), ()))
    for value in ("unconfigured-value", "query-value", "json-value", "basic-value", "phrase with blanks",
                  "header-value", "user:pass", "base64-unconfigured"):
        assert value not in result
    assert "format=json" in result and "keep me" in result and "stage=keep" in result


def test_runs_root_cold_receipts_accept_current_and_older_owner_placement(tmp_path):
    import hashlib

    runs = tmp_path / "runs"
    native_run = runs / "scoped-input"
    native_run.mkdir(parents=True)
    sidecar = tmp_path / "sidecar.jsonl"
    sidecar.write_bytes(b'{"previous":')
    env = {**os.environ, "IQS_FEEDBACK_RUNS_ROOT": str(runs), "RESEARCH_FEEDBACK_OUT": str(sidecar)}
    rejected = call("scan_result_check.py", ["--run", native_run], env)
    assert rejected.returncode == 2
    damaged, kept = sidecar.read_bytes().splitlines()
    assert damaged == b'{"previous":'
    row = json.loads(kept)
    ref = row["details_ref"]
    prefix = ["--runs-root", runs, "--db", tmp_path / "owner.sqlite"]
    def get():
        inspected = call("iqs_feedback_owner.py", [*prefix, "get-diagnostic", ref], env)
        assert inspected.returncode == 0, inspected.stderr
        return json.loads(inspected.stdout)["diagnostic"]
    assert get()["observation"] == row
    receipt, = (runs / "dashboard-runtime" / "diagnostics").glob("*.jsonl")
    legacy = runs / "diagnostics" / receipt.name
    legacy.parent.mkdir()
    receipt.rename(legacy)
    assert get()["observation"] == row

    def fingerprint(value):
        encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    owner = "invest-quick-scan"
    fields = ("owner", "origin_owner", "run_id", "attempt_id", "step_id", "check_id")
    occurrence = fingerprint([row[field] for field in fields])
    key = fingerprint(["triage", owner, occurrence])
    payload = {"occurrence_id": occurrence, "observation": row}
    request = {"schema_version": "feedback-action/1", "owner": owner, "kind": "triage", "method": "submit",
               "action_id": key, "payload": payload, "request_digest": fingerprint([owner, "triage", key, payload])}
    args = [sys.executable, "-B", str(ROOT / "scripts/iqs_feedback_owner.py"), *map(str, prefix), "triage"]
    result = subprocess.run(args, input=json.dumps(request).encode(), env=env, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    triage = json.loads(result.stdout)["result"]
    assert triage["decision"] == "needs_evidence" and triage["issue_ref"] == row["issue_key"]
    assert triage["diagnostic_ref"] == ref
    cold = call("iqs_feedback_owner.py", [*prefix, "get-action", key], env)
    assert json.loads(cold.stdout)["receipt"]["result"] == triage


def test_two_direct_failures_of_same_named_run_keep_distinct_native_attempts(tmp_path):
    runs = tmp_path / "runs"
    run = runs / "same-run"
    run.mkdir(parents=True)
    out = tmp_path / "outbox"
    env = {**os.environ, "IQS_FEEDBACK_RUNS_ROOT": str(runs), "RESEARCH_FEEDBACK_DIR": str(out)}
    for key in ("RESEARCH_FEEDBACK_OUT", "RESEARCH_FEEDBACK_ATTEMPT_ID"):
        env.pop(key, None)
    first = call("scan_result_check.py", ["--run", run], env)
    for name, body in (("answers.json", "{"), ("run-log.json", "[]"), ("index.html", "<html></html>")):
        (run / name).write_text(body, encoding="utf8")
    second = call("scan_result_check.py", ["--run", run], env)
    assert first.returncode == second.returncode == 2
    events = read_owner_outbox(out)
    assert len(events) == 2
    assert len({row["attempt_id"] for row in events}) == 2
    assert len({row["actual"] for row in events}) == 2


def test_long_owner_outbox_can_be_reopened_without_starting_the_original_business(tmp_path):
    import shutil

    def physical(path):
        return Path("\\\\?\\" + str(path.absolute())) if os.name == "nt" else path

    base = tmp_path / "deep"
    nested = base.joinpath(*["data-root-segment-0123456789" for _ in range(14)])
    inbox, runs = nested / "observations", nested / "runs"
    actual = tmp_path / "original-run"
    actual.mkdir()
    try:
        physical(inbox).mkdir(parents=True)
        env = dict(os.environ, IQS_FEEDBACK_RUNS_ROOT=str(runs), RESEARCH_FEEDBACK_DIR=str(inbox))
        env.pop("RESEARCH_FEEDBACK_OUT", None)
        original = call("scan_result_check.py", ["--run", actual], env)
        assert original.returncode == 2
        row, = read_owner_outbox(physical(inbox))
        for _ in range(2):
            cold = call("iqs_feedback_owner.py", ["--runs-root", runs, "get-diagnostic", row["details_ref"]], env)
            assert cold.returncode == 0
            assert json.loads(cold.stdout)["diagnostic"]["observation"] == row
        assert not list(actual.iterdir())
    finally:
        if physical(base).exists():
            shutil.rmtree(physical(base))
