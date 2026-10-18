"""Build a draft facts observation context from a facts pack.

Offline only. Produces the questions/field metadata that an authority producer
would need; it is not an owner authority, signature, or admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "stockqa.quick_scan_observation_context/1.0.0"
SCHEMA = "iqs.facts_context/1.0.0"


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(pack_dir, identity_path, profile_path, information_cutoff, *, root=None):
    root = Path(root or ROOT)
    pack = Path(pack_dir)
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    identity = json.loads(Path(identity_path).read_text(encoding="utf-8"))
    payload = identity.get("payload") if isinstance(identity, dict) else None
    entity_id = payload.get("entity_id") if isinstance(payload, dict) else None
    if not isinstance(entity_id, str) or not entity_id:
        raise ValueError("facts_context_identity_entity_required")
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    if profile.get("company") and payload.get("canonical_name") and profile["company"] != payload["canonical_name"]:
        raise ValueError("facts_context_profile_identity_mismatch")
    cohort = {
        "company_type": profile.get("company_type", "unclassified"),
        "industries": list(profile.get("industry_modules") or []),
        "stage": profile.get("stage", "unclassified"),
        "subtype": profile.get("business_subtype"),
    }
    questions = {}
    for row in manifest.get("questions", []):
        qid = row["id"]
        questions[qid] = {
            "frozen_prompt_sha256": hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest(),
            "metadata": {
                "construct_id": qid,
                "field_id": row["field_id"],
                "entity_id": entity_id,
                "cohort": cohort,
                "cycle_sensitive": bool(profile.get("cycle_sensitive", False)),
                "information_cutoff": information_cutoff,
                "evidence_review_status": "unreviewed",
                "response_kind": "fact",
                "relation_count": len(row.get("relations") or []),
                "max_items": row.get("max_items"),
            },
        }
    context = {
        "schema": PROTOCOL,
        "draft_context_protocol": SCHEMA,
        "manifest_content_sha256": canonical_sha256(manifest),
        "metric_registry_sha256": file_sha256(root / "questions/metric-registry.json"),
        "answer_schema_sha256": file_sha256(root / "schemas/answer-content.schema.json"),
        "observation_schema_sha256": file_sha256(root / "schemas/observation.schema.json"),
        "identity_snapshot_sha256": canonical_sha256(identity),
        "questions": questions,
    }
    context["context_sha256"] = canonical_sha256(context)
    return context


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--identity", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    context = build(args.pack, args.identity, args.profile, args.information_cutoff)
    args.output.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"protocol": SCHEMA, "questions": len(context["questions"]),
                      "output": str(args.output.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
