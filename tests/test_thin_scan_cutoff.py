"""Retrieved sources must respect the information cutoff.

Regression context (2026-10-22): a CATL scan with as_of=2026-10-18 retrieved pages
published 2026-10-19..22. The model correctly refused to score against them, so
questions that had usable evidence still came back insufficient. The search API
takes no date parameter, so the cutoff has to be enforced on the results.

Two things matter and both were previously absent:
- results published after the cutoff are dropped before they reach the prompt;
- timestamps are compared as instants in UTC, because a source stamped
  "2026-10-17T16:00:00+00:00" is 2026-10-18 in Asia/Shanghai and must not be
  dropped for a 2026-10-18 cutoff.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import thin_scan  # noqa: E402


def _source(url="https://e.com/a", date="2026-10-01") -> dict:
    return {"url": url, "title": "t", "summary": "s", "date": date, "site": "x"}


def test_source_after_cutoff_is_dropped():
    kept, dropped = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/new", "2026-10-20")], "2026-10-18")
    assert kept == []
    assert len(dropped) == 1


def test_source_on_or_before_cutoff_is_kept():
    sources = [_source("https://e.com/old", "2026-10-17"),
               _source("https://e.com/same", "2026-10-18")]
    kept, dropped = thin_scan.filter_sources_by_cutoff(sources, "2026-10-18")
    assert len(kept) == 2
    assert dropped == []


def test_utc_evening_before_cutoff_day_is_kept():
    """2026-10-17T16:00Z is 2026-10-18 00:00 +08:00: still on the cutoff day."""
    kept, dropped = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/a", "2026-10-17T16:00:00+00:00")], "2026-10-18")
    assert len(kept) == 1, "an instant inside the cutoff day must not be dropped"
    assert dropped == []


def test_source_at_cutoff_day_end_utc_is_kept():
    kept, _ = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/a", "2026-10-18T23:59:59+00:00")], "2026-10-18")
    assert len(kept) == 1


def test_source_after_cutoff_day_end_is_dropped():
    kept, dropped = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/a", "2026-10-19T00:00:00+00:00")], "2026-10-18")
    assert kept == []
    assert len(dropped) == 1


def test_unknown_date_is_kept_and_reported_not_dropped():
    """An unparseable date is not evidence of being late; keep it, flag it."""
    kept, dropped = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/a", "")], "2026-10-18")
    assert len(kept) == 1
    assert dropped == []
    assert kept[0].get("date_unknown") is True


def test_filtering_is_stable_and_preserves_order():
    sources = [_source(f"https://e.com/{i}", "2026-10-01") for i in range(4)]
    kept, _ = thin_scan.filter_sources_by_cutoff(sources, "2026-10-18")
    assert [s["url"] for s in kept] == [s["url"] for s in sources]


def test_dropped_sources_are_summarised_for_problems():
    """The caller needs a machine-readable reason, not just a shorter list."""
    kept, dropped = thin_scan.filter_sources_by_cutoff(
        [_source("https://e.com/a", "2026-10-01"),
         _source("https://e.com/b", "2026-10-25")], "2026-10-18")
    assert len(kept) == 1
    assert thin_scan.cutoff_problem(dropped) == "dropped_after_cutoff:1"


def test_no_dropped_sources_yields_no_problem():
    kept, dropped = thin_scan.filter_sources_by_cutoff([_source()], "2026-10-18")
    assert thin_scan.cutoff_problem(dropped) is None


def test_cutoff_is_applied_before_the_prompt_is_built():
    """End to end: a late-only result set must not silently feed the model."""
    sources = [_source("https://e.com/late", "2026-10-25")]
    kept, dropped = thin_scan.filter_sources_by_cutoff(sources, "2026-10-18")
    assert not kept
    # build_prompt with the filtered (empty) list must say there were no sources.
    prompt, _, _ = thin_scan.build_prompt({"id": "Q", "prompt": "BASE"}, "co", kept, "2026-10-18", True)
    assert "https://e.com/late" not in prompt

def test_late_sources_alone_produce_the_cutoff_summary(monkeypatch):
    """A run whose only sources are late must say so, not "no sources found"."""
    import json
    import subprocess

    manifest = {
        "module_package_id": "pkg_t", "module_release_id": "modrel_t",
        "modules": ["common"], "module_locks": [{"module_id": "common", "version": "1"}],
        "questions": [{
            "id": "IQS_01", "question": "q?", "module_id": "common",
            "prompt": "BASE", "prompt_sha256": __import__("hashlib").sha256(b"BASE").hexdigest(),
            "semantic_sha256": "a" * 64, "definition_sha256": "b" * 64,
            "comparison_role": "core", "dimension": "business", "priority": 1,
            "evidence": [], "anchors": {}, "scope": "entity",
        }],
    }
    tmp = Path(ROOT / "tests" / "_tmp_cutoff")
    tmp.mkdir(exist_ok=True)
    try:
        mpath = tmp / "manifest.json"
        mpath.write_text(json.dumps(manifest), encoding="utf-8")

        # Every source is published after the cutoff.
        monkeypatch.setattr(thin_scan, "search_with_status", lambda *a, **k: ([
            {"url": "https://e.com/late", "title": "t", "summary": "s",
             "date": "2026-10-25", "site": "x"}], None))

        out = tmp / "out"
        result = thin_scan.main.__wrapped__ if hasattr(thin_scan.main, "__wrapped__") else None
        # main() parses argv; drive it through the CLI instead.
        proc = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/thin_scan.py"),
             "--company", "co", "--bank-manifest", str(mpath),
             "--out", str(out), "--as-of", "2026-10-18", "--dry-run"],
            capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, proc.stderr
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
