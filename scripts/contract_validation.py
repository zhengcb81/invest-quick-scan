"""Trusted semantic validators shared by quick-scan contract entry points.

JSON Schema validates shape.  These functions close relationships that JSON
Schema cannot express, such as an embedded security belonging to its parent
entity or a profile observation belonging to the profile entity.
"""
from __future__ import annotations

import json
import hashlib
import operator
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker
from jsonschema import ValidationError as JsonSchemaValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


SCORE_SCHEMA = _load("schemas/quick_scan/score.schema.json")
IDENTITY_SCHEMA = _load("schemas/quick_scan/identity.schema.json")
SOURCE_BINDING_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": IDENTITY_SCHEMA["definitions"],
    "$ref": "#/definitions/SourceBindingV2",
}
SOURCE_BINDING_V21_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": IDENTITY_SCHEMA["definitions"],
    "$ref": "#/definitions/SourceBindingV21",
}
WORK_SCHEMA = _load("schemas/quick_scan/work.schema.json")
OBSERVATION_V2_SCHEMA = _load("schemas/observation-v2.schema.json")
METRIC_SCHEMA = _load("schemas/quick_scan/metric.schema.json")
RULE_SCHEMA = _load("schemas/quick_scan/rule.schema.json")
QUERY_SCHEMA = _load("schemas/quick_scan/query.schema.json")
EXCHANGE_SCHEMA = _load("schemas/quick_scan/exchange.schema.json")
OBSERVATION_SCHEMA = _load("schemas/observation.schema.json")
ANSWER_SCHEMA = _load("schemas/answer-content.schema.json")

REGISTRY = Registry().with_resources([
    ("urn:iqs:observation:1", Resource.from_contents(OBSERVATION_SCHEMA)),
    ("urn:iqs:answer-content:1", Resource.from_contents(ANSWER_SCHEMA)),
    ("urn:iqs:quick-scan:exchange:1", Resource.from_contents(EXCHANGE_SCHEMA)),
])


def _validate_draft7(schema: dict, value: object) -> None:
    Draft7Validator(schema, format_checker=FormatChecker()).validate(value)


def _validate_202012(schema: dict, value: object) -> None:
    Draft202012Validator(
        schema, registry=REGISTRY, format_checker=FormatChecker()
    ).validate(value)


def validate_parsed_answer(
    value: dict, *, trusted_check_level_receipts: Mapping[str, dict] | None = None,
    expected_entity_id: str | None = None,
    expected_observation_id: str | None = None,
) -> None:
    """Validate score state and refuse self-awarded check levels."""
    _validate_draft7(SCORE_SCHEMA, value)
    level = value["check_level"]
    receipt = value.get("check_level_receipt_id")
    if level == "unverified_model_output":
        return
    trusted = trusted_check_level_receipts or {}
    record = trusted.get(receipt) if isinstance(trusted, Mapping) else None
    if not isinstance(record, dict):
        raise ValueError("check level is not backed by a trusted receipt record")
    required = {
        "receipt_id", "entity_id", "question_id", "observation_id",
        "authorized_check_level", "issuer", "status", "receipt_sha256",
    }
    if not required <= record.keys() or record["receipt_id"] != receipt:
        raise ValueError("check level receipt is incomplete or mis-keyed")
    if expected_entity_id is None or expected_observation_id is None:
        raise ValueError("verified check levels require expected entity and observation context")
    allowed_issuers = {
        "execution_verified": {"stockqa"},
        "screening_audited": {"iqs", "stockwiki"},
        "formal_research_accepted": {"stockwiki", "invest-core"},
    }
    if (record["status"] != "active"
            or record["entity_id"] != expected_entity_id
            or record["question_id"] != value["question_id"]
            or record["observation_id"] != expected_observation_id
            or record["authorized_check_level"] != level
            or record["issuer"] not in allowed_issuers[level]):
        raise ValueError("check level receipt does not authorize this answer")
    digest = record["receipt_sha256"]
    body = {key: item for key, item in record.items() if key != "receipt_sha256"}
    actual = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    if not isinstance(digest, str) or digest != actual:
        raise ValueError("check level receipt hash mismatch")


def _validate_entity_ownership(value: dict, *, verify_base: bool = True) -> None:
    entity_id = value["entity_id"]
    security_ids: set[str] = set()
    binding_refs: set[str] = set()
    for security in value["securities"]:
        if security["entity_id"] != entity_id:
            raise ValueError("embedded security belongs to another entity")
        if security["security_id"] in security_ids:
            raise ValueError("duplicate security_id in entity")
        security_ids.add(security["security_id"])
        binding_ref = security.get("source_binding_ref")
        if binding_ref is not None:
            if binding_ref in binding_refs:
                raise ValueError("duplicate source binding in entity")
            binding_refs.add(binding_ref)
    if not verify_base:
        return
    for security in value["securities"]:
        base_id = security.get("ordinary_security_ref")
        if base_id is None:
            continue
        if security.get("security_type") not in {"adr", "gdr", "cdr"}:
            raise ValueError("only depositary securities can reference an ordinary base")
        if base_id == security["security_id"]:
            raise ValueError("security cannot be its own ordinary base")
        base = next((item for item in value["securities"] if item["security_id"] == base_id), None)
        if base is None or base.get("security_type") != "ordinary":
            raise ValueError("ordinary base must belong to the same entity")


def _identity_receipt(
    value: dict, receipt_id: str, trusted_receipts: Mapping[str, dict] | None
) -> dict:
    if not isinstance(trusted_receipts, Mapping):
        raise ValueError("new identity requires authoritative receipt lookup")
    receipt = trusted_receipts.get(receipt_id)
    if not isinstance(receipt, dict):
        raise ValueError("identity receipt is missing")
    if (receipt.get("receipt_id") != receipt_id
            or receipt.get("entity_id") != value["entity_id"]
            or receipt.get("identity_revision") != value["identity_revision"]
            or receipt.get("status") != "active"):
        raise ValueError("identity receipt does not bind this active revision")
    recorded_at = receipt.get("recorded_at")
    try:
        parsed_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("identity receipt needs a UTC recorded_at") from exc
    if parsed_at.tzinfo is None or parsed_at.utcoffset() != timezone.utc.utcoffset(parsed_at):
        raise ValueError("identity receipt needs a UTC recorded_at")
    return receipt


def _source_binding(
    value: dict, security: dict, trusted_bindings: Mapping[str, dict] | None
) -> dict:
    """Resolve a current owner-held source row, never a row echoed by the input."""
    if not isinstance(trusted_bindings, Mapping):
        raise ValueError("new identity requires authoritative source binding lookup")
    binding_ref = security["source_binding_ref"]
    binding = trusted_bindings.get(binding_ref)
    if not isinstance(binding, dict):
        raise ValueError("source binding is missing")
    try:
        _validate_draft7(SOURCE_BINDING_SCHEMA, binding)
    except JsonSchemaValidationError as exc:
        raise ValueError("source binding shape is invalid") from exc
    expected = {
        "binding_ref": binding_ref,
        "entity_id": value["entity_id"],
        "security_id": security["security_id"],
        "market": security["market"],
        "exchange_raw": security["exchange_raw"],
        "ticker": security["ticker"],
        "status": "active",
    }
    if any(binding.get(field) != item for field, item in expected.items()):
        raise ValueError("source binding differs from current entity or listing")
    for field in ("source_namespace", "source_record_id", "source_canonical_name"):
        item = binding.get(field)
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise ValueError("source binding lacks a stable provenance field")
    return binding


def validate_legacy_entity_read(value: dict) -> None:
    """Read a v1 Entity without upgrading its identity assurance or eligibility."""
    if "identity_state" in value or "identity_revision" in value:
        raise ValueError("v2 identity cannot use the legacy read path")
    legacy_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/Entity",
    }
    _validate_draft7(legacy_schema, value)
    _validate_entity_ownership(value, verify_base=False)


