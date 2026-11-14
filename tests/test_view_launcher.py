"""Public thin launcher works without a user-configured PYTHONPATH."""
from pathlib import Path
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import urllib.request
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/view_quick_scan.py'
DASHBOARD=ROOT/'scripts/open_dashboard.py'


def _dashboard_fixture(tmp_path, ui_root=None, *, config_overrides=None):
    ui = Path(ui_root).resolve() if ui_root is not None else tmp_path / 'ui'
    if ui_root is None:
        app = ui / 'src' / 'app'
        app.mkdir(parents=True)
        (app / 'index.html').write_text('<!doctype html><title>IQS UI</title>', encoding='utf8')
    state = tmp_path / 'state'
    config = tmp_path / 'dashboard.json'
    config_value = {'state_root': str(state), 'workspace_root': '',
                    'workspace_kind': 'unconfigured', **(config_overrides or {})}
    config.write_text(json.dumps(config_value), encoding='utf8')
    return ui, state, config


def _start_dashboard(tmp_path, *, no_refresh=False, existing_snapshot=None, ui_root=None,
                     config_overrides=None):
    ui, state, config = _dashboard_fixture(tmp_path, ui_root, config_overrides=config_overrides)
    snapshot = state / 'workbench' / 'snapshot.json'
    if existing_snapshot is not None:
        snapshot.parent.mkdir(parents=True)
        snapshot.write_bytes(existing_snapshot)
    command = [sys.executable, '-B', '-X', 'utf8', str(DASHBOARD), '--ui-root', str(ui),
               '--dashboard-config', str(config), '--port', '0']
    if no_refresh:
        command.append('--no-refresh')
    process = subprocess.Popen(command, cwd=tmp_path, env=_env(tmp_path), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding='utf8')
    lines = queue.Queue()
    reader = threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True)
    reader.start()
    try:
        ready = json.loads(lines.get(timeout=30))
    except Exception:
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
        raise AssertionError(f'dashboard failed to start: {stdout}\n{stderr}')
    return process, reader, ready, ui, state, snapshot


def _stop_dashboard(process, reader):
    if process.poll() is None:
        process.terminate()
    process.wait(timeout=10)
    reader.join(timeout=2)
    process.stdout.close()
    process.stderr.close()
    assert not reader.is_alive()


def test_dashboard_launcher_uses_the_selected_checkout_public_entry(tmp_path):
    ui, _, config = _dashboard_fixture(tmp_path)
    checkout = tmp_path / 'other-iqs'
    scripts = checkout / 'scripts'
    scripts.mkdir(parents=True)
    (scripts / 'open_dashboard.py').write_text(
        'import json, sys\nfrom pathlib import Path\n'
        'from checkout_marker import MARKER\n'
        'print(json.dumps([MARKER, str(Path(sys.argv[0]).resolve()), sys.argv[1:]]))\n',
        encoding='utf8',
    )
    (scripts / 'checkout_marker.py').write_text('MARKER = "selected-checkout"\n', encoding='utf8')
    args = ['--data-root', str(checkout), '--ui-root', str(ui), '--dashboard-config', str(config),
            '--port', '0', '--no-refresh', '--plan']
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(DASHBOARD), *args],
                            cwd=tmp_path, env=_env(tmp_path), capture_output=True,
                            text=True, encoding='utf8', timeout=15)

    assert result.returncode == 0, result.stderr
    marker, entry, forwarded = json.loads(result.stdout)
    assert marker == 'selected-checkout'
    assert Path(entry) == (scripts / 'open_dashboard.py').resolve()
    for flag, expected in [('--data-root', checkout), ('--ui-root', ui), ('--dashboard-config', config)]:
        assert Path(forwarded[forwarded.index(flag) + 1]) == expected.resolve()
    assert forwarded[forwarded.index('--port') + 1] == '0'
    assert {'--plan', '--no-refresh'} <= set(forwarded)


