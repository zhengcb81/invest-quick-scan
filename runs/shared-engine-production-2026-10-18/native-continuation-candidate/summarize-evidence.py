"""Thin measurement summary; no answer/DB/contexts or billing claims."""
from pathlib import Path
import collections,hashlib,json,sys,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent;label=sys.argv[1]
metrics=[];by_pid={}
for p in (r/"evidence"/(label+"-metrics")).glob("*.jsonl"):
    rows=[json.loads(l) for l in p.read_text(encoding="utf8").splitlines()]
    by_pid[p.stem]=rows;metrics.extend(rows)
cli=collections.defaultdict(lambda:{"calls":0,"blocking_seconds":0})
claims=[];lease=[];walls=[]
for row in metrics:
    if row["kind"]=="original_subprocess" and row["module"].startswith("stockwiki."):
        key=(row["phase"],row["module"],row["operation"])
        cli[key]["calls"]+=1;cli[key]["blocking_seconds"]+=row["seconds"]
    elif row["kind"]=="original_claim":claims.append(row)
    elif row["kind"] in ("scripted_vendor_post","native_safe_output_committed","cache_recovery_complete"):lease.append(row)
    elif row["kind"]=="phase_wall":walls.append(row)
xml=ET.parse(r/"evidence"/(label+".xml")).getroot()
cases=list(xml.iter("testcase"));failed=sum(1 for c in cases if c.find("failure") is not None or c.find("error") is not None)
summary={"protocol":"iqs.native_continuation_measurements/1.0.0","qualification":"synthetic_company_and_scripted_vendor_only_original_public_owner_sdk_runner","paid_calls":0,"test_result":{"cases":len(cases),"failed":failed,"wall_seconds":sum(float(c.get("time","0")) for c in cases)},"phase_walls":walls,"original_cli":[dict(phase=k[0],module=k[1],operation=k[2],**v) for k,v in sorted(cli.items())],"claim_count":len(claims),"claim_wall_seconds":sum(x["seconds"] for x in claims),"lease_observations":lease,"measurement_note":"CLI blocking time overlaps claim/phase wall; do not add them together. No actual model-network latency was sampled."}
(r/"evidence"/(label+"-measurements.json")).write_text(json.dumps(summary,indent=2)+"\n",encoding="utf8")
print(json.dumps(summary,indent=2))