def validate_identity_v20_read(
    value: dict, *, trusted_identity_receipts: Mapping[str, dict] | None = None,
    trusted_source_bindings: Mapping[str, dict] | None = None,
) -> None:
    """Validate a historical v2.0 identity without authorizing new writes.

    A schema-valid receipt ID supplied by an LLM or import row alone is never
    eligibility evidence. The caller must resolve it from its trusted store.
    This compatibility reader does not authorize new writes or scan eligibility.
    """
    if value.get("identity_schema_version") != "2.0.0":
        raise ValueError("historical identity reader accepts only schema 2.0.0")
    if "identity_state" not in value or "identity_revision" not in value:
        raise ValueError("historical v2 identity requires explicit state and revision")
    if isinstance(value.get("securities"), list):
        for security in value["securities"]:
            if (isinstance(security, dict)
                    and security.get("security_type") not in {"adr", "gdr", "cdr"}
                    and security.get("adr_ratio") is not None):
                raise ValueError("ADR ratio is only valid for depositary securities")
    _validate_draft7(IDENTITY_SCHEMA, value)
    if "securities" not in value:
        raise ValueError("expected an Entity")
    _validate_entity_ownership(value)
    securities = value["securities"]
    source_bindings = {
        security["security_id"]: _source_binding(value, security, trusted_source_bindings)
        for security in securities
    }
    if value["identity_state"] == "provisional":
        receipt = _identity_receipt(
            value, value["scope_attestation_id"], trusted_identity_receipts
        )
        binding = source_bindings[securities[0]["security_id"]]
        source_listing = {
            "market": securities[0]["market"],
            "exchange_raw": securities[0]["exchange_raw"],
            "ticker": securities[0]["ticker"],
            "canonical_name": value["canonical_name"],
        }
        known_attributes = {
            "incorporation_country": value["incorporation_country"],
            "exchange": securities[0]["exchange"],
            "currency": securities[0]["currency"],
            "security_type": securities[0]["security_type"],
            "listing_status": securities[0]["listing_status"],
        }
        if (receipt.get("kind") != "provisional_scope"
                or receipt.get("scope") != "listed_operating_company"
                or receipt.get("basis") not in {
                    "official_equity_category", "user_exact_security_attestation"
                }
                or receipt.get("negative_scope_flag") is not False
                or receipt.get("security_id") != securities[0]["security_id"]
                or receipt.get("source_binding_ref") != securities[0]["source_binding_ref"]
                or receipt.get("source_listing") != source_listing
                or binding["source_canonical_name"] != value["canonical_name"]
                or receipt.get("source_namespace") != binding["source_namespace"]
                or receipt.get("source_record_id") != binding["source_record_id"]
                or receipt.get("known_attributes") != known_attributes
                or not isinstance(receipt.get("evidence_ref"), str)
                or not receipt["evidence_ref"].strip()):
            raise ValueError("provisional scope has no positive listing qualification")
        if receipt["basis"] == "official_equity_category" and not receipt[
            "evidence_ref"
        ].startswith("https://"):
            raise ValueError("official qualification needs an HTTPS source")
        if (receipt["basis"] == "user_exact_security_attestation"
                and (not isinstance(receipt.get("actor_id"), str)
                     or not receipt["actor_id"].strip())):
            raise ValueError("manual qualification needs an actor")
        if securities[0]["adr_ratio"] is not None or securities[0]["ordinary_security_ref"] is not None:
            raise ValueError("provisional security cannot assert an ADR ratio or base")
        return
    if value["identity_state"] != "verified":
        raise ValueError("invalid identity state")
    receipt = _identity_receipt(
        value, value["verified_issuer_receipt_id"], trusted_identity_receipts
    )
    actual_ids = {security["security_id"] for security in securities}
    recorded_ids = receipt.get("security_ids")
    recorded_attributes = receipt.get("security_attributes")
    if (receipt.get("kind") != "verified_issuer"
            or receipt.get("same_legal_issuer") is not True
            or not isinstance(recorded_ids, list)
            or not all(isinstance(item, str) for item in recorded_ids)
            or len(recorded_ids) != len(actual_ids)
            or set(recorded_ids) != actual_ids
            or receipt.get("incorporation_country") != value["incorporation_country"]
            or receipt.get("canonical_name") != value["canonical_name"]
            or not isinstance(recorded_attributes, dict)
            or set(recorded_attributes) != actual_ids
            or not isinstance(receipt.get("evidence_ref"), str)
            or not receipt["evidence_ref"].startswith("https://")):
        raise ValueError("verified identity lacks exact issuer evidence")
    for security in securities:
        binding = source_bindings[security["security_id"]]
        expected_attributes = {
            field: security[field]
            for field in (
                "market", "exchange_raw", "exchange", "ticker", "currency", "security_type",
                "listing_status", "source_binding_ref",
            )
        }
        expected_attributes.update({
            "source_namespace": binding["source_namespace"],
            "source_record_id": binding["source_record_id"],
            "source_canonical_name": binding["source_canonical_name"],
        })
        if recorded_attributes[security["security_id"]] != expected_attributes:
            raise ValueError("verified security attributes differ from evidence")
        if security["adr_ratio"] is not None:
            ratios = receipt.get("verified_adr_ratios", {})
            if (not isinstance(ratios, dict)
                    or ratios.get(security["security_id"]) != security["adr_ratio"]):
                raise ValueError("ADR ratio is not backed by verified issuer evidence")


def _validate_entity_v21_ownership(
    value: dict, *, trusted_market_registry: Mapping[str, Iterable[str]]
) -> tuple[list[dict], list[dict]]:
    """Validate v2.1 issuer/security/listing ownership and local references."""
    entity_id = value["entity_id"]
    securities = value["securities"]
    listings = value["listings"]
    security_by_id: dict[str, dict] = {}
    for security in securities:
        if security["entity_id"] != entity_id:
            raise ValueError("security belongs to another entity")
        security_id = security["security_id"]
        if security_id in security_by_id:
            raise ValueError("duplicate security_id in entity")
        security_by_id[security_id] = security

    listing_ids: set[str] = set()
    binding_refs: set[str] = set()
    natural_keys: set[tuple[object, ...]] = set()
    listings_by_symbol: dict[
        tuple[str, str], list[tuple[str | None, datetime | None, datetime | None]]
    ] = {}
    for listing in listings:
        if listing["entity_id"] != entity_id:
            raise ValueError("listing belongs to another entity")
        listing_id = listing["listing_id"]
        if listing_id in listing_ids:
            raise ValueError("duplicate listing_id in entity")
        listing_ids.add(listing_id)
        security = security_by_id.get(listing["security_id"])
        if security is None:
            raise ValueError("listing security does not exist in this entity")
        if security["entity_id"] != listing["entity_id"]:
            raise ValueError("listing security belongs to another entity")
        market = listing["market"]
        if market not in trusted_market_registry:
            raise ValueError("listing market is absent from trusted market registry")
        registered_mics = trusted_market_registry[market]
        if (isinstance(registered_mics, (str, bytes))
                or not isinstance(registered_mics, (set, frozenset, list, tuple))
                or not registered_mics
                or any(not isinstance(registered_mic, str)
                       or not re.fullmatch(r"[A-Z0-9]{4}", registered_mic)
                       for registered_mic in registered_mics)):
            raise ValueError("trusted market registry entry is invalid")
        mic = listing["exchange_mic"]
        if mic is not None and mic not in registered_mics:
            raise ValueError("listing MIC does not belong to trusted market jurisdiction")
        binding_ref = listing["source_binding_ref"]
        if binding_ref in binding_refs:
            raise ValueError("duplicate source binding in entity")
        binding_refs.add(binding_ref)
        natural_key = (
            listing["market"], listing["exchange_mic"],
            listing["exchange_raw"].strip().casefold(),
            listing["ticker"].strip().casefold(), listing["valid_from"], listing["valid_to"],
        )
        if natural_key in natural_keys:
            raise ValueError("duplicate venue-qualified listing key in entity")
        natural_keys.add(natural_key)
        start = _listing_datetime(listing["valid_from"])
        end = _listing_datetime(listing["valid_to"])
        if start is not None and end is not None and start >= end:
            raise ValueError("listing validity must use an ordered half-open interval")
        symbol_key = (listing["market"], listing["ticker"].strip().casefold())
        mic = listing["exchange_mic"]
        for prior_mic, prior_start, prior_end in listings_by_symbol.get(
            symbol_key, []
        ):
            overlaps = ((end is None or prior_start is None or end > prior_start)
                        and (prior_end is None or start is None or prior_end > start))
            if overlaps:
                if mic is None or prior_mic is None:
                    raise ValueError("listing venue is ambiguous without MIC")
                if mic == prior_mic:
                    raise ValueError("overlapping venue-qualified listing key in entity")
        listings_by_symbol.setdefault(symbol_key, []).append((mic, start, end))

    for security in securities:
        kind = security.get("security_type")
        if kind not in {"adr", "gdr", "cdr"} and security.get("adr_ratio") is not None:
            raise ValueError("ADR ratio is only valid for depositary securities")
        base_id = security.get("ordinary_security_ref")
        if base_id is None:
            continue
        base = security_by_id.get(base_id)
        if (kind not in {"adr", "gdr", "cdr"} or base_id == security["security_id"]
                or base is None or base.get("security_type") != "ordinary"):
            raise ValueError("ordinary base must be an ordinary security of this entity")
    return securities, listings


