"""Explicit owner route/refresh CLI; no automatic migration or paid dispatch."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_module_refresh import plan_module_refresh
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_route_validation import IqsRouteValidator, RouteStoreError, read_json
from stockwiki.quick_scan_routes import QuickScanRouteStore
from stockwiki.quick_scan_store import QuickScanStore

PROTOCOL = "stockwiki.route_store_cli/1.0.0"


def register(subparsers: Any) -> None:
    for operation in ("binding", "record", "activate", "current", "anchor", "history", "refresh"):
        parser = subparsers.add_parser("quick-scan-route-" + operation, help=__doc__)
        parser.add_argument("--iqs-code-root", required=True, type=Path)
        parser.add_argument("--iqs-release-root", type=Path)
        parser.add_argument("--subject-key", required=True)
        if operation in {"record", "activate"}:
            parser.add_argument("--expected-decision-id", required=True)
        if operation == "record":
            parser.add_argument("--route", required=True, type=Path)
            parser.add_argument("--manifest", required=True, type=Path)
        if operation == "activate":
            choice = parser.add_mutually_exclusive_group(required=True)
            choice.add_argument("--expected-current-decision-id")
            choice.add_argument("--expect-no-current", action="store_true")
        if operation in {"current", "anchor", "history", "refresh"}:
            parser.add_argument("--scope", choices=("entity", "segment"), required=True)
            parser.add_argument("--scope-id", required=True)
        if operation in {"activate", "current", "anchor", "refresh"}:
            parser.add_argument("--now-utc", required=True)
        if operation == "current":
            parser.add_argument("--include-raw-bundle", action="store_true")
        if operation == "refresh":
            parser.add_argument("--provider", required=True)
            parser.add_argument("--model", required=True)
            parser.add_argument("--ttl-hours", required=True, type=int)
            parser.add_argument("--work-projection", type=Path)
        parser.set_defaults(func=run, route_operation=operation)


def _public_snapshot(row: dict[str, Any], *, include_raw: bool = False) -> dict[str, Any]:
    result = {
        key: row[key]
        for key in (
            "decision_id",
            "subject_key",
            "entity_id",
            "identity_revision",
            "perimeter_sha256",
            "scope",
            "scope_id",
            "route_raw_sha256",
            "manifest_raw_sha256",
        )
    }
    route = read_json(row["route_raw"])
    manifest = read_json(row["manifest_raw"])
    result.update(
        router_version=route["router_version"],
        route_as_of=route["as_of"],
        decided_at=route["decided_at"],
        route_execution=route["execution"],
        module_package_id=manifest.get("module_package_id"),
        module_release_id=manifest.get("module_release_id"),
        module_locks=manifest.get("module_locks", []),
        question_count=len(manifest["questions"]),
    )
    result["subject_binding"] = row["metadata"]["binding"]
    if "classification_confidence" in route:
        result["classification_confidence"] = route["classification_confidence"]
    if include_raw:
        result.update(
            route_raw_base64=base64.b64encode(row["route_raw"]).decode("ascii"),
            manifest_raw_base64=base64.b64encode(row["manifest_raw"]).decode("ascii"),
            subject_binding=row["metadata"]["binding"],
        )
    return result


def _owner_source_refs(routes: QuickScanRouteStore, snapshot: dict) -> list[str]:
    entity = routes.identity.get_entity(snapshot["entity_id"])
    if entity is None:
        raise RouteStoreError("route_identity_changed")
    return sorted({row["source_binding_ref"] for row in entity["securities"]})


def run(args: Any) -> int:
    action = args.route_operation
    try:
        if not args.root:
            raise RouteStoreError("route_workspace_required")
        paths = WorkspacePaths.from_root(Path(args.root))
        validator = IqsRouteValidator(
            args.iqs_code_root, runs_dir=paths.runs_dir, release_root=args.iqs_release_root
        )
        routes = QuickScanRouteStore(QuickScanStore(paths), validator=validator)
        if action == "binding":
            payload = routes.identity_binding(args.subject_key)
        elif action == "record":
            payload = routes.record_snapshot(
                args.route.read_bytes(),
                args.manifest.read_bytes(),
                subject_key=args.subject_key,
                expected_decision_id=args.expected_decision_id,
            )
        elif action == "activate":
            payload = routes.set_current(
                args.expected_decision_id,
                subject_key=args.subject_key,
                expected_current_decision_id=args.expected_current_decision_id,
                now_utc=args.now_utc,
            )
        elif action == "current":
            current = routes.get_for_execution(
                subject_key=args.subject_key,
                scope=args.scope,
                scope_id=args.scope_id,
                now_utc=args.now_utc,
            )
            payload = {
                "expected_decision_id": current["expected_decision_id"],
                "anchor_version": current["anchor_version"],
                "snapshot": _public_snapshot(
                    current["snapshot"], include_raw=args.include_raw_bundle
                ),
                "owner_source_binding_refs": _owner_source_refs(routes, current["snapshot"]),
                "execution_validation": current["execution_validation"],
            }
        elif action == "anchor":
            current = routes.get_current_anchor(
                subject_key=args.subject_key,
                scope=args.scope,
                scope_id=args.scope_id,
                now_utc=args.now_utc,
            )
            payload = {
                "expected_decision_id": current["expected_decision_id"],
                "anchor_version": current["anchor_version"],
                "owner_source_binding_refs": _owner_source_refs(routes, current["snapshot"]),
                "snapshot": _public_snapshot(current["snapshot"]),
                "new_execution_authorized": False,
            }
        elif action == "history":
            payload = {
                "current_history": routes.current_history(
                    subject_key=args.subject_key, scope=args.scope, scope_id=args.scope_id
                ),
                "snapshots": [
                    _public_snapshot(row)
                    for row in routes.snapshots_for_subject(args.subject_key)
                    if row["scope"] == args.scope and row["scope_id"] == args.scope_id
                ],
            }
        else:
            projection = (
                read_json(args.work_projection.read_bytes()) if args.work_projection else None
            )
            payload = plan_module_refresh(
                routes,
                QuickScanObservationStore(paths),
                subject_key=args.subject_key,
                scope=args.scope,
                scope_id=args.scope_id,
                now_utc=args.now_utc,
                provider=args.provider,
                model=args.model,
                ttl_hours=args.ttl_hours,
                work_items=projection,
            )
            # References retain the original owner payload and hash. They are
            # read-only reuse data, never newly dispatched C06 observations.
            reused = [
                row["reuse_observation_id"]
                for row in payload["fields"]
                if row["decision"] == "reuse"
            ]
            store = QuickScanObservationStore(paths)
            payload["reused_observations"] = {oid: store.get_observation(oid) for oid in reused}
            # The planner ID covers its planner body. The CLI transport carries
            # separate immutable referenced payloads; do not re-seal that ID.
        print(
            json.dumps(
                {
                    "protocol": PROTOCOL,
                    "schema_version": "1.0.0",
                    "action": action,
                    "status": "ok",
                    "payload": payload,
                    "c06_envelope_validated": False,
                    "paid_dispatch_started": False,
                },
                ensure_ascii=False,
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        code = getattr(exc, "code", getattr(exc, "error_code", "route_store_rejected"))
        print(
            json.dumps(
                {"protocol": PROTOCOL, "status": "rejected", "error_code": code}, sort_keys=True
            )
        )
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    register(subparsers)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
