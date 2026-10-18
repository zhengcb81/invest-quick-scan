"""Bind verified search receipts to a task exposure and checkpoint field.

Offline only. The checkpoint binding is a hash over canonical receipts; the
engine may store that hash, but this module never authorizes a send.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import search_receipt as receipts

PROTOCOL = "iqs.search_checkpoint_binding/1.0.0"


def canonical_sha256(value):
    return receipts.canonical_sha256(value)


def bind(profile, receipt_rows, *, checkpoint=None):
    exposure = profile.get("search_exposure") if isinstance(profile, dict) else None
    if exposure is None and isinstance(profile, dict):
        execution = profile.get("execution_profile")
        if isinstance(execution, dict):
            exposure = execution.get("search_exposure")
    errors = []
    if not isinstance(exposure, dict):
        return dict(protocol=PROTOCOL, status="rejected", errors=["task_search_exposure_missing"])
    if not isinstance(receipt_rows, list):
        return dict(protocol=PROTOCOL, status="rejected", errors=["receipts_must_be_list"])
    limit = exposure.get("max_search_queries_per_session")
    if not isinstance(limit, int) or len(receipt_rows) > limit:
        errors.append("receipt_count_exceeds_exposure")
    total_cost = 0
    checked = []
    for row in receipt_rows:
        try:
            receipts.validate(row, exposure=exposure)
        except Exception as error:
            errors.append("receipt_invalid:" + str(error).splitlines()[0])
            continue
        total_cost += row["cost_micros"]
        checked.append(row)
    if total_cost > exposure.get("max_search_cost_micros", 0):
        errors.append("receipt_cost_exceeds_exposure")
    receipts_sha256 = canonical_sha256([canonical_sha256(row) for row in checked])
    if isinstance(checkpoint, dict) and "search_receipts_sha256" in checkpoint:
        if checkpoint["search_receipts_sha256"] != receipts_sha256:
            errors.append("checkpoint_receipts_hash_mismatch")
    return dict(
        protocol=PROTOCOL,
        status="bound" if not errors else "rejected",
        exposure_sha256=canonical_sha256(exposure),
        receipt_count=len(checked),
        total_cost_micros=total_cost,
        currency=exposure.get("currency"),
        receipts_sha256=receipts_sha256,
        errors=errors,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args(argv)
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    rows = json.loads(args.receipts.read_text(encoding="utf-8"))
    checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8")) if args.checkpoint else None
    result = bind(profile, rows, checkpoint=checkpoint)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "bound" else 2


if __name__ == "__main__":
    raise SystemExit(main())
