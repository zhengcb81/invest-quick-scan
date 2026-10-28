"""Deterministic unit coverage: fake original executor, no process/API/database."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading
from contextlib import nullcontext

import pytest

from scripts.dashboard_batches import BatchGateway, DashboardBatchError
from scripts import dashboard_batches


def fingerprint(value):
    return hashlib.sha256(value.encode()).hexdigest()


class OwnerError(ValueError):
    code = "owner_rejected"


class FakeExecution:
    def __init__(self):
        self.bundles = {key: {"entity_id": "ENT_" + key, "version": key, "budget": True,
            "ready": False, "unknown": False} for key in ("a", "b", "c", "d")}
        self.runs, self.started, self.preview_calls, self.tasks_calls = {}, [], [], []
        self.next_id, self.peak_active = 1, 0
        self.crash = None
        self.lock = threading.RLock()
        self.controls = []
        self.registration_calls = []

    def bundle_registration(self, bundle_id):
        value = self.bundles[bundle_id]
        self.registration_calls.append(bundle_id)
        return {"bundle_id": bundle_id, "entity_id": value["entity_id"], "bundle_fingerprint": fingerprint(value["version"]),
            **{name: value.get(name) for name in ("company_preparation_id", "scope", "scope_id", "security_id", "expected_scope_bindings")}}

    def _control_lock(self, action):
        return nullcontext()

    def preview(self, payload):
        with self.lock:
            key = payload["bundle_id"]
            if key not in self.bundles:
                raise OwnerError("unknown")
            self.preview_calls.append(key)
            value = self.bundles[key]
            return {"bundle_id": key, "entity_id": value["entity_id"],
                **{name: value.get(name) for name in ("company_preparation_id", "scope", "scope_id", "security_id", "expected_scope_bindings")},
                "bundle_fingerprint": fingerprint(value["version"]),
                "preview_id": "preview-" + key, "inspection_sha256": fingerprint(json.dumps(value, sort_keys=True)),
                "can_start": not value["unknown"] and (value["budget"] or value["ready"]),
                "readonly_recovery": value["ready"], "API_requests": 0,
                "blocked_reasons": ["owner_work_unknown"] if value["unknown"] else [] if value["budget"] or value["ready"] else ["owner_budget_blocked"]}

    def tasks(self, *, bundle_ids=None, inspect_owner=True, limit=50, offset=0):
        with self.lock:
            self.tasks_calls.append({"bundle_ids": bundle_ids, "inspect_owner": inspect_owner})
            matching = [dict(row) for row in self.runs.values() if bundle_ids is None or row["bundle_id"] in bundle_ids]
            return {"API_requests": 0, "tasks": matching[offset:offset + limit], "total": len(matching),
                "next_offset": offset + limit if offset + limit < len(matching) else None}

    def start(self, payload):
        with self.lock:
            key = payload["bundle_id"]
            prior = [row for row in self.runs.values() if row["bundle_id"] == key]
            if prior:
                return {"run": dict(prior[-1]), "status": "attached"}
            if self.crash == "before":
                raise OwnerError("lost-before-response")
            value = self.bundles[key]
            if not value["budget"] or value["unknown"]:
                raise OwnerError("budget")
            run_id = "run-" + format(self.next_id, "032x")
            self.next_id += 1
            row = {"run_id": run_id, "bundle_id": key, "entity_id": value["entity_id"],
                "bundle_fingerprint": fingerprint(value["version"]), "process_state": "running"}
            self.runs[run_id] = row
            self.started.append(key)
            self.peak_active = max(self.peak_active, sum(item["process_state"] == "running" for item in self.runs.values()))
            if self.crash == "after":
                raise OwnerError("lost-after-response")
            return {"run": dict(row), "status": "started"}

    def finish(self, key, *, ready=True, exit_code=0):
        with self.lock:
            row = next(row for row in self.runs.values() if row["bundle_id"] == key)
            row.update(process_state="process_exited", exit_code=exit_code)
            self.bundles[key]["ready"] = ready

    def control(self, run_id, action):
        self.controls.append((run_id, action))
        raise AssertionError("Batch must not kill/pause native in-flight execution")


def test_positive_original_preflight_refusal_does_not_turn_into_unknown_launch(tmp_path):
    from scripts.dashboard_execution import ExecutionGateway,DashboardExecutionError
    class KnownPreflight(FakeExecution):
        prelaunch_refusal=staticmethod(ExecutionGateway.prelaunch_refusal)
        refusal=True
        def start(self,payload):
            if payload['bundle_id']=='a' and self.refusal:
                self.refusal=False
                detail=self.preview(payload)
                detail['blocked_reasons']=['owner_budget_or_original_work_blocked']
                raise DashboardExecutionError('execution_not_ready','before any process reference',409,detail,
                    prelaunch_not_started=True)
            return super().start(payload)
    execution=KnownPreflight();gateway=BatchGateway(execution,tmp_path/'batches',autostart=False)
    try:
        bid=start(gateway);gateway._step(bid)
        stored=row(gateway,bid);first=stored['entries'][0]
        assert first['state']=='blocked' and first['launch_uncertain'] is False
        assert first['prelaunch_refusal']['phase']=='before_process_reference'
        assert execution.started==['b'] and stored['state']=='running'
        with pytest.raises(DashboardBatchError) as running:gateway.control(bid,'resume')
        assert running.value.code=='batch_still_draining'
        execution.finish('b');gateway.control(bid,'resume');gateway._step(bid)
        assert execution.started==['b','a']
        assert 'prelaunch_refusal' not in row(gateway,bid)['entries'][0]
    finally:gateway.close()


def test_generic_same_preflight_error_code_is_still_unknown(tmp_path):
    from scripts.dashboard_execution import ExecutionGateway,DashboardExecutionError
    class UnknownPreflight(FakeExecution):
        prelaunch_refusal=staticmethod(ExecutionGateway.prelaunch_refusal)
        def start(self,payload):
            raise DashboardExecutionError('execution_not_ready','not positively classified',409,self.preview(payload))
    execution=UnknownPreflight();gateway=BatchGateway(execution,tmp_path/'batches',autostart=False)
    try:
        bid=start(gateway);gateway._step(bid)
        assert row(gateway,bid)['entries'][0]['launch_uncertain'] is True
        assert execution.started==[]
    finally:gateway.close()


def test_old_not_started_proof_is_cleared_before_a_later_lost_launch_response(tmp_path):
    from scripts.dashboard_execution import ExecutionGateway,DashboardExecutionError
    class Twice(FakeExecution):
        prelaunch_refusal=staticmethod(ExecutionGateway.prelaunch_refusal)
        first=True
        def start(self,payload):
            if self.first:
                self.first=False
                raise DashboardExecutionError('preview_changed','before reference',409,self.preview(payload),
                    prelaunch_not_started=True)
            self.crash='after'
            return super().start(payload)
    execution=Twice();gateway=BatchGateway(execution,tmp_path/'batches',autostart=False)
    try:
        bid=start(gateway,('a',));gateway._step(bid)
        assert row(gateway,bid)['entries'][0]['prelaunch_refusal']['phase']=='before_process_reference'
        gateway.control(bid,'resume');gateway._step(bid)
        entry=row(gateway,bid)['entries'][0]
        assert execution.started==['a'] and entry['launch_uncertain'] is True
        assert 'prelaunch_refusal' not in entry
    finally:gateway.close()


@pytest.fixture
def setup(tmp_path):
    execution = FakeExecution()
    gateway = BatchGateway(execution, tmp_path / "batches", autostart=False)
    yield gateway, execution
    gateway.close()


def start(gateway, keys=("a", "b")):
    preview = gateway.preview({"bundle_ids": list(keys)})
    return gateway.start({"preview_id": preview["preview_id"]})["batch"]["batch_id"]


def row(gateway, batch_id):
    return next(value for value in gateway.list()["batches"] if value["batch_id"] == batch_id)


def prepare_scope_pair(execution):
    """Representative current basic36: actual entity33 + security3 bindings."""
    prepared = "prepare_" + "a" * 32
    bindings = [{"scope": "entity", "scope_id": "ENT_a"}, {"scope": "security", "scope_id": "SEC_a_XSHE"}]
    for key, binding in zip(("a", "b"), bindings):
        execution.bundles[key].update(entity_id="ENT_a", company_preparation_id=prepared,
            expected_scope_bindings=[dict(value) for value in bindings], **binding,
            security_id=binding["scope_id"] if binding["scope"] == "security" else None)
    execution.bundles["a"]["question_ids"] = ["IQS_%02d" % index for index in range(1, 22)] + ["DUP_%d" % index for index in range(7)] + ["PORTER_%d" % index for index in range(5)]
    execution.bundles["b"]["question_ids"] = ["IQS_22", "IQS_23", "IQS_24"]
    return prepared, bindings


def test_preview_and_lists_are_read_only_and_keep_unknown_budget_and_ready_distinct(setup, tmp_path):
    gateway, execution = setup
    execution.bundles["a"].update(ready=True, budget=False)
    execution.bundles["b"]["budget"] = False
    execution.bundles["c"]["unknown"] = True
    preview = gateway.preview({"bundle_ids": ["a", "b", "c"]})
    assert [item["can_start"] for item in preview["entries"]] == [True, False, False]
    assert preview["entries"][0]["readonly_recovery"]
    assert preview["can_start"] and not preview["all_selected_ready"]
    assert gateway.status()["batches"] == [] and gateway.list()["total"] == 0
    assert execution.started == [] and execution.tasks_calls == []
    assert not (tmp_path / "batches").exists()


@pytest.mark.parametrize("payload", [{}, {"bundle_ids": []}, {"bundle_ids": ["a", "a"]},
    {"bundle_ids": ["../a"]}, {"bundle_ids": ["a"], "command": "anything"}, {"bundle_ids": "a"}])
def test_browser_selection_rejects_paths_commands_and_duplicate_ids(setup, payload):
    gateway, execution = setup
    with pytest.raises(DashboardBatchError):
        gateway.preview(payload)
    assert execution.started == []


def test_multimarket_or_other_scope_same_entity_cannot_double_count(setup):
    gateway, execution = setup
    execution.bundles["b"]["entity_id"] = "ENT_a"
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": ["a", "b"]})
    assert raised.value.code == "batch_duplicate_entity"


def test_fingerprint_contract_is_required_not_recomputed_by_coordinator(setup, monkeypatch):
    gateway, execution = setup
    original = execution.preview
    def incomplete(payload):
        value = original(payload)
        value.pop("bundle_fingerprint")
        return value
    monkeypatch.setattr(execution, "preview", incomplete)
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": ["a"]})
    assert raised.value.code == "execution_contract_incomplete"


def test_each_dispatch_checks_fresh_budget_and_explicit_resume_uses_owner_new_budget(setup):
    gateway, execution = setup
    batch_id = start(gateway, ("a",))
    execution.bundles["a"]["budget"] = False
    gateway._step(batch_id)
    assert execution.started == [] and row(gateway, batch_id)["state"] == "blocked"
    execution.bundles["a"]["budget"] = True
    # A GET or a timer on a blocked batch cannot spend the newly available quota.
    gateway.status()
    gateway._step(batch_id)
    assert execution.started == []
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a"]
    assert all(not call["inspect_owner"] for call in execution.tasks_calls)


def test_default_sequence_reuses_ready_and_exited_does_not_imply_answer_success(setup):
    gateway, execution = setup
    execution.bundles["a"].update(ready=True, budget=False)
    batch_id = start(gateway, ("a", "b", "c"))
    gateway._step(batch_id)
    assert execution.started == ["b"]
    execution.finish("b", ready=False, exit_code=0)
    gateway._step(batch_id)
    assert execution.started == ["b", "c"]
    execution.finish("c")
    gateway._step(batch_id)
    batch = row(gateway, batch_id)
    assert batch["state"] == "blocked"
    assert [item["state"] for item in batch["entries"]] == ["owner_ready", "failed", "owner_ready"]
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["b", "c"]
    assert batch["financial_accuracy_verified"] is False


def test_pause_drains_native_company_and_resume_continues_at_company_boundary(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == ["a"]
    gateway.control(batch_id, "pause")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["state"] == "draining"
    assert execution.controls == [] and execution.started == ["a"]
    execution.finish("a")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["state"] == "paused"
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a", "b"]
    execution.finish("b")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["state"] == "owner_ready"


def test_concurrency_is_small_deployment_setting_and_current_tasks_need_no_owner_inspection(tmp_path):
    execution = FakeExecution()
    gateway = BatchGateway(execution, tmp_path / "batch", max_concurrency=2, autostart=False)
    try:
        batch_id = start(gateway, ("a", "b", "c"))
        gateway._step(batch_id)
        assert execution.started == ["a", "b"] and execution.peak_active == 2
        calls = len(execution.preview_calls)
        gateway._step(batch_id)
        assert len(execution.preview_calls) == calls
        execution.finish("a")
        gateway._step(batch_id)
        assert execution.started == ["a", "b", "c"] and execution.peak_active == 2
        assert gateway.list()["batches"][0]["projection_is_dispatch_permission"] is False
    finally:
        gateway.close()
    for invalid in (0, 5, True, "2"):
        with pytest.raises(DashboardBatchError):
            BatchGateway(execution, tmp_path / "invalid", max_concurrency=invalid)


def test_repeated_click_and_fresh_same_selection_attach_one_batch(setup):
    gateway, execution = setup
    preview = gateway.preview({"bundle_ids": ["a"]})
    first = gateway.start({"preview_id": preview["preview_id"]})
    second = gateway.start({"preview_id": preview["preview_id"]})
    third = gateway.start({"preview_id": gateway.preview({"bundle_ids": ["a"]})["preview_id"]})
    assert first["batch"]["batch_id"] == second["batch"]["batch_id"] == third["batch"]["batch_id"]
    assert second["status"] == third["status"] == "attached"
    gateway._step(first["batch"]["batch_id"])
    assert execution.started == ["a"]


def test_two_servers_atomic_start_does_not_duplicate_batch_or_launch(tmp_path):
    execution = FakeExecution()
    gateways = [BatchGateway(execution, tmp_path / "batch", autostart=False) for _ in range(2)]
    previews = [gateway.preview({"bundle_ids": ["a"]}) for gateway in gateways]
    barrier = threading.Barrier(2)
    def attempt(index):
        barrier.wait()
        try:
            return gateways[index].start({"preview_id": previews[index]["preview_id"]})
        except DashboardBatchError as error:
            assert error.code == "batch_control_busy"
            return None
    try:
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(attempt, range(2)))
        assert sum(bool(item and item["status"] == "created") for item in results) == 1
        assert gateways[0].list()["total"] == 1
        assert execution.started == []
        # The stable lock inode is harmless; the OS byte lock was released.
        gateways[0].control(gateways[0].list()["batches"][0]["batch_id"], "pause")
    finally:
        for gateway in gateways:
            gateway.close()


def test_restart_never_dispatches_on_get_and_requires_explicit_resume_for_unlaunched_selection(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    restarted = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        assert row(restarted, batch_id)["state"] == "needs_original_inspection"
        assert execution.started == []
        assert restarted._step(batch_id) is False
        assert execution.started == []
        restarted.control(batch_id, "resume")
        restarted._step(batch_id)
        assert execution.started == ["a"]
        # The former instance has lost its coordinator ownership.
        assert gateway._step(batch_id) is False
    finally:
        restarted.close()


@pytest.mark.parametrize("crash", ["before", "after"])
def test_lost_launch_response_keeps_uncertainty_and_never_blindly_replays(setup, crash):
    gateway, execution = setup
    execution.crash = crash
    batch_id = start(gateway)
    gateway._step(batch_id)
    before = list(execution.started)
    assert row(gateway, batch_id)["state"] == "blocked"
    restarted = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        if crash == "after":
            with pytest.raises(DashboardBatchError) as raised:
                restarted.control(batch_id, "resume")
            assert raised.value.code == "batch_still_draining"
        else:
            restarted.control(batch_id, "resume")
        restarted._step(batch_id)
        assert execution.started == before
        execution.crash = None
        # Only original ready evidence resolves the lost-response window.
        execution.bundles["a"]["ready"] = True
        if crash == "after":
            execution.finish("a")
        restarted.control(batch_id, "resume")
        restarted._step(batch_id)
        assert execution.started == before + ["b"]
    finally:
        restarted.close()


def test_persisted_launching_crash_without_reference_blocks_even_with_new_budget(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    path = gateway.state_root / (batch_id + ".json")
    stored = json.loads(path.read_text(encoding="utf8"))
    stored["entries"][0]["state"] = "launching"
    path.write_text(json.dumps(stored), encoding="utf8")
    restarted = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        restarted.control(batch_id, "resume")
        assert row(restarted, batch_id)["state"] == "blocked"
        restarted._step(batch_id)
        assert execution.started == []
    finally:
        restarted.close()


def test_existing_active_and_exited_original_references_attach_without_start_calls(setup):
    gateway, execution = setup
    execution.start({"bundle_id": "a", "preview_id": "preview-a"})
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == ["a"]
    execution.finish("a")
    gateway._step(batch_id)
    assert execution.started == ["a", "b"]
    execution.finish("b", ready=False, exit_code=2)
    gateway._step(batch_id)
    assert row(gateway, batch_id)["entries"][1]["state"] == "failed"


def test_original_unknown_process_blocks_following_company(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    gateway._step(batch_id)
    next(iter(execution.runs.values()))["process_state"] = "needs_original_inspection"
    gateway._step(batch_id)
    assert execution.started == ["a"]
    assert row(gateway, batch_id)["state"] == "blocked"
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a"]


def test_input_changes_reject_start_and_resume_without_rewriting_frozen_selection(setup):
    gateway, execution = setup
    preview = gateway.preview({"bundle_ids": ["a"]})
    execution.bundles["a"]["version"] = "changed"
    with pytest.raises(DashboardBatchError) as raised:
        gateway.start({"preview_id": preview["preview_id"]})
    assert raised.value.code == "batch_bundle_changed"
    execution.bundles["a"]["version"] = "a"
    batch_id = start(gateway, ("a",))
    gateway.control(batch_id, "pause")
    path = gateway.state_root / (batch_id + ".json")
    before = path.read_bytes()
    execution.bundles["a"]["version"] = "changed"
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, "resume")
    assert raised.value.code == "batch_bundle_changed"
    unchanged = json.loads(before)
    blocked = json.loads(path.read_text(encoding="utf8"))
    assert blocked["selection_sha256"] == unchanged["selection_sha256"] and blocked["entries"] == unchanged["entries"]
    assert blocked["state"] == "blocked" and execution.started == []


def test_different_batches_cannot_concurrently_start_same_entity_scope(setup):
    gateway, execution = setup
    batch_id = start(gateway, ("a",))
    gateway._step(batch_id)
    execution.bundles["d"]["entity_id"] = "ENT_a"
    preview = gateway.preview({"bundle_ids": ["d"]})
    with pytest.raises(DashboardBatchError) as raised:
        gateway.start({"preview_id": preview["preview_id"]})
    assert raised.value.code == "batch_entity_active"
    assert execution.started == ["a"]


def test_corrupt_record_is_not_silently_empty_and_live_cross_instance_lock_blocks_mutations(setup):
    gateway, execution = setup
    batch_id = start(gateway, ("a",))
    path = gateway.state_root / (batch_id + ".json")
    path.write_text("{}", encoding="utf8")
    with pytest.raises(DashboardBatchError) as raised:
        gateway.list()
    assert raised.value.code == "batch_record_corrupt"
    path.unlink()
    other = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        with other._mutation():
            with pytest.raises(DashboardBatchError) as raised:
                start(gateway, ("b",))
            assert raised.value.code == "batch_control_busy"
        # The old lock file is not permission to launch, but an unlocked file
        # also cannot permanently prevent explicit owner-checked recovery.
        start(gateway, ("b",))
    finally:
        other.close()
    assert execution.started == []


def test_exception_releases_kernel_lock_for_another_instance(setup):
    gateway, execution = setup
    with pytest.raises(RuntimeError):
        with gateway._mutation():
            raise RuntimeError("simulated control failure")
    other = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        start(other, ("a",))
        assert other.list()["total"] == 1 and execution.started == []
    finally:
        other.close()


def test_shutdown_keeps_native_child_untouched_and_state_requires_inspection(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    gateway._step(batch_id)
    gateway.close()
    assert row(gateway, batch_id)["state"] == "needs_original_inspection"
    assert execution.controls == [] and execution.started == ["a"]
    assert next(iter(execution.runs.values()))["process_state"] == "running"
    assert gateway._step(batch_id) is False


def test_background_worker_runs_and_shutdown_joins_without_real_sleep_or_native_stop(tmp_path):
    execution = FakeExecution()
    started = threading.Event()
    original_start = execution.start
    def observed_start(payload):
        value = original_start(payload)
        started.set()
        return value
    execution.start = observed_start
    gateway = BatchGateway(execution, tmp_path / "batch", poll_interval=0.01)
    try:
        batch_id = start(gateway, ("a",))
        assert started.wait(3)
        assert execution.started == ["a"]
        assert row(gateway, batch_id)["state"] == "running"
    finally:
        gateway.close()
    assert all(not thread.is_alive() for thread in gateway._threads.values())
    assert execution.controls == []


def test_status_pagination_and_bad_controls_are_explicit(setup):
    gateway, _ = setup
    for key in ("a", "b", "c"):
        start(gateway, (key,))
    values = gateway.list(limit=1, offset=1)
    assert values["total"] == 3 and len(values["batches"]) == 1
    for kwargs in ({"limit": 0}, {"offset": -1}, {"limit": True}):
        with pytest.raises(DashboardBatchError):
            gateway.list(**kwargs)
    with pytest.raises(DashboardBatchError):
        gateway.control("../../anything", "pause")
    with pytest.raises(DashboardBatchError):
        gateway.control("batch-" + "0" * 32, "kill")
    with pytest.raises(DashboardBatchError):
        gateway.start({"preview_id": "unknown", "command": "python"})


def test_blocked_budget_does_not_spend_but_other_selected_company_can_run(setup):
    gateway, execution = setup
    execution.bundles["a"]["budget"] = False
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == ["b"]
    execution.finish("b")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["state"] == "blocked"
    assert row(gateway, batch_id)["entries"][0]["state"] == "blocked"
    execution.bundles["a"]["budget"] = True
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["b", "a"]


def test_changed_input_between_registration_and_dispatch_does_not_start_anything(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    execution.bundles["a"]["version"] = "changed"
    gateway._step(batch_id)
    assert execution.started == ["b"]
    assert row(gateway, batch_id)["entries"][0]["blocked_reasons"] == ["batch_bundle_changed"]


def test_truncated_original_reference_list_is_not_treated_as_empty(setup, monkeypatch):
    gateway, execution = setup
    batch_id = start(gateway)
    monkeypatch.setattr(execution, "tasks", lambda **kwargs: {"API_requests": 0, "tasks": [], "total": 1, "next_offset": 0})
    gateway._step(batch_id)
    assert execution.started == []
    assert row(gateway, batch_id)["entries"][0]["blocked_reasons"] == ["execution_tasks_truncated"]


def test_active_tick_only_queries_active_reference_not_all_pending_companies(setup):
    gateway, execution = setup
    batch_id = start(gateway, ("a", "b", "c", "d"))
    gateway._step(batch_id)
    execution.tasks_calls.clear()
    gateway._step(batch_id)
    assert execution.tasks_calls == [{"bundle_ids": ["a"], "inspect_owner": False}]
    execution.finish("a")
    gateway._step(batch_id)
    execution.tasks_calls.clear()
    gateway._step(batch_id)
    assert execution.tasks_calls == [{"bundle_ids": ["b"], "inspect_owner": False}]


def test_pause_before_first_company_never_launches_and_resume_requires_original_checks(setup):
    gateway, execution = setup
    batch_id = start(gateway)
    gateway.control(batch_id, "pause")
    gateway._step(batch_id)
    assert execution.started == [] and row(gateway, batch_id)["state"] == "paused"
    execution.bundles["a"]["unknown"] = True
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == []
    assert row(gateway, batch_id)["entries"][0]["state"] == "blocked"


def test_unknown_original_work_in_selection_blocks_whole_batch_without_inventing_parallel_capacity(setup):
    gateway, execution = setup
    execution.bundles["a"]["unknown"] = True
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == []
    assert row(gateway, batch_id)["state"] == "blocked"


def test_restart_uses_lower_deployment_concurrency_even_if_saved_batch_allowed_two(tmp_path):
    execution = FakeExecution()
    previous = BatchGateway(execution, tmp_path / "batch", max_concurrency=2, autostart=False)
    restarted = BatchGateway(execution, tmp_path / "batch", max_concurrency=1, autostart=False)
    try:
        batch_id = start(previous, ("a", "b"))
        restarted.control(batch_id, "resume")
        restarted._step(batch_id)
        assert execution.started == ["a"]
    finally:
        previous.close()
        restarted.close()


def test_shutdown_during_original_preview_does_not_dispatch_after_it_returns(setup, monkeypatch):
    gateway, execution = setup
    batch_id = start(gateway, ("a",))
    entered, release = threading.Event(), threading.Event()
    original_preview = execution.preview
    def held_preview(payload):
        entered.set()
        assert release.wait(3)
        return original_preview(payload)
    monkeypatch.setattr(execution, "preview", held_preview)
    thread = threading.Thread(target=gateway._step, args=(batch_id,))
    thread.start()
    try:
        assert entered.wait(3)
        gateway.close()
    finally:
        release.set()
        thread.join(timeout=3)
    assert not thread.is_alive() and execution.started == []
    assert row(gateway, batch_id)["state"] == "paused"


def test_resume_racing_with_finished_worker_schedules_a_replacement(tmp_path, monkeypatch):
    execution = FakeExecution()
    gateway = BatchGateway(execution, tmp_path / "batch", autostart=False, poll_interval=0.01)
    batch_id = start(gateway, ("a",))
    gateway.control(batch_id, "pause")
    finished, release, launched = threading.Event(), threading.Event(), threading.Event()
    original_step, original_start = gateway._step, execution.start
    calls = 0
    def held_step(selected_id):
        nonlocal calls
        calls += 1
        result = original_step(selected_id)
        if calls == 1:
            finished.set()
            assert release.wait(3)
        return result
    def observed_start(payload):
        result = original_start(payload)
        launched.set()
        return result
    monkeypatch.setattr(gateway, "_step", held_step)
    monkeypatch.setattr(execution, "start", observed_start)
    gateway.autostart = True
    gateway._launch_worker(batch_id)
    try:
        assert finished.wait(3)
        gateway.control(batch_id, "resume")
        release.set()
        assert launched.wait(3)
        assert execution.started == ["a"]
    finally:
        release.set()
        gateway.close()


def test_transient_windows_replace_contention_retries_only_record_write_not_execution(setup, monkeypatch):
    gateway, execution = setup
    original_replace = dashboard_batches.os.replace
    failures = 0
    def contended_replace(source, target):
        nonlocal failures
        if failures < 2:
            failures += 1
            raise PermissionError("simulated Windows reader lock")
        return original_replace(source, target)
    monkeypatch.setattr(dashboard_batches.os, "replace", contended_replace)
    batch_id = start(gateway, ("a",))
    gateway._step(batch_id)
    assert failures == 2 and execution.started == ["a"]
    assert row(gateway, batch_id)["entries"][0]["run_id"]


def test_record_failure_after_native_launch_is_recovered_by_reference_not_redispatch(setup, monkeypatch):
    gateway, execution = setup
    batch_id = start(gateway, ("a",))
    original_replace = dashboard_batches.os.replace
    def failed_after_launch(source, target):
        if execution.started:
            raise PermissionError("simulated persistent record failure")
        return original_replace(source, target)
    monkeypatch.setattr(dashboard_batches.os, "replace", failed_after_launch)
    with pytest.raises(PermissionError):
        gateway._step(batch_id)
    assert execution.started == ["a"]
    monkeypatch.setattr(dashboard_batches.os, "replace", original_replace)
    restarted = BatchGateway(execution, gateway.state_root, autostart=False)
    try:
        with pytest.raises(DashboardBatchError) as raised:
            restarted.control(batch_id, "resume")
        assert raised.value.code == "batch_still_draining"
        execution.finish("a")
        restarted.control(batch_id, "resume")
        assert row(restarted, batch_id)["state"] == "owner_ready"
        assert execution.started == ["a"]
    finally:
        restarted.close()


def test_unexpected_worker_failure_is_visible_and_resume_rechecks_before_dispatch(tmp_path, monkeypatch):
    execution = FakeExecution()
    gateway = BatchGateway(execution, tmp_path / "batch", poll_interval=0.01)
    original_step = gateway._step
    failure = threading.Event()
    def failed_step(selected_id):
        failure.set()
        raise PermissionError("simulated coordinator I/O")
    monkeypatch.setattr(gateway, "_step", failed_step)
    try:
        batch_id = start(gateway, ("a",))
        assert failure.wait(3)
        for thread in list(gateway._threads.values()):
            thread.join(timeout=3)
        batch = row(gateway, batch_id)
        assert batch["state"] == "needs_original_inspection"
        assert batch["coordinator_error"]["code"] == "batch_coordinator_io_failed"
        assert execution.started == []
        monkeypatch.setattr(gateway, "_step", original_step)
        gateway.autostart = False
        gateway.control(batch_id, "resume")
        gateway._step(batch_id)
        assert execution.started == ["a"]
    finally:
        gateway.close()


def test_shared_batch_capacity_applies_across_two_server_instances(tmp_path):
    execution = FakeExecution()
    first = BatchGateway(execution, tmp_path / "batch", autostart=False)
    second = BatchGateway(execution, tmp_path / "batch", autostart=False)
    try:
        first_id = start(first, ("a",))
        second_id = start(second, ("b",))
        first._step(first_id)
        second._step(second_id)
        assert execution.started == ["a"]
        assert row(second, second_id)["state"] == "running"
        execution.finish("a")
        first._step(first_id)
        second._step(second_id)
        assert execution.started == ["a", "b"] and execution.peak_active == 1
    finally:
        first.close()
        second.close()


def test_different_order_cannot_reserve_same_not_yet_started_companies_twice(setup):
    gateway, execution = setup
    start(gateway, ("a", "b"))
    preview = gateway.preview({"bundle_ids": ["b", "a"]})
    with pytest.raises(DashboardBatchError) as raised:
        gateway.start({"preview_id": preview["preview_id"]})
    assert raised.value.code == "batch_entity_active" and execution.started == []


def test_complementary_preparation_scopes_are_complete_ordered_and_one_company(setup):
    gateway, execution = setup
    prepared, bindings = prepare_scope_pair(execution)
    preview = gateway.preview({"bundle_ids": ["b", "a"]})
    assert [value["bundle_id"] for value in preview["entries"]] == ["a", "b"]
    assert preview["company_count"] == 1 and preview["scope_count"] == 2
    batch_id = gateway.start({"preview_id": preview["preview_id"]})["batch"]["batch_id"]
    gateway._step(batch_id)
    assert execution.started == ["a"]
    execution.finish("a")
    gateway._step(batch_id)
    assert execution.started == ["a", "b"]
    current = row(gateway, batch_id)
    assert current["company_counts"]["total"] == 1 and current["company_counts"]["owner_ready"] == 0
    assert current["scope_counts"]["owner_ready"] == 1
    assert current["company_groups"][0] == {"entity_id": "ENT_a", "company_preparation_id": prepared,
        "scope_count": 2, "ready_scope_count": 1, "expected_scope_bindings": bindings,
        "bundle_ids": ["a", "b"], "state": "running", "complete": False}
    execution.finish("b")
    gateway._step(batch_id)
    completed = row(gateway, batch_id)
    assert completed["state"] == "owner_ready" and completed["company_counts"]["owner_ready"] == 1
    assert completed["scope_counts"]["total"] == 2 and completed["scope_counts"]["owner_ready"] == 2
    actual_questions = [question for key in execution.started for question in execution.bundles[key]["question_ids"]]
    assert len(actual_questions) == len(set(actual_questions)) == 36
    assert actual_questions[-3:] == ["IQS_22", "IQS_23", "IQS_24"]


def test_same_company_scope_children_never_parallelize_even_when_two_slots_exist(tmp_path):
    execution = FakeExecution()
    prepare_scope_pair(execution)
    gateway = BatchGateway(execution, tmp_path / "batch", max_concurrency=2, autostart=False)
    try:
        batch_id = start(gateway, ("a", "b", "c"))
        gateway._step(batch_id)
        assert execution.started == ["a", "c"]
        assert row(gateway, batch_id)["entries"][1]["state"] == "selected"
        execution.finish("a")
        gateway._step(batch_id)
        assert execution.started == ["a", "c", "b"] and execution.peak_active == 2
    finally:
        gateway.close()


@pytest.mark.parametrize("selected", [["a"], ["b"]])
def test_preparation_requires_all_declared_scopes_not_only_entity33_or_security3(setup, selected):
    gateway, execution = setup
    prepare_scope_pair(execution)
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": selected})
    assert raised.value.code == "batch_scope_group_incomplete"
    assert execution.started == []


def test_dynamic_expected_scope_bindings_can_explicitly_declare_entity_only_without_hardcoded_two(setup):
    gateway, execution = setup
    prepared, _ = prepare_scope_pair(execution)
    execution.bundles["a"]["expected_scope_bindings"] = [{"scope": "entity", "scope_id": "ENT_a"}]
    preview = gateway.preview({"bundle_ids": ["a"]})
    assert preview["company_count"] == preview["scope_count"] == 1
    batch_id = gateway.start({"preview_id": preview["preview_id"]})["batch"]["batch_id"]
    gateway._step(batch_id)
    execution.finish("a")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["company_groups"][0]["company_preparation_id"] == prepared
    assert row(gateway, batch_id)["company_counts"]["owner_ready"] == 1


@pytest.mark.parametrize("mutation,code", [
    ("different_preparation", "batch_duplicate_entity"),
    ("duplicate_scope", "batch_duplicate_scope"),
    ("different_expected", "batch_scope_group_mismatch"),
    ("mixed_market_security", "batch_security_mismatch"),
])
def test_same_entity_does_not_authorize_merging_unrelated_or_duplicate_scopes(setup, mutation, code):
    gateway, execution = setup
    prepare_scope_pair(execution)
    if mutation == "different_preparation":
        execution.bundles["b"]["company_preparation_id"] = "prepare_" + "b" * 32
    elif mutation == "duplicate_scope":
        execution.bundles["b"].update(scope="entity", scope_id="ENT_a", security_id=None)
    elif mutation == "different_expected":
        execution.bundles["a"]["expected_scope_bindings"] = [{"scope": "entity", "scope_id": "ENT_a"}]
    else:
        execution.bundles["a"]["security_id"] = "SEC_a_XHKG"
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": ["a", "b"]})
    assert raised.value.code == code and execution.started == []


def test_same_preparation_id_cannot_bind_two_companies(setup):
    gateway, execution = setup
    prepared, _ = prepare_scope_pair(execution)
    execution.bundles["c"].update(company_preparation_id=prepared, scope="entity", scope_id="ENT_c",
        expected_scope_bindings=[{"scope": "entity", "scope_id": "ENT_c"}])
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": ["a", "b", "c"]})
    assert raised.value.code == "batch_preparation_identity_mismatch"


def test_partial_preparation_reuses_ready33_and_only_requests_remaining_security3(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    execution.bundles["a"].update(ready=True, budget=False)
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == ["b"]
    assert row(gateway, batch_id)["company_counts"]["owner_ready"] == 0
    execution.finish("b")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["company_counts"]["owner_ready"] == 1


def test_pause_between_scopes_preserves_partial_company_and_resume_does_not_repeat33(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    batch_id = start(gateway)
    gateway._step(batch_id)
    paused = gateway.control(batch_id, "pause")
    assert paused["pause_scope"] == "scope_or_company_boundary"
    execution.finish("a")
    gateway._step(batch_id)
    partial = row(gateway, batch_id)
    assert partial["state"] == "paused"
    assert partial["scope_counts"]["owner_ready"] == 1 and partial["company_counts"]["owner_ready"] == 0
    assert partial["entries"][1]["state"] == "selected"
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a", "b"]
    execution.finish("b")
    gateway._step(batch_id)
    assert row(gateway, batch_id)["company_counts"]["owner_ready"] == 1


def test_unknown_security_scope_blocks_preparation_until_original_state_resolved(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    execution.bundles["a"]["ready"] = True
    execution.bundles["b"]["unknown"] = True
    batch_id = start(gateway)
    gateway._step(batch_id)
    assert execution.started == [] and row(gateway, batch_id)["company_counts"]["owner_ready"] == 0
    assert row(gateway, batch_id)["scope_counts"]["owner_ready"] == 1
    execution.bundles["b"]["unknown"] = False
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["b"]


def test_entity_failure_does_not_run_following_security_scope_or_spin_forever(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    batch_id = start(gateway)
    gateway._step(batch_id)
    execution.finish("a", ready=False, exit_code=1)
    gateway._step(batch_id)
    assert execution.started == ["a"] and row(gateway, batch_id)["state"] == "blocked"
    assert row(gateway, batch_id)["company_counts"]["failed"] == 1
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a"]


def test_scope_binding_change_is_rejected_even_if_executor_fingerprint_were_incorrectly_unchanged(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    batch_id = start(gateway)
    gateway.control(batch_id, "pause")
    path = gateway.state_root / (batch_id + ".json")
    before = path.read_bytes()
    replacement = [{"scope": "entity", "scope_id": "ENT_a"}, {"scope": "security", "scope_id": "SEC_a_XHKG"}]
    for key in ("a", "b"):
        execution.bundles[key]["expected_scope_bindings"] = replacement
    execution.bundles["b"].update(scope_id="SEC_a_XHKG", security_id="SEC_a_XHKG")
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, "resume")
    assert raised.value.code == "batch_bundle_changed"
    unchanged = json.loads(before)
    blocked = json.loads(path.read_text(encoding="utf8"))
    assert blocked["selection_sha256"] == unchanged["selection_sha256"] and blocked["entries"] == unchanged["entries"]
    assert blocked["state"] == "blocked" and execution.started == []


def test_invalid_or_future_scope_metadata_requires_new_explicit_contract(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    execution.bundles["a"].update(scope="segment", scope_id="SEG_a",
        expected_scope_bindings=[{"scope": "segment", "scope_id": "SEG_a"}])
    with pytest.raises(DashboardBatchError) as raised:
        gateway.preview({"bundle_ids": ["a"]})
    assert raised.value.code == "batch_scope_metadata_invalid"


def test_original_reference_pagination_covers_large_company_pools_without_inspecting_each_owner(setup):
    gateway, execution = setup
    selected = []
    for index in range(2001):
        key = "company_%04d" % index
        run_id = "run-" + format(index, "032x")
        execution.runs[run_id] = {"run_id": run_id, "bundle_id": key, "entity_id": "ENT_" + str(index),
            "bundle_fingerprint": fingerprint(key), "process_state": "process_exited"}
        selected.append({"bundle_id": key, "state": "selected"})
    result = gateway._tasks(selected, include_selected=True)
    assert len(result) == len({row["run_id"] for row in result}) == 2001
    assert len(execution.tasks_calls) == 2
    assert all(call["inspect_owner"] is False for call in execution.tasks_calls)
    assert execution.preview_calls == [] and execution.started == []


def test_reference_pagination_changes_or_duplicates_fail_closed(setup, monkeypatch):
    gateway, execution = setup
    item = {"run_id": "run-" + "a" * 32, "bundle_id": "a"}
    def duplicate_page(**kwargs):
        return {"API_requests": 0, "tasks": [item], "total": 2,
            "next_offset": 1 if kwargs["offset"] == 0 else None}
    monkeypatch.setattr(execution, "tasks", duplicate_page)
    with pytest.raises(DashboardBatchError) as raised:
        gateway._tasks([{"bundle_id": "a", "state": "selected"}], include_selected=True)
    assert raised.value.code == "execution_tasks_invalid"


def test_resume_completed_scope_uses_local_registration_without_spawning_original_inspector(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    execution.bundles["a"]["ready"] = True
    batch_id = start(gateway)
    gateway.control(batch_id, "pause")
    execution.preview_calls.clear()
    execution.registration_calls.clear()
    gateway.control(batch_id, "resume")
    assert execution.registration_calls == ["a", "b"]
    assert execution.preview_calls == []
    gateway._step(batch_id)
    assert execution.started == ["b"] and "a" not in execution.preview_calls


def test_ready_scope_registration_drift_blocks_resume_and_keeps_original_frozen_selection(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    execution.bundles["a"]["ready"] = True
    batch_id = start(gateway)
    gateway.control(batch_id, "pause")
    before = row(gateway, batch_id)
    execution.bundles["a"]["version"] = "ready-input-was-edited"
    execution.preview_calls.clear()
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, "resume")
    assert raised.value.code == "batch_bundle_changed"
    blocked = row(gateway, batch_id)
    assert blocked["state"] == "blocked" and blocked["blocked_reasons"] == ["batch_bundle_changed"]
    assert blocked["selection_sha256"] == before["selection_sha256"]
    assert blocked["entries"] == before["entries"]
    assert execution.preview_calls == [] and execution.started == []


def registered_pool(execution, companies, with_security):
    execution.bundles.clear()
    for index in range(companies):
        entity_id = "ENT_pool_%04d" % index
        bindings = [{"scope": "entity", "scope_id": entity_id}]
        if with_security:
            bindings.append({"scope": "security", "scope_id": "SEC_pool_%04d" % index})
        for binding in bindings:
            key = "pool_%04d_%s" % (index, binding["scope"])
            execution.bundles[key] = {"entity_id": entity_id, "version": key, "budget": True, "ready": False,
                "unknown": False, "company_preparation_id": "prepare_" + format(index, "032x"),
                "expected_scope_bindings": bindings, **binding,
                "security_id": binding["scope_id"] if binding["scope"] == "security" else None}
    return list(execution.bundles)


@pytest.mark.parametrize("companies,with_security", [(2000, False), (2000, True)])
def test_large_pool_registration_preview_start_and_resume_use_zero_original_inspectors(tmp_path, companies, with_security):
    execution = FakeExecution()
    bundles = registered_pool(execution, companies, with_security)
    gateway = BatchGateway(execution, tmp_path / "batch", autostart=False)
    try:
        preview = gateway.registration_preview({"bundle_ids": bundles})
        assert preview["preview_kind"] == "registration" and preview["owner_inspected"] is False
        assert preview["coordinator_can_register"] is True and preview["owner_admission_confirmed"] is False
        assert preview["can_start"] is True  # Coordination only, explicitly not fee admission.
        assert preview["company_count"] == companies and preview["scope_count"] == len(bundles)
        assert all(row["can_start"] is None and row["owner_inspected"] is False for row in preview["entries"])
        result = gateway.start({"preview_id": preview["preview_id"]})
        batch_id = result["batch"]["batch_id"]
        assert result["batch"]["scope_counts"]["selected"] == len(bundles)
        assert result["batch"]["company_counts"]["owner_ready"] == 0
        assert execution.preview_calls == [] and execution.started == []
        gateway.control(batch_id, "pause")
        gateway.control(batch_id, "resume")
        assert execution.preview_calls == [] and execution.started == []
        assert len(execution.registration_calls) == 3 * len(bundles)
        assert row(gateway, batch_id)["state"] == "running"
    finally:
        gateway.close()


def test_local_registration_is_not_budget_admission_and_actual_dispatch_still_checks_owner(setup):
    gateway, execution = setup
    execution.bundles["a"]["budget"] = False
    plan = gateway.registration_preview({"bundle_ids": ["a"]})
    assert plan["can_start"] is True and plan["owner_admission_confirmed"] is False
    batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
    assert execution.preview_calls == [] and row(gateway, batch_id)["entries"][0]["state"] == "selected"
    gateway._step(batch_id)
    assert execution.preview_calls == ["a"] and execution.started == []
    assert row(gateway, batch_id)["state"] == "blocked"
    execution.bundles["a"]["budget"] = True
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a"]
    assert execution.preview_calls.count("a") >= 2  # No stale local preview can dispatch work.


def test_local_scope_group_keeps_entity_then_security_and_inspects_only_scope_being_dispatched(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    plan = gateway.registration_preview({"bundle_ids": ["b", "a"]})
    assert [entry["bundle_id"] for entry in plan["entries"]] == ["a", "b"]
    batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
    gateway._step(batch_id)
    assert execution.preview_calls == ["a"] and execution.started == ["a"]
    execution.finish("a")
    gateway._step(batch_id)
    assert execution.started == ["a", "b"] and execution.preview_calls[-1] == "b"


def test_registration_only_preview_refuses_incomplete_scope_groups_and_changed_inputs(setup):
    gateway, execution = setup
    prepare_scope_pair(execution)
    with pytest.raises(DashboardBatchError) as raised:
        gateway.registration_preview({"bundle_ids": ["a"]})
    assert raised.value.code == "batch_scope_group_incomplete"
    plan = gateway.registration_preview({"bundle_ids": ["a", "b"]})
    execution.bundles["a"]["version"] = "changed-after-local-preview"
    with pytest.raises(DashboardBatchError) as raised:
        gateway.start({"preview_id": plan["preview_id"]})
    assert raised.value.code == "batch_bundle_changed"
    assert gateway.list()["total"] == 0 and execution.preview_calls == [] and execution.started == []


def test_local_preview_resume_cannot_ignore_preexisting_unknown_native_execution(setup):
    gateway, execution = setup
    execution.start({"bundle_id": "a", "preview_id": "original"})
    next(iter(execution.runs.values()))["process_state"] = "needs_original_inspection"
    plan = gateway.registration_preview({"bundle_ids": ["a", "b"]})
    batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
    gateway.control(batch_id, "pause")
    gateway.control(batch_id, "resume")
    gateway._step(batch_id)
    assert execution.started == ["a"] and execution.preview_calls
    assert row(gateway, batch_id)["state"] == "blocked"
    assert row(gateway, batch_id)["entries"][0]["blocked_reasons"] == ["original_process_unknown"]


def test_native_preview_barrier_does_not_block_projection_reads_local_previews_or_busy_controls(setup, monkeypatch):
    gateway, execution = setup
    plan = gateway.registration_preview({"bundle_ids": ["a"]})
    batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
    entered, release = threading.Event(), threading.Event()
    original = execution.preview
    def slow_original_preview(payload):
        value = original(payload)
        entered.set()
        assert release.wait(5)
        return value
    monkeypatch.setattr(execution, "preview", slow_original_preview)
    worker = threading.Thread(target=gateway._step, args=(batch_id,))
    worker.start()
    readers = ThreadPoolExecutor(max_workers=5)
    try:
        assert entered.wait(3)
        futures = [readers.submit(gateway.list), readers.submit(gateway.status), readers.submit(gateway.get, batch_id),
            readers.submit(gateway.registration_preview, {"bundle_ids": ["b"]})]
        values = [future.result(timeout=1) for future in futures]
        assert values[0]["batches"][0]["entries"][0]["state"] == "selected"
        assert values[1]["batches"][0]["company_counts"]["owner_ready"] == 0
        assert values[2]["batch_id"] == batch_id and values[2]["projection_is_dispatch_permission"] is False
        assert values[3]["owner_inspected"] is False
        control = readers.submit(gateway.control, batch_id, "pause")
        with pytest.raises(DashboardBatchError) as raised:
            control.result(timeout=1)
        assert raised.value.code == "batch_control_busy"
        assert execution.preview_calls == ["a"] and execution.started == []
    finally:
        gateway.close()
        release.set()
        worker.join(timeout=3)
        readers.shutdown(wait=True)
    assert not worker.is_alive() and execution.started == []


def test_read_projection_retries_transient_windows_permission_without_returning_fake_empty(setup, monkeypatch):
    gateway, execution = setup
    plan = gateway.registration_preview({"bundle_ids": ["a"]})
    batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
    original = Path.read_bytes
    failures = 0
    def contended_read(path):
        nonlocal failures
        if path.name == batch_id + ".json" and failures < 2:
            failures += 1
            raise PermissionError("simulated transient Windows file reader")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", contended_read)
    assert gateway.get(batch_id)["entries"][0]["state"] == "selected"
    assert failures == 2 and execution.preview_calls == []
    def denied_read(path):
        if path.name == batch_id + ".json":
            raise PermissionError("simulated persistent file permission")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", denied_read)
    with pytest.raises(DashboardBatchError) as raised:
        gateway.list()
    assert raised.value.code == "batch_record_corrupt"
    assert execution.preview_calls == [] and execution.started == []


@pytest.mark.parametrize("companies,with_security", [(2000, False), (2000, True), (2500, True)])
def test_maximum_engineering_pool_completed_record_round_trip_has_capacity_headroom(tmp_path, companies, with_security):
    """Synthetic production-length IDs, completed timestamps and thin owner checks.

    This is an orchestration capacity proof, not real answers or owner qualification.
    Fake inspections below run in memory; no CLI, database or API is invoked.
    """
    execution = FakeExecution()
    bundles = registered_pool(execution, companies, with_security)
    for index, (_, value) in enumerate(execution.bundles.items()):
        company = index // (2 if with_security else 1)
        entity_id = "ENT_" + format(company, "032x")
        security_id = "SEC_" + format(company, "032x") + "_XSHE"
        value.update(entity_id=entity_id, scope_id=entity_id if value["scope"] == "entity" else security_id,
            security_id=security_id if value["scope"] == "security" else None, ready=True)
        value["expected_scope_bindings"] = [{"scope": "entity", "scope_id": entity_id}]
        if with_security:
            value["expected_scope_bindings"].append({"scope": "security", "scope_id": security_id})
    gateway = BatchGateway(execution, tmp_path / "batch", autostart=False)
    restarted = None
    try:
        plan = gateway.registration_preview({"bundle_ids": bundles})
        batch_id = gateway.start({"preview_id": plan["preview_id"]})["batch"]["batch_id"]
        record = gateway._record(batch_id)
        assert execution.preview_calls == [] and execution.started == []
        for index, entry in enumerate(record["entries"]):
            entry["launch_requested_at"] = "2026-10-25T00:00:00.000000Z"
            gateway._attach(entry, [{"bundle_id": entry["bundle_id"], "entity_id": entry["entity_id"],
                "bundle_fingerprint": entry["bundle_fingerprint"], "run_id": "run-" + format(index, "032x"),
                "process_state": "process_exited", "exit_code": 0}])
            assert set(entry["last_inspection"]) == {
                "can_start", "readonly_recovery", "inspection_sha256", "blocked_reasons"}
        gateway._settle(record)
        gateway._save(record)
        path = gateway.state_root / (batch_id + ".json")
        assert path.stat().st_size < dashboard_batches.MAX_RECORD_BYTES * 0.75
        gateway.close()
        restarted = BatchGateway(execution, gateway.state_root, autostart=False)
        restored = restarted.get(batch_id)
        assert restored["scope_counts"]["total"] == restored["scope_counts"]["owner_ready"] == len(bundles)
        assert restored["company_counts"]["total"] == restored["company_counts"]["owner_ready"] == companies
        assert all(group["complete"] for group in restored["company_groups"])
        assert len(restored["entries"]) == len(bundles) and restored["state"] == "owner_ready"
        assert restarted.list()["total"] == 1 and execution.started == []
    finally:
        gateway.close()
        if restarted:
            restarted.close()


def test_batch_record_read_and_write_share_byte_limit_and_oversize_preserves_old_record(tmp_path, monkeypatch):
    path = tmp_path / "batch-record.json"
    value = {"message": "原owner检查"}
    expected = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf8")
    monkeypatch.setattr(dashboard_batches, "MAX_RECORD_BYTES", len(expected))
    dashboard_batches._write(path, value)
    assert path.read_bytes() == expected and dashboard_batches._read(path) == value
    with pytest.raises(ValueError, match="batch_record_too_large"):
        dashboard_batches._write(path, {"message": "原owner检查多"})
    assert path.read_bytes() == expected and list(tmp_path.glob("*.pending")) == []
    # Reader uses the same byte bound, including UTF-8 and the final newline.
    path.write_bytes(expected + b" ")
    with pytest.raises(ValueError, match="batch_record_too_large"):
        dashboard_batches._read(path)


def test_all_original_inspection_paths_persist_only_necessary_status_not_scope_identity(setup):
    gateway, execution = setup
    required = {"can_start", "readonly_recovery", "inspection_sha256", "blocked_reasons"}
    first = gateway.start({"preview_id": gateway.registration_preview({"bundle_ids": ["a"]})["preview_id"]})["batch"]["batch_id"]
    gateway._step(first)
    assert set(gateway.get(first)["entries"][0]["last_inspection"]) == required
    execution.finish("a")
    gateway._step(first)
    assert set(gateway.get(first)["entries"][0]["last_inspection"]) == required
    second = gateway.start({"preview_id": gateway.registration_preview({"bundle_ids": ["b"]})["preview_id"]})["batch"]["batch_id"]
    gateway._step(second)
    execution.bundles["b"]["ready"] = True
    execution.runs.clear()  # Missing launch reference requires original inspection.
    gateway._step(second)
    restored = gateway.get(second)["entries"][0]
    assert restored["state"] == "owner_ready" and set(restored["last_inspection"]) == required


def retirement_fixture(gateway, execution):
    original_preview = execution.preview
    def checked(payload):
        value = original_preview(payload)
        value['inspection'] = {'work_items': {'Q1': {'status': 'leased' if execution.bundles[payload['bundle_id']]['unknown'] else 'pending'}}}
        return value
    execution.preview = checked
    batch_id = start(gateway, ('a',))
    gateway._step(batch_id)
    execution.finish('a', ready=False, exit_code=1)
    gateway.control(batch_id, 'pause')
    return batch_id


def test_abandon_stopped_batch_preserves_work_and_allows_fresh_same_entity(setup):
    gateway, execution = setup
    batch_id = retirement_fixture(gateway, execution)
    before = json.loads(gateway._path(batch_id).read_text())
    started = list(execution.started)
    result = gateway.control(batch_id, 'abandon')
    saved = json.loads(gateway._path(batch_id).read_text())
    assert result['batch']['state'] == 'abandoned'
    assert saved['entries'] == before['entries']
    assert saved['selection_sha256'] == before['selection_sha256']
    assert result['API_requests'] == 0 and execution.started == started
    assert result['batch']['allowed_actions'] == []
    execution.bundles['b']['entity_id'] = 'ENT_a'
    fresh = start(gateway, ('b',))
    assert fresh != batch_id and execution.started == started
    assert gateway.control(batch_id, 'abandon')['status'] == 'already_abandoned'
    with pytest.raises(DashboardBatchError):
        gateway.control(batch_id, 'resume')


@pytest.mark.parametrize('evidence', ['present', 'present_exited', 'unknown'])
def test_abandon_never_releases_unknown_or_extant_process(setup, monkeypatch, evidence):
    gateway, execution = setup
    batch_id = retirement_fixture(gateway, execution)
    next(iter(execution.runs.values())).update(process_state='needs_original_inspection', pid=12345)
    monkeypatch.setattr(dashboard_batches, '_process_recovery_evidence', lambda *_: evidence)
    before = gateway._path(batch_id).read_bytes()
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, 'abandon')
    assert raised.value.code == 'batch_abandon_process_unresolved'
    assert gateway._path(batch_id).read_bytes() == before


def test_abandon_absent_process_still_refuses_original_unknown_work(setup, monkeypatch):
    gateway, execution = setup
    batch_id = retirement_fixture(gateway, execution)
    next(iter(execution.runs.values())).update(process_state='needs_original_inspection', pid=12345)
    monkeypatch.setattr(dashboard_batches, '_process_recovery_evidence', lambda *_: 'absent')
    execution.bundles['a']['unknown'] = True
    before = gateway._path(batch_id).read_bytes()
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, 'abandon')
    assert raised.value.code == 'batch_abandon_work_unresolved'
    assert gateway._path(batch_id).read_bytes() == before


def test_abandon_requires_pause_and_complete_original_reference(setup):
    gateway, execution = setup
    batch_id = start(gateway, ('a',))
    before = gateway._path(batch_id).read_bytes()
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, 'abandon')
    assert raised.value.code == 'batch_abandon_pause_required'
    assert gateway._path(batch_id).read_bytes() == before
    gateway._step(batch_id)
    gateway.control(batch_id, 'pause')
    execution.runs.clear()
    before = gateway._path(batch_id).read_bytes()
    with pytest.raises(DashboardBatchError) as raised:
        gateway.control(batch_id, 'abandon')
    assert raised.value.code == 'batch_abandon_reference_unresolved'
    assert gateway._path(batch_id).read_bytes() == before


def test_legacy_deferred_proof_retains_original_reason_until_later_explicit_resume(tmp_path):
    class DeferredLegacy(FakeExecution):
        def inspect_legacy_prelaunch(self,entry):
            if entry['blocked_reasons']!=['execution_not_ready'] or not self.bundles['a']['budget']:return None
            return {'protocol':'iqs.prelaunch_reconciliation/1.0.0','status':'local_refusal_reconciled','bundle_id':entry['bundle_id'],'bundle_fingerprint':entry['bundle_fingerprint'],'launch_requested_at':entry['launch_requested_at'],'recorded_code':'execution_not_ready','current_preflight_sha256':'e'*64,'original_references_absent':True,'past_HTTP_history_attested':False,'API_requests':0,'database_writes':0}
    execution=DeferredLegacy();g=BatchGateway(execution,tmp_path/'batches',autostart=False)
    try:
        bid=start(g,('a',));r=g._record(bid);entry=r['entries'][0]
        entry.update(state='blocked',run_id=None,launch_uncertain=True,launch_requested_at='2026-10-27T00:00:00Z',blocked_reasons=['execution_not_ready'])
        r['state']='blocked';g._save(r)
        execution.bundles['a']['budget']=False
        g.control(bid,'resume')
        pending=row(g,bid)['entries'][0]
        assert pending['launch_uncertain'] is True and pending['blocked_reasons']==['execution_not_ready']
        assert execution.started==[]
        execution.bundles['a']['budget']=True
        g.control(bid,'resume')
        recovered=row(g,bid)['entries'][0]
        assert recovered['launch_uncertain'] is False and recovered['state']=='selected'
        assert execution.started==[]
    finally:g.close()
