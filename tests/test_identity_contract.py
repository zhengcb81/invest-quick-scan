"""Automated tests for Identity and Universe Contract (Task C01).
Covers scenarios: ID-01, ID-02, ID-03, ID-04, UNI-04.
"""
import json
from pathlib import Path
import unittest
import jsonschema
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
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

        # Rule check: If verified_same_issuer is False, merging is prohibited; must remain 2 entities
        entities = []
        if bridge_unverified["verified_same_issuer"]:
            entities.append("MERGED_ENTITY")
        else:
            entities.extend(["ENT_PARENT_CORP", "ENT_LISTED_SUB"])

        self.assertEqual(len(entities), 2)
        self.assertIn("ENT_PARENT_CORP", entities)
        self.assertIn("ENT_LISTED_SUB", entities)

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

        # Attempting conversion must fail safely when adr_ratio is None
        def calculate_converted_price(price_usd, adr_ratio):
            if adr_ratio is None:
                return "unknown"
            return price_usd / adr_ratio

        self.assertEqual(calculate_converted_price(50.0, adr_sec["adr_ratio"]), "unknown")

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
        self.assertIsNone(entity["company_wiki_ref"])
        self.assertIsNone(entity["formal_stockwiki_profile"])

    def test_uni_04_universe_manifest_capacity_expansion_and_logical_removal(self):
        """UNI-04: Universe expansion to 2003 does not evict old companies; removals are logical and reversible."""
        manifest = {
            "manifest_version": "1.1.0",
            "updated_at": "2026-09-22T21:55:00Z",
            "soft_target_capacity": 2000,
            "total_entities": 2003,
            "active_entities": 2002,
            "manual_pinned_count": 100,
            "members": [
                {
                    "entity_id": "ENT_PINNED_VALUE",
                    "membership_status": "active",
                    "manual_pin": True,
                    "added_at": "2026-01-01T00:00:00Z",
                    "version": 1
                },
                {
                    "entity_id": "ENT_TEMP_REMOVED",
                    "membership_status": "logically_removed",
                    "manual_pin": False,
                    "added_at": "2026-01-01T00:00:00Z",
                    "removed_at": "2026-09-22T21:50:00Z",
                    "removal_reason": "主业停滞重组，暂时移出自动化监控池",
                    "restored_at": None,
                    "restoration_reason": None,
                    "version": 2
                }
            ]
        }
        self.validate_type("UniverseManifest", manifest)
        self.assertEqual(manifest["total_entities"], 2003)
        self.assertTrue(manifest["total_entities"] > manifest["soft_target_capacity"])

        # Test restoring the logically removed member
        member = manifest["members"][1]
        member["membership_status"] = "active"
        member["restored_at"] = "2026-09-22T21:58:00Z"
        member["restoration_reason"] = "重组完成，重新进入监控"
        member["version"] += 1
        self.validate_type("UniverseMember", member)
        self.assertEqual(member["version"], 3)
        self.assertEqual(member["membership_status"], "active")


if __name__ == "__main__":
    unittest.main()
