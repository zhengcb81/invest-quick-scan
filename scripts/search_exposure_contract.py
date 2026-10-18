"""Validate an owner-approved bounded search exposure document.

Offline only: never calls a search provider and never reads credential values.
Presence of the named environment variables is recorded, not their content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/quick_scan/search-exposure-v1.schema.json").read_bytes())


def validate(document, *, base_dir=None, environ=None):
    environ = os.environ if environ is None else environ
    base = Path(base_dir or ".").resolve()
    errors = []
    try:
        Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(document)
    except Exception as error:
        return dict(protocol="iqs.search_exposure.validation/1.0.0", status="rejected",
                    errors=["schema: " + str(error).splitlines()[0]])
    policy = Path(document["search_policy_ref"])
    if not policy.is_absolute():
        policy = base / policy
    if not policy.is_file():
        errors.append("search_policy_missing")
    else:
        actual = hashlib.sha256(policy.read_bytes()).hexdigest()
        if actual != document["search_policy_sha256"]:
            errors.append("search_policy_sha256_mismatch")
    if not any(route["enabled"] for route in document["routes"]):
        errors.append("no_enabled_route")
    for route in document["routes"]:
        if route["enabled"] and route["credential_env"] not in environ:
            errors.append("credential_env_absent:" + route["credential_env"])
    if sum(route["max_queries"] for route in document["routes"]) < document["max_search_queries_per_session"]:
        errors.append("route_query_budget_below_session_cap")
    return dict(
        protocol="iqs.search_exposure.validation/1.0.0",
        status="valid" if not errors else "rejected",
        consumer_id=document["consumer_id"],
        search_policy_sha256=document["search_policy_sha256"],
        max_search_queries_per_session=document["max_search_queries_per_session"],
        max_search_cost_micros=document["max_search_cost_micros"],
        enabled_routes=[r["route_id"] for r in document["routes"] if r["enabled"]],
        credential_presence={r["credential_env"]: (r["credential_env"] in environ) for r in document["routes"]},
        errors=errors,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--base-dir", type=Path)
    args = parser.parse_args(argv)
    raw = args.document.read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        print(json.dumps(dict(protocol="iqs.search_exposure.validation/1.0.0", status="rejected",
                              errors=["document_not_strict_json"])))
        return 2
    result = validate(document, base_dir=args.base_dir or args.document.parent)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
