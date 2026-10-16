import pathlib,json,copy,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'csc/tests'))
import conftest
from iqs_operating_csc import validate_reference,coverage,export_bundle
from iqs_operating_csc.canonical import content_hash
f=conftest.frozen.__wrapped__();i=conftest.inputs.__wrapped__(f);e=conftest.expected.__wrapped__(f);base=conftest.reference.__wrapped__()
out=ROOT/'csc/.test-work/independent-probe';out.mkdir(parents=True,exist_ok=True)
cases={
 'observation_after_question_cutoff':lambda d:d['claims'][0].update(period_end='2026-10-12'),
 'observation_start_after_question_cutoff':lambda d:d['claims'][0].update(period_start='2026-10-12',period_end='2026-10-13'),
 'unknown_cost_zero':lambda d:d['acquisition'].update(known_cost_subtotal_usd=0),
 'nonfinite_cost':lambda d:d['acquisition'].update(known_cost_subtotal_usd=float('inf')),
}
rows=[]
for name,mutate in cases.items():
 d=copy.deepcopy(base);mutate(d);r={'case':name}
 try:d['content_sha256']=content_hash(d)
 except Exception as ex:r['hash_reject']=str(ex);rows.append(r);continue
 try:
  v=validate_reference(d,**i,expected_context=e);r.update(validate_ok=v['ok'],errors=v['errors'])
 except Exception as ex:r['validate_exception']=str(ex)
 try:
  c=coverage(reference=d,questions=i['questions'],financial_pack=i['financial_pack'],expected_context=e);r['coverage_accepted']=True
  x=export_bundle(reference=d,coverage_report=c,output_root=str(out/name));r['export_published']=True
 except Exception as ex:r['derive_error']=str(ex)
 rows.append(r)
(ROOT/'csc-probes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False,indent=2))
summary={'claims':[{k:c[k] for k in ('claim_id','claim_kind','statement','business_scope','support','source_ids','premise_claim_ids','period_start','period_end')} for c in base['claims']], 'dimensions':[{k:d[k] for k in ('dimension_id','required_proposition','status','reason','claim_ids')} for d in base['dimensions']], 'sources':[{k:s[k] for k in ('source_id','url','publication_date','date_basis','bounded_paraphrase','access_status','origin_group_id')} for s in base['sources']]}
(ROOT/'csc-material-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
