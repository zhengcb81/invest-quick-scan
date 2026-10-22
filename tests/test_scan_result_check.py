"""A run that exits 0 can still be worthless; these checks make that visible."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scan_result_check as check  # noqa: E402


def _write(run: Path, answers, *, calls=1, searches=1, importable=True, bank=True) -> Path:
    run.mkdir(parents=True, exist_ok=True)
    document = {
        "company": "c", "draft": True, "verified": False, "importable": importable,
        "provenance": "versioned_bank" if importable else "unversioned_flat_list",
        "bank": {"package_id": "pkg_x"} if bank else None,
        "meta": {"calls": calls, "searches": searches},
        "answers": answers,
    }
    (run / "answers.json").write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    (run / "run-log.json").write_text("[]", encoding="utf-8")
    (run / "index.html").write_text("<html></html>", encoding="utf-8")
    return run


def _answer(qid="Q1", status="scored", score=7, evidence=None, problems=None) -> dict:
    return {"question_id": qid, "status": status, "score": score,
            "evidence": evidence if evidence is not None else [{"url": "https://e.com/a"}],
            "problems": problems or []}


def test_a_healthy_run_is_usable(tmp_path):
    report = check.check(_write(tmp_path / "run", [_answer()]))
    assert report["ok"] and report["usable"], report["problems"]
    assert report["scored"] == 1


def test_all_insufficient_is_flagged_but_not_an_error(tmp_path):
    """Honest all-insufficient output is valid data, just not usable answers."""
    report = check.check(_write(tmp_path / "run", [_answer(status="insufficient_evidence", score=None)]))
    assert report["ok"], report["problems"]
    assert not report["usable"]
    assert report["warnings"]


def test_zero_model_calls_after_searches_is_a_problem(tmp_path):
    report = check.check(_write(tmp_path / "run",
                                 [_answer(status="insufficient_evidence", score=None)],
                                 calls=0, searches=24))
    assert not report["ok"]
    assert any("no model calls" in p for p in report["problems"])


def test_identical_failure_on_every_question_is_a_problem(tmp_path):
    answers = [_answer(qid=f"Q{i}", status="insufficient_evidence", score=None,
                       problems=["search_missing_credentials:KEY"]) for i in range(5)]
    report = check.check(_write(tmp_path / "run", answers))
    assert not report["ok"]
    assert any("same failure" in p for p in report["problems"])


def test_scored_without_evidence_is_a_problem(tmp_path):
    report = check.check(_write(tmp_path / "run", [_answer(evidence=[])]))
    assert not report["ok"]
    assert any("without evidence" in p for p in report["problems"])


def test_scored_with_invalid_score_is_a_problem(tmp_path):
    report = check.check(_write(tmp_path / "run", [_answer(score=0)]))
    assert not report["ok"]
    assert any("invalid score" in p for p in report["problems"])


def test_importable_run_needs_a_bank_identity(tmp_path):
    report = check.check(_write(tmp_path / "run", [_answer()], bank=False))
    assert not report["ok"]
    assert any("bank package identity" in p for p in report["problems"])


def test_missing_artifacts_are_unusable(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    report = check.check(run)
    assert not report["ok"] and not report["usable"]
    assert any("missing artifacts" in p for p in report["problems"])


def test_cli_exit_codes(tmp_path):
    good = _write(tmp_path / "good", [_answer()])
    result = subprocess.run([sys.executable, "-B", "-X", "utf8",
                             str(ROOT / "scripts/scan_result_check.py"), "--run", str(good)],
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout

    empty = _write(tmp_path / "empty", [_answer(status="insufficient_evidence", score=None)])
    result = subprocess.run([sys.executable, "-B", "-X", "utf8",
                             str(ROOT / "scripts/scan_result_check.py"), "--run", str(empty)],
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1, result.stdout

    broken = tmp_path / "broken"
    broken.mkdir()
    result = subprocess.run([sys.executable, "-B", "-X", "utf8",
                             str(ROOT / "scripts/scan_result_check.py"), "--run", str(broken)],
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 2, result.stdout
