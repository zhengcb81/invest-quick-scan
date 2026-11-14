"""Preserve this review evidence then remove only owned p114r1a artifacts."""
from __future__ import annotations
import importlib.util,json,os,stat
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r1_controller',HERE/'r1_acceptance_run.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
assert c.WORK.resolve()==c.ROOT/'runs/p114r1a'
assert json.loads((c.WORK/'ownership.json').read_text(encoding='utf-8'))['root']==str(c.WORK)
assert not (c.INTAKE/'cleanup.json').exists()
state=c.git_state()
assert state[0]['stdout'].strip()==c.EXPECTED
c.old.write(c.INTAKE/'source-git-after.json',state)
frozen=json.loads((c.INTAKE/'source-freeze.json').read_text(encoding='utf-8'))
changed=[]
for entry in frozen['files']:
    path=c.SOURCE/entry['path'];c.old.safe(path)
    if c.old.digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:changed.append(entry['path'])
assert not changed,changed
inputs=c.old.inspect_inputs()
records=[json.loads(p.read_text(encoding='utf-8')) for p in (c.INTAKE/'logs').glob('*.result.json')]
assert records and all(r['terminal'] and not r['timed_out'] for r in records)
cim=json.loads((c.INTAKE/'cim-terminal-check-03.json').read_text(encoding='utf-8-sig'))
assert cim['examined']=='successful read-only CIM query' and cim['matching_count']==0
assert cim['recorded_child_pids_still_running']==[]
for leaf,label in [('.acceptance-cases/results.json','counterexample-results-01.json'),
                   ('.acceptance-followup/results.json','counterexample-results-02.json'),
                   ('.acceptance-history-corrected/results.json','counterexample-results-03.json')]:
    c.old.write(c.INTAKE/label,json.loads((c.LAB/leaf).read_text(encoding='utf-8')))
src=c.LAB/'docs/handoff/FACT-CONTENT-01/remediation-01'
dst=c.INTAKE/'received-handoff/FACT-CONTENT-01/remediation-01'
assert not dst.exists()
for path in src.rglob('*'):
    c.old.safe(path)
    if path.is_file():
        target=dst/path.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(path.read_bytes())
        assert c.old.digest(target)==c.old.digest(path)

# The one deliberately created reparse object is separately enumerated.  Remove
# the junction itself with rmdir, never descend into or delete its target here.
link=c.LAB/'.acceptance-cases/junction/linked'
target=c.LAB/'.acceptance-cases/junction-target'
c.old.safe(link.parent);c.old.safe(target)
assert link.lstat().st_file_attributes & 0x400
assert link.resolve()==target.resolve()
target_hash=c.old.digest(target/'semantic-cases.json')
c.old.write(c.INTAKE/'junction-cleanup-before.json',{'link':str(link),'target':str(target),'target_sha256':target_hash,
                                                 'operation':'os.rmdir removes link only'})
os.rmdir(link)
assert not link.exists() and c.old.digest(target/'semantic-cases.json')==target_hash

files=[];dirs=[]
for path in c.WORK.rglob('*'):
    c.old.safe(path)
    if path.is_file():files.append({'path':path.relative_to(c.WORK).as_posix(),'bytes':path.stat().st_size,'sha256':c.old.digest(path)})
    elif path.is_dir():dirs.append(path.relative_to(c.WORK).as_posix())
    else:raise RuntimeError(f'Unexpected file object: {path}')
c.old.safe(c.WORK)
c.old.write(c.INTAKE/'cleanup-inventory.json',{'root':str(c.WORK),'files':files,'directories':dirs})
actual={p.relative_to(c.WORK).as_posix() for p in c.WORK.rglob('*') if p.is_file()}
assert actual=={x['path'] for x in files}
for entry in files:
    path=c.WORK/entry['path'];c.old.safe(path)
    assert path.stat().st_size==entry['bytes'] and c.old.digest(path)==entry['sha256']
for entry in files:(c.WORK/entry['path']).unlink()
for rel in sorted(dirs,key=lambda p:len(Path(p).parts),reverse=True):(c.WORK/rel).rmdir()
c.WORK.rmdir()
xml=ET.parse(c.INTAKE/'fact-r1-regression.xml').getroot()
suites=list(xml.iter('testsuite'))
counts={k:sum(int(s.attrib[k]) for s in suites) for k in ['tests','failures','errors','skipped']}
assert counts=={'tests':115,'failures':0,'errors':0,'skipped':0}
c.old.write(c.INTAKE/'acceptance-result.json',{'at':c.old.now(),'FACT-CONTENT-01':'changes_requested',
    'EVID-REF-02':'handoff_pending_not_retested','fact_head':c.EXPECTED,'source_files_unchanged':len(frozen['files']),
    'artifact_hashes_matched':len(frozen['artifacts']),'inputs':inputs,'regression':counts,
    'eight_mechanical_counterexamples_confirmed':True,'legacy_public_read_missing':True,
    'three_content_findings_static_only':True,'processes':records,'paid_api_requests':0,
    'company_document_downloads':0,'product_source_written':False,'codegraph_init_user_authorized':True,
    'global_gates_closed':False})
c.old.write(c.INTAKE/'cleanup.json',{'at':c.old.now(),'owned_root':str(c.WORK),'files_removed':len(files),
    'directories_removed_including_root':len(dirs)+1,'junction_removed_without_traversal':True,
    'junction_target_unchanged_until_inventory':True,'strict_set_lstat_single_link_bytes_sha_verified':True,
    'source_changed':changed,'verified_absent':not c.WORK.exists(),'c15a_or_shared_temp_deleted':False})
print(json.dumps({'status':'changes_requested','regression':counts,'files_cleaned':len(files),
                 'directories_cleaned':len(dirs)+1,'owned_root_absent':not c.WORK.exists()},ensure_ascii=False))
