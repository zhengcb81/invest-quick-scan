from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dashboard_service import validate_config
from workbench_snapshot import (
    _lock_diff,
    _load_roster,
    build_workbench_snapshot,
    load_workbench_snapshot,
    unavailable_workbench_snapshot,
    write_workbench_snapshot,
)


class FakeOwner:
    def universe_list(self, universe_id):
        assert universe_id == 'test-universe'
        return {'member_count': 2, 'members': [
            {'entity_id': 'CN-001', 'canonical_name': 'Example A', 'identity_state': 'verified',
             'identity_revision': 'rev-a', 'membership_status': 'active', 'bindings': [],
             'securities': [{'market': 'SSE', 'ticker': '600001', 'status': 'active'}]},
            {'entity_id': 'US-002', 'canonical_name': 'Example B', 'identity_state': 'provisional',
             'identity_revision': 'rev-b', 'bindings': [], 'securities': []},
        ]}


def test_snapshot_reads_dynamic_question_sources_and_unknown_roster_is_not_zero():
    config = validate_config({}, ROOT)
    snapshot = build_workbench_snapshot(ROOT, config, generated_at='2026-11-12T00:00:00Z')
    assert snapshot['protocol'] == 'iqs.workbench-snapshot/1.0.0'
    assert snapshot['generated_at'] == '2026-11-12T00:00:00Z'
    assert snapshot['availability']['bank'] == snapshot['availability']['versions'] == 'available'
    assert snapshot['availability']['roster'] == snapshot['availability']['answers'] == 'unavailable'
    assert snapshot['bank']['question_count'] == sum(
        len(module['questions']) for module in snapshot['bank']['modules'].values())
    assert {'common', 'dupont', 'porter'} <= set(snapshot['bank']['always_applicable_modules'])
    assert snapshot['manifest']['counts']['entities'] is None
    assert snapshot['manifest']['counts']['runs'] is None
    assert snapshot['manifest']['counts']['questions'] == snapshot['bank']['question_count']
    assert any(item['code'] == 'history_source_not_selected' for item in snapshot['warnings'])


def test_roster_projection_uses_owner_rows_and_keeps_unknown_fields_unknown():
    roster = _load_roster(FakeOwner(), 'test-universe')
    assert roster['entities'] == 2 and roster['verified'] == 1 and roster['provisional'] == 1
    assert roster['by_market'] == {'CN': 1}
    assert roster['rows'][0]['entity_id'] == 'CN-001'
    assert roster['rows'][0]['bindings'] == 0
    assert roster['rows'][0]['observations'] is None and roster['rows'][0]['search_backed'] is None
    assert roster['rows'][1]['next_action'] == 'needs_verified_identity'


def test_missing_immutable_artifacts_make_lock_comparison_incomparable_not_identical(tmp_path):
    left = {'lock_id': 'left', 'modules': [{'module_id': 'common',
        'artifact_ref': 'questions/releases/artifacts/missing-a.json', 'question_semantics': [
            {'question_id': 'Q1', 'definition_sha256': 'same', 'rubric_version': '1'}]}]}
    right = {'lock_id': 'right', 'modules': [{'module_id': 'common',
        'artifact_ref': 'questions/releases/artifacts/missing-b.json', 'question_semantics': [
            {'question_id': 'Q1', 'definition_sha256': 'same', 'rubric_version': '1'}]}]}
    diff = _lock_diff(left, right, tmp_path, set())
    assert diff['comparable'] is False
    assert diff['question_level_identical'] is False
    assert any(item['category'] == 'incomparable' for item in diff['question_diffs'])


def test_snapshot_atomic_roundtrip_and_corrupt_snapshot_is_unavailable(tmp_path):
    path = tmp_path / 'workbench' / 'snapshot.json'
    source = unavailable_workbench_snapshot('waiting')
    write_workbench_snapshot(path, source)
    assert load_workbench_snapshot(path) == source
    path.write_text('{"protocol":"wrong","availability":{},"warnings":[]}', encoding='utf8')
    unavailable = load_workbench_snapshot(path)
    assert set(unavailable['availability'].values()) == {'unavailable'}
    assert not list(path.parent.glob('*.tmp'))


def test_snapshot_cli_plan_does_not_create_output_or_read_owner(tmp_path):
    output = tmp_path / 'not-created.json'
    done = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'scripts' / 'workbench_snapshot_cli.py'),
                           '--data-root', str(ROOT), '--output', str(output), '--plan'],
                          cwd=tmp_path, capture_output=True, text=True, encoding='utf8', timeout=20)
    assert done.returncode == 0, done.stderr
    plan = json.loads(done.stdout)
    assert plan['reads_owner'] is False and plan['model_calls'] is False and plan['writes'] is False
    assert not output.exists()


def test_snapshot_cli_writes_only_the_explicit_output_with_unconfigured_owner(tmp_path):
    import shutil

    resources = tmp_path / 'resources'
    resources.mkdir()
    for directory in ('questions', 'schemas'):
        shutil.copytree(ROOT / directory, resources / directory)
    config = tmp_path / 'dashboard.json'
    state = tmp_path / 'state'
    config.write_text(json.dumps({'workspace_root': '', 'state_root': str(state),
                                  'workspace_kind': 'unconfigured'}), encoding='utf8')
    output = tmp_path / 'published' / 'snapshot.json'
    done = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'scripts' / 'workbench_snapshot_cli.py'),
                           '--data-root', str(resources), '--dashboard-config', str(config), '--output', str(output)],
                          cwd=tmp_path, capture_output=True, text=True, encoding='utf8', timeout=30)
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result['status'] == 'written' and result['model_calls'] == result['network_calls'] == 0
    snapshot = load_workbench_snapshot(output)
    assert snapshot['availability']['bank'] == 'available'
    assert snapshot['availability']['roster'] == snapshot['availability']['answers'] == 'unavailable'
    assert snapshot['manifest']['counts']['entities'] is None
    assert not (resources / 'scripts').exists()
    assert not state.exists()
