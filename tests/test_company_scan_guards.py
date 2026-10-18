"""Pure negative preflight seams; no mock is a native owner positive."""

import copy
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT.parent.name == "production-task-candidate"
PROJECTS = next(
    p.parent for p in Path(__file__).resolve().parents if (p / "task_plan.md").is_file()
)
COMPANY = ROOT.parent / "company" if CANDIDATE else PROJECTS / "iqs-company-agent-lab"
BRIDGE = (
    Path(json.loads((ROOT.parent / "runtime.json").read_text(encoding="utf8"))["root"]) / "bridge"
    if CANDIDATE
    else PROJECTS / "iqs-agent-runtime-lab"
)
sys.path.insert(0, str(COMPANY / "src"))
sys.path.insert(0, str(BRIDGE / "src"))
spec = importlib.util.spec_from_file_location(
    "scan_engine_guard_fixture", ROOT / "scripts/shared_company_engine.py"
)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
from iqs_company_agent_lab.canonical import canonical_json, sha256_hex
from iqs_company_agent_lab.scan_profile import build_scan_profile
from iqs_company_agent_lab.task import LoadedTask


def task():
    q = {
        "id": "ORIGINAL_1",
        "module_id": "base",
        "question": "Original",
        "anchors": {},
        "evidence": [],
    }
    rows = [
        dict(
            question_id=q["id"],
            question=q,
            question_object_sha256=sha256_hex(q),
            module_id="base",
            module_version="1.0.0",
        )
    ]
    profile = build_scan_profile(
        rows,
        information_cutoff="2026-10-18",
        route_id="r",
        group_keys={q["id"]: ["issuer", "perimeter"]},
    )
    company = {"origin": "synthetic"}
    board = {"records": []}
    runtime = {"model": "m"}

    def ref(n, v):
        raw = canonical_json(v).encode("utf8")
        return dict(path=n, bytes=len(raw), sha256=sha256_hex(raw))

    raw = dict(
        protocol="iqs.company-scan-task/1.0.0",
        run_id="guard-test",
        experiment_id="guard-test",
        strategy_id="module_packs",
        information_cutoff="2026-10-18",
        limits=profile["resource_limits"],
        company_ref=ref("company.json", company),
        evidence_epoch_ref=ref("board.json", board),
        runtime_profile_ref=ref("runtime.json", runtime),
        execution_profile=profile,
        execution_profile_sha256=sha256_hex(profile),
    )
    return LoadedTask(raw, None, rows, company, board, runtime, {})


def config():
    return dict(
        protocol="iqs.agent-runtime-lab.session-config/1.0.0",
        planned_model="m",
        endpoint_profile_id="m@https://example.invalid/v1/chat/completions",
        max_output_tokens=4096,
        session_input_tokens=240000,
        session_output_tokens=48000,
        wall_seconds=900,
        logical_clock=False,
    )


@pytest.mark.parametrize(
    "limit",
    [
        "logical_max_output_tokens_including_reasoning_per_request",
        "session_input_tokens",
        "session_output_tokens_including_reasoning",
        "company_wall_seconds",
    ],
)
def test_scan_actual_sdk_config_cannot_exceed_declared_task_cap(limit):
    t = task()
    t.raw["limits"][limit] = 1
    t.raw["execution_profile_sha256"] = sha256_hex(t.raw["execution_profile"])
    t.task_sha256 = sha256_hex(t.raw)
    service = SimpleNamespace(client=SimpleNamespace(model="m"))
    with pytest.raises(engine.SharedEngineRejected, match="scan_sdk_session_exceeds_profile_cap"):
        engine._scan_preflight(t, service, config())


def test_self_consistent_wrong_group_rejects_before_owner_or_claim():
    t = task()
    seen = []
    service = SimpleNamespace(
        client=SimpleNamespace(model="m"),
        questions={"ORIGINAL_1": "question-data-only"},
        lifecycle=SimpleNamespace(
            question_pack_group_key=lambda q: seen.append(q) or ["foreign-group"]
        ),
    )
    with pytest.raises(
        engine.SharedEngineRejected, match="scan_profile_native_pack_group_mismatch"
    ):
        engine._scan_preflight(t, service, config())
    assert seen == ["question-data-only"]


def test_new_capabilities_do_not_claim_multiturn_or_search_proof():
    value = engine.capabilities()
    assert value["company_scan"]["task_protocol"] == "iqs.company-scan-task/1.0.0"
    assert value["company_scan"]["search_queries"] == 0
    assert (
        "native_multiturn_packs" in value["unsupported"]
        and "official_search_backed_checkpoint" in value["unsupported"]
    )
