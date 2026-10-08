"""Inventory only the exact private root with lstat, single-link and byte checks."""
import hashlib
import json
import os
import stat
from pathlib import Path

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/'runs/qa-c06-r2-2026-10-08-01'
INTAKE=IQS/'docs/implementation/intake/QA-C06-02/2026-10-08-second-remediation'
assert OWN.resolve()==OWN and OWN.is_dir()
files=[]
dirs=[]
for current,children,leaves in os.walk(OWN,followlinks=False):
    for name in ['.']+children+leaves:
        path=Path(current) if name=='.' else Path(current)/name
        info=path.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400, 'reparse/link refused'
        assert path==OWN or OWN in path.parents
        if name=='.': continue
        rel=path.relative_to(OWN).as_posix()
        if stat.S_ISDIR(info.st_mode): dirs.append(rel)
        else:
            assert stat.S_ISREG(info.st_mode) and info.st_nlink==1, 'special file/hardlink refused'
            data=path.read_bytes()
            files.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
body={'schema':'qa100_cleanup_baseline/1','absolute_root':str(OWN),'files':sorted(files,key=lambda x:x['path']),
      'directories':sorted(dirs),'hardlinks':0,'reparse_points':0,'known_session_exits':{'52864':0,'72795':0},
      'other_commands':'focused boundary/public commands ran synchronously and have exited'}
path=INTAKE/'cleanup-baseline.json'
path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(INTAKE/'cleanup-lstat.json').write_text(json.dumps({'schema':'qa100_cleanup_lstat/1','baseline_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'root':str(OWN),'files_verified':len(files),'directories_verified':len(dirs),'hardlinks':0,'reparse_points':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'owned_files':len(files),'owned_directories':len(dirs),'hardlinks':0,'reparse_points':0}))
