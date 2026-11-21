"""Publish and verify a corrected scan coverage receipt using only the saved run."""

from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

from . import scan_result_check as check
from ..foundation.api import RuntimeArgumentParser, read_operation_failure, read_process_log

OWNER = check.OWNER
ISSUE = "F2-IQS-0001"
NEW_USAGE = {"new_model_calls": 0, "new_searches": 0, "new_cost_micros": 0}
ACTIONS = ("triage", "repair", "replay", "report", "reconcile")
OBSERVATION_IDENTITY = (
    "owner",
    "origin_owner",
    "run_id",
    "attempt_id",
    "step_id",
    "check_id",
)


class Unavailable(ValueError):
    """This action has no authoritative result to record."""


def _encode(value):
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _digest(value):
    return sha256(_encode(value).encode("ascii")).hexdigest()


def _key(kind, *scope):
    return _digest([kind, OWNER, *scope])


def _sha(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _payload(request, command):
    if not isinstance(request, dict) or (
        request.get("schema_version"),
        request.get("owner"),
        request.get("kind"),
        request.get("method"),
    ) != (
        "feedback-action/1",
        OWNER,
        command,
        "lookup" if command == "reconcile" else "submit",
    ):
        raise ValueError("invalid_action")
    payload = request.get("payload")
    key = request.get("action_id")
    if not isinstance(payload, dict) or not _sha(key):
        raise ValueError("invalid_action")
    occurrence = payload.get("occurrence_id")
    issue = payload.get("issue_ref")
    if command in ("triage", "reconcile"):
        scope = [occurrence]
    elif command == "repair":
        scope = [issue, payload.get("generation")]
    else:
        scope = [occurrence, OWNER, issue, payload.get("fixed_version")]
        if command == "report":
            scope.append(payload.get("verdict"))
    if key != _key(command, *scope) or request["request_digest"] != _digest(
        [OWNER, command, key, payload]
    ):
        raise ValueError("invalid_action_binding")
    return payload


def _observation(payload):
    row = payload.get("observation")
    if not isinstance(row, dict):
        raise ValueError("missing_observation")
    identity = [row.get(field) for field in OBSERVATION_IDENTITY]
    if (
        not all(isinstance(value, str) and value.strip() for value in identity)
        or _digest(identity) != payload["occurrence_id"]
    ):
        raise ValueError("observation_binding_mismatch")
    return row


def _native(runs_root, row):
    """Resolve an opaque, source-bound reference below the owner's configured root."""
    if not isinstance(row, dict) or row.get("origin_owner") != OWNER:
        return None
    ref = row.get("evidence_ref", "")
    run, separator, source_sha = (
        ref.rpartition("@") if isinstance(ref, str) else ("", "", "")
    )
    run_id = row.get("run_id")
    if not (
        isinstance(run_id, str)
        and run_id
        and run == f"{check.REFERENCE_PREFIX}{run_id}"
        and separator
        and _sha(source_sha)
        and row.get("step_id") == f"scan-result/{run_id}"
    ):
        return None
    try:
        root = runs_root.resolve()
        path = (root / run_id).resolve()
        if path.relative_to(root).as_posix() != run_id:
            return None
        if any((path / name).resolve().parent != path for name in check.REQUIRED_FILES):
            return None
        native = check.inspect_run(path)
    except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
        return None
    if native.source_sha256 != source_sha or not native.report["ok"]:
        return None
    return native


def _triage(runs_root, payload):
    row = _observation(payload)
    native = _native(runs_root, row)
    if native is None:
        return {"decision": "needs_evidence"}
    if row.get("issue_key") != check.COVERAGE_ISSUE:
        return (
            {"decision": "expected"}
            if row.get("expected") == row.get("actual")
            else {"decision": "needs_evidence"}
        )
    if (
        row.get("check_id"),
        row.get("expected"),
        row.get("actual"),
        native.report["coverage"],
    ) != (
        "coverage-claim",
        "partial-marked",
        "complete-claimed",
        "partial",
    ):
        return {"decision": "needs_evidence"}
    return {
        "decision": "repair",
        "issue_ref": ISSUE,
        "generation": payload["occurrence_id"],
        "gate_review": {
            "decision": "narrow",
            "reason": "Compare full-result claims to the frozen bank and keep usable partial evidence visible.",
            "evidence_ref": row["evidence_ref"],
        },
    }


def _reconcile(runs_root, payload):
    row = _observation(payload)
    native = _native(runs_root, row)
    return {
        "state": "done",
        "result": {
            "status": "cost_unknown",
            "job_status": "succeeded" if native else "unconfirmed",
            "cost_state": "unknown",
            "evidence_ref": row.get("evidence_ref", "iqs:scan/unconfirmed"),
            "recorded_search_cost_micros": (
                native.search_cost_micros if native else None
            ),
            **NEW_USAGE,
        },
    }


def _view(native, row):
    fields = (
        "coverage",
        "question_count",
        "manifest_question_count",
        "missing_question_count",
        "missing_question_ids",
        "scored",
        "usable",
        "ok",
        "model_calls",
        "searches",
    )
    return {
        "schema_version": "iqs-scan-coverage/1",
        "run_id": row["run_id"],
        "attempt_id": row["attempt_id"],
        "source_sha256": native.source_sha256,
        "historical_cost_state": "unknown",
        "recorded_search_cost_micros": native.search_cost_micros,
        **NEW_USAGE,
        **{field: native.report[field] for field in fields},
    }


def _get(connection, key):
    saved = connection.execute(
        "SELECT receipt FROM actions WHERE action_id=?", (key,)
    ).fetchone()
    return json.loads(saved[0]) if saved else None


def _repair(connection, runs_root, payload, action_id):
    triaged = _get(connection, _key("triage", payload["generation"]))
    if (
        not triaged
        or triaged["result"].get("decision") != "repair"
        or payload["issue_ref"] != ISSUE
    ):
        raise Unavailable("repair_scope_unconfirmed")
    row = triaged["request"]["payload"]["observation"]
    native = _native(runs_root, row)
    if native is None:
        raise Unavailable("native_run_unconfirmed")
    coverage = _view(native, row)
    return {
        "fixed_version": f"iqs-scan-coverage/1/{_digest(coverage)}",
        "evidence_ref": f"iqs:scan-check/{action_id}",
        "coverage": coverage,
    }


def _replay(connection, runs_root, payload):
    repaired = _get(
        connection, _key("repair", payload["issue_ref"], payload["occurrence_id"])
    )
    if (
        payload.get("acquisition") != "reuse_only"
        or payload.get("issue_owner") != OWNER
        or not repaired
    ):
        return {"verdict": "unknown"}
    published = repaired["result"]
    row = _observation(payload)
    native = _native(runs_root, row)
    if native is None or published["fixed_version"] != payload["fixed_version"]:
        return {"verdict": "unknown"}
    expected = _view(native, row)
    verdict = (
        "verified"
        if published["coverage"] == expected and expected["coverage"] == "partial"
        else "regressed"
    )
    return {
        "verdict": verdict,
        "verified_version": payload["fixed_version"],
        "evidence_ref": published["evidence_ref"],
        **NEW_USAGE,
    }


def _report(connection, payload):
    saved = _get(
        connection,
        _key(
            "replay",
            payload["occurrence_id"],
            OWNER,
            payload["issue_ref"],
            payload["fixed_version"],
        ),
    )
    expected = (payload["verdict"], payload["fixed_version"], payload["evidence_ref"])
    if (
        not saved
        or payload["origin_owner"] != OWNER
        or (
            saved["request"]["payload"]["original_occurrence_id"]
            != payload["original_occurrence_id"]
        )
        or tuple(
            saved["result"].get(key)
            for key in ("verdict", "verified_version", "evidence_ref")
        )
        != expected
    ):
        raise Unavailable("replay_unconfirmed")
    return {"recorded": True, **payload}


def _submit(db, runs_root, request, kind, payload):
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db, timeout=10)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS actions (action_id TEXT PRIMARY KEY, receipt TEXT NOT NULL)"
        )
        connection.execute("BEGIN IMMEDIATE")
        action_id = request["action_id"]
        saved = _get(connection, action_id)
        if saved:
            if saved["request"] != request:
                raise ValueError("action_conflict")
            return {"result": saved["result"]}
        if kind == "triage":
            result = _triage(runs_root, payload)
        elif kind == "repair":
            result = _repair(connection, runs_root, payload, action_id)
        elif kind == "replay":
            result = _replay(connection, runs_root, payload)
        else:
            result = _report(connection, payload)
        connection.execute(
            "INSERT INTO actions VALUES (?, ?)",
            (action_id, _encode({"request": request, "result": result})),
        )
        return {"result": result}


