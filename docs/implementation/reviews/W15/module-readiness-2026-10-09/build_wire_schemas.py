"""Generate the two explicit W15 wire contracts; no runtime or source writes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DRAFT = "https://json-schema.org/draft/2020-12/schema"
REFRESH_ID = "urn:iqs:quick-scan:module-refresh:1"
WIRE_ID = "urn:iqs:quick-scan:route-store-cli:1"
TEXT = {"type": "string", "minLength": 1, "maxLength": 500}
SHA = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
ROUTE = {"type": "string", "pattern": "^route_[a-f0-9]{64}$"}
POS = {"type": "integer", "minimum": 1}
ZERO = {"type": "integer", "minimum": 0}
STAMP = {"type": "string", "format": "date-time"}


def obj(properties, required=None, *, closed=True):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": not closed}


def array(items, **extra):
    return {"type": "array", "items": items, **extra}


def optional(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def write(name, value):
    destination = ROOT / "schemas/quick_scan" / name
    assert not destination.exists(), "immutable generation input already exists"
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    lock = obj({"module_id": TEXT, "version": TEXT, "artifact_ref": TEXT, "artifact_sha256": SHA})
    field = obj({"field_id": TEXT, "decision": {"enum": ["reuse", "resume_existing_work", "dispatch_new_work",
                    "dispatch_new_generation", "deferred_unknown", "manual_refresh_required", "deferred_scope_unbound"]},
                 "freshness_status": optional(TEXT), "reasons": array(TEXT), "generation": optional(POS),
                 "logical_todo_key": optional(TEXT), "reuse_observation_id": optional({"type": "string", "pattern": "^obs_[a-f0-9]{64}$"}),
                 "request_identity_key": optional(TEXT), "next_retry_at": STAMP},
                ["field_id", "decision", "freshness_status", "reasons", "generation", "logical_todo_key", "reuse_observation_id", "request_identity_key"])
    observation = obj({"observation_id": {"type": "string", "pattern": "^obs_[a-f0-9]{64}$"},
                       "payload_sha256": SHA, "payload": {"type": "object"}}, closed=False)
    strings = array(TEXT, uniqueItems=True)
    refresh = obj({"protocol": {"const": "stockwiki.module_refresh_plan/1.0.0"}, "schema_version": {"const": "1.0.0"},
                   "subject_key": TEXT, "identity_revision": POS, "perimeter_sha256": SHA, "decision_id": ROUTE,
                   "anchor_version": POS, "manifest_raw_sha256": SHA, "module_package_id": TEXT, "module_release_id": TEXT,
                   "module_locks": array(lock, minItems=1), "aggregation_policy": TEXT, "provider": TEXT, "model": TEXT,
                   "scope": {"enum": ["entity", "segment"]}, "scope_id": TEXT,
                   "information_cutoff": {"type": "string", "format": "date"}, "cutoff_policy": {"const": "exact_period"},
                   "ttl_hours": POS, "now": STAMP, "fields": array(field),
                   "totals": obj({key: ZERO for key in ("fields", "reuse", "planned_dispatches", "deferred_unknown", "resume_existing_work", "deferred_scope_unbound")}),
                   "module_changes": obj({key: strings for key in ("entered", "exited", "retained", "version_changed")}),
                   "comparison": obj({**{key: strings for key in ("retained_question_ids", "added_question_ids", "removed_question_ids", "meaning_changed_question_ids", "comparable_intersection")},
                                      **{key: {"type": "boolean"} for key in ("aggregation_rules_comparable", "same_question_basket")},
                                      "old_scores_recomputed": {"const": False}, "history_rewritten": {"const": False}}),
                   "dispatch_started": {"const": False}, "model_API_requests": {"const": 0}, "history_rewritten": {"const": False},
                   "paid_execution_binding_required": {"const": "stockqa_q13_durable_reconciliation_and_generation_binding"},
                   "refresh_id": {"type": "string", "pattern": "^refresh_[a-f0-9]{64}$"},
                   "reused_observations": {"type": "object", "additionalProperties": observation}}, closed=True)
    refresh["required"].remove("reused_observations")  # planner and CLI are explicit related shapes
    refresh.update({"$schema": DRAFT, "$id": REFRESH_ID,
                    "description": "W15 read-only planner/wire shape. Does not authenticate input, verify financial accuracy, or reserve paid work. refresh_id excludes CLI reused_observations."})
    write("module-refresh.schema.json", refresh)
    binding = obj({"binding_version": {"const": "stockwiki.route_subject/1.0.0"}, "subject_key": TEXT,
                   "analysis_subject_id": TEXT, "analysis_subject_revision": POS, "entity_id": TEXT,
                   "identity_revision": POS, "perimeter_sha256": SHA, "entity_sha256": SHA,
                   "subject": {"type": "object"}, "perimeter_receipt": {"type": "object"},
                   "route_identity_ref": TEXT})
    snapshot_properties = {"decision_id": ROUTE, "subject_key": TEXT, "entity_id": TEXT, "identity_revision": POS,
                           "perimeter_sha256": SHA, "scope": {"enum": ["entity", "segment"]}, "scope_id": TEXT,
                           "route_raw_sha256": SHA, "manifest_raw_sha256": SHA, "router_version": TEXT,
                           "route_as_of": {"type": "string", "format": "date"}, "decided_at": STAMP,
                           "route_execution": {"type": ["object", "null"]}, "module_package_id": TEXT, "module_release_id": TEXT,
                           "module_locks": array(lock, minItems=1), "question_count": POS, "subject_binding": binding}
    snapshot = obj({**snapshot_properties, "classification_confidence": {"type": "object"},
                    "route_raw_base64": TEXT | {"maxLength": 12*1024*1024}, "manifest_raw_base64": TEXT | {"maxLength": 12*1024*1024}}, list(snapshot_properties))
    current = {"expected_decision_id": ROUTE, "anchor_version": POS, "owner_source_binding_refs": strings, "snapshot": snapshot}
    success = obj({"protocol": {"const": "stockwiki.route_store_cli/1.0.0"}, "schema_version": {"const": "1.0.0"},
                   "status": {"const": "ok"}, "action": {"enum": ["binding", "record", "activate", "current", "anchor", "history", "refresh"]},
                   "payload": {"type": "object"}, "c06_envelope_validated": {"const": False}, "paid_dispatch_started": {"const": False}})
    history = obj({"subject_key": TEXT, "scope": TEXT, "scope_id": TEXT, "version": POS, "decision_id": ROUTE,
                   "previous_decision_id": optional(ROUTE), "activated_at": STAMP})
    shapes = {"binding": binding, "record": obj({"status": {"enum": ["recorded", "replayed"]}, "decision_id": ROUTE}),
              "activate": obj({"status": {"enum": ["activated", "unchanged"]}, "decision_id": ROUTE, "version": POS}),
              "current": obj({**current, "execution_validation": {"$ref": "urn:iqs:quick-scan:route-store-validation:1"}}),
              "anchor": obj({**current, "new_execution_authorized": {"const": False}}),
              "history": obj({"current_history": array(history), "snapshots": array(snapshot)}),
              "refresh": {"$ref": REFRESH_ID}}
    success["allOf"] = [{"if": {"properties": {"action": {"const": action}}, "required": ["action"]},
                         "then": {"properties": {"payload": payload}}} for action, payload in shapes.items()]
    rejected = obj({"protocol": {"const": "stockwiki.route_store_cli/1.0.0"}, "status": {"const": "rejected"}, "error_code": TEXT})
    write("route-store-cli.schema.json", {"$schema": DRAFT, "$id": WIRE_ID,
           "description": "Typed W15 owner route responses. Explicitly distinct from the C06 query/refresh envelope and paid dispatch authorization.",
           "oneOf": [success, rejected]})


if __name__ == "__main__":
    main()
