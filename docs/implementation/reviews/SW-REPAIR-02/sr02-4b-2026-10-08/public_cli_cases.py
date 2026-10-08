"""Real public CLI processes for the repaired decoding chain; synthetic DB only."""
import json
import os
from pathlib import Path
import subprocess
import sys

from acceptance_cases import two_backups
from stockwiki.quick_scan_backup import quick_scan_backup_root
from stockwiki.quick_scan_backup_manifest import MANIFEST_NAME,OWNER_REGISTRY_NAME

OWN=Path(os.environ['E97_OWNED_ROOT'])
records=[]

def call(workspace,operation,*arguments):
    command=[sys.executable,'-B','-X','utf8','-m','stockwiki.cli','--root',str(workspace.root),
        'quick-scan-backup',operation,*arguments]
    process=subprocess.run(command,cwd=OWN/'runtime',env=dict(os.environ),capture_output=True,timeout=45)
    label=workspace.root.relative_to(OWN).as_posix().replace('/','-')+'-'+operation
    (OWN/'logs'/(label+'.stdout.log')).write_bytes(process.stdout)
    (OWN/'logs'/(label+'.stderr.log')).write_bytes(process.stderr)
    records.append(dict(case=workspace.root.name,operation=operation,command=command,returncode=process.returncode))
    return process

def document(process):
    # The actual CLI emits canonical JSON; tolerate its logging prefix only.
    for line in reversed(process.stdout.decode('utf-8').splitlines()):
        if line.startswith(('{','[')):
            return json.loads(line)
    raise AssertionError('public CLI emitted no JSON result')

for label,payload in [('ff',b'\xff'),('truncated',b'{"files": ["\xe4\xb8')]:
    base=OWN/'public-cli-corrected'/label
    base.mkdir(parents=True)
    paths=two_backups(base)
    root=quick_scan_backup_root(paths)
    foreign=root/'foreign_corrupt_bytes'
    foreign.mkdir()
    manifest=foreign/MANIFEST_NAME
    manifest.write_bytes(payload)
    listed=call(paths,'list')
    assert listed.returncode==0,listed.stderr.decode('utf-8')
    data=document(listed)
    rows=data if isinstance(data,list) else data['backups']
    row=next(row for row in rows if row['name']==foreign.name)
    assert row['manifest_shape']=='invalid' and not row['complete']
    assert (root/'backup_a').exists() and (root/'backup_z').exists()
    pruned=call(paths,'prune','--keep','1')
    assert pruned.returncode==0,pruned.stderr.decode('utf-8')
    receipt=document(pruned)
    assert receipt['removed']==['backup_a'] and receipt['kept']==['backup_z']
    assert foreign.name in receipt['skipped'] and manifest.read_bytes()==payload
    refused=call(paths,'verify','--name',foreign.name)
    assert refused.returncode!=0 and b'manifest_invalid' in refused.stdout+refused.stderr
    assert manifest.read_bytes()==payload

base=OWN/'public-cli-corrected/registry'
base.mkdir(parents=True)
paths=two_backups(base)
root=quick_scan_backup_root(paths)
registry=root/OWNER_REGISTRY_NAME
registry.write_bytes(b'\xff')
refused=call(paths,'prune','--keep','1')
assert refused.returncode!=0 and b'owner_registry_invalid' in refused.stdout+refused.stderr
assert registry.read_bytes()==b'\xff' and (root/'backup_a').exists() and (root/'backup_z').exists()
(OWN/'public-cli-result.json').write_text(json.dumps(dict(synthetic_only=True,checks=records,
    outside_http=0,paid_calls=0,downloads=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(public_cli_checks=len(records),valid_cases=4,expected_refusals=3)))
