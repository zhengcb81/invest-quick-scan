"""Original IQS semantics through the optional Company hook; no owner grants."""
import copy
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
STOCKQA_ROOT = Path(os.environ.get("IQS_STOCKQA_ROOT", ROOT.parent / "StockQAbyLLM"))
COMPANY_AGENT_ROOT = Path(os.environ.get("IQS_COMPANY_AGENT_ROOT", ROOT.parent / "iqs-company-agent-lab"))
sys.path[:0] = [str(ROOT / "scripts"), str(STOCKQA_ROOT), str(COMPANY_AGENT_ROOT / "src")]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


engine = load("semantic_engine_units", ROOT / "scripts/shared_company_engine.py")
helpers = load("semantic_company_helpers", COMPANY_AGENT_ROOT / "tests/conftest.py")
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


def test_production_semantics_accept_forecast_derived_from_historical_input(original):
    task, qid, body, context = original
    body.update(basis="forward", period_start="2027-01-01", period_end="2027-12-31",
                summary="Synthetic analyst scenario; assumptions are not realized revenue.")
    body["evidence"][0]["claim"] = "Synthetic historical 2025 revenue: 120."
    forecast = metric()
    forecast.update(value=145.2, unit="currency", currency="CNY", basis="forward",
                    period_start="2027-01-01", period_end="2027-12-31",
                    definition="Analyst assumption: historical 120 * 1.1 * 1.1; not company guidance.")
    body["metrics"] = [forecast]
    callback = engine._frozen_answer_semantics(task, context)
    before = copy.deepcopy(body)
    callback(body, qid)
    assert body == before
    invalid = copy.deepcopy(body)
    invalid["metrics"][0]["basis"] = "current"
    with pytest.raises(ValueError, match="future historical metric"):
        callback(invalid, qid)


def test_production_fact_semantics_validate_nested_metric_references(original):
    task, qid, body, context = original
    task.questions[0]["question"].update(response_kind="fact", relations=["customer"], max_items=20)
    nested = item()
    nested["metrics"] = [metric()]
    body.update(response_kind="fact", status="answered", score=None, items=[nested], metrics=[])
    callback = engine._frozen_answer_semantics(task, context)
    before = copy.deepcopy(body)
    callback(body, qid)
    assert body == before
    invalid = copy.deepcopy(body)
    invalid["items"][0]["metrics"][0]["evidence_ids"] = ["MISSING"]
    with pytest.raises(ValueError, match="numeric metric missing evidence binding"):
        callback(invalid, qid)


@pytest.mark.parametrize("layer", ["answer", "metric", "nested_metric"])
@pytest.mark.parametrize("basis", ["current", "forward"])
@pytest.mark.parametrize("dates", [("2027-01-01", None), (None, "2027-12-31"),
                                  ("2025-12-31", "2025-01-01"), (None, None)])
def test_period_endpoint_rules_are_consistent_at_all_answer_layers(original, layer, basis, dates):
    task, qid, body, context = original
    if layer == "answer":
        row = body
    else:
        row = metric()
        if layer == "nested_metric":
            task.questions[0]["question"].update(response_kind="fact", relations=["customer"], max_items=20)
            fact = item()
            fact["metrics"] = [row]
            body.update(response_kind="fact", status="answered", score=None, items=[fact])
        else:
            body["metrics"] = [row]
    row.update(basis=basis, period_start=dates[0], period_end=dates[1])
    before = copy.deepcopy(body)
    callback = engine._frozen_answer_semantics(task, context)
    reversed_dates = all(dates) and dates[0] > dates[1]
    future_actual = basis != "forward" and any(d and d > task.raw["information_cutoff"] for d in dates)
    if reversed_dates or future_actual:
        with pytest.raises(ValueError):
            callback(body, qid)
    else:
        callback(body, qid)
    assert body == before


