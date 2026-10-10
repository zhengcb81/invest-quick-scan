"""Synthetic scope/coverage boundary fixtures; never a real owner golden."""
import copy
import base64
import hashlib
import json

import pytest

import query_contract as qc


SUBJECT = {
    'entity_id': 'ENT_11111111-1111-4111-8111-111111111111',
    'analysis_subject_id': 'ASJ_22222222-2222-4222-8222-222222222222',
    'analysis_subject_revision': 1,
    'primary_issuer_id': 'ENT_33333333-3333-4333-8333-333333333333',
    'perimeter_sha256': 'a'*64,
    'scope': 'entity',
    'scope_id': 'ENT_11111111-1111-4111-8111-111111111111',
    'security_id': None, 'listing_id': None, 'segment_id': None,
}


def pair():
    request = {'message_type':'request','schema_version':'2.0.0','request_id':'REQ_SYNTHETIC_C06',
               'consumer_id':'invest-quick-scan','operation':'get_profiles',
               'requested_at':'2026-10-09T21:00:00Z',
               'payload':{'subject_refs':[copy.deepcopy(SUBJECT)],'field_ids':['IQS_01'],
                          'information_cutoff':'2026-10-09','include_history':True,
                          'model_filter':None,'snapshot_id':None}}
    coverage = {'status':'not_covered','requested_markets':['US'],'covered_markets':[],
                'requested_field_ids':['IQS_01'],'covered_field_ids':[],
                'missing_field_ids':['IQS_01'],'scores_available':False,'facts_available':False,
                'reason':'synthetic no observation coverage'}
    watermark = {'store_id':'STORE_SYNTHETIC_C06','snapshot_id':'SNAP_SYNTHETIC_C06',
                 'member_sequence':0,'observation_sequence':0,'ack_sequence':0,
                 'read_at':'2026-10-09T21:01:00Z'}
    response = {'message_type':'response','schema_version':'2.0.0','request_id':request['request_id'],
                'operation':'get_profiles','response_at':'2026-10-09T21:01:00Z',
                'result':{'status':'coverage_gap','profiles':[{'subject_ref':copy.deepcopy(SUBJECT),
                           'canonical_name':'Synthetic C06','observations':[]}],
                          'missing_subject_refs':[],'coverage':coverage,'watermark':watermark}}
    response['result']['legacy_unbound_observations']=[]
    watermark.update(read_consistency='sequential_owner_reads',source_watermarks=[
        {'namespace':'identity','schema_version':6,'status':'available','sequence':0,
         'read_at':watermark['read_at'],'content_sha256':'2'*64},
        {'namespace':'observations','schema_version':3,'status':'available','sequence':0,
         'read_at':watermark['read_at'],'content_sha256':'3'*64}])
    seal(request,response)
    owner = {'store_id':'STORE_SYNTHETIC_C06'}
    return request, response, owner


def validate(request, response, owner):
    qc.validate_request(request)
    qc.validate_response(response,expected_request=request,expected_owner=owner)


def test_real_uuid_spelling_and_distinct_scan_entity_vs_legal_issuer():
    validate(*pair())


def test_two_reporting_subjects_for_one_entity_are_two_profiles():
    request, response, owner = pair()
    other = copy.deepcopy(SUBJECT)
    other['analysis_subject_id']='ASJ_44444444-4444-4444-8444-444444444444'
    other['perimeter_sha256']='b'*64
    request['payload']['subject_refs'].append(other)
    response['result']['profiles'].append({'subject_ref':copy.deepcopy(other),
                                           'canonical_name':'Synthetic C06','observations':[]})
    seal(request,response)
    validate(request,response,owner)


@pytest.mark.parametrize('field,new',[
    ('analysis_subject_revision',2), ('perimeter_sha256','b'*64),
    ('primary_issuer_id','ENT_55555555-5555-4555-8555-555555555555'),
    ('entity_id','ENT_66666666-6666-4666-8666-666666666666'),
    ('scope_id','ENT_66666666-6666-4666-8666-666666666666'),
])
def test_profile_cannot_drift_from_requested_subject(field,new):
    request,response,owner=pair()
    response['result']['profiles'][0]['subject_ref'][field]=new
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_conflicting_perimeters_for_same_subject_are_not_two_requests():
    request,response,owner=pair()
    other=copy.deepcopy(SUBJECT)
    other['perimeter_sha256']='b'*64
    request['payload']['subject_refs'].append(other)
    with pytest.raises(ValueError):
        qc.validate_request(request)


def test_response_cannot_return_same_profile_twice():
    request,response,owner=pair()
    response['result']['profiles']*=2
    with pytest.raises(ValueError):
        validate(request,response,owner)


