"""Build and validate a verified search receipt from a provider response.

Offline only. The receipt binds the raw provider response hash to an owner
search exposure; it never treats a search result as an accepted answer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/quick_scan/search-receipt-v1.schema.json").read_bytes())
VALIDATOR = Draft202012Validator(SCHEMA)


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def from_response(raw, *, exposure, policy_sha256, provider, route_id, query, requested_at, completed_at, cost_micros):
    try:
        payload = json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("search_response_not_strict_json") from error
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("search_response_results_required")
    results = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str) or not isinstance(row.get("title"), str):
            raise ValueError("search_response_result_invalid")
        item = {
            "title": row["title"],
            "url": row["url"],
            "snippet": row.get("snippet") or "",
            "rerank_score": float(row.get("rerank_score", 0)),
        }
        if isinstance(row.get("summary"), str):
            item["summary"] = row["summary"]
        if isinstance(row.get("content"), str):
            item["content"] = row["content"]
        results.append(item)
    receipt = {
        "protocol": "iqs.search_receipt/1.0.0",
        "exposure_sha256": canonical_sha256(exposure),
        "policy_sha256": policy_sha256,
        "provider": provider,
        "route_id": route_id,
        "query": query,
        "requested_at": requested_at,
        "completed_at": completed_at,
        "status": "ok" if results else "empty",
        "results": results,
        "result_count": len(results),
        "cost_micros": cost_micros,
        "currency": exposure["currency"],
        "response_sha256": hashlib.sha256(raw if isinstance(raw, (bytes, bytearray)) else raw.encode("utf-8")).hexdigest(),
    }
    validate(receipt, exposure=exposure)
    return receipt


def validate(receipt, *, exposure=None):
    VALIDATOR.validate(receipt)
    if exposure is not None:
        if receipt["exposure_sha256"] != canonical_sha256(exposure):
            raise ValueError("search_receipt_exposure_mismatch")
        if receipt["cost_micros"] > exposure["max_search_cost_micros"]:
            raise ValueError("search_receipt_cost_exceeds_exposure")
        if receipt["currency"] != exposure["currency"]:
            raise ValueError("search_receipt_currency_mismatch")
        routes = {r["route_id"]: r for r in exposure["routes"]}
        route = routes.get(receipt["route_id"])
        if route is None or route["provider"] != receipt["provider"]:
            raise ValueError("search_receipt_route_not_in_exposure")
    if receipt["status"] == "ok" and receipt["result_count"] != len(receipt["results"]):
        raise ValueError("search_receipt_result_count_mismatch")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--exposure", type=Path)
    args = parser.parse_args(argv)
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    exposure = json.loads(args.exposure.read_text(encoding="utf-8")) if args.exposure else None
    try:
        validate(receipt, exposure=exposure)
    except Exception as error:
        print(json.dumps({"protocol": "iqs.search_receipt.validation/1.0.0", "status": "rejected",
                          "errors": [str(error).splitlines()[0]]}, ensure_ascii=False))
        return 2
    print(json.dumps({"protocol": "iqs.search_receipt.validation/1.0.0", "status": "valid",
                      "result_count": receipt["result_count"], "receipt_status": receipt["status"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
