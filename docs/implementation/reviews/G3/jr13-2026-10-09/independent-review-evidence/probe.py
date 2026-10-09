"""Independent JR13 synthetic counterexamples; candidate files are read only."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker
import test_quick_scan_observations as fixture
from stockwiki.quick_scan_import import canonical_sha256, import_package

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
SW = OWN.parent / "sw"
IQS = OWN.parents[2]
FILES = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py",
         "stockwiki/quick_scan_backup_manifest.py", "tests/test_quick_scan_observations.py",
         "tests/test_quick_scan_delivery.py"]

def hashes():
    return {name: hashlib.sha256((SW / name).read_bytes()).hexdigest() for name in FILES}

def signed(package):
    package = copy.deepcopy(package)
    seed = {key: value for key, value in package.items() if key not in {"package_id", "package_sha256"}}
    package["package_sha256"] = canonical_sha256(seed)
    package["package_id"] = "pkg_" + package["package_sha256"]
    return package

contract = json.loads((IQS / "schemas/quick_scan/exchange.schema.json").read_bytes())
validator = Draft202012Validator({"$ref": "#/$defs/ImportAck", "$defs": contract["$defs"]}, format_checker=FormatChecker())
before = hashes()
results = {"candidate_before": before, "synthetic_only": True, "production_DB_access": False, "real_API_calls": 0}

def cli_case(label, package):
    root = OWN / label
    store, identity = fixture._workspace(root)
    package = signed(package)
    packet = root / "packet.json"
    release = root / "release.json"
    packet.write_text(json.dumps(package), encoding="utf-8")
    release.write_text(json.dumps(fixture._release()), encoding="utf-8")
    argv = [sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli", "--root", str(root),
            "observation-import", "--package", str(packet), "--release", str(release)]
    proc = subprocess.run(argv, cwd=OWN, env=dict(os.environ), capture_output=True, timeout=30)
    (root / "stdout.log").write_bytes(proc.stdout)
    (root / "stderr.log").write_bytes(proc.stderr)
    receipt = json.loads(proc.stdout)
    ack = receipt["acks"][0]
    return {"argv": argv, "returncode": proc.returncode, "ack": ack,
            "schema_errors": [{"path": list(error.path), "message": error.message} for error in validator.iter_errors(ack)],
            "durable_ack_equal": store.ack_for(ack["package_id"], ack["item_id"]) == ack,
            "counts": store.counts(), "audit": store.import_audit_for(ack["package_id"], ack["item_id"])}

package = fixture._package([fixture._jr13_obs("bad-item")])
package["items"][0]["item_id"] = "bad"
results["malformed_item_id"] = cli_case("malformed-item-id", package)
package = fixture._package([fixture._jr13_obs("missing-item")])
package["items"][0] = {}
results["missing_item_fields"] = cli_case("missing-item-fields", package)
package = fixture._package([fixture._observation("obs_cli_1", request_id="REQ_LEG_ID", attempt_id="ATT_LEG_ID")])
results["noncanonical_observation_id"] = cli_case("noncanonical-observation-id", package)

root = OWN / "wrong-original-reference"
store, identity = fixture._workspace(root)
observation = fixture._jr13_obs("reference", entity_id="E_NOT_YET")
package = fixture._package([observation])
first = import_package(store, package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
entity = fixture._seed_entity("E_NOT_YET")
bindings = entity.pop("_bindings")
identity.save_entity(entity, source_bindings=bindings)
package["created_at"] = "2026-10-01T11:00:00Z"
accepted_package = signed(package)
second = import_package(store, accepted_package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
package["created_at"] = "2026-10-01T12:00:00Z"
present_package = signed(package)
third = import_package(store, present_package, frozen_release=fixture._release(), identity_store=identity)["acks"][0]
results["wrong_original_reference"] = {"first": first, "second": second, "third": third,
    "third_audit": store.import_audit_for(third["package_id"], third["item_id"]),
    "third_reference_points_to_rejected": store.import_audit_for(third["package_id"], third["item_id"])["original_import"]["package_id"] == first["package_id"]}

results["candidate_after"] = hashes()
assert results["candidate_after"] == before
results["candidate_unchanged"] = True
for name in ["key-opens.jsonl", "network-attempts.jsonl"]:
    ledger = OWN / name
    assert not ledger.exists() or not ledger.read_bytes()
results["guard_ledgers_empty"] = True
(OWN / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: {"returncode": value["returncode"], "schema_errors": value["schema_errors"], "durable_ack_equal": value["durable_ack_equal"], "counts": value["counts"]} for key, value in results.items() if isinstance(value, dict) and "returncode" in value}, ensure_ascii=False))
print(json.dumps({"reference_statuses": [first["status"], second["status"], third["status"]],
    "third_reference_points_to_rejected": results["wrong_original_reference"]["third_reference_points_to_rejected"],
    "candidate_unchanged": True, "guard_ledgers_empty": True}))
