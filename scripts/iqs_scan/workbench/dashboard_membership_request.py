"""IQS consumer facade for StockWiki's public membership request protocol.

The facade owns no membership state and imports no StockWiki implementation.
It preserves the old preview/apply API while routing keyed writes through the
owner's durable request interface.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .dashboard_owner import DashboardOwnerError, MEMBERSHIP_REQUEST_PROTOCOL

PROTOCOL = "iqs.dashboard.member_request/1.0.0"
OWNER_PROTOCOL = MEMBERSHIP_REQUEST_PROTOCOL
FACADE_PROTOCOL = "iqs.dashboard.owner/1.0.0"

_ACTIONS = frozenset({"add", "remove", "restore", "pin", "unpin"})
_FIELDS = frozenset({
    "action", "universe_id", "entity_id", "reason", "priority", "pin",
    "idempotency_key", "expected_member_version", "expected_identity_revision",
    "preview_token",
})
_SEMANTIC_FIELDS = ("action", "universe_id", "entity_id", "reason", "priority", "pin")
_VERSION_FIELDS = ("expected_member_version", "expected_identity_revision")


def _fail(code: str, message: str, status: int = 400, details: dict | None = None):
    raise DashboardOwnerError(code, message, status, details)


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 200:
        _fail("invalid_payload", f"{field} must be a nonempty identifier of at most 200 characters")
    return value


def _version(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail("invalid_payload", f"{field} must be a nonnegative integer")
    return value


def _request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _fail("invalid_payload", "Membership request must be an object")
    unknown = sorted(set(payload) - _FIELDS)
    if unknown:
        _fail("unknown_field", "Membership request contains unsupported fields", details={"fields": unknown})
    action = payload.get("action")
    if action not in _ACTIONS:
        _fail("invalid_payload", "Unsupported membership action")
    universe_id = _identifier(payload.get("universe_id"), "universe_id")
    entity_id = _identifier(payload.get("entity_id"), "entity_id")
    key = _identifier(payload.get("idempotency_key"), "idempotency_key")
    reason = payload.get("reason", "")
    if not isinstance(reason, str) or len(reason) > 2000:
        _fail("invalid_payload", "reason must be text of at most 2000 characters")
    reason = reason.strip()
    if action in {"add", "remove", "restore"} and not reason:
        _fail("invalid_payload", "A nonempty reason is required for this action")
    priority = payload.get("priority", 0)
    pin = payload.get("pin", False)
    if isinstance(priority, bool) or not isinstance(priority, int):
        _fail("invalid_payload", "priority must be an integer")
    if not isinstance(pin, bool):
        _fail("invalid_payload", "pin must be a boolean")
    expected_member_version = _version(payload.get("expected_member_version"), "expected_member_version")
    expected_identity_revision = _version(payload.get("expected_identity_revision"), "expected_identity_revision")
    return {
        "action": action,
        "universe_id": universe_id,
        "entity_id": entity_id,
        "reason": reason,
        "priority": priority,
        "pin": pin,
        "idempotency_key": key,
        "expected_member_version": expected_member_version,
        "expected_identity_revision": expected_identity_revision,
    }


def _semantic(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {field: payload[field] for field in _SEMANTIC_FIELDS}


def _response(receipt: Mapping[str, Any], status: str) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or not isinstance(receipt.get("request_id"), str):
        _fail("owner_response_invalid", "StockWiki returned an invalid membership receipt", 502)
    result = dict(receipt)
    result.update({
        "protocol": FACADE_PROTOCOL,
        "request_protocol": PROTOCOL,
        "owner_protocol": OWNER_PROTOCOL,
        "status": status,
        "idempotent_replay": status == "replayed",
        "network_calls": 0,
        "llm_calls": 0,
    })
    return result


def preview_keyed_membership(owner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Show the current state; the write authority checks the submitted request."""
    return owner.universe_preview(_semantic(_request(payload)))


def _previous_receipt(owner: Any, request: Mapping[str, Any]) -> Mapping[str, Any] | None:
    # Earlier IQS releases inserted preview-derived versions into the canonical
    # request. A caller retrying that request may omit those inferred values.
    lookup = owner.membership_request_read({
        "universe_id": request["universe_id"], "idempotency_key": request["idempotency_key"]})
    if lookup.get("status") != "found":
        return None
    stored = lookup["request"]
    canonical = stored.get("canonical_payload")
    receipt = stored.get("receipt")
    if not isinstance(canonical, dict) or not isinstance(receipt, dict):
        _fail("owner_response_invalid", "StockWiki returned an incomplete membership request", 502)
    if any(canonical.get(field) is None for field in _VERSION_FIELDS):
        return None
    if any(canonical.get(field) != request[field] for field in _SEMANTIC_FIELDS):
        return None
    if any(request[field] is not None and canonical.get(field) != request[field]
           for field in _VERSION_FIELDS):
        return None
    return receipt


def apply_keyed_membership(owner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Submit once to StockWiki's atomic request authority."""
    request = _request(payload)
    try:
        receipt = owner.membership_request_apply(request)
    except DashboardOwnerError as error:
        if error.code != "idempotency_key_conflict":
            raise
        previous = _previous_receipt(owner, request)
        if previous is None:
            raise
        return _response(previous, "replayed")
    return _response(receipt, "replayed" if receipt.get("idempotent_replay") else "applied")


def membership_request_read(owner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _fail("invalid_payload", "Membership lookup must be an object")
    allowed = {"universe_id", "idempotency_key", "request_id"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        _fail("unknown_field", "Membership lookup contains unsupported fields", details={"fields": unknown})
    request_id = payload.get("request_id")
    key = payload.get("idempotency_key")
    universe_id = payload.get("universe_id")
    if request_id is not None:
        request_id = _identifier(request_id, "request_id")
    if key is not None:
        key = _identifier(key, "idempotency_key")
    if universe_id is not None:
        universe_id = _identifier(universe_id, "universe_id")
    if request_id is None and (key is None or universe_id is None):
        _fail("invalid_payload", "Supply request_id or both universe_id and idempotency_key")
    result = owner.membership_request_read({
        key_name: value for key_name, value in {
            "request_id": request_id, "idempotency_key": key, "universe_id": universe_id}.items()
        if value is not None})
    if not isinstance(result, dict) or result.get("status") not in {"found", "not_found"}:
        _fail("owner_response_invalid", "StockWiki returned an invalid membership lookup", 502)
    return {**result, "protocol": PROTOCOL, "owner_protocol": OWNER_PROTOCOL,
            "network_calls": 0, "llm_calls": 0}


def membership_history(owner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _fail("invalid_payload", "Membership history request must be an object")
    allowed = {"universe_id", "entity_id", "limit", "after_version", "version_pin"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        _fail("unknown_field", "Membership history contains unsupported fields", details={"fields": unknown})
    request = {
        "universe_id": _identifier(payload.get("universe_id"), "universe_id"),
        "entity_id": _identifier(payload.get("entity_id"), "entity_id"),
        "limit": payload.get("limit", 50),
        "after_version": _version(payload.get("after_version"), "after_version"),
        "version_pin": _version(payload.get("version_pin"), "version_pin"),
    }
    if isinstance(request["limit"], bool) or not isinstance(request["limit"], int) or not 1 <= request["limit"] <= 200:
        _fail("invalid_payload", "limit must be between 1 and 200")
    result = owner.membership_history(request)
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        _fail("owner_response_invalid", "StockWiki returned invalid membership history", 502)
    return {**result, "protocol": PROTOCOL, "owner_protocol": OWNER_PROTOCOL,
            "network_calls": 0, "llm_calls": 0}
