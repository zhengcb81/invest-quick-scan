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
 sub=run/"refinement";sub.mkdir();(sub/"evidence").mkdir();(sub/"companies.json").write_bytes((run/"companies.json").read_bytes())
 queries={"catl":["CATL 宁德时代 2024 半年 2024年1-5月 动力电池使用量 全球市占率"],"cncb_h":["CSC Financial 6066 中信建投 2024 interim total revenue other income RMB million total assets equity operating cash flows"],"alphabet":["Alphabet 2024 annual Year Ended December 31 in millions cash flows purchases property and equipment"]}
 b.write_json(run/"refinement-plan.json",dict(created_at=b.now(),source_sha256=p.sha(Path(__file__)),queries=queries,max_search_http=6,no_gold_numeric_queries=True,model_http=0))
 p.PROVIDERS=["brave","tavily"];p.search_topics=lambda s:queries[s];p.normalize_source=f.normalize
 print(json.dumps(p.retrieve(sub,module,ledger),ensure_ascii=False),flush=True)
finally:os.close(fd);(run/"orchestrator.lock").unlink()
