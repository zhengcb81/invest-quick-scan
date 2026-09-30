from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import g0_candidate_manifest as manifest


def test_reviewed_candidate_bytes_remain_immutable_after_g0():
    historical_manifest = ROOT / "docs/implementation/reviews/G0/archive/candidate-snapshot-2026-09-23.json"
    assert hashlib.sha256(historical_manifest.read_bytes()).hexdigest().upper() == (
        "3DE13B1596CEB1EEA0A9A66B46E957334DBE245DB094476C07527564A23C1EB3"
    )
    historical_report = ROOT / "docs/implementation/reviews/G0/archive/independent-final-review-2026-09-23.md"
    report = historical_report.read_text(encoding="utf-8")
    assert "decision: `verified`" in report
    assert "3DE13B1596CEB1EEA0A9A66B46E957334DBE245DB094476C07527564A23C1EB3" in report


def test_current_scope_can_render_a_complete_self_consistent_candidate():
    assert manifest.verify(manifest.render()) == []


def test_missing_or_extra_artifact_breaks_scope_equality():
    value = manifest.render()
    omitted = next(iter(value["artifact_hashes"]))
    value["artifact_hashes"].pop(omitted)
    assert any("missing from manifest" in error for error in manifest.verify(value))
    value = manifest.render()
    value["artifact_hashes"]["unscoped.file"] = "0" * 64
    assert any("outside declared scope" in error for error in manifest.verify(value))


def test_changed_hash_is_detected():
    value = copy.deepcopy(manifest.render())
    path = next(iter(value["artifact_hashes"]))
    value["artifact_hashes"][path] = "0" * 64
    assert manifest.verify(value) == [f"hash mismatch: {path}"]