@pytest.mark.parametrize("field", ["answer_schema_sha256", "metric_registry_sha256"])
def test_resource_digest_is_provenance_not_whole_answer_permission(original, field):
    task, qid, body, context = original
    context[field] = "0" * 64
    callback = engine._frozen_answer_semantics(task, context)
    callback(body, qid)
    assert context[field] == "0" * 64


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
    single = fixture.finalization_task([qid])
    services = fixture.MapperOnlyServices(single)
    run = {"slots": [{"question_id": qid, "execution_status": "completed", "answer": bad(body, "score_items"),
                      "attempt_refs": ["stockqa:native_" + qid]}]}
    from iqs_company_agent_lab.evidence import EvidenceBoard
    monkeypatch.setattr(engine, "_verified_finalization_export", lambda *args: (run, EvidenceBoard(2000)))
    monkeypatch.setattr(engine, "_production_answer_semantics", lambda *args, **kwargs: engine._frozen_answer_semantics(single, context))
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
    # This boundary double deliberately exposes no StockQA private members.
    # The original owner projection and parser each have their own real tests.
    lifecycle = object()
    import src.utils.quick_scan_company_context as company_context
    def public_inputs(candidate):
        assert candidate is lifecycle
        return SimpleNamespace(observation_context=copy.deepcopy(context), input_raw={
            "owner-config.json": json.dumps({"iqs_release_root": str(ROOT)}).encode("utf8")})
    monkeypatch.setattr(company_context, "company_scan_inputs", public_inputs)
    services = SimpleNamespace(lifecycle=lifecycle, store=store,
        owner=SimpleNamespace(entries={qid: {"kind": "work", "work_item_id": work_id}}),
        inspect_attempt=lambda ref: {"known": ref == "stockqa:UNIT_SDK_ATTEMPT",
            "outcome_recorded": "response_available", "native_receipt": copy.deepcopy(native),
            "response_saved": {"final_content": json.dumps(body), "tool_calls": None}})
    import src.utils.quick_scan_work_transport as transport
    monkeypatch.setattr(transport, "project_quick_scan_answer_sources", lambda *args, **kwargs:
                        {"search_status": "executed", "source_urls": [source["url"]],
                         "search_source_urls": [source["url"]], "provided_context_sources": []})

    class UnitRuntimePort:
        """Detached public Runtime DTO for glue-only semantic tests."""
        def original_scan_context(self):
            observed = getattr(services.owner, "observation_context", context)
            return SimpleNamespace(observation_context=copy.deepcopy(observed))

        def original_inputs(self):
            return SimpleNamespace(
                observation_context=copy.deepcopy(context),
                input_raw={"owner-config.json": json.dumps(
                    {"iqs_release_root": str(ROOT)}
                ).encode("utf8")},
            )

        def original_semantic_resources(self):
            from answer_validation import project_original_semantic_resources

            observed = self.original_scan_context().observation_context
            resolver = getattr(services.owner, "original_semantic_resources", None)
            if callable(resolver):
                return resolver(copy.deepcopy(observed))
            return project_original_semantic_resources(
                observed, release_root=ROOT
            )

        def answer_source_context(self, question_id, reference, observed_context):
            inspected = services.inspect_attempt(reference)
            if not inspected.get("known") or not inspected.get("response_saved"):
                raise ValueError("original successful current native reference required")
            if question_id != qid or observed_context != context:
                raise ValueError("original frozen observation context required")
            if services.store.get_external_context_use("UNIT_NATIVE") not in (None, {"proof": {"work_item_id": work_id}}):
                raise ValueError("original external context use proof required")
            execution = copy.deepcopy(native)
            execution["work_transport"] = {
                "work_attempt_id": "UNIT_NATIVE",
                "final_receipt": copy.deepcopy(native),
            }
            use = services.store.get_external_context_use("UNIT_NATIVE")
            if use is not None:
                if not isinstance(use, dict) or not isinstance(use.get("proof"), dict) or not use["proof"]:
                    raise ValueError("original external context use proof required")
                execution["external_context_use"] = copy.deepcopy(use["proof"])
            projection = transport.project_quick_scan_answer_sources(
                execution, work_store=services.store, work_item_id=work_id
            )
            verified = projection.get("search_status") == "executed" and bool(
                projection.get("search_source_urls")
            )
            return {
                "response": copy.deepcopy(inspected["response_saved"]),
                "verified_search": verified,
                "source_urls": tuple(projection.get("source_urls", ())) if verified else (),
                "entity_id": "UNIT_ENTITY",
                "metadata": copy.deepcopy(context["questions"][question_id]["metadata"]),
                "question_contract": {},
            }

        @staticmethod
        def validate_answer_transport(answer, question_id, sources):
            # A small implementation of the public Runtime port contract: the
            # owner package owns full answer-schema validation; IQS verifies
            # that it delegates transport/source checks through this method.
            if sources["verified_search"] and answer.get("score") is not None and type(
                answer["score"]
            ) is not int:
                raise ValueError("owner runtime rejected non-integral score")
            evidence_urls = {
                row.get("url") for row in answer.get("evidence", [])
                if isinstance(row, dict)
            }
            if evidence_urls - set(sources["source_urls"]):
                raise ValueError("owner runtime rejected an unbound source URL")
            if answer.get("status") == "search_unavailable" and sources["verified_search"]:
                raise ValueError("owner runtime rejected a contradictory search status")
            return None

    monkeypatch.setattr(engine, "_company_runtime", lambda *_args, **_kwargs: UnitRuntimePort())
    from iqs_company_agent_lab.evidence import EvidenceBoard
    return task, qid, body, services, source, EvidenceBoard(2000)