def test_dashboard_launcher_accepts_a_data_directory_without_code(tmp_path):
    ui, state, config = _dashboard_fixture(tmp_path)
    data = tmp_path / 'resources'
    data.mkdir()
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(DASHBOARD),
                             '--data-root', str(data), '--ui-root', str(ui),
                             '--dashboard-config', str(config), '--plan'],
                            cwd=tmp_path, env=_env(tmp_path), capture_output=True,
                            text=True, encoding='utf8', timeout=15)

    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert Path(plan['data_root']) == data.resolve()
    assert Path(plan['snapshot_path']) == (state / 'workbench' / 'snapshot.json').resolve()
    assert not plan['writes'] and not state.exists()


def test_company_dashboard_serves_static_ui_and_one_owner_snapshot_without_ui_runtime(tmp_path):
    process, reader, ready, ui, state, snapshot = _start_dashboard(tmp_path)
    try:
        assert ready['status'] == 'ready' and ready['model_calls'] == ready['network_calls'] == 0
        with urllib.request.urlopen(ready['url'], timeout=10) as response:
            assert 'IQS UI' in response.read().decode('utf8')
        with urllib.request.urlopen(ready['url'] + 'api/product/setup', timeout=10) as response:
            assert json.loads(response.read())['ok'] is True
        with urllib.request.urlopen(ready['url'] + 'generated/snapshot.json', timeout=10) as response:
            document = json.loads(response.read())
        assert document['protocol'] == 'iqs.workbench-snapshot/1.0.0'
        assert document['availability']['bank'] == 'available'
        assert document['availability']['roster'] == 'unavailable'
        assert document['manifest']['counts']['entities'] is None
        with urllib.request.urlopen(ready['url'] + 'generated/bank.json', timeout=10) as response:
            assert json.loads(response.read()) == document['bank']
        with pytest.raises(urllib.error.HTTPError) as escaped:
            urllib.request.urlopen(ready['url'] + '%2e%2e/%2e%2e/dashboard.json', timeout=10)
        assert escaped.value.code == 404
        assert snapshot.is_file()
        assert sorted(path.relative_to(ui).as_posix() for path in ui.rglob('*') if path.is_file()) == ['src/app/index.html']
    finally:
        _stop_dashboard(process, reader)


def test_company_dashboard_no_refresh_reads_existing_snapshot_without_rewriting_it(tmp_path):
    original = b'{"old":"snapshot"}\n'
    process, reader, ready, _ui, _state, snapshot = _start_dashboard(
        tmp_path, no_refresh=True, existing_snapshot=original)
    try:
        with urllib.request.urlopen(ready['url'] + 'generated/snapshot.json', timeout=10) as response:
            document = json.loads(response.read())
        assert set(document['availability'].values()) == {'unavailable'}
        assert snapshot.read_bytes() == original
    finally:
        _stop_dashboard(process, reader)


def test_company_dashboard_runs_the_current_ui_source_as_static_content(tmp_path):
    ui = Path(os.environ.get('IQS_UI_ROOT', ROOT.parent / 'iqs-question-bank-ui-lab')).resolve()
    if not (ui / 'src' / 'app' / 'index.html').is_file():
        pytest.skip('Current UI source is unavailable; provide IQS_UI_ROOT for this cross-repository smoke test.')
    process, reader, ready, _ui, state, snapshot = _start_dashboard(tmp_path, ui_root=ui)
    try:
        for asset in ('', 'styles/app.css', 'store.js'):
            with urllib.request.urlopen(ready['url'] + asset, timeout=10) as response:
                body = response.read()
                assert response.status == 200 and body
                if asset == 'store.js':
                    assert b'/generated/snapshot.json' in body
        with urllib.request.urlopen(ready['url'] + 'generated/snapshot.json', timeout=10) as response:
            document = json.loads(response.read())
        assert document['availability']['bank'] == 'available'
        assert document['bank']['question_count'] > 0
        assert document['availability']['roster'] == 'unavailable'
        assert snapshot.is_file() and snapshot.parent.parent == state
        assert all(not source['path'].startswith('src/generated/')
                   for source in document['manifest']['sources'])
    finally:
        _stop_dashboard(process, reader)


