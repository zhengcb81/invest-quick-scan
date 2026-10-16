"""Keyless synthetic fixtures; no production DB and no provider requests."""
import copy
import json
import socket
import sys
from contextlib import contextmanager
from types import ModuleType
from types import SimpleNamespace

import pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import company_agent_contrast_launcher as launch

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args,**kwargs): raise AssertionError('network_forbidden')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(socket,'getaddrinfo',deny)

@pytest.fixture
def frozen(tmp_path,monkeypatch):
    root=tmp_path/'inputs';root.mkdir();out=tmp_path/'output';out.mkdir()
    stub=SimpleNamespace(prefix_text=lambda *args: launch.canonical(args),compile_tools=lambda:[{'name':'fixture'}])
    monkeypatch.setattr(launch,'activate_sources',lambda *args:stub)
    policy={'policy_id':'existing-policy','policy_version':'v2','cost_policy':{'pricing_ref':'frozen-official'},
        'routes':[{'id':key,'eligible':True,'provider_config_ref':item['provider'],
                   'model':item['model'],'quota_group':key+'-quota'} for key,item in launch.PROVIDERS.items()]}
    docs={'questions':[{'id':f'Q{i}'} for i in range(12)],'board':{'company_key':'alphabet','cutoff':'2026-10-13'},
          'answer_schema':{},'metrics':{},'identity':{'entity_id':'fixture-only'},'policy':policy}
    documents={}
    for name,value in docs.items():
        documents[name]=name+'.json';launch.write_new(root/documents[name],value)
    (root/'pricing.py').write_text('# no executable price fixture needed for preflight\n')
    (root/'controller.py').write_text('# fixture, never provider transport\n')
    native=tmp_path/'existing-fixture.sqlite';native.write_bytes(b'SQLite format 3\x00'+b'fixture_not_real_sqlite')
    settings={'experiment_id':'t2-fixture','phase':'fixed-board-t2','files':[],
        'documents':documents,'python_paths':['fixture-src'],
        'module_bindings':{name:'controller.py' for name in launch.REQUIRED_MODULES},
        'pricing_module':'pricing.py','native_budget_store':str(native),'output_root':str(out),
        'expected_policy_id':'existing-policy','route_ids':{key:key for key in launch.PROVIDERS}}
    settings['files']=[{'path':p.name,'bytes':p.stat().st_size,'raw_sha256':launch.raw_sha(p)} for p in sorted(root.iterdir())]
    r=launch.prepare_registration(root,settings);rp=tmp_path/'registration.json';launch.write_new(rp,r)
    return SimpleNamespace(root=root,out=out,native=native,r=r,rp=rp,stub=stub,docs=docs,
                           expected=launch.raw_sha(rp))

def rewrite(frozen):
    frozen.rp.write_text(json.dumps(frozen.r,ensure_ascii=False),encoding='utf-8')
    frozen.expected=launch.raw_sha(frozen.rp)

def test_full_grid_and_task_identity(frozen):
    r,_,_=launch.preflight(frozen.root,frozen.rp,frozen.expected)
    assert len(r['cases'])==12
    assert len({c['independent_task']['task_sha256'] for c in r['cases']})==12
    assert r['cases'][0]['strategy_id']=='single' and r['cases'][6]['strategy_id']=='company_agent'
    assert r['cases'][0]['model_id'] != r['cases'][6]['model_id']
    assert r['limits']==launch.LIMITS

def test_changed_frozen_bytes_refused(frozen):
    (frozen.root/'board.json').write_text('{}')
    with pytest.raises(ValueError,match='frozen_input_changed'):
        launch.preflight(frozen.root,frozen.rp,frozen.expected)

def test_registration_hash_then_task_scope_refused(frozen):
    with pytest.raises(ValueError,match='registration_hash'):
        launch.preflight(frozen.root,frozen.rp,'0'*64)
    frozen.r['cases'][0]['independent_task']['task_sha256']='0'*64;rewrite(frozen)
    with pytest.raises(ValueError,match='task_scope_changed'):
        launch.preflight(frozen.root,frozen.rp,frozen.expected)

def test_escape_and_duplicate_path_refused(frozen):
    for path in ['../pricing.py','C:/secret.py','/secret.py','a\\b.py']:
        with pytest.raises(ValueError):launch.confined(frozen.root,path)
    with pytest.raises(ValueError,match='duplicate_input_path'):
        launch.verify_files(frozen.root,[frozen.r['files'][0]]*2)

def test_missing_key_no_claim_no_native_import(frozen,monkeypatch):
    monkeypatch.delenv('DEEPSEEK_API_KEY',raising=False)
    with pytest.raises(ValueError,match='credential_unavailable'):
        launch.run_case(frozen.root,frozen.rp,frozen.expected,frozen.r['cases'][0]['case_id'])
    assert list(frozen.out.iterdir())==[]

