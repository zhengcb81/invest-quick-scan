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
        "requires": ["original_ApprovedRefreshSession", "original_OwnerResearchServices",
                     "original_Runner", "original_RuntimeBridgePort", "native_safe_visible_output"],
        "registered_question_count": 12,
        "registered_cutoff": "2026-10-13",
        "strategies": ["fixed3", "free_agent", "evidence_agent"],
        "generation_mode": "native_one_shot_question_pack",
        "question_pack_provider": "mimo",
        "unsupported": ["native_multiturn_packs", "generic_question_sets", "automatic_unknown_resend",
                        "official_search_backed_checkpoint", "cli_owner_construction"],
        "financial_accuracy_assessed": False,
        "production_owner_admitted": False,
    }


def preflight(task, services, session_config):
    """Validate the bounded composition without claiming a new owner grant."""
    from iqs_company_agent_lab.task import LoadedTask
    from iqs_company_agent_lab.strategy import strategy_for_task
    from iqs_agent_runtime_lab.port import validate_session_config
    from src.utils.quick_scan_owner_research import OwnerResearchServices

    if not isinstance(services, OwnerResearchServices):
        raise SharedEngineRejected("original_owner_research_services_required")
    if not isinstance(task, LoadedTask) or services.task is not task:
        raise SharedEngineRejected("original_service_bound_task_required")
    if task.company_doc.get("origin") != "owner_public" or not getattr(task, "owner_binding", None):
        raise SharedEngineRejected("original_owner_public_binding_required")
    strategy_for_task(task)  # Full question IDs, contracts and scheduling projection.
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
    if services.client.provider_name != "mimo":
        raise SharedEngineRejected("native_one_shot_question_pack_requires_mimo")
    services.owner.check()
    services.owner.assert_execution_controls(pack_size=12 if task.raw["strategy_id"] == "free_agent" else 3, thinking_enabled=True,
        max_output_tokens=config["max_output_tokens"])
    return config


def _write_atomic(path, payload):
    """Same-directory replacement retains the last complete original record."""
    from iqs_company_agent_lab.events import scan_for_secret
    from iqs_company_agent_lab.canonical import canonical_json
    raw = canonical_json(payload).encode("utf8")
    scan_for_secret(raw.decode("utf8"))
    temp = path.with_name(path.name + ".pending")
    with temp.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    _replace_record(temp, path)


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
            time.sleep(0.01 * 2 ** attempt)


def _new_session(session_dir, task):
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir
    from iqs_company_agent_lab.task import task_bundle
    session_dir = Path(session_dir)
    ensure_safe_output_dir(session_dir)
    session_dir.mkdir(exist_ok=False)
    _write_atomic(session_dir / "task-bundle.json", task_bundle(task))
    return session_dir


def _journal(session_dir, run_id, *, start_seq=-1, start_head=None):
    from iqs_company_agent_lab.events import EventJournal
    from iqs_company_agent_lab.canonical import canonical_json

    class DurableOriginalJournal(EventJournal):
        """Original event validation/hash chain; add only atomic persistence."""
        def append(self, event_type, data, segment_id=None):
            event = super().append(event_type, data, segment_id)
            raw = ("\n".join(canonical_json(row) for row in self.events) + "\n").encode("utf8")
            path = session_dir / "events.jsonl"
            temporary = session_dir / "events.jsonl.pending"
            with temporary.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            _replace_record(temporary, path)
            return event
    return DurableOriginalJournal(run_id, start_seq=start_seq, start_head_sha256=start_head)


def _pending_port(port, runner_ref, session_dir, history_journals=(), recover_intent=None):
    """Save original pending state before HTTP, without another execution loop."""
    from iqs_company_agent_lab.checkpoint import build_checkpoint, write_checkpoint
    from iqs_company_agent_lab.canonical import canonical_json

    class CheckpointedPort:
        def _save(self, intent, receipt=None):
            runner = runner_ref[0]
            name = "pending-history-" + str(runner.journal.seq) + ".jsonl"
            history = session_dir / name
            events = [e for _, journal in history_journals for e in journal.events] + runner.journal.events
            raw = ("\n".join(canonical_json(e) for e in events) + "\n").encode("utf8")
            if history.exists():
                if history.read_bytes() != raw:
                    raise SharedEngineRejected("immutable_pending_history_conflict")
            else:
                with history.open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            checkpoint = build_checkpoint(runner.state, runner.journal,
                pending_intent=intent, pending_receipt=receipt)
            path = session_dir / "checkpoint.json"
            temporary = session_dir / "checkpoint.json.pending"
            if temporary.exists():
                raise SharedEngineRejected("incomplete_checkpoint_requires_inspection")
            write_checkpoint(temporary, checkpoint, [name])
            with temporary.open("r+b") as stream:
                os.fsync(stream.fileno())
            _replace_record(temporary, path)

        def model_step(self, envelope):
            self._save(envelope["intent"])
            if recover_intent is not None:
                recovered = recover_intent(copy.deepcopy(envelope["intent"]))
                if recovered is not None:
                    if recovered.get("decision") != "recover_saved_receipt" or not recovered.get("saved_receipt"):
                        raise SharedEngineRejected("native_prior_intent_unresolved_never_resend")
                    result = recovered["saved_receipt"]
                    self._save(envelope["intent"], result)
                    return result
            result = port.model_step(envelope)
            self._save(envelope["intent"], result)
            return result

        def search(self, envelope):
            return port.search(envelope)

        def inspect_attempt(self, ref):
            return port.inspect_attempt(ref)

        def request_resume(self, ref):
            return port.request_resume(ref)

    return CheckpointedPort()


