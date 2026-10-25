"""Independent counterexample. Only a temporary fake owner subprocess is run."""
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("review_execution_fixture", ROOT / "tests/test_dashboard_execution.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

with tempfile.TemporaryDirectory(prefix="unknown-resume-", dir=Path(__file__).parent) as temporary:
    config, runtime, bundle = fixture.deployment.__wrapped__(Path(temporary))
    gateway = fixture.ExecutionGateway(config)
    state = Path(config["state_root"])
    state.mkdir()
    run_id = "run-" + "a" * 32
    folder = state / run_id
    folder.mkdir()
    record = {
        "protocol": "iqs.dashboard_process_reference/1.0.0", "run_id": run_id,
        "bundle_id": "test", "bundle_fingerprint": gateway._fingerprint(bundle),
        "process_state": "needs_original_inspection", "launcher_state": "paused",
        "result_path": str(folder / "result.json"), "log_path": str(folder / "process.log"),
    }
    fixture.gateway_module._write(state / (run_id + ".json"), record)
    before = gateway.tasks()["tasks"][0]
    try:
        result = gateway.control(run_id, "resume")
        fixture.wait_done(gateway, run_id)
        error_code = None
    except fixture.DashboardExecutionError as error:
        result, error_code = {"process_started": False}, error.code
    report = {"allowed_actions_before": before["allowed_actions"],
              "original_state": "needs_original_inspection", "original_work": [],
              "readonly_recovery": before["owner_preview"]["readonly_recovery"],
              "control_process_started": result["process_started"],
              "error_code": error_code,
              "fake_process_calls": len((runtime / "calls.txt").read_text().splitlines()) if (runtime / "calls.txt").exists() else 0,
              "paid_API_calls": 0}
    print(json.dumps(report))
