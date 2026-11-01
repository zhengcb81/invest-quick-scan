"""B03 company assessment projection bridge (strictly read-only).

The owner (StockWiki) publishes immutable company assessment snapshots
through ``stockwiki.public_company_assessments`` (its public CLI is the
operator face; the narrow in-process read API used here is the owner-internal
read entry this card was granted). This module is the projection bridge
between that owner read surface and the IQS Dashboard HTTP service:

- the WORKER half (``worker_read``) runs inside the isolated owner worker
  subprocess, validates the bounded payload, maps owner refusal codes and
  returns one plain dict — it performs reads only;
- the SERVICE half (``project_result``/``project_history``) shapes the GET
  response and pins the entity-scoped IQSLink beside it.

No aggregate score is ever computed, selected or summed here: the owner's
``aggregate_score`` is passed through verbatim (``null`` with its named
reason when the owner publishes no company aggregate authority). A missing
observation store or an absent registry is forwarded as an honest named
reason, never as a zero result, and a question-level observation can never
become a company result through this projection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECTION_PROTOCOL = "iqs.dashboard.company_assessment/1"
PROJECTION_VERSION = "company_assessment/1.0.0"
# The owner's own declaration this projection was written against.
OWNER_PROTOCOL = "stockwiki.company_assessment/1"
OWNER_SCHEMA_VERSION = "1.0.0"

# Honest named absences pass through verbatim: a store that cannot be read
# or a registry with no registered result is an explicit reason, never zero.
_HONEST_ABSENT_CODES = {
    "company_result_not_registered",
    "company_assessment_registry_absent",
    "observation_store_missing",
    "observation_store_unavailable",
}
_REFUSAL_STATUS = {
    "entity_invalid": 400,
    "result_invalid": 400,
    "invalid_request": 400,
    "manifest_invalid": 400,
    "bounds_exceeded": 400,
    "registry_schema_too_new": 502,
    "registry_schema_unavailable": 502,
    "registry_integrity_mismatch": 502,
    "registry_unavailable": 503,
    "observation_store_unavailable": 503,
    "identity_store_missing": 503,
    "write_refused_read_only": 502,
    "internal_refused": 502,
}


class ProjectionError(Exception):
    """A projection refusal the transport maps to an HTTP status."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _identifier(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ProjectionError(code, "identifier is missing or malformed")
    if not value[0].isascii() or not value[0].isalnum():
        raise ProjectionError(code, "identifier is missing or malformed")
    for char in value:
        if char.isascii() and (char.isalnum() or char in "_.:-"):
            continue
        raise ProjectionError(code, "identifier is missing or malformed")
    return value


def _validated_result_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) - {"entity_id", "result_id"}:
        raise ProjectionError("invalid_payload", "unknown company_result payload fields")
    entity_id = _identifier(payload.get("entity_id"), "entity_id_invalid")
    result_id = payload.get("result_id")
    if result_id is not None:
        _identifier(result_id, "result_id_invalid")
        if not result_id.startswith("cas_") or len(result_id) > 64:
            raise ProjectionError("result_id_invalid", "result_id must be a cas_ snapshot id")
    return {"entity_id": entity_id, "result_id": result_id}


def _validated_history_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) - {"entity_id", "limit", "offset"}:
        raise ProjectionError("invalid_payload", "unknown company_history payload fields")
    entity_id = _identifier(payload.get("entity_id"), "entity_id_invalid")
    limit, offset = payload.get("limit", 20), payload.get("offset", 0)
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ProjectionError("pagination_invalid", "limit must be 1-50")
    if type(offset) is not int or offset < 0 or offset > 100000:
        raise ProjectionError("pagination_invalid", "offset must be a bounded nonnegative integer")
    return {"entity_id": entity_id, "limit": limit, "offset": offset}


def worker_read(config: dict, operation: str, payload: Any) -> dict[str, Any]:
    """Worker half: read the owner's company assessment authority (read-only).

    Runs inside the isolated owner worker subprocess with ``stockwiki_root``
    already first on ``sys.path``. Only the owner's narrow internal read
    entry is used; no registration happens here and no store is ever opened
    writable.
    """
    from stockwiki.paths import WorkspacePaths
    from stockwiki.public_company_assessments import (
        CompanyAssessmentError,
        list_company_history,
        read_company_result,
    )

    paths = WorkspacePaths.from_root(Path(config["workspace_root"]))
    if operation == "company_result":
        normalized = _validated_result_payload(payload)
        _require_entity(config, normalized["entity_id"])
        try:
            owner = read_company_result(paths, **normalized)
        except CompanyAssessmentError as error:
            raise ProjectionError(
                error.code,
                "the owner company assessment authority refused this read",
                _REFUSAL_STATUS.get(error.code, 502),
            ) from None
    elif operation == "company_history":
        normalized = _validated_history_payload(payload)
        _require_entity(config, normalized["entity_id"])
        try:
            owner = list_company_history(paths, **normalized)
        except CompanyAssessmentError as error:
            raise ProjectionError(
                error.code,
                "the owner company assessment authority refused this read",
                _REFUSAL_STATUS.get(error.code, 502),
            ) from None
    else:  # pragma: no cover - the worker dispatch only sends these two
        raise ProjectionError("operation_unknown", "Unsupported company projection read", 404)
    owner = _checked_owner_read(owner)
    return {
        "protocol": PROJECTION_PROTOCOL,
        "projection_version": PROJECTION_VERSION,
        "entity_id": normalized["entity_id"],
        "read": "result" if operation == "company_result" else "history",
        "owner_payload": _bounded(owner),
        "network_calls": 0,
        "llm_calls": 0,
    }


