"""Offline real-run answers page tests."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "runs/shared-engine-production-2026-10-18/actual-native-catl-0506-scan/recovered-export"
OBS = ROOT / "runs/shared-engine-production-2026-10-18/actual-native-catl-0506-scan/recovery-observation.json"


def test_render_real_run(tmp_path):
    output = tmp_path / "answers.html"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/run_answers_page.py"),
         "--export", str(EXPORT), "--observation", str(OBS), "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert done.returncode == 0, done.stderr
    page = output.read_text(encoding="utf-8")
    assert "IQS_05" in page and "IQS_06" in page
    assert "insufficient_evidence" in page
    assert "不是金融准确率结论" in page
