"""Read-only real engineering evidence; never prints bodies, keys or lease tokens."""
from contextlib import closing
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone

OWN=Path(__file__).resolve().parent
BASE=OWN.parent
ROOT=BASE.parents[1]
OUT=BASE/"actual-native-alphabet-01"
LEDGER=ROOT/"runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def read(p): return json.loads(p.read_text(encoding="utf8"))
def connect(p):
    db=sqlite3.connect(p.resolve().as_uri()+"?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("BEGIN")
    return db

def main():
    parser=argparse.ArgumentParser();parser.add_argument("label");args=parser.parse_args()
    assert args.label.isascii() and args.label.replace("-","").isalnum()
    destination=OWN/(args.label+".json")
    assert not destination.exists(),"append-only reviewer observations"
    backup=OUT/"backup/original-ledger.raw.sqlite"
    assert sha(backup)=="79ae4b84e293a63c762025e326753d78d998e6a5a2d54b5d83245923f03ae85e"
    with closing(connect(backup)) as original,closing(connect(LEDGER)) as current:
        preserved_tables={}
        for table_row in original.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            table=table_row[0];safe='"'+table.replace('"','""')+'"'
            def historical_tuple(row):
                # Original configure API updates only this housekeeping time;
                # policy identity/hash/limits and all other columns still match.
                return tuple((key,row[key]) for key in row.keys() if not (table=="quick_scan_budget_policy" and key=="updated_at"))
            old_tuples=Counter(repr(historical_tuple(r)) for r in original.execute("SELECT * FROM "+safe))
            current_tuples=Counter(repr(historical_tuple(r)) for r in current.execute("SELECT * FROM "+safe))
            assert not (old_tuples-current_tuples),"original historical table row mutation: "+table
            preserved_tables[table]=sum(old_tuples.values())
        old=[dict(r) for r in original.execute("SELECT * FROM quick_scan_budget_attempt ORDER BY budget_attempt_id")]
        now=[dict(r) for r in current.execute("SELECT * FROM quick_scan_budget_attempt ORDER BY budget_attempt_id")]
        byid={r["budget_attempt_id"]:r for r in now}
        assert len(old)==100
        assert all(byid[r["budget_attempt_id"]]==r for r in old),"original row mutation"
        oldids={r["budget_attempt_id"] for r in old}
        added=[r for r in now if r["budget_attempt_id"] not in oldids]
        unresolved=[r for r in old if r["status"]!="settled"]
        assert len(unresolved)==2
        assert all(r["actual_cost_micros"] is None and r["reconciled_at"] is None for r in unresolved)
        tables=[r[0] for r in current.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        selected=["work_item","attempt","quick_scan_refresh_admission","quick_scan_owner_continuation_cell","quick_scan_question_pack_send","quick_scan_research_intent","quick_scan_research_visible_output","answer_checkpoint"]
        counts={t:current.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0] for t in selected if t in tables}
        work_statuses=dict(current.execute("SELECT status,COUNT(*) FROM work_item GROUP BY status"))
        attempt_phases=dict(current.execute("SELECT phase,COUNT(*) FROM attempt GROUP BY phase"))
        earliest_expiry=current.execute("SELECT MIN(lease_expires_at) FROM work_item").fetchone()[0]
        safe_time=current.execute("SELECT MIN(recorded_at) FROM quick_scan_research_visible_output").fetchone()[0]
        lease_timing={"original_lease_seconds":600,"safe_output_before_earliest_expiry":None if earliest_expiry is None or safe_time is None else safe_time<earliest_expiry,"send_before_earliest_expiry":[None if earliest_expiry is None or r["send_intent_at"] is None else r["send_intent_at"]<earliest_expiry for r in added],"remaining_seconds_at_native_send":[None if earliest_expiry is None or r["send_intent_at"] is None else earliest_expiry-r["send_intent_at"] for r in added]}
        protocol=current.execute("PRAGMA user_version").fetchone()[0]
        new_projection=[{k:r[k] for k in ["budget_attempt_id","work_attempt_id","route_id","provider","model_requested","quota_group","pricing_ref","reserved_cost_micros","actual_cost_micros","request_counted","in_flight","status","http_status_code"]} for r in added]
        immutable_tables=[r[0] for r in current.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'quick_scan_owner_continuation_cell_no_%'")]
        native=[]
        sys.path.insert(0,str(ROOT.parent/"StockQAbyLLM"))
        from src.utils.quick_scan_work_store import QuickScanWorkStore
        from src.utils import quick_scan_research_output as visible
        from src.utils.quick_scan_research_intent import _encode, _hash
        native_receipt_row_count=current.execute("SELECT COUNT(*) FROM quick_scan_attempt_response").fetchone()[0]
        new_physical_ids={r["budget_attempt_id"] for r in added}
        for row in current.execute("SELECT * FROM quick_scan_attempt_response"):
            source=QuickScanWorkStore._response_record(current,row)
            if row["attempt_id"] not in new_physical_ids:
                continue  # Member receipt rows are not additional HTTP or usage.
            output=visible.read(QuickScanWorkStore,current,row["attempt_id"])
            join=current.execute("SELECT * FROM quick_scan_research_intent WHERE native_attempt_id=?",(row["attempt_id"],)).fetchone()
            member_count=0
            if join:
                members=json.loads(join["work_item_ids_json"])
                binding={k:join[k] for k in ["task_sha256","intent_sha256","native_attempt_id","request_payload_sha256"]}
                binding["work_item_ids"]=members
                assert _encode(members)==join["work_item_ids_json"] and _hash(binding)==join["binding_sha256"]
                assert source["receipt"]["research_intent_binding_sha256"]==join["binding_sha256"]
                assert source["receipt"]["request_payload_sha256"]==join["request_payload_sha256"]
                pack=current.execute("SELECT pack_id FROM quick_scan_question_pack_send WHERE budget_attempt_id=?",(row["attempt_id"],)).fetchone()
                assert pack is not None
                actual_members=sorted(r[0] for r in current.execute("SELECT work_item_id FROM quick_scan_question_pack_member WHERE pack_id=?",(pack[0],)))
                assert actual_members==members
                member_count=len(members)
            receipt=source["receipt"]
            native.append(dict(attempt_id=row["attempt_id"],receipt_sha256=source["receipt_sha256"],response_sha256=source["response_sha256"],request_payload_sha256=receipt.get("request_payload_sha256"),visible_output_digest=receipt.get("research_visible_output_sha256"),visible_output_valid=output is not None,member_count=member_count,actual_model=receipt.get("actual_model"),requested_model=receipt.get("requested_model"),http_status=receipt.get("http_status_code"),usage=receipt.get("usage")))
    files={name:sha(OUT/name) for name in ["before.json","migration.json","worker-observation.json","route-activation.json","refresh-request.json","owner-policy.installed.json","admission-result.json","activation-complete.json","run-config.json","pre-send-lease-observation.json","crash-native-proof.json","recovery-observation.json"] if (OUT/name).exists()}
    pins={"count":0,"all_match":False}
    if (OUT/"run-config.json").exists():
        conf=read(OUT/"run-config.json")
        assert all(sha(Path(p["path"]))==p["sha256"] for p in conf["source_pins"]),"deployed source drift"
        pins={"count":len(conf["source_pins"]),"all_match":True}
    value=dict(protocol="iqs.independent_real_native_engineering_snapshot/1.0.0",label=args.label,observed_utc=datetime.now(timezone.utc).isoformat(),all_database_reads_mode_ro=True,reviewer_paid_calls=0,original_backup_sha256=sha(backup),schema_version=protocol,original_budget_rows=100,original_full_rows_identical=True,original_budget_rows_sha256=hashlib.sha256(canon(old).encode()).hexdigest(),old_unresolved_count=2,old_unresolved_actual_and_reconciliation_null=True,old_unresolved_reserved_micros=sum(r["reserved_cost_micros"] for r in unresolved),old_unresolved_inflight=sum(r["in_flight"] for r in unresolved),new_original_budget_rows=new_projection,total_request_rows=len(now),row_counts=counts,work_statuses=work_statuses,continuation_immutability_triggers=immutable_tables,file_hashes=files,source_pins=pins,native_response_bindings=native)
    value.update(attempt_phases=attempt_phases,lease_timing=lease_timing,native_receipt_row_count=native_receipt_row_count,native_usage_counting="physical original budget attempt only; per-member receipts never summed")
    value.update(all_historical_table_rows_preserved_except_original_policy_updated_at=preserved_tables,allowed_original_housekeeping_delta="quick_scan_budget_policy.updated_at only; complete policy/limits/hash unchanged")
    destination.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"label":args.label,"original100_unchanged":True,"request_rows":len(now),"new_rows":len(added),"row_counts":counts,"source_pins":pins}))

if __name__=="__main__":main()
