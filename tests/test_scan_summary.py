"""The summary must report what a run produced, including why gaps exist."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scan_summary  # noqa: E402


def _run(tmp_path: Path, answers, *, calls=2, searches=2, cost=1400) -> Path:
    run = tmp_path / "run"
    run.mkdir(parents=True, exist_ok=True)
    document = {
        "company": "宁德时代", "importable": True,
        "summary": {"method": "draft_unweighted_mean_of_scored_not_official",
                    "core_total": len(answers), "core_scored": 1, "core_mean": 8.0},
        "meta": {"calls": calls, "searches": searches, "cost_micros": cost},
        "answers": answers,
    }
    (run / "answers.json").write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return run


def _scored(qid="IQS_01", score=8, urls=3, module="common", counter=None) -> dict:
    return {"question_id": qid, "module_id": module, "status": "scored", "score": score,
            "evidence": [{"url": f"https://e.com/{i}"} for i in range(urls)],
            "counterevidence": counter}


def _insufficient(qid="IQS_02", summary="材料晚于截止日", module="common") -> dict:
    return {"question_id": qid, "module_id": module, "status": "insufficient_evidence",
            "score": None, "summary": summary, "evidence": []}


def test_score_statistics_and_coverage(tmp_path):
    report = scan_summary.summarise(_run(tmp_path, [_scored(score=8), _scored("Q2", score=6),
                                                    _insufficient()]))
    assert report["questions"] == 3
    assert report["scored"] == 2
    assert report["coverage_pct"] == 66.7
    assert report["mean_score"] == 7.0
    assert report["score_distribution"] == {6: 1, 8: 1}


def test_per_module_breakdown(tmp_path):
    answers = [_scored("Q1", module="common", score=8),
               _scored("Q2", module="operating", score=6),
               _insufficient("Q3", module="operating")]
    report = scan_summary.summarise(_run(tmp_path, answers))

    assert report["by_module"]["common"]["scored"] == 1
    assert report["by_module"]["operating"]["scored"] == 1
    assert report["by_module"]["operating"]["total"] == 2
    assert report["by_module"]["operating"]["mean"] == 6.0


def test_evidence_density_is_reported(tmp_path):
    report = scan_summary.summarise(_run(tmp_path, [_scored(urls=3), _scored("Q2", urls=5)]))
    assert report["evidence"]["answers_with_evidence"] == 2
    assert report["evidence"]["mean_urls_per_scored"] == 4.0
    assert report["evidence"]["max_urls"] == 5


def test_insufficient_reasons_are_grouped(tmp_path):
    answers = [_insufficient("Q1", "材料晚于截止日"), _insufficient("Q2", "材料晚于截止日"),
               _insufficient("Q3", "无可用来源")]
    report = scan_summary.summarise(_run(tmp_path, answers))
    assert report["insufficient_reasons"]["材料晚于截止日"] == 2
    assert report["insufficient_reasons"]["无可用来源"] == 1


def test_missing_scores_do_not_produce_a_mean(tmp_path):
    report = scan_summary.summarise(_run(tmp_path, [_insufficient()]))
    assert report["scored"] == 0
    assert report["mean_score"] is None
    assert report["score_distribution"] == {}


def test_counterevidence_is_counted(tmp_path):
    report = scan_summary.summarise(_run(tmp_path, [_scored(counter="revenue declined")]))
    assert report["evidence"]["with_counterevidence"] == 1


def test_text_render_mentions_the_gap_reason(tmp_path):
    run = _run(tmp_path, [_scored(), _insufficient(summary="材料晚于截止日")])
    text = scan_summary.render(scan_summary.summarise(run))
    assert "宁德时代" in text
    assert "覆盖率" in text
    assert "材料晚于截止日" in text


def test_cli_json_and_missing_file(tmp_path):
    run = _run(tmp_path, [_scored()])
    result = subprocess.run([sys.executable, "-B", "-X", "utf8",
                             str(ROOT / "scripts/scan_summary.py"), "--run", str(run), "--json"],
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0
    assert json.loads(result.stdout)["scored"] == 1

    empty = tmp_path / "empty"
    empty.mkdir()
    result = subprocess.run([sys.executable, "-B", "-X", "utf8",
                             str(ROOT / "scripts/scan_summary.py"), "--run", str(empty)],
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 2
