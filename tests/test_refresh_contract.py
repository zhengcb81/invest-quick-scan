"""Synthetic controlled-refresh boundaries, never proof of financial accuracy."""
import copy
import pytest
import query_contract as query
import refresh_contract as refresh
from test_query_contract_v2 import pair


def inputs():
    source, response, owner = pair()
    source['payload']['snapshot_id'] = response['result']['watermark']['snapshot_id']
    request = dict(protocol='iqs.refresh_request/1.0.0', operation='request_refresh',
        request_id='refresh-synthetic', consumer_id=source['consumer_id'],
        requested_at='2026-10-10T12:02:00Z', source_query=source,
        subject_refs=copy.deepcopy(source['payload']['subject_refs']),
        field_ids=['IQS_01'], origin_task_id='synthetic-consumer', reason='missing field')
    ref = request['subject_refs'][0]
    state = dict(store_id=owner['store_id'], policy_id='owner-policy', policy_version=1,
        policy_sha256='a'*64, provider='mimo', model='mimo-v2.6-pro', ttl_hours=72,
        member_versions={ref['entity_id']:1},
        anchors=[dict(subject_ref=copy.deepcopy(ref), decision_id='decision-synthetic',
            anchor_version=1, manifest_raw_sha256='b'*64, identity_revision=1)],
        items=[dict(subject_ref=copy.deepcopy(ref), field_id='IQS_01', question_id='IQS_01',
            decision='dispatch_new_work', generation=1, reuse_observation_id=None,existing_work_status=None)],
        quote=dict(currency='USD', max_cost_micros=100000, max_http_requests=2,
            budget_state_sha256='c'*64, budget_available=True))
    return request,state


def preview(request=None,state=None):
    if request is None: request,state=inputs()
    return refresh.create_preview(request,state,created_at='2026-10-10T12:03:00Z',
        expires_at='2026-10-10T12:13:00Z')


def test_preview_is_explicit_and_cannot_authorize_or_start_dispatch():
    request,state=inputs()
    result=preview(request,state)
    refresh.validate_preview(result,request=request,owner_state=state)
    assert result['status']=='ready' and result['requires_user_confirmation'] is True
    assert result['dispatch_started'] is False and result['API_requests']==0
    assert result['items']==state['items']
    assert 'confirmation_id' not in result


@pytest.mark.parametrize('mutation',[
    lambda r:r.update(confirmed=True),
    lambda r:r.update(model='caller-model'),
    lambda r:r.update(cost_cap_micros=1),
    lambda r:r.update(field_ids=['not-in-snapshot']),
    lambda r:r.update(field_ids=['IQS_01','IQS_01']),
    lambda r:r['subject_refs'][0].update(perimeter_sha256='d'*64),
    lambda r:r['subject_refs'][0].update(analysis_subject_revision=2),
    lambda r:r['source_query']['payload'].update(snapshot_id=None),
    lambda r:r.update(consumer_id='different-consumer'),
])
def test_request_cannot_expand_snapshot_or_self_assign_authority(mutation):
    request,state=inputs(); mutation(request)
    with pytest.raises(ValueError): refresh.validate_request(request)


@pytest.mark.parametrize('key,value',[
    ('model','another-model'),('policy_version',2),
    ('member_versions',{'ENT_11111111-1111-4111-8111-111111111111':2}),
    ('quote',dict(currency='USD',max_cost_micros=200000,max_http_requests=2,
        budget_state_sha256='d'*64,budget_available=True)),
])
def test_previous_preview_is_not_valid_under_changed_owner_state(key,value):
    request,state=inputs(); result=preview(request,state)
    changed=copy.deepcopy(state); changed[key]=value
    with pytest.raises(ValueError): refresh.validate_preview(result,request=request,owner_state=changed)


def test_even_content_resealed_price_or_plan_cannot_replace_independent_owner():
    request,state=inputs()
    fake=copy.deepcopy(state); fake['quote']['max_cost_micros']=1
    forged=preview(request,fake)
    with pytest.raises(ValueError): refresh.validate_preview(forged,request=request,owner_state=state)
    fake=copy.deepcopy(state); fake['items'][0]['decision']='reuse'
    fake['items'][0]['reuse_observation_id']='obs_'+'e'*64
    fake['quote'].update(max_cost_micros=0,max_http_requests=0)
    forged=preview(request,fake)
    with pytest.raises(ValueError): refresh.validate_preview(forged,request=request,owner_state=state)


def test_multiple_questions_for_one_field_stay_distinct_and_scope_is_not_truncated():
    request,state=inputs(); item=copy.deepcopy(state['items'][0]); item['question_id']='extension_01'
    state['items'].append(item)
    result=preview(request,state)
    assert len(result['items'])==2
    state['items']=[]
    with pytest.raises(ValueError): preview(request,state)


