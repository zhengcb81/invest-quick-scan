"""Pure routing policy contract; independent of package storage and execution."""
import re
import module_contract as mc

AXES = {"common": "common", "types": "type", "industries": "industry", "stages": "lifecycle",
        "overlays": "attribute", "diagnostics": "diagnostic", "lenses": "lens",
        "common_extensions": "common_extension"}
PREDICATES = {"always", "type_evidence", "industry_evidence", "lifecycle_evidence",
              "cycle_evidence", "attribute_evidence", "user_diagnostic", "default_diagnostic",
              "recovery_evidence", "user_lens", "common_extension"}
POSITION = {"upturn", "peak", "downturn", "trough", "recovery", "unknown"}
RECOVERY_POSITIONS = {"downturn", "trough", "recovery"}
BASE_SHARES = {"revenue_share", "gross_profit_share", "invested_capital_share"}
STRATEGIC_SHARES = {"committed_capex_share", "binding_backlog_share"}
SHARES = BASE_SHARES | STRATEGIC_SHARES
FACT_KEYS = {"module_id", "confidence", "evidence_type", "rationale", "sources",
             "materiality", "cycle_position", "business_id", "period_count", "major_event"}


def validate_policy(policy, modules):
    base_fields = {"schema_version", "router_version", "materiality", "rules"}
    protocol_fields = base_fields | {"request_protocol", "partial_dispatch"}
    confidence_fields = protocol_fields | {"classification_confidence_gate"}
    if (not isinstance(policy, dict) or set(policy) not in (base_fields, protocol_fields, confidence_fields)
            or policy["schema_version"] not in {"1.0.0", "1.1.0", "1.2.0", "1.3.0"}
            or not isinstance(policy["router_version"], str)
            or not re.fullmatch(r"2\.\d+\.\d+", policy["router_version"])):
        raise ValueError("unsupported routing policy")
    if ((policy["schema_version"] == "1.0.0" and set(policy) != base_fields)
            or (policy["schema_version"] == "1.1.0"
                and (policy.get("request_protocol") != "stockqa-route-confidence-1"
                     or policy.get("partial_dispatch") != "common_and_mandatory_risk"))
            or (policy["schema_version"] == "1.2.0"
                and (set(policy) != confidence_fields or policy.get("router_version") != "2.2.0"
                     or policy.get("request_protocol") != "stockqa-route-confidence-2"
                     or policy.get("partial_dispatch") != "common_and_mandatory_risk"))
            or (policy["schema_version"] == "1.3.0"
                and (set(policy) != confidence_fields
                     or tuple(int(part) for part in policy["router_version"].split(".")) < (2, 3, 0)
                     or policy.get("request_protocol") != "stockqa-route-confidence-3"
                     or policy.get("partial_dispatch") != "common_and_mandatory_risk"))
            or (policy["schema_version"] == "1.0.0" and policy.get("router_version") != "2.0.0")
            or (policy["schema_version"] == "1.1.0" and policy.get("router_version") != "2.1.0")):
        raise ValueError("routing policy has an unsupported request protocol")
    if policy["schema_version"] in {"1.2.0", "1.3.0"}:
        gate = policy["classification_confidence_gate"]
        if (not isinstance(gate, dict) or set(gate) != {"minimum_score", "below_threshold"}
                or type(gate["minimum_score"]) is not int or not 1 <= gate["minimum_score"] <= 10
                or gate["below_threshold"] != "mark_llm_candidates_uncertain"):
            raise ValueError("invalid classification confidence gate")
    material = policy["materiality"]
    if not isinstance(material, dict) or set(material) != {"enter_share", "retain_share", "strategic_share", "share_metrics", "strategic_metrics", "exit_confirmation_periods", "switch_confirmation_periods", "major_event_can_override"}:
        raise ValueError("incomplete materiality policy")
    if (any(type(material[k]) not in (int, float) for k in ("enter_share", "retain_share", "strategic_share"))
            or not 0 <= material["retain_share"] < material["enter_share"] <= 1
            or not 0 < material["strategic_share"] <= 1
            or set(material["share_metrics"]) != BASE_SHARES
            or set(material["strategic_metrics"]) != STRATEGIC_SHARES
            or type(material["exit_confirmation_periods"]) is not int or material["exit_confirmation_periods"] < 2
            or type(material["switch_confirmation_periods"]) is not int
            or material["switch_confirmation_periods"] < 2
            or type(material["major_event_can_override"]) is not bool):
        raise ValueError("invalid materiality or hysteresis thresholds")
    rules = policy["rules"]
    if (not isinstance(rules, list) or any(not isinstance(r, dict) or "module_id" not in r for r in rules)
            or [r["module_id"] for r in rules] != sorted(modules)
            or len(rules) != len(modules)):
        raise ValueError("routing policy must cover each released module exactly once")
    for rule in rules:
        if set(rule) != {"module_id", "axis", "predicate", "minimum_confidence", "evidence_tags", "excluded_tags", "mandatory_question_ids"}:
            raise ValueError("incomplete routing rule")
        module = modules[rule["module_id"]]
        axis = "cycle" if rule["module_id"] == "cyclical" else AXES[module["kind"]]
        if rule["axis"] != axis or rule["predicate"] not in PREDICATES or rule["minimum_confidence"] not in {"medium", "high"}:
            raise ValueError("unknown routing axis or predicate")
        allowed = {"common": {"always"}, "type": {"type_evidence"}, "industry": {"industry_evidence"},
                   "lifecycle": {"lifecycle_evidence"}, "cycle": {"cycle_evidence"}, "attribute": {"attribute_evidence"},
                   "diagnostic": {"user_diagnostic", "default_diagnostic", "recovery_evidence"}, "lens": {"user_lens"},
                   "common_extension": {"common_extension"}}
        if rule["predicate"] not in allowed[axis] or (rule["predicate"] == "recovery_evidence") != (rule["module_id"] == "recovery"):
            raise ValueError("predicate does not match module purpose")
        if "activation" in module:
            activation = module["activation"]
            expected_mode = "manual" if axis == "lens" else "diagnostic" if axis == "diagnostic" else "automatic"
            if (activation["mode"] != expected_mode
                    or (activation["minimum_confidence"] == "high" and rule["minimum_confidence"] != "high")):
                raise ValueError("routing policy weakens declared module activation")
        for key in ("evidence_tags", "excluded_tags", "mandatory_question_ids"):
            values = rule[key]
            if (not isinstance(values, list) or len(values) != len(set(values))
                    or any(not isinstance(x, str) or not x for x in values)):
                raise ValueError("invalid rule tags or mandatory IDs")
        if set(rule["evidence_tags"]) & set(rule["excluded_tags"]):
            raise ValueError("routing evidence and exclusion conflict")
        if not set(rule["mandatory_question_ids"]) <= {q["id"] for q in module["questions"]}:
            raise ValueError("mandatory question is outside its module")
        if (tuple(map(int, policy["router_version"].split("."))) >= (2, 5, 0)
                and rule["predicate"] == "default_diagnostic"
                and set(rule["mandatory_question_ids"]) != {q["id"] for q in module["questions"]}):
            raise ValueError("policy cannot drop mandatory basic diagnostic questions")
    by_id = {r["module_id"]: r for r in rules}
    for module_id, ids in {"distressed": {"DISTRESSED_01", "DISTRESSED_02"},
                           "recovery": {f"RECOVERY_{i:02}" for i in range(1, 5)}}.items():
        if module_id in by_id and set(by_id[module_id]["mandatory_question_ids"]) != ids:
            raise ValueError("policy cannot drop mandatory distress/recovery questions")
    mc.digest(policy)

