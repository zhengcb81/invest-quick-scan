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

# Test adapter adds declared synthetic schema fields before actual durable prepare;
# checkpoint-derived identity/answer/execution remain unchanged. Never edit an ACK.
qa_root = OWN / "qa"
qa_root.mkdir()
qa_store = qa_fixture._store(qa_root)
seeded = qa_fixture._seed_checkpoint(qa_store, qa_fixture._lifecycle(qa_store), "IQS_05")
wid = seeded["handle"]["work_item_id"]
qa_package = qa_fixture._build_package(qa_fixture._checkpoint_payload(qa_store, wid), qa_fixture._c06_authority())
minimal = qa_package["items"][0]["observation"]
full = fixture._observation(minimal["observation_id"], entity_id=minimal["entity_id"], question_id=minimal["question_id"], field_id="score.iqs_05")
full["execution"].update(minimal["execution"])
execution = full["execution"]
full.update(minimal)
full["execution"] = execution
full["observed_at"] = execution["answered_at"]
full["execution"]["started_at"] = execution["answered_at"]
item = qa_package["items"][0]
item["observation"] = full
item["payload_sha256"] = canonical_sha256(full)
item["item_id"] = "itm_" + canonical_sha256({"observation_id": item["observation_id"], "payload_sha256": item["payload_sha256"]})
qa_package = signed(qa_package)
ready = qa_store.prepare_result_delivery(wid, qa_package)
assert json.loads(ready["package_bytes"]) == qa_package
receiver_root = OWN / "old-receiver"
paths, identity = identity_only(receiver_root, full["entity_id"])
historical_store = old_obs.QuickScanObservationStore(paths)
descriptor = {"component": "StockWiki", "namespace": "quick_scan", "store_id": historical_store.store_id}
qa_store.bind_result_delivery_consumer(wid, descriptor, source_ref="independent-synthetic-test-adapter:receiver-before-send")
qa_store.begin_result_delivery(wid)
release = fixture._release()
release["questions"][full["question_id"]] = {"field_id": full["field_id"], "scope": full["scope"], "response_kind": "score"}
legacy_ack = old_import.import_package(historical_store, qa_package, frozen_release=release, identity_store=identity)["acks"][0]
assert legacy_ack["status"] == "accepted", legacy_ack
receipt = cli(receiver_root, "original-accepted-replay", qa_package, release=release)
assert receipt["returncode"] == 0 and receipt["receipt"]["legacy_wire_pending"] is True
assert receipt["receipt"]["acks"] == [legacy_ack]
prior = hashlib.sha256("\n".join(qa_fixture._jr2_snapshot(qa_store)).encode()).hexdigest()
try:
    qa_store.apply_result_delivery_ack(wid, receipt["receipt"]["acks"][0])
    raise AssertionError("accepted legacy enriched ACK advanced QA")
except ValueError as exc:
    error = str(exc)
    assert error == "import ACK fields mismatch"
after = hashlib.sha256("\n".join(qa_fixture._jr2_snapshot(qa_store)).encode()).hexdigest()
state = qa_store.get_result_delivery(wid)["state"]
assert after == prior and state == "send_uncertain"
result.update(accepted_original_ack=legacy_ack, actual_cli_replay=receipt, QA_state=state, QA_error=error, QA_before_sha256=prior, QA_after_sha256=after, consumer_prebound_before_send=descriptor, package=qa_package, synthetic_adapter_fields_added_before_prepare=True, ACK_never_projected=True, delivered=False)
result["candidate_after"] = hashes()
assert result["candidate_after"] == before
for ledger_name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / ledger_name
    assert not ledger.exists() or not ledger.read_bytes()
result.update(candidate_unchanged=True, guard_ledgers_empty=True, all_probe_processes_completed=True)
(OWN / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"legacy_original_status": "accepted", "QA_state": state, "QA_snapshot_unchanged": True, "original_ACK_no_projection": True, "candidate_unchanged": True, "guard_ledgers_empty": True}))

