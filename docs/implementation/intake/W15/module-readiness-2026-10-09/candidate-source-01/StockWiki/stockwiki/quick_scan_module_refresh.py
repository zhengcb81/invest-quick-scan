"""W15 module deltas and per-question freshness over immutable owner stores.

Plans only, never executes. Original observation/model/time/score stays intact.
Without its matching stored producer manifest an old answer is not reusable.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from stockwiki.quick_scan_analysis import perimeter_sha256, receipt_key
from stockwiki.quick_scan_freshness import build_gap_plan, parse_utc, ttl_valid_until
from stockwiki.quick_scan_import import canonical_sha256
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_route_validation import RouteStoreError, read_json
from stockwiki.quick_scan_routes import QuickScanRouteStore

PROTOCOL = "stockwiki.module_refresh_plan/1.0.0"
_CONTEXT_KEYS = ("reporting_currency", "accounting_standard", "fiscal_year_end", "security_class")


def _routing_fingerprint(
    manifest: dict[str, Any], snapshot: dict[str, Any], question: dict[str, Any]
) -> str:
    route = read_json(snapshot["route_raw"])
    profile = manifest.get("profile", route.get("profile_context", {}))
    return canonical_sha256(
        {
            "subject_key": snapshot["subject_key"],
            "perimeter_sha256": snapshot["perimeter_sha256"],
            "scope": _question_scope(question, snapshot),
            "scope_id": _question_scope_id(question, snapshot),
            "context": {key: profile.get(key) for key in _CONTEXT_KEYS},
        }
    )


def _question_scope(question: dict[str, Any], snapshot: dict[str, Any]) -> str:
    route = read_json(snapshot["route_raw"])
    return (
        "segment"
        if route.get("scope") == "segment" and question["scope"] == "entity"
        else question["scope"]
    )


def _question_scope_id(question: dict[str, Any], snapshot: dict[str, Any]) -> str | None:
    route = read_json(snapshot["route_raw"])
    scope = _question_scope(question, snapshot)
    if scope == "entity":
        return snapshot["entity_id"]
    if scope == "security":
        return route.get("profile_context", {}).get("security_id")
    if scope == "segment":
        return route.get("segment_id")
    return None


def _module_changes(old: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    a = {row["module_id"]: row["version"] for row in old.get("module_locks", [])} if old else {}
    b = {row["module_id"]: row["version"] for row in current["module_locks"]}
    return {
        "entered": sorted(b.keys() - a.keys()),
        "exited": sorted(a.keys() - b.keys()),
        "retained": sorted(a.keys() & b.keys()),
        "version_changed": sorted(mid for mid in a.keys() & b.keys() if a[mid] != b[mid]),
    }


def _comparison(old: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    a = {q["id"]: q for q in old["questions"]} if old else {}
    b = {q["id"]: q for q in current["questions"]}
    retained = a.keys() & b.keys()
    changed = sorted(
        qid
        for qid in retained
        if any(
            a[qid].get(key) != b[qid].get(key)
            for key in (
                "semantic_sha256",
                "definition_sha256",
                "scope",
                "metric_id",
                "construct_id",
                "rubric_version",
            )
        )
    )
    rules_same = (
        old is not None
        and old.get("aggregation_policy") == current.get("aggregation_policy")
        and old.get("quality_weights") == current.get("quality_weights")
    )
    return {
        "retained_question_ids": sorted(retained),
        "added_question_ids": sorted(b.keys() - a.keys()),
        "removed_question_ids": sorted(a.keys() - b.keys()),
        "meaning_changed_question_ids": changed,
        "aggregation_rules_comparable": rules_same,
        "same_question_basket": bool(old) and a.keys() == b.keys() and not changed,
        "comparable_intersection": sorted(retained - set(changed)) if rules_same else [],
        "old_scores_recomputed": False,
        "history_rewritten": False,
    }


def _matching_meta(
    row: dict[str, Any],
    *,
    question: dict[str, Any],
    current: dict[str, Any],
    binding: dict[str, Any],
    manifests: list[tuple[dict[str, Any], dict[str, Any]]],
    provider: str,
    model: str,
    ttl_hours: int,
) -> dict[str, Any] | None:
    payload = row["payload"]
    subject = payload.get("analysis_subject")
    if (
        not isinstance(subject, dict)
        or receipt_key(subject) != binding["subject_key"]
        or perimeter_sha256(subject) != binding["perimeter_sha256"]
        or payload.get("identity_revision") != binding["identity_revision"]
        or payload.get("entity_id") != binding["entity_id"]
        or payload.get("scope") != _question_scope(question, current)
        or payload.get("segment_id")
        != (
            _question_scope_id(question, current)
            if _question_scope(question, current) == "segment"
            else None
        )
        or payload.get("security_id")
        != (
            _question_scope_id(question, current)
            if _question_scope(question, current) == "security"
            else None
        )
        or payload.get("field_id") != question["metric_id"]
        or payload.get("question_semantic_sha256") != question["semantic_sha256"]
        or payload.get("question_definition_sha256") != question["definition_sha256"]
        or payload.get("question_version") != question["rubric_version"]
        or payload.get("execution", {}).get("provider") != provider
        or payload.get("execution", {}).get("model_resolved") != model
    ):
        return None
    source_manifest = None
    origin = None
    for candidate, snapshot in manifests:
        if (
            candidate.get("module_package_id") != payload.get("module_package_id")
            or candidate.get("module_release_id") != payload.get("module_release_id")
            or candidate.get("template_version") != payload.get("template_version")
            or read_json(snapshot["route_raw"])["as_of"] != payload.get("information_cutoff")
        ):
            continue
        previous = next((q for q in candidate["questions"] if q["id"] == question["id"]), None)
        if (
            previous is not None
            and previous["semantic_sha256"] == question["semantic_sha256"]
            and previous["definition_sha256"] == question["definition_sha256"]
        ):
            source_manifest, origin = candidate, snapshot
            break
    if source_manifest is None or origin is None:
        return None
    answer = payload["answer"]
    info = answer.get("information_as_of")
    valid_until = None
    if info is not None:
        # Source/information time cannot gain a new TTL merely by importing it.
        information_stamp = info if "T" in info else info + "T00:00:00Z"
        valid_until = min(
            ttl_valid_until(payload["observed_at"], ttl_hours),
            ttl_valid_until(information_stamp, ttl_hours),
            key=parse_utc,
        )
    return {
        "observation_id": row["observation_id"],
        "information_as_of": info,
        "valid_until": valid_until,
        "response_status": "insufficient_evidence"
        if answer["status"] == "unknown"
        else answer["status"],
        "question_fingerprint": question["semantic_sha256"],
        "routing_fingerprint": _routing_fingerprint(source_manifest, origin, question),
        "scope": _question_scope(question, current),
        "scope_id": _question_scope_id(question, current),
        "meaning_version": question["rubric_version"],
        "information_cutoff": payload["information_cutoff"],
        "check_level": "unverified_model_output",
        "observed_at": payload["observed_at"],
    }


def plan_module_refresh(
    routes: QuickScanRouteStore,
    observations: QuickScanObservationStore,
    *,
    subject_key: str,
    scope: str,
    scope_id: str,
    now_utc: str,
    provider: str,
    model: str,
    ttl_hours: int,
    work_items: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Use W06 for exact-period/model reuse; no fallback to a different model.

    work_items is a caller-owned executor projection, never LLM output. It is
    conservative: unresolved paid work resumes even if the new question changed.
    A later Q13 binding must reconcile/reserve durably before any paid dispatch.
    """
    if observations.paths.root != routes.identity.paths.root:
        raise RouteStoreError("route_observation_workspace_mismatch")
    if not all(isinstance(value, str) and value for value in (provider, model)):
        raise RouteStoreError("refresh_model_required")
    if type(ttl_hours) is not int or ttl_hours < 1:
        raise RouteStoreError("refresh_ttl_invalid")
    active = routes.get_for_execution(
        subject_key=subject_key, scope=scope, scope_id=scope_id, now_utc=now_utc
    )
    snapshot = active["snapshot"]
    current = read_json(snapshot["manifest_raw"])
    route = read_json(snapshot["route_raw"])
    cutoff = route["as_of"]
    date.fromisoformat(cutoff)
    archives = [
        (read_json(row["manifest_raw"]), row) for row in routes.snapshots_for_subject(subject_key)
    ]
    history = routes.current_history(subject_key=subject_key, scope=scope, scope_id=scope_id)
    if not history or history[-1]["decision_id"] != active["expected_decision_id"]:
        raise RouteStoreError("route_current_changed")
    previous_id = history[-1]["previous_decision_id"]
    previous = read_json(routes.get_snapshot(previous_id)["manifest_raw"]) if previous_id else None
    rows = (
        observations.observations_for_entity(snapshot["entity_id"])
        if observations.database_path.exists()
        else []
    )
    for row in rows:
        if (
            canonical_sha256(row["payload"]) != row["payload_sha256"]
            or row["payload"].get("observation_id") != row["observation_id"]
        ):
            raise RouteStoreError("refresh_observation_corrupted")
    work_items = work_items or {}
    if not isinstance(work_items, dict) or set(work_items) - {
        q["id"] for q in current["questions"]
    }:
        raise RouteStoreError("refresh_work_projection_invalid")
    fields = {}
    deferred = []
    entity = routes.identity.get_entity(snapshot["entity_id"])
    for question in current["questions"]:
        qid = question["id"]
        effective_scope = _question_scope(question, snapshot)
        question_scope_id = _question_scope_id(question, snapshot)
        if effective_scope == "security" and not any(
            row["security_id"] == question_scope_id for row in entity["securities"]
        ):
            question_scope_id = None
        if effective_scope == "segment" and not any(
            row["segment_id"] == question_scope_id for row in entity["segments"]
        ):
            question_scope_id = None
        if not question_scope_id:
            deferred.append(
                {
                    "field_id": qid,
                    "decision": "deferred_scope_unbound",
                    "freshness_status": None,
                    "reasons": ["question_scope_unbound"],
                    "generation": None,
                    "logical_todo_key": None,
                    "reuse_observation_id": None,
                    "request_identity_key": None,
                }
            )
            continue
        work = work_items.get(qid)
        if work is not None and (
            not isinstance(work, dict)
            or type(work.get("generation")) is not int
            or work["generation"] < 1
        ):
            raise RouteStoreError("refresh_work_projection_invalid")
        candidates = []
        for row in rows:
            if row["question_id"] != qid:
                continue
            meta = _matching_meta(
                row,
                question=question,
                current=snapshot,
                binding=snapshot["metadata"]["binding"],
                manifests=archives,
                provider=provider,
                model=model,
                ttl_hours=ttl_hours,
            )
            if meta is not None:
                candidates.append(meta)
        meta = (
            max(candidates, key=lambda m: (parse_utc(m["observed_at"]), m["observation_id"]))
            if candidates
            else None
        )
        fields[qid] = {
            "expected": {
                "entity_id": snapshot["entity_id"],
                "question_id": qid,
                "scope": effective_scope,
                "scope_id": question_scope_id,
                "model": model,
                "question_fingerprint": question["semantic_sha256"],
                "routing_fingerprint": _routing_fingerprint(current, snapshot, question),
                "meaning_version": question["rubric_version"],
                "information_cutoff": cutoff,
                "minimum_check_level": "unverified_model_output",
            },
            "observation": meta,
            "work_item": work,
        }
    gap = (
        build_gap_plan(
            now=now_utc, fields=fields, global_catalog_version=current["template_version"]
        )
        if fields
        else {
            "fields": [],
            "totals": {
                "fields": 0,
                "reuse": 0,
                "planned_dispatches": 0,
                "deferred_unknown": 0,
                "resume_existing_work": 0,
            },
        }
    )
    gap["fields"] = sorted(gap["fields"] + deferred, key=lambda row: row["field_id"])
    gap["totals"]["fields"] += len(deferred)
    gap["totals"]["deferred_scope_unbound"] = len(deferred)
    for row in gap["fields"]:
        work = work_items.get(row["field_id"])
        if row["decision"] == "dispatch_new_work" and work:
            row["generation"] = work["generation"] + 1
            # W06 todo key used the pre-projection generation; recalculate from
            # the original deterministic owner function, not a second ledger.
            from stockwiki.quick_scan_freshness import _todo_key

            row["logical_todo_key"] = _todo_key(
                row["field_id"], row["generation"], row["request_identity_key"]
            )
    result = {
        "protocol": PROTOCOL,
        "schema_version": "1.0.0",
        "subject_key": subject_key,
        "identity_revision": snapshot["identity_revision"],
        "perimeter_sha256": snapshot["perimeter_sha256"],
        "decision_id": active["expected_decision_id"],
        "anchor_version": active["anchor_version"],
        "manifest_raw_sha256": snapshot["manifest_raw_sha256"],
        "module_package_id": current["module_package_id"],
        "module_release_id": current["module_release_id"],
        "module_locks": current["module_locks"],
        "aggregation_policy": current["aggregation_policy"],
        "provider": provider,
        "model": model,
        "scope": scope,
        "scope_id": scope_id,
        "information_cutoff": cutoff,
        "cutoff_policy": "exact_period",
        "ttl_hours": ttl_hours,
        "now": now_utc,
        "fields": gap["fields"],
        "totals": gap["totals"],
        "module_changes": _module_changes(previous, current),
        "comparison": _comparison(previous, current),
        "dispatch_started": False,
        "model_API_requests": 0,
        "history_rewritten": False,
        "paid_execution_binding_required": "stockqa_q13_durable_reconciliation_and_generation_binding",
    }
    result["refresh_id"] = "refresh_" + canonical_sha256(result)
    return result
