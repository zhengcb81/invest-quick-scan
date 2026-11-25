"""The legacy comparator calls the two public StockWiki value operations."""
from pathlib import Path
import os
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.mark.parametrize("export_metadata", [False, True])
def test_legacy_freshness_works_via_owner_exports_without_checkout(tmp_path, export_metadata):
    package = tmp_path / "stockwiki"
    package.mkdir()
    (package / "__init__.py").touch()
    module = package / "quick_scan_freshness.py"
    exports = ("MODULE_API_VERSION = '1.0.0'\n"
               "MODULE_API_EXPORTS = ('freshness_status', 'ttl_valid_until')\n")
    module.write_text(
        (exports if export_metadata else "")
        + "def freshness_status(meta, at):\n"
        + "    assert meta == {'information_as_of': 'fixture'} and at == 'input-clock'\n"
        + "    return 'owner-freshness'\n"
        + "def ttl_valid_until(observed_at, ttl_hours):\n"
        + "    assert observed_at == 'observed' and ttl_hours == 24\n"
        + "    return 'owner-ttl'\n",
        encoding="utf-8",
    )
    program = """
from iqs_scan.workbench.iqs_temporal_vendor.legacy_oracle import legacy_freshness_status, legacy_ttl_valid_until
assert legacy_freshness_status({'information_as_of': 'fixture'}, 'input-clock') == 'owner-freshness'
assert legacy_ttl_valid_until('observed', 24) == 'owner-ttl'
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", program], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, [tmp_path, SCRIPTS]))),
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stderr
