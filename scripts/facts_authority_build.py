"""Build a draft facts authority envelope (not an owner authority).

Offline only. Wraps the draft facts context with contract versions, capabilities
and producer metadata so downstream checks can validate the shape before a real
authority producer is wired.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import facts_context_build

SCHEMA = "iqs.facts_authority.draft/1.0.0"


def build(pack, identity, profile, information_cutoff, run_context, contract_versions, producer):
    context = facts_context_build.build(pack, identity, profile, information_cutoff)
    required = {"answer_schema", "identity_schema", "model_policy_schema", "observation_schema", "question_catalog"}
    if not isinstance(contract_versions, dict) or set(contract_versions) != required:
        raise ValueError("facts_authority_contract_versions_invalid")
    if contract_versions["observation_schema"] != "1.2.0" or contract_versions["answer_schema"] != "1.0.0":
        raise ValueError("facts_authority_contract_versions_invalid")
    if not isinstance(run_context, dict) or not {
        "run_id", "scan_id", "inputset_id", "task_mode", "comparison_group_id"
    } <= set(run_context):
        raise ValueError("facts_authority_run_context_required")
    if not isinstance(producer, dict) or set(producer) != {"component_version", "build_id"}:
        raise ValueError("facts_authority_producer_required")
    manifest = json.loads((Path(pack) / "manifest.json").read_text(encoding="utf-8"))
    if contract_versions["question_catalog"] != manifest["template_version"]:
        raise ValueError("facts_authority_catalog_mismatch")
    return {
        "draft_authority_protocol": SCHEMA,
        "schema_version": "3.0.0",
        "draft": True,
        "contract_versions": dict(contract_versions),
        "capabilities": ["entity_security_identity_v1", "standard_observation_v1", "fact_v1"],
        "producer": dict(producer),
        "run_context": dict(run_context),
        "observation_context": context,
        "observation_context_sha256": context["context_sha256"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--identity", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--run-context", required=True, type=Path)
    parser.add_argument("--contract-versions", required=True, type=Path)
    parser.add_argument("--producer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    authority = build(
        args.pack,
        args.identity,
        args.profile,
        args.information_cutoff,
        json.loads(args.run_context.read_text(encoding="utf-8")),
        json.loads(args.contract_versions.read_text(encoding="utf-8")),
        json.loads(args.producer.read_text(encoding="utf-8")),
    )
    args.output.write_text(json.dumps(authority, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"protocol": SCHEMA, "questions": len(authority["observation_context"]["questions"]),
                      "output": str(args.output.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
