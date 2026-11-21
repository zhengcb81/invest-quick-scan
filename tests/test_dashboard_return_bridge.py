"""CROSS-ID-DASHBOARD-RETURN: the dual-workspace return mapping verifier.

The verifier confirms an original-business return address only when the two
StockWiki workspaces resolve the business and r25 entities to the SAME
issuer coordinates and listing credentials (both verified, both actively
listed, same NFKC canonical name). Every other outcome is a named
non-confirmation that keeps the readable payload intact. The bridge call is
substituted with a fake runner: no real workspace, no network, no writes.
"""
from pathlib import Path
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dashboard_return_bridge import (
    BRIDGE_SCHEMA,
    REASON_BUSINESS_LISTING_UNSELECTED,
    REASON_BUSINESS_UNRESOLVED,
    REASON_BUSINESS_UNVERIFIED,
    REASON_COORDINATES_MISMATCH,
    REASON_NAME_MISMATCH,
    REASON_NOT_CONFIGURED,
    REASON_R25_NO_ACTIVE_LISTING,
    REASON_R25_UNRESOLVED,
    REASON_R25_UNVERIFIED,
    REASON_UNAVAILABLE,
    ReturnBridge,
    parse_return_scope,
)


AMEC_BUSINESS = 'ENT_a74f8604-6e43-482f-8e91-bdd4518d5eef'
AMEC_BUSINESS_LISTING = 'LST_c1e34bdb-fd78-48d6-b2c5-da6eba4b44b0'
AMEC_R25 = 'ENT_99deceb6-f58a-48b1-bd6b-437621015d76'
AMEC_R25_LISTING = 'LST_4b1d9b36-f70b-4c7b-b107-4ceb5bfa1b59'
RETURN_URL = (f'http://127.0.0.1:48766/company/{AMEC_BUSINESS}'
              f'/quickscan?listing_id={AMEC_BUSINESS_LISTING}')


def _reply(entity_id, name, listing_id, ticker='688012', mic='XSHG', currency='CNY',
           market='CN', status='resolved', identity_state='verified', listing_status='active'):
    listing = {'currency': currency, 'entity_id': entity_id, 'exchange_mic': mic,
               'listing_id': listing_id, 'listing_status': listing_status, 'market': market,
               'ticker': ticker}
    return {'schema_version': BRIDGE_SCHEMA, 'authority': 'stockwiki', 'command': 'resolve',
            'resolution_status': status, 'entity_id': entity_id,
            'listing_scope': 'explicit_listing_selected', 'selected_listing_id': listing_id,
            'lookup_receipt_sha256': 'a' * 64,
            'entity': {'entity_id': entity_id, 'canonical_name': name,
                       'identity_state': identity_state, 'listings': [listing]}}


class FakeRunner:
    """Scripted subprocess stand-in recording the argv it was handed."""

    def __init__(self, replies):
        # replies: list of (returncode, stdout) consumed per call
        self.replies = list(replies)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if not self.replies:
            raise AssertionError('unexpected extra bridge call')
        returncode, stdout = self.replies.pop(0)
        return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr='')


def _bridge(tmp_path, replies):
    config = {'stockwiki_root': str(tmp_path / 'stockwiki'),
              'stockwiki_python': str(tmp_path / 'python.exe'),
              'workspace_root': str(tmp_path / 'r25-workspace'),
              'return_bridge_workspace_root': str(tmp_path / 'business-workspace'),
              'timeout_seconds': 30}
    runner = FakeRunner(replies)
    return ReturnBridge(config, runner=runner), runner


def _write_cli_roots(tmp_path):
    (tmp_path / 'stockwiki').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'stockwiki' / 'dashboard_identity_bridge_cli.py').write_text('', encoding='utf8')
    (tmp_path / 'python.exe').write_text('', encoding='utf8')


def test_parse_return_scope_extracts_the_business_scope():
    scope = parse_return_scope(RETURN_URL)
    assert scope == {'entity_id': AMEC_BUSINESS, 'listing_id': AMEC_BUSINESS_LISTING,
                     'analysis_subject_id': None}
    scope = parse_return_scope(
        f'http://localhost:48766/company/{AMEC_BUSINESS}/quickscan'
        f'?listing_id={AMEC_BUSINESS_LISTING}&analysis_subject_id=SUBJ_1')
    assert scope['analysis_subject_id'] == 'SUBJ_1'
    # a malformed listing id degrades to "no listing scope", never a fuzzy one
    scope = parse_return_scope(f'http://127.0.0.1:1/company/{AMEC_BUSINESS}/quickscan?listing_id=bad id')
    assert scope['listing_id'] is None and scope['entity_id'] == AMEC_BUSINESS
    # only absolute company URLs carry a verifiable scope: hash forms and
    # non-company paths are refused (the verifier is never handed them by the
    # service gate, and would refuse them here too)
    for bad in (None, 42, '', 'http://127.0.0.1:1/results', 'http://127.0.0.1:1/company/../x',
                '#/company/ENT_X/quickscan'):
        assert parse_return_scope(bad) is None


def test_verify_confirms_the_same_issuer_and_listing(tmp_path):
    """Business + r25 resolves to equal coordinates and NFKC-equal names."""
    _write_cli_roots(tmp_path)
    # full-width vs half-width parens: NFKC folds them to the same name
    bridge, runner = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(_reply(AMEC_BUSINESS, '中微半导体设备（上海）股份有限公司', AMEC_BUSINESS_LISTING), ensure_ascii=False)),
    ])
    verdict = bridge.verify(AMEC_R25, RETURN_URL)
    assert verdict['confirmed'] is True and verdict['reason'] is None
    assert verdict['detail']['r25_listing_id'] == AMEC_R25_LISTING
    assert verdict['detail']['confirmed_listing_coordinates'] == ['CN', 'XSHG', '688012', 'CNY']
    assert len(runner.calls) == 2
    r25_argv, r25_kwargs = runner.calls[0]
    business_argv, business_kwargs = runner.calls[1]
    assert f'--root' in ' '.join(r25_argv) and AMEC_R25 in r25_argv
    assert AMEC_R25_LISTING not in r25_argv, 'the r25 side resolves the entity, not one listing'
    assert AMEC_BUSINESS in business_argv and AMEC_BUSINESS_LISTING in business_argv
    assert business_kwargs['cwd'] == str(tmp_path / 'stockwiki')


