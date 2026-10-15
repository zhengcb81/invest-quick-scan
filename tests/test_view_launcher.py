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


def _env(tmp_path):
    return {**{k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC'}},
            'TEMP':str(tmp_path),'TMP':str(tmp_path),'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}


def test_missing_viewer_has_actionable_refusal(tmp_path):
    p=subprocess.run([sys.executable,'-B','-X','utf8',str(SCRIPT),'--bundle',str(tmp_path/'missing.json'),
                      '--viewer-root',str(tmp_path/'missing-viewer')],cwd=tmp_path,env=_env(tmp_path),capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert p.returncode==2 and '--viewer-root' in p.stderr
    assert 'Traceback' not in p.stderr and not p.stdout


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
