"""Bounded first-party composition; no HTTP, model client, or ledger of its own.

The callable entry point consumes an already admitted StockQA owner service.
The CLI deliberately exposes only capabilities and validated report rendering;
it cannot turn arbitrary configuration, factories, or callbacks into authority.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

PROTOCOL = "iqs.shared-company-engine/1.0.0"


class SharedEngineRejected(ValueError):
    pass


class SharedEngineInterrupted(RuntimeError):
    """Original durable events remain available; this is not retry permission."""

    def __init__(self, session_dir):
        super().__init__("shared engine interrupted; inspect original session before recovery")
        self.session_dir = Path(session_dir)


def capabilities():
    return {
        "protocol": PROTOCOL,
        "execution_api": "execute_shared_engine",
        "finalization_api": "finalize_shared_engine",
        "finalization_mode": "explicit_original_owner_checkpoint_only",
        "finalization_requires_verified_search": True,
        "requires": [
            "original_ApprovedRefreshSession",
            "original_OwnerResearchServices",
            "original_Runner",
            "original_RuntimeBridgePort",
            "native_safe_visible_output",
        ],
        "registered_question_count": 12,
        "registered_cutoff": "2026-10-13",
        "strategies": ["fixed3", "free_agent", "evidence_agent"],
        "generation_mode": "native_one_shot_question_pack",
        "question_pack_provider": "mimo",
        "company_scan": {
            "task_protocol": "iqs.company-scan-task/1.0.0",
            "profile_protocol": "iqs.company-scan-profile/1.0.0",
            "factory": "create_company_scan_task",
            "question_set": "original_approved_nonempty_unique_subset",
            "cutoff": "original_owner_actual_cutoff",
            "pack_size_range": [1, 12],
            "mode": "one_shot_packs",
            "provider_selection": "original_stockqa_endpoint_capabilities",
            "automatic_cross_model_fallback": False,
            "resource_defaults": "derived_from_actual_question_packs",
            "search_queries": 0,
            "qualification_granted": False,
        },
        "unsupported_scope": "implicit_research_execution_and_cli",
        "unsupported": [
            "native_multiturn_packs",
            "automatic_unknown_resend",
            "official_search_backed_checkpoint",
            "cli_owner_construction",
        ],
        "financial_accuracy_assessed": False,
        "production_owner_admitted": False,
    }


def preflight(task, services, session_config):
    """Validate the bounded composition without claiming a new owner grant."""
    from iqs_agent_runtime_lab.port import validate_session_config
    from iqs_company_agent_lab.strategy import strategy_for_task
    from iqs_company_agent_lab.task import LoadedTask
    from src.utils.quick_scan_owner_research import OwnerResearchServices

    if not isinstance(services, OwnerResearchServices):
        raise SharedEngineRejected("original_owner_research_services_required")
    if not isinstance(task, LoadedTask) or services.task is not task:
        raise SharedEngineRejected("original_service_bound_task_required")
    if task.company_doc.get("origin") != "owner_public" or not getattr(task, "owner_binding", None):
        raise SharedEngineRejected("original_owner_public_binding_required")
    strategy_for_task(task)  # Full question IDs, contracts and scheduling projection.
    if task.raw.get("protocol") == "iqs.company-scan-task/1.0.0":
        return _scan_preflight(task, services, session_config)
    if len(task.question_ids) != 12 or task.raw.get("information_cutoff") != "2026-10-13":
        raise SharedEngineRejected("registered_twelve_question_task_required")
    config = validate_session_config(session_config)
    if config.get("logical_clock") is not False:
        raise SharedEngineRejected("native_runtime_requires_wall_clock")
    if config["planned_model"] != services.client.model:
        raise SharedEngineRejected("original_model_route_mismatch")
    if services.native_session:
        # All three registered strategies may select several questions in one
        # intent. Native session registration presently supports singleton work.
        raise SharedEngineRejected("native_multiturn_question_pack_not_supported")
    if not callable(getattr(services, "recover_intent", None)):
        raise SharedEngineRejected("original_native_intent_lookup_required")
    if services.attempt_observations(transport_origin="scripted_wire"):
        # Observer classification is per execution, while native SQLite and
        # budget history persist. Reusing a prior run's observer would mislabel
        # historical responses as newly sent requests in the new summary.
        raise SharedEngineRejected("fresh_owner_service_observer_required")
    _production_answer_semantics(task, services)
    if services.client.provider_name != "mimo":
        raise SharedEngineRejected("native_one_shot_question_pack_requires_mimo")
    services.owner.check()
    services.owner.assert_execution_controls(
        pack_size=12 if task.raw["strategy_id"] == "free_agent" else 3,
        thinking_enabled=True,
        max_output_tokens=config["max_output_tokens"],
    )
    return config


def _original_answer_resources(context, root):
    """Resolve resources already named by the original owner, not current files.

    Production contexts name an immutable module package. Older research
    contexts carry only the two original digests; retain that format by looking
    up matching existing resources, without requiring new fields or rewriting
    the task. An unrelated new registry entry cannot change old semantics.
    """
    import module_registry
    import standard_answers

    names = {"answer_schema_sha256": "schemas/answer-content.schema.json",
             "metric_registry_sha256": "questions/metric-registry.json"}
    if not isinstance(context, dict):
        raise SharedEngineRejected("original_answer_context_required")

    def matches(resources):
        return all(standard_answers.digest(resources[name]) == context.get(key)
                   for key, name in names.items())

    ids = {row.get("metadata", {}).get("module_package_id")
           for row in context.get("questions", {}).values() if isinstance(row, dict)} - {None}
    if ids:
        if len(ids) != 1:
            raise SharedEngineRejected("original_answer_resource_package_mismatch")
        package, _, _, _ = module_registry.load_package(next(iter(ids)), root=root)
        resources = package["format_resources"]
        return copy.deepcopy(resources)

    # Legacy research contexts have no package ID. Resource hashes are lookup
    # keys, not a requirement that today's catalog still has the same hash.
    legacy_resources = None
    try:
        resources = {name: standard_answers.library.read_json(root / name) for name in names.values()}
        legacy_resources = resources
        if matches(resources):
            return resources
    except (OSError, ValueError, KeyError, TypeError):
        # An unavailable current authoring tree is not a prerequisite for
        # reading an old, independently verified resource package.
        pass
    for path in sorted((root / "questions/releases/packages").glob("pkg_*.json")):
        try:
            package, _, _, _ = module_registry.load_package(path.stem, root=root)
        except (OSError, ValueError, KeyError, TypeError):
            continue  # An unrelated broken package must not hide the original.
        if matches(package["format_resources"]):
            return copy.deepcopy(package["format_resources"])
    # Original research-only contexts did not bind a package. Their descriptive
    # whole-resource hashes were never an admission gate. Keep that old reader
    # when no original archive can be identified, rather than inventing one.
    if legacy_resources is not None:
        return legacy_resources
    raise SharedEngineRejected("original_answer_resources_unavailable")


def _frozen_answer_semantics(task, context, *, release_root=None):
    """Validate original questions; whole registry hashes are provenance only.

    Adding an unrelated metric or schema annotation must not invalidate an
    already received answer. Actual question, unit and evidence semantics are
    still validated below, without changing the original body or hash record.
    """
    import sys

    scripts = Path(__file__).resolve().parent
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import standard_answers
    import question_prompts

    if (Path(standard_answers.__file__).resolve() != scripts / "standard_answers.py"
        or Path(question_prompts.__file__).resolve() != scripts / "question_prompts.py"):
        raise SharedEngineRejected("original_standard_answer_validator_required")
    root = Path(release_root) if release_root is not None else scripts.parent
    resources = _original_answer_resources(context, root)
    schema = resources["schemas/answer-content.schema.json"]
    registry = resources["questions/metric-registry.json"]
    questions = {row["question_id"]: copy.deepcopy(row["question"]) for row in task.questions}
    if (len(questions) != len(task.questions)
        or set(questions) != set(task.question_ids)
        or any(question.get("id") != qid for qid, question in questions.items())):
        raise SharedEngineRejected("original_semantic_question_contract_required")
    cutoff = task.raw["information_cutoff"]

    def validate_original(answer, question_id):
        if question_id not in questions or answer.get("question_id") != question_id:
            raise ValueError("original semantic question mismatch")
        before = copy.deepcopy(answer)
        standard_answers.validate_content(answer, questions[question_id], cutoff,
                                          answer_schema=schema, metric_registry=registry)
        if answer != before:
            raise ValueError("original semantic validator changed answer")

    validate_original.prompt_rules = tuple(question_prompts.typed_semantic_rules(q)
                                            for q in questions.values())
    validate_original.legacy_prompt_rules = tuple(question_prompts.legacy_typed_semantic_rules(q)
                                                   for q in questions.values())
    return validate_original


def _production_answer_semantics(task, services):
    # Synthetic/old research entry points retain their historical default.
    # Public production preflight already requires an original owner task.
    if getattr(task, "company_doc", {}).get("origin") != "owner_public":
        return None
    from src.utils.quick_scan_company_context import company_scan_inputs

    inputs = company_scan_inputs(services.lifecycle)
    context = inputs.observation_context
    owner_config = json.loads(inputs.input_raw["owner-config.json"])
    original = _frozen_answer_semantics(task, context,
        release_root=owner_config["iqs_release_root"])

    def validate_native(answer, question_id, *, attempt_ref, evidence_board):
        original(answer, question_id)
        return _validate_native_answer_sources(task, services, context, answer, question_id,
                                               attempt_ref=attempt_ref, evidence_board=evidence_board)

    validate_native.semantic_version = 2
    validate_native.base_semantic_validator = original
    validate_native.prompt_rules = original.prompt_rules
    validate_native.legacy_prompt_rules = original.legacy_prompt_rules
    return validate_native


def _validate_native_answer_sources(task, services, context, answer, question_id,
                                    *, attempt_ref, evidence_board):
    """Read the exact native member/use proof; never infer a latest response."""
    from iqs_company_agent_lab.answers import check_citation_closure
    from src.core.models import Answer
    from src.utils.quick_scan_observation_context import validate_standard_answer
    from src.utils.quick_scan_observation_context import split_standard_answer_transport
    from src.utils.quick_scan_result_outbox import canonical_sha256
    from src.utils.quick_scan_work_transport import project_quick_scan_answer_sources

    inspected = services.inspect_attempt(attempt_ref)
    if (not inspected.get("known") or not inspected.get("response_saved")
        or inspected.get("outcome_recorded") != "response_available" or evidence_board is None):
        raise ValueError("original successful current native reference required")
    body, board = copy.deepcopy(answer), copy.deepcopy(evidence_board)
    entry = services.owner.entries.get(question_id)
    if not isinstance(entry, dict) or entry.get("kind") != "work":
        raise ValueError("original question work member required")
    work_id, native = entry["work_item_id"], inspected["native_receipt"]
    matches = [row for row in services.store.list_attempts(work_id)
        if row["phase"] == "response_available"
        and (services.store.get_attempt_response(row["attempt_id"]) or {}).get("receipt") == native]
    if len(matches) != 1:
        raise ValueError("exact original successful native work member required")
    attempt_id = matches[0]["attempt_id"]
    use = services.store.get_external_context_use(attempt_id)
    if use is not None and (not isinstance(use, dict) or not isinstance(use.get("proof"), dict) or not use["proof"]):
        raise ValueError("original external context use proof required")
    saved_context = services.store.get_observation_context(work_id)
    if (not saved_context or saved_context["context"] != context
        or saved_context["context_sha256"] != canonical_sha256(context)):
        raise ValueError("original frozen observation context required")
    execution = copy.deepcopy(native)
    execution["work_transport"] = dict(work_attempt_id=attempt_id, final_receipt=copy.deepcopy(native))
    if use is not None:
        execution["external_context_use"] = copy.deepcopy(use["proof"])
    # Native search has its own original execution receipt. Never require or
    # manufacture an external-search use row for that independent path.
    projection = project_quick_scan_answer_sources(execution, work_store=services.store, work_item_id=work_id)
    if projection.get("search_status") != "executed" or not projection.get("search_source_urls"):
        raise ValueError("original verified source projection required")
    verified_urls = tuple(projection["source_urls"])
    check_citation_closure(body, board, board.publication_exclusive_date,
                           verified_source_urls=verified_urls)
    _native_final_answer(inspected["response_saved"], question_id, body,
                         evidence_board=evidence_board, verified_source_urls=verified_urls)
    transported = Answer(json.dumps(body, ensure_ascii=False), score=body.get("score"),
                         status=body.get("status"), source="llm", metadata={"execution": execution})
    summary, standard = split_standard_answer_transport(transported.text)
    normalized = dict(entity_id=services.store.get_item(work_id)["entity_id"], question_id=question_id,
                      status=transported.status, score=transported.score, description=summary)
    validate_standard_answer(standard, metadata=context["questions"][question_id]["metadata"],
                             normalized_answer=normalized, source_urls=projection["source_urls"])
    return verified_urls


def _write_atomic(path, payload):
    """Same-directory replacement retains the last complete original record."""
    from iqs_company_agent_lab.canonical import canonical_json
    from iqs_company_agent_lab.events import scan_for_secret

    raw = canonical_json(payload).encode("utf8")
    scan_for_secret(raw.decode("utf8"))
    _publish_atomic(path, lambda temporary: temporary.write_bytes(raw))


def _publish_atomic(path, write):
    """Publish a complete record without reusing private crash leftovers."""
    descriptor, name = tempfile.mkstemp(prefix=".iqs-", suffix=".pending", dir=path.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        write(temporary)
        with temporary.open("r+b") as stream:
            os.fsync(stream.fileno())
        _replace_record(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            # A private, unreferenced candidate never becomes recovery input.
            # Antivirus/indexer handles may keep it open until later.
            pass


def _replace_record(temporary, path):
    # Windows indexers/virus scanners can briefly hold the old record without
    # FILE_SHARE_DELETE. Retry only the same completed rename, never generation.
    for attempt in range(7):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in {5, 32} or attempt == 6:
                raise
            time.sleep(0.01 * 2**attempt)


def _new_session(session_dir, task):
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir
    from iqs_company_agent_lab.task import task_bundle

    session_dir = Path(session_dir)
    ensure_safe_output_dir(session_dir)
    session_dir.mkdir(exist_ok=False)
    _write_atomic(session_dir / "task-bundle.json", task_bundle(task))
    return session_dir


def _journal(session_dir, run_id, *, start_seq=-1, start_head=None):
    from iqs_company_agent_lab.canonical import canonical_json
    from iqs_company_agent_lab.events import EventJournal

    class DurableOriginalJournal(EventJournal):
        """Original event validation/hash chain; add only atomic persistence."""

        def append(self, event_type, data, segment_id=None):
            event = super().append(event_type, data, segment_id)
            raw = ("\n".join(canonical_json(row) for row in self.events) + "\n").encode("utf8")
            path = session_dir / "events.jsonl"
            _publish_atomic(path, lambda temporary: temporary.write_bytes(raw))
            return event

    return DurableOriginalJournal(run_id, start_seq=start_seq, start_head_sha256=start_head)


def _pending_port(port, runner_ref, session_dir, history_journals=(), recover_intent=None,
                  replay_only=False):
    """Save original pending state before HTTP, without another execution loop."""
    from iqs_company_agent_lab.canonical import canonical_json
    from iqs_company_agent_lab.checkpoint import build_checkpoint, write_checkpoint
    from iqs_company_agent_lab.runtime import SavedResponseBoundary

    class CheckpointedPort:
        def _save(self, intent, receipt=None):
            runner = runner_ref[0]
            import hashlib
            events = [
                e for _, journal in history_journals for e in journal.events
            ] + runner.journal.events
            raw = ("\n".join(canonical_json(e) for e in events) + "\n").encode("utf8")
            # 128-bit filename discriminator avoids growing Windows paths;
            # exact bytes and the original full event/checkpoint hashes remain checked.
            name = "pending-history-" + str(runner.journal.seq) + "-" + hashlib.sha256(raw).hexdigest()[:32] + ".jsonl"
            history = session_dir / name
            if history.exists():
                if history.read_bytes() != raw:
                    raise SharedEngineRejected("immutable_pending_history_conflict")
            else:
                _publish_atomic(history, lambda temporary: temporary.write_bytes(raw))
            checkpoint = build_checkpoint(
                runner.state, runner.journal, pending_intent=intent, pending_receipt=receipt
            )
            path = session_dir / "checkpoint.json"
            _publish_atomic(path, lambda temporary: write_checkpoint(temporary, checkpoint, [name]))

        def model_step(self, envelope):
            if replay_only:
                recovered = (recover_intent(copy.deepcopy(envelope["intent"]))
                             if recover_intent is not None else None)
                if (recovered and recovered.get("decision") == "recover_saved_receipt"
                    and recovered.get("saved_receipt")):
                    result = recovered["saved_receipt"]
                    self._save(envelope["intent"], result)
                    return result
                # End local replay with the slots already recovered. There is
                # no fabricated receipt or pending checkpoint for an unasked
                # question, and unknown work never reaches the live port.
                raise SavedResponseBoundary("replay_only_saved_responses_exhausted")
            self._save(envelope["intent"])
            if recover_intent is not None:
                recovered = recover_intent(copy.deepcopy(envelope["intent"]))
                if recovered is not None:
                    if recovered.get("decision") == "recover_saved_receipt" and recovered.get("saved_receipt"):
                        result = recovered["saved_receipt"]
                        self._save(envelope["intent"], result)
                        return result
                    if not (recovered.get("decision") == "not_sent"
                            and recovered.get("saved_receipt") is None and not replay_only):
                        raise SharedEngineRejected("native_prior_intent_unresolved_never_resend")
                    # The native store classified an exact released unsent
                    # scope. This is not send permission: normal generation,
                    # current owner, claim, attempt and budget guards follow.
            result = port.model_step(envelope)
            self._save(envelope["intent"], result)
            return result

        def search(self, envelope):
            if replay_only:
                raise SavedResponseBoundary("replay_only_new_search_forbidden")
            return port.search(envelope)

        def inspect_attempt(self, ref):
            return port.inspect_attempt(ref)

        def request_resume(self, ref):
            return port.request_resume(ref)

    return CheckpointedPort()


def _export(
    task, services, runner, *, output, transport_origin, journals=None, mode="native_owner"
):
    from iqs_company_agent_lab.checkpoint import build_checkpoint
    from iqs_company_agent_lab.export import write_run_export
    from iqs_company_agent_lab.provenance import evidence_origin, runtime_evidence_document
    from iqs_company_agent_lab.runner import input_manifest_sha256

    journals = journals or [("events.jsonl", runner.journal)]
    events = [event for _, journal in journals for event in journal.events]
    evidence = runtime_evidence_document(
        run_id=task.raw["run_id"],
        input_manifest_sha256=input_manifest_sha256(task.raw),
        events=events,
        attempts=services.attempt_observations(transport_origin=transport_origin),
        evidence_origin=evidence_origin(task.evidence_board_doc, runner.state.board.snapshot()),
    )
    checkpoint = build_checkpoint(runner.state, runner.journal)
    return write_run_export(
        Path(output),
        runner.state,
        journals,
        input_manifest_sha256(task.raw),
        mode,
        checkpoint=checkpoint,
        runtime_evidence=evidence,
    )


def execute_shared_engine(
    task, services, session_config, output, *, session_dir, transport_origin="stockqa_live"
):
    """Execute the sole original Runner using original approved native services.

    Output remains a research artifact, not an official owner checkpoint. The
    caller must describe its observed wire as scripted_wire in offline tests.
    Native refusal, failed output or interrupted execution does not authorize
    another send. The durable session directory is retained for inspection.
    """
    from iqs_agent_runtime_lab.port import create_runtime_port
    from iqs_company_agent_lab.checkpoint import write_checkpoint
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir
    from iqs_company_agent_lab.runner import RunCrashed, Runner

    config = preflight(task, services, session_config)
    if transport_origin not in {"stockqa_live", "scripted_wire"}:
        raise SharedEngineRejected("explicit_transport_origin_required")
    output, session_dir = Path(output), Path(session_dir)
    if (
        output.absolute() == session_dir.absolute()
        or output.absolute() in session_dir.absolute().parents
        or session_dir.absolute() in output.absolute().parents
    ):
        raise SharedEngineRejected("session_and_export_must_be_disjoint")
    ensure_safe_output_dir(output)  # Fail before any send or session creation.
    port = create_runtime_port(services, task=task, session_config=config)
    return _execute_with_port(
        task,
        services,
        port,
        output=output,
        session_dir=session_dir,
        transport_origin=transport_origin,
    )


def _execute_with_port(task, services, port, *, output, session_dir, transport_origin):
    """Internal engine seam also exercised by explicitly synthetic tests.

    This is not the owner-admitting public entry point. No caller callback or
    Python factory is loaded by the CLI. The sole scheduling loop is Runner.
    """
    from iqs_company_agent_lab.checkpoint import write_checkpoint
    from iqs_company_agent_lab.runner import RunCrashed, Runner

    session_dir = _new_session(session_dir, task)
    journal = _journal(session_dir, task.raw["run_id"])
    runner_ref = []
    semantic_validator = _production_answer_semantics(task, services)
    runner = Runner(
        task,
        _pending_port(
            port, runner_ref, session_dir, recover_intent=getattr(services, "recover_intent", None)
        ),
        journal=journal,
        execution_revision=2,
        answer_semantic_validator=semantic_validator,
        answer_semantic_validator_version=getattr(semantic_validator, "semantic_version", 1),
        answer_semantic_rules=getattr(semantic_validator, "prompt_rules", ()),
    )
    runner_ref.append(runner)
    try:
        runner.run()
    except RunCrashed as exc:
        _publish_atomic(session_dir / "checkpoint.json",
                        lambda temporary: write_checkpoint(temporary, exc.checkpoint, ["events.jsonl"]))
        raise SharedEngineInterrupted(session_dir) from exc
    except Exception as exc:
        # The port already saved the original pre-send state, so a real process
        # death or SDK exception does not depend on SyntheticCrash control flow.
        raise SharedEngineInterrupted(session_dir) from exc
    return _export(task, services, runner, output=output, transport_origin=transport_origin)


def inspect_native_recovery(services, *, attempt_ref=None, intent=None):
    """Original native inspection only; an unknown result never triggers HTTP."""
    from src.utils.quick_scan_owner_research import OwnerResearchServices

    if not isinstance(services, OwnerResearchServices):
        raise SharedEngineRejected("original_owner_research_services_required")
    if (attempt_ref is None) == (intent is None):
        raise SharedEngineRejected("exactly_one_original_recovery_key_required")
    if attempt_ref is not None:
        return services.request_resume(attempt_ref)
    if not callable(getattr(services, "recover_intent", None)):
        return {
            "decision": "pause_for_inspection",
            "reason": "native_intent_lookup_not_available",
            "saved_receipt": None,
        }
    result = services.recover_intent(copy.deepcopy(intent))
    return result or {
        "decision": "pause_for_inspection",
        "reason": "no_native_intent_proof",
        "saved_receipt": None,
    }


def resume_shared_engine(
    task,
    services,
    session_config,
    checkpoint_path,
    output,
    *,
    session_dir,
    transport_origin="stockqa_live",
    replay_only=False,
):
    """Resume an original verified checkpoint through native read-before-send.

    A fresh private runtime port is created; hidden reasoning is never restored.
    Pending sent/unknown work requires original native safe output. Only an
    original released-unsent classification with no receipt may continue into
    normal dispatch, and never in replay_only mode. No lease is renewed here.
    """
    from iqs_agent_runtime_lab.port import create_runtime_port
    from iqs_company_agent_lab.canonical import sha256_hex
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir
    from iqs_company_agent_lab.resume import RecoveryMismatch, load_verified_recovery, reconcile_saved_receipt
    from iqs_company_agent_lab.runner import Runner
    from iqs_company_agent_lab.task import task_bundle

    config = preflight(task, services, session_config)
    if transport_origin not in {"stockqa_live", "scripted_wire"}:
        raise SharedEngineRejected("explicit_transport_origin_required")
    checkpoint_path, output, session_dir = Path(checkpoint_path), Path(output), Path(session_dir)
    semantic_validator = _production_answer_semantics(task, services)
    try:
        recovery = load_verified_recovery(checkpoint_path, task,
            answer_semantic_rules=getattr(semantic_validator, "legacy_prompt_rules",
                                          getattr(semantic_validator, "prompt_rules", ())))
    except RecoveryMismatch as error:
        raise SharedEngineRejected(str(error)) from error
    checkpoint, history = recovery.checkpoint, recovery.history_journals
    pending_intent, pending = recovery.pending_intent, recovery.pending_receipt
    if pending_intent is not None:
        if pending_intent.get("kind") != "model_step":
            raise SharedEngineRejected("non_model_pending_recovery_not_supported")
        recovered = inspect_native_recovery(
            services,
            **(
                {"attempt_ref": pending["runtime_attempt_ref"]}
                if pending is not None
                else {"intent": pending_intent}
            ),
        )
        unsent = (pending is None and not replay_only
                  and recovered.get("decision") == "not_sent"
                  and recovered.get("saved_receipt") is None)
        unavailable_read = (replay_only and recovered.get("saved_receipt") is None
                            and recovered.get("decision") != "recover_saved_receipt")
        if not (unsent or unavailable_read) and (recovered.get("decision") != "recover_saved_receipt"
                           or not recovered.get("saved_receipt")):
            raise SharedEngineRejected("native_safe_output_required_never_resend_unknown")
        # A missing response stays an open slot. In read-only mode it must not
        # hide earlier completed slots or authorize resending this pending one.
        native_saved = None if unsent or unavailable_read else recovered["saved_receipt"]
        try:
            pending = reconcile_saved_receipt(recovery, native_saved)
        except RecoveryMismatch as error:
            raise SharedEngineRejected(str(error)) from error
    elif pending is not None:
        raise SharedEngineRejected("orphan_pending_receipt")
    # Observe historical native receipts from their original source. No session,
    # hidden reasoning, response regeneration or model HTTP is involved.
    for reference in recovery.attempt_refs:
        services.inspect_attempt(reference)
    if (
        output.absolute() == session_dir.absolute()
        or output.absolute() in session_dir.absolute().parents
        or session_dir.absolute() in output.absolute().parents
    ):
        raise SharedEngineRejected("session_and_export_must_be_disjoint")
    ensure_safe_output_dir(output)
    session_dir = _new_session(session_dir, task)
    _write_atomic(
        session_dir / "parent-checkpoint.json",
        {
            "checkpoint_sha256": sha256_hex(checkpoint_path.read_bytes()),
            "event_head_sha256": recovery.event_head_sha256,
        },
    )
    journal = _journal(
        session_dir, task.raw["run_id"], start_seq=recovery.event_seq, start_head=recovery.event_head_sha256
    )
    port = create_runtime_port(services, task=task, session_config=config)
    runner_ref = []
    runner = Runner.continue_from_checkpoint(
        task,
        _pending_port(
            port, runner_ref, session_dir, history, recover_intent=services.recover_intent,
            replay_only=replay_only,
        ),
        checkpoint,
        journal,
        answer_semantic_validator=semantic_validator,
        answer_semantic_validator_version=getattr(semantic_validator, "semantic_version", 1),
        answer_semantic_rules=recovery.answer_semantic_rules,
    )
    runner_ref.append(runner)
    try:
        runner.run_continued(pending_intent, pending)
    except Exception as exc:
        raise SharedEngineInterrupted(session_dir) from exc
    return _export(
        task,
        services,
        runner,
        output=output,
        transport_origin=transport_origin,
        journals=history + [("events.jsonl", journal)],
        mode="native_owner_resume",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capabilities")
    report = commands.add_parser("report")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "capabilities":
        result = capabilities()
    else:
        from iqs_company_agent_lab.reporter import generate_report

        result = generate_report(args.input, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _scan_preflight(task, services, session_config):
    """Same native guards and executor, explicit one-shot scan profile."""
    from iqs_agent_runtime_lab.port import validate_session_config
    from iqs_company_agent_lab.scan_profile import validate_scan_task

    profile = validate_scan_task(task)
    config = validate_session_config(session_config)
    if config.get("logical_clock") is not False:
        raise SharedEngineRejected("native_runtime_requires_wall_clock")
    if config["planned_model"] != services.client.model:
        raise SharedEngineRejected("original_model_route_mismatch")
    caps = profile["resource_limits"]
    for actual, declared in (
        ("max_output_tokens", "logical_max_output_tokens_including_reasoning_per_request"),
        ("session_input_tokens", "session_input_tokens"),
        ("session_output_tokens", "session_output_tokens_including_reasoning"),
        ("wall_seconds", "company_wall_seconds"),
    ):
        if config[actual] > caps[declared]:
            raise SharedEngineRejected("scan_sdk_session_exceeds_profile_cap:" + actual)
    from iqs_company_agent_lab.canonical import sha256_hex

    for qid in task.question_ids:
        actual = services.lifecycle.question_pack_group_key(services.questions[qid])
        if sha256_hex(actual) != profile["native_pack_group_sha256"][qid]:
            raise SharedEngineRejected("scan_profile_native_pack_group_mismatch")
    # Compare display/provenance bytes against the ACTUAL native owner, not
    # just a caller-provided self-consistent profile. No second quote or grant.
    from iqs_company_agent_lab.scan_profile import (
        native_company_projection,
        native_input_references,
    )

    from src.utils.quick_scan_company_context import company_scan_inputs
    original = company_scan_inputs(services.lifecycle)
    refs = native_input_references(original.input_raw)
    subject = original.observation_context["questions"][task.question_ids[0]][
        "subject_binding"
    ]["subject_ref"]
    company = native_company_projection(
        json.loads(original.input_raw["identity.json"]).get("payload"), subject
    )
    expected_runtime = dict(
        protocol="iqs.company-scan-runtime/1.0.0",
        synthetic=False,
        provider=original.route_provider,
        model=original.route_model,
        native_inputs_sha256=sha256_hex(refs),
    )
    binding = dict(
        protocol="iqs.native-company-owner-binding/1.0.0",
        synthetic=False,
        subject_ref=subject,
        authority_ref=refs["authority.json"],
        native_scope={"scope": subject["scope"], "scope_id": subject["scope_id"]},
        original_inputs_sha256=sha256_hex(refs),
    )
    if (
        task.raw.get("native_inputs") != refs
        or task.company_doc != company
        or task.runtime_profile != expected_runtime
        or task.raw.get("module_locks") != original.bundle["manifest"]["module_locks"]
        or task.raw.get("owner_binding") != binding
        or getattr(task, "owner_binding", None) != binding
    ):
        raise SharedEngineRejected("scan_profile_original_native_source_projection_mismatch")
    if services.native_session:
        raise SharedEngineRejected("scan_multiturn_not_supported_in_one_shot_profile")
    if profile["route_id"] != original.route_id:
        raise SharedEngineRejected("scan_profile_native_route_mismatch")
    if not callable(getattr(services, "recover_intent", None)):
        raise SharedEngineRejected("original_native_intent_lookup_required")
    if services.attempt_observations(transport_origin="scripted_wire"):
        raise SharedEngineRejected("fresh_owner_service_observer_required")
    _production_answer_semantics(task, services)
    # Original comparison approval is exact, not a pack-size upper bound.
    for pack in profile["packs"]:
        services.owner.assert_execution_controls(
            pack_size=len(pack),
            thinking_enabled=True,
            max_output_tokens=config["max_output_tokens"],
        )

    return config


def _verified_finalization_export(task, export_dir, answer_semantic_rules=()):
    """Consume the Company's verified slot projection, not its file internals."""
    from iqs_company_agent_lab.resume import RecoveryMismatch, read_verified_answer_export

    try:
        slots, board = read_verified_answer_export(task, export_dir,
            answer_semantic_rules=answer_semantic_rules)
    except RecoveryMismatch as error:
        raise SharedEngineRejected(str(error)) from error
    return {"slots": slots}, board


