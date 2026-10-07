"""Small paid experiment; reuses B01 and StockQA transport, never production data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import batching_benchmark as b
import batching_benchmark_archive as archive_tools
import batching_benchmark_report as report

QIDS = ['IQS_01','IQS_02','IQS_04','IQS_05','IQS_08','IQS_09','IQS_10','IQS_12','IQS_13','IQS_16']
MODELS = ['mimo','mimo_pro','deepseek']
SOURCES = ['scripts/mimo_pro_pilot.py','scripts/batching_benchmark.py',
           'scripts/batching_benchmark_report.py','scripts/batching_benchmark_archive.py']
TOPICS = {
    'catl': ['2025 2026 动力电池 储能电池 客户 复购 市占率',
             '2025 2026 营业收入 净利润 经营现金流 研发 资本支出',
             '2025 2026 净资产 股东权益 现金 负债 到期债务',
             '2025 2026 公司治理 管理层 关联交易 股权 激励'],
    'cncb_h': ['2025 2026 财富管理 投顾 客户 复购 竞争优势',
               '2025 2026 营业收入 净利润 经营现金流 加权净资产收益率',
               '2025 2026 净资本 风险覆盖率 客户资产 负债 到期债务',
               '2025 2026 公司治理 管理层 永续资本 股东权益'],
    'alphabet': ['2025 2026 Google Search Cloud advertising customers competition retention',
                 '2025 2026 revenue net income operating cash flow capex AI',
                 '2025 2026 cash debt maturity shareholder equity returns capital',
                 '2025 2026 governance Class A B C voting rights management compensation'],
}
DOMAINS = {'catl':['catl.com','szse.cn'],
           'cncb_h':['csc108.com','hkexnews.hk','sse.com.cn'],
           'alphabet':['abc.xyz','google.com','sec.gov']}


def install_live_guard(run,extra_hosts=frozenset()):
    """Bounded Python audit guard; not an OS sandbox for native extensions."""
    if set(extra_hosts)-{'api.minimaxi.com'}:raise ValueError('unexpected_extra_host')
    hosts={'api.xiaomimimo.com','api.deepseek.com','api.search.brave.com','api.tavily.com'}|set(extra_hosts)
    def audit(event,args):
        if event=='socket.getaddrinfo' and args[0] not in hosts:
            raise PermissionError('pilot_nonallowlisted_dns')
        if event=='socket.connect' and isinstance(args[1],tuple) and args[1][1]!=443:
            raise PermissionError('pilot_non_https_connect')
        if event in ('subprocess.Popen','os.system','os.posix_spawn'):
            raise PermissionError('pilot_no_subprocess')
        writing=event=='open' and ((isinstance(args[1],str) and any(m in args[1] for m in 'wax+'))
                    or (isinstance(args[2],int) and bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))))
        paths=[args[0]] if writing or event in ('os.mkdir','os.remove','os.rmdir') else args[:2] if event in ('os.rename','os.link','os.symlink') else []
        for path in paths:
            if isinstance(path,(str,bytes,os.PathLike)) and not Path(os.fsdecode(path)).resolve().is_relative_to(run):
                raise PermissionError('pilot_root_out_write')
    sys.addaudithook(audit)
    try:
        with (run.parent/'mimo-pro-guard-canary').open('w'):
            pass
    except PermissionError:
        pass
    else:
        raise AssertionError('write_guard_canary_failed')
    import socket
    try:
        socket.getaddrinfo('example.invalid',443)
    except PermissionError:
        pass
    else:
        raise AssertionError('dns_guard_canary_failed')


def prepare(run):
    if (b.ROOT/'docs/implementation/experiments/artifacts'/run.name).exists():
        raise ValueError('run_id_already_archived_zero_send')
    if (run/'pilot-registration.json').exists():
        return {'resumed':True,'live_requests':0}
    b.prepare(run)
    original=json.loads((run/'questions.json').read_text(encoding='utf-8'))
    qmap={q['question_id']:q for q in original}
    if not set(QIDS)<=set(qmap):
        raise ValueError('frozen_question_missing')
    b.write_json(run/'questions.json',[qmap[q] for q in QIDS])
    b.write_json(run/'budget.json',dict(model_http_cap=160,search_http_cap=24,cash_usd_cap=5,
                 authorized_by='user_mimo_pro_small_pilot_2026-10-07'))
    b.write_json(run/'pilot-registration.json',dict(experiment='mimo_pro_pilot/1',created_at=b.now(),
                 companies=list(TOPICS),question_ids=QIDS,routes={r:b.ROUTES[r] for r in MODELS},
                 matrix_groups=[1,5,10],planned_model_calls=132,planned_search_calls=24,
                 topics=TOPICS,domains=DOMAINS,model_native_search=False,
                 accuracy='agent source-support audit, not human gold/world accuracy',
                 price_source='https://mimo.mi.com/docs/pricing'))
    (run/'source').mkdir()
    for path in SOURCES:
        (run/'source'/Path(path).name).write_bytes((b.ROOT/path).read_bytes())
    b.write_json(run/'run-manifest.json',dict(experiment='mimo_pro_pilot/1',created_at=b.now(),
                 stockqa_commit=b.FROZEN_COMMIT,files={p:hashlib.sha256((b.ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
                 scope='three-company pilot; not L03/production/gate closure'))
    return {'companies':3,'questions_each':10,'live_requests':0}


def freeze(run, check_only=False):
    paths=['questions.json','companies.json','runtime-manifest.json','budget.json','pilot-registration.json']
    paths += ['source/'+Path(p).name for p in SOURCES]
    paths += ['evidence/'+s+'-targeted.json' for s in TOPICS]
    lock={'files':{p:hashlib.sha256((run/p).read_bytes()).hexdigest() for p in paths},
          'system_sha256':hashlib.sha256(b.SYSTEM.encode()).hexdigest(),
          'routes_sha256':b.fingerprint({r:b.ROUTES[r] for r in MODELS})}
    target=run/'pilot-input-lock.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))!=lock:
            raise ValueError('pilot_input_drift_zero_send')
    elif check_only:
        raise ValueError('pilot_not_frozen')
    else:
        b.write_json(target,lock)
        b.verify_model_inputs(run)
    # Archived source and executing source must match, not merely each other.
    for path in SOURCES:
        if (run/'source'/Path(path).name).read_bytes()!=(b.ROOT/path).read_bytes():
            raise ValueError('executing_source_drift_zero_send')
    return b.fingerprint(lock)


def search(run, module, ledger):
    results=[]
    for slug in TOPICS:
        results.append(b.targeted_search(run,module,ledger,slug,TOPICS[slug],DOMAINS[slug]))
    return {'results':results,'budget':ledger.summary()}


def execute(run, module, ledger, stage):
    binding=freeze(run,True)
    companies=json.loads((run/'companies.json').read_text(encoding='utf-8'))
    questions=json.loads((run/'questions.json').read_text(encoding='utf-8'))
    groups=[1,5,10] if stage=='matrix' else [10] if stage=='repeat' else [5]
    routes=MODELS if stage!='thinking' else ['mimo_pro']
    blocks=[(s,r,g) for s in TOPICS for r in routes for g in groups]
    random.Random(20261007+{'matrix':101,'repeat':102,'thinking':103}[stage]).shuffle(blocks)
    delegate=b.install_observer(module)
    summaries=[]
    for slug,route,group in blocks:
        arm=f'pilot-{stage}.{slug}.{route}.g{group}.targeted'
        marker=run/'blocks'/(arm+'.json')
        if marker.exists():
            old=json.loads(marker.read_text(encoding='utf-8'))
            if old['run_fingerprint']!=binding:
                raise ValueError('block_binding_drift')
            summaries.append(old)
            continue
        if any(r.get('arm')==arm for r in ledger.reserved.values()):
            print(json.dumps({'arm':arm,'state':'pending_reconciliation'}),flush=True)
            continue
        if any(f.get('http_status') in (401,403,429) and ledger.reserved[a].get('route')==route
               for a,f in ledger.finished.items()):
            print(json.dumps({'arm':arm,'state':'route_cooldown'}),flush=True)
            continue
        evidence=json.loads((run/'evidence'/(slug+'-targeted.json')).read_text(encoding='utf-8'))
        chunks=[questions[i:i+group] for i in range(0,len(questions),group)]
        overrides={'thinking':{'type':'enabled'},'max_completion_tokens':10000} if stage=='thinking' else None
        start=time.monotonic()
        with ThreadPoolExecutor(max_workers=min(4,len(chunks))) as pool:
            futures=[pool.submit(b.call_chunk,module,delegate,ledger,run,companies[slug],q,evidence,route,arm,
                                 repeat=int(stage=='repeat'),generation_overrides=overrides) for q in chunks]
            answers=[f.result() for f in futures]
        valid=[r for r in answers if r['state']=='valid']
        block=dict(arm=arm,stage='pilot-'+stage,run_fingerprint=binding,prompt_profile='v5',
                   company=slug,route=route,group_size=group,requested=10,
                   valid_rows=sum(len(r['answers']) for r in valid),
                   scored=sum(q['status']=='scored' for r in valid for q in r['answers']),
                   wall_s=round(time.monotonic()-start,3),concurrency=min(4,len(chunks)),
                   evidence_variant='targeted',evidence_sha256=b.fingerprint(evidence),
                   question_ids=QIDS,thinking=stage=='thinking',
                   chunks=[r['chunk_id'] for r in answers],
                   attempts=[r['receipt']['attempt_id'] for r in answers if r.get('receipt')])
        b.write_json(marker,block)
        summaries.append(block)
        print(json.dumps({k:block[k] for k in ['arm','valid_rows','scored','wall_s']}),flush=True)
    b.write_json(run/(stage+'-summary.json'),summaries)
    return ledger.summary()


def warm(run, ledger):
    freeze(run,True)
    old_read=b.read_key
    def refuse(*args):
        raise AssertionError('warm_must_not_read_credentials')
    before=hashlib.sha256((run/'attempts.jsonl').read_bytes()).hexdigest()
    companies=json.loads((run/'companies.json').read_text(encoding='utf-8'))
    qmap={q['question_id']:q for q in json.loads((run/'questions.json').read_text(encoding='utf-8'))}
    count=0
    b.read_key=refuse
    try:
        for p in sorted((run/'results').glob('*.json')):
            result=json.loads(p.read_text(encoding='utf-8'))
            if result['state']!='valid':
                continue
            slug=next(s for s,c in companies.items() if c['entity_id']==result['entity_id'])
            evidence=json.loads((run/'evidence'/(slug+'-targeted.json')).read_text(encoding='utf-8'))
            overrides={'thinking':{'type':'enabled'},'max_completion_tokens':10000} if result['arm'].startswith('pilot-thinking.') else None
            cached=b.call_chunk(None,None,ledger,run,companies[slug],[qmap[q] for q in result['question_ids']],
                                evidence,result['route'],result['arm'],warm=True,generation_overrides=overrides)
            if not cached['cache_hit']:
                raise AssertionError('cache_miss')
            count+=1
    finally:
        b.read_key=old_read
    if hashlib.sha256((run/'attempts.jsonl').read_bytes()).hexdigest()!=before:
        raise AssertionError('warm_changed_ledger')
    result={'cache_hits':count,'new_http':0,'key_reads':0,'ledger_sha256':before}
    b.write_json(run/'cache-resume-proof.json',result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['prepare','search','freeze','matrix','repeat','thinking','warm','summary','archive'])
    ap.add_argument('--run',required=True)
    args=ap.parse_args()
    run=Path(args.run).resolve()
    if not run.is_relative_to(b.ROOT/'runs') or not run.name.startswith('mimo-pro-pilot-') or run.is_symlink():
        raise ValueError('not_owned_pilot_root')
    run.mkdir(parents=True,exist_ok=True)
    for folder in ['evidence','blocks','results','tmp','logs']:
        (run/folder).mkdir(exist_ok=True)
    for name in ['TEMP','TMP','TMPDIR']:
        os.environ[name]=str(run/'tmp')
    tempfile.tempdir=str(run/'tmp')
    sys.dont_write_bytecode=True
    lock=run/'orchestrator.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode())
        if args.action=='prepare':
            result=prepare(run)
        elif args.action=='freeze':
            result={'input_fingerprint':freeze(run),'live_requests':0}
        elif args.action=='archive':
            dest=b.ROOT/'docs/implementation/experiments/artifacts'/run.name
            result=archive_tools.archive(run,dest,lock_owner_pid=os.getpid())
        else:
            budget=json.loads((run/'budget.json').read_text(encoding='utf-8'))
            ledger=b.Ledger(run,budget['model_http_cap'],budget['search_http_cap'],budget['cash_usd_cap'])
            if args.action=='warm':
                result=warm(run,ledger)
            elif args.action=='summary':
                result=report.summarize(run)
                b.write_json(run/'analysis.json',result)
            else:
                install_live_guard(run)
                module=b.load_runtime(run)
                result=search(run,module,ledger) if args.action=='search' else execute(run,module,ledger,args.action)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        if fd is not None:
            os.close(fd);lock.unlink()


if __name__=='__main__':
    main()
