"""Link external retrieval to existing Q09 accounting without model rerouting.

The returned composite is a budget projection ONLY. Answer-model dispatch must
retain its original model policy and priority. No scheduler or ledger lives here.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any

from src.config.quick_scan_search_policy import SearchPolicy, execution_query_plans
from src.utils.quick_scan_external_journal import MODEL_BUDGET_LABEL
from src.utils.quick_scan_work_store import _budget_policy_projection


def build_shared_external_budget_policy(model_policy: dict[str, Any], search_policy: SearchPolicy) -> dict[str, Any]:
    """Add admitted retrieval route identities to one unchanged spending owner."""
    original = _budget_policy_projection(model_policy)
    execution_query_plans(search_policy)  # Requires the loader's unchanged 1.1 plan.
    if not search_policy.admitted or not search_policy.requires_external:
        raise ValueError("no executable admitted external route")
    shared = copy.deepcopy(model_policy)
    route_ids = {route["id"] for route in shared["routes"]}
    groups = {group["id"]: group for group in shared["quota_groups"]}
    for route_id in search_policy.admitted:
        route = next(item for item in search_policy.routes if item["route_id"] == route_id)
        pricing, dispatch = route["pricing"], route["dispatch"]
        if route_id in route_ids:
            raise ValueError("external and answer-model route identities overlap")
        if pricing["currency"] != original["currency"]:
            raise ValueError("search and answer-model budget currencies differ")
        if pricing["per_request_cap_micros"] > min(original["max_cost_per_attempt_micros"], original["max_cost_micros"]):
            raise ValueError("external request bound exceeds the existing budget cap")
        group_id = dispatch["quota_group"]
        group_limit = dispatch["quota_group_max_in_flight"]
        if group_id in groups:
            if groups[group_id]["max_in_flight"] != group_limit:
                raise ValueError("external quota-group concurrency conflicts with the model policy")
        else:
            group = {"id": group_id, "max_in_flight": group_limit}
            groups[group_id] = group
            shared["quota_groups"].append(group)
        shared["routes"].append({
            "id": route_id, "provider_config_ref": route["kind"],
            "model": MODEL_BUDGET_LABEL, "quota_group": group_id,
            "max_in_flight": dispatch["max_in_flight"], "eligible": True,
            "unavailable_reason": None,
        })
        route_ids.add(route_id)
    # A policy-version change never creates a new policy_id or resets counters.
    basis = (original["policy_snapshot_sha256"] + ":" + search_policy.policy_sha256).encode("ascii")
    shared["policy_version"] = "external_budget/1.0.0:" + hashlib.sha256(basis).hexdigest()
    _budget_policy_projection(shared)  # Validate through the original Q09 owner.
    return shared
