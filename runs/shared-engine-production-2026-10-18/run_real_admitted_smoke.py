"""Controller experiment driver: original admitted services, no HTTP implementation.

Requires a genuine public confirmation and original five-file subject bundle.
It does not create identity, approval, budget policy, or release an old request.
The cold process deliberately exits only AFTER the native safe output commit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from contextlib import closing, contextmanager
import sqlite3
import time


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read(path):
    # Original task validators provide the final authority/shape checks.
    # Avoid duplicate JSON keys even in local orchestration configuration.
    from iqs_company_agent_lab.strictjson import loads
    return loads(Path(path).read_text(encoding="utf-8"))


def atomic_json(path, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    pending = path.with_suffix(path.suffix + ".pending")
    with pending.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--phase", choices=["cold", "recover"], required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    qa, company, bridge = [root.parent / name for name in
                          ("StockQAbyLLM", "iqs-company-agent-lab", "iqs-agent-runtime-lab")]
    sys.path[:0] = [str(qa), str(company / "src"), str(bridge / "src"), str(root / "scripts")]
    config = read(args.config)
    if config.get("protocol") != "iqs.real-admitted-smoke-config/1.0.0":
        raise ValueError("actual_native_smoke_config_required")
    # Final deployed source pins must be recorded by the controller AFTER both
    # reviewed engineering slices are delivered. Hashes are integrity, not grants.
    if not config.get("source_pins"):
        raise ValueError("reviewed_deployed_source_pins_required")
    for row in config["source_pins"]:
        if hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("deployed_source_changed")
    own = Path(config["run_root"]).resolve(strict=True)
    if args.config.resolve().parent != own:
        raise ValueError("controller_owned_config_root_required")
    if args.phase == "cold" and ((own / "crash-native-proof.json").exists()
                                  or (own / "cold-session").exists()):
        raise ValueError("inspect_existing_cold_state_never_automatically_resend")
    if args.phase == "recover":
        # Test isolation, not a replacement HTTP client or a model grant.
        # Keep the original SDK intact and fail before any new TCP connection.
        def deny_recovery_network(event, event_args):
            if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
                raise RuntimeError("cache_only_recovery_network_forbidden")
        sys.addaudithook(deny_recovery_network)
    from src.providers.llm_client import LLMClient
    from src.runners.llm_runner import QuickScanWorkLifecycle
    from src.utils.quick_scan_owner_research import OwnerResearchServices
    from src.utils.quick_scan_refresh_execution import prepare_execution

    owner = prepare_execution(config["deployment"], config["confirmation_id"],
        input_paths={name: Path(config["bundle"]) / name for name in
                     ("manifest.json", "identity.json", "authority.json", "owner-config.json", "questions.json")},
        process_env=dict(os.environ))
    policy = read(config["budget_policy_file"])
    routes = [row for row in policy["routes"] if row["id"] == config["route_id"]]
    if len(routes) != 1 or routes[0]["model"] != "mimo-v2.6-pro":
        raise ValueError("exact_original_mimo_route_required")
    route = routes[0]
    first = owner.requested_question_ids[0]
    subject = owner.native.observation_context["questions"][first]["subject_binding"]["subject_ref"]
    lifecycle = QuickScanWorkLifecycle(owner.service.store, entity_id=subject["entity_id"],
        run_id=config["run_id"], scan_id=config["run_id"] + "_SCAN",
        identity=owner.bundle["identity"], transport_managed=True,
        route_id=route["id"], provider_name=route["provider_config_ref"], model_requested=route["model"],
        budget_policy=policy, budget_route=route, owner_refresh_session=owner,
        observation_context=owner.native.observation_context, scope_by_question=owner.scope_bindings,
        generation_by_question={qid: owner.existing_work(qid)["generation"] for qid in owner.requested_question_ids})
    factory = load_module("actual_native_task", root / "scripts/shared_company_task.py")
    engine = load_module("actual_native_engine", root / "scripts/shared_company_engine.py")
    empty_task = factory.create_native_task(lifecycle, experiment_id=config["experiment_id"],
                                            run_id=config["run_id"], strategy_id="free_agent")
    adapter = load_module("actual_evidence_adapter", Path(__file__).parent /
                          "actual-evidence-projection/project_existing_sources.py")
    board_path, identity_path = Path(config["public_board"]), Path(config["public_identity"])
    board, provenance = adapter.project_existing_sources(empty_task,
        public_board_raw=board_path.read_bytes(), identity_raw=identity_path.read_bytes(),
        locked_refs=config["public_input_refs"])
    task = factory.create_native_task(lifecycle, experiment_id=config["experiment_id"],
        run_id=config["run_id"], strategy_id="free_agent", evidence_board=board)
    if task.company_ref != empty_task.company_ref:
        raise ValueError("native_company_reference_changed_during_input_projection")
    if args.phase == "cold":
        atomic_json(own / "evidence-projection-provenance.json", provenance)
    elif read(own / "evidence-projection-provenance.json") != provenance:
        raise ValueError("exact_original_evidence_projection_required_for_recovery")
    key = os.environ.get("MIMO_API_KEY")
    if args.phase == "cold" and not key:
        raise ValueError("mimo_credential_not_visible")
    # Recovery is deliberately keyless. Original native intent lookup must read
    # the prior safe receipt before any dispatch; no HTTP client is replaced.
    client = LLMClient(key if args.phase == "cold" else "RECOVERY-NO-GENERATION-CREDENTIAL",
        route["model"], "https://api.xiaomimimo.com/v1/chat/completions",
        provider_name="mimo", timeout=240)
    pricing_path = root / "runs/real-contrast-2026-10-16-03/inputs/frozen/pricing/s0_measurement.py"
    pricing_lock = read(root / "runs/real-contrast-2026-10-16-03/inputs.lock.json")
    pricing_rows = [x for x in pricing_lock["files"] if x["path"] == "frozen/pricing/s0_measurement.py"]
    if (len(pricing_rows) != 1 or hashlib.sha256(pricing_path.read_bytes()).hexdigest()
            != pricing_rows[0]["raw_sha256"]):
        raise ValueError("original_locked_rate_resolver_changed")
    price = load_module("actual_original_rate_resolver", pricing_path)
    start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    resolver = price.CohortPriceResolver(provider="mimo", model=route["model"],
        pricing_ref=policy["cost_policy"]["pricing_ref"], window_start=start, window_seconds=900)
    services = OwnerResearchServices(lifecycle, client, task=task, cost_resolver=resolver)
    if args.phase == "cold":
        original_scope = services.generation_scope

        @contextmanager
        def scope_with_diagnostic_time_budget(envelope):
            # Adds a refusal only; original owner/SDK still guards every POST.
            with original_scope(envelope):
                work_ids = [h["work_item_id"] for h in services._handles.values()]
                with closing(sqlite3.connect(services.store.path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                    db.execute("PRAGMA query_only=ON")
                    rows = db.execute("SELECT lease_expires_at FROM work_item WHERE work_item_id IN (" +
                        ",".join("?" for _ in work_ids) + ")", work_ids).fetchall()
                if not rows or any(r[0] is None for r in rows):
                    raise ValueError("native_active_lease_required")
                remaining = min(r[0] for r in rows) - time.time()
                atomic_json(own / "pre-send-lease-observation.json", dict(
                    original_lease_seconds=600, remaining_seconds=remaining,
                    model_network_timeout_seconds=240, minimum_remaining_required_seconds=360,
                    original_owner_and_sdk_guards_retained=True))
                if remaining < 360:
                    raise ValueError("insufficient_native_lease_time_stop_without_send")
                yield

        services.generation_scope = scope_with_diagnostic_time_budget
    runtime = dict(protocol="iqs.agent-runtime-lab.session-config/1.0.0", planned_model=route["model"],
        endpoint_profile_id=route["model"] + "@https://api.xiaomimimo.com/v1/chat/completions",
        max_output_tokens=16384, session_input_tokens=240000, session_output_tokens=48000,
        wall_seconds=900, logical_clock=False)
    if args.phase == "cold":
        original = services.observe_native_step

        def stop_after_original_safe_commit(step):
            native_ref = original(step)
            # The callback is downstream of original SDK/native transaction,
            # upstream of Runner receipt journaling. It records no answer text.
            atomic_json(own / "crash-native-proof.json", dict(
                protocol="iqs.real-native-safe-output-boundary/1.0.0", native_reference=native_ref,
                actual_wire="stockqa_live", intentional_exit_code=86,
                original_confirmation_id=config["confirmation_id"], task_sha256=task.task_sha256))
            os._exit(86)

        services.observe_native_step = stop_after_original_safe_commit
        engine.execute_shared_engine(task, services, runtime, own / "cold-unused-export",
            session_dir=own / "cold-session", transport_origin="stockqa_live")
        raise ValueError("expected_original_safe_output_boundary_not_reached")
    result = engine.resume_shared_engine(task, services, runtime, own / "cold-session/checkpoint.json",
        own / "recovered-export", session_dir=own / "recovered-session", transport_origin="stockqa_live")
    from iqs_company_agent_lab.reporter import generate_report
    report = generate_report(own / "recovered-export", own / "recovered-report")
    summary = result["runtime_summary"]
    if summary["new_model_http"] != 0 or summary["replayed_native_attempts"] != 1:
        raise ValueError("cache_recovery_must_reuse_exactly_one_original_attempt")
    atomic_json(own / "recovery-observation.json", dict(
        protocol="iqs.real-native-recovery-observation/1.0.0", all_slots_completed=result["all_slots_completed"],
        slot_count=len(result["run"]["slots"]), runtime_summary=summary,
        report_matches_summary=report["runtime_observations"] == summary,
        financial_accuracy_assessed=False, formal_search_checkpoint_created=False))
    print(json.dumps(dict(phase="recovered", slots=len(result["run"]["slots"]),
                         completed=result["all_slots_completed"], new_model_http=summary["new_model_http"])))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # No raw provider body, exception instance, environment or reasoning.
        import traceback
        frames = [{"file": row.filename, "line": row.lineno, "function": row.name}
                  for row in traceback.extract_tb(error.__traceback__)]
        print(json.dumps({"status": "stopped_no_automatic_resend", "error_type": type(error).__name__,
                          "stack_locations_only": frames}))
        raise SystemExit(2) from None
