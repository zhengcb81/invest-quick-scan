"""Build the IQS-owned read-only workbench snapshot at one explicit path."""
from __future__ import annotations

from iqs_scan import REPO_ROOT

import argparse
import json
from pathlib import Path
import sys

ROOT = REPO_ROOT

from .dashboard_service import validate_config  # noqa: E402
from .workbench_snapshot import build_workbench_snapshot, write_workbench_snapshot  # noqa: E402


def _config(path: Path | None, data_root: Path) -> dict:
    if path is None:
        path = data_root / "config" / "dashboard.local.json"
    if not path.is_file():
        return validate_config({}, data_root)
    if path.stat().st_size > 1_048_576:
        raise ValueError("dashboard configuration exceeds the read limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate configuration key")
            result[key] = value
        return result
    raw = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=pairs,
                     parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite configuration")))
    return validate_config(raw, data_root)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT, help="IQS configuration and question resources")
    parser.add_argument("--dashboard-config", type=Path, help="Optional local owner configuration")
    parser.add_argument("--output", type=Path, required=True, help="Explicit snapshot output path")
    parser.add_argument("--plan", action="store_true", help="Print the export plan without reading owners or writing")
    args = parser.parse_args(argv)
    root = args.data_root.resolve()
    output = args.output.resolve()
    if not root.is_dir():
        parser.error("--data-root must point to an existing IQS data directory")
    if args.plan:
        print(json.dumps({"data_root": str(root), "output": str(output),
                          "reads_owner": False, "model_calls": False, "writes": False}, ensure_ascii=False))
        return 0
    try:
        config = _config(args.dashboard_config.resolve() if args.dashboard_config else None, root)
        snapshot = build_workbench_snapshot(root, config)
        write_workbench_snapshot(output, snapshot)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        sys.stderr.write(f"Snapshot export failed: {error}\n")
        return 2
    print(json.dumps({"status": "written", "output": str(output),
                      "availability": snapshot["availability"], "model_calls": 0,
                      "network_calls": 0}, ensure_ascii=False))
    return 0
