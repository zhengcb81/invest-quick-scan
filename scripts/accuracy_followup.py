"""Paired follow-up to locked accuracy pilot; no production adapter or new HTTP stack."""
import argparse
import json
import os
import random
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlsplit
import accuracy_pilot as p
import batching_benchmark as b
import zai_route_diagnostic as z
PARENT=b.ROOT/'runs/accuracy-pilot-2026-10-07-01'
DIAG=b.ROOT/'runs/accuracy-pilot-zai-diagnostic-2026-10-07-01'
FILES=['scripts/accuracy_followup.py','scripts/zai_route_diagnostic.py','scripts/accuracy_pilot.py','scripts/batching_benchmark.py']
QUERIES={
 'catl':['CATL 2024 H1 revenue cash flow gross margin site:catl.com','CATL Jan May 2024 global battery market share site:catl.com','宁德时代 2024 半年 毛利率 全球份额 site:catl.com'],
 'cncb_h':['CSC Financial 6066 H1 2024 revenue other income site:hkexnews.hk','CSC Financial June 2024 assets equity cash flow site:hkexnews.hk','中信建投 6066 2024 半年 现金流 股东权益 site:hkexnews.hk'],
 'alphabet':['Alphabet FY2024 revenue net income diluted EPS site:abc.xyz','Alphabet FY2024 operating cash flow capital expenditures site:sec.gov','Alphabet FY2024 cash flow purchases property equipment site:abc.xyz']}
DOMAINS={'catl':['catl.com'],'cncb_h':['csc108.com','hkexnews.hk','sse.com.cn'],'alphabet':['abc.xyz','sec.gov']}
SCORE_SYSTEM=b.SYSTEM


def normalize(row,provider,query):
    """Keep bounded summary headers/units; never fetch webpage or raw content."""
    text=row.get('description','') if provider=='brave' else row.get('content','')
    if provider=='brave':text+='\n'+'\n'.join(row.get('extra_snippets') or [])
    if not isinstance(text,str):raise ValueError('search_summary_type')
    item=p.normalize_source(row,provider,query)
    if item:
        item['snippet']=text[:4000]
        item['source_id']=provider[0].upper()+b.fingerprint(dict(url=item['url'],snippet=item['snippet']))[:12]
    return item


def prepare(run):
    if (PARENT/'orchestrator.lock').exists() or (DIAG/'orchestrator.lock').exists():raise ValueError('parent_still_running')
    if (run/'registration.json').exists():raise ValueError('already_prepared')
    p.freeze(PARENT,True)
    used=[b.Ledger(x).summary() for x in [PARENT,DIAG]]
    for d in ['evidence','results','score-results','cache','source','runtime','logs','tmp']:(run/d).mkdir(exist_ok=True)
    for name in ['companies.json','fact-questions.json','reference.json','score-questions.json','runtime-manifest.json','questions.json']:
        (run/name).write_bytes((PARENT/name).read_bytes())
    for name in b.RUNTIME_FILES:
        dst=run/'runtime'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((PARENT/'runtime'/name).read_bytes())
    for path in FILES:(run/'source'/Path(path).name).write_bytes((b.ROOT/path).read_bytes())
    b.write_json(run/'budget.json',dict(model_http_cap=p.CAPS['model']-sum(x['model_requests'] for x in used),
        search_http_cap=p.CAPS['search']-sum(x['search_requests'] for x in used),cash_usd_cap=p.CAPS['usd']-sum(x['charged_upper_usd'] for x in used)))
    b.write_json(run/'registration.json',dict(version='accuracy-followup/1',created_at=b.now(),parent_ledgers={str(x):p.sha(x/'attempts.jsonl') for x in [PARENT,DIAG]},
        parent_lock=p.sha(PARENT/'input-lock.json'),prior_usage=used,MCP_queries=QUERIES,
        MCP_expected_search_calls=9,MCP_protocol_calls=3,guided_search_calls=12,
        plan='MCP four models 12; enhanced selected two 6; independent repeats selected two 6; preferred model 1/3 question groups 24; score sufficiency 12 max',
        source_revisions={f:p.sha(b.ROOT/f) for f in FILES},production=False,temperature='omitted',thinking='enabled/adaptive',
        query_design='guided primary source targets separate from ordinary open search; no numeric reference answers in queries',
        evidence_summary_cap_chars=4000,score_calls=6,score_facts_are_stale=True))
    return dict(prepared=True,http=0)


