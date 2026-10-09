"""Public offline adapter for W15; reuse IQS's released routing/manifest validators.

The expected ID must come from caller-owned state. Content hashes are not
source authentication, a fee approval, or proof of real company evidence.
History validation never grants a new execution. No network or DB access.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

import module_contract
import question_manifest
import routing

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "iqs.route_store_validation/1.0.0"
MAX_INPUT_BYTES = 8 * 1024 * 1024
_ROUTE_ID = re.compile(r"^route_[a-f0-9]{64}$")
DTO_SCHEMA = json.loads((ROOT / "schemas/quick_scan/route-store-validation.schema.json").read_bytes())


class RouteBundleError(ValueError):
    """Bounded, named refusal before the owner stores or dispatches a bundle."""

    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def _read(path, kind):
    try:
        with Path(path).open("rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise RouteBundleError(kind + "_unreadable", type(exc).__name__) from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise RouteBundleError(kind + "_too_large")
    try:
        document = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=module_contract._unique_object)
        if not isinstance(document, dict):
            raise ValueError("object required")
        # The existing strict serializer also rejects NaN/Infinity/1e400 at
        # any depth, including optional metadata not selected by schemas.
        module_contract.canonical_bytes(document)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise RouteBundleError(kind + "_json_invalid", type(exc).__name__) from exc
    return document, raw


def validate_route_bundle(route_path, manifest_path, *, root=ROOT, expected_decision_id,
                          validation_mode="history", now_utc=None):
    """Validate exactly one released route/manifest pair without persisting it.

    Consumers must obtain this DTO from a trusted validator transport and
    compare both input SHA256s before storage. They cannot authenticate a
    DTO by accepting an arbitrary object that claims to use this protocol.
    """
    if not isinstance(expected_decision_id, str) or not _ROUTE_ID.fullmatch(expected_decision_id):
        raise RouteBundleError("independent_anchor_required")
    if validation_mode not in {"history", "execution"}:
        raise RouteBundleError("validation_mode_invalid")
    if validation_mode == "execution" and now_utc is None:
        raise RouteBundleError("execution_time_required")
    if validation_mode == "history" and now_utc is not None:
        raise RouteBundleError("unexpected_execution_time")
    route, route_raw = _read(route_path, "route")
    if route.get("decision_id") != expected_decision_id:
        raise RouteBundleError("route_anchor_mismatch")
    if route.get("schema_version") != "2.0.0":
        raise RouteBundleError("route_schema_unsupported")
    manifest, manifest_raw = _read(manifest_path, "manifest")
    if (manifest.get("route_decision") != route or
            manifest.get("route_decision_id") != expected_decision_id):
        raise RouteBundleError("route_manifest_binding_mismatch")
    if (manifest.get("schema_version") != "3.1" or
            manifest.get("metric_contract_version") != "1.0.0" or
            not isinstance(manifest.get("module_package_id"), str)):
        # Older readers can retain legacy snapshots; this new adapter must
        # never fall through the legacy validator's intentional None result.
        raise RouteBundleError("published_manifest_required")
    try:
        routing.validate_route_snapshot(route, root=Path(root))
    except (ValueError, ValidationError, KeyError, TypeError, OSError) as exc:
        raise RouteBundleError("route_invalid", type(exc).__name__) from exc
    try:
        mappings = question_manifest.validate_manifest_metric_contract(manifest, root=Path(root))
        if mappings is None:
            raise ValueError("released manifest validation required")
    except (ValueError, ValidationError, KeyError, TypeError, OSError) as exc:
        raise RouteBundleError("manifest_invalid", type(exc).__name__) from exc
    if validation_mode == "execution":
        try:
            routing.validate_route_for_execution(route, root=Path(root), now_utc=now_utc,
                                                 expected_decision_id=expected_decision_id)
        except (ValueError, ValidationError, KeyError, TypeError, OSError) as exc:
            raise RouteBundleError("route_execution_invalid", type(exc).__name__) from exc
    result = {
        "protocol": PROTOCOL, "schema_version": "1.0.0", "status": "validated",
        "validation_mode": validation_mode, "expected_decision_id": expected_decision_id,
        "decision_id": route["decision_id"], "entity_id": route["entity_id"],
        "scope": route["scope"], "segment_id": route["segment_id"],
        "route_raw_sha256": hashlib.sha256(route_raw).hexdigest(),
        "manifest_raw_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "module_package_id": manifest["module_package_id"],
        "module_release_id": manifest["module_release_id"], "router_version": route["router_version"],
        "method_id": manifest["method_id"], "question_count": manifest["question_count"],
        "module_locks": copy.deepcopy(manifest["module_locks"]),
        "original_routing_execution": copy.deepcopy(manifest["routing_execution"]),
        "route_execution": copy.deepcopy(route["execution"]),
        "execution_checked_at": now_utc,
        "new_execution_authorized": validation_mode == "execution",
        "source_authentication": "caller_owned_anchor_and_trusted_validator_transport_required",
        "model_API_requests": 0, "database_writes": 0,
    }
    if "classification_confidence" in route:
        result["classification_confidence"] = copy.deepcopy(route["classification_confidence"])
    try:
        Draft202012Validator(DTO_SCHEMA, format_checker=FormatChecker()).validate(result)
    except ValidationError as exc:
        raise RouteBundleError("validator_output_invalid") from exc
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-decision-id", required=True)
    parser.add_argument("--validation-mode", choices=("history", "execution"), default="history")
    parser.add_argument("--now-utc")
    args = parser.parse_args(argv)
    try:
        result = validate_route_bundle(args.route, args.manifest, root=args.root,
                                       expected_decision_id=args.expected_decision_id,
                                       validation_mode=args.validation_mode, now_utc=args.now_utc)
    except RouteBundleError as exc:
        print(json.dumps({"protocol": PROTOCOL, "status": "rejected", "error_code": exc.code},
                         ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
