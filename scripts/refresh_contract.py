"""Versioned pure preview contract. Content integrity never grants permission.

Query v2 and legacy refresh remain unchanged. The owner independently supplies
the current W15 plan, membership, policy and original QA budget quote. This
module has no databases, authentication, queue, model client or HTTP execution.
"""

import copy
import json
from datetime import timedelta
from pathlib import Path

import module_contract
import query_contract as query
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.schema.json").read_bytes()
)
CURRENCY_SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.1.schema.json"
    ).read_bytes()
)
CONTROL_SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.2.schema.json"
    ).read_bytes()
)
TARGET_SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.3.schema.json"
    ).read_bytes()
)
EXPOSURE_SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.4.schema.json"
    ).read_bytes()
)
PROFILE_EXPOSURE_SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[1] / "schemas/quick_scan/refresh-v1.5.schema.json"
    ).read_bytes()
)
from query_vendor_contract import SCHEMA as VENDOR_QUERY_SCHEMA

REGISTRY = Registry().with_resources(
    [
        (s["$id"], Resource.from_contents(s))
        for s in (
            SCHEMA,
            CURRENCY_SCHEMA,
            CONTROL_SCHEMA,
            TARGET_SCHEMA,
            EXPOSURE_SCHEMA,
            PROFILE_EXPOSURE_SCHEMA,
            query.SCHEMA,
            VENDOR_QUERY_SCHEMA,
        )
    ]
)
MAX_BYTES = 8 * 1024 * 1024
DISPATCH = {"dispatch_new_work", "dispatch_new_generation", "resume_existing_work"}
HELD = {"deferred_unknown", "deferred_scope_unbound", "manual_refresh_required"}


def paid_work_count(items):
    # An already durable answer only needs delivery. This does not decide
    # retries: uncertain attempts remain governed by the original executor.
    return sum(
        i["decision"] in DISPATCH
        and not (
            i["decision"] == "resume_existing_work" and i["existing_work_status"] == "result_ready"
        )
        for i in items
    )


def digest(value):
    return query._digest(value)


def _shape(
    value,
    kind,
    *,
    currency_dialect=False,
    control_dialect=False,
    target_dialect=False,
    exposure_dialect=False,
    profile_exposure_dialect=False
):
    if kind != "OwnerState":
        profile_exposure_dialect = isinstance(value, dict) and value.get("protocol") in {
            "iqs.refresh_request/1.5.0",
            "stockwiki.refresh_preview/1.5.0",
            "stockwiki.refresh_owner_policy/1.5.0",
        }
        exposure_dialect = isinstance(value, dict) and value.get("protocol") in {
            "iqs.refresh_request/1.4.0",
            "stockwiki.refresh_preview/1.4.0",
            "stockwiki.refresh_owner_policy/1.4.0",
        }
        currency_dialect = isinstance(value, dict) and value.get("protocol") in {
            "iqs.refresh_request/1.1.0",
            "stockwiki.refresh_preview/1.1.0",
            "stockwiki.refresh_owner_policy/1.1.0",
        }
        control_dialect = isinstance(value, dict) and value.get("protocol") in {
            "iqs.refresh_request/1.2.0",
            "stockwiki.refresh_preview/1.2.0",
            "stockwiki.refresh_owner_policy/1.2.0",
        }
        target_dialect = isinstance(value, dict) and value.get("protocol") in {
            "iqs.refresh_request/1.3.0",
            "stockwiki.refresh_preview/1.3.0",
            "stockwiki.refresh_owner_policy/1.3.0",
        }
    schema = (
        PROFILE_EXPOSURE_SCHEMA
        if profile_exposure_dialect
        else (
            EXPOSURE_SCHEMA
            if exposure_dialect
            else (
                TARGET_SCHEMA
                if target_dialect
                else (
                    CONTROL_SCHEMA
                    if control_dialect
                    else CURRENCY_SCHEMA if currency_dialect else SCHEMA
                )
            )
        )
    )
    try:
        if len(module_contract.canonical_bytes(value)) > MAX_BYTES:
            raise ValueError("refresh_input_too_large")
        Draft202012Validator(
            {"$ref": schema["$id"] + "#/$defs/" + kind},
            registry=REGISTRY,
            format_checker=FormatChecker(),
        ).validate(value)
    except (ValidationError, TypeError, ValueError, RecursionError) as error:
        raise ValueError("refresh_document_invalid") from error


