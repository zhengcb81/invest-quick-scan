"""Force two normal importers to see the same schema-1 migration boundary."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading

import test_quick_scan_observations as fixture
from stockwiki.quick_scan_import import import_package

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
SW = OWN.parent / "sw"
FILES = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py",
         "stockwiki/quick_scan_backup_manifest.py", "tests/test_quick_scan_observations.py",
         "tests/test_quick_scan_delivery.py"]
before = {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in FILES}
store, identity = fixture._workspace(OWN / "migration-race")
old_package = fixture._package([fixture._jr13_obs("race-old", request_id="REQ_OLD", attempt_id="ATT_OLD")])
old_ack = import_package(store, old_package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
with sqlite3.connect(store.database_path) as con:
    con.execute("DROP TABLE quick_scan_import_audit")
    con.execute("PRAGMA user_version=1")
original_connect = sqlite3.connect
barrier = threading.Barrier(2)

class RaceConnection(sqlite3.Connection):
    def execute(self, statement, *args, **kwargs):
        cursor = super().execute(statement, *args, **kwargs)
        if statement == "PRAGMA user_version":
            # Both real PRAGMA queries have returned schema 1 before either
            # importer can acquire BEGIN IMMEDIATE. No candidate SQL is altered.
            barrier.wait(timeout=10)
        return cursor

def connected(*args, **kwargs):
    return original_connect(*args, factory=RaceConnection, **kwargs)

outcomes = []
lock = threading.Lock()
def worker(tag):
    package = fixture._package([fixture._jr13_obs(tag, request_id="REQ_" + tag, attempt_id="ATT_" + tag)])
    try:
        result = import_package(store, package, frozen_release=fixture._release(), identity_store=identity)
        outcome = {"tag": tag, "outcome": "success", "ack": result["acks"][0]}
    except Exception as exc:
        outcome = {"tag": tag, "outcome": type(exc).__name__, "error_code": getattr(exc, "error_code", None), "message": str(exc)}
    with lock:
        outcomes.append(outcome)

sqlite3.connect = connected
try:
    threads = [threading.Thread(target=worker, args=(tag,)) for tag in ["race-a", "race-b"]]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert all(not thread.is_alive() for thread in threads)
finally:
    sqlite3.connect = original_connect
with sqlite3.connect(store.database_path) as con:
    version = con.execute("PRAGMA user_version").fetchone()[0]
    audit_table_count = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='quick_scan_import_audit'").fetchone()[0]
after = {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in FILES}
assert before == after
for name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / name
    assert not ledger.exists() or not ledger.read_bytes()
result = {"outcomes": outcomes, "final_version": version, "audit_table_count": audit_table_count,
          "counts": store.counts(), "old_ack_unchanged": store.ack_for(old_ack["package_id"], old_ack["item_id"]) == old_ack,
          "candidate_before": before, "candidate_after": after, "candidate_unchanged": True,
          "guard_ledgers_empty": True, "synthetic_only": True, "real_API_calls": 0, "production_DB_access": False}
(OWN / "concurrency-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
