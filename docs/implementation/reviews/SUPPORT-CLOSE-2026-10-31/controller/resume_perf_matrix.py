"""Keep completed measurements; after bounded interruption rerun only missing cell.

Never signals the original worker, starts duplicate benchmark cells or reads a
live fixture database. Full raw records must exist before a cell is reusable.
"""
import os,sys,json,time,hashlib,subprocess,shutil,uuid,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent;W=OUT/'perf/work';O=OUT/'perf';P=O/'completed-matrix-records'
active=json.loads((O/'benchmark-active.json').read_bytes());source=Path(active['cwd'])/'bench'
deadline=time.monotonic()+3000
while time.monotonic()<deadline:
    if (O/'benchmark-result.json').is_file():
        print('original matrix completed; no duplicate work');raise SystemExit(0)
    if source.is_dir():
        for p in (source/'runs').glob('close31-fresh-preflight-*.json'):
            try:
                b=p.read_bytes();record=json.loads(b)
                if len(record['reps'])==3:(P/p.name).write_bytes(b)
            except (OSError,ValueError,KeyError):pass  # Writer has not published a complete record.
    if (O/'benchmark-cleanup.json').is_file() and not Path(active['cwd']).exists():break
    time.sleep(10)
else:raise RuntimeError('original bounded worker not observed complete; no overlapping cell started')
records={}
for p in P.glob('close31-fresh-preflight-*.json'):
    key=p.stem.removeprefix('close31-fresh-preflight-').rsplit('-',1)
    records[key[0]+'/'+key[1]]=json.loads(p.read_bytes())
