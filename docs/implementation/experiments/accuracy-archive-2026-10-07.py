"""One-time, offline Phase96 archive. Does not invoke providers or release budget."""
import hashlib
import json
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import accuracy_pilot as p
import accuracy_followup as f
import accuracy_report as report

DEST = ROOT / 'docs/implementation/experiments/artifacts/accuracy-first-2026-10-07'
RUNS = {
    'main': 'accuracy-pilot-2026-10-07-01',
    'followup': 'accuracy-pilot-followup-2026-10-07-01',
    'diagnostic': 'accuracy-pilot-zai-diagnostic-2026-10-07-01',
    'validation': 'accuracy-validation-2026-10-07-01',
}
HELD = 'ATT_0668931b18ec49be99137252163a00c2'


def metadata(path):
    return dict(size=path.stat().st_size, sha256=p.sha(path))


def safe(path):
    s = path.lstat()
    if path.is_symlink() or s.st_nlink != 1 or getattr(s, 'st_file_attributes', 0) & 1024:
        raise ValueError('link/reparse refused: ' + str(path))
    if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):
        raise ValueError('nonregular path refused')


def build():
    if DEST.exists():
        raise ValueError('archive exists; do not overwrite')
    roots = {k: ROOT / 'runs' / v for k, v in RUNS.items()}
    p.freeze(roots['main'], check=True)
    f.freeze(roots['followup'], check=True)
    for label, root in roots.items():
        if (root / 'orchestrator.lock').exists():
            raise ValueError('active owned lock')
        safe(root)
        for path in root.rglob('*'):
            safe(path)
        if label != 'validation':
            for path, sha in p.read(root / 'runtime-manifest.json')['files'].items():
                if p.sha(root / 'runtime' / path) != sha:
                    raise ValueError('runtime hash mismatch')
    if report.report(roots['main'], roots['followup'], roots['diagnostic']) != p.read(roots['followup'] / 'terminal-report.json'):
        raise ValueError('terminal report mismatch')
    budgets = {k: p.b.Ledger(v).summary() for k, v in roots.items() if k != 'validation'}
    if sum(x['unresolved_attempts'] for x in budgets.values()) != 1:
        raise ValueError('unknown disposition drift')
    events = [json.loads(x) for x in (roots['followup'] / 'attempts.jsonl').read_text('utf-8').splitlines()]
    held = [x for x in events if x['attempt_id'] == HELD]
    if len(held) != 2 or held[0]['reserve_usd'] != .03 or held[1]['state'] != 'outcome_unknown':
        raise ValueError('held budget drift')
    DEST.mkdir(parents=True)
    for label, root in roots.items():
        dest = DEST / label
        dest.mkdir()
        kept = [x for x in root.iterdir() if x.is_file() and x.suffix in ('.json', '.jsonl', '.log')]
        for dirname in ['results', 'score-results', 'source']:
            kept.extend(x for x in (root / dirname).glob('*') if x.is_file())
        for path in kept:
            target = dest / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            if metadata(target) != metadata(path):
                raise ValueError('copy drift')
        # Metadata only: no search snippet, response, reasoning, page, cache or runtime copy.
        catalog = []
        for dirname in ['evidence', 'refinement', 'precision']:
            for path in sorted((root / dirname).glob('*.json')):
                data = p.read(path)
                if not isinstance(data, list):
                    continue
                for row in data:
                    if not isinstance(row, dict) or 'source_id' not in row:
                        continue
                    record = {k: row.get(k) for k in ['source_id', 'url', 'published_at', 'retrieved_at', 'provider', 'query_sha256', 'context_origin']}
                    record.update(title=str(row.get('title', ''))[:160], pool=path.relative_to(root).as_posix(),
                        snippet_utf8_sha256=hashlib.sha256(str(row.get('snippet', '')).encode('utf-8')).hexdigest(),
                        pool_file_sha256=p.sha(path))
                    catalog.append(record)
        p.b.write_json(dest / 'source-catalog.json', dict(kind='source metadata; controller coverage annotations retained separately; not original snippet replay', entries=catalog))
        p.b.write_json(dest / 'archive-manifest.json', dict(schema='phase96_minimal_archive/1', run_name=RUNS[label],
            run_path=str(root.resolve()), budget=budgets.get(label), source_freeze_verified=label != 'validation',
            retained_files={x.relative_to(dest).as_posix(): metadata(x) for x in dest.rglob('*') if x.is_file()},
            cleanup_baseline={x.relative_to(root).as_posix(): metadata(x) for x in root.rglob('*') if x.is_file()},
            excluded=['full snippets/pages/filings', 'cache', 'runtime copies', 'tmp', 'raw provider response', 'independent reasoning'],
            replay_limit='Numerical/coverage/report arithmetic reproducible; exact model prompt and invalid final body not reconstructible after cleanup.'))
    sources = DEST / 'sources'
    sources.mkdir()
    for name in ['accuracy_report.py', 'accuracy_assessment.py']:
        shutil.copyfile(ROOT / 'scripts' / name, sources / name)
    p.b.write_json(DEST / 'unknown-disposition.json', dict(attempt_id=HELD, state='outcome_unknown', reserve_usd=.03,
        send_repeated=False, budget_released=False, reason='Local post-response normalization recursion; raw response not retained. No active runner. Historical reconciliation stays open after file cleanup.'))
    p.b.write_json(DEST / 'index.json', dict(schema='phase96_archive_index/1', created_at=p.b.now(),
        runs=RUNS, stockqa_source_commit='6a9ff13864ebb160d5c4ab3cf2f42155d9f4aa99',
        files={x.relative_to(DEST).as_posix(): metadata(x) for x in DEST.rglob('*') if x.is_file()},
        totals=p.read(roots['followup'] / 'terminal-report.json')['totals']))
    print('archive created, unknown budget preserved; cleanup not performed')


if __name__ == '__main__':
    build()