def validate_request(request):
    _shape(request, "Request")
    source = request["source_query"]
    selected = query
    if (
        request["protocol"]
        in {
            "iqs.refresh_request/1.1.0",
            "iqs.refresh_request/1.4.0",
            "iqs.refresh_request/1.5.0",
            "iqs.refresh_request/1.2.0",
            "iqs.refresh_request/1.3.0",
        }
        and source.get("schema_version") == "2.6.0"
    ):
        import query_vendor_contract as selected
    selected.validate_request(source)
    if source["payload"]["snapshot_id"] is None:
        raise ValueError("refresh_frozen_snapshot_required")
    if request["consumer_id"] != source["consumer_id"]:
        raise ValueError("refresh_consumer_mismatch")
    query._subject_map(request["subject_refs"])
    captured = {digest(r) for r in source["payload"]["subject_refs"]}
    if any(digest(r) not in captured for r in request["subject_refs"]):
        raise ValueError("refresh_subject_outside_snapshot")
    if set(request["field_ids"]) - set(source["payload"]["field_ids"]):
        raise ValueError("refresh_field_outside_snapshot")
    if query._utc(request["requested_at"]) < query._utc(source["requested_at"]):
        raise ValueError("refresh_request_before_query")


def validate_policy(policy):
    """Validate owner-configured structure, never a consumer permission claim."""
    _shape(policy, "OwnerPolicy")
    if type(policy["policy_version"]) is not int or type(policy["ttl_hours"]) is not int:
        raise ValueError("refresh_integer_required")
    dynamic_routes = policy.get("route_resolution", "explicit_routes") == "current_owner_members"
    dynamic_fields = policy.get("field_permission", "explicit_fields") == "current_manifest"
    if (dynamic_routes and policy["routes"]) or (not dynamic_routes and not policy["routes"]):
        raise ValueError("refresh_policy_route_permission_ambiguous")
    if (dynamic_fields and policy["field_ids"]) or (not dynamic_fields and not policy["field_ids"]):
        raise ValueError("refresh_policy_field_permission_ambiguous")
    seen = set()
    for row in policy["routes"]:
        ref = row["subject_ref"]
        query._subject_map([ref])
        key = digest(ref)
        if key in seen:
            raise ValueError("refresh_policy_duplicate_subject")
        seen.add(key)
        if row["subject_key"] != ref["analysis_subject_id"] + "@" + str(
            ref["analysis_subject_revision"]
        ):
            raise ValueError("refresh_policy_subject_key_mismatch")
        scope = "segment" if ref["scope"] == "segment" else "entity"
        scope_id = ref["segment_id"] if scope == "segment" else ref["entity_id"]
        if row["scope"] != scope or row["scope_id"] != scope_id:
            raise ValueError("refresh_policy_route_scope_mismatch")
    for key in ("code_root", "work_store", "budget_policy_file"):
        if not Path(policy["qa"][key]).is_absolute():
            raise ValueError("refresh_policy_absolute_path_required")
    return copy.deepcopy(policy)