def _listing_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def _source_binding_v21(
    value: dict, listing: dict, trusted_bindings: Mapping[str, dict] | None
) -> dict:
    """Resolve an owner-held listing binding and compare every identity field."""
    if not isinstance(trusted_bindings, Mapping):
        raise ValueError("new identity requires authoritative source binding lookup")
    binding_ref = listing["source_binding_ref"]
    binding = trusted_bindings.get(binding_ref)
    if not isinstance(binding, dict):
        raise ValueError("source binding is missing")
    try:
        _validate_draft7(SOURCE_BINDING_V21_SCHEMA, binding)
    except JsonSchemaValidationError as exc:
        raise ValueError("source binding shape is invalid") from exc
    expected_status = "retired" if listing["listing_status"] == "delisted" else "active"
    expected = {
        "binding_ref": binding_ref, "entity_id": value["entity_id"],
        "security_id": listing["security_id"], "listing_id": listing["listing_id"],
        "market": listing["market"], "exchange_raw": listing["exchange_raw"],
        "exchange_mic": listing["exchange_mic"], "ticker_raw": listing["ticker_raw"],
        "ticker": listing["ticker"], "valid_from": listing["valid_from"],
        "valid_to": listing["valid_to"], "status": expected_status,
    }
    if any(binding.get(field) != item for field, item in expected.items()):
        raise ValueError("source binding differs from current entity or listing")
    for field in ("source_namespace", "source_record_id", "source_canonical_name"):
        item = binding.get(field)
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise ValueError("source binding lacks a stable provenance field")
    return binding


def _receipt_has_exact_ids(receipt: dict, field: str, actual: set[str]) -> bool:
    recorded = receipt.get(field)
    return (
        isinstance(recorded, list)
        and all(isinstance(item, str) for item in recorded)
        and len(recorded) == len(set(recorded))
        and set(recorded) == actual
    )


def validate_entity(
    value: dict, *, trusted_identity_receipts: Mapping[str, dict] | None = None,
    trusted_source_bindings: Mapping[str, dict] | None = None,
    trusted_market_registry: Mapping[str, Iterable[str]] | None = None,
) -> None:
    """Validate the only supported new identity-write format, schema v2.1.0."""
    if value.get("identity_schema_version") != "2.1.0":
        raise ValueError("new writes require identity schema 2.1.0")
    _validate_draft7(IDENTITY_SCHEMA, value)
    if "securities" not in value or "listings" not in value:
        raise ValueError("expected a v2.1 issuer Entity")
    if not isinstance(trusted_market_registry, Mapping):
        raise ValueError("identity writes require a trusted market/MIC registry")
    securities, listings = _validate_entity_v21_ownership(
        value, trusted_market_registry=trusted_market_registry
    )
    bindings = {
        listing["listing_id"]: _source_binding_v21(value, listing, trusted_source_bindings)
        for listing in listings
    }

    if value["identity_state"] == "provisional":
        receipt = _identity_receipt(
            value, value["scope_attestation_id"], trusted_identity_receipts
        )
        listing = listings[0]
        security = securities[0]
        binding = bindings[listing["listing_id"]]
        source_listing = {
            **{field: listing[field] for field in (
                "listing_id", "security_id", "market", "exchange_raw", "exchange_mic",
                "ticker_raw", "ticker", "valid_from", "valid_to",
            )},
            "canonical_name": binding["source_canonical_name"],
        }
        known_attributes = {
            "incorporation_country": value["incorporation_country"],
            "security_type": security["security_type"],
            "share_class": security["share_class"],
            "currency": listing["currency"],
            "listing_status": listing["listing_status"],
        }
        if (receipt.get("kind") != "provisional_scope"
                or receipt.get("scope") != "listed_operating_company"
                or receipt.get("basis") not in {
                    "official_equity_category", "user_exact_security_attestation"
                }
                or receipt.get("negative_scope_flag") is not False
                or receipt.get("security_id") != security["security_id"]
                or receipt.get("listing_id") != listing["listing_id"]
                or receipt.get("source_binding_ref") != listing["source_binding_ref"]
                or receipt.get("source_listing") != source_listing
                or receipt.get("source_namespace") != binding["source_namespace"]
                or receipt.get("source_record_id") != binding["source_record_id"]
                or receipt.get("known_attributes") != known_attributes
                or not isinstance(receipt.get("evidence_ref"), str)
                or not receipt["evidence_ref"].strip()):
            raise ValueError("provisional scope has no positive listing qualification")
        if receipt["basis"] == "official_equity_category" and not receipt[
            "evidence_ref"
        ].startswith("https://"):
            raise ValueError("official qualification needs an HTTPS source")
        if (receipt["basis"] == "user_exact_security_attestation"
                and (not isinstance(receipt.get("actor_id"), str)
                     or not receipt["actor_id"].strip())):
            raise ValueError("manual qualification needs an actor")
        if security["adr_ratio"] is not None or security["ordinary_security_ref"] is not None:
            raise ValueError("provisional security cannot assert an ADR ratio or base")
        return

    if value["identity_state"] != "verified":
        raise ValueError("invalid identity state")
    receipt = _identity_receipt(
        value, value["verified_issuer_receipt_id"], trusted_identity_receipts
    )
    security_ids = {security["security_id"] for security in securities}
    listing_ids = {listing["listing_id"] for listing in listings}
    if (receipt.get("kind") != "verified_issuer"
            or receipt.get("same_legal_issuer") is not True
            or not _receipt_has_exact_ids(receipt, "security_ids", security_ids)
            or not _receipt_has_exact_ids(receipt, "listing_ids", listing_ids)
            or receipt.get("incorporation_country") != value["incorporation_country"]
            or receipt.get("canonical_name") != value["canonical_name"]
            or not isinstance(receipt.get("security_attributes"), dict)
            or set(receipt["security_attributes"]) != security_ids
            or not isinstance(receipt.get("listing_attributes"), dict)
            or set(receipt["listing_attributes"]) != listing_ids
            or not isinstance(receipt.get("evidence_ref"), str)
            or not receipt["evidence_ref"].startswith("https://")):
        raise ValueError("verified identity lacks exact issuer evidence")

    expected_adr_ratios: dict[str, float] = {}
    for security in securities:
        expected_security = {
            field: security[field]
            for field in ("security_type", "share_class", "adr_ratio", "ordinary_security_ref")
        }
        if receipt["security_attributes"][security["security_id"]] != expected_security:
            raise ValueError("verified security attributes differ from evidence")
        if security["adr_ratio"] is not None:
            expected_adr_ratios[security["security_id"]] = security["adr_ratio"]

    for listing in listings:
        binding = bindings[listing["listing_id"]]
        expected_listing = {
            field: listing[field]
            for field in (
                "security_id", "market", "exchange_raw", "exchange_mic", "ticker_raw",
                "ticker", "currency", "listing_status", "source_binding_ref", "valid_from",
                "valid_to",
            )
        }
        expected_listing.update({
            field: binding[field]
            for field in ("source_namespace", "source_record_id", "source_canonical_name")
        })
        if receipt["listing_attributes"][listing["listing_id"]] != expected_listing:
            raise ValueError("verified listing attributes differ from evidence")
    if receipt.get("verified_adr_ratios", {}) != expected_adr_ratios:
        raise ValueError("ADR ratio is not backed by verified issuer evidence")


