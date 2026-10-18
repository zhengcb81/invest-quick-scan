"""Bind an owner-approved search exposure document to an owner policy cell.

Offline only. The cell's control.search_policy_sha256 must equal the canonical
hash of the exposure document, and the exposure must pass the offline exposure
contract (policy file hash, enabled routes, credential presence, storage rights).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import search_exposure_contract as exposure_contract

PROTOCOL = "iqs.search_exposure.binding/1.0.0"


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def bind(policy, exposure, *, base_dir=None, environ=None):
    checked = exposure_contract.validate(exposure, base_dir=base_dir, environ=environ)
    if checked["status"] != "valid":
        return dict(protocol=PROTOCOL, status="rejected", errors=checked["errors"])
    document_sha256 = canonical_sha256(exposure)
    control = (
        policy.get("budget_exposure_acceptance", {}).get("control")
        if isinstance(policy, dict)
        else None
    )
    cells = control.get("cells") if isinstance(control, dict) else None
    errors = []
    matched = []
    if not isinstance(cells, list) or not cells:
        errors.append("owner_policy_cells_missing")
    else:
        for cell in cells:
            controls = cell.get("controls") if isinstance(cell, dict) else None
            if isinstance(controls, dict) and controls.get("search_policy_sha256") == document_sha256:
                matched.append(cell.get("cell_id"))
        if not matched:
            errors.append("cell_search_exposure_binding_missing")
    allowed = policy.get("allowed_consumer_ids") if isinstance(policy, dict) else None
    if not isinstance(allowed, list) or exposure["consumer_id"] not in allowed:
        errors.append("consumer_not_allowed_by_owner_policy")
    routes = policy.get("external_routes") if isinstance(policy, dict) else None
    admitted = [
        route
        for route in (routes or [])
        if isinstance(route, dict)
        and route.get("enabled") is True
        and route.get("cost_bound_verified") is True
    ]
    if not admitted:
        errors.append("owner_policy_search_route_not_admitted")
    exposure_routes = {route["route_id"] for route in exposure.get("routes", [])}
    policy_routes = {route.get("route_id") for route in (routes or []) if isinstance(route, dict)}
    if exposure_routes - policy_routes:
        errors.append("exposure_route_not_in_owner_policy")
    return dict(
        protocol=PROTOCOL,
        status="bound" if not errors else "rejected",
        exposure_sha256=document_sha256,
        policy_id=policy.get("policy_id") if isinstance(policy, dict) else None,
        matched_cells=matched,
        enabled_routes=checked["enabled_routes"],
        errors=errors,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--exposure", required=True, type=Path)
    parser.add_argument("--base-dir", type=Path)
    args = parser.parse_args(argv)
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    exposure = json.loads(args.exposure.read_text(encoding="utf-8"))
    result = bind(policy, exposure, base_dir=args.base_dir or args.exposure.parent)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "bound" else 2


if __name__ == "__main__":
    raise SystemExit(main())
