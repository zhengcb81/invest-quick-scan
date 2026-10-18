"""Mechanical financial checks: valid answer and every mutation rule."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import financial_mechanical_check as tool  # noqa: E402


def observation():
    return {
        "observation_id": "obs_1",
        "question_id": "IQS_12",
        "entity_id": "ENT_a",
        "information_cutoff": "2026-10-18",
        "answer": {
            "question_id": "IQS_12",
            "response_kind": "score",
            "status": "insufficient_evidence",
            "score": None,
            "information_as_of": "2026-03-10",
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "metrics": [
                {
                    "metric_id": "financial.revenue",
                    "basis": "trailing",
                    "currency": "CNY",
                    "unit": "currency",
                    "value": 100,
                    "period_start": "2025-01-01",
                    "period_end": "2025-12-31",
                    "definition": "revenue",
                    "evidence_ids": ["SRC_1"],
                }
            ],
            "evidence": [
                {
                    "id": "SRC_1",
                    "url": "https://example.com/a",
                    "title": "official",
                    "published_at": "2026-03-10",
                }
            ],
            "missing_fields": ["debt"],
        },
    }


def test_valid_answer_passes():
    result = tool.check_answer(observation())
    assert result["mechanical_pass"] is True
    assert result["findings"] == []


def test_scored_answer_without_evidence_is_caught():
    value = observation()
    value["answer"]["status"] = "scored"
    value["answer"]["score"] = 5
    value["answer"]["evidence"] = []
    result = tool.check_answer(value)
    assert "scored_without_evidence" in {f["code"] for f in result["findings"]}


def test_each_mutation_is_caught():
    cases = {
        "score_on_unscored": lambda a: a["answer"].__setitem__("score", 5),
        "evidence_url_invalid": lambda a: a["answer"]["evidence"][0].__setitem__("url", "http://x"),
        "evidence_after_cutoff": lambda a: a["answer"]["evidence"][0].__setitem__("published_at", "2027-01-01"),
        "metric_evidence_unknown": lambda a: a["answer"]["metrics"][0].__setitem__("evidence_ids", ["NOPE"]),
        "metric_period_after_cutoff": lambda a: a["answer"]["metrics"][0].__setitem__("period_end", "2027-01-01"),
        "metric_currency_missing": lambda a: a["answer"]["metrics"][0].__setitem__("currency", None),
        "reversed_period": lambda a: a["answer"].__setitem__("period_start", "2026-01-01"),
        "question_mismatch": lambda a: a["answer"].__setitem__("question_id", "IQS_16"),
    }
    expected = {
        "score_on_unscored": "score_on_unscored",
        "evidence_url_invalid": "evidence_url_invalid",
        "evidence_after_cutoff": "evidence_after_cutoff",
        "metric_evidence_unknown": "metric_evidence_unknown",
        "metric_period_after_cutoff": "metric_period_after_cutoff",
        "metric_currency_missing": "metric_currency_missing",
        "reversed_period": "reversed_period",
        "question_mismatch": "question_mismatch",
    }
    for name, mutate in cases.items():
        value = copy.deepcopy(observation())
        mutate(value)
        result = tool.check_answer(value)
        assert result["mechanical_pass"] is False, name
        assert expected[name] in {f["code"] for f in result["findings"]}, name
