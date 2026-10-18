"""Two-question production-profile experiment using ORIGINAL admitted services.

The native owner and SDK retain every authority, intent, lease and cost guard.
This controller creates no permission or identity and never settles old charges.
The historical failed Task3 driver stays byte-for-byte unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller_delivery as delivery


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def configuration(raw, *, config_path):
    """Refusal-only local checks; configuration hashes are never owner grants."""
    if not isinstance(raw, dict) or raw.get("protocol") != "iqs.real-profile-smoke-config/1.0.0":
        raise ValueError("explicit_real_profile_config_required")
    qids = raw.get("question_ids")
    if (not isinstance(qids, list) or len(qids) != 2
            or any(not isinstance(q, str) or not q for q in qids) or len(set(qids)) != 2):
        raise ValueError("exact_two_original_questions_required")
    if raw.get("owner_batch_claim") is not True or raw.get("pack_by") != "module":
        raise ValueError("explicit_original_batch_and_module_pack_required")
    if raw.get("max_questions_per_pack") != 2 or type(raw.get("max_questions_per_pack")) is not int:
        raise ValueError("exact_two_question_pack_cap_required")
    if raw.get("route_id") != "mimo-pro-t2":
        raise ValueError("original_qualified_mimo_route_required")
    if (raw.get("thinking_enabled") is not True
            or type(raw.get("max_output_tokens")) is not int or raw["max_output_tokens"] != 16384):
        raise ValueError("thinking_and_explicit_output_cap_required")
    limits = raw.get("limits")
    if (not isinstance(limits, dict)
            or type(limits.get("max_model_requests_per_session")) is not int
            or limits["max_model_requests_per_session"] != 1
            or type(limits.get("max_search_queries_per_session")) is not int
            or limits["max_search_queries_per_session"] != 0):
        raise ValueError("one_original_model_request_zero_new_search_required")
    profile = raw.get("execution_profile")
    if (not isinstance(profile, dict) or profile.get("question_ids") != qids
            or profile.get("packs") != [qids] or profile.get("resource_limits") != limits
            or profile.get("information_cutoff") != raw.get("information_cutoff")):
        raise ValueError("exact_precomputed_original_profile_required")
    own = Path(raw["run_root"]).resolve(strict=True)
    if Path(config_path).resolve(strict=True).parent != own:
        raise ValueError("controller_owned_config_root_required")
    if not isinstance(raw.get("deployment_proof"), dict):
        raise ValueError("reviewed_deployed_source_proof_required")
    delivered = delivery.verify_deployment(raw["deployment_proof"])
    if "source_pins" in raw and raw["source_pins"] != delivered["files"]:
        raise ValueError("self_selected_runtime_inventory_forbidden")
    delivery.verify_public_inputs(raw, own, delivered)
    return own



def recovery_output_root(own, label):
    """Choose fresh analysis output without changing original task/checkpoint."""
    if label is None:
        if any((own / name).exists() for name in (
                "recovered-session", "recovered-export", "recovered-report", "recovery-observation.json")):
            raise ValueError("existing_recovery_outputs_require_fresh_label")
        return own
    result = own / ("recovery-" + label)
    if result.resolve().parent != own or result.exists():
        raise ValueError("fresh_recovery_output_directory_required")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--phase", choices=("cold", "recover"), required=True)
    parser.add_argument("--recovery-label", default=None,
        help="Fresh ASCII alphanumeric output label for cache-only recovery")
    args = parser.parse_args()
    if args.recovery_label is not None and (args.phase != "recover"
            or not args.recovery_label.isascii() or not args.recovery_label.isalnum()
            or len(args.recovery_label) > 32):
        raise ValueError("explicit_safe_cache_recovery_label_required")
    qa, company, bridge = [ROOT.parent / name for name in (
        "StockQAbyLLM", "iqs-company-agent-lab", "iqs-agent-runtime-lab")]
    sys.path[:0] = [str(qa), str(company / "src"), str(bridge / "src"), str(ROOT / "scripts")]
    config = delivery.read(args.config)
    own = configuration(config, config_path=args.config)
    historical = module("historical_smoke_helpers", BASE / "run_real_admitted_smoke.py")
    read, atomic_json = historical.read, historical.atomic_json
    if args.phase == "cold" and any((own / name).exists() for name in (
            "crash-native-proof.json", "cold-session", "cold-started.json")):
        raise ValueError("inspect_existing_cold_state_never_automatically_resend")
    if args.phase == "recover":
        if any(name.upper().endswith("API_KEY") for name in os.environ):
            raise ValueError("fresh_recovery_process_must_be_keyless")
        def offline(event, event_args):
            if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
                raise RuntimeError("cache_only_recovery_network_forbidden")
        sys.addaudithook(offline)
        if not (own / "crash-native-proof.json").is_file():
            raise ValueError("original_safe_output_boundary_required_before_recovery")
    from src.providers.llm_client import LLMClient
    from src.runners.llm_runner import QuickScanWorkLifecycle
    from src.utils.quick_scan_owner_research import OwnerResearchServices
    from src.utils.quick_scan_refresh_execution import prepare_execution
    from iqs_company_agent_lab.canonical import sha256_hex

    owner = prepare_execution(config["deployment"], config["confirmation_id"],
        input_paths={name: Path(config["bundle"]) / name for name in (
            "manifest.json", "identity.json", "authority.json", "owner-config.json", "questions.json")},
        process_env=dict(os.environ))
    if list(owner.requested_question_ids) != config["question_ids"]:
        raise ValueError("exact_original_approved_question_order_required")
    policy = read(config["budget_policy_file"])
    routes = [row for row in policy["routes"] if row["id"] == config["route_id"]]
    if (len(routes) != 1 or routes[0]["model"] != "mimo-v2.6-pro"
            or routes[0]["provider_config_ref"] != "mimo"):
        raise ValueError("exact_original_mimo_route_required")
    route = routes[0]
    first = owner.requested_question_ids[0]
    subject = owner.native.observation_context["questions"][first]["subject_binding"]["subject_ref"]
    if subject != config["native_subject_ref"]:
        raise ValueError("exact_original_native_subject_required")
    delivery.verify_public_inputs(config, own,
        delivery.verify_deployment(config["deployment_proof"]), subject=subject)
    lifecycle = QuickScanWorkLifecycle(owner.service.store, entity_id=subject["entity_id"],
        run_id=config["run_id"], scan_id=config["run_id"] + "_SCAN", identity=owner.bundle["identity"],
        transport_managed=True, route_id=route["id"], provider_name=route["provider_config_ref"],
        model_requested=route["model"], budget_policy=policy, budget_route=route,
        owner_refresh_session=owner, observation_context=owner.native.observation_context,
        scope_by_question=owner.scope_bindings,
        generation_by_question={q: owner.existing_work(q)["generation"] for q in config["question_ids"]})
    factory = module("real_profile_task", ROOT / "scripts/shared_company_task.py")
    engine = module("real_profile_engine", ROOT / "scripts/shared_company_engine.py")
    factory_args = dict(experiment_id=config["experiment_id"], run_id=config["run_id"],
        question_ids=config["question_ids"], limits=config["limits"], pack_by="module",
        max_questions_per_pack=2)
    empty_task = factory.create_company_scan_task(lifecycle, **factory_args)
    if (empty_task.raw["execution_profile"] != config["execution_profile"]
            or empty_task.raw["execution_profile_sha256"] != sha256_hex(config["execution_profile"])):
        raise ValueError("actual_original_profile_differs_from_preapproved_profile")
    adapter = module("real_profile_public_evidence", BASE / "actual-evidence-projection/project_existing_sources.py")
    board, provenance = adapter.project_existing_sources(empty_task,
        public_board_raw=Path(config["public_board"]).read_bytes(),
        identity_raw=Path(config["public_identity"]).read_bytes(), locked_refs=config["public_input_refs"])
    task = factory.create_company_scan_task(lifecycle, evidence_board=board, **factory_args)
    if (task.company_ref != empty_task.company_ref
            or task.raw["execution_profile"] != config["execution_profile"]):
        raise ValueError("original_subject_or_profile_changed_during_context_projection")
    if args.phase == "cold":
        atomic_json(own / "evidence-projection-provenance.json", provenance)
    elif read(own / "evidence-projection-provenance.json") != provenance:
        raise ValueError("exact_original_context_required_for_cache_recovery")
    key = os.environ.get("MIMO_API_KEY")
    if args.phase == "cold" and not key:
        raise ValueError("mimo_credential_not_visible")
    client = LLMClient(key if args.phase == "cold" else "RECOVERY-NO-GENERATION-CREDENTIAL",
        route["model"], "https://api.xiaomimimo.com/v1/chat/completions", provider_name="mimo", timeout=240)
    pricing_path = ROOT / "runs/real-contrast-2026-10-16-03/inputs/frozen/pricing/s0_measurement.py"
    lock = read(ROOT / "runs/real-contrast-2026-10-16-03/inputs.lock.json")
    price_refs = [row for row in lock["files"] if row["path"] == "frozen/pricing/s0_measurement.py"]
    if len(price_refs) != 1 or hashlib.sha256(pricing_path.read_bytes()).hexdigest() != price_refs[0]["raw_sha256"]:
        raise ValueError("original_locked_rate_resolver_changed")
    price = module("real_profile_original_price", pricing_path)
    resolver = price.CohortPriceResolver(provider="mimo", model=route["model"],
        pricing_ref=policy["cost_policy"]["pricing_ref"],
        window_start=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), window_seconds=900)
    services = OwnerResearchServices(lifecycle, client, task=task, cost_resolver=resolver,
        owner_batch_claim=True)
    runtime = dict(protocol="iqs.agent-runtime-lab.session-config/1.0.0", planned_model=route["model"],
        endpoint_profile_id=route["model"] + "@https://api.xiaomimimo.com/v1/chat/completions",
        max_output_tokens=16384, session_input_tokens=240000, session_output_tokens=48000,
        wall_seconds=900, logical_clock=False)
    if args.phase == "cold":
        original_scope = services.generation_scope
        @contextmanager
        def refuse_short_scope(envelope):
            with original_scope(envelope):
                ids = [handle["work_item_id"] for handle in services._handles.values()]
                with closing(sqlite3.connect(services.store.path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                    db.execute("PRAGMA query_only=ON")
                    rows = db.execute("SELECT lease_expires_at FROM work_item WHERE work_item_id IN ("
                                      + ",".join("?" for _ in ids) + ")", ids).fetchall()
                if len(rows) != 2 or any(row[0] is None for row in rows):
                    raise ValueError("two_original_active_leases_required")
                remaining = min(row[0] for row in rows) - time.time()
                atomic_json(own / "scope-lease-diagnostic.json", dict(original_lease_seconds=600,
                    remaining_seconds=remaining, network_timeout_seconds=240,
                    minimum_scope_remaining_seconds=360, actual_wire_headroom_proven=False))
                if remaining < 360:
                    raise ValueError("insufficient_scope_time_stop_without_send")
                yield
        services.generation_scope = refuse_short_scope
        observe = services.observe_native_step
        def stop_at_safe_commit(step):
            native_ref = observe(step)
            atomic_json(own / "crash-native-proof.json", dict(protocol="iqs.real-native-safe-output-boundary/1.0.0",
                native_reference=native_ref, actual_wire="stockqa_live", intentional_exit_code=86,
                original_confirmation_id=config["confirmation_id"], task_sha256=task.task_sha256,
                execution_profile_sha256=task.raw["execution_profile_sha256"]))
            os._exit(86)
        services.observe_native_step = stop_at_safe_commit
        atomic_json(own / "cold-started.json", dict(observed_at=datetime.now(timezone.utc).isoformat(),
                    task_sha256=task.task_sha256, financial_accuracy_assessed=False))
        engine.execute_shared_engine(task, services, runtime, own / "cold-unused-export",
            session_dir=own / "cold-session", transport_origin="stockqa_live")
        raise ValueError("expected_original_safe_output_boundary_not_reached")
    recovery_root = recovery_output_root(own, args.recovery_label)
    if recovery_root != own:
        recovery_root.mkdir()
    result = engine.resume_shared_engine(task, services, runtime, own / "cold-session/checkpoint.json",
        recovery_root / "recovered-export", session_dir=recovery_root / "recovered-session", transport_origin="stockqa_live")
    from iqs_company_agent_lab.reporter import generate_report
    report = generate_report(recovery_root / "recovered-export", recovery_root / "recovered-report")
    summary = result["runtime_summary"]
    if summary["new_model_http"] != 0 or summary["replayed_native_attempts"] != 1:
        raise ValueError("cache_recovery_must_reuse_one_exact_original_pack")
    atomic_json(recovery_root / "recovery-observation.json", dict(protocol="iqs.real-native-recovery-observation/1.0.0",
        all_slots_completed=result["all_slots_completed"], slot_count=len(result["run"]["slots"]),
        runtime_summary=summary, report_matches_summary=report["runtime_observations"] == summary,
        financial_accuracy_assessed=False, formal_search_checkpoint_created=False))
    print(json.dumps(dict(phase="recovered", slots=len(result["run"]["slots"]),
                         completed=result["all_slots_completed"], new_model_http=0)))
    if not result["all_slots_completed"]:
        raise SystemExit(4)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import traceback
        frames = [{"file": row.filename, "line": row.lineno, "function": row.name}
                  for row in traceback.extract_tb(error.__traceback__)]
        print(json.dumps(dict(status="stopped_no_automatic_resend", error_type=type(error).__name__,
                              stack_locations_only=frames)))
        raise SystemExit(2) from None