def _export(task, services, runner, *, output, transport_origin, journals=None, mode="native_owner"):
    from iqs_company_agent_lab.checkpoint import build_checkpoint
    from iqs_company_agent_lab.export import write_run_export
    from iqs_company_agent_lab.provenance import runtime_evidence_document, _evidence_origin
    from iqs_company_agent_lab.runner import input_manifest_sha256
    journals = journals or [("events.jsonl", runner.journal)]
    events = [event for _, journal in journals for event in journal.events]
    evidence = runtime_evidence_document(run_id=task.raw["run_id"],
        input_manifest_sha256=input_manifest_sha256(task.raw), events=events,
        attempts=services.attempt_observations(transport_origin=transport_origin),
        evidence_origin=_evidence_origin(task.evidence_board_doc, runner.state.board.snapshot()))
    checkpoint = build_checkpoint(runner.state, runner.journal)
    return write_run_export(Path(output), runner.state, journals,
        input_manifest_sha256(task.raw), mode, checkpoint=checkpoint, runtime_evidence=evidence)


def execute_shared_engine(task, services, session_config, output, *, session_dir,
                          transport_origin="stockqa_live"):
    """Execute the sole original Runner using original approved native services.

    Output remains a research artifact, not an official owner checkpoint. The
    caller must describe its observed wire as scripted_wire in offline tests.
    Native refusal, failed output or interrupted execution does not authorize
    another send. The durable session directory is retained for inspection.
    """
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir
    from iqs_company_agent_lab.runner import Runner, RunCrashed
    from iqs_company_agent_lab.checkpoint import write_checkpoint
    from iqs_agent_runtime_lab.port import create_runtime_port

    config = preflight(task, services, session_config)
    if transport_origin not in {"stockqa_live", "scripted_wire"}:
        raise SharedEngineRejected("explicit_transport_origin_required")
    output, session_dir = Path(output), Path(session_dir)
    if output.absolute() == session_dir.absolute() or output.absolute() in session_dir.absolute().parents or session_dir.absolute() in output.absolute().parents:
        raise SharedEngineRejected("session_and_export_must_be_disjoint")
    ensure_safe_output_dir(output)  # Fail before any send or session creation.
    port = create_runtime_port(services, task=task, session_config=config)
    return _execute_with_port(task, services, port, output=output,
        session_dir=session_dir, transport_origin=transport_origin)


def _execute_with_port(task, services, port, *, output, session_dir, transport_origin):
    """Internal engine seam also exercised by explicitly synthetic tests.

    This is not the owner-admitting public entry point. No caller callback or
    Python factory is loaded by the CLI. The sole scheduling loop is Runner.
    """
    from iqs_company_agent_lab.runner import Runner, RunCrashed
    from iqs_company_agent_lab.checkpoint import write_checkpoint
    session_dir = _new_session(session_dir, task)
    journal = _journal(session_dir, task.raw["run_id"])
    runner_ref = []
    runner = Runner(task, _pending_port(port, runner_ref, session_dir,
        recover_intent=getattr(services, "recover_intent", None)), journal=journal, execution_revision=2)
    runner_ref.append(runner)
    try:
        runner.run()
    except RunCrashed as exc:
        write_checkpoint(session_dir / "checkpoint.json", exc.checkpoint, ["events.jsonl"])
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
        return {"decision": "pause_for_inspection", "reason": "native_intent_lookup_not_available",
                "saved_receipt": None}
    result = services.recover_intent(copy.deepcopy(intent))
    return result or {"decision": "pause_for_inspection", "reason": "no_native_intent_proof",
                      "saved_receipt": None}