def test_company_dashboard_composes_current_ui_with_isolated_stockwiki_owner(tmp_path):
    """The product snapshot must cross the real public StockWiki CLI boundary."""
    stockwiki = Path(os.environ.get('IQS_STOCKWIKI_ROOT', ROOT.parent / 'StockWiki')).resolve()
    if not (stockwiki / 'stockwiki' / 'quick_scan_dashboard_cli.py').is_file():
        pytest.skip('Current StockWiki public owner source is unavailable.')
    ui = Path(os.environ.get('IQS_UI_ROOT', ROOT.parent / 'iqs-question-bank-ui-lab')).resolve()
    if not (ui / 'src' / 'app' / 'index.html').is_file():
        pytest.skip('Current UI source is unavailable; provide IQS_UI_ROOT for this cross-repository test.')

    owner_workspace = tmp_path / 'owner-workspace'
    seed = r'''
import sys
from pathlib import Path
stockwiki = Path(sys.argv[1])
sys.path.insert(0, str(stockwiki / 'tests'))
from test_quick_scan_universe import _seed, _entity, _plant
from stockwiki.quick_scan_universe import add_member
store, _ = _seed(Path(sys.argv[2]), 'IQS_WORKBENCH_TEST')
_plant(store, _entity('ENT_IQS_WORKBENCH', ticker='600001', name='Isolated Workbench Member'))
add_member(store, 'IQS_WORKBENCH_TEST', 'ENT_IQS_WORKBENCH',
           added_reason='isolated workbench integration', at='2026-11-12T00:00:00Z')
'''
    seed_env = _env(tmp_path)
    seed_env['PYTHONPATH'] = os.pathsep.join((str(stockwiki), str(stockwiki / 'tests')))
    seeded = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', seed,
                             str(stockwiki), str(owner_workspace)],
                            cwd=stockwiki, env=seed_env, capture_output=True,
                            text=True, encoding='utf8', timeout=60)
    assert seeded.returncode == 0, seeded.stderr

    def file_hashes(root):
        import hashlib
        return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob('*') if path.is_file()}

    owner_before = file_hashes(owner_workspace)
    process, reader, ready, _ui, state, snapshot_path = _start_dashboard(
        tmp_path, ui_root=ui, config_overrides={
            'stockwiki_root': str(stockwiki),
            'workspace_root': str(owner_workspace),
            'stockwiki_python': sys.executable,
            'universe_id': 'IQS_WORKBENCH_TEST',
            'workspace_kind': 'isolated_test',
        })
    try:
        assert ready['status'] == 'ready'
        assert ready['model_calls'] == ready['network_calls'] == 0
        with urllib.request.urlopen(ready['url'] + 'generated/snapshot.json', timeout=20) as response:
            snapshot = json.loads(response.read())
        assert snapshot['protocol'] == 'iqs.workbench-snapshot/1.0.0'
        assert snapshot['availability']['bank'] == snapshot['availability']['roster'] == 'available'
        assert snapshot['bank']['question_count'] > 0
        assert {'common', 'dupont', 'porter'} <= set(snapshot['bank']['always_applicable_modules'])
        assert snapshot['roster']['entities'] == 1
        assert snapshot['roster']['rows'][0]['entity_id'] == 'ENT_IQS_WORKBENCH'
        assert snapshot['roster']['rows'][0]['name'] == 'Isolated Workbench Member'
        assert snapshot['roster']['rows'][0]['listings'][0] == {
            'market': 'CN', 'ticker': '600001', 'status': 'active'}
        assert snapshot_path.is_file() and snapshot_path.parent.parent == state
        with urllib.request.urlopen(ready['url'], timeout=10) as response:
            assert response.status == 200 and response.read()
        assert file_hashes(owner_workspace) == owner_before
    finally:
        _stop_dashboard(process, reader)


def test_company_dashboard_plan_and_missing_static_root_are_actionable(tmp_path):
    missing = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(DASHBOARD), '--ui-root', str(tmp_path/'missing'), '--plan'],
                             cwd=tmp_path, env=_env(tmp_path), capture_output=True, text=True, encoding='utf8', timeout=20)
    assert missing.returncode == 2 and '--ui-root' in missing.stderr and 'Traceback' not in missing.stderr
    ui, state, config = _dashboard_fixture(tmp_path)
    planned = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(DASHBOARD), '--ui-root', str(ui), '--data-root', str(ROOT),
                              '--dashboard-config', str(config), '--port', '0', '--plan'],
                             cwd=tmp_path, env=_env(tmp_path), capture_output=True, text=True, encoding='utf8', timeout=20)
    assert planned.returncode == 0
    details = json.loads(planned.stdout)
    assert details['refresh'] is False and details['tests'] is False
    assert details['model_calls'] is False and details['owner_reads'] is False and details['writes'] is False
    assert not state.exists()


