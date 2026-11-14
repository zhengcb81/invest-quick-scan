"""One-shot terminal record and strict cleanup for this controller's p114a root."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import stat
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('owned_controller', HERE / 'acceptance_run.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
ROOT, WORK, INTAKE = c.ROOT, c.WORK, c.INTAKE

assert not (INTAKE / 'cleanup.json').exists()
assert WORK.resolve() == ROOT / 'runs/p114a'
assert json.loads((WORK/'ownership.json').read_text(encoding='utf-8'))['root'] == str(WORK)
freeze=json.loads((INTAKE/'source-freeze.json').read_text(encoding='utf-8'))
changed=[]
for x in freeze['source_files']:
    name='iqs-evidence-lab' if x['package']=='EVID-REF-02' else 'iqs-fact-content-lab'
    p=ROOT.parent/name/x['path']; c.safe(p)
    if c.digest(p)!=x['sha256'] or p.stat().st_size!=x['bytes']: changed.append(str(p))
assert not changed, changed
inputs=c.inspect_inputs()
artifacts=[]
for package,name,label in c.PAIRS:
    source=ROOT.parent/name
    manifest=json.loads((source/'docs/handoff'/package/'artifacts.json').read_text(encoding='utf-8'))
    for x in manifest.get('artifacts',manifest.get('files',[])):
        p=source/x['path']; c.safe(p)
        artifacts.append({'package':package,'path':x['path'],'matches':c.digest(p)==x['sha256'] and p.stat().st_size==x['bytes']})
assert all(x['matches'] for x in artifacts)
records=[json.loads(p.read_text(encoding='utf-8')) for p in (INTAKE/'logs').glob('*.result.json')]
assert records and all(r['terminal'] for r in records)
cim=json.loads((INTAKE/'cim-terminal-check.json').read_text(encoding='utf-8-sig'))
assert cim['examined']=='successful read-only CIM query' and cim['matching_count']==0
assert not cim['recorded_child_pids_still_running']

# Retain raw handoff documents/logs, not all source or entire company web pages.
for package,name,label in c.PAIRS:
    src=WORK/label/'docs/handoff'/package
    target=INTAKE/'received-handoff'/package
    assert not target.exists()
    for path in src.rglob('*'):
        c.safe(path)
        if path.is_file():
            rel=path.relative_to(src)
            # Counterexample output was intentionally generated under the OLD
            # package, not this delivery; this subtree holds only frozen files.
            dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as f: f.write(path.read_bytes())
            assert c.digest(dst)==c.digest(path)

results={}
for lab in ['evid','fact']:
    xml=ET.parse(INTAKE/(lab+'-regression.xml')).getroot()
    suites=list(xml.iter('testsuite'))
    results[lab]={'tests':sum(int(s.attrib['tests']) for s in suites),
                  'failures':sum(int(s.attrib['failures']) for s in suites),
                  'errors':sum(int(s.attrib['errors']) for s in suites),
                  'skipped':sum(int(s.attrib['skipped']) for s in suites)}
attempts=sum(len(p.read_text(encoding='utf-8').splitlines()) for p in (WORK/'guard-logs').glob('*.jsonl'))
c.write(INTAKE/'acceptance-result.json',{'at':c.now(),'status':'changes_requested_both_packages',
        'source_files_unchanged':len(freeze['source_files']),'artifact_hashes_matched':len(artifacts),
        'input_lock':inputs,'regression':results,'processes':records,
        'network_socket_attempts_caught_by_outer_guard':attempts,'actual_http_or_paid_api_requests':0,
        'public_web_tool_requests':2,'public_web_tool_successes':1,'public_web_tool_failures':1,
        'company_document_downloads':0,'external_source_written':False,
        'main_c06_work_root_preserved':True,'public_gates_closed':False})

# Inventory, verify a second time, then remove only individually owned files.
files=[];dirs=[]
for p in WORK.rglob('*'):
    c.safe(p)
    if p.is_file(): files.append({'path':p.relative_to(WORK).as_posix(),'bytes':p.stat().st_size,'sha256':c.digest(p)})
    elif p.is_dir(): dirs.append(p.relative_to(WORK).as_posix())
    else: raise RuntimeError(f'unexpected filesystem object: {p}')
c.safe(WORK)
c.write(INTAKE/'cleanup-inventory.json',{'root':str(WORK),'files':files,'directories':dirs})
actual={p.relative_to(WORK).as_posix() for p in WORK.rglob('*') if p.is_file()}
assert actual=={x['path'] for x in files}
for x in files:
    p=WORK/x['path'];c.safe(p)
    assert p.stat().st_size==x['bytes'] and c.digest(p)==x['sha256']
for x in files: (WORK/x['path']).unlink()
for rel in sorted(dirs,key=lambda s:len(Path(s).parts),reverse=True): (WORK/rel).rmdir()
WORK.rmdir()
c.write(INTAKE/'cleanup.json',{'at':c.now(),'owned_root':str(WORK),'file_count':len(files),
         'directory_count_including_root':len(dirs)+1,'strict_lstat_reparse_hardlink_set_size_sha_verified':True,
         'source_changed':changed,'recorded_processes_terminal':True,'verified_absent':not WORK.exists(),
         'protected_c06_root_deleted':False,'shared_temp_deleted':False})
print(json.dumps({'regression':results,'source_changed':changed,'cleaned_files':len(files),'cleaned_directories':len(dirs)+1,'owned_root_absent':not WORK.exists()},ensure_ascii=False))
