"""Independent negative/file-integrity/real disposable SQLite cases.

No successful owner double or native admission is constructed. Grant objects
below are deliberately invalid shape probes, not authority. All files are
owned disposable test artifacts; network is denied.
"""
import copy
import importlib.util
import os
import socket
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
CANDIDATE = BASE / "delegated-owner-candidate"
PROJECTS = BASE.parents[2]
sys.path[:0] = [str(PROJECTS / "StockQAbyLLM"), str(PROJECTS / "StockWiki")]
import src.utils
import stockwiki

src.utils.__path__.insert(0, str(CANDIDATE / "qa/src/utils"))
stockwiki.__path__.insert(0, str(CANDIDATE / "sw/stockwiki"))
from stockwiki.quick_scan_refresh_delegation import _safe_bytes, validate_grant
from stockwiki.quick_scan_import import canonical_sha256
from src.utils.quick_scan_work_store import QuickScanWorkStore
from src.utils.quick_scan_refresh_inspect import ReadOnlyWorkView
from tests.unit.test_quick_scan_budget import _policy, _reserve

spec = importlib.util.spec_from_file_location("independent_delegation_legacy_fixture",
    CANDIDATE / "qa/tests/c06_legacy_fixture.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("independent delegated review forbids network")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def bad_grant(fault):
    # Deliberately only used after invalidating one strict temporal/provenance
    # field. No service installs or admits this shape object.
    binding = dict(preview_id="rv1_" + "a" * 64, consumer_id="shape-only", store_id="shape-only",
        subject_refs=[], field_ids=[], items=[], anchors=[], provider="shape-only", model="shape-only",
        cohort_id=None, qa={}, quote={"max_cost_micros": 1, "max_http_requests": 1})
    for k in ["preview_record_sha256", "request_sha256", "scope_sha256", "owner_state_sha256",
              "policy_sha256", "budget_policy_sha256"]:
        binding[k] = "b" * 64
    grant = dict(protocol="stockwiki.refresh_delegation/1.0.0", owner_principal="shape-only",
        workspace_root="shape-only", agent=dict(profile_id="shape-only", profile_sha256="c" * 64,
        harness_ref="shape-only"), agent_assurance="local_owner_namespace",
        authorization_basis="recorded_user_authorization", authorization_reference="shape-only",
        binding=binding, created_at="2026-10-18T00:00:00Z", expires_at="2026-10-18T01:00:00Z")
    if fault == "over_24h":
        grant["expires_at"] = "2026-10-19T00:00:01Z"
    elif fault == "zero_validity":
        grant["expires_at"] = grant["created_at"]
    elif fault == "backwards":
        grant["expires_at"] = "2026-10-17T23:59:59Z"
    elif fault == "non_utc":
        grant["expires_at"] = "2026-10-18T01:00:00+00:00"
    elif fault == "agent_control_character":
        grant["agent"]["harness_ref"] = "shape-only\nclaimed"
    elif fault == "claimed_signature":
        grant["agent_assurance"] = "cryptographic_agent_signature"
    elif fault == "boolean_quote":
        grant["binding"]["quote"]["max_http_requests"] = True
    grant["grant_id"] = "dg1_" + canonical_sha256(dict(owner_principal=grant["owner_principal"],
        workspace_root=grant["workspace_root"], consumer_id=binding["consumer_id"],
        preview_id=binding["preview_id"]))
    grant["record_sha256"] = canonical_sha256(grant)
    return grant


@pytest.mark.parametrize("fault", ["over_24h", "zero_validity", "backwards", "non_utc",
    "agent_control_character", "claimed_signature", "boolean_quote"])
def test_resealed_invalid_scope_grant_never_passes_validator(fault):
    with pytest.raises(ValueError):
        validate_grant(bad_grant(fault))


def test_fixed_owner_file_hardlink_is_rejected_before_payload_parse(tmp_path):
    original, alias = tmp_path / "owner.json", tmp_path / "alias.json"
    original.write_bytes(b"not-a-valid-grant-and-must-not-be-parsed")
    os.link(original, alias)
    with pytest.raises(ValueError, match="regular_owner_file_required"):
        _safe_bytes(alias)
    assert original.read_bytes() == b"not-a-valid-grant-and-must-not-be-parsed"


def test_fixed_owner_file_mutation_during_read_is_rejected(tmp_path, monkeypatch):
    file = tmp_path / "fixed-owner.json"
    file.write_bytes(b"shape-only")
    real_open = Path.open

    class ChangedRead:
        def __init__(self, stream):
            self.stream = stream
        def fileno(self):
            return self.stream.fileno()
        def read(self, *args):
            raw = self.stream.read(*args)
            with real_open(file, "ab") as changed:
                changed.write(b"-changed")
            return raw

    @contextmanager
    def altered(path, *args, **kwargs):
        with real_open(path, *args, **kwargs) as stream:
            if args and args[0] == "rb" and os.path.samefile(path, file):
                yield ChangedRead(stream)
            else:
                yield stream
    monkeypatch.setattr(Path, "open", altered)
    with pytest.raises(ValueError, match="owner_file_changed"):
        _safe_bytes(file)


def test_v18_read_keeps_mixed_unknown_unpriced_and_active_reservations(tmp_path):
    store = QuickScanWorkStore(tmp_path / "mixed-native.sqlite")
    policy = _policy(max_cost_per_attempt=1)
    store.configure_quick_scan_budget(policy)
    _reserve(store, policy, "DISPATCH_unknown", "route-a1")
    _reserve(store, policy, "DISPATCH_unpriced", "route-a2")
    _reserve(store, policy, "DISPATCH_reserved", "route-b1")
    store.record_budget_outcome("DISPATCH_unknown", outcome="unknown", http_status_code=None)
    store.record_budget_outcome("DISPATCH_unpriced", outcome="response_available", http_status_code=200)
    prior = store.get_quick_scan_budget_status(policy["policy_id"])
    with sqlite3.connect(store.path) as connection:
        before_rows = connection.execute("SELECT * FROM quick_scan_budget_attempt ORDER BY budget_attempt_id").fetchall()
        legacy.remove_c06_additions(connection, after_version=18)
        connection.execute("PRAGMA user_version=18")
    frozen = store.path.read_bytes()
    status = ReadOnlyWorkView(store.path).get_quick_scan_budget_status(policy["policy_id"])
    for name in ["reserved_micros", "spent_micros", "requests", "in_flight", "unreconciled_attempts"]:
        assert status[name] == prior[name]
    assert status["requests"] == 3 and status["unreconciled_attempts"] == 2
    assert status["blocking_unreconciled_attempts"] == 2
    assert not status["cash_actual_complete"] and status["quota_accounted_attempts"] == 0
    assert store.path.read_bytes() == frozen
    with sqlite3.connect(store.path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT * FROM quick_scan_budget_attempt ORDER BY budget_attempt_id").fetchall() == before_rows
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 18
