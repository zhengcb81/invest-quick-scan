"""Original public owner + SDK + Runner + process-death/cache recovery.

Synthetic company/evidence and scripted vendor wire only. The approval, native
SQLite, SDK, pack transport, intent binding and Runner are the original code.
Run only in an explicitly owned three-component runtime, never production DBs.
"""

import importlib.util
import copy
import hashlib
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
    external = None
    if config.get("external_policy"):
        from src.config.quick_scan_search_policy import load_search_policy
        from src.utils.quick_scan_provider_health import QuickScanProviderHealth

        external = dict(
            policy=load_search_policy(config["external_policy"]),
            model_policy=config.get("model_policy", policy),
            question_manifest_sha256=owner.bundle["manifest"]["manifest_sha256"],
            health_store=QuickScanProviderHealth(Path(config["root"]) / "search-health.sqlite"),
            unknown_reset_cooldown_seconds=60,
            rate_limit_cooldown_seconds=20,
        )
    lifecycle = QuickScanWorkLifecycle(
        owner.service.store,
        entity_id=ref["entity_id"],
        run_id=owner.record["inputs"]["run_id"],
        scan_id=owner.record["inputs"]["scan_id"],
        identity=owner.bundle["identity"],
        transport_managed=True,
        route_id=route["id"],
        provider_name=route["provider_config_ref"],
        model_requested="mimo-v2.6-pro",
        budget_policy=policy,
        budget_route=route,
        owner_refresh_session=owner,
        c06_authority=owner.bundle["authority"],
        observation_context=owner.native.observation_context,
        scope_by_question=owner.scope_bindings,
        generation_by_question={
            qid: owner.existing_work(qid)["generation"] for qid in owner.requested_question_ids
        },
        external_retrieval=external,
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


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_explicit_finalization_uses_actual_external_context_and_original_owner_checkpoint(
    actual, tmp_path, monkeypatch
):
    """Original software E2E, synthetic issuer and scripted provider wire only."""
    from src.config.quick_scan_search_policy import load_search_policy
    from src.utils.http_client import http_client_manager
    from tests.unit.test_external_search_provider import _response
    from tests.unit.test_quick_scan_external_context import _execution_policy_document
    from iqs_company_agent_lab import synthfixtures as sf

    from src.utils.quick_scan_external_context import build_shared_external_budget_policy
    import tests.delegated_fixture as delegated_fixture

    original_invoke = delegated_fixture.invoke

    def invoke_slow_windows_cli(command, directory, label, *, timeout=80, **extra):
        # Source/schema verification can exceed the historical 80-second test
        # cap on a busy Windows host. Only the harness wait changes; the actual
        # public owner CLI and all its permission checks remain untouched.
        return original_invoke(command, directory, label, timeout=max(timeout, 240), **extra)

    monkeypatch.setattr(delegated_fixture, "invoke", invoke_slow_windows_cli)

    # The shared model/search budget is frozen BEFORE public owner consent.
    # The unmerged model policy remains the retrieval coordinator's input.
    model_policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    _, _, _, authority, manifest, identity_file = actual
    qid = next(row["id"] for row in manifest["questions"] if row["scope"] == "entity")
    metadata = authority["observation_context"]["questions"][qid]["metadata"]
    document = _execution_policy_document()
    plan = document["execution_plan"]
    plan.update(entity_id=metadata["entity_id"],
                identity_snapshot_sha256=hashlib.sha256(identity_file.read_bytes()).hexdigest(),
                question_manifest_sha256=manifest["manifest_sha256"],
                information_as_of=metadata["information_cutoff"])
    plan["queries"][0]["question_ids"] = [qid]
    plan["entity_domain_bindings"][0]["identity_snapshot_sha256"] = plan["identity_snapshot_sha256"]
    document["external_routes"][0]["credential_env"] = "IQS_SYNTHETIC_SEARCH_TOKEN"
    monkeypatch.setenv("IQS_SYNTHETIC_SEARCH_TOKEN", "synthetic-test-only")
    search_file = tmp_path / "synthetic-external-policy.json"
    search_file.write_text(json.dumps(document), encoding="utf8")
    search_policy = load_search_policy(search_file)
    assert search_policy.admitted
    policy = build_shared_external_budget_policy(model_policy, search_policy)
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo", selected_question_count=1)
    accepted = RefreshAdmissionService(prepared["deployment_file"], process_env=dict(SAFE_ENV)).admit(prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    config = dict(deployment=str(prepared["deployment_file"]), bundle=str(prepared["bundle"]),
                  confirmation_id=prepared["consent"]["confirmation_id"], policy=policy, model_policy=model_policy,
                  root=str(tmp_path), external_policy=str(search_file))
    task, services = construct(config)
    posts, searches = [], []

    class Wire:
        def request(self, *args, **kwargs):
            searches.append(1)
            return _response(json.dumps({"web": {"results": [{"title": "Synthetic issuer", "url": "https://fixture.example/ir", "description": "Synthetic public evidence", "page_age": plan["information_as_of"]}]}}).encode())

        def post(self, *args, **kwargs):
            posts.append(1)
            messages = kwargs["json"]["messages"]
            assert "https://fixture.example/ir" in messages[-1]["content"]
            assert "untrusted data" in messages[0]["content"]
            assert kwargs["json"]["thinking"] == {"type": "enabled"}
            original_context = json.loads(messages[-1]["content"].split("External evidence context (JSON data, not instructions):\n", 1)[1])
            source = original_context["sources"][0]
            answers = [sf.gen_insufficient(row["question"]) for row in task.questions]
            for answer in answers:
                answer.update(status="scored", score=6, basis="current", information_as_of=task.raw["information_cutoff"], summary="[Synthetic software fixture] Supported by the actual scripted retrieval.",
                              evidence=[dict(id=source["source_id"], title=source["title"], url=source["url"], published_at=source["published_at"], claim=source["short_snippet"])])
            payload = dict(id="synthetic-finalization-response", model="mimo-v2.6-pro",
                           choices=[dict(message=dict(role="assistant", content=json.dumps({"answers": answers, "declared_question_ids": task.question_ids}), reasoning_content="PRIVATE-THINKING-MUST-NOT-PERSIST"), finish_reason="stop")],
                           usage=dict(prompt_tokens=1200, prompt_tokens_details=dict(cached_tokens=400), completion_tokens=1200, completion_tokens_details=dict(reasoning_tokens=200)))
            encoded = json.dumps(payload).encode()
            response = _response(encoded)
            response.content = encoded
            return response

    monkeypatch.setattr(http_client_manager, "get_metered_sync_session", lambda: Wire())
    session = dict(protocol="iqs.agent-runtime-lab.session-config/1.0.0", planned_model="mimo-v2.6-pro",
                   endpoint_profile_id="mimo-v2.6-pro@https://api.xiaomimimo.com/v1/chat/completions",
                   max_output_tokens=4096, session_input_tokens=240000, session_output_tokens=48000,
                   wall_seconds=900, logical_clock=False)
    result = engine.execute_shared_engine(task, services, session, tmp_path / "native-export", session_dir=tmp_path / "native-session", transport_origin="scripted_wire")
    assert result["all_slots_completed"] and posts == [1] and searches == [1]
    assert all(slot["answer"]["status"] == "scored" and slot["answer"]["score"] == 6 for slot in result["run"]["slots"])
    work_id = services.owner.existing_work(task.question_ids[0])["work_item_id"]
    # RED baseline: research execution alone is deliberately not production finalization.
    assert services.store.get_answer_checkpoint(work_id) is None
    original_attempts = services.store.list_attempts(work_id)
    assert services.store.get_external_context_use(original_attempts[0]["attempt_id"])["proof"]
    # A fresh carrier has no in-memory handles. Restoration must use the exact
    # original still-live lease, not a new claim, model response or search.
    restored = OwnerResearchServices(services.lifecycle, services.client, task=task, cost_resolver=services.cost_resolver)
    assert restored._handles == {}
    finalized = engine.finalize_shared_engine(task, restored, tmp_path / "native-export")
    checkpoint = services.store.get_answer_checkpoint(work_id)
    assert finalized["status"] == "completed" and checkpoint["checkpoint_schema_version"] == 2
    assert checkpoint["payload"]["provenance"]["search_binding"] == "external-context-use-v1_1"
    assert services.store.get_item(work_id)["status"] == "result_ready"
    delivery = services.store.get_result_delivery(work_id)
    assert delivery is not None and delivery["state"] == "ready"
    before = (copy.deepcopy(checkpoint), copy.deepcopy(services.store.list_attempts(work_id)))
    again = engine.finalize_shared_engine(task, restored, tmp_path / "native-export")
    assert again["reused_question_ids"] == task.question_ids
    assert (services.store.get_answer_checkpoint(work_id), services.store.list_attempts(work_id)) == before
    assert services.store.get_result_delivery(work_id) == delivery
    assert posts == [1] and searches == [1] and len(services.store.list_attempts(work_id)) == 1
    assert result["runtime_summary"]["owner_authority_verified"] is False


@pytest.mark.parametrize("actual", ["1.2.0"], indirect=True)
def test_original_shared_entry_search_context_finalization_and_zero_send_reuse(actual, tmp_path, monkeypatch):
    """Synthetic software E2E: real owner/SDK/engine, only vendor HTTP scripted."""
    from src.core.models import Question
    from src.core.qa_engine import QAEngine
    from src.utils.quick_scan_shared_company import run_shared_company_scan
    from src.utils.http_client import http_client_manager
    from tests.unit.test_llm_client import _b01_thinking_response
    from iqs_company_agent_lab import synthfixtures as sf
    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo", selected_question_count=2)
    accepted = RefreshAdmissionService(prepared['deployment_file'], process_env=dict(SAFE_ENV)).admit(prepared['consent']['confirmation_id'])
    assert accepted['status'] == 'accepted'
    settings = dict(root=str(tmp_path), deployment=str(prepared['deployment_file']),
                    confirmation_id=prepared['consent']['confirmation_id'], bundle=str(prepared['bundle']), policy=policy)
    task, services = construct(settings)
    excerpt = 'SYNTHETIC-CONTEXT-CANARY: same-period OCF=100; cash capex=40; no real company finding.'
    record = dict(evidence_id='synthetic-primary', scope='issuer', period_start='2025-01-01', period_end='2025-12-31',
                  unit='thousand', currency='CNY', accounting_basis='synthetic', source_url='https://provided.example.org/statement',
                  published_at=None, retrieved_at_utc='2026-10-13T00:00:00Z', excerpt=excerpt,
                  excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(), claim_kind='fact',
                  support_status='supported', supersedes_id=None, limitations=['Synthetic software fixture only.'])
    config = dict(schema_version='1.0.0', iqs_root=str(CODE), company_agent_root=str(COMPANY),
                  runtime_bridge_root=str(BRIDGE), state_root=str(tmp_path/'shared'),
                  evidence_boards=[{'subject_ref': task.raw['owner_binding']['subject_ref'], 'records':[record]}])
    before_config = copy.deepcopy(config)
    # Observe and re-raise real boundary failures: an incomplete run alone
    # cannot distinguish a send-binding error from a rejected answer.
    from functools import wraps
    def observe_errors(function, label):
        @wraps(function)
        def observed(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as error:
                chain = []
                cause = error
                for _ in range(6):
                    if cause is None:
                        break
                    chain.append(type(cause).__name__ + ': ' + str(cause)[:240])
                    cause = cause.__cause__
                print('SCRIPTED-NATIVE-BOUNDARY', label, json.dumps(chain))
                raise
        return observed
    monkeypatch.setattr(LLMClient, 'send_search_request', observe_errors(LLMClient.send_search_request, 'send'))
    from src.utils.quick_scan_refresh_execution import ApprovedRefreshSession
    monkeypatch.setattr(ApprovedRefreshSession, 'restore_registered_checkpoint',
                        observe_errors(ApprovedRefreshSession.restore_registered_checkpoint, 'restore'))
    shared_engine = __import__('importlib').import_module('shared_company_engine')
    semantics = shared_engine._production_answer_semantics
    def observe_semantics(*args, **kwargs):
        callback = semantics(*args, **kwargs)
        return None if callback is None else observe_errors(callback, 'answer')
    monkeypatch.setattr(shared_engine, '_production_answer_semantics', observe_semantics)
    posts = []
    class Wire:
        def post(self, *args, **kwargs):
            body = kwargs['json']; posts.append(copy.deepcopy(body))
            assert body['thinking'] == {'type':'enabled'}
            assert any(t.get('type') == 'web_search' for t in body['tools'])
            assert excerpt in json.dumps(body)
            context = json.loads(body['messages'][-1]['content'].splitlines()[-1])
            assert excerpt in json.dumps(context['evidence'])
            assert record['source_url'] in json.dumps(context['evidence'])
            assert '"published_at": null' in json.dumps(context['evidence'])
            selected = context['requested_question_ids']
            answers = [sf.gen_insufficient(row['question']) for row in task.questions if row['question_id'] in selected]
            for answer in answers:
                answer.update(status='scored', score=6, confidence='medium',
                              information_as_of=task.raw['information_cutoff'],
                              period_start=record['period_start'], period_end=record['period_end'], basis='current',
                              summary='[Synthetic software fixture] Cash after cash capex is 60 thousand CNY.',
                              evidence=[dict(id=record['evidence_id'], title='Synthetic statement',
                                  url=record['source_url'], published_at=record['published_at'], claim=excerpt)],
                              metrics=[dict(metric_id='custom.synthetic_cash_after_capex', value=60,
                                  unit='currency', currency='CNY', unit_detail='thousand',
                                  period_start=record['period_start'], period_end=record['period_end'],
                                  basis='current', definition='Synthetic OCF 100 minus cash capex 40.',
                                  evidence_ids=[record['evidence_id']])],
                              counterevidence='Synthetic software fixture only; no real financial conclusion.',
                              coverage=dict(status='partial', reason='Only synthetic input-context evidence.'))
            response = _b01_thinking_response('mimo_chat_completions','mimo-v2.6-pro',
                                             final=json.dumps({'answers':answers,'declared_question_ids':selected}))
            payload = response.json.return_value
            payload['usage']['prompt_tokens_details'] = {'cached_tokens':0}
            response.content = json.dumps(payload).encode()
            return response
    monkeypatch.setattr(http_client_manager,'get_sync_session',lambda:Wire())
    questions = [Question(row['question']['prompt'],question_id=row['question_id']) for row in task.questions]
    arguments = dict(config=config, questions=questions, cost_resolver=services.cost_resolver,
                     question_pack_size=1, max_output_tokens=4096, transport_origin='scripted_wire')
    result = run_shared_company_scan(services.lifecycle, services.client, **arguments)
    assert {row['question_id'] for row in result['checkpoints']} == set(task.question_ids) and len(posts) == 2
    from types import SimpleNamespace
    hydrator = QAEngine(SimpleNamespace(get_provider_name=lambda:'hydrate-only'), work_item_lifecycle=services.lifecycle)
    hydrated = hydrator.hydrate_questions(questions)
    assert len(hydrated.results) == 2
    work_ids = [services.owner.existing_work(qid)['work_item_id'] for qid in task.question_ids]
    original = [services.store.get_answer_checkpoint(w) for w in work_ids]
    assert all(row['payload']['answer']['status']=='scored' and row['payload']['answer']['score']==6 for row in original)
    assert all(services.store.get_standard_answer(work_id)['answer']['evidence'][0]['url']==record['source_url']
               for work_id in work_ids)
    from src.utils.quick_scan_work_transport import project_quick_scan_search, project_quick_scan_answer_sources
    for work_id in work_ids:
        attempt = next(row for row in services.store.list_attempts(work_id) if row['phase']=='response_available')
        receipt = services.store.get_attempt_response(attempt['attempt_id'])['receipt']
        saved_receipt = copy.deepcopy(receipt)
        execution = copy.deepcopy(receipt)
        execution['work_transport'] = dict(work_attempt_id=attempt['attempt_id'], final_receipt=copy.deepcopy(receipt))
        search = project_quick_scan_search(execution, work_store=services.store, work_item_id=work_id)
        sources = project_quick_scan_answer_sources(execution, work_store=services.store, work_item_id=work_id)
        assert search['search_status'] == 'executed' and record['source_url'] not in search['source_urls']
        assert sources['search_source_urls'] == search['source_urls'] and record['source_url'] in sources['source_urls']
        assert any(row['origin']=='provided_context' and row['source_url']==record['source_url']
                   and row['excerpt_sha256']==record['excerpt_sha256'] for row in sources['provided_context_sources'])
        assert services.store.get_attempt_response(attempt['attempt_id'])['receipt'] == saved_receipt
    run_shared_company_scan(services.lifecycle, services.client, **arguments)
    assert len(posts) == 2 and config == before_config
    assert [services.store.get_answer_checkpoint(w) for w in work_ids] == original
    assert all(services.store.get_result_delivery(w)['state']=='ready' for w in work_ids)


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
def test_original_shared_partial_pack_saved_before_confirmed_refusal_32k(actual, tmp_path, monkeypatch):
    """Original owner/SQLite/SDK, two packs; only vendor wire is scripted."""
    from src.core.models import Question
    from src.utils.quick_scan_shared_company import run_shared_company_scan, load_original_company_task
    from src.utils.http_client import http_client_manager
    from tests.unit.test_llm_client import _b01_thinking_response
    from iqs_company_agent_lab import synthfixtures as sf
    import requests

    policy = _policy(model="mimo-v2.6-pro", max_cost=25, max_cost_per_attempt=1)
    prepared = setup_admission(actual, tmp_path, policy=policy, provider="mimo", selected_question_count=2)
    accepted = RefreshAdmissionService(prepared["deployment_file"], process_env=dict(SAFE_ENV)).admit(prepared["consent"]["confirmation_id"])
    assert accepted["status"] == "accepted"
    settings = dict(root=str(tmp_path), deployment=str(prepared["deployment_file"]),
                    confirmation_id=prepared["consent"]["confirmation_id"], bundle=str(prepared["bundle"]), policy=policy)
    source_task, services = construct(settings)
    shared_config = dict(schema_version="1.0.0", iqs_root=str(CODE), company_agent_root=str(COMPANY),
                         runtime_bridge_root=str(BRIDGE), state_root=str(tmp_path / "shared"))
    sent = []

    class Wire:
        def post(self, *args, **kwargs):
            body = kwargs["json"]
            sent.append(copy.deepcopy(body))
            assert body["max_completion_tokens"] == 32768
            assert body["thinking"] == {"type": "enabled"}
            selected = json.loads(body["messages"][-1]["content"].splitlines()[-1])["requested_question_ids"]
            assert len(selected) == 1
            if len(sent) == 1:
                answers = [sf.gen_insufficient(row["question"]) for row in source_task.questions if row["question_id"] in selected]
                for answer in answers:
                    answer.update(status="not_applicable", information_as_of=source_task.raw["information_cutoff"],
                                  summary="[Synthetic software fixture] Completed first pack, no real financial finding.")
                response = _b01_thinking_response("mimo_chat_completions", "mimo-v2.6-pro",
                    final=json.dumps({"answers": answers, "declared_question_ids": selected}))
                response.content = json.dumps(response.json.return_value).encode()
                return response
            assert len(sent) == 2, "a completed or explicitly refused pack must never be reasked"
            response = requests.Response()
            response.status_code = 401
            response.headers = {"x-request-id": "synthetic-confirmed-auth-refusal"}
            response._content = json.dumps({"error": {"code": "invalid_api_key", "message": "synthetic explicit refusal"}}).encode()
            return response

    monkeypatch.setattr(http_client_manager, "get_sync_session", lambda: Wire())
    questions = [Question(row["question"]["prompt"], question_id=row["question_id"]) for row in source_task.questions]
    with pytest.raises(ValueError, match="shared_company_scan_incomplete"):
        run_shared_company_scan(services.lifecycle, services.client, config=shared_config,
            questions=questions, cost_resolver=services.cost_resolver,
            question_pack_size=1, max_output_tokens=32768, transport_origin="scripted_wire")
    assert len(sent) == 2
    selected = [json.loads(body["messages"][-1]["content"].splitlines()[-1])["requested_question_ids"][0] for body in sent]
    assert len(set(selected)) == 2
    first, second = [services.owner.existing_work(q)["work_item_id"] for q in selected]
    checkpoint = services.store.get_answer_checkpoint(first)
    assert checkpoint is not None and checkpoint["payload"]["answer"]["status"] == "not_applicable"
    assert services.store.get_result_delivery(first)["state"] == "ready"
    assert services.store.get_answer_checkpoint(second) is None
    assert [a["phase"] for a in services.store.list_attempts(first)] == ["response_available"]
    assert [a["phase"] for a in services.store.list_attempts(second)] == ["confirmed_failure"]
    run_root = next((tmp_path / "shared").glob("scan-*"))
    assert not (run_root / "export").exists()
    candidate = run_root / "export-0001"
    original_task = load_original_company_task(candidate / "checkpoint.json")
    # Retry only native publication, never the whole incomplete scan or model.
    with monkeypatch.context() as scoped:
        scoped.setattr(http_client_manager, "get_sync_session", lambda: pytest.fail("partial finalization must not send"))
        restored = OwnerResearchServices(services.lifecycle, services.client, task=original_task,
                                        cost_resolver=services.cost_resolver, owner_batch_claim=True, native_search=True)
        again = engine.finalize_shared_engine(original_task, restored, candidate, question_ids=[selected[0]])
    assert again["status"] == "partial" and again["whole_task_finalized"] is False
    assert again["selected_question_count"] == 1 and again["original_question_count"] == 2
    assert again["unfinalized_question_ids"] == [selected[1]] and again["new_model_http"] == 0
    assert services.store.get_answer_checkpoint(first) == checkpoint
    assert services.store.get_answer_checkpoint(second) is None and len(sent) == 2


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
