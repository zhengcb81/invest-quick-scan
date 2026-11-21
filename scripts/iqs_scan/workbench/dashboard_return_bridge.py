"""Cross-workspace return mapping verification (CROSS-ID-DASHBOARD-RETURN).

The Dashboard may hand this owner an absolute loopback company return that
names ITS business entity, while this owner composes the link for its own
r25 research entity. The two workspaces mint different identifiers for the
same issuer+listing, so entity-ID equality cannot authenticate that return
and the B03 cross-scope rule collapses it. What CAN authenticate it is the
identity the StockWiki owner publishes: both workspaces must resolve the two
entities to the SAME issuer coordinates and listing credentials, both
verified and actively listed. Only then is the original business return
address confirmed; every other outcome keeps the readable result untouched
and degrades the return hop alone.

This module is deliberately narrow: read-only ``resolve`` calls against the
public ``dashboard_identity_bridge_cli.py`` of the configured StockWiki
release, one per workspace, then a strict comparison. It reads no database
itself, performs no writes, caches nothing and never takes a path from
request JSON - workspace roots come from deployment config only, and the
entity/listing ids handed over are the same bounded identifiers the link
boundary already accepts. A research subject (`analysis_subject_id`) riding
on the return URL is the Dashboard's own scope key: it is kept verbatim and
is not part of the issuer identity check.
"""

from __future__ import annotations

import subprocess
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .dashboard_owner import TIMEOUT_SECONDS_MAX, _MAX_BYTES, _env, valid_timeout_seconds
from .dashboard_json import decode_owner_json
from .dashboard_iqs_link import safe_entity_id

BRIDGE_CLI = "dashboard_identity_bridge_cli.py"
BRIDGE_SCHEMA = "stockwiki.dashboard_identity/1"

# The named degradation reasons. Every refusal keeps the entity payload,
# history and observations readable; only the return hop is downgraded, and
# the reason travels in operator evidence, never into the frozen IQSLink
# (which is `additionalProperties: false`).
REASON_NOT_CONFIGURED = "return_bridge_not_configured"
REASON_UNAVAILABLE = "return_bridge_unavailable"
REASON_R25_UNRESOLVED = "r25_identity_unresolved"
REASON_R25_UNVERIFIED = "r25_identity_unverified"
REASON_R25_NO_ACTIVE_LISTING = "r25_active_listing_missing"
REASON_BUSINESS_UNRESOLVED = "business_identity_unresolved"
REASON_BUSINESS_UNVERIFIED = "business_identity_unverified"
REASON_BUSINESS_LISTING_UNSELECTED = "business_listing_unselected"
REASON_COORDINATES_MISMATCH = "listing_coordinates_mismatch"
REASON_NAME_MISMATCH = "issuer_name_mismatch"


def parse_return_scope(return_to):
    """The business scope named by an absolute company return URL, else None.

    Only meaningful on a value that already passed `safe_return_to`'s absolute
    form: exact loopback authority, exact `/company/...` route, bounded query
    keys. This re-derives the scope independently so the verifier never trusts
    a parsed representation from another layer.
    """
    if not isinstance(return_to, str):
        return None
    parsed = urlsplit(return_to)
    segments = parsed.path.split("/")
    # /company/<ENT>[/<tab>]: the entity segment is index 2.
    if len(segments) < 3 or segments[0] or segments[1] != "company":
        return None
    entity_id = safe_entity_id(segments[2])
    if not entity_id:
        return None
    listing_id = subject_id = None
    query = parse_qs(parsed.query, keep_blank_values=True)
    values = query.get("listing_id")
    if values:
        listing_id = safe_entity_id(values[-1]) or None
    values = query.get("analysis_subject_id")
    if values:
        subject_id = safe_entity_id(values[-1]) or None
    return {"entity_id": entity_id, "listing_id": listing_id, "analysis_subject_id": subject_id}