missing=[(variant,n) for n in [1,3,33,36] for variant in ['baseline','candidate'] if f'{variant}/{n}' not in records]
if missing!=[('candidate',36)]:raise RuntimeError('unexpected missing cells; do not guess: '+repr(missing))
short=ROOT/('.c31resume-'+uuid.uuid4().hex[:6]);short.mkdir()
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',TEMP=str(short),TMP=str(short))
started=datetime.now(timezone.utc).isoformat();commands=[]
try:
    for item in W.iterdir():
        if item.name in {'.git','.tmp','__pycache__','.pytest_cache'}:continue
        if item.is_dir():shutil.copytree(item,short/item.name)
        else:shutil.copyfile(item,short/item.name)
    subprocess.run(['git','-C',str(short),'init','--quiet'],env=env,capture_output=True,check=True)
    (short/'.tmp').mkdir(exist_ok=True)
    variant=short/'.tmp/candidate'
    argv=[sys.executable,'-B',str(short/'tools/prepare_variant.py'),'--target',str(variant),'--patch',str(short/'integration/candidate.patch')]
    p=subprocess.run(argv,cwd=short,env=env,capture_output=True,timeout=180);commands.append({'argv':argv,'exit_code':p.returncode})
    if p.returncode:raise RuntimeError('resume variant preparation failed')
    target=short/'bench/resumed-candidate-36.json'
    argv=[sys.executable,'-B',str(short/'bench/run_once.py'),'--variant-root',str(variant),'--packets','36','--reps','3','--out',str(target),'--workdir',str(short/'.tmp/resumed-run'),'--label','candidate-36']
    p=subprocess.run(argv,cwd=short,env=env,capture_output=True,timeout=2100);commands.append({'argv':argv,'exit_code':p.returncode})
    (O/'benchmark-resume.log').write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('resumed missing benchmark cell failed')
    records['candidate/36']=json.loads(target.read_bytes())
    (P/'close31-fresh-preflight-candidate-36.json').write_bytes(target.read_bytes())
    sys.path.insert(0,str(W/'src'))
    spec=importlib.util.spec_from_file_location('perf_summary',W/'bench/run_benchmark.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from iqs_import_perf.orchestrate import normalize_snapshot
    results={};semantic={};performance={}
    for n in [1,3,33,36]:
        key=str(n);results[key]={};snaps=[]
        for v in ['baseline','candidate']:
            record=records[v+'/'+key];assert len(record['reps'])==3
            for rep in record['reps']:
                assert rep['verification']['ack_status_counts']=={'accepted':n}
                snaps.append(json.dumps(normalize_snapshot(rep['semantic_snapshot']),ensure_ascii=False,sort_keys=True))
            results[key][v]=module.summarize(record['reps'])
        semantic[key]={'snapshots_compared':len(snaps),'distinct_normalized_snapshots':len(set(snaps)),
            'semantic_equivalence_passed':len(set(snaps))==1,'alignment_note':'Original normalize_snapshot; statuses/ACK/refusal/content hashes retained.'}
        if len(set(snaps))!=1:raise RuntimeError('normal semantic parity failed at '+key)
        base=results[key]['baseline']['delivery_ms'];cand=results[key]['candidate']['delivery_ms']
        performance[key]={'baseline':base,'candidate':cand,'baseline_spawns':results[key]['baseline']['spawn_count'],
            'candidate_spawns':results[key]['candidate']['spawn_count'],'performance_improvement_observed':cand['median']<base['median'],
            'speedup_ratio_baseline_over_candidate':round(base['median']/cand['median'],3)}
    source_refs=json.loads((W/'docs/consumed-inputs.json').read_bytes())['source_repositories']
    summary={'protocol':'iqs.original_import_benchmark/1.0.0','bench_id':'close31-fresh-preflight','package_id':'IMPORT-PERF-30','dataset_kind':'synthetic_native',
        'packet_counts':[1,3,33,36],'repetitions_per_invocation':3,'variants':['baseline','candidate'],'results':results,'performance':performance,
        'semantic_equivalence':semantic,'source_repositories':source_refs,'production_ready':False,
        'limitations':['Initial bounded40-minute controller timed out during candidate36;21 complete measurements preserved, missing cell rerun alone after owned cleanup.',
            'Other desktop load uncontrolled; descriptive wall ratios only, no production throughput/general speedup. Preserved-cell aggregate driver wall unrecorded; per-rep measured delivery/fixture/verify retained.']}
    def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    manifest=(P/'candidate-source-manifest.json').read_bytes();(W/'bench/candidate-source-manifest.json').write_bytes(manifest)
    dump(W/'bench/benchmark-summary.json',summary)
    thin={}
    for key,record in records.items():
        thin[key]={'packets':record['packets'],'label':record['label'],'baseline_commit':source_refs['iqs']['commit'],
            'source_repositories':source_refs,'candidate_source_manifest_sha256':hashlib.sha256(manifest).hexdigest() if key.startswith('candidate/') else None,
            'driver_wall_s':None,'reps':[{k:rep[k] for k in ['rep','cold_or_warm','delivery_ms','fixture_ms','export_ms','verify_ms','spawn_summary']} for rep in record['reps']]}
        for row,rep in zip(thin[key]['reps'],record['reps']):row['verification_counts']={k:rep['verification'][k] for k in ['imported_packages','ack_status_counts','work_item_status_counts','delivery_state_counts']}
    dump(W/'bench/raw-runs.json',thin)
    dump(W/'bench/semantic-equivalence.json',{'protocol':'iqs.import_perf.semantic_equivalence/1.0.0','normal_matrix':semantic,'production_ready':False,
        'fault_cases_ref':'tests/integration/test_native_fault_parity.py;test_service_preflight.py','limits':['Grant/publisher unit uses explicit synthetic typed boundaries;not production CLI authority.']})
    for p in P.glob('close31-fresh-preflight-*.json'):shutil.copyfile(p,W/'bench/runs'/p.name)
    result={'exit_code':0,'commands':commands,'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat(),'resumed':True,
        'preserved_measurements':21,'resumed_measurements':3,'performance':performance,'summary_sha256':hashlib.sha256((W/'bench/benchmark-summary.json').read_bytes()).hexdigest()}
    dump(O/'benchmark-result.json',result);print(json.dumps(result))
finally:
    if short.resolve().parent!=ROOT.resolve() or not short.name.startswith('.c31resume-'):raise ValueError('cleanup boundary')
    from cleanup_benchmark_root import cleanup_owned
    cleanup_owned(short)
    (O/'benchmark-resume-cleanup.json').write_text(json.dumps({'root':str(short),'removed':not short.exists(),'paid_calls':0}),encoding='utf-8')