def _lookup(db, key, command):
    if not _sha(key) or not db.is_file():
        return {}
    with closing(
        sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    ) as connection:
        receipt = _get(connection, key)
    if receipt and command == "get-action":
        return {"receipt": receipt}
    if receipt and receipt["request"]["kind"] == "repair":
        return {"coverage": receipt["result"]["coverage"]}
    return {}


def main(argv=None):
    parser = RuntimeArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--runs-root", type=Path)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ACTIONS:
        subs.add_parser(command)
    for command in ("get-action", "get-coverage"):
        subs.add_parser(command).add_argument("action_id")
    for command in ("get-diagnostic", "republish-diagnostic"):
        reader = subs.add_parser(command)
        reader.add_argument("reference")
        reader.add_argument("--state-root", type=Path)
    log_reader = subs.add_parser("get-process-log", help="Read a page of the original UTF-8 diagnostic log")
    log_reader.add_argument("reference")
    log_reader.add_argument("--state-root", type=Path, required=True)
    log_reader.add_argument("--offset", type=int, default=0)
    log_reader.add_argument("--limit", type=int, default=65536)
    log_reader.add_argument("--tail-bytes", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "get-process-log":
            reply = {"log": read_process_log(args.state_root, args.reference, offset=args.offset,
                                             limit=args.limit, tail_bytes=args.tail_bytes)}
        elif args.command in ("get-diagnostic", "republish-diagnostic"):
            if args.state_root is None and args.runs_root is None:
                parser.error("supply --state-root or --runs-root to locate the saved diagnostic")
            root = args.state_root or args.runs_root / "dashboard-runtime"
            reply = {"diagnostic": read_operation_failure(
                root, args.reference, republish=args.command == "republish-diagnostic"
            )}
        elif args.db is None or args.runs_root is None:
            parser.error("this action requires --db and --runs-root")
        elif args.command in ("get-action", "get-coverage"):
            reply = _lookup(args.db, args.action_id, args.command)
        else:
            request = json.load(sys.stdin)
            payload = _payload(request, args.command)
            if args.command == "reconcile":
                reply = _reconcile(args.runs_root, payload)
            else:
                reply = _submit(args.db, args.runs_root, request, args.command, payload)
    except Unavailable as error:
        print(_encode({"code": str(error), "state": "unknown"}))
        return 2
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        sqlite3.Error,
    ) as error:
        code = str(error) if type(error) is ValueError else type(error).__name__
        print(_encode({"code": code}))
        return 2
    print(_encode(reply))
    return 0
