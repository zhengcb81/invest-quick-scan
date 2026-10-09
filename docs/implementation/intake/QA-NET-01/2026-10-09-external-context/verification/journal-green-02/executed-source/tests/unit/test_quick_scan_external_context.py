"""External retrieval safety regressions before enabling the production path.

Only synthetic provider data and private pytest paths are used. These assert
behavior of existing functions, so RED is a product gap, not a missing import.
"""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest

from src.config.quick_scan_search_policy import SearchPolicyRejected, load_search_policy
from src.providers.external_search_parsers import unwrap_json_text
from src.providers.search_capability import verify_evidence_binding
from src.utils.quick_scan_evidence import build_evidence_package
from tests.unit.test_qa_net01_search_boundary import _policy_document
from tests.unit.test_quick_scan_work_store import _created, _store
from src.utils.quick_scan_work_store import BudgetAdmissionError, LeaseFencedError, WorkConflictError


def _policy(tmp_path, monkeypatch, mutate):
    monkeypatch.setenv("BRAVE_API_KEY", "synthetic-test-only")
    document = _policy_document()
    mutate(document)
    path = tmp_path / "search-policy.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return load_search_policy(path)


@pytest.mark.parametrize("reference", [None, "", "   "])
def test_confirmed_storage_requires_a_nonempty_entitlement_reference(tmp_path, monkeypatch, reference):
    policy = _policy(tmp_path, monkeypatch, lambda d: d["external_routes"][0]["storage_rights"].update(entitlement_ref=reference))
    assert policy.admitted == ()
    assert any(r["reason"] == "storage_rights_unconfirmed" for r in policy.rejections)


@pytest.mark.parametrize("field", ["selection", "retrieval", "budget"])
def test_unknown_execution_fields_cannot_be_silently_ignored(tmp_path, monkeypatch, field):
    with pytest.raises(SearchPolicyRejected):
        _policy(tmp_path, monkeypatch, lambda d: d[field].update(future_unapproved_override=True))


@pytest.mark.parametrize("raw", ['{"results": [], "results": [1]}', '{"results": [], "value": NaN}', '{"results": [], "value": 1e400}'])
def test_ambiguous_or_nonfinite_search_json_is_refused(raw):
    with pytest.raises(ValueError):
        unwrap_json_text(raw)


def test_object_input_does_not_bypass_search_response_byte_bound():
    with pytest.raises(ValueError):
        unwrap_json_text({"results": [{"snippet": "x" * 4096}]}, max_bytes=1024)


def test_query_target_alone_does_not_certify_a_candidate_company():
    package = build_evidence_package(
        [{"url": "https://example.com/another-issuer", "title": "Other issuer", "snippet": "Other issuer has margins of 99%", "published_at": "2026-10-01", "query": "target margins"}],
        entity_id="ENT_target", as_of="2026-10-08", retrieved_at="2026-10-08T12:00:00Z",
        adapter_version="fixture/1", request_id="search-1", query_bindings={"target margins": ["IQS_01"]}, question_ids=["IQS_01"],
    )
    assert not any(e["eligible"] for e in package["entries"])
    assert package["question_context"]["IQS_01"]["sources"] == []


def test_entity_and_question_must_be_bound_by_the_same_evidence_entry():
    verdict = verify_evidence_binding(
        [{"entity_id": "ENT_target", "question_ids": ["other"], "published_at": "2026-10-01"},
         {"entity_id": "ENT_other", "question_ids": ["IQS_01"], "published_at": "2026-10-01"}],
        entity_id="ENT_target", question_ids=["IQS_01"], as_of="2026-10-08",
    )
    assert verdict.ok is False


def test_company_limit_bounds_retained_evidence_not_only_selected_snippets():
    candidates = [{"url": f"https://example.com/{i}", "entity_id": "ENT_target", "title": "T" * 500, "snippet": "S" * 500, "publisher": "P" * 100, "published_at": "2026-10-01", "query": "target margins"} for i in range(20)]
    package = build_evidence_package(candidates, entity_id="ENT_target", as_of="2026-10-08", retrieved_at="2026-10-08T12:00:00Z", adapter_version="fixture/1", request_id="search-1", query_bindings={"target margins": ["IQS_01"]}, question_ids=["IQS_01"], company_limit=1200)
    retained = sum(len(e.get("title") or "") + len(e.get("short_snippet") or "") + len(e.get("publisher") or "") for e in package["entries"])
    assert retained <= 1200
    assert package["stats"]["context_chars"] <= 1200


