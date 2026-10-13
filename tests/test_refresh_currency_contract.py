"""Explicit currency dialect; synthetic protocol inputs, no execution."""
import copy
import pytest
import refresh_contract as refresh
from test_refresh_contract import inputs,preview


def test_explicit_new_refresh_retains_native_cny_without_conversion():
    request,state=inputs();request['protocol']='iqs.refresh_request/1.1.0'
    request['source_query']['schema_version']='2.6.0';state['quote']['currency']='CNY'
    result=preview(request,state)
    assert result['protocol']=='stockwiki.refresh_preview/1.1.0'
    assert result['quote']==state['quote'] and result['dispatch_started'] is False
    refresh.validate_preview(result,request=request,owner_state=state)
    changed=copy.deepcopy(state);changed['quote']['currency']='USD'
    with pytest.raises(ValueError):refresh.validate_preview(result,request=request,owner_state=changed)


@pytest.mark.parametrize('fault',['cny','new_query','unknown_currency','future_protocol'])
def test_old_dialect_never_silently_accepts_new_currency_or_query(fault):
    request,state=inputs()
    if fault=='cny':state['quote']['currency']='CNY'
    elif fault=='new_query':request['source_query']['schema_version']='2.6.0'
    elif fault=='unknown_currency':
        request['protocol']='iqs.refresh_request/1.1.0';state['quote']['currency']='ZZZ'
    else:request['protocol']='iqs.refresh_request/9.0.0'
    with pytest.raises(ValueError):preview(request,state)
