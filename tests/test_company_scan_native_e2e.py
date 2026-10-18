"""Original public owner + SDK + Runner + process-death/cache recovery.

Synthetic company/evidence and scripted vendor wire only. The approval, native
SQLite, SDK, pack transport, intent binding and Runner are the original code.
Run only in an explicitly owned three-component runtime, never production DBs.
"""

import importlib.util
import json
import os
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

if os.environ.get("IQS_C06_RUN_INTEGRATION") != "1":
    pytest.skip("requires explicitly owned three-component runtime", allow_module_level=True)

_ENV_NAMES = (
    "SystemRoot",
    "SYSTEMROOT",
    "WINDIR",
    "PATH",
    "TEMP",
    "TMP",
    "PYTHONUTF8",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONPATH",
    "IQS_C06_RUN_INTEGRATION",
    "IQS_C06_OWN",
    "IQS_C06_COMPOSITION_CODE_ROOT",
    "IQS_C06_COMPANY_ROOT",
    "IQS_C06_BRIDGE_ROOT",
)
SAFE_ENV = {name: os.environ[name] for name in _ENV_NAMES if name in os.environ}
# This is an explicitly isolated test process. Original fixture code also uses
# dict(os.environ); constrain that process before importing any fixture/client.
os.environ.clear()
os.environ.update(SAFE_ENV)

OWN = Path(os.environ["IQS_C06_OWN"])
CODE = Path(os.environ["IQS_C06_COMPOSITION_CODE_ROOT"])
COMPANY = Path(os.environ["IQS_C06_COMPANY_ROOT"])
BRIDGE = Path(os.environ["IQS_C06_BRIDGE_ROOT"])
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

from tests.delegated_fixture import setup_delegated as setup_admission
from tests.integration.test_c06_subject_public_e2e import actual
from tests.unit.test_quick_scan_budget import _policy


def construct(config):
    owner = prepare_execution(
        config["deployment"],
        config["confirmation_id"],
        input_paths={
            name: Path(config["bundle"]) / name
            for name in (
                "manifest.json",
                "identity.json",
                "authority.json",
                "owner-config.json",
                "questions.json",
            )
        },
        process_env=dict(SAFE_ENV),
    )
    first = owner.requested_question_ids[0]
    ref = owner.native.observation_context["questions"][first]["subject_binding"]["subject_ref"]
    policy = config["policy"]
    route = policy["routes"][0]
    lifecycle = QuickScanWorkLifecycle(
        owner.service.store,
        entity_id=ref["entity_id"],
        run_id="NATIVE_SCAN_2",
        scan_id="NATIVE_SCAN_2_SCAN",
        identity=owner.bundle["identity"],
        transport_managed=True,
        route_id=route["id"],
        provider_name=route["provider_config_ref"],
        model_requested="mimo-v2.6-pro",
        budget_policy=policy,
        budget_route=route,
        owner_refresh_session=owner,
        observation_context=owner.native.observation_context,
        scope_by_question=owner.scope_bindings,
        generation_by_question={
            qid: owner.existing_work(qid)["generation"] for qid in owner.requested_question_ids
        },
    )
    task = factory.create_company_scan_task(
        lifecycle,
        experiment_id="native-scan-software-e2e",
        run_id="NATIVE_SCAN_DYNAMIC",
        max_questions_per_pack=1,
    )
    client = LLMClient(
        "SCRIPTED-NOT-A-SECRET",
        "mimo-v2.6-pro",
        "https://api.xiaomimimo.com/v1/chat/completions",
        provider_name="mimo",
        timeout=10,
    )
    services = OwnerResearchServices(
        lifecycle,
        client,
        task=task,
        cost_resolver=lambda _: dict(
            actual_cost=0.001,
            pricing_ref=policy["cost_policy"]["pricing_ref"],
            source_ref="synthetic-software-e2e",
        ),
    )
    return task, services


