"""Execute exact driver AST refusal seams only: no native authority/DB/network."""
import ast
from contextlib import contextmanager, closing
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

BASE = Path(__file__).resolve().parents[1]

def worker_scan(processes):
    tree = ast.parse((BASE / "activate_real_native_smoke.py").read_text(encoding="utf8"))
    main = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "main")
    start = next(i for i,x in enumerate(main.body) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Tuple) and any(isinstance(n, ast.Name) and n.id == "matched_workers" for n in t.elts) for t in x.targets))
    end = next(i for i,x in enumerate(main.body[start:],start) if isinstance(x,ast.If) and isinstance(x.test,ast.BoolOp) and any(isinstance(v,ast.Name) and v.id=="matched_workers" for v in x.test.values))
    module = ast.Module(body=main.body[start:end+1],type_ignores=[])
    class Unreadable(Exception): pass
    env = {"ROOT": Path.cwd(), "Path":Path, "os":os, "psutil":SimpleNamespace(process_iter=lambda _:processes,AccessDenied=Unreadable,NoSuchProcess=Unreadable)}
    exec(compile(module,"exact-activation-worker-seam","exec"),env)

class Process:
    pid = -1
    info = {"name":"python.exe"}
    def __init__(self,cwd,args): self.working,self.args=cwd,args
    def cwd(self): return str(self.working)
    def cmdline(self): return self.args

@pytest.mark.parametrize("kind", ["cwd", "relative_arg", "absolute_ledger"])
def test_original_worker_relative_and_absolute_paths_refuse(kind):
    root=Path.cwd(); original=root/"runs/company-agent-owner-2026-10-15-01"
    working=original if kind=="cwd" else root
    args={"cwd":["python","worker.py"],"relative_arg":["python","runs/company-agent-owner-2026-10-15-01/worker.py"],"absolute_ledger":["python",str(original/"execution/quick_scan_work.sqlite")]}[kind]
    with pytest.raises(ValueError,match="not_quiescent"):
        worker_scan([Process(working,args)])

def test_unrelated_similar_prefix_does_not_masquerade_as_worker():
    worker_scan([Process(Path.cwd()/"runs/company-agent-owner-2026-10-15-01-other",["python","worker.py"])])

def lease_scope(expiry):
    tree=ast.parse((BASE/"run_real_admitted_smoke.py").read_text(encoding="utf8"))
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="scope_with_diagnostic_time_budget")
    observations=[]; original_calls=[]
    @contextmanager
    def original_scope(envelope):
        original_calls.append(envelope)
        yield
    class Connection:
        def close(self): pass
        def execute(self,*args): return self
        def fetchall(self): return [(expiry,)]
    env={"contextmanager":contextmanager,"closing":closing,"original_scope":original_scope,"services":SimpleNamespace(_handles={"Q":{"work_item_id":"W"}},store=SimpleNamespace(path=Path.cwd()/"no-read.sqlite")),"sqlite3":SimpleNamespace(connect=lambda *a,**kw:Connection()),"time":SimpleNamespace(time=lambda:100),"atomic_json":lambda p,v:observations.append(v),"own":BASE}
    exec(compile(ast.Module(body=[node],type_ignores=[]),"exact-driver-time-seam","exec"),env)
    return env["scope_with_diagnostic_time_budget"],observations,original_calls

@pytest.mark.parametrize("expiry,allowed", [(459,False),(460,True),(None,False)])
def test_diagnostic_refuses_insufficient_time_after_original_scope(expiry,allowed):
    scope,observed,calls=lease_scope(expiry)
    if allowed:
        with scope({"original":"called"}): pass
        assert observed[0]["model_network_timeout_seconds"]==240
        assert observed[0]["minimum_remaining_required_seconds"]==360
    else:
        with pytest.raises(ValueError):
            with scope({"original":"called"}):
                pytest.fail("insufficient lease yielded to SDK")
    assert calls==[{"original":"called"}]
