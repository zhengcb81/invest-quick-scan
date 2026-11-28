"""Offline answer rendering and the separate original owner archive check."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def render(export, observation, output):
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/run_answers_page.py"),
         "--export", str(export), "--observation", str(observation), "--output", str(output)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert done.returncode == 0, done.stderr
    return output.read_text(encoding="utf-8")


def test_render_preserves_missing_evidence_and_does_not_modify_owner_export(tmp_path):
    export = tmp_path / "frozen"
    export.mkdir()
    run_path = export / "research-run.json"
    run_path.write_text(json.dumps({
        "run_id": "ISO_RENDER",
        "mode": "fixture",
        "slots": [
            {"question_id": "FIXTURE_01", "answer": {"status": "insufficient_evidence", "score": None}},
            {"question_id": "FIXTURE_02", "answer": {
                "status": "scored", "summary": "Synthetic reference", "score": 4,
                "evidence": [{"id": "E1", "url": "https://example.invalid/filing", "title": "Filing <title>"}],
            }},
        ],
    }), encoding="utf-8")
    observation = tmp_path / "recovery-observation.json"
    observation.write_text('{"runtime_summary":{}}', encoding="utf-8")
    before = (run_path.read_bytes(), observation.read_bytes())
    page = render(export, observation, tmp_path / "report/answers.html")
    assert "FIXTURE_01 · insufficient_evidence" in page
    assert "FIXTURE_02 · scored" in page
    assert "Filing &lt;title&gt;" in page
    assert "不是金融准确率结论" in page
    assert (run_path.read_bytes(), observation.read_bytes()) == before


@pytest.mark.owner_assets
def test_render_real_run(tmp_path):
    archive = Path(os.environ["IQS_ARCHIVED_ANSWERS_RUN"])
    page = render(archive / "recovered-export", archive / "recovery-observation.json", tmp_path / "answers.html")
    assert "IQS_05" in page and "IQS_06" in page
    assert "insufficient_evidence" in page
    assert "不是金融准确率结论" in page
