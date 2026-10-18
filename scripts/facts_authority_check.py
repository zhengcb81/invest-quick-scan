"""Validate a draft facts authority envelope and its context coverage.

Offline only. Checks hashes, contract versions, capabilities and that every
facts question is covered by the embedded observation context.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import facts_context_build
import facts_context_check

PROTOCOL = "iqs.facts_authority_check/1.0.0"
VERSIONS = {"answer_schema", "identity_schema", "model_policy_schema", "observation_schema", "question_catalog"}


def check(authority, pack_dir):
    errors = []
    context = authority.get("observation_context") if isinstance(authority, dict) else None
    if not isinstance(context, dict):
        return dict(protocol=PROTOCOL, status="rejected", errors=["facts_authority_context_missing"])
    if authority.get("draft_authority_protocol") != "iqs.facts_authority.draft/1.0.0":
        errors.append("facts_authority_protocol_invalid")
    if authority.get("draft") is not True:
        errors.append("facts_authority_must_be_draft")
    unsigned = {key: value for key, value in context.items() if key != "context_sha256"}
    if facts_context_build.canonical_sha256(unsigned) != authority.get("observation_context_sha256"):
        errors.append("facts_authority_context_sha256_mismatch")
    versions = authority.get("contract_versions")
    if not isinstance(versions, dict) or set(versions) != VERSIONS:
        errors.append("facts_authority_contract_versions_invalid")
    if authority.get("capabilities") != [
        "entity_security_identity_v1", "standard_observation_v1", "fact_v1"
    ]:
        errors.append("facts_authority_capabilities_invalid")
    coverage = facts_context_check.check(pack_dir, context)
    if coverage["status"] != "ready":
        errors.append("facts_authority_context_coverage_incomplete")
    return dict(
        protocol=PROTOCOL,
        status="valid" if not errors else "rejected",
        questions=len(context.get("questions") or {}),
        coverage=coverage["status"],
        errors=errors,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", required=True, type=Path)
    parser.add_argument("--pack", required=True, type=Path)
    args = parser.parse_args(argv)
    authority = json.loads(args.authority.read_text(encoding="utf-8"))
    result = check(authority, args.pack)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
