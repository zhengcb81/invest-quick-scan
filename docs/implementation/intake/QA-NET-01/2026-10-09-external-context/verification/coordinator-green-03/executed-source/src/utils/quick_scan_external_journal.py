"""Private retrieval journal over the existing Q09 transaction/ledger owner.

This is not a second work scheduler or budget store. Search requests have their
own origin and immutable short-data receipts; no search service becomes an LLM
answer attempt. All HTTP sends require a persisted one-use dispatch boundary.
"""
from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from datetime import date
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    import sqlite3
    from src.utils.quick_scan_work_store import Lease, QuickScanWorkStore

MODEL_BUDGET_LABEL = "external_retrieval_v1"  # Internal budget label, never an answer model.
ENDPOINTS = {
    "brave": "https://api.search.brave.com/res/v1/web/search",
    "tavily": "https://api.tavily.com/search",
    "zai_rest": "https://api.z.ai/api/paas/v4/web_search",
    "zai_mcp_streamable": "https://api.z.ai/api/mcp/web_search_prime/mcp",
}

DDL_V9_ADDITIONS = (
    """CREATE TABLE quick_scan_external_operation (
        operation_id TEXT PRIMARY KEY,
        cache_key TEXT NOT NULL UNIQUE CHECK(length(cache_key)=64),
        corpus_key TEXT NOT NULL CHECK(length(corpus_key)=64),
        work_item_id TEXT NOT NULL REFERENCES work_item(work_item_id),
        budget_attempt_id TEXT NOT NULL UNIQUE REFERENCES quick_scan_budget_attempt(budget_attempt_id),
        lease_epoch INTEGER NOT NULL CHECK(lease_epoch>=1),
        lease_token TEXT NOT NULL,
        context_json TEXT NOT NULL,
        context_sha256 TEXT NOT NULL CHECK(length(context_sha256)=64),
        created_at REAL NOT NULL
    )""",
    """CREATE TRIGGER quick_scan_external_operation_insert_guard
        BEFORE INSERT ON quick_scan_external_operation BEGIN
        SELECT RAISE(ABORT,'invalid external search intent') WHERE NOT EXISTS (
            SELECT 1 FROM work_item w,quick_scan_budget_attempt b
            WHERE w.work_item_id=NEW.work_item_id AND w.status='leased'
            AND w.lease_epoch=NEW.lease_epoch AND w.lease_token=NEW.lease_token
            AND w.lease_expires_at>NEW.created_at
            AND b.budget_attempt_id=NEW.budget_attempt_id AND b.work_attempt_id IS NULL
            AND b.model_requested='external_retrieval_v1' AND b.status='in_flight'); END""",
    """CREATE TRIGGER quick_scan_external_operation_no_update BEFORE UPDATE ON quick_scan_external_operation
        BEGIN SELECT RAISE(ABORT,'external operations are immutable'); END""",
    """CREATE TRIGGER quick_scan_external_operation_no_delete BEFORE DELETE ON quick_scan_external_operation
        BEGIN SELECT RAISE(ABORT,'external operations are immutable'); END""",
    """CREATE TABLE quick_scan_external_dispatch (
        operation_id TEXT PRIMARY KEY REFERENCES quick_scan_external_operation(operation_id),
        sent_at REAL NOT NULL
    )""",
    """CREATE TRIGGER quick_scan_external_dispatch_insert_guard BEFORE INSERT ON quick_scan_external_dispatch
        BEGIN SELECT RAISE(ABORT,'invalid external search dispatch') WHERE NOT EXISTS (
            SELECT 1 FROM quick_scan_external_operation o
            JOIN work_item w USING(work_item_id)
            JOIN quick_scan_budget_attempt b USING(budget_attempt_id)
            WHERE o.operation_id=NEW.operation_id AND w.status='leased'
            AND w.lease_epoch=o.lease_epoch AND w.lease_token=o.lease_token
            AND w.lease_expires_at>NEW.sent_at AND b.status='in_flight'); END""",
    """CREATE TRIGGER quick_scan_external_dispatch_no_update BEFORE UPDATE ON quick_scan_external_dispatch
        BEGIN SELECT RAISE(ABORT,'external dispatches are immutable'); END""",
    """CREATE TRIGGER quick_scan_external_dispatch_no_delete BEFORE DELETE ON quick_scan_external_dispatch
        BEGIN SELECT RAISE(ABORT,'external dispatches are immutable'); END""",
    """CREATE TABLE quick_scan_external_result (
        operation_id TEXT PRIMARY KEY REFERENCES quick_scan_external_operation(operation_id),
        receipt_json TEXT NOT NULL,
        receipt_sha256 TEXT NOT NULL CHECK(length(receipt_sha256)=64),
        input_receipt_sha256 TEXT NOT NULL CHECK(length(input_receipt_sha256)=64),
        charge_json TEXT NOT NULL,
        retained_entry_chars INTEGER NOT NULL CHECK(retained_entry_chars>=0),
        entries_retention_truncated INTEGER NOT NULL CHECK(entries_retention_truncated IN (0,1)),
        recorded_at REAL NOT NULL,
        late INTEGER NOT NULL CHECK(late IN (0,1))
    )""",
    """CREATE TRIGGER quick_scan_external_result_insert_guard BEFORE INSERT ON quick_scan_external_result
        BEGIN SELECT RAISE(ABORT,'external result without dispatch and outcome') WHERE NOT EXISTS (
            SELECT 1 FROM quick_scan_external_operation o
            JOIN quick_scan_external_dispatch d USING(operation_id)
            JOIN quick_scan_budget_attempt b USING(budget_attempt_id)
            WHERE o.operation_id=NEW.operation_id AND b.status!='in_flight'); END""",
    """CREATE TRIGGER quick_scan_external_result_no_update BEFORE UPDATE ON quick_scan_external_result
        BEGIN SELECT RAISE(ABORT,'external results are immutable'); END""",
    """CREATE TRIGGER quick_scan_external_result_no_delete BEFORE DELETE ON quick_scan_external_result
        BEGIN SELECT RAISE(ABORT,'external results are immutable'); END""",
)

