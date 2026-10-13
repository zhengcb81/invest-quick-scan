"""Synthetic wire controls; hashes are integrity, never owner authentication."""
import copy
import pytest
import refresh_contract as refresh
from test_refresh_contract import inputs,preview

def controlled_inputs():
    request,state=inputs()
    request.update(protocol='iqs.refresh_request/1.2.0',cohort_id='B01_SYNTHETIC',work_decision_refs=[])
    state['quote']['currency']='CNY'
    for index,item in enumerate(state['items']):
        control=dict(decision_id='owd1_'+str(index+1)*64,document_sha256='d'*64,
            source_work_item_id='WORK_SYNTHETIC_'+str(index),source_generation=1,
            confirmation_id='rc1_'+'e'*64,purpose='comparison',
            next_retry_at='2026-09-30T09:00:00Z',target_generation=2,cohort_id=request['cohort_id'],
            comparison_controls=dict(pack_size=3,thinking_enabled=True,max_output_tokens=32768))
        item.update(decision='dispatch_new_generation',generation=2,reuse_observation_id=None,
            existing_work_status='failed',owner_control=control)
        request['work_decision_refs'].append(dict(work_item_id=control['source_work_item_id'],decision_id=control['decision_id']))
    return request,state

def test_explicit_control_dialect_binds_cohort_source_refs_generation_and_visible_controls():
    req,state=controlled_inputs();out=preview(req,state)
    assert out['protocol']=='stockwiki.refresh_preview/1.2.0'
    assert out['items']==state['items'] and out['requires_user_confirmation'] is True
    refresh.validate_preview(out,request=req,owner_state=state)
    assert out['API_requests']==0 and out['dispatch_started'] is False

@pytest.mark.parametrize('fault',['cohort','ref','generation','source_generation','missing_control','bool_pack','bool_tokens','unapproved_extra'])
def test_resealed_but_semantically_inconsistent_control_is_rejected(fault):
    req,state=controlled_inputs();c=state['items'][0]['owner_control']
    if fault=='cohort':c['cohort_id']='OTHER'
    elif fault=='ref':req['work_decision_refs'][0]['decision_id']='owd1_'+'0'*64
    elif fault=='generation':state['items'][0]['generation']=3
    elif fault=='source_generation':c['source_generation']=2
    elif fault=='missing_control':del state['items'][0]['owner_control']
    elif fault=='bool_pack':c['comparison_controls']['pack_size']=True
    elif fault=='bool_tokens':c['comparison_controls']['max_output_tokens']=True
    else:c['approved']=True
    with pytest.raises(ValueError):preview(req,state)

def test_legacy_request_does_not_accept_control_fields_or_upgrade_itself():
    req,state=controlled_inputs();req['protocol']='iqs.refresh_request/1.1.0'
    with pytest.raises(ValueError):preview(req,state)