def test_persistent_test_fixtures_are_in_candidate_scope():
    fixture_paths = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tests/fixtures").glob("**/*")
        if path.is_file()
    }
    candidate = manifest.render()
    assert fixture_paths
    assert fixture_paths.issubset(candidate["artifact_hashes"])
    assert manifest.verify(candidate) == []


def test_every_g0_read_first_input_is_in_declared_scope_and_manifest(monkeypatch):
    plan = json.loads((ROOT / "docs/implementation/tasks.json").read_text(encoding="utf-8"))
    g0 = next(task for task in plan["tasks"] if task["id"] == "G0")
    required = set(g0["read_first"])
    candidate = manifest.render()
    assert required == {
        "docs/stock-pool-design.md",
        "docs/universe-and-operations-design.md",
    }
    assert required.issubset(candidate["artifact_hashes"])
    assert manifest.verify(candidate) == []

    monkeypatch.setattr(
        manifest,
        "PATTERNS",
        tuple(pattern for pattern in manifest.PATTERNS if pattern not in required),
    )
    incomplete = manifest.render()
    errors = manifest.verify(incomplete)
    assert any("G0 read_first inputs outside declared scope" in error for error in errors)


def test_mutable_journals_and_postseal_g0_artifacts_are_excluded():
    expected_excluded = {
        "task_plan.md",
        "progress.md",
        "findings.md",
        "docs/implementation/reviews/G0/candidate-snapshot.json",
        "docs/implementation/reviews/G0/independent-final-review.md",
        "docs/implementation/reviews/G0/independent-final-review.json",
        "docs/implementation/contracts/receipt-G0.json",
        "docs/implementation/contracts/validation-G0-final-r1-2026-09-26.json",
    }
    assert expected_excluded == manifest.EXCLUDED
    assert expected_excluded.isdisjoint(manifest.scope_paths())


def test_g0_candidate_excludes_downstream_validation_and_review_outputs():
    plan = json.loads((ROOT / "docs/implementation/tasks.json").read_text(encoding="utf-8"))
    downstream = manifest._downstream_task_ids(plan)
    candidate = manifest.render()

    assert {"S01", "S04"} <= downstream
    assert "C01" not in downstream
    for task_id in downstream:
        assert f"docs/implementation/contracts/receipt-{task_id}.json" not in candidate["scope_exclusions"]
        assert f"docs/implementation/contracts/validation-{task_id}-*" in candidate["scope_exclusions"]
        assert f"docs/implementation/reviews/{task_id}/**" in candidate["scope_exclusions"]
    assert "docs/implementation/contracts/receipt-C01.json" in candidate["artifact_hashes"]
    assert "scripts/question_sets.py" in candidate["artifact_hashes"]
    assert "tests/test_question_sets.py" in candidate["artifact_hashes"]
    assert manifest.verify(candidate) == []

    reintroduced = copy.deepcopy(candidate)
    reintroduced["artifact_hashes"]["unscoped.file"] = "0" * 64
    assert any("outside declared scope" in error for error in manifest.verify(reintroduced))


def test_g0_future_descendant_validation_exclusions_are_derived_from_dependency_graph():
    plan = {"tasks": [
        {"id": "G0", "depends_on": []},
        {"id": "S01", "depends_on": ["G0"]},
        {"id": "FUTURE", "depends_on": ["S01"]},
    ]}
    exclusions = set(manifest.scope_exclusions(plan))
    assert "docs/implementation/contracts/receipt-S01.json" not in exclusions
    assert "docs/implementation/contracts/validation-FUTURE-*" in exclusions


@pytest.mark.parametrize("dependency", ["MISSING", 17])
def test_g0_candidate_refuses_unknown_or_non_string_dependency_ids(dependency):
    plan = {"tasks": [
        {"id": "G0", "depends_on": []},
        {"id": "FUTURE", "depends_on": [dependency]},
    ]}
    with pytest.raises(ValueError, match="dependency"):
        manifest._downstream_task_ids(plan)


def test_g0_candidate_omits_actual_descendant_validation_files(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "ROOT", tmp_path)
    contract_dir = tmp_path / "docs/implementation/contracts"
    contract_dir.mkdir(parents=True)
    (tmp_path / "SKILL.md").write_text("fixture", encoding="utf-8")
    plan = {"version": "test", "tasks": [
        {"id": "P00", "depends_on": []},
        {"id": "G0", "depends_on": ["P00"], "read_first": ["SKILL.md"]},
        {"id": "S01", "depends_on": ["G0"]},
    ]}
    (tmp_path / "docs/implementation/tasks.json").write_text(
        json.dumps(plan), encoding="utf-8"
    )
    for filename in (
        "receipt-P00.json",
        "validation-P00-upstream.log",
        "receipt-S01.json",
        "validation-S01-current.log",
    ):
        (contract_dir / filename).write_text("fixture", encoding="utf-8")
    upstream_review_dir = tmp_path / "docs/implementation/reviews/P00"
    downstream_review_dir = tmp_path / "docs/implementation/reviews/S01"
    neighboring_review_dir = tmp_path / "docs/implementation/reviews/S01-extra"
    upstream_review_dir.mkdir(parents=True)
    downstream_review_dir.mkdir(parents=True)
    neighboring_review_dir.mkdir(parents=True)
    (upstream_review_dir / "review.json").write_text("upstream review", encoding="utf-8")
    (downstream_review_dir / "review.json").write_text("downstream review", encoding="utf-8")
    (neighboring_review_dir / "review.json").write_text("neighbor review", encoding="utf-8")

    candidate = manifest.render()
    assert "docs/implementation/contracts/receipt-P00.json" in candidate["artifact_hashes"]
    assert "docs/implementation/contracts/validation-P00-upstream.log" in candidate["artifact_hashes"]
    assert "docs/implementation/contracts/receipt-S01.json" in candidate["artifact_hashes"]
    assert "docs/implementation/contracts/validation-S01-current.log" not in candidate["artifact_hashes"]
    assert "docs/implementation/reviews/P00/review.json" in candidate["artifact_hashes"]
    assert "docs/implementation/reviews/S01/review.json" not in candidate["artifact_hashes"]
    assert "docs/implementation/reviews/S01-extra/review.json" in candidate["artifact_hashes"]
    assert manifest.verify(candidate) == []


def test_manifest_rejects_stale_version_or_tampered_scope_declaration():
    value = manifest.render()
    value["plan_version"] = "1.6.0"
    assert "manifest plan version does not match current plan" in manifest.verify(value)
    value = manifest.render()
    value["scope_patterns"] = []
    assert "manifest scope patterns do not match current declaration" in manifest.verify(value)