def test_production_v2_keeps_original_body_while_validating_exact_native(native_bound):
    task, qid, body, services, _, board = native_bound
    callback = engine._production_answer_semantics(task, services)
    before, board_before = copy.deepcopy(body), copy.deepcopy(board.snapshot())
    callback(body, qid, attempt_ref="stockqa:UNIT_SDK_ATTEMPT", evidence_board=board)
    assert body == before and board.snapshot() == board_before
    assert callback.semantic_version == 2


@pytest.mark.parametrize("kind", ["wrong_ref", "bad_source", "invalid_proof", "future_date"])
def test_production_v2_source_ref_cutoff_fail_closed(native_bound, kind):
    task, qid, body, services, source, board = native_bound
    ref = "stockqa:UNIT_SDK_ATTEMPT"
    if kind == "wrong_ref":
        ref = "stockqa:FOREIGN"
    elif kind == "bad_source":
        source["url"] = "https://example.invalid/foreign-original-receipt"
    elif kind == "invalid_proof":
        services.store.get_external_context_use = lambda _: {"proof": None}
    else:
        body["evidence"][0]["published_at"] = "2099-01-01"
    callback = engine._production_answer_semantics(task, services)
    with pytest.raises(ValueError):
        callback(body, qid, attempt_ref=ref, evidence_board=board)


@pytest.mark.parametrize('executed',[True,False])
def test_native_search_uses_original_source_projection_without_fabricating_external_use(native_bound,monkeypatch,executed):
    # Unit boundary only: the actual projector's native receipt verification is
    # independently covered in StockQA. No fake original owner/search golden.
    task,qid,body,services,source,board=native_bound
    services.store.get_external_context_use=lambda _:None
    captured=[]
    def projection(execution,**kwargs):
        captured.append(copy.deepcopy(execution))
        # A provided URL alone must never qualify as an executed native search.
        return {'search_status':'executed' if executed else 'not_executed',
                'search_source_urls':[source['url']] if executed else [],
                'source_urls':[source['url']], 'provided_context_sources':[]}
    import src.utils.quick_scan_work_transport as transport
    monkeypatch.setattr(transport,'project_quick_scan_answer_sources',projection)
    callback=engine._production_answer_semantics(task,services)
    if executed:
        callback(body,qid,attempt_ref='stockqa:UNIT_SDK_ATTEMPT',evidence_board=board)
    else:
        with pytest.raises(ValueError,match='verified source projection'):
            callback(body,qid,attempt_ref='stockqa:UNIT_SDK_ATTEMPT',evidence_board=board)
    assert len(captured)==1 and 'external_context_use' not in captured[0]
    assert captured[0]['work_transport']['work_attempt_id']=='UNIT_NATIVE'


