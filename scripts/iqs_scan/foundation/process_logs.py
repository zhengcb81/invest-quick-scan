"""Process diagnostic streams: normalize Windows output and read one bounded display page at a time."""
from __future__ import annotations

import codecs
import io
import json
from pathlib import Path
import re
import uuid

from .json_io import atomic_write_json, physical_path


PREFIX = "iqs:process-log/"


def decoded_output_lines(stream):
    """Yield complete lines, preserving secrets split across binary reads for redaction."""
    if not isinstance(stream, (io.BufferedIOBase, io.RawIOBase)):
        yield from stream
        return
    first = stream.read(4)
    encoding = "utf-8-sig"
    if first.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        encoding = "utf-32"
    elif first.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    # A redirected Windows process may emit UTF-16/32 ASCII-led text without a BOM.
    elif len(first) == 4 and first[:3] == b"\0\0\0":
        encoding = "utf-32-be"
    elif len(first) == 4 and first[1:] == b"\0\0\0":
        encoding = "utf-32-le"
    elif len(first) >= 4 and first[0] == first[2] == 0:
        encoding = "utf-16-be"
    elif len(first) >= 4 and first[1] == first[3] == 0:
        encoding = "utf-16-le"

    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    read = getattr(stream, "read1", stream.read)
    chunk = first
    pieces = []
    while True:
        text = decoder.decode(chunk, final=not chunk)
        sections = text.split("\n")
        for finished in sections[:-1]:
            pieces.append(finished)
            yield "".join(pieces) + "\n"
            pieces.clear()
        if sections[-1]:
            pieces.append(sections[-1])
        if not chunk:
            break
        chunk = read(64 * 1024)
    if pieces:
        yield "".join(pieces)


_NAMED_CREDENTIAL = re.compile(
    r"""(?ix)
    (?P<label>(?<!\w)["']?(?:[a-z0-9]+[-_])*
        (?:api[-_]?key|access[-_]?key|private[-_]?key|password|passwd|pwd|key|secret|
           token|authorization|credential)["']?[ \t]*[:=][ \t]*)
    (?P<value>\[REDACTED\]|"(?:\\.|[^"\\\r\n])*"|'(?:\\.|[^'\\\r\n])*'|
               (?:basic|bearer)[ \t]+[^\s&,;}\]]+|[^\s&,;}\]"']+)
    """
)
_AUTH_VALUE = re.compile(r"(?i)(?:\b(?:sk-|tvly-|gh[pousr]_|AIza)[a-z0-9_.-]{6,}|\b(?:basic|bearer)[ \t]+[a-z0-9_./+=-]{6,})")
_URL_USERINFO = re.compile(r"(?i)(https?://)[^/\s@]+@")
_AUTH_FIELD = r"\b(?:proxy[-_])?authorization[ \t]*:[ \t]*"
_AUTH_SCHEME = r"(?:bearer|basic)"
_AUTH_HEADER = re.compile(rf"(?i){_AUTH_FIELD}{_AUTH_SCHEME}(?=[ \t\r\n]|$)")
_RENDERED_AUTH_FOLD = re.compile(
    rf"(?i)({_AUTH_FIELD}){_AUTH_SCHEME}"
    r"(?:[ \t]+[^\s\\\"']+)?[ \t]*"
    r"(?:(?:\\r\\n|\\[rn])(?:[ \t]|\\t)+[^\s\\\"'][^\\\r\n\"']*)+"
)
_PRIVATE_START = re.compile(r"-----BEGIN [^-\n]*PRIVATE KEY-----")
_PRIVATE_END = re.compile(r"-----END [^-\n]*PRIVATE KEY-----")


def _hide_field(match):
    value = match["value"]
    quote = value[0] if value.startswith(("'", '"')) else ""
    return match["label"] + quote + "[REDACTED]" + quote


def redacted_output_lines(stream, secrets):
    """Filter credentials before either live display or durable output sees them."""
    inside_key = False
    authorization = False
    for line in decoded_output_lines(stream):
        if authorization and line.startswith((" ", "\t")) and line.strip():
            tail = line[len(line.rstrip("\r\n")):]
            line = "[REDACTED]" + tail
        else:
            authorization = bool(_AUTH_HEADER.search(line))
        start = _PRIVATE_START.search(line)
        if start or inside_key:
            end = _PRIVATE_END.search(line)
            inside_key = end is None
            before = line[:start.start()] if start else ""
            after = line[end.end():] if end else ("\n" if line.endswith("\n") else "")
            line = before + "[REDACTED]" + after
        for secret in secrets:
            line = line.replace(secret, "[REDACTED]")
        line = _RENDERED_AUTH_FOLD.sub(r"\1[REDACTED]", line)
        line = _NAMED_CREDENTIAL.sub(_hide_field, line)
        line = _AUTH_VALUE.sub("[REDACTED]", line)
        yield _URL_USERINFO.sub(r"\1[REDACTED]@", line)


def redact_diagnostic_text(text):
    """Apply the same credential projection to a diagnostic string."""
    return "".join(redacted_output_lines(io.StringIO(text, newline=""), ()))


def register_process_log(state_root, log_path, run_id):
    """Bind an original owner-created log under its state root; never copy its contents."""
    root = physical_path(state_root).resolve()
    try:
        relative = physical_path(log_path).resolve().relative_to(root)
        if relative.suffix != ".log":
            return None
        relative_name = relative.as_posix()
        identity = json.dumps([run_id, relative_name], ensure_ascii=True)
        key = uuid.uuid5(uuid.NAMESPACE_URL, identity).hex
        atomic_write_json(root / "process-log-refs" / (key + ".json"),
                      {"run_id": run_id, "relative_log": relative_name})
        return PREFIX + key
    except (OSError, ValueError, RuntimeError):
        return None


def read_process_log(state_root, reference, *, offset=0, limit=65536, tail_bytes=None):
    """Page in UTF-8 byte coordinates. Every valid forward cursor preserves full characters."""
    if offset < 0 or limit <= 0 or (tail_bytes is not None and tail_bytes <= 0):
        raise ValueError("invalid_log_page")
    key = re.fullmatch(re.escape(PREFIX) + "([0-9a-f]{32})", reference)
    if not key:
        raise ValueError("invalid_log_reference")
    root = physical_path(state_root).resolve()
    binding = json.loads((root / "process-log-refs" / (key[1] + ".json")).read_bytes())
    relative_name = binding["relative_log"]
    target = (root / relative_name).resolve()
    if target.relative_to(root).as_posix() != relative_name or target.suffix != ".log":
        raise ValueError("invalid_log_binding")
    identity = json.dumps([binding["run_id"], relative_name], ensure_ascii=True)
    if uuid.uuid5(uuid.NAMESPACE_URL, identity).hex != key[1]:
        raise ValueError("invalid_log_binding")
    with target.open("rb") as handle:
        size = handle.seek(0, 2)
        start = min(offset, size) if tail_bytes is None else max(0, size - tail_bytes)
        handle.seek(start)
        first = handle.read(1)
        while first and first[0] & 0xC0 == 0x80:
            start += 1
            first = handle.read(1)
        handle.seek(start)
        window = min(size - start, limit if tail_bytes is None else tail_bytes)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        text = decoder.decode(handle.read(window))
        while decoder.getstate()[0] and handle.tell() < size:
            text += decoder.decode(handle.read(1))
        end = handle.tell()
        text += decoder.decode(b"", final=True)
    return {"reference": reference, "offset": start, "next_offset": end,
            "total_bytes": size, "eof": end == size, "text": text}
