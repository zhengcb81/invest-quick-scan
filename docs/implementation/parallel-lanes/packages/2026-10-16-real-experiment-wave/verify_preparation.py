"""Verify one independently movable package input subset; no source fallback."""
from pathlib import Path
import argparse, hashlib, json, sys

PROTOCOL='iqs.real-experiment-parallel-input-lock/1.0.0'
def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate JSON key')
        out[k]=v
    return out
def load(path):
    raw=Path(path).read_bytes()
    if len(raw)>8000000:raise ValueError('oversized manifest')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def relative(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value:
        raise ValueError('nonportable relative path')
    p=Path(value)
    if p.is_absolute() or '..' in p.parts or p.as_posix()!=value:raise ValueError('path escape')
    return p
def verify(inputs,lock,package_id=None,expected_lock_sha256=None):
    inputs=Path(inputs).resolve();lock=Path(lock)
    digest=hashlib.sha256(lock.read_bytes()).hexdigest()
    if expected_lock_sha256 is not None and digest!=expected_lock_sha256:raise ValueError('lock hash mismatch')
    doc=load(lock)
    if doc.get('protocol')!=PROTOCOL:raise ValueError('unknown input protocol')
    packages=doc['packages']; roots=[Path(p['workspace']).resolve() for p in packages]
    if len({p['package_id'] for p in packages})!=len(packages):raise ValueError('duplicate package id')
    for i,p in enumerate(roots):
        for q in roots[i+1:]:
            if p.is_relative_to(q) or q.is_relative_to(p):raise ValueError('overlapping writer roots')
    ids={p['package_id'] for p in packages}
    if package_id and package_id not in ids:raise ValueError('unknown package')
    seen=set();checked=0;total_bytes=0
    for row in doc['files']:
        path=relative(row['path']);relative(row['source_path'])
        key=path.as_posix().casefold()
        if key in seen:raise ValueError('duplicate or Windows-colliding path')
        seen.add(key)
        if not row['consumers'] or not set(row['consumers'])<=ids:raise ValueError('bad consumer set')
        if package_id and package_id not in row['consumers']:continue
        file=inputs/path
        if not file.resolve().is_relative_to(inputs) or file.is_symlink():raise ValueError('input link escape')
        raw=file.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['raw_sha256']:raise ValueError('input raw hash mismatch: '+path.as_posix())
        checked+=1;total_bytes+=len(raw)
    if not checked:raise ValueError('empty input subset')
    return {'valid':True,'package_id':package_id,'files_checked':checked,'bytes_checked':total_bytes,'lock_raw_sha256':digest,'scope':'input integrity only; not product/financial acceptance'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--lock',default=str(Path(__file__).with_name('inputs.lock.json')));p.add_argument('--package-id');p.add_argument('--expected-lock-sha256')
    a=p.parse_args()
    try:out=verify(a.inputs,a.lock,a.package_id,a.expected_lock_sha256)
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(json.dumps({'valid':False,'error':str(e)},ensure_ascii=False),file=sys.stderr);return 2
    print(json.dumps(out,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
