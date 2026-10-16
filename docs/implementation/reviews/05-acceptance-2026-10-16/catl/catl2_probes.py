import sys,pathlib,json,copy,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'catl2/tests'))
from helpers import package_inputs,reference_document,refresh_hashes,validate
from iqs_operating_catl.coverage_lib import coverage
from iqs_operating_catl.export_lib import export_bundle
i=package_inputs();results=[]
cases={
 'inverted_period':lambda d:d['claims'][0].update(period_start='2026-10-10',period_end='2026-10-01'),
 'unknown_cost_as_zero':lambda d:d['acquisition'].update(known_cost_subtotal_usd=0,cost_basis='unknown'),
 'false_source_count':lambda d:d['acquisition'].update(new_source_count=1),
 'company_statement_observed_subject':lambda d:d['claims'][0].update(observed_subject='operating_reality'),
 'unbounded_paraphrase':lambda d:d['sources'][0].update(bounded_paraphrase='word '*201),
 'unknown_date_verified':lambda d:next(s for s in d['sources'] if s['publication_date'] is None).update(access_status='verified'),
 'dated_date_unknown':lambda d:next(s for s in d['sources'] if s['publication_date'] is not None and not s['eligible_by_research_cutoff']).update(access_status='date_unknown'),
 'access_date_as_page_date':lambda d:next(s for s in d['sources'] if s['publication_date'] is not None).update(accessed_at=next(s for s in d['sources'] if s['publication_date'] is not None)['publication_date']+'T00:00:00Z'),
 'query_overcap':lambda d:d['acquisition'].update(query_count=21),
 'failed_open_count':lambda d:d['acquisition'].update(failed_open_count=100),
 'total_cost_below_subtotal':lambda d:d['acquisition'].update(known_cost_subtotal_usd=2,complete_cost_usd=1),
 'out_of_scope_with_claims':lambda d:next(x for x in d['dimensions'] if x['claim_ids'] and not x['sufficient_declared']).update(status='out_of_scope'),
 'reference_only_with_claims':lambda d:next(x for x in d['dimensions'] if x['claim_ids'] and not x['sufficient_declared']).update(status='reference_only'),
}
baseline=reference_document()
baseline_coverage=coverage(reference=baseline,questions=i['questions'],financial_pack=i['financial_pack'],expected_context=i['expected_context'])
for name,mutation in cases.items():
 d=reference_document();mutation(d)
 for s in d['sources']:s['paraphrase_sha256']=hashlib.sha256(s['bounded_paraphrase'].encode()).hexdigest()
 refresh_hashes(d);v=validate(d);row={'case':name,'validate_valid':v['valid'],'error_codes':sorted({e['code'] for e in v['errors']})}
 try:coverage(reference=d,questions=i['questions'],financial_pack=i['financial_pack'],expected_context=i['expected_context']);row['coverage_accepted']=True
 except ValueError as ex:row['coverage_accepted']=False;row['coverage_error']=str(ex)
 target=ROOT/('catl2-probe-'+name)
 try:export_bundle(reference=d,coverage_report=baseline_coverage,output_root=str(target));row['export_published']=True
 except ValueError as ex:row['export_published']=False;row['export_error']=str(ex)
 row['output_exists']=target.exists();results.append(row)
(ROOT/'catl2-probes.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
assert all(not x['validate_valid'] and not x['coverage_accepted'] and not x['export_published'] and not x['output_exists'] for x in results),results
print(json.dumps({'cases':len(results),'all_three_apis_rejected':True,'outputs':0}))
