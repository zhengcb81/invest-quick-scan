"""S06 fixed offline routing cases; no provider or network implementation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc
import module_registry as registry
import question_sets as qs
import routing


def partial_route_body():
    return {
        "schema_version": "2.0.0", "release_id": "modrel_" + "1" * 64,
        "module_package_id": "pkg_" + "2" * 64, "router_version": "2.0.0",
        "routing_policy_sha256": "3" * 64,
        "identity_ref": "fixture-identity", "entity_id": "E1", "scope": "entity",
        "segment_id": None, "as_of": "2026-09-19", "decided_at": "2026-09-20T12:00:00Z",
        "status": "partial", "previous_decision_id": None, "execution": None,
        "profile_context": {"company": "Fictional company", "ticker": "EXAMPLE", "exchange": "TEST",
                            "entity_id": "E1", "as_of": "2026-09-19", "security_id": None,
                            "segment_id": None, "company_type": None, "industry_modules": [],
                            "stage": None, "business_subtype": None, "cycle_sensitive": None,
                            "cycle_position": "unknown", "recovery_review": False,
                            "recovery_rationale": "", "overlays": [], "diagnostic_modules": [],
                            "diagnostic_rationale": {}, "investment_lenses": [], "lens_rationale": {}},
        "dispatch_plan": {"requested_mode": "quick", "resolved_mode": "quick", "status": "ready",
                          "business_scope_compatible": None,
                          "mandatory_question_ids": [], "minimum_questions": 24,
                          "coverage_gaps": [], "segment_requests": []},
        "module_decisions": [{"module_id": "common", "module_version": "3.0.0", "decision": "selected",
                              "basis": "policy", "confidence": "high", "rationale": "Universal core",
                              "sources": [], "rule_id": "always", "reason_code": "universal_core"}],
    }


class RouteSchemaTests(unittest.TestCase):
    def test_v2_policy_common_and_unavailable_sources_are_representable(self):
        body = partial_route_body()
        body["module_decisions"].append({"module_id": "semiconductors", "module_version": "3.0.0",
            "decision": "uncertain", "basis": "unavailable", "confidence": "low",
            "rationale": "No verified search evidence", "sources": [],
            "rule_id": "industry_evidence", "reason_code": "missing_evidence"})
        sealed = mc.seal_route_decision(body)
        self.assertEqual(sealed["schema_version"], "2.0.0")
        self.assertEqual(sealed["module_decisions"][1]["sources"], [])

    def test_v2_cannot_use_unavailable_to_select_objective_module(self):
        body = partial_route_body()
        body["module_decisions"][0].update(module_id="bank", basis="unavailable")
        with self.assertRaises(ValidationError):
            mc.seal_route_decision(body)

    def test_router_21_schema_rejects_router_22_confidence_field(self):
        body = partial_route_body()
        body["router_version"] = "2.1.0"
        body["classification_confidence"] = {
            "status": "not_run", "score": None, "minimum_score": 7,
            "llm_candidates_eligible": False}
        with self.assertRaises(ValidationError):
            mc.seal_route_decision(body)


class RoutingFixture(unittest.TestCase):
    """Use a real immutable package in a unique temporary root for every case."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iqs-s06-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "questions", self.root / "questions", ignore=shutil.ignore_patterns("releases"))
        for ref in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                    "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                    "schemas/quick_scan/module-legacy-baseline.json"):
            target = self.root / ref
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / ref, target)
        self.package = routing.publish_routing_package(root=self.root,
            renderer_version=qs.RENDERER_VERSION, renderer_rules_sha256=qs.renderer_rules_sha256())
        self.package_id = self.package["package_id"]
        self.identity = {"entity_id": "E_SEMI", "identity_ref": "trusted:E_SEMI:v1",
                         "company": "Fictional dual-listed equipment company", "ticker": "600TEST",
                         "exchange": "SSE", "security_id": "E_SEMI_CN", "as_of": "2026-09-19"}
        self.now = "2026-09-20T12:00:00Z"
        self.policy = registry.load_routing_policy(self.package_id, root=self.root)

    def fact(self, mid, **extra):
        tag = next(r["evidence_tags"][0] for r in self.policy["rules"] if r["module_id"] == mid)
        return {"module_id": mid, "confidence": "high", "evidence_type": tag,
                "rationale": "Fixture verified operating evidence: " + mid,
                "sources": [{"title": "Fixture only", "url": "https://example.invalid/" + mid,
                             "published_at": "2026-09-18", "entity_id": "E_SEMI", "claim": mid}], **extra}

    def normal(self, stage="scaling"):
        return [self.fact("operating"), self.fact("semiconductors", materiality={"revenue_share": .70}), self.fact(stage)]

    def route(self, facts=None, **options):
        inputs = {**self.identity, "verified_facts": facts if facts is not None else self.normal()}
        inputs.update(options.pop("input_changes", {}))
        if options.get("candidate") is not None:
            confidence = options.get("classification_confidence", {"status": "scored", "score": 8})
            response = self.native_response(options.pop("candidate")["candidates"],
                                            status=confidence["status"], score=confidence["score"])
            options.pop("classification_confidence", None)
            options["route_response"] = response
            if options.get("execution_receipt") is not None:
                options["execution_receipt"] = {
                    **options["execution_receipt"],
                    "answer_sha256": hashlib.sha256(mc.canonical_bytes(response)).hexdigest()}
        if options.get("previous_decision") is not None:
            options.setdefault("expected_previous_decision_id", options["previous_decision"]["decision_id"])
        return routing.resolve_route_decision(inputs, package_id=self.package_id, root=self.root,
                                               now_utc=options.pop("now_utc", self.now), **options)

    def native_response(self, candidates, *, status="scored", score=8):
        return {"question_id": "ROUTE_02", "entity_id": self.identity["entity_id"],
                "company_name": self.identity["company"], "status": status, "score": score,
                "description": json.dumps({"schema_version": "2.0.0", "question_id": "ROUTE_02",
                                           "candidates": candidates}, ensure_ascii=False)}

    @staticmethod
    def selected(decision):
        return {d["module_id"] for d in decision["module_decisions"] if d["decision"] == "selected"}

    @staticmethod
    def item(decision, mid):
        return next(d for d in decision["module_decisions"] if d["module_id"] == mid)

    def receipt(self, *, classification_status="scored", classification_score=8, answer_sha256=None):
        request = routing.build_route_request(self.identity, package_id=self.package_id, root=self.root)
        if answer_sha256 is None:
            answer_sha256 = hashlib.sha256(mc.canonical_bytes(
                self.native_response(self.normal(), status=classification_status,
                                     score=classification_score))).hexdigest()
        return {"provider": "fixture", "model_requested": "fixture-v1", "model_resolved": "fixture-v1",
                "model_revision": "1", "request_id": "r1", "attempt_id": "a1", "entity_id": "E_SEMI",
                "as_of": "2026-09-19", "answered_at": "2026-09-20T11:59:00Z", "search_status": "executed",
                "classification_status": classification_status, "classification_score": classification_score,
                "answer_sha256": answer_sha256,
                "search_receipt_id": "s1", "prompt_sha256": request["prompt_sha256"],
                "web_search_calls": [{"id": "s1", "status": "completed", "action_type": "search",
                                      "source_urls": ["https://example.invalid/operating",
                                                      "https://example.invalid/semiconductors",
                                                      "https://example.invalid/scaling",
                                                      "https://example.invalid/concentrated"]}]}


