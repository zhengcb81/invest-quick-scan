"""IQS consumer facade for StockWiki's public membership request protocol.

The facade owns no membership state and imports no StockWiki implementation.
It preserves the old preview/apply API while routing keyed writes through the
owner's durable request interface.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

if __package__:
    from .dashboard_owner import DashboardOwnerError, MEMBERSHIP_REQUEST_PROTOCOL
else:  # pragma: no cover - direct script import
    from dashboard_owner import DashboardOwnerError, MEMBERSHIP_REQUEST_PROTOCOL

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
_CANONICAL_FIELDS = (*_SEMANTIC_FIELDS, "expected_member_version", "expected_identity_revision")


def _fail(code: str, message: str, status: int = 400, details: dict | None = None):
    raise DashboardOwnerError(code, message, status, details)


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 200:
        _fail("invalid_payload", f"{field} must be a nonempty identifier of at most 200 characters")
    return value


def _version(value: Any, field: str, *, optional: bool = True) -> int | None:
    if value is None and optional:
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
    preview_token = payload.get("preview_token")
    if preview_token is not None and (not isinstance(preview_token, str) or len(preview_token) > 4096):
        _fail("invalid_payload", "preview_token must be bounded text")
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
        "preview_token": preview_token,
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


def apply_keyed_membership(owner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Lookup first, then confirm current preview, then ask owner to apply.

    Expected versions are captured from the owner's preview and enforced again
    inside the owner's atomic write transaction. Replays return the stored
    receipt before requiring a still-current preview token.
    """
    request = _request(payload)
    lookup = owner.membership_request_read({
        "universe_id": request["universe_id"], "idempotency_key": request["idempotency_key"]})
    if not isinstance(lookup, dict) or lookup.get("status") not in {"found", "not_found"}:
        _fail("owner_response_invalid", "StockWiki returned an invalid membership lookup", 502)
    if lookup["status"] == "found":
        stored = lookup.get("request")
        canonical = stored.get("canonical_payload") if isinstance(stored, dict) else None
        receipt = stored.get("receipt") if isinstance(stored, dict) else None
        if not isinstance(canonical, dict) or not isinstance(receipt, dict):
            _fail("owner_response_invalid", "StockWiki returned an incomplete membership request", 502)
        if any(canonical.get(field) != request[field] for field in _SEMANTIC_FIELDS):
            _fail("idempotency_key_conflict", "This key was already used for a different membership request", 409)
        for field in ("expected_member_version", "expected_identity_revision"):
            if request[field] is not None and canonical.get(field) != request[field]:
                _fail("idempotency_key_conflict", "This key was already used with different version preconditions", 409)
        return _response(receipt, "replayed")

    if not request["preview_token"]:
        _fail("preview_required", "Review the current membership preview before applying", 409)
    preview = owner.universe_preview({field: request[field] for field in _SEMANTIC_FIELDS})
    if not isinstance(preview, dict) or preview.get("status") != "preview":
        _fail("owner_response_invalid", "StockWiki returned an invalid membership preview", 502)
    if preview.get("preview_token") != request["preview_token"]:
        _fail("preview_stale", "Refresh and review the membership preview before applying", 409)
    if preview.get("can_apply") is not True:
        _fail("membership_state_conflict", "This action does not match current membership state", 409)
    member = preview.get("member")
    entity = preview.get("entity")
    if member is not None and not isinstance(member, dict):
        _fail("owner_response_invalid", "StockWiki returned an invalid member version", 502)
    if not isinstance(entity, dict):
        _fail("owner_response_invalid", "StockWiki preview did not include its identity revision", 502)
    member_version = _version(member.get("version", 0) if member else 0, "member.version", optional=False)
    identity_revision = _version(entity.get("identity_revision"), "entity.identity_revision", optional=False)
    for field, current in (("expected_member_version", member_version),
                           ("expected_identity_revision", identity_revision)):
        if request[field] is not None and request[field] != current:
            _fail("preview_stale", "Refresh and review the membership preview before applying", 409)

    wire = {field: request[field] for field in _CANONICAL_FIELDS}
    wire["idempotency_key"] = request["idempotency_key"]
    wire["expected_member_version"] = member_version
    wire["expected_identity_revision"] = identity_revision
    receipt = owner.membership_request_apply(wire)
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
