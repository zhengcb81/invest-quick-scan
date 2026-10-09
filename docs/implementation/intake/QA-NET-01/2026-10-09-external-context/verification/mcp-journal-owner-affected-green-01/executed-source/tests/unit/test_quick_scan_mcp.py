"""MCP control stages over the REAL Q09 store; synthetic data, no HTTP/key.

Not provider interoperability, financial golden or a second budget owner.
Transport/official tool schema tests follow when the adapter is connected.
"""
import json
import sqlite3
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from src.config.quick_scan_search_policy import execution_query_plans
from src.utils.quick_scan_external_context import build_shared_external_budget_policy
from src.utils.quick_scan_work_store import QuickScanWorkStore, BudgetAdmissionError, WorkConflictError
from tests.unit.test_quick_scan_external_context import _coordinator_fixture


def _mcp_fixture(tmp_path, monkeypatch):
    def route(document):
        document["external_routes"][0].update(kind="zai_mcp_streamable", endpoint="https://api.z.ai/api/mcp/web_search_prime/mcp")
    args, session, clock = _coordinator_fixture(tmp_path, monkeypatch, mutate=route)
    request = {
        "policy": build_shared_external_budget_policy(args["model_policy"], args["policy"]),
        "plan": execution_query_plans(args["policy"])[0], "route_id": "brave-primary", "provider": "zai_mcp_streamable",
        "quota_group": "search-brave", "adapter_version": "stockqa.external_retrieval/1.0.0",
        "search_policy_sha256": args["policy"].policy_sha256,
        "endpoint": "https://api.z.ai/api/mcp/web_search_prime/mcp",
    }
    return args, request, session, clock


def _stage(args, request, name):
    return args["store"].begin_mcp_stage(args["work_item_id"], args["lease"], stage=name, **request)


def _control_receipt(stage, *, outcome="response_available", status=200):
    value = {"origin": "external", "adapter_version": "stockqa.external_retrieval/1.0.0",
        "route_id": "brave-primary", "route_kind": "zai_mcp_streamable", "attempt_id": stage["budget_attempt_id"],
        "http_request_count": 1, "http_status_code": status, "request_id": "synthetic-mcp-request",
        "outcome": outcome, "response_body_sha256": "f" * 64}
    if outcome == "response_available":
        value.update(parse_status="ok", provider_result_count=0, entries=[])
    return value


def _finish(args, stage, control, *, cost=Decimal("0.003"), consume=True, status=200):
    if consume:
        args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    return args["store"].record_mcp_stage(stage["stage_id"], receipt=_control_receipt(stage, status=status),
        control=control, actual_cost=cost, cost_source_ref=None if cost is None else "operator-synthetic-pricing/1")


def _initialize(args, request):
    return _finish(args, _stage(args, request, "initialize"),
        {"protocol_version": "2025-03-26", "session_id": "SESSION_SYNTHETIC_ONLY"})


def test_mcp_control_intent_and_q09_reservation_are_atomic_before_send(tmp_path, monkeypatch):
    args, request, session, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    saved = args["store"].get_mcp_stage(stage["stage_id"])
    assert stage["send_required"] and saved["dispatch"] is None and saved["result"] is None
    assert saved["budget"]["work_attempt_id"] is None and saved["budget"]["model_requested"] == "external_retrieval_v1"
    assert saved["message"]["method"] == "initialize"
    assert saved["message"]["params"]["protocolVersion"] == "2025-03-26"
    assert saved["budget"]["status"] == "in_flight"
    assert args["store"].list_attempts(args["work_item_id"]) == []
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["requests"] == 1
    session.request.assert_not_called()


@pytest.mark.parametrize("name", ["initialized", "discovery"])
def test_mcp_stage_order_cannot_be_forged_before_initialization(tmp_path, monkeypatch, name):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    with pytest.raises(BudgetAdmissionError, match="mcp_parent_not_ready"):
        _stage(args, request, name)
    assert args["store"].list_attempts(args["work_item_id"]) == []
    with closing(args["store"]._connect()) as connection:
        assert connection.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0] == 0


