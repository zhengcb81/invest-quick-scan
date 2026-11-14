"""Independent original-CLI R1 controls and adversarial cases, owned files only."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

LAB=Path.cwd()
OWN=LAB.parent
ROOT=Path(__file__).resolve().parents[5]
LOCK=ROOT/'docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json'
OUT=LAB/'.acceptance-cases'
OUT.mkdir()
from iqs_fact_content_lab.canonical import pack_id_for,sha256_of
import iqs_fact_content_lab.export as export
BASE=json.loads((LAB/'content/content-pack.json').read_text(encoding='utf-8'))
CASES=json.loads((LAB/'content/semantic-cases.json').read_text(encoding='utf-8'))
ROWS=[]

def put(path,obj):
    blob=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()

def row(name,expected,result,passed):
    ROWS.append({'case':name,'expected':expected,'actual':result,'passed':passed})
    print(json.dumps(ROWS[-1],ensure_ascii=False),flush=True)

def prepare(name,pack_change=None,case_change=None,view='none',case_filename='semantic-cases.json'):
    dest=OUT/name
    dest.mkdir()
    p,c=copy.deepcopy(BASE),copy.deepcopy(CASES)
    if pack_change: pack_change(p)
    if case_change:
        target=next(x for x in c['cases'] if x['case_id']=='FC02-uses-production-equipment-ok')
        case_change(target)
        target['input_sha']=sha256_of(target['source_facts'])
    p['input_refs']['case_file']['path']=case_filename
    p['input_refs']['case_file']['sha256']=put(dest/case_filename,c)
    p['pack_id']=pack_id_for(p)
    put(dest/'content-pack.json',p)
    if view=='stale': shutil.copyfile(LAB/'content/question-map.json',dest/'question-map.json')
    elif view=='synced': put(dest/'question-map.json',{'source_pack_id':p['pack_id'],'question_map':p['question_map']})
    return dest

def cli(args,extra=None):
    env=dict(os.environ)
    if extra: env.update(extra)
    p=subprocess.run([sys.executable,'-B','-X','utf8','-m','iqs_fact_content_lab',*args],
                     cwd=LAB,env=env,capture_output=True,text=True,encoding='utf-8',timeout=45)
    return {'exit_code':p.returncode,'stdout':p.stdout[-1500:],'stderr':p.stderr[-3000:]}

def validate(dest):
    return cli(['validate-pack','--input',str(dest/'content-pack.json'),'--inputs-lock',str(LOCK)])

def verdict(name,dest,expected,code,markers=()):
    result=validate(dest)
    row(name,expected,result,result['exit_code']==code and all(m in result['stderr'] for m in markers))

control=prepare('control')
verdict('FC-CONTROL','unchanged no-view pack validates',control,0) if False else None
verdict('FC-CONTROL',control,'unchanged no-view pack validates',0)
def hashes(p):
    p['question_map'][1]['source_question_sha256']='0'*64
    p['question_map'][1]['source_file_sha256']='0'*64
verdict('FC01-source-hash',prepare('hash',pack_change=hashes),'target source SHA error',4,('source_question_sha256','source_file_sha256'))
verdict('FC02-stale-view-does-not-mask-hash',prepare('stale',pack_change=hashes,view='stale'),'target source SHA visible despite stale view',4,('source_question_sha256','source_file_sha256'))
def absent(c):
    c['source_facts']['assertions'][0]['evidence_state']='explicitly_absent'
    c['source_facts']['assertions'][0]['claim']='明确未使用该设备。'
    c['target']['evidence_state']='explicitly_absent'
verdict('FC03-absence',prepare('absence',case_change=absent),'explicit absence rejects true target',4,('[evidence]',))
def date(c):
    c['period']['information_as_of']=c['target']['information_as_of']='2026-99-99'
verdict('FC04-invalid-date',prepare('date',case_change=date),'calendar date rejection',4,('[date]',))
race=prepare('race')
sentinel=race/'sentinel.json'
sentinel.write_bytes(b'OWNED_SENTINEL\n')
before=hashlib.sha256(sentinel.read_bytes()).hexdigest()
real_validate=export.validate_pack
def swap(pack,lock):
    snapshot=real_validate(pack,lock)
    put(race/'semantic-cases.json',{'cases':[{'case_id':'../../sentinel','unexpected':True}]})
    return snapshot
export.validate_pack=swap
try:
    result=export.export_cases(race/'content-pack.json',race/'export',str(LOCK))
    envelope=json.loads((race/'export/cases/envelope.json').read_text(encoding='utf-8'))
    good=(sentinel.read_bytes()==b'OWNED_SENTINEL\n' and envelope['case_count']==len(CASES['cases']) and envelope['cases']==CASES['cases'])
    row('FC05-snapshot-only','sentinel unchanged and all original verified cases exported',
        {'case_count':envelope['case_count'],'sentinel_sha_before':before,'sentinel_sha_after':hashlib.sha256(sentinel.read_bytes()).hexdigest()},good)
finally: export.validate_pack=real_validate
override=OWN/'fact-schema-override'
override.mkdir()
shutil.copytree(LAB/'schemas',override/'schemas')
result=cli(['export-cases','--input',str(control/'content-pack.json'),'--inputs-lock',str(LOCK),'--output',str(override/'export')],{'IQS_FACT_CONTENT_LAB_SCHEMAS':str(override)})
row('FC06-output-root','schema override cannot widen output root, exit3 and no output',result,result['exit_code']==3 and not (override/'export').exists())

# Valid, synchronously sealed cases isolate remaining temporal checks.
def future(c):
    c['target']['valid_from']=c['source_facts']['assertions'][0]['valid_from']='2027-01-01'
verdict('FC07-future-relation',prepare('future',case_change=future),'future valid_from cannot support current target',4,('[period]',))
def historical(c):
    c['target']['kind']='historical_relation'
    c['period']['basis']=c['target']['basis']='historical'
    for key,value in [('period_start','2020-01-01'),('period_end','2020-12-31')]:
        c['period'][key]=c['target'][key]=value
    for key,value in [('valid_from','2025-01-01'),('valid_to','2025-12-31')]:
        c['target'][key]=c['source_facts']['assertions'][0][key]=value
verdict('FC08-disjoint-history',prepare('history',case_change=historical),'2025 evidence cannot establish 2020 historical target',4,('[period]',))

# A valid JSON payload under a fake secret filename must be rejected before read.
verdict('FC09-nested-secret-name',prepare('secret',case_filename='api_key.json'),'nested fake secret path rejects exit6',6)

# Actual Windows junction, owned source and target, then original public CLI.
j=prepare('junction')
target=OUT/'junction-target'
target.mkdir()
shutil.copyfile(j/'semantic-cases.json',target/'semantic-cases.json')
env=dict(os.environ,IQS_R1_JUNCTION=str(j/'linked'),IQS_R1_TARGET=str(target))
native=subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:IQS_R1_JUNCTION -Value $env:IQS_R1_TARGET | Out-Null"],env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
if native.returncode:
    row('FC10-junction-fixture','actual owned junction created',{'fixture_exit':native.returncode,'stderr':native.stderr},False)
else:
    p=json.loads((j/'content-pack.json').read_text(encoding='utf-8'))
    p['input_refs']['case_file']['path']='linked/semantic-cases.json'
    p['pack_id']=pack_id_for(p)
    put(j/'content-pack.json',p)
    verdict('FC10-nested-junction',j,'reject original nested reparse chain before resolve',6)

# Real-source qualification may not be obtained by a forged suffix alone.
def provenance(c):
    source=next(x for x in BASE['input_refs']['source_files'] if x['path']=='questions/facts.json')
    c['fixture_class']='real_source_excerpt'
    c['source_provenance']={'input_lock_ref':'arbitrary-unbound-lock','original_path':'C:/untrusted-not-locked-root/'+source['path'],
                            'sha256':source['sha256'],'note':'Owned negative fixture only; not real evidence'}
verdict('FC11-forged-provenance-root',prepare('provenance',case_change=provenance),'reject root/lock outside frozen provenance',4,('[provenance]',))

old=cli(['validate-pack','--input',str(LAB/'content/archive/content-pack-1.0.0.json'),'--inputs-lock',str(LOCK)])
row('FC12-legacy-read','supported public read-only legacy interpretation (no target/gold fabrication)',old,old['exit_code']==0)
report={'cases':ROWS,'all_expectations_met':all(r['passed'] for r in ROWS),
        'paid_api_requests':0,'company_document_downloads':0,'source_repo_written':False}
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':len(ROWS),'failed':[r['case'] for r in ROWS if not r['passed']]},ensure_ascii=False))
