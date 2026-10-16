"""Independent offline acceptance launcher; applies guards to descendants too."""
import os, sys, pathlib, subprocess, runpy, json, datetime
ROOT = pathlib.Path(__file__).resolve().parent
LAB = ROOT / 'catl2'
ALLOWED = (ROOT.resolve(),)
events = {'network_attempts': 0, 'external_write_attempts': 0}
def audit(event, args):
    if event.startswith('socket.'):
        events['network_attempts'] += 1
        raise RuntimeError('acceptance network guard: ' + event)
    paths = []
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes, os.PathLike)) and ((isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))): paths = [path]
    elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.utime'): paths = [args[0]]
    elif event in ('os.rename','os.replace'): paths = list(args[:2])
    for path in paths:
        p = pathlib.Path(os.fsdecode(path)).resolve()
        if not any(p.is_relative_to(base) for base in ALLOWED):
            events['external_write_attempts'] += 1
            raise RuntimeError('acceptance external write guard: ' + str(p))
sys.addaudithook(audit)
original_popen = subprocess.Popen
class GuardedPopen(original_popen):
    def __init__(self, args, *a, **kw):
        if isinstance(args, list) and pathlib.Path(str(args[0])).name.lower() in ('python.exe','python','python3'):
            rest = args[1:]
            if rest[:3] == ['-B','-X','utf8']: rest = rest[3:]
            args = [args[0], '-B', '-X', 'utf8', str(ROOT/'catl2_guard.py'), '--child', *rest]
        else: raise RuntimeError('unapproved child command')
        super().__init__(args,*a,**kw)
subprocess.Popen = GuardedPopen
sys.dont_write_bytecode = True
sys.path.insert(0,str(LAB))
args = sys.argv[1:]
if args and args[0] == '--child': args.pop(0)
try:
    if args[:1] == ['-m']:
        sys.argv = args[1:]
        runpy.run_module(args[1], run_name='__main__', alter_sys=True)
    elif args[:1] == ['-c']:
        sys.argv = ['-c', *args[2:]]
        exec(compile(args[1], '<guarded-child>', 'exec'), {'__name__':'__main__'})
    elif args[:1] == ['--suite']:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(LAB/'tests'), pattern='test*.py',top_level_dir=str(LAB))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(not result.wasSuccessful())
    elif args[:1] == ['--script']:
        sys.argv = args[1:]
        runpy.run_path(args[1], run_name='__main__')
    elif args and args[0].endswith('.py') and pathlib.Path(args[0]).resolve().is_relative_to(LAB):
        sys.argv = args
        runpy.run_path(args[0], run_name='__main__')
    else: raise RuntimeError('unsupported launcher arguments')
finally:
    with (ROOT/'catl2-guard-events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'pid':os.getpid(),'argv':args,**events})+'\n')
