"""Process diagnostic streams: normalize Windows output and read one bounded display page at a time."""
from __future__ import annotations

import codecs
import io
import json
from pathlib import Path
import re
import uuid

from .json_io import atomic_write_json


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


def register_process_log(state_root, log_path, run_id):
    """Bind an original owner-created log under its state root; never copy its contents."""
    root = Path(state_root).resolve()
    try:
        relative = Path(log_path).resolve().relative_to(root)
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
    root = Path(state_root).resolve()
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
