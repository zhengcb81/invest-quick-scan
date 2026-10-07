"""Adaptive paired experiment: frozen parent inputs, existing StockQA transport.

No production data, new HTTP implementation, or question repair. Fee limits are
shared by terminal ledger snapshots, not independent unaccounted child caps.
"""
import argparse
import json
import os
import random
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import batching_benchmark as b
import batching_benchmark_archive as a
import batching_benchmark_report as report
import mimo_pro_pilot as p

SOURCES=['scripts/mimo_pilot_extension.py','scripts/mimo_pro_pilot.py','scripts/batching_benchmark.py',
         'scripts/batching_benchmark_report.py','scripts/batching_benchmark_archive.py']
PARENT=b.ROOT/'runs/mimo-pro-pilot-2026-10-07-01'
THINKING=b.ROOT/'runs/mimo-pro-pilot-2026-10-07-thinking-all'
JSONOFF=b.ROOT/'runs/mimo-pro-pilot-2026-10-07-jsonoff'
AGGREGATE=dict(model=200,search=24,usd=8)


def policy(route,mode):
    if mode=='jsonoff':return None
    return dict(thinking={'type':'adaptive' if route=='minimax' and mode=='on' else 'enabled' if mode=='on' else 'disabled'},
                max_completion_tokens=10000,omit_temperature=True)


def blocks_for(kind):
    if kind=='thinking':
        return [(s,r,m) for s in p.TOPICS for r in ('mimo','mimo_pro','deepseek','minimax')
                for m in ('off','on') if not (r=='mimo_pro' and m=='on')]
    return [(s,r+'_nojson','jsonoff') for s in p.TOPICS for r in ('mimo','mimo_pro')]


def digest(path):return b.hashlib.sha256(path.read_bytes()).hexdigest()


def check_parent(parent):
    lock=json.loads((parent/'pilot-input-lock.json').read_text(encoding='utf-8'))
    for name,sha in lock['files'].items():
        if digest(parent/name)!=sha:raise ValueError('parent_input_drift_zero_send')
    if lock['system_sha256']!=b.hashlib.sha256(b.SYSTEM.encode()).hexdigest():
        raise ValueError('parent_system_drift_zero_send')
    return lock


def freeze_files(run,names):
    names=names+['source/'+Path(s).name for s in SOURCES]
    b.write_json(run/'extension-input-lock.json',dict(files={n:digest(run/n) for n in names},
          system_sha256=b.hashlib.sha256(b.SYSTEM.encode()).hexdigest(),routes_sha256=b.fingerprint(b.ROUTES)))


def verify_files(run):
    lock=json.loads((run/'extension-input-lock.json').read_text(encoding='utf-8'))
    if any(digest(run/n)!=sha for n,sha in lock['files'].items()):raise ValueError('extension_input_drift_zero_send')
    if lock['system_sha256']!=b.hashlib.sha256(b.SYSTEM.encode()).hexdigest() or lock['routes_sha256']!=b.fingerprint(b.ROUTES):
        raise ValueError('extension_input_drift_zero_send')
    for s in SOURCES:
        if (run/'source'/Path(s).name).read_bytes()!=(b.ROOT/s).read_bytes():raise ValueError('extension_input_drift_zero_send')
    return b.fingerprint(lock)


def dependencies(kind):return [PARENT]+([THINKING] if kind=='jsonoff' else [])


