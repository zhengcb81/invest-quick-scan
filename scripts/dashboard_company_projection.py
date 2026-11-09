"""B03 company assessment projection bridge (strictly read-only).

StockWiki's public read-only command owns the assessment and identity reads.
This adapter checks the versioned command response and shapes the existing IQS
Dashboard result and history payloads.

No aggregate score is ever computed, selected or summed here: the owner's
``aggregate_score`` is passed through verbatim (``null`` with its named
reason when the owner publishes no company aggregate authority). A missing
observation store or an absent registry is forwarded as an honest named
reason, never as a zero result, and a question-level observation can never
become a company result through this projection.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

if __package__:
    from .dashboard_json import decode_owner_json
else:
    from dashboard_json import decode_owner_json

PROJECTION_PROTOCOL = "iqs.dashboard.company_assessment/1"
PROJECTION_VERSION = "company_assessment/1.0.0"
# The owner's own declaration this projection was written against.
OWNER_PROTOCOL = "stockwiki.company_assessment/1"
OWNER_SCHEMA_VERSION = "1.0.0"
_OWNER_COMMAND = "dashboard_company_assessment_cli.py"
_MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_ERROR_CODE = re.compile(r"[a-z][a-z0-9_]{0,100}")

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
    "response_too_large": 502,
    "write_refused_read_only": 502,
    "internal_refused": 502,
}
_IDENTITY_REFUSALS = {
    "identity_store_missing": "owner_database_missing",
    "identity_store_unavailable": "owner_store_unreadable",
    "identity_store_busy": "owner_busy",
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


def read_company_assessment(
    config: dict, operation: str, payload: Any, *, environment: dict[str, str] | None = None
) -> dict[str, Any]:
    """Read one company projection over the owner's versioned public command."""
    if operation == "company_result":
        normalized = _validated_result_payload(payload)
        action, read = "read", "result"
        pin = normalized["result_id"]
        options = ["--result-id", pin] if pin is not None else []
    elif operation == "company_history":
        normalized = _validated_history_payload(payload)
        action = read = "history"
        options = ["--limit", str(normalized["limit"]), "--offset", str(normalized["offset"])]
    else:
        raise ProjectionError("operation_unknown", "Unsupported company projection read", 404)

    root = Path(config["stockwiki_root"]).resolve()
    script = root / _OWNER_COMMAND
    if not script.is_file():
        raise _owner_unavailable()
    entity_id = normalized["entity_id"]
    command = [config["stockwiki_python"], "-B", "-X", "utf8", str(script), action,
               "--root", config["workspace_root"], "--entity", entity_id, "--require-identity", *options]
    if environment is None:
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "LD_LIBRARY_PATH"}}
    try:
        process = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                                 capture_output=True, timeout=config.get("timeout_seconds", 30),
                                 env=environment)
    except subprocess.TimeoutExpired:
        raise ProjectionError("owner_timeout", "StockWiki owner request timed out", 504) from None
    except OSError:
        raise ProjectionError("owner_process_unavailable", "Cannot start StockWiki interpreter", 503) from None
    if process.returncode == 2 and not process.stdout:
        _raise_owner_refusal(process.stderr)
    if process.returncode != 0:
        raise ProjectionError("owner_process_failed", "StockWiki owner command failed", 502)
    owner = _checked_owner_read(_decode_owner_output(process.stdout))
    if owner.get("action") != action or owner.get("entity_id") != entity_id:
        raise ProjectionError("owner_projection_invalid", "owner read does not match the request", 502)
    envelope = {
        "protocol": PROJECTION_PROTOCOL,
        "projection_version": PROJECTION_VERSION,
        "entity_id": entity_id,
        "read": read,
        "owner_payload": {key: value for key, value in owner.items() if key != "action"},
        "network_calls": 0,
        "llm_calls": 0,
    }
    absent = owner.get("reason_code") == "company_not_registered"
    if read == "result":
        if not {"result", "reason_code"} <= owner.keys() or (absent and owner["result"] is not None):
            raise ProjectionError("owner_projection_invalid", "owner result status is malformed", 502)
        if absent:
            raise ProjectionError("entity_not_found", "No registered entity has this ID", 404)
        result = project_result(envelope)["company_result"]
        if pin is not None and result is not None and result["result_id"] != pin:
            raise ProjectionError("company_result_pin_mismatch", "owner returned a different pinned result", 502)
    else:
        history = project_history(envelope, limit=normalized["limit"], offset=normalized["offset"])
        unknown = history["registry_state"] == "entity_not_registered"
        if absent != unknown or (absent and (history["items"] or history["page"]["total"] != 0)):
            raise ProjectionError("owner_projection_invalid", "owner history identity status is malformed", 502)
        if unknown:
            raise ProjectionError("entity_not_found", "No registered entity has this ID", 404)
    return envelope


def _owner_unavailable() -> ProjectionError:
    return ProjectionError(
        "owner_company_projection_unavailable",
        "the StockWiki owner does not publish the required company assessment read",
        502,
    )


def _decode_owner_output(raw: bytes) -> Any:
    if len(raw) > _MAX_OUTPUT_BYTES:
        raise ProjectionError("owner_response_too_large", "owner projection exceeds the response bound", 502)

    try:
        return decode_owner_json(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        raise ProjectionError("owner_projection_invalid", "owner returned invalid JSON", 502) from None


def _raise_owner_refusal(raw: bytes) -> None:
    refusal = _decode_owner_output(raw)
    code = refusal.get("error_code") if isinstance(refusal, dict) else None
    if not isinstance(code, str) or not _ERROR_CODE.fullmatch(code):
        raise ProjectionError("owner_projection_invalid", "owner refusal is malformed", 502)
    if refusal.get("schema_version") != OWNER_SCHEMA_VERSION:
        raise ProjectionError("owner_protocol_unsupported", "owner company assessment protocol is unsupported", 502)
    if code == "invalid_invocation":
        # An older command does not support the strict identity option.
        raise _owner_unavailable()
    if code in _IDENTITY_REFUSALS:
        raise ProjectionError(_IDENTITY_REFUSALS[code], "the owner identity store could not confirm registration", 503)
    raise ProjectionError(
        code, "the owner company assessment authority refused this read", _REFUSAL_STATUS.get(code, 502)
    )


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
    if any(type(owner[key]) is not int or owner[key] != 0 for key in ("network_calls", "llm_calls")):
        raise ProjectionError("owner_projection_invalid", "owner read reported unexpected I/O", 502)
    return owner


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
    entity_id = owner_payload["entity_id"]
    if any(item.get("entity_id", entity_id) != entity_id for item in items):
        raise ProjectionError("owner_projection_invalid", "owner history item names a different entity", 502)
    if len(items) > limit:
        raise ProjectionError("owner_projection_invalid", "owner history page exceeds the requested limit", 502)
    if (type(page.get("limit")) is not int or type(page.get("offset")) is not int
            or page["limit"] != limit or page["offset"] != offset):
        raise ProjectionError("owner_projection_invalid", "owner history page does not echo the request", 502)
    total = page.get("total")
    if type(total) is not int or total < 0:
        raise ProjectionError("owner_projection_invalid", "owner history total is malformed", 502)
    # A page beyond the end is VALID and must be an empty page: only a page
    # that actually carries rows beyond the reported total is malformed.
    if items and total < offset + len(items):
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