class RoutingTests(RoutingFixture):
    def test_mod19_a09_policy_versions_and_confidence_threshold_are_exact(self):
        _, modules, _, _ = registry.load_package(self.package_id, root=self.root)
        self.assertEqual((self.policy["schema_version"], self.policy["router_version"],
                          self.policy["request_protocol"]),
                         ("1.3.0", "2.3.0", "stockqa-route-confidence-3"))
        routing.validate_policy(self.policy, modules)
        archived22 = copy.deepcopy(self.policy)
        archived22.update(schema_version="1.2.0", router_version="2.2.0",
                          request_protocol="stockqa-route-confidence-2")
        routing.validate_policy(archived22, modules)
        archived21 = copy.deepcopy(self.policy)
        archived21.update(schema_version="1.1.0", router_version="2.1.0",
                          request_protocol="stockqa-route-confidence-1")
        archived21.pop("classification_confidence_gate")
        routing.validate_policy(archived21, modules)
        archived20 = copy.deepcopy(archived21)
        archived20.update(schema_version="1.0.0", router_version="2.0.0")
        archived20.pop("request_protocol"); archived20.pop("partial_dispatch")
        routing.validate_policy(archived20, modules)
        for gate in ({"minimum_score": True, "below_threshold": "mark_llm_candidates_uncertain"},
                     {"minimum_score": 0, "below_threshold": "mark_llm_candidates_uncertain"},
                     {"minimum_score": 11, "below_threshold": "mark_llm_candidates_uncertain"},
                     {"minimum_score": 7, "below_threshold": "accept_all"},
                     {"minimum_score": 7, "below_threshold": "mark_llm_candidates_uncertain", "extra": True}):
            invalid = copy.deepcopy(self.policy); invalid["classification_confidence_gate"] = gate
            with self.subTest(gate=gate), self.assertRaisesRegex(ValueError, "confidence gate"):
                routing.validate_policy(invalid, modules)
        for change in ({"router_version": "2.2.0"},
                       {"request_protocol": "stockqa-route-confidence-2"},
                       {"schema_version": "1.2.0"}):
            invalid = copy.deepcopy(self.policy); invalid.update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "unsupported request protocol"):
                routing.validate_policy(invalid, modules)

    def test_mod19_v23_execution_receipt_requires_hash_of_parsed_native_answer(self):
        native = self.native_response(self.normal())
        parsed = routing.parse_route_response(native, self.identity)
        receipt = self.receipt(answer_sha256=parsed["answer_sha256"])
        route = routing.resolve_route_decision(
            {**self.identity, "verified_facts": []}, package_id=self.package_id,
            route_response=native, execution_receipt=receipt,
            now_utc=self.now, root=self.root)
        self.assertEqual(route["execution"]["answer_sha256"], parsed["answer_sha256"])
        altered = copy.deepcopy(route)
        del altered["execution"]["answer_sha256"]
        with self.assertRaisesRegex(ValidationError, "answer_sha256"):
            mc.seal_route_decision(altered)

    def test_mod19_previous_router_policy_requires_explicit_migration(self):
        with tempfile.TemporaryDirectory(prefix="iqs-s06-router-migration-") as temp_root:
            root = Path(temp_root)
            shutil.copytree(ROOT / "questions", root / "questions",
                            ignore=shutil.ignore_patterns("releases"))
            for ref in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                        "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                        "schemas/quick_scan/module-legacy-baseline.json"):
                target = root / ref; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / ref, target)
            policy_path = root / "questions/routing-policy.v2.json"
            current_policy = json.loads(policy_path.read_text(encoding="utf-8"))
            archived_policy = copy.deepcopy(current_policy)
            archived_policy.update(schema_version="1.2.0", router_version="2.2.0",
                                   request_protocol="stockqa-route-confidence-2")
            policy_path.write_text(json.dumps(archived_policy, ensure_ascii=False), encoding="utf-8")
            old_package = routing.publish_routing_package(
                root=root, renderer_version=qs.RENDERER_VERSION,
                renderer_rules_sha256=qs.renderer_rules_sha256())
            old_route = routing.resolve_route_decision(
                {**self.identity, "verified_facts": self.normal()},
                package_id=old_package["package_id"], now_utc=self.now, root=root)

            policy_path.write_text(json.dumps(current_policy, ensure_ascii=False), encoding="utf-8")
            current_package = routing.publish_routing_package(
                root=root, renderer_version=qs.RENDERER_VERSION,
                renderer_rules_sha256=qs.renderer_rules_sha256())
            with self.assertRaisesRegex(ValueError, "incompatible router or routing policy; explicit migration"):
                routing.resolve_route_decision(
                    {**self.identity, "verified_facts": self.normal()},
                    package_id=current_package["package_id"], previous_decision=old_route,
                    expected_previous_decision_id=old_route["decision_id"],
                    now_utc=self.now, root=root)

    def test_t1_semiconductor_scaling_is_deterministic_and_dual_listing_one_entity(self):
        first = self.route()
        self.assertEqual(self.selected(first), {"common", "operating", "semiconductors", "scaling"})
        self.assertEqual(first, self.route(list(reversed(self.normal()))))
        ah = self.route(input_changes={"exchange": "HKEX", "ticker": "TEST.HK", "security_id": "E_SEMI_HK"})
        self.assertEqual(first["entity_id"], ah["entity_id"])
        self.assertEqual(self.selected(first), self.selected(ah))
        self.assertEqual(first["profile_context"]["stage"], "scaling")
        changed = self.normal(); changed[1]["materiality"]["revenue_share"] = .8
        self.assertNotEqual(first["decision_id"], self.route(changed)["decision_id"])
        accounting = self.route(input_changes={"accounting_standard": "IFRS", "reporting_currency": "CNY"})
        self.assertEqual(accounting["profile_context"]["accounting_standard"], "IFRS")
        unknown = self.fact("operating"); unknown["module_id"] = "ai_super_chip"
        with self.assertRaisesRegex(ValueError, "unknown route module"):
            self.route([unknown])

    def test_t1_llm_candidates_require_real_prompt_bound_receipt(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02", "candidates": self.normal()}
        first = self.route([], candidate=candidate, execution_receipt=self.receipt())
        candidate["candidates"].reverse()
        reordered = self.route([], candidate=candidate, execution_receipt=self.receipt())
        self.assertEqual(self.selected(first), self.selected(reordered))
        self.assertEqual(first["dispatch_plan"]["eligible_module_ids"],
                         reordered["dispatch_plan"]["eligible_module_ids"])
        self.assertNotEqual(first["execution"]["answer_sha256"],
                            reordered["execution"]["answer_sha256"])
        self.assertEqual(self.item(first, "semiconductors")["basis"], "searched_llm")
        for key, value in (("prompt_sha256", "0" * 64), ("entity_id", "OTHER"), ("as_of", "2026-09-18")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.route([], candidate=candidate, execution_receipt={**self.receipt(), key: value})
        with self.assertRaises(ValidationError):
            self.route([], candidate=candidate, execution_receipt={**self.receipt(), "search_status": "unavailable"})
        changed = copy.deepcopy(first)
        changed["execution"]["entity_id"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "archived search receipt"):
            routing.validate_route_snapshot(mc.seal_route_decision(changed), root=self.root)

    def test_mod19_a01_a07_parser_preserves_outer_confidence_and_unscored_null(self):
        fact = self.fact("concentrated")
        native = {"question_id": "ROUTE_02", "entity_id": self.identity["entity_id"],
                  "company_name": self.identity["company"], "status": "scored", "score": 6,
                  "description": json.dumps({"schema_version": "2.0.0", "question_id": "ROUTE_02",
                                             "candidates": [fact]})}
        parsed = routing.parse_route_response(native, self.identity)
        self.assertEqual(parsed["classification_confidence"], {"status": "scored", "score": 6})
        self.assertEqual(parsed["candidate"]["candidates"], [fact])
        self.assertEqual(parsed["answer_sha256"], hashlib.sha256(mc.canonical_bytes(native)).hexdigest())
        for status in ("unknown", "insufficient_evidence"):
            empty = {**native, "status": status, "score": None,
                     "description": json.dumps({"schema_version": "2.0.0", "question_id": "ROUTE_02",
                                                "candidates": []})}
            parsed = routing.parse_route_response(empty, self.identity)
            self.assertEqual(parsed["classification_confidence"], {"status": status, "score": None})
            self.assertEqual(parsed["candidate"]["candidates"], [])
        with self.assertRaisesRegex(ValueError, "scored classification requires"):
            routing.parse_route_response({**native, "description": json.dumps(
                {"schema_version": "2.0.0", "question_id": "ROUTE_02", "candidates": []})},
                self.identity)
        not_run = self.route([])
        self.assertEqual(not_run["classification_confidence"], {
            "status": "not_run", "score": None, "minimum_score": 7, "llm_candidates_eligible": False})

    def test_mod19_a02_a05_overall_gate_only_demotes_model_candidates_and_keeps_verified_facts(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": [self.fact("concentrated")]}
        score6 = self.route(self.normal(), candidate=candidate,
            classification_confidence={"status": "scored", "score": 6},
            execution_receipt=self.receipt(classification_score=6))
        self.assertEqual(self.selected(score6), {"common", "operating", "semiconductors", "scaling"})
        self.assertEqual(self.item(score6, "concentrated")["decision"], "uncertain")
        self.assertEqual(self.item(score6, "concentrated")["reason_code"], "overall_confidence_below_threshold")
        self.assertTrue({"common", "operating", "semiconductors", "scaling"} <=
                        set(score6["dispatch_plan"]["eligible_module_ids"]))

        score7 = self.route(self.normal(), candidate=candidate,
            classification_confidence={"status": "scored", "score": 7},
            execution_receipt=self.receipt(classification_score=7))
        self.assertTrue(score7["classification_confidence"]["llm_candidates_eligible"])
        self.assertEqual(self.item(score7, "concentrated")["decision"], "selected")

        low_module = copy.deepcopy(candidate)
        low_module["candidates"][0]["confidence"] = "low"
        score10 = self.route(self.normal(), candidate=low_module,
            classification_confidence={"status": "scored", "score": 10},
            execution_receipt=self.receipt(classification_score=10))
        self.assertEqual(self.item(score10, "concentrated")["decision"], "uncertain")
        self.assertEqual(self.item(score10, "concentrated")["reason_code"], "low_confidence")

    def test_mod19_a06_snapshot_recomputes_gate_and_rejects_resealed_bypass(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": [self.fact("concentrated")]}
        route = self.route(self.normal(), candidate=candidate,
            classification_confidence={"status": "scored", "score": 7},
            execution_receipt=self.receipt(classification_score=7))
        forged = copy.deepcopy(route)
        forged["classification_confidence"].update(score=6, llm_candidates_eligible=False)
        forged["execution"].update(classification_score=6)
        with self.assertRaisesRegex(ValueError, "below-threshold model candidate cannot be selected"):
            routing.validate_route_snapshot(mc.seal_route_decision(forged), root=self.root)

        for change in ({"minimum_score": 6}, {"llm_candidates_eligible": False}):
            altered = copy.deepcopy(route)
            altered["classification_confidence"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                routing.validate_route_snapshot(mc.seal_route_decision(altered), root=self.root)

        # A self-computed route hash is not an authenticity proof. Even if a
        # resealed snapshot rewrites its source label and all dependent fields,
        # new execution must still match the decision ID held by the caller.
        resealed = copy.deepcopy(route)
        searched = self.item(resealed, "concentrated")
        self.assertEqual(searched["basis"], "searched_llm")
        searched["basis"] = "deterministic"
        resealed["classification_confidence"].update(score=6, llm_candidates_eligible=False)
        resealed["execution"].update(classification_score=6)
        resealed["dispatch_plan"]["coverage_gaps"].append("classification_confidence_below_threshold")
        resealed["status"] = "partial"
        resealed = mc.seal_route_decision(resealed)
        self.assertNotEqual(resealed["decision_id"], route["decision_id"])
        routing.validate_route_snapshot(resealed, root=self.root)
        with self.assertRaisesRegex(ValueError, "independently stored decision identity"):
            routing.validate_route_for_execution(
                resealed, root=self.root, now_utc=self.now,
                expected_decision_id=route["decision_id"])

    def test_searched_candidate_urls_must_belong_to_selected_completed_call(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02", "candidates": self.normal()}
        valid = self.route([], candidate=candidate, execution_receipt=self.receipt())
        self.assertEqual(self.item(valid, "semiconductors")["basis"], "searched_llm")

        alien = copy.deepcopy(candidate)
        alien["candidates"][1]["sources"][0]["url"] = "https://not-in-search-receipt.invalid/hallucinated"
        uncertain = self.route([], candidate=alien, execution_receipt=self.receipt())
        self.assertEqual(uncertain["dispatch_plan"]["eligible_module_ids"], ["common"])
        self.assertEqual(uncertain["dispatch_plan"]["status"], "ready_common_and_risk")
        self.assertIn("unbound_search_source:semiconductors", uncertain["dispatch_plan"]["coverage_gaps"])
        self.assertNotIn("semiconductors", self.selected(uncertain))

        no_call_sources = copy.deepcopy(self.receipt())
        no_call_sources["web_search_calls"][0]["source_urls"] = []
        result = self.route([], candidate=candidate, execution_receipt=no_call_sources)
        self.assertEqual(result["dispatch_plan"]["eligible_module_ids"], ["common"])

        wrong_call = copy.deepcopy(self.receipt())
        wrong_call["search_receipt_id"] = "other-call"
        result = self.route([], candidate=candidate, execution_receipt=wrong_call)
        self.assertEqual(result["dispatch_plan"]["eligible_module_ids"], ["common"])

        mixed = copy.deepcopy(self.receipt())
        mixed["web_search_calls"][0]["source_urls"].remove("https://example.invalid/semiconductors")
        mixed["web_search_calls"].append({"id": "failed-call", "status": "failed",
                                          "action_type": "search",
                                          "source_urls": ["https://example.invalid/semiconductors"]})
        result = self.route([], candidate=candidate, execution_receipt=mixed)
        self.assertEqual(result["dispatch_plan"]["eligible_module_ids"], ["common"])

        missing_calls = copy.deepcopy(self.receipt())
        del missing_calls["web_search_calls"]
        with self.assertRaises(ValidationError):
            self.route([], candidate=candidate, execution_receipt=missing_calls)

        tampered = copy.deepcopy(valid)
        tampered["execution"]["web_search_calls"][0]["source_urls"].remove(
            "https://example.invalid/semiconductors")
        with self.assertRaisesRegex(ValueError, "source is not in completed search receipt"):
            routing.validate_route_snapshot(mc.seal_route_decision(tampered), root=self.root)

    def test_unbound_model_candidate_cannot_override_verified_risk_fact(self):
        verified = self.fact("distressed", evidence_type="covenant_breach")
        candidate_fact = copy.deepcopy(verified)
        candidate_fact["sources"][0]["url"] = "https://unbound.invalid/distressed"
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": [candidate_fact]}
        result = self.route([verified], candidate=candidate,
                            execution_receipt=self.receipt())
        self.assertEqual(self.item(result, "distressed")["basis"], "deterministic")
        self.assertIn("distressed", self.selected(result))
        self.assertIn("recovery", self.selected(result))
        self.assertEqual(len(result["dispatch_plan"]["mandatory_question_ids"]), 6)
        self.assertNotIn("unbound_search_source:distressed",
                         result["dispatch_plan"]["coverage_gaps"])
        routing.validate_route_snapshot(result, root=self.root)


    def test_t2_mature_cycle_trough_preserves_stage_and_adds_recovery(self):
        facts = self.normal("mature") + [self.fact("cyclical", cycle_position="trough")]
        result = self.route(facts)
        self.assertEqual(self.selected(result), {"common", "operating", "semiconductors", "mature", "cyclical", "recovery"})
        self.assertEqual(result["profile_context"]["stage"], "mature")
        self.assertEqual(result["profile_context"]["cycle_position"], "trough")
        self.assertEqual(result["dispatch_plan"]["mandatory_question_ids"], [f"RECOVERY_{i:02}" for i in range(1, 5)])
        changed = copy.deepcopy(facts); changed[-1]["rationale"] += " Revised disclosed backlog."
        self.assertNotEqual(result["decision_id"], self.route(changed)["decision_id"])
        price = self.fact("cyclical", evidence_type="price_decline", cycle_position="trough")
        only_price = self.route(self.normal("mature") + [price])
        self.assertTrue({"cyclical", "recovery", "distressed"}.isdisjoint(self.selected(only_price)))

    def test_t3_distressed_scaling_six_mandatory_questions_budget_and_manual_veto(self):
        facts = self.normal() + [self.fact("distressed", evidence_type="covenant_breach")]
        result = self.route(facts)
        self.assertEqual(self.selected(result), {"common", "operating", "semiconductors", "scaling", "distressed", "recovery"})
        self.assertEqual(result["dispatch_plan"]["minimum_questions"], 30)
        self.assertEqual(len(result["dispatch_plan"]["mandatory_question_ids"]), 6)
        with self.assertRaisesRegex(ValueError, "budget below mandatory"):
            routing.enforce_route_budget(result, 24)
        self.assertEqual(routing.enforce_route_budget(result, 30), 30)
        for mid in ("recovery", "distressed"):
            with self.subTest(mid=mid), self.assertRaisesRegex(ValueError, "cannot suppress"):
                self.route(facts, user_policy={"manual_overrides": [{"module_id": mid, "decision": "rejected",
                    "actor": "fixture-user", "reason": "Fixture veto", "valid_until": "2026-09-21T00:00:00Z"}]})
        changed = copy.deepcopy(result)
        changed["dispatch_plan"]["mandatory_question_ids"] = []
        changed["dispatch_plan"]["minimum_questions"] = 24
        with self.assertRaisesRegex(ValueError, "mandatory risk coverage"):
            routing.validate_route_snapshot(mc.seal_route_decision(changed), root=self.root)

    def test_t4_three_material_industries_do_not_truncate_and_full_needs_scope(self):
        facts = self.normal() + [self.fact(m, materiality={"revenue_share": .3}, business_id=m)
                                 for m in ("software", "industrial")]
        quick = self.route(facts)
        self.assertEqual(quick["profile_context"]["industry_modules"], ["industrial", "semiconductors", "software"])
        self.assertEqual(quick["dispatch_plan"]["status"], "requires_full_or_segments")
        full = self.route(facts, input_changes={"requested_mode": "full", "compatible_business_scope": True})
        self.assertEqual(full["dispatch_plan"]["status"], "ready")
        unknown_scope = self.route(facts, input_changes={"requested_mode": "full"})
        self.assertEqual(unknown_scope["dispatch_plan"]["status"], "requires_segments")
        incompatible = self.route(facts, input_changes={"compatible_business_scope": False})
        self.assertEqual(incompatible["dispatch_plan"]["status"], "requires_segments")
        self.assertIsNone(incompatible["segment_id"])
        forged = copy.deepcopy(quick); forged["dispatch_plan"]["status"] = "ready"
        with self.assertRaisesRegex(ValueError, "dispatch coverage"):
            routing.validate_route_snapshot(mc.seal_route_decision(forged), root=self.root)

    def test_t4_two_labels_for_one_business_need_review_not_holding(self):
        facts = self.normal()
        facts[1]["business_id"] = "equipment"
        facts.append(self.fact("industrial", business_id="equipment", materiality={"revenue_share": .7}))
        result = self.route(facts)
        self.assertEqual(result["dispatch_plan"]["status"], "ready_common_and_risk")
        self.assertEqual(result["dispatch_plan"]["eligible_module_ids"], ["common"])
        self.assertNotIn("holding", self.selected(result))
        self.assertEqual(self.item(result, "industrial")["decision"], "uncertain")
        self.assertEqual(self.item(result, "semiconductors")["decision"], "uncertain")

    def test_t5_unavailable_keeps_common_and_verified_risk_without_fake_other(self):
        missing = self.route([])
        self.assertEqual(self.selected(missing), {"common"})
        self.assertEqual(self.item(missing, "other")["decision"], "uncertain")
        self.assertEqual(self.item(missing, "operating")["sources"], [])
        risk = self.route([self.fact("distressed", evidence_type="default")])
        self.assertEqual(self.selected(risk), {"common", "distressed", "recovery"})
        self.assertEqual(risk["dispatch_plan"]["minimum_questions"], 30)
        self.assertEqual(risk["status"], "partial")
        unclassified = self.fact("other", evidence_type="business_activity", materiality={"revenue_share": 1})
        self.assertNotIn("other", self.selected(self.route([unclassified])))

    def test_t5_override_expiry_blocks_execution_but_history_remains_readable(self):
        override = {"module_id": "semiconductors", "decision": "selected", "actor": "fixture-user",
                    "reason": "Verified user classification", "valid_until": "2026-09-21T00:00:00Z"}
        result = self.route(user_policy={"manual_overrides": [override]})
        with self.assertRaisesRegex(ValueError, "requires independently stored decision identity"):
            routing.validate_route_for_execution(result, root=self.root, now_utc="2026-09-20T23:59:59Z")
        routing.validate_route_for_execution(
            result, root=self.root, now_utc="2026-09-20T23:59:59Z",
            expected_decision_id=result["decision_id"])
        for instant in ("2026-09-21T00:00:00Z", "2026-09-22T00:00:00Z"):
            with self.subTest(now=instant), self.assertRaisesRegex(ValueError, "expired at execution"):
                routing.validate_route_for_execution(
                    result, root=self.root, now_utc=instant,
                    expected_decision_id=result["decision_id"])
        self.assertEqual(routing.validate_route_snapshot(result, root=self.root), result)
        with self.assertRaisesRegex(ValueError, "independently stored"):
            routing.validate_route_for_execution(result, root=self.root, now_utc=self.now,
                                                  expected_decision_id="route_" + "0" * 64)

    def test_t5_equal_authority_type_conflicts_require_segments_manual_precedence_is_explicit(self):
        facts = self.normal() + [self.fact("bank")]
        result = self.route(facts)
        self.assertIsNone(result["profile_context"]["company_type"])
        self.assertEqual(result["dispatch_plan"]["status"], "ready_common_and_risk")
        self.assertEqual(result["dispatch_plan"]["eligible_module_ids"], ["common"])
        override = {"module_id": "operating", "decision": "selected", "actor": "fixture-user",
                    "reason": "Resolved company type", "valid_until": "2026-09-21T00:00:00Z"}
        resolved = self.route(facts, user_policy={"manual_overrides": [override]})
        self.assertEqual(resolved["profile_context"]["company_type"], "operating")
        self.assertEqual(self.item(resolved, "bank")["reason_code"], "trusted_axis_precedence")

    def test_materiality_entry_strategic_survival_and_pre_revenue_project(self):
        for materiality, expected in (({"revenue_share": .149}, False), ({"gross_profit_share": .15}, True),
                 ({"invested_capital_share": .15}, True), ({"committed_capex_share": .20}, True),
                 ({"binding_backlog_share": .20}, True), ({"survival_critical": True}, True)):
            with self.subTest(materiality=materiality):
                facts = self.normal(); facts[1]["materiality"] = materiality
                self.assertEqual("semiconductors" in self.selected(self.route(facts)), expected)
        project = [self.fact("pre_revenue"), self.fact("validation"), self.fact("semiconductors",
                   materiality={"primary_development_project": True})]
        self.assertIn("semiconductors", self.selected(self.route(project)))
        project[0] = self.fact("operating")
        self.assertNotIn("semiconductors", self.selected(self.route(project)))

    def test_materiality_exit_hysteresis_and_lifecycle_event(self):
        previous = self.route()
        low = {"revenue_share": .05, "gross_profit_share": .05, "invested_capital_share": .05}
        facts = self.normal(); facts[1].update(materiality=low, period_count=1)
        retained = self.route(facts, previous_decision=previous)
        self.assertIn("semiconductors", self.selected(retained))
        facts[1]["period_count"] = 2
        exited = self.route(facts, previous_decision=previous)
        self.assertNotIn("semiconductors", self.selected(exited))
        self.assertEqual(routing.diff_routes(previous, exited)["exited"], ["semiconductors"])
        facts[1]["materiality"] = {"revenue_share": .10}
        self.assertIn("semiconductors", self.selected(self.route(facts, previous_decision=previous)))
        facts[1]["materiality"] = {"revenue_share": .05}
        self.assertEqual(self.item(self.route(facts, previous_decision=previous), "semiconductors")["decision"], "uncertain")
        facts = self.normal("mature")
        pending = self.route(facts, previous_decision=previous)
        self.assertEqual(self.item(pending, "mature")["reason_code"], "confirmation_pending")
        facts[-1]["major_event"] = True
        self.assertEqual(self.route(facts, previous_decision=previous)["profile_context"]["stage"], "mature")

    def test_mod19_previous_route_requires_independent_id_before_hysteresis(self):
        previous = self.route()
        facts = self.normal()
        facts[1]["materiality"] = {
            "revenue_share": .12, "gross_profit_share": .12, "invested_capital_share": .12}
        inputs = {**self.identity, "verified_facts": facts}
        with self.assertRaisesRegex(ValueError, "caller-held identity is required"):
            routing.resolve_route_decision(
                inputs, package_id=self.package_id, previous_decision=previous,
                now_utc=self.now, root=self.root)

        wrong_generation = self.route([self.fact("operating"), self.fact("scaling")])
        with self.assertRaisesRegex(ValueError, "previous route decision identity mismatch"):
            routing.resolve_route_decision(
                inputs, package_id=self.package_id, previous_decision=wrong_generation,
                expected_previous_decision_id=previous["decision_id"],
                now_utc=self.now, root=self.root)

        retained = routing.resolve_route_decision(
            inputs, package_id=self.package_id, previous_decision=previous,
            expected_previous_decision_id=previous["decision_id"],
            now_utc=self.now, root=self.root)
        self.assertIn("semiconductors", self.selected(retained))

    def test_mod19_rejects_answer_from_another_execution_attempt(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": [self.fact("concentrated")]}
        response_a = {"question_id": "ROUTE_02", "entity_id": self.identity["entity_id"],
                      "company_name": self.identity["company"], "status": "scored", "score": 8,
                      "description": json.dumps(candidate, ensure_ascii=False)}
        response_b = copy.deepcopy(response_a)
        response_b["description"] = json.dumps(
            {**candidate, "candidates": [self.fact("concentrated", rationale="Different model answer")]},
            ensure_ascii=False)
        answer_b_sha256 = hashlib.sha256(mc.canonical_bytes(response_b)).hexdigest()
        receipt_from_model_b = self.receipt()
        receipt_from_model_b.update(model_resolved="model-B", answer_sha256=answer_b_sha256)
        with self.assertRaisesRegex(ValueError, "answer hash differs from execution receipt"):
            routing.resolve_route_decision(
                {**self.identity, "verified_facts": []}, package_id=self.package_id,
                route_response=response_a, execution_receipt=receipt_from_model_b,
                now_utc=self.now, root=self.root)

    def test_mod19_resolver_cannot_pair_one_answers_candidate_with_another_answers_hash(self):
        response_a = self.native_response(self.normal())
        different_candidates = copy.deepcopy(self.normal())
        different_candidates[0]["rationale"] = "A different model's classification"
        response_b = self.native_response(different_candidates)
        parsed_a = routing.parse_route_response(response_a, self.identity)
        parsed_b = routing.parse_route_response(response_b, self.identity)
        receipt_from_model_b = self.receipt(answer_sha256=parsed_b["answer_sha256"])
        receipt_from_model_b["model_resolved"] = "model-B"

        with self.assertRaisesRegex(TypeError, "unexpected keyword argument 'candidate'"):
            routing.resolve_route_decision(
                {**self.identity, "verified_facts": []}, package_id=self.package_id,
                candidate=parsed_a["candidate"],
                classification_confidence=parsed_a["classification_confidence"],
                answer_sha256=parsed_b["answer_sha256"],
                execution_receipt=receipt_from_model_b,
                now_utc=self.now, root=self.root)

        with self.assertRaisesRegex(ValueError, "answer hash differs from execution receipt"):
            routing.resolve_route_decision(
                {**self.identity, "verified_facts": []}, package_id=self.package_id,
                route_response=response_a, execution_receipt=receipt_from_model_b,
                now_utc=self.now, root=self.root)

    def test_mod19_stockqa_public_result_adapter_binds_answer_and_execution_receipt(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": self.normal()}
        answer = {"question_id": "ROUTE_02", "status": "scored", "score": 8,
                  "description": json.dumps(candidate, ensure_ascii=False),
                  "source_urls": ["https://example.invalid/operating",
                                  "https://example.invalid/semiconductors",
                                  "https://example.invalid/scaling"],
                  "published_date": None, "information_as_of": None,
                  "check_level": "unverified_model_output", "check_level_receipt_id": None}
        answer_sha256 = hashlib.sha256(mc.canonical_bytes(answer)).hexdigest()
        request = routing.build_route_request(self.identity, package_id=self.package_id, root=self.root)
        public_receipt = {
            "answer_sha256": answer_sha256, "answered_at": "2026-09-20T11:59:00Z",
            "input_question_sha256": request["prompt_sha256"], "provider": "openai",
            "requested_model": "model-A", "actual_model": "model-A", "request_id": "req-A",
            "attempt_id": "attempt-A", "search_receipt_id": "search-A", "search_status": "executed",
            "web_search_calls": [{"id": "search-A", "status": "completed", "action_type": "search",
                                   "source_urls": ["https://example.invalid/operating",
                                                   "https://example.invalid/semiconductors",
                                                   "https://example.invalid/scaling"]}],
        }
        public_result = {
            "schema_version": "stockqa.quick_scan_result/1.0.0",
            "entity": {"entity_id": self.identity["entity_id"], "name": self.identity["company"]},
            "observed_at": "2026-09-20T12:00:00Z",
            "provider": {"name": "openai", "requested_model": "model-A"},
            "answers": {"ROUTE_02": answer},
            "execution_receipts": {"ROUTE_02": public_receipt},
        }
        parsed = routing.parse_route_response(public_result, self.identity)
        self.assertEqual(parsed["answer_sha256"], answer_sha256)
        self.assertEqual(parsed["execution_receipt"]["model_resolved"], "model-A")
        decision = routing.resolve_route_decision(
            {**self.identity, "verified_facts": []}, package_id=self.package_id,
            route_response=public_result,
            now_utc=self.now, root=self.root)
        self.assertEqual(decision["execution"]["answer_sha256"], answer_sha256)
        self.assertEqual(decision["execution"]["provider"], "openai")

    def test_mod19_schema_rejects_execution_status_score_mismatch(self):
        candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02",
                     "candidates": [self.fact("operating")]}
        snapshot = self.route([], candidate=candidate, execution_receipt=self.receipt())
        snapshot["execution"]["classification_status"] = "unknown"

        with self.assertRaises(ValidationError):
            mc._validate(mc.ROUTE_SCHEMA, snapshot)

    def test_policy_covers_all48_and_frozen_artifact_not_mutable_source(self):
        self.assertEqual(len(self.policy["rules"]), 48)
        self.assertFalse((self.root / "questions/releases/current.json").exists())
        source = self.root / "questions/routing-policy.v2.json"
        changed = copy.deepcopy(self.policy); changed["materiality"]["enter_share"] = .3
        source.write_text(json.dumps(changed), encoding="utf8")
        self.assertEqual(registry.load_routing_policy(self.package_id, root=self.root), self.policy)
        with self.assertRaisesRegex(ValueError, "without router version increase"):
            routing.publish_routing_package(root=self.root, renderer_version=qs.RENDERER_VERSION,
                                              renderer_rules_sha256=qs.renderer_rules_sha256())
        _, modules, release, _ = registry.load_package(self.package_id, root=self.root)
        changed = copy.deepcopy(self.policy); changed["rules"].pop()
        with self.assertRaisesRegex(ValueError, "each released module"):
            routing.validate_policy(changed, modules)
        changed = copy.deepcopy(self.policy); changed["rules"][0]["predicate"] = "guess_ai"
        with self.assertRaisesRegex(ValueError, "unknown routing axis or predicate"):
            routing.validate_policy(changed, modules)
        archived = self.root / release["routing_policy_ref"]
        archived.write_bytes(archived.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "routing policy archive hash mismatch"):
            registry.load_package(self.package_id, root=self.root)

    def test_legacy_package_and_current_pointer_survive_unactivated_routing_publish(self):
        legacy = registry.publish(root=self.root, renderer_version=qs.RENDERER_VERSION,
                                  renderer_rules_sha256=qs.renderer_rules_sha256(), router_version="1.0.0")
        pointer = (self.root / "questions/releases/current.json").read_bytes()
        result = routing.publish_routing_package(root=self.root, renderer_version=qs.RENDERER_VERSION,
                                                  renderer_rules_sha256=qs.renderer_rules_sha256())
        self.assertEqual(result, self.package)
        self.assertEqual(pointer, (self.root / "questions/releases/current.json").read_bytes())
        self.assertEqual(registry.load_package(legacy["package_id"], root=self.root)[2]["schema_version"], "1.0.0")
        with self.assertRaisesRegex(ValueError, "historical package"):
            registry.load_routing_policy(legacy["package_id"], root=self.root)
        _, modules, release, _ = registry.load_package(self.package_id, root=self.root)
        body = {"schema_version": "1.0.0", "release_id": release["release_id"], "router_version": release["router_version"],
                "entity_id": "E_SEMI", "as_of": "2026-09-19", "decided_at": self.now, "status": "resolved",
                "module_decisions": [{"module_id": mid, "module_version": module["version"],
                     "decision": "selected" if mid == "common" else "rejected", "basis": "deterministic",
                     "confidence": "high", "rationale": "Fixture legacy", "sources": [{"title": "Fixture",
                     "url": "https://example.invalid/legacy", "published_at": "2026-09-18"}]}
                     for mid, module in modules.items()]}
        with self.assertRaisesRegex(ValueError, "legacy route cannot"):
            mc.validate_route_decision(mc.seal_route_decision(body), release)

    def test_new_lens_requires_registered_policy_and_explicit_nontransferable_authorization(self):
        module = json.loads((self.root / "questions/industries/semiconductors.json").read_text(encoding="utf8"))
        question = copy.deepcopy(module["questions"][0])
        question.update(id="FIXTURE_LENS_01", metric_id="score.fixture_lens_01", construct_id=None,
                        comparison_role="context", priority=1)
        module.update(module_id="fixture_lens", version="1.0.0", kind="lenses", name="Fixture lens",
                      applies_when="Explicit user lens", questions=[question], dependencies=[], conflicts=[],
                      introduced_in="1.0.0", activation={"mode": "manual", "required_evidence": ["User request"],
                      "exclude_when": [], "minimum_confidence": "high"})
        path = self.root / "questions/lenses/fixture_lens.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(module), encoding="utf8")
        catalog_path = self.root / "questions/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf8"))
        catalog["modules"].append({"id": "fixture_lens", "kind": "lenses", "name": "Fixture lens",
                                   "path": "questions/lenses/fixture_lens.json", "question_count": 1,
                                   "applies_when": "Explicit user lens"})
        catalog["version"] = "3.3.0"
        catalog_path.write_text(json.dumps(catalog), encoding="utf8")
        policy = copy.deepcopy(self.policy)
        policy["router_version"] = "2.4.0"
        policy["rules"].append({"module_id": "fixture_lens", "axis": "lens", "predicate": "user_lens",
            "minimum_confidence": "medium", "evidence_tags": ["user_request"], "excluded_tags": [], "mandatory_question_ids": []})
        policy["rules"].sort(key=lambda r: r["module_id"])
        kwargs = {"root": self.root, "renderer_version": qs.RENDERER_VERSION, "router_version": "2.4.0",
                  "renderer_rules_sha256": qs.renderer_rules_sha256(), "routing_policy": policy, "activate": False}
        with self.assertRaisesRegex(ValueError, "weakens declared module activation"):
            registry.publish(**kwargs)
        next(r for r in policy["rules"] if r["module_id"] == "fixture_lens")["minimum_confidence"] = "high"
        contexts_path = self.root / "questions/scoring-contexts.json"
        contexts = json.loads(contexts_path.read_text(encoding="utf8"))
        contexts["lenses"] = {"fixture_lens": "Fixture evidence and user research perspective"}
        contexts_path.write_text(json.dumps(contexts), encoding="utf8")
        self.package_id = registry.publish(**kwargs)["package_id"]
        self.policy = registry.load_routing_policy(self.package_id, root=self.root)
        self.assertNotIn("fixture_lens", self.selected(self.route(self.normal() + [self.fact("fixture_lens")])))
        approval = {"actor": "fixture-user", "reason": "Explicit lens", "valid_until": "2026-09-21T00:00:00Z"}
        self.assertIn("fixture_lens", self.selected(self.route(user_policy={"enabled_lenses": {"fixture_lens": approval}})))
        with self.assertRaisesRegex(ValueError, "must not override module identity"):
            self.route(user_policy={"enabled_lenses": {"fixture_lens": {**approval, "module_id": "bank"}}})


class ArchivedRouterCompatibilityTests(unittest.TestCase):
    """A real 2.0 package remains readable, but cannot create a new run."""

    def test_archived_search_snapshot_is_read_only(self):
        decision = json.loads((ROOT / "tests/fixtures/s06_router_20_search_route.json")
                              .read_text(encoding="utf-8"))
        package, _, release, _ = registry.load_package(decision["module_package_id"], root=ROOT)
        self.assertEqual(release["router_version"], "2.0.0")
        self.assertNotIn("web_search_calls", decision["execution"])
        mc.validate_route_decision(decision, release, package=package)
        routing.validate_route_snapshot(decision, root=ROOT)
        with self.assertRaisesRegex(ValueError, "historical|archived"):
            routing.resolve_route_decision(
                {**decision["profile_context"], "identity_ref": decision["identity_ref"],
                 "verified_facts": []}, package_id=decision["module_package_id"],
                root=ROOT, now_utc="2026-09-20T12:01:00Z")
        with self.assertRaisesRegex(ValueError, "historical|archived"):
            routing.validate_route_for_execution(
                decision, root=ROOT, now_utc="2026-09-20T12:01:00Z",
                expected_decision_id=decision["decision_id"])
        with tempfile.TemporaryDirectory(prefix="iqs-s06-history-") as temp_root:
            output = Path(temp_root) / "new-run"
            with self.assertRaisesRegex(ValueError, "historical|archived"):
                qs.compose_from_route(
                    decision, output, now_utc="2026-09-20T12:01:00Z",
                    expected_route_decision_id=decision["decision_id"])
            self.assertFalse(output.exists())

    def test_archived_router_20_manifest_remains_readable(self):
        decision = json.loads((ROOT / "tests/fixtures/s06_router_20_search_route.json")
                              .read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="iqs-s06-old-manifest-") as temp_root:
            output = Path(temp_root) / "archived-run"
            # Recreate the archived producer solely inside TEMP; current new-run
            # entry points still refuse this router once the patch exits.
            with patch.object(routing, "validate_route_for_execution",
                              side_effect=lambda value, **_: routing.validate_route_snapshot(
                                  value, root=ROOT)):
                exported = qs.compose_from_route(
                    decision, output, now_utc="2026-09-20T12:01:00Z",
                    expected_route_decision_id=decision["decision_id"])
            self.assertEqual(exported["question_count"], 28)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            qs.validate_manifest_metric_contract(manifest)
            altered = copy.deepcopy(manifest)
            altered["routing_execution"]["expected_decision_id"] = "route_" + "0" * 64
            with self.assertRaisesRegex(ValueError, "expected decision identity"):
                qs.validate_manifest_metric_contract(altered)

    def test_archived_router_21_snapshot_is_readable_but_cannot_start_or_execute_work(self):
        with tempfile.TemporaryDirectory(prefix="iqs-s06-router21-") as temp_root:
            root = Path(temp_root)
            shutil.copytree(ROOT / "questions", root / "questions",
                            ignore=shutil.ignore_patterns("releases"))
            for ref in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                        "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                        "schemas/quick_scan/module-legacy-baseline.json"):
                target = root / ref; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / ref, target)
            policy_path = root / "questions/routing-policy.v2.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy.update(schema_version="1.1.0", router_version="2.1.0",
                          request_protocol="stockqa-route-confidence-1")
            policy.pop("classification_confidence_gate")
            policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
            package = routing.publish_routing_package(root=root, renderer_version=qs.RENDERER_VERSION,
                renderer_rules_sha256=qs.renderer_rules_sha256(), activate=False)
            identity = {"entity_id": "E_ARCHIVE", "identity_ref": "fixture:E_ARCHIVE",
                        "company": "Archived fixture", "ticker": "ARCHIVE", "exchange": "TEST",
                        "as_of": "2026-09-19"}
            with patch.object(routing, "_current_router_compatible",
                              side_effect=lambda version: version == "2.1.0"):
                snapshot = routing.resolve_route_decision(identity, package_id=package["package_id"],
                                                          root=root, now_utc="2026-09-20T12:00:00Z")
            self.assertEqual(snapshot["router_version"], "2.1.0")
            self.assertNotIn("classification_confidence", snapshot)
            routing.validate_route_snapshot(snapshot, root=root)
            with self.assertRaisesRegex(ValueError, "historical router 2.1.0 package"):
                routing.resolve_route_decision(identity, package_id=package["package_id"],
                                               root=root, now_utc="2026-09-20T12:00:00Z")
            with self.assertRaisesRegex(ValueError, "historical router 2.1.0 decision"):
                routing.validate_route_for_execution(snapshot, root=root, now_utc="2026-09-20T12:00:00Z")
            with patch.object(qs, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "historical router 2.1.0 decision"):
                    qs.compose_from_route(snapshot, root / "new-run", now_utc="2026-09-20T12:00:00Z",
                                          expected_route_decision_id=snapshot["decision_id"])
            self.assertFalse((root / "new-run").exists())


if __name__ == "__main__":
    unittest.main()
