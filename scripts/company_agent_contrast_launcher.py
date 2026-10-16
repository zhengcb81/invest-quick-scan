"""Frozen T2 launcher. No HTTP client, budget reset, seal or pricing ledger.

The coordinator first freezes all sources and inputs, writes a registration using
prepare_registration, then supplies its RAW SHA256 to every CLI invocation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

PROTOCOL = 'iqs.real-contrast-registration/1.1.0'
LEGACY_PROTOCOL = 'iqs.real-contrast-registration/1.0.0'
SDK_OPTIONS = {'tool_argument_validation':'controller'}
LIMITS = {'max_sdk_steps':24, 'max_output_tokens':16384,
          'session_input_tokens':2000000, 'session_output_tokens':192000,
          'wall_seconds':1800}
PROVIDERS = {
    'deepseek-flash': {'provider':'deepseek', 'model':'deepseek-flash',
        'endpoint':'https://api.deepseek.com/chat/completions', 'key_env':'DEEPSEEK_API_KEY'},
    'mimo-pro': {'provider':'mimo', 'model':'mimo-v2.6-pro',
        'endpoint':'https://api.xiaomimimo.com/v1/chat/completions', 'key_env':'MIMO_API_KEY'},
}
REQUIRED_MODULES = ('company_agent_contrast', 'company_agent_research_pilot',
    'standard_answers', 'iqs_answer_codec', 'iqs_session_packing', 'iqs_claim_guard',
    'iqs_company_agent_lab', 'iqs_agent_evaluation_lab',
    'src.providers.llm_client', 'src.providers.llm_research_client',
    'src.utils.quick_scan_work_store', 'src.utils.quick_scan_work_transport')

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)

def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))

def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())

def confined(root, value):
    if not isinstance(value, str) or '\\' in value:
        raise ValueError('nonportable_input_path')
    part = PurePosixPath(value)
    if part.is_absolute() or not part.parts or any(x in ('.','..') for x in part.parts) or ':' in value:
        raise ValueError('unsafe_input_path')
    target = (root/value).resolve()
    if not target.is_relative_to(root.resolve()): raise ValueError('input_escape')
    return target

def verify_files(root, files):
    seen = set()
    for item in files:
        if set(item) != {'path','bytes','raw_sha256'}: raise ValueError('invalid_input_ref')
        key = item['path'].casefold()
        if key in seen: raise ValueError('duplicate_input_path')
        seen.add(key)
        path = confined(root, item['path'])
        if not path.is_file() or path.stat().st_size != item['bytes'] or raw_sha(path) != item['raw_sha256']:
            raise ValueError('frozen_input_changed')
    return seen

def activate_sources(root, registration):
    """No imports until every frozen byte is checked; refuse foreign cached modules."""
    locked = {x['path'].casefold() for x in registration['files']}
    bindings = registration['module_bindings']
    if set(bindings) != set(REQUIRED_MODULES): raise ValueError('missing_module_binding')
    for name, relative in bindings.items():
        if relative.casefold() not in locked: raise ValueError('module_not_frozen')
        path = confined(root, relative)
        old = sys.modules.get(name)
        if old is not None and Path(old.__file__).resolve() != path:
            raise ValueError('foreign_cached_module')
    for relative in reversed(registration['python_paths']):
        path = confined(root, relative)
        if not path.is_dir(): raise ValueError('missing_python_path')
        sys.path.insert(0, str(path))
    # Prefix composition needs the first five packages; native SDK imports wait
    # until the explicit live invocation and existing-store check.
    return importlib.import_module('company_agent_contrast')

def assert_imports(root, registration):
    for name, relative in registration['module_bindings'].items():
        module = importlib.import_module(name)
        if Path(module.__file__).resolve() != confined(root, relative):
            raise ValueError('import_origin_mismatch')

def cohort(experiment_id, phase):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', experiment_id): raise ValueError('invalid_experiment_id')
    # Reverse provider/packing order in repeat two to limit order confounding.
    result = []
    for repeat in (1,2):
        models = list(PROVIDERS) if repeat == 1 else list(reversed(PROVIDERS))
        strategies = ['single','pack3','company_agent'] if repeat == 1 else ['company_agent','pack3','single']
        for strategy in strategies:
            for model in models:
                result.append({'case_id':f'{experiment_id}-{model}-{strategy}-r{repeat}',
                    'model_id':model, 'strategy_id':strategy, 'repeat':repeat, 'phase':phase})
    return result

def scope_for(registration, case):
    scope = {'experiment_id':registration['experiment_id'], 'case':case,
        'company_key':registration['company_key'], 'cutoff':registration['cutoff'],
        'question_sha256':registration['question_sha256'], 'board_sha256':registration['board_sha256'],
        'prefix_sha256':registration['prefix_sha256'], 'tools_sha256':registration['tools_sha256'],
        'limits':registration['limits'], 'pricing_sha256':registration['pricing_sha256'],
        'policy_sha256':registration['policy_sha256'], 'input_files_sha256':sha(registration['files']),
        'route_id':registration['route_ids'][case['model_id']],
        'module_bindings_sha256':sha(registration['module_bindings']),
        'python_paths_sha256':sha(registration['python_paths']),
        'native_budget_store':registration['native_budget_store']}
    if registration.get('protocol') == PROTOCOL:scope['sdk_options']=registration['sdk_options']
    return scope

def prepare_registration(root, settings):
    """Settings point ONLY to already frozen files; this function does not copy inputs."""
    root = Path(root).resolve()
    result = dict(settings)
    result.update(protocol=PROTOCOL, sdk_options=dict(SDK_OPTIONS), limits=dict(LIMITS), providers=PROVIDERS,
                  cases=cohort(settings['experiment_id'],settings['phase']))
    verify_files(root, result['files'])
    controller = activate_sources(root,result)
    data = {key:load(confined(root,path)) for key,path in result['documents'].items()}
    result.update(company_key=data['board']['company_key'], cutoff=data['board']['cutoff'],
        question_sha256=sha(data['questions']), board_sha256=sha(data['board']),
        prefix_sha256=sha(controller.prefix_text(data['questions'],data['board'],data['answer_schema'],data['metrics'],data['identity'])),
        tools_sha256=sha(controller.compile_tools()), pricing_sha256=raw_sha(confined(root,result['pricing_module'])),
        policy_sha256=sha(data['policy']))
    for case in result['cases']:
        case['independent_task']={'task_id':case['case_id'], 'task_sha256':sha(scope_for(result,case))}
    return result

def preflight(root, registration_path, expected_sha):
    root = Path(root).resolve()
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha) or raw_sha(registration_path) != expected_sha:
        raise ValueError('registration_hash_mismatch')
    r = load(registration_path)
    if r.get('protocol') not in {PROTOCOL,LEGACY_PROTOCOL} or r.get('limits') != LIMITS or r.get('providers') != PROVIDERS:
        raise ValueError('unsupported_registered_protocol')
    if ((r['protocol']==PROTOCOL and r.get('sdk_options')!=SDK_OPTIONS) or (r['protocol']==LEGACY_PROTOCOL and 'sdk_options' in r)):
        raise ValueError('unsupported_registered_sdk_options')
    verify_files(root,r['files'])
    required = {'questions','board','answer_schema','metrics','identity','policy'}
    if set(r['documents']) != required: raise ValueError('invalid_documents')
    locked = {x['path'].casefold() for x in r['files']}
    for path in list(r['documents'].values())+[r['pricing_module']]:
        if path.casefold() not in locked: raise ValueError('document_not_frozen')
    docs = {key:load(confined(root,path)) for key,path in r['documents'].items()}
    controller = activate_sources(root,r)
    if len(docs['questions']) != 12 or len({q['id'] for q in docs['questions']}) != 12:
        raise ValueError('registered_twelve_questions_required')
    expected = cohort(r['experiment_id'],r['phase'])
    clean_cases=[]
    for case in r['cases']:
        clean={k:v for k,v in case.items() if k!='independent_task'}
        if case.get('independent_task') != {'task_id':case['case_id'], 'task_sha256':sha(scope_for(r,clean))}:
            raise ValueError('task_scope_changed')
        clean_cases.append(clean)
    if clean_cases != expected: raise ValueError('cohort_changed')
    if (r['company_key'] != docs['board']['company_key'] or r['cutoff'] != docs['board']['cutoff']
        or r['question_sha256'] != sha(docs['questions']) or r['board_sha256'] != sha(docs['board'])
        or r['prefix_sha256'] != sha(controller.prefix_text(docs['questions'],docs['board'],docs['answer_schema'],docs['metrics'],docs['identity']))
        or r['tools_sha256'] != sha(controller.compile_tools()) or r['pricing_sha256'] != raw_sha(confined(root,r['pricing_module']))
        or r['policy_sha256'] != sha(docs['policy'])):
        raise ValueError('registered_context_changed')
    policy=docs['policy']
    if policy['policy_id'] != r['expected_policy_id']: raise ValueError('policy_owner_changed')
    for model_id, route_id in r['route_ids'].items():
        if model_id not in PROVIDERS: raise ValueError('unsupported_model_route')
        matches=[x for x in policy['routes'] if x['id']==route_id and x['eligible'] is True]
        if len(matches)!=1 or matches[0]['model'] != PROVIDERS[model_id]['model'] or matches[0]['provider_config_ref'] != PROVIDERS[model_id]['provider']:
            raise ValueError('policy_model_route_not_admitted')
    if set(r['route_ids']) != set(PROVIDERS): raise ValueError('missing_model_route')
    return r,docs,controller

def budget_ready(status):
    # Seals are original native audited facts; never subtract unknowns ourselves.
    return (status.get('effective_in_flight') == 0 and status.get('blocking_unreconciled_attempts') == 0
        and status['requests'] < status['max_requests']
        and status['spent_micros']+status['reserved_micros'] < status['max_cost_micros'])

def run_case(root, registration_path, expected_sha, case_id):
    root = Path(root).resolve()
    r,docs,controller = preflight(root,registration_path,expected_sha)
    selected = [x for x in r['cases'] if x['case_id']==case_id]
    if len(selected)!=1: raise ValueError('unregistered_case')
    case=selected[0]; model=PROVIDERS[case['model_id']]
    key=os.environ.get(model['key_env'])
    if not isinstance(key,str) or not key.strip(): raise ValueError('credential_unavailable_no_request_sent')
    native=Path(r['native_budget_store'])
    if not native.is_absolute() or not native.is_file():
        raise ValueError('existing_native_store_required')
    with native.open('rb') as stream:
        if stream.read(16) != b'SQLite format 3\x00': raise ValueError('existing_native_store_required')
    assert_imports(root,r)
    from src.providers.llm_client import LLMClient
    from src.providers.llm_research_client import ResearchChatSession
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    from src.utils.quick_scan_work_transport import bind_quick_scan_budget,bind_quick_scan_route
    from src.utils.http_client import http_client_manager
    policy=docs['policy']; store=QuickScanWorkStore(native)
    status=lambda:store.get_quick_scan_budget_status(policy['policy_id'],include_isolation=True)
    if not budget_ready(status()): raise ValueError('native_budget_not_ready')
    output_root=Path(r['output_root'])
    if not output_root.is_absolute() or not output_root.is_dir(): raise ValueError('existing_output_root_required')
    claim=output_root/(case_id+'.claim.json')
    output=output_root/case_id
    if output.exists(): raise ValueError('case_output_exists_no_retry')
    write_new(claim,{'protocol':'iqs.real-contrast-case-claim/1.0.0', 'registration_raw_sha256':expected_sha,
        'case':case, 'started_at':datetime.now(timezone.utc).isoformat(), 'pid':os.getpid(),
        'credential_present':True, 'budget_before':status(), 'automatic_retry':False})
    spec=importlib.util.spec_from_file_location('frozen_t2_native_price',confined(root,r['pricing_module']))
    pricing=importlib.util.module_from_spec(spec);spec.loader.exec_module(pricing)
    current=[None]
    def before_step():
        current[0]=pricing.CohortPriceResolver(provider=model['provider'],model=model['model'],
            pricing_ref=policy['cost_policy']['pricing_ref'],window_start=datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    def resolver(receipt):
        return current[0](receipt) if current[0] is not None else None
    route=next(x for x in policy['routes'] if x['id']==r['route_ids'][case['model_id']])
    try:
        client=LLMClient(key,model['model'],model['endpoint'],provider_name=model['provider'],timeout=180)
        def factory(**kwargs): return ResearchChatSession(client,**r.get('sdk_options',{}),**kwargs)
        with bind_quick_scan_budget(store,policy,cost_resolver=resolver,independent_task=case['independent_task']),bind_quick_scan_route(
            route_id=route['id'],provider=model['provider'],model_requested=model['model'],quota_group=route['quota_group']):
            return controller.execute_case(case=case,questions=docs['questions'],board=docs['board'],
                answer_schema=docs['answer_schema'],metrics=docs['metrics'],identity=docs['identity'],
                limits=r['limits'],session_factory=factory,inputs_root=root,output=output,
                check_budget=lambda:budget_ready(status()),before_step=before_step)
    finally:
        http_client_manager.close_all()
        write_new(output_root/(case_id+'.terminal.json'),{'case_id':case_id,'budget_after':status(),
            'completed_at':datetime.now(timezone.utc).isoformat(), 'financial_accuracy':None, 'cash_invoice_usd':None})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--live-case');args=parser.parse_args()
    if args.live_case:
        result=run_case(args.inputs,args.registration,args.registration_sha256,args.live_case)
        print(canonical({k:result[k] for k in ('session_ref','terminal','sdk_step_invocations','unanswered_question_ids')}))
    else:
        r,_,_=preflight(args.inputs,args.registration,args.registration_sha256)
        print(canonical({'status':'preflight_valid','planned_cases':len(r['cases']),'planned_slots':len(r['cases'])*12,
            'model_http':0,'search_http':0,'credentials_present':{k:bool(os.environ.get(v['key_env'])) for k,v in PROVIDERS.items()}}))

if __name__=='__main__':
    try: main()
    except Exception as error:
        # Raw exceptions can contain provider text or credentials. Never print.
        print(canonical({'status':'stopped','error_type':type(error).__name__}),file=sys.stderr)
        raise SystemExit(2)
