"""Pure offline reference policy for the C07 deployment/lifecycle contract.

No filesystem, process, database, network, provider, or credential access is used.
StockWiki/StockQA must implement these rules at their public owner APIs.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

import exchange_contract as exchange
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_SCHEMA = json.loads(
    (ROOT / "schemas/quick_scan/deployment.schema.json").read_text(encoding="utf-8")
)
DEPLOYMENT_VALIDATOR = Draft202012Validator(
    DEPLOYMENT_SCHEMA, format_checker=FormatChecker()
)

REQUIRED_COMPONENTS = ("iqs", "stockqa", "stockwiki", "theme", "industry")
OPTIONAL_COMPONENTS = ("company_wiki",)
REQUIRED_GATES = tuple(f"G{i}" for i in range(7))
REQUIRED_CONSUMERS = ("theme", "industry")
_READ_ONLY_OPERATIONS = {"doctor", "plan", "status"}


def build_release_set(*, release_set_id: str, created_at: str,
                      components: list[dict], rollback_set_id: str | None = None) -> dict:
    """Return a detached, content-hashed release set manifest."""
    body = {
        "schema_version": "1.0.0",
        "release_set_id": release_set_id,
        "created_at": created_at,
        "components": deepcopy(components),
        "required_gates": list(REQUIRED_GATES),
        "required_consumers": list(REQUIRED_CONSUMERS),
        "optional_components": list(OPTIONAL_COMPONENTS),
        "rollback_set_id": rollback_set_id,
    }
    body["manifest_sha256"] = exchange.canonical_sha256(body)
    return body


def validate_release_set(release_set: dict) -> tuple[bool, str | None]:
    """Check manifest identity, owner set and its content hash."""
    if not isinstance(release_set, dict):
        return False, "invalid_manifest"
    try:
        DEPLOYMENT_VALIDATOR.validate(release_set)
    except ValidationError:
        return False, "invalid_manifest"
    digest = release_set.get("manifest_sha256")
    body = {key: value for key, value in release_set.items() if key != "manifest_sha256"}
    try:
        actual = exchange.canonical_sha256(body)
    except (TypeError, ValueError):
        return False, "invalid_manifest"
    if digest != actual:
        return False, "manifest_hash_mismatch"
    components = release_set.get("components")
    if not isinstance(components, list):
        return False, "invalid_manifest"
    ids = [item.get("component_id") for item in components if isinstance(item, dict)]
    if len(ids) != len(components) or len(set(ids)) != len(ids):
        return False, "duplicate_or_invalid_component"
    if set(REQUIRED_COMPONENTS) - set(ids):
        return False, "missing_required_component"
    if set(ids) - set(REQUIRED_COMPONENTS) - set(OPTIONAL_COMPONENTS):
        return False, "unsupported_component"
    by_id = {item["component_id"]: item for item in components}
    if any(by_id[name].get("required") is not True for name in REQUIRED_COMPONENTS):
        return False, "required_component_marked_optional"
    if "company_wiki" in by_id and by_id["company_wiki"].get("required") is not False:
        return False, "optional_identity_source_marked_required"
    gates = release_set.get("required_gates", [])
    if not isinstance(gates, list) or len(gates) != len(REQUIRED_GATES) or set(gates) != set(REQUIRED_GATES):
        return False, "incomplete_gate_set"
    consumers = release_set.get("required_consumers", [])
    if (not isinstance(consumers, list) or len(consumers) != len(REQUIRED_CONSUMERS)
            or set(consumers) != set(REQUIRED_CONSUMERS)):
        return False, "incomplete_consumer_set"
    return True, None


def validate_readiness_response(response: dict, *, release_set: dict) -> None:
    """Validate a response and bind all readiness evidence to one release."""
    DEPLOYMENT_VALIDATOR.validate(response)
    valid, error = validate_release_set(release_set)
    if not valid:
        raise ValueError(f"invalid expected release set: {error}")
    result = response.get("result", {})
    evidence = result.get("readiness_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("readiness response requires evidence")
    release_id = release_set["release_set_id"]
    manifest_hash = release_set["manifest_sha256"]
    if (evidence.get("release_set_id") != release_id
            or evidence.get("manifest_sha256") != manifest_hash):
        raise ValueError("readiness evidence does not match expected release")
    if result.get("readiness") != evidence.get("level"):
        raise ValueError("reported readiness differs from evidence level")
    if evidence.get("level") != "full_release_verified":
        return
    gates = evidence.get("gate_evidence", [])
    by_gate = {item.get("gate_id"): item for item in gates if isinstance(item, dict)}
    if (len(gates) != len(REQUIRED_GATES) or len(by_gate) != len(gates)
            or set(by_gate) != set(REQUIRED_GATES)):
        raise ValueError("full readiness requires G0 through G6 exactly once")
    if any(item.get("release_set_id") != release_id
           or item.get("manifest_sha256") != manifest_hash for item in gates):
        raise ValueError("gate evidence belongs to another release")
    if set(evidence.get("loaded_consumers", [])) != set(REQUIRED_CONSUMERS):
        raise ValueError("full readiness requires both consumers exactly once")
    if evidence.get("all_required_component_hashes_match") is not True:
        raise ValueError("full readiness requires matching required component hashes")
    search_receipt = evidence.get("live_search_receipt_id")
    paid_receipt = evidence.get("paid_usage_receipt_id")
    derived = assess_readiness(
        release_set=release_set,
        component_statuses=result.get("components", []),
        install_record_present=True,
        setup_complete=evidence.get("setup_complete") is True,
        doctor_passed=evidence.get("doctor_passed") is True,
        live_probe={
            "release_set_id": release_id,
            "manifest_sha256": manifest_hash,
            "actual_search_executed": isinstance(search_receipt, str) and bool(search_receipt),
            "paid_usage_recorded": isinstance(paid_receipt, str) and bool(paid_receipt),
            "receipt_id": f"{search_receipt}:{paid_receipt}",
        },
        gate_evidence=gates,
    )
    if derived.get("readiness") != "full_release_verified":
        raise ValueError("full readiness is not supported by component and release evidence")


def assess_readiness(*, release_set: dict, component_statuses: list[dict],
                     install_record_present: bool, setup_complete: bool,
                     doctor_passed: bool, live_probe: dict | None = None,
                     gate_evidence: list[dict] | None = None) -> dict:
    """Derive the strongest readiness level supported by matching evidence."""
    valid, error = validate_release_set(release_set)
    if not valid:
        return {"readiness": "not_ready", "status": "version_mismatch", "error_code": error}
    if not install_record_present:
        return {"readiness": "not_ready", "status": "setup_required", "error_code": "missing_install_record"}
    expected = {c["component_id"]: c for c in release_set["components"]}
    actual_items = [c for c in component_statuses if isinstance(c, dict)]
    actual_ids = [c.get("component_id") for c in actual_items]
    if len(actual_ids) != len(actual_items) or len(set(actual_ids)) != len(actual_ids):
        return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "duplicate_component_status"}
    if set(actual_ids) - set(expected):
        return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "unsupported_component_status"}
    actual = {c["component_id"]: c for c in actual_items}
    missing = set(REQUIRED_COMPONENTS) - set(actual)
    if missing:
        return {"readiness": "not_ready", "status": "setup_required", "error_code": "missing_component"}
    for component_id in REQUIRED_COMPONENTS:
        spec, report = expected[component_id], actual[component_id]
        if report.get("status") == "missing":
            return {"readiness": "not_ready", "status": "setup_required", "error_code": "missing_component"}
        if report.get("status") == "failed":
            return {"readiness": "not_ready", "status": "failed_component", "error_code": "component_failed"}
        if (report.get("status") == "incompatible"
                or report.get("expected_version") != spec.get("version")
                or report.get("actual_version") != spec.get("version")
                or report.get("expected_artifact_sha256") != spec.get("artifact_sha256")
                or report.get("actual_loaded_sha256") != spec.get("artifact_sha256")):
            return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "loaded_hash_or_version_mismatch"}
        if report.get("contract_versions") != spec.get("contract_versions"):
            return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "contract_version_mismatch"}
        if not set(spec.get("capabilities", [])) <= set(report.get("capabilities", [])):
            return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "capability_missing"}
        interpreter = spec.get("interpreter", {})
        if (interpreter.get("executable_sha256") is not None
                and report.get("executable_sha256") != interpreter.get("executable_sha256")):
            return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "interpreter_hash_mismatch"}
        if (interpreter.get("python_version") is not None
                and report.get("python_version") != interpreter.get("python_version")):
            return {"readiness": "not_ready", "status": "version_mismatch", "error_code": "interpreter_version_mismatch"}
    if not setup_complete:
        return {"readiness": "installed", "status": "setup_required", "error_code": "profile_incomplete"}
    if not doctor_passed:
        return {"readiness": "installed", "status": "failed_component", "error_code": "doctor_failed"}
    level = "offline_ready"
    status = "ready"
    probe = live_probe or {}
    live_valid = (
        probe.get("release_set_id") == release_set.get("release_set_id")
        and probe.get("manifest_sha256") == release_set.get("manifest_sha256")
        and probe.get("actual_search_executed") is True
        and probe.get("paid_usage_recorded") is True
        and isinstance(probe.get("receipt_id"), str) and bool(probe.get("receipt_id"))
    )
    if live_valid:
        level, status = "live_verified", "ready"
        gates = gate_evidence or []
        by_gate = {g.get("gate_id"): g for g in gates if isinstance(g, dict)}
        gates_valid = (
            len(gates) == len(REQUIRED_GATES)
            and len(by_gate) == len(gates)
            and set(by_gate) == set(REQUIRED_GATES)
            and all(by_gate[g].get("status") == "passed"
                    and by_gate[g].get("release_set_id") == release_set["release_set_id"]
                    and by_gate[g].get("manifest_sha256") == release_set["manifest_sha256"]
                    and isinstance(by_gate[g].get("receipt_sha256"), str)
                    and re.fullmatch(r"[a-f0-9]{64}", by_gate[g]["receipt_sha256"]) is not None
                    for g in REQUIRED_GATES)
        )
        consumers_valid = all(
            actual.get(name, {}).get("actual_loaded_sha256") == expected[name]["artifact_sha256"]
            for name in REQUIRED_CONSUMERS
        )
        if gates_valid and consumers_valid:
            level, status = "full_release_verified", "ready"
    return {"readiness": level, "status": status, "error_code": None}


def command_decision(operation: str, context: dict[str, Any]) -> dict:
    """Decide what a public lifecycle command may request; execute nothing."""
    base = {"operation": operation, "action": "none", "status": "blocked",
            "dispatch_started": False, "paid_calls_started": False,
            "network_calls_started": False, "process_spawned": False,
            "generic_research_scheduler_started": False, "source_pipeline_started": False,
            "unowned_process_terminated": False}
    if operation == "doctor":
        return {**base, "status": "accepted", "action": "read_only_preflight"}
    if operation == "plan":
        return {**base, "status": "accepted", "action": "preview_only"}
    if operation == "status":
        return {**base, "status": "accepted", "action": "read_status"}
    if operation == "setup":
        return {**base, "status": "accepted", "action": "delegate_owner_configuration",
                "configuration_owners": ["stockwiki", "stockqa"], "secret_values_transmitted": False}
    if operation == "verify_live":
        budget_cap = context.get("budget_cap")
        approved = bool(
            context.get("external_action") == "execute_one_live_search_probe"
            and _is_bounded_live_probe_budget(budget_cap)
            and isinstance(context.get("expected_release_set_id"), str)
            and bool(context.get("expected_release_set_id"))
            and context.get("active_release_set_id") == context.get("expected_release_set_id")
            and isinstance(context.get("policy_revision"), str)
            and bool(context.get("policy_revision"))
            and context.get("active_policy_revision") == context.get("policy_revision")
            and context.get("budget_status") == "available"
        )
        return {**base, "status": "accepted" if approved else "blocked",
                "action": "authorize_bounded_search_probe" if approved else "require_explicit_action_and_budget_cap",
                "dispatch_authorized": approved,
                "authorized_external_action": context.get("external_action") if approved else None,
                "dispatch_budget_cap": dict(budget_cap) if approved else None}
    if operation == "stop":
        target = context.get("run")
        if not (isinstance(target, dict) and target.get("run_id")
                and target.get("workspace_id") == context.get("workspace_id")
                and target.get("profile_id") == context.get("profile_id")):
            return {**base, "status": "blocked", "action": "refuse_unowned_run_control",
                    "error_code": "unowned_process"}
        return {**base, "status": "stopped", "action": "stop_new_dispatch_and_drain",
                "run_id": target["run_id"], "preserve_inflight_and_outbox": True}
    if operation not in {"start", "resume"}:
        return {**base, "status": "blocked", "action": "unsupported_operation"}
    if context.get("readiness") not in {"offline_ready", "live_verified", "full_release_verified"}:
        return {**base, "status": context.get("preflight_status", "setup_required"),
                "action": "block_until_preflight_passes"}
    active = context.get("active_run")
    workspace, profile = context.get("workspace_id"), context.get("profile_id")
    if not (isinstance(workspace, str) and workspace and isinstance(profile, str) and profile):
        return {**base, "status": "blocked", "action": "require_workspace_and_profile_identity"}
    if (isinstance(active, dict) and active.get("run_id")
            and active.get("workspace_id") == workspace and active.get("profile_id") == profile):
        return {**base, "status": "attached", "action": "attach_existing_run",
                "run_id": active.get("run_id"), "attached_to_existing": True,
                "create_run": False, "reset_budget": False}
    resumable = context.get("resumable_run")
    if (isinstance(resumable, dict) and resumable.get("run_id")
            and resumable.get("workspace_id") == workspace and resumable.get("profile_id") == profile):
        if context.get("budget_status") == "exhausted":
            return {**base, "status": "budget_exhausted", "action": "preserve_run_until_budget_change",
                    "run_id": resumable.get("run_id"), "reset_budget": False}
        return {**base, "status": "accepted", "action": "resume_existing_run",
                "run_id": resumable.get("run_id"), "create_run": False, "reset_budget": False}
    if operation == "resume":
        return {**base, "status": "no_resumable_run", "action": "do_not_create_new_run"}
    if context.get("budget_status") == "exhausted":
        return {**base, "status": "budget_exhausted", "action": "do_not_reset_or_create_run",
                "create_run": False, "reset_budget": False}
    if context.get("plan_has_work") is False:
        return {**base, "status": "no_work", "action": "do_not_spawn_or_dispatch",
                "create_run": False}
    if context.get("plan_has_work") is not True:
        return {**base, "status": "blocked", "action": "require_current_plan_result",
                "create_run": False}
    if context.get("budget_status") != "available":
        return {**base, "status": "blocked", "action": "require_stockqa_budget_status",
                "create_run": False}
    return {**base, "status": "accepted", "action": "create_or_attach_idempotent_run",
            "create_run": True, "reset_budget": False}


def _is_bounded_live_probe_budget(value: object) -> bool:
    """Accept only the fixed one-request probe envelope and bounded token caps."""
    if not isinstance(value, dict) or set(value) != {
        "max_model_requests", "max_search_requests", "max_input_tokens", "max_output_tokens"
    }:
        return False
    if value["max_model_requests"] != 1 or isinstance(value["max_model_requests"], bool):
        return False
    if value["max_search_requests"] != 1 or isinstance(value["max_search_requests"], bool):
        return False
    for field, maximum in (("max_input_tokens", 4096), ("max_output_tokens", 1024)):
        amount = value[field]
        if isinstance(amount, bool) or not isinstance(amount, int) or not 1 <= amount <= maximum:
            return False
    return True


def process_identity_matches(recorded: dict, observed: dict) -> bool:
    """A PID/port alone is insufficient; compare workspace and instance proof."""
    keys = ("workspace_id", "profile_id", "component_id", "process_instance_id",
            "pid", "process_started_at", "executable_sha256", "working_directory")
    if not (all(key in recorded and key in observed for key in keys)
            and all(recorded[key] == observed[key] for key in keys)):
        return False
    return (type(observed["pid"]) is int and observed["pid"] > 0
            and isinstance(observed["process_instance_id"], str)
            and len(observed["process_instance_id"]) >= 16)
