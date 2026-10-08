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
RESULT = 'd4360fdbbd9a83d2830066546edf1827ab424834'
RECEIVED = 'aeff0e68022f56b331a58503df7b53ed8d2b3882'
OWN = IQS / 'runs/evid-lab-second-remediation-2026-10-08-01'
INTAKE = IQS / 'docs/implementation/intake/EVID-LAB-01/2026-10-08-second-remediation'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    return subprocess.run(['git','-C',str(SOURCE),*args], env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),
                          capture_output=True, check=True).stdout

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
    for item in manifest['files']:
        rel = PurePosixPath(item['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        source = SOURCE.joinpath(*rel.parts)
        assert source.resolve().is_relative_to(SOURCE.resolve()) and not source.is_symlink()
        data = source.read_bytes()
        blob = git('show', RECEIVED+':'+item['path'])
        oid = git('rev-parse', RECEIVED+':'+item['path']).decode().strip()
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
    assert len(matches)==122 and all(i['worktree_matched'] and i['git_oid_matched'] and i['eol_equivalent'] for i in matches), 'manifest mismatch'
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
