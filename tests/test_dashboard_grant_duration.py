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