def _journal_budget():
    return {
        "configured": True, "policy_id": "external-fixture-budget", "policy_version": "fixture/1",
        "budget": {"currency": "USD", "max_cost": 25, "max_requests": 10, "max_cost_per_attempt": 1},
        "dispatch": {"max_in_flight_total": 2},
        "cost_policy": {"pricing_basis": "verified_rate_card", "pricing_ref": "synthetic-pricing/1", "reserve_before_dispatch": True, "unknown_actual_cost_action": "retain_reservation_and_pause"},
        "quota_groups": [{"id": "search", "max_in_flight": 1}],
        "routes": [{"id": "brave-primary", "quota_group": "search", "provider_config_ref": "brave", "model": "external_retrieval_v1", "max_in_flight": 1}],
    }


def _journal_plan():
    # Explicit synthetic identity-domain proof, never StockWiki owner golden.
    return {
        "schema_version": "quick_scan_external_plan/1.0.0",
        "entity_id": "ENT_BYD", "identity_snapshot_sha256": "a" * 64,
        "question_manifest_sha256": "d" * 64, "question_ids": ["IQS_05"],
        "query_id": "margins", "query": "Synthetic issuer margin",
        "information_as_of": "2026-10-08", "locale": "en-US",
        "ttl_seconds": 300, "top_k": 3, "company_limit": 30000, "snippet_limit": 500,
        "entity_domain_bindings": [{"host": "fixture.example", "source_ref": "operator-synthetic-fixture/1", "identity_snapshot_sha256": "a" * 64}],
    }


def _begin_search(store, item, lease, *, consume=True, **changes):
    args = dict(policy=_journal_budget(), plan=_journal_plan(), route_id="brave-primary",
                provider="brave", quota_group="search", adapter_version="stockqa.external_retrieval/1.0.0",
                search_policy_sha256="e" * 64, endpoint="https://api.search.brave.com/res/v1/web/search")
    args.update(changes)
    operation = store.begin_external_search(item["work_item_id"], lease, **args)
    if consume and operation["send_required"]:
        # Exercise the actual durable boundary; no HTTP is sent by this fixture.
        store.consume_external_search(operation["operation_id"], budget_attempt_id=operation["budget_attempt_id"])
    return operation


def _search_receipt(operation, **changes):
    value = {
        "origin": "external", "adapter_version": "stockqa.external_retrieval/1.0.0",
        "route_id": "brave-primary", "route_kind": "brave", "attempt_id": operation["budget_attempt_id"],
        "http_request_count": 1, "http_status_code": 200, "request_id": "header-search-id",
        "outcome": "response_available", "response_body_sha256": "f" * 64,
        "parse_status": "ok", "provider_result_count": 1,
        "entries": [{"url": "https://fixture.example/ir", "title": "Synthetic issuer", "snippet": "Margin disclosure", "publisher": "Synthetic IR", "published_at": "2026-10-01", "query": "Synthetic issuer margin"}],
    }
    value.update(changes)
    return value


def _journal(tmp_path):
    clock = [1_800_000_000.0]
    store = _store(tmp_path, clock)
    item = _created(store)
    lease = store.claim(item["work_item_id"], lease_seconds=60)
    return store, item, lease, clock


def test_search_intent_and_budget_are_linked_before_http_without_answer_attempt(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    assert op["send_required"] is True
    reopened = type(store)(store.path)
    saved = reopened.get_external_search(op["operation_id"])
    assert saved["budget"]["work_attempt_id"] is None
    assert saved["budget"]["status"] == "in_flight"
    assert saved["plan"] == _journal_plan() and saved["result"] is None
    assert reopened.list_attempts(item["work_item_id"]) == []
    assert reopened.get_quick_scan_budget_status("external-fixture-budget")["requests"] == 1


def test_process_restart_cannot_repeat_an_unresolved_paid_search(tmp_path):
    store, item, lease, clock = _journal(tmp_path)
    _begin_search(store, item, lease)
    clock[0] += 61
    assert store.recover_expired(item["work_item_id"]) == "pending"
    reopened = type(store)(store.path, clock=lambda: clock[0])
    new_lease = reopened.claim(item["work_item_id"], lease_seconds=60)
    with pytest.raises(BudgetAdmissionError, match="external_search_unresolved"):
        _begin_search(reopened, item, new_lease)
    assert reopened.get_quick_scan_budget_status("external-fixture-budget")["requests"] == 1


def test_concurrent_workers_obtain_only_one_search_send_intent(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    def start(_):
        try:
            return _begin_search(store, item, lease)["send_required"]
        except BudgetAdmissionError as error:
            assert error.reason == "external_search_unresolved"
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(start, range(4))) == 1
    assert store.get_quick_scan_budget_status("external-fixture-budget")["requests"] == 1


@pytest.mark.parametrize("change", [{"entity_id": "ENT_OTHER"}, {"identity_snapshot_sha256": "0" * 64}, {"question_ids": ["IQS_99"]}])
def test_search_plan_identity_or_question_mismatch_has_no_reservation(tmp_path, change):
    store, item, lease, _ = _journal(tmp_path)
    plan = _journal_plan()
    plan.update(change)
    with pytest.raises(ValueError):
        _begin_search(store, item, lease, plan=plan)
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0] == 0