def source_check(run):
    reg=p.read(run/'registration.json')
    if (PARENT/'orchestrator.lock').exists() or (DIAG/'orchestrator.lock').exists():raise ValueError('parent_running')
    if p.sha(PARENT/'input-lock.json')!=reg['parent_lock']:raise ValueError('parent_lock_drift')
    for name,sha in reg['parent_ledgers'].items():
        if p.sha(Path(name)/'attempts.jsonl')!=sha:raise ValueError('parent_ledger_drift')
    for name,sha in reg['source_revisions'].items():
        if p.sha(b.ROOT/name)!=sha or p.sha(run/'source'/Path(name).name)!=sha:raise ValueError('followup_source_drift')


def collect(run,module,ledger):
    source_check(run);session=module.http_client_manager.get_sync_session();key=b.read_key('ZAI_API_KEY')
    endpoint='https://api.z.ai/api/mcp/web_search_prime/mcp';headers={'Authorization':'Bearer '+key,'Accept':'application/json, text/event-stream','Content-Type':'application/json'}
    def post(body,method):
        qkey=b.fingerprint(body)
        if any(x.get('query_key')==qkey for x in ledger.reserved.values()):raise ValueError('MCP_already_sent_no_retry')
        aid=ledger.reserve('search',.03,dict(provider='zai_mcp',method=method,query_key=qkey))
        start=time.monotonic()
        try:r=session.post(endpoint,json=body,headers=headers,timeout=45,allow_redirects=False)
        except Exception as exc:
            ledger.finish(aid,dict(state='outcome_unknown',exception_type=type(exc).__name__));raise RuntimeError('MCP_unknown_stop') from None
        if r.status_code not in (200,202):
            body=z.decode(r);ledger.finish(aid,dict(state='http_rejected',http_status=r.status_code,**z.error_summary(body,key)));raise RuntimeError('MCP_rejected_stop')
        try:obj=z.decode(r) if r.status_code==200 else {}
        except (ValueError,TypeError):
            ledger.finish(aid,dict(state='invalid_envelope',http_status=r.status_code));raise ValueError('MCP_envelope_invalid_no_retry') from None
        if r.headers.get('Mcp-Session-Id'):headers['Mcp-Session-Id']=r.headers['Mcp-Session-Id']
        ledger.finish(aid,dict(state='completed',http_status=r.status_code,latency_s=round(time.monotonic()-start,3),is_search=method=='tools/call',actual_cash_usd=None))
        return obj
    obj=post(dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='iqs-accuracy-pilot',version='1'))),'initialize')
    headers['MCP-Protocol-Version']=obj['result']['protocolVersion']
    post(dict(jsonrpc='2.0',method='notifications/initialized'),'notifications/initialized')
    obj=post(dict(jsonrpc='2.0',id=2,method='tools/list'),'tools/list')
    if 'web_search_prime' not in [x['name'] for x in obj['result']['tools']]:raise ValueError('tool_unavailable')
    for slug,queries in QUERIES.items():
        items=[]
        for i,query in enumerate(queries):
            obj=post(dict(jsonrpc='2.0',id=100+list(QUERIES).index(slug)*3+i,method='tools/call',params=dict(name='web_search_prime',arguments=dict(search_query=query,search_recency_filter='noLimit',content_size='medium'))),'tools/call')
            result=obj.get('result') or {}
            if result.get('isError'):raise ValueError('MCP_tool_error_no_fabricated_results')
            for block in result.get('content',[]):
                value=block.get('text','')
                for _ in range(3):
                    if not isinstance(value,str):break
                    try:value=json.loads(value)
                    except ValueError:break
                if not isinstance(value,list):continue
                for row in value:
                    item=normalize(row,'zai',query)
                    if item and any((urlsplit(item['url']).hostname or '')==d or (urlsplit(item['url']).hostname or '').endswith('.'+d) for d in DOMAINS[slug]):
                        item['provider']='zai_mcp';items.append(item)
            print(json.dumps(dict(slug=slug,query_index=i,MCP_sources_so_far=len(items))),flush=True)
        b.write_json(run/'evidence'/(slug+'-mcp.json'),list({x['source_id']:x for x in items}.values()))
    # Equal-query targeted alternative: discovered reference URL supplies location,
    # never the gold numeric value. Clearly labelled guided retrieval.
    ref=p.read(run/'reference.json')
    for slug in ref['companies']:
        items=[]
        url=ref['companies'][slug][0]['source_url']
        special=ref['companies'][slug][4]['source_url']
        queries=[url+' '+('January June 2024 total revenue other income assets equity' if slug=='cncb_h' else '2024 H1 operating cash flow gross margin' if slug=='catl' else 'Year Ended December 31 2024 operating cash flow purchases property equipment')]
        queries.append(special+' '+('2024 1-5月 全球市占率' if slug=='catl' else '2024 total assets equity attributable holders' if slug=='cncb_h' else '2024 annual net cash provided operating activities capital expenditures'))
        for provider in ('brave','tavily'):
            key=b.read_key('BRAVE_API_KEY' if provider=='brave' else 'TAVILY_API_KEY')
            for query in queries:
                qkey=b.fingerprint(dict(provider=provider,query=query));checkpoint=run/'evidence'/('guided-'+qkey+'.json')
                if checkpoint.exists():items+=p.read(checkpoint)['items'];continue
                if any(x.get('query_key')==qkey for x in ledger.reserved.values()):raise ValueError('guided_already_sent_no_retry')
                aid=ledger.reserve('search',.03,dict(provider=provider,query_key=qkey,phase='guided'))
                try:
                    if provider=='brave':r=session.get('https://api.search.brave.com/res/v1/web/search',params=dict(q=query,count=4,extra_snippets=True),headers={'X-Subscription-Token':key},timeout=45,allow_redirects=False)
                    else:r=session.post('https://api.tavily.com/search',json=dict(api_key=key,query=query,search_depth='advanced',max_results=4,include_domains=DOMAINS[slug],include_raw_content=False,include_answer=False),timeout=45,allow_redirects=False)
                except Exception as exc:
                    ledger.finish(aid,dict(state='outcome_unknown',exception_type=type(exc).__name__));raise RuntimeError('guided_unknown_stop') from None
                if r.status_code!=200:
                    ledger.finish(aid,dict(state='http_rejected',http_status=r.status_code));raise ValueError('guided_rejection_stop')
                obj=r.json();rows=(obj.get('web') or {}).get('results',[]) if provider=='brave' else obj.get('results',[]);new=[]
                for row in rows:
                    item=normalize(row,provider,query)
                    if item and any((urlsplit(item['url']).hostname or '')==d or (urlsplit(item['url']).hostname or '').endswith('.'+d) for d in DOMAINS[slug]):new.append(item)
                b.write_json(checkpoint,dict(items=new));items+=new;ledger.finish(aid,dict(state='completed',http_status=200,credits=2 if provider=='tavily' else None,result_count=len(rows)))
        b.write_json(run/'evidence'/(slug+'-enhanced.json'),list({x['source_id']:x for x in items}.values()))
    return dict(budget=ledger.summary(),model_requests=0)


