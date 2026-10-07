import json,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"scripts"))
import accuracy_followup as f
p,b=f.p,f.b
run=Path(__file__).resolve().parents[1]
fd=os.open(run/"orchestrator.lock",os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
 f.source_check(run)
 for n in ("TEMP","TMP","TMPDIR"):os.environ[n]=str(run/"tmp")
 tempfile.tempdir=str(run/"tmp");sys.dont_write_bytecode=True;p.guard(run)
 module=b.load_runtime(run);cfg=p.read(run/"budget.json");ledger=b.Ledger(run,cfg["model_http_cap"],cfg["search_http_cap"],cfg["cash_usd_cap"])
 sub=run/"precision";sub.mkdir();(sub/"evidence").mkdir();b.write_json(sub/"companies.json",dict(alphabet=p.read(run/"companies.json")["alphabet"]))
 queries={"alphabet":['Alphabet "2024" "Year Ended December 31" "Purchases of property and equipment" "millions"','Alphabet annual 2024 consolidated cash flows table fiscal year capital expenditures purchases property equipment']}
 b.write_json(run/"precision-plan.json",dict(created_at=b.now(),source_sha256=p.sha(Path(__file__)),queries=queries,max_search_http=2,no_gold_numeric_queries=True,model_http=0))
 original=p.normalize_source
 def expanded(row,provider,query):
  item=original(row,provider,query)
  if item:
   text=row.get("content","");item["snippet"]=text[:4000];item["source_id"]=provider[0].upper()+b.fingerprint(dict(url=item["url"],snippet=item["snippet"]))[:12]
  return item
 p.PROVIDERS=["tavily"];p.search_topics=lambda s:queries[s];p.normalize_source=expanded
 print(json.dumps(p.retrieve(sub,module,ledger),ensure_ascii=False),flush=True)
finally:os.close(fd);(run/"orchestrator.lock").unlink()
