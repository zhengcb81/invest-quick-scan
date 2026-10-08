"""Preserve new boundary output bytes and verify unchanged inputs before cleanup."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from run import IQS,OWN,LAB,INTAKE,inputs

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text('utf-8-sig'))
def save(path,body): path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

root=INTAKE/'counterexamples/published'
root.mkdir(parents=True,exist_ok=True)
for name in ('custom-period-output','historical-missing-binding-output','overflow-output'):
    source=LAB/'.controller-followup'/name
    target=root/name
    target.mkdir(exist_ok=True)
    for path in source.glob('*.json'): (target/path.name).write_bytes(path.read_bytes())
result=read(INTAKE/'verification/result.json')
assert inputs()==result['original_inputs_before'], 'original IQS drift after focused cases'
changed=[]
for item in read(OWN/'snapshot.json'):
    data=(LAB/item['path']).read_bytes()
    if len(data)!=item['bytes'] or sha(data)!=item['sha256']: changed.append(item['path'])
assert not changed, 'source export drift'
p=subprocess.run([sys.executable,'-B','-X','utf8',str(IQS/'scripts/parallel_handoff_cli.py'),
    '--catalog',str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json'),
    '--package-id','EVID-LAB-01','--input',str(INTAKE/'worker/handoff.json')],cwd=IQS,capture_output=True,check=False)
save(INTAKE/'shape-public.json',{'command_scope':'IQS public CLI shape and declared scope only',
     'exit_code':p.returncode,'result':json.loads(p.stdout.decode('utf-8'))})
assert p.returncode==0
result.update(status='changes_requested',coordinator_regression={'passed':81,'failed':0,'pytest_seconds':9.63,'command_wall_s':10.568},
    frozen_counterexamples={'passed':9,'failed':0,'unittest_seconds':2.002,'command_wall_s':2.423,
        'repeated_in_worker_suite':True,'io_predicate_adapted_to_staging':True},
    public_cli={'catalog_fixtures':34,'expectations':42,'records':350,'individual_replays_passed':34,
                'index_replays_passed':2,'index_payloads_byte_stable':True,'commands_total':39,'failed_commands':0},
    additional_batches=[{'case_methods':5,'passed':3,'failed':2,'pytest_seconds':2.68,'command_wall_s':3.281},
        {'case_methods':6,'passed':0,'failed':6,'pytest_seconds':0.64,'command_wall_s':1.161}],
    residual_groups=6,additional_counting_note='custom-period and numeric-overflow repeated through public path; not eleven independent defects',
    original_inputs_after_all_cases=inputs(),snapshot_changed_after_all_cases=changed,
    draft_status='draft_not_signed; accepted only as a non-executing draft with unresolved cost cap',
    production_database_reads_or_writes=0,source_repository_writes=0,cleanup_pending=True)
save(INTAKE/'verification/result.json',result)
for name in ('boundary_cases.py','followup_cases.py'):
    (INTAKE/'verification'/('executed-'+name)).write_bytes((OWN/name).read_bytes())
print(json.dumps({'original_inputs_unchanged':len(inputs()),'source_snapshot_unchanged':105,
      'original_cases_passed':True,'residual_groups':6,'status':'changes_requested'}))
