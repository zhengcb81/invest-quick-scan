"""Rotating owner-local IQS trace, independent of F4 delivery."""

from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import time

from .file_lock import ControlBusyError, control_lock
from .json_io import physical_path


class _LocalHandler(RotatingFileHandler):
    def handleError(self, record):
        error = sys.exc_info()[1]
        if error is not None:
            raise error

    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            # A Windows reader can temporarily block rename; keep the next row.
            pass


def _append(directory, filename, payload):
    log_path = physical_path(directory / filename)
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    payload = {"schema_version": "iqs-runtime-log/1", "timestamp_utc": now, **payload}
    line = json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    deadline = time.monotonic() + 0.4
    while True:
        try:
            with control_lock(log_path.with_suffix(".lock")):
                # A terminated writer may have left a partial final line.
                with log_path.open("a+b") as stream:
                    if stream.seek(0, os.SEEK_END):
                        stream.seek(-1, os.SEEK_END)
                        if stream.read(1) != b"\n":
                            stream.write(b"\n")
                handler = _LocalHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=2,
                                        encoding="utf-8", delay=True)
                try:
                    handler.handle(logging.LogRecord(__name__, logging.ERROR, "", 0, line, (), None))
                finally:
                    handler.close()
            return
        except ControlBusyError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def append_operation_failure(directory, observation, chain, owned):
    """Write only already-projected identifiers and structural error facts."""
    payload = {key: observation[key] for key in ("owner", "run_id", "attempt_id", "step_id")}
    payload.update(state="failed", code=observation["actual"], chain=chain)
    payload["version"] = observation["version"]
    if owned:
        payload.update(native_run_id=owned[0], native_attempt_id=owned[1])
    if observation.get("details_ref"):
        payload["details_ref"] = observation["details_ref"]
    _append(directory, "runtime-failures.jsonl", payload)


def append_operation_checkpoint(directory, payload):
    _append(directory, "runtime-events.jsonl", payload)


def read_operation_trace(directory, owner, run, attempt):
    """Read the retained owner trace without locks, retries or feedback writes."""
    events = []
    for filename in ("runtime-events.jsonl", "runtime-failures.jsonl"):
        for suffix in (".2", ".1", ""):
            path = physical_path(directory / (filename + suffix))
            try:
                with path.open("rb") as stream:
                    for line in stream:
                        try:
                            row = json.loads(line)
                        except (ValueError, RecursionError):
                            continue  # A killed writer may leave a torn final row.
                        if (isinstance(row, dict) and isinstance(row.get("timestamp_utc"), str)
                                and row.get("owner") == owner and (run, attempt) in (
                                    (row.get("run_id"), row.get("attempt_id")),
                                    (row.get("native_run_id"), row.get("native_attempt_id")),
                                )):
                            try:
                                instant = datetime.fromisoformat(row["timestamp_utc"])
                            except ValueError:
                                continue
                            if instant.tzinfo is None:
                                continue
                            row.setdefault("state", "failed")
                            events.append((instant, row))
            except FileNotFoundError:
                continue
    return [row for _, row in sorted(events, key=lambda entry: entry[0])]
