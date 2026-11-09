"""Synthetic preregistration/profile contract, not an owner golden."""
import copy

import pytest
import subject_dispatch_contract as dc
import query_contract as qc
import test_vendor_http_identity_profile as profile_fixture
from test_query_contract_v2 import SUBJECT

@pytest.fixture(scope='module')
def values():
    profile_fixture.VendorIdentityProfileTests.setUpClass();f=profile_fixture.VendorIdentityProfileTests();obs=f.record()
    obs['entity_id']=SUBJECT['entity_id'];obs['security_id']=None;obs['segment_id']=None;obs['scope']='entity'
    obs['observation_id']='obs_'+qc._digest({k:v for k,v in obs.items() if k!='observation_id'})
    import observation_profiles as profiles
    catalog=profiles._read('schemas/observation-execution-profiles.json')['profiles']['vendor-http-identity-v1']
    profile=dict(profile_id='vendor-http-identity-v1',observation_schema_version='1.2.0',observation_schema_sha256=catalog['schema_sha256'])
    dispatch=dict(protocol='stockwiki.subject_dispatch_request/1.2.0',subject_ref=copy.deepcopy(SUBJECT),
        work_item_id='WORK_SYNTHETIC',work_attempt_id='LOGICAL_SYNTHETIC',work_request_id='REQ_LOCAL_SYNTHETIC',
        execution_attempt_id=obs['execution']['attempt_id'],provider=obs['execution']['provider'],route_provider=obs['execution']['provider'],
        model_requested=obs['execution']['model_requested'],identity_revision=1,question_id=obs['question_id'],field_id=obs['field_id'],
        information_cutoff=obs['information_cutoff'],dispatch_identity_snapshot_sha256='a'*64,dispatch_manifest_sha256='b'*64,
        dispatch_prompt_sha256=obs['execution']['prompt_sha256'],dispatch_work_prompt_sha256='c'*64,
        question_definition_sha256=obs['question_definition_sha256'],question_semantic_sha256=obs['question_semantic_sha256'],
        question_contract=copy.deepcopy(f.fixture.manifest['questions'][0]),execution_profile=profile,
        **{k:obs[k] for k in ('module_package_id','module_release_id','question_version','template_version','method_id')})
    start=obs['execution']['started_at'];now=qc._utc(start)
    from datetime import timedelta
    pre=(now-timedelta(seconds=1)).isoformat().replace('+00:00','Z')
    return dispatch,obs,pre

def receipt(dispatch,pre):
    r=dict(protocol='stockwiki.subject_dispatch_receipt/1.0.0',store_id='SYNTHETIC_STORE',dispatch_request=dispatch,request_sha256=dc.digest(dispatch),registered_at=pre)
    r['receipt_id']='sdr_'+dc.digest(r);return r

def bind(d,o,t):
    r=receipt(d,t);dc.validate_receipt(r,store_id=r['store_id'])
    return dc.bind_original(r,o,payload_sha256=qc._digest(o),observation_sequence=1,ack_sequence=1,bound_at=o['execution']['answered_at'])

def test_explicit_profile_preregister_and_post_binding_keep_null_distinct(values):
    d,o,t=copy.deepcopy(values);assert dc.validate_dispatch_request(d,registered_at=t)==d
    b=bind(d,o,t)
    assert b['protocol']=='stockwiki.observation_subject_binding/1.1.0'
    assert b['execution_request_id'] is None and b['execution_response_id']==o['execution']['response_id']
    assert b['execution_profile']==d['execution_profile']
    for k in ['request_payload_sha256','response_sha256','receipt_sha256']:assert b['execution_'+k]==o['execution'][k]
    assert b['recorded_before_send_at']==t
    assert 'execution_response_id' not in receipt(d,t) # post-answer identity never used as PRE receipt

@pytest.mark.parametrize('field,value',[('profile_id','unknown'),('observation_schema_version','1.1.0'),('observation_schema_sha256','9'*64)])
def test_unknown_or_drifted_profile_is_refused_before_dispatch(values,field,value):
    d,o,t=copy.deepcopy(values);d['execution_profile'][field]=value
    with pytest.raises(ValueError):dc.validate_dispatch_request(d,registered_at=t)

