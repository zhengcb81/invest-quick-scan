"""Public membership-request facade ordering and compatibility contract."""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.dashboard_membership_request import apply_keyed_membership, membership_request_read
from scripts.dashboard_owner import DashboardOwnerError


BASE = {
    "action": "add",
    "universe_id": "TEST",
    "entity_id": "ENT_TEST",
    "reason": "screening candidate",
    "priority": 0,
    "pin": False,
    "idempotency_key": "REQ-1",
    "expected_member_version": None,
    "expected_identity_revision": None,
    "preview_token": "preview-1",
}


def _receipt(payload=None):
    payload = payload or {key: value for key, value in BASE.items()
                          if key not in {"idempotency_key", "preview_token"}}
    return {
        "request_id": "REQ_1",
        "request_scope": "ws:TEST",
        "workspace_scope": "ws",
        "universe_id": "TEST",
        "idempotency_key": "REQ-1",
        "entity_id": "ENT_TEST",
        "action": "add",
        "payload_sha256": "abc",
        "canonical_payload": payload,
        "member_version": 1,
        "created_at": "2026-11-12T00:00:00Z",
        "member": {"entity_id": "ENT_TEST", "version": 1},
    }


class Owner:
    def __init__(self, lookup=None, preview=None, applied=None):
        self.lookup = lookup or {"status": "not_found"}
        self.preview = preview or {
            "status": "preview", "can_apply": True, "preview_token": "preview-1",
            "member": {"version": 0}, "entity": {"identity_revision": 3},
        }
        self.applied = applied or _receipt()
        self.calls = []

    def membership_request_read(self, payload):
        self.calls.append(("lookup", deepcopy(payload)))
        return deepcopy(self.lookup)

    def universe_preview(self, payload):
        self.calls.append(("preview", deepcopy(payload)))
        return deepcopy(self.preview)

    def membership_request_apply(self, payload):
        self.calls.append(("apply", deepcopy(payload)))
        return deepcopy(self.applied)


def test_exact_same_key_replay_precedes_preview_and_returns_stored_receipt():
    canonical = {key: value for key, value in BASE.items()
                 if key not in {"idempotency_key", "preview_token", "expected_member_version", "expected_identity_revision"}}
    receipt = _receipt(canonical)
    owner = Owner({"status": "found", "request": {"canonical_payload": canonical, "receipt": receipt}})
    request = {**BASE, "preview_token": "stale-or-missing"}

    result = apply_keyed_membership(owner, request)

    assert result["status"] == "replayed"
    assert result["request_id"] == "REQ_1"
    assert result["idempotent_replay"] is True
    assert [call[0] for call in owner.calls] == ["lookup"]


def test_different_payload_using_known_key_conflicts_before_preview():
    stored_payload = {key: value for key, value in BASE.items()
                      if key not in {"idempotency_key", "preview_token", "expected_member_version", "expected_identity_revision"}}
    owner = Owner({"status": "found", "request": {
        "canonical_payload": {**stored_payload, "reason": "different"},
        "receipt": _receipt({**stored_payload, "reason": "different"}),
    }})

    with pytest.raises(DashboardOwnerError) as error:
        apply_keyed_membership(owner, BASE)

    assert error.value.code == "idempotency_key_conflict"
    assert error.value.status == 409
    assert [call[0] for call in owner.calls] == ["lookup"]


def test_new_key_checks_preview_then_owner_applies_with_atomic_version_pins():
    owner = Owner()

    result = apply_keyed_membership(owner, BASE)

    assert result["status"] == "applied"
    assert [call[0] for call in owner.calls] == ["lookup", "preview", "apply"]
    applied = owner.calls[-1][1]
    assert applied["idempotency_key"] == "REQ-1"
    assert applied["expected_member_version"] == 0
    assert applied["expected_identity_revision"] == 3
    assert "preview_token" not in applied


def test_stale_preview_does_not_reach_membership_writer():
    owner = Owner(preview={"status": "preview", "can_apply": True,
                           "preview_token": "new-token", "member": {"version": 0},
                           "entity": {"identity_revision": 3}})

    with pytest.raises(DashboardOwnerError) as error:
        apply_keyed_membership(owner, BASE)

    assert error.value.code == "preview_stale"
    assert [call[0] for call in owner.calls] == ["lookup", "preview"]


def test_read_facade_requires_exactly_one_lookup_selector():
    owner = Owner()
    with pytest.raises(DashboardOwnerError) as error:
        membership_request_read(owner, {"universe_id": "TEST"})
    assert error.value.code == "invalid_payload"
    assert owner.calls == []
