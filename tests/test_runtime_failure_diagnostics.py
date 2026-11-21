"""Runtime diagnostics explain failures without becoming execution prerequisites."""

from contextlib import nullcontext
import io
import json
from pathlib import Path
import sqlite3
import threading
from types import SimpleNamespace

import pytest

from scripts import dashboard_execution, dashboard_prepare
from scripts.dashboard_delivery_jobs import DeliveryJobs


SECRET = "sk-local-only-secret https://private.invalid/?token=never-log"


class Output:
    def __init__(self):
        self.read = []

    def __iter__(self):
        for line in ("first\n", SECRET + "\n", "last\n"):
            self.read.append(line)
            yield line


def original_process(tmp_path):
    gateway = object.__new__(dashboard_execution.ExecutionGateway)
    gateway.state_root = tmp_path
    gateway._lock = threading.RLock()
    gateway._control_lock = lambda _: nullcontext()
    record = {"run_id": "run-original", "launcher_state": "running",
              "process_state": "running", "log_path": str(tmp_path / "process.log")}
    path = tmp_path / "run-original.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    output = Output()
    waits = []

    def wait():
        assert len(output.read) == 3
        waits.append(True)
        return 0

    process = SimpleNamespace(stdout=output, wait=wait)
    gateway._processes = {record["run_id"]: process}
    return gateway, process, record, path, waits


@pytest.mark.parametrize("fault", ["open", "write", "flush"])
def test_optional_log_failure_never_stops_stdout_drain_or_process_wait(tmp_path, monkeypatch, fault):
    gateway, process, record, path, waits = original_process(tmp_path)
    original_open = Path.open

    class BrokenLog(io.StringIO):
        def write(self, _):
            if fault == "write":
                raise OSError(13, SECRET)
            return 1

        def flush(self):
            if fault == "flush":
                raise OSError(13, SECRET)

    def opening(target, *args, **kwargs):
        if target == Path(record["log_path"]):
            if fault == "open":
                raise OSError(13, SECRET)
            return BrokenLog()
        return original_open(target, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opening)
    gateway._finish(process, path, record)
    assert waits == [True]
    final = json.loads(path.read_text(encoding="utf-8"))
    assert final["process_state"] == "process_exited" and final["exit_code"] == 0
    assert final["log_tracking_incomplete"] is True
    assert final["work_completion_authoritative"] is False
    assert not gateway._processes


def test_error_projection_keeps_cause_location_not_messages_or_locals():
    from iqs_scan.foundation.api import exception_diagnostic

    local_secret = SECRET
    try:
        try:
            raise sqlite3.OperationalError(local_secret)
        except sqlite3.Error:
            raise RuntimeError(SECRET)
    except RuntimeError as error:
        diagnostic = exception_diagnostic(error)
    encoded = json.dumps(diagnostic)
    assert "OperationalError" in encoded and "RuntimeError" in encoded
    assert "test_error_projection_keeps_cause_location_not_messages_or_locals" in encoded
    assert SECRET not in encoded and "private.invalid" not in encoded


def test_owner_wrapper_retains_safe_diagnostic_and_native_cause(tmp_path, monkeypatch):
    gateway = object.__new__(dashboard_execution.ExecutionGateway)
    gateway.state_root = tmp_path
    source = PermissionError(13, SECRET)

    def unavailable(*_args, **_kwargs):
        raise source

    monkeypatch.setattr(dashboard_execution.subprocess, "run", unavailable)
    with pytest.raises(dashboard_execution.DashboardExecutionError) as caught:
        gateway._call(["unused"], tmp_path, tmp_path)
    assert caught.value.code == "owner_transport_unavailable"
    assert caught.value.__cause__ is source
    diagnostic = caught.value.details["failure_diagnostic"]
    assert diagnostic["recorded"] is True
    assert "PermissionError" in json.dumps(diagnostic)
    assert SECRET not in json.dumps(diagnostic)
    assert list((tmp_path / "diagnostics").glob("*.jsonl"))


def test_prepare_wrapper_retains_original_safe_failure_without_raw_stderr(tmp_path, monkeypatch):
    config = {"stockqa_root": str(tmp_path), "state_root": str(tmp_path / "state"),
              "prepare": {"runtime_dir": str(tmp_path)}}
    source = OSError(13, SECRET)

    def unavailable(*_args, **_kwargs):
        raise source

    monkeypatch.setattr(dashboard_prepare.subprocess, "run", unavailable)
    with pytest.raises(dashboard_prepare.DashboardPrepareError) as caught:
        dashboard_prepare._native_cli(config, "qa", "src.utils.owner", [])
    assert caught.value.code == "native_transport_unavailable"
    assert caught.value.__cause__ is source
    diagnostic = caught.value.details["failure_diagnostic"]
    assert diagnostic["recorded"] is True and "OSError" in json.dumps(diagnostic)
    assert SECRET not in json.dumps(diagnostic)


def test_diagnostic_output_failure_is_nonblocking_and_records_incomplete(tmp_path, monkeypatch, capsys):
    from iqs_scan.foundation.api import record_operation_failure

    original_open = Path.open

    def broken(target, *args, **kwargs):
        if target.suffix == ".jsonl":
            raise OSError(13, SECRET)
        return original_open(target, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken)
    diagnostic = record_operation_failure(RuntimeError(SECRET), "test", directory=tmp_path)
    assert diagnostic["recorded"] is False
    assert "tracking incomplete" in capsys.readouterr().err
    assert SECRET not in json.dumps(diagnostic)


def test_delivery_worker_records_owner_failure_while_preserving_original_job(tmp_path):
    class Execution:
        def bundle_registration(self, bundle_id):
            return {"bundle_id": bundle_id, "entity_id": "ENT_TEST", "bundle_fingerprint": "a" * 64}

    def fail(_):
        raise OSError(13, SECRET)

    jobs = DeliveryJobs(Execution(), tmp_path, "b" * 64, fail, lambda _: None)
    job = jobs.submit({"bundle_id": "original"})["job"]
    worker = jobs._threads.get(job["job_id"])
    if worker:
        worker.join(5)
    final = jobs.get(job["job_id"])
    assert final["state"] == "partial" and final["model_calls"] == 0
    assert final["entries"][0]["error_code"] == "delivery_interrupted"
    assert final["entries"][0]["failure_diagnostic"]["recorded"] is True
    assert SECRET not in json.dumps(final)
