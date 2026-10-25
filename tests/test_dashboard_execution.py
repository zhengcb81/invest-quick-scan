"""Product execution boundary tests; every child is a temporary fake owner CLI."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("iqs_dashboard_execution_test", ROOT / "scripts/dashboard_execution.py")
gateway_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway_module)
ExecutionGateway = gateway_module.ExecutionGateway
DashboardExecutionError = gateway_module.DashboardExecutionError


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


@pytest.fixture
def deployment(tmp_path):
    source, runtime, bundle_dir = (tmp_path / name for name in ("source", "runtime", "bundle"))
    for folder in (source, runtime, bundle_dir):
        folder.mkdir()
    for folder in (source / "src", source / "src/utils", source / "src/config"):
        folder.mkdir(exist_ok=True)
        (folder / "__init__.py").write_text("")
    (source / "src/utils/quick_scan_refresh_inspect_cli.py").write_text('''
import json, pathlib, sys
request = json.loads(pathlib.Path(sys.argv[sys.argv.index("--request") + 1]).read_text())
assert not any("KEY" in name for name in __import__("os").environ)
print(json.dumps({"protocol":"stockqa.refresh_inspection/1.0.0", "API_requests":0, "reservation_created":False,
 "quote":{"budget_available":request.get("available", True), "max_http_requests":2}, "work_items":request.get("work_items", [])}))
''', encoding="utf-8")
    (source / "main_with_llm.py").write_text('''
import argparse, json, os, pathlib, sys, time
pathlib.Path("calls.txt").open("a").write("1\\n")
print("key=" + os.environ.get("MODEL_API_KEY", "none"), flush=True)
print("Bearer abcdefghijklmnopqrstuvwxyz", flush=True)
time.sleep(0.08)
pathlib.Path(sys.argv[sys.argv.index("--output")+1]).write_text(json.dumps({"argv":sys.argv[1:]}))
''', encoding="utf-8")
    (source / "src/config/llm_config.py").write_text('''
import json, pathlib
class LLMConfig:
 def __init__(self, path): self.path=pathlib.Path(path)
 @staticmethod
 def _validate_quick_scan_policy(value):
  if not isinstance(value,dict) or set(value)!={"models"}: raise ValueError("invalid")
 def save_quick_scan_model_policy(self, policy):
  self._validate_quick_scan_policy(policy)
  data=json.loads(self.path.read_text());data["quick_scan_model_policy"]=policy;self.path.write_text(json.dumps(data))
''', encoding="utf-8")
    llm = put(runtime / "llm_apis.json", {"providers": {"test": {"api_key": "never-return-this"}}, "quick_scan_model_policy": {"models": ["first", "second"]}})
    ledger, policy = put(tmp_path / "ledger.sqlite", {}), put(tmp_path / "policy.json", {})
    bundle = {"entity_id": "ENT_TEST", "company": "Test Corporation", "provider": "test", "confirmation_id": "confirm-1"}
    for key in ("questions", "manifest", "identity_snapshot", "c06_authority", "owner_config", "spend_authorization", "inspection_request"):
        bundle[key] = put(bundle_dir / (key + ".json"), {"entity_id": "ENT_TEST"} if key in {"identity_snapshot", "inspection_request"} else {})
    bundle["admission_config"] = put(bundle_dir / "admission.json", {"work_store": ledger, "budget_policy_file": policy})
    config = {"stockqa_root": str(source), "stockqa_python": sys.executable, "runtime_dir": str(runtime),
              "state_root": str(tmp_path / "state"), "model_policy_path": llm, "bundles": {"test": bundle}}
    return config, runtime, bundle


def wait_done(gateway, run_id):
    deadline = time.monotonic() + 8
    while run_id in gateway._processes and time.monotonic() < deadline:
        time.sleep(0.01)
    assert run_id not in gateway._processes


def start(gateway):
    preview = gateway.preview({"bundle_id": "test"})
    return gateway.start({"bundle_id": "test", "preview_id": preview["preview_id"]})


def test_unconfigured_status_and_read_do_not_create_state(tmp_path):
    gateway = ExecutionGateway({"state_root": str(tmp_path / "state")})
    assert gateway.status()["configured"] is False
    assert gateway.tasks()["tasks"] == []
    assert gateway.settings()["configured"] is False
    assert not (tmp_path / "state").exists()


def test_deployment_availability_is_distinct_from_registration(deployment):
    config, _, _ = deployment
    assert ExecutionGateway(config).status()['available'] is True
    config['runtime_dir'] = ''
    assert ExecutionGateway(config).status()['available'] is False


def test_first_policy_setup_is_editable_template_without_saving_or_enabling(deployment):
    config, runtime, _ = deployment
    path=runtime/'llm_apis.json'
    put(path,{'providers':{'test':{'api_key':'sentinel-do-not-return'}}})
    before=path.read_bytes()
    result=ExecutionGateway(config).settings()
    assert result['configured'] is False and result['editable'] is True
    assert result['needs_initial_policy'] is True and result['policy']['configured'] is False
    assert 'sentinel-do-not-return' not in json.dumps(result)
    assert path.read_bytes()==before


def test_unknown_persisted_process_cannot_resume_by_direct_post(deployment):
    config, runtime, _ = deployment
    gateway = ExecutionGateway(config)
    run_id = start(gateway)['run']['run_id']
    wait_done(gateway, run_id)
    record_path = Path(config['state_root']) / (run_id + '.json')
    record = json.loads(record_path.read_text(encoding='utf8'))
    record.update(process_state='needs_original_inspection', launcher_state='paused')
    put(record_path, record)
    restarted = ExecutionGateway(config)
    assert 'resume' not in restarted.tasks()['tasks'][0]['allowed_actions']
    with pytest.raises(DashboardExecutionError) as raised:
        restarted.control(run_id, 'resume')
    assert raised.value.code == 'original_process_unknown'
    assert (runtime/'calls.txt').read_text().splitlines() == ['1']


def test_preview_calls_only_original_inspector_and_keeps_ledger_bytes(deployment, monkeypatch):
    config, runtime, bundle = deployment
    monkeypatch.setenv("MODEL_API_KEY", "a-secret-key-value")
    ledger = Path(json.loads(Path(bundle["admission_config"]).read_text())["work_store"])
    before = ledger.read_bytes()
    result = ExecutionGateway(config).preview({"bundle_id": "test"})
    assert result["can_start"] and result["API_requests"] == 0
    assert ledger.read_bytes() == before
    assert not (runtime / "calls.txt").exists()
    assert not Path(config["state_root"]).exists()


@pytest.mark.parametrize("payload", [{"bundle_id": "test", "command": "anything"}, {"bundle_id": "../test"}, {"bundle_id": "test", "entity_id": "ENT_OTHER"}])
def test_browser_cannot_supply_commands_paths_or_other_entity(deployment, payload):
    config, runtime, _ = deployment
    with pytest.raises(DashboardExecutionError):
        ExecutionGateway(config).start(payload)
    assert not (runtime / "calls.txt").exists()


def test_missing_or_wrong_identity_and_config_block_before_launch(deployment):
    config, runtime, bundle = deployment
    put(Path(bundle["identity_snapshot"]), {"entity_id": "ENT_OTHER"})
    gateway = ExecutionGateway(config)
    assert "identity_entity_mismatch" in gateway.preview({"bundle_id": "test"})["missing"]
    with pytest.raises(DashboardExecutionError) as raised:
        start(gateway)
    assert raised.value.code == "preview_required"
    assert not (runtime / "calls.txt").exists()


def test_budget_block_is_not_zero_success(deployment):
    config, runtime, bundle = deployment
    put(Path(bundle["inspection_request"]), {"entity_id": "ENT_TEST", "available": False})
    result = ExecutionGateway(config).preview({"bundle_id": "test"})
    assert result["status"] == "blocked" and result["can_start"] is False
    assert not (runtime / "calls.txt").exists()


def test_start_is_fixed_argv_idempotent_and_logs_redact_secrets(deployment, monkeypatch):
    config, runtime, _ = deployment
    monkeypatch.setenv("MODEL_API_KEY", "a-secret-key-value")
    gateway = ExecutionGateway(config)
    preview = gateway.preview({"bundle_id": "test"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: gateway.start({"bundle_id": "test", "preview_id": preview["preview_id"]}), range(2)))
    assert sorted(result["status"] for result in results) == ["attached", "started"]
    run_id = results[0]["run"]["run_id"]
    wait_done(gateway, run_id)
    assert (runtime / "calls.txt").read_text().splitlines() == ["1"]
    row = gateway.tasks()["tasks"][0]
    assert row["process_state"] == "process_exited"
    assert row["work_completion_authoritative"] is False
    log = Path(row["log_path"]).read_text()
    assert "a-secret-key-value" not in log and "abcdefghijklmnopqrstuvwxyz" not in log
    argv = json.loads(Path(row["result_path"]).read_text())["argv"]
    assert "--require-search" in argv and argv[argv.index("--thinking-enabled")+1] == "true"
    assert gateway.start({"bundle_id": "test"})["process_started"] is False


def test_restart_never_reposts_unknown_process_and_controls_do_not_kill(deployment):
    config, runtime, _ = deployment
    child = Path(config['stockqa_root'])/'main_with_llm.py'
    source = child.read_text(encoding='utf8')
    child.write_text(source.replace('time.sleep(0.08)',
        'deadline=time.monotonic()+10\nwhile not pathlib.Path("release-child").exists() and time.monotonic()<deadline: time.sleep(0.01)'), encoding='utf8')
    gateway = ExecutionGateway(config)
    result = start(gateway)
    run_id = result["run"]["run_id"]
    restarted = ExecutionGateway(config)
    assert restarted.tasks()["tasks"][0]["process_state"] == "needs_original_inspection"
    assert restarted.start({"bundle_id": "test"})["status"] == "attached"
    assert restarted.control(run_id, "pause")["state"] == "draining"
    with pytest.raises(DashboardExecutionError) as raised:
        restarted.control(run_id, "resume")
    assert raised.value.code == "original_process_unknown"
    assert restarted.control(run_id, "inspect")["preview"]["API_requests"] == 0
    (runtime/'release-child').write_text('release')
    wait_done(gateway, run_id)
    assert (runtime / "calls.txt").read_text().splitlines() == ["1"]


def test_pause_drains_company_then_resume_rechecks_original(deployment):
    config, runtime, bundle = deployment
    gateway = ExecutionGateway(config)
    result = start(gateway)
    run_id = result["run"]["run_id"]
    assert gateway.control(run_id, "pause")["state"] == "draining"
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.control(run_id, "resume")
    assert raised.value.code == "company_still_draining"
    wait_done(gateway, run_id)
    assert gateway.tasks()["tasks"][0]["launcher_state"] == "paused"
    # Real ledger state changes, not the immutable registered request file.
    source = Path(config["stockqa_root"]) / "src/utils/quick_scan_refresh_inspect_cli.py"
    original = source.read_text()
    source.write_text(original.replace('request.get("work_items", [])', '[{"status":"uncertain"}]'))
    assert "resume" not in gateway.tasks()["tasks"][0]["allowed_actions"]
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.control(run_id, "resume")
    assert raised.value.code == "resume_blocked"
    assert len((runtime / "calls.txt").read_text().splitlines()) == 1
    source.write_text(original.replace('request.get("available", True)', 'False').replace('request.get("work_items", [])', '[{"status":"result_ready"}]'))
    assert "resume" in gateway.tasks()["tasks"][0]["allowed_actions"]
    assert gateway.control(run_id, "resume")["state"] == "running"
    wait_done(gateway, run_id)
    assert gateway.tasks()["tasks"][0]["launch_attempt"] == 2


def test_start_requires_original_preview_and_refuses_changed_plan(deployment):
    config, runtime, bundle = deployment
    gateway = ExecutionGateway(config)
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.start({"bundle_id": "test"})
    assert raised.value.code == "preview_required"
    preview = gateway.preview({"bundle_id": "test"})
    source = Path(config["stockqa_root"]) / "src/utils/quick_scan_refresh_inspect_cli.py"
    source.write_text(source.read_text().replace('request.get("work_items", [])', '[{"status":"pending"}]'))
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.start({"bundle_id": "test", "preview_id": preview["preview_id"]})
    assert raised.value.code == "preview_changed"
    assert not (runtime / "calls.txt").exists()


def test_owner_policy_read_write_preserves_provider_secret_and_uses_revision(deployment):
    config, runtime, _ = deployment
    gateway = ExecutionGateway(config)
    settings = gateway.settings()
    assert settings["policy"] == {"models": ["first", "second"]}
    assert "never-return-this" not in json.dumps(settings)
    changed = gateway.save_settings({"policy": {"models": ["second", "first"]}, "revision_sha256": settings["revision_sha256"]})
    assert changed["policy"]["models"] == ["second", "first"]
    assert json.loads((runtime / "llm_apis.json").read_text())["providers"]["test"]["api_key"] == "never-return-this"
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.save_settings({"policy": {"models": ["first"]}, "revision_sha256": settings["revision_sha256"]})
    assert raised.value.code == "settings_changed"
    assert not (runtime / "calls.txt").exists()


def test_settings_rejects_secret_fields_before_child(deployment):
    config, runtime, _ = deployment
    gateway = ExecutionGateway(config)
    original = (runtime / "llm_apis.json").read_bytes()
    with pytest.raises(DashboardExecutionError) as raised:
        gateway.save_settings({"policy": {"api_key": "not-allowed"}, "revision_sha256": "a"*64})
    assert raised.value.code == "settings_secret_forbidden"
    assert original == (runtime / "llm_apis.json").read_bytes()


def test_bad_original_inspection_is_an_error_not_fabricated_empty_success(deployment):
    config, _, _ = deployment
    source = Path(config["stockqa_root"])
    (source / "src/utils/quick_scan_refresh_inspect_cli.py").write_text('print("not-json")')
    with pytest.raises(DashboardExecutionError) as raised:
        ExecutionGateway(config).preview({"bundle_id": "test"})
    assert raised.value.code == "owner_transport_unavailable"


def test_corrupt_launch_reference_cannot_turn_into_new_start(deployment):
    config, runtime, _ = deployment
    state = Path(config["state_root"])
    state.mkdir()
    (state / ("run-" + "a"*32 + ".json")).write_text("{broken")
    gateway = ExecutionGateway(config)
    with pytest.raises(DashboardExecutionError) as raised:
        start(gateway)
    assert raised.value.code == "process_reference_corrupt"
    assert not (runtime / "calls.txt").exists()
