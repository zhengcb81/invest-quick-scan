"""Shared local question-catalog and profile contract.

This layer reads authoring JSON and applies deterministic validation. It has no
CLI, answer-builder, provider, network client, job runner, or production-store
dependency. Output JSON is limited to explicit local artifacts in caller paths.
"""
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from json_io import read_json, write_json
import module_registry

ROOT = Path(__file__).resolve().parents[1]
__all__ = ["ROOT", "read_json", "write_json", "load_library", "valid_url", "validate_profile"]


def load_library(*, root=None):
    """Load the currently authored catalog through the versioned registry."""
    catalog, modules, _ = module_registry.source_catalog(Path(root) if root else ROOT)
    return catalog, modules


def valid_url(value):
    """Return whether a source locator is a syntactically valid HTTP(S) URL."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname)
    except ValueError:
        return False


def validate_profile(profile, modules, contexts=None, *, root=None):
    """Validate deterministic company/module selection inputs without side effects."""
    root = Path(root) if root else ROOT
    for key in ("company", "ticker", "exchange", "as_of", "company_type", "stage",
                "routing_rationale", "routing_confidence"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise ValueError(f"profile requires a nonempty {key}")
    date.fromisoformat(profile["as_of"])
    if profile.get("quote_date"):
        if date.fromisoformat(profile["quote_date"]) > date.fromisoformat(profile["as_of"]):
            raise ValueError("quote_date cannot be after as_of")
    if profile["routing_confidence"] not in ("high", "medium"):
        raise ValueError("uncertain routing: export common first, then resolve the classification")
    if not isinstance(profile.get("routing_sources"), list) or not profile["routing_sources"]:
        raise ValueError("profile requires routing_sources")
    for source in profile["routing_sources"]:
        if not isinstance(source, dict) or not valid_url(source.get("url")):
            raise ValueError("routing source must have a valid HTTP(S) URL")
        published = source.get("published_at", "unknown")
        if published != "unknown" and date.fromisoformat(published) > date.fromisoformat(profile["as_of"]):
            raise ValueError("routing source is after as_of")
    for key, kind in (("company_type", "types"), ("stage", "stages")):
        if profile[key] not in modules or modules[profile[key]]["kind"] != kind:
            raise ValueError(f"unknown {key}: {profile[key]}")
    if profile["stage"] == "cyclical":
        raise ValueError("choose a lifecycle stage and set cycle_sensitive separately")
    for key, kind, limit in (("industry_modules", "industries", 2), ("overlays", "overlays", 8),
                             ("diagnostic_modules", "diagnostics", 3),
                             ("investment_lenses", "lenses", 8),
                             ("common_extension_modules", "common_extensions", 8)):
        values = profile.get(key, [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError(f"{key} must be a list of IDs")
        if len(values) > limit or len(values) != len(set(values)):
            raise ValueError(f"invalid number or duplicate {key}")
        if any(value not in modules or modules[value]["kind"] != kind for value in values):
            raise ValueError(f"unknown module in {key}")
    reasons = profile.get("diagnostic_rationale", {})
    if not isinstance(reasons, dict) or any(
            not isinstance(reasons.get(value), str) or not reasons[value].strip()
            for value in profile.get("diagnostic_modules", [])):
        raise ValueError("each optional diagnostic needs a specific unresolved question in diagnostic_rationale")
    lens_reasons = profile.get("lens_rationale", {})
    if not isinstance(lens_reasons, dict) or any(
            not isinstance(lens_reasons.get(value), str) or not lens_reasons[value].strip()
            for value in profile.get("investment_lenses", [])):
        raise ValueError("each investment lens requires a user rationale")
    if profile["company_type"] in ("operating", "pre_revenue") and not profile.get("industry_modules"):
        raise ValueError("operating and pre_revenue require an industry; use other if coverage is missing")
    if type(profile.get("cycle_sensitive", False)) is not bool:
        raise ValueError("cycle_sensitive must be boolean")
    if profile.get("cycle_sensitive") and not profile.get("cycle_position"):
        raise ValueError("cyclical companies require cycle_position, including uncertainty if needed")
    if type(profile.get("recovery_review", False)) is not bool:
        raise ValueError("recovery_review must be boolean")
    if profile.get("recovery_review") and (not isinstance(profile.get("recovery_rationale"), str)
                                             or not profile["recovery_rationale"].strip()):
        raise ValueError("recovery_review requires recovery_rationale")
    if profile.get("business_subtype"):
        contexts = contexts or read_json(root / "questions/scoring-contexts.json")
        relevant = [profile["company_type"], *profile.get("industry_modules", [])]
        allowed = {key for module in relevant for key in contexts["subtypes"].get(module, {})}
        if profile["business_subtype"] not in allowed:
            raise ValueError("business_subtype does not match selected type/industry")
