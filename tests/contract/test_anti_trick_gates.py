"""Ratchet real IQS source scope without codifying the old short CI selection."""
from pathlib import Path
import json

from tools.anti_trick_gate_spec.evidence import baseline, changed_inventory, compare, renamed_waivers
from tools.anti_trick_gate_spec.static_scan import scan


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("scripts",)
MACHINE_ENTRYPOINTS = (
    "scripts/iqs_scan/tools/feedback_owner.py",
    "scripts/iqs_scan/workbench/dashboard_jobs.py",
    "scripts/iqs_scan/workbench/dashboard_service.py",
    "scripts/iqs_scan/workbench/open_dashboard.py",
)


def inspect_sources():
    return scan(ROOT, SOURCES, entry=MACHINE_ENTRYPOINTS)


def test_anti_trick_baseline_covers_standalone_and_native_iqs_sources():
    result = inspect_sources()
    expected = {path.relative_to(ROOT).as_posix() for path in (ROOT / "scripts").rglob("*.py")}
    assert expected == set(result.files)
    saved = json.loads((ROOT / "tests/contract/ratchet_baseline.json").read_text(encoding="utf-8"))
    current = {**baseline(result.findings), "constant_shapes": result.constant_shapes}
    assert not changed_inventory(result, saved, ROOT)
    assert not compare(current, saved)
    assert not renamed_waivers(current, saved)
