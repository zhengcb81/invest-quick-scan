"""Bounded first-party composition; no HTTP, model client, or ledger of its own.

The callable entry point consumes an already admitted StockQA owner service.
The CLI deliberately exposes only capabilities and validated report rendering;
it cannot turn arbitrary configuration, factories, or callbacks into authority.
"""

from __future__ import annotations

from iqs_scan import REPO_ROOT

import argparse
import copy
import json
import os
import sys
import tempfile
import time
from pathlib import Path


PROTOCOL = "iqs.shared-company-engine/1.1.0"

class SharedEngineRejected(ValueError):
    pass


class SharedEngineInterrupted(RuntimeError):
    """Original durable events remain available; this is not retry permission."""

    def __init__(self, session_dir):
        super().__init__("shared engine interrupted; inspect original session before recovery")
        self.session_dir = Path(session_dir)


def _current_owner_api_protocols():
    from .shared_company_ports import current_owner_api_protocols

    return current_owner_api_protocols()


def _task_contract(task):
    """Read the Company's versioned detached task DTO, never its fields."""
    from iqs_company_agent_lab.api import task_snapshot

    try:
        contract = task_snapshot(task)
    except (TypeError, ValueError) as error:
        raise SharedEngineRejected("original_company_task_contract_required") from error
    if contract.get("protocol") != "iqs.company-agent-task-contract/1.1.0":
        raise SharedEngineRejected("company_task_contract_version_unsupported")
    return contract


def _company_runtime(services, contract=None):
    """Ask StockQA's public API for its opaque, task-bound Runtime port."""
    try:
        from src.utils.quick_scan_company_api import create_company_research_runtime

        return create_company_research_runtime(services, task_contract=contract)
    except ImportError as error:
        raise SharedEngineRejected("stockqa_company_runtime_api_unavailable") from error
    except (TypeError, ValueError) as error:
        raise SharedEngineRejected(str(error)) from error


def capabilities():
    # Capability discovery reports our minimum public-port requirements and
    # remains usable before sibling repositories are installed. Runtime
    # admission checks their actual declarations separately.
    from .shared_company_ports import required_owner_api_protocols

    owner_apis = required_owner_api_protocols()
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
        # Historical sample metadata is informational only. Execution is
        # derived from the bound task and StockQA's endpoint capabilities.
        "legacy_sample_profile": {
            "registered_question_count": 12,
            "cutoff": "2026-10-13",
            "provider": "mimo",
            "pack_size_range": [1, 12],
        },
        "strategies": ["fixed3", "free_agent", "evidence_agent"],
        "generation_mode": "native_one_shot_question_pack",
        "company_scan": {
            "task_protocol": "iqs.company-scan-task/1.0.0",
            "profile_protocol": "iqs.company-scan-profile/1.0.0",
            "factory": "create_company_scan_task",
            "question_set": "original_approved_nonempty_unique_subset",
            "cutoff": "original_owner_actual_cutoff",
            "pack_size_range": "owner_admitted_positive_range",
            "mode": "one_shot_packs",
            "provider_selection": "original_stockqa_endpoint_capabilities",
            "required_execution_controls": ["thinking_enabled", "max_output_tokens"],
            "automatic_cross_model_fallback": False,
            "resource_defaults": "derived_from_actual_question_packs",
            "search_queries": 0,
            "qualification_granted": False,
        },
        "required_owner_api_protocols": owner_apis,
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
    try:
        _current_owner_api_protocols()
    except ValueError as error:
        raise SharedEngineRejected(str(error)) from error
    from iqs_agent_runtime_lab.api import validate_session_config
    from iqs_company_agent_lab.api import task_pack_sizes
    contract = _task_contract(task)
    runtime = _company_runtime(services, contract)
    if contract["company_doc"].get("origin") != "owner_public" or not contract.get("owner_binding"):
        raise SharedEngineRejected("original_owner_public_binding_required")
    raw = contract["raw"]
    question_ids = contract["question_ids"]
    pack_sizes = task_pack_sizes(task)
    if raw.get("protocol") == "iqs.company-scan-task/1.0.0":
        return _scan_preflight(task, services, session_config)
    if not question_ids or not isinstance(raw.get("information_cutoff"), str) or not pack_sizes:
        raise SharedEngineRejected("registered_question_task_contract_required")
    config = validate_session_config(session_config)
    if config.get("logical_clock") is not False:
        raise SharedEngineRejected("native_runtime_requires_wall_clock")
    if config["planned_model"] != runtime.model:
        raise SharedEngineRejected("original_model_route_mismatch")
    if runtime.has_native_session():
        # All three registered strategies may select several questions in one
        # intent. Native session registration presently supports singleton work.
        raise SharedEngineRejected("native_multiturn_question_pack_not_supported")
    if not runtime.supports_intent_recovery():
        raise SharedEngineRejected("original_native_intent_lookup_required")
    if runtime.attempt_observations(transport_origin="scripted_wire"):
        # Observer classification is per execution, while native SQLite and
        # budget history persist. Reusing a prior run's observer would mislabel
        # historical responses as newly sent requests in the new summary.
        raise SharedEngineRejected("fresh_owner_service_observer_required")
    _production_answer_semantics(task, runtime)
    runtime.check_admission()
    runtime.assert_execution_controls(
        pack_size=max(pack_sizes),
        thinking_enabled=True,
        max_output_tokens=config["max_output_tokens"],
    )
    return config


