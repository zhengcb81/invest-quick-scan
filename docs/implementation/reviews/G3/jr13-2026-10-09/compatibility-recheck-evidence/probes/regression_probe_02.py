"""Continuation of the same JR13 review, guarded synthetic owner paths only."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading

from jsonschema import Draft202012Validator, FormatChecker
import test_quick_scan_observations as fixture
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_import import canonical_sha256, import_package, validate_item
from stockwiki.quick_scan_observations import ObservationImportError, QuickScanObservationStore
from stockwiki.quick_scan_store import QuickScanStore

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
SW = OWN.parents[1] / "sw"
IQS = OWN.parents[3]
FILES = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py",
         "stockwiki/quick_scan_backup_manifest.py", "tests/test_quick_scan_observations.py",
         "tests/test_quick_scan_delivery.py"]
def hashes():
    return {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in FILES}
expected = json.loads((IQS / "docs/implementation/intake/G3/2026-10-09-jr13/affected-final-04/process.json").read_bytes())["source_sha256"]
before = hashes()
assert before == expected
schema = json.loads((IQS / "schemas/quick_scan/exchange.schema.json").read_bytes())
validator = Draft202012Validator({"$ref": "#/$defs/ImportAck", "$defs": schema["$defs"]}, format_checker=FormatChecker())
result = {"candidate_before": before, "expected_113P_hashes_match": True, "synthetic_only": True,
          "real_API_calls": 0, "production_DB_access": False}

def signed(package):
    package = copy.deepcopy(package)
    package["package_sha256"] = canonical_sha256({key: value for key, value in package.items() if key not in {"package_id", "package_sha256"}})
    package["package_id"] = "pkg_" + package["package_sha256"]
    return package

def snapshot(store):
    with sqlite3.connect(store.database_path) as con:
        audit_count = con.execute("SELECT COUNT(*) FROM quick_scan_import_audit").fetchone()[0]
    return {"counts": store.counts(), "audit_count": audit_count,
            "database_sha256": hashlib.sha256(store.database_path.read_bytes()).hexdigest()}

def cli(root, label, package):
    packet, release = root / (label + ".package.json"), root / (label + ".release.json")
    packet.write_text(json.dumps(package), encoding="utf-8")
    release.write_text(json.dumps(fixture._release()), encoding="utf-8")
    argv = [sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli", "--root", str(root),
            "observation-import", "--package", str(packet), "--release", str(release)]
    proc = subprocess.run(argv, cwd=OWN, env=dict(os.environ), capture_output=True, timeout=30)
    (root / (label + ".stdout.log")).write_bytes(proc.stdout)
    (root / (label + ".stderr.log")).write_bytes(proc.stderr)
    documents = [json.loads(line) for line in (proc.stdout + b"\n" + proc.stderr).decode("utf-8").splitlines() if line.startswith("{")]
    return {"argv": argv, "returncode": proc.returncode, "receipt": documents[-1] if documents else None}

negatives = {}
for case in ["bad_item", "empty_item", "short_obs", "bad_sha", "null_obs", "valid_then_empty"]:
    root = OWN / case
    store, identity = fixture._workspace(root)
    observation = fixture._jr13_obs(case)
    if case == "short_obs":
        observation["observation_id"] = "obs_cli_1"
    package = fixture._package([observation])
    if case == "bad_item": package["items"][0]["item_id"] = "bad"
    if case == "empty_item": package["items"][0] = {}
    if case == "bad_sha": package["items"][0]["payload_sha256"] = ""
    if case == "null_obs": package["items"][0]["observation_id"] = None
    if case == "valid_then_empty": package["items"].append({})
    package = signed(package)
    prior = snapshot(store)
    observed = cli(root, case, package)
    observed.update(before=prior, after=snapshot(store))
    assert observed["returncode"] == 2 and observed["receipt"]["error_code"] == "ack_address_invalid"
    assert observed["before"] == observed["after"]
    negatives[case] = observed
result["F1_cli_negatives"] = negatives

root = OWN / "direct_store_batch"
store, identity = fixture._workspace(root)
package = fixture._package([fixture._jr13_obs("direct")])
good = validate_item(package, package["items"][0], frozen_release=fixture._release(), identity_store=identity)
bad = {**good, "item_id": "bad", "status": "rejected", "error_code": "shape_invalid"}
prior = snapshot(store)
try:
    store.apply_decisions([good, bad])
    raise AssertionError("invalid mixed direct batch accepted")
except ObservationImportError as exc:
    assert exc.error_code == "ack_address_invalid"
    result["F1_direct_batch"] = {"error_code": exc.error_code, "before": prior, "after": snapshot(store)}
assert result["F1_direct_batch"]["before"] == result["F1_direct_batch"]["after"]

root = OWN / "valid_wire_states"
store, identity = fixture._workspace(root)
observation = fixture._jr13_obs("valid-state", request_id="REQ_VALID", attempt_id="ATT_VALID")
package = fixture._package([observation])
accepted = cli(root, "accepted", package)
package["created_at"] = "2026-10-01T11:00:00Z"
present = cli(root, "present", signed(package))
changed = copy.deepcopy(observation)
changed["answer"]["score"] = 3
conflict = cli(root, "conflict", fixture._package([changed]))
rejected = cli(root, "rejected", fixture._package([fixture._jr13_obs("missing", entity_id="E_MISSING")]))
states = [accepted, present, conflict, rejected]
for record in states:
    assert record["returncode"] == 0
    ack = record["receipt"]["acks"][0]
    validator.validate(ack)
    assert store.ack_for(ack["package_id"], ack["item_id"]) == ack
assert [record["receipt"]["acks"][0]["status"] for record in states] == ["accepted", "already_present", "conflict", "rejected"]
result["valid_wire_states"] = states

root = OWN / "original_reference"
store, identity = fixture._workspace(root)
observation = fixture._jr13_obs("reference", entity_id="E_NOT_YET")
package = fixture._package([observation])
first = import_package(store, package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
entity = fixture._seed_entity("E_NOT_YET")
bindings = entity.pop("_bindings")
identity.save_entity(entity, source_bindings=bindings)
package["created_at"] = "2026-10-01T11:00:00Z"
second = import_package(store, signed(package), frozen_release=fixture._release(), identity_store=identity)["acks"][0]
package["created_at"] = "2026-10-01T12:00:00Z"
third = import_package(store, signed(package), frozen_release=fixture._release(), identity_store=identity)["acks"][0]
audit = store.import_audit_for(third["package_id"], third["item_id"])
assert [first["status"], second["status"], third["status"]] == ["rejected", "accepted", "already_present"]
assert audit["original_import"]["package_id"] == second["package_id"]
result["F2_original_reference"] = {"first": first, "second": second, "third": third, "audit": audit, "references_accepted": True}

def identity_only(root):
    paths = WorkspacePaths.from_root(root)
    identity = QuickScanStore(paths)
    identity.migrate()
    entity = fixture._seed_entity("E01")
    bindings = entity.pop("_bindings")
    identity.save_entity(entity, source_bindings=bindings)
    return paths, identity

def concurrent_imports(label, version):
    root = OWN / label
    paths, identity = identity_only(root)
    store = QuickScanObservationStore(paths)
    if version == 1:
        store.migrate()
        old = fixture._package([fixture._jr13_obs(label + "old", request_id="REQ_OLD", attempt_id="ATT_OLD")])
        old_ack = import_package(store, old, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
        with sqlite3.connect(store.database_path) as con:
            con.execute("DROP TABLE quick_scan_import_audit")
            con.execute("PRAGMA user_version=1")
    else:
        old_ack = None
        assert not store.database_path.exists()
    barrier, lock = threading.Barrier(2), threading.Lock()
    seen, trace, outcomes = set(), [], []
    original_connect = sqlite3.connect
    class OrderedConnection(sqlite3.Connection):
        def execute(self, statement, *args, **kwargs):
            thread = threading.get_ident()
            first_begin = False
            if statement == "BEGIN IMMEDIATE":
                with lock:
                    first_begin = thread not in seen
                    seen.add(thread)
                if first_begin:
                    barrier.wait(timeout=10)
            cursor = super().execute(statement, *args, **kwargs)
            if statement in {"BEGIN", "BEGIN IMMEDIATE"}:
                self.last_begin = statement
            if statement == "PRAGMA user_version":
                with lock:
                    trace.append({"thread": thread, "statement": statement, "in_transaction": self.in_transaction, "begin_mode": getattr(self, "last_begin", None)})
            return cursor
    def connected(*args, **kwargs):
        return original_connect(*args, factory=OrderedConnection, **kwargs)
    def worker(tag):
        package = fixture._package([fixture._jr13_obs(label + tag, request_id="REQ_" + tag, attempt_id="ATT_" + tag)])
        try:
            ack = import_package(store, package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
            outcome = {"tag": tag, "ack": ack}
        except Exception as exc:
            outcome = {"tag": tag, "error_code": getattr(exc, "error_code", None), "message": str(exc)}
        with lock:
            outcomes.append(outcome)
    sqlite3.connect = connected
    try:
        threads = [threading.Thread(target=worker, args=(tag,)) for tag in ["a", "b"]]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=20)
        assert all(not thread.is_alive() for thread in threads)
    finally:
        sqlite3.connect = original_connect
    assert len(outcomes) == 2 and all("ack" in entry for entry in outcomes), outcomes
    assert len(trace) >= 2 and all(entry["in_transaction"] for entry in trace)
    assert sum(entry["begin_mode"] == "BEGIN IMMEDIATE" for entry in trace) == 2
    for entry in outcomes: validator.validate(entry["ack"])
    with sqlite3.connect(store.database_path) as con:
        final_version = con.execute("PRAGMA user_version").fetchone()[0]
    assert final_version == 2
    if old_ack is not None:
        assert store.ack_for(old_ack["package_id"], old_ack["item_id"]) == old_ack
    return {"initial_version": version, "final_version": final_version, "outcomes": outcomes, "trace": trace, "counts": store.counts(), "old_ack_unchanged": old_ack is None or store.ack_for(old_ack["package_id"], old_ack["item_id"]) == old_ack}
result["F3_schema1_concurrent_imports"] = concurrent_imports("schema1_concurrent", 1)
result["schema0_concurrent_imports"] = concurrent_imports("schema0_concurrent", 0)

result["candidate_after"] = hashes()
assert result["candidate_after"] == before
for name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / name
    assert not ledger.exists() or not ledger.read_bytes()
result.update(candidate_unchanged=True, guard_ledgers_empty=True, all_threads_joined=True)
(OWN / "regression-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"F1_cli_cases": len(negatives), "F1_direct_batch_zero_write": True, "public_wire_states": ["accepted","already_present","conflict","rejected"], "F2_accepted_reference": True, "F3_schema1_concurrent_success": True, "schema0_concurrent_success": True, "candidate_unchanged": True, "guard_ledgers_empty": True, "all_threads_joined": True}))