@pytest.mark.parametrize("status", ["not_applicable", "insufficient_evidence", "search_unavailable"])
def test_original_source_free_terminal_answer_replays_without_publication(native_bound, monkeypatch, status):
    task, qid, body, services, _, board = native_bound
    missing = helpers.sf.gen_insufficient(task.questions[0]["question"])
    missing.update(status=status)
    body.clear()
    body.update(missing)
    services.store.get_external_context_use = lambda _: None
    from src.utils import quick_scan_work_transport
    monkeypatch.setattr(quick_scan_work_transport, "project_quick_scan_answer_sources", lambda *args, **kwargs: {
        "search_status": "not_executed", "search_source_urls": [], "source_urls": [],
    })
    callback = engine._production_answer_semantics(task, services)
    assert callback(body, qid, attempt_ref="stockqa:UNIT_SDK_ATTEMPT", evidence_board=board) == ()
    publish = engine._production_answer_semantics(task, services, for_publication=True)
    with pytest.raises(ValueError, match="verified source projection"):
        publish(body, qid, attempt_ref="stockqa:UNIT_SDK_ATTEMPT", evidence_board=board)


@pytest.mark.parametrize("kind", ["integral_float", "sourced_search_unavailable"])
def test_publication_preflight_retains_native_checkpoint_value_types(native_bound, kind):
    task, qid, body, services, _, board = native_bound
    if kind == "integral_float":
        body["score"] = float(body["score"])
    else:
        body.clear()
        body.update(helpers.sf.gen_insufficient(task.questions[0]["question"]), status="search_unavailable")
    publish = engine._production_answer_semantics(task, services, for_publication=True)
    with pytest.raises(ValueError):
        publish(body, qid, attempt_ref="stockqa:UNIT_SDK_ATTEMPT", evidence_board=board)


def test_actual_native_http_source_does_not_require_https(native_bound):
    from iqs_company_agent_lab.answers import AnswerRejection, validate_single_answer
    task, qid, body, services, source, board = native_bound
    source['url'] = 'http://example.invalid/original-search-result.pdf'
    body['evidence'][0]['url'] = source['url']
    body['metrics'] = [metric()]
    callback = engine._production_answer_semantics(task, services)
    verified = callback(body, qid, attempt_ref='stockqa:UNIT_SDK_ATTEMPT', evidence_board=board)
    validate_single_answer(copy.deepcopy(body), qid, board, board.publication_exclusive_date,
                           verified_source_urls=verified)
    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw['run_id']),
                    answer_semantic_validator=callback, answer_semantic_validator_version=2)
    runner._start()
    runner._apply_answers({'question_ids': [qid]}, [copy.deepcopy(body)], 'stockqa:UNIT_SDK_ATTEMPT')
    assert runner.state.slot(qid)['execution_status'] == 'completed'
    # The same transport scheme does not qualify an unreturned source.
    source['url'] += '?different-document'
    with pytest.raises((ValueError, AnswerRejection)):
        callback(body, qid, attempt_ref='stockqa:UNIT_SDK_ATTEMPT', evidence_board=board)


def test_external_url_does_not_reactivate_invalidated_board_evidence(original):
    from iqs_company_agent_lab.answers import AnswerRejection, validate_single_answer
    from iqs_company_agent_lab.evidence import EvidenceBoard
    task, qid, body, _ = original
    record = helpers.sf.evidence_record('e1', task.company_ref, 'moat')
    body['evidence'][0].update(id='e1', url=record['source_url'])
    board = EvidenceBoard(2000)
    board.add(record)
    board.invalidate(['e1'], 'superseded')
    with pytest.raises(AnswerRejection, match='inactive|not_in_evidence_store'):
        validate_single_answer(body, qid, board, '2026-10-14', verified_source_urls=(record['source_url'],))


def scan_board(task):
    from iqs_company_agent_lab.evidence import EvidenceBoard
    return EvidenceBoard(2000, allow_undated_retrieved=True, validation_context={
        'information_cutoff': '2026-10-13', 'publication_exclusive_date': '2026-10-14',
        'profile_sha256': '0' * 64, 'company_ref_sha256': sha256_hex(task.raw['company_ref'])})


@pytest.mark.parametrize('day', ['2026-10-12', '2026-10-13', None])
def test_answer_date_may_precede_search_cutoff_without_being_rewritten(original, day):
    from iqs_company_agent_lab.answers import validate_single_answer
    task, qid, body, _ = original
    body['information_as_of'] = day
    before = copy.deepcopy(body)
    validate_single_answer(body, qid, scan_board(task), '2026-10-14')
    assert body['information_as_of'] == before['information_as_of']