def _original_answer_resources(context, root):
    """Compatibility wrapper for callers of the original helper."""
    from iqs_scan.answers import api
    try:
        return api.original_answer_resources(context, root)
    except api.AnswerSemanticsRejected as error:
        raise SharedEngineRejected(str(error)) from error


def _frozen_answer_semantics(task, context, *, release_root=None, semantic_resources=None):
    """Delegate answer validation to the IQS-owned public validation module."""
    from iqs_scan.answers import api
    try:
        return api.frozen_answer_semantics(
            task,
            context,
            release_root=release_root,
            semantic_resources=semantic_resources,
        )
    except api.AnswerSemanticsRejected as error:
        raise SharedEngineRejected(str(error)) from error


def _production_answer_semantics(task, services, *, for_publication=False):
    # Synthetic/old research entry points retain their historical default.
    # Public production preflight already requires an original owner task.
    try:
        contract = _task_contract(task)
    except SharedEngineRejected:
        # Synthetic/local research tests retain their historical no-native
        # semantics; production preflight requires the versioned DTO first.
        return None
    if contract["company_doc"].get("origin") != "owner_public":
        return None
    runtime = _company_runtime(services, contract)
    inputs = runtime.original_scan_context()
    context = inputs.observation_context
    # StockQA 1.7 resolves the compatibility module from the selected checkout.
    script_root = str(REPO_ROOT / "scripts")
    if script_root not in sys.path:
        sys.path.insert(0, script_root)
    # The owner resolves its original frozen package. Only a detached, path-free
    # semantic resource DTO crosses the runtime boundary; production never falls
    # back to the current IQS code/release tree.
    try:
        resources = runtime.original_semantic_resources()
    except (TypeError, ValueError) as error:
        raise SharedEngineRejected(str(error) or "original_semantic_resources_unavailable") from error
    original = _frozen_answer_semantics(
        contract, context, semantic_resources=resources
    )

    def validate_native(answer, question_id, *, attempt_ref, evidence_board):
        original(answer, question_id)
        return _validate_native_answer_sources(contract, runtime, context, answer, question_id,
                                               attempt_ref=attempt_ref, evidence_board=evidence_board,
                                               for_publication=for_publication)

    validate_native.semantic_version = 2
    validate_native.base_semantic_validator = original
    validate_native.prompt_rules = original.prompt_rules
    validate_native.legacy_prompt_rules = original.legacy_prompt_rules
    return validate_native


def _validate_native_answer_sources(task, services, context, answer, question_id,
                                    *, attempt_ref, evidence_board, for_publication):
    """Read the exact native member/use proof; never infer a latest response."""
    from iqs_company_agent_lab.api import check_citation_closure
    if evidence_board is None:
        raise ValueError("original successful current native reference required")
    runtime = _company_runtime(services, task)
    sources = runtime.answer_source_context(question_id, attempt_ref, context)
    body, board = copy.deepcopy(answer), copy.deepcopy(evidence_board)
    # A diagnostic with no claims may complete research/replay of an already
    # received response. Publishing a native checkpoint still requires search.
    source_free_diagnostic = (
        body["status"] in {"not_applicable", "insufficient_evidence", "search_unavailable"}
        and body.get("score") is None and not body.get("evidence")
    )
    if not sources["verified_search"] and (for_publication or not source_free_diagnostic):
        raise ValueError("original verified source projection required")
    verified_urls = sources["source_urls"]
    check_citation_closure(body, board, board.publication_exclusive_date,
                           verified_source_urls=verified_urls)
    _native_final_answer(sources["response"], question_id, body,
                         evidence_board=evidence_board, verified_source_urls=verified_urls)
    runtime.validate_answer_transport(body, question_id, sources)
    return verified_urls