@pytest.mark.parametrize('kind',['complete','overlap','unrequested'])
def test_field_coverage_is_an_exact_partition_of_request(kind):
    request,response,owner=pair()
    coverage=response['result']['coverage']
    if kind=='complete': coverage['status']='complete'
    elif kind=='overlap': coverage['covered_field_ids']=['IQS_01']
    else: coverage['missing_field_ids']=['IQS_02']
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_response_store_must_match_independent_owner():
    request,response,owner=pair()
    response['result']['watermark']['store_id']='STORE_FOREIGN'
    with pytest.raises(ValueError):
        validate(request,response,owner)


def test_response_requires_explicit_independent_owner():
    request,response,_=pair()
    with pytest.raises(ValueError):
        qc.validate_response(response,expected_request=request,expected_owner=None)


@pytest.mark.parametrize('field,value',[('request_id','REQ_FOREIGN'),('schema_version','1.0.0'),('operation','search')])
def test_response_does_not_silently_change_request_or_protocol(field,value):
    request,response,owner=pair()
    response[field]=value
    with pytest.raises(ValueError):
        validate(request,response,owner)


@pytest.mark.parametrize('raw',[b'{"request_id":"one","request_id":"two"}',b'{"x":NaN}',b'{"x":1e400}',b'{"truncated":'])
def test_strict_input_rejects_duplicate_nonfinite_and_truncated_json(tmp_path,raw):
    path=tmp_path/'input.json'
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        qc.load_document(path)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                    ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def seal(request,response):
    """Fixture content-addressing only; does not authorise any owner binding."""
    w=response['result']['watermark']
    semantics={k:copy.deepcopy(v) for k,v in request['payload'].items() if k!='snapshot_id'}
    w['query_sha256']=digest({'consumer_id':request['consumer_id'],
                              'operation':request['operation'],'payload':semantics})
    core=copy.deepcopy(response['result'])
    for k in ('snapshot_id','snapshot_content_sha256'):
        core['watermark'].pop(k,None)
    w['snapshot_content_sha256']=digest(core)
    w['snapshot_id']='snap2_'+w['snapshot_content_sha256']


def observation(*,model='actual-a',status='scored'):
    """Complete but deliberately synthetic portable Observation, never real gold."""
    answer={'question_id':'IQS_01','response_kind':'score','status':status,
        'score':8 if status=='scored' else None,'summary':'synthetic answer',
        'information_as_of':'2026-10-08','period_start':None,'period_end':None,
        'basis':'current','trend':'stable','confidence':'low','metrics':[],'items':[],
        'evidence':[{'id':'E1','title':'synthetic pointer','url':'https://example.com/evidence',
                     'published_at':'2026-10-08','claim':'synthetic claim'}] if status=='scored' else [],
        'counterevidence':'synthetic uncertainty','watch_triggers':[],'missing_fields':[],
        'coverage':{'status':'partial','reason':'synthetic scope'}}
    obs={'schema_version':'1.1.0','entity_id':SUBJECT['entity_id'],'security_id':None,
        'segment_id':None,'field_id':'IQS_01','construct_id':None,'question_id':'IQS_01',
        'question_version':'1.0','template_version':'synthetic-v1','method_id':'synthetic-method',
        'scope':'entity','cohort':{'company_type':'unclassified','industries':[],
                                  'stage':'unclassified','subtype':None},
        'information_cutoff':'2026-10-08','run_id':'SYN_RUN','scan_id':'SYN_SCAN',
        'inputset_id':'SYN_INPUT','task_mode':'primary','comparison_group_id':None,
        'observed_at':'2026-10-09T20:01:00Z',
        'execution':{'provider':'synthetic-provider','model_requested':'requested-a',
            'model_resolved':model,'model_revision':None,'request_id':'SYN_REQ',
            'attempt_id':'SYN_ATT','started_at':'2026-10-09T20:00:00Z',
            'answered_at':'2026-10-09T20:01:00Z','search_status':'executed',
            'search_receipt_id':'SYN_SEARCH','prompt_sha256':'c'*64},
        'answer':answer,'evidence_review_status':'unreviewed','module_package_id':'pkg_'+'4'*64,
        'module_release_id':'modrel_'+'5'*64,'question_definition_sha256':'d'*64,
        'question_semantic_sha256':'e'*64,'cycle_sensitive':False}
    obs['observation_id']='obs_'+digest(obs)
    return obs


