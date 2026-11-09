"""OWNERPKG-INVEST-QUICK-SCAN-01: public job façade semantics.

Every dispatch in these tests goes through fakes that RECORD the call, so the
tests double as the evidence that the façade only *delegates* to the existing
execution chain (never wraps thin_scan, never fabricates bundles or budgets).
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dashboard_job_facade import (OwnerJobError, OwnerJobFacade, RECOVERY_DURABLE,
                                  RECOVERY_UNAVAILABLE)

JOBVIEW_FIELDS = {"command_id", "owner", "owner_job_id", "status", "status_known",
                  "allowed_actions", "started_at", "updated_at", "cost", "cost_state",
                  "error", "recovery_capability"}


def command_request(command_id="cmd-1", idempotency_key="idem-1", entity_id="ENT_A", **overrides):
    request = {
        "command_id": command_id,
        "idempotency_key": idempotency_key,
        "owner": "invest-quick-scan",
        "company": {"entity_id": entity_id, "listing_id": None, "analysis_subject_id": None,
                    "resolution_status": "resolved", "display_name": "Company A"},
        "requested_action": "run_scan",
        "explicit_scope": {"scope_version": "1", "scan_kind": "formal",
                           "universe_id": None, "questionnaire_version": None},
        "as_of": None,
        "limits_ref": None,
    }
    for key, value in overrides.items():
        if key == "company":
            request["company"].update(value)
        elif key == "scope":
            request["explicit_scope"].update(value)
        else:
            request[key] = value
    return request


class FakeExecution:
    def __init__(self):
        self.start_calls = []
        self.control_calls = []
        self.runs = {}
        self._counter = 0

    def launch(self, run_id, record):
        base = {"run_id": run_id, "bundle_id": "b1", "bundle_fingerprint": "f" * 64,
                "entity_id": record.get("entity_id", "ENT_A"), "started_at": "2026-11-07T00:00:00Z"}
        base.update(record)
        self.runs[run_id] = base
        return base

    def start(self, payload):
        self.start_calls.append(dict(payload))
        self._counter += 1
        run_id = "run-" + f"{self._counter:032x}"
        record = self.launch(run_id, {"entity_id": payload.get("entity_id"),
                                      "process_state": "running", "launcher_state": "running"})
        return {"status": "started", "run": record, "process_started": True,
                "paid_dispatch_started": None}

    def resolve_job_bundle(self, *, bundle_id, entity_id, listing_id, analysis_subject_id, as_of):
        assert bundle_id is None or bundle_id == "b1"
        return {"bundle_id": "b1", "entity_id": entity_id, "bundle_fingerprint": "f" * 64}

    def control(self, run_id, action):
        self.control_calls.append((run_id, action))
        if run_id not in self.runs:
            from dashboard_errors import DashboardExecutionError
            raise DashboardExecutionError("run_unknown", "没有该启动记录", 404)
        if action == "inspect":
            return {"run": self.runs[run_id], "preview": {"inspection_sha256": "a" * 64,
                "inspection": {"work_items": self.inspect_items(run_id)}}}
        if action == "resume":
            self.runs[run_id]["process_state"] = "running"
            self.runs[run_id]["launcher_state"] = "running"
            return {"run": self.runs[run_id], "state": "running", "process_started": True,
                    "paid_dispatch_started": None}
        raise AssertionError(f"unexpected action {action}")

    def inspect_items(self, run_id):
        return [{"question_id": "q1", "status": "result_ready"},
                {"question_id": "q2", "status": "delivered"}]

    def tasks(self, *, bundle_ids=None, run_ids=None, inspect_owner=True, limit=50, offset=0):
        rows = [dict(row, run_id=run_id) for run_id, row in sorted(self.runs.items())
                if (run_ids is None or run_id in run_ids)
                and (bundle_ids is None or row["bundle_id"] in bundle_ids)]
        return {"tasks": rows[offset:offset + limit], "total": len(rows), "offset": offset,
                "limit": limit,
                "next_offset": offset + limit if offset + limit < len(rows) else None,
                "API_requests": 0}


class FakePrepJobs:
    def __init__(self):
        self.jobs = {}
        self.control_calls = []

    def get(self, job_id):
        if job_id not in self.jobs:
            class Unknown(Exception):
                code = "preparation_job_unknown"
                status = 404
            raise Unknown()
        return dict(self.jobs[job_id])

    def list(self):
        return {"jobs": [dict(row) for row in self.jobs.values()], "total": len(self.jobs),
                "API_requests": 0}


class FakeDeliveryJobs:
    def __init__(self):
        self.jobs = {}
        self.control_calls = []

    def get(self, job_id):
        if job_id not in self.jobs:
            class Unknown(Exception):
                code = "delivery_job_unknown"
                status = 404
            raise Unknown()
        return dict(self.jobs[job_id])

    def list(self):
        return {"jobs": [dict(row) for row in self.jobs.values()], "total": len(self.jobs),
                "API_requests": 0}

    def control(self, job_id, action):
        self.control_calls.append((job_id, action))
        self.jobs[job_id]["state"] = "running"
        return dict(self.jobs[job_id])


class FakeBatches:
    def __init__(self):
        self.batches = {}
        self.control_calls = []

    def get(self, batch_id):
        if batch_id not in self.batches:
            class Unknown(Exception):
                code = "batch_unknown"
                status = 404
            raise Unknown()
        return dict(self.batches[batch_id])

    def list(self, limit=50, offset=0):
        rows = list(self.batches.values())[offset:offset + limit]
        return {"batches": [dict(row) for row in rows], "total": len(self.batches),
                "limit": limit, "offset": offset, "API_requests": 0}

    def control(self, batch_id, action):
        self.control_calls.append((batch_id, action))
        self.batches[batch_id]["state"] = "running"
        return {"batch": dict(self.batches[batch_id])}


@pytest.fixture
def gates():
    return {"execution": FakeExecution(), "prep": FakePrepJobs(),
            "delivery": FakeDeliveryJobs(), "batches": FakeBatches()}


def make_facade(tmp_path, gates, universe="default"):
    return OwnerJobFacade(tmp_path / "owner-jobs",
        execution=lambda: gates["execution"],
        preparation_jobs=lambda: gates["prep"],
        delivery_jobs=lambda: gates["delivery"],
        batches=lambda: gates["batches"],
        universe_id=universe)


def submit(facade, request=None, **kwargs):
    return facade.submit_run_scan({"command_request": request or command_request(**kwargs)})


def test_explicit_bundle_is_bound_before_launch(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    request = command_request(scope={"bundle_id": "b1"}, company={
        "listing_id": "LST_1", "analysis_subject_id": "ASJ_1"}, as_of="2026-11-07")
    resolve = gates["execution"].resolve_job_bundle
    seen = []
    def check_scope(**scope):
        seen.append(scope)
        return resolve(**scope)
    gates["execution"].resolve_job_bundle = check_scope
    result = submit(facade, request)
    assert seen == [{"bundle_id": "b1", "entity_id": "ENT_A", "listing_id": "LST_1",
                     "analysis_subject_id": "ASJ_1", "as_of": "2026-11-07"}]
    assert result["command"]["submission"]["bundle_id"] == "b1"
    assert gates["execution"].start_calls == [{
        "bundle_id": "b1", "entity_id": "ENT_A", "bundle_fingerprint": "f" * 64}]


def test_ambiguous_dispatch_cold_replay_only_adopts_original_run(tmp_path, gates):
    execution = gates["execution"]
    start = execution.start
    def lost_reply(payload):
        start(payload)
        raise OSError("owner reply lost after durable start")
    execution.start = lost_reply
    facade = make_facade(tmp_path, gates)
    assert submit(facade)["job_view"]["status"] == "unknown"
    assert facade.get_command("cmd-1")["job_view"]["owner_job_id"] == next(iter(execution.runs))
    replay = submit(make_facade(tmp_path, gates))
    assert replay["job_view"]["owner_job_id"] == next(iter(execution.runs))
    assert len(execution.start_calls) == 1


def test_ambiguous_dispatch_without_reference_stays_unknown(tmp_path, gates):
    execution = gates["execution"]
    calls = []
    def disconnected(payload):
        calls.append(payload)
        raise OSError("transport unavailable")
    execution.start = disconnected
    assert submit(make_facade(tmp_path, gates))["job_view"]["status"] == "unknown"
    assert submit(make_facade(tmp_path, gates))["job_view"]["status"] == "unknown"
    assert len(calls) == 1


def test_different_job_can_reconcile_while_a_submission_waits(tmp_path, gates):
    import threading
    facade = make_facade(tmp_path, gates)
    execution = gates["execution"]
    other_run = "run-" + "b" * 32
    execution.launch(other_run, {"process_state": "process_exited", "launcher_state": "running"})
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    start = execution.start
    def slow_start(payload):
        entered.set()
        assert release.wait(5)
        return start(payload)
    execution.start = slow_start
    launched = threading.Thread(target=lambda: submit(facade), daemon=True)
    projected = {}
    def reconcile():
        projected.update(facade.act(other_run, {"action": "reconcile", "idempotency_key": "other"}))
        finished.set()
    checked = threading.Thread(target=reconcile, daemon=True)
    launched.start()
    assert entered.wait(2)
    try:
        checked.start()
        assert finished.wait(1)
        assert projected["job_view"]["status"] == "succeeded"
    finally:
        release.set()
        launched.join(5)
        checked.join(5)


def test_reconcile_observation_expires_when_same_run_starts_another_attempt(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    run_id = submit(facade)["job_view"]["owner_job_id"]
    native = gates["execution"].runs[run_id]
    native.update(process_state="process_exited", launch_attempt=1)
    result = facade.act(run_id, {"action": "reconcile", "idempotency_key": "first-exit"})
    assert result["job_view"]["status"] == "succeeded"
    native.update(launch_attempt=2)
    assert facade.get_status(run_id)["job_view"]["status"] == "unknown"


def test_corrupt_action_record_does_not_replay_native_action(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    run_id = submit(facade)["job_view"]["owner_job_id"]
    request = {"action": "reconcile", "idempotency_key": "inspection"}
    facade.act(run_id, request)
    action = next((tmp_path / "owner-jobs" / "actions" / run_id).glob("*.json"))
    action.write_text("{}", encoding="utf-8")
    with pytest.raises(OwnerJobError) as caught:
        facade.act(run_id, request)
    assert caught.value.code == "action_record_unavailable"
    assert gates["execution"].control_calls == [(run_id, "inspect")]


# --------------------------------------------------------------- G-m8-IQS-01

def test_submit_walks_existing_chain_and_binds_run(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    result = submit(facade)
    # The original gateway resolves and launches the same frozen registration.
    assert gates["execution"].start_calls == [{
        "bundle_id": "b1", "entity_id": "ENT_A", "bundle_fingerprint": "f" * 64}]
    assert result["attached"] is False
    run_id = result["command"]["owner_job_id"]
    assert run_id.startswith("run-") and len(run_id) == 36
    view = result["job_view"]
    assert set(view) == JOBVIEW_FIELDS
    assert view["owner_job_id"] == run_id
    assert view["status"] == "running" and view["status_known"] is True
    # paid_dispatch_started is recorded verbatim as None: cost stays unknown.
    assert result["command"]["submission"]["paid_dispatch_started"] is None
    assert result["command"]["submission"]["work_completion_authoritative"] is False
    assert view["cost_state"] == "unknown" and view["cost"] is None
    assert view["recovery_capability"] == RECOVERY_DURABLE


def test_submit_is_idempotent_same_key_same_job_no_second_billing(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    first = submit(facade, command_id="cmd-1", idempotency_key="idem-X")
    second = submit(facade, command_id="cmd-1", idempotency_key="idem-X")
    assert gates["execution"].start_calls and len(gates["execution"].start_calls) == 1
    assert second["attached"] is True
    assert second["command"]["owner_job_id"] == first["command"]["owner_job_id"]
    assert second["job_view"]["owner_job_id"] == first["job_view"]["owner_job_id"]


def test_crash_window_resubmit_binds_same_run_without_double_start(tmp_path, gates):
    """Intent survives a crash before start returned; replay attaches, never re-runs a
    second process (the native start is bundle-level attach)."""
    facade = make_facade(tmp_path, gates)
    # Simulate: intent written, process died before start() returned a binding.
    body = {"command_request": command_request(command_id="cmd-crash", idempotency_key="idem-C")}
    facade._validate_command_request(body["command_request"])
    from dashboard_job_facade import PROTOCOL, _now
    record = {"protocol": PROTOCOL, "command_id": "cmd-crash",
              "idempotency_key": "idem-C", "kind": "run_scan", "owner_job_id": None,
              "owner_kind": None, "entity_id": "ENT_A", "company": body["command_request"]["company"],
              "scan_scope": body["command_request"]["explicit_scope"], "as_of": None,
              "limits_ref": None, "limits_target": "bundle.spend_authorization",
              "return_to": None, "state": "submitting", "created_at": _now(),
              "updated_at": _now(), "submission": None, "error": None}
    facade._save_command(record)
    facade._bind_idempotency("idem-C", "cmd-crash")
    result = facade.submit_run_scan(body)
    # The replay re-drives the recorded intent once and binds the run.
    assert result["attached"] is True
    assert gates["execution"].start_calls and result["command"]["owner_job_id"].startswith("run-")
    # The rebound command still answers the original key with the same job id.
    again = facade.submit_run_scan(body)
    assert again["attached"] is True
    assert again["command"]["owner_job_id"] == result["command"]["owner_job_id"]


def test_command_read_recovers_reference_after_process_exit_without_resubmission(tmp_path, gates, monkeypatch):
    gateway = gates['execution']
    native_start = gateway.start

    def crashed_after_start(payload):
        native_start(payload)
        raise SystemExit(1)

    monkeypatch.setattr(gateway, 'start', crashed_after_start)
    with pytest.raises(SystemExit):
        submit(make_facade(tmp_path, gates))
    reopened = make_facade(tmp_path, gates)
    receipt = reopened.get_command('cmd-1')
    assert receipt['job_view']['owner_job_id'] == next(iter(gateway.runs))
    assert len(gateway.start_calls) == 1


def test_owner_refusal_records_durable_refusal_and_unavailable_recovery(tmp_path, gates):
    from dashboard_errors import DashboardExecutionError
    def refuse(payload):
        raise DashboardExecutionError("execution_not_ready", "执行前置未满足", 409,
                                      {"bundle_id": "b1"}, prelaunch_not_started=True)
    gates["execution"].start = refuse
    facade = make_facade(tmp_path, gates)
    with pytest.raises(OwnerJobError) as caught:
        submit(facade, command_id="cmd-ref", idempotency_key="idem-R")
    assert caught.value.code == "submission_refused"
    assert caught.value.details["refusal_code"] == "execution_not_ready"
    # The refusal is durable and projects honestly: no job, nothing dispatched.
    fetched = facade.get_command("cmd-ref")
    view = fetched["job_view"]
    assert view["status"] == "failed" and view["status_known"] is True
    assert view["owner_job_id"] is None
    assert view["recovery_capability"] == RECOVERY_UNAVAILABLE
    assert view["allowed_actions"] == []
    assert view["error"]["code"] == "execution_not_ready"
    assert view["cost_state"] == "not_applicable"
    # Same key replays the same refusal; it never silently re-launches.
    gates["execution"].start = lambda payload: (_ for _ in ()).throw(AssertionError("must not re-dispatch"))
    replay = submit(facade, command_id="cmd-ref", idempotency_key="idem-R")
    assert replay["attached"] is True and replay["command"]["state"] == "refused"


def test_draft_scope_is_never_exposable(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    with pytest.raises(OwnerJobError) as caught:
        submit(facade, scope={"scan_kind": "draft"})
    assert caught.value.code == "draft_scan_not_exposable"
    assert gates["execution"].start_calls == []
    # 红线1 counterexample: the façade must not import, shell out to or wrap
    # the draft CLI in any way (docstring mentions are documentation only).
    import ast
    module = sys.modules["dashboard_job_facade"]
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all("thin_scan" not in alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert "thin_scan" not in (node.module or "")
        elif isinstance(node, (ast.Attribute, ast.Name)):
            name = getattr(node, "attr", None) or getattr(node, "id", None)
            assert name != "thin_scan"


@pytest.mark.parametrize("body_kwargs,code", [
    ({"scope": {"scan_kind": "formal", "universe_id": "other"}}, "universe_mismatch"),
    ({"scope": {"questionnaire_version": "v9"}}, "questionnaire_version_unverifiable"),
    ({"company": {"resolution_status": "ambiguous"}}, "company_unresolved"),
    ({"entity_id": "../evil"}, "company_invalid"),
])
def test_scope_and_identity_gates(tmp_path, gates, body_kwargs, code):
    facade = make_facade(tmp_path, gates, universe="default")
    overrides = dict(body_kwargs)
    if "scope" in overrides:
        overrides = {"scope": {**overrides["scope"]}}
    with pytest.raises(OwnerJobError) as caught:
        submit(facade, **overrides)
    assert caught.value.code == code
    assert gates["execution"].start_calls == []


def test_limits_ref_must_name_a_deployed_key(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    with pytest.raises(OwnerJobError) as caught:
        submit(facade, limits_ref="made-up-budget")
    assert caught.value.code == "limits_ref_unknown"
    ok = submit(facade, command_id="cmd-2", idempotency_key="idem-2",
                limits_ref="iqs.bundle.spend_authorization")
    assert ok["command"]["limits_target"] == "bundle.spend_authorization"


def test_return_to_whitelist_binding(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    for key, idem in (("https://evil.example/#/results", "idem-b1"),
                      ("#/company/OTHER/results", "idem-b2")):
        with pytest.raises(OwnerJobError) as caught:
            facade.submit_run_scan({"command_request": command_request(command_id="cmd-bad",
                idempotency_key=idem), "return_to": key})
        assert caught.value.code == "return_to_invalid"
    ok = facade.submit_run_scan({"command_request": command_request(command_id="cmd-ok",
        idempotency_key="idem-ok"), "return_to": "#/company/ENT_A/quickscan"})
    assert ok["command"]["return_to"] == "#/company/ENT_A/quickscan"


# --------------------------------------------------------------- G-m8-IQS-02

def test_run_projection_states(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    run_id = gates["execution"].runs and next(iter(gates["execution"].runs))
    # running → known
    view, annotation = facade.project_job(run_id)
    assert (view["status"], view["status_known"]) == ("running", True)
    # local exit is NOT completion → unknown, only reconcile
    gates["execution"].runs[run_id].update(process_state="process_exited",
        launcher_state="paused", finished_at="2026-11-07T01:00:00Z")
    view, _ = facade.project_job(run_id)
    assert (view["status"], view["status_known"], view["allowed_actions"]) == \
        ("unknown", False, ["reconcile"])
    # retired with a validated all-terminal proof → succeeded without I/O
    gates["execution"].runs[run_id].update(process_state="observed_stopped",
        launcher_state="retired",
        retirement={"work_status_counts": {"result_ready": 1, "delivered": 1}})
    view, _ = facade.project_job(run_id)
    assert (view["status"], view["status_known"]) == ("succeeded", True)
    assert view["allowed_actions"] == []
    # retired with pending work → failed
    gates["execution"].runs[run_id]["retirement"] = {"work_status_counts": {"result_ready": 1, "pending": 1}}
    view, _ = facade.project_job(run_id)
    assert (view["status"], view["status_known"]) == ("failed", True)


def test_run_failed_after_inspection_resumable(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    run_id = next(iter(gates["execution"].runs))
    gates["execution"].runs[run_id].update(process_state="process_exited",
        launcher_state="paused")
    gates["execution"].inspect_items = lambda run_id: [
        {"question_id": "q1", "status": "result_ready"},
        {"question_id": "q2", "status": "pending"}]
    result = facade.act(run_id, {"action": "reconcile", "idempotency_key": "rec-1"})
    assert result["action_result"]["outcome"] == "inspected"
    view = result["job_view"]
    assert view["status"] == "failed" and view["status_known"] is True
    assert view["allowed_actions"] == ["resume", "reconcile"]
    view, _ = facade.project_job(run_id)
    assert view["status"] == "failed"  # cached observation persists across reads


def test_prepjob_delivery_batch_projections(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    gates["prep"].jobs["prepjob_" + "a" * 32] = {
        "job_id": "prepjob_" + "a" * 32, "state": "registered", "created_at": "2026-11-07T00:00:00Z",
        "model_dispatch_started": False}
    gates["prep"].jobs["prepjob_" + "b" * 32] = {
        "job_id": "prepjob_" + "b" * 32, "state": "needs_original_inspection",
        "created_at": "2026-11-07T00:00:00Z"}
    gates["prep"].jobs["prepjob_" + "c" * 32] = {
        "job_id": "prepjob_" + "c" * 32, "state": "abandoned", "created_at": "2026-11-07T00:00:00Z"}
    gates["delivery"].jobs["deliveryjob_" + "a" * 32] = {
        "job_id": "deliveryjob_" + "a" * 32, "state": "completed", "created_at": "2026-11-07T00:00:00Z",
        "entries": [{"bundle_id": "b", "state": "delivered"}]}
    gates["delivery"].jobs["deliveryjob_" + "b" * 32] = {
        "job_id": "deliveryjob_" + "b" * 32, "state": "partial", "created_at": "2026-11-07T00:00:00Z",
        "entries": [{"bundle_id": "b", "state": "pending", "error_code": "ack_missing"}]}
    gates["delivery"].jobs["deliveryjob_" + "c" * 32] = {
        "job_id": "deliveryjob_" + "c" * 32, "state": "running", "session": "gone",
        "created_at": "2026-11-07T00:00:00Z", "entries": [{"bundle_id": "b", "state": "importing"}]}
    gates["batches"].batches["batch-" + "a" * 32] = {
        "batch_id": "batch-" + "a" * 32, "state": "owner_ready", "created_at": "2026-11-07T00:00:00Z"}
    gates["batches"].batches["batch-" + "b" * 32] = {
        "batch_id": "batch-" + "b" * 32, "state": "paused", "created_at": "2026-11-07T00:00:00Z"}
    gates["batches"].batches["batch-" + "c" * 32] = {
        "batch_id": "batch-" + "c" * 32, "state": "blocked", "created_at": "2026-11-07T00:00:00Z",
        "entries": [{"blocked_reasons": ["original_process_unknown"]}]}
    view, _ = facade.project_job("prepjob_" + "a" * 32)
    assert (view["status"], view["cost_state"], view["allowed_actions"]) == ("succeeded", "not_applicable", [])
    view, _ = facade.project_job("prepjob_" + "b" * 32)
    assert (view["status"], view["status_known"], view["allowed_actions"]) == ("unknown", False, ["reconcile"])
    view, _ = facade.project_job("prepjob_" + "c" * 32)
    assert (view["status"], view["status_known"]) == ("cancelled", True)
    view, _ = facade.project_job("deliveryjob_" + "a" * 32)
    assert (view["status"], view["cost_state"]) == ("succeeded", "not_applicable")
    view, _ = facade.project_job("deliveryjob_" + "b" * 32)
    assert (view["status"], view["allowed_actions"]) == ("failed", ["resume", "reconcile"])
    view, annotation = facade.project_job("deliveryjob_" + "c" * 32)
    # a dead-session delivery is unknown until the native get() marks it; the
    # fake has no restart detection, so it stays running-known in this fake.
    assert view["status"] in {"running", "unknown"}
    view, _ = facade.project_job("batch-" + "a" * 32)
    assert (view["status"], view["cost_state"]) == ("succeeded", "unknown")
    view, _ = facade.project_job("batch-" + "b" * 32)
    assert (view["status"], view["allowed_actions"]) == ("queued", ["resume", "reconcile"])
    view, _ = facade.project_job("batch-" + "c" * 32)
    assert (view["status"], view["status_known"], view["allowed_actions"]) == ("unknown", False, ["reconcile"])


def test_missing_native_reference_is_unknown_never_empty_history(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    view, annotation = facade.project_job("run-" + "f" * 32)
    assert (view["status"], view["status_known"], view["allowed_actions"]) == \
        ("unknown", False, ["reconcile"])
    assert "不存在" in annotation["notice"]


# --------------------------------------------------------------- G-m8-IQS-03

def test_unknown_status_allows_only_reconcile(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    run_id = "run-" + "e" * 32
    gates["execution"].launch(run_id, {"process_state": "needs_original_inspection",
                                       "launcher_state": "running"})
    actions = facade.allowed_actions(run_id)
    assert actions["allowed_actions"] == ["reconcile"]
    assert actions["status_known"] is False
    assert actions["mapping_version"] == "iqs.owner_job_actions/1.0.0"


def test_cancel_and_retry_are_always_refused_with_authoritative_reason(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    run_id = next(iter(gates["execution"].runs))
    for action, code in (("cancel", "cancel_unsupported"), ("retry", "retry_forbidden")):
        with pytest.raises(OwnerJobError) as caught:
            facade.act(run_id, {"action": action, "idempotency_key": f"k-{action}"})
        assert caught.value.code == code
        assert caught.value.details["mapping_version"] == "iqs.owner_job_actions/1.0.0"
    assert gates["execution"].control_calls == []  # nothing reached the owner
    # ...and they never appear in any allowed_actions either.
    assert facade.get_status(run_id)["job_view"]["allowed_actions"] == []


def test_reconcile_run_inspects_readonly_and_never_resends(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    run_id = next(iter(gates["execution"].runs))
    gates["execution"].runs[run_id]["process_state"] = "process_exited"
    starts_before = len(gates["execution"].start_calls)
    result = facade.act(run_id, {"action": "reconcile", "idempotency_key": "rec-A"})
    assert result["action_result"]["outcome"] == "inspected"
    assert result["action_result"]["status_after"] == "succeeded"
    assert len(gates["execution"].start_calls) == starts_before  # zero re-dispatch
    assert gates["execution"].control_calls == [(run_id, "inspect")]
    replay = facade.act(run_id, {"action": "reconcile", "idempotency_key": "rec-A"})
    assert replay["replayed"] is True
    assert gates["execution"].control_calls == [(run_id, "inspect")]


def test_reconcile_on_prepjob_is_read_only(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    job_id = "prepjob_" + "d" * 32
    gates["prep"].jobs[job_id] = {"job_id": job_id, "state": "needs_original_inspection",
                                  "created_at": "2026-11-07T00:00:00Z"}
    result = facade.act(job_id, {"action": "reconcile", "idempotency_key": "rec-P"})
    assert result["action_result"]["outcome"] == "reread"
    assert gates["prep"].control_calls == []  # native registration-reconcile NOT invoked


def test_resume_delegates_to_native_owner_guard(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    run_id = next(iter(gates["execution"].runs))
    gates["execution"].runs[run_id].update(process_state="process_exited", launcher_state="paused")
    result = facade.act(run_id, {"action": "resume", "idempotency_key": "res-1"})
    assert result["action_result"]["outcome"] == "requested"
    assert gates["execution"].control_calls == [(run_id, "resume")]
    assert result["job_view"]["status"] == "running"
    # delivery resume delegates too
    delivery_id = "deliveryjob_" + "a" * 32
    gates["delivery"].jobs[delivery_id] = {"job_id": delivery_id, "state": "partial",
        "created_at": "2026-11-07T00:00:00Z", "entries": [{"bundle_id": "b", "state": "pending"}]}
    facade.act(delivery_id, {"action": "resume", "idempotency_key": "res-2"})
    assert gates["delivery"].control_calls == [(delivery_id, "resume")]


def test_resume_prepjob_unsupported(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    with pytest.raises(OwnerJobError) as caught:
        facade.act("prepjob_" + "a" * 32, {"action": "resume", "idempotency_key": "k"})
    assert caught.value.code == "resume_unsupported"


def test_resume_unknown_replays_durable_intent_without_second_owner_call(tmp_path, gates, monkeypatch):
    facade = make_facade(tmp_path, gates)
    submit(facade)
    gateway = gates['execution']
    run_id = next(iter(gateway.runs))
    gateway.runs[run_id].update(process_state='process_exited', launcher_state='paused', launch_attempt=1)
    effects = []

    def lost_running_reference(job_id, action):
        assert job_id == run_id and action == 'resume'
        gateway.runs[run_id]['launch_attempt'] += 1
        effects.append(gateway.runs[run_id]['launch_attempt'])
        raise OSError('process started before reference write failed')

    monkeypatch.setattr(gateway, 'control', lost_running_reference)
    body = {'action': 'resume', 'idempotency_key': 'resume-once'}
    first = facade.act(run_id, body)
    assert first['action_result']['outcome'] == 'unknown'
    replay = make_facade(tmp_path, gates).act(run_id, body)
    assert replay['replayed'] and replay['action_result'] == first['action_result']
    assert effects == [2]


# --------------------------------------------------------------- G-m8-IQS-04

def test_list_jobs_bounded_page_cursor_and_authoritative_flag(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    for index in range(7):
        submit(facade, command_id=f"cmd-{index}", idempotency_key=f"idem-{index}")
    gates["execution"].launch("run-" + "1" * 32, {"process_state": "process_exited",
        "launcher_state": "paused"})  # workbench-originated, unbound
    page = facade.list_jobs(limit=5)
    assert len(page["items"]) == 5
    assert page["page"]["total"] == 8
    assert page["page"]["next_cursor"].startswith("v1:")
    assert page["page"]["total_status"] == "exact"
    assert page["work_completion_authoritative_default"] is False
    assert all(row["work_completion_authoritative"] is False for row in page["annotations"])
    second = facade.list_jobs(cursor=page["page"]["next_cursor"], limit=5)
    assert len(second["items"]) == 3
    assert second["page"]["next_cursor"] is None
    ids = {view["owner_job_id"] for view in page["items"] + second["items"]}
    assert len(ids) == 8  # bound jobs listed once, through their command
    unbound = [row for row in second["annotations"] if row["command_bound"] is False]
    assert unbound and unbound[0]["owner_job_id"] == "run-" + "1" * 32


def test_bound_command_projects_jobview_command_id(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    result = submit(facade)
    run_id = result["command"]["owner_job_id"]
    page = facade.list_jobs(limit=50)
    bound = [view for view in page["items"] if view["owner_job_id"] == run_id]
    assert len(bound) == 1 and bound[0]["command_id"] == "cmd-1"


def test_job_catalog_keeps_annotations_aligned_when_one_owner_read_fails(tmp_path, gates, monkeypatch):
    facade = make_facade(tmp_path, gates)
    broken = submit(facade)['job_view']['owner_job_id']
    healthy = 'run-' + '1' * 32
    gateway = gates['execution']
    gateway.launch(healthy, {'process_state': 'running', 'launcher_state': 'running'})
    tasks = gateway.tasks

    def one_unreadable(*args, **kwargs):
        if kwargs.get('run_ids') == [broken]:
            raise OSError('owner reference temporarily unavailable')
        return tasks(*args, **kwargs)

    monkeypatch.setattr(gateway, 'tasks', one_unreadable)
    page = facade.list_jobs()
    assert page['page']['total_status'] == 'estimate'
    assert [row['owner_job_id'] for row in page['annotations']] == [row['owner_job_id'] for row in page['items']]
    assert {row['owner_job_id']: row['status'] for row in page['items']} == {broken: 'unknown', healthy: 'running'}


# --------------------------------------------------------------- G-m8-IQS-05

def test_command_binding_survives_completion_and_failure(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    facade.submit_run_scan({"command_request": command_request(command_id="cmd-link",
        idempotency_key="idem-link"), "return_to": "#/company/ENT_A/quickscan"})
    run_id = next(iter(gates["execution"].runs))
    binding = facade.get_command("cmd-link")
    assert binding["command"]["owner_job_id"] == run_id
    assert binding["command"]["return_to"] == "#/company/ENT_A/quickscan"
    # job completes → binding persists
    gates["execution"].runs[run_id].update(process_state="observed_stopped",
        launcher_state="retired",
        retirement={"work_status_counts": {"delivered": 2}})
    binding = facade.get_command("cmd-link")
    assert binding["job_view"]["status"] == "succeeded"
    assert binding["command"]["owner_job_id"] == run_id
    # and through a failed state as well
    gates["execution"].runs[run_id]["retirement"] = {"work_status_counts": {"failed": 2}}
    binding = facade.get_command("cmd-link")
    assert binding["job_view"]["status"] == "failed"
    assert binding["command"]["owner_job_id"] == run_id


def test_get_status_by_owner_job_id(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    result = submit(facade)
    run_id = result["command"]["owner_job_id"]
    status = facade.get_status(run_id)
    assert status["job_view"]["owner_job_id"] == run_id
    assert status["annotation"]["owner_kind"] == "run"
    assert status["annotation"]["work_completion_authoritative"] is False


def test_unknown_owner_job_id_shape_refused(tmp_path, gates):
    facade = make_facade(tmp_path, gates)
    for call in (lambda: facade.get_status("../../etc"),
                 lambda: facade.act("not-a-job", {"action": "reconcile", "idempotency_key": "k"})):
        with pytest.raises(OwnerJobError) as caught:
            call()
        assert caught.value.code == "owner_job_id_invalid"


# ------------------------------------------------- §8-1 review follow-ups

def test_command_id_beyond_windows_filename_charset_is_accepted(tmp_path, gates):
    """REV-1: the Dashboard contract puts no pattern on command_id, so the
    ledger file is digest-named and ANY contract-legal id (including ':')
    must round-trip without touching the filesystem with raw characters."""
    facade = make_facade(tmp_path, gates)
    result = submit(facade, command_id="cmd:1", idempotency_key="idem-colon")
    assert result["command"]["command_id"] == "cmd:1"
    assert result["command"]["owner_job_id"].startswith("run-")
    fetched = facade.get_command("cmd:1")
    assert fetched["command"]["idempotency_key"] == "idem-colon"
    # Raw id never becomes a filename; only 32-hex digest files exist.
    for path in (tmp_path / "owner-jobs" / "commands").iterdir():
        assert path.stem.isalnum() and len(path.stem) == 32
    with pytest.raises(OwnerJobError) as caught:
        submit(facade, command_id="cmd/bad", idempotency_key="idem-slash")
    assert caught.value.code == "command_id_invalid"
    assert gates["execution"].start_calls == [{
        "bundle_id": "b1", "entity_id": "ENT_A", "bundle_fingerprint": "f" * 64}]


def test_crash_orphan_is_adopted_only_for_an_exact_replay(tmp_path, gates):
    """REV-4: a crash between the intent write and the index write must not
    wedge the command_id forever; an exact replay adopts and re-drives it,
    anything else stays a hard refusal."""
    facade = make_facade(tmp_path, gates)
    body = {"command_request": command_request(command_id="cmd-orphan", idempotency_key="idem-O")}
    facade._validate_command_request(body["command_request"])
    from dashboard_job_facade import PROTOCOL, _now
    record = {"protocol": PROTOCOL, "command_id": "cmd-orphan",
              "idempotency_key": "idem-O", "kind": "run_scan", "owner_job_id": None,
              "owner_kind": None, "entity_id": "ENT_A",
              "company": body["command_request"]["company"],
              "scan_scope": body["command_request"]["explicit_scope"], "as_of": None,
              "limits_ref": None, "limits_target": "bundle.spend_authorization",
              "return_to": None, "state": "submitting", "created_at": _now(),
              "updated_at": _now(), "submission": None, "error": None}
    facade._save_command(record)  # No idempotency index: crash window.
    result = facade.submit_run_scan(body)
    assert result["attached"] is True
    assert result["command"]["owner_job_id"].startswith("run-")
    # A DIFFERENT body under the same command id is still refused outright.
    other = {"command_request": command_request(command_id="cmd-orphan",
                                               idempotency_key="idem-O2",
                                               entity_id="ENT_B")}
    with pytest.raises(OwnerJobError) as caught:
        facade.submit_run_scan(other)
    assert caught.value.code == "command_id_reused"


def test_concurrent_same_key_acts_reach_the_owner_once(tmp_path, gates):
    """REV-3: the check-record-act sequence is serialised; the loser replays
    the recorded result instead of dispatching a second native control."""
    import threading
    facade = make_facade(tmp_path, gates)
    result = submit(facade)
    run_id = result["command"]["owner_job_id"]
    gates["execution"].runs[run_id]["process_state"] = "process_exited"
    release = threading.Event()
    entered = threading.Event()

    def slow_control(rid, action):
        entered.set()
        assert release.wait(5)
        return {"run": {"run_id": rid}, "preview": {"inspection_sha256": "a" * 64,
                "inspection": {"work_items": [{"question_id": "q1", "status": "delivered"}]}}}

    gates["execution"].control = slow_control
    outcomes = {}

    def act_once(tag):
        outcomes[tag] = facade.act(run_id, {"action": "reconcile", "idempotency_key": "race-1"})

    first = threading.Thread(target=act_once, args=("a",))
    second = threading.Thread(target=act_once, args=("b",))
    first.start()
    assert entered.wait(5)
    second.start()
    import time
    deadline = time.monotonic() + 2
    while "b" not in outcomes and time.monotonic() < deadline:
        time.sleep(0.01)  # b must be blocked on the facade lock, not dispatching
    release.set()
    first.join(timeout=5)
    second.join(timeout=5)
    assert set(outcomes) == {"a", "b"}
    replayed = sorted(row["replayed"] for row in outcomes.values())
    assert replayed == [False, True]  # exactly one dispatch, one replay


def test_results_route_return_to_with_query_context(tmp_path, gates):
    """§5-5 breadth: the /results context-restoration form (filters/snapshot
    tokens) passes verbatim and is stored on the durable command."""
    facade = make_facade(tmp_path, gates)
    return_to = "#/results?query=msft&offset=20&limit=50&filters=%7B%7D&snapshot_token=abc"
    result = facade.submit_run_scan({"command_request": command_request(
        command_id="cmd-ctx", idempotency_key="idem-ctx"), "return_to": return_to})
    assert result["command"]["return_to"] == return_to
    assert facade.get_command("cmd-ctx")["command"]["return_to"] == return_to