def _write_atomic(path, payload):
    """Same-directory replacement retains the last complete original record."""
    from iqs_company_agent_lab.api import canonical_json
    from iqs_company_agent_lab.api import scan_for_secret

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
    from iqs_company_agent_lab.api import ensure_safe_output_dir
    from iqs_company_agent_lab.api import task_bundle

    session_dir = Path(session_dir)
    ensure_safe_output_dir(session_dir)
    session_dir.mkdir(exist_ok=False)
    _write_atomic(session_dir / "task-bundle.json", task_bundle(task))
    return session_dir


def _journal(session_dir, run_id, *, start_seq=-1, start_head=None):
    from iqs_company_agent_lab.api import canonical_json
    from iqs_company_agent_lab.api import create_durable_event_journal

    def persist_events(events):
        raw = ("\n".join(canonical_json(row) for row in events) + "\n").encode("utf8")
        _publish_atomic(session_dir / "events.jsonl", lambda temporary: temporary.write_bytes(raw))

    return create_durable_event_journal(
        run_id, persist_events, start_seq=start_seq, start_head=start_head
    )


def _pending_port(port, runner_ref, session_dir, history_journals=(), recover_intent=None,
                  replay_only=False):
    """Save original pending state before HTTP, without another execution loop."""
    from iqs_company_agent_lab.api import canonical_json
    from iqs_company_agent_lab.api import build_runner_checkpoint, write_checkpoint
    from iqs_company_agent_lab.api import event_journal_projection, runner_event_projection

    class CheckpointedPort:
        def _save(self, intent, receipt=None):
            runner = runner_ref[0]
            import hashlib
            events = [
                event
                for _, journal in history_journals
                for event in event_journal_projection(journal)["events"]
            ] + runner_event_projection(runner)["events"]
            raw = ("\n".join(canonical_json(e) for e in events) + "\n").encode("utf8")
            # 128-bit filename discriminator avoids growing Windows paths;
            # exact bytes and the original full event/checkpoint hashes remain checked.
            sequence = runner_event_projection(runner)["sequence"]
            name = "pending-history-" + str(sequence) + "-" + hashlib.sha256(raw).hexdigest()[:32] + ".jsonl"
            history = session_dir / name
            if history.exists():
                if history.read_bytes() != raw:
                    raise SharedEngineRejected("immutable_pending_history_conflict")
            else:
                _publish_atomic(history, lambda temporary: temporary.write_bytes(raw))
            checkpoint = build_runner_checkpoint(
                runner, pending_intent=intent, pending_receipt=receipt
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
                from iqs_company_agent_lab.api import raise_saved_response_boundary
                raise_saved_response_boundary("replay_only_saved_responses_exhausted")
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
                from iqs_company_agent_lab.api import raise_saved_response_boundary
                raise_saved_response_boundary("replay_only_new_search_forbidden")
            return port.search(envelope)

        def inspect_attempt(self, ref):
            return port.inspect_attempt(ref)

        def request_resume(self, ref):
            return port.request_resume(ref)

    return CheckpointedPort()


def _export(
    task, runtime, runner, *, output, transport_origin, journals=None, mode="native_owner"
):
    from iqs_company_agent_lab.api import write_runner_export

    return write_runner_export(
        task,
        runner,
        Path(output),
        journals=journals,
        attempts=runtime.attempt_observations(transport_origin=transport_origin),
        transport_origin=transport_origin,
        mode=mode,
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
    from iqs_agent_runtime_lab.api import create_runtime_port
    from iqs_company_agent_lab.api import ensure_safe_output_dir

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
    contract = _task_contract(task)
    runtime = _company_runtime(services, contract)
    port = create_runtime_port(runtime, task=contract, session_config=config)
    return _execute_with_port(
        task,
        services,
        port,
        runtime=runtime,
        output=output,
        session_dir=session_dir,
        transport_origin=transport_origin,
    )


def _execute_with_port(task, services, port, *, output, session_dir, transport_origin,
                       runtime=None):
    """Internal engine seam also exercised by explicitly synthetic tests.

    This is not the owner-admitting public entry point. No caller callback or
    Python factory is loaded by the CLI. The sole scheduling loop is Runner.
    """
    from iqs_company_agent_lab.api import write_checkpoint
    from iqs_company_agent_lab.api import RunnerPortCrashed, create_runner_port

    contract = _task_contract(task)
    session_dir = _new_session(session_dir, task)
    journal = _journal(session_dir, contract["raw"]["run_id"])
    runner_ref = []
    observation_port = runtime if runtime is not None else services
    semantic_validator = _production_answer_semantics(task, observation_port)
    recover_intent = getattr(observation_port, "recover_intent", None)
    supports_recovery = getattr(observation_port, "supports_intent_recovery", None)
    if callable(supports_recovery) and not supports_recovery():
        recover_intent = None
    runner = create_runner_port(
        task,
        _pending_port(
            port, runner_ref, session_dir, recover_intent=recover_intent
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
    except RunnerPortCrashed as exc:
        checkpoint = exc.checkpoint
        _publish_atomic(session_dir / "checkpoint.json",
                        lambda temporary: write_checkpoint(temporary, checkpoint, ["events.jsonl"]))
        raise SharedEngineInterrupted(session_dir) from exc
    except Exception as exc:
        # The port already saved the original pre-send state, so a real process
        # death or SDK exception does not depend on SyntheticCrash control flow.
        raise SharedEngineInterrupted(session_dir) from exc
    return _export(task, observation_port, runner, output=output,
                   transport_origin=transport_origin)


def inspect_native_recovery(services, *, attempt_ref=None, intent=None):
    """Original native inspection only; an unknown result never triggers HTTP."""
    try:
        _current_owner_api_protocols()
    except ValueError as error:
        raise SharedEngineRejected(str(error)) from error
    runtime = _company_runtime(services)
    if (attempt_ref is None) == (intent is None):
        raise SharedEngineRejected("exactly_one_original_recovery_key_required")
    if attempt_ref is not None:
        return runtime.request_resume(attempt_ref)
    if not runtime.supports_intent_recovery():
        return {
            "decision": "pause_for_inspection",
            "reason": "native_intent_lookup_not_available",
            "saved_receipt": None,
        }
    result = runtime.recover_intent(copy.deepcopy(intent))
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
    from iqs_agent_runtime_lab.api import create_runtime_port
    from iqs_company_agent_lab.api import sha256_hex
    from iqs_company_agent_lab.api import ensure_safe_output_dir
    from iqs_company_agent_lab.api import RecoveryMismatch, load_verified_recovery, reconcile_saved_receipt
    from iqs_company_agent_lab.api import continue_runner_port

    config = preflight(task, services, session_config)
    if transport_origin not in {"stockqa_live", "scripted_wire"}:
        raise SharedEngineRejected("explicit_transport_origin_required")
    checkpoint_path, output, session_dir = Path(checkpoint_path), Path(output), Path(session_dir)
    semantic_validator = _production_answer_semantics(task, services)
    contract = _task_contract(task)
    runtime = _company_runtime(services, contract)
    try:
        recovery = load_verified_recovery(checkpoint_path, task,
            answer_semantic_rules=getattr(semantic_validator, "legacy_prompt_rules",
                                          getattr(semantic_validator, "prompt_rules", ())))
    except RecoveryMismatch as error:
        raise SharedEngineRejected(str(error)) from error
    from iqs_company_agent_lab.api import recovery_event_journals, recovery_projection

    projection = recovery_projection(recovery)
    checkpoint, history = projection["checkpoint"], recovery_event_journals(recovery)
    pending_intent, pending = projection["pending_intent"], projection["pending_receipt"]
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
    for reference in projection["attempt_refs"]:
        runtime.inspect_attempt(reference)
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
            "event_head_sha256": projection["event_head_sha256"],
        },
    )
    journal = _journal(
        session_dir,
        _task_contract(task)["raw"]["run_id"],
        start_seq=projection["event_seq"],
        start_head=projection["event_head_sha256"],
    )
    port = create_runtime_port(runtime, task=contract, session_config=config)
    runner_ref = []
    runner = continue_runner_port(
        task,
        _pending_port(
            port, runner_ref, session_dir, history,
            recover_intent=runtime.recover_intent if runtime.supports_intent_recovery() else None,
            replay_only=replay_only,
        ),
        checkpoint,
        journal,
        answer_semantic_validator=semantic_validator,
        answer_semantic_validator_version=getattr(semantic_validator, "semantic_version", 1),
        answer_semantic_rules=projection["answer_semantic_rules"],
    )
    runner_ref.append(runner)
    try:
        runner.run_continued(pending_intent, pending)
    except Exception as exc:
        raise SharedEngineInterrupted(session_dir) from exc
    return _export(
        task,
        runtime,
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
        from iqs_company_agent_lab.api import generate_report

        result = generate_report(args.input, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0




def _scan_preflight(task, services, session_config):
    """Same native guards and executor, explicit one-shot scan profile."""
    from iqs_agent_runtime_lab.api import validate_session_config
    from iqs_company_agent_lab.api import validate_scan_task
    profile = validate_scan_task(task)
    contract = _task_contract(task)
    raw = contract["raw"]
    question_ids = contract["question_ids"]
    config = validate_session_config(session_config)
    # Caller-controlled resource limits are deterministic. Reject an invalid
    # profile before asking StockQA to bind or inspect the owner service.
    caps = profile["resource_limits"]
    for actual, declared in (
        ("max_output_tokens", "logical_max_output_tokens_including_reasoning_per_request"),
        ("session_input_tokens", "session_input_tokens"),
        ("session_output_tokens", "session_output_tokens_including_reasoning"),
        ("wall_seconds", "company_wall_seconds"),
    ):
        if config[actual] > caps[declared]:
            raise SharedEngineRejected("scan_sdk_session_exceeds_profile_cap:" + actual)
    if config.get("logical_clock") is not False:
        raise SharedEngineRejected("native_runtime_requires_wall_clock")
    runtime = _company_runtime(services, contract)
    if config["planned_model"] != runtime.model:
        raise SharedEngineRejected("original_model_route_mismatch")
    from iqs_company_agent_lab.api import sha256_hex

    for qid in question_ids:
        actual = runtime.pack_group_key(qid)
        if sha256_hex(actual) != profile["native_pack_group_sha256"][qid]:
            raise SharedEngineRejected("scan_profile_native_pack_group_mismatch")
    # Compare display/provenance bytes against the ACTUAL native owner, not
    # just a caller-provided self-consistent profile. No second quote or grant.
    from iqs_company_agent_lab.api import native_company_projection

    original = runtime.original_scan_context()
    refs = dict(original.native_input_references)
    subject = original.observation_context["questions"][question_ids[0]][
        "subject_binding"
    ]["subject_ref"]
    company = native_company_projection(
        dict(original.identity_payload), subject
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
        raw.get("native_inputs") != refs
        or contract["company_doc"] != company
        or contract["runtime_profile"] != expected_runtime
        or raw.get("module_locks") != [dict(lock) for lock in original.module_locks]
        or raw.get("owner_binding") != binding
        or contract.get("owner_binding") != binding
    ):
        raise SharedEngineRejected("scan_profile_original_native_source_projection_mismatch")
    if runtime.has_native_session():
        raise SharedEngineRejected("scan_multiturn_not_supported_in_one_shot_profile")
    if profile["route_id"] != original.route_id:
        raise SharedEngineRejected("scan_profile_native_route_mismatch")
    if not runtime.supports_intent_recovery():
        raise SharedEngineRejected("original_native_intent_lookup_required")
    if runtime.attempt_observations(transport_origin="scripted_wire"):
        raise SharedEngineRejected("fresh_owner_service_observer_required")
    _production_answer_semantics(task, runtime)
    # Original comparison approval is exact, not a pack-size upper bound.
    for pack in profile["packs"]:
        runtime.assert_execution_controls(
            pack_size=len(pack),
            thinking_enabled=True,
            max_output_tokens=config["max_output_tokens"],
        )

    return config


def _verified_finalization_export(task, export_dir, answer_semantic_rules=()):
    """Consume the Company's verified slot projection, not its file internals."""
    from iqs_company_agent_lab.api import RecoveryMismatch, read_verified_answer_export

    try:
        slots, board = read_verified_answer_export(task, export_dir,
            answer_semantic_rules=answer_semantic_rules)
    except RecoveryMismatch as error:
        raise SharedEngineRejected(str(error)) from error
    return {"slots": slots}, board


def _native_final_answer(saved, question_id, expected_answer, *, evidence_board=None,
                         verified_source_urls=()):
    """Match the completed slot to safe original output, never caller text."""
    from iqs_company_agent_lab.api import AnswerRejection, check_citation_closure, parse_answers_payload
    from iqs_company_agent_lab.api import loads

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
    try:
        _current_owner_api_protocols()
    except ValueError as error:
        raise SharedEngineRejected(str(error)) from error
    contract = _task_contract(task)
    runtime = _company_runtime(services, contract)
    task_question_ids = contract["question_ids"]
    runtime.validate_registered_inputs()
    selected_ids = None
    if question_ids is not None:
        if (not isinstance(question_ids, list) or not question_ids
            or any(not isinstance(qid, str) for qid in question_ids)
            or len(set(question_ids)) != len(question_ids)
            or not set(question_ids) <= set(task_question_ids)):
            raise SharedEngineRejected("finalization_original_question_selection_required")
        selected_ids = [qid for qid in task_question_ids if qid in question_ids]
    semantic_validator = _production_answer_semantics(task, runtime, for_publication=True)
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
        work_id = runtime.work_item_id(qid)
        if work_id is None:
            raise SharedEngineRejected("finalization_original_work_member_required")
        original = None
        for reference in reversed(slot.get("attempt_refs", [])):
            if not isinstance(reference, str) or not reference.startswith("stockqa:"):
                continue
            inspected = runtime.inspect_answer_reference(work_id, reference)
            if inspected is None:
                continue
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
                    _native_final_answer(inspected["response"], qid, body, evidence_board=evidence_board)
                except SharedEngineRejected:
                    continue
            original = (reference, inspected["attempt_id"], inspected["provider_attempt_id"])
            break
        if original is None:
            raise SharedEngineRejected("finalization_original_native_answer_and_member_required")
        reference, attempt_id, provider_attempt_id = original
        checkpoint = runtime.checkpoint(work_id, body, attempt_id, provider_attempt_id)
        if checkpoint["status"] == "conflict":
            raise SharedEngineRejected("finalization_existing_checkpoint_conflict")
        plan.append((qid, body, work_id, reference, checkpoint["status"] == "matching", attempt_id, provider_attempt_id))
    # Inspect every selected original member/answer before the first save.
    # The native commit then independently rechecks lease, context, receipt and
    # schema atomically. This never grants or renews a work item.
    result, reused, errors, unsaved = [], [], [], []
    for qid, body, work_id, reference, existed, attempt_id, native_id in plan:
        # The original service also repairs a prior checkpoint->seal crash.
        # Its idempotent branch validates the same full answer and receipt and
        # reseals through the native lifecycle, without another lease or send.
        failure = runtime.publish_answer(qid, body, reference, checkpoint_exists=existed)
        if failure is not None:
            errors.append(dict(question_id=qid, work_item_id=work_id, **failure))
        checkpoint = runtime.checkpoint(work_id, body, attempt_id, native_id)
        if checkpoint["status"] != "matching":
            if failure is not None:
                unsaved.append(qid)
                continue
            if checkpoint["status"] == "missing":
                raise SharedEngineRejected("finalization_native_checkpoint_not_persisted")
            raise SharedEngineRejected("finalization_existing_checkpoint_conflict")
        if existed:
            reused.append(qid)
        delivery = runtime.delivery(work_id)
        result.append(dict(question_id=qid, work_item_id=work_id, native_reference=reference,
                           checkpoint_id=checkpoint["checkpoint_id"], checkpoint_sha256=checkpoint["sha256"],
                           delivery_state=delivery["state"], delivery_matches_authority=delivery["matches_authority"]))
    pending = [row["question_id"] for row in result if not row["delivery_matches_authority"]]
    result = dict(protocol="iqs.shared-engine-finalization/1.0.0", run_id=contract["raw"]["run_id"],
                status="partial" if unsaved else ("checkpointed_delivery_pending" if pending else "completed"),
                checkpoint_status="partial" if unsaved else "completed", pending_delivery_question_ids=pending,
                finalization_errors=errors, unfinalized_question_ids=unsaved,
                whole_task_finalized=not unsaved and not pending,
                checkpoints=result, reused_question_ids=reused,
                new_model_http=0, financial_accuracy_assessed=False)
    if selected_ids is not None:
        remaining = [qid for qid in task_question_ids if qid not in selected_ids or qid in unsaved]
        result.update(selected_question_ids=selected_ids,
                      selected_question_count=len(selected_ids),
                      original_question_count=len(task_question_ids),
                      unfinalized_question_ids=remaining,
                      whole_task_finalized=not remaining and not pending)
        if remaining:
            result.update(status="partial", checkpoint_status="partial")
    return result
