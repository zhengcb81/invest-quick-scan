"""W10 delivery/ACK projection tests.

Binds acceptance cases JOB-07, JOB-08, PAR-06 (plus read-side re-checks of
DB-02/DB-03) to real selectors. Fixtures are built through the REAL W05
transactional write path (`apply_decisions`), never by mocking the ledger;
every test runs under a socket bomb because recovery must never call an LLM.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_delivery import (
    DeliveryProjectionError,
    ack_status,
    apply_delivery_transition,
    project_runtime_status,
    reconcile_delivery,
    validate_ack,
)
from stockwiki.quick_scan_observations import QuickScanObservationStore


def _no_network(monkeypatch) -> None:
    def _bomb(*args, **kwargs):
        raise AssertionError("network call attempted from delivery projection")

    monkeypatch.setattr(socket, "socket", _bomb)
    monkeypatch.setattr(socket, "create_connection", _bomb)


def _observation(obs_id: str, entity_id: str = "ENT_A") -> dict:
    return {
        "observation_id": obs_id,
        "entity_id": entity_id,
        "security_id": None,
        "listing_id": None,
        "segment_id": None,
        "source_binding_ref": None,
        "identity_revision": 1,
        "analysis_subject": None,
        "field_id": "score.iqs_05",
        "question_id": "IQS_05",
        "scope": "entity",
        "observed_at": "2026-10-03T09:00:00Z",
        "information_cutoff": "2026-09-01",
        "answer": {"status": "scored", "score": 7},
    }


def _decision(
    item_id: str,
    obs_id: str,
    payload_sha: str,
    *,
    status: str = "accepted",
    entity_id: str = "ENT_A",
    package_id: str = "pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
) -> dict:
    return {
        "package_id": package_id,
        "item_id": item_id,
        "observation_id": obs_id,
        "payload_sha256": payload_sha,
        "exec_key": f"exec_{item_id}",
        "status": status,
        "error_code": None if status == "accepted" else "rejected_by_fixture",
        "observation": _observation(obs_id, entity_id),
    }


def _store(tmp_path: Path) -> QuickScanObservationStore:
    store = QuickScanObservationStore(WorkspacePaths.from_root(tmp_path))
    store.migrate()
    return store


def _seed_loop(store: QuickScanObservationStore) -> tuple[str, str]:
    """Land one accepted item through the real transactional path."""
    item_id = "itm_8eb12ba77c9e16c038840efad756492de09bdb3aa01e3533ddc6d0eb444d217a"
    payload_sha = "a" * 64
    acks = store.apply_decisions(
        [
            _decision(
                item_id,
                "obs_b272796b8cc0d26970fa8bfd9dfddcbb53ce2336e2d825daf76d9a689575b0a0",
                payload_sha,
            )
        ],
        identity_lookup=None,
    )
    assert acks[0]["status"] == "accepted"
    return item_id, payload_sha


def test_job_07_unknown_send_never_becomes_acked_without_receipt(tmp_path, monkeypatch) -> None:
    """JOB-07: unknown send stays unknown; a real ACK advances it once, idempotently."""
    _no_network(monkeypatch)
    store = _store(tmp_path)
    item_id, payload_sha = _seed_loop(store)

    # JOB-07 recovery: caller has no ACK in hand, so the exact receipt in the
    # ledger is consumed first -> sent_unknown advances to acked, settling once
    no_ack = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="sent_unknown",
        incoming_ack=None,
    )
    assert no_ack["state"] == "acked"
    assert no_ack["ack_found_in_ledger"] is True
    assert no_ack["incoming_ack_accepted"] is False
    assert no_ack["settled_once"] is True
    assert no_ack["llm_calls"] == 0

    # replaying the same situation yields the same state (idempotent)
    again = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="acked",
        incoming_ack=None,
    )
    assert again["state"] == "acked"
    assert again["llm_calls"] == 0 and again["network_calls"] == 0

    # a genuinely missing receipt keeps the unknown state
    unseen = reconcile_delivery(
        store,
        package_id="pkg_3b77c99ab9ae36ccb2103991d09adcb9e664aa493f83ead3cf8164a71bf97ea0",
        item_id="itm_ac8913dba9b986e0d2c0ee89006f6954857addc1276d015cb5df16b76ee895c2",
        expected_payload_sha256="b" * 64,
        current="sent_unknown",
        incoming_ack=None,
    )
    assert unseen["state"] == "sent_unknown"
    assert unseen["ack_found_in_ledger"] is False
    assert unseen["settled_once"] is False


def test_job_08_mismatched_ack_and_illegal_transitions_refused(tmp_path, monkeypatch) -> None:
    """JOB-08: wrong item/hash ACK rejected; illegal jumps refused; no fake delivered."""
    _no_network(monkeypatch)
    store = _store(tmp_path)
    item_id, payload_sha = _seed_loop(store)
    ledger = ack_status(
        store, package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33"
    )
    good_ack = ledger["receipts"][0]["ack"]

    validated = validate_ack(
        good_ack, expected_item_id=item_id, expected_payload_sha256=payload_sha
    )
    assert validated["status"] == "accepted"

    with pytest.raises(DeliveryProjectionError) as exc:
        validate_ack(
            good_ack,
            expected_item_id="itm_5bc615141fcd2eee0004969c31884cff61982f007cfead1659a0ba0aeca6b576",
            expected_payload_sha256=payload_sha,
        )
    assert exc.value.error_code == "ack_item_mismatch"

    with pytest.raises(DeliveryProjectionError) as exc:
        validate_ack(good_ack, expected_item_id=item_id, expected_payload_sha256="c" * 64)
    assert exc.value.error_code == "ack_payload_hash_mismatch"

    bad_status = dict(good_ack, status="made_up")
    with pytest.raises(DeliveryProjectionError) as exc:
        validate_ack(bad_status, expected_item_id=item_id, expected_payload_sha256=payload_sha)
    assert exc.value.error_code == "ack_status_invalid"

    with pytest.raises(DeliveryProjectionError) as exc:
        validate_ack(
            {"item_id": "", "payload_sha256": "", "status": ""},
            expected_item_id="x",
            expected_payload_sha256="y",
        )
    assert exc.value.error_code == "ack_shape"

    # illegal state jumps are refused, never coerced
    with pytest.raises(DeliveryProjectionError) as exc:
        apply_delivery_transition("pending", "acked", has_ack=True)
    assert exc.value.error_code == "delivery_transition_illegal"
    with pytest.raises(DeliveryProjectionError) as exc:
        apply_delivery_transition("pending", "delivered", has_ack=False)
    assert exc.value.error_code == "delivery_transition_illegal"
    with pytest.raises(DeliveryProjectionError) as exc:
        apply_delivery_transition("failed", "acked", has_ack=True)
    assert exc.value.error_code == "delivery_transition_illegal"
    with pytest.raises(DeliveryProjectionError) as exc:
        apply_delivery_transition("sent_unknown", "acked", has_ack=False)
    assert exc.value.error_code == "delivery_ack_required"
    with pytest.raises(DeliveryProjectionError) as exc:
        apply_delivery_transition("pending", "teleported", has_ack=True)
    assert exc.value.error_code == "delivery_state_invalid"

    # a mismatched late ACK is refused outright: state held, reason named
    stuck = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="sent_unknown",
        incoming_ack=dict(
            good_ack, item_id="itm_5bc615141fcd2eee0004969c31884cff61982f007cfead1659a0ba0aeca6b576"
        ),
    )
    assert stuck["state"] == "sent_unknown"
    assert stuck["incoming_ack_accepted"] is False
    assert stuck["incoming_ack_error"] == "ack_item_mismatch"
    assert stuck["settled_once"] is False

    # error receipts stay errors (never masquerade as delivered)
    store.apply_decisions(
        [
            _decision(
                "itm_2152bd4f36cd140893609ff8d41c7657abd563c1aae54fa894fd1999cff40508",
                "obs_6e9fed04cedf18764e56a11b04c1bcacca9520b1651579350dc2df2490eb976a",
                "d" * 64,
                status="rejected",
            )
        ],
        identity_lookup=None,
    )
    err = ack_status(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id="itm_2152bd4f36cd140893609ff8d41c7657abd563c1aae54fa894fd1999cff40508",
    )
    assert err["count"] == 1
    assert err["error_receipts"] == 1
    assert err["receipts"][0]["status"] == "rejected"
    assert err["receipts"][0]["error_code"] == "rejected_by_fixture"
    assert err["llm_calls"] == 0


def test_par_06_late_ack_settles_once_and_replay_is_import_only(tmp_path, monkeypatch) -> None:
    """PAR-06: late valid receipt settles the unknown result exactly once, no LLM."""
    _no_network(monkeypatch)
    store = _store(tmp_path)
    item_id, payload_sha = _seed_loop(store)
    ledger = ack_status(
        store, package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33"
    )
    late_ack = ledger["receipts"][0]["ack"]

    first = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="sent_unknown",
        incoming_ack=late_ack,
    )
    assert first["state"] == "acked"
    assert first["incoming_ack_accepted"] is True
    assert first["settled_once"] is True
    assert first["llm_calls"] == 0

    # an identical late ACK settles to the SAME state (idempotent, no re-settle)
    replay = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="acked",
        incoming_ack=late_ack,
    )
    assert replay["state"] == "acked"
    assert replay["llm_calls"] == 0 and replay["network_calls"] == 0

    # a late ACK for the WRONG payload is refused and nothing advances
    wrong = reconcile_delivery(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
        expected_payload_sha256=payload_sha,
        current="sent_unknown",
        incoming_ack=dict(late_ack, payload_sha256="e" * 64),
    )
    assert wrong["incoming_ack_accepted"] is False
    assert wrong["incoming_ack_error"] == "ack_payload_hash_mismatch"
    assert wrong["state"] == "sent_unknown"


def test_db_02_03_read_side_idempotency_and_conflict_counts(tmp_path, monkeypatch) -> None:
    """DB-02/DB-03 read-side: original receipt preserved; conflicts surfaced as unknown."""
    _no_network(monkeypatch)
    store = _store(tmp_path)
    item_id, payload_sha = _seed_loop(store)

    # same package+item replay returns the ORIGINAL receipt (DB-02)
    replayed = store.apply_decisions(
        [
            _decision(
                item_id,
                "obs_b272796b8cc0d26970fa8bfd9dfddcbb53ce2336e2d825daf76d9a689575b0a0",
                payload_sha,
            )
        ],
        identity_lookup=None,
    )
    assert replayed[0]["status"] == "accepted"  # ledger returns the ORIGINAL ack
    original = ack_status(
        store,
        package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
        item_id=item_id,
    )
    assert original["count"] == 1, "one ledger row per package+item (idempotent)"
    assert (
        original["receipts"][0]["ack"]["ack_id"]
        == ack_status(
            store,
            package_id="pkg_56febcfa6f28061c711405f664b7f9c469a4d9d9bf5ce488fd58e19883b34a33",
            item_id=item_id,
        )["receipts"][0]["ack"]["ack_id"]
    )

    # same observation id with a different payload -> conflict (DB-03), counted as unknown
    store.apply_decisions(
        [
            _decision(
                "itm_0eaf7897e7344564dde6f107d715ddf8a7f0bfb8cbb465fc08d95677d1d306a3",
                "obs_b272796b8cc0d26970fa8bfd9dfddcbb53ce2336e2d825daf76d9a689575b0a0",
                "f" * 64,
                package_id="pkg_0efe81e52cf12cc283f218f73390a1805cba497bac78beb34611110514b15340",
            )
        ],
        identity_lookup=None,
    )
    status = project_runtime_status(store)
    assert status["import_items"]["conflict"] == 1
    assert status["unknown"] == 1
    assert status["conflicts"] == 1
    assert status["observations"] == 1, "conflict never becomes a second observation"

    # executions are never counted as companies (W10 step 3)
    store.apply_decisions(
        [
            _decision(
                "itm_a8ae2e6f37ed80073411b8899777dcffa17102fdcd87cb924d6da4b936cb8f4e",
                "obs_14fe042a27e6d9330fe6705c97c888296cd289f34b6f70f7bab27ee2f8c9d844",
                "1" * 64,
                package_id="pkg_dc6f14bcc79a981028291cfb69157b6682029aa0fd46a613e0e3cb2a67465d59",
            ),
            _decision(
                "itm_ad068dfcd14cfcafef70fbe1800450456ae20a7a61a1b3719a938eb3718e5bbd",
                "obs_f05ff916d779b8369c4d5d561bdbac33fa28db3333a8b74587353a747dfccfe6",
                "2" * 64,
                package_id="pkg_dc6f14bcc79a981028291cfb69157b6682029aa0fd46a613e0e3cb2a67465d59",
            ),
        ],
        identity_lookup=None,
    )
    status2 = project_runtime_status(store)
    assert status2["import_attempts"] > status2["distinct_companies"], (
        "attempts (items) must not be presented as company counts"
    )
    assert status2["counting_note"]
    assert status2["llm_calls"] == 0 and status2["network_calls"] == 0
    assert status2["coverage"]["facts_available"] is False


def test_ack_status_requires_a_query_and_tolerates_unmigrated_store(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    store = _store(tmp_path)
    with pytest.raises(DeliveryProjectionError) as exc:
        ack_status(store)
    assert exc.value.error_code == "ack_query_shape"

    from stockwiki.quick_scan_observations import QuickScanObservationStore as ObsStore

    unmigrated = ObsStore(WorkspacePaths.from_root(tmp_path / "fresh"))
    with pytest.raises(DeliveryProjectionError) as exc:
        project_runtime_status(unmigrated)
    assert exc.value.error_code == "store_not_migrated"

    # file exists but migrate() never committed its schema -> same named refusal
    empty_root = WorkspacePaths.from_root(tmp_path / "empty_db")
    half = ObsStore(empty_root)
    half.database_path.parent.mkdir(parents=True, exist_ok=True)
    half.database_path.write_bytes(b"")
    with pytest.raises(DeliveryProjectionError) as exc:
        project_runtime_status(half)
    assert exc.value.error_code == "store_not_migrated"
    with pytest.raises(DeliveryProjectionError) as exc:
        ack_status(
            half, package_id="pkg_349ef0158bf93e9bdece509a8dcffbcbc1d6f1f96c0ea7034a0efbdfddc0efc3"
        )
    assert exc.value.error_code == "store_not_migrated"

    with pytest.raises(DeliveryProjectionError) as exc:
        ack_status("not-a-store", package_id="p")
    assert exc.value.error_code == "store_shape"


def test_jr13_schema2_backup_and_restore_preserves_original_ack(tmp_path):
    from stockwiki.quick_scan_backup import create_backup, restore_backup, verify_backup

    paths = WorkspacePaths.from_root(tmp_path)
    store = QuickScanObservationStore(paths)
    store.migrate()
    decision = _decision(
        "itm_7ecacc4ff4034249c562dafa9c69e050e6a9a4dd19ab8e6fa33962e3a6a44484",
        "obs_3145a514677f4233f1d1198ffe9e6605cdd4dfd04f1f1e4a15b9c660b9ec8888",
        "b" * 64,
    )
    ack = store.apply_decisions([decision])[0]
    snapshot = create_backup(paths, name="jr13-schema2")
    assert snapshot is not None
    verify_backup(paths, "jr13-schema2")
    import shutil

    # Only this synthetic pytest workspace is removed, never the source repo.
    shutil.rmtree(paths.data_dir / "quick_scan")
    restore_backup(paths, "jr13-schema2")
    restored = QuickScanObservationStore(paths)
    assert restored.ack_for(decision["package_id"], decision["item_id"]) == ack
    assert (
        restored.import_audit_for(decision["package_id"], decision["item_id"])[
            "internal_error_code"
        ]
        is None
    )


def test_jr13_schema1_migration_preserves_legacy_ack_and_does_not_backfill(tmp_path):
    import json
    import sqlite3

    store = _store(tmp_path)
    decision = _decision(
        "itm_ffddd1a9fe95e98c7cd2c912564e6044f27e95d3b668e1035a5dcd10769571ee",
        "obs_aa4839925d74278774aea2379a0cc020a446b039d46ad2779fee685b2ea5fd55",
        "c" * 64,
    )
    ack = store.apply_decisions([decision])[0]
    legacy = {**ack, "ack_sequence": 1}
    raw = json.dumps(legacy, sort_keys=True, separators=(",", ":"))
    with sqlite3.connect(store.database_path) as con:
        con.execute("UPDATE quick_scan_import_item SET ack_json=?", (raw,))
        con.execute("DROP TABLE quick_scan_import_audit")
        con.execute("PRAGMA user_version=1")
    assert store.ack_for(decision["package_id"], decision["item_id"]) == legacy
    assert store.import_audit_for(decision["package_id"], decision["item_id"]) is None
    assert store.migrate() == 2
    assert store.apply_decisions([decision])[0] == legacy
    assert store.import_audit_for(decision["package_id"], decision["item_id"]) is None
    with sqlite3.connect(store.database_path) as con:
        assert con.execute("SELECT ack_json FROM quick_scan_import_item").fetchone()[0] == raw


def test_jr13_newer_schema_and_failed_upgrade_are_atomic(tmp_path, monkeypatch):
    import sqlite3

    import pytest

    from stockwiki.quick_scan_observations import ObservationImportError

    store = _store(tmp_path)
    decision = _decision(
        "itm_ac1f3ee6a5945de810d83a394518f1ee6778e5cee66b94fc35398fd432996190",
        "obs_bb61b8515bbbcfb97af23be4f838737129c8f926bd6784b4887558ce0a683a6e",
        "d" * 64,
    )
    ack = store.apply_decisions([decision])[0]
    with sqlite3.connect(store.database_path) as con:
        con.execute("DROP TABLE quick_scan_import_audit")
        con.execute("PRAGMA user_version=1")

    def fail(con):
        con.execute("CREATE TABLE rollback_probe (value TEXT)")
        raise RuntimeError("injected migration interruption")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_create_import_audit", fail)
        with pytest.raises(ObservationImportError, match="observation_migration_failed"):
            store.migrate()
    with sqlite3.connect(store.database_path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1
        assert (
            con.execute("SELECT 1 FROM sqlite_master WHERE name='rollback_probe'").fetchone()
            is None
        )
        con.execute("PRAGMA user_version=99")
    with pytest.raises(ObservationImportError, match="observation_store_newer_schema"):
        store.migrate()
    assert store.ack_for(decision["package_id"], decision["item_id"]) == ack
