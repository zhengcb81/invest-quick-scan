"""Exact baseline control for three pre-existing legacy receipt fixtures."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"


def main():
    spec = json.loads((OUT / "executor-input-01.json").read_text(encoding="utf-8"))
    source = Path(spec["source"])
    target = ROOT / "runs/w15a/qa_baseline"
    assert not target.exists()
    copied = {}
    for row in spec["artifacts"]:
        path = source / row["path"]
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]
        copied[row["path"]] = raw
    target.mkdir()
    for name, raw in copied.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    print(json.dumps(dict(baseline_files=len(copied), baseline_head=spec["head"], source_writes=0)))


if __name__ == "__main__":
    main()
