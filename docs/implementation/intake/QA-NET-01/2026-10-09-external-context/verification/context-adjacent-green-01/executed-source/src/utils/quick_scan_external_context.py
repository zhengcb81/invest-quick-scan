"""Link external retrieval to existing Q09 accounting without model rerouting.

The returned composite is a budget projection ONLY. Answer-model dispatch must
retain its original model policy and priority. No scheduler or ledger lives here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

from src.config.quick_scan_search_policy import SearchPolicy, execution_query_plans
from src.utils.quick_scan_external_journal import MODEL_BUDGET_LABEL, _identity_basis, _reusable
from src.utils.quick_scan_work_store import Lease, QuickScanWorkStore, _budget_policy_projection, _cost_to_micros


def build_shared_external_budget_policy(model_policy: dict[str, Any], search_policy: SearchPolicy) -> dict[str, Any]:
    """Add admitted retrieval route identities to one unchanged spending owner."""
    original = _budget_policy_projection(model_policy)
    execution_query_plans(search_policy)  # Requires the loader's unchanged 1.1 plan.
    if not search_policy.admitted or not search_policy.requires_external:
        raise ValueError("no executable admitted external route")
    shared = copy.deepcopy(model_policy)
    route_ids = {route["id"] for route in shared["routes"]}
    groups = {group["id"]: group for group in shared["quota_groups"]}
    for route_id in search_policy.admitted:
        route = next(item for item in search_policy.routes if item["route_id"] == route_id)
        pricing, dispatch = route["pricing"], route["dispatch"]
        if route_id in route_ids:
            raise ValueError("external and answer-model route identities overlap")
        if pricing["currency"] != original["currency"]:
            raise ValueError("search and answer-model budget currencies differ")
        if pricing["per_request_cap_micros"] > min(original["max_cost_per_attempt_micros"], original["max_cost_micros"]):
            raise ValueError("external request bound exceeds the existing budget cap")
        group_id = dispatch["quota_group"]
        group_limit = dispatch["quota_group_max_in_flight"]
        if group_id in groups:
            if groups[group_id]["max_in_flight"] != group_limit:
                raise ValueError("external quota-group concurrency conflicts with the model policy")
        else:
            group = {"id": group_id, "max_in_flight": group_limit}
            groups[group_id] = group
            shared["quota_groups"].append(group)
        shared["routes"].append({
            "id": route_id, "provider_config_ref": route["kind"],
            "model": MODEL_BUDGET_LABEL, "quota_group": group_id,
            "max_in_flight": dispatch["max_in_flight"], "eligible": True,
            "unavailable_reason": None,
        })
        route_ids.add(route_id)
    # A policy-version change never creates a new policy_id or resets counters.
    basis = (original["policy_snapshot_sha256"] + ":" + search_policy.policy_sha256).encode("ascii")
    shared["policy_version"] = "external_budget/1.0.0:" + hashlib.sha256(basis).hexdigest()
    _budget_policy_projection(shared)  # Validate through the original Q09 owner.
    return shared


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _publication_date(value: Any) -> str | None:
    """Accept actual ISO/RFC dates, never a guessed first-ten-character prefix."""
    if not isinstance(value, str) or not 1 <= len(value) <= 100 or value != value.strip():
        return None
    try:
        if len(value) == 10:
            parsed = date.fromisoformat(value)
            return parsed.isoformat() if parsed.isoformat() == value else None
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            instant = parsedate_to_datetime(value)
        if instant.tzinfo is None:
            return None
        return instant.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _origin_binding(url: str, bindings: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Use exact host and canonical path segments, not query target or suffix."""
    try:
        parts = urlsplit(url)
        if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.port not in {None, 443}):
            return None
        path = parts.path or "/"
        if (any(ord(c) < 33 or c in "\\%" for c in path) or "//" in path
            or any(part in {".", ".."} for part in path.split("/"))):
            return None
    except ValueError:
        return None
    for binding in bindings:
        prefix = binding["path_prefix"]
        if parts.hostname == binding["host"] and (prefix == "/" or path == prefix
            or path.startswith(prefix if prefix.endswith("/") else prefix + "/")):
            return binding
    return None


