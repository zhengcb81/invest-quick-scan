"""Original IQS semantics through the optional Company hook; no owner grants."""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT.parent / "StockQAbyLLM"),
                str(ROOT.parent / "iqs-company-agent-lab/src")]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


engine = load("semantic_engine_units", ROOT / "scripts/shared_company_engine.py")
helpers = load("semantic_company_helpers", ROOT.parent / "iqs-company-agent-lab/tests/conftest.py")
standard_tests = load("semantic_body_fixtures", ROOT / "tests/test_standard_answers.py")
from iqs_company_agent_lab.runner import Runner
from iqs_company_agent_lab.runtime import SyntheticReplayPort
from iqs_company_agent_lab.events import EventJournal
from iqs_company_agent_lab.checkpoint import build_checkpoint
from iqs_company_agent_lab.canonical import sha256_hex
import question_prompts


@pytest.fixture
def original():
    task = helpers.make_task("fixed3", "semantic-hook-synthetic")
    qid = task.question_ids[0]
    body = standard_tests.content({"id": qid})
    context = {key: sha256_hex(json.loads((ROOT / path).read_text(encoding="utf-8")))
               for key, path in (("answer_schema_sha256", "schemas/answer-content.schema.json"),
                                 ("metric_registry_sha256", "questions/metric-registry.json"))}
    return task, qid, body, context


def metric():
    return dict(metric_id="custom.synthetic", value=1, unit="ratio", currency=None,
                unit_detail=None, period_start=None, period_end=None, basis="current",
                definition="Synthetic only", evidence_ids=["e1"])


def item():
    return dict(name="Synthetic only", canonical_entity_id=None, aliases=[], relation="customer",
                segment=None, role="customer", commercial_stage="unknown", description="Synthetic only",
                valid_from=None, valid_to=None, taxonomy_id=None, metrics=[], evidence_ids=["e1"],
                confidence="low")


def bad(body, kind):
    body = copy.deepcopy(body)
    if kind == "score_items":
        body["items"] = [item()]
    elif kind == "unavailable_metrics":
        body.update(status="insufficient_evidence", score=None, metrics=[metric()])
    elif kind == "fact_status":
        body.update(response_kind="fact", status="answered", score=None, items=[item()])
    else:
        registry = json.loads((ROOT / "questions/metric-registry.json").read_text(encoding="utf-8"))["metrics"]
        name, spec = next(iter(registry.items()))
        row = metric()
        row.update(metric_id=name, unit="percent" if spec["unit"] != "percent" else "ratio")
        body["metrics"] = [row]
    return body


@pytest.mark.parametrize("kind", ["score_items", "unavailable_metrics", "fact_status", "metric_unit"])
def test_original_semantics_reject_before_company_completion(original, kind):
    task, qid, body, context = original
    callback = engine._frozen_answer_semantics(task, context)
    body = bad(body, kind)
    before = copy.deepcopy(body)
    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw["run_id"]),
                    answer_semantic_validator=callback)
    runner._start()
    runner._apply_answers({"question_ids": [qid]}, [body], "synthetic:semantic-rejection")
    slot = runner.state.slot(qid)
    assert slot["execution_status"] == "invalid" and slot["answer"] is None
    assert slot["gap_codes"] == ["answer_semantic_contract_rejected"]
    assert body == before


def test_original_callback_preserves_valid_answer_and_frozen_inputs(original):
    task, qid, body, context = original
    callback = engine._frozen_answer_semantics(task, context)
    before = copy.deepcopy(body)
    callback(body, qid)
    assert body == before
    task.questions[0]["question"]["response_kind"] = "fact"
    callback(body, qid)  # Original construction snapshot; no current-question drift.


@pytest.mark.parametrize("field", ["answer_schema_sha256", "metric_registry_sha256"])
def test_missing_original_resource_version_refused(original, field):
    task, _, _, context = original
    context[field] = "0" * 64
    with pytest.raises(engine.SharedEngineRejected, match="frozen.*resource"):
        engine._frozen_answer_semantics(task, context)


