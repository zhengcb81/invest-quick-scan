import json, os
from pathlib import Path
from pytest import MonkeyPatch
from src.providers.external_search_provider import ExternalSearchProvider
from src.utils.quick_scan_external_context import build_external_question_context
from tests.unit.test_quick_scan_external_context import _external_answer_fixture, _created, _send_external_answer
root=Path(os.environ['E97_OWNED_ROOT'])
parser=ExternalSearchProvider.__new__(ExternalSearchProvider)
parser.retrieval={'max_json_unwrap_layers':3,'max_in_memory_response_bytes':1000000}
stage={'stage':'initialize','message':{'id':'review-init'}}
accepted=[]
for value in [None, {'name':17,'version':None}, {'name':'synthetic','version':'1'}]:
    result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}}}
    if value is not None: result['serverInfo']=value
    doc={'jsonrpc':'2.0','id':'review-init','result':result}
    try:
        control=parser._parse_mcp_control(stage,json.dumps(doc).encode(),None,{},200,None)
        accepted.append({'serverInfo':value,'accepted':True,'control':control})
    except Exception as e:
        accepted.append({'serverInfo':value,'accepted':False,'error_type':type(e).__name__})
mp=MonkeyPatch()
case=root/'generation'
case.mkdir()
try:
    args, context, search, sync, _, model, url, _, clock = _external_answer_fixture(case,mp)
    old=args['store'].get_item(args['work_item_id'])
    fresh=_created(args['store'],generation=2)
    args.update(work_item_id=fresh['work_item_id'],lease=args['store'].claim(fresh['work_item_id'],lease_seconds=60))
    rebuilt=build_external_question_context(args['store'],args['work_item_id'],args['lease'],args['policy'],[ref['operation_id'] for ref in context['retrievals']],question_manifest_sha256=args['question_manifest_sha256'])
    answer=_send_external_answer(args,rebuilt,model,url)
    attempt=args['store'].list_attempts(args['work_item_id'])[-1]
    proof=args['store'].get_external_context_use(attempt['attempt_id'])['proof']
    info={'original_generation':old['generation'],'current_generation':fresh['generation'],'old_operation_used':proof['retrievals'][0]['operation_id']==context['retrievals'][0]['operation_id'],'new_work_bound':proof['work_item_id']==fresh['work_item_id'],'search_http_count':search.request.call_count,'model_http_count':sync.post.call_count,'proof_present':proof is not None}
finally:
    mp.undo()
print(json.dumps({'initialize':accepted,'generation':info,'real_network':False,'synthetic_only':True},ensure_ascii=False))
