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
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except (OSError, TypeError, ValueError) as error:
        diagnose_feedback(error)
        return False
    return True
