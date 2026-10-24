"""Tests for the applicability-pipeline cross-check tool."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import applic_pipeline_check as apc  # noqa: E402


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
def files(tmp_path):
    def write(doc, name):
        path = tmp_path / name
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return path
    return write


def test_full_agreement_exits_zero(files, capsys):
    manifest = files(_manifest(["common", "auto"]), "m.json")
    snap = files(_snapshot([
        _cell("ENT_x", "common", "applicable", "common_always_applicable"),
        _cell("ENT_x", "auto", "applicable"),
    ]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["rows_checked"] == 2
    assert out["disagreements"] == []
    assert out["summary"]["agree"] == 2


def test_snapshot_applicable_but_not_composed(files, capsys):
    manifest = files(_manifest(["common"]), "m.json")
    snap = files(_snapshot([
        _cell("ENT_x", "common", "applicable", "common_always_applicable"),
        _cell("ENT_x", "scaling", "applicable"),
    ]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["snapshot_only"] == 1
    assert out["disagreements"][0]["category"] == "snapshot_applicable_not_composed"
    assert out["disagreements"][0]["module_id"] == "scaling"


def test_composed_but_snapshot_not_applicable(files, capsys):
    manifest = files(_manifest(["common", "industrial"]), "m.json")
    snap = files(_snapshot([
        _cell("ENT_x", "common", "applicable", "common_always_applicable"),
        _cell("ENT_x", "industrial", "unknown", "negative_evidence_not_verified"),
    ]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["composed_not_applicable"] == 1
    assert out["disagreements"][0]["category"] == "composed_but_not_applicable"
    assert out["disagreements"][0]["snapshot_state"] == "unknown"


def test_unaligned_module_ids_are_reported_separately(files, capsys):
    """A composed module the snapshot has no axis for is an ID-level mismatch.

    The reverse (snapshot axis without a composition) is normal — the snapshot
    carries all 48 axes while a composition selects only a few — so it is not
    "unaligned"; its state decides (agreement or a classified disagreement).
    """
    manifest = files(_manifest(["common", "ghost_module"]), "m.json")
    snap = files(_snapshot([
        _cell("ENT_x", "common", "applicable", "common_always_applicable"),
        _cell("ENT_x", "phantom_axis", "unknown", "attribute_unresolved"),
    ]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert [d["category"] for d in out["unaligned"]] == ["composed_module_missing_in_snapshot"]
    assert out["unaligned"][0]["module_id"] == "ghost_module"
    # phantom_axis: unknown and not composed -> both sides exclude it = agreement
    assert out["summary"]["agree"] == 2


def test_bad_data_exits_three(files):
    manifest = files({"schema_version": "3.1", "modules": []}, "m.json")  # no questions
    snap = files(_snapshot([]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 3


def test_entity_id_mismatch_is_data_error(files):
    manifest = files(_manifest(["common"], entity_id="ENT_a"), "m.json")
    snap = files(_snapshot([_cell("ENT_b", "common", "applicable")]), "s.json")

    code = apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])

    assert code == 3


def test_versions_are_recorded(files, capsys):
    manifest = files(_manifest(["common"]), "m.json")
    snap = files(_snapshot([_cell("ENT_x", "common", "applicable")]), "s.json")

    apc.main(["--manifest", str(manifest), "--snapshot", str(snap)])
    out = json.loads(capsys.readouterr().out)

    assert out["manifest_identity"]["package_id"] == "pkg_test"
    assert out["snapshot_identity"]["inputs"]["predicate_version"] == "pred_t"
