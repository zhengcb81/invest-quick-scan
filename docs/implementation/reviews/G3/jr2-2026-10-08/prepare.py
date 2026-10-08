"""Freeze accepted QA only; StockWiki authorization is still pending."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / 'runs/jr2-2026-10-08-01'
OUT = IQS / 'docs/implementation/intake/G3/2026-10-08-jr2'
SOURCE = 'C:/Users/郑曾波/Projects/StockQAbyLLM'
RESULT = 'b6eaa082e6e1df1306fa144bd623aa6de68213a1'
HEAD = 'a39d7eafceacfa1114f5e5cb094eadb32030652c'


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', SOURCE, *args])


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    original = json.loads((IQS / 'docs/implementation/intake/G3/2026-10-08-joint/source-baseline.json').read_text('utf-8'))[0]
    status = git('status', '--porcelain=v1').decode()
    assert status == original['status'], 'Reconcile source drift first'
    assert not OWN.exists() and not OUT.exists()
    OWN.mkdir(parents=True)
    OUT.mkdir(parents=True)
    expected = json.loads((IQS / 'docs/implementation/intake/G3/2026-10-08-joint/source-snapshot.json').read_text('utf-8'))[0]['files']
    catalog = {row['path']: row for row in expected}
    export = git('archive', '--format=tar', RESULT, 'src', 'tests', 'main_with_llm.py', 'pyproject.toml')
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(export), mode='r:') as archive:
        for entry in archive.getmembers():
            path = PurePosixPath(entry.name)
            assert not path.is_absolute() and '..' not in path.parts and (entry.isdir() or entry.isfile())
            if not entry.isfile() or entry.name not in catalog:
                continue
            raw = archive.extractfile(entry).read()
            lf = raw.replace(b'\r\n', b'\n')
            accepted = [data for data in [raw, lf, lf.replace(b'\n', b'\r\n')]
                       if hashlib.sha256(data).hexdigest() == catalog[entry.name]['sha256']]
            assert accepted, 'Frozen EOL convention missing'
            target = OWN / 'qa' / entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(accepted[0])
            seen.add(entry.name)
    assert seen == set(catalog)
    for name in ['guard', 'tmp', 'logs']:
        (OWN / name).mkdir()
    (OWN / 'guard/sitecustomize.py').write_bytes((IQS / 'docs/implementation/reviews/QA-C06-02/second-remediation-2026-10-08/sitecustomize.py').read_bytes())
    save(OUT / 'source-baseline.json', dict(source=SOURCE, result=RESULT, head=HEAD, status=status))
    save(OUT / 'source-snapshot.json', expected)
    print(json.dumps(dict(frozen_qa_files=len(seen), external_written=False)))


if __name__ == '__main__':
    main()
