"""Private staging is not a committed checkpoint or journal."""
import json

import pytest

from test_shared_company_engine import engine, helpers, ContextPort, SyntheticObservations


def test_orphan_private_staging_does_not_block_a_later_atomic_write(tmp_path):
    target = tmp_path / 'parent-checkpoint.json'
    engine._write_atomic(target, {'state': 'old'})
    orphan = target.with_name(target.name + '.pending')
    orphan.write_bytes(b'{"half-written":')
    engine._write_atomic(target, {'state': 'new'})
    assert json.loads(target.read_text()) == {'state': 'new'}
    assert orphan.read_bytes() == b'{"half-written":'


def test_crash_checkpoint_write_cannot_truncate_the_last_published_checkpoint(tmp_path, monkeypatch):
    from iqs_company_agent_lab import checkpoint as cp
    from iqs_company_agent_lab.runner import Runner, RunCrashed
    task = helpers.make_task('fixed3', 'publication-crash')
    port = ContextPort(task)
    published = tmp_path / 'session/checkpoint.json'
    original_write = cp.write_checkpoint
    before = {}

    def stop_runner(runner):
        runner._start()
        snapshot = cp.build_checkpoint(runner.state, runner.journal)
        original_write(published, snapshot, ['events.jsonl'])
        before['raw'] = published.read_bytes()
        raise RunCrashed('synthetic-before-republication', snapshot)

    def tear_write(path, checkpoint, journal_files):
        path.write_bytes(b'{"interrupted":')
        raise OSError('synthetic process interruption during checkpoint write')

    monkeypatch.setattr(Runner, 'run', stop_runner)
    monkeypatch.setattr(cp, 'write_checkpoint', tear_write)
    with pytest.raises(OSError, match='synthetic process interruption'):
        engine._execute_with_port(task, SyntheticObservations(port), port,
            output=tmp_path / 'export', session_dir=tmp_path / 'session', transport_origin='scripted_wire')
    assert published.read_bytes() == before['raw']
    assert cp.load_checkpoint(published)['checkpoint_sha256'] == json.loads(before['raw'])['checkpoint_sha256']
    assert port.calls == 0


def test_pending_publication_retry_ignores_only_unpublished_private_fragments(tmp_path):
    from iqs_company_agent_lab.runner import Runner
    from iqs_company_agent_lab.checkpoint import load_checkpoint
    task = helpers.make_task('fixed3', 'publication-private-fragments')
    port = ContextPort(task)
    runner = Runner(task, port)
    runner._start()
    guarded = engine._pending_port(port, [runner], tmp_path)
    guarded._save(None)
    before = load_checkpoint(tmp_path / 'checkpoint.json')
    fragments = [tmp_path / 'checkpoint.json.pending',
                 tmp_path / f'pending-history-{runner.journal.seq}.jsonl']
    for path in fragments:
        path.write_bytes(b'{"unpublished":')
    guarded._save(None)
    after = load_checkpoint(tmp_path / 'checkpoint.json')
    assert after['state'] == before['state'] and after['event_chain'] == before['event_chain']
    assert all(path.read_bytes() == b'{"unpublished":' for path in fragments)
    assert port.calls == 0


def test_corrupt_history_referenced_by_published_checkpoint_still_refuses(tmp_path, monkeypatch):
    from iqs_company_agent_lab.strictjson import StrictJsonError
    task = helpers.make_task('fixed3', 'publication-bad-history')
    port = ContextPort(task, fail=True)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, SyntheticObservations(port), port,
            output=tmp_path / 'export', session_dir=tmp_path / 'original', transport_origin='scripted_wire')
    checkpoint = tmp_path / 'original/checkpoint.json'
    data = json.loads(checkpoint.read_text())
    (checkpoint.parent / data['event_chain']['journal_files'][0]).write_bytes(b'bad published history')
    monkeypatch.setattr(engine, 'preflight', lambda *args: {})
    monkeypatch.setattr(engine, 'inspect_native_recovery', lambda *args, **kwargs: pytest.fail('must verify history before native access'))
    with pytest.raises(StrictJsonError, match='invalid json'):
        engine.resume_shared_engine(task, object(), {}, checkpoint, tmp_path / 'new-export',
                                    session_dir=tmp_path / 'new-session', replay_only=True)
    assert port.calls == 1
