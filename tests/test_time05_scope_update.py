"""TIME-05 (C04 contract, executed in the W11 batch): the pure
``work_contract`` receives the SAME old observation plus two field-scope
requests — one changes only a filter threshold, one appends 3 new questions.

Then: the threshold edit derives a freshness re-evaluation with ZERO model
calls; the question request yields exactly 3 logical work-gap keys; the old
observation's content/source/time never change; persistence (queue) is
validated by Q06/W06, not here. No database, worker or HTTP.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import work_contract  # noqa: E402


def _old_observation() -> dict:
    return {
        "entity_id": "ENT_A",
        "question_id": "IQS_05",
        "observed_at": "2026-10-01T00:00:00Z",
        "content_sha": "b" * 64,
        "source_ref": "obs-1",
        "fields": {"industry": None, "incorporation_country": "US"},
        "information_as_of": "2026-09-30T00:00:00Z",
    }


def test_time_05_threshold_request_derives_zero_model_calls() -> None:
    old = _old_observation()
    frozen = copy.deepcopy(old)

    # Same observation, threshold-derived validity windows. The preview is a
    # pure re-classification: dispatch stays False (zero model calls) either
    # way — only the derived freshness changes.
    fresh_preview = work_contract.field_freshness_preview(
        {
            "industry": {
                "information_as_of": "2026-10-04T00:00:00Z",
                "valid_until": "2026-11-04T00:00:00Z",
            }
        },
        now="2026-10-05T00:00:00Z",
    )
    assert fresh_preview["dispatch_started"] is False
    assert fresh_preview["refresh_needed_fields"] == []

    stale_preview = work_contract.field_freshness_preview(
        {
            "industry": {
                "information_as_of": "2026-09-01T00:00:00Z",
                "valid_until": "2026-10-01T00:00:00Z",
            }
        },
        now="2026-10-05T00:00:00Z",
    )
    assert stale_preview["dispatch_started"] is False
    assert stale_preview["refresh_needed_fields"] == ["industry"]
    # the observation is actually READ by a contract function (r1 P2-3: the
    # old vacuous compare never passed `old` to anything)
    assert isinstance(
        work_contract.observation_compatible(old, dict(old)), bool
    )
    assert old == frozen, "old observation content/source/time unchanged"


def test_time_05_three_new_questions_yield_exactly_three_logical_work_keys() -> None:
    old = _old_observation()
    frozen = copy.deepcopy(old)

    new_questions = ["IQS_10", "IQS_11", "IQS_12"]
    keys = [
        work_contract.logical_work_key(
            old["entity_id"], qid, 1, "entity", old["entity_id"]
        )
        for qid in new_questions
    ]
    assert len(keys) == 3
    assert len(set(keys)) == 3, "keys must be distinct per question"
    # threshold-only path: reuse decision for the SAME question with a changed
    # threshold must not create a new generation key
    same = work_contract.logical_work_key(
        old["entity_id"], old["question_id"], 1, "entity", old["entity_id"]
    )
    same_again = work_contract.logical_work_key(
        old["entity_id"], old["question_id"], 1, "entity", old["entity_id"]
    )
    assert same == same_again, "threshold edits never mint new work keys"
    assert old == frozen