def projection(obs,*,bound=True):
    raw=json.dumps(obs,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    binding={'protocol':'stockwiki.observation_subject_binding/1.0.0',
             'receipt_id':'SYN_BINDING','subject_ref':copy.deepcopy(SUBJECT),
             'observation_id':obs['observation_id'],'payload_sha256':digest(obs),
             'execution_request_id':obs['execution']['request_id'],
             'execution_attempt_id':obs['execution']['attempt_id'],
             'dispatch_identity_snapshot_sha256':'f'*64,'dispatch_manifest_sha256':'1'*64,
             'recorded_before_send_at':'2026-10-09T19:59:00Z'} if bound else None
    return {'observation_id':obs['observation_id'],'payload_sha256':digest(obs),
            'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'original_json_base64':base64.b64encode(raw).decode(),
            'observation_wire_profile':'stockwiki-portable-observation/1.0.0',
            'binding_status':'bound' if bound else 'legacy_unbound',
            'subject_binding':binding,'observation_sequence':1,'ack_sequence':1,
            'ingest_status':'accepted','qualification_status':'review_pending'}


def advanced_pair(*,bound=True,status='scored'):
    req,res,owner=pair()
    row=projection(observation(status=status),bound=bound)
    res['result']['legacy_unbound_observations']=[]
    if bound: res['result']['profiles'][0]['observations']=[row]
    else: res['result']['legacy_unbound_observations']=[row]
    w=res['result']['watermark']
    w.update(observation_sequence=1,ack_sequence=1,
        read_consistency='sequential_owner_reads',
        source_watermarks=[{'namespace':'identity','schema_version':6,'status':'available',
          'sequence':0,'read_at':w['read_at'],'content_sha256':'2'*64},
         {'namespace':'observations','schema_version':3,'status':'available',
          'sequence':1,'read_at':w['read_at'],'content_sha256':'3'*64}])
    if bound and status=='scored':
        res['result']['status']='ok'
        res['result']['coverage'].update(status='complete',covered_field_ids=['IQS_01'],
                                         missing_field_ids=[],scores_available=True)
    owner['observation_refs']={row['observation_id']:{
        'payload_sha256':row['payload_sha256'],
        'binding_sha256':digest(row['subject_binding']) if bound else None,
        'observation_sequence':1,'ack_sequence':1,'ingest_status':'accepted',
        'qualification_status':'review_pending'}}
    seal(req,res)
    return req,res,owner


def repackage(row,obs):
    """Re-sign only the presented payload; independently stored refs stay fixed."""
    replacement=projection(obs,bound=row['binding_status']=='bound')
    row.update(replacement)


def test_original_bound_answer_keeps_requested_and_actual_model_separate():
    req,res,owner=advanced_pair()
    validate(req,res,owner)
    raw=base64.b64decode(res['result']['profiles'][0]['observations'][0]['original_json_base64'])
    original=json.loads(raw)
    assert original['execution']['model_requested']=='requested-a'
    assert original['execution']['model_resolved']=='actual-a'
    assert original['evidence_review_status']=='unreviewed'


def test_legacy_unbound_history_is_visible_but_not_current_subject_coverage():
    validate(*advanced_pair(bound=False))


def test_unavailable_original_answer_stays_null_and_uncovered():
    validate(*advanced_pair(status='insufficient_evidence'))


@pytest.mark.parametrize('field,value',[
    ('analysis_subject_revision',2),('perimeter_sha256','9'*64),
    ('primary_issuer_id','ENT_55555555-5555-4555-8555-555555555555'),
    ('scope','security'),('scope_id','SEC_FOREIGN')])
def test_bound_answer_refuses_foreign_subject_even_when_presented_hashes_are_resigned(field,value):
    req,res,owner=advanced_pair()
    res['result']['profiles'][0]['observations'][0]['subject_binding']['subject_ref'][field]=value
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


@pytest.mark.parametrize('field,value',[
    ('execution_request_id','FOREIGN'),('execution_attempt_id','FOREIGN'),
    ('recorded_before_send_at','2026-10-09T20:02:00Z'),
    ('dispatch_identity_snapshot_sha256','9'*64),('dispatch_manifest_sha256','9'*64)])
def test_dispatch_binding_cannot_be_reconstructed_from_current_route(field,value):
    req,res,owner=advanced_pair()
    res['result']['profiles'][0]['observations'][0]['subject_binding'][field]=value
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


def test_owner_observation_refs_are_required_for_nonempty_answers():
    req,res,owner=advanced_pair()
    owner.pop('observation_refs')
    with pytest.raises(ValueError): validate(req,res,owner)


@pytest.mark.parametrize('mutation',['raw','payload_hash','immutable_id','qualification','ack_sequence','duplicate'])
def test_original_answer_reference_integrity(mutation):
    req,res,owner=advanced_pair()
    row=res['result']['profiles'][0]['observations'][0]
    if mutation=='raw': row['original_json_base64']=base64.b64encode(b'{"truncated":').decode()
    elif mutation=='payload_hash': row['payload_sha256']='9'*64
    elif mutation=='immutable_id': row['observation_id']='obs_'+'9'*64
    elif mutation=='qualification': row['qualification_status']='independently_checked'
    elif mutation=='ack_sequence': row['ack_sequence']=2
    else: res['result']['profiles'][0]['observations'].append(copy.deepcopy(row))
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


@pytest.mark.parametrize('mutation',['future_cutoff','future_information','reversed_time','different_observed',
 'future_answer','missing_actual_model','wrong_question','bool_score','unknown_with_score',
 'source_after_cutoff','detached_fact','model_self_qualification'])
def test_bad_original_answer_remains_bad_with_new_self_consistent_presentation(mutation):
    req,res,owner=advanced_pair()
    row=res['result']['profiles'][0]['observations'][0]
    obs=json.loads(base64.b64decode(row['original_json_base64']))
    if mutation=='future_cutoff': obs['information_cutoff']='2026-10-10'
    elif mutation=='future_information': obs['answer']['information_as_of']='2026-10-10'
    elif mutation=='reversed_time': obs['execution']['started_at']='2026-10-09T20:02:00Z'
    elif mutation=='different_observed': obs['observed_at']='2026-10-09T20:02:00Z'
    elif mutation=='future_answer':
        obs['observed_at']=obs['execution']['answered_at']='2026-10-10T20:01:00Z'
    elif mutation=='missing_actual_model': obs['execution']['model_resolved']=None
    elif mutation=='wrong_question': obs['answer']['question_id']='IQS_02'
    elif mutation=='bool_score': obs['answer']['score']=True
    elif mutation=='unknown_with_score': obs['answer']['status']='insufficient_evidence'
    elif mutation=='source_after_cutoff': obs['answer']['evidence'][0]['published_at']='2026-10-10'
    elif mutation=='detached_fact': obs['answer']['response_kind']='fact'
    else: obs['answer']['check_level']='independently_checked'
    # An independent bad-row fixture deliberately grants the presented address:
    # semantic defects must still be refused, not hidden behind a hash mismatch.
    obs['observation_id']='obs_'+digest({k:v for k,v in obs.items() if k!='observation_id'})
    repackage(row,obs)
    owner['observation_refs']={row['observation_id']:{'payload_sha256':row['payload_sha256'],
        'binding_sha256':digest(row['subject_binding']),'observation_sequence':1,'ack_sequence':1,
        'ingest_status':'accepted','qualification_status':'review_pending'}}
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


def test_model_filter_is_applied_to_actual_model_only():
    req,res,owner=advanced_pair()
    req['payload']['model_filter']={'provider':'synthetic-provider','model_resolved':'requested-a'}
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)
    req['payload']['model_filter']['model_resolved']='actual-a'
    seal(req,res)
    validate(req,res,owner)


