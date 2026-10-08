"""Build the SW-REPAIR-02 post-fix export manifest (new producer record).

Records the byte hashes of the public files this package changed plus the
ORIGINAL frozen counterexample file and the legacy (pre-conditions) query
producer pulled straight from Git. It is a NEW record for the repaired tree —
it never replaces the original SW-READY-01 freeze manifest.

Usage::

    python -B -X utf8 docs/handoff/SW-REPAIR-02/build_export_manifest.py \
        --repo C:/Users/郑曾波/Projects/StockWiki \
        --out <OWN>/export-manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

DEFAULT_FILES = (
    "stockwiki/quick_scan_backup.py",
    "stockwiki/quick_scan_backup_manifest.py",
    "stockwiki/quick_scan_profiles.py",
    "stockwiki/quick_scan_query.py",
    "stockwiki/quick_scan_rows.py",
    "stockwiki/ui_quick_scan.py",
    "stockwiki/ui_static/app.js",
    "stockwiki/ui_static/index.html",
    "stockwiki/ui_static/styles.css",
    "tests/test_swr_cases.py",
    "tests/test_swr_backup.py",
    "tests/test_swr_profiles.py",
    "tests/test_swr_query.py",
    "tests/test_quick_scan_backup.py",
    "tests/test_quick_scan_profiles.py",
    "tests/test_quick_scan_query.py",
    "tests/test_ui_quick_scan.py",
    "tests/test_e2e_quick_scan_ui.py",
    "docs/quick-scan-backup-restore.md",
    "docs/ui.md",
)
LEGACY_QUERY_COMMIT = "9f552a67"
ORIGINAL_FREEZE = (
    "invest-quick-scan/docs/implementation/intake/SW-READY-01/2026-10-07/export-manifest.json"
)
ACCEPTANCE_PATH = (
    "C:/Users/郑曾波/Projects/invest-quick-scan/"
    "docs/implementation/reviews/SW-READY-01/acceptance_cases.py"
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()

    def git(*argv: str) -> bytes:
        return subprocess.run(["git", *argv], cwd=repo, check=True, capture_output=True).stdout

    rows = []
    for rel in DEFAULT_FILES:
        data = (repo / rel).read_bytes()
        rows.append(
            {
                "path": rel,
                "bytes": len(data),
                "sha256": _sha(data),
                "source_kind": "working_tree_bytes",
            }
        )

    legacy = git("show", f"{LEGACY_QUERY_COMMIT}:stockwiki/quick_scan_query.py")
    head = git("rev-parse", "HEAD").decode().strip()
    acceptance = Path(ACCEPTANCE_PATH).read_bytes()

    manifest = {
        "format_version": "1.0.0",
        "kind": "swr02_post_fix_export_manifest",
        "note": (
            "NEW producer export record for SW-REPAIR-02. It does NOT replace the "
            "original SW-READY-01 freeze manifest at " + ORIGINAL_FREEZE + "."
        ),
        "original_freeze_manifest": ORIGINAL_FREEZE,
        "head_commit_at_generation": head,
        "legacy_query_commit": LEGACY_QUERY_COMMIT,
        "legacy_quick_scan_query": {
            "path": "stockwiki/quick_scan_query.py",
            "git_revision": LEGACY_QUERY_COMMIT,
            "bytes": len(legacy),
            "sha256": _sha(legacy),
        },
        "frozen_acceptance_cases": {
            "path": ACCEPTANCE_PATH,
            "bytes": len(acceptance),
            "sha256": _sha(acceptance),
        },
        "files": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "out": str(args.out),
                "files": len(rows),
                "sha256": _sha(args.out.read_bytes()),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
