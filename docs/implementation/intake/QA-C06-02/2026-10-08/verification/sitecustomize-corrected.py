"""Controller test guard, inherited by Python subprocesses. No provider calls."""
import os
from pathlib import Path
import subprocess
import sys

OWNED = Path(os.environ['E97_OWNED_ROOT']).resolve()


def writable(raw):
    if isinstance(raw, int):
        return
    path = Path(os.fsdecode(raw)).resolve()
    if path == Path(os.devnull).resolve():
        return  # pytest's default logging sink; no persistent file write
    if not path.is_relative_to(OWNED):
        raise PermissionError('E97 write outside owned test root')


_qa100_pair_sockets=[]

def audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind', 'socket.sendto'}:
        # Windows asyncio's socketpair: exact ephemeral loopback binding and
        # connect only to one of those bound sockets. No external address,
        # arbitrary listener or model/search HTTP is admitted.
        if event == 'socket.bind' and args[1] == ('127.0.0.1', 0):
            _qa100_pair_sockets.append(args[0])
            return
        if event == 'socket.connect':
            for sock in _qa100_pair_sockets:
                try:
                    if sock.getsockname() == args[1]:
                        return
                except OSError:
                    pass
        raise PermissionError('E97 network forbidden')
    if event == 'open':
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            writable(args[0])
    if event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime'}:
        writable(args[0])
    if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'}:
        writable(args[0]); writable(args[1])
    if event in {'os.system', 'os.exec', 'os.posix_spawn'}:
        raise PermissionError('E97 shell execution forbidden')
    if event == 'subprocess.Popen':
        executable, argv, cwd, env = args
        # Windows audit exposes executable=None and a command-line string.
        same_python = (Path(executable).resolve() == Path(sys.executable).resolve()) if executable else (
            isinstance(argv,str) and argv.startswith(subprocess.list2cmdline([sys.executable])+' '))
        if not same_python:
            raise PermissionError('E97 only Python child processes allowed')
        if cwd is None or not Path(cwd).resolve().is_relative_to(OWNED):
            raise PermissionError('E97 child cwd outside owned root')
        if env is None or env.get('E97_OWNED_ROOT') != str(OWNED):
            raise PermissionError('E97 child guard not inherited')
        # The delivered test resets PYTHONPATH to src. Enforce the controller's
        # guard at the launch boundary while running the real child CLI intact.
        guard_dir = str(OWNED / 'guard')
        if guard_dir not in env.get('PYTHONPATH', '').split(os.pathsep):
            env['PYTHONPATH'] = guard_dir + os.pathsep + env.get('PYTHONPATH','')
        if any(k.upper().endswith('_API_KEY') for k in env):
            raise PermissionError('E97 credentials in child environment')


sys.addaudithook(audit)

if os.environ.get('QA100_STUB_HTTP') == '1':
    import importlib.util
    import json
    import re
    import requests
    test_path = Path(os.environ['QA100_QA_ROOT'])/'tests/integration/test_qa_c06_02_e2e.py'
    spec = importlib.util.spec_from_file_location('qa100_fixture',test_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    def _qa100_post(self,*args,**kwargs):
        text=kwargs['json']['input']
        match=re.search(r'Target question_id: ([A-Za-z0-9_.]+)\.',text)
        assert match is not None
        with (Path.cwd()/'http-stub-sends.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'question_id':match.group(1),'synthetic_only':True})+'\n')
        return fixture._response_for(match.group(1))
    requests.Session.post=_qa100_post
