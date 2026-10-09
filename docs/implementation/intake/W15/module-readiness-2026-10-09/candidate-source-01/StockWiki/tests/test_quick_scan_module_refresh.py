"""Real durable route/observation stores; producer/validator substituted only at boundary."""

import copy
import hashlib
import json
import sqlite3

import pytest
from test_quick_scan_routes import _raw, _routes, _workspace

from stockwiki.quick_scan_analysis import receipt_key
from stockwiki.quick_scan_import import canonical_sha256
from stockwiki.quick_scan_observations import QuickScanObservationStore

NOW = "2026-01-02T12:00:00Z"


def _question(qid, module="common"):
    return {
        "id": qid,
        "module_id": module,
        "scope": "entity",
        "rubric_version": "1.0.0",
        "metric_id": "score." + qid.lower(),
        "construct_id": qid,
        "semantic_sha256": hashlib.sha256(qid.encode()).hexdigest(),
        "definition_sha256": hashlib.sha256((qid + "def").encode()).hexdigest(),
        "prompt_sha256": hashlib.sha256((qid + "prompt").encode()).hexdigest(),
    }


def _activate(
    routes, identity, subject, questions, *, tag="route1", previous=None, segment_id=None
):
    raw, manifest = _raw(identity, subject, tag=tag)
    m = json.loads(manifest)
    if segment_id is not None:
        route = json.loads(raw)
        route.update(scope="segment", segment_id=segment_id)
        raw = json.dumps(route).encode()
        m["route_decision"] = route
    m.update(
        questions=questions,
        question_count=len(questions),
        template_version="catalog-" + tag,
        module_package_id="pkg_" + "a" * 64,
        module_release_id="modrel_" + "b" * 64,
        modules=sorted({q["module_id"] for q in questions}),
        module_locks=[
            {"module_id": mid, "version": "1.0.0"}
            for mid in sorted({q["module_id"] for q in questions})
        ],
        aggregation_policy="core-constructs-v1",
        quality_weights={"business": 1},
    )
    routes.record_snapshot(
        raw,
        json.dumps(m).encode(),
        subject_key=receipt_key(subject),
        expected_decision_id=m["route_decision_id"],
    )
    routes.set_current(
        m["route_decision_id"],
        subject_key=receipt_key(subject),
        expected_current_decision_id=previous,
        now_utc=NOW,
    )
    return m["route_decision_id"]


def _observe(
    store,
    identity,
    subject,
    question,
    *,
    model="M1",
    info="2025-12-31",
    status="scored",
    segment_id=None,
):
    # This boundary seeds actual observation storage; it does not certify a
    # released producer package or grant formal qualification.
    obs = {
        "observation_id": "obs_"
        + hashlib.sha256(
            (question["id"] + model + info + status + (segment_id or "")).encode()
        ).hexdigest(),
        "entity_id": subject["primary_issuer_id"],
        "identity_revision": 1,
        "analysis_subject": copy.deepcopy(subject),
        "field_id": question["metric_id"],
        "question_id": question["id"],
        "question_version": "1.0.0",
        "scope": "segment" if segment_id else "entity",
        "observed_at": "2026-01-01T12:00:00Z",
        "information_cutoff": info,
        "question_definition_sha256": question["definition_sha256"],
        "question_semantic_sha256": question["semantic_sha256"],
        "execution": {"provider": "P1", "model_resolved": model},
        "answer": {
            "status": status,
            "score": 8 if status == "scored" else None,
            "information_as_of": info,
        },
    }
    if segment_id:
        obs["segment_id"] = segment_id
    manifests = [
        json.loads(row["manifest_raw"])
        for row in _routes(identity).snapshots_for_subject(receipt_key(subject))
    ]
    m = next(
        m
        for m in manifests
        if any(
            q["id"] == question["id"] and q["semantic_sha256"] == question["semantic_sha256"]
            for q in m["questions"]
        )
    )
    obs.update(
        module_package_id=m["module_package_id"],
        module_release_id=m["module_release_id"],
        template_version=m["template_version"],
    )
    digest = canonical_sha256(obs)
    decision = {
        "status": "accepted",
        "package_id": "pkg_" + digest,
        "item_id": "itm_" + digest,
        "observation_id": obs["observation_id"],
        "payload_sha256": digest,
        "exec_key": digest,
        "observation": obs,
        "error_code": None,
    }
    store.apply_decisions([decision], identity_lookup=identity)
    return obs["observation_id"]


