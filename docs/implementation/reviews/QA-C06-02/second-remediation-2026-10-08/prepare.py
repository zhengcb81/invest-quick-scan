"""Receive QA-C06-02 read-only and freeze a private offline test copy."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

IQS = Path(__file__).resolve().parents[5]
SOURCE = Path('C:/Users/郑曾波/Projects/StockQAbyLLM')
BASE = '361a721df382c468640b27bbafc484e31c8aa321'
LEGACY = '09f68a69bbdbf76e3a4fff63043cdd4815572e5b'
RESULT = 'b6eaa082e6e1df1306fa144bd623aa6de68213a1'
HEAD = 'a39d7eafceacfa1114f5e5cb094eadb32030652c'
OWN = IQS / 'runs/qa-c06-r2-2026-10-08-01'
INTAKE = IQS / 'docs/implementation/intake/QA-C06-02/2026-10-08-second-remediation'

def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def git(*args):
    return subprocess.run(['git','-C',str(SOURCE),*args], capture_output=True,
        check=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).stdout

def main():
    assert git('rev-parse','HEAD').decode().strip() == HEAD
    status = git('status','--porcelain=v1').decode('utf-8')
    assert len(status.splitlines()) == 7 and all(x.startswith('?? ') for x in status.splitlines())
    delta = git('diff','--name-only',BASE,RESULT).decode().splitlines()
    later = git('diff','--name-only',RESULT,HEAD).decode().splitlines()
    assert all(p.startswith('docs/handoff/QA-C06-02/') or p=='.gitignore' for p in later)
    OWN.mkdir(parents=True, exist_ok=False)
    INTAKE.mkdir(parents=True, exist_ok=False)
    save(INTAKE/'source-baseline.json', dict(head=HEAD,result=RESULT,base=BASE,
        branch=git('branch','--show-current').decode().strip(),status=status,
        changed_paths=delta,post_result_paths=later,source_written=False))
    manifest = json.loads((SOURCE/'docs/handoff/QA-C06-02/artifacts.json').read_text('utf-8'))
    matches=[]
    for item in manifest['artifacts']:
        rel=PurePosixPath(item['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        p=SOURCE.joinpath(*rel.parts)
        assert not p.is_symlink() and p.resolve().is_relative_to(SOURCE.resolve())
        data=p.read_bytes()  # opaque hash only for .secrets.baseline; never copied/printed
        blob=git('show',HEAD+':'+str(rel))
        matches.append(dict(path=str(rel),bytes=len(data),sha256=sha(data),
            matched=len(data)==item['bytes'] and sha(data)==item['sha256'],
            git_sha256=sha(blob),exact=data==blob,
            eol_equivalent=data.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n'),
            opaque_only=str(rel)=='.secrets.baseline'))
    save(INTAKE/'artifact-verification.json', matches)
    assert all(x['matched'] and x['eol_equivalent'] for x in matches)
    # Only tracked inert source/test/schema and docs. No API configuration, DB,
    # cache, .env, credential baseline or untracked pilots enter the snapshot.
    snapshot=[]
    with tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',RESULT,
            'src','tests','main_with_llm.py','pyproject.toml')), mode='r:') as archive:
        for member in archive.getmembers():
            rel=PurePosixPath(member.name)
            assert not rel.is_absolute() and '..' not in rel.parts
            assert member.isfile() or member.isdir()
            if member.isdir(): continue
            allowed = (str(rel) in {'main_with_llm.py','pyproject.toml'} or
                rel.suffix=='.py' or (str(rel).startswith('src/config/quick_scan_') and rel.suffix=='.json') or
                (str(rel).startswith('tests/fixtures/') and rel.suffix in {'.json','.sql'}))
            if not allowed: continue
            data=archive.extractfile(member).read()
            raw=(SOURCE/Path(*rel.parts)).read_bytes()
            assert raw.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'), str(rel)
            # Execute RECEIVED WORKTREE byte convention, anchored to the result
            # Git blob and to fixed-input SHA; do not normalize frozen fixtures.
            target=OWN/'qa'/Path(*rel.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            snapshot.append(dict(path=str(rel),bytes=len(raw),sha256=sha(raw),git_sha256=sha(data)))
    for path in sorted((SOURCE/'docs/handoff/QA-C06-02').rglob('*')):
        if path.is_dir(): continue
        assert not path.is_symlink()
        rel=path.relative_to(SOURCE).as_posix()
        blob=git('show',HEAD+':'+rel)
        raw=path.read_bytes()
        assert raw.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
        target=INTAKE/'worker'/path.relative_to(SOURCE/'docs/handoff/QA-C06-02')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
    save(OWN/'snapshot.json',snapshot)
    save(INTAKE/'verification/source-snapshot.json',snapshot)
    (OWN/'guard').mkdir()
    guard=IQS/'docs/implementation/reviews/EVID-LAB-01/lab_sitecustomize.py'
    (OWN/'guard/sitecustomize.py').write_bytes((Path(__file__).parent/'sitecustomize.py').read_bytes())
    legacy=git('show',LEGACY+':src/utils/quick_scan_work_store.py')
    (OWN/'legacy_work_store.py').write_bytes(legacy)
    (INTAKE/'verification/v5-work-store-source.py').write_bytes(legacy)
    (OWN/'remaining_cases.py').write_bytes((Path(__file__).parent/'remaining_cases.py').read_bytes())
    (INTAKE/'verification/remaining-cases-executed.py').parent.mkdir(parents=True,exist_ok=True)
    (INTAKE/'verification/remaining-cases-executed.py').write_bytes((OWN/'remaining_cases.py').read_bytes())
    (OWN/'controller_cases.py').write_bytes((Path(__file__).parent.parent/'acceptance_cases.py').read_bytes())
    (INTAKE/'verification/controller-cases-executed.py').write_bytes((OWN/'controller_cases.py').read_bytes())
    for name in ('tmp','logs'): (OWN/name).mkdir()
    print(json.dumps(dict(snapshot_files=len(snapshot),artifacts=len(matches),
        eol_differences=sum(not x['exact'] for x in matches),source_written=False)))

if __name__=='__main__': main()
