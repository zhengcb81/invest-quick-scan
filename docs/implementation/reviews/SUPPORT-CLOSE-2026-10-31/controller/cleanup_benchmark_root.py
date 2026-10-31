"""Delete only controller-owned temporary benchmark roots, after handle release."""
from pathlib import Path
import shutil,time
ROOT=Path(__file__).resolve().parents[2]


def cleanup_owned(path):
    path=Path(path)
    if path.is_symlink() or path.is_junction() or path.resolve().parent!=ROOT.resolve() or not path.name.startswith(('.c31bench-','.c31resume-')):
        raise ValueError('benchmark cleanup outside owned boundary')
    deadline=time.monotonic()+30
    retries=0
    while path.exists():
        try:
            shutil.rmtree(path)
        except PermissionError:
            # Terminated Windows descendants may close SQLite handles slightly
            # later than the tree-kill command returns. Never ignore leftovers.
            if time.monotonic()>=deadline:raise
            retries+=1
            time.sleep(.5)
    return {'root':str(path),'removed':True,'bounded_handle_release_retry':True,'retries':retries}
