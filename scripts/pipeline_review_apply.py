"""Ingest owner decisions from a review pack into the adjudication ledger.

The ledger is append-only JSONL under docs/implementation/parallel-lanes/
packages/2026-10-24/review-ledger/: one record per decision with pack and
input hashes for provenance. Re-applying the same pack updates nothing and
reports idempotent; a row missing its decision or reason is rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PACK_SCHEMA = "pipeline-review-pack/1.0.0"
DECISIONS_SCHEMA = "pipeline-review-decisions/1.0.0"
LEDGER_SCHEMA = "pipeline-review-ledger/1.0.0"
VALID_DECISIONS = {"adopt_snapshot", "keep_composition", "known_deviation"}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ledger_path(pack_id: str, ledger_dir: Path) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in pack_id)
    return ledger_dir / f"{safe}.jsonl"


def apply_decisions(pack_path: Path, decisions_path: Path, ledger_dir: Path,
                    allow_partial: bool = False) -> tuple[int, dict]:
    """Ingest owner decisions into the append-only ledger.

    Strict by default: any incomplete row (missing reason or invalid decision)
    rejects the whole batch and nothing is written. With ``allow_partial`` the
    complete rows are written and the incomplete ones are reported as pending —
    large review batches should not lose fifty good decisions to two blank
    reasons. Completed rows are still idempotent and never rewritten.
    """
    if pack_path.is_dir():
        pack_path = pack_path / "pack.json"
    pack = json.loads(pack_path.read_text(encoding="utf-8-sig"))
    if pack.get("schema") != PACK_SCHEMA:
        return 2, {"status": "invalid", "error": f"pack schema mismatch: {pack.get('schema')}"}
    doc = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    if doc.get("schema") != DECISIONS_SCHEMA:
        return 2, {"status": "invalid", "error": f"decisions schema mismatch: {doc.get('schema')}"}
    if doc.get("pack_id") != pack.get("pack_id"):
        return 2, {"status": "invalid", "error": "decisions pack_id does not match pack"}

    rows = {row["row_id"]: row for company in pack["companies"] for row in company["rows"]}
    decisions = doc.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        return 2, {"status": "invalid", "error": "decisions list is empty"}

    records = []
    incomplete = []
    for item in decisions:
        row_id = item.get("row_id")
        row = rows.get(row_id)
        if row is None:
            return 2, {"status": "invalid", "error": f"unknown row_id: {row_id}"}
        decision = item.get("decision")
        reason = str(item.get("reason") or "").strip()
        if decision not in VALID_DECISIONS:
            incomplete.append({"row_id": row_id, "problem": f"invalid decision: {decision!r}"})
            continue
        if not reason:
            incomplete.append({"row_id": row_id, "problem": "reason is empty"})
            continue
        company = next(c for c in pack["companies"] if row_id in {r["row_id"] for r in c["rows"]})
        records.append(
            {
                "schema": LEDGER_SCHEMA,
                "pack_id": pack["pack_id"],
                "row_id": row_id,
                "entity_id": company["entity_id"],
                "company": company["company"],
                "module_id": row["module_id"],
                "category": row["category"],
                "decision": decision,
                "owner_reason_verbatim": reason,
                "pack_sha256": _sha256_file(pack_path),
                "decisions_sha256": _sha256_file(decisions_path),
                "snapshot_id": pack["snapshot"]["snapshot_id"],
            }
        )

    if incomplete and not allow_partial:
        return 2, {"status": "incomplete", "incomplete": incomplete}

    ledger_dir.mkdir(parents=True, exist_ok=True)
    target = _ledger_path(pack["pack_id"], ledger_dir)
    existing = []
    if target.is_file():
        existing = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]

    by_key = {f"{r['pack_id']}:{r['row_id']}": r for r in existing}
    added = 0
    for record in records:
        key = f"{record['pack_id']}:{record['row_id']}"
        if key in by_key:
            old = by_key[key]
            if old["decision"] != record["decision"] or old["owner_reason_verbatim"] != record["owner_reason_verbatim"]:
                return 2, {
                    "status": "conflict",
                    "error": f"row {record['row_id']} already adjudicated with a different verdict — "
                             "ledger is append-only; start a new pack to revise",
                }
        else:
            by_key[key] = record
            existing.append(record)
            added += 1

    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for record in existing:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    result = {
        "status": "partial" if incomplete else "ok",
        "ledger": str(target),
        "rows_total": len(records),
        "rows_added": added,
        "rows_idempotent": len(records) - added,
    }
    if incomplete:
        result["pending"] = incomplete
        result["pending_count"] = len(incomplete)
        return 2, result
    return 0, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--ledger-dir", required=True, type=Path)
    parser.add_argument("--allow-partial", action="store_true",
                        help="写入已完成裁定，未完成行（缺理由/无效裁定）仅报告为 pending")
    args = parser.parse_args(argv)
    code, result = apply_decisions(args.pack, args.decisions, args.ledger_dir,
                                   allow_partial=args.allow_partial)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