def freeze(run,check=False):
    source_check(run)
    names=['registration.json','budget.json','reference.json','fact-questions.json','score-questions.json','companies.json','runtime-manifest.json','coverage.json','selection.json']
    names += ['evidence/'+s+'-'+v+'.json' for s in QUERIES for v in ['mcp','enhanced']]
    names += ['source/'+Path(s).name for s in FILES]
    lock=dict(files={n:p.sha(run/n) for n in names},parent_lock=p.sha(PARENT/'input-lock.json'),
        fact_system_sha256=b.fingerprint(p.SYSTEM),score_system_sha256=b.fingerprint(SCORE_SYSTEM),routes_sha256=b.fingerprint(b.ROUTES))
    path=run/'input-lock.json'
    if path.exists():
        if p.read(path)!=lock:raise ValueError('followup_input_drift_zero_send')
    elif check:raise ValueError('not_frozen')
    else:b.write_json(path,lock)
    return b.fingerprint(lock)


def execute(run,module,ledger,stage):
    binding=freeze(run,True);selection=p.read(run/'selection.json');qs=p.read(run/'fact-questions.json');delegate=b.install_observer(module)
    if stage=='matrix':blocks=[(s,r,'mcp',qs[s],f'mcp.{s}.{r}') for s in qs for r in p.MODELS]+[(s,r,'enhanced',qs[s],f'enhanced.{s}.{r}') for s in qs for r in selection['routes']]
    elif stage=='repeat':blocks=[(s,r,'enhanced',qs[s],f'repeat.{s}.{r}') for s in qs for r in selection['routes']]
    else:blocks=[(s,selection['routes'][0],'enhanced',qs[s][i:i+g],f'pack.{s}.g{g}.i{i}') for s in qs for g in [1,3] for i in range(0,6,g)]
    old=p.freeze
    # Reuse original request/parser/cache/transport, supplying this independent
    # immutable follow-up binding. No change to parent sources or old results.
    p.freeze=lambda root,check=False:freeze(root,check)
    try:
        random.Random(2026100796).shuffle(blocks)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[]
            for block in blocks:
                result=run/'results'/(block[-1]+'.json')
                if result.exists():
                    if p.read(result)['run_fingerprint']!=binding:raise ValueError('existing_result_drift')
                    continue
                futures.append(pool.submit(p.request,run,module,delegate,ledger,*block))
            for future in as_completed(futures):print(json.dumps(future.result()),flush=True)
    finally:p.freeze=old
    return dict(stage=stage,budget=ledger.summary())