def test_verify_refuses_mismatched_listing_coordinates(tmp_path):
    """A wrong listing (here: another exchange's ticker) never confirms."""
    _write_cli_roots(tmp_path)
    bridge, _ = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(_reply(AMEC_BUSINESS, '中微半导体设备（上海）股份有限公司', AMEC_BUSINESS_LISTING,
                              ticker='688999'), ensure_ascii=False)),
    ])
    verdict = bridge.verify(AMEC_R25, RETURN_URL)
    assert verdict == {'confirmed': False, 'reason': REASON_COORDINATES_MISMATCH,
                       'detail': verdict['detail']}
    assert verdict['detail']['business_entity_id'] == AMEC_BUSINESS


def test_verify_refuses_a_different_issuer_name(tmp_path):
    _write_cli_roots(tmp_path)
    bridge, _ = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(_reply(AMEC_BUSINESS, '另一家同名坐标公司', AMEC_BUSINESS_LISTING), ensure_ascii=False)),
    ])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_NAME_MISMATCH


def test_verify_refuses_when_the_returned_listing_is_not_the_selected_one(tmp_path):
    """`--listing-id` must come back as the bridge's explicit selection."""
    _write_cli_roots(tmp_path)
    other_listing = 'LST_00000000-0000-0000-0000-000000000000'
    bridge, runner = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(_reply(AMEC_BUSINESS, '中微半导体设备(上海)股份有限公司', other_listing), ensure_ascii=False)),
    ])
    verdict = bridge.verify(AMEC_R25, RETURN_URL)
    assert verdict['reason'] == REASON_BUSINESS_LISTING_UNSELECTED
    # the requested listing id was still handed to the bridge verbatim
    assert AMEC_BUSINESS_LISTING in runner.calls[1][0]


def test_verify_reports_each_side_without_an_active_listing(tmp_path):
    _write_cli_roots(tmp_path)
    inactive = _reply(AMEC_BUSINESS, '中微半导体设备(上海)股份有限公司', AMEC_BUSINESS_LISTING,
                      listing_status='delisted')
    bridge, _ = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING,
                              listing_status='delisted'), ensure_ascii=False)),
    ])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_R25_NO_ACTIVE_LISTING
    bridge, _ = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(inactive, ensure_ascii=False)),
    ])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_BUSINESS_LISTING_UNSELECTED


def test_verify_reports_unresolved_and_unverified_identity(tmp_path):
    _write_cli_roots(tmp_path)
    unresolved = _reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING, status='no_match')
    unresolved.pop('entity')
    bridge, _ = _bridge(tmp_path, [(0, json.dumps(unresolved, ensure_ascii=False))])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_R25_UNRESOLVED
    unverified = _reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING,
                        identity_state='provisional')
    bridge, _ = _bridge(tmp_path, [(0, json.dumps(unverified, ensure_ascii=False))])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_R25_UNVERIFIED
    bridge, _ = _bridge(tmp_path, [
        (0, json.dumps(_reply(AMEC_R25, '中微半导体设备(上海)股份有限公司', AMEC_R25_LISTING), ensure_ascii=False)),
        (0, json.dumps(_reply(AMEC_BUSINESS, '中微半导体设备(上海)股份有限公司', AMEC_BUSINESS_LISTING,
                              identity_state='provisional'), ensure_ascii=False)),
    ])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_BUSINESS_UNVERIFIED


def test_verify_without_configuration_degrades_without_calls(tmp_path):
    config = {'stockwiki_root': '', 'stockwiki_python': '', 'workspace_root': '',
              'return_bridge_workspace_root': ''}
    bridge = ReturnBridge(config)
    verdict = bridge.verify(AMEC_R25, RETURN_URL)
    assert verdict['confirmed'] is False and verdict['reason'] == REASON_NOT_CONFIGURED


def test_verify_degrades_on_bridge_transport_failures(tmp_path):
    _write_cli_roots(tmp_path)
    bridge, runner = _bridge(tmp_path, [(2, json.dumps({'error_code': 'entity_not_found'},
                                                       ensure_ascii=False))])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_UNAVAILABLE
    assert runner.calls[0][0][0].endswith('python.exe')
    bridge, _ = _bridge(tmp_path, [])
    bridge._runner = lambda *a, **k: (_ for _ in ()).throw(OSError('no exec'))
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_UNAVAILABLE
    bridge, _ = _bridge(tmp_path, [(0, 'not json')])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_UNAVAILABLE
    bridge, _ = _bridge(tmp_path, [(0, json.dumps({'schema_version': 'other/1'}))])
    assert bridge.verify(AMEC_R25, RETURN_URL)['reason'] == REASON_UNAVAILABLE


def test_verify_never_raises_and_names_an_unparseable_return(tmp_path):
    _write_cli_roots(tmp_path)
    bridge, _ = _bridge(tmp_path, [])
    for bad in (None, 42, '', 'http://127.0.0.1:1/not-company'):
        verdict = bridge.verify(AMEC_R25, bad)
        assert verdict['confirmed'] is False
        assert verdict['reason'] in {REASON_NOT_CONFIGURED, REASON_BUSINESS_UNRESOLVED}
