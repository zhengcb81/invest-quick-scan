"""Tests for the owner-review pack builder and the decision-ledger applier."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pipeline_review_pack as prp  # noqa: E402
import pipeline_review_apply as pra  # noqa: E402


def _manifest(modules, entity_id="ENT_x", company="X"):
    return {
        "schema_version": "3.1",
        "module_package_id": "pkg_test",
        "module_release_id": "qrel_test",
        "mode": "full",
        "modules": modules,
        "profile": {"entity_id": entity_id, "company": company, "as_of": "2026-10-18"},
        "questions": [{"id": "IQS_01", "construct_id": "IQS_01", "comparison_role": "core"}],
    }


def _snapshot(cells):
    return {
        "schema_version": "1.0.0",
        "snapshot_id": "applicsnap_test",
        "inputs": {"attributes_version": "attr_t", "predicate_version": "pred_t",
                   "catalog_sha256": "c" * 64, "policy_sha256": "p" * 64,
                   "roster_sha256": "r" * 64, "overrides_version": "ovr_t"},
        "cells": cells,
    }


def _cell(entity_id, module_id, state, kind="predicate_true"):
    return {
        "entity_id": entity_id,
        "module_id": module_id,
        "state": state,
        "source": "auto",
        "basis": {"kind": kind, "reason": f"{module_id}: {state}"},
    }


@pytest.fixture()
def sample(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(_manifest(["common", "industrial"])), encoding="utf-8")
    snapshot = tmp_path / "s.json"
    snapshot.write_text(json.dumps(_snapshot([
        _cell("ENT_x", "common", "applicable", "common_always_applicable"),
        _cell("ENT_x", "industrial", "unknown", "negative_evidence_not_verified"),
        _cell("ENT_x", "scaling", "applicable"),
    ])), encoding="utf-8")
    return manifest, snapshot


def test_pack_contains_every_disagreement_with_ids_and_labels(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"

    pack = prp.build_pack([manifest], snapshot, out)

    assert pack["row_count"] == 2
    rows = [row for co in pack["companies"] for row in co["rows"]]
    by_module = {row["module_id"]: row for row in rows}
    assert set(by_module) == {"industrial", "scaling"}
    assert by_module["industrial"]["category_label"] == "组装已选，快照不适用/不可判"
    assert by_module["scaling"]["category_label"] == "快照适用，组装未选"
    assert pack["snapshot"]["snapshot_id"] == "applicsnap_test"
    assert pack["snapshot"]["sha256"] == prp._sha256_file(snapshot)


def test_pack_writes_pack_json_and_selfcontained_html(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"

    prp.build_pack([manifest], snapshot, out)

    assert (out / "pack.json").is_file()
    html = (out / "review.html").read_text(encoding="utf-8")
    # self-contained: pack data embedded, no external srcipt/link
    assert "const PACK = " in html
    assert 'src="' not in html and 'href="http' not in html
    assert "industrial" in html and "scaling" in html
    assert "导出 decisions.json" in html


def test_pack_multiple_companies_keep_rows_separate(tmp_path):
    m1 = tmp_path / "m1.json"
    m1.write_text(json.dumps(_manifest(["common", "auto"], "ENT_a", "Alpha")), encoding="utf-8")
    m2 = tmp_path / "m2.json"
    m2.write_text(json.dumps(_manifest(["common", "bank"], "ENT_b", "Beta")), encoding="utf-8")
    snapshot = tmp_path / "s.json"
    snapshot.write_text(json.dumps(_snapshot([
        _cell("ENT_a", "common", "applicable", "common_always_applicable"),
        _cell("ENT_a", "auto", "unknown", "attribute_unresolved"),
        _cell("ENT_b", "common", "applicable", "common_always_applicable"),
        _cell("ENT_b", "bank", "unknown", "negative_evidence_not_verified"),
    ])), encoding="utf-8")
    out = tmp_path / "review-packs" / "r2"

    pack = prp.build_pack([m1, m2], snapshot, out)

    assert len(pack["companies"]) == 2
    assert pack["companies"][0]["company"] == "Alpha"
    assert pack["companies"][1]["company"] == "Beta"
    assert pack["companies"][1]["rows"][0]["row_id"] == "R002"


def test_apply_writes_ledger_with_verbatim_reason(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "module_id": "industrial", "decision": "keep_composition",
             "reason": "保留组装，人工优先"},
            {"row_id": "R002", "module_id": "scaling", "decision": "known_deviation",
             "reason": "extra 旗标通道未建，先记录"},
        ],
    }), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"

    code, result = pra.apply_decisions(out / "pack.json", decisions, ledger_dir)

    assert code == 0
    assert result["rows_added"] == 2
    ledger = [json.loads(l) for l in (ledger_dir / f"{pack['pack_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(ledger) == 2
    assert ledger[0]["owner_reason_verbatim"] == "保留组装，人工优先"
    assert ledger[0]["snapshot_id"] == "applicsnap_test"
    assert ledger[0]["pack_sha256"] == prp._sha256_file(out / "pack.json")


def test_apply_rejects_missing_reason_or_bad_decision(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "  "},
            {"row_id": "R002", "decision": "whatever", "reason": "x"},
        ],
    }), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"

    code, result = pra.apply_decisions(out / "pack.json", decisions, ledger_dir)

    assert code == 2
    assert result["status"] == "incomplete"
    assert {x["problem"] for x in result["incomplete"]} == {"reason is empty", "invalid decision: 'whatever'"}
    assert not list(ledger_dir.iterdir()) if ledger_dir.exists() else True


def test_apply_is_idempotent_for_identical_resubmission(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    doc = {
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "人工优先"},
            {"row_id": "R002", "decision": "known_deviation", "reason": "通道未建"},
        ],
    }
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps(doc), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"

    first = pra.apply_decisions(out / "pack.json", decisions, ledger_dir)
    second = pra.apply_decisions(out / "pack.json", decisions, ledger_dir)

    assert first[0] == 0 and second[0] == 0
    assert second[1]["rows_added"] == 0
    assert second[1]["rows_idempotent"] == 2


def test_apply_partial_writes_complete_rows_and_reports_pending(sample, tmp_path):
    """A blank reason must not sink the whole batch: complete rows land, blanks stay pending."""
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "人工优先"},
            {"row_id": "R002", "decision": "adopt_snapshot", "reason": ""},
        ],
    }), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"

    code, result = pra.apply_decisions(out / "pack.json", decisions, ledger_dir, allow_partial=True)

    assert code == 2
    assert result["status"] == "partial"
    assert result["rows_added"] == 1
    assert [p["row_id"] for p in result["pending"]] == ["R002"]
    ledger = [json.loads(l) for l in (ledger_dir / f"{pack['pack_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["row_id"] for r in ledger] == ["R001"]


def test_apply_partial_then_complete_the_pending_row(sample, tmp_path):
    """A follow-up decisions file may add the previously pending row."""
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    ledger_dir = tmp_path / "ledger"
    first = tmp_path / "d1.json"
    first.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "人工优先"},
            {"row_id": "R002", "decision": "adopt_snapshot", "reason": ""},
        ],
    }), encoding="utf-8")
    pra.apply_decisions(out / "pack.json", first, ledger_dir, allow_partial=True)

    second = tmp_path / "d2.json"
    second.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R002", "decision": "adopt_snapshot", "reason": "机器学习平台是真实业务"},
        ],
    }), encoding="utf-8")
    code, result = pra.apply_decisions(out / "pack.json", second, ledger_dir)

    assert code == 0
    assert result["rows_added"] == 1
    ledger = [json.loads(l) for l in (ledger_dir / f"{pack['pack_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {r["row_id"]: r["owner_reason_verbatim"] for r in ledger} == {
        "R001": "人工优先", "R002": "机器学习平台是真实业务"
    }


def test_apply_strict_still_rejects_the_whole_batch(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "人工优先"},
            {"row_id": "R002", "decision": "adopt_snapshot", "reason": ""},
        ],
    }), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"

    code, result = pra.apply_decisions(out / "pack.json", decisions, ledger_dir)

    assert code == 2 and result["status"] == "incomplete"
    assert not ledger_dir.exists()


def test_apply_conflicts_with_a_different_verdict_are_rejected(sample, tmp_path):
    manifest, snapshot = sample
    out = tmp_path / "review-packs" / "r1"
    pack = prp.build_pack([manifest], snapshot, out)
    ledger_dir = tmp_path / "ledger"
    doc_v1 = {
        "schema": "pipeline-review-decisions/1.0.0",
        "pack_id": pack["pack_id"],
        "decisions": [
            {"row_id": "R001", "decision": "keep_composition", "reason": "人工优先"},
            {"row_id": "R002", "decision": "known_deviation", "reason": "通道未建"},
        ],
    }
    v1 = tmp_path / "d1.json"
    v1.write_text(json.dumps(doc_v1), encoding="utf-8")
    pra.apply_decisions(out / "pack.json", v1, ledger_dir)

    doc_v2 = json.loads(json.dumps(doc_v1))
    doc_v2["decisions"][0]["decision"] = "adopt_snapshot"
    v2 = tmp_path / "d2.json"
    v2.write_text(json.dumps(doc_v2), encoding="utf-8")

    code, result = pra.apply_decisions(out / "pack.json", v2, ledger_dir)

    assert code == 2
    assert result["status"] == "conflict"
    # original verdict untouched
    ledger = [json.loads(l) for l in (ledger_dir / f"{pack['pack_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert ledger[0]["decision"] == "keep_composition"