def _bound_candidate(entry: dict[str, Any], plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    binding = _origin_binding(entry["url"], plan["entity_domain_bindings"])
    published = _publication_date(entry.get("published_at"))
    if (binding is None or published is None or published > plan["information_as_of"]
        or not isinstance(entry.get("snippet"), str) or not entry["snippet"].strip()):
        return None
    return dict(entry, entity_id=plan["entity_id"], published_at=published), binding


def build_external_question_context(
    store: QuickScanWorkStore, work_item_id: str, lease: Lease, policy: SearchPolicy,
    operation_ids: list[str], *, question_manifest_sha256: str,
) -> dict[str, Any]:
    """Rebuild bounded untrusted data from verified durable retrieval records.

    The manifest hash is required from the producer's independently frozen
    authority, never inferred from the search configuration. No HTTP, answer
    attempt, model/native receipt, refreshed timestamp or extra storage is made.
    The eventual answer dispatch must bind this hash to its actual prompt.
    """
    from src.utils.quick_scan_cost_resolver import ExternalSearchCostResolver
    from src.utils.quick_scan_evidence import build_evidence_package

    plans = execution_query_plans(policy)
    if not isinstance(store, QuickScanWorkStore) or not isinstance(lease, Lease):
        raise ValueError("external context requires a durable work store and lease")
    item = store.get_item(work_item_id)
    now = store._now()
    store._assert_lease(item, lease, now)
    expected = policy.execution_plan
    if (expected is None or expected["entity_id"] != item["entity_id"]
        or expected["identity_snapshot_sha256"] != item["identity_snapshot_sha256"]
        or expected["question_manifest_sha256"] != question_manifest_sha256):
        raise ValueError("external policy does not match the independently frozen work authority")
    question_id = item["question_id"]
    required = {plan["query_id"]: plan for plan in plans if question_id in plan["question_ids"]}
    if not required:
        raise ValueError("external policy has no frozen queries for this question")
    if not isinstance(operation_ids, list) or not operation_ids or any(not isinstance(value, str) for value in operation_ids):
        raise ValueError("external operation identifiers required")
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("duplicate external operation identifiers")
    if len(operation_ids) != len(required):
        raise ValueError("external query plan incomplete or ambiguous")
    current_basis = _identity_basis({"work_fingerprint": {key: item[key] for key in (
        "entity_id", "question_id", "generation", "scope", "scope_id", "identity_revision",
        "source_binding_version", "identity_state", "source_binding_ref", "source_binding_refs_json",
        "identity_snapshot_sha256", "question_fingerprint", "routing_fingerprint",
    )}})
    resolver = ExternalSearchCostResolver(policy)
    records: dict[str, dict[str, Any]] = {}
    for operation_id in operation_ids:
        record = store.get_external_search(operation_id)  # Rechecks hashes/ledger, not caller dictionaries.
        plan, original = record["plan"], record["context"]
        query_id = plan["query_id"]
        if (original["search_policy_sha256"] != policy.policy_sha256
            or original["route"]["route_id"] not in policy.admitted
            or plan != required.get(query_id) or _identity_basis(original) != current_basis):
            raise ValueError("external policy, query or work scope binding mismatch")
        if query_id in records:
            raise ValueError("duplicate external query result")
        _reusable(record, now)
        result = record["result"]
        if result["recorded_at"] > now:
            raise ValueError("external retrieval time is in the future")
        price = resolver(result["receipt"])
        if (price is None or result["charge"]["actual_cost_micros"] != _cost_to_micros(price["actual_cost"], "actual_cost", allow_zero=True)
            or result["charge"]["cost_source_ref"] != price["source_ref"]):
            raise ValueError("external pricing proof does not match the frozen policy")
        records[query_id] = record
    candidates, retrievals, origins = [], [], {}
    for query_id, plan in required.items():
        record = records[query_id]
        result = record["result"]
        receipt = result["receipt"]
        retrieved_at = datetime.fromtimestamp(result["recorded_at"], timezone.utc).isoformat().replace("+00:00", "Z")
        retrievals.append({
            "operation_id": record["operation_id"], "query_id": query_id,
            "route_id": receipt["route_id"], "route_kind": receipt["route_kind"],
            "receipt_sha256": result["receipt_sha256"], "retrieved_at": retrieved_at,
        })
        for entry in receipt["entries"]:
            bound = _bound_candidate(entry, plan)
            if bound is None:
                continue
            candidate, binding = bound
            candidates.append(candidate)
            origins.setdefault(entry["url"], {"binding": binding, "retrieved_at": retrieved_at,
                                            "operation_id": record["operation_id"]})
    package = build_evidence_package(candidates, entity_id=item["entity_id"], as_of=expected["information_as_of"],
        retrieved_at=retrievals[0]["retrieved_at"], adapter_version="stockqa.external_context/1.0.0",
        request_id=record["operation_id"], query_bindings={plan["query"]: plan["question_ids"] for plan in required.values()},
        question_ids=[question_id], snippet_limit=policy.retrieval["max_snippet_unicode_characters"],
        company_limit=policy.retrieval["max_company_evidence_unicode_characters"])
    sources = []
    for entry in package["entries"]:
        if not entry["eligible"]:
            continue
        origin = origins[entry["url"]]
        query_id = next(key for key, plan in required.items() if plan["query"] == entry["query"])
        sources.append({key: entry[key] for key in ("source_id", "title", "publisher", "url", "published_at", "short_snippet")}
                       | {"retrieved_at": origin["retrieved_at"], "operation_id": origin["operation_id"],
                          "query_id": query_id,
                          "identity_binding_kind": origin["binding"]["binding_kind"],
                          "identity_binding_source_ref": origin["binding"]["source_ref"]})
    if not sources:
        raise ValueError("no eligible company evidence for this question")
    context = {
        "schema": "stockqa.external_question_context/1.0.0", "content_trust": "untrusted_source_data",
        "claim_verification": "not_automatic",
        "entity_id": item["entity_id"], "work_item_id": work_item_id,
        "scope": item["scope"], "scope_id": item["scope_id"], "question_id": question_id,
        "identity_snapshot_sha256": item["identity_snapshot_sha256"],
        "question_manifest_sha256": question_manifest_sha256,
        "information_as_of": expected["information_as_of"], "answer_search_mode": expected["answer_search_mode"],
        "retrievals": retrievals, "sources": sources,
        "query_coverage": {"required": list(required),
                           "eligible": [query_id for query_id in required if any(source["query_id"] == query_id for source in sources)],
                           "missing": [query_id for query_id in required if not any(source["query_id"] == query_id for source in sources)]},
    }
    context["context_sha256"] = hashlib.sha256(_canonical(context).encode("utf-8")).hexdigest()
    if len(_canonical(context)) > policy.retrieval["max_company_evidence_unicode_characters"]:
        raise ValueError("external context metadata and sources exceed the company cap")
    return context