def _listing_coordinates(listing):
    """The comparable identity of one listing row, or None when incomplete."""
    if not isinstance(listing, dict):
        return None
    fields = tuple(listing.get(key) for key in ("market", "exchange_mic", "ticker", "currency"))
    if any(not isinstance(field, str) or not field for field in fields):
        return None
    return fields


def _active_coordinates(entity):
    """{(market, exchange_mic, ticker, currency): listing_id} for active listings."""
    coordinates = {}
    listings = entity.get("listings") if isinstance(entity, dict) else None
    if isinstance(listings, list):
        for listing in listings:
            if not isinstance(listing, dict) or listing.get("listing_status") != "active":
                continue
            keys = _listing_coordinates(listing)
            if keys is not None:
                coordinates[keys] = listing.get("listing_id")
    return coordinates


def _canonical_name(entity):
    name = entity.get("canonical_name") if isinstance(entity, dict) else None
    return unicodedata.normalize("NFKC", name) if isinstance(name, str) and name else None


def _identity_state(entity):
    state = entity.get("identity_state") if isinstance(entity, dict) else None
    return state if isinstance(state, str) else None


def _resolved_entity(reply, reason_unresolved):
    """The verified entity payload of one bridge resolve reply, else (None, reason)."""
    if not isinstance(reply, dict) or reply.get("resolution_status") != "resolved":
        return None, reason_unresolved
    entity = reply.get("entity")
    if not isinstance(entity, dict):
        return None, reason_unresolved
    if _identity_state(entity) != "verified":
        return None, (REASON_R25_UNVERIFIED if reason_unresolved == REASON_R25_UNRESOLVED
                      else REASON_BUSINESS_UNVERIFIED)
    return entity, None


