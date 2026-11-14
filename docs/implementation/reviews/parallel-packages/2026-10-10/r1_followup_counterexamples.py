"""Only new review counterexamples and corrected real-junction fixture."""
from __future__ import annotations
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
from iqs_fact_content_lab.canonical import pack_id_for,sha256_of,term_identity_sha256
LAB=Path.cwd()
ROOT=Path(__file__).resolve().parents[5]
LOCK=ROOT/'docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json'
OUT=LAB/'.acceptance-followup'
OUT.mkdir()
BASE=json.loads((LAB/'content/content-pack.json').read_text(encoding='utf-8'))
CASES=json.loads((LAB/'content/semantic-cases.json').read_text(encoding='utf-8'))
ROWS=[]
def put(path,obj):
    blob=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()
def prepare(name,case_change=None,pack_change=None):
    d=OUT/name;d.mkdir()
    p,c=copy.deepcopy(BASE),copy.deepcopy(CASES)
    if case_change:
        item=next(x for x in c['cases'] if x['case_id']=='FC02-uses-production-equipment-ok')
        case_change(item)
        item['input_sha']=sha256_of(item['source_facts'])
    if pack_change: pack_change(p)
    p['input_refs']['case_file']['sha256']=put(d/'semantic-cases.json',c)
    p['pack_id']=pack_id_for(p);put(d/'content-pack.json',p)
    return d
def check(name,path,expect,code,markers=()):
    proc=subprocess.run([sys.executable,'-B','-X','utf8','-m','iqs_fact_content_lab','validate-pack',
                         '--input',str(path),'--inputs-lock',str(LOCK)],env=dict(os.environ),cwd=LAB,
                        capture_output=True,text=True,encoding='utf-8',timeout=45)
    row={'case':name,'expected':expect,'exit_code':proc.returncode,'stdout':proc.stdout[-1500:],
         'stderr':proc.stderr[-2200:],'passed':proc.returncode==code and all(m in proc.stderr for m in markers)}
    ROWS.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
control=prepare('control')
check('FC-CONTROL-02',control/'content-pack.json','unchanged pack valid',0)
def unsourced(c):
    c['source_facts']['assertions'][0]['evidence_state']='unsourced'
    c['target']['evidence_state']='unsourced'
check('FC13-unsourced-true',prepare('unsourced',case_change=unsourced)/'content-pack.json',
      'unsourced assertion cannot give supported/strict true',4,('[evidence]',))
def subject(c): c['scope']['entity']='Synthetic-OTHER（不同公司）'
check('FC14-different-subject',prepare('subject',case_change=subject)/'content-pack.json',
      'source subject and scope entity disagreement rejected',4)
def membership(p):
    item=next(t for t in p['terms'] if t['candidate_term_id']=='ct.subsidiary')
    item['member_of_refs']=['ct.undefined']
    for proposal in p['proposals']:
        if proposal.get('subject_ref')==item['candidate_term_id']:
            proposal['subject_sha256']=term_identity_sha256(item)
check('FC15-missing-membership-target',prepare('membership',pack_change=membership)/'content-pack.json',
      'undefined member_of_refs rejects with target reason',4,('member_of_refs',))
j=LAB/'.acceptance-cases/junction'
assert (j/'linked').is_dir() and (j/'linked').lstat().st_file_attributes & 0x400
p=json.loads((j/'content-pack.json').read_text(encoding='utf-8'))
p['input_refs']['case_file']['path']='linked/semantic-cases.json'
p['pack_id']=pack_id_for(p);put(j/'content-pack.json',p)
check('FC10-real-junction',j/'content-pack.json','nested real junction rejects exit6 before resolve',6)
(OUT/'results.json').write_text(json.dumps({'cases':ROWS,'all_expectations_met':all(r['passed'] for r in ROWS)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':len(ROWS),'failed':[r['case'] for r in ROWS if not r['passed']]},ensure_ascii=False))