def score_request(run,module,delegate,ledger,slug,route,arm,warm=False):
    binding=freeze(run,True);company=p.read(run/'companies.json')[slug]
    qs=p.read(run/'score-questions.json');context=p.read(run/'evidence'/(slug+'-enhanced.json'))
    _,prompt=b.build_prompt(company,qs,context,'v5');params=p.policy(route)
    key=b.fingerprint(dict(system=SCORE_SYSTEM,prompt=prompt,parameters=params,route=b.ROUTES[route],parser='score-sufficiency/1',transport='explicit_only/2'))
    cache=b.AnswerCache(run/'cache')
    if warm:
        result=cache.get(key)
        if result is None:raise ValueError('warm_score_miss_zero_send')
        return result
    if any(r.get('arm')==arm for r in ledger.reserved.values()):raise ValueError('score_already_sent_no_resend')
    meta=dict(arm=arm,company=slug,entity_id=company['entity_id'],question_ids=[q['question_id'] for q in qs],variant='enhanced',
        evidence_sha256=b.fingerprint(context),questions_sha256=b.fingerprint(qs),run_fingerprint=binding,cache_key=key,
        prompt_sha256=b.fingerprint(dict(system=SCORE_SYSTEM,prompt=prompt)))
    observer=b.TransportObserver(delegate,ledger,route,meta,params);b._thread_context.observer=observer
    started=time.monotonic();result=dict(**meta,route=route,created_at=b.now(),state='failed',answers=[])
    try:
        cfg=b.ROUTES[route];client=module.LLMClient(b.read_key(cfg['key_env']),cfg['model'],cfg['endpoint'],timeout=180,provider_name=route)
        content=client.send_request(prompt,SCORE_SYSTEM)
        try:
            rows=b.parse_answers(content,meta['question_ids'],[x['source_id'] for x in context])
            if not observer.receipt or observer.receipt.get('finish_reason')!='stop' or observer.receipt.get('actual_model')!=cfg['model']:raise ValueError('score_receipt_invalid')
            result.update(state='valid',answers=rows)
        except (ValueError,TypeError) as exc:
            result.update(state='invalid_answer',parse_error=type(exc).__name__,final_content_sha256=b.fingerprint(content))
    except Exception as exc:result['exception_type']=type(exc).__name__
    finally:b._thread_context.observer=None
    result.update(receipt=observer.receipt,wall_s=round(time.monotonic()-started,3))
    b.write_json(run/'score-results'/(arm+'.json'),result)
    if result['state']=='valid' and cache.get(key) is None:cache.put(key,result)
    return dict(arm=arm,state=result['state'],wall_s=result['wall_s'])