def _checked_owner_read(owner: Any) -> dict[str, Any]:
    """Validate the owner's own read envelope before it is projected.

    The owner's protocol/schema declaration is checked rather than assumed, so
    a future owner shape is never relabelled under this projection version.
    """
    if not isinstance(owner, dict):
        raise ProjectionError("owner_projection_invalid", "owner read is not an object", 502)
    for key in ("protocol", "schema_version", "network_calls", "llm_calls"):
        if key not in owner:
            raise ProjectionError("owner_projection_invalid", "owner read is missing envelope fields", 502)
    if owner.get("protocol") != OWNER_PROTOCOL or owner.get("schema_version") != OWNER_SCHEMA_VERSION:
        raise ProjectionError("owner_protocol_unsupported", "owner company assessment protocol is unsupported", 502)
    if owner.get("network_calls") != 0 or owner.get("llm_calls") != 0:
        raise ProjectionError("owner_projection_invalid", "owner read reported unexpected I/O", 502)
    return owner


def _require_entity(config: dict, entity_id: str) -> None:
    """A company projection only answers for a registered canonical entity."""
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore

    paths = WorkspacePaths.from_root(Path(config["workspace_root"]))
    identity = QuickScanStore(paths)
    if not identity.database_path.is_file():
        raise ProjectionError("owner_database_missing", "StockWiki identity store is not initialized", 503)
    if identity.get_entity(entity_id) is None:
        raise ProjectionError("entity_not_found", "No registered entity has this ID", 404)


def _bounded(value: Any) -> Any:
    """Reject unexpectedly huge owner payloads instead of truncating them."""
    encoded = json.dumps(value, ensure_ascii=False)
    if len(encoded) > 16 * 1024 * 1024:
        raise ProjectionError("owner_response_too_large", "owner projection exceeds the response bound", 502)
    return value


def project_result(owner_payload: dict[str, Any]) -> dict[str, Any]:
    """Service half: shape one GET ``company/result`` response.

    The owner's honest absent reasons pass through verbatim; ``company_result``
    stays ``null`` unless the owner itself published a registered snapshot.
    """
    _require_owner_envelope(owner_payload, "result")
    owner = owner_payload["owner_payload"]
    result = owner.get("result")
    reason_code = owner.get("reason_code")
    if result is None and reason_code not in _HONEST_ABSENT_CODES:
        raise ProjectionError(
            "owner_projection_invalid", "owner result read has neither a result nor a named reason", 502
        )
    if result is not None:
        if not isinstance(result, dict) or not isinstance(result.get("result_id"), str) or not result["result_id"]:
            raise ProjectionError("owner_projection_invalid", "owner result snapshot is malformed", 502)
        if result.get("entity_id") != owner_payload["entity_id"]:
            raise ProjectionError(
                "owner_projection_invalid",
                "owner result snapshot names a different entity than the read",
                502,
            )
        if result.get("aggregate_score") is not None:
            raise ProjectionError(
                "owner_projection_invalid",
                "this owner version publishes no aggregate score; a non-null one is refused",
                502,
            )
        reason_code = None
    return {
        "protocol": PROJECTION_PROTOCOL,
        "projection_version": PROJECTION_VERSION,
        "entity_id": owner_payload["entity_id"],
        "company_result": result,
        "reason_code": reason_code,
        "store_id": owner.get("store_id"),
        "registry_store_id": owner.get("registry_store_id"),
        "network_calls": 0,
        "llm_calls": 0,
    }


def project_history(owner_payload: dict[str, Any], *, limit: int, offset: int) -> dict[str, Any]:
    """Service half: shape one GET ``company/history`` response.

    The page is re-checked against the REQUESTED bounds: a bounded route must
    not forward a page the owner was not asked for (defence in depth against
    an owner that ignores its own limit).
    """
    _require_owner_envelope(owner_payload, "history")
    owner = owner_payload["owner_payload"]
    items = owner.get("items")
    page = owner.get("page")
    if not isinstance(items, list) or not isinstance(page, dict):
        raise ProjectionError("owner_projection_invalid", "owner history read is missing items/page", 502)
    if any(not isinstance(item, dict) or not isinstance(item.get("result_id"), str)
           or not item["result_id"] for item in items):
        raise ProjectionError("owner_projection_invalid", "owner history item is malformed", 502)
    if len(items) > limit:
        raise ProjectionError("owner_projection_invalid", "owner history page exceeds the requested limit", 502)
    if page.get("limit") != limit or page.get("offset") != offset:
        raise ProjectionError("owner_projection_invalid", "owner history page does not echo the request", 502)
    total = page.get("total")
    if type(total) is not int or total < len(items) + (offset or 0):
        raise ProjectionError("owner_projection_invalid", "owner history total is malformed", 502)
    return {
        "protocol": PROJECTION_PROTOCOL,
        "projection_version": PROJECTION_VERSION,
        "entity_id": owner_payload["entity_id"],
        "items": items,
        "page": {"limit": limit, "offset": offset, "total": total},
        "registry_state": owner.get("registry_state"),
        "registry_store_id": owner.get("registry_store_id"),
        "network_calls": 0,
        "llm_calls": 0,
    }


def _require_owner_envelope(owner_payload: Any, read: str) -> None:
    if not isinstance(owner_payload, dict):
        raise ProjectionError("owner_projection_invalid", "owner payload is missing", 502)
    if owner_payload.get("protocol") != PROJECTION_PROTOCOL:
        raise ProjectionError("owner_projection_invalid", "owner payload protocol mismatch", 502)
    if owner_payload.get("projection_version") != PROJECTION_VERSION:
        raise ProjectionError("projection_version_unsupported", "company projection version is unsupported", 502)
    if owner_payload.get("read") != read:
        raise ProjectionError("owner_projection_invalid", "owner payload read kind mismatch", 502)
