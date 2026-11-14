"""Pure negative preflight seams; no mock is a native owner positive."""

import copy
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
COMPANY = Path(os.environ.get(
    "IQS_COMPANY_AGENT_ROOT",
    str(ROOT.parent / "company" if CANDIDATE else PROJECTS / "iqs-company-agent-lab"),
))
BRIDGE = (
    Path(json.loads((ROOT.parent / "runtime.json").read_text(encoding="utf8"))["root"]) / "bridge"
    if CANDIDATE
    else Path(os.environ.get("IQS_AGENT_RUNTIME_ROOT", PROJECTS / "iqs-agent-runtime-lab"))
)
sys.path.insert(0, str(COMPANY / "src"))
sys.path.insert(0, str(BRIDGE / "src"))
from scripts import shared_company_engine as engine
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


def use_scan_runtime(monkeypatch, services):
    """Inject a detached public Runtime DTO for composition-only guard tests."""
    class RuntimePort:
        model = services.client.model

        def has_native_session(self):
            return False

        def pack_group_key(self, question_id):
            question = services.questions[question_id]
            return services.lifecycle.question_pack_group_key(question)

        def original_inputs(self):
            import src.utils.quick_scan_company_context as context
            return context.company_scan_inputs(services.lifecycle)

        def original_scan_context(self):
            import src.utils.quick_scan_company_context as context
            return context.company_scan_contract(services.lifecycle)

        def supports_intent_recovery(self):
            return True

        def attempt_observations(self, *, transport_origin):
            return []

        def check_admission(self):
            return services.owner.check()

        def assert_execution_controls(self, **_controls):
            return services.owner.assert_execution_controls(**_controls)

    monkeypatch.setattr(engine, "_company_runtime", lambda *_args, **_kwargs: RuntimePort())


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


def test_self_consistent_wrong_group_rejects_before_owner_or_claim(monkeypatch):
    t = task()
    seen = []
    service = SimpleNamespace(
        client=SimpleNamespace(model="m"),
        questions={"ORIGINAL_1": "question-data-only"},
        lifecycle=SimpleNamespace(
            question_pack_group_key=lambda q: seen.append(q) or ["foreign-group"]
        ),
    )
    use_scan_runtime(monkeypatch, service)
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


def test_pure_scan_construction_does_not_recheck_current_permissions(monkeypatch):
    """Data-projection unit only, not a native admission positive."""
    from iqs_company_agent_lab.scan_profile import native_input_references
    import iqs_company_agent_lab.api as company_api
    import iqs_company_agent_lab.scan_profile as scan_profile
    import src.utils.quick_scan_company_context as public_context

    t = task()
    subject = {"entity_id": "synthetic"}
    original = SimpleNamespace(
        input_raw={name: b"{}" for name in ("identity.json", "manifest.json", "authority.json", "owner-config.json", "questions.json")},
        observation_context={"questions": {"ORIGINAL_1": {"subject_binding": {"subject_ref": subject}}}},
        plan={"provider": "synthetic", "model": "m"}, bundle={"manifest": {"module_locks": []}},
        route_id="r", route_provider="synthetic", route_model="m")
    refs = native_input_references(original.input_raw)
    binding = dict(protocol="iqs.native-company-owner-binding/1.0.0", synthetic=False,
                   subject_ref=subject, authority_ref=refs["authority.json"],
                   native_scope={"scope": "entity", "scope_id": "synthetic"},
                   original_inputs_sha256=sha256_hex(refs))
    subject.update(scope="entity", scope_id="synthetic")
    t.runtime_profile = dict(protocol="iqs.company-scan-runtime/1.0.0", synthetic=False,
                             provider="synthetic", model="m", native_inputs_sha256=sha256_hex(refs))
    raw = canonical_json(t.runtime_profile).encode("utf8")
    t.raw["runtime_profile_ref"] = dict(path="runtime.json", bytes=len(raw), sha256=sha256_hex(raw))
    t.raw.update(native_inputs=refs, module_locks=[], owner_binding=binding)
    t.owner_binding = copy.deepcopy(binding)
    t.task_sha256 = sha256_hex(t.raw)
    monkeypatch.setattr(public_context, "company_scan_inputs", lambda lifecycle: original)
    monkeypatch.setattr(public_context, "company_scan_contract", lambda lifecycle: SimpleNamespace(
        native_input_references=refs,
        observation_context=copy.deepcopy(original.observation_context),
        identity_payload={},
        module_locks=(),
        route_provider="synthetic",
        route_model="m",
        route_id="r",
    ))
    monkeypatch.setattr(scan_profile, "native_company_projection", lambda identity, ref: t.company_doc)
    monkeypatch.setattr(
        company_api,
        "native_company_projection",
        lambda identity, ref: t.company_doc,
    )
    monkeypatch.setattr(engine, "_production_answer_semantics", lambda *args: None)
    controls = []
    owner = SimpleNamespace(check=lambda: pytest.fail("pure construction must not invoke current permission I/O"),
                            assert_execution_controls=lambda **kw: controls.append(kw))
    services = SimpleNamespace(client=SimpleNamespace(model="m"), native_session=False,
        lifecycle=SimpleNamespace(question_pack_group_key=lambda q: ["issuer", "perimeter"]),
        questions={"ORIGINAL_1": "original"}, recover_intent=lambda intent: None,
        attempt_observations=lambda **kw: [], owner=owner)
    use_scan_runtime(monkeypatch, services)
    assert engine._scan_preflight(t, services, config()) == config()
    assert len(controls) == 1