def scores(run,module,ledger):
    freeze(run,True);delegate=b.install_observer(module);selection=p.read(run/'selection.json')
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(score_request,run,module,delegate,ledger,s,r,'score.'+s+'.'+r)
            for s in p.read(run/'companies.json') for r in selection['routes']
            if not (run/'score-results'/('score.'+s+'.'+r+'.json')).exists()]
        for future in as_completed(futures):print(json.dumps(future.result()),flush=True)
    return dict(stage='scores',budget=ledger.summary())


def warm(run,ledger):
    old_freeze=p.freeze;p.freeze=lambda root,check=False:freeze(root,check)
    try:out=p.warm(run,ledger)
    finally:p.freeze=old_freeze
    before=p.sha(run/'attempts.jsonl');old_key=b.read_key;b.read_key=lambda _:(_ for _ in ()).throw(AssertionError('warm_key_read'))
    count=0
    try:
        for path in (run/'score-results').glob('*.json'):
            result=p.read(path)
            if result['state']=='valid':score_request(run,None,None,ledger,result['company'],result['route'],result['arm'],True);count+=1
    finally:b.read_key=old_key
    if before!=p.sha(run/'attempts.jsonl'):raise AssertionError('warm_ledger_changed')
    out['score_cache_hits']=count;b.write_json(run/'warm-proof.json',out);return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','search','freeze','matrix','repeat','packing','scores','warm','summary']);ap.add_argument('--run',required=True);args=ap.parse_args()
    run=Path(args.run).resolve()
    if not run.is_relative_to(b.ROOT/'runs') or not run.name.startswith('accuracy-pilot-followup-'):raise ValueError('unowned_root')
    run.mkdir(exist_ok=True);(run/'tmp').mkdir(exist_ok=True)
    for k in ['TEMP','TMP','TMPDIR']:os.environ[k]=str(run/'tmp')
    tempfile.tempdir=str(run/'tmp');sys.dont_write_bytecode=True
    lock=run/'orchestrator.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode())
    try:
        if args.action=='prepare':out=prepare(run)
        elif args.action=='freeze':out={'fingerprint':freeze(run),'http':0}
        else:
            budget=p.read(run/'budget.json');ledger=b.Ledger(run,budget['model_http_cap'],budget['search_http_cap'],budget['cash_usd_cap'])
            if args.action=='summary':out=p.summarize(run,ledger)
            elif args.action=='warm':out=warm(run,ledger)
            else:
                p.guard(run);module=b.load_runtime(run)
                out=collect(run,module,ledger) if args.action=='search' else scores(run,module,ledger) if args.action=='scores' else execute(run,module,ledger,args.action)
        print(json.dumps(out,ensure_ascii=False),flush=True)
    finally:os.close(fd);lock.unlink()


if __name__=='__main__':main()