def validate_entity_relationship(value: dict) -> None:
    """Validate a sourced corporate/group relation without equating issuers."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/EntityRelationshipV21",
    }
    _validate_draft7(schema, value)
    if value["from_entity_id"] == value["to_entity_id"]:
        raise ValueError("relationship cannot relate an entity to itself")
    _validate_effective_interval(value["valid_from"], value["valid_to"])


def validate_name_alias_claim_v21(value: dict) -> None:
    """Validate sourced, non-unique alias claims without granting merge authority."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/NameAliasClaimV21",
    }
    _validate_draft7(schema, value)
    _validate_effective_interval(value["valid_from"], value["valid_to"])
    if value["verification_status"] == "verified" and not value["evidence_ref"].strip():
        raise ValueError("verified alias claim needs evidence")


def validate_identifier_claim_v21(value: dict) -> None:
    """Validate a sourced identifier claim; linking still needs a trusted scheme registry."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/IssuerIdentifierClaimV21",
    }
    _validate_draft7(schema, value)
    _validate_effective_interval(value["valid_from"], value["valid_to"])
    if value["verification_status"] == "verified" and not value["evidence_ref"].strip():
        raise ValueError("verified identifier claim needs evidence")


def validate_identity_event(value: dict) -> None:
    """Validate an append-only identity event bound to one revision step."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/IdentityEventV21",
    }
    _validate_draft7(schema, value)
    if value["to_revision"] != value["from_revision"] + 1:
        raise ValueError("identity event must advance exactly one revision")
    related = value["related_entity_ids"]
    if value["entity_id"] in related:
        raise ValueError("identity event cannot merge or split into itself")
    if (value["event_type"] in {"renamed", "ticker_changed"}
            and value["old_value"] == value["new_value"]):
        raise ValueError("no-op identity event is not allowed")
    if (value["event_type"] == "identity_corrected"
            and value["field_path"] is not None
            and value["old_value"] == value["new_value"]):
        raise ValueError("no-op identity correction is not allowed")
    if value["event_type"] == "renamed" and value["field_path"] != "canonical_name":
        raise ValueError("rename event must target canonical_name")
    if value["event_type"] == "security_added":
        if value["security_id"] is None or value["affected_security_ids"] != [value["security_id"]]:
            raise ValueError("security-added event must bind its exact affected security")
    if (value["event_type"] == "ticker_changed"
            and (value["listing_id"] not in value["affected_listing_ids"]
                 or value["security_id"] not in value["affected_security_ids"]
                 or value["field_path"] != "ticker")):
        raise ValueError("ticker change must bind its exact listing and security")
    if (value["event_type"] == "ticker_changed"
            and (value["affected_listing_ids"] != [value["listing_id"]]
                 or value["affected_security_ids"] != [value["security_id"]])):
        raise ValueError("ticker change affected IDs must be exact")
    if (value["event_type"] in {"listing_added", "listing_retired"}
            and (value["listing_id"] not in value["affected_listing_ids"]
                 or value["security_id"] not in value["affected_security_ids"])):
        raise ValueError("listing event must bind its exact listing and security")
    if (value["event_type"] in {"listing_added", "listing_retired"}
            and (value["affected_listing_ids"] != [value["listing_id"]]
                 or value["affected_security_ids"] != [value["security_id"]])):
        raise ValueError("listing event affected IDs must be exact")


def validate_identity_transition(value: dict, before_entity: dict, after_entity: dict) -> None:
    """Check a single-issuer event against immutable before/after snapshots."""
    validate_identity_event(value)
    if (before_entity.get("entity_id") != value["entity_id"]
            or after_entity.get("entity_id") != value["entity_id"]
            or before_entity.get("identity_revision") != value["from_revision"]
            or after_entity.get("identity_revision") != value["to_revision"]):
        raise ValueError("identity transition snapshots do not match event revisions")
    _validate_transition_snapshot_references(before_entity, value["entity_id"])
    _validate_transition_snapshot_references(after_entity, value["entity_id"])
    before = deepcopy(before_entity)
    after = deepcopy(after_entity)
    before.pop("identity_revision", None)
    after.pop("identity_revision", None)
    event_type = value["event_type"]
    if event_type == "renamed":
        if (before_entity.get("canonical_name") != value["old_value"]
                or after_entity.get("canonical_name") != value["new_value"]):
            raise ValueError("rename event does not match before/after names")
        expected_security_ids = {row["security_id"] for row in before_entity["securities"]}
        expected_listing_ids = {row["listing_id"] for row in before_entity["listings"]}
        if (expected_security_ids != {row["security_id"] for row in after_entity["securities"]}
                or expected_listing_ids != {row["listing_id"] for row in after_entity["listings"]}
                or set(value["affected_security_ids"]) != expected_security_ids
                or set(value["affected_listing_ids"]) != expected_listing_ids):
            raise ValueError("rename affected IDs must exactly cover the issuer's securities and listings")
        before["canonical_name"] = after["canonical_name"]
    elif event_type == "ticker_changed":
        listing_id = value["listing_id"]
        old_listing = next((x for x in before["listings"] if x["listing_id"] == listing_id), None)
        new_listing = next((x for x in after["listings"] if x["listing_id"] == listing_id), None)
        if (old_listing is None or new_listing is None
                or old_listing["ticker"] != value["old_value"]
                or new_listing["ticker"] != value["new_value"]
                or old_listing["security_id"] != value["security_id"]
                or new_listing["security_id"] != value["security_id"]):
            raise ValueError("ticker event does not match before/after listing")
        old_listing["ticker"] = new_listing["ticker"]
    elif event_type == "security_added":
        security_id = value["security_id"]
        before_ids = {x["security_id"] for x in before["securities"]}
        after_ids = {x["security_id"] for x in after["securities"]}
        if security_id in before_ids or security_id not in after_ids:
            raise ValueError("security-added event does not match before/after securities")
        added = after_ids - before_ids
        if added != {security_id}:
            raise ValueError("security-added event must bind the exact added security set")
        after["securities"] = before["securities"]
    elif event_type in {"listing_added", "listing_retired"}:
        listing_id = value["listing_id"]
        before_by_id = {x["listing_id"]: x for x in before["listings"]}
        after_by_id = {x["listing_id"]: x for x in after["listings"]}
        if event_type == "listing_added":
            if listing_id in before_by_id or listing_id not in after_by_id:
                raise ValueError("listing-added event does not match before/after listings")
            if after_by_id[listing_id]["security_id"] != value["security_id"]:
                raise ValueError("listing-added event security does not match added listing")
            added = set(after_by_id) - set(before_by_id)
            if added != {listing_id}:
                raise ValueError("listing-added event must bind the exact added listing set")
            after["listings"] = before["listings"]
        else:
            if listing_id not in before_by_id or listing_id not in after_by_id:
                raise ValueError("listing-retired event must preserve its listing history")
            if (before_by_id[listing_id]["security_id"] != value["security_id"]
                    or after_by_id[listing_id]["security_id"] != value["security_id"]):
                raise ValueError("listing-retired event security does not match historical listing")
            if (before_by_id[listing_id]["listing_status"] == "delisted"
                    or after_by_id[listing_id]["listing_status"] != "delisted"):
                raise ValueError("listing-retired event must change status to delisted")
            before_by_id[listing_id]["listing_status"] = after_by_id[listing_id]["listing_status"]
    else:
        raise ValueError("event type requires an owner transaction beyond a single-issuer snapshot")
    if before != after:
        raise ValueError("identity event does not explain the exact snapshot change")


