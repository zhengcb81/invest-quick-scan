"""Independent package acceptance counterexamples; copies and sentinels only.

Runs under acceptance_run.env(). A finding is evidence, not a product patch.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

LAB = Path.cwd()
HERE = Path(__file__).resolve().parent
IQS = HERE.parents[4]
LOCK = IQS / 'docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json'
RESULTS = []

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def record(case, expected, observed, reproduced):
    RESULTS.append({'case_id': case, 'expected': expected, 'observed': observed,
                    'finding_reproduced': reproduced})

def cli(args, extra_env=None):
    e = dict(os.environ)
    if extra_env:
        e.update(extra_env)
    p = subprocess.run([sys.executable,'-B','-X','utf8',*args], cwd=LAB, env=e,
                       capture_output=True, text=True, encoding='utf-8', timeout=150)
    return {'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

def evid():
    from iqs_evidence_lab.reference.compare import normalize_answer, compare_item
    from iqs_evidence_lab.reference.pack import compute_pack_id
    pack_path = LAB / 'fixtures/reference/reference-pack.json'
    pack = load(pack_path)
    recs = {r['record_id']:r for r in pack['records']}
    sources = {s['source_id']:s for s in pack['source_refs']}
    out = LAB / '.acceptance-cases'
    out.mkdir()
    valid = cli(['tools/reference_entry.py','validate','--pack',str(pack_path)])
    record('ER-CONTROL', 'original pack validates', valid, valid['exit_code'] != 0)
    for name, rid, raw, dimension in [
        ('ER01-unverified', 'REC-cncb_h-F01', {'value':14830,'unit':'CNY_million','period':'2024-H1','scope':'consolidated','rationale':'2024 H1'},'numeric'),
        ('ER02-unknown', 'REC-catl-F06', {'value':None,'status':'unknown','rationale':''},'numeric'),
        ('ER03-score-without-basis', 'REC-catl-IQS_10', {'score':7,'status':'scored','rationale':'no capital return calculation'},'score_basis'),
        ('ER04-empty-text', 'REC-catl-F01', {'value':166.77,'unit':'CNY_billion','period':'2024-H1','scope':'consolidated','rationale':'2024。'},'text'),
        ('ER05-wrong-text-year', 'REC-catl-F01', {'value':166.77,'unit':'CNY_billion','period':'2024-H1','scope':'consolidated','rationale':'2024 是比较年；2023 年收入为 166.77 billion yuan'},'text'),
        ('ER06-wrong-reporting-basis', 'REC-catl-F01', {'value':166.77,'unit':'CNY_billion','period':'2024-H1','scope':'consolidated','reporting_basis':'restated','listing':'WRONG','rationale':'2024 H1'},'subject_period_scope'),
    ]:
        r = recs[rid]
        dims, _, _ = compare_item(r, normalize_answer(raw), r['company_key'], r['company_key'], sources, [])
        record(name, 'insufficient/unbound evidence never establishes correctness',
               {'dimension':dimension,'verdict':dims[dimension], 'qualification':r['qualification']['source_checked'], 'missing':r['score_support']['missing']},
               dims[dimension]['verdict']=='supported')
    p = copy.deepcopy(pack)
    for c in p['company_refs']:
        if c['company_key']=='cncb_h': c['canonical_name']='中信证券股份有限公司'
    for r in p['records']:
        if r['company_key']=='cncb_h': r['scope_ref']['issuer_name']='中信证券股份有限公司'
    p['pack_id']=compute_pack_id(p)
    wrong = out/'wrong-company.json';put(wrong,p)
    ans=cli(['tools/reference_entry.py','validate','--pack',str(wrong)])
    record('ER07-synchronized-wrong-company','reject disagreement with frozen identities',ans,ans['exit_code']==0)
    p = copy.deepcopy(pack)
    dummy=LAB/'fixtures/reference/api_key.json';sha=put(dummy,{})
    p['input_refs'].append({'ref_id':'INP-FAKESECRET','source_root':'lab','path':'fixtures/reference/api_key.json','bytes':dummy.stat().st_size,'sha256':sha,'role':'experiment_report'})
    p['pack_id']=compute_pack_id(p);fake=out/'nested-input.json';put(fake,p)
    ans=cli(['tools/reference_entry.py','validate','--pack',str(fake)])
    record('ER08-nested-secret-path','exit6 before reading any nested forbidden path; dummy bytes only',ans,ans['exit_code']==0)
    idx=load(LAB/'fixtures/reference/answers-index.json')
    ent=copy.deepcopy(idx['sets'][0]); original=load(IQS/ent['path'])
    requested=original.get('question_ids') or [a['question_id'] for a in original['answers']]
    original['question_ids']=requested
    removed=original['answers'].pop(1)['question_id']
    answer_path=out/'missing-answer.json';sha=put(answer_path,original)
    ent.update(root='lab',path=str(answer_path.relative_to(LAB).as_posix()),sha256=sha)
    idx['sets']=[ent]; missing=out/'missing-index.json';put(missing,idx)
    output=out/'missing-evaluation'
    ans=cli(['tools/reference_entry.py','evaluate','--pack',str(pack_path),'--answers',str(missing),'--output',str(output)])
    if ans['exit_code']==0:
        ev=load(output/'evaluation.json')
        detail={'requested':requested,'deleted_answer':removed,'result_questions':[i['question_id'] for i in ev['items']],'denominator':ev['denominator']}
    else: detail=ans
    record('ER09-missing-answer-denominator','request6 includes missing-answer item or rejects incomplete request',detail,ans['exit_code']==0 and removed not in detail['result_questions'])
    forbidden_output=LAB/'docs/handoff/EVID-LAB-01/acceptance-new-output'
    ans=cli(['tools/reference_entry.py','evaluate','--pack',str(pack_path),'--answers',str(missing),'--output',str(forbidden_output)])
    record('ER10-old-package-output','exit3; old package directory not authorized for new writer',ans,ans['exit_code']==0)

def fact():
    from iqs_fact_content_lab.canonical import pack_id_for, sha256_of
    import iqs_fact_content_lab.export as export
    base=load(LAB/'content/content-pack.json'); original_cases=load(LAB/'content/semantic-cases.json')
    owned=LAB/'.acceptance-cases';owned.mkdir()
    def prepare(name, changes=None, case_changes=None, with_view=False):
        d=owned/name;d.mkdir()
        p=copy.deepcopy(base); c=copy.deepcopy(original_cases)
        if changes: changes(p)
        if case_changes: case_changes(c)
        p['input_refs']['case_file']['sha256']=put(d/'semantic-cases.json',c)
        p['pack_id']=pack_id_for(p);put(d/'content-pack.json',p)
        if with_view: shutil.copyfile(LAB/'content/question-map.json',d/'question-map.json')
        return d
    def validate(d):
        return cli(['-m','iqs_fact_content_lab','validate-pack','--input',str(d/'content-pack.json'),'--inputs-lock',str(LOCK)])
    control=prepare('control');ans=validate(control)
    record('FC-CONTROL-no-view','unmodified pack valid with optional view absent',ans,ans['exit_code']!=0)
    def wrong_hash(p):
        p['question_map'][1]['source_question_sha256']='0'*64
        p['question_map'][1]['source_file_sha256']='0'*64
    wrong=prepare('wrong-hash',changes=wrong_hash);ans=validate(wrong)
    record('FC01-source-hash-not-bound','reject wrong row source SHAs against frozen question',ans,ans['exit_code']==0)
    fake=prepare('wrong-hash-stale-view',changes=wrong_hash,with_view=True);ans=validate(fake)
    record('FC02-unrelated-rejection','negative test must fail for intended hash reason',ans,ans['exit_code']==4 and 'source_pack_id' in ans['stderr'])
    def invalid(c):
        case=next(x for x in c['cases'] if x['case_id']=='FC02-uses-production-equipment-ok')
        case['source_facts']['assertions'][0]['evidence_state']='explicitly_absent'
        case['source_facts']['assertions'][0]['claim']='明确未使用该设备。'
        case['input_sha']=sha256_of(case['source_facts'])
    bad=prepare('absent-but-true',case_changes=invalid);ans=validate(bad)
    record('FC03-explicitly-absent-but-strict','reject supported/strict true against explicit absence',ans,ans['exit_code']==0)
    def invalid_date(c):
        case=next(x for x in c['cases'] if x['case_id']=='FC02-uses-production-equipment-ok')
        case['period']['information_as_of']='2026-99-99'
    bad=prepare('invalid-date',case_changes=invalid_date);ans=validate(bad)
    record('FC04-invalid-calendar-date','reject invalid ISO calendar date',ans,ans['exit_code']==0)
    race=prepare('export-race'); sentinel=race/'sentinel.json';sentinel.write_text('OWNED_SENTINEL\n',encoding='utf-8')
    old_hash=hashlib.sha256(sentinel.read_bytes()).hexdigest()
    original_validate=export.validate_pack
    def real_validate_then_swap(pack, lock):
        summary=original_validate(pack,lock)
        put(race/'semantic-cases.json',{'cases':[{'case_id':'../../sentinel','unexpected':True}]})
        return summary
    export.validate_pack=real_validate_then_swap
    try:
        result=export.export_cases(race/'content-pack.json',race/'export',str(LOCK))
        env=load(race/'export/cases/envelope.json')
        detail={'result':result,'envelope':env,'sentinel_before':old_hash,'sentinel_after':hashlib.sha256(sentinel.read_bytes()).hexdigest(),'sentinel_text':sentinel.read_text(encoding='utf-8')}
        record('FC05-reparse-after-validate','export only validated immutable snapshot; sentinel untouched',detail,detail['sentinel_before']!=detail['sentinel_after'])
    except Exception as exc:
        record('FC05-reparse-after-validate','export only validated immutable snapshot; sentinel untouched',{'exception':type(exc).__name__,'message':str(exc)},False)
    finally: export.validate_pack=original_validate
    outside=LAB.parent/'fact-schema-override';outside.mkdir();shutil.copytree(LAB/'schemas',outside/'schemas')
    ans=cli(['-m','iqs_fact_content_lab','export-cases','--input',str(control/'content-pack.json'),'--inputs-lock',str(LOCK),'--output',str(outside/'export')],{'IQS_FACT_CONTENT_LAB_SCHEMAS':str(outside)})
    record('FC06-schema-override-output-boundary','schema lookup override cannot widen package write root',ans,ans['exit_code']==0)
    for cid in ['FC03-dealer','FC07-homophone-name','FC10-supplier-roles-periods-ok','FC12-stable-replay']:
        values=[c for c in original_cases['cases'] if cid in c['case_id']]
        record('FC-CONTENT-'+cid,'content review only; explicit target/identity/period independent evidence required',values,False)

def evid_secret():
    from iqs_evidence_lab.reference.pack import compute_pack_id
    p=load(LAB/'fixtures/reference/reference-pack.json')
    dummy=LAB/'fixtures/reference/api_key.json'
    p['input_refs'].append({'ref_id':'INP-9999','source_root':'lab','path':'fixtures/reference/api_key.json',
                           'bytes':dummy.stat().st_size,'sha256':hashlib.sha256(dummy.read_bytes()).hexdigest(),'role':'experiment_report'})
    p['pack_id']=compute_pack_id(p)
    path=LAB/'.acceptance-cases/nested-input-valid-id.json';put(path,p)
    ans=cli(['tools/reference_entry.py','validate','--pack',str(path)])
    record('ER08-nested-secret-path-valid-fixture','exit6 before reading forbidden nested dummy path',ans,ans['exit_code']==0)

if __name__=='__main__':
    try:
        {'evid':evid,'fact':fact,'evid-secret':evid_secret}[sys.argv[1]]()
    except Exception as exc:
        record('CONTROLLER-ERROR','all planned counterexamples run',{'exception':type(exc).__name__,'message':str(exc)},False)
        print(json.dumps({'results':RESULTS,'controller_error':True},ensure_ascii=False,indent=2))
        raise
    print(json.dumps({'results':RESULTS,'controller_error':False},ensure_ascii=False,indent=2))
