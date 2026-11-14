"""Small, redacted diagnostics shared by the unknown-intent native E2E."""
import json
import os
from pathlib import Path
import re
import traceback


_FIELDS = frozenset(
    {
        "phase",
        "execute_returned",
        "execute_exception_type",
        "execute_cause_chain",
        "summary",
        "checkpoint_exists",
        "checkpoint_sha256",
        "pending_intent_present",
        "pending_intent_kind",
        "pending_receipt_present",
        "pending_receipt_outcome",
        "pending_receipt_reason_code",
        "pending_receipt_final_content_present",
        "pending_receipt_tool_calls_present",
        "export_exists",
        "recovery_decision",
        "recovery_reason",
        "saved_receipt_present",
        "resume_returned",
        "resume_exception_type",
        "resume_cause_chain",
        "resume_reason_code",
        "recovered_session_exists",
        "recovered_export_exists",
        "wire_post_count",
        "child_exception_type",
        "child_cause_chain",
    }
)
_SUMMARY_FIELDS = frozenset(
    {"status", "all_slots_completed", "runtime_summary_present", "new_model_http", "replayed_native_attempts"}
)


def write_child_diagnostic(destination_path, payload):
    """Persist only allowlisted control-flow evidence, never request material."""
    safe = {key: value for key, value in payload.items() if key in _FIELDS}
    summary = safe.get("summary")
    if isinstance(summary, dict):
        safe["summary"] = {key: value for key, value in summary.items() if key in _SUMMARY_FIELDS}
    if safe.get("pending_receipt_outcome") not in {
        "response_available", "rejected", "outcome_unknown"
    }:
        safe.pop("pending_receipt_outcome", None)
    reason_code = safe.get("pending_receipt_reason_code")
    if not isinstance(reason_code, str) or not re.fullmatch(
        r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", reason_code
    ):
        safe.pop("pending_receipt_reason_code", None)
    for field in (
        "pending_receipt_final_content_present",
        "pending_receipt_tool_calls_present",
    ):
        if type(safe.get(field)) is not bool:
            safe.pop(field, None)
    for field in ("execute_cause_chain", "resume_cause_chain", "child_cause_chain"):
        chain = safe.get(field)
        sanitized = []
        if isinstance(chain, list):
            for item in chain[:8]:
                if not isinstance(item, dict):
                    continue
                row = {}
                for key in ("module", "class"):
                    value = item.get(key)
                    if isinstance(value, str) and len(value) <= 160:
                        row[key] = value
                code = item.get("stable_error_code")
                if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", code):
                    row["stable_error_code"] = code
                frames = []
                for frame in item.get("frames", [])[:20] if isinstance(item.get("frames"), list) else []:
                    if not isinstance(frame, dict):
                        continue
                    frame_path = frame.get("path")
                    function = frame.get("function")
                    line = frame.get("line")
                    if isinstance(frame_path, str) and isinstance(function, str) and type(line) is int:
                        frames.append({"path": frame_path[:240], "function": function[:160], "line": line})
                row["frames"] = frames
                sanitized.append(row)
        safe[field] = sanitized
    encoded = json.dumps(safe, sort_keys=True, separators=(",", ":"), allow_nan=False)
    destination = Path(destination_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    with temporary.open("w", encoding="utf8", newline="\n") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, destination)


def exception_cause_chain(error, roots):
    """Extract exception identities and local frames without exception text.

    ``roots`` is an ordered iterable of (short-name, absolute-path) pairs.
    Messages are kept only when they are complete stable snake-case codes.
    """
    chain = []
    seen = set()
    current = error
    while current is not None and id(current) not in seen and len(chain) < 8:
        seen.add(id(current))
        cls = type(current)
        row = {"module": cls.__module__, "class": cls.__name__, "frames": []}
        message = str(current)
        if re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", message):
            row["stable_error_code"] = message
        for frame in traceback.extract_tb(current.__traceback__)[-20:]:
            try:
                filename = Path(frame.filename).resolve()
            except (OSError, RuntimeError, ValueError):
                continue
            for prefix, base_path in roots:
                try:
                    relative = filename.relative_to(Path(base_path).resolve())
                except (OSError, RuntimeError, ValueError):
                    continue
                row["frames"].append(
                    {"path": prefix + "/" + relative.as_posix(), "function": frame.name, "line": frame.lineno}
                )
                break
        chain.append(row)
        current = current.__cause__ or current.__context__
    return chain