def test_company_callback_cannot_rewrite_original_answer(original):
    task, qid, body, _ = original
    before = copy.deepcopy(body)

    def mutate(copy_only, _qid):
        copy_only["score"] = 10

    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw["run_id"]),
                    answer_semantic_validator=mutate)
    runner._start()
    runner._apply_answers({"question_ids": [qid]}, [body], "synthetic:mutator-refused")
    assert runner.state.slot(qid)["execution_status"] == "invalid"
    assert body == before


def test_continued_runner_uses_same_semantic_gate(original):
    task, qid, body, context = original
    callback = engine._frozen_answer_semantics(task, context)
    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw["run_id"]))
    runner._start()
    checkpoint = build_checkpoint(runner.state, runner.journal)
    chain = checkpoint["event_chain"]
    journal = EventJournal(task.raw["run_id"], start_seq=chain["seq"], start_head_sha256=chain["head_sha256"])
    continued = Runner.continue_from_checkpoint(task, runner.port, checkpoint, journal,
                                               answer_semantic_validator=callback)
    continued._apply_answers({"question_ids": [qid]}, [bad(body, "score_items")], "synthetic:restored")
    assert continued.state.slot(qid)["execution_status"] == "invalid"


def test_typed_semantic_prompt_is_explicit_without_changing_questions(original):
    task, qid, _, _ = original
    question = task.questions[0]["question"]
    before = copy.deepcopy(question)
    rules = question_prompts.typed_semantic_rules(question)
    assert "items=[]" in rules and "answered" in rules and "score" in rules
    assert question == before
    fact = question_prompts.typed_semantic_rules(dict(question, response_kind="fact"))
    assert "score=null" in fact and "scored" in fact


def test_semantic_rules_reach_actual_request_with_new_stable_hash(original):
    task, _, _, context = original
    callback = engine._frozen_answer_semantics(task, context)
    questions_before = copy.deepcopy(task.questions)
    captured = []

    class CapturingPort:
        def model_step(self, request):
            captured.append(copy.deepcopy(request))
            raise RuntimeError("synthetic stop before any vendor transport")

    runner = Runner(task, CapturingPort(), answer_semantic_validator=callback,
                    answer_semantic_rules=callback.prompt_rules)
    runner._start()
    intent = runner.strategy.next_action(runner.state.public_state())
    with pytest.raises(RuntimeError, match="synthetic stop"):
        runner._dispatch_model(intent)
    request = captured[0]
    assert all(rule in request["stable_prefix"]["rules"] for rule in callback.prompt_rules)
    assert request["stable_prefix_sha256"] == sha256_hex(request["stable_prefix"])
    assert task.questions == questions_before == request["stable_prefix"]["questions"]


def test_finalizer_rechecks_original_semantics_before_native_output_match(original, monkeypatch):
    task, qid, body, context = original
    # A contract-only mapper: not an admission or a sender.
    fixture = load("semantic_finalization_fixture", ROOT / "tests/test_shared_company_engine_finalization.py")
    single = SimpleNamespace(question_ids=[qid], questions=task.questions[:1],
                             raw={"run_id": "synthetic-final", "information_cutoff": task.raw["information_cutoff"]})
    services = fixture.MapperOnlyServices(single)
    run = {"slots": [{"question_id": qid, "execution_status": "completed", "answer": bad(body, "score_items"),
                      "attempt_refs": ["stockqa:native_" + qid]}]}
    from iqs_company_agent_lab.evidence import EvidenceBoard
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: (run, EvidenceBoard(2000)))
    monkeypatch.setattr(engine, "_production_answer_semantics", lambda *args: engine._frozen_answer_semantics(single, context))
    with pytest.raises(engine.SharedEngineRejected, match="standard_answer_contract"):
        engine.finalize_shared_engine(single, services, Path("unused-unit-only"))
    assert services.saves == [] and services.restores == []


