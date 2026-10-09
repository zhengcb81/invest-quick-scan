"""Independent storage/transport probe. Synthetic owner; no producer/HTTP claim."""
import importlib.util
import json
import os
from pathlib import Path

import pytest

from src.utils.quick_scan_owner_refresh import OwnerRefreshClient, OwnerRefreshSession
from src.utils.quick_scan_work_store import QuickScanWorkStore
from src.utils.quick_scan_work_transport import (
    QuickScanWorkPersistenceError, bind_owner_refresh_guard, bind_quick_scan_budget,
    bind_quick_scan_route, bind_quick_scan_work, begin_quick_scan_send,
)
from tests.unit.test_quick_scan_budget import _policy, _reserve
from tests.unit.test_quick_scan_work_store import _spec
from tests.unit.test_w15_owner_refresh import _binding


def _sw_fixture_module():
    root = Path(os.environ['IQS_W15_OWN'])
    spec = importlib.util.spec_from_file_location('w15_sw_review_fixture', root / 'sw/tests/test_quick_scan_routes.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_changed_during_real_capacity_wait_must_refuse_send(tmp_path, monkeypatch):
    import src.utils.quick_scan_work_transport as transport
    from stockwiki.quick_scan_analysis import receipt_key
    from stockwiki.quick_scan_routes_cli import _public_snapshot, _owner_source_refs

    fixture = _sw_fixture_module()
    owner, subject = fixture._workspace(tmp_path / 'owner')
    routes = fixture._routes(owner)
    subject_key = receipt_key(subject)
    entity_id = subject['primary_issuer_id']
    first_id = second_id = None
    for tag in ('first', 'second'):
        raw, manifest = fixture._raw(owner, subject, tag=tag)
        did = json.loads(raw)['decision_id']
        routes.record_snapshot(raw, manifest, subject_key=subject_key, expected_decision_id=did)
        if tag == 'first':
            first_id = did
        else:
            second_id = did
    routes.set_current(first_id, subject_key=subject_key, expected_current_decision_id=None,
                       now_utc='2026-01-02T12:00:00Z')

    calls = []
    class LiveOwnerAnchor(OwnerRefreshClient):
        def _call(self, operation, extra):
            assert operation == 'anchor'
            calls.append(operation)
            active = routes.get_current_anchor(subject_key=subject_key, scope='entity',
                                               scope_id=entity_id, now_utc=extra[1])
            return dict(expected_decision_id=active['expected_decision_id'],
                        anchor_version=active['anchor_version'],
                        snapshot=_public_snapshot(active['snapshot']),
                        owner_source_binding_refs=_owner_source_refs(routes, active['snapshot']),
                        new_execution_authorized=False)

    client = LiveOwnerAnchor.__new__(LiveOwnerAnchor)
    current = client._call('anchor', ['--now-utc', '2026-10-09T12:00:00Z'])
    session = OwnerRefreshSession(client, current, {'fields': []}, {}, {}, {}, None)
    store = QuickScanWorkStore(tmp_path / 'work.sqlite')
    binding = _binding(entity_id=entity_id, scope_id=entity_id, subject_key=subject_key,
                       identity_revision=1, decision_id=first_id, provider='provider-a1', model='fixture-a')
    row = store.create_or_attach(**_spec(entity_id=entity_id, scope_id=entity_id, identity_revision=1,
                                        generation=2), run_id='RUN_PROBE', scan_id='SCAN_PROBE',
                                owner_refresh_binding=binding)
    lease = store.claim(row['work_item_id'], lease_seconds=300)
    policy = _policy(max_cost=100)
    _reserve(store, policy, 'DISPATCH_busy')
    sleep_calls = []
    def release_capacity_and_change_anchor(seconds):
        sleep_calls.append(seconds)
        routes.set_current(second_id, subject_key=subject_key, expected_current_decision_id=first_id,
                           now_utc='2026-10-09T12:00:00Z')
        store.record_budget_outcome('DISPATCH_busy', outcome='confirmed_failure', http_status_code=429,
                                    actual_cost=0, cost_source_ref='synthetic-review-no-HTTP')
    monkeypatch.setattr(transport.time, 'sleep', release_capacity_and_change_anchor)
    calls.clear()
    raised = None
    handle = None
    with bind_owner_refresh_guard(session.check), bind_quick_scan_work(store, row['work_item_id'], lease), \
         bind_quick_scan_budget(store, policy), bind_quick_scan_route(route_id='route-a1',
             provider='provider-a1', model_requested='fixture-a', quota_group='A'):
        try:
            handle = begin_quick_scan_send('synthetic prompt', 'synthetic system', model_requested='fixture-a')
        except QuickScanWorkPersistenceError as error:
            raised = str(error)
    active = routes.get_current_anchor(subject_key=subject_key, scope='entity', scope_id=entity_id,
                                      now_utc='2026-10-09T12:00:00Z')
    facts = dict(expected_decision_id=first_id, actual_decision_id=active['expected_decision_id'],
                 anchor_checks=len(calls), capacity_waits=len(sleep_calls),
                 attempt_phases=[a['phase'] for a in store.list_attempts(row['work_item_id'])],
                 permit_returned=handle is not None, rejection=raised,
                 real_owner_SQLite=True, real_QA_budget_admission=True,
                 external_IQS_validator='existing UnitValidator storage-boundary substitute',
                 OS_owner_transport='typed substitution; actual SQLite anchor reads', HTTP_calls=0)
    (tmp_path / 'observed.json').write_text(json.dumps(facts, indent=2), encoding='utf-8')
    print(json.dumps(facts, sort_keys=True))
    assert len(sleep_calls) == 1 and active['expected_decision_id'] == second_id
    assert raised is not None and handle is None, 'owner drift during capacity wait returned send permit'
