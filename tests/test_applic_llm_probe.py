"""Offline tests for the applicability LLM probe (model calls are injected)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import applic_llm_probe as probe  # noqa: E402


CATALOG = {
    "modules": [
        {"id": "common", "title": "通用核心", "applies_when": "所有公司"},
        {"id": "industrial", "title": "工业制造、自动化与专业设备", "applies_when": "资本品、机械等"},
        {"id": "software", "title": "软件、SaaS与IT服务", "applies_when": "按订阅、许可证解释"},
    ]
}

SNAPSHOT = {
    "snapshot_id": "applicsnap_test",
    "cells": [
        {"entity_id": "ENT_a", "module_id": "common", "state": "applicable"},
        {"entity_id": "ENT_a", "module_id": "industrial", "state": "unknown"},
        {"entity_id": "ENT_a", "module_id": "software", "state": "unknown"},
    ],
}

LEDGER = [
    {"entity_id": "ENT_a", "module_id": "industrial", "decision": "keep_composition",
     "owner_reason_verbatim": "电池制造业当然是制造业（工业）"},
    {"entity_id": "ENT_a", "module_id": "software", "decision": "known_deviation",
     "owner_reason_verbatim": "暂记"},
]


@pytest.fixture()
def env(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps(CATALOG, ensure_ascii=False), encoding="utf-8")
    snapshot = tmp_path / "snap.json"
    snapshot.write_text(json.dumps(SNAPSHOT), encoding="utf-8")
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in LEDGER), encoding="utf-8")
    return catalog, snapshot, ledger


def _fake_model(answer):
    calls = []

    def call(provider, prompt, max_tokens=0):
        calls.append({"provider": provider, "prompt": prompt, "max_tokens": max_tokens})
        return dict(answer, _usage={"prompt_tokens": 100, "completion_tokens": 50})

    call.calls = calls
    return call


def test_prompt_lists_every_module_with_its_rule():
    prompt = probe.build_prompt({"name": "X", "ticker": "1", "market": "M"}, probe.load_catalog(
        Path(__file__).resolve().parents[1] / "questions" / "catalog.json"), None)
    assert "industrial｜industries｜工业制造、自动化与专业设备｜资本品、机械、自动化、航空航天和国防装备等。" in prompt
    assert "必须覆盖上面列出的全部 48 个模块 id" in prompt


def test_snapshot_mapping_turns_rules_into_yes_no_unsure():
    states = probe.snapshot_state_map(
        {"cells": [
            {"entity_id": "E", "module_id": "a", "state": "applicable"},
            {"entity_id": "E", "module_id": "b", "state": "not_applicable"},
            {"entity_id": "E", "module_id": "c", "state": "unknown"},
            {"entity_id": "E", "module_id": "d", "state": "not_evaluated"},
            {"entity_id": "OTHER", "module_id": "e", "state": "applicable"},
        ]},
        "E",
    )
    assert states == {"a": "yes", "b": "no", "c": "unsure", "d": "unsure"}


def test_parse_answer_rejects_unknown_values_and_reports_missing():
    modules = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    parsed, missing = probe.parse_answer(
        {"modules": {"a": {"applies": "yes", "confidence": "high", "reason": "r"},
                     "b": {"applies": "maybe", "confidence": "high", "reason": "r"}}},
        modules,
    )
    assert parsed == {"a": {"applies": "yes", "confidence": "high", "reason": "r"}}
    assert missing == ["b", "c"]


def test_confidence_is_optional_and_normalised():
    modules = [{"id": "a"}, {"id": "b"}]
    parsed, _ = probe.parse_answer(
        {"modules": {"a": {"applies": "yes", "confidence": "HIGH", "reason": "r"},
                     "b": {"applies": "no", "confidence": "certain", "reason": "r"}}},
        modules,
    )
    assert parsed["a"]["confidence"] == "high"
    assert parsed["b"]["confidence"] is None


def test_ledger_implies_owner_verdicts_and_skips_known_deviation(tmp_path):
    ledger = tmp_path / "l.jsonl"
    ledger.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in LEDGER), encoding="utf-8")
    implied = probe.ledger_implied(ledger)
    assert implied[("ENT_a", "industrial")]["implied_applies"] == "yes"
    assert ("ENT_a", "software") not in implied  # known_deviation carries no applicability claim


def test_run_probe_compares_llm_snapshot_and_owner(env, tmp_path):
    catalog, snapshot, ledger = env
    model = _fake_model({"modules": {
        "common": {"applies": "yes", "reason": "所有公司"},
        "industrial": {"applies": "yes", "reason": "电池制造属于制造业"},
        "software": {"applies": "no", "reason": "非软件主业"},
    }})
    out = tmp_path / "out"

    report = probe.run_probe(
        companies=[{"name": "宁德时代", "ticker": "300750", "market": "XSHE", "entity_id": "ENT_a"}],
        snapshot_path=snapshot, catalog_path=catalog, ledger_path=ledger,
        out_dir=out, model_call=model, provider={"model": "fake"}, tag="T",
    )

    company = report["companies"][0]
    assert company["stats"] == {
        "cells": 3,
        "llm_agree_snapshot": 1,       # common yes==yes; industrial yes!=unsure, software no!=unsure
        "llm_disagree_snapshot": 2,
        "llm_unsure": 0,
        "adjudicated_rows": 1,          # industrial only (software is known_deviation)
        "llm_agree_owner": 1,           # LLM says industrial applies, owner implies yes
        "snapshot_agree_owner": 0,      # snapshot said unsure for industrial
    }
    assert (out / "prompt-T-ENT_a-0.txt").is_file()
    assert (out / "answer-T-ENT_a-0.json").is_file()
    assert report["usage"] == {"prompt_tokens": 100, "completion_tokens": 50}
    assert model.calls[0]["max_tokens"] == 12000


def test_chunked_calls_are_merged(env, tmp_path):
    """Splitting the module list must not lose rows or double-count usage."""
    catalog, snapshot, ledger = env
    seen = []

    def model(provider, prompt, max_tokens=0):
        seen.append(prompt)
        # answer only the modules named in this prompt slice
        block = {}
        for mid in ("common", "industrial", "software"):
            if f"- {mid}｜" in prompt:
                block[mid] = {"applies": "yes", "reason": "r"}
        return {"modules": block, "_usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    out = tmp_path / "out"
    report = probe.run_probe(
        companies=[{"name": "X", "ticker": "", "market": "", "entity_id": "ENT_a"}],
        snapshot_path=snapshot, catalog_path=catalog, ledger_path=ledger,
        out_dir=out, model_call=model, provider={"model": "fake"}, tag="C", chunk=2,
    )

    company = report["companies"][0]
    assert len(seen) == 2                     # 3 modules / chunk 2 -> 2 calls
    assert company["missing_modules"] == []
    assert report["usage"] == {"prompt_tokens": 20, "completion_tokens": 10}
    assert isinstance(company["prompt_sha256"], list) and len(company["prompt_sha256"]) == 2


def test_model_error_is_recorded_not_raised(env, tmp_path):
    catalog, snapshot, ledger = env
    out = tmp_path / "out"
    report = probe.run_probe(
        companies=[{"name": "X", "ticker": "", "market": "", "entity_id": "ENT_a"}],
        snapshot_path=snapshot, catalog_path=catalog, ledger_path=ledger,
        out_dir=out, model_call=lambda *a, **k: {"error": "model_truncated_no_content"},
        provider={"model": "fake"}, tag="T",
    )
    assert report["companies"][0]["error"] == "model_truncated_no_content"
    assert not (out / "answer-T-ENT_a.json").exists()
