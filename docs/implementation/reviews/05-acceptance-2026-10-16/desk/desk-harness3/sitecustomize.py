"""Independent audit sandbox. Inherited by every Python child."""
import os, sys, pathlib, socket, subprocess
ROOT = pathlib.Path(__file__).resolve().parent
LAB = ROOT.parent / 'desk3'
ROOTS = (ROOT.parent,)
def allowed(path):
    if isinstance(path, int) or path is None: return True
    if os.fsdecode(path).lower() in ('nul', '\\\\.\\nul'): return True
    p = pathlib.Path(os.fsdecode(path)).resolve()
    return any(p == r or p.is_relative_to(r) for r in ROOTS)
def check(path):
    if not allowed(path): raise PermissionError('audit external write refused: ' + str(path))
def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and any(t in os.fsdecode(path).lower() for t in ('trial-t4', 't4/results', 'budget.sqlite')):
            raise PermissionError('audit active/private read refused')
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND): check(path)
    elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'): check(args[0])
    elif event in ('os.rename','os.link','os.symlink'):
        check(args[0]); check(args[1])
    elif event == 'socket.connect':
        address=args[1]
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
            raise PermissionError('audit external network refused')
    elif event == 'socket.bind':
        address=args[1]
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
            raise PermissionError('audit non-loopback bind refused')
sys.addaudithook(audit)
_popen = subprocess.Popen
class GuardedPopen(_popen):
    def __init__(self, *args, **kwargs):
        env = dict(kwargs.get('env') or os.environ)
        env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
        kwargs['env'] = env
        super().__init__(*args, **kwargs)
subprocess.Popen = GuardedPopen