def _validate_transition_snapshot_references(snapshot: Mapping, entity_id: str) -> None:
    """Require every event snapshot to have internally resolvable local security links."""
    securities: dict[str, Mapping] = {}
    for security in snapshot["securities"]:
        if security["entity_id"] != entity_id or security["security_id"] in securities:
            raise ValueError("transition snapshot contains a duplicate or foreign security")
        securities[security["security_id"]] = security
    listing_ids: set[str] = set()
    for listing in snapshot["listings"]:
        if (listing["entity_id"] != entity_id
                or listing["listing_id"] in listing_ids
                or listing["security_id"] not in securities):
            raise ValueError("transition snapshot listing references a missing or foreign security")
        listing_ids.add(listing["listing_id"])


def analysis_subject_perimeter_snapshot(value: Mapping) -> dict:
    """Return the order-independent immutable fields covered by a perimeter receipt."""
    memberships = sorted(
        (dict(member) for member in value["memberships"]),
        key=lambda member: member["entity_id"],
    )
    return {
        "analysis_subject_id": value["analysis_subject_id"],
        "analysis_subject_revision": value["analysis_subject_revision"],
        "primary_issuer_id": value["primary_issuer_id"],
        "scope_kind": value["scope_kind"],
        "scope_as_of": value["scope_as_of"],
        "perimeter_coverage": value["perimeter_coverage"],
        "memberships": memberships,
    }


def analysis_subject_perimeter_sha256(value: Mapping) -> str:
    """Hash the exact reporting perimeter; display-name edits do not change it."""
    payload = json.dumps(
        analysis_subject_perimeter_snapshot(value), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _analysis_subject_receipt_key(value: Mapping) -> str:
    return f"{value['analysis_subject_id']}@{value['analysis_subject_revision']}"


def _require_trusted_reporting_perimeter(
    value: Mapping, receipts: Mapping[str, dict] | None,
) -> None:
    if not isinstance(receipts, Mapping):
        raise ValueError("consolidated subject lacks an exact trusted reporting-perimeter receipt")
    receipt = receipts.get(_analysis_subject_receipt_key(value))
    if (not isinstance(receipt, Mapping)
            or receipt.get("status") != "verified"
            or not isinstance(receipt.get("receipt_id"), str)
            or not receipt["receipt_id"].strip()
            or receipt.get("analysis_subject_id") != value["analysis_subject_id"]
            or receipt.get("analysis_subject_revision") != value["analysis_subject_revision"]
            or receipt.get("primary_issuer_id") != value["primary_issuer_id"]
            or not isinstance(receipt.get("evidence_ref"), str)
            or not receipt["evidence_ref"].startswith("https://")
            or receipt.get("perimeter_sha256") != analysis_subject_perimeter_sha256(value)):
        raise ValueError("consolidated subject lacks an exact trusted reporting-perimeter receipt")


def validate_analysis_subject(
    value: dict, *, trusted_issuer_states: Mapping[str, str] | None = None,
    trusted_listing_to_issuer: Mapping[str, str] | None = None,
    trusted_reporting_perimeter_receipts: Mapping[str, dict] | None = None,
) -> None:
    """Validate a subject against owner issuer/listing registries and a trusted perimeter receipt."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/AnalysisSubjectV10",
    }
    _validate_draft7(schema, value)
    if not isinstance(trusted_issuer_states, Mapping):
        raise ValueError("analysis subject requires trusted issuer registry")
    memberships = value["memberships"]
    member_ids = [member["entity_id"] for member in memberships]
    if len(member_ids) != len(set(member_ids)):
        raise ValueError("duplicate issuer membership in analysis subject")
    primary = [m for m in memberships if m["role"] == "primary_issuer"]
    if len(primary) != 1 or primary[0]["entity_id"] != value["primary_issuer_id"]:
        raise ValueError("analysis subject must have exactly its declared primary issuer")
    primary_state = trusted_issuer_states.get(value["primary_issuer_id"])
    if primary_state not in {"provisional", "verified"}:
        raise ValueError("primary issuer is not in the trusted issuer registry")
    as_of = _listing_datetime(value["scope_as_of"])
    for member in memberships:
        member_state = trusted_issuer_states.get(member["entity_id"])
        if member_state not in {"provisional", "verified"}:
            raise ValueError("analysis subject member is not in the trusted issuer registry")
        _validate_effective_interval(member["valid_from"], member["valid_to"])
        start = _listing_datetime(member["valid_from"])
        end = _listing_datetime(member["valid_to"])
        if (start is not None and as_of < start) or (end is not None and as_of >= end):
            raise ValueError("analysis subject membership is not effective at scope_as_of")
        if member["role"] != "primary_issuer" and member_state != "verified":
            raise ValueError("non-primary perimeter members must be verified issuers")
    if primary_state == "provisional":
        if value["scope_kind"] != "provisional_listing_scope":
            raise ValueError("provisional issuer cannot define a reporting group")
        if member_ids != [value["primary_issuer_id"]]:
            raise ValueError("provisional listing scope cannot include another issuer")
        if not isinstance(trusted_listing_to_issuer, Mapping):
            raise ValueError("provisional subject requires trusted issuer registry listing mapping")
        if trusted_listing_to_issuer.get(value["anchor_listing_id"]) != value["primary_issuer_id"]:
            raise ValueError("anchor listing does not belong to the provisional issuer")
    elif value["scope_kind"] == "provisional_listing_scope":
        raise ValueError("verified issuer cannot use provisional listing scope")
    elif value["scope_kind"] == "standalone_issuer" and member_ids != [value["primary_issuer_id"]]:
        raise ValueError("standalone scope cannot include another issuer")
    elif value["scope_kind"] == "consolidated_reporting_group":
        _require_trusted_reporting_perimeter(value, trusted_reporting_perimeter_receipts)


def validate_analysis_subject_event(value: dict) -> None:
    """Validate an append-only reporting-scope event with a single revision step."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": IDENTITY_SCHEMA["definitions"],
        "$ref": "#/definitions/AnalysisSubjectEventV10",
    }
    _validate_draft7(schema, value)
    if value["to_revision"] != value["from_revision"] + 1:
        raise ValueError("analysis subject event must advance exactly one revision")
    if value["old_value"] == value["new_value"]:
        raise ValueError("no-op analysis subject event is not allowed")