def test_mcp_control_response_cannot_be_accepted_before_actual_dispatch(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    with pytest.raises(WorkConflictError, match="before.*dispatch"):
        _finish(args, stage, {"protocol_version": "2025-03-26", "session_id": None}, consume=False)
    assert args["store"].get_mcp_stage(stage["stage_id"])["result"] is None


def test_mcp_all_three_controls_are_separately_charged_and_reused_after_reopen(tmp_path, monkeypatch):
    args, request, session, clock = _mcp_fixture(tmp_path, monkeypatch)
    first = _initialize(args, request)
    second = _finish(args, _stage(args, request, "initialized"), {"initialized": True}, status=202)
    third = _finish(args, _stage(args, request, "discovery"), {"tool_name": "webSearchPrime", "input_schema_sha256": "a" * 64})
    totals = args["store"].get_quick_scan_budget_status("q09-fixture")
    assert totals["requests"] == 3 and totals["spent_micros"] == 9000 and totals["reserved_micros"] == 0
    args["store"] = QuickScanWorkStore(args["store"].path, clock=lambda: clock[0])
    for name, before in zip(("initialize", "initialized", "discovery"), (first, second, third)):
        after = _stage(args, request, name)
        assert after["send_required"] is False
        assert {k: v for k, v in after.items() if k != "send_required"} == before
    binding = args["store"].get_mcp_binding(first["sequence_key"])
    assert binding["protocol_version"] == "2025-03-26" and binding["session_id"] == "SESSION_SYNTHETIC_ONLY"
    assert binding["stage_ids"] == [r["stage_id"] for r in (first, second, third)]
    assert args["store"].get_quick_scan_budget_status("q09-fixture") == totals
    session.request.assert_not_called()


def test_mcp_unknown_control_holds_reservation_and_blocks_next_stage_without_replay(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    args["store"].record_mcp_stage(stage["stage_id"], receipt=_control_receipt(stage, outcome="unknown", status=None), control=None)
    with pytest.raises(BudgetAdmissionError, match="mcp_control_unresolved"):
        _stage(args, request, "initialize")
    with pytest.raises(BudgetAdmissionError, match="mcp_parent_not_ready"):
        _stage(args, request, "initialized")
    totals = args["store"].get_quick_scan_budget_status("q09-fixture")
    assert totals["requests"] == 1 and totals["reserved_micros"] == 6_000_000


def test_mcp_missing_control_price_cannot_advance_even_with_valid_protocol(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    _finish(args, _stage(args, request, "initialize"), {"protocol_version": "2025-03-26", "session_id": None}, cost=None)
    with pytest.raises(BudgetAdmissionError, match="mcp_parent_not_ready"):
        _stage(args, request, "initialized")
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["reserved_micros"] > 0


def test_mcp_two_handles_can_consume_only_one_durable_send_permit(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    first = _stage(args, request, "initialize")
    second = _stage(args, request, "initialize")
    assert first["stage_id"] == second["stage_id"] and first["budget_attempt_id"] == second["budget_attempt_id"]
    def consume():
        try:
            args["store"].consume_mcp_stage(first["stage_id"], budget_attempt_id=first["budget_attempt_id"])
            return "sent"
        except WorkConflictError:
            return "fenced"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: consume(), range(2)))
    assert sorted(results) == ["fenced", "sent"]
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["requests"] == 1


def test_mcp_result_and_budget_settlement_roll_back_together_on_save_failure(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    with closing(args["store"]._connect()) as connection:
        connection.execute("CREATE TRIGGER synthetic_mcp_save_failure BEFORE INSERT ON quick_scan_mcp_result BEGIN SELECT RAISE(ABORT,'synthetic mcp save failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="synthetic mcp save failure"):
        _finish(args, stage, {"protocol_version": "2025-03-26", "session_id": None}, consume=False)
    saved = args["store"].get_mcp_stage(stage["stage_id"])
    assert saved["result"] is None and saved["budget"]["status"] == "in_flight"
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["spent_micros"] == 0


@pytest.mark.parametrize("command", ["UPDATE quick_scan_mcp_result SET control_sha256=control_sha256", "DELETE FROM quick_scan_mcp_stage"])
def test_mcp_control_rows_are_immutable(tmp_path, monkeypatch, command):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    first = _initialize(args, request)
    with closing(args["store"]._connect()) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(command)
    assert args["store"].get_mcp_stage(first["stage_id"]) == first


def test_mcp_session_and_control_hash_corruption_cannot_create_a_binding(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    first = _initialize(args, request)
    with closing(args["store"]._connect()) as connection:
        connection.execute("DROP TRIGGER quick_scan_mcp_result_no_update")
        connection.execute("UPDATE quick_scan_mcp_result SET control_json=?", (json.dumps({"protocol_version": "2025-03-26", "session_id": "SESSION_FOREIGN"}),))
    with pytest.raises(ValueError, match="MCP.*binding|MCP.*hash"):
        args["store"].get_mcp_stage(first["stage_id"])


def test_observed_but_unknown_control_is_not_reusable_even_when_price_settled(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    args["store"].record_mcp_stage(stage["stage_id"], receipt=_control_receipt(stage, outcome="unknown", status=503),
                                 control=None, actual_cost=Decimal("0.003"), cost_source_ref="operator-synthetic-pricing/1")
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["spent_micros"] == 3000
    with pytest.raises(BudgetAdmissionError, match="mcp_control_unresolved"):
        _stage(args, request, "initialize")


def test_unknown_mcp_also_blocks_fresh_search_route_before_any_new_reservation(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    args["store"].record_mcp_stage(stage["stage_id"], receipt=_control_receipt(stage, outcome="unknown", status=None), control=None)
    with pytest.raises(BudgetAdmissionError, match="mcp_control_unresolved"):
        args["store"].begin_external_search(args["work_item_id"], args["lease"], **request)
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["requests"] == 1


@pytest.mark.parametrize("field,sql_value", [("lease_epoch", "lease_epoch+1"), ("created_at", "created_at+1")])
def test_mcp_frozen_owner_and_creation_time_are_bound_to_metadata(tmp_path, monkeypatch, field, sql_value):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    with closing(args["store"]._connect()) as connection:
        connection.execute("DROP TRIGGER quick_scan_mcp_stage_no_update")
        connection.execute(f"UPDATE quick_scan_mcp_stage SET {field}={sql_value}")
    with pytest.raises(ValueError, match="MCP.*binding"):
        args["store"].get_mcp_stage(stage["stage_id"])


@pytest.mark.parametrize("control", [
    {"protocol_version": "2024-11-05", "session_id": None},
    {"protocol_version": "2025-03-26", "session_id": "bad\r\nheader"},
    {"protocol_version": "2025-03-26", "session_id": ""},
    {"protocol_version": "2025-03-26", "session_id": "x" * 2001},
    {"protocol_version": "2025-03-26", "session_id": "session", "api_key": "synthetic-key"},
])
def test_mcp_invalid_protocol_or_private_session_is_not_persisted_or_settled(tmp_path, monkeypatch, control):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    with pytest.raises(ValueError):
        _finish(args, stage, control, consume=False)
    record = args["store"].get_mcp_stage(stage["stage_id"])
    assert record["result"] is None and record["budget"]["status"] == "in_flight"


def test_mcp_late_control_keeps_known_cash_but_cannot_advance_protocol(tmp_path, monkeypatch):
    args, request, _, clock = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    clock[0] += 61
    result = _finish(args, stage, {"protocol_version": "2025-03-26", "session_id": None}, consume=False)
    assert result["result"]["late"] is True
    assert args["store"].recover_expired(args["work_item_id"]) == "pending"
    args["lease"] = args["store"].claim(args["work_item_id"], lease_seconds=60)
    assert args["lease"] is not None
    with pytest.raises(BudgetAdmissionError, match="mcp_parent_not_ready"):
        _stage(args, request, "initialized")
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["spent_micros"] == 3000


def test_mcp_paid_rejection_is_cached_as_failure_without_resend(tmp_path, monkeypatch):
    args, request, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    stage = _stage(args, request, "initialize")
    args["store"].consume_mcp_stage(stage["stage_id"], budget_attempt_id=stage["budget_attempt_id"])
    first = args["store"].record_mcp_stage(stage["stage_id"], receipt=_control_receipt(stage, outcome="confirmed_failure", status=401),
                                        control=None, actual_cost=Decimal("0.003"), cost_source_ref="operator-synthetic-pricing/1")
    after = _stage(args, request, "initialize")
    assert not after["send_required"] and after["result"] == first["result"]
    with pytest.raises(BudgetAdmissionError, match="mcp_parent_not_ready"):
        _stage(args, request, "initialized")
    assert args["store"].get_quick_scan_budget_status("q09-fixture")["requests"] == 1


def _install_real_v12(store):
    with closing(store._connect()) as connection, connection:
        for table in ("quick_scan_mcp_result", "quick_scan_mcp_dispatch", "quick_scan_mcp_stage"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("PRAGMA user_version=12")


def test_v12_upgrade_keeps_actual_http_events_cash_and_creates_no_control_history(tmp_path, monkeypatch):
    from tests.unit.test_quick_scan_external_context import _native_event_answer
    from src.utils.quick_scan_work_store import SCHEMA_VERSION
    args, _, attempt_id, search, sync, clock = _native_event_answer(tmp_path, monkeypatch)
    _install_real_v12(args["store"])
    before_response = args["store"].get_attempt_response(attempt_id)
    before_cash = args["store"].get_quick_scan_budget_status("q09-fixture")
    with closing(args["store"]._connect()) as connection:
        before_events = [tuple(row) for row in connection.execute("SELECT * FROM quick_scan_native_search_events")]
    reopened = QuickScanWorkStore(args["store"].path, clock=lambda: clock[0])
    assert reopened.get_attempt_response(attempt_id) == before_response
    assert reopened.get_quick_scan_budget_status("q09-fixture") == before_cash
    with closing(reopened._connect()) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert [tuple(row) for row in connection.execute("SELECT * FROM quick_scan_native_search_events")] == before_events
        for table in ("quick_scan_mcp_result", "quick_scan_mcp_dispatch", "quick_scan_mcp_stage"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert search.request.call_count == sync.post.call_count == 1


def test_v13_migration_interruption_rolls_back_to_exact_v12_schema_and_rows(tmp_path, monkeypatch):
    from src.utils.quick_scan_work_store import SCHEMA_VERSION
    args, _, _, _ = _mcp_fixture(tmp_path, monkeypatch)
    _install_real_v12(args["store"])
    with closing(args["store"]._connect()) as connection:
        original = tuple(connection.iterdump())
    validate = QuickScanWorkStore._validate_schema
    def reject_final(connection, *, schema_version):
        validate(connection, schema_version=schema_version)
        if schema_version == SCHEMA_VERSION:
            raise sqlite3.OperationalError("synthetic MCP migration interruption")
    monkeypatch.setattr(QuickScanWorkStore, "_validate_schema", staticmethod(reject_final))
    with pytest.raises(sqlite3.OperationalError, match="synthetic MCP migration interruption"):
        QuickScanWorkStore(args["store"].path)
    with closing(args["store"]._connect()) as connection:
        assert tuple(connection.iterdump()) == original
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 12