def _env(tmp_path):
    return {**{k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC'}},
            'TEMP':str(tmp_path),'TMP':str(tmp_path),'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}


def test_missing_viewer_has_actionable_refusal(tmp_path):
    p=subprocess.run([sys.executable,'-B','-X','utf8',str(SCRIPT),'--bundle',str(tmp_path/'missing.json'),
                      '--viewer-root',str(tmp_path/'missing-viewer')],cwd=tmp_path,env=_env(tmp_path),capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert p.returncode==2 and '--viewer-root' in p.stderr
    assert 'Traceback' not in p.stderr and not p.stdout


def test_view_launcher_only_requires_the_public_module_entrypoint(tmp_path):
    viewer = tmp_path / 'viewer'
    package = viewer / 'src' / 'iqs_viewer_lab'
    package.mkdir(parents=True)
    (package / '__init__.py').touch()
    (package / '__main__.py').write_text(
        'import json, os, sys\n'
        'if __name__ == "__main__":\n'
        '    print(json.dumps({"argv": sys.argv[1:], "pid": os.getpid()}), flush=True)\n'
        '    raise SystemExit(7)\n', encoding='utf8')
    bundle = tmp_path / 'bundle.json'
    with subprocess.Popen(
        [sys.executable, '-B', str(SCRIPT), '--bundle', str(bundle), '--viewer-root', str(viewer), '--open'],
        cwd=tmp_path, env=_env(tmp_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf8',
    ) as process:
        stdout, stderr = process.communicate(timeout=20)
    assert process.returncode == 7, stderr
    assert json.loads(stdout) == {
        'argv': ['serve', '--bundle', str(bundle), '--host', '127.0.0.1', '--port', '0', '--open'],
        'pid': process.pid,
    }


@pytest.mark.parametrize('explicit_root',[False,True])
def test_real_thin_launcher_reads_meta_and_releases_port(tmp_path,explicit_root):
    # Test inputs are explicitly provided; the launcher itself never defaults
    # to a synthetic fixture or reads a production database.
    viewer=(Path(os.environ.get('IQS_TEST_VIEWER_ROOT',ROOT.parent/'iqs-viewer-lab')) if explicit_root else ROOT.parent/'iqs-viewer-lab')
    bundle=viewer/'fixtures/demo/bundle.json'
    if not bundle.is_file():pytest.skip('External VIEW source unavailable; provide IQS_TEST_VIEWER_ROOT for explicit-root integration.')
    args=[sys.executable,'-B','-X','utf8',str(SCRIPT),'--bundle',str(bundle)]
    if explicit_root:args.extend(['--viewer-root',str(viewer)])
    p=subprocess.Popen(args,cwd=tmp_path,env=_env(tmp_path),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
    lines=queue.Queue()
    reader=threading.Thread(target=lambda:lines.put(p.stdout.readline()),daemon=True);reader.start()
    try:
        ready=json.loads(lines.get(timeout=15))
        assert ready['pid']==p.pid and ready['data_kind']=='synthetic'
        with urllib.request.urlopen(ready['url']+'api/meta',timeout=5) as response:
            assert json.loads(response.read())['bundle_sha256']==ready['bundle_sha256']
        port=int(ready['url'].rsplit(':',1)[1].rstrip('/'))
    finally:
        if p.poll() is None:p.terminate()
        p.wait(timeout=10);reader.join(timeout=2)
        p.stdout.close();p.stderr.close()
    assert not reader.is_alive()
    with socket.socket() as sock:
        sock.settimeout(1)
        try:sock.connect(('127.0.0.1',port))
        except OSError:pass
        else:raise AssertionError('Owned listener was not closed')
