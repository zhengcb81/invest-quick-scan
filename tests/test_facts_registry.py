"""Offline facts pack registry tests."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "docs/implementation/reviews"


def test_registry_lists_catl_pack(tmp_path):
    output = tmp_path / "index.html"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_registry.py"),
         "--root", str(REVIEWS), "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert done.returncode == 0, done.stderr
    page = output.read_text(encoding="utf-8")
    assert "宁德时代新能源科技股份有限公司" in page
    assert "DRAFT" in page
    assert "review" in page
    assert page.count("<tr>") >= 2
