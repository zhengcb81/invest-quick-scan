"""Finite deployment-controlled grant duration; no owner writes or network."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dashboard_service import ProductError, validate_config
from scripts import dashboard_prepare as prepare


def test_duration_is_optional_bounded_and_does_not_change_worker_timeouts(tmp_path):
    config = validate_config({'prepare': {'delegation_ttl_seconds': 14400}}, tmp_path)
    assert config['prepare']['delegation_ttl_seconds'] == 14400
    assert prepare._delegation_ttl_seconds(config) == 14400
    assert prepare._delegation_ttl_seconds({}) == 3600
    assert prepare._timeouts(config) == (900, 300)


@pytest.mark.parametrize('bad', [True, False, 0, -1, 899, 86401, 3600.0, '14400', None])
def test_bad_duration_rejected_before_native_owner_write(tmp_path, bad):
    config = {'prepare': {'delegation_ttl_seconds': bad}}
    with pytest.raises(ProductError):
        validate_config(config, tmp_path)
    with pytest.raises(prepare.DashboardPrepareError):
        prepare._timeouts(config)


@pytest.mark.parametrize('value', [900, 3600, 14400, 86400])
def test_native_duration_matches_original_owner_finite_cap(tmp_path, value):
    config = validate_config({'prepare': {'delegation_ttl_seconds': value}}, tmp_path)
    assert prepare._delegation_ttl_seconds(config) == value


def test_future_work_lease_is_separate_from_existing_grants_and_preparation_timeout(tmp_path):
    config = validate_config({'prepare': {'work_lease_seconds': 3600, 'delegation_ttl_seconds': 43200}}, tmp_path)
    assert config['prepare']['work_lease_seconds'] == 3600
    assert prepare._timeouts(config) == (900, 300)
    assert prepare._delegation_ttl_seconds(config) == 43200


@pytest.mark.parametrize('bad', [True, False, 0, -1, 86401, 600.0, '3600', None, float('inf'), float('nan')])
def test_invalid_future_lease_rejected_before_original_prepare(tmp_path, bad):
    with pytest.raises(ProductError):
        validate_config({'prepare': {'work_lease_seconds': bad}}, tmp_path)
    with pytest.raises(prepare.DashboardPrepareError):
        prepare._timeouts({'prepare': {'work_lease_seconds': bad}})
