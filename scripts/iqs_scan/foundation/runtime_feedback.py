"""Durable IQS runtime diagnostics and the public F4 occurrence produced from each."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

from .feedback_io import FEEDBACK_SCHEMA, append_feedback
from .json_io import atomic_write_json, physical_path
from .runtime_log import append_operation_failure

OWNER = "invest-quick-scan"
DEFAULT_STATE_ROOT = Path(__file__).resolve().parents[3] / "runs" / "dashboard-runtime"
REFERENCE = "iqs:diagnostic/"
_SCOPE = ContextVar("iqs_operation_scope", default=(None, None))


def operation_identifiers(run_id=None, attempt_id=None):
    inherited_run, inherited_attempt = _SCOPE.get()
    run = _scope(os.environ.get("RESEARCH_FEEDBACK_RUN_ID") or run_id or inherited_run, "run-" + uuid.uuid4().hex)
    attempt = _scope(os.environ.get("RESEARCH_FEEDBACK_ATTEMPT_ID") or attempt_id or inherited_attempt,
                     "attempt-" + uuid.uuid4().hex)
    return run, attempt


def child_feedback_environment(run_id=None, attempt_id=None):
    """Return this child's public tracing fields without changing the process environment."""
    run, attempt = operation_identifiers(run_id, attempt_id)
    fields = {"RESEARCH_FEEDBACK_RUN_ID": run, "RESEARCH_FEEDBACK_ATTEMPT_ID": attempt}
    for key in ("RESEARCH_FEEDBACK_OUT", "RESEARCH_FEEDBACK_DIR"):
        if os.environ.get(key):
            fields[key] = os.environ[key]
    return fields


@contextmanager
def operation_scope(run_id=None, attempt_id=None):
    token = _SCOPE.set(operation_identifiers(run_id, attempt_id))
    try:
        yield
    finally:
        _SCOPE.reset(token)


def _record_from_exception(error):
    """An outer catch returns the original owner's existing diagnostic."""
    seen = set()
    pending = [error]
    while pending:
        current = pending.pop()
        if not isinstance(current, BaseException) or id(current) in seen:
            continue
        seen.add(id(current))
        attrs = BaseException.__dict__["__dict__"].__get__(current)
        details = attrs.get("details")
        if type(details) is dict:
            saved = details.get("failure_diagnostic")
            if (type(saved) is dict and saved.get("recorded") and type(saved.get("observation")) is dict
                    and saved["observation"].get("owner") == OWNER):
                return saved
        pending.extend((BaseException.__context__.__get__(current), BaseException.__cause__.__get__(current)))
    return None


def operation_state_root(runs_root=None):
    """Locate the same native diagnostics for direct commands and owner lookups."""
    root = runs_root or os.environ.get("IQS_FEEDBACK_RUNS_ROOT")
    return Path(root) / "dashboard-runtime" if root else DEFAULT_STATE_ROOT


class RuntimeArgumentParser(argparse.ArgumentParser):
    """Keep argparse's on-screen diagnostics; capture the refusal without its raw arguments."""

    def error(self, message):
        record_operation_failure(None, "cli.arguments", code="invalid_arguments", refusal=True,
                                 directory=operation_state_root())
        super().error(message)


def _tracking_incomplete():
    try:
        print("IQS failure tracking incomplete", file=sys.stderr)
    except (ValueError, OSError):
        pass


def exception_diagnostic(error):
    """Only native exception relations and source coordinates; never messages, locals or arguments."""
    chain = []
    pending = [("raised", error)]
    seen = set()
    while pending:
        relation, current = pending.pop()
        if not isinstance(current, BaseException) or id(current) in seen:
            continue
        seen.add(id(current))
        name = type.__getattribute__(type(current), "__name__")
        item = {"relation": relation, "type": name, "frames": []}
        tb = BaseException.__traceback__.__get__(current)
        while tb is not None:
            code = tb.tb_frame.f_code
            item["frames"].append({"file": Path(code.co_filename).name,
                                   "function": code.co_name, "line": tb.tb_lineno})
            tb = tb.tb_next
        if isinstance(current, OSError):
            item["family"] = "OSError"
            number = OSError.errno.__get__(current)
            if type(number) is int:
                item["errno"] = number
        chain.append(item)
        pending.append(("context", BaseException.__context__.__get__(current)))
        pending.append(("cause", BaseException.__cause__.__get__(current)))
    return {"chain": chain}


def _scope(raw, default):
    if not isinstance(raw, str) or not raw:
        return default
    if re.fullmatch(r"[a-zA-Z0-9_.:/-]+", raw) and not any(x in raw for x in ("..", "://", ":/")):
        return raw
    return "ref-" + hashlib.sha256(raw.encode("utf8")).hexdigest()


