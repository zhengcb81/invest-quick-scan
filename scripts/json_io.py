"""Small shared UTF-8 JSON file helpers for local configuration and artifacts."""
import json
from pathlib import Path


def read_json(path):
    """Read UTF-8 JSON and tolerate an optional BOM in existing inputs."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, obj):
    """Write a readable UTF-8 JSON artifact to the caller-provided path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
