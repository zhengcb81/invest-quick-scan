"""Index this finite acceptance and compare every staged artifact's raw bytes."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

IQS = Path(__file__).resolve().parents[5]
REVIEW = Path(__file__).resolve().parent
INTAKE = IQS / 'docs/implementation/intake/QA-C06-02/2026-10-08-second-remediation'
OWN = IQS / 'runs/qa-c06-r2-2026-10-08-01'
INDEX = REVIEW / 'artifacts.json'
JOINT = [IQS / 'docs/implementation/reviews/G3/joint-acceptance-preparation-2026-10-08.md',
         IQS / 'docs/implementation/reviews/G3/joint-source-state-2026-10-08-after-repairs.json']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git(*args):
    return subprocess.run(['git', *args], cwd=IQS, capture_output=True, check=True).stdout


def main():
    cleanup = json.loads((INTAKE / 'cleanup-receipt.json').read_text('utf-8-sig'))
    assert cleanup['applied'] and cleanup['files_deleted'] == 615 and not OWN.exists()
    proof = json.loads((INTAKE / 'verification/final-verification.json').read_text('utf-8'))
    assert not proof['snapshot_changed_after_all_cases']
    assert all(x['matched'] for x in proof['source_artifacts'])
    tests = {}
    for name, count in [('affected-regression', 247), ('original-nine-boundaries', 9),
                        ('remaining-seven-and-mirrors', 16), ('segment-two', 2)]:
        result = json.loads((INTAKE / 'verification' / (name + '.result.json')).read_text('utf-8'))
        output = (INTAKE / 'verification' / (name + '.stdout.log')).read_text('utf-8')
        assert result['returncode'] == 0 and not result['timed_out']
        assert re.search(r'\b' + str(count) + r' passed\b', output)
        tests[name] = dict(passed=count, wall_s=result['wall_s'])
    if '--index' in sys.argv:
        links = 0
        for path in [*REVIEW.glob('*.md'), JOINT[0]]:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text('utf-8')):
                assert (path.parent / target).resolve().exists(), target
                links += 1
        for path in REVIEW.glob('*.py'):
            ast.parse(path.read_text('utf-8'))
        save(INTAKE / 'acceptance-receipt.json', dict(
            schema='iqs_qa_c06_02_remaining_acceptance/1',
            verdict='verified_for_finite_software_acceptance_scope',
            source_result_commit=proof['source_result_commit'],
            source_received_head=proof['source_head_after'], source_written=False,
            source_snapshot_files=136, worker_artifacts=57, raw_inputs_unchanged=True,
            tests=tests, unique_test_count_not_aggregated=True,
            normal_cli_iqs_validated=31, wrong_security_cli_key_opens=0,
            wrong_security_cli_stub_sends=0, wrong_security_cli_database_created=False,
            public_handoff='exit2 temporary_root_not_cleaned; historical reservation kept',
            one_independent_review=True, worker_full_and_extended='received_only_not_reexecuted',
            cleanup_applied=True, owned_root_absent=True, files_deleted=615,
            directories_deleted=284, historical_shared_temp_provenance='open',
            external_http=0, paid_calls=0, downloads=0, real_owner_golden=False,
            real_stockwiki_joint='not_run', gate_closed=False,
            old_roots_shared_temp_opencode_preserved=True))
        save(INTAKE / 'verification/document-check.json', dict(
            helper_ast_valid=True, local_links_valid=links, cleanup_applied=True,
            gate_closed=False, product_tests_reexecuted_for_document_check=False))
        paths = sorted([path for root in (REVIEW, INTAKE) for path in root.rglob('*')
                        if path.is_file() and path != INDEX] + JOINT)
        save(INDEX, dict(schema='iqs_acceptance_artifact_index/1',
                        scope='QA-C06-02 original four-chain remaining acceptance and joint readiness',
                        files=[dict(path=p.relative_to(IQS).as_posix(), bytes=p.stat().st_size,
                                    sha256=sha(p.read_bytes())) for p in paths],
                        excludes=['this index', 'root PWF files', '.gitattributes', 'new-agent handoff'],
                        secrets_baseline='opaque metadata only; content not copied'))
        print(json.dumps(dict(indexed_files=len(paths), local_links_valid=links)))
    if '--check-staged' in sys.argv:
        document = json.loads(INDEX.read_text('utf-8'))
        for entry in document['files']:
            raw = git('show', ':' + entry['path'])
            assert len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], entry['path']
        assert git('show', ':' + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
        allowed = {e['path'] for e in document['files']} | {
            INDEX.relative_to(IQS).as_posix(), '.gitattributes', 'task_plan.md', 'findings.md',
            'progress.md', 'docs/implementation/handoff-for-new-agent.md'}
        staged = set(git('diff', '--cached', '--name-only').decode('utf-8').splitlines())
        assert staged == allowed, (staged - allowed, allowed - staged)
        print(json.dumps(dict(staged_byte_hashes_matched=len(document['files']),
                              index_exact=True, staged_files=len(staged))))


if __name__ == '__main__':
    main()
