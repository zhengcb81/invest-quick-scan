"""Append contract counterexamples only in the owned candidate test file."""
from pathlib import Path

IQS=Path(__file__).resolve().parents[5]
TARGET=IQS/"runs/r13a/sw/tests/test_quick_scan_observations.py"
ADDITION=r'''

# JR1/JR3: public wire format and raw ingress, independent of internal ledger.
_JR13_ACK_KEYS = {"schema_version", "ack_id", "package_id", "item_id", "observation_id",
    "payload_sha256", "status", "error_code", "received_at", "consumer"}

def _jr13_public_ack(ack):
    assert set(ack) == _JR13_ACK_KEYS
    assert ack["schema_version"] == "1.0.0"
    assert set(ack["consumer"]) == {"component", "namespace", "store_id"}
    assert ack["consumer"]["component"] == "StockWiki"
    assert ack["consumer"]["namespace"] == "quick_scan"
    if ack["status"] in {"accepted", "already_present"}:
        assert ack["error_code"] is None
    elif ack["status"] == "conflict":
        assert ack["error_code"] == "immutable_key_hash_conflict"
    else:
        assert ack["status"] == "rejected"
        assert ack["error_code"] in {"unsupported_schema", "missing_entity", "unknown_question", "invalid_payload", "lineage_violation"}
    import os
    if os.environ.get("IQS_JR13_SCHEMA"):
        from jsonschema import Draft202012Validator, FormatChecker
        contract = json.loads(Path(os.environ["IQS_JR13_SCHEMA"]).read_text("utf-8"))
        Draft202012Validator({"$ref":"#/$defs/ImportAck", "$defs":contract["$defs"]}, format_checker=FormatChecker()).validate(ack)

def _jr13_obs(tag="a", **kwargs):
    import hashlib
    return _observation("obs_"+hashlib.sha256(tag.encode()).hexdigest(), **kwargs)

def test_jr13_public_ack_all_outcomes_and_audit(tmp_path):
    store, identity = _workspace(tmp_path)
    original=_jr13_obs(request_id="REQ_JR13", attempt_id="ATT_JR13")
    package=_package([original])
    first=import_package(store,package,frozen_release=_release(),identity_store=identity)["acks"][0]
    _jr13_public_ack(first)
    replay=_package([original]); replay["created_at"]="2026-10-01T11:00:00Z"
    seed={k:v for k,v in replay.items() if k not in {"package_id","package_sha256"}}
    replay["package_sha256"]=canonical_sha256(seed); replay["package_id"]="pkg_"+replay["package_sha256"]
    duplicate=import_package(store,replay,frozen_release=_release(),identity_store=identity)["acks"][0]
    changed=copy.deepcopy(original); changed["answer"]["score"]=3
    collision=import_package(store,_package([changed]),frozen_release=_release(),identity_store=identity)["acks"][0]
    for ack in (duplicate,collision): _jr13_public_ack(ack)
    assert [first["status"],duplicate["status"],collision["status"]]==["accepted","already_present","conflict"]
    missing=import_package(store,_package([_jr13_obs("missing",entity_id="MISSING")]),frozen_release=_release(),identity_store=identity)["acks"][0]
    _jr13_public_ack(missing); assert missing["error_code"]=="missing_entity"
    audit=store.import_audit_for(duplicate["package_id"],duplicate["item_id"])
    assert audit["original_import"]["package_id"]==package["package_id"]
    rejected_audit=store.import_audit_for(missing["package_id"],missing["item_id"])
    assert rejected_audit["internal_error_code"]=="entity_not_found"
    assert rejected_audit["detail"]=="MISSING"
    reopened=QuickScanObservationStore(store.paths)
    assert reopened.ack_for(first["package_id"],first["item_id"])==first
    assert import_package(reopened,package,frozen_release=_release(),identity_store=identity)["acks"][0]==first

@pytest.mark.parametrize("changes,expected", [
    ({"question_id":"UNKNOWN"},"unknown_question"),
    ({"schema_version":"9.0.0"},"unsupported_schema"),
    ({"field_id":"score.other"},"lineage_violation"),
    ({"answer": {"question_id":"IQS_LEG","response_kind":"score","status":"scored","score":11}},"invalid_payload")])
def test_jr13_public_rejection_taxonomy(tmp_path,changes,expected):
    store,identity=_workspace(tmp_path)
    observation=_jr13_obs("reject"); observation.update(changes)
    if "question_id" in changes: observation["answer"]["question_id"]=changes["question_id"]
    ack=import_package(store,_package([observation]),frozen_release=_release(),identity_store=identity)["acks"][0]
    _jr13_public_ack(ack); assert ack["error_code"]==expected
    assert store.counts()["observations"]==0

@pytest.mark.parametrize("raw,code", [
    ('{"x":1,"x":1}',"json_duplicate_key"),
    ('{"a":{"x":1,"x":1}}',"json_duplicate_key"),
    ('{"a":[{"x":1,"x":1}]}',"json_duplicate_key"),
    ('{"x":NaN}',"json_constant_forbidden"),
    ('{"x":Infinity}',"json_constant_forbidden"),
    ('{"x":-Infinity}',"json_constant_forbidden"),
    ('{"x":1e400}',"json_number_nonfinite"),
    ('{"x":-1e400}',"json_number_nonfinite")])
def test_jr13_raw_json_rejects_before_decisions(raw,code):
    with pytest.raises(ImportValidationError) as caught: parse_package(raw)
    assert caught.value.error_code==code

@pytest.mark.parametrize("value", [float("nan"),float("inf"),float("-inf"),(1,2)])
def test_jr13_direct_dict_cannot_bypass_ingress(value,tmp_path):
    store,identity=_workspace(tmp_path); before=store.counts()
    with pytest.raises(ImportValidationError):
        import_package(store,{"nested":[{"value":value}]},frozen_release=_release(),identity_store=identity)
    assert store.counts()==before

@pytest.mark.parametrize("mutation", ["duplicate_root","duplicate_nested","duplicate_array","overflow"])
def test_jr13_real_cli_invalid_raw_json_zero_writes(tmp_path,mutation):
    import subprocess
    import sys
    store,identity=_workspace(tmp_path)
    package=_package([_jr13_obs("cli")]); raw=json.dumps(package)
    if mutation=="duplicate_root": raw=raw.replace('"schema_version": "1.0.0"','"schema_version": "1.0.0", "schema_version": "1.0.0"',1)
    elif mutation=="duplicate_nested": raw=raw.replace('"summary": "fixture summary"','"summary": "fixture summary", "summary": "fixture summary"',1)
    elif mutation=="duplicate_array": raw=raw.replace('"items": [','"items": [',1).replace('"item_id":','"item_id": "ignored", "item_id":',1)
    else: raw=raw.replace('"summary": "fixture summary"','"summary": 1e400',1)
    packet=tmp_path/"packet.json"; packet.write_text(raw,encoding="utf-8")
    release=tmp_path/"release.json"; release.write_text(json.dumps(_release()),encoding="utf-8")
    before=store.counts()
    proc=subprocess.run([sys.executable,"-B","-X","utf8","-m","stockwiki.cli","--root",str(tmp_path),"observation-import","--package",str(packet),"--release",str(release)],cwd=Path(__file__).parent.parent,capture_output=True,timeout=30)
    assert proc.returncode!=0, proc.stdout.decode()
    assert store.counts()==before

def test_jr13_historical_ack_bytes_are_not_projected_on_replay(tmp_path):
    import hashlib
    import sqlite3
    store,identity=_workspace(tmp_path); package=_package([_jr13_obs("legacy")])
    ack=import_package(store,package,frozen_release=_release(),identity_store=identity)["acks"][0]
    historical={**ack,"ack_sequence":1,"original_import":{"package_id":package["package_id"],"ack_sequence":1,"received_at":ack["received_at"]}}
    raw=json.dumps(historical,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    with sqlite3.connect(store.database_path) as con:
        con.execute("UPDATE quick_scan_import_item SET ack_json=? WHERE package_id=? AND item_id=?",(raw,ack["package_id"],ack["item_id"]))
    before=hashlib.sha256(raw.encode()).hexdigest()
    assert store.ack_for(ack["package_id"],ack["item_id"])==historical
    assert import_package(store,package,frozen_release=_release(),identity_store=identity)["acks"][0]==historical
    with sqlite3.connect(store.database_path) as con:
        actual=con.execute("SELECT ack_json FROM quick_scan_import_item").fetchone()[0]
    assert actual==raw and hashlib.sha256(actual.encode()).hexdigest()==before
'''

def main():
    old=TARGET.read_text("utf-8")
    assert "test_jr13_public_ack_all_outcomes_and_audit" not in old
    TARGET.write_text(old+ADDITION,encoding="utf-8",newline="\n")
    print("Added 22 new parametrized contract cases; unchanged product source")

if __name__=="__main__":main()
