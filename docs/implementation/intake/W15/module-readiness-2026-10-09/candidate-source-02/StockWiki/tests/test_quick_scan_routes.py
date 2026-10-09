"""W15 durable route/subject anchors in isolated SQLite, synthetic unit inputs.

Producer validation is the external boundary in these storage-only cases;
actual IQS CLI interoperability belongs to the concentrated package E2E.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import uuid

import pytest

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_analysis import AnalysisSubjectStore, perimeter_sha256, receipt_key
from stockwiki.quick_scan_store import QuickScanStore


def _workspace(tmp_path, *, segments=()):
    paths = WorkspacePaths.from_root(tmp_path)
    identity = QuickScanStore(paths)
    identity.migrate()
    issuer = "ENT_" + str(uuid.uuid4())
    security = "SEC_" + uuid.uuid4().hex
    binding = "BND_" + uuid.uuid4().hex
    identity.save_entity(
        {
            "entity_id": issuer,
            "identity_schema_version": "2.0.0",
            "identity_state": "verified",
            "identity_revision": 1,
            "canonical_name": "Synthetic W15 issuer",
            "incorporation_country": "US",
            "scope_attestation_id": "ATT_UNIT_ONLY",
            "verified_issuer_receipt_id": "IVR_UNIT_ONLY",
            "company_wiki_ref": None,
            "formal_stockwiki_profile": None,
            "segments": list(segments),
            "securities": [
                {
                    "security_id": security,
                    "entity_id": issuer,
                    "market": "US",
                    "exchange_raw": "NASDAQ",
                    "exchange": "XNAS",
                    "ticker": "TEST",
                    "currency": "USD",
                    "security_type": "ordinary",
                    "listing_status": "active",
                    "source_binding_ref": binding,
                    "adr_ratio": None,
                    "ordinary_security_ref": None,
                }
            ],
        },
        source_bindings=[
            {
                "binding_ref": binding,
                "source_namespace": "synthetic-w15",
                "source_record_id": issuer,
                "source_canonical_name": "Synthetic W15 issuer",
                "security_id": security,
                "entity_id": issuer,
                "market": "US",
                "exchange_raw": "NASDAQ",
                "ticker": "TEST",
                "status": "active",
            }
        ],
    )
    subjects = AnalysisSubjectStore(paths)
    subjects.migrate()
    # All evidence is synthetic; this fixture is not a real owner golden.
    subject = {
        "analysis_subject_schema_version": "1.0.0",
        "analysis_subject_id": "ASJ_" + str(uuid.uuid4()),
        "analysis_subject_revision": 1,
        "display_name": "Synthetic W15 reporting group",
        "primary_issuer_id": issuer,
        "anchor_listing_id": None,
        "scope_kind": "consolidated_reporting_group",
        "scope_as_of": "2025-12-31T00:00:00Z",
        "perimeter_coverage": "not_enumerated",
        "memberships": [
            {
                "entity_id": issuer,
                "role": "primary_issuer",
                "valid_from": None,
                "valid_to": None,
                "evidence_ref": "https://example.invalid/w15",
            }
        ],
    }
    receipt = {
        "receipt_id": "PRC_UNIT_ONLY",
        "status": "verified",
        "analysis_subject_id": subject["analysis_subject_id"],
        "analysis_subject_revision": 1,
        "primary_issuer_id": issuer,
        "evidence_ref": "https://example.invalid/w15",
        "perimeter_sha256": perimeter_sha256(subject),
        "decision_ref": "unit-test-only",
    }
    subjects.import_subject(identity, {"analysis_subject": subject, "perimeter_receipt": receipt})
    return identity, subject


def _raw(identity, subject, *, confidence=True, tag="one"):
    route = {
        "schema_version": "2.0.0",
        "decision_id": "route_" + hashlib.sha256(tag.encode()).hexdigest(),
        "entity_id": subject["primary_issuer_id"],
        "scope": "entity",
        "segment_id": None,
        "identity_ref": _routes(identity).identity_binding(receipt_key(subject))[
            "route_identity_ref"
        ],
        "router_version": "2.2.0" if confidence else "2.1.0",
        "as_of": "2025-12-31",
        "decided_at": "2026-01-01T12:00:00Z",
        "execution": None,
    }
    if confidence:
        route["classification_confidence"] = dict(
            status="scored", score=8, minimum_score=7, llm_candidates_eligible=True
        )
    manifest = {"route_decision": route, "route_decision_id": route["decision_id"], "questions": []}
    return json.dumps(route).encode() + b"\r\n", json.dumps(manifest).encode() + b"\n"


class UnitValidator:
    """A typed external boundary substitute, not a producer/authenticity claim."""

    def validate(self, route_raw, manifest_raw, *, expected_decision_id, **kwargs):
        route = json.loads(route_raw)
        if route["decision_id"] != expected_decision_id:
            raise ValueError("route_anchor_mismatch")
        return {
            "protocol": "iqs.route_store_validation/1.0.0",
            "status": "validated",
            "expected_decision_id": expected_decision_id,
            "route_raw_sha256": hashlib.sha256(route_raw).hexdigest(),
            "manifest_raw_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "validation_mode": kwargs.get("validation_mode", "history"),
        }


def _routes(identity):
    from stockwiki.quick_scan_routes import QuickScanRouteStore

    return QuickScanRouteStore(identity, validator=UnitValidator())


def test_route_schema6_adds_tables_without_rewriting_identity(tmp_path):
    identity, subject = _workspace(tmp_path)
    assert identity.migrate() == 6
    with sqlite3.connect(identity.database_path) as con:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"quick_scan_route_snapshot", "quick_scan_route_current"} <= tables
    assert identity.get_entity(subject["primary_issuer_id"])["identity_state"] == "verified"


@pytest.mark.parametrize("confidence", [True, False])
def test_classification_raw_and_subject_binding_survive_storage(tmp_path, confidence):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    raw, manifest = _raw(identity, subject, confidence=confidence)
    expected = json.loads(raw)["decision_id"]
    accepted = routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=expected
    )
    assert accepted["status"] == "recorded"
    got = routes.get_snapshot(expected)
    assert got["route_raw"] == raw and got["manifest_raw"] == manifest
    assert got["subject_key"] == receipt_key(subject)
    assert got["perimeter_sha256"] == perimeter_sha256(subject)
    assert ("classification_confidence" in json.loads(got["route_raw"])) is confidence
    assert (
        routes.record_snapshot(
            raw, manifest, subject_key=receipt_key(subject), expected_decision_id=expected
        )["status"]
        == "replayed"
    )


def test_independent_current_anchor_rejects_resealed_candidate_and_stale_cas(tmp_path):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    raw, manifest = _raw(identity, subject)
    expected = json.loads(raw)["decision_id"]
    routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=expected
    )
    routes.set_current(
        expected,
        subject_key=receipt_key(subject),
        expected_current_decision_id=None,
        now_utc="2026-01-02T12:00:00Z",
    )
    altered = copy.deepcopy(json.loads(raw))
    altered["decision_id"] = "route_" + "f" * 64
    with pytest.raises(ValueError, match="route_anchor_mismatch"):
        routes.get_for_execution(
            subject_key=receipt_key(subject),
            scope="entity",
            scope_id=subject["primary_issuer_id"],
            now_utc="2026-01-03T12:00:00Z",
            candidate_route=json.dumps(altered).encode(),
        )
    with pytest.raises(ValueError, match="route_current_conflict"):
        routes.set_current(
            expected,
            subject_key=receipt_key(subject),
            expected_current_decision_id="route_" + "e" * 64,
            now_utc="2026-01-03T12:00:00Z",
        )
    execution = routes.get_for_execution(
        subject_key=receipt_key(subject),
        scope="entity",
        scope_id=subject["primary_issuer_id"],
        now_utc="2026-01-03T12:00:00Z",
    )
    assert execution["expected_decision_id"] == expected
    with pytest.raises(ValueError, match="route_time_before_activation"):
        routes.get_for_execution(
            subject_key=receipt_key(subject),
            scope="entity",
            scope_id=subject["primary_issuer_id"],
            now_utc="2026-01-01T12:00:00Z",
        )


def test_changed_snapshot_bytes_are_named_refusal_not_history_rewrite(tmp_path):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    raw, manifest = _raw(identity, subject)
    expected = json.loads(raw)["decision_id"]
    routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=expected
    )
    with sqlite3.connect(identity.database_path) as con:
        con.execute(
            "UPDATE quick_scan_route_snapshot SET route_raw=? WHERE decision_id=?",
            (raw + b" ", expected),
        )
    with pytest.raises(ValueError, match="route_snapshot_corrupted"):
        routes.get_snapshot(expected)


def test_subject_perimeter_and_identity_ref_cannot_be_selected_by_route(tmp_path):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    raw, manifest = _raw(identity, subject)
    original = json.loads(raw)
    changed = copy.deepcopy(original)
    changed["identity_ref"] = "self-reported-and-not-owner-bound"
    manifest_obj = json.loads(manifest)
    manifest_obj["route_decision"] = changed
    with pytest.raises(ValueError, match="route_subject_binding_mismatch"):
        routes.record_snapshot(
            json.dumps(changed).encode(),
            json.dumps(manifest_obj).encode(),
            subject_key=receipt_key(subject),
            expected_decision_id=changed["decision_id"],
        )
    assert routes.get_snapshot(original["decision_id"]) is None


def test_migration_rolls_back_route_tables_and_preserves_v5_data(tmp_path, monkeypatch):
    from stockwiki import quick_scan_schema

    identity, subject = _workspace(tmp_path)
    with sqlite3.connect(identity.database_path) as con:
        con.execute("DROP TABLE quick_scan_route_current_history")
        con.execute("DROP TABLE quick_scan_route_current")
        con.execute("DROP TABLE quick_scan_route_snapshot")
        con.execute("PRAGMA user_version=5")
    real = quick_scan_schema.apply_v6

    def broken(con):
        real(con)
        raise RuntimeError("injected-migration-failure")

    monkeypatch.setattr(quick_scan_schema, "apply_v6", broken)
    with pytest.raises(Exception, match="injected-migration-failure"):
        identity.migrate()
    with sqlite3.connect(identity.database_path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 5
        assert (
            con.execute(
                "SELECT count(*) FROM sqlite_master WHERE name='quick_scan_route_snapshot'"
            ).fetchone()[0]
            == 0
        )
    assert identity.get_entity(subject["primary_issuer_id"])["identity_state"] == "verified"


def test_distinct_subjects_and_revisions_do_not_share_current_or_route_binding(tmp_path):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    raw, manifest = _raw(identity, subject)
    decision_id = json.loads(raw)["decision_id"]
    second = copy.deepcopy(subject)
    second["analysis_subject_id"] = "ASJ_" + str(uuid.uuid4())
    receipt = copy.deepcopy(routes.identity_binding(receipt_key(subject))["perimeter_receipt"])
    receipt.update(
        analysis_subject_id=second["analysis_subject_id"], perimeter_sha256=perimeter_sha256(second)
    )
    routes.subjects.import_subject(
        identity, {"analysis_subject": second, "perimeter_receipt": receipt}
    )
    with pytest.raises(ValueError, match="route_subject_binding_mismatch"):
        routes.record_snapshot(
            raw, manifest, subject_key=receipt_key(second), expected_decision_id=decision_id
        )
    routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=decision_id
    )
    routes.set_current(
        decision_id,
        subject_key=receipt_key(subject),
        expected_current_decision_id=None,
        now_utc="2026-01-02T12:00:00Z",
    )
    with pytest.raises(ValueError, match="route_current_unavailable"):
        routes.get_for_execution(
            subject_key=receipt_key(second),
            scope="entity",
            scope_id=subject["primary_issuer_id"],
            now_utc="2026-01-03T12:00:00Z",
        )


def test_concurrent_cas_uses_two_real_sqlite_writers(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    decisions = []
    for tag in ("first", "second"):
        raw, manifest = _raw(identity, subject, tag=tag)
        decision_id = json.loads(raw)["decision_id"]
        decisions.append(decision_id)
        routes.record_snapshot(
            raw, manifest, subject_key=receipt_key(subject), expected_decision_id=decision_id
        )

    def activate(decision_id):
        try:
            return _routes(identity).set_current(
                decision_id,
                subject_key=receipt_key(subject),
                expected_current_decision_id=None,
                now_utc="2026-01-02T12:00:00Z",
            )["status"]
        except ValueError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(activate, decisions))
    assert sorted(outcomes) == ["activated", "route_current_conflict"]
    with sqlite3.connect(identity.database_path) as con:
        assert (
            con.execute("SELECT count(*) FROM quick_scan_route_current_history").fetchone()[0] == 1
        )
