"""Public, read-only JSON entry point for the IQS identity contract.

This validates package structure and reference consistency. It does not
authenticate caller-supplied trust context or certify a StockWiki producer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker
from jsonschema import ValidationError as JsonSchemaValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "2.2.0"
MAX_INPUT_BYTES = 1_048_576
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "quick_scan" / "identity-cli-request.schema.json"
IDENTITY_SCHEMA_PATH = ROOT / "schemas" / "quick_scan" / "identity.schema.json"


class _InputFailure(Exception):
    def __init__(self, code: str, pointer: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.pointer = pointer


class _DuplicateKeyError(ValueError):
    pass


def _object_no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError("duplicate_json_key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError("non_finite_number")


def _json_pointer(parts: Any) -> str:
    if not parts:
        return ""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


def _load_schemas() -> tuple[dict[str, Any], dict[str, Any], Registry]:
    request_schema = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    identity_schema = json.loads(IDENTITY_SCHEMA_PATH.read_text(encoding="utf-8"))
    registry = Registry().with_resource(
        identity_schema["$id"], Resource.from_contents(identity_schema)
    )
    return request_schema, identity_schema, registry


def _response(version: str, errors: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": version,
        "status": "valid" if not errors else "invalid",
        "validation_scope": "contract_consistency_only",
        "errors": errors,
    }


def _read_request(path: str) -> dict[str, Any]:
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise _InputFailure("input_unreadable") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise _InputFailure("input_too_large")
    try:
        text = raw.decode("utf-8-sig")
        value = json.loads(
            text,
            object_pairs_hook=_object_no_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except _DuplicateKeyError as exc:
        raise _InputFailure("duplicate_json_key") from exc
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise _InputFailure("invalid_json") from exc
    if not isinstance(value, dict):
        raise _InputFailure("request_must_be_object")
    return value


def _selected_request_schema(
    request_schema: dict[str, Any], object_type: Any
) -> dict[str, Any] | None:
    if not isinstance(object_type, str):
        return None
    for variant in request_schema.get("oneOf", []):
        props = variant.get("properties", {})
        if props.get("object_type", {}).get("const") == object_type:
            return variant
    return None


def _schema_failure(
    schema: dict[str, Any], value: dict[str, Any], registry: Registry
) -> dict[str, str] | None:
    validator = Draft7Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            str(error.validator or ""),
        ),
    )
    if not errors:
        return None
    return {
        "code": "request_schema_invalid",
        "pointer": _json_pointer(errors[0].absolute_path),
    }


def _validate_semantics(request: dict[str, Any]) -> None:
    # Imported only after schema/version/input gates. This CLI remains the
    # public boundary; callers do not import this module's Python internals.
    import contract_validation as cv

    payload = request["payload"]
    trusted = request["trusted_context"]
    if request["object_type"] == "entity":
        cv.validate_entity(
            payload,
            trusted_identity_receipts=trusted["identity_receipts"],
            trusted_source_bindings=trusted["source_bindings"],
            trusted_market_registry=trusted["market_registry"],
        )
        return
    cv.validate_analysis_subject(
        payload,
        trusted_issuer_states=trusted["issuer_states"],
        trusted_listing_to_issuer=trusted["listing_to_issuer"],
        trusted_reporting_perimeter_receipts=trusted["reporting_perimeter_receipts"],
    )


def validate_file(input_path: str, schema_version: str) -> tuple[dict[str, Any], int]:
    """Validate one public request document and return its JSON response/exit code."""
    if schema_version != SCHEMA_VERSION:
        return _response(schema_version, [{
            "code": "unknown_schema_version",
            "pointer": "/schema_version",
        }]), 3

    try:
        request = _read_request(input_path)
    except _InputFailure as exc:
        return _response(schema_version, [{"code": exc.code, "pointer": exc.pointer}]), 2

    if request.get("schema_version") != schema_version:
        return _response(schema_version, [{
            "code": "schema_version_mismatch",
            "pointer": "/schema_version",
        }]), 2

    try:
        request_schema, identity_schema, registry = _load_schemas()
        # Confirm the public package schema is itself well-formed before using it.
        Draft7Validator.check_schema(request_schema)
        Draft7Validator.check_schema(identity_schema)
        if _selected_request_schema(request_schema, request.get("object_type")) is None:
            return _response(schema_version, [{
                "code": "unsupported_object_type",
                "pointer": "/object_type",
            }]), 2
        # Validate against the document root so local #/definitions refs keep
        # resolving from the schema resource that owns them.
        failure = _schema_failure(request_schema, request, registry)
        if failure:
            return _response(schema_version, [failure]), 2
        _validate_semantics(request)
    except JsonSchemaValidationError as exc:
        pointer = "/payload" + _json_pointer(exc.absolute_path)
        return _response(schema_version, [{
            "code": "identity_schema_invalid",
            "pointer": pointer,
        }]), 2
    except (ValueError, KeyError, TypeError):
        # Do not echo payload values or validator exception messages.
        return _response(schema_version, [{
            "code": "semantic_validation_failed",
            "pointer": "/payload",
        }]), 2
    except OSError:
        return _response(schema_version, [{
            "code": "validator_unavailable",
            "pointer": "",
        }]), 2
    except Exception:
        # Keep the public CLI fail-closed if a local schema reference or
        # validator dependency is unexpectedly broken; never emit a traceback
        # that could include caller-controlled input.
        return _response(schema_version, [{
            "code": "validator_unavailable",
            "pointer": "",
        }]), 2
    return _response(schema_version, []), 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only validation for IQS identity contract JSON requests."
    )
    parser.add_argument("--input", required=True, help="Path to one JSON validation request")
    parser.add_argument("--schema-version", required=True, help="Identity package version")
    args = parser.parse_args(argv)
    response, exit_code = validate_file(args.input, args.schema_version)
    print(json.dumps(response, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
