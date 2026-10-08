"""Receive QA-C06-02 read-only and freeze a private offline test copy."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

IQS = Path(__file__).resolve().parents[4]
SOURCE = Path('C:/Users/郑曾波/Projects/StockQAbyLLM')
BASE = '09f68a69bbdbf76e3a4fff63043cdd4815572e5b'
RESULT = '7e71b2cd8bbb042a72b282e83cb361a1ddcbb8b7'
HEAD = 'a12bc29bf20f5fc48df69236f2e07c3c2472bacd'
OWN = IQS / 'runs/qa-c06-02-2026-10-08-01'
INTAKE = IQS / 'docs/implementation/intake/QA-C06-02/2026-10-08'

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
    assert all(p.startswith('docs/handoff/QA-C06-02/') for p in later)
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
                (str(rel).startswith('tests/fixtures/') and rel.suffix=='.json'))
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
    (OWN/'guard/sitecustomize.py').write_bytes(guard.read_bytes())
    for name in ('tmp','logs'): (OWN/name).mkdir()
    print(json.dumps(dict(snapshot_files=len(snapshot),artifacts=len(matches),
        eol_differences=sum(not x['exact'] for x in matches),source_written=False)))

if __name__=='__main__': main()
