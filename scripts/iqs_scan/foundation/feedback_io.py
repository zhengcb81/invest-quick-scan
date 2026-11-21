"""Common optional feedback sidecar output for the IQS producers."""

import json
import os
from pathlib import Path
import sys

FEEDBACK_SCHEMA = "feedback-observation/1"
FEEDBACK_OUT_ENV = "RESEARCH_FEEDBACK_OUT"
FEEDBACK_RUN_ENV = "RESEARCH_FEEDBACK_RUN_ID"
FEEDBACK_ATTEMPT_ENV = "RESEARCH_FEEDBACK_ATTEMPT_ID"


def feedback_path(environ=None):
    environ = os.environ if environ is None else environ
    raw = environ.get(FEEDBACK_OUT_ENV)
    return Path(raw).expanduser() if isinstance(raw, str) and raw.strip() else None


def diagnose_feedback(error):
    if isinstance(error, OSError):
        message = f"feedback observation write failed: {error.strerror or 'output unavailable'}"
    else:
        message = f"feedback observation skipped ({error.__class__.__name__})"
    try:
        print(message, file=sys.stderr)
    except (OSError, ValueError):
        pass


def append_feedback(path, rows):
    """Append self-contained rows without changing the business result on failure."""
    try:
        payload = "".join(
            json.dumps(
                {"schema_version": FEEDBACK_SCHEMA, **row},
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
            for row in rows
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+b") as handle:
            separator = b""
            if handle.seek(0, os.SEEK_END):
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    separator = b"\n"
            handle.write(separator + payload.encode("utf8"))
            handle.flush()
            os.fsync(handle.fileno())
    except (OSError, TypeError, ValueError) as error:
        diagnose_feedback(error)
        return False
    return True
