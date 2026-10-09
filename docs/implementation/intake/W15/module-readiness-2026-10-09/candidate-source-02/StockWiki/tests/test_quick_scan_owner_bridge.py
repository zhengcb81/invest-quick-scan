"""Real IQS producer/owner OS CLI/executor SQLite. Synthetic answers; no HTTP.

The observation import fixture is a storage boundary, not a financial golden.
This tests first-party transport and execution actions, not source correctness.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest
from test_quick_scan_route_integration import NOW
from test_quick_scan_route_integration import actual_bundle as actual_bundle

from stockwiki.quick_scan_analysis import receipt_key
from stockwiki.quick_scan_import import canonical_sha256
from stockwiki.quick_scan_observations import QuickScanObservationStore


def _executor_root():
    path = Path(os.environ["IQS_W15_QA_CODE_ROOT"])
    assert path.is_dir()
    sys.path.insert(0, str(path))  # test fixture only; products use CLI transport


def _seed_actual_manifest_observation(routes, subject, manifest, question):
    store = QuickScanObservationStore(routes.identity.paths)
    store.migrate()
    payload = dict(
        observation_id="obs_" + hashlib.sha256(question["id"].encode()).hexdigest(),
        entity_id=subject["primary_issuer_id"],
        identity_revision=1,
        analysis_subject=subject,
        field_id=question["metric_id"],
        question_id=question["id"],
        question_version=question["rubric_version"],
        scope="entity",
        observed_at=NOW,
        information_cutoff="2026-10-08",
        question_semantic_sha256=question["semantic_sha256"],
        question_definition_sha256=question["definition_sha256"],
        module_package_id=manifest["module_package_id"],
        module_release_id=manifest["module_release_id"],
        template_version=manifest["template_version"],
        execution={"provider": "P1", "model_resolved": "M1"},
        answer={
            "question_id": question["id"],
            "status": "scored",
            "score": 8,
            "summary": "Synthetic original score, not a financial judgement",
            "information_as_of": "2026-10-08",
        },
    )
    digest = canonical_sha256(payload)
    store.apply_decisions(
        [
            dict(
                status="accepted",
                package_id="pkg_" + digest,
                item_id="itm_" + digest,
                observation_id=payload["observation_id"],
                payload_sha256=digest,
                exec_key=digest,
                observation=payload,
                error_code=None,
            )
        ],
        identity_lookup=routes.identity,
    )
    return store, payload


def test_owner_public_cli_reuse_and_only_selected_new_questions_reach_provider(
    actual_bundle, tmp_path
):
    _executor_root()
    from src.core.models import Question, SearchResult
    from src.core.qa_engine import QAEngine
    from src.runners.llm_runner import QuickScanWorkLifecycle
    from src.utils.quick_scan_owner_refresh import OwnerRefreshClient, OwnerRefreshRejected
    from src.utils.quick_scan_question_manifest import load_question_manifest
    from src.utils.quick_scan_work_store import QuickScanWorkStore

    routes, subject, raw, manifest_raw, decision_id, validator = actual_bundle
    key = receipt_key(subject)
    routes.record_snapshot(raw, manifest_raw, subject_key=key, expected_decision_id=decision_id)
    routes.set_current(decision_id, subject_key=key, expected_current_decision_id=None, now_utc=NOW)
    manifest = json.loads(manifest_raw)
    entity_questions = [q for q in manifest["questions"] if q["scope"] == "entity"]
    originals = [
        _seed_actual_manifest_observation(routes, subject, manifest, q)
        for q in entity_questions[:2]
    ]
    config = dict(
        protocol="stockqa.owner_refresh_config/1.0.0",
        stockwiki_code_root=str(Path(__file__).resolve().parents[1]),
        stockwiki_workspace_root=str(routes.identity.paths.root),
        iqs_code_root=str(validator.code_root),
        iqs_release_root=str(validator.release_root),
        subject_key=key,
        scope="entity",
        scope_id=subject["primary_issuer_id"],
        ttl_hours=120,
        runs_dir=str(tmp_path / "executor-temporary"),
    )
    config_file = tmp_path / "owner-config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    incoming = tmp_path / "manifest.json"
    incoming.write_bytes(manifest_raw)
    loaded = load_question_manifest(incoming)
    actual_refs = sorted(
        {
            row["source_binding_ref"]
            for row in routes.identity.get_entity(subject["primary_issuer_id"])["securities"]
        }
    )
    identity = dict(
        entity_id=subject["primary_issuer_id"],
        identity_revision=1,
        source_binding_version=1,
        identity_state="verified",
        source_binding_ref=actual_refs[0],
        source_binding_refs=actual_refs,
        identity_snapshot_sha256="a" * 64,
    )
    client = OwnerRefreshClient(config_file, process_env=dict(os.environ))
    store = QuickScanWorkStore(tmp_path / "work.sqlite")
    session = client.prepare(loaded, store, identity=identity, provider="P1", model="M1", now=NOW)
    assert (
        session.plan["totals"]["reuse"] == 2 and session.plan["totals"]["planned_dispatches"] == 19
    )
    assert session.plan["totals"]["deferred_scope_unbound"] == 3
    assert list(Path(config["runs_dir"]).iterdir()) == []

    class Provider:
        calls = 0

        def get_provider_name(self):
            return "synthetic-no-http-boundary"

        def search(self, query):
            self.calls += 1
            return [
                SearchResult(
                    title="test", snippet="Synthetic boundary response", score=8, status="scored"
                )
            ]

    provider = Provider()
    selected = [Question(text=q["prompt"], question_id=q["id"]) for q in entity_questions[:4]]
    generations = {
        qid: row["generation"]
        for qid, row in session.fields.items()
        if type(row.get("generation")) is int
    }
    lifecycle = QuickScanWorkLifecycle(
        store,
        entity_id=identity["entity_id"],
        run_id="RUN_1",
        scan_id="SCAN_1",
        identity=identity,
        provider_name="P1",
        model_requested="M1",
        scope_by_question=session.scope_bindings,
        generation_by_question=generations,
        owner_refresh_session=session,
    )
    batch = QAEngine(provider, work_item_lifecycle=lifecycle).process_questions(selected)
    assert provider.calls == 2
    from src.utils.quick_scan_owner_refresh import build_refresh_result

    wire = build_refresh_result(
        batch,
        session,
        dict(
            entity_id=identity["entity_id"],
            company_name="Synthetic",
            provider_name="P1",
            requested_model="M1",
            work_store=store,
        ),
    )
    assert wire["schema_version"] == "stockqa.owner_refresh_result/1.0.0"
    assert set(wire["observation_references"]) == {q["id"] for q in entity_questions[:2]}
    assert set(wire["dispatched_result"]["answers"]) == {q["id"] for q in entity_questions[2:4]}
    assert wire["original_observations_resealed"] is False
    assert batch.results[0].answer.source == "stockwiki_observation_reference"
    assert batch.results[0].answer.created_at.isoformat() == NOW.replace("Z", "+00:00")
    for original_store, original in originals:
        assert original_store.get_observation(original["observation_id"])["payload"] == original
    import sqlite3

    with sqlite3.connect(store.path) as con:
        assert con.execute("SELECT COUNT(*) FROM work_item").fetchone()[0] == 2
        assert con.execute("SELECT COUNT(*) FROM answer_checkpoint").fetchone()[0] == 0
    # No genuine HTTP receipt was supplied: the two boundary calls stay honest
    # unknown and a fresh first-party refresh resumes/defer them without calls.
    resumed = client.prepare(loaded, store, identity=identity, provider="P1", model="M1", now=NOW)
    second = QuickScanWorkLifecycle(
        store,
        entity_id=identity["entity_id"],
        run_id="RUN_2",
        scan_id="SCAN_1",
        identity=identity,
        scope_by_question=resumed.scope_bindings,
        owner_refresh_session=resumed,
    )
    QAEngine(provider, work_item_lifecycle=second).process_questions(selected)
    assert provider.calls == 2
    assert resumed.plan["totals"]["resume_existing_work"] == 2
    # A re-sealed local manifest cannot replace the independent owner current.
    mismatched = dict(loaded, manifest_sha256="e" * 64)
    with pytest.raises(OwnerRefreshRejected, match="owner_refresh_manifest_identity_mismatch"):
        client.prepare(mismatched, store, identity=identity, provider="P1", model="M1", now=NOW)
    with pytest.raises(OwnerRefreshRejected, match="owner_refresh_manifest_identity_mismatch"):
        client.prepare(
            loaded,
            store,
            identity=dict(
                identity, source_binding_ref="BND_WRONG", source_binding_refs=["BND_WRONG"]
            ),
            provider="P1",
            model="M1",
            now=NOW,
        )
