"""U01/U02 real observation → query profile projection tests.

Binds the projection half of SW-READY-01: identities, listings, aliases,
analysis subjects and W05 observations arrive ONLY through the public import
entry points (no hand-written profiles), then the projection must keep original
scores/status/model/dates/versions/sources, dedup rows by entity_id without
name-merging, expose W06 freshness and W08 recovery output without inventing a
quality average, and feed W07 three-valued score conditions through
``quick_scan_query.search``.

Socket-bombed: browsing/projection never reaches an LLM or the network.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from test_quick_scan_observations import _observation, _package, _seed_entity

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_analysis import AnalysisSubjectStore, perimeter_sha256
from stockwiki.quick_scan_evidence import QuickScanEvidenceStore
from stockwiki.quick_scan_import import import_package
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_profiles import (
    build_entity_detail,
    build_profiles,
)
from stockwiki.quick_scan_query import QueryError, search
from stockwiki.quick_scan_store import QuickScanStore

E01 = "ENT_11111111-1111-4111-8111-111111111111"
E02 = "ENT_22222222-2222-4222-8222-222222222222"
FRESHNESS_MISSING_DATE = "missing_date"

RECOVERY_QUESTION_IDS = ("RECOVERY_01", "RECOVERY_02", "RECOVERY_03", "RECOVERY_04")


def _no_network(monkeypatch) -> None:
    def _bomb(*args, **kwargs):
        raise AssertionError("network call attempted from quick-scan projection")

    monkeypatch.setattr(socket, "socket", _bomb)
    monkeypatch.setattr(socket, "create_connection", _bomb)


def _field_for(question_id: str) -> str:
    fixed = {"IQS_LEG": "score.iqs_01", "IQS_PUB": "score.iqs_05", "FACT_10": "facts.customers"}
    return fixed.get(question_id, f"score.{question_id.lower()}")


def _release() -> dict:
    questions = {
        "IQS_LEG": {
            "field_id": _field_for("IQS_LEG"),
            "scope": "entity",
            "response_kind": "score",
        },
        "IQS_PUB": {
            "field_id": _field_for("IQS_PUB"),
            "scope": "entity",
            "response_kind": "score",
            "rubric_version": "1.0.0",
            "construct_id": "IQS_05",
            "definition_sha256": "d" * 64,
            "semantic_sha256": "a" * 64,
        },
        "FACT_10": {
            "field_id": _field_for("FACT_10"),
            "scope": "entity",
            "response_kind": "fact",
        },
    }
    for qid in ("IQS_06", "IQS_16", *RECOVERY_QUESTION_IDS):
        questions[qid] = {
            "field_id": _field_for(qid),
            "scope": "entity",
            "response_kind": "score",
        }
    return {
        "module_package_id": "modpkg_fixture_0001",
        "release_id": "rel_fixture_1",
        "catalog_version": "3.0.0",
        "semantic_fingerprint_version": "2.0.0",
        "questions": questions,
    }


def _score(
    entity_id: str,
    qid: str,
    score: int | None,
    *,
    status: str = "scored",
    request_id: str,
    attempt_id: str,
    observation_id: str,
    evidence: list[dict] | None = None,
) -> dict:
    return _observation(
        observation_id,
        entity_id=entity_id,
        question_id=qid,
        field_id=_field_for(qid),
        score=score,
        status=status,
        request_id=request_id,
        attempt_id=attempt_id,
        published=qid == "IQS_PUB",
        answer_extra={"evidence": evidence} if evidence else None,
    )


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.from_root(tmp_path)
    identity = QuickScanStore(paths)
    identity.migrate()
    for entity in (
        _seed_entity(E01, tickers=["600745", "0700"]),
        _seed_entity(E02, tickers=["600519"]),
    ):
        bindings = entity.pop("_bindings")
        identity.save_entity(entity, source_bindings=bindings)

    subjects = AnalysisSubjectStore(paths)
    subjects.migrate()
    consolidated = {
        "analysis_subject_schema_version": "1.0.0",
        "analysis_subject_id": "ASJ_11111111-1111-4111-8111-111111111111",
        "analysis_subject_revision": 1,
        "display_name": "Same display name",
        "primary_issuer_id": E01,
        "anchor_listing_id": None,
        "scope_kind": "consolidated_reporting_group",
        "scope_as_of": "2026-09-30T00:00:00Z",
        "perimeter_coverage": "not_enumerated",
        "memberships": [
            {
                "entity_id": E01,
                "role": "primary_issuer",
                "valid_from": None,
                "valid_to": None,
                "evidence_ref": "https://example.invalid/consolidated",
            }
        ],
    }
    receipt = {
        "receipt_id": "PRC_1111111111111111111111111111111111111111111111111111111111111111",
        "status": "verified",
        "analysis_subject_id": consolidated["analysis_subject_id"],
        "analysis_subject_revision": 1,
        "primary_issuer_id": E01,
        "evidence_ref": "https://example.invalid/consolidated",
        "perimeter_sha256": perimeter_sha256(consolidated),
        "decision_ref": "sw-ready-01-fixture",
    }
    subjects.import_subject(
        identity,
        {"analysis_subject": consolidated, "perimeter_receipt": receipt},
        at="2026-10-06T01:00:00Z",
    )
    security = identity.get_entity(E01)["securities"][0]
    from stockwiki.identity_snapshot import listing_id_for_security

    provisional = dict(
        consolidated,
        analysis_subject_id="ASJ_22222222-2222-4222-8222-222222222222",
        scope_kind="provisional_listing_scope",
        anchor_listing_id=listing_id_for_security(security),
        perimeter_coverage="not_applicable",
    )
    receipt2 = dict(
        receipt,
        receipt_id="PRC_2222222222222222222222222222222222222222222222222222222222222222",
        analysis_subject_id=provisional["analysis_subject_id"],
        evidence_ref="https://example.invalid/provisional",
        perimeter_sha256=perimeter_sha256(provisional),
    )
    subjects.import_subject(
        identity,
        {"analysis_subject": provisional, "perimeter_receipt": receipt2},
        at="2026-10-06T02:00:00Z",
    )

    evidence = QuickScanEvidenceStore(paths)
    evidence.migrate()
    evidence.record_identity_evidence(
        aliases=[
            {
                "alias_name": "中微半导体",
                "alias_type": "trading_short_name",
                "language": "zh",
                "entity_id": E01,
                "source_namespace": "dayu",
                "source_record_id": "row:1",
                "valid_from": None,
                "valid_to": None,
                "recorded_at": "2026-10-06T00:00:00Z",
            }
        ],
        identity_store=identity,
    )

    observations = QuickScanObservationStore(paths)
    observations.migrate()
    import_package(
        observations,
        _package(
            [
                _score(
                    E01,
                    "IQS_LEG",
                    8,
                    request_id="REQ_A1",
                    attempt_id="ATT_A1",
                    observation_id="obs_p_iqs_leg",
                    evidence=[
                        {
                            "id": "e1",
                            "title": "安全来源",
                            "url": "https://example.invalid/source-a",
                            "published_at": "2026-09-01",
                            "claim": "短依据",
                        },
                        {
                            "id": "e2",
                            "title": "注入来源",
                            "url": "javascript:alert(1)",
                            "published_at": None,
                            "claim": "必须被丢弃",
                        },
                    ],
                ),
                _score(
                    E01,
                    "IQS_PUB",
                    6,
                    request_id="REQ_A2",
                    attempt_id="ATT_A2",
                    observation_id="obs_p_iqs_pub",
                ),
                _score(
                    E01,
                    "IQS_06",
                    2,
                    request_id="REQ_A3",
                    attempt_id="ATT_A3",
                    observation_id="obs_p_iqs_06",
                ),
                _score(
                    E01,
                    "IQS_16",
                    2,
                    request_id="REQ_A4",
                    attempt_id="ATT_A4",
                    observation_id="obs_p_iqs_16",
                ),
                *[
                    _score(
                        E01,
                        qid,
                        score,
                        request_id=f"REQ_{qid}",
                        attempt_id=f"ATT_{qid}",
                        observation_id=f"obs_p_{qid.lower()}",
                    )
                    for qid, score in zip(RECOVERY_QUESTION_IDS, (7, 8, 7, 7), strict=True)
                ],
                _observation(
                    "obs_p_e02_unknown",
                    entity_id=E02,
                    question_id="IQS_LEG",
                    field_id="score.iqs_01",
                    score=None,
                    status="insufficient_evidence",
                    request_id="REQ_B1",
                    attempt_id="ATT_B1",
                ),
                _observation(
                    "obs_p_e02_na",
                    entity_id=E02,
                    question_id="IQS_PUB",
                    field_id="score.iqs_05",
                    score=None,
                    status="not_applicable",
                    request_id="REQ_B2",
                    attempt_id="ATT_B2",
                    published=True,
                ),
            ]
        ),
        frozen_release=_release(),
        identity_store=identity,
    )
    return paths


def test_projection_keeps_score_status_model_dates_versions_and_sources(
    tmp_path: Path, monkeypatch
) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    profiles = {p["entity_id"]: p for p in build_profiles(paths)}
    assert set(profiles) == {E01, E02}

    e01 = profiles[E01]
    field = e01["score_fields"]["score.iqs_01"]
    assert field["score"] == 8 and field["status"] == "scored"
    assert field["provider"] and field["model_resolved"]
    assert field["versions"]["question_version"] == "1.0.0"
    assert field["versions"]["method_id"] and field["versions"]["template_version"]
    assert field["information_cutoff"] == "2026-09-30"
    assert field["observed_at"].endswith("Z")
    assert field["imported_at"]
    assert field["observation_id"] == _observation("obs_p_iqs_leg")["observation_id"]
    assert field["payload_sha256"]
    assert field["freshness"]["status"] == FRESHNESS_MISSING_DATE
    assert field["freshness"]["policy_available"] is False
    assert field["check_level"] == "unreviewed"

    published = e01["score_fields"]["score.iqs_05"]
    assert published["versions"]["module_release_id"] == "rel_fixture_1"
    assert published["versions"]["module_package_id"] == "modpkg_fixture_0001"

    e02 = profiles[E02]
    assert e02["score_fields"]["score.iqs_01"]["score"] is None
    assert e02["score_fields"]["score.iqs_01"]["status"] == "insufficient_evidence"
    assert e02["score_fields"]["score.iqs_05"]["status"] == "not_applicable"

    # Sources: only safe http(s) evidence survives projection.
    assert e01["citations"], "stored evidence URLs must surface as citations"
    assert all(c["url"].startswith(("https://", "http://")) for c in e01["citations"])

    # Aliases and both listings stay on one entity row (dedup by entity_id).
    assert e01["aliases"] == ["中微半导体"]
    assert {s["ticker"] for s in e01["securities"]} == {"600745", "0700"}
    assert len([p for p in profiles.values() if p["entity_id"] == E01]) == 1

    # Search by alias finds the same single row.
    result = search(list(profiles.values()), text="中微半导体")
    assert result["total"] == 1 and result["rows"][0]["entity_id"] == E01


def test_quality_is_never_invented_and_original_low_scores_survive(
    tmp_path: Path, monkeypatch
) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    profiles = {p["entity_id"]: p for p in build_profiles(paths)}
    e01 = profiles[E01]

    assert e01["quality_score"] is None
    assert e01["quality_verified"] is False
    card = e01["recovery_card"]
    assert card["quality_score"] is None
    assert "quality_score_missing" in card["gaps"]
    assert card["whitelist_eligible"] is False
    assert card["quality_gate_overridden"] is False
    assert card["reported_score_promoted"] is False
    low = {row["id"]: row["score"] for row in card["low_scores"]}
    assert low.get("IQS_06") == 2, "original low score must stay visible"
    watch = e01["recovery_watch"]
    assert watch["status"] != "not_assessed"
    assert watch["criteria"], "diagnostic criteria must be shown, not summarised away"
    assert e01["recovery_status"] == watch["status"]

    # Views stay independent: quality view empty, recovery view has E01.
    assert search(list(profiles.values()), view="quality")["total"] == 0
    recovery_rows = search(list(profiles.values()), view="recovery")["rows"]
    assert {row["entity_id"] for row in recovery_rows} == {E01}
    assert {
        row["entity_id"] for row in search(list(profiles.values()), view="all_relevant")["rows"]
    } == {E01, E02}

    gaps = {str(g) for g in e01["gaps"]}
    assert any("quality" in g for g in gaps), "missing quality summary must be a visible gap"


def test_two_subjects_stay_distinct_and_legacy_subject_is_not_fabricated(
    tmp_path: Path, monkeypatch
) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    detail = build_entity_detail(paths, E01)
    assert detail is not None
    subjects = {s["analysis_subject_id"]: s for s in detail["subjects"]}
    assert len(subjects) == 2, "same display name must never merge two subjects"
    kinds = sorted(s["scope_kind"] for s in subjects.values())
    assert kinds == ["consolidated_reporting_group", "provisional_listing_scope"]
    assert all(s["display_name"] == "Same display name" for s in subjects.values())

    # Legacy observation rows carry no subject binding: explicitly not recorded.
    assert all(
        row["subject"]["recorded"] is False for group in detail["groups"] for row in group["fields"]
    )
    assert all(
        "历史未记录" in row["subject"]["note"]
        for group in detail["groups"]
        for row in group["fields"]
    )


def test_detail_groups_rows_and_states_capability_gaps(tmp_path: Path, monkeypatch) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    detail = build_entity_detail(paths, E02)
    assert detail is not None
    groups = {g["key"]: g for g in detail["groups"]}
    assert "common" in groups and "facts" not in groups
    fields = {row["field_id"]: row for g in detail["groups"] for row in g["fields"]}
    unknown = fields["score.iqs_01"]
    assert unknown["status"] == "insufficient_evidence" and unknown["score"] is None
    assert unknown["freshness"]["status"] == FRESHNESS_MISSING_DATE
    na = fields["score.iqs_05"]
    assert na["status"] == "not_applicable" and na["score"] is None
    assert detail["capabilities"]["facts_available"] is False
    gaps = " ".join(str(g) for g in detail["gaps"])
    for marker in (
        "facts_relations_unavailable",
        "cross_version_comparison_unavailable",
        "history_view_unavailable",
        "quality_summary_unavailable",
        "freshness_policy_unavailable",
        "replacement_mapping_unavailable",
    ):
        assert marker in gaps, marker
    assert detail["llm_calls"] == 0 and detail["network_calls"] == 0

    detail_e01 = build_entity_detail(paths, E01)
    e01_groups = [g["key"] for g in detail_e01["groups"]]
    assert "diagnostics" in e01_groups, "RECOVERY_* questions must group as diagnostics"
    assert detail_e01["entity"]["entity_id"] == E01
    assert build_entity_detail(paths, "ENT_missing") is None


def test_search_score_conditions_are_three_valued_and_reversible(
    tmp_path: Path, monkeypatch
) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    profiles = build_profiles(paths)

    ge = search(
        profiles,
        conditions=[{"field": "score.iqs_01", "op": ">=", "value": 8}],
        condition_combine="all",
    )
    assert {row["entity_id"] for row in ge["rows"]} == {E01}
    assert ge["condition_rules"]["outcome_counts"] == {"pass": 1, "fail": 0, "unknown": 1}
    assert ge["condition_rules"]["rules_version"] == "quick_scan_rules/1.0.0"
    e01_row = next(r for r in ge["rows"] if r["entity_id"] == E01)
    assert e01_row["score_conditions"][0]["outcome"] == "pass"

    gt = search(
        profiles,
        conditions=[{"field": "score.iqs_01", "op": ">", "value": 8}],
        condition_combine="all",
    )
    assert gt["total"] == 0
    assert gt["condition_rules"]["outcome_counts"] == {"pass": 0, "fail": 1, "unknown": 1}

    both = search(
        profiles,
        conditions=[
            {"field": "score.iqs_01", "op": ">=", "value": 8},
            {"field": "score.iqs_05", "op": ">=", "value": 6},
        ],
        condition_combine="all",
    )
    assert {row["entity_id"] for row in both["rows"]} == {E01}
    either = search(
        profiles,
        conditions=[
            {"field": "score.iqs_01", "op": ">=", "value": 8},
            {"field": "score.iqs_05", "op": ">=", "value": 6},
        ],
        condition_combine="any",
    )
    assert {row["entity_id"] for row in either["rows"]} == {E01}

    # N/A and unknown never pass: E02 stays 待核实, never qualified.
    na = search(
        profiles,
        conditions=[{"field": "score.iqs_05", "op": ">=", "value": 1}],
        condition_combine="all",
    )
    assert {row["entity_id"] for row in na["rows"]} == {E01}
    assert na["condition_rules"]["outcome_counts"]["unknown"] == 1
    reasons = na["condition_rules"]["leaf_reasons"]["score.iqs_05"]
    assert reasons.get("not_applicable") == 1, "N/A is its own reason, never a miss"
    assert reasons.get("compared") == 1


def test_score_conditions_refuse_bad_shapes(tmp_path: Path, monkeypatch) -> None:
    _no_network(monkeypatch)
    paths = _workspace(tmp_path)
    profiles = build_profiles(paths)
    with pytest.raises(QueryError) as exc:
        search(profiles, conditions=[{"field": "score.iqs_01", "op": "~", "value": 8}])
    assert exc.value.error_code == "condition_unknown_operator"
    with pytest.raises(QueryError) as exc:
        search(profiles, conditions=[{"field": "score.iqs_01", "op": ">=", "value": "8"}])
    assert exc.value.error_code == "condition_threshold_not_number"
    with pytest.raises(QueryError) as exc:
        search(
            profiles,
            conditions=[{"field": "score.iqs_01", "op": ">=", "value": 8}],
            condition_combine="xor",
        )
    assert exc.value.error_code == "condition_combine_invalid"
    with pytest.raises(QueryError) as exc:
        search(profiles, conditions=[], condition_combine="all")
    assert exc.value.error_code == "conditions_shape"


def test_stale_score_never_counts_as_a_current_hit() -> None:
    """Unit-level: a known-expired value is unknown, not pass (过期不冒充有效)."""
    from stockwiki.quick_scan_query import search as query_search

    profiles = [
        {
            "entity_id": "ENT_stale",
            "canonical_name": "Stale Co",
            "identity_state": "verified",
            "securities": [],
            "score_fields": {
                "score.iqs_01": {
                    "field_id": "score.iqs_01",
                    "question_id": "IQS_LEG",
                    "status": "scored",
                    "score": 8,
                    "check_level": "unverified_model_output",
                    "freshness": {"status": "stale", "policy_available": True},
                }
            },
        }
    ]
    result = query_search(profiles, conditions=[{"field": "score.iqs_01", "op": ">=", "value": 8}])
    assert result["total"] == 0
    assert result["condition_rules"]["outcome_counts"] == {"pass": 0, "fail": 0, "unknown": 1}
    assert result["condition_rules"]["leaf_reasons"]["score.iqs_01"] == {"stale": 1}
