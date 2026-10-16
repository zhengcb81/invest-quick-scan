"""Isolated driver boundaries with the original IQS answer validator."""
import copy
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from company_agent_research_pilot import AnswerSink,public_board,run_session
from standard_answers import validate_content

SOURCE={'source_id':'SYN-SOURCE','official_url':'https://example.com/synthetic','publication_date':'2026-01-01'}
QUESTIONS=[{'id':'Q1'},{'id':'Q2'}]

def answer(qid,score=None):
    return dict(question_id=qid,response_kind='score',status='insufficient_evidence' if score is None else 'scored',score=score,
      summary='Synthetic fixture; not a company assessment.',information_as_of='2026-10-13',period_start=None,period_end=None,
      basis='current',trend='uncertain',confidence='low',metrics=[],items=[],evidence=[] if score is None else [dict(id='SYN-SOURCE',title='Synthetic',url=SOURCE['official_url'],published_at=SOURCE['publication_date'],claim='Synthetic source claim.')],
      counterevidence='Synthetic fixture.',watch_triggers=[],missing_fields=['Synthetic gap.'],coverage={'status':'partial','reason':'Synthetic.'})

def validate(a,q,cutoff):return validate_content(a,q,cutoff,metric_registry={'metrics':{}})

def sink():return AnswerSink(QUESTIONS,[SOURCE],validate,'2026-10-13')

def test_unknown_does_not_become_automatic_five():
    s=sink();assert s.submit([answer('Q1')],['Q1'])['status']=='committed';assert s.answers['Q1']['score'] is None
    bad=answer('Q2');bad['score']=5
    assert s.submit([bad],['Q2'])['status']=='rejected'
    assert 'Q2' not in s.answers

@pytest.mark.parametrize('kind',['duplicate','unrequested','bad_citation'])
def test_invalid_batch_is_atomic_and_previous_valid_answer_preserved(kind):
    s=sink();s.submit([answer('Q1')],['Q1']);before=copy.deepcopy((s.answers,s.revisions))
    batch=[answer('Q1',8),answer('Q2',8)]
    if kind=='duplicate':batch=[answer('Q2'),answer('Q2')]
    if kind=='unrequested':batch=[answer('Q2')]
    if kind=='bad_citation':batch[1]['evidence'][0]['url']='https://example.com/fabricated'
    result=s.submit(batch,['Q1'] if kind=='unrequested' else ['Q1','Q2'])
    assert result['status']=='rejected' and (s.answers,s.revisions)==before


def test_dedup_public_evidence_rejects_conflicting_same_id():
    a={'company_key':'synthetic','facts':[{'fact_id':'F','claim':'A'}],'sources':[SOURCE]}
    b=copy.deepcopy(a);b['facts'][0]['claim']='B'
    with pytest.raises(ValueError,match='conflicting duplicate'):public_board({'entries':[a,b],'cutoff':'2026-10-13','limitations':[]},'synthetic')

class Strategy:
    def next_action(self,state):
        ids=[s['question_id'] for s in state['slots'] if s['execution_status']=='not_attempted']
        return {'kind':'model_step','question_ids':ids[:1],'payload':{'dynamic_directive':'Synthetic directive'}} if ids else {'kind':'finish'}

class Session:
    def __init__(self):self.calls=[];self.closed=False
    def step(self,**kwargs):
        self.calls.append(kwargs);i=len(self.calls)
        return {'receipt':{'attempt_id':'SYN-'+str(i)},'usage_observation':{'prompt_tokens':None},'elapsed_seconds':.02,
                'stable_prefix_sha256':'a'*64,'content':'','tool_calls':[{'id':'call'+str(i),'name':'submit_answers','arguments':{'answers':[answer('Q'+str(i))]}}]}
    def close(self):self.closed=True

