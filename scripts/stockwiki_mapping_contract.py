"""Independent IQS consumer validation of StockWiki mapping DTO 1.0.0.

The caller must obtain the snapshot and mapping DTO from StockWiki's public
owner API. This validates their internal consistency; it does not establish
the source's authenticity by itself.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/quick_scan/identity-mapping-dto.schema.json").read_text(encoding="utf-8"))
_VALIDATOR = Draft202012Validator(SCHEMA)
_QUERY_FIELDS = ("ticker", "ticker_raw", "market", "exchange_raw", "exchange_mic", "as_of")


class MappingContractError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise MappingContractError("mapping_effective_time_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise MappingContractError("mapping_effective_time_invalid") from None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise MappingContractError("mapping_effective_time_invalid")
    return parsed


def _active_at(listing: dict, binding: dict, as_of: datetime) -> bool:
    if binding["status"] != "active" or listing["listing_status"] == "delisted":
        return False
    start = listing["valid_from"]
    end = listing["valid_to"]
    parsed_start = _utc(start) if start is not None else None
    parsed_end = _utc(end) if end is not None else None
    if parsed_start is not None and parsed_end is not None and parsed_start >= parsed_end:
        raise MappingContractError("mapping_effective_time_invalid")
    if parsed_start is not None and as_of < parsed_start:
        return False
    if parsed_end is not None and as_of >= parsed_end:
        return False
    return True


def _expected_candidates(snapshot: dict, query: dict) -> tuple[list[dict], bool]:
    bindings = {row["binding_ref"]: row for row in snapshot["source_bindings"]}
    if len(bindings) != len(snapshot["source_bindings"]):
        raise MappingContractError("snapshot_duplicate_binding")
    candidate_rows = []
    mismatch = False
    as_of = _utc(query["as_of"])
    expectation = query.get("source_binding_expectation")
    seen = set()
    for entity in snapshot["entities"]:
        security_ids = {row["security_id"] for row in entity["securities"]}
        if len(security_ids) != len(entity["securities"]):
            raise MappingContractError("snapshot_duplicate_security")
        for listing in entity["listings"]:
            key = (entity["entity_id"], listing["listing_id"])
            if key in seen:
                raise MappingContractError("snapshot_duplicate_listing")
            seen.add(key)
            if not (
                listing["ticker"] == query["ticker"]
                and listing["ticker_raw"] == query["ticker_raw"]
                and listing["market"] == query["market"]
                and listing["exchange_raw"] == query["exchange_raw"]
                and (query.get("exchange_mic") is None or listing["exchange_mic"] == query["exchange_mic"])
            ):
                continue
            binding = bindings.get(listing["source_binding_ref"])
            if binding is None:
                raise MappingContractError("candidate_binding_missing")
            if not _active_at(listing, binding, as_of):
                continue
            if expectation is not None and (
                binding["source_namespace"] != expectation["source_namespace"]
                or binding["source_record_id"] != expectation["source_record_id"]
            ):
                mismatch = True
                continue
            if (listing["entity_id"] != entity["entity_id"]
                    or listing["security_id"] not in security_ids
                    or binding["entity_id"] != entity["entity_id"]
                    or binding["security_id"] != listing["security_id"]
                    or binding["listing_id"] != listing["listing_id"]
                    or binding["market"] != listing["market"]
                    or binding["exchange_raw"] != listing["exchange_raw"]
                    or binding["ticker_raw"] != listing["ticker_raw"]
                    or binding["ticker"] != listing["ticker"]
                    or binding["exchange_mic"] not in (None, listing["exchange_mic"])
                    or binding["valid_from"] != listing["valid_from"]
                    or binding["valid_to"] != listing["valid_to"]):
                raise MappingContractError("candidate_owner_join_mismatch")
            candidate_rows.append({
                "entity_id": entity["entity_id"],
                "entity_canonical_name": entity["canonical_name"],
                "security_id": listing["security_id"],
                "listing_id": listing["listing_id"],
                "market": listing["market"],
                "exchange_raw": listing["exchange_raw"],
                "exchange_mic": listing["exchange_mic"],
                "ticker_raw": listing["ticker_raw"],
                "ticker": listing["ticker"],
                "currency": listing["currency"],
                "listing_status": listing["listing_status"],
                "as_of": listing["valid_from"],
                "source_binding": binding,
            })
    candidate_rows.sort(key=lambda row: (row["entity_id"], row["listing_id"]))
    return candidate_rows, mismatch


def validate_mapping_dto(dto: dict, snapshot: dict, query: dict | None) -> dict:
    """Reject any DTO whose four-state decision differs from owner snapshot data."""
    if not isinstance(dto, dict) or dto.get("mapping_dto_schema_version") != "1.0.0":
        raise MappingContractError("unsupported_mapping_dto_version")
    if not _VALIDATOR.is_valid(dto):
        raise MappingContractError("mapping_dto_schema_invalid")
    if not isinstance(snapshot, dict) or not all(
        key in snapshot for key in ("snapshot_sha256", "snapshot_schema_version",
                              "identity_package_version", "as_of", "entities", "source_bindings")
    ):
        raise MappingContractError("snapshot_invalid")
    if snapshot["snapshot_schema_version"] != "1.0.0" or snapshot["identity_package_version"] != "2.2.0":
        raise MappingContractError("snapshot_version_unsupported")
    payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    try:
        digest = hashlib.sha256(_canonical(payload)).hexdigest()
    except (TypeError, ValueError):
        raise MappingContractError("snapshot_invalid") from None
    if digest != snapshot["snapshot_sha256"] or dto["snapshot_sha256"] != digest:
        raise MappingContractError("snapshot_hash_mismatch")
    if query is not None:
        if not isinstance(query, dict) or not all(key in query for key in _QUERY_FIELDS):
            raise MappingContractError("mapping_query_invalid")
        if query["as_of"] != snapshot["as_of"]:
            raise MappingContractError("mapping_as_of_mismatch")
        expectation = query.get("source_binding_expectation")
        if expectation is not None and (
            not isinstance(expectation, dict)
            or set(expectation) != {"source_namespace", "source_record_id"}
        ):
            raise MappingContractError("mapping_query_invalid")
        try:
            candidates, mismatch = _expected_candidates(snapshot, query)
        except MappingContractError:
            raise
        except (KeyError, TypeError, ValueError):
            raise MappingContractError("snapshot_invalid") from None
        status = "mapped" if len(candidates) == 1 else "ambiguous" if candidates else "unknown"
        queried_identity = {key: query[key] for key in _QUERY_FIELDS}
    else:
        candidates, mismatch, status, queried_identity = [], False, None, None
    expected = {
        "mapping_dto_schema_version": "1.0.0",
        "snapshot_sha256": digest,
        "mapping_status": status,
        "attempted": query is not None,
        "queried_identity": queried_identity,
        "candidate": candidates[0] if status == "mapped" else None,
        "candidates": candidates,
        "binding_mismatch": mismatch,
    }
    if dto != expected:
        raise MappingContractError("mapping_semantic_mismatch")
    return dto
