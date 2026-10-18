from pathlib import Path
from contextlib import closing
import sqlite3,json,hashlib,datetime
here=Path(__file__).resolve().parent;base=here.parent;root=base.parents[1];actual=base/'actual-native-catl-profile-01'
original=actual/'backup/original-ledger.sqlite';current=root/'runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite'
def connect(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');return c
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
obs=json.loads((actual/'recovery-carrier02/recovery-observation.json').read_bytes())
with closing(connect(original)) as old,closing(connect(current)) as new:
 preserved={}
 for table in ('quick_scan_budget_attempt','work_item','attempt'):
  before=old.execute('SELECT * FROM '+table).fetchall();after={r[0]:r for r in new.execute('SELECT * FROM '+table)};same=all(after.get(r[0])==r for r in before);assert same
  preserved[table]={'original_rows':len(before),'all_original_rows_exactly_unchanged':same,'current_rows':len(after)}
 counts=dict(new.execute('SELECT status,COUNT(*) FROM quick_scan_budget_attempt GROUP BY status'))
 new.row_factory=sqlite3.Row
 budget=dict(new.execute('SELECT * FROM quick_scan_budget_attempt WHERE budget_attempt_id=?',('PACK_BUDGET_d6bd408466d74fdd9eeaaa5911644b4d',)).fetchone());assert budget['status']=='settled' and budget['actual_cost_micros']==14537
 visible=new.execute('SELECT * FROM quick_scan_research_visible_output WHERE provider_attempt_id=?',('4d46a825-728f-4372-8947-26ec3737ff3f',)).fetchone()
 native_payload_sha=hashlib.sha256(visible['payload_json'].encode('utf-8')).hexdigest();assert native_payload_sha==sha(actual/'native-safe-output.private.json')=='3f67b6130da82cfbf49c744ef204732673763652a00ac6ae0d28343b54c6e70e'
 cas=json.loads((base/'batch-carrier-recovery-candidate/combined-correction-cas.json').read_bytes())
 for key in ('original_run_config','original_checkpoint','original_safe_output_proof'):
  row=cas[key];assert sha(row['path'])==row['sha256']
 summary=obs['runtime_summary'];assert summary['new_model_http']==0 and summary['replayed_native_attempts']==1
 result={'protocol':'iqs.actual-recovery-thin-audit/1.0.0','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'readonly_sqlite':True,'original_rows_preserved':preserved,'budget_status_counts':counts,'actual_total_requests':sum(counts.values()),'this_pack_native_physical_requests':1,'recovery_new_model_http':summary['new_model_http'],'replayed_native_attempts':summary['replayed_native_attempts'],'estimated_cost_usd':0.014537,'cost_source':'published-ratecard-estimate-not-invoice','cash_invoice_confirmed':False,'original_unknown_rows_retained':True,'native_payload_sha256':native_payload_sha,'original_config_checkpoint_safe_boundary_unchanged':True,'all_slots_completed':obs['all_slots_completed'],'formal_native_search_checkpoint_created':False,'financial_sufficiency_qualified':False}
 p=actual/'recovery-correction-02-ledger-audit.json';assert not p.exists();p.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(result,ensure_ascii=False))
