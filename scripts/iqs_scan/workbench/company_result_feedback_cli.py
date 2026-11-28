"""Replay the public company read once and write its observations.

Read-only: this runs the same public entry the Dashboard uses
(``read_company_assessment`` -> StockWiki ``dashboard_company_assessment_cli.py``)
against an existing owner workspace. It never registers, publishes, imports or
calls a model, and it never writes into the owner workspace.

    python -B -X utf8 scripts/company_result_feedback.py \
        --stockwiki-root <StockWiki checkout> \
        --workspace-root runs/r25-live/owner-workspace \
        --entity ENT_... [--result-id cas_...] [--receipts receipts.json] \
        --out observations.jsonl [--run-id ...] [--attempt-id ...]

Exit codes: 0 = read succeeded, 2 = the read was refused, 3 = the observation
output could not be written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ..foundation.api import RuntimeArgumentParser, record_operation_failure
from . import dashboard_company_feedback as feedback
from . import dashboard_company_projection as projection


def _line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def main(argv=None) -> int:
    parser = RuntimeArgumentParser(
        description="Read one company result through the public entry and record its observations.")
    parser.add_argument("--stockwiki-root", type=Path,
                        help="StockWiki checkout that publishes the owner command")
    parser.add_argument("--workspace-root", type=Path,
                        help="owner workspace the command reads")
    parser.add_argument("--stockwiki-python", default=sys.executable)
    parser.add_argument("--entity", help="entity to read; defaults to the injected snapshot's own")
    parser.add_argument("--result-id")
    parser.add_argument("--receipts", type=Path,
                        help="optional per-question receipt summary (offline replay only)")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--inject-result", type=Path,
                        help="temporary public response: project this saved owner snapshot "
                             "through the same public projection instead of reading the owner")
    parser.add_argument("--run-id", default=feedback.DEFAULT_RUN_ID)
    parser.add_argument("--attempt-id", default=feedback.DEFAULT_ATTEMPT_ID)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args(argv)
    feedback_environment = {
        feedback.ENV_OUT: str(args.out.resolve()),
        feedback.ENV_RUN_ID: args.run_id,
        feedback.ENV_ATTEMPT_ID: args.attempt_id,
    }

    def read_input(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def input_failure(error):
        record_operation_failure(error, "company.input", code="company_input_unreadable",
                                 directory=args.out.resolve().parent, run_id=args.run_id,
                                 attempt_id=args.attempt_id, sidecar=args.out,
                                     feedback_environment=feedback_environment)
        print(json.dumps({"ok": False, "code": "company_input_unreadable"}))
        return 2

    receipts = None
    if args.receipts is not None:
        try:
            receipts = read_input(args.receipts)
        except (OSError, ValueError) as error:
            return input_failure(error)
    config = {
        # Both roots are resolved here: the owner command runs with the
        # StockWiki checkout as its working directory, so a relative owner
        # workspace would silently point at the wrong store.
        "stockwiki_root": str(args.stockwiki_root.resolve()) if args.stockwiki_root else "",
        "workspace_root": str(args.workspace_root.resolve()) if args.workspace_root else "",
        "stockwiki_python": args.stockwiki_python,
        "timeout_seconds": args.timeout_seconds,
    }
    payload = {"entity_id": args.entity}
    if args.result_id:
        payload["result_id"] = args.result_id
    injected = args.inject_result is not None
    if injected:        # A temporary public response: the saved snapshot is placed where the
        # owner's read would put it, and the same projection and checks run.
        try:
            result = read_input(args.inject_result)
            if not isinstance(result, dict):
                raise ValueError("unsupported_company_input")
        except (OSError, ValueError) as error:
            return input_failure(error)
        payload["entity_id"] = args.entity or result.get("entity_id")
        envelope = {
            "protocol": projection.PROJECTION_PROTOCOL,
            "projection_version": projection.PROJECTION_VERSION,
            "entity_id": payload["entity_id"],
            "read": "result",
            "owner_payload": {
                "protocol": projection.OWNER_PROTOCOL,
                "schema_version": projection.OWNER_SCHEMA_VERSION,
                "store_id": "qsobs_injected",
                "registry_store_id": "qsca_injected",
                "result": result,
                "reason_code": None,
                "network_calls": 0,
                "llm_calls": 0,
            },
            "network_calls": 0,
            "llm_calls": 0,
        }
    else:
        if not args.entity:
            parser.error("--entity is required when reading the owner")
        if not args.stockwiki_root or not args.workspace_root:
            parser.error("--stockwiki-root and --workspace-root are required when reading the owner")
        # The public read emits its own observations; point it at this output
        # once instead of writing the same read twice.
        before = _line_count(args.out)
        try:
            envelope = projection.read_company_assessment(
                config, "company_result", payload, question_receipts=receipts,
                feedback_environment=feedback_environment)
        except projection.ProjectionError as error:
            record_operation_failure(error, "company.result", code=error.code, refusal=error.status < 500,
                                     directory=args.out.resolve().parent, run_id=args.run_id, attempt_id=args.attempt_id,
                                     sidecar=args.out, feedback_environment=feedback_environment)
            print(json.dumps({"ok": False, "code": error.code, "status": error.status}))
            return 2

    try:
        projected = projection.project_result(envelope, question_receipts=receipts)
    except projection.ProjectionError as error:
        record_operation_failure(error, "company.projection", code=error.code, refusal=error.status < 500,
                                 directory=args.out.resolve().parent, run_id=args.run_id, attempt_id=args.attempt_id,
                                 sidecar=args.out)
        print(json.dumps({"ok": False, "code": error.code, "status": error.status}))
        return 2
    rows = feedback.observations(projected, read="result", receipts=receipts,
                                 run_id=args.run_id, attempt_id=args.attempt_id,
                                 version=projection.PROJECTION_VERSION)
    if injected:
        context = feedback.Context(out_path=args.out, run_id=args.run_id,
                                   attempt_id=args.attempt_id,
                                   version=projection.PROJECTION_VERSION)
        if not feedback.emit(context, rows):
            return 3
    elif _line_count(args.out) - before != len(rows):
        # The read ran, but the observation file did not receive this read's
        # rows: that is a tracking fault, not a business result.
        return 3
    coverage = projected.get("coverage") or {}
    result = projected.get("company_result") or {}
    print(json.dumps({
        "ok": True,
        "injected": injected,
        "result_id": result.get("result_id"),
        "reason_code": projected.get("reason_code"),
        "verdict": coverage.get("verdict"),
        "claim_matches_refs": coverage.get("claim_matches_refs"),
        "missing_question_ids": coverage.get("missing_question_ids"),
        "scale_versions": coverage.get("scale_versions"),
        "observations": len(rows),
    }, ensure_ascii=False))
    return 0
