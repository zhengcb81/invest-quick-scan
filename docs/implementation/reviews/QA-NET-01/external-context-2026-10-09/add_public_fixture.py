"""Add the one inert tracked example required by the existing boundary suite."""
import hashlib
import json
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
SOURCE = "C:/Users/郑曾波/Projects/StockQAbyLLM"
HEAD = "42a517c4bd6bc8219f926957c6c332944da3278a"
NAME = "examples/quick_scan_search_policy.example.json"


def main():
    assert subprocess.check_output(["git", "--no-optional-locks", "-C", SOURCE, "rev-parse", "HEAD"]).decode().strip() == HEAD
    raw = subprocess.check_output(["git", "--no-optional-locks", "-C", SOURCE, "show", HEAD + ":" + NAME])
    document = json.loads(raw)
    assert all(route["enabled"] is False for route in document["external_routes"])
    assert all(route["cost_bound_verified"] is False for route in document["external_routes"])
    target = OWN / "qa" / NAME
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    catalog_path = OUT / "source-snapshot.json"
    catalog = json.loads(catalog_path.read_text("utf-8"))
    assert NAME not in {r["path"] for r in catalog}
    catalog.append(dict(path=NAME, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), provenance="tracked_inert_example_at_fixed_HEAD"))
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(added_files=1, owner_written=False, secrets_read=False)))


if __name__ == "__main__":
    main()