def test_v2_callback_receives_exact_current_ref_and_readonly_board(original):
    task, qid, body, _ = original
    seen = []

    def callback(probe, question_id, *, attempt_ref, evidence_board):
        seen.append((question_id, attempt_ref, evidence_board.snapshot()))

    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw["run_id"]),
                    answer_semantic_validator=callback, answer_semantic_validator_version=2)
    runner._start()
    runner._apply_answers({"question_ids": [qid]}, [body], "synthetic:exact-current-ref")
    assert seen[0][0:2] == (qid, "synthetic:exact-current-ref")
    assert runner.state.slot(qid)["execution_status"] == "completed"


@pytest.fixture
def native_bound(original, monkeypatch):
    # Boundary-only unit double, not an owner admission or actual search positive.
    task, qid, body, context = original
    task.company_doc["origin"] = "owner_public"
    context = copy.deepcopy(context)
    context["questions"] = {qid: {"metadata": {"entity_id": "UNIT_ENTITY", "question_id": qid,
                                               "information_cutoff": task.raw["information_cutoff"]}}}
    native = {"attempt_id": "UNIT_SDK_ATTEMPT"}
    work_id = "UNIT_WORK"
    source = {"url": body["evidence"][0]["url"]}
    store = SimpleNamespace(
        list_attempts=lambda _: [{"attempt_id": "UNIT_NATIVE", "phase": "response_available"}],
        get_attempt_response=lambda _: {"receipt": copy.deepcopy(native)},
        get_external_context_use=lambda _: {"proof": {"work_item_id": work_id}},
        get_item=lambda _: {"entity_id": "UNIT_ENTITY"},
        get_observation_context=lambda _: {"context": copy.deepcopy(context), "context_sha256": sha256_hex(context)},
    )
    from src.runners.llm_runner import QuickScanWorkLifecycle
    lifecycle = SimpleNamespace(_observation_context=copy.deepcopy(context))
    lifecycle._standard_transport = lambda text: QuickScanWorkLifecycle._standard_transport(lifecycle, text)
    services = SimpleNamespace(lifecycle=lifecycle, store=store,
        owner=SimpleNamespace(entries={qid: {"kind": "work", "work_item_id": work_id}}),
        inspect_attempt=lambda ref: {"known": ref == "stockqa:UNIT_SDK_ATTEMPT",
            "outcome_recorded": "response_available", "native_receipt": copy.deepcopy(native),
            "response_saved": {"final_content": json.dumps(body), "tool_calls": None}})
    import src.utils.quick_scan_work_transport as transport
    monkeypatch.setattr(transport, "project_quick_scan_search", lambda *args, **kwargs:
                        {"search_status": "executed", "source_urls": [source["url"]]})
    from iqs_company_agent_lab.evidence import EvidenceBoard
    return task, qid, body, services, source, EvidenceBoard(2000)


def test_production_v2_keeps_original_body_while_validating_exact_native(native_bound):
    task, qid, body, services, _, board = native_bound
    callback = engine._production_answer_semantics(task, services)
    before, board_before = copy.deepcopy(body), copy.deepcopy(board.snapshot())
    callback(body, qid, attempt_ref="stockqa:UNIT_SDK_ATTEMPT", evidence_board=board)
    assert body == before and board.snapshot() == board_before
    assert callback.semantic_version == 2


@pytest.mark.parametrize("kind", ["wrong_ref", "bad_source", "missing_proof", "future_date"])
def test_production_v2_source_ref_cutoff_fail_closed(native_bound, kind):
    task, qid, body, services, source, board = native_bound
    ref = "stockqa:UNIT_SDK_ATTEMPT"
    if kind == "wrong_ref":
        ref = "stockqa:FOREIGN"
    elif kind == "bad_source":
        source["url"] = "https://example.invalid/foreign-original-receipt"
    elif kind == "missing_proof":
        services.store.get_external_context_use = lambda _: None
    else:
        body["evidence"][0]["published_at"] = "2099-01-01"
    callback = engine._production_answer_semantics(task, services)
    with pytest.raises(ValueError):
        callback(body, qid, attempt_ref=ref, evidence_board=board)