def test_unbound_history_cannot_be_moved_inside_a_subject_profile():
    req,res,owner=advanced_pair(bound=False)
    res['result']['profiles'][0]['observations']=res['result']['legacy_unbound_observations']
    res['result']['legacy_unbound_observations']=[]
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


@pytest.mark.parametrize('mutation',['digest','old_snapshot','negative_sequence','read_error','foreign_query','read_before_answer'])
def test_snapshot_and_owner_watermark_are_not_live_page_decorations(mutation):
    req,res,owner=advanced_pair()
    w=res['result']['watermark']
    if mutation=='digest': w['snapshot_content_sha256']='9'*64
    elif mutation=='old_snapshot': req['payload']['snapshot_id']='SNAP_OLD'
    elif mutation=='negative_sequence': w['observation_sequence']=-1
    elif mutation=='read_error':
        w['source_watermarks'][1].update(status='read_error',content_sha256=None)
        seal(req,res)
    elif mutation=='foreign_query': w['query_sha256']='9'*64
    else:
        w['read_at']='2026-10-09T20:00:30Z'
        seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)


def test_explicit_read_failure_cannot_be_reported_as_complete_empty():
    req,res,owner=advanced_pair(bound=False)
    res['result']['legacy_unbound_observations']=[]
    owner['observation_refs']={}
    res['result']['watermark']['source_watermarks'][1].update(status='read_error',content_sha256=None)
    res['result']['coverage']['status']='unknown'
    res['result']['status']='unavailable'
    seal(req,res)
    validate(req,res,owner)
    res['result']['status']='ok'
    res['result']['coverage']['status']='complete'
    seal(req,res)
    with pytest.raises(ValueError): validate(req,res,owner)