def validate_analysis_subject_transition(
    value: dict, before_subject: dict, after_subject: dict, *,
    trusted_issuer_states: Mapping[str, str],
    trusted_listing_to_issuer: Mapping[str, str] | None = None,
    trusted_reporting_perimeter_receipts: Mapping[str, dict] | None = None,
) -> None:
    """Bind a subject event to exact immutable before/after scope snapshots."""
    validate_analysis_subject_event(value)
    if (before_subject.get("analysis_subject_id") != value["analysis_subject_id"]
            or after_subject.get("analysis_subject_id") != value["analysis_subject_id"]
            or before_subject.get("analysis_subject_revision") != value["from_revision"]
            or after_subject.get("analysis_subject_revision") != value["to_revision"]):
        raise ValueError("analysis subject transition snapshots do not match event revisions")

    validate_analysis_subject(
        before_subject, trusted_issuer_states=trusted_issuer_states,
        trusted_listing_to_issuer=trusted_listing_to_issuer,
        trusted_reporting_perimeter_receipts=trusted_reporting_perimeter_receipts,
    )
    validate_analysis_subject(
        after_subject, trusted_issuer_states=trusted_issuer_states,
        trusted_listing_to_issuer=trusted_listing_to_issuer,
        trusted_reporting_perimeter_receipts=trusted_reporting_perimeter_receipts,
    )
    before = {key: value for key, value in before_subject.items()
              if key != "analysis_subject_revision"}
    after = {key: value for key, value in after_subject.items()
             if key != "analysis_subject_revision"}
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    event_type = value["event_type"]

    if event_type == "display_name_changed":
        if (before_subject["display_name"] != value["old_value"]
                or after_subject["display_name"] != value["new_value"]
                or changed != {"display_name"}):
            raise ValueError("display-name event does not explain the exact subject change")
        expected_affected = {before_subject["primary_issuer_id"]}
    elif event_type == "perimeter_changed":
        allowed = {"scope_as_of", "perimeter_coverage", "memberships"}
        if (not changed or not changed <= allowed
                or before_subject["primary_issuer_id"] != after_subject["primary_issuer_id"]
                or before_subject["scope_kind"] != after_subject["scope_kind"]
                or value["old_value"] != analysis_subject_perimeter_sha256(before_subject)
                or value["new_value"] != analysis_subject_perimeter_sha256(after_subject)):
            raise ValueError("perimeter event does not explain the exact subject change")
        expected_affected = _changed_membership_ids(before_subject, after_subject)
        if not expected_affected:
            expected_affected = {before_subject["primary_issuer_id"]}
    elif event_type == "primary_issuer_changed":
        old_primary = before_subject["primary_issuer_id"]
        new_primary = after_subject["primary_issuer_id"]
        changed_members = _changed_membership_ids(before_subject, after_subject)
        before_members = {m["entity_id"]: m for m in before_subject["memberships"]}
        after_members = {m["entity_id"]: m for m in after_subject["memberships"]}
        role_swap_only = changed_members == {old_primary, new_primary}
        for entity_id in (old_primary, new_primary):
            before_member = before_members.get(entity_id)
            after_member = after_members.get(entity_id)
            if before_member is None or after_member is None:
                role_swap_only = False
                break
            before_non_role = {k: v for k, v in before_member.items() if k != "role"}
            after_non_role = {k: v for k, v in after_member.items() if k != "role"}
            if before_non_role != after_non_role:
                role_swap_only = False
        if (old_primary == new_primary
                or value["old_value"] != old_primary
                or value["new_value"] != new_primary
                or not changed <= {"primary_issuer_id", "memberships"}
                or changed != {"primary_issuer_id", "memberships"}
                or not role_swap_only
                or before_members[old_primary]["role"] != "primary_issuer"
                or after_members[new_primary]["role"] != "primary_issuer"
                or after_members[old_primary]["role"] == "primary_issuer"
                or before_members[new_primary]["role"] == "primary_issuer"):
            raise ValueError("primary-issuer event does not explain the exact subject change")
        expected_affected = {old_primary, new_primary}
    elif event_type == "scope_kind_changed":
        if (before_subject["scope_kind"] == after_subject["scope_kind"]
                or value["old_value"] != before_subject["scope_kind"]
                or value["new_value"] != after_subject["scope_kind"]
                or not changed <= {"scope_kind", "memberships", "perimeter_coverage", "anchor_listing_id"}
                or "scope_kind" not in changed):
            raise ValueError("scope-kind event does not explain the exact subject change")
        expected_affected = _changed_membership_ids(before_subject, after_subject)
        if not expected_affected:
            expected_affected = {before_subject["primary_issuer_id"]}
    else:
        raise ValueError("unsupported analysis subject event type")

    if set(value["affected_entity_ids"]) != expected_affected:
        raise ValueError("analysis subject event affected entities do not match the exact scope change")


def _changed_membership_ids(before_subject: Mapping, after_subject: Mapping) -> set[str]:
    before = {member["entity_id"]: member for member in before_subject["memberships"]}
    after = {member["entity_id"]: member for member in after_subject["memberships"]}
    return {entity_id for entity_id in before.keys() | after.keys()
            if before.get(entity_id) != after.get(entity_id)}


def _validate_effective_interval(start_value: str | None, end_value: str | None) -> None:
    start = _listing_datetime(start_value)
    end = _listing_datetime(end_value)
    if start is not None and end is not None and start >= end:
        raise ValueError("validity must use an ordered half-open interval")


def validate_universe_manifest(value: dict) -> None:
    _validate_draft7(IDENTITY_SCHEMA, value)
    members = value.get("members")
    if not isinstance(members, list):
        raise ValueError("expected a UniverseManifest")
    entity_ids = [member["entity_id"] for member in members]
    if len(entity_ids) != len(set(entity_ids)):
        raise ValueError("duplicate universe member")
    if value["total_entities"] != len(members):
        raise ValueError("total_entities does not match members")
    active = sum(member["membership_status"] == "active" for member in members)
    pinned = sum(member["manual_pin"] is True for member in members)
    if value["active_entities"] != active:
        raise ValueError("active_entities does not match members")
    if value.get("manual_pinned_count", 0) != pinned:
        raise ValueError("manual_pinned_count does not match members")


def validate_work_item(
    value: dict, *, scope_owner_entity_id: str | None = None
) -> None:
    """Historical v1 read path; never authorizes a new identity-bound dispatch."""
    if value.get("schema_version") == "2.0.0":
        raise ValueError("v2 work requires the identity-bound validator; legacy read rejected")
    _validate_work_item_common(value, scope_owner_entity_id=scope_owner_entity_id)


def _validate_work_item_common(value: dict, *, scope_owner_entity_id: str | None) -> None:
    _validate_draft7(WORK_SCHEMA, value)
    attempts = value.get("attempts", [])
    attempt_ids = [item["attempt_id"] for item in attempts]
    if len(set(attempt_ids)) != len(attempt_ids):
        raise ValueError("work item contains duplicate attempt_id values")
    if value.get("status") == "uncertain":
        uncertain_id = value.get("uncertain_attempt_id")
        if not isinstance(uncertain_id, str) or attempt_ids.count(uncertain_id) != 1:
            raise ValueError("uncertain_attempt_id must bind exactly one persisted attempt")
    scope = value["scope"]
    if scope == "entity":
        if value["scope_id"] != value["entity_id"]:
            raise ValueError("entity scope_id must equal entity_id")
    else:
        if scope_owner_entity_id is None:
            raise ValueError("security/segment scope requires authoritative owner lookup")
        if scope_owner_entity_id != value["entity_id"]:
            raise ValueError("scope belongs to another entity")


def _owner_context_v2(context: Mapping[str, object] | None) -> Mapping[str, object]:
    """Check the shape of an owner-supplied identity projection, not its provenance."""
    if not isinstance(context, Mapping):
        raise ValueError("v2 work requires trusted identity owner context")
    required = {"entity_id", "identity_state", "identity_revision", "source_binding_version",
                "scan_eligibility", "active_source_binding_refs", "security_binding_refs",
                "segment_ids"}
    if not required <= context.keys():
        raise ValueError("trusted identity owner context is incomplete")
    state = context["identity_state"]
    eligible = context["scan_eligibility"]
    if (state, eligible) not in {("provisional", "eligible_provisional"),
                                 ("verified", "eligible_verified")}:
        raise ValueError("identity owner does not authorize dispatch")
    for field in ("identity_revision", "source_binding_version"):
        value = context[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"invalid owner {field}")
    refs = context["active_source_binding_refs"]
    bindings = context["security_binding_refs"]
    segments = context["segment_ids"]
    if (not isinstance(context["entity_id"], str)
            or not re.fullmatch(r"ENT_[A-Za-z0-9_]+", context["entity_id"])
            or not isinstance(refs, list) or not refs
            or not all(isinstance(ref, str) and re.fullmatch(r"BND_[A-Za-z0-9_]+", ref)
                       for ref in refs)
            or refs != sorted(set(refs))
            or not isinstance(bindings, Mapping) or not bindings
            or not all(isinstance(security_id, str)
                       and re.fullmatch(r"SEC_[A-Za-z0-9_.]+", security_id)
                       and isinstance(ref, str) and ref in refs
                       for security_id, ref in bindings.items())
            or set(bindings.values()) != set(refs)
            or len(bindings) != len(set(bindings.values()))
            or not isinstance(segments, list)
            or not all(isinstance(segment_id, str)
                       and re.fullmatch(r"SEG_[A-Za-z0-9_]+", segment_id)
                       for segment_id in segments)):
        raise ValueError("trusted identity binding projection is invalid")
    if state == "provisional" and len(refs) != 1:
        raise ValueError("provisional identity must bind one source security")
    return context


