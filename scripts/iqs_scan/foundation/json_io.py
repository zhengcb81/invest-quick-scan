"""Small shared UTF-8 JSON file helpers for local configuration and artifacts."""
import json
import os
from pathlib import Path
import time
import uuid

API_PROTOCOL = "iqs.json-file-api/1.0.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "read_json", "write_json", "replace_after_readers_close",
})


def replace_after_readers_close(source, destination):
    """Publish a completed local file despite transient Windows reader sharing."""
    for delay in (0.005, 0.01, 0.02, 0.04, 0.04, 0.04, 0.04, None):
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            if delay is None or getattr(error, "winerror", None) not in (5, 32, 33):
                raise
            time.sleep(delay)


def atomic_write_json(path, value):
    """Publish a complete JSON record on the same volume."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + uuid.uuid4().hex + path.suffix)
    try:
        with temporary.open("x", encoding="utf8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        replace_after_readers_close(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    """Read UTF-8 JSON and tolerate an optional BOM in existing inputs."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, obj):
    """Write a readable UTF-8 JSON artifact to the caller-provided path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