def prepare(run,kind):
    if (run/'extension-input-lock.json').exists():return {'resumed':True,'live_requests':0}
    if (run/'attempts.jsonl').exists() and (run/'attempts.jsonl').stat().st_size:raise ValueError('prepare_after_send')
    parent_lock=check_parent(PARENT)
    for source in dependencies(kind):
        if (source/'orchestrator.lock').exists():raise ValueError('parent_is_running')
    summaries=[b.Ledger(source).summary() for source in dependencies(kind)]
    # Pending outcomes remain fully reserved; they never create free budget.
    used={k:sum(s[v] for s in summaries) for k,v in (('model','model_requests'),('search','search_requests'),('usd','charged_upper_usd'))}
    calls=len(blocks_for(kind))*2
    if used['model']+calls>AGGREGATE['model'] or used['search']>AGGREGATE['search'] or used['usd']>=AGGREGATE['usd']:
        raise ValueError('aggregate_budget_exhausted')
    for folder in ('source','parent-source','runtime','evidence','results','blocks','tmp','logs'):
        (run/folder).mkdir(parents=True,exist_ok=True)
    for name in ('questions.json','companies.json','runtime-manifest.json'):
        (run/name).write_bytes((PARENT/name).read_bytes())
    for slug in p.TOPICS:
        (run/'evidence'/(slug+'-targeted.json')).write_bytes((PARENT/'evidence'/(slug+'-targeted.json')).read_bytes())
    for name in b.RUNTIME_FILES:
        target=run/'runtime'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((PARENT/'runtime'/name).read_bytes())
    for name in p.SOURCES:
        (run/'parent-source'/Path(name).name).write_bytes((PARENT/'source'/Path(name).name).read_bytes())
    for name in SOURCES:
        (run/'source'/Path(name).name).write_bytes((b.ROOT/name).read_bytes())
    # Preserve the original adaptive prepare record rather than rewrite history.
    if (run/'run-manifest.json').exists() and not (run/'initial-adaptive-registration.json').exists():
        (run/'initial-adaptive-registration.json').write_bytes((run/'run-manifest.json').read_bytes())
    budget=dict(model_http_cap=calls,search_http_cap=0,cash_usd_cap=round(AGGREGATE['usd']-used['usd'],6))
    b.write_json(run/'budget.json',budget)
    registration=dict(experiment='mimo_paired_extension/2',kind=kind,created_at=b.now(),calls=calls,
            aggregate_caps=AGGREGATE,previous_budget=used,parent_input_fingerprint=b.fingerprint(parent_lock),
            parent_ledgers={str(s):digest(s/'attempts.jsonl') for s in dependencies(kind)},
            parent_file_hashes={name:parent_lock['files'][name] for name in ['questions.json','companies.json','runtime-manifest.json']+
                               ['evidence/'+s+'-targeted.json' for s in p.TOPICS]},
            blocks=blocks_for(kind),policies={r+':'+m:policy(r,m) for _,r,m in blocks_for(kind)},
            reused_pro_on='three original main thinking blocks; same cap/no temperature/exact frozen prompt; do not resend',
            reasoning_storage='separate field discarded; final answer and usage only',
            accuracy='source-support audit, not human gold/world factual correctness',
            source_revisions={s:digest(b.ROOT/s) for s in SOURCES})
    b.write_json(run/'registration.json',registration)
    b.write_json(run/'run-manifest.json',registration)
    b.write_json(run/'route-snapshot.json',b.ROUTES)
    names=['questions.json','companies.json','runtime-manifest.json','budget.json','registration.json','run-manifest.json','route-snapshot.json']
    names+=['evidence/'+s+'-targeted.json' for s in p.TOPICS]+['runtime/'+s for s in b.RUNTIME_FILES]
    names+=['parent-source/'+Path(s).name for s in p.SOURCES]
    freeze_files(run,names)
    return {'prepared':kind,'planned_calls':calls,'remaining_upper_usd':budget['cash_usd_cap'],'live_requests':0}


def verify(run,kind):
    binding=verify_files(run)
    reg=json.loads((run/'registration.json').read_text(encoding='utf-8'))
    if reg['kind']!=kind or b.fingerprint(check_parent(PARENT))!=reg['parent_input_fingerprint']:
        raise ValueError('parent_binding_drift_zero_send')
    for source,sha in reg['parent_ledgers'].items():
        if digest(Path(source)/'attempts.jsonl')!=sha or (Path(source)/'orchestrator.lock').exists():
            raise ValueError('parent_ledger_drift_zero_send')
    for name,sha in reg['parent_file_hashes'].items():
        if digest(run/name)!=sha:raise ValueError('paired_copy_drift_zero_send')
    return binding