def test_old11_request_cannot_register_new12_answer(values):
    d,o,t=copy.deepcopy(values);d['protocol']='stockwiki.subject_dispatch_request/1.1.0';d.pop('execution_profile')
    dc.validate_dispatch_request(d,registered_at=t)
    with pytest.raises(ValueError):bind(d,o,t)

def test_request12_cannot_silently_bind_legacy11_observation(values):
    d,o,t=copy.deepcopy(values);o['schema_version']='1.1.0';o['execution']['request_id']='SYNTHETIC_header'
    for k in ['response_id','request_payload_sha256','response_sha256','receipt_sha256']:o['execution'].pop(k)
    o['observation_id']='obs_'+qc._digest({k:v for k,v in o.items() if k!='observation_id'})
    with pytest.raises(ValueError):bind(d,o,t)

def test_physical_attempt_mismatch_does_not_bind(values):
    d,o,t=copy.deepcopy(values);o['execution']['attempt_id']='OTHER_PHYSICAL'
    o['observation_id']='obs_'+qc._digest({k:v for k,v in o.items() if k!='observation_id'})
    with pytest.raises(ValueError):bind(d,o,t)


def query_pair(values):
    import test_query_contract_v2 as old
    import query_vendor_contract as vendor
    d,o,t=copy.deepcopy(values);request,response,owner=old.advanced_pair()
    request['schema_version']=response['schema_version']='2.6.0'
    request['payload']['field_ids']=[o['field_id']]
    row=old.projection(o);row['subject_binding']=bind(d,o,t)
    row['observation_wire_profile']='stockwiki-portable-observation/1.1.0'
    response['result']['profiles'][0]['observations']=[row]
    response['result']['coverage'].update(requested_field_ids=[o['field_id']],covered_field_ids=[o['field_id']])
    owner['observation_refs']={o['observation_id']:{**{k:row[k] for k in ['payload_sha256','observation_sequence','ack_sequence','ingest_status','qualification_status']},
        'binding_sha256':qc._digest(row['subject_binding']),'question_contract':d['question_contract']}}
    response=vendor.seal_response(response,request=request)
    return request,response,owner


def test_query26_roundtrip_retains_original_and_explicit_profile(values):
    import query_vendor_contract as vendor
    request,response,owner=query_pair(values)
    vendor.validate_response(response,expected_request=request,expected_owner=owner)
    row=response['result']['profiles'][0]['observations'][0]
    assert vendor.original_observation(row)==values[1]
    assert row['qualification_status']=='review_pending'
    with pytest.raises(ValueError):qc.validate_response(response,expected_request=request,expected_owner=owner)


def test_query26_keeps_legacy_observation_and_rejects_foreign_snapshot():
    from test_query_contract_v2 import advanced_pair, observation
    import query_vendor_contract as vendor

    request, response, owner = advanced_pair()
    request['schema_version'] = response['schema_version'] = '2.6.0'
    response = vendor.seal_response(response, request=request)
    vendor.validate_response(response, expected_request=request, expected_owner=owner)
    row = response['result']['profiles'][0]['observations'][0]
    assert vendor.original_observation(row) == observation()
    request['payload']['snapshot_id'] = 'snap2_' + '9' * 64
    with pytest.raises(ValueError, match='query_requested_snapshot_unavailable'):
        vendor.validate_response(response, expected_request=request, expected_owner=owner)


def test_query26_profile_selection_does_not_replace_raw_hash_validation(values):
    import query_vendor_contract as vendor

    _, response, _ = query_pair(values)
    row = response['result']['profiles'][0]['observations'][0]
    row['raw_sha256'] = '9' * 64
    with pytest.raises(ValueError, match='query_original_observation_invalid'):
        vendor.original_observation(row)


def test_enclosing_contract_cannot_mutate_shared_query_schemas():
    import query_vendor_contract as vendor

    for dialect in (qc, vendor):
        snapshot = dialect.profile_query_schema()
        snapshot['$defs'].clear()
        assert dialect.profile_query_schema()['$defs']