def test_answer_future_information_date_still_rejected(original):
    from iqs_company_agent_lab.answers import AnswerRejection, validate_single_answer
    task, qid, body, _ = original
    body['information_as_of'] = '2026-10-14'
    with pytest.raises(AnswerRejection):
        validate_single_answer(body, qid, scan_board(task), '2026-10-14')


def test_scan_undated_source_retains_unknown_and_requires_known_availability(original):
    from iqs_company_agent_lab.evidence import EvidenceBoard
    task, _, _, _ = original
    ref = task.raw['company_ref']
    record = helpers.sf.evidence_record('provided', ref, 'moat')
    record.update(published_at=None, retrieved_at_utc='2026-10-13T10:00:00Z',
                  limitations=['Publication date not independently known'])
    board = scan_board(task)
    assert board.intake([record], ref)['accepted'] == ['provided']
    restored = EvidenceBoard.from_snapshot(board.snapshot())
    assert restored.get('provided')['published_at'] is None
    assert restored.source_available(record, '2026-10-14')
    for change in ({'published_at': '2026-10-14'},
                   {'retrieved_at_utc': '2026-10-14T00:00:00Z'},
                   {'retrieved_at_utc': '2026-10-13TgarbageZ'},
                   {'limitations': []}):
        invalid = {**record, **change, 'evidence_id': 'invalid'}
        assert scan_board(task).intake([invalid], ref)['accepted'] == []
    assert EvidenceBoard(2000).intake([record], ref)['accepted'] == []


@pytest.mark.parametrize('allow_undated', [False, True])
def test_evidence_replay_keeps_original_acceptance_policy(allow_undated):
    scan_helpers = load('semantic_scan_fixtures', COMPANY_AGENT_ROOT / 'tests/test_scan_profile.py')
    from iqs_company_agent_lab.replay import ReplayEngine
    from iqs_company_agent_lab.evidence import EvidenceBoard
    task = scan_helpers.scan_task(qs=scan_helpers.questions(1))
    record = helpers.sf.evidence_record('undated', task.company_ref, 'moat')
    record.update(published_at=None, retrieved_at_utc='2026-10-17T10:00:00Z',
                  limitations=['Publication date unknown'])
    task.evidence_board_doc['records'] = [record]
    from iqs_company_agent_lab.canonical import canonical_json
    raw_board = canonical_json(task.evidence_board_doc).encode('utf-8')
    import hashlib
    task.raw['evidence_epoch_ref'].update(bytes=len(raw_board), sha256=hashlib.sha256(raw_board).hexdigest())
    task.task_sha256 = sha256_hex(task.raw)
    runner = Runner(task, SyntheticReplayPort(helpers.scenario_doc([]), task.raw['run_id']))
    runner.state.board.allow_undated_retrieved = allow_undated
    runner._start()
    snapshot = runner.state.board.snapshot()
    assert len(snapshot['records']) == int(allow_undated)
    if not allow_undated:
        assert 'allow_undated_retrieved' not in snapshot
        assert 'allow_undated_retrieved' not in runner.journal.events[0]['data']
    assert EvidenceBoard.from_snapshot(snapshot).snapshot() == snapshot
    replayed = ReplayEngine(task).replay(runner.journal.events)['state']
    assert replayed.board.snapshot() == snapshot
    from iqs_company_agent_lab.runner import input_manifest_sha256
    from iqs_company_agent_lab.export import build_research_run
    from iqs_company_agent_lab.provenance import runtime_evidence_document, summarize_runtime_evidence
    manifest = input_manifest_sha256(task.raw)
    run = build_research_run(runner.state, manifest, [], {}, [], {})
    document = runtime_evidence_document(run_id=run['run_id'], input_manifest_sha256=manifest,
        events=runner.journal.events, attempts=[], evidence_origin='synthetic')
    summarize_runtime_evidence(document, run=run, events=runner.journal.events, run_raw=b'',
        board_doc=task.evidence_board_doc, board_snapshot=snapshot)
