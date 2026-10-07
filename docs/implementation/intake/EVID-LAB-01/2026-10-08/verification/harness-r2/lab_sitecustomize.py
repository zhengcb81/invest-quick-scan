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


def audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind', 'socket.sendto'}:
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
        if env is None or env.get('E97_OWNED_ROOT') != str(OWNED) or str(OWNED / 'guard') not in env.get('PYTHONPATH', ''):
            raise PermissionError('E97 child guard not inherited')
        if any(k.upper().endswith('_API_KEY') for k in env):
            raise PermissionError('E97 credentials in child environment')


sys.addaudithook(audit)
