"""Existing public-mechanism blockers on actual data, no state changes or HTTP."""
from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import sys

OWN=Path(__file__).resolve().parent;BASE=OWN.parent;ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT.parent/"StockQAbyLLM"))
from src.utils.quick_scan_known_outcome_journal import _physical
from src.utils.quick_scan_owner_budget_continuation import exposure_snapshot
from src.utils.quick_scan_work_store import QuickScanWorkStore
LEDGER=ROOT/"runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf8"))
before=sha(LEDGER)
config=read(BASE/"actual-native-alphabet-01/run-config.json")
policy=read(Path(config["budget_policy_file"]))
oldrefs=["DISPATCH_86004529874040469881f32f71aa5a55","DISPATCH_a11c198286874b70a7fa6de11af144ee"]
newref="PACK_BUDGET_286f07509a5a41d28cb5e11ef8e6493a"
try:
    exposure_snapshot(LEDGER,policy,oldrefs+[newref])
except ValueError as error:
    snapshot_three_result=str(error)
else:raise AssertionError("three exposures unexpectedly supported by old contract")
with closing(sqlite3.connect(LEDGER.resolve().as_uri()+"?mode=ro",uri=True)) as db:
    db.row_factory=sqlite3.Row;db.execute("PRAGMA query_only=ON");db.execute("BEGIN")
    row=db.execute("SELECT * FROM attempt ORDER BY prepared_at,attempt_id LIMIT 1").fetchone()
    item=db.execute("SELECT * FROM work_item WHERE work_item_id=?",(row["work_item_id"],)).fetchone()
    try:_physical(QuickScanWorkStore,db,item,row)
    except ValueError as error:known_resolution_result=str(error)
    else:raise AssertionError("unpriced native physical request unexpectedly usable as settled evidence")
    held=db.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt WHERE status IN ('outcome_uncertain','response_unpriced','failure_unpriced')").fetchone()[0]
    remaining=db.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt WHERE status IN ('outcome_uncertain','response_unpriced','failure_unpriced') AND budget_attempt_id NOT IN (?,?)",oldrefs).fetchone()[0]
    receipt=db.execute("SELECT receipt_json FROM quick_scan_attempt_response WHERE attempt_id=?",(newref,)).fetchone()
    receipt=read_receipt=json.loads(receipt[0])
    new=db.execute("SELECT status,actual_cost_micros,in_flight,http_status_code FROM quick_scan_budget_attempt WHERE budget_attempt_id=?",(newref,)).fetchone()
    pack=db.execute("SELECT physical_outcome,members_uncertain FROM quick_scan_question_pack_outcome").fetchone()
    decisions=db.execute("SELECT COUNT(*) FROM quick_scan_owner_work_decision").fetchone()[0]
    results=dict(schema=db.execute("PRAGMA user_version").fetchone()[0],original_total_attempts=db.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0],held_exposure_count=held,remaining_after_old14_exclusion=remaining,known_resolution_physical_guard=known_resolution_result,three_source_old14_guard=snapshot_three_result,new_request=dict(status=new[0],actual_cost_micros=new[1],in_flight=new[2],http_status=new[3],physical_outcome=pack[0],members_uncertain=bool(pack[1]),response_status=receipt.get("response_status"),validation_code=receipt.get("research_validation_code"),visible_output_count=db.execute("SELECT COUNT(*) FROM quick_scan_research_visible_output").fetchone()[0]),owner_work_decision_count=decisions)
assert sha(LEDGER)==before
assert held==3 and remaining==1
assert known_resolution_result=="owner_work_physical_not_settled"
assert snapshot_three_result=="owner_exposure_exact_two_budget_refs_required"
results.update(protocol="iqs.read_only_post_smoke_authority_evidence/1.0.0",ledger_sha256_before=before,ledger_sha256_after=sha(LEDGER),all_reads_mode_ro=True,database_writes=0,paid_calls=0,source_writes=0)
(OWN/"evidence.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf8")
print(json.dumps(results))
