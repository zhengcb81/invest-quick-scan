"""Automated tests for Identity and Universe Contract (Task C01).
Covers scenarios: ID-01, ID-02, ID-03, ID-04, UNI-04.
"""
import json
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import contract_validation as cv
SCHEMA_PATH = ROOT / "schemas/quick_scan/identity.schema.json"


class IdentityContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def validate_type(self, definition_name: str, instance: dict):
        wrapper_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": self.schema.get("definitions", {}),
            "$ref": f"#/definitions/{definition_name}"
        }
        validate(instance=instance, schema=wrapper_schema)

    def validate_entity(self, value: dict, **kwargs):
        kwargs.setdefault("trusted_market_registry", {
            "US": {"XNAS", "XNYS"}, "JP": {"XTKS"}, "GB": {"XLON"},
            "SG": {"XSES"}, "CN": {"XSHG", "XSHE"}, "HK": {"XHKG"},
        })
        return cv.validate_entity(value, **kwargs)

    def test_id_01_dual_listed_entity_separation(self):
        """ID-01: A/H dual-listed entity has 1 entity, 2 securities, separate valuation scopes."""
        entity = {
            "entity_id": "ENT_BYD_COMPANY",
            "canonical_name": "比亚迪股份有限公司",
            "incorporation_country": "CN",
            "company_wiki_ref": None,
            "formal_stockwiki_profile": None,
            "securities": [
                {
                    "security_id": "SEC_002594_SZ",
                    "entity_id": "ENT_BYD_COMPANY",
                    "market": "CN",
                    "exchange": "SZSE",
                    "ticker": "002594",
                    "currency": "CNY",
                    "security_type": "ordinary",
                    "adr_ratio": None,
                    "ordinary_security_ref": None,
                    "listing_status": "active"
                },
                {
                    "security_id": "SEC_01211_HK",
                    "entity_id": "ENT_BYD_COMPANY",
                    "market": "HK",
                    "exchange": "HKEX",
                    "ticker": "01211",
                    "currency": "HKD",
                    "security_type": "ordinary",
                    "adr_ratio": None,
                    "ordinary_security_ref": None,
                    "listing_status": "active"
                }
            ],
            "segments": [
                {"segment_id": "SEG_AUTO", "segment_name": "汽车业务", "revenue_share_pct": 80.0}
            ]
        }
        self.validate_type("Entity", entity)
        cv.validate_legacy_entity_read(entity)

        # Simulation of business vs valuation question routing:
        business_questions = ["IQS_01_MOAT", "IQS_02_MANAGEMENT"]
        valuation_questions = ["IQS_VALUATION_PE"]

        # Business questions asked once per Entity
        business_tasks = [(q, entity["entity_id"]) for q in business_questions]
        self.assertEqual(len(business_tasks), 2)

        # Valuation questions evaluated per Security
        valuation_tasks = [(q, sec["security_id"], sec["currency"]) for q in valuation_questions for sec in entity["securities"]]
        self.assertEqual(len(valuation_tasks), 2)
        self.assertEqual(valuation_tasks[0][2], "CNY")
        self.assertEqual(valuation_tasks[1][2], "HKD")

    def test_id_02_parent_subsidiary_cannot_merge_without_verified_issuer(self):
        """ID-02: PARENT and LISTED_SUB with same brand cannot merge unless verified_same_issuer is true."""
        bridge_unverified = {
            "bridge_id": "BRG_UNVERIFIED_PARENT_SUB",
            "entity_id": "ENT_PARENT_CORP",
            "security_ids": ["SEC_PARENT_STOCK", "SEC_SUB_STOCK"],
            "verified_same_issuer": False,
            "verification_source": "brand_name_heuristic",
            "verified_at": "2026-09-22T21:00:00Z",
            "notes": "母子公司虽同品牌，但属不同法人"
        }
        self.validate_type("VerifiedIssuerBridge", bridge_unverified)

        # Exercise the public v2 write validator, not a branch implemented only
        # inside this test. A candidate that places both listings in one Entity
        # must be rejected when the trusted issuer record says they are distinct.
        merged_entity, issuer_receipt = self._verified_pair()
        issuer_receipt["same_legal_issuer"] = bridge_unverified["verified_same_issuer"]
        with self.assertRaisesRegex(ValueError, "verified identity lacks exact issuer evidence"):
            cv.validate_identity_v20_read(
                merged_entity,
                trusted_identity_receipts={issuer_receipt["receipt_id"]: issuer_receipt},
                trusted_source_bindings=self._bindings_for(merged_entity),
            )

    def test_id_03_adr_ratio_boundary_and_no_guessing(self):
        """ID-03: When ADR ratio is unverified/null, adr_ratio must be null and no conversion guessed."""
        adr_sec = {
            "security_id": "SEC_BYDDY_US",
            "entity_id": "ENT_BYD_COMPANY",
            "market": "US",
            "exchange": "OTHER",
            "ticker": "BYDDY",
            "currency": "USD",
            "security_type": "adr",
            "adr_ratio": None,
            "ordinary_security_ref": "SEC_01211_HK",
            "listing_status": "active"
        }
        self.validate_type("Security", adr_sec)
        self.assertIsNone(adr_sec["adr_ratio"])

        with self.assertRaises(ValueError):
            cv.converted_ordinary_share_price(50.0, adr_sec["adr_ratio"])

    def test_id_04_lightweight_identity_without_wiki_prerequisite(self):
        """ID-04: Entity with company_wiki_ref=None and formal_stockwiki_profile=None is valid."""
        entity = {
            "entity_id": "ENT_NEW_TECH",
            "canonical_name": "新前沿科技股份有限公司",
            "incorporation_country": "CN",
            "company_wiki_ref": None,
            "formal_stockwiki_profile": None,
            "securities": [
                {
                    "security_id": "SEC_688999_SH",
                    "entity_id": "ENT_NEW_TECH",
                    "market": "CN",
                    "exchange": "SSE",
                    "ticker": "688999",
                    "currency": "CNY",
                    "security_type": "ordinary",
                    "adr_ratio": None,
                    "ordinary_security_ref": None,
                    "listing_status": "active"
                }
            ],
            "segments": []
        }
        self.validate_type("Entity", entity)
        cv.validate_legacy_entity_read(entity)
        self.assertIsNone(entity["company_wiki_ref"])
        self.assertIsNone(entity["formal_stockwiki_profile"])

    def test_uni_04_universe_manifest_capacity_expansion_and_logical_removal(self):
        """UNI-04: Universe expansion to 2003 does not evict old companies; removals are logical and reversible."""
        members = [
            {
                "entity_id": f"ENT_POOL_{index:04d}",
                "membership_status": "active" if index != 2002 else "logically_removed",
                "manual_pin": index < 100,
                "added_at": "2026-01-01T00:00:00Z",
                "removed_at": "2026-09-22T21:50:00Z" if index == 2002 else None,
                "removal_reason": "暂时移出" if index == 2002 else None,
                "restored_at": None,
                "restoration_reason": None,
                "version": 2 if index == 2002 else 1,
            }
            for index in range(2003)
        ]
        manifest = {
            "manifest_version": "1.1.0",
            "updated_at": "2026-09-22T21:55:00Z",
            "soft_target_capacity": 2000,
            "total_entities": 2003,
            "active_entities": 2002,
            "manual_pinned_count": 100,
            "members": members
        }
        self.validate_type("UniverseManifest", manifest)
        cv.validate_universe_manifest(manifest)
        self.assertEqual(manifest["total_entities"], 2003)
        self.assertTrue(manifest["total_entities"] > manifest["soft_target_capacity"])

        # Test restoring the logically removed member
        member = manifest["members"][-1]
        member["membership_status"] = "active"
        member["restored_at"] = "2026-09-22T21:58:00Z"
        member["restoration_reason"] = "重组完成，重新进入监控"
        member["version"] += 1
        self.validate_type("UniverseMember", member)
        self.assertEqual(member["version"], 3)
        self.assertEqual(member["membership_status"], "active")

    @staticmethod
    def _provisional_entity() -> dict:
        return {
            "identity_schema_version": "2.0.0",
            "identity_state": "provisional",
            "identity_revision": 1,
            "entity_id": "ENT_OPAQUE_1",
            "canonical_name": "示例挂牌公司",
            "incorporation_country": None,
            "scope_attestation_id": "ATT_EXACT_1",
            "company_wiki_ref": None,
            "formal_stockwiki_profile": None,
            "securities": [{
                "security_id": "SEC_OPAQUE_1",
                "entity_id": "ENT_OPAQUE_1",
                "market": "US",
                "exchange_raw": "NYSE ARCA",
                "exchange": None,
                "ticker": "EXAMPLE",
                "currency": None,
                "security_type": None,
                "listing_status": None,
                "source_binding_ref": "BND_SOURCE_1",
                "adr_ratio": None,
                "ordinary_security_ref": None,
            }],
            "segments": [],
        }

    @staticmethod
    def _scope_receipt() -> dict:
        return {
            "receipt_id": "ATT_EXACT_1",
            "kind": "provisional_scope",
            "entity_id": "ENT_OPAQUE_1",
            "identity_revision": 1,
            "security_id": "SEC_OPAQUE_1",
            "source_binding_ref": "BND_SOURCE_1",
            "source_namespace": "company-wiki-us",
            "source_record_id": "0000000001",
            "source_listing": {
                "market": "US", "exchange_raw": "NYSE ARCA",
                "ticker": "EXAMPLE", "canonical_name": "示例挂牌公司",
            },
            "known_attributes": {
                "incorporation_country": None, "exchange": None,
                "currency": None, "security_type": None, "listing_status": None,
            },
            "status": "active",
            "scope": "listed_operating_company",
            "basis": "user_exact_security_attestation",
            "negative_scope_flag": False,
            "evidence_ref": "user-selection-2026-09-26",
            "actor_id": "USER_1",
            "recorded_at": "2026-09-26T00:00:00Z",
        }

    @staticmethod
    def _bindings_for(entity: dict) -> dict[str, dict]:
        return {
            security["source_binding_ref"]: {
                "binding_ref": security["source_binding_ref"],
                "source_namespace": f"company-wiki-{security['market'].lower()}",
                "source_record_id": f"{index:010d}",
                "source_canonical_name": entity["canonical_name"],
                "security_id": security["security_id"],
                "entity_id": entity["entity_id"],
                "market": security["market"],
                "exchange_raw": security["exchange_raw"],
                "ticker": security["ticker"],
                "status": "active",
            }
            for index, security in enumerate(entity["securities"], start=1)
        }

    @classmethod
    def _verified_pair(cls) -> tuple[dict, dict]:
        first = deepcopy(cls._provisional_entity()["securities"][0])
        first.update({
            "market": "CN", "exchange_raw": "SSE", "exchange": "SSE",
            "ticker": "600001", "currency": "CNY", "security_type": "ordinary",
            "listing_status": "active",
        })
        second = deepcopy(first)
        second.update({
            "security_id": "SEC_OPAQUE_2", "market": "HK",
            "exchange_raw": "HKEX", "exchange": "HKEX", "ticker": "00001",
            "currency": "HKD", "source_binding_ref": "BND_SOURCE_2",
        })
        entity = {
            "identity_schema_version": "2.0.0", "identity_state": "verified",
            "identity_revision": 2, "entity_id": "ENT_OPAQUE_1",
            "canonical_name": "示例公司", "incorporation_country": "CN",
            "verified_issuer_receipt_id": "IVR_SAME_1", "company_wiki_ref": None,
            "formal_stockwiki_profile": None, "securities": [first, second], "segments": [],
        }
        bindings = cls._bindings_for(entity)
        receipt = {
            "receipt_id": "IVR_SAME_1", "kind": "verified_issuer",
            "entity_id": "ENT_OPAQUE_1", "identity_revision": 2,
            "status": "active", "recorded_at": "2026-09-26T00:00:00Z",
            "same_legal_issuer": True,
            "security_ids": ["SEC_OPAQUE_1", "SEC_OPAQUE_2"],
            "incorporation_country": "CN", "canonical_name": "示例公司",
            "security_attributes": {
                security["security_id"]: {
                    **{
                        field: security[field]
                        for field in ("market", "exchange_raw", "exchange", "ticker",
                                      "currency", "security_type", "listing_status",
                                      "source_binding_ref")
                    },
                    **{
                        field: bindings[security["source_binding_ref"]][field]
                        for field in ("source_namespace", "source_record_id",
                                      "source_canonical_name")
                    },
                }
                for security in (first, second)
            },
            "evidence_ref": "https://example.org/official-issuer-filing",
        }
        return entity, receipt

    def test_v2_provisional_preserves_unknowns_with_trusted_positive_scope(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        self.validate_type("ProvisionalEntityV2", entity)
        cv.validate_identity_v20_read(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                           trusted_source_bindings=self._bindings_for(entity))
        security = entity["securities"][0]
        self.assertIsNone(entity["incorporation_country"])
        for field in ("exchange", "currency", "security_type", "listing_status"):
            self.assertIsNone(security[field])
        self.assertEqual(security["exchange_raw"], "NYSE ARCA")

    def test_v2_legacy_read_does_not_authorize_new_write(self):
        legacy = {
            "entity_id": "ENT_LEGACY", "canonical_name": "旧记录",
            "incorporation_country": "CN", "securities": [{
                "security_id": "SEC_LEGACY", "entity_id": "ENT_LEGACY",
                "market": "CN", "exchange": "SSE", "ticker": "600000",
                "currency": "CNY", "security_type": "ordinary",
                "listing_status": "active",
            }], "segments": [],
        }
        cv.validate_legacy_entity_read(legacy)
        mismatched = deepcopy(legacy)
        mismatched["securities"][0]["entity_id"] = "ENT_OTHER"
        with self.assertRaisesRegex(ValueError, "belongs to another entity"):
            cv.validate_legacy_entity_read(mismatched)
        old_depositary = deepcopy(legacy)
        old_depositary["securities"][0].update({
            "security_type": "adr", "ordinary_security_ref": "SEC_OLD_BASE"
        })
        cv.validate_legacy_entity_read(old_depositary)
        with self.assertRaisesRegex(ValueError, "new writes require identity schema 2.1.0"):
            self.validate_entity(legacy)
        new_entity = self._provisional_entity()
        with self.assertRaisesRegex(ValueError, "legacy read path"):
            cv.validate_legacy_entity_read(new_entity)

    def test_v2_provisional_scope_receipt_must_match_exact_security_and_source(self):
        entity = self._provisional_entity()
        good = self._scope_receipt()
        with self.assertRaisesRegex(ValueError, "authoritative receipt"):
            cv.validate_identity_v20_read(entity, trusted_source_bindings=self._bindings_for(entity))
        for change in (
            {"status": "revoked"},
            {"entity_id": "ENT_OTHER"},
            {"identity_revision": 2},
            {"security_id": "SEC_OTHER"},
            {"source_binding_ref": "BND_OTHER"},
            {"source_listing": {"market": "US", "exchange_raw": "NYSE ARCA",
                                "ticker": "OTHER", "canonical_name": "示例挂牌公司"}},
            {"known_attributes": {"incorporation_country": "US"}},
            {"source_record_id": ""},
            {"scope": "listed_instrument"},
            {"negative_scope_flag": True},
            {"basis": "llm_guess"},
            {"actor_id": ""},
            {"recorded_at": "2026-09-26T01:00:00+01:00"},
        ):
            bad = {**good, **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                cv.validate_identity_v20_read(entity, trusted_identity_receipts={good["receipt_id"]: bad},
                                   trusted_source_bindings=self._bindings_for(entity))

    def test_v2_official_equity_category_requires_official_https_reference(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        receipt.update({"basis": "official_equity_category", "evidence_ref": "cninfo:A股"})
        with self.assertRaisesRegex(ValueError, "HTTPS source"):
            cv.validate_identity_v20_read(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=self._bindings_for(entity))
        receipt["evidence_ref"] = "https://www.cninfo.com.cn/new/data/szse_stock.json"
        cv.validate_identity_v20_read(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                           trusted_source_bindings=self._bindings_for(entity))

    def test_v2_provisional_cannot_silently_merge_two_listings(self):
        entity = self._provisional_entity()
        second = deepcopy(entity["securities"][0])
        second.update({"security_id": "SEC_OPAQUE_2", "source_binding_ref": "BND_SOURCE_2"})
        entity["securities"].append(second)
        with self.assertRaises(ValidationError):
            cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": self._scope_receipt()},
                               trusted_source_bindings=self._bindings_for(entity))

    def test_v2_verified_cross_listing_requires_exact_issuer_receipt_and_owner(self):
        entity, receipt = self._verified_pair()
        bindings = self._bindings_for(entity)
        cv.validate_identity_v20_read(entity, trusted_identity_receipts={"IVR_SAME_1": receipt},
                           trusted_source_bindings=bindings)
        for change in ({"same_legal_issuer": False},
                       {"security_ids": ["SEC_OPAQUE_1", "SEC_OTHER"]},
                       {"incorporation_country": "US"},
                       {"canonical_name": "另一公司"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                cv.validate_identity_v20_read(entity, trusted_identity_receipts={
                    "IVR_SAME_1": {**receipt, **change}
                }, trusted_source_bindings=bindings)
        wrong_type = deepcopy(entity)
        wrong_type["securities"][1]["security_type"] = "preferred"
        with self.assertRaisesRegex(ValueError, "attributes differ"):
            cv.validate_identity_v20_read(wrong_type, trusted_identity_receipts={"IVR_SAME_1": receipt},
                               trusted_source_bindings=bindings)
        wrong_owner = deepcopy(entity)
        wrong_owner["securities"][1]["entity_id"] = "ENT_LISTED_SUB"
        with self.assertRaisesRegex(ValueError, "belongs to another entity"):
            cv.validate_identity_v20_read(wrong_owner, trusted_identity_receipts={"IVR_SAME_1": receipt},
                               trusted_source_bindings=bindings)
        guessed_country = deepcopy(entity)
        guessed_country["incorporation_country"] = "ZZ"
        with self.assertRaises(ValidationError):
            cv.validate_identity_v20_read(guessed_country, trusted_identity_receipts={"IVR_SAME_1": receipt},
                               trusted_source_bindings=bindings)

    def test_v2_provisional_known_attributes_need_owner_receipt(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        entity["incorporation_country"] = "US"
        with self.assertRaisesRegex(ValueError, "positive listing qualification"):
            cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": receipt},
                               trusted_source_bindings=self._bindings_for(entity))
        receipt["known_attributes"]["incorporation_country"] = "US"
        cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": receipt},
                           trusted_source_bindings=self._bindings_for(entity))

    def test_v2_receipt_cannot_self_certify_missing_source_binding(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        receipt["source_record_id"] = "FORGED_RECORD"
        # A receipt and incoming Entity that agree with each other do not
        # establish that either matches the owner's source binding row.
        with self.assertRaisesRegex(ValueError, "source binding"):
            cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": receipt})
        with self.assertRaisesRegex(ValueError, "positive listing qualification"):
            cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": receipt},
                               trusted_source_bindings=self._bindings_for(entity))

    def test_v2_source_binding_must_match_current_owner_row(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        baseline = self._bindings_for(entity)
        for field, changed in (
            ("source_namespace", "company-wiki-cn"),
            ("source_record_id", "OTHER"),
            ("security_id", "SEC_OTHER"),
            ("entity_id", "ENT_OTHER"),
            ("market", "CN"),
            ("exchange_raw", "BATS"),
            ("ticker", "OTHER"),
            ("status", "retired"),
        ):
            bindings = deepcopy(baseline)
            bindings["BND_SOURCE_1"][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                cv.validate_identity_v20_read(entity, trusted_identity_receipts={"ATT_EXACT_1": receipt},
                                   trusted_source_bindings=bindings)

    def test_v2_verified_receipt_must_cover_raw_listing_identity(self):
        entity, receipt = self._verified_pair()
        for field, changed in (("ticker", "99999"), ("exchange_raw", "BATS")):
            altered = deepcopy(entity)
            altered["securities"][1][field] = changed
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "attributes differ"):
                cv.validate_identity_v20_read(altered, trusted_identity_receipts={"IVR_SAME_1": receipt},
                                   trusted_source_bindings=self._bindings_for(altered))

    def test_v2_ordinary_and_preferred_cannot_have_adr_ratio(self):
        entity, receipt = self._verified_pair()
        for kind in ("ordinary", "preferred"):
            altered = deepcopy(entity)
            altered["securities"][0]["security_type"] = kind
            altered["securities"][0]["adr_ratio"] = 2.0
            matching = deepcopy(receipt)
            matching["security_attributes"]["SEC_OPAQUE_1"]["security_type"] = kind
            matching["verified_adr_ratios"] = {"SEC_OPAQUE_1": 2.0}
            with self.subTest(kind=kind, boundary="schema"), self.assertRaises(ValidationError):
                self.validate_type("SecurityV2", altered["securities"][0])
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "ADR ratio"):
                cv.validate_identity_v20_read(altered, trusted_identity_receipts={"IVR_SAME_1": matching},
                                   trusted_source_bindings=self._bindings_for(entity))


    @staticmethod
    def _provisional_entity_v21() -> dict:
        return {
            "identity_schema_version": "2.1.0", "identity_state": "provisional",
            "identity_revision": 1, "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
            "canonical_name": "Example issuer", "incorporation_country": None,
            "scope_attestation_id": "ATT_V21", "company_wiki_ref": None,
            "formal_stockwiki_profile": None,
            "securities": [{
                "security_id": "SEC_22222222-2222-4222-8222-222222222222", "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
                "security_type": None, "share_class": None, "adr_ratio": None,
                "ordinary_security_ref": None,
            }],
            "listings": [{
                "listing_id": "LST_33333333-3333-4333-8333-333333333333", "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
                "security_id": "SEC_22222222-2222-4222-8222-222222222222", "market": "US",
                "exchange_raw": "NYSE ARCA", "exchange_mic": None,
                "ticker_raw": "EXAMPLE", "ticker": "EXAMPLE",
                "currency": None, "listing_status": None,
                "source_binding_ref": "BND_V21", "valid_from": None, "valid_to": None,
            }],
            "segments": [],
        }

    @staticmethod
    def _bindings_for_v21(entity: dict) -> dict[str, dict]:
        return {
            listing["source_binding_ref"]: {
                "binding_ref": listing["source_binding_ref"],
                "source_namespace": "fixture-exchange-master",
                "source_record_id": f"row:{listing['listing_id']}",
                "source_canonical_name": entity["canonical_name"],
                "entity_id": entity["entity_id"], "security_id": listing["security_id"],
                "listing_id": listing["listing_id"], "market": listing["market"],
                "exchange_raw": listing["exchange_raw"], "exchange_mic": listing["exchange_mic"],
                "ticker_raw": listing["ticker_raw"], "ticker": listing["ticker"],
                "valid_from": listing["valid_from"], "valid_to": listing["valid_to"],
                "status": "active",
            }
            for listing in entity["listings"]
        }

    @classmethod
    def _scope_receipt_v21(cls, entity: dict) -> dict:
        listing = entity["listings"][0]
        binding = cls._bindings_for_v21(entity)[listing["source_binding_ref"]]
        return {
            "receipt_id": entity["scope_attestation_id"],
            "kind": "provisional_scope", "entity_id": entity["entity_id"],
            "identity_revision": entity["identity_revision"], "status": "active",
            "security_id": listing["security_id"], "listing_id": listing["listing_id"],
            "source_binding_ref": listing["source_binding_ref"],
            "source_namespace": binding["source_namespace"],
            "source_record_id": binding["source_record_id"],
            "source_listing": {
                **{field: listing[field] for field in (
                    "listing_id", "security_id", "market", "exchange_raw", "exchange_mic",
                    "ticker_raw", "ticker", "valid_from", "valid_to"
                )},
                "canonical_name": entity["canonical_name"],
            },
            "known_attributes": {
                "incorporation_country": entity["incorporation_country"],
                "security_type": entity["securities"][0]["security_type"],
                "share_class": entity["securities"][0]["share_class"],
                "currency": listing["currency"], "listing_status": listing["listing_status"],
            },
            "scope": "listed_operating_company", "basis": "user_exact_security_attestation",
            "negative_scope_flag": False, "evidence_ref": "user-selection-v21",
            "actor_id": "USER_1", "recorded_at": "2026-09-28T00:00:00Z",
        }

    def test_v21_provisional_uses_separate_issuer_security_and_listing_layers(self):
        entity = self._provisional_entity_v21()
        receipt = self._scope_receipt_v21(entity)
        self.validate_type("ProvisionalEntityV21", entity)
        self.validate_type("SecurityV21", entity["securities"][0])
        self.validate_type("ListingV21", entity["listings"][0])
        self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                           trusted_source_bindings=self._bindings_for_v21(entity))
        self.assertNotIn("ticker", entity["securities"][0])
        self.assertNotIn("exchange_raw", entity["securities"][0])
        self.assertIsNone(entity["listings"][0]["exchange_mic"])

    def test_v21_internal_entity_security_listing_ids_are_opaque_uuid4(self):
        security = self._provisional_entity_v21()["securities"][0]
        self.validate_type("SecurityV21", security)
        for field, value in (("entity_id", "ENT_600000"), ("security_id", "SEC_AAPL")):
            bad = {**security, field: value}
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.validate_type("SecurityV21", bad)
        listing = self._provisional_entity_v21()["listings"][0]
        listing["listing_id"] = "LST_NASDAQ_AAPL"
        with self.assertRaises(ValidationError):
            self.validate_type("ListingV21", listing)

    def test_v21_group_relationships_never_assert_issuer_equivalence(self):
        relationship = {
            "relationship_id": "REL_99999999-9999-4999-8999-999999999999",
            "from_entity_id": "ENT_11111111-1111-4111-8111-111111111111",
            "to_entity_id": "ENT_88888888-8888-4888-8888-888888888888",
            "relationship_type": "controlled_by", "verification_status": "verified",
            "source_namespace": "official-register", "source_record_id": "record:1",
            "evidence_ref": "https://example.org/relationship",
            "valid_from": "2020-01-01T00:00:00Z", "valid_to": None,
        }
        self.validate_type("EntityRelationshipV21", relationship)
        cv.validate_entity_relationship(relationship)
        false_equivalence = {**relationship, "relationship_type": "same_issuer"}
        with self.assertRaises(ValidationError):
            self.validate_type("EntityRelationshipV21", false_equivalence)
        self_relation = {**relationship, "to_entity_id": relationship["from_entity_id"]}
        with self.assertRaisesRegex(ValueError, "cannot relate an entity to itself"):
            cv.validate_entity_relationship(self_relation)

    def test_v21_similar_names_remain_distinct_issuers_without_authoritative_bridge(self):
        first = self._provisional_entity_v21()
        second = deepcopy(first)
        first["canonical_name"] = "中微公司"
        second["entity_id"] = "ENT_88888888-8888-4888-8888-888888888888"
        second["canonical_name"] = "中微半导体"
        second["scope_attestation_id"] = "ATT_V21_SECOND"
        second["securities"][0].update({
            "entity_id": second["entity_id"],
            "security_id": "SEC_88888888-8888-4888-8888-888888888888",
        })
        second["listings"][0].update({
            "entity_id": second["entity_id"], "security_id": second["securities"][0]["security_id"],
            "listing_id": "LST_88888888-8888-4888-8888-888888888888",
            "source_binding_ref": "BND_V21_SECOND",
        })
        for entity in (first, second):
            receipt = self._scope_receipt_v21(entity)
            self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=self._bindings_for_v21(entity))
        self.assertNotEqual(first["entity_id"], second["entity_id"])

    def test_v21_identity_event_binds_append_only_revision_and_change(self):
        entity = self._provisional_entity_v21()
        event = {
            "event_id": "EVT_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "entity_id": entity["entity_id"], "from_revision": 1, "to_revision": 2,
            "event_type": "renamed", "effective_at": "2026-01-01T00:00:00Z",
            "recorded_at": "2026-02-01T00:00:00Z",
            "source_namespace": "official-register", "source_record_id": "record:2",
            "evidence_ref": "https://example.org/rename", "actor_id": None,
            "related_entity_ids": [], "affected_security_ids": [entity["securities"][0]["security_id"]],
            "affected_listing_ids": [entity["listings"][0]["listing_id"]],
            "listing_id": None, "security_id": None,
            "field_path": "canonical_name", "old_value": "Old name", "new_value": "New name",
            "reason": "Official legal-name change.",
        }
        self.validate_type("IdentityEventV21", event)
        cv.validate_identity_event(event)
        skipped_revision = {**event, "to_revision": 3}
        with self.assertRaisesRegex(ValueError, "exactly one revision"):
            cv.validate_identity_event(skipped_revision)
        no_op = {**event, "new_value": event["old_value"]}
        with self.assertRaisesRegex(ValueError, "no-op identity event"):
            cv.validate_identity_event(no_op)
        self_link = {**event, "event_type": "issuer_merged",
                     "related_entity_ids": [entity["entity_id"]],
                     "field_path": None, "old_value": None, "new_value": None}
        with self.assertRaisesRegex(ValueError, "cannot merge or split into itself"):
            cv.validate_identity_event(self_link)

    def test_v21_rename_and_ticker_events_must_explain_exact_snapshots(self):
        before = self._provisional_entity_v21()
        after = deepcopy(before)
        after["identity_revision"] = 2
        after["canonical_name"] = "Renamed issuer"
        rename = {
            "event_id": "EVT_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "entity_id": before["entity_id"], "from_revision": 1, "to_revision": 2,
            "event_type": "renamed", "effective_at": "2026-01-01T00:00:00Z",
            "recorded_at": "2026-02-01T00:00:00Z", "source_namespace": "registry",
            "source_record_id": "R4", "evidence_ref": "https://example.org/rename",
            "actor_id": None, "related_entity_ids": [],
            "affected_security_ids": [before["securities"][0]["security_id"]],
            "affected_listing_ids": [before["listings"][0]["listing_id"]],
            "listing_id": None, "security_id": None, "field_path": "canonical_name",
            "old_value": before["canonical_name"], "new_value": after["canonical_name"],
            "reason": "Official name change.",
        }
        cv.validate_identity_transition(rename, before, after)
        with self.assertRaisesRegex(ValueError, "rename affected IDs must exactly cover"):
            cv.validate_identity_transition({**rename, "affected_security_ids": []}, before, after)
        inconsistent = deepcopy(after)
        inconsistent["listings"][0]["ticker"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "does not explain the exact snapshot change"):
            cv.validate_identity_transition(rename, before, inconsistent)

        new_security_id = "SEC_44444444-4444-4444-8444-444444444444"
        after_security = deepcopy(before)
        after_security["identity_revision"] = 2
        after_security["securities"].append({
            "security_id": new_security_id, "entity_id": before["entity_id"],
            "security_type": "ordinary", "share_class": "B", "adr_ratio": None,
            "ordinary_security_ref": None,
        })
        security_event = {
            **rename, "event_id": "EVT_bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "event_type": "security_added", "field_path": None, "old_value": None,
            "new_value": None, "security_id": new_security_id,
            "affected_security_ids": [new_security_id], "affected_listing_ids": [],
            "listing_id": None,
        }
        cv.validate_identity_transition(security_event, before, after_security)
        after_unrelated_change = deepcopy(after_security)
        after_unrelated_change["canonical_name"] = "Unrelated rename"
        with self.assertRaisesRegex(ValueError, "does not explain the exact snapshot change"):
            cv.validate_identity_transition(security_event, before, after_unrelated_change)

        ticker_after = deepcopy(before)
        ticker_after["identity_revision"] = 2
        ticker_after["listings"][0]["ticker"] = "RENAMED"
        wrong_security_ticker = {
            **rename, "event_id": "EVT_cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "event_type": "ticker_changed", "field_path": "ticker",
            "listing_id": before["listings"][0]["listing_id"],
            "security_id": new_security_id,
            "affected_listing_ids": [before["listings"][0]["listing_id"]],
            "affected_security_ids": [new_security_id], "old_value": "EXAMPLE",
            "new_value": "RENAMED",
        }
        with self.assertRaisesRegex(ValueError, "ticker event does not match before/after listing"):
            cv.validate_identity_transition(wrong_security_ticker, before, ticker_after)
        correct_security_ticker = {
            **wrong_security_ticker,
            "security_id": before["listings"][0]["security_id"],
            "affected_security_ids": [before["listings"][0]["security_id"]],
        }
        cv.validate_identity_transition(correct_security_ticker, before, ticker_after)

        dangling_before = deepcopy(before)
        dangling_after = deepcopy(ticker_after)
        phantom_security_id = "SEC_77777777-7777-4777-8777-777777777777"
        dangling_before["listings"][0]["security_id"] = phantom_security_id
        dangling_after["listings"][0]["security_id"] = phantom_security_id
        dangling_event = {
            **correct_security_ticker, "security_id": phantom_security_id,
            "affected_security_ids": [phantom_security_id],
        }
        with self.assertRaisesRegex(ValueError, "missing or foreign security"):
            cv.validate_identity_transition(dangling_event, dangling_before, dangling_after)

        foreign_before = deepcopy(before)
        foreign_after = deepcopy(ticker_after)
        foreign_issuer_id = "ENT_88888888-8888-4888-8888-888888888888"
        foreign_before["securities"][0]["entity_id"] = foreign_issuer_id
        foreign_after["securities"][0]["entity_id"] = foreign_issuer_id
        with self.assertRaisesRegex(ValueError, "duplicate or foreign security"):
            cv.validate_identity_transition(correct_security_ticker, foreign_before, foreign_after)

        listing_after = deepcopy(before)
        listing_after["identity_revision"] = 2
        new_listing = deepcopy(before["listings"][0])
        new_listing.update({"listing_id": "LST_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                            "ticker": "NEW", "ticker_raw": "NEW",
                            "source_binding_ref": "BND_NEW_LISTING"})
        listing_after["listings"].append(new_listing)
        listing_added = {
            **rename, "event_id": "EVT_dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "event_type": "listing_added", "field_path": None, "old_value": None,
            "new_value": None, "listing_id": new_listing["listing_id"],
            "security_id": new_security_id, "affected_listing_ids": [new_listing["listing_id"]],
            "affected_security_ids": [new_security_id],
        }
        with self.assertRaisesRegex(ValueError, "listing-added event security does not match"):
            cv.validate_identity_transition(listing_added, before, listing_after)

    def test_v21_provisional_receipt_must_bind_exact_listing(self):
        entity = self._provisional_entity_v21()
        receipt = self._scope_receipt_v21(entity)
        for path, changed in (("listing_id", "LST_OTHER"), ("exchange_mic", "XNAS"),
                              ("ticker_raw", "OTHER"), ("ticker", "OTHER")):
            bad = deepcopy(receipt)
            bad["source_listing"][path] = changed
            with self.subTest(field=path), self.assertRaisesRegex(
                ValueError, "positive listing qualification"
            ):
                self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: bad},
                                   trusted_source_bindings=self._bindings_for_v21(entity))

    def test_v21_source_binding_must_match_raw_and_normalized_listing_key(self):
        entity = self._provisional_entity_v21()
        receipt = self._scope_receipt_v21(entity)
        baseline = self._bindings_for_v21(entity)
        for field, changed in (("ticker_raw", "EXAMPLE.A"), ("ticker", "OTHER"),
                              ("exchange_raw", "NYSE"), ("exchange_mic", "XNYS"),
                              ("valid_from", "2026-01-01T00:00:00Z"),
                               ("listing_id", "LST_OTHER"), ("source_record_id", "source:other")):
            bindings = deepcopy(baseline)
            bindings["BND_V21"][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                                   trusted_source_bindings=bindings)

    def test_v21_listing_cannot_reference_foreign_or_missing_security(self):
        entity = self._provisional_entity_v21()
        receipt = self._scope_receipt_v21(entity)
        entity["listings"][0]["security_id"] = "SEC_66666666-6666-4666-8666-666666666666"
        with self.assertRaisesRegex(ValueError, "listing security"):
            self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=self._bindings_for_v21(entity))
        entity = self._provisional_entity_v21()
        entity["listings"][0]["entity_id"] = "ENT_77777777-7777-4777-8777-777777777777"
        with self.assertRaisesRegex(ValueError, "listing belongs to another entity"):
            self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=self._bindings_for_v21(entity))

    def test_v20_identity_is_historical_read_only(self):
        entity = self._provisional_entity()
        receipt = self._scope_receipt()
        self.validate_type("ProvisionalEntityV20", entity)
        cv.validate_identity_v20_read(
            entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
            trusted_source_bindings=self._bindings_for(entity),
        )
        with self.assertRaisesRegex(ValueError, "new writes require identity schema 2.1.0"):
            self.validate_entity(entity)

    def test_v21_aliases_are_nonunique_claims_and_issuer_ids_are_namespaced(self):
        alias_claim = {
            "alias_id": "ALS_1", "entity_id": "ENT_11111111-1111-4111-8111-111111111111", "name": "中微",
            "alias_type": "trading_short_name", "language": "zh-CN", "jurisdiction": "CN",
            "source_namespace": "official-exchange", "source_record_id": "issuer:1",
            "verification_status": "verified", "evidence_ref": "https://example.org/issuer",
            "valid_from": None, "valid_to": None,
        }
        identifier_claim = {
            "claim_id": "ICL_1", "entity_id": "ENT_11111111-1111-4111-8111-111111111111", "subject_type": "issuer",
            "scheme": "cninfo_org_id", "assigning_authority": "CNINFO",
            "jurisdiction": "CN", "value": "123456", "source_namespace": "cninfo",
            "source_record_id": "listing:1", "verification_status": "verified",
            "evidence_ref": "https://example.org/issuer", "valid_from": None, "valid_to": None,
        }
        self.validate_type("NameAliasClaimV21", alias_claim)
        self.validate_type("IssuerIdentifierClaimV21", identifier_claim)
        other_alias = {**alias_claim, "alias_id": "ALS_2", "entity_id": "ENT_88888888-8888-4888-8888-888888888888"}
        self.validate_type("NameAliasClaimV21", other_alias)
        cv.validate_name_alias_claim_v21(alias_claim)
        cv.validate_name_alias_claim_v21(other_alias)
        other_namespace = {**identifier_claim, "claim_id": "ICL_2", "entity_id": "ENT_88888888-8888-4888-8888-888888888888",
                           "scheme": "provider_local_id", "assigning_authority": "provider-B",
                           "source_namespace": "provider-B"}
        self.validate_type("IssuerIdentifierClaimV21", other_namespace)
        security_claim = {**identifier_claim, "claim_id": "ICL_SECURITY", "subject_type": "security"}
        with self.assertRaises(ValidationError):
            self.validate_type("IssuerIdentifierClaimV21", security_claim)
        security_claim["subject_id"] = "SEC_22222222-2222-4222-8222-222222222222"
        self.validate_type("IssuerIdentifierClaimV21", security_claim)
        security_claim["subject_id"] = "LST_33333333-3333-4333-8333-333333333333"
        with self.assertRaises(ValidationError):
            self.validate_type("IssuerIdentifierClaimV21", security_claim)

    def test_v21_claim_validation_requires_evidence_and_ordered_effective_dates(self):
        alias = {
            "alias_id": "ALS_3", "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
            "name": "Example", "alias_type": "former_legal_name", "language": "en",
            "jurisdiction": "US", "source_namespace": "registry", "source_record_id": "R1",
            "verification_status": "verified", "evidence_ref": None,
            "valid_from": "2026-02-01T00:00:00Z", "valid_to": "2026-01-01T00:00:00Z",
        }
        with self.assertRaises(ValidationError):
            self.validate_type("NameAliasClaimV21", alias)
        alias["evidence_ref"] = "https://example.org/alias"
        self.validate_type("NameAliasClaimV21", alias)
        with self.assertRaisesRegex(ValueError, "ordered half-open interval"):
            cv.validate_name_alias_claim_v21(alias)

        claim = {
            "claim_id": "ICL_2", "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
            "subject_type": "issuer", "scheme": "lei", "assigning_authority": "GLEIF",
            "jurisdiction": "US", "value": "549300EXAMPLE", "source_namespace": "registry",
            "source_record_id": "R2", "verification_status": "verified", "evidence_ref": None,
            "valid_from": None, "valid_to": None,
        }
        with self.assertRaises(ValidationError):
            self.validate_type("IssuerIdentifierClaimV21", claim)
        claim["evidence_ref"] = "https://example.org/lei"
        self.validate_type("IssuerIdentifierClaimV21", claim)
        claim["valid_from"] = "2026-02-01T00:00:00Z"
        claim["valid_to"] = "2026-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "ordered half-open interval"):
            cv.validate_identifier_claim_v21(claim)

    def test_v21_market_code_is_global_and_missing_mic_collision_fails_closed(self):
        for market in ("JP", "GB", "SG"):
            entity = self._provisional_entity_v21()
            entity["listings"][0]["market"] = market
            receipt = self._scope_receipt_v21(entity)
            bindings = self._bindings_for_v21(entity)
            bindings["BND_V21"]["market"] = market
            with self.subTest(market=market):
                self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                                   trusted_source_bindings=bindings)

        invalid_market = self._provisional_entity_v21()
        invalid_market["listings"][0]["market"] = "ZZ"
        with self.assertRaisesRegex(ValueError, "absent from trusted market registry"):
            self.validate_entity(invalid_market)

        wrong_market_mic = self._provisional_entity_v21()
        wrong_market_mic["listings"][0].update({"market": "JP", "exchange_mic": "XNAS"})
        with self.assertRaisesRegex(ValueError, "MIC does not belong"):
            self.validate_entity(wrong_market_mic)

        malformed_registry = self._provisional_entity_v21()
        with self.assertRaisesRegex(ValueError, "registry entry is invalid"):
            self.validate_entity(malformed_registry, trusted_market_registry={"US": "XNAS"})

        entity, receipt = self._verified_pair_v21_for_listings()
        first, second = entity["listings"]
        first.update({"market": "US", "exchange_raw": "New York Stock Exchange",
                      "exchange_mic": None, "ticker": "DUAL", "ticker_raw": "DUAL"})
        second.update({"market": "US", "exchange_raw": "NYSE", "exchange_mic": "XNYS",
                       "ticker": "DUAL", "ticker_raw": "DUAL"})
        bindings = self._bindings_for_v21(entity)
        receipt = self._verified_receipt_v21(entity, bindings)
        with self.assertRaisesRegex(ValueError, "venue is ambiguous without MIC"):
            self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=bindings)

    def test_v21_delisted_listing_can_match_retired_owner_binding(self):
        entity = self._provisional_entity_v21()
        listing = entity["listings"][0]
        listing.update({"listing_status": "delisted", "valid_from": "2020-01-01T00:00:00Z",
                        "valid_to": "2025-01-01T00:00:00Z"})
        receipt = self._scope_receipt_v21(entity)
        bindings = self._bindings_for_v21(entity)
        bindings[listing["source_binding_ref"]].update({
            "valid_from": listing["valid_from"], "valid_to": listing["valid_to"], "status": "retired",
        })
        self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                           trusted_source_bindings=bindings)
        bindings[listing["source_binding_ref"]]["status"] = "active"
        with self.assertRaisesRegex(ValueError, "source binding differs"):
            self.validate_entity(entity, trusted_identity_receipts={receipt["receipt_id"]: receipt},
                               trusted_source_bindings=bindings)

    def test_analysis_subject_separates_reporting_scope_from_legal_issuer(self):
        subject = self._analysis_subject_v10()
        self.validate_type("AnalysisSubjectV10", subject)
        validate(instance=subject, schema=self.schema)
        issuer_states = {subject["primary_issuer_id"]: "verified"}
        with self.assertRaisesRegex(ValueError, "trusted reporting-perimeter receipt"):
            cv.validate_analysis_subject(subject, trusted_issuer_states=issuer_states)
        cv.validate_analysis_subject(
            subject, trusted_issuer_states=issuer_states,
            trusted_reporting_perimeter_receipts=self._trusted_perimeter_receipts(subject),
        )

        # A valid issuer/security/listing record alone does not define the
        # reporting perimeter for a paid company scan.
        issuer = self._provisional_entity_v21()
        with self.assertRaisesRegex(ValueError, "trusted issuer registry"):
            cv.validate_analysis_subject(subject)
        with self.assertRaisesRegex(ValueError, "not in the trusted issuer registry"):
            cv.validate_analysis_subject(subject, trusted_issuer_states={})
        self.assertNotIn("analysis_subject_id", issuer)

        standalone = deepcopy(subject)
        standalone["scope_kind"] = "standalone_issuer"
        standalone["perimeter_coverage"] = "not_applicable"
        standalone["memberships"].append({
            "entity_id": "ENT_88888888-8888-4888-8888-888888888888",
            "role": "consolidated_subsidiary", "valid_from": None, "valid_to": None,
            "evidence_ref": "https://example.org/consolidation",
        })
        with self.assertRaises(ValidationError):
            cv.validate_analysis_subject(standalone, trusted_issuer_states={
                standalone["primary_issuer_id"]: "verified",
                "ENT_88888888-8888-4888-8888-888888888888": "verified",
            })

    def test_analysis_subject_membership_is_not_inferred_from_group_relationship(self):
        subject = self._analysis_subject_v10()
        subject["memberships"].append({
            "entity_id": "ENT_88888888-8888-4888-8888-888888888888",
            "role": "consolidated_subsidiary", "valid_from": None, "valid_to": None,
            "evidence_ref": "fabricated",
        })
        # Verified issuer identity and a self-asserted membership reference do
        # not prove a consolidated reporting relationship.
        issuer_states = {
            subject["primary_issuer_id"]: "verified",
            "ENT_88888888-8888-4888-8888-888888888888": "verified",
        }
        with self.assertRaisesRegex(ValueError, "exact trusted reporting-perimeter receipt"):
            cv.validate_analysis_subject(subject, trusted_issuer_states=issuer_states)
        subject["memberships"][1]["evidence_ref"] = "https://example.org/reporting-scope"
        cv.validate_analysis_subject(
            subject, trusted_issuer_states=issuer_states,
            trusted_reporting_perimeter_receipts=self._trusted_perimeter_receipts(subject),
        )
        stale_receipt = self._trusted_perimeter_receipts(subject)
        stale_receipt[f"{subject['analysis_subject_id']}@{subject['analysis_subject_revision']}"][
            "perimeter_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(ValueError, "exact trusted reporting-perimeter receipt"):
            cv.validate_analysis_subject(
                subject, trusted_issuer_states=issuer_states,
                trusted_reporting_perimeter_receipts=stale_receipt,
            )
        duplicate = deepcopy(subject)
        duplicate["memberships"].append(deepcopy(duplicate["memberships"][1]))
        with self.assertRaisesRegex(ValueError, "duplicate issuer membership"):
            cv.validate_analysis_subject(duplicate, trusted_issuer_states=issuer_states)

    def test_provisional_analysis_subject_is_exact_listing_scoped_and_cannot_expand_group(self):
        entity = self._provisional_entity_v21()
        subject = self._analysis_subject_v10()
        subject.update({
            "scope_kind": "provisional_listing_scope", "perimeter_coverage": "not_applicable",
            "anchor_listing_id": entity["listings"][0]["listing_id"],
            "memberships": [{
                "entity_id": entity["entity_id"], "role": "primary_issuer",
                "valid_from": None, "valid_to": None, "evidence_ref": "receipt://ATT_V21",
            }],
        })
        with self.assertRaisesRegex(ValueError, "trusted issuer registry"):
            cv.validate_analysis_subject(subject, trusted_issuer_states={entity["entity_id"]: "provisional"})
        cv.validate_analysis_subject(
            subject, trusted_issuer_states={entity["entity_id"]: "provisional"},
            trusted_listing_to_issuer={entity["listings"][0]["listing_id"]: entity["entity_id"]},
        )
        wrong_anchor = deepcopy(subject)
        wrong_anchor["anchor_listing_id"] = "LST_44444444-4444-4444-8444-444444444444"
        with self.assertRaisesRegex(ValueError, "does not belong to the provisional issuer"):
            cv.validate_analysis_subject(
                wrong_anchor, trusted_issuer_states={entity["entity_id"]: "provisional"},
                trusted_listing_to_issuer={entity["listings"][0]["listing_id"]: entity["entity_id"]},
            )
        wrong_scope = deepcopy(subject)
        wrong_scope["scope_kind"] = "consolidated_reporting_group"
        wrong_scope["perimeter_coverage"] = "not_enumerated"
        with self.assertRaises(ValidationError):
            cv.validate_analysis_subject(
                wrong_scope, trusted_issuer_states={entity["entity_id"]: "provisional"},
                trusted_listing_to_issuer={entity["listings"][0]["listing_id"]: entity["entity_id"]},
            )

    def test_analysis_subject_event_advances_one_revision_and_requires_evidence(self):
        before = self._analysis_subject_v10()
        after = deepcopy(before)
        after["analysis_subject_revision"] = 2
        additional_member = {
            "entity_id": "ENT_88888888-8888-4888-8888-888888888888",
            "role": "consolidated_subsidiary", "valid_from": None, "valid_to": None,
            "evidence_ref": "https://example.org/new-perimeter",
        }
        after["memberships"].append(additional_member)
        after["perimeter_coverage"] = "complete_as_disclosed"
        issuer_states = {
            before["primary_issuer_id"]: "verified",
            additional_member["entity_id"]: "verified",
        }
        event = {
            "event_id": "ASE_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "analysis_subject_id": "ASJ_99999999-9999-4999-8999-999999999999",
            "from_revision": 1, "to_revision": 2, "event_type": "perimeter_changed",
            "effective_at": "2026-01-01T00:00:00Z", "recorded_at": "2026-02-01T00:00:00Z",
            "affected_entity_ids": [additional_member["entity_id"]],
            "evidence_ref": "https://example.org/new-perimeter", "reason": "New annual report scope.",
            "old_value": cv.analysis_subject_perimeter_sha256(before),
            "new_value": cv.analysis_subject_perimeter_sha256(after),
        }
        receipts = self._trusted_perimeter_receipts(before, after)
        self.validate_type("AnalysisSubjectEventV10", event)
        validate(instance=event, schema=self.schema)
        cv.validate_analysis_subject_event(event)
        cv.validate_analysis_subject_transition(
            event, before, after, trusted_issuer_states=issuer_states,
            trusted_reporting_perimeter_receipts=receipts,
        )
        with self.assertRaisesRegex(ValueError, "exactly one revision"):
            cv.validate_analysis_subject_event({**event, "to_revision": 3})
        with self.assertRaises(ValidationError):
            self.validate_type("AnalysisSubjectEventV10", {**event, "evidence_ref": None})
        wrong_affected = {**event, "affected_entity_ids": [before["primary_issuer_id"]]}
        with self.assertRaisesRegex(ValueError, "affected entities do not match"):
            cv.validate_analysis_subject_transition(
                wrong_affected, before, after, trusted_issuer_states=issuer_states,
                trusted_reporting_perimeter_receipts=receipts,
            )

        alternate_primary = "ENT_77777777-7777-4777-8777-777777777777"
        primary_before = self._analysis_subject_v10()
        primary_before["memberships"].extend([
            {"entity_id": additional_member["entity_id"], "role": "consolidated_subsidiary",
             "valid_from": None, "valid_to": None, "evidence_ref": "https://example.org/member-c"},
            {"entity_id": alternate_primary, "role": "consolidated_subsidiary",
             "valid_from": None, "valid_to": None, "evidence_ref": "https://example.org/member-d"},
        ])
        primary_after = deepcopy(primary_before)
        primary_after["analysis_subject_revision"] = 2
        primary_after["primary_issuer_id"] = alternate_primary
        next(m for m in primary_after["memberships"] if m["entity_id"] == primary_before[
            "primary_issuer_id"])["role"] = "consolidated_subsidiary"
        next(m for m in primary_after["memberships"] if m["entity_id"] == alternate_primary)[
            "role"
        ] = "primary_issuer"
        primary_event = {
            **event, "event_type": "primary_issuer_changed",
            "affected_entity_ids": [primary_before["primary_issuer_id"], alternate_primary],
            "old_value": primary_before["primary_issuer_id"], "new_value": alternate_primary,
        }
        primary_states = {entity_id: "verified" for entity_id in (
            primary_before["primary_issuer_id"], additional_member["entity_id"], alternate_primary,
        )}
        cv.validate_analysis_subject_transition(
            primary_event, primary_before, primary_after, trusted_issuer_states=primary_states,
            trusted_reporting_perimeter_receipts=self._trusted_perimeter_receipts(
                primary_before, primary_after,
            ),
        )
        altered_third_party = deepcopy(primary_after)
        next(m for m in altered_third_party["memberships"] if m["entity_id"] == additional_member[
            "entity_id"])["evidence_ref"] = "https://example.org/changed-member-c"
        with self.assertRaisesRegex(ValueError, "primary-issuer event does not explain"):
            cv.validate_analysis_subject_transition(
                primary_event, primary_before, altered_third_party,
                trusted_issuer_states=primary_states,
                trusted_reporting_perimeter_receipts=self._trusted_perimeter_receipts(
                    primary_before, altered_third_party,
                ),
            )
        missing_primary_values = {**event, "event_type": "primary_issuer_changed"}
        missing_primary_values.pop("old_value")
        missing_primary_values.pop("new_value")
        with self.assertRaises(ValidationError):
            self.validate_type("AnalysisSubjectEventV10", missing_primary_values)

    def test_security_added_event_must_bind_the_added_security(self):
        entity = self._provisional_entity_v21()
        event = {
            "event_id": "EVT_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "entity_id": entity["entity_id"], "from_revision": 1, "to_revision": 2,
            "event_type": "security_added", "effective_at": "2026-01-01T00:00:00Z",
            "recorded_at": "2026-02-01T00:00:00Z", "source_namespace": "registry",
            "source_record_id": "R3", "evidence_ref": "https://example.org/security",
            "actor_id": None, "related_entity_ids": [], "affected_security_ids": [],
            "affected_listing_ids": [], "listing_id": None, "security_id": None,
            "field_path": None, "old_value": None, "new_value": None,
            "reason": "New class issued.",
        }
        with self.assertRaises(ValidationError):
            self.validate_type("IdentityEventV21", event)
        with self.assertRaises(ValidationError):
            cv.validate_identity_event(event)
        security_id = "SEC_44444444-4444-4444-8444-444444444444"
        valid_event = {**event, "security_id": security_id,
                       "affected_security_ids": [security_id]}
        cv.validate_identity_event(valid_event)

    @staticmethod
    def _analysis_subject_v10() -> dict:
        issuer_id = "ENT_11111111-1111-4111-8111-111111111111"
        return {
            "analysis_subject_schema_version": "1.0.0",
            "analysis_subject_id": "ASJ_99999999-9999-4999-8999-999999999999",
            "analysis_subject_revision": 1, "display_name": "Example reporting group",
            "primary_issuer_id": issuer_id, "anchor_listing_id": None,
            "scope_kind": "consolidated_reporting_group",
            "scope_as_of": "2026-06-30T00:00:00Z", "perimeter_coverage": "not_enumerated",
            "memberships": [{
                "entity_id": issuer_id, "role": "primary_issuer", "valid_from": None,
                "valid_to": None, "evidence_ref": "https://example.org/annual-report",
            }],
        }

    @staticmethod
    def _trusted_perimeter_receipts(*subjects: dict) -> dict[str, dict]:
        return {
            f"{subject['analysis_subject_id']}@{subject['analysis_subject_revision']}": {
                "receipt_id": f"RPR_{subject['analysis_subject_revision']}",
                "analysis_subject_id": subject["analysis_subject_id"],
                "analysis_subject_revision": subject["analysis_subject_revision"],
                "primary_issuer_id": subject["primary_issuer_id"],
                "status": "verified", "evidence_ref": "https://example.org/audited-report",
                "perimeter_sha256": cv.analysis_subject_perimeter_sha256(subject),
            }
            for subject in subjects
            if subject["scope_kind"] == "consolidated_reporting_group"
        }

    def _verified_pair_v21_for_listings(self):
        entity = self._provisional_entity_v21()
        entity["identity_state"] = "verified"
        entity["identity_revision"] = 2
        entity["incorporation_country"] = "US"
        entity.pop("scope_attestation_id")
        entity["verified_issuer_receipt_id"] = "IVR_V21"
        entity["securities"][0].update({"security_type": "ordinary", "share_class": "A"})
        entity["listings"][0].update({"exchange_raw": "NASDAQ", "exchange_mic": "XNAS"})
        second = deepcopy(entity["listings"][0])
        second.update({"listing_id": "LST_55555555-5555-4555-8555-555555555555",
                       "exchange_raw": "NYSE", "exchange_mic": "XNYS",
                       "ticker": "OTHER", "ticker_raw": "OTHER",
                       "source_binding_ref": "BND_SECOND"})
        entity["listings"].append(second)
        bindings = self._bindings_for_v21(entity)
        receipt = self._verified_receipt_v21(entity, bindings)
        return entity, receipt

    @staticmethod
    def _verified_receipt_v21(entity: dict, bindings: dict) -> dict:
        securities = entity["securities"]
        listings = entity["listings"]
        return {
            "receipt_id": entity["verified_issuer_receipt_id"], "kind": "verified_issuer",
            "entity_id": entity["entity_id"], "identity_revision": entity["identity_revision"],
            "status": "active", "same_legal_issuer": True,
            "canonical_name": entity["canonical_name"],
            "incorporation_country": entity["incorporation_country"],
            "security_ids": [s["security_id"] for s in securities],
            "listing_ids": [row["listing_id"] for row in listings],
            "security_attributes": {
                s["security_id"]: {
                    "security_type": s["security_type"], "share_class": s["share_class"],
                    "adr_ratio": s["adr_ratio"], "ordinary_security_ref": s["ordinary_security_ref"],
                } for s in securities
            },
            "listing_attributes": {
                row["listing_id"]: {
                    **{key: row[key] for key in (
                        "security_id", "market", "exchange_raw", "exchange_mic", "ticker_raw",
                        "ticker", "valid_from", "valid_to", "currency", "listing_status",
                        "source_binding_ref",
                    )},
                    "source_namespace": bindings[row["source_binding_ref"]]["source_namespace"],
                    "source_record_id": bindings[row["source_binding_ref"]]["source_record_id"],
                    "source_canonical_name": bindings[row["source_binding_ref"]]["source_canonical_name"],
                } for row in listings
            },
            "evidence_ref": "https://example.org/verified-issuer",
            "recorded_at": "2026-09-28T00:00:00Z",
        }

    def test_v21_two_venue_listings_can_point_to_one_security(self):
        entity = self._provisional_entity_v21()
        entity["identity_state"] = "verified"
        entity["identity_revision"] = 2
        entity["incorporation_country"] = "US"
        entity.pop("scope_attestation_id")
        entity["verified_issuer_receipt_id"] = "IVR_V21"
        security = entity["securities"][0]
        security.update({"security_type": "ordinary", "share_class": "A"})
        entity["listings"][0].update({"exchange_raw": "NASDAQ", "exchange_mic": "XNAS"})
        second = deepcopy(entity["listings"][0])
        second.update({"listing_id": "LST_55555555-5555-4555-8555-555555555555", "exchange_raw": "NYSE",
                       "exchange_mic": "XNYS", "ticker": "EXAMPLE",
                       "source_binding_ref": "BND_SECOND"})
        entity["listings"].append(second)
        bindings = self._bindings_for_v21(entity)
        receipt = {
            "receipt_id": "IVR_V21", "kind": "verified_issuer", "entity_id": entity["entity_id"],
            "identity_revision": 2, "status": "active", "same_legal_issuer": True,
            "canonical_name": entity["canonical_name"], "incorporation_country": "US",
            "security_ids": [security["security_id"]],
            "listing_ids": [row["listing_id"] for row in entity["listings"]],
            "security_attributes": {security["security_id"]: {
                "security_type": "ordinary", "share_class": "A", "adr_ratio": None,
                "ordinary_security_ref": None,
            }},
            "listing_attributes": {
                row["listing_id"]: {
                    **{key: row[key] for key in (
                        "security_id", "market", "exchange_raw", "exchange_mic",
                        "ticker_raw", "ticker", "valid_from", "valid_to",
                        "currency", "listing_status", "source_binding_ref",
                    )},
                    "source_namespace": bindings[row["source_binding_ref"]]["source_namespace"],
                    "source_record_id": bindings[row["source_binding_ref"]]["source_record_id"],
                    "source_canonical_name": bindings[row["source_binding_ref"]]["source_canonical_name"],
                }
                for row in entity["listings"]
            },
            "evidence_ref": "https://example.org/verified-issuer",
            "recorded_at": "2026-09-28T00:00:00Z",
        }
        self.validate_type("VerifiedEntityV21", entity)
        self.validate_entity(entity, trusted_identity_receipts={"IVR_V21": receipt},
                           trusted_source_bindings=bindings)
        self.assertEqual(entity["listings"][0]["security_id"], entity["listings"][1]["security_id"])
        for change in (
            {"listing_ids": ["LST_33333333-3333-4333-8333-333333333333"]},
            {"listing_ids": ["LST_33333333-3333-4333-8333-333333333333", "LST_33333333-3333-4333-8333-333333333333"]},
            {"security_ids": ["SEC_22222222-2222-4222-8222-222222222222", "SEC_EXTRA"]},
        ):
            bad = {**receipt, **change}
            with self.subTest(change=change), self.assertRaisesRegex(
                ValueError, "verified identity lacks exact issuer evidence"
            ):
                self.validate_entity(entity, trusted_identity_receipts={"IVR_V21": bad},
                                   trusted_source_bindings=bindings)
        bad_listing_receipt = deepcopy(receipt)
        bad_listing_receipt["listing_attributes"]["LST_33333333-3333-4333-8333-333333333333"]["ticker_raw"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "verified listing attributes differ"):
            self.validate_entity(entity, trusted_identity_receipts={"IVR_V21": bad_listing_receipt},
                               trusted_source_bindings=bindings)
        duplicate_listing = deepcopy(entity)
        duplicate_listing["listings"][1]["exchange_raw"] = duplicate_listing["listings"][0]["exchange_raw"]
        duplicate_listing["listings"][1]["exchange_mic"] = duplicate_listing["listings"][0]["exchange_mic"]
        duplicate_listing["listings"][1]["ticker"] = duplicate_listing["listings"][0]["ticker"]
        duplicate_listing["listings"][1]["ticker_raw"] = duplicate_listing["listings"][0]["ticker_raw"]
        with self.assertRaisesRegex(ValueError, "duplicate venue-qualified listing key"):
            self.validate_entity(duplicate_listing, trusted_identity_receipts={"IVR_V21": receipt},
                               trusted_source_bindings=self._bindings_for_v21(duplicate_listing))
        invalid_interval = deepcopy(entity)
        invalid_interval["listings"][0]["valid_from"] = "2026-01-01T00:00:00Z"
        invalid_interval["listings"][0]["valid_to"] = "2025-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "ordered half-open interval"):
            self.validate_entity(invalid_interval, trusted_identity_receipts={"IVR_V21": receipt},
                               trusted_source_bindings=self._bindings_for_v21(invalid_interval))
        overlapping = deepcopy(entity)
        first, second = overlapping["listings"]
        first.update({"exchange_raw": "NYSE", "exchange_mic": "XNYS",
                      "valid_from": "2025-01-01T00:00:00Z", "valid_to": "2026-01-01T00:00:00Z"})
        second.update({"valid_from": "2025-12-01T00:00:00Z", "valid_to": "2027-01-01T00:00:00Z"})
        with self.assertRaisesRegex(ValueError, "overlapping venue-qualified listing key"):
            self.validate_entity(overlapping, trusted_identity_receipts={"IVR_V21": receipt},
                               trusted_source_bindings=self._bindings_for_v21(overlapping))


if __name__ == "__main__":
    unittest.main()