def _check_state(request, state):
    targeted = request["protocol"] == "iqs.refresh_request/1.3.0"
    controlled = request["protocol"] in {
        "iqs.refresh_request/1.2.0",
        "iqs.refresh_request/1.3.0",
    }
    _shape(
        state,
        "OwnerState",
        currency_dialect=request["protocol"] == "iqs.refresh_request/1.1.0",
        control_dialect=controlled,
        target_dialect=targeted,
        exposure_dialect=request["protocol"] == "iqs.refresh_request/1.4.0",
        profile_exposure_dialect=request["protocol"] == "iqs.refresh_request/1.5.0",
    )
    numbers = [
        state["policy_version"],
        state["ttl_hours"],
        *state["member_versions"].values(),
        *[a[k] for a in state["anchors"] for k in ("anchor_version", "identity_revision")],
        state["quote"]["max_cost_micros"],
        state["quote"]["max_http_requests"],
        *[i["generation"] for i in state["items"] if i["generation"] is not None],
    ]
    if any(type(n) is not int for n in numbers):
        raise ValueError("refresh_integer_required")
    refs = {digest(r): r for r in request["subject_refs"]}
    if set(state["member_versions"]) != {r["entity_id"] for r in refs.values()}:
        raise ValueError("refresh_owner_roster_scope_mismatch")
    if {digest(a["subject_ref"]) for a in state["anchors"]} != set(refs):
        raise ValueError("refresh_owner_anchor_scope_mismatch")
    if len(state["anchors"]) != len(refs):
        raise ValueError("refresh_duplicate_anchor")
    seen = set()
    covered = set()
    expected = {(key, field) for key in refs for field in request["field_ids"]}
    for item in state["items"]:
        key = digest(item["subject_ref"])
        pair = (key, item["field_id"])
        unique = (*pair, item["question_id"])
        if pair not in expected or unique in seen:
            raise ValueError("refresh_owner_plan_scope_mismatch")
        seen.add(unique)
        covered.add(pair)
        if (item["decision"] == "reuse") != (item["reuse_observation_id"] is not None):
            raise ValueError("refresh_original_reference_required")
        if item["decision"] in DISPATCH and item["generation"] is None:
            raise ValueError("refresh_work_generation_required")
        if item["decision"] == "resume_existing_work" and item["existing_work_status"] is None:
            raise ValueError("refresh_existing_work_status_required")
    if covered != expected:
        raise ValueError("refresh_owner_plan_incomplete")
    if controlled:
        requested = {(r["work_item_id"], r["decision_id"]) for r in request["work_decision_refs"]}
        observed = set()
        for item in state["items"]:
            control = item["owner_control"]
            key = (control["source_work_item_id"], control["decision_id"])
            if (
                key in observed
                or control["cohort_id"] != request["cohort_id"]
                or control["target_generation"] != control["source_generation"] + 1
                or item["decision"]
                not in {
                    "dispatch_new_generation",
                    "deferred_unknown",
                    "manual_refresh_required",
                }
                or (
                    item["decision"] == "dispatch_new_generation"
                    and item["generation"] != control["target_generation"]
                )
                or (
                    item["decision"] != "dispatch_new_generation" and item["generation"] is not None
                )
            ):
                raise ValueError("refresh_owner_control_mismatch")
            if (control["purpose"] == "comparison") != (control["comparison_controls"] is not None):
                raise ValueError("refresh_owner_control_options_mismatch")
            if targeted and control["comparison_target"] is not None:
                target = control["comparison_target"]
                if (
                    target["provider"] != state["provider"]
                    or target["model"] != state["model"]
                    or target["owner_policy_sha256"] != state["policy_sha256"]
                ):
                    raise ValueError("refresh_owner_control_target_mismatch")
            observed.add(key)
        if observed != requested:
            raise ValueError("refresh_owner_control_scope_mismatch")
    source_filter = request["source_query"]["payload"]["model_filter"]
    if source_filter is not None and source_filter != {
        "provider": state["provider"],
        "model_resolved": state["model"],
    }:
        raise ValueError("refresh_selected_model_outside_snapshot_filter")
    tasks = paid_work_count(state["items"])
    quote = state["quote"]
    if request["protocol"] in {"iqs.refresh_request/1.4.0", "iqs.refresh_request/1.5.0"}:
        if set(request["question_ids"]) != {i["question_id"] for i in state["items"]}:
            raise ValueError("refresh_exposure_question_scope_mismatch")
        tasks = quote["planned_physical_requests"] if tasks else 0
    if tasks and quote["budget_available"] and quote["max_http_requests"] < tasks:
        raise ValueError("refresh_quote_request_bound_insufficient")
    if not tasks and (quote["max_http_requests"] or quote["max_cost_micros"]):
        raise ValueError("refresh_no_work_must_be_zero_cost")


