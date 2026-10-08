"""Freeze received remediation bytes in a new IQS-only snapshot; source is read-only."""
import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

IQS = Path(__file__).resolve().parents[5]
SOURCE = Path('C:/Users/郑曾波/Projects/iqs-evidence-lab')
RESULT = 'cef3d95969671d10b42138ed97010c9c164b5118'
RECEIVED = '2c0efb6370e401ca84d5f23cd5047de2bbfdec0a'
OWN = IQS / 'runs/evid-lab-lr02b-2026-10-08-01'
INTAKE = IQS / 'docs/implementation/intake/EVID-LAB-01/2026-10-08-lr02b'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    return subprocess.run(['git','-C',str(SOURCE),*args], env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),
                          capture_output=True, check=True).stdout

def blobs(ref, paths):
    stream = io.BytesIO(subprocess.run(['git','-C',str(SOURCE),'cat-file','--batch'],
        input=(''.join(ref+':'+path+'\n' for path in paths)).encode('utf-8'),
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True,check=True,timeout=60).stdout)
    found = {}
    for path in paths:
        header=stream.readline().decode().strip().split()
        assert len(header)==3 and header[1]=='blob', path
        data=stream.read(int(header[2])); assert stream.read(1)==b'\n'
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==header[0]
        found[path]=(header[0],data)
    assert not stream.read()
    return found


def main():
    assert git('rev-parse','HEAD').decode().strip() == RECEIVED, 'source moved before freeze'
    assert not git('status','--porcelain=v1'), 'source dirty before freeze'
    non_handoff = git('diff','--name-only',RESULT,RECEIVED).decode().splitlines()
    assert all(p.startswith('docs/handoff/EVID-LAB-01/') or p == 'tools/make_artifacts.py' for p in non_handoff), 'runtime source changed after result'
    OWN.mkdir(parents=True, exist_ok=False)
    INTAKE.mkdir(parents=True, exist_ok=False)
    save(INTAKE/'source-baseline.json', {'branch':git('branch','--show-current').decode().strip(),
         'head':RECEIVED,'result_commit':RESULT,'status':'','post_result_paths':non_handoff,
         'remotes':git('remote').decode().splitlines(),'source_written':False})
    manifest = json.loads((SOURCE/'docs/handoff/EVID-LAB-01/artifacts.json').read_text('utf-8'))
    matches = []
    committed = blobs(RECEIVED, [row['path'] for row in manifest['files']])
    for item in manifest['files']:
        rel = PurePosixPath(item['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        source = SOURCE.joinpath(*rel.parts)
        assert source.resolve().is_relative_to(SOURCE.resolve()) and not source.is_symlink()
        data = source.read_bytes()
        oid, blob = committed[item['path']]
        matches.append({'path':item['path'],'bytes':len(data),'worktree_sha256':sha(data),
            'worktree_matched':len(data)==item['bytes'] and sha(data)==item['worktree_sha256'],
            'git_blob_oid':oid,'git_oid_matched':oid==item['git_blob_oid'],'git_blob_sha256':sha(blob),
            'exact':data==blob,'eol_equivalent':data.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')})
        if item['path'].startswith('docs/handoff/EVID-LAB-01/'):
            target = INTAKE/'worker'/Path(*rel.parts[3:])
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
    (INTAKE/'worker/artifacts.json').write_bytes((SOURCE/'docs/handoff/EVID-LAB-01/artifacts.json').read_bytes())
    save(INTAKE/'artifact-verification.json',matches)
    assert len(matches)==141 and all(i['worktree_matched'] and i['git_oid_matched'] and i['eol_equivalent'] for i in matches), 'manifest mismatch'
    snapshot=[]
    with tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',RECEIVED)),mode='r:') as archive:
        for member in archive.getmembers():
            rel=PurePosixPath(member.name)
            assert not rel.is_absolute() and '..' not in rel.parts and (member.isdir() or member.isfile())
            if member.isdir(): continue
            data=archive.extractfile(member).read()
            target=OWN/'lab'/Path(*rel.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            snapshot.append({'path':str(rel),'bytes':len(data),'sha256':sha(data)})
    save(OWN/'snapshot.json',snapshot)
    save(INTAKE/'verification/source-snapshot.json',snapshot)
    old=IQS/'docs/implementation/reviews/EVID-LAB-01'
    (OWN/'guard').mkdir()
    (OWN/'guard/sitecustomize.py').write_bytes((old/'lab_sitecustomize.py').read_bytes())
    (OWN/'logs').mkdir()
    (OWN/'tmp').mkdir()
    print(json.dumps({'snapshot_files':len(snapshot),'artifacts_dual_hash_matched':len(matches),
          'eol_differences':sum(not i['exact'] for i in matches),'received_head':RECEIVED,'source_clean':True}))

if __name__=='__main__': main()
