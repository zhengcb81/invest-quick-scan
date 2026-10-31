from pathlib import Path
import subprocess,os,json,hashlib,statistics
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];REPO=ROOT.parent/'iqs-import-performance-lab'
C='d4679a1c22bad1590b40db7c7c6300f306148e81'
EXPECTED='890ff0d4c5e52531dde9d404dd8f601af2917f2dd8c7258c14ea457ca1e051fe'
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],env=env)
def blob(p):return git('show',C+':'+p)
def sha(b):return hashlib.sha256(b).hexdigest()
assert git('rev-parse',C).decode().strip()==C
m=blob('docs/payload-manifest.json');assert sha(m)==EXPECTED
tested=json.loads((OUT/'round2-tests.json').read_bytes())
binding=[]
for row in tested['pins']:
 raw=blob(row['path']);forms={'git_blob':raw,'CRLF':raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')}
 matched=[name for name,b in forms.items() if sha(b)==row['sha256']]
 if not matched and row['path']=='tests/integration/test_service_preflight.py':
  before=(OUT/'round2-snapshot'/row['path']).read_text(encoding='utf-8')
  added=" assert execution.bind_calls==0, 'mutable preflight failure must precede any consumer binding call'\n"
  strengthened=before.replace(" assert after['state']=='ready'\n"," assert after['state']=='ready'\n"+added)
  if strengthened==raw.decode('utf-8').replace('\r\n','\n'):
   matched=['one_stronger_bind_call_assertion_static_review_not_independently_rerun']
 assert matched,('test/runtime code changed since independent execution',row['path'])
 binding.append({'path':row['path'],'tested_sha256':row['sha256'],'git_blob_sha256':sha(raw),'matching_byte_forms':matched})
raw=json.loads(blob('bench/raw-runs.json'));summary=json.loads(blob('bench/benchmark-summary.json'))
assert summary['bench_id']=='close31-fresh-preflight'
assert summary['production_ready'] is False
counts=[1,3,33,36];metrics=[]
for n in counts:
 vals={}
 for v in ['baseline','candidate']:
  r=raw[f'{v}/{n}'];assert len(r['reps'])==3
  assert r['baseline_commit']=='092b1a2677ef91a0ba03e57d0105138b432acc7c'
  assert r['source_repositories']==summary['source_repositories']
  vals[v]=statistics.median(x['delivery_ms'] for x in r['reps'])
  assert round(vals[v],1)==summary['results'][str(n)][v]['delivery_ms']['median']
 ratio=round(vals['baseline']/vals['candidate'],3)
 assert ratio==summary['performance'][str(n)]['speedup_ratio_baseline_over_candidate']
 metrics.append({'packets':n,'baseline_median_ms':vals['baseline'],'candidate_median_ms':vals['candidate'],'ratio':ratio})
assert metrics[-1]['ratio']<1
design=blob('integration/performance-design.md').decode('utf-8')
assert '0.843' in design and '更慢' in design and '2000' in design and '不能' in design
assert summary['limitations'] and any('21' in s and 'missing' in s for s in summary['limitations'])
doc=json.loads(blob('docs/consumed-inputs.json'))
assert doc['source_repositories']==summary['source_repositories']
diff=git('diff','5c19ebd0b23b4a7136e7b4de493e4a7e9521cff0',C,'--','bench/run_benchmark.py').decode()
assert 'baseline_source_commits' in diff
result={'protocol':'iqs.independent_perf_runtime_review/1.0.0','status':'passed','open_findings':[],
 'reviewer_agent_id':'/root/review_time_result_wiring31','runtime_patch_author_agent_id':'/root','payload_commit':C,'payload_manifest_sha256':EXPECTED,'input_lock_sha256':'d432ffce06bf5fc204a703f829f14a3e4de62f1d32957322981c6f13a1c367ab',
 'review_scope':'Final-C runtime patch/provenance delta and honest performance description; not full-payload test-design final approval',
 'previous_effective_red':'PERF-CACHE-SEAM-01 baseline1P/candidate1F; candidate immutable consumer_binding persisted before bundle rejection',
 'resolved_in_final_C':True,'tested_file_final_C_bindings':binding,
 'actual_prior_independent_run':{'cases':8,'exit_code':tested['exit_code'],'raw_log_sha256':tested['log_sha256'],'evidence':'round2-tests.json','rerun_in_this_binding':False,'not_added_to_root64':True},
 'new_provenance_change':'baseline_commit now comes from locked source_repositories.iqs.commit, not Lab/scratch HEAD; helper validates exact source keys and40hex commits;2 focused tests are reviewed statically, not independently rerun here',
 'current_archived_measurements':24,'metrics_recomputed_from_archived_rows':metrics,
 'performance_limits_preserved':['36packet candidate slower:0.843; other desktop load uncontrolled; no general speed guarantee or2000-company/production throughput claim','21completed measurements preserved after bounded controller timeout; missing3 rerun alone; provenance remains disclosed','Source inputset uses fixed upstream commits, not temporary harness HEAD'],
 'service_probe_authorship':['/root/review_time_result_wiring31','/root'],
 'test_design_and_full_payload_final_reviewer':'/root/review_answer_close31 (separate; this review does not self-sign reviewer-authored service probes)',
 'production_ready':False,'financial_qualification_granted':False,'source_writes':False,'paid_api_calls':0,'network_calls':0,'reviewed_at_utc':datetime.now(timezone.utc).isoformat()}
(OUT/'runtime-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'status':result['status'],'payload':C,'metrics':metrics},ensure_ascii=False))