_PLAN_KEYS = frozenset({"schema_version", "entity_id", "identity_snapshot_sha256", "question_manifest_sha256", "question_ids", "query_id", "query", "information_as_of", "locale", "ttl_seconds", "top_k", "company_limit", "snippet_limit", "entity_domain_bindings"})
_RECEIPT_KEYS = frozenset({"origin", "adapter_version", "route_id", "route_kind", "attempt_id", "http_request_count", "http_status_code", "request_id", "provider_request_id", "usage", "usage_status", "outcome", "response_body_sha256", "parse_status", "provider_result_count", "entries", "provider_error_code", "failure_type"})
_ENTRY_KEYS = frozenset({"url", "title", "snippet", "publisher", "published_at", "query"})
_WORK_KEYS = ("entity_id", "question_id", "generation", "scope", "scope_id", "identity_revision", "source_binding_version", "identity_state", "source_binding_ref", "source_binding_refs_json", "identity_snapshot_sha256", "question_fingerprint", "routing_fingerprint")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def strict_search_json(value: str) -> Any:
    # providers.__init__ imports transport -> work_store. Defer the shared
    # parser import until this store is fully defined, preserving standalone
    # crash/recovery workers without duplicating the strict JSON parser.
    from src.providers.external_search_parsers import strict_search_json as decode

    return decode(value)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _identity_basis(context: dict) -> dict:
    # A query can serve several questions. The manifest binds all question
    # definitions; an individual question id/fingerprint is not a cache key.
    return {key: value for key, value in context["work_fingerprint"].items()
            if key not in {"question_id", "question_fingerprint", "routing_fingerprint", "generation"}}


def _cache_key(context: dict) -> str:
    # Same-generation questions share one query. An explicitly new scan must
    # be able to refresh stale evidence, retaining all earlier fees/history.
    # This schema is still private/unpublished; no production v9 history exists.
    return _digest({"cache_schema": "external_query_cache/1.1.0", "identity": _identity_basis(context),
                    "generation": context["work_fingerprint"]["generation"], "plan": context["plan"],
                    "route": context["route"], "search_policy_sha256": context["search_policy_sha256"],
                    "budget_policy_id": context["budget"]["policy_id"]})


