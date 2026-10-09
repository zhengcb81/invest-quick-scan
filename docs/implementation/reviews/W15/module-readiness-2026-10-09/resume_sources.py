"""Explicit W15 partial-publication continuation; never rerun apply.

Reuse already-installed, exact-version normal hook environments. The standard
pre-commit cache is neither deleted nor restored over other processes. Product
tests, TEMP and formatter caches remain owned; no hook or security check skipped.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import inspect_hook_cache
import publish_sources as publish

ROOT, OUT, PUB = publish.ROOT, publish.OUT, publish.PUB
REPO = ROOT.parent / 'StockQAbyLLM'


def cache_inventory():
    cache = inspect_hook_cache.CACHE
    con = sqlite3.connect((cache / 'db.db').as_uri() + '?mode=ro', uri=True)
    try:
        rows = con.execute('SELECT repo, ref, path FROM repos').fetchall()
    finally:
        con.close()
    result = []
    for url, ref in inspect_hook_cache.EXPECTED:
        key = url + (':types-requests' if 'mirrors-mypy' in url else '')
        found = [(repo, revision, Path(path)) for repo, revision, path in rows
                 if repo == key and revision == ref]
        assert len(found) == 1, key
        _, _, directory = found[0]
        assert directory.resolve().is_relative_to(cache.resolve())
        states = list((directory / 'py_env-python3').glob('.install_state*'))
        assert states
        files = [directory / '.pre-commit-hooks.yaml', *states]
        result.append(dict(public_hook=url.rsplit('/', 1)[-1], revision=ref,
                           additional_dependencies=key[len(url):], directory=directory.name,
                           metadata_sha256={str(p.relative_to(cache)):publish.sha(p.read_bytes()) for p in files}))
    return result


def main(label):
    assert label.replace('-', '').isalnum()
    assert not (PUB / (label + '-before.json')).exists()
    assert json.loads((PUB/'StockWiki-result.json').read_bytes())['commit'] == 'a5a97d6efbf5f0ee79122a1ec375def388700690'
    original = json.loads((PUB/'apply-preflight.json').read_bytes())['sources']['StockQAbyLLM']
    index = json.loads((OUT/'candidate-index-02.json').read_bytes())
    rows = index['files']['StockQAbyLLM']
    paths = {row['path'] for row in rows}
    review = json.loads((publish.CONTROL/'review/concentrated-recheck-02.json').read_bytes())
    assert review['software_open_findings'] == 0
    assert review['candidate_index_sha256'] == publish.sha((OUT/'candidate-index-02.json').read_bytes())
    assert publish.git(REPO,'rev-parse','HEAD').decode().strip() == original['head']
    unstaged = set(publish.git(REPO,'diff','--name-only').decode().splitlines())
    normalized = {}
    if label == 'StockQAbyLLM-commit-resume-02':
        # Previous *normal* hook changed only mixed EOL in this non-runtime file.
        previous = json.loads((PUB/'StockQAbyLLM-commit-resume-01.process.json').read_bytes())
        assert previous['returncode'] == 1 and previous['terminal_confirmed']
        # Git's text filter can hide raw EOL-only changes from diff --name-only.
        assert unstaged <= {'.gitignore'}
        frozen = (OUT/'candidate-source-02/StockQAbyLLM/.gitignore').read_bytes()
        current = (REPO/'.gitignore').read_bytes()
        assert current == frozen.replace(b'\r\n', b'\n') and current != frozen
        normalized['.gitignore'] = dict(reviewed_execution_sha256=publish.sha(frozen),
                                        hook_execution_sha256=publish.sha(current),
                                        EOL_only_normalization=True, logic_changed=False)
        publish.save(label+'-hook-EOL.json', normalized)
        (PUB/'.gitignore-after-normal-hook').write_bytes(current)
        publish.git(REPO,'add','--','.gitignore')
    else:
        assert not unstaged
    assert not publish.git(REPO,'diff','--name-only')
    assert set(filter(None,publish.git(REPO,'diff','--cached','--name-only','-z').decode().split('\0'))) == paths
    for row in rows:
        raw = (REPO/row['path']).read_bytes()
        expected = normalized.get(row['path'], {}).get('hook_execution_sha256', row['execution_sha256'])
        assert publish.sha(raw) == expected
        assert publish.sha((OUT/'candidate-source-02/StockQAbyLLM'/row['path']).read_bytes()) == row['execution_sha256']
    protected = original['protected_nonsecret_source_sha256']
    assert all(publish.sha((REPO/name).read_bytes()) == h for name,h in protected.items())
    status = publish.git(REPO,'status','--porcelain=v1','-uall').decode().replace('\r\n','\n')
    assert ''.join(line+'\n' for line in status.splitlines() if line.startswith('?? ')) == original['status']
    before_cache = cache_inventory()
    publish.save(label+'-before.json',dict(candidate_index_sha256=review['candidate_index_sha256'],
                 head=original['head'], staged_paths=sorted(paths), public_hook_cache=before_cache,
                 normal_hooks=True, API_requests=0, hook_config_unchanged=True,
                 runtime_TEST_environment='owned; standard preexisting hook environments only reused'))
    old_env = publish.env
    def reused_env():
        value = old_env()
        value['PRE_COMMIT_HOME'] = str(inspect_hook_cache.CACHE)
        return value
    publish.env = reused_env
    publish.git(REPO,'commit','-m','Persist modular quick scan routes and execute incremental refresh safely',label=label)
    commit = publish.git(REPO,'rev-parse','HEAD').decode().strip()
    assert set(filter(None,publish.git(REPO,'diff-tree','--no-commit-id','--name-only','-r','-z',commit).decode().split('\0'))) == paths
    assert publish.git(REPO,'status','--porcelain=v1','-uall').decode().replace('\r\n','\n') == original['status']
    assert all(publish.sha((REPO/name).read_bytes()) == h for name,h in protected.items())
    domains = json.loads((PUB/'StockQAbyLLM-staged-domains.json').read_bytes())
    for name,pair in normalized.items():
        domains[name]['reviewed_execution_sha256'] = pair['reviewed_execution_sha256']
        domains[name]['execution_sha256'] = pair['hook_execution_sha256']
        domains[name]['normal_hook_EOL_only'] = True
    if normalized:
        publish.save('StockQAbyLLM-staged-domains-resume-02.json', domains)
    for name,pair in domains.items():
        assert publish.sha((REPO/name).read_bytes()) == pair['execution_sha256']
        assert publish.sha(publish.git(REPO,'show',commit+':'+name)) == pair['Git_blob_sha256']
    assert cache_inventory() == before_cache, 'Installed public hook metadata changed'
    publish.git(REPO,'push','origin','master',label='StockQAbyLLM-push')
    remote = publish.git(REPO,'ls-remote','origin','refs/heads/master').decode().split()[0]
    assert remote == commit
    qa = dict(commit=commit,remote_head=remote,paths=sorted(paths),
              protected_files_unchanged=len(protected),original_unknowns_preserved=True,
              source_worktree_and_Git_domains=domains,normal_hook_reused_cache=True,
              normal_hook_EOL_only_paths=list(normalized))
    publish.save('StockQAbyLLM-result.json',qa)
    sw = json.loads((PUB/'StockWiki-result.json').read_bytes())
    publish.save('result.json',dict(protocol='iqs.w15_foundation_publication/1.0.0',
              sources={'StockWiki':sw,'StockQAbyLLM':qa},source_published=True,
              normal_hooks=True,force_push=False,production_DB_migrations=0,API_requests=0,
              whole_W15_complete=False,financial_accuracy_validated=False,
              cleanup_pending=str(publish.OWN),normal_hook_install_timeout_preserved=True))
    print(json.dumps(dict(commit=commit,remote_head=remote,source_published=True)))


if __name__ == '__main__':
    main(sys.argv[1])
