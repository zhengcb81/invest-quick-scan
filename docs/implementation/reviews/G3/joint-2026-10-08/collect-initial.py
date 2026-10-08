"""Archive only this synthetic batch and verify fixed inputs before cleanup."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run as h


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_state(root):
    return dict(head=subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD']).decode().strip(),
       status=subprocess.check_output(['git', '-C', root, 'status', '--porcelain=v1', '-uall']).decode())


def copy_file(source, target):
    info = source.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    assert not getattr(info, 'st_file_attributes', 0) & 0x400
    raw = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return dict(path=target.relative_to(h.IQS).as_posix(), bytes=len(raw), sha256=sha(raw))


def main():
    alias = h.actor('qa', 'actual-model-alias-snapshot', dict(op='snapshot',
        root=str(h.OWN / 'cases/b'), question_id='IQS_01'))
    assert alias['checkpoint'] is None
    source = json.loads((h.OUT / 'source-snapshot.json').read_text('utf-8'))
    unchanged, mixed = [], []
    for owner in source:
        for row in owner['files']:
            path = h.OWN / owner['owner'] / row['path']
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Source snapshot drift'
            normalized = raw.replace(b'\r\n', b'\n')
            if raw != normalized and raw != normalized.replace(b'\n', b'\r\n'):
                mixed.append(copy_file(path, h.OUT / 'mixed-eol-source' / owner['owner'] / row['path']))
        unchanged.append(dict(owner=owner['owner'], unchanged_files=len(owner['files'])))
    selected = ['questions.json', 'manifest.json', 'identity.json', 'spend_authorization.json',
       'quick_scan_c06_authority.json', 'stub-responses.json', 'result.json', 'http-stub-sends.jsonl',
       'key-opens.jsonl', 'cold.stdout.log', 'cold.stderr.log', 'warm.stdout.log', 'warm.stderr.log',
       'seal.stdout.log', 'seal.stderr.log']
    archived = []
    sends = {}
    for case in ['a-selected', 'b', 'b-direct']:
        root = h.OWN / 'cases' / case
        for name in selected:
            path = root / name
            if path.is_file():
                archived.append(copy_file(path, h.OUT / 'synthetic-cases' / case / name))
        sends[case] = len((root / 'http-stub-sends.jsonl').read_bytes().splitlines())
        for path in root.glob('*.package.json'):
            archived.append(copy_file(path, h.OUT / 'synthetic-cases' / case / path.name))
    for name in ['duplicate.package.json', 'actual-recovered-ack.json', 'c-ack-wrong-store.json',
                 'wrong-release.json', 'bad-hash.json']:
        path = h.OWN / 'cases' / name
        if path.exists():
            archived.append(copy_file(path, h.OUT / 'synthetic-negative-inputs' / name))
    for name in ['old.package.json', 'new.package.json']:
        archived.append(copy_file(h.OWN / 'cases/legacy' / name,
                                 h.OUT / 'synthetic-cases/legacy' / name))
    baselines = json.loads((h.OUT / 'source-baseline.json').read_text('utf-8'))
    print(type(baselines).__name__, flush=True)
    states = {}
    for name, root in [('qa', 'C:/Users/郑曾波/Projects/StockQAbyLLM'), ('sw', 'C:/Users/郑曾波/Projects/StockWiki')]:
        states[name] = git_state(root)
    h.save(h.OUT / 'source-state-after.json', states)
    h.save(h.OUT / 'final-verification.json', dict(source_snapshot_unchanged=unchanged,
       source_state_before=baselines, source_state_after=states, source_written=False,
       paid_calls=0, external_http=0, synthetic_http_sends=sends,
       archived=archived, mixed_eol_recovery=mixed,
       config_or_keys_archived=False, actual_model_alias_checkpoint_supported=False))
    print(json.dumps(dict(unchanged=unchanged, synthetic_http_sends=sends,
                          archived_files=len(archived), mixed_eol_files=len(mixed))))


if __name__ == '__main__':
    main()