def test_missing_store_is_not_created(frozen,monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY','SYNTHETIC_NOT_A_REAL_KEY');frozen.native.unlink()
    with pytest.raises(ValueError,match='existing_native_store_required'):
        launch.run_case(frozen.root,frozen.rp,frozen.expected,frozen.r['cases'][0]['case_id'])
    assert not frozen.native.exists()

def test_native_raw_unknown_stays_blocked_without_explicit_effective_fields():
    raw={'requests':35,'max_requests':350,'spent_micros':207993,'reserved_micros':100000,
         'max_cost_micros':25000000,'in_flight':1,'unreconciled_attempts':1}
    assert not launch.budget_ready(raw)
    reviewed=dict(raw,effective_in_flight=0,blocking_unreconciled_attempts=0)
    assert launch.budget_ready(reviewed)
    assert not launch.budget_ready(dict(reviewed,blocking_unreconciled_attempts=1))
    assert raw['reserved_micros']==100000 and raw['in_flight']==1

def test_cohort_or_limits_mutation_rejected(frozen):
    frozen.r['cases'].reverse();rewrite(frozen)
    with pytest.raises(ValueError,match='cohort_changed'):
        launch.preflight(frozen.root,frozen.rp,frozen.expected)
    frozen.r['limits']['max_sdk_steps']=25;rewrite(frozen)
    with pytest.raises(ValueError,match='unsupported_registered_protocol'):
        launch.preflight(frozen.root,frozen.rp,frozen.expected)

def test_synthetic_sdk_binding_price_window_and_exclusive_claim(frozen,monkeypatch):
    calls=[]
    status={'requests':35,'max_requests':350,'spent_micros':207993,'reserved_micros':100000,
        'max_cost_micros':25000000,'in_flight':1,'unreconciled_attempts':1,
        'effective_in_flight':0,'blocking_unreconciled_attempts':0,'sealed_unknown_attempts':1}
    class Store:
        def __init__(self,path):assert path==frozen.native
        def get_quick_scan_budget_status(self,policy_id,**kwargs):
            assert kwargs=={'include_isolation':True};return dict(status)
    @contextmanager
    def binding(*args,**kwargs):calls.append(('binding',kwargs));yield
    class Client:
        def __init__(self,*args,**kwargs):
            assert args[0]=='SYNTHETIC_NOT_A_REAL_KEY';calls.append(('client',args[1:],kwargs))
    class Session:
        def __init__(self,client,**kwargs):calls.append(('session',kwargs))
    specs={'src.providers.llm_client':{'LLMClient':Client},
        'src.providers.llm_research_client':{'ResearchChatSession':Session},
        'src.utils.quick_scan_work_store':{'QuickScanWorkStore':Store},
        'src.utils.quick_scan_work_transport':{'bind_quick_scan_budget':binding,'bind_quick_scan_route':binding},
        'src.utils.http_client':{'http_client_manager':SimpleNamespace(close_all=lambda:calls.append(('closed',)))}}
    for name,fields in specs.items():
        mod=ModuleType(name)
        for key,value in fields.items():setattr(mod,key,value)
        monkeypatch.setitem(sys.modules,name,mod)
    monkeypatch.setattr(launch,'assert_imports',lambda *args:None)
    monkeypatch.setenv('DEEPSEEK_API_KEY','SYNTHETIC_NOT_A_REAL_KEY')
    # Replace frozen fixture pricer with a local non-network observer; lock is
    # deliberately re-registered BEFORE invoking, as a distinct synthetic test.
    (frozen.root/'pricing.py').write_text('class CohortPriceResolver:\n def __init__(self,**kwargs): pass\n def __call__(self,receipt): return {"fixture":True}\n')
    for row in frozen.r['files']:
        if row['path']=='pricing.py':row.update(bytes=(frozen.root/'pricing.py').stat().st_size,raw_sha256=launch.raw_sha(frozen.root/'pricing.py'))
    settings={k:v for k,v in frozen.r.items() if k in ('experiment_id','phase','files','documents','python_paths','module_bindings','pricing_module','native_budget_store','output_root','expected_policy_id','route_ids')}
    frozen.r=launch.prepare_registration(frozen.root,settings);rewrite(frozen)
    def execute(**kwargs):
        assert kwargs['check_budget']()
        kwargs['before_step']()
        bound=next(c[1] for c in calls if c[0]=='binding' and 'cost_resolver' in c[1])
        assert bound['cost_resolver']({})=={'fixture':True}
        assert bound['independent_task']==kwargs['case']['independent_task']
        kwargs['session_factory'](system_prefix='fixture',tools=[],**{k:v for k,v in launch.LIMITS.items() if k!='max_sdk_steps'})
        kwargs['output'].mkdir()
        return {'session_ref':kwargs['case']['case_id'],'terminal':'fixture_only','sdk_step_invocations':0,
            'unanswered_question_ids':[q['id'] for q in kwargs['questions']]}
    frozen.stub.execute_case=execute;case=frozen.r['cases'][0]
    result=launch.run_case(frozen.root,frozen.rp,frozen.expected,case['case_id'])
    assert result['terminal']=='fixture_only'
    assert calls[-1]==('closed',)
    assert next(c[1] for c in calls if c[0]=='session')['tool_argument_validation']=='controller'
    assert status['reserved_micros']==100000 and status['in_flight']==1
    assert (frozen.out/(case['case_id']+'.claim.json')).exists()
    with pytest.raises(ValueError,match='case_output_exists_no_retry'):
        launch.run_case(frozen.root,frozen.rp,frozen.expected,case['case_id'])


def test_sdk_validation_mode_is_registered_and_cannot_silently_weaken(frozen):
    frozen.r['sdk_options']['tool_argument_validation']='unknown_mode';rewrite(frozen)
    with pytest.raises(ValueError,match='unsupported_registered_sdk_options'):
        launch.preflight(frozen.root,frozen.rp,frozen.expected)


def test_legacy_registration_keeps_original_strict_branch_and_task_scope(frozen):
    frozen.r['protocol']=launch.LEGACY_PROTOCOL;del frozen.r['sdk_options']
    for case in frozen.r['cases']:
        clean={k:v for k,v in case.items() if k!='independent_task'}
        case['independent_task']={'task_id':case['case_id'],'task_sha256':launch.sha(launch.scope_for(frozen.r,clean))}
    rewrite(frozen)
    r,_,_=launch.preflight(frozen.root,frozen.rp,frozen.expected)
    assert r['protocol']==launch.LEGACY_PROTOCOL and 'sdk_options' not in r
