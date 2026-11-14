"""Original public owner + SDK + Runner + process-death/cache recovery.

Synthetic company/evidence and scripted vendor wire only. The approval, native
SQLite, SDK, pack transport, intent binding and Runner are the original code.
Run only in an explicitly owned three-component runtime, never production DBs.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

if os.environ.get("IQS_C06_RUN_INTEGRATION") != "1":
    pytest.skip("requires explicitly owned three-component runtime", allow_module_level=True)

_ENV_NAMES = ("SystemRoot", "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "PYTHONUTF8",
    "PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "IQS_C06_RUN_INTEGRATION", "IQS_C06_OWN",
    "IQS_C06_COMPOSITION_CODE_ROOT", "IQS_C06_COMPANY_ROOT", "IQS_C06_BRIDGE_ROOT")
SAFE_ENV = {name: os.environ[name] for name in _ENV_NAMES if name in os.environ}
OWN = Path(SAFE_ENV["IQS_C06_OWN"]).resolve()
CODE = Path(SAFE_ENV["IQS_C06_COMPOSITION_CODE_ROOT"]).resolve()
COMPANY = Path(SAFE_ENV["IQS_C06_COMPANY_ROOT"]).resolve()
BRIDGE = Path(SAFE_ENV["IQS_C06_BRIDGE_ROOT"]).resolve()
sys.path.insert(0, str(COMPANY / "src"))
sys.path.insert(0, str(BRIDGE / "src"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


engine = load("native_shared_engine", CODE / "scripts/shared_company_engine.py")
factory = load("native_shared_task", CODE / "scripts/shared_company_task.py")
from src.providers.llm_client import LLMClient
from src.runners.llm_runner import QuickScanWorkLifecycle
from src.utils.quick_scan_owner_research import OwnerResearchServices
from src.utils.quick_scan_refresh_admission import RefreshAdmissionService
from src.utils.quick_scan_refresh_execution import prepare_execution
from src.utils.quick_scan_owner_refresh_api import adapt_owner_refresh
from tests.integration.test_c06_subject_public_e2e import actual
from tests.integration.test_c06_refresh_admission import setup_admission
from tests.unit.test_quick_scan_budget import _policy


def construct(config):
    owner = prepare_execution(config["deployment"], config["confirmation_id"],
        input_paths={name: Path(config["bundle"]) / name for name in
            ("manifest.json", "identity.json", "authority.json", "owner-config.json", "questions.json")},
        process_env=dict(SAFE_ENV))
    owner_port = adapt_owner_refresh(owner)
    owner_snapshot = owner_port.snapshot()
    # This helper is a test composition root: the official QA CLI owns the
    # mutable store; its detached public snapshot intentionally omits it.
    first = owner_snapshot.requested_question_ids[0]
    ref = owner_snapshot.observation_context["questions"][first]["subject_binding"]["subject_ref"]
    policy = config["policy"]
    route = policy["routes"][0]
    lifecycle = QuickScanWorkLifecycle(owner.service.store, entity_id=ref["entity_id"],
        run_id="NATIVE_SHARED_12", scan_id="NATIVE_SHARED_12_SCAN", identity=owner_snapshot.bundle["identity"],
        transport_managed=True, route_id=route["id"], provider_name=route["provider_config_ref"],
        model_requested="mimo-v2.6-pro", budget_policy=policy, budget_route=route,
        owner_refresh_session=owner_port, observation_context=owner_snapshot.observation_context,
        scope_by_question=dict(owner_snapshot.scope_bindings),
        generation_by_question={qid: owner_port.existing_work(qid)["generation"] for qid in owner_snapshot.requested_question_ids})
    task = factory.create_native_task(lifecycle, experiment_id="native-shared-software-e2e",
        run_id="NATIVE_SHARED_12", strategy_id="free_agent")
    client = LLMClient("SCRIPTED-NOT-A-SECRET", "mimo-v2.6-pro",
        "https://api.xiaomimimo.com/v1/chat/completions", provider_name="mimo", timeout=10)
    services = OwnerResearchServices(lifecycle, client, task=task,
        cost_resolver=lambda _: dict(actual_cost=0.001, pricing_ref="scripted-native-rate",
                                     source_ref="synthetic-software-e2e"))
    return task, services


def _task_snapshot(task):
    """Use the Company Agent consumer DTO for opaque owner task handles."""
    from iqs_company_agent_lab.api import task_snapshot
    return task_snapshot(task)


def child_run(config_path, phase):
    config = json.loads(Path(config_path).read_text(encoding="utf8"))
    base = Path(config["root"])
    policy = config["policy"]
    task, services = construct(config)
    task_contract = _task_snapshot(task)
    from src.providers import llm_research_client as sdk
    from iqs_company_agent_lab import synthfixtures as sf
    posts = []

    class Response:
        status_code = 200
        headers = {"x-request-id": "scripted-native-owner-12"}
        def __init__(self):
            answers = [sf.gen_insufficient(row["question"]) for row in task_contract["questions"]]
            for answer in answers:
                answer["status"] = "not_applicable"
                answer["summary"] = "[Synthetic software fixture] No real company finding."
            self.content = json.dumps(dict(id="scripted-native-owner-response", model="mimo-v2.6-pro",
                choices=[dict(message=dict(role="assistant", content=json.dumps({"answers": answers,
                    "declared_question_ids": task_contract["question_ids"]}),
                    reasoning_content="PRIVATE-NATIVE-REASONING-NEVER-PERSIST"), finish_reason="stop")],
                usage=dict(prompt_tokens=1200, prompt_tokens_details=dict(cached_tokens=400),
                    completion_tokens=1200, completion_tokens_details=dict(reasoning_tokens=200)))).encode("utf8")
        def raise_for_status(self):
            pass

    class Wire:
        def post(self, *args, **kwargs):
            posts.append(1)
            if phase != "crash":
                raise AssertionError("native saved response must recover without another POST")
            assert kwargs["json"]["thinking"] == {"type": "enabled"}
            assert len(kwargs["json"]["messages"]) >= 2
            return Response()

    sdk.http_client_manager.get_metered_sync_session = lambda: Wire()
    session = dict(protocol="iqs.agent-runtime-lab.session-config/1.0.0", planned_model="mimo-v2.6-pro",
        endpoint_profile_id="mimo-v2.6-pro@https://api.xiaomimimo.com/v1/chat/completions",
        max_output_tokens=4096, session_input_tokens=240000, session_output_tokens=48000,
        wall_seconds=900, logical_clock=False)
    if phase == "crash":
        original = services.observe_native_step
        def die_after_native_commit(step):
            ref = original(step)
            (base / "crash-native-proof.json").write_text(json.dumps({"native_reference": ref,
                "scripted_posts": len(posts)}), encoding="utf8")
            os._exit(86)
        services.observe_native_step = die_after_native_commit
        engine.execute_shared_engine(task, services, session, base / "unused-export",
            session_dir=base / "crashed-session", transport_origin="scripted_wire")
        raise AssertionError("child did not die at native response boundary")
    result = engine.resume_shared_engine(task, services, session, base / "crashed-session/checkpoint.json",
        base / "recovered-export", session_dir=base / "recovered-session", transport_origin="scripted_wire")
    from iqs_company_agent_lab.reporter import generate_report
    report = generate_report(base / "recovered-export", base / "recovered-report")
    assert result["all_slots_completed"] and not posts
    summary = result["runtime_summary"]
    assert summary["new_model_http"] == 0 and summary["replayed_native_attempts"] == 1
    assert summary["runtime_origin"] == "scripted_wire"
    assert not summary["owner_authority_verified"] and not summary["financial_qualification_granted"]
    assert summary["cash_cost"] is None
    assert report["runtime_observations"] == summary
    assert services.store.get_quick_scan_budget_status(policy["policy_id"])["requests"] == 1
    assert len(posts) == 0, "cold replay must not send another model request"
    for qid in task_contract["question_ids"]:
        assert services.store.get_answer_checkpoint(services.owner.existing_work(qid)["work_item_id"]) is None
    result_payload = dict(scripted_posts=len(posts), slots=len(result["run"]["slots"]), runtime_summary=summary,
                          original_owner_rechecked=True, official_search_checkpoint_created=False)
    (base / "recovery-result.json").write_text(json.dumps(result_payload), encoding="utf8")


@pytest.mark.parametrize("actual", [{"observation_version": "1.2.0", "information_cutoff": "2026-10-13"}], indirect=True)
def test_original_twelve_owner_sdk_runner_and_process_resume_zero_new_http(actual, tmp_path):
    # Native owner quotes conservatively for all twelve fields before the pack
    # executor reduces physical HTTP to one. The isolated synthetic budget must
    # cover that upper bound; do not weaken the original admission policy.
    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo",
                               selected_question_count=12, information_cutoff="2026-10-13")
    accepted = RefreshAdmissionService(prepared["deployment_file"], process_env=dict(SAFE_ENV)).admit(
        prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    config = dict(deployment=str(prepared["deployment_file"]), bundle=str(prepared["bundle"]),
        confirmation_id=prepared["consent"]["confirmation_id"], policy=policy, root=str(tmp_path))
    config_file = tmp_path / "owned-native-test.json"
    config_file.write_text(json.dumps(config), encoding="utf8")
    for phase, expected in (("crash", 86), ("resume", 0)):
        stdout_path = tmp_path / (phase + ".stdout.log")
        stderr_path = tmp_path / (phase + ".stderr.log")
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                completed = subprocess.run(
                    [sys.executable, "-B", str(Path(__file__)), phase, str(config_file)],
                    cwd=OWN / "qa",
                    stdout=stdout,
                    stderr=stderr,
                    env=dict(SAFE_ENV, PYTHONDONTWRITEBYTECODE="1"),
                    timeout=600,
                )
        except subprocess.TimeoutExpired as error:
            diagnostic = stderr_path.read_bytes()[-4000:].decode(errors="replace")
            raise AssertionError(f"native {phase} child timed out: {diagnostic}") from error
        assert completed.returncode == expected, stderr_path.read_bytes()[-4000:].decode(errors="replace")
    payload = json.loads((tmp_path / "recovery-result.json").read_text(encoding="utf8"))
    assert payload["slots"] == 12 and payload["scripted_posts"] == 0
    assert payload["official_search_checkpoint_created"] is False
    assert json.loads((tmp_path / "crash-native-proof.json").read_text())["scripted_posts"] == 1
    for file in (tmp_path / "recovered-export").iterdir():
        if file.is_file():
            assert b"PRIVATE-NATIVE-REASONING" not in file.read_bytes()


if __name__ == "__main__":
    child_run(sys.argv[2], sys.argv[1])
