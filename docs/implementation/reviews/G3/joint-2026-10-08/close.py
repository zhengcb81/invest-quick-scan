"""Close this finite acceptance batch; index exact bytes, not global gates."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import IQS, OWN, OUT, REVIEW, save

INTAKE = OUT.parent
INDEX = REVIEW / 'artifacts.json'
META = ['.gitattributes', 'task_plan.md', 'progress.md', 'findings.md',
        'docs/implementation/handoff-for-new-agent.md']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    if '--prepare' in sys.argv:
        assert not OWN.exists(), 'Private root not cleaned'
        cleanup = json.loads((INTAKE / 'cleanup-receipt.json').read_text('utf-8-sig'))
        proof = json.loads((OUT / 'final-verification.json').read_text('utf-8'))
        assert cleanup['applied'] and cleanup['files_deleted'] == 1074
        assert proof['source_state_unchanged'] and not proof['source_written']
        assert proof['paid_calls'] == proof['external_http'] == 0
        for path in REVIEW.glob('*.py'):
            ast.parse(path.read_text('utf-8'))
        links = 0
        for path in REVIEW.glob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text('utf-8')):
                if target.startswith(('https:', 'http:', '#')):
                    continue
                assert (path.parent / target.split('#')[0]).exists(), (path, target)
                links += 1
        for row in proof['archived'] + proof['mixed_eol_recovery']:
            raw = (IQS / row['path']).read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        save(INTAKE / 'acceptance-receipt.json', dict(schema='iqs_joint_acceptance/1',
          verdict='partial_verified_changes_requested', blocked_groups=['JR1', 'JR2', 'JR3'],
          original_suite=dict(instances=17, passed=6, failed=11, seconds=68.10),
          correction_suite=dict(instances=9, passed=7, failed=2, seconds=31.75),
          not_aggregated_as_success=True, synthetic_http_sends=93, real_model_calls=0,
          real_search_calls=0, paid_calls=0, downloads=0, source_written=False,
          source_snapshot_files=dict(qa=136, sw=296), source_state_unchanged=True,
          original_read_acks_are_not_projected=True, independent_review_and_same_batch_addendum=True,
          cleanup_applied=True, owned_root_absent=True, files_deleted=1074, directories_deleted=78,
          real_owner_golden=False, browser_ui_tested=False, gate_closed=False,
          pending_stockwiki_authorization=['stockwiki/quick_scan_import.py', 'stockwiki/quick_scan_observations.py',
             'tests/test_quick_scan_observations.py', 'tests/test_quick_scan_delivery.py'],
          original_roots_shared_temp_opencode_preserved=True))
        save(OUT / 'document-check.json', dict(helper_ast_valid=True, local_links_valid=links,
                 archived_files_checked=len(proof['archived']), cleanup_applied=True,
                 product_tests_reexecuted=False, global_gate_closed=False))
        paths = sorted(p for root in [REVIEW, INTAKE] for p in root.rglob('*') if p.is_file() and p != INDEX)
        save(INDEX, dict(schema='iqs_acceptance_artifact_index/1', scope='Phase108 real public joint acceptance and bounded JR1-JR3 repair',
          files=[dict(path=p.relative_to(IQS).as_posix(), bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in paths],
          excludes=['this index'] + META))
        print(json.dumps(dict(indexed_files=len(paths), total_bytes=sum(p.stat().st_size for p in paths), local_links_valid=links)))
    if '--stage' in sys.argv:
        doc = json.loads(INDEX.read_text('utf-8'))
        allowed = sorted({row['path'] for row in doc['files']} | set(META) | {INDEX.relative_to(IQS).as_posix()})
        assert not subprocess.check_output(['git', '-C', str(IQS), 'diff', '--cached', '--name-only']).strip(), 'Existing staging belongs to another writer'
        specification = IQS / 'runs/joint-stage-paths-2026-10-08-01'
        assert not specification.exists() and specification.parent.is_dir()
        raw = b'\0'.join(path.encode('utf-8') for path in allowed) + b'\0'
        with specification.open('xb') as stream:
            stream.write(raw)
        try:
            subprocess.run(['git', '-C', str(IQS), 'add', '-f', '--pathspec-from-file=' + str(specification),
                            '--pathspec-file-nul'], check=True)
        finally:
            info = specification.lstat()
            assert info.st_nlink == 1 and not specification.is_symlink() and specification.read_bytes() == raw
            specification.unlink()  # only this exact file, created above; no directory deletion
        print(json.dumps(dict(exact_paths_staged=len(allowed), temporary_pathspec_removed=True)))
    if '--check-staged' in sys.argv:
        def git(*args):
            return subprocess.check_output(['git', '-C', str(IQS), *args])
        doc = json.loads(INDEX.read_text('utf-8'))
        for row in doc['files']:
            raw = git('show', ':' + row['path'])
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], row['path']
        assert git('show', ':' + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
        allowed = {row['path'] for row in doc['files']} | set(META) | {INDEX.relative_to(IQS).as_posix()}
        actual = set(git('diff', '--cached', '--name-only').decode('utf-8').splitlines())
        assert actual == allowed, (actual - allowed, allowed - actual)
        print(json.dumps(dict(staged_files=len(actual), exact_artifact_hashes=len(doc['files']))))


if __name__ == '__main__':
    main()
