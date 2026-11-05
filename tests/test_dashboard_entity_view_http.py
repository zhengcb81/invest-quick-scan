"""New view negotiates explicitly; original endpoint and read-only behavior preserved."""
from copy import deepcopy
from test_dashboard_http import product,call,Owner


def test_entity_view_http_does_not_change_original_entity(product,monkeypatch):
    original={'entity':{'entity_id':'ENT_FIXTURE'},'groups':[], 'gaps':['fixture_gap']}
    monkeypatch.setattr(Owner,'entity',lambda self,eid:deepcopy(original),raising=False)
    monkeypatch.setattr(Owner,'entity_view',lambda self,eid:{'protocol':'iqs.company_research_view/1.0.0',
        'entity':deepcopy(original),'temporal_shadow':{'protocol':'iqs.temporal_shadow/1.0.0','reuse_authorized':False}},raising=False)
    _,_,root=product
    before=list(root.rglob('*'))
    status,legacy=call(product,path='/api/product/entity?id=ENT_FIXTURE')
    assert status==200
    # B03 LIVE-OWNER-VERIFY-REPAIR-01: the frozen IQSLink declaration now
    # travels with the entity response (G-IQS-01); the original entity facts
    # and the draft track are unchanged. The view comparison therefore strips
    # the declaration before comparing shapes.
    assert 'iqs_link' in legacy['data']
    legacy_without_link={k:v for k,v in legacy['data'].items() if k!='iqs_link'}
    status,actual=call(product,path='/api/product/entity-view?id=ENT_FIXTURE')
    assert status==200
    assert actual['data']['entity']==legacy_without_link
    assert actual['data']['temporal_shadow']['reuse_authorized'] is False
    assert list(root.rglob('*'))==before


def test_entity_view_requires_registered_identifier_at_native_gateway_boundary(product):
    status,actual=call(product,path='/api/product/entity-view')
    assert status==400 and actual['error']['code']=='entity_required'