def create_preview(request, owner_state, *, created_at, expires_at):
    validate_request(request)
    _check_state(request, owner_state)
    created, end = query._utc(created_at), query._utc(expires_at)
    if created < query._utc(request["requested_at"]) or not created < end <= created + timedelta(
        hours=1
    ):
        raise ValueError("refresh_preview_time_invalid")
    state = copy.deepcopy(owner_state)
    if request["protocol"] in {
        "iqs.refresh_request/1.2.0",
        "iqs.refresh_request/1.3.0",
    }:
        for item in state["items"]:
            c = item["owner_control"]
            expected = (
                "deferred_unknown"
                if created < query._utc(c["next_retry_at"])
                else (
                    "manual_refresh_required"
                    if c["purpose"] == "retry_unknown_answer"
                    and item["existing_work_status"] == "result_ready"
                    else "dispatch_new_generation"
                )
            )
            if (
                item["decision"] != expected
                or item["existing_work_status"] not in {"failed", "result_ready", "delivered"}
                or c["purpose"] == "retry_unusable_checkpoint"
                and item["existing_work_status"] != "result_ready"
                or c["purpose"] == "retry_unusable_answer"
                and item["existing_work_status"] != "failed"
            ):
                raise ValueError("refresh_owner_control_schedule_mismatch")
    tasks = any(i["decision"] in DISPATCH for i in state["items"])
    paid_tasks = paid_work_count(state["items"])
    if (
        request["protocol"] in {"iqs.refresh_request/1.4.0", "iqs.refresh_request/1.5.0"}
        and paid_tasks
    ):
        paid_tasks = state["quote"]["planned_physical_requests"]
    held = any(i["decision"] in HELD for i in state["items"])
    status = (
        "blocked"
        if held or (paid_tasks and not state["quote"]["budget_available"])
        else "ready" if tasks else "noop"
    )
    scope = dict(
        source_snapshot_id=request["source_query"]["payload"]["snapshot_id"],
        subject_refs=request["subject_refs"],
        field_ids=request["field_ids"],
        consumer_id=request["consumer_id"],
        origin_task_id=request["origin_task_id"],
    )
    if request["protocol"] in {
        "iqs.refresh_request/1.2.0",
        "iqs.refresh_request/1.3.0",
    }:
        scope.update(
            cohort_id=request["cohort_id"],
            work_decision_refs=request["work_decision_refs"],
        )
    if request["protocol"] in {"iqs.refresh_request/1.4.0", "iqs.refresh_request/1.5.0"}:
        scope.update(
            cohort_id=request["cohort_id"],
            continuation_decision_ref=request["continuation_decision_ref"],
            question_ids=request["question_ids"],
        )
        if request["protocol"] == "iqs.refresh_request/1.5.0":
            scope["execution_profile_sha256"] = request["execution_profile_sha256"]
    result = dict(
        protocol="stockwiki.refresh_preview/" + request["protocol"].split("/")[-1],
        operation="request_refresh",
        request_sha256=digest(request),
        scope_sha256=digest(scope),
        owner_state_sha256=digest(state),
        source_snapshot_id=scope["source_snapshot_id"],
        **{
            k: state[k]
            for k in (
                "store_id",
                "policy_id",
                "policy_version",
                "policy_sha256",
                "provider",
                "model",
                "items",
                "quote",
            )
        },
        created_at=created_at,
        expires_at=expires_at,
        status=status,
        requires_user_confirmation=status == "ready",
        dispatch_started=False,
        API_requests=0
    )
    result["preview_id"] = "rv1_" + digest(result)
    _shape(result, "Preview")
    return result


def validate_preview(preview, *, request, owner_state, now=None):
    _shape(preview, "Preview")
    if type(preview["API_requests"]) is not int or type(preview["policy_version"]) is not int:
        raise ValueError("refresh_integer_required")
    expected = create_preview(
        request,
        owner_state,
        created_at=preview["created_at"],
        expires_at=preview["expires_at"],
    )
    if preview != expected:
        raise ValueError("refresh_preview_owner_mismatch")
    if now is not None and not query._utc(preview["created_at"]) <= query._utc(now) < query._utc(
        preview["expires_at"]
    ):
        raise ValueError("refresh_preview_expired")
    return copy.deepcopy(preview)