def child_run(config_path, phase):
    config = json.loads(Path(config_path).read_text(encoding="utf8"))
    base = Path(config["root"])
    task, services = construct(config)
    from iqs_company_agent_lab import synthfixtures as sf
    from src.providers import llm_research_client as sdk

    posts = []

    class Response:
        status_code = 200
        headers = {"x-request-id": "scripted-native-scan-2"}

        def __init__(self, selected):
            answers = [
                sf.gen_insufficient(row["question"])
                for row in task.questions
                if row["question_id"] in selected
            ]
            for answer in answers:
                answer["status"] = "not_applicable"
                answer["information_as_of"] = task.raw["information_cutoff"]
                answer["summary"] = "[Synthetic software fixture] No real company finding."
            self.content = json.dumps(
                dict(
                    id="scripted-native-owner-response",
                    model="mimo-v2.6-pro",
                    choices=[
                        dict(
                            message=dict(
                                role="assistant",
                                content=json.dumps(
                                    {"answers": answers, "declared_question_ids": selected}
                                ),
                                reasoning_content="PRIVATE-NATIVE-REASONING-NEVER-PERSIST",
                            ),
                            finish_reason="stop",
                        )
                    ],
                    usage=dict(
                        prompt_tokens=1200,
                        prompt_tokens_details=dict(cached_tokens=400),
                        completion_tokens=1200,
                        completion_tokens_details=dict(reasoning_tokens=200),
                    ),
                )
            ).encode("utf8")

        def raise_for_status(self):
            pass

    class Wire:
        def post(self, *args, **kwargs):
            posts.append(1)
            context = json.loads(kwargs["json"]["messages"][-1]["content"].splitlines()[-1])
            selected = context["requested_question_ids"]
            if phase != "crash" and task.question_ids[0] in selected:
                raise AssertionError("native saved first response must never be posted again")
            assert kwargs["json"]["thinking"] == {"type": "enabled"}
            assert len(kwargs["json"]["messages"]) >= 2
            return Response(selected)

    sdk.http_client_manager.get_metered_sync_session = lambda: Wire()
    session = dict(
        protocol="iqs.agent-runtime-lab.session-config/1.0.0",
        planned_model="mimo-v2.6-pro",
        endpoint_profile_id="mimo-v2.6-pro@https://api.xiaomimimo.com/v1/chat/completions",
        max_output_tokens=4096,
        session_input_tokens=240000,
        session_output_tokens=48000,
        wall_seconds=900,
        logical_clock=False,
    )
    if phase == "crash":
        original = services.observe_native_step

        def die_after_native_commit(step):
            ref = original(step)
            (base / "crash-native-proof.json").write_text(
                json.dumps({"native_reference": ref, "scripted_posts": len(posts)}), encoding="utf8"
            )
            os._exit(86)

        services.observe_native_step = die_after_native_commit
        engine.execute_shared_engine(
            task,
            services,
            session,
            base / "unused-export",
            session_dir=base / "crashed-session",
            transport_origin="scripted_wire",
        )
        raise AssertionError("child did not die at native response boundary")
    result = engine.resume_shared_engine(
        task,
        services,
        session,
        base / "crashed-session/checkpoint.json",
        base / "recovered-export",
        session_dir=base / "recovered-session",
        transport_origin="scripted_wire",
    )
    from iqs_company_agent_lab.reporter import generate_report

    report = generate_report(base / "recovered-export", base / "recovered-report")
    assert result["all_slots_completed"] and len(posts) == 1
    summary = result["runtime_summary"]
    assert summary["new_model_http"] == 1 and summary["replayed_native_attempts"] == 1
    assert summary["runtime_origin"] == "scripted_wire"
    assert (
        not summary["owner_authority_verified"] and not summary["financial_qualification_granted"]
    )
    assert summary["cash_cost"] is None
    assert report["runtime_observations"] == summary
    with closing(services.store._connect()) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0] == 2
        )
    for qid in task.question_ids:
        assert (
            services.store.get_answer_checkpoint(services.owner.existing_work(qid)["work_item_id"])
            is None
        )
    result_payload = dict(
        scripted_posts=len(posts),
        slots=len(result["run"]["slots"]),
        runtime_summary=summary,
        original_owner_rechecked=True,
        official_search_checkpoint_created=False,
    )
    (base / "recovery-result.json").write_text(json.dumps(result_payload), encoding="utf8")


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_original_dynamic_scan_owner_sdk_process_resume_no_duplicate_http(actual, tmp_path):
    # Native owner quotes conservatively for both selected fields before the pack
    # executor reduces physical HTTP to independent sends. The isolated synthetic budget must
    # cover that upper bound; do not weaken the original admission policy.
    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    prepared = setup_admission(
        actual, tmp_path, policy=policy, provider="mimo", selected_question_count=2
    )
    accepted = RefreshAdmissionService(
        prepared["deployment_file"], process_env=dict(SAFE_ENV)
    ).admit(prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    config = dict(
        deployment=str(prepared["deployment_file"]),
        bundle=str(prepared["bundle"]),
        confirmation_id=prepared["consent"]["confirmation_id"],
        policy=policy,
        root=str(tmp_path),
    )
    config_file = tmp_path / "owned-native-test.json"
    config_file.write_text(json.dumps(config), encoding="utf8")
    for phase, expected in (("crash", 86), ("resume", 0)):
        completed = subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), phase, str(config_file)],
            cwd=OWN / "qa",
            capture_output=True,
            env=dict(SAFE_ENV, PYTHONDONTWRITEBYTECODE="1"),
            timeout=900,
        )
        (tmp_path / (phase + ".stdout.log")).write_bytes(completed.stdout[-16000:])
        (tmp_path / (phase + ".stderr.log")).write_bytes(completed.stderr[-16000:])
        assert completed.returncode == expected, completed.stderr[-4000:].decode(errors="replace")
    payload = json.loads((tmp_path / "recovery-result.json").read_text(encoding="utf8"))
    assert payload["slots"] == 2 and payload["scripted_posts"] == 1
    assert payload["official_search_checkpoint_created"] is False
    assert json.loads((tmp_path / "crash-native-proof.json").read_text())["scripted_posts"] == 1
    for file in (tmp_path / "recovered-export").iterdir():
        if file.is_file():
            assert b"PRIVATE-NATIVE-REASONING" not in file.read_bytes()


if __name__ == "__main__":
    child_run(sys.argv[2], sys.argv[1])
