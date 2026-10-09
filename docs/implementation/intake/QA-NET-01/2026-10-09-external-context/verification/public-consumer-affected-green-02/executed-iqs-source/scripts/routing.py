"""S06 pure, evidence-bound routing. No network, model client or company store.

verified_facts, identity_ref and user_policy are trusted caller inputs; model
candidates are a separate argument and cannot overwrite identity or receipts.
The caller must authenticate those inputs. This module does not verify URLs by
fetching their contents and must not be described as a live evidence reviewer.
"""
from __future__ import annotations

import copy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import module_contract as mc
import module_registry as registry

ROOT = Path(__file__).resolve().parents[1]
ROUTER_VERSION = "2.3.0"
AXES = {"common": "common", "types": "type", "industries": "industry", "stages": "lifecycle",
        "overlays": "attribute", "diagnostics": "diagnostic", "lenses": "lens",
        "common_extensions": "common_extension"}
PREDICATES = {"always", "type_evidence", "industry_evidence", "lifecycle_evidence",
              "cycle_evidence", "attribute_evidence", "user_diagnostic", "recovery_evidence",
              "user_lens", "common_extension"}
POSITION = {"upturn", "peak", "downturn", "trough", "recovery", "unknown"}
RECOVERY_POSITIONS = {"downturn", "trough", "recovery"}
BASE_SHARES = {"revenue_share", "gross_profit_share", "invested_capital_share"}
STRATEGIC_SHARES = {"committed_capex_share", "binding_backlog_share"}
SHARES = BASE_SHARES | STRATEGIC_SHARES
FACT_KEYS = {"module_id", "confidence", "evidence_type", "rationale", "sources",
             "materiality", "cycle_position", "business_id", "period_count", "major_event"}


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("trusted routing clock must be an ISO UTC string")
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant.utcoffset() != timezone.utc.utcoffset(instant):
        raise ValueError("trusted routing clock must be UTC")
    return instant


def _current_router_compatible(version):
    """Router 2.2 defines the confidence protocol; later 2.x policy releases retain it."""
    if not isinstance(version, str) or not re.fullmatch(r"2\.\d+\.\d+", version):
        return False
    return tuple(map(int, version.split("."))) >= (2, 2, 0)