def test_budget_refusal_and_uncertain_existing_work_never_become_ready():
    request,state=inputs(); state['quote']['budget_available']=False
    assert preview(request,state)['status']=='blocked'
    state['quote']['budget_available']=True
    state['items'][0].update(decision='deferred_unknown')
    state['quote'].update(max_cost_micros=0,max_http_requests=0)
    result=preview(request,state)
    assert result['status']=='blocked' and result['requires_user_confirmation'] is False


def test_all_reused_is_zero_cost_noop_and_original_reference_survives():
    request,state=inputs(); state['items'][0].update(decision='reuse',reuse_observation_id='obs_'+'e'*64)
    state['quote'].update(max_cost_micros=0,max_http_requests=0)
    result=preview(request,state)
    assert result['status']=='noop' and result['items'][0]['reuse_observation_id']=='obs_'+'e'*64
    assert result['requires_user_confirmation'] is False


@pytest.mark.parametrize('mutate',[
    lambda s:s.update(policy_version=True),
    lambda s:s['anchors'][0].update(anchor_version=True),
    lambda s:s['quote'].update(max_cost_micros=-1),
    lambda s:s['quote'].update(max_http_requests=0),
    lambda s:s['items'].append(copy.deepcopy(s['items'][0])),
])
def test_invalid_owner_state_is_not_silently_normalized(mutate):
    request,state=inputs();mutate(state)
    with pytest.raises(ValueError):preview(request,state)


def test_preview_expiry_does_not_extend_capture_or_answer_ttl():
    request,state=inputs(); result=preview(request,state)
    refresh.validate_preview(result,request=request,owner_state=state,now='2026-10-10T12:12:59Z')
    with pytest.raises(ValueError):
        refresh.validate_preview(result,request=request,owner_state=state,now='2026-10-10T12:13:00Z')
    assert result['source_snapshot_id']==request['source_query']['payload']['snapshot_id']


def test_model_filter_must_match_the_actual_owner_selected_model():
    request,state=inputs();request['source_query']['payload']['model_filter']={'provider':'mimo','model_resolved':'other-model'}
    with pytest.raises(ValueError):preview(request,state)


def test_durable_answer_delivery_can_resume_with_zero_model_budget():
    request,state=inputs()
    state['items'][0].update(decision='resume_existing_work',existing_work_status='result_ready')
    state['quote'].update(max_cost_micros=0,max_http_requests=0,budget_available=False)
    result=preview(request,state)
    assert result['status']=='ready' and result['requires_user_confirmation'] is True
    assert result['quote']['max_http_requests']==0 and result['dispatch_started'] is False
    state['items'][0]['existing_work_status']='pending'
    assert preview(request,state)['status']=='blocked'


@pytest.mark.parametrize('key,value',[('policy_version',1.0),('ttl_hours',72.0)])
def test_float_integer_lookalikes_do_not_cross_the_wire(key,value):
    request,state=inputs();state[key]=value
    with pytest.raises(ValueError):preview(request,state)


def policy(tmp_path):
    request,state=inputs();ref=request['subject_refs'][0]
    return dict(protocol='stockwiki.refresh_owner_policy/1.0.0',policy_id='owner-fixture',policy_version=1,
        owner_principal='synthetic-principal',allowed_consumer_ids=['invest-quick-scan'],universe_id='synthetic-universe',
        field_ids=['IQS_01'],provider='mimo',model='mimo-v2.6-pro',ttl_hours=72,
        routes=[dict(subject_ref=ref,subject_key=ref['analysis_subject_id']+'@1',scope='entity',scope_id=ref['entity_id'])],
        qa=dict(code_root=str(tmp_path/'qa'),work_store=str(tmp_path/'work.sqlite'),budget_policy_file=str(tmp_path/'policy.json'),
            policy_id='original-budget',route_id='route1',provider_config_ref='primary'))


@pytest.mark.parametrize('change',[
    lambda p:p.update(confirmed=True),
    lambda p:p.update(policy_version=True),
    lambda p:p['routes'][0].update(subject_key='display-name-as-identity'),
    lambda p:p['routes'][0].update(scope_id='another-entity'),
    lambda p:p['qa'].update(work_store='relative.sqlite'),
    lambda p:p['routes'].append(copy.deepcopy(p['routes'][0])),
])
def test_owner_policy_rejects_unknown_fields_and_ambiguous_routes(tmp_path,change):
    value=policy(tmp_path);refresh.validate_policy(value);change(value)
    with pytest.raises(ValueError):refresh.validate_policy(value)


def test_dynamic_pool_and_module_permission_require_explicit_owner_opt_in(tmp_path):
    value=policy(tmp_path)
    value.update(routes=[],field_ids=[])
    with pytest.raises(ValueError):refresh.validate_policy(value)
    value.update(route_resolution='current_owner_members',field_permission='current_manifest')
    assert refresh.validate_policy(value)==value
    value['routes']=policy(tmp_path)['routes']
    with pytest.raises(ValueError):refresh.validate_policy(value)