def test_profile_dialects_cannot_use_private_contract_helpers():
    import ast
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[1] / 'scripts'
    contract_modules = {
        'query_contract', 'query_vendor_contract', 'query_pool_contract',
        'query_pool_assessment_contract', 'module_contract',
        'standard_answers', 'observation_profiles', 'query_capabilities_contract',
        'query_pool_scope_contract',
    }
    own_resource_consumers = {
        'query_facts_contract', 'query_capabilities_contract', 'query_capabilities_vendor_contract',
    }
    consumers = (
        'query_contract', 'query_vendor_contract', 'query_contract_cli',
        'query_field_assessment', 'query_research_contract',
        'query_review_lead_contract', 'query_pool_contract',
        'query_pool_assessment_contract', 'query_pool_scope_contract',
        'subject_dispatch_contract', 'subject_dispatch_cli', 'refresh_contract',
    ) + tuple(sorted(own_resource_consumers))
    violations = []
    for name in consumers:
        source = scripts / f'{name}.py'
        tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
        aliases = {
            entry.asname or entry.name
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for entry in node.names if entry.name in contract_modules
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in contract_modules:
                for entry in node.names:
                    if entry.name.startswith('_'):
                        violations.append(f'{source.name}:{node.lineno}: {node.module}.{entry.name}')
            if isinstance(node, ast.Attribute) and (
                node.attr.startswith('_') or (name in own_resource_consumers and node.attr == 'ROOT')
            ):
                reference = ast.unparse(node)
                if reference.split('.', 1)[0] in aliases:
                    violations.append(f'{source.name}:{node.lineno}: {reference}')
    assert not violations, '\n'.join(violations)

@pytest.mark.parametrize('field',['execution_response_id','execution_response_sha256','execution_receipt_sha256','execution_request_payload_sha256'])
def test_query26_self_hashing_binding_does_not_override_owner_or_execution(values,field):
    import query_vendor_contract as vendor
    request,response,owner=query_pair(values)
    binding=response['result']['profiles'][0]['observations'][0]['subject_binding'];binding[field]='9'*64
    # Even a matching presented owner reference cannot replace original execution.
    row=response['result']['profiles'][0]['observations'][0]
    owner['observation_refs'][row['observation_id']]['binding_sha256']=qc._digest(binding)
    response=vendor.seal_response(response,request=request)
    with pytest.raises(ValueError,match='query_vendor_execution_binding_mismatch'):
        vendor.validate_response(response,expected_request=request,expected_owner=owner)


def test_query26_unsupported_wire_profile_does_not_become_empty_coverage(values):
    import query_vendor_contract as vendor
    request,response,owner=query_pair(values);row=response['result']['profiles'][0]['observations'][0]
    row['observation_wire_profile']='stockwiki-portable-observation/1.0.0'
    response=vendor.seal_response(response,request=request)
    with pytest.raises(ValueError):vendor.validate_response(response,expected_request=request,expected_owner=owner)


def test_stockwiki_fixed_cli_preserves_long_explanation_and_extensions(values, tmp_path):
    import os
    from pathlib import Path
    import sys

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root.parent / "StockWiki"))
    from stockwiki.quick_scan_subject_authority import IqsSubjectContract
    from stockwiki.quick_scan_observations import ObservationImportError

    _, observation, _ = copy.deepcopy(values)
    observation["answer"].update(
        summary="Synthetic public explanation. " * 220,
        confidence_rationale={"text": "Partial coverage; synthetic only"},
    )
    observation["observation_id"] = "obs_" + qc._digest(
        {k: v for k, v in observation.items() if k != "observation_id"}
    )
    original = copy.deepcopy(observation)
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "PATH",
        "PATHEXT",
        "COMSPEC",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "SYSTEMDRIVE",
    }
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    contract = IqsSubjectContract(root, runs_dir=tmp_path / "public-cli", process_env=env)
    assert contract.validate_vendor_original(observation) == original
    assert observation == original
    for fault in ("private", "entity", "score"):
        bad = copy.deepcopy(observation)
        if fault == "private":
            bad["answer"]["confidence_rationale"] = {"thinking_content": "SYNTHETIC_PRIVATE"}
        elif fault == "entity":
            bad["answer"]["entity_id"] = "ANOTHER_ISSUER"
        else:
            bad["answer"]["score"] = 11
        bad["observation_id"] = "obs_" + qc._digest(
            {k: v for k, v in bad.items() if k != "observation_id"}
        )
        with pytest.raises(ObservationImportError):
            contract.validate_vendor_original(bad)
    assert not list((tmp_path / "public-cli").iterdir())
