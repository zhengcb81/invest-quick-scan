"""SWR-04 comparability-boundary counterexamples for the U01/U02 projection.

Every observation reaches the store through the PUBLIC ``import_package``
entry point (identity through ``QuickScanStore.save_entity``) — no hand-written
profiles anywhere. Covered:

* two accepted analysis subjects on one field stay visible AND the ``>=8``
  condition never selects the higher one;
* a late replay of an OLDER observation cannot become "latest" (reverse-order
  import), and an old high score never masks a newer unknown;
* two models answering the same question are not blended;
* one issuer with several listings stays ONE row; two issuers that happen to
  share a display name are NEVER merged.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_quick_scan_observations import _observation, _package, _seed_entity
from test_quick_scan_profiles import E01, E02, _field_for, _release

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_import import import_package
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_profiles import build_entity_detail, build_profiles
from stockwiki.quick_scan_query import search
from stockwiki.quick_scan_store import QuickScanStore

SUBJECT_A = "ASJ_11111111-1111-4111-8111-111111111111"
SUBJECT_B = "ASJ_22222222-2222-4222-8222-222222222222"
FIELD = "score.iqs_01"


def _bare_workspace(root: Path, *entity_ids: str) -> WorkspacePaths:
    """Identity + empty observation store, seeded only through public entry points."""
    paths = WorkspacePaths.from_root(root)
    identity = QuickScanStore(paths)
    identity.migrate()
    for entity_id in entity_ids or (E01,):
        entity = _seed_entity(
            entity_id, tickers=["600745", "0700"] if entity_id == E01 else ["600519"]
        )
        bindings = entity.pop("_bindings")
        identity.save_entity(entity, source_bindings=bindings)
    QuickScanObservationStore(paths).migrate()
    return paths


def _import(paths: WorkspacePaths, observations: list[dict]) -> dict:
    return import_package(
        QuickScanObservationStore(paths),
        _package(observations),
        frozen_release=_release(),
        identity_store=QuickScanStore(paths),
    )


def _accepted(paths: WorkspacePaths, observations: list[dict]) -> None:
    receipt = _import(paths, observations)
    assert [ack["status"] for ack in receipt["acks"]] == ["accepted"] * len(observations), receipt[
        "acks"
    ]


def _score_fields(paths: WorkspacePaths) -> dict:
    return {p["entity_id"]: p for p in build_profiles(paths)}


def _hit(paths: WorkspacePaths, *, op: str, value: int) -> dict:
    profiles = build_profiles(paths)
    return search(
        profiles,
        conditions=[{"field": FIELD, "op": op, "value": value}],
        condition_combine="all",
    )


def _subject_observation(observation_id: str, subject: str, score: int, index: int) -> dict:
    return _observation(
        observation_id,
        entity_id=E01,
        question_id="IQS_LEG",
        field_id=FIELD,
        score=score,
        request_id=f"request-{index}",
        attempt_id=f"attempt-{index}",
        extra={
            "analysis_subject": {
                "analysis_subject_id": subject,
                "analysis_subject_revision": 1,
                "entity_id": E01,
                "primary_issuer_id": E01,
            }
        },
    )


def test_swr4_two_subjects_stay_visible_and_the_high_score_never_wins_a_condition(
    tmp_path: Path,
) -> None:
    paths = _bare_workspace(tmp_path / "ws")
    _accepted(
        paths,
        [
            _subject_observation("OBS_SUBJ_A_AAA", SUBJECT_A, 2, 1),
            _subject_observation("OBS_SUBJ_B_BBB", SUBJECT_B, 9, 2),
        ],
    )

    detail = build_entity_detail(paths, E01)
    assert detail is not None
    fields = [
        field
        for group in detail["groups"]
        for field in group["fields"]
        if field["field_id"] == FIELD
    ]
    represented = {
        field.get("subject", {}).get("analysis_subject_id")
        for field in fields
        if field.get("subject", {}).get("recorded")
    }
    assert represented == {SUBJECT_A, SUBJECT_B}, represented
    assert {field["score"] for field in fields} == {2, 9}, (
        "both original scores must stay visible side by side"
    )
    assert all(field.get("ambiguous") for field in fields)
    assert {len(field["variants"]) for field in fields} == {2}, (
        "every detail row carries the full variant list for the UI"
    )
    assert FIELD in detail["score_summary"]["ambiguous_fields"]

    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["ambiguous"] is True
    assert entry["score"] is None, "no single score may be invented"
    assert {v["score"] for v in entry["variants"]} == {2, 9}
    assert {v["subject"]["analysis_subject_id"] for v in entry["variants"]} == {
        SUBJECT_A,
        SUBJECT_B,
    }

    result = _hit(paths, op=">=", value=8)
    assert result["total"] == 0, (
        "the imported 9 must not satisfy >=8 when no subject/scope was chosen"
    )
    assert result["condition_rules"]["outcome_counts"]["unknown"] == 1
    reasons = result["condition_rules"]["leaf_reasons"][FIELD]
    assert "status_ambiguous" in reasons, reasons


def test_swr4_reverse_order_import_keeps_the_newest_information_not_the_last_write(
    tmp_path: Path,
) -> None:
    paths = _bare_workspace(tmp_path / "reverse")
    # information_cutoff drives the "newest" ordering; observed_at is pinned by
    # the package contract (observed_at == execution.answered_at), so the two
    # rows differ only in information time — exactly the late-replay case.
    newer = _observation(
        "OBS_NEWER_FIRST",
        entity_id=E01,
        question_id="IQS_LEG",
        field_id=FIELD,
        score=4,
        request_id="REQ_NEW",
        attempt_id="ATT_NEW",
        extra={"information_cutoff": "2026-10-01"},
    )
    older = _observation(
        "OBS_OLDER_LATE",
        entity_id=E01,
        question_id="IQS_LEG",
        field_id=FIELD,
        score=9,
        request_id="REQ_OLD",
        attempt_id="ATT_OLD",
        extra={"information_cutoff": "2026-09-01"},
    )
    _accepted(paths, [newer, older])  # the OLD one is imported LAST

    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["observation_id"] == newer["observation_id"], (
        "a late replay of an old observation must never become 'latest'"
    )
    assert entry["score"] == 4
    assert entry.get("ambiguous") is not True, "same subject/scope/model/口径 is ONE group"

    result = _hit(paths, op=">=", value=8)
    assert result["total"] == 0, "the stale 9 must not qualify after a newer observation arrived"
    assert result["condition_rules"]["outcome_counts"]["fail"] == 1


def test_swr4_old_high_score_never_masks_a_newer_unknown(tmp_path: Path) -> None:
    paths = _bare_workspace(tmp_path / "stale_high")
    newer_unknown = _observation(
        "OBS_NEW_UNKNOWN",
        entity_id=E01,
        question_id="IQS_LEG",
        field_id=FIELD,
        score=None,
        status="insufficient_evidence",
        request_id="REQ_NEW_U",
        attempt_id="ATT_NEW_U",
        extra={"information_cutoff": "2026-10-01"},
    )
    old_high = _observation(
        "OBS_OLD_HIGH",
        entity_id=E01,
        question_id="IQS_LEG",
        field_id=FIELD,
        score=9,
        request_id="REQ_OLD_H",
        attempt_id="ATT_OLD_H",
        extra={"information_cutoff": "2026-09-01"},
    )
    _accepted(paths, [newer_unknown, old_high])  # the high score arrives LAST

    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["status"] == "insufficient_evidence"
    assert entry["score"] is None

    result = _hit(paths, op=">=", value=8)
    assert result["total"] == 0
    assert result["condition_rules"]["outcome_counts"]["unknown"] == 1


def test_swr4_two_models_on_one_question_are_not_blended(tmp_path: Path) -> None:
    paths = _bare_workspace(tmp_path / "models")

    def with_model(observation: dict, model: str, score: int, suffix: str) -> dict:
        observation["execution"] = dict(
            observation["execution"],
            model_resolved=model,
            model_requested=model,
            model_revision=f"{model}-1",
            attempt_id=f"ATT_{suffix}",
            request_id=f"REQ_{suffix}",
        )
        observation["answer"] = dict(observation["answer"], score=score)
        return observation

    first = with_model(
        _observation(
            "OBS_MODEL_A",
            entity_id=E01,
            question_id="IQS_LEG",
            field_id=FIELD,
            request_id="REQ_A",
            attempt_id="ATT_A",
        ),
        "model-alpha",
        3,
        "A",
    )
    second = with_model(
        _observation(
            "OBS_MODEL_B",
            entity_id=E01,
            question_id="IQS_LEG",
            field_id=FIELD,
            request_id="REQ_B",
            attempt_id="ATT_B",
        ),
        "model-beta",
        8,
        "B",
    )
    _accepted(paths, [first, second])

    detail = build_entity_detail(paths, E01)
    assert detail is not None
    rows = [
        field
        for group in detail["groups"]
        for field in group["fields"]
        if field["field_id"] == FIELD
    ]
    assert {row["model_resolved"] for row in rows} == {"model-alpha", "model-beta"}
    assert {row["score"] for row in rows} == {3, 8}

    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["ambiguous"] is True
    assert entry["score"] is None
    assert {v["model_resolved"] for v in entry["variants"]} == {"model-alpha", "model-beta"}

    result = _hit(paths, op=">=", value=8)
    assert result["total"] == 0, "model-beta's 8 must not be selected silently"
    assert result["condition_rules"]["outcome_counts"]["unknown"] == 1


def test_swr4_one_issuer_with_two_listings_stays_one_row(tmp_path: Path) -> None:
    paths = _bare_workspace(tmp_path / "listings")
    _accepted(paths, [_observation("obs_listing_score", entity_id=E01, score=8)])
    rows = search(build_profiles(paths), page=1, page_size=100)["rows"]
    e01 = [row for row in rows if row["entity_id"] == E01]
    assert len(e01) == 1, "A/H listings of one issuer collapse to ONE result row"
    assert {(s["market"], s["ticker"]) for s in e01[0]["securities"]} == {
        ("CN-A", "600745"),
        ("HK", "0700"),
    }


def test_swr4_two_issuers_sharing_a_display_name_are_never_merged(tmp_path: Path) -> None:
    paths = WorkspacePaths.from_root(tmp_path / "same_name")
    identity = QuickScanStore(paths)
    identity.migrate()
    for entity_id in ("ENT_SAME_A", "ENT_SAME_B"):
        entity = _seed_entity(entity_id, tickers=[f"{entity_id[-1]}0001"])
        entity["canonical_name"] = "Identical Holdings Ltd"
        bindings = entity.pop("_bindings")
        identity.save_entity(entity, source_bindings=bindings)
    QuickScanObservationStore(paths).migrate()
    _accepted(
        paths,
        [
            _observation("obs_same_a", entity_id="ENT_SAME_A", score=9),
            _observation("obs_same_b", entity_id="ENT_SAME_B", score=3),
        ],
    )

    rows = search(build_profiles(paths), page=1, page_size=100)["rows"]
    assert {row["entity_id"] for row in rows} == {"ENT_SAME_A", "ENT_SAME_B"}
    assert all(row["canonical_name"] == "Identical Holdings Ltd" for row in rows)
    by_id = {row["entity_id"]: row for row in rows}
    assert by_id["ENT_SAME_A"]["score_fields"][FIELD]["score"] == 9
    assert by_id["ENT_SAME_B"]["score_fields"][FIELD]["score"] == 3


def test_swr4_unknown_and_missing_facts_keep_their_original_meaning(tmp_path: Path) -> None:
    paths = _bare_workspace(tmp_path / "unknowns", E01, E02)
    _accepted(
        paths,
        [
            _observation(
                "obs_e02_unknown",
                entity_id=E02,
                question_id="IQS_LEG",
                field_id=FIELD,
                score=None,
                status="insufficient_evidence",
                request_id="REQ_U1",
                attempt_id="ATT_U1",
            ),
            _observation(
                "obs_e02_na",
                entity_id=E02,
                question_id="IQS_PUB",
                field_id="score.iqs_05",
                score=None,
                status="not_applicable",
                request_id="REQ_U2",
                attempt_id="ATT_U2",
                published=True,
            ),
        ],
    )
    detail = build_entity_detail(paths, E02)
    assert detail is not None
    statuses = {
        field["status"]
        for group in detail["groups"]
        for field in group["fields"]
        if field["field_id"] in {FIELD, "score.iqs_05"}
    }
    assert statuses == {"insufficient_evidence", "not_applicable"}

    e02 = _score_fields(paths)[E02]
    assert e02["score_fields"][FIELD]["score"] is None
    assert e02["facts_relations"] is False
    assert "facts_relations_unavailable" in e02["gaps"]
    assert _field_for("FACT_10") not in e02["score_fields"]


# ------------------------------------------------- SR02-1 boundary cases ----


def _boundary_observations(dimension: str) -> list[dict]:
    """The frozen intake counterexamples: two legal observations on ONE
    entity/field that differ only by an incomparable dimension (segment A/B,
    FY2025 vs 2026H1 under cutoff 2026-09-30, or current vs normalized for the
    same 2026H1). Scores are 2 then 9 — never blended, never averaged, never
    silently resolved to the newest high score.
    """
    observations = []
    for index, score in enumerate((2, 9)):
        extra, answer_extra = {}, {}
        if dimension == "segment":
            extra = {"scope": "segment", "segment_id": "SEG_A" if index == 0 else "SEG_B"}
        elif dimension == "period":
            answer_extra = {
                "period_start": "2025-01-01" if index == 0 else "2026-01-01",
                "period_end": "2025-12-31" if index == 0 else "2026-06-30",
                "basis": "current",
            }
        else:
            answer_extra = {
                "period_start": "2026-01-01",
                "period_end": "2026-06-30",
                "basis": "current" if index == 0 else "normalized",
            }
        observations.append(
            _observation(
                "OBS_BOUNDARY_" + dimension + str(index),
                entity_id=E01,
                question_id="IQS_LEG",
                field_id=FIELD,
                score=score,
                request_id="REQ_" + dimension + str(index),
                attempt_id="ATT_" + dimension + str(index),
                extra=extra,
                answer_extra=answer_extra,
            )
        )
    return observations


def _field_rows(paths: WorkspacePaths, field_id: str = FIELD) -> list[dict]:
    detail = build_entity_detail(paths, E01)
    assert detail is not None
    return [
        field
        for group in detail["groups"]
        for field in group["fields"]
        if field["field_id"] == field_id
    ]


@pytest.mark.parametrize("dimension", ["segment", "period", "basis"])
def test_public_import_never_blends_incomparable_segments_periods_or_basis(
    tmp_path: Path, dimension: str
) -> None:
    paths = _bare_workspace(tmp_path / dimension)
    _accepted(paths, _boundary_observations(dimension))

    fields = _field_rows(paths)
    assert {field["score"] for field in fields} == {2, 9}, (
        "incomparable accepted values disappeared from the detail view"
    )
    assert all(field.get("ambiguous") is True for field in fields)
    assert {len(field["variants"]) for field in fields} == {2}

    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["score"] is None and entry["status"] == "ambiguous", (
        "no comparable dimension was chosen, so no single score may be emitted"
    )
    assert {variant["score"] for variant in entry["variants"]} == {2, 9}

    result = _hit(paths, op=">=", value=8)
    assert not result["rows"], "an unselected high-scoring variant entered the whitelist"
    assert result["condition_rules"]["outcome_counts"]["unknown"] == 1


@pytest.mark.parametrize(("index", "qualifies"), [(0, False), (1, True)])
def test_explicitly_selected_single_comparable_variant_decides_the_condition(
    tmp_path: Path, index: int, qualifies: bool
) -> None:
    """The public interface has NO safe query-time variant selection, so an
    explicit choice is expressed by storing ONLY that comparable variant:
    choosing the low 2 never satisfies >=8, choosing the high 9 does.
    """
    chosen = _boundary_observations("segment")[index]
    score = int(chosen["answer"]["score"])
    paths = _bare_workspace(tmp_path / f"chosen_{score}")
    _accepted(paths, [chosen])

    fields = _field_rows(paths)
    assert len(fields) == 1 and fields[0].get("ambiguous") is not True
    entry = _score_fields(paths)[E01]["score_fields"][FIELD]
    assert entry["score"] == score and entry["status"] == "scored"

    result = _hit(paths, op=">=", value=8)
    assert bool(result["rows"]) is qualifies, (
        f"selected variant score={score} must {'hit' if qualifies else 'miss'} >=8"
    )
    assert result["condition_rules"]["outcome_counts"] == (
        {"pass": 1, "fail": 0, "unknown": 0} if qualifies else {"pass": 0, "fail": 1, "unknown": 0}
    )


def test_single_plain_entity_observation_still_qualifies_for_a_condition(
    tmp_path: Path,
) -> None:
    paths = _bare_workspace(tmp_path / "single_plain")
    _accepted(
        paths,
        [
            _observation(
                "OBS_PLAIN_SINGLE",
                entity_id=E01,
                question_id="IQS_LEG",
                field_id=FIELD,
                score=8,
                request_id="REQ_PLAIN",
                attempt_id="ATT_PLAIN",
            )
        ],
    )
    result = _hit(paths, op=">=", value=8)
    assert [row["entity_id"] for row in result["rows"]] == [E01]
    assert result["condition_rules"]["outcome_counts"] == {"pass": 1, "fail": 0, "unknown": 0}
