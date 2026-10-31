from pathlib import Path
import sys,json,copy,hashlib
root=Path.cwd();out=root/'runs/close-support31/wiring-independent'
sys.path[:0]=[str(root/'scripts'),str(root/'tests'),str(root),str(root.parent/'StockWiki')]
from test_dashboard_temporal import specimen,result,NOW
import dashboard_temporal as temporal
cases=[]
mutations={
 'ordinary_missing_revision':lambda obs:None,
 'model_self_verification':lambda obs:obs.update(verified_at=NOW,evidence_review_status='formal_research_accepted',verification_receipt={'verified_at':NOW}),
 'future_information':lambda obs:obs['answer'].update(information_as_of='2027-01-01'),
 'information_after_cutoff':lambda obs:obs.update(information_cutoff='2026-10-29'),
 'unknown_publication':lambda obs:obs['answer']['evidence'][0].pop('published_at'),
 'withdrawn_source':lambda obs:obs['answer']['evidence'][0].update(retracted_at='2026-10-30T00:00:00Z'),
 'future_publication':lambda obs:obs['answer']['evidence'][0].update(published_at='2027-01-01'),
 'event_invalidated':lambda obs:obs.update(event_invalidated_at='2026-10-30T00:00:00Z'),
 'malformed_event':lambda obs:obs.update(event_invalidated_at='legacy-unknown'),
}
for name,mutate in mutations.items():
 detail,raw=specimen();raw['identity_revision']=None;raw['payload'].pop('identity_revision');mutate(raw['payload']);raw['payload_sha256']=temporal._sha(raw['payload']);raw['information_cutoff']=raw['payload']['information_cutoff']
 row=detail['groups'][0]['fields'][0];row.update(payload_sha256=raw['payload_sha256'],information_cutoff=raw['information_cutoff']);before=copy.deepcopy((detail,raw));actual=result(detail,raw)
 assert actual['decision']=='not_assessable' and actual['reuse_authorized'] is False and actual['current_context_verified'] is False and 'captured_context_assessment' not in actual and (detail,raw)==before
 if 'clock_only_assessment' in actual:
  assert actual['clock_only_assessment']['context_assessed'] is False and actual['clock_only_assessment']['actual_source_dates']['verified_at'] is None
 cases.append({'case':name,'outcome':actual})
(out/'installed-fallback-probes.json').write_text(json.dumps({'source_sha256':hashlib.sha256((root/'scripts/dashboard_temporal.py').read_bytes()).hexdigest(),'cases':cases},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{'case':x['case'],'reasons':x['outcome']['reason_codes'],'has_clock_only_assessment':'clock_only_assessment' in x['outcome']} for x in cases],ensure_ascii=True))