def validate_work_item_v2(
    value: dict, *, trusted_identity_context: Mapping[str, object] | None
) -> None:
    """New-write gate: exact owner identity revision, binding set, scope and eligibility."""
    if value.get("schema_version") != "2.0.0":
        raise ValueError("v2 work requires schema_version 2.0.0")
    context = _owner_context_v2(trusted_identity_context)
    _validate_work_item_common(value, scope_owner_entity_id=context["entity_id"])
    for field in ("entity_id", "identity_state", "identity_revision", "source_binding_version"):
        if value[field] != context[field]:
            raise ValueError(f"work {field} differs from trusted identity owner")
    scope = value["scope"]
    if scope == "security":
        ref = context["security_binding_refs"].get(value["scope_id"])
        if ref is None:
            raise ValueError("security scope is absent from trusted identity owner")
        expected_refs = [ref]
    else:
        if scope == "segment" and value["scope_id"] not in context["segment_ids"]:
            raise ValueError("segment scope is absent from trusted identity owner")
        expected_refs = context["active_source_binding_refs"]
    if value["source_binding_refs"] != expected_refs:
        raise ValueError("work source bindings differ from trusted identity owner")


def validate_observation_identity_v2(
    observation: dict, work_item: dict, *,
    trusted_dispatch_identity_context: Mapping[str, object] | None,
    expected_observation_id: str | None,
) -> None:
    """Validate a persisted v2 envelope against its immutable dispatch snapshot.

    This checks self-consistent work/attempt lineage and identity, not independent
    search receipt or S05 answer-content/package proof. It does not authorize a
    current score. A late observation may remain valid history.
    """
    if observation.get("schema_version") != "2.0.0":
        raise ValueError("v2 identity observation requires schema_version 2.0.0")
    if expected_observation_id is None:
        raise ValueError("v2 identity observation requires an independently stored ID")
    _validate_202012(OBSERVATION_V2_SCHEMA, observation)
    validate_work_item_v2(work_item, trusted_identity_context=trusted_dispatch_identity_context)
    if observation["observation_id"] != expected_observation_id:
        raise ValueError("v2 observation differs from independently stored ID")
    body = {key: value for key, value in observation.items() if key != "observation_id"}
    actual_hash = hashlib.sha256(json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    if observation["observation_id"] != "obs_" + actual_hash:
        raise ValueError("v2 observation immutable hash mismatch")
    if work_item["status"] not in {"result_ready", "delivered"}:
        raise ValueError("v2 observation requires persisted result-ready or delivered work")
    payload_hash = hashlib.sha256(json.dumps(
        observation, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    if (work_item.get("observation_ref") != observation["observation_id"]
            or work_item.get("observation_hash") != payload_hash
            or not work_item.get("request_cache_key")):
        raise ValueError("v2 observation does not match persisted work result")
    pairs = {
        "work_item_id": "work_item_id", "work_generation": "generation",
        "entity_id": "entity_id", "question_id": "question_id", "scope": "scope",
        "scope_id": "scope_id", "question_fingerprint": "question_fingerprint",
        "routing_fingerprint": "routing_fingerprint",
        "identity_state_at_answer": "identity_state",
        "identity_revision": "identity_revision", "source_binding_version": "source_binding_version",
        "source_binding_refs": "source_binding_refs",
    }
    for observation_field, work_field in pairs.items():
        if observation[observation_field] != work_item[work_field]:
            raise ValueError(f"v2 observation {observation_field} differs from dispatched work")
    if (observation["run_id"] not in work_item["run_ids"]
            or observation["scan_id"] not in work_item["scan_ids"]):
        raise ValueError("v2 observation run or scan was not attached to work")
    execution = observation["execution"]
    attempts = [item for item in work_item["attempts"]
                if item["attempt_id"] == execution["attempt_id"]]
    if len(attempts) != 1:
        raise ValueError("v2 observation execution attempt was not persisted on work")
    attempt = attempts[0]
    attempt_pairs = {
        "provider": "provider", "model_requested": "model_requested",
        "model_resolved": "model_resolved", "request_id": "request_id",
        "started_at": "started_at", "answered_at": "answered_at",
        "prompt_sha256": "prompt_hash",
    }
    if any(attempt.get(work_field) != execution[execution_field]
           for execution_field, work_field in attempt_pairs.items()):
        raise ValueError("v2 observation execution differs from persisted attempt")
    if observation["observed_at"] != execution["answered_at"]:
        raise ValueError("v2 observation time differs from persisted attempt")
    if observation["answer"]["status"] != work_item.get("response_status"):
        raise ValueError("v2 observation disposition differs from persisted work")
    if (observation["answer"]["status"] in {"scored", "answered"}
            and (execution["search_status"] != "executed"
                 or not execution["search_receipt_id"])):
        raise ValueError("v2 successful answer requires an executed search receipt reference")
    scope = observation["scope"]
    if scope == "entity" and (observation["security_id"] is not None
                              or observation["segment_id"] is not None):
        raise ValueError("v2 entity observation cannot claim a security or segment")
    if scope == "security" and (observation["security_id"] != observation["scope_id"]
                                or observation["segment_id"] is not None):
        raise ValueError("v2 security observation scope differs from security ID")
    if scope == "segment" and (observation["segment_id"] != observation["scope_id"]
                               or observation["security_id"] is not None):
        raise ValueError("v2 segment observation scope differs from segment ID")
    if observation["answer"]["question_id"] != observation["question_id"]:
        raise ValueError("v2 observation answer question differs from work")


def observation_identity_is_current(
    observation: dict, trusted_current_identity_context: Mapping[str, object] | None, *,
    trusted_dispatch_identity_context: Mapping[str, object] | None = None,
    persisted_work_item: dict | None = None,
    persisted_attempt: Mapping[str, object] | None = None,
    trusted_search_receipt: Mapping[str, object] | None = None,
    trusted_ingest_receipt: Mapping[str, object] | None = None,
    trusted_content_receipt: Mapping[str, object] | None = None,
    expected_observation_id: str | None = None,
) -> bool:
    """Fail-closed current-score gate over independent persisted lineage proofs.

    All trusted_* and persisted_* inputs must be fetched from their authoritative
    stores. An observation's own claimed IDs are never proof of those records.
    """
    if not isinstance(observation, dict) or observation.get("schema_version") != "2.0.0":
        return False
    if (not isinstance(persisted_work_item, dict) or persisted_attempt is None
            or trusted_search_receipt is None or trusted_ingest_receipt is None
            or trusted_content_receipt is None
            or trusted_dispatch_identity_context is None or expected_observation_id is None):
        return False
    try:
        validate_observation_identity_v2(
            observation, persisted_work_item,
            trusted_dispatch_identity_context=trusted_dispatch_identity_context,
            expected_observation_id=expected_observation_id,
        )
        context = _owner_context_v2(trusted_current_identity_context)
    except (ValueError, TypeError, KeyError, JsonSchemaValidationError):
        return False
    answer = observation["answer"]
    score = answer.get("score")
    if (persisted_work_item["status"] != "delivered"
            or answer["status"] != "scored" or answer["response_kind"] != "score"
            or isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10):
        return False
    execution = observation["execution"]
    if (not isinstance(persisted_attempt, Mapping)
            or persisted_attempt.get("status") != "completed"
            or persisted_attempt.get("work_item_id") != persisted_work_item["work_item_id"]
            or any(persisted_attempt.get(field) != execution[source] for field, source in {
                "attempt_id": "attempt_id", "provider": "provider",
                "model_requested": "model_requested", "model_resolved": "model_resolved",
                "request_id": "request_id", "started_at": "started_at",
                "answered_at": "answered_at", "prompt_hash": "prompt_sha256",
            }.items())):
        return False
    if (not isinstance(trusted_search_receipt, Mapping)
            or trusted_search_receipt.get("receipt_id") != execution["search_receipt_id"]
            or trusted_search_receipt.get("work_item_id") != persisted_work_item["work_item_id"]
            or trusted_search_receipt.get("attempt_id") != execution["attempt_id"]
            or trusted_search_receipt.get("request_id") != execution["request_id"]
            or trusted_search_receipt.get("search_status") != "executed"):
        return False
    if (not isinstance(trusted_ingest_receipt, Mapping)
            or trusted_ingest_receipt.get("consumer") != "stockwiki"
            or trusted_ingest_receipt.get("ack_status") != "accepted"
            or trusted_ingest_receipt.get("work_item_id") != persisted_work_item["work_item_id"]
            or trusted_ingest_receipt.get("observation_id") != observation["observation_id"]
            or trusted_ingest_receipt.get("observation_hash") != persisted_work_item["observation_hash"]):
        return False
    if (not isinstance(trusted_content_receipt, Mapping)
            or trusted_content_receipt.get("issuer") != "stockwiki"
            or trusted_content_receipt.get("status") != "validated"
            or trusted_content_receipt.get("validation_scope") != "frozen_package_and_answer_semantics"
            or trusted_content_receipt.get("schema_version") != "2.0.0"
            or trusted_content_receipt.get("observation_id") != observation["observation_id"]
            or trusted_content_receipt.get("observation_hash") != persisted_work_item["observation_hash"]
            or trusted_content_receipt.get("module_package_id") != observation["module_package_id"]
            or trusted_content_receipt.get("question_id") != observation["question_id"]):
        return False
    scope = observation.get("scope")
    if scope == "entity":
        if observation.get("scope_id") != context["entity_id"]:
            return False
        expected_refs = context["active_source_binding_refs"]
    elif scope == "security":
        security_id = observation.get("security_id")
        if security_id != observation.get("scope_id"):
            return False
        ref = context["security_binding_refs"].get(security_id)
        if ref is None:
            return False
        expected_refs = [ref]
    elif scope == "segment":
        if observation.get("segment_id") != observation.get("scope_id") or observation.get("scope_id") not in context["segment_ids"]:
            return False
        expected_refs = context["active_source_binding_refs"]
    else:
        return False
    pairs = {
        "entity_id": "entity_id", "identity_state_at_answer": "identity_state",
        "identity_revision": "identity_revision", "source_binding_version": "source_binding_version",
    }
    return (observation.get("source_binding_refs") == expected_refs
            and all(observation.get(field) == context[owner_field]
                    for field, owner_field in pairs.items()))


def validate_question_mapping(value: dict) -> None:
    _validate_draft7(METRIC_SCHEMA, value)


def validate_rule(value: dict) -> None:
    _validate_draft7(RULE_SCHEMA, value)


def _validate_score_ref(score_ref: dict) -> None:
    if score_ref["status"] == "scored":
        required = (
            "information_as_of", "observed_at", "observation_id",
            "model_resolved", "check_level",
        )
        if any(score_ref.get(field) is None for field in required):
            raise ValueError("scored result is missing lineage, model, level, or time")


def _validate_coverage(coverage: dict) -> None:
    requested = set(coverage["requested_field_ids"])
    covered = set(coverage["covered_field_ids"])
    missing = set(coverage["missing_field_ids"])
    if covered & missing:
        raise ValueError("covered and missing fields overlap")
    if covered | missing != requested:
        raise ValueError("coverage fields do not partition requested fields")
    if coverage["status"] == "complete" and missing:
        raise ValueError("complete coverage cannot have missing fields")
    if coverage["status"] == "not_covered" and covered:
        raise ValueError("not_covered cannot have covered fields")


def validate_query_response(value: dict) -> None:
    """Validate query response shape and cross-object consistency."""
    _validate_202012(QUERY_SCHEMA, value)
    if value.get("message_type") != "response":
        raise ValueError("expected a query response")
    operation = value["operation"]
    result = value["result"]
    coverage = result.get("coverage")
    if coverage is not None:
        _validate_coverage(coverage)
    if operation == "search":
        status, items = result["status"], result["items"]
        if status == "ok" and (not items or coverage["status"] != "complete"):
            raise ValueError("ok search requires non-empty items and complete coverage")
        for item in items:
            for score_ref in item["score_refs"]:
                _validate_score_ref(score_ref)
    elif operation == "get_profiles":
        profile_ids: set[str] = set()
        for profile in result["profiles"]:
            entity_id = profile["entity_id"]
            if entity_id in profile_ids:
                raise ValueError("duplicate profile entity")
            profile_ids.add(entity_id)
            for observation in profile["observations"]:
                if observation.get("entity_id") != entity_id:
                    raise ValueError("profile contains observation for another entity")


def validate_exchange_package(value: dict) -> None:
    _validate_202012(EXCHANGE_SCHEMA, value)
    if value.get("extensions"):
        raise ValueError("unregistered exchange extensions are forbidden")
    try:
        from .exchange_contract import validate_package_integrity
    except ImportError:
        from exchange_contract import validate_package_integrity

    validate_package_integrity(value)


def assert_same_entity(*entity_ids: str) -> None:
    if not entity_ids or len(set(entity_ids)) != 1:
        raise ValueError("cross-object entity mismatch")


def converted_ordinary_share_price(price: float, adr_ratio: float | None) -> float:
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        raise ValueError("price must be a non-negative number")
    if isinstance(adr_ratio, bool) or not isinstance(adr_ratio, (int, float)) or adr_ratio <= 0:
        raise ValueError("verified positive adr_ratio is required")
    return float(price) / float(adr_ratio)


def reconcile_answer_score(
    *, expected_question_id: str, actual_question_id: str,
    outer_score: object, inner_score: object,
) -> int:
    if expected_question_id != actual_question_id:
        raise ValueError("question_id mismatch")
    for value in (outer_score, inner_score):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
            raise ValueError("score must be an integer from 1 to 10")
    if outer_score != inner_score:
        raise ValueError("outer and inner score mismatch")
    return inner_score


def coverage_rate(*, selected_count: int, valid_scored_count: int,
                  na_count: int, na_is_audited: bool) -> float:
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0
           for v in (selected_count, valid_scored_count, na_count)):
        raise ValueError("coverage counts must be non-negative integers")
    denominator = selected_count - na_count if na_is_audited else selected_count
    if denominator <= 0 or valid_scored_count > denominator:
        raise ValueError("invalid coverage denominator")
    return valid_scored_count / denominator


_OPS = {
    ">": operator.gt, ">=": operator.ge, "<": operator.lt,
    "<=": operator.le, "==": operator.eq, "!=": operator.ne,
}


def evaluate_rule(rule: dict, fields: Mapping[str, object]) -> str:
    """Evaluate a validated rule with fail/pass/unknown semantics."""
    validate_rule(rule)
    if "condition" in rule:
        condition = rule["condition"]
        value = fields.get(condition["field"])
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "unknown"
        return "pass" if _OPS[condition["op"]](value, condition["value"]) else "fail"
    if "not" in rule:
        value = evaluate_rule(rule["not"], fields)
        return {"pass": "fail", "fail": "pass", "unknown": "unknown"}[value]
    key = "all" if "all" in rule else "any"
    values = [evaluate_rule(child, fields) for child in rule[key]]
    if key == "all":
        return "fail" if "fail" in values else "unknown" if "unknown" in values else "pass"
    return "pass" if "pass" in values else "unknown" if "unknown" in values else "fail"


def evaluate_policy(root_rule: dict, fields: Mapping[str, object],
                    critical_gates: Iterable[dict] = ()) -> str:
    for gate in critical_gates:
        if evaluate_rule({"condition": gate}, fields) != "pass":
            return "fail"
    return evaluate_rule(root_rule, fields)


def metrics_comparable(left: dict, right: dict) -> bool:
    for item in (left, right):
        _validate_draft7(METRIC_SCHEMA, item)
    if left["metric_id"] != right["metric_id"] or left["unit"] != right["unit"]:
        return False
    if "non_comparable" in (left["comparability_scope"], right["comparability_scope"]):
        return False
    if "within_cohort_only" in (left["comparability_scope"], right["comparability_scope"]):
        return left["cohort"] == right["cohort"]
    return True


def diagnostic_decision(*, has_unanswered_risk: bool, evidence_status: str) -> str:
    if evidence_status not in {"not_applicable", "unknown", "valid"}:
        raise ValueError("invalid evidence status")
    if evidence_status == "not_applicable":
        return "skip_diagnostic"
    if evidence_status == "unknown":
        return "needs_verification"
    return "trigger_diagnostic" if has_unanswered_risk else "skip_diagnostic"

