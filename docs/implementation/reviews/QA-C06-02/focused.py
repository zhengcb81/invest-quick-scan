"""Correct only controller setup errors; run concentrated new boundaries."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import IQS,OWN,QA,OUT,execute,save

def main():
    guard=OWN/'guard/sitecustomize.py'
    original=guard.read_text('utf-8')
    needle="    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind', 'socket.sendto'}:\n        raise PermissionError('E97 network forbidden')"
    replacement="""    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind', 'socket.sendto'}:
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
        raise PermissionError('E97 network forbidden')"""
    assert original.count(needle)==1
    guard.write_text(original.replace(needle,replacement).replace('def audit(event, args):',
        '_qa100_pair_sockets=[]\n\ndef audit(event, args):'),encoding='utf-8')
    (OUT/'sitecustomize-corrected.py').write_bytes(guard.read_bytes())
    cases=OWN/'controller_cases.py'
    cases.write_bytes((Path(__file__).resolve().parent/'acceptance_cases.py').read_bytes())
    (OUT/'controller-cases-executed.py').write_bytes(cases.read_bytes())
    selectors=[
       'tests/unit/test_quick_scan_work_store.py::test_v1_migration_preserves_work_rows_and_adds_empty_checkpoint_table',
       'tests/unit/test_quick_scan_work_store.py::test_v1_migration_rejects_completed_work_without_checkpoint',
       'tests/unit/test_quick_scan_work_store.py::test_fixed_v2_migration_preserves_existing_rows_and_adds_budget_ledger',
       'tests/unit/test_quick_scan_budget.py::test_async_search_settles_the_same_durable_budget_ledger']
    checks=[]
    checks.append(execute('controller-setup-retest',['-m','pytest',*selectors,'-q','-o','addopts=',
       '-p','no:cacheprovider','--basetemp',str(OWN/'tmp/retest')]))
    checks.append(execute('public-handoff-correct-catalog',[str(IQS/'scripts/parallel_handoff_cli.py'),
       '--input',str(OUT.parent/'worker/handoff.json'),'--package-id','QA-C06-02',
       '--catalog',str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json')]))
    checks.append(execute('controller-boundaries',['-m','pytest',str(cases),'-q','-o','addopts=',
       '-p','no:cacheprovider','--basetemp',str(OWN/'tmp/boundaries')]))
    save(OUT/'focused-result.json',dict(checks=checks,source_written=False,
       internal_loopback='only ephemeral Windows asyncio socketpair',external_http=0,paid_calls=0))

if __name__=='__main__': main()
