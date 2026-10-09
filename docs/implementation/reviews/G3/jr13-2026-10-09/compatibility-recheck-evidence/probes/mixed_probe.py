"""Independent order-sensitive direct store binding counterexample."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import test_quick_scan_observations as fixture
from stockwiki.quick_scan_import import import_package, validate_item
from stockwiki.quick_scan_observations import ObservationImportError

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
SW, IQS = OWN.parent / "sw", OWN.parents[2]
names = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py", "stockwiki/quick_scan_backup_manifest.py", "tests/test_quick_scan_observations.py", "tests/test_quick_scan_delivery.py"]
before = {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in names}
expected = json.loads((IQS / "docs/implementation/intake/G3/2026-10-09-jr13/affected-final-03/process.json").read_bytes())["source_sha256"]
assert before == expected

def snapshot(store):
    with sqlite3.connect(store.database_path) as con:
        audits = con.execute("SELECT COUNT(*) FROM quick_scan_import_audit").fetchone()[0]
    return {"counts": store.counts(), "audits": audits, "database_sha256": hashlib.sha256(store.database_path.read_bytes()).hexdigest()}

outcomes = {}
for existing_first in [False, True]:
    name = "existing_first" if existing_first else "missing_first"
    store, identity = fixture._workspace(OWN / name)
    old_package = fixture._package([fixture._jr13_obs(name + "old", request_id="REQ_OLD", attempt_id="ATT_OLD")])
    old_ack = import_package(store, old_package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
    old_decision = validate_item(old_package, old_package["items"][0], frozen_release=fixture._release(), identity_store=identity)
    wrong_old = {**old_decision, "payload_sha256": "f" * 64}
    new_package = fixture._package([fixture._jr13_obs(name + "new", request_id="REQ_NEW", attempt_id="ATT_NEW")])
    new_decision = validate_item(new_package, new_package["items"][0], frozen_release=fixture._release(), identity_store=identity)
    decisions = [wrong_old, new_decision] if existing_first else [new_decision, wrong_old]
    prior = snapshot(store)
    try:
        acks = store.apply_decisions(decisions, identity_lookup=identity)
        outcome = {"returned": True, "acks": acks, "wrong_old_incoming_payload_sha256": wrong_old["payload_sha256"], "old_ack": old_ack}
    except ObservationImportError as exc:
        outcome = {"returned": False, "error_code": exc.error_code, "detail": exc.detail}
    outcome.update(before=prior, after=snapshot(store), decisions=decisions)
    outcomes[name] = outcome
after = {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in names}
assert after == before
for ledger_name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / ledger_name
    assert not ledger.exists() or not ledger.read_bytes()
record = {"candidate_before": before, "candidate_after": after, "candidate_unchanged": True,
          "outcomes": outcomes, "real_API_calls": 0, "production_DB_access": False, "guard_ledgers_empty": True}
(OWN / "mixed-results.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({name: {"returned": value["returned"], "error_code": value.get("error_code"), "before": value["before"], "after": value["after"]} for name, value in outcomes.items()}, ensure_ascii=False))