def _corpus_key(context: dict) -> str:
    return _digest({"identity": _identity_basis(context), "generation": context["work_fingerprint"]["generation"],
                    "plan": {key: context["plan"][key] for key in ("question_manifest_sha256", "information_as_of", "company_limit", "snippet_limit", "entity_domain_bindings")},
                    "search_policy_sha256": context["search_policy_sha256"]})


def _text(value: Any, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError("invalid external journal text")
    return value


def _hash(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ValueError("invalid external journal hash")
    return value


def _plan(value: Any) -> dict:
    if not isinstance(value, dict) or set(value) != _PLAN_KEYS or value["schema_version"] not in {"quick_scan_external_plan/1.0.0", "quick_scan_external_plan/1.1.0"}:
        raise ValueError("invalid frozen external plan")
    result = strict_search_json(_canonical(value))
    if re.fullmatch(r"ENT_[A-Za-z0-9_-]+", _text(result["entity_id"], 160)) is None:
        raise ValueError("invalid external plan entity")
    _hash(result["identity_snapshot_sha256"])
    _hash(result["question_manifest_sha256"])
    _text(result["query_id"], 160)
    _text(result["query"], 2000)
    cutoff = result["information_as_of"]
    if not isinstance(cutoff, str) or len(cutoff) != 10 or date.fromisoformat(cutoff).isoformat() != cutoff:
        raise ValueError("invalid external plan cutoff")
    if not isinstance(result["locale"], str) or re.fullmatch(r"[a-z]{2}-[A-Z]{2}", result["locale"]) is None:
        raise ValueError("invalid external plan locale")
    for name, maximum in (("ttl_seconds", 86400 * 30), ("top_k", 10), ("company_limit", 30000), ("snippet_limit", 500)):
        if type(result[name]) is not int or not 1 <= result[name] <= maximum:
            raise ValueError("invalid external plan limit")
    questions = result["question_ids"]
    if not isinstance(questions, list) or not 1 <= len(questions) <= 200 or len(questions) != len(set(_text(q, 160) for q in questions)):
        raise ValueError("invalid external plan questions")
    bindings = result["entity_domain_bindings"]
    if result["schema_version"] == "quick_scan_external_plan/1.1.0":
        # Runtime import preserves standalone store/migration processes.
        from src.config.quick_scan_search_policy import validate_external_domain_bindings

        validate_external_domain_bindings(bindings, result["identity_snapshot_sha256"])
        return result
    if not isinstance(bindings, list) or not 1 <= len(bindings) <= 20:
        raise ValueError("explicit identity-domain binding required")
    hosts = set()
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"host", "source_ref", "identity_snapshot_sha256"}:
            raise ValueError("invalid identity-domain binding")
        host = _text(binding["host"], 253)
        if re.fullmatch(r"[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?)+", host) is None or host in hosts:
            raise ValueError("invalid or duplicate identity-domain host")
        hosts.add(host)
        _text(binding["source_ref"], 300)
        if binding["identity_snapshot_sha256"] != result["identity_snapshot_sha256"]:
            raise ValueError("identity-domain snapshot mismatch")
    return result


def _receipt(value: Any, context: dict, budget_attempt_id: str) -> dict:
    if not isinstance(value, dict) or not set(value) <= _RECEIPT_KEYS:
        raise ValueError("invalid external receipt fields")
    result = strict_search_json(_canonical(value))
    route = context["route"]
    if (result.get("origin") != "external" or result.get("adapter_version") != route["adapter_version"]
        or result.get("route_id") != route["route_id"] or result.get("route_kind") != route["provider"]
        or result.get("attempt_id") != budget_attempt_id or type(result.get("http_request_count")) is not int
        or result["http_request_count"] != 1):
        raise ValueError("external receipt transport binding mismatch")
    status = result.get("http_status_code")
    outcome = result.get("outcome")
    if outcome not in {"response_available", "confirmed_failure", "unknown"}:
        raise ValueError("invalid external receipt outcome")
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError("invalid external receipt HTTP status")
    if outcome == "response_available" and (status is None or not 200 <= status < 300):
        raise ValueError("external success requires a 2xx response")
    if outcome == "confirmed_failure" and (status not in (401, 403, 404, 429)):
        raise ValueError("external failure is not a confirmed rejection")
    if result.get("request_id") is not None:
        _text(result["request_id"], 300)
    if result.get("provider_request_id") is not None:
        _text(result["provider_request_id"], 300)
    if "usage_status" in result or "usage" in result:
        state = result.get("usage_status")
        if route["provider"] != "tavily" or state not in {"missing", "invalid", "reported", "exceeds_verified_bound"}:
            raise ValueError("invalid external usage status")
        usage = result.get("usage")
        if state in {"reported", "exceeds_verified_bound"}:
            if (not isinstance(usage, dict) or set(usage) != {"schema", "unit", "count"}
                or usage["schema"] != "stockqa.external_search_usage/1.0.0" or usage["unit"] != "credits"
                or type(usage["count"]) is not int or not 0 <= usage["count"] <= 9_223_372_036_854_775_807):
                raise ValueError("invalid external observed usage")
        elif "usage" in result:
            raise ValueError("unavailable usage cannot carry observed units")
    if result.get("response_body_sha256") is not None:
        _hash(result["response_body_sha256"])
    if outcome == "response_available":
        _hash(result.get("response_body_sha256"))
        if result.get("parse_status") not in {"ok", "empty", "parse_failure", "business_error"}:
            raise ValueError("invalid external parse status")
        entries = result.get("entries")
        if not isinstance(entries, list) or len(entries) > context["plan"]["top_k"]:
            raise ValueError("invalid external result entry bound")
        if type(result.get("provider_result_count")) is not int or result["provider_result_count"] < len(entries):
            raise ValueError("invalid provider result count")
        for entry in entries:
            if not isinstance(entry, dict) or not set(entry) <= _ENTRY_KEYS:
                raise ValueError("invalid short external entry fields")
            url = urlsplit(_text(entry.get("url"), 2048))
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise ValueError("unsafe external result URL")
            for name in ("title", "snippet", "publisher"):
                text = entry.get(name)
                if text is not None and (not isinstance(text, str) or len(text) > 500):
                    raise ValueError("external result exceeds short-data bound")
            for name, maximum in (("query", 2000), ("published_at", 100)):
                if entry.get(name) is not None:
                    _text(entry[name], maximum)
    elif "entries" in result:
        raise ValueError("failed external transport cannot carry evidence entries")
    for name in ("provider_error_code", "failure_type"):
        if result.get(name) is not None:
            _text(result[name], 160)
    if len(_canonical(result).encode("utf-8")) > 60000:
        raise ValueError("external result journal exceeds short-data cap")
    return result


def read_record(connection: "sqlite3.Connection", row: "sqlite3.Row") -> dict:
    context = strict_search_json(row["context_json"])
    if _canonical(context) != row["context_json"] or _digest(context) != row["context_sha256"]:
        raise ValueError("external operation context hash mismatch")
    _plan(context["plan"])
    route = context["route"]
    if route["endpoint"] != ENDPOINTS.get(route["provider"]):
        raise ValueError("external operation endpoint mismatch")
    _hash(context["search_policy_sha256"])
    if row["cache_key"] != _cache_key(context) or row["corpus_key"] != _corpus_key(context):
        raise ValueError("external operation cache binding mismatch")
    if row["operation_id"] != "SEARCH_" + _digest(context) or row["budget_attempt_id"] != "DISPATCH_" + _digest({"external_operation": row["operation_id"]}):
        raise ValueError("external operation identity mismatch")
    work = connection.execute("SELECT * FROM work_item WHERE work_item_id=?", (row["work_item_id"],)).fetchone()
    budget = connection.execute("SELECT * FROM quick_scan_budget_attempt WHERE budget_attempt_id=?", (row["budget_attempt_id"],)).fetchone()
    if (work is None or budget is None or context["work_item_id"] != row["work_item_id"]
        or context["work_fingerprint"] != {name: work[name] for name in _WORK_KEYS}
        or budget["work_attempt_id"] is not None or budget["model_requested"] != MODEL_BUDGET_LABEL
        or budget["policy_id"] != context["budget"]["policy_id"] or budget["policy_version"] != context["budget"]["policy_version"]
        or budget["route_id"] != route["route_id"] or budget["provider"] != route["provider"] or budget["quota_group"] != route["quota_group"]):
        raise ValueError("external operation durable binding mismatch")
    raw = connection.execute("SELECT * FROM quick_scan_external_result WHERE operation_id=?", (row["operation_id"],)).fetchone()
    result = None
    dispatch = connection.execute("SELECT * FROM quick_scan_external_dispatch WHERE operation_id=?", (row["operation_id"],)).fetchone()
    if raw is not None:
        receipt = _receipt(strict_search_json(raw["receipt_json"]), context, row["budget_attempt_id"])
        if _canonical(receipt) != raw["receipt_json"] or _digest(receipt) != raw["receipt_sha256"] or dispatch is None or budget["status"] == "in_flight":
            raise ValueError("external result durable binding mismatch")
        charge = strict_search_json(raw["charge_json"])
        if _canonical(charge) != raw["charge_json"] or set(charge) != {"actual_cost_micros", "cost_source_ref"}:
            raise ValueError("external result charge binding mismatch")
        _hash(raw["input_receipt_sha256"])
        if (charge["actual_cost_micros"] is not None and budget["status"] == "settled"
            and (charge["actual_cost_micros"] != budget["actual_cost_micros"] or charge["cost_source_ref"] != budget["cost_source_ref"])):
            raise ValueError("external result charge ledger mismatch")
        retained = sum(len(_canonical(entry)) for entry in receipt.get("entries", []))
        if retained != raw["retained_entry_chars"] or retained > context["plan"]["company_limit"]:
            raise ValueError("external result retained data bound mismatch")
        result = {"receipt": receipt, "receipt_sha256": raw["receipt_sha256"], "input_receipt_sha256": raw["input_receipt_sha256"], "charge": charge,
                  "retained_entry_chars": retained, "entries_retention_truncated": bool(raw["entries_retention_truncated"]), "recorded_at": raw["recorded_at"], "late": bool(raw["late"])}
    return {**dict(row), "context": context, "plan": context["plan"], "budget": dict(budget), "result": result, "dispatch": None if dispatch is None else dict(dispatch)}


def validate_tables(connection: "sqlite3.Connection") -> None:
    for row in connection.execute("SELECT * FROM quick_scan_external_operation"):
        read_record(connection, row)
    for row in connection.execute("SELECT o.corpus_key,o.context_json,SUM(r.retained_entry_chars) AS retained FROM quick_scan_external_operation o JOIN quick_scan_external_result r USING(operation_id) GROUP BY o.corpus_key"):
        context = strict_search_json(row["context_json"])
        if row["retained"] > context["plan"]["company_limit"]:
            raise ValueError("company retained evidence cap exceeded")


def _reusable(record: dict, now: float) -> None:
    from src.utils.quick_scan_work_store import BudgetAdmissionError
    if record["budget"]["status"] != "settled" or record["result"] is None:
        raise BudgetAdmissionError("external_search_unresolved")
    result = record["result"]
    receipt = result["receipt"]
    if receipt.get("usage_status") == "exceeds_verified_bound":
        raise BudgetAdmissionError("external_pricing_bound_exceeded")
    if receipt["outcome"] != "response_available":
        raise BudgetAdmissionError("external_search_failed")
    if receipt["parse_status"] != "ok" or not receipt["entries"]:
        raise BudgetAdmissionError("external_evidence_insufficient")
    if now >= result["recorded_at"] + record["plan"]["ttl_seconds"]:
        raise BudgetAdmissionError("external_search_stale_generation_required")


def _request_context(store: "QuickScanWorkStore", connection: "sqlite3.Connection", work_item_id: str, lease: "Lease", *, normalized: dict, plan: dict, route_id: str, provider: str, quota_group: str, adapter_version: str, search_policy_sha256: str, endpoint: str) -> dict:
    frozen = _plan(plan)
    _hash(search_policy_sha256)
    if endpoint != ENDPOINTS.get(provider):
        raise ValueError("external endpoint protocol mismatch")
    route = {"route_id": _text(route_id, 200), "provider": provider, "quota_group": _text(quota_group, 200), "adapter_version": _text(adapter_version, 160), "endpoint": endpoint}
    item = store._item(connection, work_item_id)
    store._assert_lease(item, lease, store._now())
    if frozen["entity_id"] != item["entity_id"] or frozen["identity_snapshot_sha256"] != item["identity_snapshot_sha256"] or item["question_id"] not in frozen["question_ids"]:
        raise ValueError("external plan work binding mismatch")
    return {"work_item_id": work_item_id, "work_fingerprint": {name: item[name] for name in _WORK_KEYS}, "plan": frozen, "route": route, "search_policy_sha256": search_policy_sha256,
            "budget": {name: normalized[name] for name in ("policy_id", "policy_version", "policy_snapshot_sha256")}}


def _resumable_unsent(record: dict, work_item_id: str, lease: "Lease") -> bool:
    # A dispatch row is written before HTTP. Its absence proves this intent
    # never entered the adapter's transport. Reuse only its original live
    # owner; an expired/fenced lease cannot acquire another owner's permit.
    return (record["budget"]["status"] == "in_flight" and record["dispatch"] is None
            and record["result"] is None and record["work_item_id"] == work_item_id
            and record["lease_token"] == lease.lease_token and record["lease_epoch"] == lease.lease_epoch)


def _assert_no_unknown_scope(connection: "sqlite3.Connection", context: dict) -> None:
    from src.utils.quick_scan_work_store import BudgetAdmissionError
    item = context["work_fingerprint"]
    for row in connection.execute("SELECT o.* FROM quick_scan_external_operation o JOIN work_item w USING(work_item_id) WHERE w.entity_id=? AND w.scope=? AND w.scope_id=?", (item["entity_id"], item["scope"], item["scope_id"])):
        old = read_record(connection, row)
        terminal = connection.execute("SELECT terminal_outcome FROM quick_scan_budget_terminal WHERE budget_attempt_id=?", (old["budget_attempt_id"],)).fetchone()
        if old["budget"]["status"] != "settled" or terminal is None or terminal[0] == "unknown":
            raise BudgetAdmissionError("external_search_unresolved")


def lookup(store: "QuickScanWorkStore", work_item_id: str, lease: "Lease", *, policy: dict, **request: Any) -> dict | None:
    """Find the actual durable result before key/health/reservation side effects.

    Known failures remain available for the coordinator to price and skip;
    this is neither a successful-evidence verdict nor permission to send.
    """
    from src.utils.quick_scan_work_store import _budget_policy_projection
    normalized = _budget_policy_projection(policy)
    with closing(store._connect()) as connection:
        context = _request_context(store, connection, work_item_id, lease, normalized=normalized, **request)
        previous = connection.execute("SELECT * FROM quick_scan_external_operation WHERE cache_key=?", (_cache_key(context),)).fetchone()
        if previous is not None:
            return read_record(connection, previous)
        _assert_no_unknown_scope(connection, context)
        return None


def begin(store: "QuickScanWorkStore", work_item_id: str, lease: "Lease", *, policy: dict, plan: dict, route_id: str, provider: str, quota_group: str, adapter_version: str, search_policy_sha256: str, endpoint: str) -> dict:
    from src.utils.quick_scan_work_store import BudgetAdmissionError
    normalized = store.configure_quick_scan_budget(policy)
    now = store._now()
    with store._transaction() as connection:
        context = _request_context(store, connection, work_item_id, lease, normalized=normalized, plan=plan, route_id=route_id, provider=provider, quota_group=quota_group, adapter_version=adapter_version, search_policy_sha256=search_policy_sha256, endpoint=endpoint)
        operation_id = "SEARCH_" + _digest(context)
        cache_key, corpus_key = _cache_key(context), _corpus_key(context)
        previous = connection.execute("SELECT * FROM quick_scan_external_operation WHERE cache_key=?", (cache_key,)).fetchone()
        if previous is not None:
            record = read_record(connection, previous)
            if _resumable_unsent(record, work_item_id, lease):
                return {**record, "send_required": True, "resumed_unsent_intent": True}
            _reusable(record, now)
            return {**record, "send_required": False}
        _assert_no_unknown_scope(connection, context)
        budget_attempt_id = "DISPATCH_" + _digest({"external_operation": operation_id})
        store._reserve_budget_attempt_tx(connection, normalized_policy=normalized, budget_attempt_id=budget_attempt_id, work_attempt_id=None, route_id=route_id, provider=provider, model_requested=MODEL_BUDGET_LABEL, quota_group=quota_group, now=now)
        connection.execute("INSERT INTO quick_scan_external_operation (operation_id,cache_key,corpus_key,work_item_id,budget_attempt_id,lease_epoch,lease_token,context_json,context_sha256,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (operation_id, cache_key, corpus_key, work_item_id, budget_attempt_id, lease.lease_epoch, lease.lease_token, _canonical(context), _digest(context), now))
        row = connection.execute("SELECT * FROM quick_scan_external_operation WHERE operation_id=?", (operation_id,)).fetchone()
        return {**read_record(connection, row), "send_required": True}


def consume(store: "QuickScanWorkStore", operation_id: str, *, budget_attempt_id: str) -> None:
    from src.utils.quick_scan_work_store import Lease, WorkConflictError
    with store._transaction() as connection:
        row = connection.execute("SELECT * FROM quick_scan_external_operation WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            raise KeyError("unknown external operation")
        record = read_record(connection, row)
        if record["budget_attempt_id"] != budget_attempt_id or record["dispatch"] is not None or record["budget"]["status"] != "in_flight":
            raise WorkConflictError("external send intent already consumed or mismatched")
        store._assert_lease(store._item(connection, row["work_item_id"]), Lease(row["lease_token"], row["lease_epoch"]), store._now())
        connection.execute("INSERT INTO quick_scan_external_dispatch (operation_id,sent_at) VALUES (?,?)", (operation_id, store._now()))


def get(store: "QuickScanWorkStore", operation_id: str) -> dict:
    with closing(store._connect()) as connection:
        row = connection.execute("SELECT * FROM quick_scan_external_operation WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            raise KeyError("unknown external operation")
        return read_record(connection, row)


def record_result(store: "QuickScanWorkStore", operation_id: str, *, receipt: dict, actual_cost: Any = None, cost_source_ref: str | None = None) -> dict:
    from src.utils.quick_scan_work_store import Lease, LeaseFencedError, WorkConflictError, _cost_to_micros, _safe_text
    micros = None if actual_cost is None else _cost_to_micros(actual_cost, "actual_cost", allow_zero=True)
    if micros is not None:
        cost_source_ref = _safe_text(cost_source_ref, "cost_source_ref", maximum=300)
    elif cost_source_ref is not None:
        raise ValueError("cost reference without an exact cost")
    charge = {"actual_cost_micros": micros, "cost_source_ref": cost_source_ref}
    now = store._now()
    with store._transaction() as connection:
        row = connection.execute("SELECT * FROM quick_scan_external_operation WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            raise KeyError("unknown external operation")
        record = read_record(connection, row)
        safe = _receipt(receipt, record["context"], row["budget_attempt_id"])
        input_sha256 = _digest(safe)
        if record["result"] is not None:
            if record["result"]["input_receipt_sha256"] != input_sha256 or record["result"]["charge"] != charge:
                raise WorkConflictError("external operation already has a different result")
            return record
        if record["dispatch"] is None:
            raise WorkConflictError("external result arrived before durable dispatch")
        retained, truncated = 0, False
        if "entries" in safe:
            previously_retained = connection.execute("SELECT COALESCE(SUM(r.retained_entry_chars),0) FROM quick_scan_external_operation o JOIN quick_scan_external_result r USING(operation_id) WHERE o.corpus_key=?", (row["corpus_key"],)).fetchone()[0]
            remaining = record["plan"]["company_limit"] - previously_retained
            entries = []
            for entry in safe["entries"]:
                size = len(_canonical(entry))
                if retained + size > remaining:
                    truncated = True
                    break
                retained += size
                entries.append(entry)
            safe["entries"] = entries
        late = False
        try:
            store._assert_lease(store._item(connection, row["work_item_id"]), Lease(row["lease_token"], row["lease_epoch"]), now)
        except LeaseFencedError:
            late = True
        store._record_budget_outcome_tx(connection, row["budget_attempt_id"], outcome=safe["outcome"], http_status_code=safe.get("http_status_code"), now=now, actual_cost_micros=micros, cost_source_ref=cost_source_ref)
        connection.execute("INSERT INTO quick_scan_external_result (operation_id,receipt_json,receipt_sha256,input_receipt_sha256,charge_json,retained_entry_chars,entries_retention_truncated,recorded_at,late) VALUES (?,?,?,?,?,?,?,?,?)", (operation_id, _canonical(safe), _digest(safe), input_sha256, _canonical(charge), retained, int(truncated), now, int(late)))
        return read_record(connection, row)