def _native_final_answer(saved, question_id, expected_answer, *, evidence_board=None,
                         verified_source_urls=()):
    """Match the completed slot to safe original output, never caller text."""
    from iqs_company_agent_lab.answers import AnswerRejection, check_citation_closure, parse_answers_payload
    from iqs_company_agent_lab.strictjson import loads

    payloads = []
    if saved.get("final_content"):
        try:
            payloads.append(parse_answers_payload(saved["final_content"]))
        except (ValueError, TypeError, KeyError):
            # Runner supports a bare single-answer carrier. Require an entire
            # strict JSON value here; raw_decode would permit trailing text.
            try:
                bare = loads(saved["final_content"])
            except (ValueError, TypeError, KeyError):
                bare = None
            if (isinstance(bare, dict) and "answers" not in bare
                and bare.get("question_id") == question_id):
                payloads.append(dict(answers=[bare]))
    for call in saved.get("tool_calls") or []:
        if call.get("name") == "submit_answers":
            arguments = call.get("arguments")
            payloads.append(loads(arguments) if isinstance(arguments, str) else arguments)
    matches = []
    for payload in payloads:
        if not isinstance(payload, dict) or not isinstance(payload.get("answers"), list):
            continue
        matches.extend(
            answer
            for answer in payload["answers"]
            if isinstance(answer, dict) and answer.get("question_id") == question_id
        )
    if len(matches) != 1:
        raise SharedEngineRejected("finalization_answer_differs_from_original_native_output")
    original = copy.deepcopy(matches[0])
    if evidence_board is not None:
        # Runner validates citations in-place before committing a slot. Replay
        # its original rule against the byte-verified historical board, never a
        # caller board, and do not mutate native output/checkpoint/slot objects.
        board = copy.deepcopy(evidence_board)
        try:
            check_citation_closure(original, board, board.publication_exclusive_date,
                                   verified_source_urls=verified_source_urls)
        except (AnswerRejection, ValueError, TypeError, KeyError) as error:
            raise SharedEngineRejected("finalization_original_citation_validation_failed") from error
    if original != expected_answer:
        raise SharedEngineRejected("finalization_answer_differs_from_original_native_output")


