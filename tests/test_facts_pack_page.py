"""Offline facts pack review page tests."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATL_PACK = ROOT / "docs/implementation/reviews/catl-profile-2026-10-18/facts-pack-quick"


def test_render_catl_pack(tmp_path):
    output = tmp_path / "facts.html"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_pack_page.py"),
         "--pack", str(CATL_PACK), "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert done.returncode == 0, done.stderr
    page = output.read_text(encoding="utf-8")
    assert "facts pack review" in page
    assert "DRAFT" in page
    assert page.count("<tr>") >= 16
    assert "source_sha256" in page


def test_missing_pack_fails(tmp_path):
    output = tmp_path / "facts.html"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_pack_page.py"),
         "--pack", str(tmp_path / "missing"), "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert done.returncode != 0