class ReturnBridge:
    """Read-only dual-workspace identity verifier for cross-ID company returns."""

    def __init__(self, config, runner=None):
        if not isinstance(config, dict):
            raise ValueError("return bridge config must be an object")
        self.config = dict(config)
        self._runner = runner or subprocess.run

    # -- one workspace resolve ------------------------------------------------

    def _resolve(self, workspace_root, entity_id, listing_id=None):
        """One public bridge resolve; (reply, error_code). Never raises."""
        config = self.config
        code_root = Path(config["stockwiki_root"])
        cli = code_root / BRIDGE_CLI
        if not cli.is_file():
            return None, "bridge_cli_missing"
        executable = Path(config["stockwiki_python"])
        if not executable.is_file():
            return None, "bridge_python_missing"
        timeout = config.get("timeout_seconds", 30)
        if not valid_timeout_seconds(timeout):
            timeout = 30
        timeout = min(float(timeout), float(TIMEOUT_SECONDS_MAX))
        command = [str(executable), "-B", "-X", "utf8", str(cli), "resolve",
                   "--entity-id", entity_id, "--root", str(workspace_root)]
        if listing_id:
            command.extend(("--listing-id", listing_id))
        try:
            result = self._runner(command, cwd=str(code_root), capture_output=True,
                                  text=True, encoding="utf-8", errors="strict",
                                  timeout=timeout, env=_env())
        except subprocess.TimeoutExpired:
            return None, "bridge_timeout"
        except (OSError, ValueError, UnicodeError):
            return None, "bridge_process_unavailable"
        if len(result.stdout.encode("utf-8", "replace")) > _MAX_BYTES:
            return None, "bridge_response_too_large"
        if result.returncode != 0:
            return None, "bridge_refused"
        try:
            reply = decode_owner_json(result.stdout)
        except ValueError:
            return None, "bridge_response_invalid"
        if not isinstance(reply, dict) or reply.get("schema_version") != BRIDGE_SCHEMA:
            return None, "bridge_response_invalid"
        return reply, None

    # -- the mapping check ----------------------------------------------------

    def verify(self, r25_entity_id, return_to):
        """Confirm `return_to` names the same issuer+listing as `r25_entity_id`.

        Returns ``{"confirmed": bool, "reason": str|None, "detail": {...}}`` and
        never raises: every non-confirmation keeps the readable payload intact
        and only degrades the return hop.
        """
        detail: dict = {}
        config = self.config
        business_root = config.get("return_bridge_workspace_root")
        owner_root = config.get("workspace_root")
        if (not isinstance(business_root, str) or not business_root
                or not isinstance(owner_root, str) or not owner_root
                or not config.get("stockwiki_root") or not config.get("stockwiki_python")):
            return {"confirmed": False, "reason": REASON_NOT_CONFIGURED, "detail": detail}
        scope = parse_return_scope(return_to)
        if scope is None:
            return {"confirmed": False, "reason": REASON_BUSINESS_UNRESOLVED, "detail": detail}
        detail.update({"business_entity_id": scope["entity_id"],
                       "business_listing_id": scope["listing_id"],
                       "analysis_subject_id": scope["analysis_subject_id"]})
        # Side 1 - this owner's r25 workspace: the entity the link composes.
        reply, error = self._resolve(owner_root, r25_entity_id)
        if error is not None:
            return {"confirmed": False, "reason": REASON_UNAVAILABLE, "detail": {**detail, "bridge_error": error}}
        r25_entity, reason = _resolved_entity(reply, REASON_R25_UNRESOLVED)
        if r25_entity is None:
            return {"confirmed": False, "reason": reason, "detail": detail}
        r25_coordinates = _active_coordinates(r25_entity)
        if not r25_coordinates:
            return {"confirmed": False, "reason": REASON_R25_NO_ACTIVE_LISTING, "detail": detail}
        detail["r25_entity_id"] = r25_entity_id
        detail["r25_listing_ids"] = sorted(str(value) for value in r25_coordinates.values() if value)
        detail["r25_lookup_receipt_sha256"] = reply.get("lookup_receipt_sha256")
        # Side 2 - the Dashboard's business workspace: the entity/listing the
        # return address names. An explicit listing_id must be the selected one.
        reply, error = self._resolve(business_root, scope["entity_id"], scope["listing_id"])
        if error is not None:
            return {"confirmed": False, "reason": REASON_UNAVAILABLE, "detail": {**detail, "bridge_error": error}}
        business_entity, reason = _resolved_entity(reply, REASON_BUSINESS_UNRESOLVED)
        if business_entity is None:
            return {"confirmed": False, "reason": reason, "detail": detail}
        if scope["listing_id"]:
            if reply.get("listing_scope") != "explicit_listing_selected" or reply.get(
                    "selected_listing_id") != scope["listing_id"]:
                return {"confirmed": False, "reason": REASON_BUSINESS_LISTING_UNSELECTED, "detail": detail}
        business_coordinates = _active_coordinates(business_entity)
        selected = (reply.get("selected_listing_id") if isinstance(reply, dict) else None)
        selected_keys = [keys for keys, listing in business_coordinates.items()
                         if listing is not None and listing == selected] if selected else []
        if not selected_keys:
            return {"confirmed": False, "reason": REASON_BUSINESS_LISTING_UNSELECTED, "detail": detail}
        detail["business_lookup_receipt_sha256"] = reply.get("lookup_receipt_sha256")
        # Same issuer+listing: one active business listing must carry exactly
        # the coordinates of one active r25 listing, under the same NFKC name.
        matched = next((keys for keys in selected_keys if keys in r25_coordinates), None)
        if matched is None:
            return {"confirmed": False, "reason": REASON_COORDINATES_MISMATCH, "detail": detail}
        if _canonical_name(r25_entity) != _canonical_name(business_entity) or _canonical_name(r25_entity) is None:
            return {"confirmed": False, "reason": REASON_NAME_MISMATCH, "detail": detail}
        detail["confirmed_listing_coordinates"] = list(matched)
        detail["r25_listing_id"] = r25_coordinates[matched]
        return {"confirmed": True, "reason": None, "detail": detail}
