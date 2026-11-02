"""Ordered model choices extend the original preview, not a new permission system."""
import copy
import sys
from pathlib import Path

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refresh_contract as refresh
from test_refresh_contract import inputs, policy, preview


def targets():
    return [dict(provider='mimo', model='mimo-v2.6-pro', route_id='route1',
                 provider_config_ref='primary', quota_group='group1'),
            dict(provider='mimo', model='mimo-v2.6-flash', route_id='route2',
                 provider_config_ref='secondary', quota_group='group2')]


def ordered_inputs():
    request, state = inputs()
    request['protocol'] = 'iqs.refresh_request/1.6.0'
    request['source_query']['schema_version'] = '2.6.0'
    state['ordered_route_targets'] = targets()
    return request, state


def test_ordered_routes_are_bound_to_original_preview_and_order():
    request, state = ordered_inputs()
    frozen = copy.deepcopy((request, state))
    result = preview(request, state)
    assert result['ordered_route_targets'] == targets()
    assert result['API_requests'] == 0 and not result['dispatch_started']
    refresh.validate_preview(result, request=request, owner_state=state)
    assert (request, state) == frozen
    changed = copy.deepcopy(state)
    changed['ordered_route_targets'][1]['route_id'] = 'other-account'
    with pytest.raises(ValueError):
        refresh.validate_preview(result, request=request, owner_state=changed)


def test_owner_routes_start_at_exact_primary_and_have_unique_accounts(tmp_path):
    value = policy(tmp_path)
    value.update(protocol='stockwiki.refresh_owner_policy/1.6.0', ordered_route_targets=targets())
    value['qa']['quote_schema_version'] = '1.6.0'
    assert refresh.validate_policy(value) == value
    for mutation in ('reverse', 'duplicate', 'alias', 'model', 'extra'):
        changed = copy.deepcopy(value)
        if mutation == 'reverse':
            changed['ordered_route_targets'].reverse()
        elif mutation == 'duplicate':
            changed['ordered_route_targets'].append(copy.deepcopy(targets()[0]))
        elif mutation == 'extra':
            changed['ordered_route_targets'][0]['confirmed'] = True
        else:
            changed['ordered_route_targets'][0][
                'provider_config_ref' if mutation == 'alias' else 'model'] = 'wrong'
        with pytest.raises(ValueError):
            refresh.validate_policy(changed)


def test_old_single_model_contract_does_not_gain_route_fallback():
    request, state = inputs()
    original = preview(request, state)
    assert 'ordered_route_targets' not in original
    state['ordered_route_targets'] = targets()
    with pytest.raises(ValueError):
        preview(request, state)


@pytest.mark.parametrize('fault', ['empty', 'duplicate_id', 'duplicate_target', 'invalid_value'])
def test_standalone_targets_validator_rejects_ambiguous_order(fault):
    selected = targets()
    if fault == 'empty': selected = []
    elif fault == 'duplicate_id': selected[1]['route_id'] = selected[0]['route_id']
    elif fault == 'duplicate_target': selected.append(dict(selected[0], route_id='route3'))
    else: selected[1]['quota_group'] = ''
    with pytest.raises(ValueError):
        refresh.validate_route_targets(selected)
