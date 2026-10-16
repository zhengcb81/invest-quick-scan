"""Meaningful research-controller boundaries; synthetic transport, real contracts."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
LABS=Path('C:/Users/郑曾波/Projects')
for directory in ('iqs-answer-codec-lab','iqs-session-packing-lab','iqs-claim-guard-lab'):
    sys.path.insert(0,str(LABS/directory))
from company_agent_contrast import make_context, prefix_text, compile_tools, execute_case
from iqs_session_packing.synthetic import SyntheticStep,default_usage,make_synthetic_factory

FROZEN=ROOT/'runs/research-tools-wave-2026-10-16/inputs'
def load(name): return json.loads((FROZEN/'trial'/name).read_text(encoding='utf-8'))
ALL=load('questions.json')
BOARD=load('evidence-board.json')
SCHEMA=load('answer-schema.json')
METRICS=load('metrics.json')
LIMITS={'max_sdk_steps':24,'max_output_tokens':16384,'session_input_tokens':2000000,'session_output_tokens':192000,'wall_seconds':1800}

def answer(qid):
    return dict(question_id=qid,response_kind='score',status='insufficient_evidence',score=None,
        summary='Bounded evidence does not establish the full requested construct.',information_as_of='2026-10-13',
        period_start=None,period_end=None,basis='current',trend='uncertain',confidence='low',metrics=[],items=[],
        source_claims=[],counterevidence='No adequate independent operating evidence.',watch_triggers=[],
        missing_fields=['Direct operating support'],coverage={'status':'partial','reason':'Financial proxies do not establish the requested construct.'})

def step(answers,identity,kind='tool',usage=True):
    payload={'protocol':'iqs.compact-answer-batch/1.0.0','company_key':'alphabet','answers':answers}
    return SyntheticStep('unknown_usage' if not usage else 'final',content=json.dumps(payload) if kind=='content' else '',
        calls=[] if kind=='content' else [{'id':identity,'name':'submit_answers','arguments':payload}],
        usage=default_usage() if usage else None)

def run(tmp_path,scripts,*,strategy='single',questions=None,check_budget=lambda:True):
    questions=questions or ALL[:3]
    return execute_case(case={'case_id':'synthetic-case','strategy_id':strategy,'repeat':1,'model':'synthetic-model','phase':'T2-test'},
        questions=questions,board=BOARD,answer_schema=SCHEMA,metrics=METRICS,identity={'company':'Alphabet Inc.'},
        limits=LIMITS,session_factory=make_synthetic_factory(scripts),inputs_root=FROZEN,
        output=tmp_path/'run',check_budget=check_budget)

def test_single_segments_keep_one_company_usage_and_real_tool_acknowledgments(tmp_path):
    result=run(tmp_path,[[step([answer(q['id'])],'c'+str(i))] for i,q in enumerate(ALL[:3])])
    assert len(result['answers'])==3 and not result['unanswered_question_ids']
    state=json.loads((tmp_path/'run/session-state.json').read_text(encoding='utf-8'))
    assert state['cumulative']['input_tokens_used']==300
    assert len(state['segments'])==3
    assert all(a['score'] is None for a in result['answers'])

def test_pack3_atomic_rejection_and_same_segment_repair(tmp_path):
    batch=[answer(q['id']) for q in ALL[:3]]
    bad=copy.deepcopy(batch); bad[2]['score']=5
    result=run(tmp_path,[[step(bad,'bad'),step(batch,'fixed')]],strategy='pack3')
    assert len(result['answers'])==len(result['revisions'])==3
    assert result['sdk_step_invocations']==2
    events=[json.loads(s) for s in (tmp_path/'run/events.jsonl').read_text(encoding='utf-8').splitlines()]
    assert any(e.get('result',{}).get('status')=='rejected' for e in events)

def test_free_agent_selects_actual_subset_without_controller_reordering(tmp_path):
    qs=ALL[:3]
    result=run(tmp_path,[[step([answer(qs[2]['id'])],'first'),step([answer(qs[0]['id']),answer(qs[1]['id'])],'second')]],strategy='company_agent')
    assert [r['question_id'] for r in result['revisions']]==[qs[2]['id'],qs[0]['id'],qs[1]['id']]

def test_unknown_last_step_does_not_become_success_or_auto_resend(tmp_path):
    result=run(tmp_path,[[step([answer(ALL[0]['id'])],'unknown',usage=False)]],questions=ALL[:1])
    assert result['sdk_step_invocations']==1
    assert result['terminal']!='all_slots_returned'
    assert result['usage_observations'][0]['prompt_tokens'] is None

def test_native_budget_pause_is_checked_before_any_new_send(tmp_path):
    result=run(tmp_path,[[step([answer(ALL[0]['id'])],'never')]],questions=ALL[:1],check_budget=lambda:False)
    assert result['sdk_step_invocations']==0 and result['answers']==[]

def test_hidden_thinking_in_compact_answer_is_not_persisted(tmp_path):
    a=answer(ALL[0]['id']);a['summary']='<think>PRIVATE_REASONING_SENTINEL</think>'
    result=run(tmp_path,[[step([a],'c1'),step([answer(ALL[0]['id'])],'c2')]],questions=ALL[:1])
    assert len(result['answers'])==1
    assert all('PRIVATE_REASONING_SENTINEL' not in p.read_text(encoding='utf-8') for p in (tmp_path/'run').glob('*.json*'))

def test_oversize_subset_does_not_cross_single_question_boundary(tmp_path):
    batch=[answer(q['id']) for q in ALL[:2]]
    result=run(tmp_path,[[step(batch,'wrong'),step([answer(ALL[0]['id'])],'right')],[step([answer(ALL[1]['id'])],'last')]],questions=ALL[:2])
    assert len(result['revisions'])==2 and result['sdk_step_invocations']==3

def test_prefix_and_tools_are_treatment_independent_but_evidence_bound():
    a=prefix_text(ALL,BOARD,SCHEMA,METRICS,{'company':'Alphabet Inc.'})
    changed=copy.deepcopy(BOARD);changed['facts'][0]['claim']='Different public evidence'
    b=prefix_text(ALL,changed,SCHEMA,METRICS,{'company':'Alphabet Inc.'})
    assert a!=b and make_context(ALL,BOARD)!=make_context(ALL,changed)
    assert compile_tools()==compile_tools()


def test_partial_pack_progress_is_not_misclassified_as_protocol_failure(tmp_path):
    qs=ALL[:3]
    result=run(tmp_path,[[step([answer(q['id'])],'c'+str(i)) for i,q in enumerate(qs)]],strategy='pack3')
    assert len(result['answers'])==3 and result['terminal']=='all_slots_returned'
    assert result['sdk_step_invocations']==3


def test_common_repair_allows_two_safe_feedback_rounds_but_keeps_company_cap(tmp_path):
    a=answer(ALL[0]['id']);a['score']=5
    result=run(tmp_path,[[step([a],'bad1'),step([a],'bad2'),step([answer(ALL[0]['id'])],'fixed')]],questions=ALL[:1])
    assert result['sdk_step_invocations']==3 and len(result['answers'])==1


def test_three_nonprogress_agent_steps_stop_without_spending_remaining_company_budget(tmp_path):
    a=answer(ALL[0]['id']);a['score']=5
    result=run(tmp_path,[[step([a],'bad'+str(i)) for i in range(4)]],questions=ALL[:1],strategy='company_agent')
    assert result['sdk_step_invocations']==3 and not result['answers']
    assert result['terminal']=='pack_protocol_repair_exhausted'