def resume_shared_engine(task, services, session_config, checkpoint_path, output, *,
                         session_dir, transport_origin="stockqa_live"):
    """Resume an original verified checkpoint through native read-before-send.

    A fresh private runtime port is created; hidden reasoning is never restored.
    Pending work without original native safe-output proof is refused before a
    new session or HTTP. This does not implement lease renewal or owner consent.
    """
    from iqs_company_agent_lab.checkpoint import load_checkpoint
    from iqs_company_agent_lab.canonical import sha256_hex
    from iqs_company_agent_lab.events import EventJournal
    from iqs_company_agent_lab.resume import _verify_snapshot_against_history, journals_for_export
    from iqs_company_agent_lab.runner import Runner
    from iqs_company_agent_lab.task import task_bundle
    from iqs_company_agent_lab.pathsafety import ensure_safe_output_dir, check_traceable_links
    from iqs_agent_runtime_lab.port import create_runtime_port

    config = preflight(task, services, session_config)
    if transport_origin not in {"stockqa_live", "scripted_wire"}:
        raise SharedEngineRejected("explicit_transport_origin_required")
    checkpoint_path, output, session_dir = Path(checkpoint_path), Path(output), Path(session_dir)
    check_traceable_links(checkpoint_path)
    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint.get("protocol") != "iqs.company-agent-lab.checkpoint/1.1.0":
        raise SharedEngineRejected("original_revision_two_checkpoint_required")
    if sha256_hex(checkpoint["task_bundle"]) != sha256_hex(task_bundle(task)):
        raise SharedEngineRejected("checkpoint_differs_from_original_registered_task")
    _verify_snapshot_against_history(checkpoint_path, checkpoint, task)
    history = journals_for_export(checkpoint_path, checkpoint, [])[:-1]
    pending_intent, pending = checkpoint.get("pending_intent"), checkpoint.get("pending_receipt")
    if pending_intent is not None:
        if pending_intent.get("kind") != "model_step":
            raise SharedEngineRejected("non_model_pending_recovery_not_supported")
        recovered = inspect_native_recovery(services,
            **({"attempt_ref": pending["runtime_attempt_ref"]} if pending is not None else {"intent": pending_intent}))
        if recovered.get("decision") != "recover_saved_receipt" or not recovered.get("saved_receipt"):
            raise SharedEngineRejected("native_safe_output_required_never_resend_unknown")
        native_saved = recovered["saved_receipt"]
        original_events = [event for _, journal in history for event in journal.events
            if event["event_type"] == "receipt_model"
            and event["data"]["attempt_ref"] == native_saved["runtime_attempt_ref"]]
        if original_events:
            # Native reconstruction intentionally has no private session and
            # may use native timestamps rather than bridge host observations.
            # Preserve the EXACT original journal receipt for strict physical
            # deduplication; native safe output and usage must still agree.
            from iqs_company_agent_lab.checkpoint import _receipt_from_event
            original = _receipt_from_event(original_events[-1]["data"])
            core = ("runtime_attempt_ref", "outcome", "planned_model", "actual_model",
                    "final_content", "tool_calls", "usage", "finish_reason")
            if any(original.get(key) != native_saved.get(key) for key in core):
                raise SharedEngineRejected("native_saved_output_conflicts_with_original_journal")
            if pending is not None and pending != original:
                raise SharedEngineRejected("checkpoint_receipt_conflicts_with_original_journal")
            pending = original
        else:
            pending = native_saved
    elif pending is not None:
        raise SharedEngineRejected("orphan_pending_receipt")
    # Observe historical native receipts from their original source. No session,
    # hidden reasoning, response regeneration or model HTTP is involved.
    for _, journal in history:
        for event in journal.events:
            if event["event_type"] == "receipt_model":
                services.inspect_attempt(event["data"]["attempt_ref"])
    if output.absolute() == session_dir.absolute() or output.absolute() in session_dir.absolute().parents or session_dir.absolute() in output.absolute().parents:
        raise SharedEngineRejected("session_and_export_must_be_disjoint")
    ensure_safe_output_dir(output)
    session_dir = _new_session(session_dir, task)
    _write_atomic(session_dir / "parent-checkpoint.json", {
        "checkpoint_sha256": sha256_hex(checkpoint_path.read_bytes()),
        "event_head_sha256": checkpoint["event_chain"]["head_sha256"]})
    chain = checkpoint["event_chain"]
    journal = _journal(session_dir, task.raw["run_id"], start_seq=chain["seq"], start_head=chain["head_sha256"])
    port = create_runtime_port(services, task=task, session_config=config)
    runner_ref = []
    runner = Runner.continue_from_checkpoint(task, _pending_port(port, runner_ref, session_dir, history,
        recover_intent=services.recover_intent), checkpoint, journal)
    runner_ref.append(runner)
    try:
        runner.run_continued(pending_intent, pending)
    except Exception as exc:
        raise SharedEngineInterrupted(session_dir) from exc
    return _export(task, services, runner, output=output, transport_origin=transport_origin,
        journals=history + [("events.jsonl", journal)], mode="native_owner_resume")


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
