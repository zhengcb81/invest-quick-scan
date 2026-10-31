"""Independently recompute the final saved measurements, without rerunning them."""
from pathlib import Path
import hashlib
import json
import shutil
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT/'runs/close-support31/perf/work'
OUT = Path(__file__).parent

def load(path): return json.loads(path.read_bytes())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def dump(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))

def main():
    summary=load(LAB/'bench/benchmark-summary.json')
    thin=load(LAB/'bench/raw-runs.json')
    semantic=load(LAB/'bench/semantic-equivalence.json')['normal_matrix']
    candidate_manifest=load(LAB/'bench/candidate-source-manifest.json')
    candidate_manifest_sha=sha((LAB/'bench/candidate-source-manifest.json').read_bytes())
    expected_sources=load(LAB/'docs/consumed-inputs.json')['source_repositories']
    seen=set(); rep_hashes=set(); cells=[]; snapshots={}; all_findings=[]
    assert summary['bench_id']=='close31-fresh-preflight'
    assert set(thin)=={f'{v}/{p}' for v in ['baseline','candidate'] for p in [1,3,33,36]}
    for packets in [1,3,33,36]:
        snapshots[packets]=set()
        for variant in ['baseline','candidate']:
            key=f'{variant}/{packets}'
            raw_path=LAB/f'bench/runs/close31-fresh-preflight-{variant}-{packets}.json'
            raw=load(raw_path); reps=raw['reps']; reduced=thin[key]
            assert raw['packets']==packets and raw['dataset_kind']=='synthetic_native'
            assert len(reps)==3 and [r['rep'] for r in reps]==[1,2,3]
            assert len(reduced['reps'])==3 and reduced['source_repositories']==expected_sources
            assert reduced['baseline_commit']==expected_sources['iqs']['commit']
            assert reduced['candidate_source_manifest_sha256']==(candidate_manifest_sha if variant=='candidate' else None)
            for row,thinrep in zip(reps,reduced['reps']):
                identity=(variant,packets,row['rep']);assert identity not in seen;seen.add(identity)
                h=sha(dump(row).encode());assert h not in rep_hashes;rep_hashes.add(h)
                for name in ['rep','cold_or_warm','delivery_ms','fixture_ms','export_ms','verify_ms','spawn_summary']:
                    assert thinrep[name]==row[name],(key,row['rep'],name)
                expected_counts={'imported_packages':packets,'ack_status_counts':{'accepted':packets},'work_item_status_counts':{'delivered':packets},'delivery_state_counts':{'delivered':packets}}
                assert thinrep['verification_counts']==expected_counts
                for name,value in expected_counts.items(): assert row['verification'][name]==value
                assert row['cold_or_warm']==('cold' if row['rep']==1 else 'warm')
                # Raw snapshot is already normalized by original DeliveryRun.
                # Compare every stored semantic byte; do not drop extra fields.
                snap=row['semantic_snapshot'];assert snap==row['verification']['semantic_snapshot']
                assert all(len(value)==packets for value in snap.values())
                snapshots[packets].add(dump(snap))
                assert row['spawn_summary']['spawn_count']==sum(op['count'] for op in row['spawn_summary']['by_operation'].values())
            assert len(raw['spawns'])==sum(row['spawn_summary']['spawn_count'] for row in reps)
            assert all(spawn['returncode']==0 for spawn in raw['spawns'])
            delivery=[r['delivery_ms'] for r in reps]
            expected_stat={'median':round(statistics.median(delivery),1),'min':round(min(delivery),1),'max':round(max(delivery),1),'stdev':round(statistics.stdev(delivery),1),'values':[round(v,1) for v in delivery]}
            cell=summary['results'][str(packets)][variant]
            assert cell['delivery_ms']==expected_stat
            assert cell['repetitions']==3
            assert cell['spawn_breakdown']==reps[0]['spawn_summary']
            spawn_counts=[r['spawn_summary']['spawn_count'] for r in reps]
            assert cell['spawn_count']=={'median':statistics.median(spawn_counts),'values':spawn_counts}
            assert summary['performance'][str(packets)][variant]==expected_stat
            cells.append({'key':key,'source_file_sha256':sha(raw_path.read_bytes()),'rep_count':3,'delivery_ms':delivery,'spawn_counts':spawn_counts,'all_original_counts_match':True,'first_rep_spawn_breakdown_not_median':True})
        assert len(snapshots[packets])==1
        eq={'snapshots_compared':6,'distinct_normalized_snapshots':1,'semantic_equivalence_passed':True}
        for k,v in eq.items():
            assert summary['semantic_equivalence'][str(packets)][k]==v
            assert semantic[str(packets)][k]==v
        b=summary['results'][str(packets)]['baseline']['delivery_ms']['median']
        c=summary['results'][str(packets)]['candidate']['delivery_ms']['median']
        assert summary['performance'][str(packets)]['speedup_ratio_baseline_over_candidate']==round(b/c,3)
        assert summary['performance'][str(packets)]['performance_improvement_observed']==(c<b)
    assert len(seen)==24 and len(rep_hashes)==24
    preserved_root=ROOT/'runs/close-support31/perf/completed-matrix-records'
    preservation=load(preserved_root/'preservation.json')
    preserved_count=0
    for item in preservation['records']:
        original=(preserved_root/item['name']).read_bytes()
        assert sha(original)==item['sha256']
        assert load(preserved_root/item['name'])==load(LAB/'bench/runs'/item['name'])
        preserved_count+=len(json.loads(original)['reps'])
    assert preserved_count==21
    temp=Path(tempfile.mkdtemp(prefix='.pc31-',dir=ROOT))
    patch_checks=[]
    try:
        target=temp/'variant'
        for row in candidate_manifest['files']:
            local=target/row['path'];local.parent.mkdir(parents=True,exist_ok=True)
            raw=(LAB/'vendor_upstream'/row['path']).read_bytes()
            assert sha(raw)==row['baseline_sha256']
            local.write_bytes(raw)
        p=subprocess.run(['git','apply','--unsafe-paths','-p1','--directory',str(target),'-'],input=(LAB/'integration/candidate.patch').read_bytes(),capture_output=True)
        assert p.returncode==0,p.stderr.decode('utf8',errors='replace')
        for row in candidate_manifest['files']:
            raw=(target/row['path']).read_bytes()
            assert len(raw)==row['candidate_bytes'] and sha(raw)==row['candidate_sha256']
            patch_checks.append({'path':row['path'],'baseline_sha256':row['baseline_sha256'],'candidate_sha256':sha(raw),'matches':True})
    finally: shutil.rmtree(temp)
    cleanup=load(ROOT/'runs/close-support31/perf/benchmark-cleanup.json')
    resumed=load(ROOT/'runs/close-support31/perf/benchmark-resume-cleanup.json')
    assert cleanup['removed'] and not Path(cleanup['root']).exists()
    assert resumed['removed'] and not Path(resumed['root']).exists()
    result={'protocol':'iqs.independent_perf_measurement_verify/1.0','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'status':'passed','distinct_measurements':24,'cells':cells,'raw_semantic_snapshots_already_normalized':True,'normalized_snapshot_distinct_count_by_packet':{str(k):len(v) for k,v in snapshots.items()},'speedup_ratios':{k:v['speedup_ratio_baseline_over_candidate'] for k,v in summary['performance'].items()},'candidate_manifest_sha256':candidate_manifest_sha,'patched_source_checks':patch_checks,'own_patch_temp_removed':not temp.exists(),'initial_timed_out_root_removed':True,'resumed_root_removed':True,'benchmark_success_initial':False,'preserved_original_cell_file_hashes_verified':True,'resumed_preserved_measurements':preserved_count,'resumed_new_measurements':3,'production_ready':False,'findings':all_findings,'limitations':['Baseline/candidate ran in fixed sequence on an uncontrolled desktop; descriptive medians only, not a causal speedup estimate or confidence guarantee.','Each cell spawn_breakdown is its first rep, not aggregate/median timing; per-rep raw records retain all values.','Cold/warm labels are process order; no OS cache purge.','Production integration/public-CLI authority authorization and 2000-company throughput are not established.']}
    (OUT/'final-measurement-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='cells'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
