import json,os,sys,tempfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"scripts"))
import accuracy_followup as f
p,b=f.p,f.b;run=Path(__file__).resolve().parents[1]
fd=os.open(run/"orchestrator.lock",os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
 f.freeze(run,True)
 for n in ("TEMP","TMP","TMPDIR"):os.environ[n]=str(run/"tmp")
 tempfile.tempdir=str(run/"tmp");sys.dont_write_bytecode=True;p.guard(run)
 module=b.load_runtime(run);cfg=p.read(run/"budget.json");ledger=b.Ledger(run,cfg["model_http_cap"],cfg["search_http_cap"],cfg["cash_usd_cap"]);delegate=b.install_observer(module)
 p.freeze=lambda root,check=False:f.freeze(root,check)
 qs=p.read(run/"fact-questions.json")
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(p.request,run,module,delegate,ledger,s,r,"enhanced",qs[s],"enhanced_more."+s+"."+r) for s in qs for r in ["mimo","mimo_pro"] if not (run/"results"/("enhanced_more."+s+"."+r+".json")).exists()]
  for future in as_completed(futures):print(json.dumps(future.result()),flush=True)
 print(json.dumps(ledger.summary()),flush=True)
finally:os.close(fd);(run/"orchestrator.lock").unlink()