def test_sql_failure_rolls_back_search_intent_and_budget_in_the_same_transaction(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("CREATE TRIGGER fail_external_operation BEFORE INSERT ON quick_scan_external_operation BEGIN SELECT RAISE(ABORT,'synthetic disk failure'); END")
        connection.commit()
    with pytest.raises(sqlite3.IntegrityError, match="synthetic disk failure"):
        _begin_search(store, item, lease)
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_external_operation").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_attempt_resolution").fetchone()[0] == 0


def test_search_result_and_settlement_are_atomic_and_exact_replay_is_free(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    receipt = _search_receipt(op)
    result = store.record_external_search(op["operation_id"], receipt=receipt, actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    assert result["budget"]["status"] == "settled" and result["budget"]["actual_cost_micros"] == 4000
    assert store.record_external_search(op["operation_id"], receipt=receipt, actual_cost=0.004, cost_source_ref="synthetic-pricing/1") == result
    before = store.get_quick_scan_budget_status("external-fixture-budget")
    warm = _begin_search(store, item, lease)
    assert warm["send_required"] is False
    assert warm["result"]["receipt"] == receipt
    assert store.get_quick_scan_budget_status("external-fixture-budget") == before
    assert store.list_attempts(item["work_item_id"]) == []
    with pytest.raises(WorkConflictError):
        store.record_external_search(op["operation_id"], receipt=_search_receipt(op, request_id="different"), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")


def test_result_insert_failure_keeps_original_reservation_until_durable_retry(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("CREATE TRIGGER fail_external_result BEFORE INSERT ON quick_scan_external_result BEGIN SELECT RAISE(ABORT,'synthetic result failure'); END")
        connection.commit()
    with pytest.raises(sqlite3.IntegrityError, match="synthetic result failure"):
        store.record_external_search(op["operation_id"], receipt=_search_receipt(op), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    assert store.get_external_search(op["operation_id"])["budget"]["status"] == "in_flight"
    assert store.get_external_search(op["operation_id"])["result"] is None


def test_unpriced_search_success_retains_reservation_and_requires_reconciliation(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    store.record_external_search(op["operation_id"], receipt=_search_receipt(op))
    status = store.get_quick_scan_budget_status("external-fixture-budget")
    assert status["spent_micros"] == 0 and status["reserved_micros"] == 1_000_000
    assert status["unreconciled_attempts"] == 1
    with pytest.raises(BudgetAdmissionError, match="external_search_unresolved"):
        _begin_search(store, item, lease)
    store.reconcile_budget_attempt(op["budget_attempt_id"], resolved_outcome="completed", actual_cost=0.004, cost_source_ref="synthetic-provider-invoice/1")
    assert _begin_search(store, item, lease)["send_required"] is False


def test_timeout_cannot_be_replayed_even_after_zero_cost_unknown_receipt(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    receipt = {"origin": "external", "adapter_version": "stockqa.external_retrieval/1.0.0", "route_id": "brave-primary", "route_kind": "brave", "attempt_id": op["budget_attempt_id"], "http_request_count": 1, "http_status_code": None, "request_id": None, "outcome": "unknown", "failure_type": "TimeoutError"}
    saved = store.record_external_search(op["operation_id"], receipt=receipt, actual_cost=0, cost_source_ref="synthetic-unverified-zero")
    assert saved["budget"]["status"] == "outcome_uncertain"
    assert saved["budget"]["actual_cost_micros"] is None
    with pytest.raises(BudgetAdmissionError, match="external_search_unresolved"):
        _begin_search(store, item, lease)


def test_late_search_reply_retains_billing_without_advancing_a_new_lease(tmp_path):
    store, item, lease, clock = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    clock[0] += 61
    store.recover_expired(item["work_item_id"])
    new_lease = store.claim(item["work_item_id"], lease_seconds=60)
    before = store.get_item(item["work_item_id"])
    saved = store.record_external_search(op["operation_id"], receipt=_search_receipt(op), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    assert saved["result"]["late"] is True
    assert store.get_item(item["work_item_id"]) == before
    assert store.list_attempts(item["work_item_id"]) == []
    with pytest.raises(LeaseFencedError):
        _begin_search(store, item, lease)
    assert _begin_search(store, item, new_lease)["send_required"] is False


@pytest.mark.parametrize("extra", [{"actual_model": "fake-search-model"}, {"web_search_calls": [{"status": "completed"}]}, {"raw_content": "private full page"}])
def test_external_receipt_never_accepts_native_or_raw_document_fields(tmp_path, extra):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    receipt = _search_receipt(op, **extra)
    with pytest.raises(ValueError):
        store.record_external_search(op["operation_id"], receipt=receipt, actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    assert store.get_external_search(op["operation_id"])["result"] is None


def test_external_result_cannot_be_rebound_to_a_different_transport_attempt(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    with pytest.raises(ValueError):
        store.record_external_search(op["operation_id"], receipt=_search_receipt(op, attempt_id="wrong-budget-id"), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    assert store.get_external_search(op["operation_id"])["budget"]["status"] == "in_flight"


def test_expired_search_context_requires_new_generation_instead_of_blind_rerun(tmp_path):
    store, item, lease, clock = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    store.record_external_search(op["operation_id"], receipt=_search_receipt(op), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    clock[0] += 301
    store.recover_expired(item["work_item_id"])
    new_lease = store.claim(item["work_item_id"], lease_seconds=60)
    with pytest.raises(BudgetAdmissionError, match="external_search_stale_generation_required"):
        _begin_search(store, item, new_lease)
    assert store.get_quick_scan_budget_status("external-fixture-budget")["requests"] == 1


@pytest.mark.parametrize("table", ["quick_scan_external_operation", "quick_scan_external_result"])
def test_external_journal_sql_rows_are_immutable(tmp_path, table):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease)
    store.record_external_search(op["operation_id"], receipt=_search_receipt(op), actual_cost=0.004, cost_source_ref="synthetic-pricing/1")
    with closing(sqlite3.connect(store.path)) as connection:
        for command in (f"UPDATE {table} SET operation_id=operation_id", f"DELETE FROM {table}"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(command)


def test_v8_upgrade_preserves_work_and_creates_no_fake_search_history(tmp_path):
    from src.utils import quick_scan_work_store as module
    store, item, _, _ = _journal(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        objects = connection.execute("SELECT type,name FROM sqlite_master WHERE name LIKE 'quick_scan_external_%' AND type='trigger'").fetchall()
        for _, name in objects:
            connection.execute(f"DROP TRIGGER {name}")
        for name in ("quick_scan_external_result", "quick_scan_external_dispatch", "quick_scan_external_operation"):
            connection.execute(f"DROP TABLE {name}")
        connection.execute("PRAGMA user_version=8")
        connection.commit()
    reopened = type(store)(store.path)
    assert module.SCHEMA_VERSION == 9
    assert reopened.get_item(item["work_item_id"])["identity_snapshot_sha256"] == "a" * 64
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 9
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_external_operation").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_external_result").fetchone()[0] == 0


def test_external_dispatch_is_durable_one_use_and_cannot_accept_a_pre_dispatch_reply(tmp_path):
    store, item, lease, _ = _journal(tmp_path)
    op = _begin_search(store, item, lease, consume=False)
    with pytest.raises(WorkConflictError, match="before durable dispatch"):
        store.record_external_search(op["operation_id"], receipt=_search_receipt(op))
    store.consume_external_search(op["operation_id"], budget_attempt_id=op["budget_attempt_id"])
    reopened = type(store)(store.path)
    assert reopened.get_external_search(op["operation_id"])["dispatch"] is not None
    with pytest.raises(WorkConflictError, match="already consumed"):
        reopened.consume_external_search(op["operation_id"], budget_attempt_id=op["budget_attempt_id"])


def test_external_dispatch_rechecks_lease_immediately_before_http(tmp_path):
    store, item, lease, clock = _journal(tmp_path)
    op = _begin_search(store, item, lease, consume=False)
    clock[0] += 61
    with pytest.raises(LeaseFencedError):
        store.consume_external_search(op["operation_id"], budget_attempt_id=op["budget_attempt_id"])
    assert store.get_external_search(op["operation_id"])["dispatch"] is None
