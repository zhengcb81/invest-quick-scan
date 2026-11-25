"""Rotating owner-local log for IQS failure facts, independent of F4 delivery."""

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


def append_operation_failure(directory, observation, chain):
    """Write only already-projected identifiers and structural error facts."""
    log_path = physical_path(directory / "runtime-failures.jsonl")
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    payload = {"schema_version": "iqs-runtime-log/1", "timestamp_utc": now.replace("+00:00", "Z"),
               "owner": observation["owner"], "run_id": observation["run_id"],
               "attempt_id": observation["attempt_id"], "step_id": observation["step_id"],
               "code": observation["actual"], "chain": chain}
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
