"""Offline facts pack composition tests."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from question_library import load_library  # noqa: E402


def profile():
    _, modules = load_library(root=ROOT)
    stages = [k for k, m in modules.items() if m["kind"] == "stages" and k != "cyclical"]
    company_type = next(k for k, m in modules.items() if m["kind"] == "types")
    industries = [k for k, m in modules.items() if m["kind"] == "industries"]
    industry_modules = industries[:1] if company_type in ("operating", "pre_revenue") else []
    return {
        "company": "Fixture Co",
        "ticker": "FIX",
        "exchange": "TEST",
        "as_of": "2026-10-18",
        "company_type": company_type,
        "stage": stages[0],
        "routing_rationale": "fixture only",
        "routing_confidence": "high",
        "routing_sources": [{"url": "https://example.com/profile", "published_at": "2026-10-01"}],
        "industry_modules": industry_modules,
        "overlays": [],
    }


def run(tmp_path, value):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(value), encoding="utf-8")
    output = tmp_path / "facts-out"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_compose.py"),
         "--profile", str(profile_path), "--mode", "quick", "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, output


def test_compose_quick_facts_pack(tmp_path):
    done, output = run(tmp_path, profile())
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["protocol"] == "iqs.facts_pack/1.0.0"
    assert result["fact_questions"] >= 1
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["answer_format"] == "standard-1"
    assert all(q["response_kind"] == "fact" for q in manifest["questions"])


def test_invalid_profile_is_rejected(tmp_path):
    bad = profile()
    bad["routing_confidence"] = "low"
    done, _ = run(tmp_path, bad)
    assert done.returncode != 0
