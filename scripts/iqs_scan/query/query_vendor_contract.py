"""Query 2.6 selects an explicit original observation profile."""

from iqs_scan import REPO_ROOT
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from iqs_scan.foundation.api import observation_schema_for as schema_for
from .query_contract import ProfileQueryDialect, query_sha256, seal_response

API_PROTOCOL = "iqs.query-vendor-contract-api/1.0.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "ProfileQueryDialect",
    "original_observation", "validate_request",
})

__all__ = ['profile_query_schema', 'query_sha256', 'original_observation',
           'seal_response', 'validate_request', 'validate_response']

_SCHEMA = json.loads((REPO_ROOT / 'schemas/quick_scan/query-v2.6.schema.json').read_bytes())
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_WIRE_PROFILES = {
    '1.1.0': 'stockwiki-portable-observation/1.0.0',
    '1.2.0': 'stockwiki-portable-observation/1.1.0',
}


def profile_query_schema():
    """Return the 2.6 query schema for enclosing wire contracts."""
    return copy.deepcopy(_SCHEMA)


def _select_schema(version, wire_profile):
    if not isinstance(version, str) or version not in _WIRE_PROFILES:
        raise ValueError('query_observation_profile_unavailable')
    if wire_profile != _WIRE_PROFILES[version]:
        raise ValueError('query_original_wire_profile_mismatch')
    if version == '1.2.0':
        return schema_for(version)
    return None


_DIALECT = ProfileQueryDialect(_VALIDATOR, select_observation_schema=_select_schema)


def validate_request(value):
    _DIALECT.validate_request(value)
    return copy.deepcopy(value)


def original_observation(row):
    return _DIALECT.original_observation(row)


# Compatibility for the StockWiki 2.6 synthetic fixture. Runtime adapters use
# original_observation, and this name is excluded from the public exports.
_original = original_observation


def validate_response(value, *, expected_request, expected_owner):
    return _DIALECT.validate_response(value, expected_request=expected_request, expected_owner=expected_owner)
