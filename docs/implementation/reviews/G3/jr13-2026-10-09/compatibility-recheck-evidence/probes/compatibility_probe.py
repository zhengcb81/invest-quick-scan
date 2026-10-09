"""Final continuation: actual old serializer, current owner paths, fake data only."""
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
from concurrent.futures import ThreadPoolExecutor

from jsonschema import Draft202012Validator, FormatChecker
import test_quick_scan_observations as fixture
import test_q10_delivery as qa_fixture
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_import import canonical_sha256, import_package, validate_item
from stockwiki.quick_scan_observations import ObservationImportError, QuickScanObservationStore
from stockwiki.quick_scan_store import QuickScanStore

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
SW, IQS = OWN.parents[1] / "sw", OWN.parents[3]
names = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py", "stockwiki/quick_scan_backup_manifest.py", "tests/test_quick_scan_observations.py", "tests/test_quick_scan_delivery.py"]
def hashes(): return {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in names}
expected = json.loads(Path(sys.argv[1]).read_bytes())
if "source_sha256" in expected: expected = expected["source_sha256"]
before = hashes()
assert before == expected
schema = json.loads((IQS / "schemas/quick_scan/exchange.schema.json").read_bytes())
validator = Draft202012Validator({"$ref": "#/$defs/ImportAck", "$defs": schema["$defs"]}, format_checker=FormatChecker())
result = {"candidate_before": before, "synthetic_only": True, "real_API_calls": 0, "production_DB_access": False}
def load_old(name):
    path = OWN.parent / "legacy" / (name + ".py")
    spec = importlib.util.spec_from_file_location("compat_old_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
old_obs, old_import = load_old("quick_scan_observations"), load_old("quick_scan_import")
result["old_source_commit"] = "c40de21403720306ba21edbf71b9634a40ee58f8"
result["old_source_sha256"] = {name: hashlib.sha256((OWN.parent / "legacy" / (name + ".py")).read_bytes()).hexdigest() for name in ["quick_scan_import", "quick_scan_observations"]}
assert result["old_source_sha256"] == {"quick_scan_import": "87c77921428cb52239f0276a647198aeb3988954f07b4debb468a1a1237dfa56", "quick_scan_observations": "c06f4c58ea5557ab678721f78c5a14d595c26fef5fb1e55843382be956866691"}

def signed(package):
    package = copy.deepcopy(package)
    package["package_sha256"] = canonical_sha256({key: value for key, value in package.items() if key not in {"package_id", "package_sha256"}})
    package["package_id"] = "pkg_" + package["package_sha256"]
    return package
def identity_only(root, entity_id="E01"):
    paths = WorkspacePaths.from_root(root)
    identity = QuickScanStore(paths)
    identity.migrate()
    entity = fixture._seed_entity(entity_id)
    bindings = entity.pop("_bindings")
    identity.save_entity(entity, source_bindings=bindings)
    return paths, identity
def snapshot(store):
    with sqlite3.connect(store.database_path.as_uri() + "?mode=ro", uri=True) as con:
        version = con.execute("PRAGMA user_version").fetchone()[0]
        has_audit = con.execute("SELECT 1 FROM sqlite_master WHERE name='quick_scan_import_audit'").fetchone() is not None
        audits = con.execute("SELECT COUNT(*) FROM quick_scan_import_audit").fetchone()[0] if has_audit else None
        rows = con.execute("SELECT package_id,item_id,ack_json FROM quick_scan_import_item ORDER BY ack_sequence").fetchall()
    return {"version": version, "audit_table": has_audit, "audits": audits, "counts": store.counts(),
            "database_sha256": hashlib.sha256(store.database_path.read_bytes()).hexdigest(),
            "ack_json_sha256": [hashlib.sha256(row[2].encode()).hexdigest() for row in rows]}
def cli(root, label, package=None, raw=None, release=None):
    root.mkdir(parents=True, exist_ok=True)
    packet, release_path = root / (label + ".package.json"), root / (label + ".release.json")
    packet.write_text(raw if raw is not None else json.dumps(package), encoding="utf-8")
    release_path.write_text(json.dumps(release or fixture._release()), encoding="utf-8")
    argv = [sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli", "--root", str(root), "observation-import", "--package", str(packet), "--release", str(release_path)]
    proc = subprocess.run(argv, cwd=OWN, env=dict(os.environ), capture_output=True, timeout=30)
    (root / (label + ".stdout.log")).write_bytes(proc.stdout)
    (root / (label + ".stderr.log")).write_bytes(proc.stderr)
    docs = [json.loads(line) for line in (proc.stdout + b"\n" + proc.stderr).decode("utf-8").splitlines() if line.startswith("{")]
    return {"argv": argv, "returncode": proc.returncode, "receipt": docs[-1] if docs else None}

histories = {}
for short in [True, False]:
    label = "short_history" if short else "canonical_history"
    root = OWN / label
    paths, identity = identity_only(root)
    historical_store = old_obs.QuickScanObservationStore(paths)
    observation = fixture._jr13_obs(label)
    if short: observation["observation_id"] = "obs_legacy_short"
    package = fixture._package([observation])
    original = old_import.import_package(historical_store, package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
    store = QuickScanObservationStore(paths)
    prior = snapshot(store)
    replay = cli(root, "exact_replay", package)
    repeated = cli(root, "exact_replay_again", package)
    keys = {field: original[field] for field in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    direct = store.apply_decisions([keys])
    assert replay["returncode"] == repeated["returncode"] == 0
    assert replay["receipt"]["acks"] == repeated["receipt"]["acks"] == direct == [original]
    assert replay["receipt"]["legacy_wire_pending"] is repeated["receipt"]["legacy_wire_pending"] is True
    assert store.ack_for(original["package_id"], original["item_id"]) == original
    assert snapshot(store) == prior and prior["version"] == 1 and prior["audit_table"] is False
    with sqlite3.connect(store.database_path.as_uri() + "?mode=ro", uri=True) as con:
        raw_ack = con.execute("SELECT ack_json FROM quick_scan_import_item").fetchone()[0]
    assert json.dumps(replay["receipt"]["acks"][0], ensure_ascii=False, sort_keys=True, separators=(",", ":")) == raw_ack
    histories[label] = {"original_ack": original, "replay": replay, "repeated": repeated, "before": prior, "after": snapshot(store), "package": package}
result["histories"] = histories

store = QuickScanObservationStore(WorkspacePaths.from_root(OWN / "short_history"))
package = histories["short_history"]["package"]
prior = snapshot(store)
negative_cli = {}
tamper = copy.deepcopy(package)
tamper["items"][0]["observation"]["answer"]["score"] = 10
cases = {"raw_hash_tamper": json.dumps(tamper)}
raw = json.dumps(package)
assert raw.count('"summary": "fixture summary"') == 1
cases["deep_duplicate"] = raw.replace('"summary": "fixture summary"', '"summary": "contradictory", "summary": "fixture summary"')
cases["array_duplicate"] = raw.replace('"item_id":', '"item_id": "ignored", "item_id":', 1)
cases["signed_new_short"] = json.dumps(signed(tamper))
mixed = copy.deepcopy(histories["canonical_history"]["package"])
mixed["items"].append({})
cases["mixed_old_and_empty"] = json.dumps(signed(mixed))
missing = copy.deepcopy(package)
missing["items"][0].pop("payload_sha256")
cases["missing_field"] = json.dumps(signed(missing))
for label, raw_value in cases.items():
    observed = cli(OWN / "short_history", label, raw=raw_value)
    assert observed["returncode"] == 2, (label, observed)
    assert snapshot(store) == prior
    negative_cli[label] = observed
result["negative_cli"] = negative_cli
original = histories["short_history"]["original_ack"]
wrong_slots = {}
for field in ["observation_id", "payload_sha256"]:
    keys = {name: original[name] for name in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    keys[field] = "obs_" + "f" * 64 if field == "observation_id" else "f" * 64
    try:
        store.apply_decisions([keys])
        raise AssertionError("wrong historical binding accepted")
    except ObservationImportError as exc:
        assert exc.error_code == "historical_ack_binding_mismatch"
        wrong_slots[field] = {"error_code": exc.error_code, "detail": exc.detail}
    assert snapshot(store) == prior
result["wrong_history_slots"] = wrong_slots

mixed_outcomes = {}
for wrong in [False, True]:
    for existing_first in [False, True]:
        label = ("wrong" if wrong else "correct") + ("_existing_first" if existing_first else "_new_first")
        store, identity = fixture._workspace(OWN / label)
        old_package = fixture._package([fixture._jr13_obs(label + "old", request_id="REQ_OLD", attempt_id="ATT_OLD")])
        old_ack = import_package(store, old_package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
        old_decision = validate_item(old_package, old_package["items"][0], frozen_release=fixture._release(), identity_store=identity)
        if wrong: old_decision["payload_sha256"] = "f" * 64
        new_package = fixture._package([fixture._jr13_obs(label + "new", request_id="REQ_NEW", attempt_id="ATT_NEW")])
        new_decision = validate_item(new_package, new_package["items"][0], frozen_release=fixture._release(), identity_store=identity)
        decisions = [old_decision, new_decision] if existing_first else [new_decision, old_decision]
        prior = snapshot(store)
        if wrong:
            try:
                store.apply_decisions(decisions, identity_lookup=identity)
                raise AssertionError("wrong mixed batch accepted")
            except ObservationImportError as exc:
                assert exc.error_code == "historical_ack_binding_mismatch"
                outcome = {"error_code": exc.error_code}
            assert snapshot(store) == prior
        else:
            acks = store.apply_decisions(decisions, identity_lookup=identity)
            assert old_ack in acks and len(acks) == 2
            for ack in acks: validator.validate(ack)
            assert store.counts()["observations"] == store.counts()["acked_items"] == 2
            outcome = {"acks": acks}
        outcome.update(before=prior, after=snapshot(store))
        mixed_outcomes[label] = outcome
result["mixed_batches"] = mixed_outcomes

store, identity = fixture._workspace(OWN / "interleaved_real_connection")
def decision(tag):
    package = fixture._package([fixture._jr13_obs(tag, request_id="REQ_" + tag, attempt_id="ATT_" + tag)])
    return validate_item(package, package["items"][0], frozen_release=fixture._release(), identity_store=identity)
first, incoming, competing = decision("first"), decision("incoming"), decision("competing")
competing["package_id"], competing["item_id"] = incoming["package_id"], incoming["item_id"]
real_replay = store.replay_decisions
scheduled = {}
def after_real_read(decisions):
    outcome = real_replay(decisions)
    assert outcome is None
    other_store = QuickScanObservationStore(store.paths)
    scheduled["competing_ack"] = other_store.apply_decisions([competing], identity_lookup=identity)[0]
    scheduled["committed_snapshot"] = snapshot(store)
    return outcome
store.replay_decisions = after_real_read
try:
    store.apply_decisions([first, incoming], identity_lookup=identity)
    raise AssertionError("concurrently inserted wrong slot accepted")
except ObservationImportError as exc:
    assert exc.error_code == "historical_ack_binding_mismatch"
    scheduled["outer_error_code"] = exc.error_code
assert snapshot(store) == scheduled["committed_snapshot"]
assert store.get_observation(first["observation_id"]) is None
result["interleaved_real_connection"] = {**scheduled, "outer_after": snapshot(store), "first_insert_rolled_back": True, "real_read_not_mocked_none": True}

store, identity = fixture._workspace(OWN / "accepted_reference")
observation = fixture._jr13_obs("reference", entity_id="E_NOT_YET")
package = fixture._package([observation])
first_ack = import_package(store, package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
entity = fixture._seed_entity("E_NOT_YET")
bindings = entity.pop("_bindings")
identity.save_entity(entity, source_bindings=bindings)
package["created_at"] = "2026-10-01T11:00:00Z"
accepted = import_package(store, signed(package), frozen_release=fixture._release(), identity_store=identity)["acks"][0]
package["created_at"] = "2026-10-01T12:00:00Z"
present = import_package(store, signed(package), frozen_release=fixture._release(), identity_store=identity)["acks"][0]
audit = store.import_audit_for(present["package_id"], present["item_id"])
assert first_ack["status"] == "rejected" and accepted["status"] == "accepted"
assert audit["original_import"]["package_id"] == accepted["package_id"] and audit["original_import"]["item_id"] == accepted["item_id"]
result["accepted_reference_with_item_id"] = {"accepted": accepted, "audit": audit}

qa_root = OWN / "qa_strict_consumer"
qa_root.mkdir()
qa_store, wid, ready = qa_fixture._jr2_ready(qa_root)
qa_package = json.loads(ready["package_bytes"])
qa_observation = qa_package["items"][0]["observation"]
receiver_root = OWN / "qa_old_receiver"
paths, identity = identity_only(receiver_root, qa_observation["entity_id"])
historical_store = old_obs.QuickScanObservationStore(paths)
descriptor = {"component": "StockWiki", "namespace": "quick_scan", "store_id": historical_store.store_id}
qa_store.bind_result_delivery_consumer(wid, descriptor, source_ref="independent-owner-fixture:old-receiver-before-send")
qa_store.begin_result_delivery(wid)
release = fixture._release()
release["questions"][qa_observation["question_id"]] = {"field_id": qa_observation["field_id"], "scope": qa_observation["scope"], "response_kind": "score"}
legacy_ack = old_import.import_package(historical_store, qa_package, frozen_release=release, identity_store=identity)["acks"][0]
legacy_receipt = cli(receiver_root, "qa_legacy_replay", qa_package, release=release)
assert legacy_receipt["returncode"] == 0 and legacy_receipt["receipt"]["legacy_wire_pending"] is True
assert legacy_receipt["receipt"]["acks"] == [legacy_ack]
dump_before = hashlib.sha256("\n".join(qa_fixture._jr2_snapshot(qa_store)).encode()).hexdigest()
try:
    qa_store.apply_result_delivery_ack(wid, legacy_receipt["receipt"]["acks"][0])
    raise AssertionError("QA consumed legacy enriched wire")
except ValueError as exc:
    qa_error = str(exc)
    assert "fields mismatch" in qa_error
dump_after = hashlib.sha256("\n".join(qa_fixture._jr2_snapshot(qa_store)).encode()).hexdigest()
assert dump_after == dump_before
qa_delivery = qa_store.get_result_delivery(wid)
assert qa_delivery["state"] == "send_uncertain"
result["QA_legacy_wire_refusal"] = {"state": qa_delivery["state"], "error": qa_error, "before_dump_sha256": dump_before, "after_dump_sha256": dump_after,
    "prebound_receiver_descriptor": descriptor, "actual_old_ack": legacy_ack, "actual_current_cli_receipt": legacy_receipt,
    "no_projection": True, "delivered": False, "fixture_identity_is_synthetic_test_data_not_owner_golden": True}

result["candidate_after"] = hashes()
assert result["candidate_after"] == before
for ledger_name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / ledger_name
    assert not ledger.exists() or not ledger.read_bytes()
result.update(candidate_unchanged=True, guard_ledgers_empty=True, all_probe_processes_completed=True)
(OWN / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"legacy_exact_replay_schema1_no_write": True, "negative_cli_cases": len(negative_cli), "mixed_batch_cases": len(mixed_outcomes),
    "actual_second_connection_slot_conflict_atomic": True, "accepted_reference_item_id": True, "QA_state": qa_delivery["state"],
    "candidate_unchanged": True, "guard_ledgers_empty": True, "all_probe_processes_completed": True}, ensure_ascii=False))
