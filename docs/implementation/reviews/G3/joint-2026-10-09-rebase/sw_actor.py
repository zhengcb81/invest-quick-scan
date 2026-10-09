"""Thin test-only receiver descriptor adapter; no production DTO/golden claim."""
import importlib.util
import json
import os
from pathlib import Path
import sys

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
spec = importlib.util.spec_from_file_location("joint108_sw_actor", OWN / "legacy_sw_actor.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def inside(value):
    path = Path(value).resolve()
    if not path.is_relative_to(OWN):
        raise ValueError("test actor path outside the owned runtime")
    return path


def main(request):
    root = inside(request["root"])
    if request["op"] not in {"empty", "seed", "import", "observations", "ack", "query", "backup", "receiver-owner"}:
        raise ValueError("unsupported current SW test actor operation")
    if request["op"] == "import":
        inside(request["package"])
        inside(request["release"])
    if request["op"] != "receiver-owner":
        return legacy.main(request)
    paths = legacy.WorkspacePaths.from_root(root)
    # This is the real public receiver property in the synthetic workspace.
    # It is not an identity/facts/query golden or a new public CLI capability.
    store = legacy.QuickScanObservationStore(paths)
    return {"schema_version": "joint_receiver_fixture/1.0.0", "synthetic_only": True,
            "basis": "public QuickScanObservationStore.store_id", "workspace_root": str(root),
            "consumer": {"component": "StockWiki", "namespace": "quick_scan", "store_id": store.store_id}}


if __name__ == "__main__":
    request = json.loads(inside(sys.argv[1]).read_bytes())
    inside(sys.argv[2]).write_text(json.dumps(main(request), ensure_ascii=False), encoding="utf-8")