def resolve_module_dependency_closure(selected_module_ids, modules, module_decisions=None):
    """Return a stable dependency-complete selection and fail-closed issues.

    When route decisions are supplied, dependencies must already be selected by
    the evidence/policy layer. Without decisions, this pure helper expands the
    graph for callers that only need to normalize a proposed selection.
    """
    if (not isinstance(selected_module_ids, (list, tuple, set, frozenset))
            or not isinstance(modules, dict)):
        return {"module_ids": [], "issues": ["module_selection_invalid"]}

    issues = set()
    states = None
    if module_decisions is not None:
        if isinstance(module_decisions, dict):
            states = {key: value.get("decision") if isinstance(value, dict) else value
                      for key, value in module_decisions.items()}
        elif isinstance(module_decisions, list):
            states = {}
            for item in module_decisions:
                if not isinstance(item, dict) or not isinstance(item.get("module_id"), str):
                    issues.add("module_decisions_invalid")
                    continue
                module_id = item["module_id"]
                if module_id in states:
                    issues.add(f"module_decision_duplicate:{module_id}")
                states[module_id] = item.get("decision")
        else:
            return {"module_ids": [], "issues": ["module_decisions_invalid"]}

    roots = set()
    for module_id in selected_module_ids:
        if not isinstance(module_id, str) or not module_id:
            issues.add("module_id_invalid")
        else:
            roots.add(module_id)

    closure = set()
    visiting = []
    visited = set()

    def visit(module_id, parent=None):
        if module_id not in modules:
            if parent is None:
                issues.add(f"module_missing:{module_id}")
            else:
                issues.add(f"dependency_missing:{parent}:{module_id}")
            return
        if module_id in visiting:
            cycle = visiting[visiting.index(module_id):] + [module_id]
            issues.add("dependency_cycle:" + "->".join(cycle))
            return
        if module_id in visited:
            return
        closure.add(module_id)
        if states is not None and states.get(module_id) != "selected":
            state = states.get(module_id) or "missing_decision"
            if parent is None:
                issues.add(f"module_not_selected:{module_id}:{state}")
            else:
                issues.add(f"dependency_not_selected:{parent}:{module_id}:{state}")
        visiting.append(module_id)
        dependencies = modules[module_id].get("dependencies", [])
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            issues.add(f"dependency_list_invalid:{module_id}")
            dependencies = []
        for dependency in sorted(set(dependencies)):
            visit(dependency, parent=module_id)
        visiting.pop()
        visited.add(module_id)

    for module_id in sorted(roots):
        visit(module_id)

    selected_for_conflicts = (closure if states is None else
                              {module_id for module_id in closure if states.get(module_id) == "selected"})
    for index, left in enumerate(sorted(selected_for_conflicts)):
        left_conflicts = set(modules[left].get("conflicts", []))
        for right in sorted(selected_for_conflicts)[index + 1:]:
            right_conflicts = set(modules[right].get("conflicts", []))
            if right in left_conflicts or left in right_conflicts:
                issues.add(f"selected_conflict:{left}:{right}")

    kind_priority = {"common": 0, "common_extensions": 1, "types": 2, "industries": 3,
                     "stages": 4, "overlays": 5, "diagnostics": 6, "lenses": 7}
    indegree = {module_id: 0 for module_id in closure}
    dependents = {module_id: set() for module_id in closure}
    for module_id in closure:
        dependencies = modules[module_id].get("dependencies", [])
        if isinstance(dependencies, list):
            for dependency in set(dependencies) & closure:
                indegree[module_id] += 1
                dependents[dependency].add(module_id)

    def order_key(module_id):
        return (kind_priority.get(modules[module_id].get("kind"), 99), module_id)

    ready = sorted((module_id for module_id, count in indegree.items() if count == 0), key=order_key)
    ordered = []
    while ready:
        module_id = ready.pop(0)
        ordered.append(module_id)
        for dependent in sorted(dependents[module_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=order_key)
    if len(ordered) != len(closure):
        ordered.extend(sorted(closure - set(ordered), key=order_key))
    return {"module_ids": ordered, "issues": sorted(issues)}


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
                   "diagnostic": {"user_diagnostic", "recovery_evidence"}, "lens": {"user_lens"},
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
    by_id = {r["module_id"]: r for r in rules}
    for module_id, ids in {"distressed": {"DISTRESSED_01", "DISTRESSED_02"},
                           "recovery": {f"RECOVERY_{i:02}" for i in range(1, 5)}}.items():
        if module_id in by_id and set(by_id[module_id]["mandatory_question_ids"]) != ids:
            raise ValueError("policy cannot drop mandatory distress/recovery questions")
    mc.digest(policy)


def publish_routing_package(*, root=ROOT, renderer_version, renderer_rules_sha256, activate=False):
    policy = registry._read_json(Path(root) / "questions/routing-policy.v2.json")
    return registry.publish(root=Path(root), renderer_version=renderer_version,
                            router_version=policy["router_version"], renderer_rules_sha256=renderer_rules_sha256,
                            routing_policy=policy, activate=activate)


def _identity(route_input):
    required = ("entity_id", "identity_ref", "company", "ticker", "exchange", "as_of")
    if any(not isinstance(route_input.get(k), str) or not route_input[k].strip() for k in required):
        raise ValueError("routing requires trusted resolved identity and information cutoff")
    date.fromisoformat(route_input["as_of"])
    out = {k: route_input[k] for k in required}
    out.update(security_id=route_input.get("security_id"), segment_id=route_input.get("segment_id"))
    for key in ("security_class", "reporting_currency", "quote_currency", "quote_date", "accounting_standard", "fiscal_year_end"):
        if key in route_input:
            out[key] = route_input[key]
    return out


def build_route_request(route_input, *, package_id, root=ROOT):
    identity = _identity(route_input)
    package, modules, release, _ = registry.load_package(package_id, root=Path(root))
    policy = registry.load_routing_policy(package_id, root=Path(root))
    rules = {r["module_id"]: r for r in policy["rules"]}
    candidates = [{"module_id": k, "name": modules[k]["name"], "applies_when": modules[k]["applies_when"],
                   "rule": rules[k], "activation": modules[k].get("activation")}
                  for k in sorted(modules)]
    prompt = ("[ROUTE_02] Search public sources only; do not download company documents. "
              "Return schema_version=2.0.0, question_id=ROUTE_02 and candidates[]. "
              "Each candidate requires module_id, confidence(high/medium/low), evidence_type, rationale, sources "
              "(title/url/published_at/entity_id/claim). Optional materiality uses disclosed, comparable 0..1 "
              "revenue_share/gross_profit_share/invested_capital_share/committed_capex_share/binding_backlog_share; "
              "survival_critical and primary_development_project are booleans. Unknown denominators stay unknown, "
              "never estimate a share. Use business_id to identify one economic business across labels. "
              "period_count means consecutive annual disclosures supporting that condition; cycle_position uses "
              "upturn/peak/downturn/trough/recovery/unknown. Do not invent execution receipts, identity, "
              "manual overrides or user investment lenses. A price fall or concept label is insufficient. "
              "Unknown industry is not other. Give conflicting candidates when evidence conflicts.\n"
              + mc.canonical_bytes({"identity": identity, "modules": candidates}).decode("utf-8"))
    protocol = policy.get("request_protocol", "candidate-only-1")
    if protocol in {"stockqa-route-confidence-1", "stockqa-route-confidence-2", "stockqa-route-confidence-3"}:
        confidence_instruction = ""
        if protocol in {"stockqa-route-confidence-2", "stockqa-route-confidence-3"}:
            threshold = policy["classification_confidence_gate"]["minimum_score"]
            confidence_instruction = (f"The overall score is classification-evidence confidence only. The frozen policy threshold is {threshold}; "
                                      "below it the system keeps model candidates uncertain. This score never overrides "
                                      "deterministic verified facts or per-module evidence rules. ")
        prompt = ("Return only a StockQA native JSON object with question_id=ROUTE_02, "
                  "entity_id and company_name exactly as in the trusted identity below, "
                  "status, score, and description. The score assesses classification evidence only "
                  "(1=weak/ambiguous, 5=partly supported, 10=consistent verified sources); it is NEVER "
                  "a company investment score. Use status=scored and an integer 1..10 when you can "
                  "provide sourced candidates. If none can be sourced, use status=unknown or "
                  "insufficient_evidence with score=null and candidates=[]. Never use a placeholder 5. "
                  "description must be the serialized JSON string of the candidate envelope specified next. "
                  + confidence_instruction + prompt)
    exported = {"question_id": "ROUTE_02", "text": prompt} if protocol in {
        "stockqa-route-confidence-1", "stockqa-route-confidence-2", "stockqa-route-confidence-3"} else prompt
    return {"question_id": "ROUTE_02", "module_package_id": package["package_id"],
            "release_id": release["release_id"], "routing_policy_sha256": release["routing_policy_sha256"],
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "request_protocol": protocol,
            "questions": [{"category": "路由候选（不计企业分）", "questions": [exported]}]}


def parse_route_response(value, route_input):
    """Read the existing StockQA native envelope; never interpret its score as company quality."""
    identity = _identity(route_input)
    if isinstance(value, str):
        value = json.loads(value, object_pairs_hook=mc._unique_object)
    if isinstance(value, dict) and value.get("schema_version") in {
            "stockqa.quick_scan_result/1.0.0", "stockqa.quick_scan_result/1.1.0"}:
        import stockqa_adapter
        trusted_identity = dict(identity)
        if "identity_snapshot_sha256" in route_input:
            trusted_identity["identity_snapshot_sha256"] = route_input["identity_snapshot_sha256"]
        return stockqa_adapter.adapt_quick_scan_result(value, trusted_identity)
    required = {"question_id", "entity_id", "company_name", "status", "score", "description"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("ROUTE_02 requires the exact native response envelope")
    if (value["question_id"] != "ROUTE_02" or value["entity_id"] != identity["entity_id"]
            or value["company_name"] != identity["company"]):
        raise ValueError("native routing response identity mismatch")
    if value["status"] not in {"scored", "unknown", "insufficient_evidence"}:
        raise ValueError("invalid native classification status")
    if value["status"] == "scored":
        if type(value["score"]) is not int or not 1 <= value["score"] <= 10:
            raise ValueError("classification confidence must be an integer 1..10")
    elif value["score"] is not None:
        raise ValueError("unscored classification must use null, never a placeholder score")
    if not isinstance(value["description"], str):
        raise ValueError("native routing description must be serialized candidate JSON")
    candidate = json.loads(value["description"], object_pairs_hook=mc._unique_object)
    if (not isinstance(candidate, dict) or set(candidate) != {"schema_version", "question_id", "candidates"}
            or candidate["schema_version"] != "2.0.0" or candidate["question_id"] != "ROUTE_02"
            or not isinstance(candidate["candidates"], list)):
        raise ValueError("invalid native candidate envelope or inner identity")
    if value["status"] != "scored" and candidate["candidates"]:
        raise ValueError("unscored classification cannot assert usable model candidates")
    if value["status"] == "scored" and not candidate["candidates"]:
        raise ValueError("scored classification requires at least one sourced candidate")
    return {"candidate": candidate,
            "answer_sha256": hashlib.sha256(mc.canonical_bytes(value)).hexdigest(),
            "classification_confidence": {"status": value["status"], "score": value["score"]}}


def _fact(fact, identity, rules):
    if (not isinstance(fact, dict) or set(fact) - FACT_KEYS
            or not {"module_id", "confidence", "evidence_type", "rationale", "sources"} <= set(fact)):
        raise ValueError("invalid route candidate fields")
    if fact["module_id"] not in rules:
        raise ValueError("unknown route module ID")
    if fact["confidence"] not in {"high", "medium", "low"} or not isinstance(fact["rationale"], str) or not fact["rationale"].strip():
        raise ValueError("candidate needs confidence and rationale")
    if not isinstance(fact["sources"], list) or not fact["sources"]:
        raise ValueError("objective candidate needs source evidence")
    for source in fact["sources"]:
        mc._validate(mc.ROUTE_SCHEMA["$defs"]["SourceV2"], source)
        if source["entity_id"] != identity["entity_id"] or (source["published_at"] != "unknown" and source["published_at"] > identity["as_of"]):
            raise ValueError("candidate source identity or cutoff mismatch")
    result = copy.deepcopy(fact)
    result["sources"] = sorted(result["sources"], key=mc.canonical_bytes)
    material = result.get("materiality", {})
    if not isinstance(material, dict) or set(material) - (SHARES | {"survival_critical", "primary_development_project"}):
        raise ValueError("unknown materiality measure")
    if any(type(v) not in (int, float) or not 0 <= v <= 1 for k, v in material.items() if k in SHARES):
        raise ValueError("materiality shares must be finite fractions, not booleans")
    if any(type(material[k]) is not bool for k in ("survival_critical", "primary_development_project") if k in material):
        raise ValueError("survival/project materiality must be boolean")
    if type(result.get("period_count", 1)) is not int or result.get("period_count", 1) < 1 or type(result.get("major_event", False)) is not bool:
        raise ValueError("invalid event or confirmation count")
    if "cycle_position" in result and result["cycle_position"] not in POSITION:
        raise ValueError("unknown cycle position")
    if "business_id" in result and (not isinstance(result["business_id"], str) or not result["business_id"].strip()):
        raise ValueError("business reference must be nonempty text, not an invented segment ID")
    mc.digest(result)
    return result


def _completed_search_urls(receipt):
    """Only the selected, completed provider search call can attest model URLs."""
    if not isinstance(receipt, dict):
        return frozenset()
    if "search_binding" in receipt:
        import stockqa_adapter
        return stockqa_adapter.external_search_urls(receipt, entity_id=receipt.get("entity_id"),
            question_id="ROUTE_02", route_receipt=True)
    calls = receipt.get("web_search_calls")
    if not isinstance(calls, list):
        return frozenset()
    selected = [call for call in calls if isinstance(call, dict)
                and call.get("id") == receipt.get("search_receipt_id")]
    if len(selected) != 1:
        return frozenset()
    call = selected[0]
    if call.get("status") != "completed" or call.get("action_type") != "search":
        return frozenset()
    urls = call.get("source_urls")
    if not isinstance(urls, list) or not urls:
        return frozenset()
    return frozenset(urls)


def resolve_route_decision(route_input, *, package_id, route_response=None, execution_receipt=None,
                           user_policy=None, previous_decision=None,
                           expected_previous_decision_id=None,
                           now_utc, root=ROOT):
    identity = _identity(route_input)
    now = _utc(now_utc)
    if now.date() < date.fromisoformat(identity["as_of"]):
        raise ValueError("decision cannot precede information cutoff")
    package, modules, release, _ = registry.load_package(package_id, root=Path(root))
    policy = registry.load_routing_policy(package_id, root=Path(root))
    if not _current_router_compatible(release["router_version"]):
        raise ValueError(f"historical router {release['router_version']} package is read only")
    rules = {r["module_id"]: r for r in policy["rules"]}
    requested_mode = route_input.get("requested_mode", "quick")
    if requested_mode not in {"quick", "full"}:
        raise ValueError("unknown route mode")
    scope_compatible = route_input.get("compatible_business_scope")
    if scope_compatible is not None and type(scope_compatible) is not bool:
        raise ValueError("business scope compatibility must be true, false or unknown")
    prior = set()
    if previous_decision is None and expected_previous_decision_id is not None:
        raise ValueError("expected previous route identity supplied without a previous route")
    if previous_decision is not None:
        validate_route_snapshot(previous_decision, root=root)
        if (not isinstance(expected_previous_decision_id, str)
                or not re.fullmatch(r"route_[a-f0-9]{64}", expected_previous_decision_id)
                or expected_previous_decision_id != previous_decision["decision_id"]):
            raise ValueError("previous route decision identity mismatch; caller-held identity is required")
        if (previous_decision["entity_id"] != identity["entity_id"]
                or previous_decision["segment_id"] != identity["segment_id"]
                or previous_decision["as_of"] > identity["as_of"]):
            raise ValueError("previous route identity, scope or cutoff mismatch")
        if (previous_decision["router_version"] != policy["router_version"]
                or previous_decision["routing_policy_sha256"] != release["routing_policy_sha256"]):
            raise ValueError("previous route uses an incompatible router or routing policy; explicit migration required")
        previous_modules = {item["module_id"]: item for item in previous_decision["module_decisions"]}
        for module_id in (item["module_id"] for item in previous_decision["module_decisions"]
                          if item["decision"] == "selected"):
            previous_module = previous_modules[module_id]
            current_module = modules.get(module_id)
            if (current_module is None
                    or previous_module.get("module_version") != current_module.get("version")):
                raise ValueError("previous route selected module version is incompatible; explicit migration required")
        prior = {x["module_id"] for x in previous_decision["module_decisions"] if x["decision"] == "selected"}
    user_policy = copy.deepcopy(user_policy or {})
    if set(user_policy) - {"diagnostics", "enabled_lenses", "manual_overrides"}:
        raise ValueError("unknown user routing policy field")
    confidence_gate = policy.get("classification_confidence_gate")
    minimum_confidence_score = confidence_gate["minimum_score"] if confidence_gate else None
    facts = {}
    unbound_sources = set()
    parsed_response = parse_route_response(route_response, route_input) if route_response is not None else None
    if parsed_response is not None:
        bound_receipt = parsed_response.get("execution_receipt")
        if bound_receipt is not None:
            if execution_receipt is not None and execution_receipt != bound_receipt:
                raise ValueError("separate execution receipt differs from the bound StockQA result")
            execution_receipt = bound_receipt
        candidate = parsed_response["candidate"]
        classification_confidence = parsed_response["classification_confidence"]
        answer_sha256 = parsed_response["answer_sha256"]
    else:
        candidate = None
        classification_confidence = None
        answer_sha256 = None
    if candidate is None:
        if execution_receipt is not None or classification_confidence is not None:
            raise ValueError("classification confidence and receipt require a parsed response")
        normalized_confidence = {"status": "not_run", "score": None}
    else:
        candidate_list = candidate.get("candidates") if isinstance(candidate, dict) else None
        if (not isinstance(classification_confidence, dict)
                or set(classification_confidence) != {"status", "score"}
                or classification_confidence["status"] not in {"scored", "unknown", "insufficient_evidence"}):
            raise ValueError("current route requires parsed classification confidence")
        status, score = classification_confidence["status"], classification_confidence["score"]
        if ((status == "scored" and (type(score) is not int or not 1 <= score <= 10
                                      or not candidate_list))
                or (status != "scored" and (score is not None or candidate_list))):
            raise ValueError("classification status and candidate score/content disagree")
        normalized_confidence = {"status": status, "score": score}
    if candidate is not None:
        if (not isinstance(candidate, dict) or set(candidate) != {"schema_version", "question_id", "candidates"}
                or candidate["schema_version"] != "2.0.0" or candidate["question_id"] != "ROUTE_02"
                or not isinstance(candidate["candidates"], list)):
            raise ValueError("invalid ROUTE_02 candidate envelope")
        request = build_route_request(route_input, package_id=package_id, root=root)
        receipt_schema = mc.ROUTE_SCHEMA["$defs"]["RouteV2"]["properties"]["execution"]["anyOf"][1]
        mc._validate(receipt_schema, execution_receipt)
        if request["request_protocol"] == "stockqa-route-confidence-3":
            if (not isinstance(answer_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", answer_sha256)
                    or execution_receipt.get("answer_sha256") != answer_sha256):
                raise ValueError("parsed answer hash differs from execution receipt")
        if (execution_receipt.get("classification_status") != normalized_confidence["status"]
                or execution_receipt.get("classification_score") != normalized_confidence["score"]):
            raise ValueError("search receipt classification confidence differs from parsed response")
        if (execution_receipt["entity_id"] != identity["entity_id"] or execution_receipt["as_of"] != identity["as_of"]
                or execution_receipt["prompt_sha256"] != request["prompt_sha256"]
                or not date.fromisoformat(identity["as_of"]) <= _utc(execution_receipt["answered_at"]).date()
                or _utc(execution_receipt["answered_at"]) > now):
            raise ValueError("search receipt does not bind this identity, prompt and cutoff")
        trusted_urls = _completed_search_urls(execution_receipt)
        candidate_ids = set()
        for raw in candidate["candidates"]:
            fact = _fact(raw, identity, rules)
            if fact["module_id"] in candidate_ids:
                raise ValueError("duplicate candidate module")
            candidate_ids.add(fact["module_id"])
            if not trusted_urls or any(source["url"] not in trusted_urls for source in fact["sources"]):
                if rules[fact["module_id"]]["predicate"] not in {"always", "user_diagnostic", "user_lens"}:
                    unbound_sources.add(fact["module_id"])
                continue
            facts[fact["module_id"]] = (fact, "searched_llm")
    elif execution_receipt is not None:
        raise ValueError("search receipt without candidates")
    verified_ids = set()
    for raw in route_input.get("verified_facts", []):
        fact = _fact(raw, identity, rules)
        if fact["module_id"] in verified_ids:
            raise ValueError("duplicate verified fact module")
        verified_ids.add(fact["module_id"])
        facts[fact["module_id"]] = (fact, "deterministic")
        unbound_sources.discard(fact["module_id"])
    decisions = {}
    def decision(mid, state="uncertain", basis="unavailable", confidence="low", reason="missing_evidence", rationale="No verified classification evidence", sources=None, override=None):
        item = {"module_id": mid, "module_version": modules[mid]["version"], "decision": state,
                "basis": basis, "confidence": confidence, "rationale": rationale, "sources": sources or [],
                "rule_id": rules[mid]["predicate"], "reason_code": reason}
        if mid in facts:
            item["evidence_context"] = {k: copy.deepcopy(v) for k, v in facts[mid][0].items()
                                        if k not in {"module_id", "confidence", "rationale", "sources"}}
        if override is not None:
            item["manual_override"] = override
        decisions[mid] = item
    for mid, rule in rules.items():
        decision(mid)
        if rule["predicate"] == "always":
            decision(mid, "selected", "policy", "high", "universal_core", "Universal core")
        elif rule["predicate"] in {"user_diagnostic", "user_lens"}:
            decision(mid, "rejected", "policy", "high", "not_requested", "No explicit user research request")
        elif mid in unbound_sources:
            decision(mid, "uncertain", "unavailable", "low", "unbound_search_source",
                     "Candidate source was not returned by the completed provider search")
        elif mid in facts:
            fact, basis = facts[mid]
            tag = fact["evidence_type"]
            if tag in rule["excluded_tags"] or tag not in rule["evidence_tags"]:
                decision(mid, "rejected", basis, fact["confidence"], "evidence_not_applicable", fact["rationale"], fact["sources"])
                continue
            if (basis == "searched_llm" and minimum_confidence_score is not None
                    and (normalized_confidence["status"] != "scored"
                         or normalized_confidence["score"] < minimum_confidence_score)):
                decision(mid, "uncertain", basis, "low", "overall_confidence_below_threshold",
                         fact["rationale"], fact["sources"])
                continue
            if fact["confidence"] == "low" or (rule["minimum_confidence"] == "high" and fact["confidence"] != "high"):
                decision(mid, "uncertain", basis, "low", "low_confidence", fact["rationale"], fact["sources"])
                continue
            if rule["axis"] == "industry":
                material = fact.get("materiality", {})
                if not material and not (fact.get("major_event", False) and policy["materiality"]["major_event_can_override"]):
                    decision(mid, "uncertain", basis, "low", "missing_materiality", fact["rationale"], fact["sources"])
                    continue
                thresholds = policy["materiality"]
                relevant = (material.get("survival_critical") or material.get("primary_development_project")
                            or (fact.get("major_event", False) and thresholds["major_event_can_override"])
                            or any(material.get(k, 0) >= thresholds["strategic_share"] for k in STRATEGIC_SHARES))
                if mid in prior:
                    # Exit needs two consecutive annual observations covering all
                    # three comparable base denominators, with no strategic trigger.
                    exit_confirmed = (BASE_SHARES <= material.keys()
                                      and all(material[k] < thresholds["retain_share"] for k in BASE_SHARES)
                                      and fact.get("period_count", 1) >= thresholds["exit_confirmation_periods"])
                    retain_evidence = (any(material.get(k, 0) >= thresholds["retain_share"] for k in BASE_SHARES)
                                       or (BASE_SHARES <= material.keys() and not exit_confirmed))
                    if not relevant and not retain_evidence and not BASE_SHARES <= material.keys():
                        decision(mid, "uncertain", basis, "low", "missing_comparable_denominators", fact["rationale"], fact["sources"])
                        continue
                    relevant = relevant or retain_evidence
                else:
                    relevant = relevant or any(material.get(k, 0) >= thresholds["enter_share"] for k in BASE_SHARES)
                if not relevant:
                    decision(mid, "rejected", basis, fact["confidence"], "below_materiality", fact["rationale"], fact["sources"])
                    continue
            if (previous_decision and mid not in prior and rule["axis"] in {"type", "lifecycle"}
                    and fact.get("period_count", 1) < policy["materiality"]["switch_confirmation_periods"]
                    and not (fact.get("major_event", False) and policy["materiality"]["major_event_can_override"])):
                decision(mid, "uncertain", basis, "low", "confirmation_pending", fact["rationale"], fact["sources"])
                continue
            decision(mid, "selected", basis, fact["confidence"], "evidence_supported", fact["rationale"], fact["sources"])
    for mid, reason in user_policy.get("diagnostics", {}).items():
        if mid not in rules or rules[mid]["predicate"] != "user_diagnostic" or not isinstance(reason, str) or not reason.strip():
            raise ValueError("unknown diagnostic or missing user rationale")
        decision(mid, "selected", "policy", "high", "user_requested", reason)
    overrides = list(user_policy.get("manual_overrides", []))
    for mid, approval in user_policy.get("enabled_lenses", {}).items():
        if mid not in rules or rules[mid]["predicate"] != "user_lens":
            raise ValueError("unknown user investment lens")
        if not isinstance(approval, dict) or set(approval) != {"actor", "reason", "valid_until"}:
            raise ValueError("lens approval must not override module identity or decision")
        overrides.append({"module_id": mid, "decision": "selected", **approval})
    seen_overrides = set()
    for override in overrides:
        if (set(override) != {"module_id", "decision", "actor", "reason", "valid_until"}
                or override["module_id"] not in rules or override["module_id"] in seen_overrides
                or override["decision"] not in {"selected", "rejected"}
                or not all(isinstance(override[k], str) and override[k].strip() for k in ("actor", "reason"))
                or _utc(override["valid_until"]) <= now):
            raise ValueError("invalid or expired manual override")
        mid = override["module_id"]; seen_overrides.add(mid)
        if mid == "common" and override["decision"] != "selected":
            raise ValueError("manual override cannot remove common")
        if mid == "distressed" and decisions[mid]["decision"] == "selected" and override["decision"] == "rejected":
            raise ValueError("manual override cannot suppress evidenced distress coverage")
        decision(mid, override["decision"], "manual", "high", "user_override", override["reason"], override={k: override[k] for k in ("actor", "reason", "valid_until")})
    gaps = [f"unbound_search_source:{mid}" for mid in sorted(unbound_sources)]
    if unbound_sources:
        gaps.append("unbound_search_source")
    if (minimum_confidence_score is not None and normalized_confidence["status"] == "scored"
            and normalized_confidence["score"] < minimum_confidence_score):
        gaps.append("classification_confidence_below_threshold")
    for axis in ("type", "lifecycle"):
        selected = [mid for mid, d in decisions.items() if rules[mid]["axis"] == axis and d["decision"] == "selected"]
        if len(selected) > 1:
            rank = {"manual": 3, "deterministic": 2, "searched_llm": 1}
            highest = max(rank[decisions[mid]["basis"]] for mid in selected)
            strongest = [mid for mid in selected if rank[decisions[mid]["basis"]] == highest]
            if len(strongest) == 1:
                for mid in set(selected) - set(strongest):
                    decisions[mid].update(decision="rejected", reason_code="trusted_axis_precedence")
            else:
                gaps.append("conflicting_" + axis)
                for mid in selected:
                    decisions[mid].update(decision="uncertain", confidence="low", reason_code="conflicting_axis_evidence")
    selected = {mid for mid, d in decisions.items() if d["decision"] == "selected"}
    main_type = next((mid for mid in selected if rules[mid]["axis"] == "type"), None)
    stage = next((mid for mid in selected if rules[mid]["axis"] == "lifecycle"), None)
    for mid in sorted(selected):
        if rules[mid]["axis"] != "industry" or mid not in facts:
            continue
        fact = facts[mid][0]
        material = fact.get("materiality", {})
        if material.get("primary_development_project") and main_type != "pre_revenue":
            decisions[mid].update(decision="uncertain", confidence="low", reason_code="pre_revenue_type_unconfirmed")
            selected.remove(mid)
    business_modules = {}
    for mid in sorted(selected):
        if rules[mid]["axis"] == "industry" and mid in facts and facts[mid][0].get("business_id"):
            business_modules.setdefault(facts[mid][0]["business_id"], []).append(mid)
    for mids in business_modules.values():
        if len(mids) > 1:
            gaps.append("duplicate_business_classification")
            for mid in mids:
                selected.remove(mid)
                decisions[mid].update(decision="uncertain", confidence="low", reason_code="duplicate_business_classification")
    industries = sorted(mid for mid in selected if rules[mid]["axis"] == "industry")
    cycle = "cyclical" in selected
    position = facts.get("cyclical", ({}, None))[0].get("cycle_position", "unknown") if cycle else "unknown"
    triggers = sorted(selected & {"distressed", "turnaround", "declining"})
    if cycle and position in RECOVERY_POSITIONS:
        triggers.append("cyclical")
    if triggers:
        if decisions["recovery"]["basis"] == "manual" and decisions["recovery"]["decision"] == "rejected":
            raise ValueError("manual override cannot suppress triggered recovery coverage")
        sources = {mc.digest(s): s for mid in triggers for s in decisions[mid]["sources"]}
        # Manual-only triggers retain their original user authorization and TTL.
        if sources:
            decision("recovery", "selected", "deterministic", "high", "recovery_trigger", "Recovery review triggered by " + ",".join(triggers), sorted(sources.values(), key=mc.canonical_bytes))
        else:
            trigger = decisions[triggers[0]]
            decision("recovery", "selected", "manual", "high", "recovery_trigger", trigger["rationale"], override=trigger["manual_override"])
        selected.add("recovery")
    module_selection = resolve_module_dependency_closure(
        selected, modules, {mid: item["decision"] for mid, item in decisions.items()})
    module_selection_issues = module_selection["issues"]
    gaps.extend(module_selection_issues)
    if not main_type: gaps.append("company_type_unresolved")
    if not stage: gaps.append("lifecycle_unresolved")
    if main_type in {"operating", "pre_revenue"} and not industries: gaps.append("industry_unresolved")
    dispatch_status = "ready"
    if set(gaps) & {"conflicting_type", "conflicting_lifecycle", "duplicate_business_classification"} or scope_compatible is False:
        dispatch_status = "requires_segments"
    elif len(industries) > 2:
        gaps.append("multi_business_coverage")
        if requested_mode == "quick":
            dispatch_status = "requires_full_or_segments"
        elif scope_compatible is not True:
            dispatch_status = "requires_segments"
            gaps.append("business_scope_unconfirmed")
    mandatory = sorted({qid for mid in selected for qid in rules[mid]["mandatory_question_ids"]})
    eligible = sorted(selected) if not module_selection_issues else []
    segment_requests = sorted({f.get("business_id", mid) for mid, (f, _) in facts.items()
                               if rules[mid]["axis"] == "industry"}) if dispatch_status == "requires_segments" else []
    if (policy.get("partial_dispatch") == "common_and_mandatory_risk"
            and set(gaps) & {"unbound_search_source", "company_type_unresolved", "lifecycle_unresolved", "industry_unresolved",
                             "conflicting_type", "conflicting_lifecycle", "duplicate_business_classification"}):
        eligible = sorted({"common"} | {mid for mid in selected if rules[mid]["mandatory_question_ids"]})
        dispatch_status = "ready_common_and_risk"
    if module_selection_issues:
        dispatch_status = "needs_review"
        eligible = []
    profile = {k: v for k, v in identity.items() if k != "identity_ref"}
    diagnostics = sorted(mid for mid in selected if rules[mid]["axis"] == "diagnostic")
    lenses = sorted(mid for mid in selected if rules[mid]["axis"] == "lens")
    profile.update(company_type=main_type, industry_modules=industries, stage=stage, business_subtype=None,
                   cycle_sensitive=True if cycle else None, cycle_position=position, recovery_review="recovery" in selected,
                   recovery_rationale=decisions["recovery"]["rationale"] if "recovery" in selected else "",
                   overlays=sorted(mid for mid in selected if rules[mid]["axis"] == "attribute"),
                   diagnostic_modules=diagnostics, diagnostic_rationale={mid: decisions[mid]["rationale"] for mid in diagnostics},
                   investment_lenses=lenses, lens_rationale={mid: decisions[mid]["rationale"] for mid in lenses})
    body = {"schema_version": "2.0.0", "module_package_id": package_id, "release_id": release["release_id"],
            "router_version": policy["router_version"], "routing_policy_sha256": release["routing_policy_sha256"],
            "identity_ref": identity["identity_ref"], "entity_id": identity["entity_id"], "as_of": identity["as_of"],
            "scope": "segment" if identity["segment_id"] else "entity", "segment_id": identity["segment_id"],
            "decided_at": now.isoformat().replace("+00:00", "Z"), "status": "partial" if gaps else "resolved",
            "previous_decision_id": previous_decision["decision_id"] if previous_decision else None,
            "execution": copy.deepcopy(execution_receipt), "profile_context": profile,
            "module_decisions": [decisions[mid] for mid in sorted(decisions)],
            "dispatch_plan": {"requested_mode": requested_mode, "resolved_mode": requested_mode,
                              "business_scope_compatible": scope_compatible,
                              "status": dispatch_status, "mandatory_question_ids": mandatory,
                              "minimum_questions": 24 + len(mandatory), "coverage_gaps": sorted(set(gaps)),
                              "segment_requests": segment_requests}}
    if policy.get("partial_dispatch") == "common_and_mandatory_risk":
        body["dispatch_plan"]["eligible_module_ids"] = eligible
    if minimum_confidence_score is not None:
        score = normalized_confidence["score"]
        body["classification_confidence"] = {
            **normalized_confidence,
            "minimum_score": minimum_confidence_score,
            "llm_candidates_eligible": (normalized_confidence["status"] == "scored"
                                         and score >= minimum_confidence_score),
        }
    result = mc.seal_route_decision(body)
    validate_route_snapshot(result, root=root)
    return result


def validate_route_snapshot(decision, *, root=ROOT):
    if decision.get("schema_version") != "2.0.0":
        raise ValueError("use legacy module contract for historical v1 route")
    package, modules, release, _ = registry.load_package(decision["module_package_id"], root=Path(root))
    policy = registry.load_routing_policy(decision["module_package_id"], root=Path(root))
    mc.validate_route_decision(decision, release, package=package)
    rules = {r["module_id"]: r for r in policy["rules"]}
    selected = set()
    for item in decision["module_decisions"]:
        mid = item["module_id"]; rule = rules[mid]
        if item["rule_id"] != rule["predicate"]:
            raise ValueError("route rule differs from frozen policy")
        if item["basis"] == "policy":
            allowed = {("always", "selected", "universal_core"), ("user_diagnostic", "selected", "user_requested"),
                       ("user_diagnostic", "rejected", "not_requested"), ("user_lens", "rejected", "not_requested")}
            if (rule["predicate"], item["decision"], item["reason_code"]) not in allowed:
                raise ValueError("policy basis cannot assert objective classification")
        if item["decision"] == "selected":
            selected.add(mid)
            if item["confidence"] == "low" or (rule["axis"] == "lens" and item["basis"] != "manual"):
                raise ValueError("unconfirmed or unauthorized selected module")
        if item["basis"] == "searched_llm" and decision["execution"] is None:
            raise ValueError("searched classification requires execution receipt")
        if item["basis"] == "searched_llm" and release["router_version"] != "2.0.0":
            trusted_urls = _completed_search_urls(decision["execution"])
            if not trusted_urls or any(source["url"] not in trusted_urls for source in item["sources"]):
                raise ValueError("searched classification source is not in completed search receipt")
        if item["basis"] in {"deterministic", "searched_llm"} and item["reason_code"] != "recovery_trigger":
            evidence = item.get("evidence_context")
            if evidence is None:
                raise ValueError("objective route decision requires frozen evaluation inputs")
            _fact({"module_id": mid, "confidence": item["confidence"], "rationale": item["rationale"],
                   "sources": item["sources"], **evidence}, decision, rules)
            if item["decision"] == "selected" and evidence["evidence_type"] not in rule["evidence_tags"]:
                raise ValueError("selected objective module has inapplicable evidence")
    for axis in ("type", "lifecycle"):
        if sum(rules[mid]["axis"] == axis for mid in selected) > 1:
            raise ValueError("route contains conflicting primary axes")
    module_selection = resolve_module_dependency_closure(
        selected, modules, {item["module_id"]: item["decision"] for item in decision["module_decisions"]})
    module_selection_issues = module_selection["issues"]
    profile = decision["profile_context"]
    receipt = decision["execution"]
    if receipt is not None:
        if "search_binding" in receipt:
            if tuple(map(int, release["router_version"].split("."))) < (2, 3, 0):
                raise ValueError("external search binding requires router 2.3 or newer")
            # Unknown classification has no searched module to trigger the
            # per-source loop above. Its original receipt must still be bound.
            _completed_search_urls(receipt)
        request = build_route_request({**profile, "identity_ref": decision["identity_ref"]},
                                      package_id=decision["module_package_id"], root=root)
        if (receipt["entity_id"] != decision["entity_id"] or receipt["as_of"] != decision["as_of"]
                or receipt["prompt_sha256"] != request["prompt_sha256"]
                or _utc(receipt["answered_at"]) > _utc(decision["decided_at"])
                or _utc(receipt["answered_at"]).date() < date.fromisoformat(decision["as_of"])):
            raise ValueError("archived search receipt differs from frozen request, identity or time")
    expected = {"company_type": next((m for m in selected if rules[m]["axis"] == "type"), None),
                "stage": next((m for m in selected if rules[m]["axis"] == "lifecycle"), None),
                "industry_modules": sorted(m for m in selected if rules[m]["axis"] == "industry"),
                "overlays": sorted(m for m in selected if rules[m]["axis"] == "attribute"),
                "diagnostic_modules": sorted(m for m in selected if rules[m]["axis"] == "diagnostic"),
                "investment_lenses": sorted(m for m in selected if rules[m]["axis"] == "lens")}
    if (any(profile[k] != v for k, v in expected.items())
            or (profile["cycle_sensitive"] is True) != ("cyclical" in selected)
            or profile["recovery_review"] != ("recovery" in selected)
            or ("cyclical" not in selected and profile["cycle_position"] != "unknown")):
        raise ValueError("frozen profile contradicts selected modules")
    if ((selected & {"distressed", "turnaround", "declining"}
         or ("cyclical" in selected and profile["cycle_position"] in RECOVERY_POSITIONS))
            and "recovery" not in selected):
        raise ValueError("route removed mandatory triggered recovery review")
    by_id = {item["module_id"]: item for item in decision["module_decisions"]}
    if "cyclical" in selected and profile["cycle_position"] != by_id["cyclical"].get("evidence_context", {}).get("cycle_position", "unknown"):
        raise ValueError("cycle position differs from frozen routing evidence")
    if (profile["diagnostic_rationale"] != {mid: by_id[mid]["rationale"] for mid in expected["diagnostic_modules"]}
            or profile["lens_rationale"] != {mid: by_id[mid]["rationale"] for mid in expected["investment_lenses"]}
            or profile["recovery_rationale"] != (by_id["recovery"]["rationale"] if "recovery" in selected else "")):
        raise ValueError("frozen profile rationale contradicts module decisions")
    mandatory = sorted({qid for mid in selected for qid in rules[mid]["mandatory_question_ids"]})
    if decision["dispatch_plan"]["mandatory_question_ids"] != mandatory or decision["dispatch_plan"]["minimum_questions"] != 24 + len(mandatory):
        raise ValueError("route mandatory risk coverage differs from frozen policy")
    dispatch = decision["dispatch_plan"]
    if dispatch["requested_mode"] != dispatch["resolved_mode"]:
        raise ValueError("route cannot silently change requested mode")
    conflict = any(x["reason_code"] in {"conflicting_axis_evidence", "duplicate_business_classification"}
                   for x in decision["module_decisions"])
    scope_compatible = dispatch["business_scope_compatible"]
    status = "ready"
    if module_selection_issues:
        status = "needs_review"
    elif conflict or scope_compatible is False:
        status = "requires_segments"
    elif len(expected["industry_modules"]) > 2:
        status = "requires_full_or_segments" if dispatch["requested_mode"] == "quick" else (
            "ready" if scope_compatible is True else "requires_segments")
    expected_gaps = []
    for axis in ("type", "lifecycle"):
        if any(rules[x["module_id"]]["axis"] == axis and x["reason_code"] == "conflicting_axis_evidence"
               for x in decision["module_decisions"]):
            expected_gaps.append("conflicting_" + axis)
    if any(x["reason_code"] == "duplicate_business_classification" for x in decision["module_decisions"]):
        expected_gaps.append("duplicate_business_classification")
    unbound = sorted(x["module_id"] for x in decision["module_decisions"]
                     if x["reason_code"] == "unbound_search_source")
    if unbound:
        expected_gaps.extend(f"unbound_search_source:{mid}" for mid in unbound)
        expected_gaps.append("unbound_search_source")
    expected_gaps.extend(module_selection_issues)
    if expected["company_type"] is None: expected_gaps.append("company_type_unresolved")
    if expected["stage"] is None: expected_gaps.append("lifecycle_unresolved")
    if expected["company_type"] in {"operating", "pre_revenue"} and not expected["industry_modules"]:
        expected_gaps.append("industry_unresolved")
    if not conflict and scope_compatible is not False and len(expected["industry_modules"]) > 2:
        expected_gaps.append("multi_business_coverage")
        if dispatch["requested_mode"] == "full" and scope_compatible is not True:
            expected_gaps.append("business_scope_unconfirmed")
    confidence_policy = policy.get("classification_confidence_gate")
    if confidence_policy:
        confidence = decision.get("classification_confidence")
        if not isinstance(confidence, dict):
            raise ValueError("route snapshot lacks classification confidence")
        threshold = confidence_policy["minimum_score"]
        confidence_status, confidence_score = confidence.get("status"), confidence.get("score")
        eligible_by_score = (confidence_status == "scored" and type(confidence_score) is int
                             and confidence_score >= threshold)
        if (set(confidence) != {"status", "score", "minimum_score", "llm_candidates_eligible"}
                or confidence["minimum_score"] != threshold
                or confidence["llm_candidates_eligible"] is not eligible_by_score
                or (confidence_status == "scored" and (type(confidence_score) is not int
                                                        or not 1 <= confidence_score <= 10))
                or (confidence_status != "scored" and (
                    confidence_status not in {"unknown", "insufficient_evidence", "not_run"}
                    or confidence_score is not None))
                or ((confidence_status == "not_run") != (receipt is None))):
            raise ValueError("route classification confidence contradicts frozen policy or execution")
        if receipt is not None and (receipt.get("classification_status") != confidence_status
                                    or receipt.get("classification_score") != confidence_score):
            raise ValueError("archived execution confidence differs from route classification")
        if confidence_status == "scored" and confidence_score < threshold:
            expected_gaps.append("classification_confidence_below_threshold")
        for item in decision["module_decisions"]:
            if item["basis"] != "searched_llm":
                continue
            if not eligible_by_score and item["decision"] == "selected":
                raise ValueError("below-threshold model candidate cannot be selected")
            if item["reason_code"] == "overall_confidence_below_threshold":
                if (eligible_by_score or item["decision"] != "uncertain" or item["confidence"] != "low"):
                    raise ValueError("overall confidence downgrade is inconsistent")
            elif (not eligible_by_score and item["reason_code"] != "evidence_not_applicable"
                  and (item["decision"] != "uncertain"
                       or item["reason_code"] != "overall_confidence_below_threshold")):
                raise ValueError("below-threshold model candidate bypasses confidence downgrade")
    elif "classification_confidence" in decision:
        raise ValueError("historical route cannot claim a current confidence policy")
    if dispatch["coverage_gaps"] != sorted(set(expected_gaps)) or decision["status"] != ("partial" if expected_gaps else "resolved"):
        raise ValueError("route coverage gaps or resolution status contradicts frozen classification")
    if policy.get("partial_dispatch") == "common_and_mandatory_risk":
        eligible = sorted(selected)
        if module_selection_issues:
            eligible = []
        elif set(expected_gaps) & {"unbound_search_source", "company_type_unresolved", "lifecycle_unresolved", "industry_unresolved",
                                   "conflicting_type", "conflicting_lifecycle", "duplicate_business_classification"}:
            eligible = sorted({"common"} | {mid for mid in selected if rules[mid]["mandatory_question_ids"]})
            status = "ready_common_and_risk"
        if dispatch.get("eligible_module_ids") != eligible:
            raise ValueError("route dispatch modules bypass unresolved primary axes or mandatory risk")
    elif "eligible_module_ids" in dispatch:
        raise ValueError("legacy routing policy has no partial dispatch list")
    if dispatch["status"] != status:
        raise ValueError("route dispatch coverage or scope contradiction")
    return decision


def validate_recorded_route_execution(decision, *, now_utc, expected_decision_id=None, root=ROOT):
    """Check the recorded execution context of an archived manifest.

    This read path never authorizes a new dispatch; historical router 2.0
    manifests still need their original time, expected ID and manual TTL.
    """
    validate_route_snapshot(decision, root=root)
    now = _utc(now_utc)
    if expected_decision_id is not None and decision["decision_id"] != expected_decision_id:
        raise ValueError("route differs from independently stored decision identity")
    if now < _utc(decision["decided_at"]):
        raise ValueError("execution cannot precede routing decision")
    for item in decision["module_decisions"]:
        if item["basis"] == "manual" and _utc(item["manual_override"]["valid_until"]) <= now:
            raise ValueError("manual route override expired at execution")
    if decision["dispatch_plan"]["status"] not in {"ready", "ready_common_and_risk"}:
        raise ValueError(decision["dispatch_plan"]["status"])
    return decision


def validate_route_for_execution(decision, *, now_utc, expected_decision_id=None, root=ROOT):
    """Authorize new execution only against a caller-held decision ID.

    The route hash detects accidental changes, but is self-computable and does
    not authenticate classification provenance. The caller must obtain the
    expected ID from its own trusted state rather than echoing this payload.
    """
    validate_recorded_route_execution(
        decision, now_utc=now_utc,
        expected_decision_id=expected_decision_id, root=root)
    if not _current_router_compatible(decision["router_version"]):
        raise ValueError(f"historical router {decision['router_version']} decision cannot be executed")
    if expected_decision_id is None:
        raise ValueError("current route execution requires independently stored decision identity")
    return decision


def enforce_route_budget(decision, maximum):
    if type(maximum) is not int or maximum < decision["dispatch_plan"]["minimum_questions"]:
        raise ValueError("budget below mandatory core and routed risk questions")
    return maximum


def profile_from_route(decision):
    return {k: copy.deepcopy(v) for k, v in decision["profile_context"].items() if v is not None}


def diff_routes(previous, current):
    if (previous["entity_id"], previous["segment_id"]) != (current["entity_id"], current["segment_id"]):
        raise ValueError("cannot diff routes across entity or scope")
    def selected(value):
        return {x["module_id"] for x in value["module_decisions"] if x["decision"] == "selected"}
    old, new = selected(previous), selected(current)
    return {"previous_decision_id": previous["decision_id"], "decision_id": current["decision_id"],
            "entered": sorted(new - old), "exited": sorted(old - new), "retained": sorted(old & new),
            "uncertain": sorted(x["module_id"] for x in current["module_decisions"] if x["decision"] == "uncertain")}