def finalize_shared_engine(task, services, export_dir, *, question_ids=None):
    """Explicitly seal original successful answers with existing owner services.

    The research execute/resume APIs stay read/export-only. This separate API
    requires each final answer to match a safe original native response and
    its exact original work member. StockQA's public method restores the
    original handle (including its verified paid-response recovery rules),
    then commit_standard_answers preserves the same received answer.
    Existing matching checkpoints are reused without a lease or another HTTP.

    Each native checkpoint is atomic, while a multi-question publication can
    stop after an earlier checkpoint was saved. Such partial progress stays in
    the original store; invoking this API again reuses it, never resends a model
    request. Missing search proof or an unbound response remains a native refusal.

    By default every task slot must be completed, preserving the original API.
    An explicit question_ids subset saves only those original completed slots
    from the same verified export; incomplete members remain unfinalized and
    the result reports the entire original task scope, never full completion.
    """
    from src.utils.quick_scan_owner_research import OwnerResearchServices
    from src.utils.quick_scan_work_store import WorkConflictError, LeaseFencedError
    from src.utils.quick_scan_delivery_seal import get_matching_sealed_delivery

    if not isinstance(services, OwnerResearchServices) or services.task is not task:
        raise SharedEngineRejected("original_owner_research_services_required")
    services.validate_registered_inputs()
    selected_ids = None
    if question_ids is not None:
        if (not isinstance(question_ids, list) or not question_ids
            or any(not isinstance(qid, str) for qid in question_ids)
            or len(set(question_ids)) != len(question_ids)
            or not set(question_ids) <= set(task.question_ids)):
            raise SharedEngineRejected("finalization_original_question_selection_required")
        selected_ids = [qid for qid in task.question_ids if qid in question_ids]
    semantic_validator = _production_answer_semantics(task, services)
    if semantic_validator is None:
        raise SharedEngineRejected("original_production_answer_semantics_required")
    run, evidence_board = _verified_finalization_export(task, export_dir,
        getattr(semantic_validator, "legacy_prompt_rules", getattr(semantic_validator, "prompt_rules", ())))
    slots = run["slots"] if selected_ids is None else [
        row for row in run["slots"] if row["question_id"] in selected_ids
    ]
    if selected_ids is not None and [row["question_id"] for row in slots] != selected_ids:
        raise SharedEngineRejected("finalization_original_question_selection_mismatch")
    if any(row["execution_status"] != "completed" or row.get("answer") is None for row in slots):
        raise SharedEngineRejected("finalization_all_original_slots_must_be_completed")
    plan = []
    for slot in slots:
        qid, body = slot["question_id"], slot["answer"]
        try:
            probe = copy.deepcopy(body)
            getattr(semantic_validator, "base_semantic_validator", semantic_validator)(probe, qid)
            if probe != body:
                raise ValueError("original semantic validator changed answer")
        except Exception as error:
            raise SharedEngineRejected("finalization_standard_answer_contract_requires_repair") from error
        entry = services.owner.entries.get(qid)
        if not isinstance(entry, dict) or entry.get("kind") != "work":
            raise SharedEngineRejected("finalization_original_work_member_required")
        work_id = entry["work_item_id"]
        candidates = []
        for reference in reversed(slot.get("attempt_refs", [])):
            if not isinstance(reference, str) or not reference.startswith("stockqa:"):
                continue
            inspected = services.inspect_attempt(reference)
            saved = inspected.get("response_saved")
            if not inspected.get("known") or not isinstance(saved, dict):
                continue
            native = inspected["native_receipt"]
            members = [
                attempt
                for attempt in services.store.list_attempts(work_id)
                if (services.store.get_attempt_response(attempt["attempt_id"]) or {}).get("receipt") == native
            ]
            if len(members) == 1:
                if getattr(semantic_validator, "semantic_version", 1) == 2:
                    try:
                        probe = copy.deepcopy(body)
                        semantic_validator(probe, qid, attempt_ref=reference,
                                           evidence_board=copy.deepcopy(evidence_board))
                        if probe != body:
                            raise ValueError("original semantic validator changed answer")
                    except SharedEngineRejected as error:
                        if str(error) == "finalization_answer_differs_from_original_native_output":
                            continue
                        raise SharedEngineRejected("finalization_standard_answer_contract_requires_repair") from error
                    except Exception as error:
                        raise SharedEngineRejected("finalization_standard_answer_contract_requires_repair") from error
                else:
                    try:
                        _native_final_answer(saved, qid, body, evidence_board=evidence_board)
                    except SharedEngineRejected:
                        continue
                candidates.append((reference, members[0]["attempt_id"], native))
                break
        if not candidates:
            raise SharedEngineRejected("finalization_original_native_answer_and_member_required")
        reference, attempt_id, native = candidates[0]
        checkpoint = services.store.get_answer_checkpoint(work_id)
        if checkpoint is not None:
            standard = services.store.get_standard_answer(work_id)
            if (
                checkpoint["attempt_id"] != attempt_id
                or not isinstance(standard, dict)
                or standard.get("answer") != body
                or checkpoint["payload"]["provenance"].get("provider_attempt_id") != native["attempt_id"]
            ):
                raise SharedEngineRejected("finalization_existing_checkpoint_conflict")
        plan.append((qid, body, work_id, reference, checkpoint, attempt_id, native["attempt_id"]))
    # Inspect every selected original member/answer before the first save.
    # The native commit then independently rechecks lease, context, receipt and
    # schema atomically. This never grants or renews a work item.
    result, reused, errors, unsaved = [], [], [], []
    for qid, body, work_id, reference, checkpoint, attempt_id, native_id in plan:
        # The original service also repairs a prior checkpoint->seal crash.
        # Its idempotent branch validates the same full answer and receipt and
        # reseals through the native lifecycle, without another lease or send.
        existed = checkpoint is not None
        stage, failed = "restore", False
        try:
            if not existed:
                services.restore_finalization_handle(qid, native_reference=reference)
            stage = "commit"
            services.commit_standard_answers([copy.deepcopy(body)], native_reference=reference)
        except (WorkConflictError, LeaseFencedError) as error:
            failed = True
            errors.append(dict(question_id=qid, work_item_id=work_id, stage=stage,
                               error_type=type(error).__name__))
        checkpoint = services.store.get_answer_checkpoint(work_id)
        if checkpoint is None:
            if failed:
                unsaved.append(qid)
                continue
            raise SharedEngineRejected("finalization_native_checkpoint_not_persisted")
        standard = services.store.get_standard_answer(work_id)
        if (checkpoint["attempt_id"] != attempt_id or not isinstance(standard, dict)
            or standard.get("answer") != body
            or checkpoint["payload"]["provenance"].get("provider_attempt_id") != native_id):
            if failed:
                unsaved.append(qid)
                continue
            raise SharedEngineRejected("finalization_existing_checkpoint_conflict")
        if existed:
            reused.append(qid)
        delivery = services.store.get_result_delivery(work_id)
        matching_delivery = get_matching_sealed_delivery(
            services.store, work_id, authority=services.owner.bundle["authority"])
        result.append(dict(question_id=qid, work_item_id=work_id, native_reference=reference,
                           checkpoint_id=checkpoint["checkpoint_id"], checkpoint_sha256=checkpoint["payload_sha256"],
                           delivery_state=None if delivery is None else delivery["state"],
                           delivery_matches_authority=matching_delivery is not None))
    pending = [row["question_id"] for row in result if not row["delivery_matches_authority"]]
    result = dict(protocol="iqs.shared-engine-finalization/1.0.0", run_id=run["run_id"],
                status="partial" if unsaved else ("checkpointed_delivery_pending" if pending else "completed"),
                checkpoint_status="partial" if unsaved else "completed", pending_delivery_question_ids=pending,
                finalization_errors=errors, unfinalized_question_ids=unsaved,
                whole_task_finalized=not unsaved and not pending,
                checkpoints=result, reused_question_ids=reused,
                new_model_http=0, financial_accuracy_assessed=False)
    if selected_ids is not None:
        remaining = [qid for qid in task.question_ids if qid not in selected_ids or qid in unsaved]
        result.update(selected_question_ids=selected_ids,
                      selected_question_count=len(selected_ids),
                      original_question_count=len(task.question_ids),
                      unfinalized_question_ids=remaining,
                      whole_task_finalized=not remaining and not pending)
        if remaining:
            result.update(status="partial", checkpoint_status="partial")
    return result
