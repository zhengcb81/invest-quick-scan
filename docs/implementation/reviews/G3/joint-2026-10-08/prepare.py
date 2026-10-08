"""Freeze both accepted owners from Git, never execute a dynamic source tree."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import sys
import stat

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / 'runs/joint-2026-10-08-01'
OUT = IQS / 'docs/implementation/intake/G3/2026-10-08-joint'
OWNERS = [
    dict(name='qa', source='C:/Users/郑曾波/Projects/StockQAbyLLM',
         result='b6eaa082e6e1df1306fa144bd623aa6de68213a1',
         received='a39d7eafceacfa1114f5e5cb094eadb32030652c',
         manifest='docs/implementation/intake/QA-C06-02/2026-10-08-second-remediation/verification/source-snapshot.json',
         archive=['src', 'tests', 'main_with_llm.py', 'pyproject.toml']),
    dict(name='sw', source='C:/Users/郑曾波/Projects/StockWiki',
         result='cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa',
         received='d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff',
         manifest='docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/source-snapshot.json',
         archive=['stockwiki', 'tests', 'pyproject.toml'])]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git(owner, *args):
    return subprocess.run(['git', '-C', owner['source'], *args], capture_output=True,
                          check=True, timeout=60,
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).stdout


def main():
    states = []
    for owner in OWNERS:
        head = git(owner, 'rev-parse', 'HEAD').decode().strip()
        assert head == owner['received'], 'Reconcile changed source before freezing'
        status = git(owner, 'status', '--porcelain=v1').decode('utf-8')
        assert (not status if owner['name'] == 'sw'
                else len(status.splitlines()) == 7 and all(x.startswith('?? ') for x in status.splitlines()))
        states.append(dict(name=owner['name'], result=owner['result'], head=head,
                           source=owner['source'], status=status, source_written=False))
    if '--resume-empty' in sys.argv:
        for root in (OWN, OUT):
            assert root.is_dir() and not list(root.iterdir()) and root.resolve() == root
            info = root.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    else:
        OWN.mkdir(parents=True, exist_ok=False)
        OUT.mkdir(parents=True, exist_ok=False)
    save(OUT / 'source-baseline.json', states)
    snapshots = []
    for owner in OWNERS:
        expected = json.loads((IQS / owner['manifest']).read_text('utf-8'))
        catalog = {row['path']: row for row in expected}
        blobs = {}
        archive = git(owner, 'archive', '--format=tar', owner['result'], *owner['archive'])
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as stream:
            for entry in stream.getmembers():
                relative = PurePosixPath(entry.name)
                assert not relative.is_absolute() and '..' not in relative.parts
                assert entry.isdir() or entry.isfile()
                if entry.isfile() and entry.name in catalog:
                    blobs[entry.name] = stream.extractfile(entry).read()
        if owner['name'] == 'sw':
            blobs['legacy_quick_scan_query.py'] = git(owner, 'show', '9f552a67:stockwiki/quick_scan_query.py')
        assert set(blobs) == set(catalog)
        rows = []
        for path, raw in blobs.items():
            normalized = raw.replace(b'\r\n', b'\n')
            candidates = [raw, normalized, normalized.replace(b'\n', b'\r\n')]
            # A mixed-EOL original cannot be reconstructed by uniform conversion.
            # Recovery is allowed ONLY if the current tracked file has the exact
            # previously accepted raw hash AND equals the fixed blob modulo EOL;
            # no dynamic or missing source is accepted by filename alone.
            original = Path(owner['source']) / path
            if original.exists() and not original.is_symlink():
                original_raw = original.read_bytes()
                if (sha(original_raw) == catalog[path]['sha256'] and
                    original_raw.replace(b'\r\n', b'\n') == raw.replace(b'\r\n', b'\n')):
                    candidates.append(original_raw)
            candidates = [data for data in candidates if sha(data) == catalog[path]['sha256']]
            assert candidates, 'Accepted byte convention missing: ' + path
            data = candidates[0]
            assert len(data) == catalog[path]['bytes']
            target = OWN / owner['name'] / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append(dict(path=path, bytes=len(data), sha256=sha(data), git_sha256=sha(raw)))
        snapshots.append(dict(owner=owner['name'], files=sorted(rows, key=lambda x: x['path'])))
    (OWN / 'sw/config').mkdir(exist_ok=True)
    inert = IQS / 'docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/llm_providers.inert.yaml'
    (OWN / 'sw/config/llm_providers.yaml').write_bytes(inert.read_bytes())
    (OWN / 'guard').mkdir()
    guard = IQS / 'docs/implementation/reviews/QA-C06-02/second-remediation-2026-10-08/sitecustomize.py'
    (OWN / 'guard/sitecustomize.py').write_bytes(guard.read_bytes())
    for name in ['tmp', 'logs', 'cases']:
        (OWN / name).mkdir()
    save(OUT / 'source-baseline.json', states)
    save(OUT / 'source-snapshot.json', snapshots)
    print(json.dumps(dict(files={s['owner']: len(s['files']) for s in snapshots},
                          source_written=False, fixed_accepted_bytes=True)))


if __name__ == '__main__':
    main()
