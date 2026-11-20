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
    def __init__(self, lookup=None, applied=None, failure=None):
        self.lookup = lookup or {"status": "not_found"}
        self.applied = applied or _receipt()
        self.failure = failure
        self.calls = []

    def membership_request_read(self, payload):
        self.calls.append(("lookup", deepcopy(payload)))
        return deepcopy(self.lookup)

    def membership_request_apply(self, payload):
        self.calls.append(("apply", deepcopy(payload)))
        if self.failure:
            raise self.failure
        return deepcopy(self.applied)


def test_exact_same_key_replay_uses_owner_receipt_directly():
    owner = Owner(applied={**_receipt(), "idempotent_replay": True})

    result = apply_keyed_membership(owner, BASE)

    assert result["status"] == "replayed"
    assert result["request_id"] == "REQ_1"
    assert result["idempotent_replay"] is True
    assert [call[0] for call in owner.calls] == ["apply"]


def _historical_owner():
    canonical = {**_receipt()["canonical_payload"], "expected_member_version": 0,
                 "expected_identity_revision": 3}
    return Owner({"status": "found", "request": {
        "canonical_payload": canonical, "receipt": _receipt(canonical),
    }}, failure=DashboardOwnerError("idempotency_key_conflict", "conflict", 409))


def test_historical_replay_accepts_original_request_without_owner_added_preconditions():
    owner = _historical_owner()

    result = apply_keyed_membership(owner, BASE)

    assert result["idempotent_replay"] is True
    assert result["request_id"] == "REQ_1"
    assert result["canonical_payload"]["expected_identity_revision"] == 3
    assert [call[0] for call in owner.calls] == ["apply", "lookup"]


@pytest.mark.parametrize("change", [{"reason": "different"}, {"expected_member_version": 2}])
def test_same_key_cannot_replay_changed_semantics_or_explicit_versions(change):
    owner = _historical_owner()

    with pytest.raises(DashboardOwnerError) as error:
        apply_keyed_membership(owner, {**BASE, **change})

    assert error.value.code == "idempotency_key_conflict"
    assert error.value.status == 409
    assert [call[0] for call in owner.calls] == ["apply", "lookup"]


def test_new_receipt_with_different_canonical_version_keeps_conflict():
    canonical = {**_receipt()["canonical_payload"], "expected_member_version": 0}
    owner = Owner({"status": "found", "request": {
        "canonical_payload": canonical, "receipt": _receipt(canonical),
    }}, failure=DashboardOwnerError("idempotency_key_conflict", "conflict", 409))

    with pytest.raises(DashboardOwnerError) as error:
        apply_keyed_membership(owner, BASE)

    assert error.value.code == "idempotency_key_conflict"


@pytest.mark.parametrize("preview_token", [None, "stale-or-missing"])
def test_new_key_applies_with_caller_version_pins_and_no_preview_gate(preview_token):
    owner = Owner()
    request = {**BASE, "expected_member_version": 0, "preview_token": preview_token}

    result = apply_keyed_membership(owner, request)

    assert result["status"] == "applied"
    assert [call[0] for call in owner.calls] == ["apply"]
    applied = owner.calls[0][1]
    assert applied["idempotency_key"] == "REQ-1"
    assert applied["expected_member_version"] == 0
    assert applied["expected_identity_revision"] is None
    assert "preview_token" not in applied


def test_membership_conflict_preserves_atomic_owner_reason():
    owner = Owner(failure=DashboardOwnerError("member_version_conflict", "stale version", 409))

    with pytest.raises(DashboardOwnerError) as error:
        apply_keyed_membership(owner, {**BASE, "expected_member_version": 4})

    assert error.value.code == "member_version_conflict"
    assert [call[0] for call in owner.calls] == ["apply"]


def test_read_facade_requires_exactly_one_lookup_selector():
    owner = Owner()
    with pytest.raises(DashboardOwnerError) as error:
        membership_request_read(owner, {"universe_id": "TEST"})
    assert error.value.code == "invalid_payload"
    assert owner.calls == []
