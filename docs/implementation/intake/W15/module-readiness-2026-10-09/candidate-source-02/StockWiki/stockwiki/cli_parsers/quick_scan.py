"""Quick-scan candidate/identity/universe CLI parser registration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import stockwiki.quick_scan_import as quick_scan_import
import stockwiki.quick_scan_refresh as quick_scan_refresh
from stockwiki.identity_import import run_entity_import
from stockwiki.quick_scan_analysis import run_analysis_subject_import
from stockwiki.quick_scan_candidate_import import run_candidate_import
from stockwiki.quick_scan_identity import register_identity_preview_parser
from stockwiki.quick_scan_issuer_bridge import (
    run_issuer_bridge_import,
    run_issuer_bridge_report,
)
from stockwiki.quick_scan_maintenance import (
    run_maintenance_apply_auto,
    run_maintenance_nominate,
    run_maintenance_report,
)
from stockwiki.quick_scan_observations import (
    ObservationImportError,
    QuickScanObservationStore,
)
from stockwiki.quick_scan_routes_cli import register as register_routes
from stockwiki.quick_scan_store import QuickScanStore, QuickScanStoreError
from stockwiki.quick_scan_universe import (
    run_entity_add_security,
    run_universe_add,
    run_universe_diff,
    run_universe_explain,
    run_universe_list,
    run_universe_pin,
    run_universe_remove,
    run_universe_restore,
)
from stockwiki.services._common import paths_from_args


def register(subparsers: Any) -> None:
    register_routes(subparsers)
    register_identity_preview_parser(subparsers)

    add = subparsers.add_parser(
        "universe-add",
        help=(
            "Add an existing entity to a universe (idempotent; never creates "
            "entities, never re-requests questions). stdout: one canonical JSON."
        ),
    )
    add.add_argument("--universe-id", required=True)
    add.add_argument("--entity-id", required=True)
    add.add_argument("--reason", required=True, help="Non-empty added_reason.")
    add.add_argument("--priority", type=int, default=0)
    add.add_argument("--pin", action="store_true", help="Set manual_pin on add.")
    add.add_argument("--at", default=None, help="Optional explicit UTC timestamp.")
    add.set_defaults(func=run_universe_add)

    remove = subparsers.add_parser(
        "universe-remove",
        help="Explicit logical removal with a reason (never score-driven).",
    )
    remove.add_argument("--universe-id", required=True)
    remove.add_argument("--entity-id", required=True)
    remove.add_argument("--reason", required=True, help="Non-empty removal_reason.")
    remove.add_argument("--at", default=None)
    remove.set_defaults(func=run_universe_remove)

    restore = subparsers.add_parser(
        "universe-restore",
        help="Restore a logically removed member; history and reasons preserved.",
    )
    restore.add_argument("--universe-id", required=True)
    restore.add_argument("--entity-id", required=True)
    restore.add_argument("--reason", required=True, help="Non-empty restoration_reason.")
    restore.add_argument("--at", default=None)
    restore.set_defaults(func=run_universe_restore)

    pin = subparsers.add_parser("universe-pin", help="Set manual_pin=true for one active member.")
    pin.add_argument("--universe-id", required=True)
    pin.add_argument("--entity-id", required=True)
    pin.add_argument("--at", default=None)
    pin.set_defaults(func=run_universe_pin, pinned=True)

    unpin = subparsers.add_parser(
        "universe-unpin", help="Set manual_pin=false for one active member."
    )
    unpin.add_argument("--universe-id", required=True)
    unpin.add_argument("--entity-id", required=True)
    unpin.add_argument("--at", default=None)
    unpin.set_defaults(func=run_universe_pin, pinned=False)

    listing = subparsers.add_parser(
        "universe-list", help="List members of a universe (canonical JSON)."
    )
    listing.add_argument("--universe-id", required=True)
    listing.set_defaults(func=run_universe_list)

    diff = subparsers.add_parser(
        "universe-diff",
        help=(
            "Compare live membership against an expected JSON list file; "
            "report-only: no eviction, no mutation."
        ),
    )
    diff.add_argument("--universe-id", required=True)
    diff.add_argument(
        "--expected",
        required=True,
        help="Path to a JSON array of {entity_id, priority?, manual_pin?}.",
    )
    diff.set_defaults(func=run_universe_diff)

    explain = subparsers.add_parser(
        "universe-explain",
        help=(
            "Explain one member's current state and full version history; "
            "score is informational only (never removes)."
        ),
    )
    explain.add_argument("--universe-id", required=True)
    explain.add_argument("--entity-id", required=True)
    explain.add_argument("--score", type=int, default=None)
    explain.set_defaults(func=run_universe_explain)

    add_sec = subparsers.add_parser(
        "entity-add-security",
        help=(
            "Append a source-bound listing to an existing entity from a "
            "{security, binding, expected_identity_revision?} JSON file; "
            "duplicate re-add is an idempotent no-op."
        ),
    )
    add_sec.add_argument("--entity-id", required=True)
    add_sec.add_argument(
        "--security-file",
        required=True,
        help="Path to JSON with {security, binding, expected_identity_revision?}.",
    )
    add_sec.set_defaults(func=run_entity_add_security)

    cand = subparsers.add_parser(
        "candidate-import",
        help=(
            "Stage owner-confirmed candidates from a frozen identity-preview "
            "report (idempotent by content hash; unresolved rows never become "
            "entities/members; stdout: one canonical JSON receipt)."
        ),
    )
    cand.add_argument(
        "--report",
        required=True,
        help="Path to the frozen identity-preview report JSON.",
    )
    cand.add_argument("--at", default=None, help="Optional explicit UTC timestamp.")
    cand.set_defaults(func=run_candidate_import)

    ent = subparsers.add_parser(
        "entity-import",
        help=(
            "Import one owner entity payload (+ optional identity receipt) via "
            "the real two-phase path (stdout: one canonical JSON receipt)."
        ),
    )
    ent.add_argument("--file", required=True, help="Path to the owner payload JSON.")
    ent.add_argument("--at", default=None, help="Optional explicit UTC timestamp.")
    ent.set_defaults(func=run_entity_import)

    brg = subparsers.add_parser(
        "issuer-bridge-import",
        help=(
            "Import an owner-signed A/H same-issuer pair evidence table into "
            "the quick_scan_issuer_bridge evidence table (content-addressed "
            "idempotent replay; never creates entities/members/eligibility; "
            "stdout: one canonical JSON receipt)."
        ),
    )
    brg.add_argument(
        "--source",
        required=True,
        help="Path to the owner-signed A/H bridge JSON (status=SIGNED).",
    )
    brg.add_argument("--at", default=None, help="Optional explicit UTC timestamp.")
    brg.add_argument(
        "--expect-decision-ref",
        default=None,
        help=(
            "Pin the exact owner sign-off this import must carry "
            "(owner-YYYY-MM-DD-slug); a different decision_ref is refused."
        ),
    )
    brg.add_argument(
        "--report",
        default=None,
        help="Also write the canonical receipt JSON copy to this path.",
    )
    brg.set_defaults(func=run_issuer_bridge_import)

    brg_rep = subparsers.add_parser(
        "issuer-bridge-report",
        help=(
            "Read-only aggregation over landed A/H bridge evidence (row count, "
            "confidence distribution, decision refs; optional --source proves "
            "DB<->source diff=0; stdout: canonical JSON)."
        ),
    )
    brg_rep.add_argument(
        "--source",
        default=None,
        help="Optional signed source JSON to diff the database against.",
    )
    brg_rep.set_defaults(func=run_issuer_bridge_report)

    subj = subparsers.add_parser(
        "analysis-subject-import",
        help=(
            "Import one owner AnalysisSubject payload + perimeter receipt "
            "(single-transaction; stdout: one canonical JSON receipt)."
        ),
    )
    subj.add_argument("--file", required=True, help="Path to the owner payload JSON.")
    subj.add_argument("--at", default=None, help="Optional explicit UTC timestamp.")
    subj.set_defaults(func=run_analysis_subject_import)

    obs = subparsers.add_parser(
        "observation-import",
        help=(
            "Import one C06 exchange package plus its frozen S05 release "
            "manifest (transactional ACK per item; stdout: one canonical JSON receipt)."
        ),
    )
    obs.add_argument("--package", required=True, help="Path to the exchange package JSON.")
    obs.add_argument(
        "--release", required=True, help="Path to the frozen S05 release manifest JSON."
    )
    obs.set_defaults(func=run_observation_import)

    nominate = subparsers.add_parser(
        "maintenance-nominate",
        help=(
            "Intake nominations from a JSON file (idempotent by source row; "
            "never creates members; stdout: one canonical JSON receipt)."
        ),
    )
    nominate.add_argument("--universe-id", required=True)
    nominate.add_argument(
        "--source-file",
        required=True,
        help='Path to a JSON array (or {"nominations": [...]}) of nomination records.',
    )
    nominate.add_argument("--at", default=None)
    nominate.set_defaults(func=run_maintenance_nominate)

    apply_auto = subparsers.add_parser(
        "maintenance-apply-auto",
        help=(
            "Evaluate candidate nominations and atomically admit eligible ones "
            "with their scan intent (mutates members/intents; receipt lists "
            "admitted/held/skipped; zero LLM/network)."
        ),
    )
    apply_auto.add_argument("--universe-id", required=True)
    apply_auto.add_argument("--window-key", required=True, help="Maintenance window key.")
    apply_auto.add_argument("--at", default=None)
    apply_auto.set_defaults(func=run_maintenance_apply_auto)

    maint_report = subparsers.add_parser(
        "maintenance-report",
        help=(
            "Read-only maintenance pass: low-score/delisting findings with NO "
            "removals (evicted is always empty)."
        ),
    )
    maint_report.add_argument("--universe-id", required=True)
    maint_report.add_argument(
        "--scores",
        default=None,
        help="Path to a JSON object {entity_id: integer score} for read-only findings.",
    )
    maint_report.set_defaults(func=run_maintenance_report)

    ref = subparsers.add_parser(
        "quick-scan-refresh-request",
        help=(
            "Owner-interface targeted refresh (W11): scope+cap checked gap "
            "task emitting a main_with_llm-consumable artifact (stdout: one "
            "canonical JSON; no SQL write surface — read-only SELECTs via "
            "W09 — and never expands to the full pool)."
        ),
    )
    ref.add_argument("--entity", action="append", required=True, dest="entities")
    ref.add_argument("--field", action="append", required=True, dest="fields")
    ref.add_argument("--cost-cap-micros", type=int, required=True)
    ref.add_argument("--roster-version", type=int, default=1)
    ref.add_argument(
        "--prior-task",
        default=None,
        help="Path to the prior task JSON (JOB-06 carry-over keys).",
    )
    ref.add_argument(
        "--questions",
        default=None,
        help="Path to field->questions JSON: {field:[{question_id,text}]} for gap fields.",
    )
    ref.add_argument("--out", default=None, help="Also write the artifact JSON here.")
    ref.set_defaults(func=run_refresh_request)

    ref_status = subparsers.add_parser(
        "quick-scan-refresh-status",
        help="W10 read-only runtime status projection for refresh consumers (I13).",
    )
    ref_status.set_defaults(func=run_refresh_status)


def _emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


def _fail(exc: Exception, code: str) -> int:
    print(
        json.dumps({"error_code": code, "detail": str(exc)}, ensure_ascii=False, sort_keys=True),
        file=sys.stderr,
    )
    return 2


def run_refresh_request(args: Any) -> int:
    try:
        paths = paths_from_args(args)
        store = QuickScanStore(paths)
        questions_by_field = {}
        if args.questions:
            questions_by_field = json.loads(Path(args.questions).read_text(encoding="utf-8"))
        prior_task = None
        if args.prior_task:
            prior_task = json.loads(Path(args.prior_task).read_text(encoding="utf-8"))
        task = quick_scan_refresh.request_refresh(
            store,
            entities=list(args.entities),
            fields=list(args.fields),
            cost_cap_micros=args.cost_cap_micros,
            roster_version=args.roster_version,
            prior_task=prior_task,
        )
        artifact = quick_scan_refresh.render_refresh_artifact(
            task, questions_by_field=questions_by_field
        )
        if args.out:
            Path(args.out).write_text(
                json.dumps(artifact, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
        return _emit(artifact)
    except Exception as exc:  # noqa: BLE001
        return _fail(exc, "refresh_request_failed")


def run_refresh_status(args: Any) -> int:
    try:
        paths = paths_from_args(args)
        return _emit(quick_scan_refresh.refresh_status(paths))
    except Exception as exc:  # noqa: BLE001
        return _fail(exc, "refresh_status_failed")


def run_observation_import(args: Any) -> int:
    """CLI entry for `observation-import`: one package + frozen release in."""
    try:
        paths = paths_from_args(args)
        obs_store = QuickScanObservationStore(paths)
        identity_store = QuickScanStore(paths)
        package_raw = open(str(args.package), "rb").read()
        release = json.loads(open(str(args.release), "rb").read().decode("utf-8"))
        receipt = quick_scan_import.import_package(
            obs_store,
            package_raw,
            frozen_release=release,
            identity_store=identity_store,
        )
        receipt["action"] = "observation-import"
        return _emit(receipt)
    except (QuickScanStoreError, ObservationImportError, ValueError) as exc:
        code = getattr(exc, "error_code", "observation_import_rejected")
        return _fail(exc, code)
    except OSError as exc:
        return _fail(exc, "input_file_unreadable")
