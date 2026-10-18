"""Check whether an observation context covers a facts pack.

Offline only. A pack whose fact fields are not present in the frozen observation
context cannot be registered for native execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import facts_pack_check

PROTOCOL = "iqs.facts_context_check/1.0.0"


def _questions(context):
    if isinstance(context, dict) and isinstance(context.get("observation_context"), dict):
        return context["observation_context"].get("questions") or {}
    if isinstance(context, dict):
        return context.get("questions") or {}
    return {}


def check(pack_dir, context):
    pack = facts_pack_check.check(pack_dir)
    if pack["status"] != "valid":
        return dict(protocol=PROTOCOL, status="rejected", errors=pack["errors"])
    manifest = json.loads((Path(pack_dir) / "manifest.json").read_text(encoding="utf-8"))
    questions = _questions(context)
    covered_fields = set()
    covered_ids = set()
    for qid, row in questions.items():
        metadata = row.get("metadata") if isinstance(row, dict) else None
        if isinstance(metadata, dict):
            covered_ids.add(qid)
            if isinstance(metadata.get("field_id"), str):
                covered_fields.add(metadata["field_id"])
    pack_fields = [row.get("field_id") for row in manifest.get("questions", [])]
    pack_ids = [row.get("id") for row in manifest.get("questions", [])]
    missing_fields = [field for field in pack_fields if field not in covered_fields]
    missing_ids = [qid for qid in pack_ids if qid not in covered_ids]
    return dict(
        protocol=PROTOCOL,
        status="ready" if not missing_fields and not missing_ids else "blocked",
        pack_questions=len(pack_fields),
        context_questions=len(questions),
        missing_field_count=len(missing_fields),
        missing_question_count=len(missing_ids),
        missing_fields=missing_fields[:100],
        missing_question_ids=missing_ids[:100],
        errors=[],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    args = parser.parse_args(argv)
    context = json.loads(args.context.read_text(encoding="utf-8"))
    result = check(args.pack, context)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
