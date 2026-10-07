"""Bounded REST versus MCP diagnostic using existing frozen StockQA HTTP pool.

Explicit diagnostic only, never a dispatcher retry or production MCP client.
No secret/session headers or raw provider body are persisted. One REST query and
one MCP query, at most five HTTP requests; stateful MCP headers remain ephemeral.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
import accuracy_pilot as p
import batching_benchmark as b


def decode(response):
    try:return response.json()
    except ValueError:
        data=[line[5:].strip() for line in response.text.splitlines() if line.startswith('data:')]
        if len(data)!=1:raise ValueError('unexpected_mcp_sse_envelope')
        return json.loads(data[0])


def error_summary(body,key):
    err=body.get('error',body) if isinstance(body,dict) else {}
    if not isinstance(err,dict):return {}
    out={}
    code=err.get('code')
    if type(code) in (str,int):out['error_code']=str(code)[:50]
    text=err.get('message') or err.get('msg')
    if isinstance(text,str):out['error_message']=text.replace(key,'[REDACTED]')[:240]
    return out


def main():
    root=b.ROOT/'runs/accuracy-pilot-zai-diagnostic-2026-10-07-01'
    if root.exists():raise ValueError('diagnostic_run_exists_do_not_resend')
    root.mkdir();(root/'tmp').mkdir();(root/'logs').mkdir();(root/'runtime').mkdir()
    parent=b.ROOT/'runs/accuracy-pilot-2026-10-07-01'
    (root/'runtime-manifest.json').write_bytes((parent/'runtime-manifest.json').read_bytes())
    for name in b.RUNTIME_FILES:
        dst=root/'runtime'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((parent/'runtime'/name).read_bytes())
    for n in ('TEMP','TMP','TMPDIR'):os.environ[n]=str(root/'tmp')
    tempfile.tempdir=str(root/'tmp');sys.dont_write_bytecode=True
    lock=root/'orchestrator.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode())
    try:
        p.guard(root);module=b.load_runtime(root);session=module.http_client_manager.get_sync_session();key=b.read_key('ZAI_API_KEY')
        ledger=b.Ledger(root,0,5,1);steps=[]
        def post(endpoint,body,headers,method,kind):
            aid=ledger.reserve('search',.03,dict(provider='zai_'+kind,method=method,request_body_sha256=b.fingerprint(body)))
            started=time.monotonic()
            try:r=session.post(endpoint,json=body,headers=headers,timeout=45,allow_redirects=False)
            except Exception as exc:
                ledger.finish(aid,dict(state='outcome_unknown',exception_type=type(exc).__name__))
                raise RuntimeError('unknown_diagnostic_stop') from None
            item=dict(method=method,interface=kind,http_status=r.status_code,latency_s=round(time.monotonic()-started,3))
            try:value=decode(r) if r.status_code!=202 else {}
            except (ValueError,TypeError):value={};item['body_unparseable']=True
            item.update(error_summary(value,key));ledger.finish(aid,dict(**item,state='completed' if 200<=r.status_code<300 else 'http_rejected'))
            steps.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
            return r,value,item
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
        query='Microsoft investor relations annual report 2025 revenue'
        rest='https://api.z.ai/api/paas/v4/web_search'
        r,data,item=post(rest,dict(search_engine='search-prime',search_query=query,count=3),headers,'web_search','rest')
        if r.status_code==200:
            rows=data.get('search_result',data.get('web_search',[]));item['returned_count']=len(rows)
        mcp='https://api.z.ai/api/mcp/web_search_prime/mcp';headers={**headers,'Accept':'application/json, text/event-stream'}
        r,data,item=post(mcp,dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='iqs-bounded-diagnostic',version='1.0'))),headers,'initialize','mcp')
        if r.status_code==200 and 'result' in data:
            token=r.headers.get('Mcp-Session-Id')
            if token:headers['Mcp-Session-Id']=token
            headers['MCP-Protocol-Version']=data['result'].get('protocolVersion','2024-11-05')
            post(mcp,dict(jsonrpc='2.0',method='notifications/initialized'),headers,'notifications/initialized','mcp')
            r,data,item=post(mcp,dict(jsonrpc='2.0',id=2,method='tools/list'),headers,'tools/list','mcp')
            tools=(data.get('result') or {}).get('tools',[])
            names=[x.get('name') for x in tools if isinstance(x,dict)];item['tool_names']=names
            if 'web_search_prime' in names:
                r,data,item=post(mcp,dict(jsonrpc='2.0',id=3,method='tools/call',params=dict(name='web_search_prime',arguments=dict(search_query=query,search_recency_filter='noLimit',content_size='medium'))),headers,'tools/call','mcp')
                value=data.get('result') or {};item['tool_is_error']=value.get('isError');rows=[]
                for content in value.get('content',[]):
                    text=content.get('text') if isinstance(content,dict) else None
                    if not isinstance(text,str):continue
                    decoded=text
                    for _ in range(3):
                        if not isinstance(decoded,str):break
                        try:decoded=json.loads(decoded)
                        except ValueError:break
                    if isinstance(decoded,list):rows.extend(decoded)
                    elif isinstance(decoded,dict):item.update(error_summary(decoded,key))
                    elif value.get('isError'):item['tool_error_message']=text.replace(key,'[REDACTED]')[:240]
                item['returned_count']=len(rows)
                item['results_sample']=[dict(title=x.get('title'),url=x.get('link'),has_summary=bool(x.get('content'))) for x in rows[:2] if isinstance(x,dict)]
        out=dict(observed_at=b.now(),credential_env='ZAI_API_KEY',same_credential_for_both=True,steps=steps,
            budget=ledger.summary(),search_calls=sum(x['method'] in ('web_search','tools/call') for x in steps),
            raw_response_persisted=False,session_headers_persisted=False,retries=0,production_enabled=False)
        b.write_json(root/'diagnostic.json',out);print(json.dumps(out,ensure_ascii=False),flush=True)
    finally:os.close(fd);lock.unlink()


if __name__=='__main__':main()