def _outbox(directory):
    override = os.environ.get("RESEARCH_FEEDBACK_DIR")
    return Path(override) if override else directory / "observations"


def _publish(record, directory, key, sidecar=None):
    row = record["observation"]
    explicit = sidecar or os.environ.get("RESEARCH_FEEDBACK_OUT")
    if explicit:
        return append_feedback(Path(explicit), [row])
    stem = _outbox(directory) / ("feedback-" + key)
    atomic_write_json(stem.with_suffix(".jsonl"), row)
    marker = {field: row[field] for field in ("owner", "run_id", "attempt_id", "step_id")}
    atomic_write_json(stem.with_suffix(".ready"), marker)
    return True


def _diagnostic_path(directory, reference):
    match = re.fullmatch(re.escape(REFERENCE) + "([0-9a-f]{32})", reference)
    if not match:
        raise ValueError("invalid_diagnostic_reference")
    return physical_path(directory / "diagnostics" / (match[1] + ".jsonl"))


def read_operation_failure(directory, reference, *, republish=False):
    """Read or re-deliver the original diagnostic. Neither action re-runs the failed work."""
    path = _diagnostic_path(Path(directory), reference)
    record = json.loads(path.read_text(encoding="utf8"))
    if record["observation"]["details_ref"] != reference:
        raise ValueError("diagnostic_reference_mismatch")
    if republish and not record.get("feedback_recorded"):
        record["feedback_recorded"] = _publish(record, path.parent.parent, path.stem)
        if record["feedback_recorded"]:
            atomic_write_json(path, record)
    return record


def read_runs_failure(runs_root, reference, *, republish=False):
    """Older explicit runs roots stored diagnostics beside the business runs."""
    try:
        return read_operation_failure(operation_state_root(runs_root), reference, republish=republish)
    except FileNotFoundError:
        return read_operation_failure(runs_root, reference, republish=republish)


def record_operation_failure(error, stage, *, directory=None, code="execution_failed",
                             run_id=None, attempt_id=None, refusal=False,
                             disposition="deviation", evidence_ref=None, sidecar=None,
                             substep=None):
    """Best-effort capture at the owner boundary; diagnostics never own payment or work state."""
    result = {"recorded": False, "feedback_recorded": False}
    local_record = None
    try:
        prior = _record_from_exception(error)
        if prior is not None:
            return prior
        root = Path(directory) if directory is not None else operation_state_root()
        original_run, original_attempt = _SCOPE.get()
        run_id = run_id or original_run
        attempt_id = attempt_id or original_attempt
        run, attempt = operation_identifiers(run_id, attempt_id)
        stage = _scope(stage, "operation")
        step = stage + "/" + _scope(substep, "substep") if substep else stage
        code = code if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", code) else "execution_failed"
        identity = [OWNER, run, attempt, step, "operation-outcome"]
        key = uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(identity, ensure_ascii=True)).hex
        reference = REFERENCE + key
        result.update({"details_ref": reference})
        path = _diagnostic_path(root, reference)
        if path.is_file():
            return read_operation_failure(root, reference, republish=True)
        row = {"schema_version": FEEDBACK_SCHEMA, "owner": OWNER, "origin_owner": OWNER,
               "run_id": run, "attempt_id": attempt, "step_id": step, "check_id": "operation-outcome",
               "expected": "completed", "actual": code, "disposition": disposition,
               "issue_key": "iqs-runtime/" + stage + "/" + code, "version": "iqs-runtime/1",
               "evidence_ref": evidence_ref or reference, "details_ref": reference}
        if refusal:
            row["refusal_code"] = code
        result.update(exception_diagnostic(error) if error is not None else {"chain": []})
        local_record = (root, row, result["chain"])
        record = {**result, "recorded": True, "observation": row}
        if run_id:
            record["native_run_id"] = _scope(run_id, run)
        if attempt_id:
            record["native_attempt_id"] = _scope(attempt_id, attempt)
        try:
            atomic_write_json(path, record)
        except OSError:
            # Storage and outbox are independent destinations. If the native
            # write fails, publish only references which actually exist.
            row.pop("details_ref")
            if not evidence_ref:
                row.pop("evidence_ref")
            result.pop("details_ref")
            result["feedback_recorded"] = _publish({"observation": row}, root, key, sidecar)
            _tracking_incomplete()
            return result
        result = record
        result["feedback_recorded"] = _publish(record, root, key, sidecar)
        if result["feedback_recorded"]:
            atomic_write_json(path, result)
        else:
            _tracking_incomplete()
    except Exception:
        # Optional reporting must also tolerate broken exception introspection,
        # clocks, JSON encoding, rich custom exception attributes and storage I/O.
        _tracking_incomplete()
    finally:
        if local_record is not None:
            try:
                append_operation_failure(*local_record)
            except Exception:
                _tracking_incomplete()
    return result
