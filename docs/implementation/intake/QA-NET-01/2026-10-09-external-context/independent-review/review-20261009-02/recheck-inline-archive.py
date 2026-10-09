import json,os
from pathlib import Path
from pytest import MonkeyPatch
from src.providers.external_search_provider import ExternalSearchProvider
from src.utils.quick_scan_external_context import build_external_question_context,ExternalRetrievalBlocked
from src.utils.quick_scan_work_store import QuickScanWorkStore,LeaseFencedError
from tests.unit.test_quick_scan_external_context import _external_answer_fixture,_created,_send_external_answer,_retrieve
from tests.unit.test_quick_scan_mcp import _mcp_fixture,_mcp_replies,_mcp_response
root=Path(os.environ['E97_OWNED_ROOT'])
results={'initialize':[],'generation':[],'synthetic_only':True,'real_network':False}
# Exact original unsafe parser boundary now rejects all six mandatory-field defects.
parser=ExternalSearchProvider.__new__(ExternalSearchProvider)
parser.retrieval={'max_json_unwrap_layers':3,'max_in_memory_response_bytes':1000000}
stage={'stage':'initialize','message':{'id':'review-init'}}
for defect in ['missing','non_object','missing_name','name_type','missing_version','version_type','valid']:
    info={'name':'synthetic','version':'1'}
    if defect=='missing_name': info.pop('name')
    elif defect=='name_type': info['name']=17
    elif defect=='missing_version': info.pop('version')
    elif defect=='version_type': info['version']=None
    result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}}}
    if defect!='missing': result['serverInfo']=[] if defect=='non_object' else info
    payload={'jsonrpc':'2.0','id':'review-init','result':result}
    try: control=parser._parse_mcp_control(stage,json.dumps(payload).encode(),None,{},200,None)
    except ValueError:
        assert defect!='valid'; accepted=False
    else:
        assert defect=='valid'; assert control=={'protocol_version':'2025-03-26','session_id':None}; accepted=True
    results['initialize'].append({'defect':defect,'accepted':accepted})
# Drive the ordinary paid MCP entry and reopen for every invalid InitializeResult.
results['mcp_runtime']=[]
for defect in ['missing','non_object','missing_name','name_type','missing_version','version_type']:
    case=root/('mcp-'+defect); case.mkdir(); mp=MonkeyPatch()
    try:
        args,_,session,clock=_mcp_fixture(case,mp); ordinary=_mcp_replies()
        def reply(method,endpoint,**kwargs):
            message=kwargs['json']
            if message['method']!='initialize': return ordinary(method,endpoint,**kwargs)
            info={'name':'synthetic','version':'1'}
            if defect=='missing_name': info.pop('name')
            elif defect=='name_type': info['name']=17
            elif defect=='missing_version': info.pop('version')
            elif defect=='version_type': info['version']=None
            result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}}}
            if defect!='missing': result['serverInfo']=[] if defect=='non_object' else info
            return _mcp_response({'jsonrpc':'2.0','id':message['id'],'result':result})
        session.request.side_effect=reply
        for cycle in range(2):
            if cycle: args['store']=QuickScanWorkStore(args['store'].path,clock=lambda:clock[0])
            try: _retrieve(args)
            except ExternalRetrievalBlocked as exc: assert str(exc)=='mcp_control_unusable'
            else: raise AssertionError('invalid initialize advanced to paid search')
            totals=args['store'].get_quick_scan_budget_status('q09-fixture')
            assert totals['requests']==1 and totals['spent_micros']==3000 and totals['reserved_micros']==0
            assert session.request.call_count==1 and args['store'].list_attempts(args['work_item_id'])==[]
            if not cycle: original_totals=totals
            else: assert totals==original_totals
        results['mcp_runtime'].append({'defect':defect,'http_count':session.request.call_count,'spent_micros':totals['spent_micros'],'warm_resends':0})
    finally: mp.undo()
# Both direct build and actual LLM binding must reject generation 1 evidence at generation 2.
for entry in ['context','actual_send']:
    case=root/('generation-'+entry);case.mkdir();mp=MonkeyPatch()
    try:
        args,context,search,sync,_,model,url,_,clock=_external_answer_fixture(case,mp)
        old=args['store'].get_item(args['work_item_id']);fresh=_created(args['store'],generation=2)
        args.update(work_item_id=fresh['work_item_id'],lease=args['store'].claim(fresh['work_item_id'],lease_seconds=60))
        totals=args['store'].get_quick_scan_budget_status('q09-fixture')
        try:
            if entry=='context': build_external_question_context(args['store'],args['work_item_id'],args['lease'],args['policy'],[ref['operation_id'] for ref in context['retrievals']],question_manifest_sha256=args['question_manifest_sha256'])
            else: _send_external_answer(args,context,model,url)
        except ValueError as exc: assert 'binding' in str(exc)
        else: raise AssertionError('generation boundary accepted stale evidence')
        assert old['generation']==1 and fresh['generation']==2
        assert search.request.call_count==1 and sync.post.call_count==0
        assert args['store'].list_attempts(args['work_item_id'])==[]
        assert args['store'].get_quick_scan_budget_status('q09-fixture')==totals
        results['generation'].append({'entry':entry,'rejected':True,'model_http_count':sync.post.call_count,'budget_unchanged':True})
    finally:mp.undo()
# The generation check must preserve lawful paid evidence recovery under a fresh lease.
case=root/'same-generation-new-lease';case.mkdir();mp=MonkeyPatch()
try:
    args,context,search,sync,_,model,url,_,clock=_external_answer_fixture(case,mp)
    old_args=dict(args);old_lease=args['lease'];clock[0]+=61
    store=QuickScanWorkStore(args['store'].path,clock=lambda:clock[0]);assert store.recover_expired(args['work_item_id'])=='pending'
    lease=store.claim(args['work_item_id'],lease_seconds=60);assert lease.lease_epoch==old_lease.lease_epoch+1
    try:_send_external_answer(old_args,context,model,url)
    except LeaseFencedError:pass
    else:raise AssertionError('old lease sent model HTTP')
    args.update(store=store,lease=lease);mp.delenv('IQS_SYNTHETIC_SEARCH_TOKEN')
    rebuilt=_retrieve(args);assert rebuilt==context
    answer=_send_external_answer(args,rebuilt,model,url)
    attempt=store.list_attempts(args['work_item_id'])[-1];proof=store.get_external_context_use(attempt['attempt_id'])['proof']
    assert proof is not None and attempt['lease_epoch']==lease.lease_epoch
    assert search.request.call_count==1 and sync.post.call_count==1
    results['same_generation_recovery']={'search_http_count':1,'model_http_count':1,'old_lease_fenced':True,'new_lease_proof':True,'retrieval_unchanged':True}
finally:mp.undo()
# Persistence-side binding is independently exercised with the legal fresh generation and rehashed old references.
from tests.unit.test_quick_scan_external_context import test_external_use_rehashed_previous_generation_reference_is_rejected_by_owner
case=root/'persisted-generation';case.mkdir();mp=MonkeyPatch()
try:test_external_use_rehashed_previous_generation_reference_is_rejected_by_owner(case,mp);results['persisted_generation']={'fresh_generation_answer_valid':True,'rehashed_old_retrieval_rejected':True,'budget_unchanged_after_read':True}
finally:mp.undo()
assert not (root/'network-attempts.jsonl').exists()
results['guard_network_attempts']=0
print(json.dumps(results,ensure_ascii=False))
