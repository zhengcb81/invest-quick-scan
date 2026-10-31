import os,sys,json,shutil,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;SNAP=OUT/'snapshot-final'
sys.path.insert(0,str(SNAP/'src'))
import iqs_answer_audit as audit
private=ROOT/'runs/package-inputs-2026-10-30-mainline-next/live-answers-32.json'
samples=audit.load_private_samples(private,'5342c92a5a5ad6a85c4fe030190969578af30c44eaa36e159d9966f01e3937ee')
results=[]
mutations={
 'read_window_after_recording':lambda docs:docs['sources.json']['rows'][0].update(read_window_utc={'start':'2026-11-01T00:00:00Z','end':'2026-11-01T00:01:00Z'},read_at_utc='2026-11-01T00:01:00Z',read_at_precision='window_end',recorded_after_builtin_read_at_utc='2026-10-31T20:00:00Z'),
 'reasoning_support_counter':lambda docs:docs['coverage.json']['rows']['reasoning_support'].__setitem__('consistent_with_bound_rubric',32),
 'mixed_source_wire':lambda docs:docs['sources.json'].__setitem__('protocol','iqs.live_answer_content_audit/1.0.0'),
 'digest_claim_as_direct_source':lambda docs:docs['sources.json']['rows'][0].__setitem__('verification_mode','search_digest'),
 'direct_source_without_toolref':lambda docs:docs['sources.json']['rows'][0].__setitem__('verification_tool_refs',[]),
 'recorded_timestamp_not_utc':lambda docs:docs['sources.json']['rows'][0].__setitem__('recorded_after_builtin_read_at_utc','2026-10-31T21:00:00+05:30'),
 'behavior_counted_as_financial':lambda docs:docs['coverage.json']['rows']['financial_fact_support'].__setitem__('claims_total',96),
 'original_score_altered':lambda docs:next(r for r in docs['sample-verdicts.json']['rows'] if r['original_status']=='scored').__setitem__('original_score',1),
}
for name,mutate in mutations.items():
 tmp=ROOT/('.aa31edge-'+uuid.uuid4().hex[:8]);tmp.mkdir(exist_ok=False)
 try:
  shutil.copytree(SNAP/'content',tmp/'content')
  docs={n:json.loads((tmp/'content'/n).read_bytes()) for n in ['claims.json','sources.json','sample-verdicts.json','coverage.json','audit-summary.json']}
  mutate(docs)
  for n,d in docs.items():(tmp/'content'/n).write_text(json.dumps(d,ensure_ascii=False),encoding='utf8')
  try:
   audit.validate_chain(tmp/'content',samples);result={'case':name,'rejected':False}
  except audit.AuditIntegrityError as e:result={'case':name,'rejected':True,'reason':str(e)}
  results.append(result)
 finally:
  if tmp.resolve().parent!=ROOT.resolve() or not tmp.name.startswith('.aa31edge-'):raise ValueError('cleanup')
  shutil.rmtree(tmp)
(OUT/'adversarial-final-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(results,ensure_ascii=False))
