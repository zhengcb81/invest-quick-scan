"""Correct only the invalid historical-basis controller fixture; retain first log."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from iqs_fact_content_lab.canonical import pack_id_for
LAB=Path.cwd()
ROOT=Path(__file__).resolve().parents[5]
LOCK=ROOT/'docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json'
OLD=LAB/'.acceptance-cases/history'
DEST=LAB/'.acceptance-history-corrected'
DEST.mkdir()
pack=json.loads((OLD/'content-pack.json').read_text(encoding='utf-8'))
cases=json.loads((OLD/'semantic-cases.json').read_text(encoding='utf-8'))
case=next(c for c in cases['cases'] if c['case_id']=='FC02-uses-production-equipment-ok')
case['period']['basis']=case['target']['basis']='trailing'
raw=(json.dumps(cases,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
(DEST/'semantic-cases.json').write_bytes(raw)
pack['input_refs']['case_file']['sha256']=hashlib.sha256(raw).hexdigest()
pack['pack_id']=pack_id_for(pack)
(DEST/'content-pack.json').write_text(json.dumps(pack,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
proc=subprocess.run([sys.executable,'-B','-X','utf8','-m','iqs_fact_content_lab','validate-pack',
                     '--input',str(DEST/'content-pack.json'),'--inputs-lock',str(LOCK)],cwd=LAB,
                    env=dict(os.environ),capture_output=True,text=True,encoding='utf-8',timeout=45)
result={'case':'FC08-disjoint-history-corrected','basis':'trailing',
        'target_period':['2020-01-01','2020-12-31'],'source_validity':['2025-01-01','2025-12-31'],
        'expected_exit':4,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,
        'guard_expectation_met':proc.returncode==4 and '[period]' in proc.stderr}
(DEST/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
