"""Validate a generated facts pack before registration or owner admission.

Offline only. Checks the manifest contract, question identity, source hashes and
that every question is a facts question; it does not register or send anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "iqs.facts_pack_check/1.0.0"


def check(pack_dir, *, root=None):
    root = Path(root or ROOT)
    pack = Path(pack_dir)
    errors = []
    manifest_path = pack / "manifest.json"
    questions_path = pack / "questions.json"
    if not manifest_path.is_file() or not questions_path.is_file():
        return dict(protocol=PROTOCOL, status="rejected", errors=["facts_pack_files_missing"])
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        questions = json.loads(questions_path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return dict(protocol=PROTOCOL, status="rejected", errors=["facts_pack_not_strict_json"])
    if manifest.get("schema_version") != "3.0":
        errors.append("facts_pack_schema_version_required")
    if manifest.get("answer_format") != "standard-1":
        errors.append("facts_pack_standard_1_required")
    if not isinstance(manifest.get("template_version"), str) or not manifest["template_version"]:
        errors.append("facts_pack_template_version_required")
    rows = manifest.get("questions")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
        errors.append("facts_pack_question_count_invalid")
        rows = []
    ids, fields = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("facts_pack_question_invalid")
            continue
        qid = row.get("id")
        field = row.get("field_id")
        if row.get("response_kind") != "fact":
            errors.append("facts_pack_non_fact_question:" + str(qid))
        if not isinstance(qid, str) or not qid or qid in ids:
            errors.append("facts_pack_duplicate_or_invalid_id:" + str(qid))
        if not isinstance(field, str) or not field.startswith("facts.") or field in fields:
            errors.append("facts_pack_invalid_field:" + str(field))
        if not isinstance(row.get("prompt"), str) or not row["prompt"].strip():
            errors.append("facts_pack_prompt_required:" + str(qid))
        ids.add(qid)
        fields.add(field)
    sources = manifest.get("source_sha256")
    if not isinstance(sources, dict) or not sources:
        errors.append("facts_pack_source_hashes_required")
    else:
        for rel, expected in sources.items():
            target = root / rel
            if not target.is_file():
                errors.append("facts_pack_source_missing:" + str(rel))
            elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                errors.append("facts_pack_source_changed:" + str(rel))
    if manifest.get("mode") not in {"quick", "full"}:
        errors.append("facts_pack_mode_invalid")
    return dict(
        protocol=PROTOCOL,
        status="valid" if not errors else "rejected",
        question_count=len(ids),
        template_version=manifest.get("template_version"),
        mode=manifest.get("mode"),
        source_files=sorted(sources) if isinstance(sources, dict) else [],
        errors=errors,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    args = parser.parse_args(argv)
    result = check(args.pack)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