def test_session_keeps_new_group_with_real_tool_id_and_all_slots(tmp_path):
    session=Session()
    result=run_session(session=session,strategy_id='fixed3',repeat=1,questions=QUESTIONS,projection={'A':'Q1','B':'Q2'},board={'company_key':'synthetic','cutoff':'2026-10-13','sources':[SOURCE]},sink_factory=sink,tools=[],make_strategy=lambda *_a,**_k:Strategy(),output=tmp_path/'run',check_budget=lambda:True)
    assert len(session.calls)==2 and session.closed and result['unanswered_question_ids']==[]
    second=session.calls[1];assert set(second['tool_results'])=={'call1'}
    assert json.loads(second['continuation_context'])['requested_question_ids']==['Q2']
    assert result['production_owner_verified'] is False and result['financial_accuracy'] is None
    assert result['usage_observations'][0]['prompt_tokens'] is None


def test_unreconciled_native_budget_stops_before_next_call(tmp_path):
    session=Session()
    result=run_session(session=session,strategy_id='fixed3',repeat=1,questions=QUESTIONS,projection={'A':'Q1','B':'Q2'},board={'company_key':'synthetic','cutoff':'2026-10-13','sources':[SOURCE]},sink_factory=sink,tools=[],make_strategy=lambda *_a,**_k:Strategy(),output=tmp_path/'run',check_budget=lambda:False)
    assert len(session.calls)==1 and result['terminal']=='native_budget_unreconciled'
    assert result['unanswered_question_ids']==['Q2']


def test_specific_feedback_contains_no_raw_validator_instance():
    from company_agent_research_pilot import safe_validation_error
    from jsonschema import Draft202012Validator
    err=next(Draft202012Validator({'type':'integer'}).iter_errors('PRIVATE_CANARY_INSTANCE'))
    result=safe_validation_error(err)
    assert result['code']=='schema_type' and 'PRIVATE_CANARY_INSTANCE' not in json.dumps(result)
    s=AnswerSink(QUESTIONS,[SOURCE],validate,'2026-10-13',diagnostic_feedback=True,max_answers=3)
    bad=answer('Q1');bad['score']=5
    assert s.submit([bad],['Q1'])['validation_feedback']['code']=='score/status mismatch'


def test_bounded_batch_never_commits_an_oversize_submission():
    s=AnswerSink(QUESTIONS,[SOURCE],validate,'2026-10-13',diagnostic_feedback=True,max_answers=1)
    result=s.submit([answer('Q1'),answer('Q2')],['Q1','Q2'])
    assert result['validation_feedback']['code']=='answer_batch_exceeds_limit' and s.answers=={}


def test_global_static_prefix_precedes_mutable_company_scope():
    from company_agent_research_pilot import build_prefix
    cfg={'protocol':'iqs.isolated-research-pilot-config/1.1.0','identity':{'name':'synthetic-A'},'company_profile':{'company':'A'}}
    board={'cutoff':'2026-10-13','sources':[SOURCE]}
    a=build_prefix(cfg,QUESTIONS,board,{}, {})
    cfg['identity']={'name':'synthetic-B'};cfg['company_profile']={'company':'B'}
    b=build_prefix(cfg,QUESTIONS,board,{}, {})
    assert a.split('COMPANY SCOPE')[0]==b.split('COMPANY SCOPE')[0]
    assert a.index('QUESTION MODULE')<a.index('COMPANY SCOPE')<a.index('PUBLIC EVIDENCE')


def test_public_drafts_are_retained_only_when_explicitly_screened(tmp_path):
    session=Session()
    kwargs=dict(strategy_id='fixed3',repeat=1,questions=QUESTIONS,projection={'A':'Q1','B':'Q2'},board={'company_key':'synthetic','cutoff':'2026-10-13','sources':[SOURCE]},sink_factory=sink,tools=[],make_strategy=lambda *_a,**_k:Strategy(),check_budget=lambda:True,driver_variant='bounded3-feedback1.1',record_drafts=True)
    result=run_session(session=session,output=tmp_path/'retain',leak_scan=lambda _x:False,**kwargs)
    assert result['protocol']=='iqs.isolated-company-research/1.1.0'
    assert (tmp_path/'retain/draft-01.json').exists()
    run_session(session=Session(),output=tmp_path/'discard',leak_scan=lambda _x:True,**kwargs)
    assert not (tmp_path/'discard/draft-01.json').exists()