def execute(run,kind,ledger,module):
    binding=verify(run,kind)
    companies=json.loads((run/'companies.json').read_text(encoding='utf-8'))
    qs=json.loads((run/'questions.json').read_text(encoding='utf-8'))
    delegate=b.install_observer(module)
    blocks=blocks_for(kind);random.Random(2026100742).shuffle(blocks)
    for slug,route,mode in blocks:
        arm=f'paired-{mode}.{slug}.{route}.g5.targeted';target=run/'blocks'/(arm+'.json')
        if target.exists():
            if json.loads(target.read_text(encoding='utf-8'))['run_fingerprint']!=binding:raise ValueError('block_binding_drift')
            continue
        if any(x.get('arm')==arm for x in ledger.reserved.values()):
            raise ValueError('pending_reconciliation_no_resend')
        verify(run,kind)
        base=route.removesuffix('_nojson')
        for source in dependencies(kind):
            old=b.Ledger(source)
            if any((f.get('http_status') in (401,403,429) or f.get('business_error_code')==2056)
                   and old.reserved[aid].get('route') in (base,route) for aid,f in old.finished.items()):
                raise ValueError('parent_route_cooldown_no_alias_bypass')
        ev=json.loads((run/'evidence'/(slug+'-targeted.json')).read_text(encoding='utf-8'))
        t=time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as pool:
            fs=[pool.submit(b.call_chunk,module,delegate,ledger,run,companies[slug],qs[i:i+5],ev,route,arm,
                            generation_overrides=policy(route,mode)) for i in (0,5)]
            results=[f.result() for f in fs]
        valid=[r for r in results if r['state']=='valid']
        block=dict(arm=arm,stage='paired-'+mode,company=slug,route=route,group_size=5,requested=10,
              valid_rows=sum(len(r['answers']) for r in valid),scored=sum(q['status']=='scored' for r in valid for q in r['answers']),
              wall_s=round(time.monotonic()-t,3),question_ids=p.QIDS,evidence_variant='targeted',
              evidence_sha256=b.fingerprint(ev),prompt_profile='v5',chunks=[r['chunk_id'] for r in results],
              run_fingerprint=binding,concurrency=2,thinking=mode=='on',parameters=policy(route,mode))
        b.write_json(target,block);print(json.dumps({k:block[k] for k in ('arm','valid_rows','scored','wall_s')}),flush=True)
    return ledger.summary()


def warm(run,kind,ledger):
    verify(run,kind)
    before=digest(run/'attempts.jsonl')
    outputs={str(f):digest(f) for f in (run/'results').glob('*.json')}
    companies=json.loads((run/'companies.json').read_text(encoding='utf-8'))
    qs={q['question_id']:q for q in json.loads((run/'questions.json').read_text(encoding='utf-8'))}
    old=b.read_key
    b.read_key=lambda *_: (_ for _ in ()).throw(AssertionError('warm_key_read'))
    hits=0
    try:
        for f in (run/'results').glob('*.json'):
            result=json.loads(f.read_text(encoding='utf-8'))
            if result['state']!='valid':continue
            slug=next(s for s,c in companies.items() if c['entity_id']==result['entity_id'])
            mode=result['arm'].split('.')[0].removeprefix('paired-')
            ev=json.loads((run/'evidence'/(slug+'-targeted.json')).read_text(encoding='utf-8'))
            cached=b.call_chunk(None,None,ledger,run,companies[slug],[qs[q] for q in result['question_ids']],ev,
                     result['route'],result['arm'],warm=True,generation_overrides=policy(result['route'],mode))
            if not cached['cache_hit']:raise AssertionError('warm_miss')
            hits+=1
    finally:b.read_key=old
    if digest(run/'attempts.jsonl')!=before or any(digest(Path(f))!=sha for f,sha in outputs.items()):
        raise AssertionError('warm_mutation')
    proof=dict(cache_hits=hits,new_http=0,key_reads=0,ledger_sha256=before,result_hashes_unchanged=True,
               scope='valid cached chunks only; invalid/unknown are not replayed or declared cached')
    b.write_json(run/'cache-resume-proof.json',proof)
    return proof


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run','warm','summary','archive'])
    ap.add_argument('--kind',required=True,choices=['thinking','jsonoff']);args=ap.parse_args()
    run=THINKING if args.kind=='thinking' else JSONOFF
    run.mkdir(parents=True,exist_ok=True)
    for folder in ('tmp','logs'):(run/folder).mkdir(exist_ok=True)
    for name in ('TEMP','TMP','TMPDIR'):os.environ[name]=str(run/'tmp')
    tempfile.tempdir=str(run/'tmp');sys.dont_write_bytecode=True
    if args.kind=='jsonoff':
        for base in ('mimo','mimo_pro'):b.ROUTES[base+'_nojson']=dict(b.ROUTES[base])
    lock=run/'orchestrator.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode())
        if args.action=='prepare':result=prepare(run,args.kind)
        else:
            verify(run,args.kind)
            budget=json.loads((run/'budget.json').read_text(encoding='utf-8'))
            ledger=b.Ledger(run,budget['model_http_cap'],0,budget['cash_usd_cap'])
            if args.action=='warm':result=warm(run,args.kind,ledger)
            elif args.action=='summary':
                result=report.summarize(run);b.write_json(run/'analysis.json',result)
            elif args.action=='archive':
                result=a.archive(run,b.ROOT/'docs/implementation/experiments/artifacts'/run.name,lock_owner_pid=os.getpid())
            else:
                # Main guard plus the one additional official MiniMax host.
                p.install_live_guard(run,extra_hosts={'api.minimaxi.com'})
                result=execute(run,args.kind,ledger,b.load_runtime(run))
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:os.close(fd);lock.unlink()


if __name__=='__main__':main()
