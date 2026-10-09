"""Append frozen mixed-batch counterexamples in the owned source only."""
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
FILE = IQS / "runs/r13a/sw/tests/test_quick_scan_observations.py"
TESTS = '''

@pytest.mark.parametrize("field", ["payload_sha256", "observation_id"])
@pytest.mark.parametrize("old_first", [False, True])
def test_jr13_review_mixed_conflicting_slot_is_atomic(tmp_path, field, old_first):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("mixed-old")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    wrong = {key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    wrong.update(status="rejected", error_code="unknown_question")
    wrong[field] = "f" * 64 if field == "payload_sha256" else "obs_" + "f" * 64
    new = dict(package_id="pkg_" + "c" * 64, item_id="itm_" + "b" * 64,
               observation_id="obs_" + "a" * 64, payload_sha256="d" * 64,
               status="rejected", error_code="unknown_question")
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    counts = store.counts()
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([wrong, new] if old_first else [new, wrong], identity_lookup=identity)
    assert error.value.error_code == "historical_ack_binding_mismatch"
    assert store.counts() == counts
    assert store.ack_for(new["package_id"], new["item_id"]) is None
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("field", ["payload_sha256", "observation_id"])
def test_jr13_review_slot_created_after_read_is_rechecked_in_transaction(tmp_path, monkeypatch, field):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("race-old")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    wrong = {key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    wrong.update(status="rejected", error_code="unknown_question")
    wrong[field] = "f" * 64 if field == "payload_sha256" else "obs_" + "f" * 64
    new = dict(package_id="pkg_" + "c" * 64, item_id="itm_" + "b" * 64,
               observation_id="obs_" + "a" * 64, payload_sha256="d" * 64,
               status="rejected", error_code="unknown_question")
    # Emulate the absence of the old slot in the pre-transaction snapshot.
    # The actual SQLite write transaction must recheck the now-present row.
    monkeypatch.setattr(store, "replay_decisions", lambda decisions: None)
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    counts = store.counts()
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([new, wrong], identity_lookup=identity)
    assert error.value.error_code == "historical_ack_binding_mismatch"
    assert store.counts() == counts
    assert store.ack_for(new["package_id"], new["item_id"]) is None
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


def test_jr13_review_mixed_exact_slot_and_new_item_is_supported(tmp_path):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("mixed-exact")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    replay = {key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    replay.update(status="rejected", error_code="unknown_question")
    new = dict(package_id="pkg_" + "c" * 64, item_id="itm_" + "b" * 64,
               observation_id="obs_" + "a" * 64, payload_sha256="d" * 64,
               status="rejected", error_code="unknown_question")
    result = store.apply_decisions([new, replay], identity_lookup=identity)
    assert result[1] == ack and result[0]["status"] == "rejected"
    assert store.ack_for(new["package_id"], new["item_id"]) == result[0]
'''

if __name__ == "__main__":
    original = FILE.read_text("utf-8")
    assert "test_jr13_review_mixed_conflicting_slot_is_atomic" not in original
    FILE.write_text(original + TESTS, encoding="utf-8", newline="\n")