def _setup(tmp_path):
    identity, subject = _workspace(tmp_path)
    routes = _routes(identity)
    observations = QuickScanObservationStore(identity.paths)
    observations.migrate()
    return identity, subject, routes, observations


def _plan(routes, observations, subject, **kwargs):
    from stockwiki.quick_scan_module_refresh import plan_module_refresh

    return plan_module_refresh(
        routes,
        observations,
        subject_key=receipt_key(subject),
        scope=kwargs.pop("scope", "entity"),
        scope_id=kwargs.pop("scope_id", subject["primary_issuer_id"]),
        now_utc=kwargs.pop("now_utc", NOW),
        provider="P1",
        model=kwargs.pop("model", "M1"),
        ttl_hours=kwargs.pop("ttl_hours", 120),
        **kwargs,
    )


def test_added_module_only_dispatches_added_questions_and_keeps_core_observations(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    core = [_question(f"IQS_{i:02d}") for i in range(1, 25)]
    first = _activate(routes, identity, subject, core)
    ids = [_observe(observations, identity, subject, q) for q in core]
    extra = [_question("SEMI_01", "industry_semiconductor"), _question("GROW_01", "stage_growth")]
    _activate(routes, identity, subject, core + extra, tag="route2", previous=first)
    before = observations.counts()
    plan = _plan(routes, observations, subject)
    assert plan["totals"]["reuse"] == 24 and plan["totals"]["planned_dispatches"] == 2
    assert plan["module_changes"]["entered"] == ["industry_semiconductor", "stage_growth"]
    assert set(plan["comparison"]["retained_question_ids"]) == {q["id"] for q in core}
    assert plan["aggregation_policy"] == "core-constructs-v1"
    assert {
        row["reuse_observation_id"] for row in plan["fields"] if row["decision"] == "reuse"
    } == set(ids)
    assert observations.counts() == before and plan["dispatch_started"] is False
    assert _plan(routes, observations, subject) == plan


def test_segment_route_never_borrows_the_issuer_answer(tmp_path):
    identity, subject = _workspace(
        tmp_path, segments=[{"segment_id": "SEG_TEST", "segment_name": "Synthetic segment"}]
    )
    routes = _routes(identity)
    observations = QuickScanObservationStore(identity.paths)
    observations.migrate()
    question = _question("IQS_01")
    _activate(routes, identity, subject, [question], segment_id="SEG_TEST")
    issuer_id = _observe(observations, identity, subject, question)
    plan = _plan(routes, observations, subject, scope="segment", scope_id="SEG_TEST")
    assert plan["totals"]["reuse"] == 0 and plan["totals"]["planned_dispatches"] == 1
    segment_id = _observe(observations, identity, subject, question, segment_id="SEG_TEST")
    assert issuer_id != segment_id
    plan = _plan(routes, observations, subject, scope="segment", scope_id="SEG_TEST")
    assert plan["fields"][0]["reuse_observation_id"] == segment_id
    assert observations.counts()["observations"] == 2


def test_ttl_exact_boundary_new_model_and_removed_modules(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    core, overlay = _question("IQS_01"), _question("GROW_01", "stage_growth")
    first = _activate(routes, identity, subject, [core, overlay])
    _observe(observations, identity, subject, core)
    _observe(observations, identity, subject, overlay)
    assert _plan(routes, observations, subject)["totals"]["reuse"] == 2
    # Information time, not import time, bounds freshness.
    assert _plan(routes, observations, subject, ttl_hours=60)["totals"]["planned_dispatches"] == 2
    _activate(routes, identity, subject, [core], tag="route2", previous=first)
    plan = _plan(routes, observations, subject)
    assert plan["module_changes"]["exited"] == ["stage_growth"]
    assert plan["comparison"]["removed_question_ids"] == ["GROW_01"]
    assert observations.counts()["observations"] == 2 and len(plan["fields"]) == 1
    assert _plan(routes, observations, subject, model="M2")["totals"]["planned_dispatches"] == 1


def test_unknown_cooldown_and_unresolved_paid_work_take_priority(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    question = _question("IQS_01")
    _activate(routes, identity, subject, [question])
    _observe(observations, identity, subject, question, status="insufficient_evidence")
    work = {
        question["id"]: {
            "generation": 3,
            "status": "complete",
            "next_retry_at": "2026-01-03T12:00:00Z",
        }
    }
    plan = _plan(routes, observations, subject, work_items=work)
    assert plan["fields"][0]["decision"] == "deferred_unknown"
    due = _plan(routes, observations, subject, now_utc="2026-01-03T12:00:00Z", work_items=work)
    assert due["fields"][0]["decision"] == "dispatch_new_generation"
    assert due["fields"][0]["generation"] == 4
    work[question["id"]].update(status="uncertain")
    unresolved = _plan(
        routes, observations, subject, now_utc="2026-01-04T12:00:00Z", work_items=work
    )
    assert unresolved["fields"][0]["decision"] == "resume_existing_work"
    assert unresolved["totals"]["planned_dispatches"] == 0


def test_changed_meaning_is_incomparable_and_legacy_subjectless_does_not_reuse(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    question = _question("IQS_01")
    first = _activate(routes, identity, subject, [question])
    _observe(observations, identity, subject, question)
    changed = copy.deepcopy(question)
    changed["semantic_sha256"] = "e" * 64
    _activate(routes, identity, subject, [changed], tag="route2", previous=first)
    plan = _plan(routes, observations, subject)
    assert plan["comparison"]["meaning_changed_question_ids"] == ["IQS_01"]
    assert plan["totals"]["reuse"] == 0 and plan["totals"]["planned_dispatches"] == 1


def test_unbound_security_does_not_borrow_first_listing_and_rules_change_does_not_reask(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    core = _question("IQS_01")
    quote = _question("IQS_22")
    quote["scope"] = "security"
    first = _activate(routes, identity, subject, [core, quote])
    _observe(observations, identity, subject, core)
    plan = _plan(routes, observations, subject)
    assert plan["totals"]["reuse"] == 1 and plan["totals"]["deferred_scope_unbound"] == 1
    assert plan["totals"]["planned_dispatches"] == 0
    second = _activate(routes, identity, subject, [core], tag="route2", previous=first)
    assert second != first
    assert _plan(routes, observations, subject)["totals"]["reuse"] == 1


def test_tampered_observation_payload_named_refusal_and_no_unknown_reask(tmp_path):
    identity, subject, routes, observations = _setup(tmp_path)
    q = _question("IQS_01")
    _activate(routes, identity, subject, [q])
    obsid = _observe(observations, identity, subject, q, status="insufficient_evidence")
    plan = _plan(routes, observations, subject)
    assert plan["fields"][0]["decision"] == "manual_refresh_required"
    assert plan["totals"]["planned_dispatches"] == 0
    with sqlite3.connect(observations.database_path) as con:
        row = con.execute(
            "SELECT payload_json FROM quick_scan_observation WHERE observation_id=?", (obsid,)
        ).fetchone()
        payload = json.loads(row[0])
        payload["answer"]["status"] = "scored"
        payload["answer"]["score"] = 10
        con.execute(
            "UPDATE quick_scan_observation SET payload_json=? WHERE observation_id=?",
            (json.dumps(payload), obsid),
        )
    with pytest.raises(ValueError, match="refresh_observation_corrupted"):
        _plan(routes, observations, subject)
