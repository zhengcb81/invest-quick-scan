"""Run and record IQS's self-contained offline suite under native isolation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from iqs_scan import REPO_ROOT
from iqs_scan.tools.run_tests import run_group


def current_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    status = subprocess.run(
        ["git", "--no-optional-locks", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT, check=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if status.stdout:
        raise ValueError("pytest evidence requires a clean checkout")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("collect", "run"))
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        revision = current_revision()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        parser.error(str(error))
    if args.revision != revision:
        parser.error("revision does not name the current checkout")

    platform = "windows" if os.name == "nt" else "linux"
    policy = json.loads((REPO_ROOT / "tools/ci_test_policy.json").read_text(encoding="utf-8"))
    selection = policy["platforms"][platform]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = f"{platform}-{args.action}"
    evidence = output / f"s6-{name}.json"
    if evidence.exists():
        parser.error("evidence path already exists; choose a fresh output directory")
    options = [
        *selection["roots"], "--strict-markers", "-m", selection["markexpr"],
        "-p", "tools.anti_trick_gate_spec.pytest_probe",
        "--s6-revision", args.revision, "--s6-evidence", str(evidence),
    ]
    collect_only = args.action == "collect"
    if collect_only:
        options.append("--collect-only")
    result = run_group(
        REPO_ROOT, name, [], output, pytest_args=options, collect_only=collect_only,
    )
    if not collect_only or result["exit_code"]:
        sys.stdout.write((output / f"{name}.log").read_text(encoding="utf-8", errors="replace"))
    if result["exit_code"] == 0 and not evidence.is_file():
        parser.error("pytest returned without recording evidence")
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
