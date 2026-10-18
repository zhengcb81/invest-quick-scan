"""Composition regressions: synthetic engine positives, native refusals.

No test below is a production owner or financial accuracy positive. Production
owner acceptance is deliberately left to the existing original service suite.
"""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
IQS_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "task_plan.md").is_file())
IS_CANDIDATE = PACKAGE.name == "composition-candidate"
BASE = PACKAGE.parent if IS_CANDIDATE else PACKAGE / "runs/shared-engine-production-2026-10-18"
COMPANY = BASE / "company-candidate" if IS_CANDIDATE else PACKAGE.parent / "iqs-company-agent-lab"
STOCKQA = BASE / "native-integration-candidate" if IS_CANDIDATE else PACKAGE.parent / "StockQAbyLLM"
OWNER_UTILS = BASE / "owner-services-candidate/src/utils" if IS_CANDIDATE else STOCKQA / "src/utils"
sys.path.insert(0, str(COMPANY / "src"))
sys.path.insert(0, str(STOCKQA))
sys.path.insert(0, str(IQS_ROOT.parent / "iqs-agent-runtime-lab/src"))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

engine = load("shared_company_engine_candidate", PACKAGE / "scripts/shared_company_engine.py")
helpers = load("composition_company_helpers", COMPANY / "tests/conftest.py")
from iqs_company_agent_lab import synthfixtures as sf
from iqs_company_agent_lab.runtime import SyntheticReplayPort, SyntheticCrash
from iqs_company_agent_lab.events import load_events
from iqs_company_agent_lab.runner import Runner
from iqs_company_agent_lab.provenance import runtime_evidence_document


class ContextPort(SyntheticReplayPort):
    def __init__(self, task, *, fail=False):
        super().__init__(helpers.scenario_doc([]), task.raw["run_id"])
        self.calls, self.fail, self.receipts, self.requests = 0, fail, [], []

    def model_step(self, request):
        self.calls += 1
        self.requests.append(copy.deepcopy(request))
        if self.fail:
            raise RuntimeError("synthetic interrupted SDK")
        intent = request["intent"]
        questions = {q["question_id"]: q["question"] for q in request["stable_prefix"]["questions"]}
        answers = [sf.gen_insufficient(questions[q]) for q in intent["question_ids"]]
        for answer in answers:
            answer["status"] = "not_applicable"
            answer["summary"] = "[Synthetic fixture] Recovery/composition example only."
        response = sf.answers_respond(answers)
        response["usage"] = sf.usage_block()
        receipt = self._build_model_receipt(intent, response, self._next_attempt_ref("model"))
        self.receipts.append(receipt)
        return receipt


class SyntheticObservations:
    def __init__(self, port):
        self.port = port

    def recover_intent(self, intent):
        return None

    def attempt_observations(self, *, transport_origin):
        assert transport_origin == "scripted_wire"
        rows = []
        for index, receipt in enumerate(self.port.receipts):
            usage = receipt["usage"]
            native = {"provider": "synthetic", "attempt_id": "synthetic-native-" + str(index),
                "requested_model": receipt["planned_model"], "actual_model": receipt["actual_model"],
                "http_status_code": 200,
                "usage": {"schema": "quick-scan-usage-v1", "input_tokens": usage["input_tokens"] - usage["cache_read_tokens"],
                    "cached_input_tokens": usage["cache_read_tokens"], "cache_creation_input_tokens": 0,
                    "output_tokens": usage["output_tokens"], "reasoning_output_tokens": usage["reasoning_tokens"], "search_tool_calls": 0}}
            rows.append(dict(runtime_attempt_ref=receipt["runtime_attempt_ref"], native_receipt=native,
                             transport_origin=transport_origin, replayed=False))
        return rows


def test_cli_capabilities_has_no_unreviewed_production_launch():
    result = subprocess.run([sys.executable, str(Path(engine.__file__)), "capabilities"], capture_output=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["production_owner_admitted"] is False
    assert payload["financial_accuracy_assessed"] is False
    assert "native_multiturn_packs" in payload["unsupported"]
    assert "cli_owner_construction" in payload["unsupported"]


@pytest.mark.parametrize("strategy", ["fixed3", "free_agent", "evidence_agent"])
def test_sole_original_runner_durable_export_and_validated_summary(tmp_path, strategy):
    task = helpers.make_task(strategy, "composition-" + strategy)
    port = ContextPort(task)
    services = SyntheticObservations(port)
    result = engine._execute_with_port(task, services, port, output=tmp_path / "export",
        session_dir=tmp_path / "session", transport_origin="scripted_wire")
    assert result["all_slots_completed"] is True
    durable = load_events(tmp_path / "session/events.jsonl")
    exported = load_events(tmp_path / "export/events.jsonl")
    assert durable == exported
    assert len([e for e in durable if e["event_type"] == "answer_committed"]) == 12
    native = result["runtime_summary"]
    assert native["runtime_origin"] == "scripted_wire"
    assert native["evidence_origin"] == "synthetic"
    assert native["owner_authority_verified"] is False
    assert native["financial_qualification_granted"] is False
    assert native["new_model_http"] == port.calls
    assert native["cash_cost"] is None
    from iqs_company_agent_lab.reporter import generate_report
    report = generate_report(tmp_path / "export", tmp_path / "report")
    assert report["runtime_observations"] == native


def test_interruption_preserves_original_pre_send_checkpoint(tmp_path):
    task = helpers.make_task("fixed3", "composition-crash")
    port = ContextPort(task, fail=True)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, SyntheticObservations(port), port, output=tmp_path / "export",
            session_dir=tmp_path / "session", transport_origin="scripted_wire")
    assert port.calls == 1
    events = load_events(tmp_path / "session/events.jsonl")
    assert any(e["event_type"] == "intent" and e["data"]["kind"] == "model_step" for e in events)
    checkpoint = json.loads((tmp_path / "session/checkpoint.json").read_text(encoding="utf8"))
    assert checkpoint["pending_intent"]["kind"] == "model_step"
    assert checkpoint["pending_receipt"] is None
    assert checkpoint["event_chain"]["journal_files"][0].startswith("pending-history-")
    assert not (tmp_path / "export").exists()
    assert (tmp_path / "session/task-bundle.json").is_file()


def test_atomic_original_journal_write_fails_before_next_engine_send(tmp_path, monkeypatch):
    task = helpers.make_task("fixed3", "composition-diskfailure")
    port = ContextPort(task)
    real_replace = engine.os.replace
    def fail_events(source, destination):
        if Path(destination).name == "events.jsonl":
            raise OSError("synthetic disk unavailable")
        return real_replace(source, destination)
    monkeypatch.setattr(engine.os, "replace", fail_events)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, SyntheticObservations(port), port, output=tmp_path / "export",
            session_dir=tmp_path / "session", transport_origin="scripted_wire")
    assert port.calls == 0
    assert not (tmp_path / "session/events.jsonl").exists()


def test_existing_session_never_overwritten_or_cleaned(tmp_path):
    task = helpers.make_task("fixed3", "composition-existing")
    session = tmp_path / "session"
    session.mkdir()
    sentinel = session / "keep.txt"
    sentinel.write_text("other run", encoding="utf8")
    port = ContextPort(task)
    with pytest.raises(ValueError):
        engine._execute_with_port(task, SyntheticObservations(port), port, output=tmp_path / "export",
            session_dir=session, transport_origin="scripted_wire")
    assert sentinel.read_text(encoding="utf8") == "other run"
    assert port.calls == 0


def test_public_api_rejects_arbitrary_services_before_http_or_output(tmp_path):
    # Import the actual first-party service class, not a forged test grant.
    import src.utils
    src.utils.__path__.insert(0, str(OWNER_UTILS))
    task = helpers.make_task("fixed3", "composition-refusal")
    with pytest.raises(engine.SharedEngineRejected, match="original_owner_research_services"):
        engine.execute_shared_engine(task, SimpleNamespace(), {}, tmp_path / "export", session_dir=tmp_path / "session")
    assert not (tmp_path / "export").exists()
    assert not (tmp_path / "session").exists()


def test_native_inspection_rejects_double_never_falls_back_to_resend():
    with pytest.raises(engine.SharedEngineRejected, match="original_owner_research_services"):
        engine.inspect_native_recovery(SimpleNamespace(), attempt_ref="stockqa:unproven")


def test_prior_service_observations_refused_instead_of_relabelled_new_http():
    # A constructor-bypassed object is used ONLY as an invalid-input counterexample.
    # It never reaches owner.check, native dispatch or an asserted native positive.
    from src.utils.quick_scan_owner_research import OwnerResearchServices
    task = helpers.make_task("fixed3", "composition-staleobserver")
    task.company_doc["origin"] = "owner_public"
    task.owner_binding = {"synthetic": False}
    services = OwnerResearchServices.__new__(OwnerResearchServices)
    services.task, services.native_session = task, False
    services.client = SimpleNamespace(model="deepseek-flash", provider_name="mimo")
    services.attempt_observations = lambda **kwargs: [{"runtime_attempt_ref": "stockqa:previous-run"}]
    services.owner = SimpleNamespace(check=lambda: pytest.fail("must reject before fake owner check"))
    with pytest.raises(engine.SharedEngineRejected, match="fresh_owner_service_observer"):
        engine.preflight(task, services, {"protocol": "iqs.agent-runtime-lab.session-config/1.0.0"})


def test_windows_transient_rename_retries_same_completed_record_only(tmp_path, monkeypatch):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"complete")
    real_replace = engine.os.replace
    attempts = []
    def transient(src, dst):
        attempts.append((src, dst))
        if len(attempts) < 3:
            error = PermissionError("scripted Windows scanner hold")
            error.winerror = 5
            raise error
        return real_replace(src, dst)
    monkeypatch.setattr(engine.os, "replace", transient)
    monkeypatch.setattr(engine.time, "sleep", lambda _: None)
    engine._replace_record(source, target)
    assert len(attempts) == 3 and len(set(attempts)) == 1
    assert target.read_bytes() == b"complete"


def _crash_checkpoint(tmp_path, *, strategy="free_agent", legacy=False):
    task = helpers.make_task(strategy, "composition-recovery")
    class CrashPort(ContextPort):
        def model_step(self, request):
            receipt = super().model_step(request)
            if legacy:
                raise SyntheticCrash("before_commit", receipt["runtime_attempt_ref"], receipt)
            # Ordinary fatal wire/SDK failure after a known native response:
            # the pre-send checkpoint survives without a synthetic crash marker.
            raise RuntimeError("synthetic SDK death after native durable outcome")
    port = CrashPort(task)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, SyntheticObservations(port), port, output=tmp_path / "unused-export",
            session_dir=tmp_path / "original", transport_origin="scripted_wire")
    return task, port, tmp_path / "original/checkpoint.json"


def test_resume_unknown_original_proof_refuses_before_new_session_or_http(tmp_path, monkeypatch):
    task, old_port, checkpoint = _crash_checkpoint(tmp_path)
    # These patches isolate composition control flow. They are explicitly not
    # native authority positives or acceptance of a fabricated owner DTO.
    monkeypatch.setattr(engine, "preflight", lambda *args: {})
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *args, **kwargs:
        {"decision": "pause_for_inspection", "saved_receipt": None})
    with pytest.raises(engine.SharedEngineRejected, match="never_resend_unknown"):
        engine.resume_shared_engine(task, SimpleNamespace(), {}, checkpoint, tmp_path / "export",
            session_dir=tmp_path / "resumed", transport_origin="scripted_wire")
    assert old_port.calls == 1
    assert not (tmp_path / "resumed").exists()
    assert not (tmp_path / "export").exists()


@pytest.mark.parametrize("legacy", [False, True])
def test_resume_original_saved_receipt_uses_fresh_port_zero_new_model_calls(tmp_path, monkeypatch, legacy):
    task, old_port, checkpoint = _crash_checkpoint(tmp_path, legacy=legacy)
    monkeypatch.setattr(engine, "preflight", lambda *args: {})
    saved = copy.deepcopy(old_port.receipts[0])
    saved["session_handle"] = None
    from iqs_company_agent_lab.receipts import finalize_receipt_digest
    saved["receipt_sha256"] = finalize_receipt_digest(saved)
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *args, **kwargs:
        {"decision": "recover_saved_receipt", "saved_receipt": saved})
    fresh_port = ContextPort(task)
    import iqs_agent_runtime_lab.port
    monkeypatch.setattr(iqs_agent_runtime_lab.port, "create_runtime_port", lambda *args, **kwargs: fresh_port)
    class Replayed(SyntheticObservations):
        def inspect_attempt(self, ref):
            return {"known": True}
        def attempt_observations(self, **kwargs):
            rows = super().attempt_observations(**kwargs)
            for row in rows:
                row["replayed"] = True
            return rows
    result = engine.resume_shared_engine(task, Replayed(old_port), {}, checkpoint, tmp_path / "export",
        session_dir=tmp_path / "resumed", transport_origin="scripted_wire")
    assert result["all_slots_completed"]
    assert fresh_port.calls == 0
    assert result["runtime_summary"]["new_model_http"] == 0
    assert result["runtime_summary"]["replayed_native_attempts"] == 1
    assert not result["runtime_summary"]["owner_authority_verified"]
    events = load_events(tmp_path / "resumed/events.jsonl",
        expected_seq_start=json.loads(checkpoint.read_text(encoding="utf8"))["event_chain"]["seq"] + 1,
        expected_prev_sha256=json.loads(checkpoint.read_text(encoding="utf8"))["event_chain"]["head_sha256"])
    assert events[0]["event_type"] == "segment"
    assert events[0]["data"]["reason"] == "restart_with_new_segment"


def test_native_recovery_conflicting_known_usage_never_hidden_by_physical_dedup(tmp_path, monkeypatch):
    task, old_port, checkpoint = _crash_checkpoint(tmp_path, legacy=True)
    monkeypatch.setattr(engine, "preflight", lambda *args: {})
    saved = copy.deepcopy(old_port.receipts[0])
    saved["usage"]["output_tokens"] += 1
    from iqs_company_agent_lab.receipts import finalize_receipt_digest
    saved["receipt_sha256"] = finalize_receipt_digest(saved)
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *args, **kwargs:
        {"decision": "recover_saved_receipt", "saved_receipt": saved})
    with pytest.raises(engine.SharedEngineRejected, match="conflicts_with_original_journal"):
        engine.resume_shared_engine(task, SimpleNamespace(), {}, checkpoint, tmp_path / "export",
            session_dir=tmp_path / "resumed", transport_origin="scripted_wire")
    assert old_port.calls == 1
    assert not (tmp_path / "resumed").exists()


def test_original_intent_cache_hit_skips_every_new_generation(tmp_path):
    task = helpers.make_task("fixed3", "composition-intentcache")
    first = ContextPort(task)
    engine._execute_with_port(task, SyntheticObservations(first), first, output=tmp_path / "first-export",
        session_dir=tmp_path / "first-session", transport_origin="scripted_wire")
    cached = {r["intent"]["action_id"]: copy.deepcopy(receipt)
              for r, receipt in zip(first.requests, first.receipts)}
    fresh = ContextPort(task)
    class Warm(SyntheticObservations):
        def recover_intent(self, intent):
            return {"decision": "recover_saved_receipt", "saved_receipt": copy.deepcopy(cached[intent["action_id"]])}
        def attempt_observations(self, **kwargs):
            rows = super().attempt_observations(**kwargs)
            for row in rows:
                row["replayed"] = True
            return rows
    result = engine._execute_with_port(task, Warm(first), fresh, output=tmp_path / "warm-export",
        session_dir=tmp_path / "warm-session", transport_origin="scripted_wire")
    assert result["all_slots_completed"]
    assert fresh.calls == 0
    assert result["runtime_summary"]["new_model_http"] == 0
    assert result["runtime_summary"]["replayed_native_attempts"] == first.calls


def test_unresolved_original_intent_stops_before_generation(tmp_path):
    task = helpers.make_task("fixed3", "composition-unresolved")
    port = ContextPort(task)
    class Unknown(SyntheticObservations):
        def recover_intent(self, intent):
            return {"decision": "pause_for_inspection", "saved_receipt": None}
    with pytest.raises(engine.SharedEngineInterrupted) as raised:
        engine._execute_with_port(task, Unknown(port), port, output=tmp_path / "export",
            session_dir=tmp_path / "session", transport_origin="scripted_wire")
    assert isinstance(raised.value.__cause__, engine.SharedEngineRejected)
    assert port.calls == 0
    assert (tmp_path / "session/checkpoint.json").is_file()


def test_os_process_death_after_response_restores_original_pending_checkpoint(tmp_path, monkeypatch):
    # The child exits immediately: no exception handler or Python finally can
    # manufacture the checkpoint after the fact. The response is a labelled
    # synthetic native-output stand-in; no network socket or owner is used.
    program = r'''
import importlib.util, json, os, pathlib, sys
path, base = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("composition_child_helpers", path)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
task = t.helpers.make_task("free_agent", "composition-osdeath")
class KillPort(t.ContextPort):
    def model_step(self, request):
        receipt = super().model_step(request)
        with (base / "synthetic-safe-response.json").open("w", encoding="utf8") as stream:
            json.dump(receipt, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os._exit(86)
port = KillPort(task)
t.engine._execute_with_port(task, t.SyntheticObservations(port), port,
    output=base / "unused-export", session_dir=base / "original", transport_origin="scripted_wire")
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    child = subprocess.run([sys.executable, "-B", "-c", program, str(Path(__file__)), str(tmp_path)],
        capture_output=True, env=env, timeout=30)
    assert child.returncode == 86, child.stderr.decode(errors="replace")
    checkpoint = tmp_path / "original/checkpoint.json"
    raw = json.loads(checkpoint.read_text(encoding="utf8"))
    assert raw["pending_receipt"] is None
    assert raw["pending_intent"]["kind"] == "model_step"
    task = helpers.make_task("free_agent", "composition-osdeath")
    saved = json.loads((tmp_path / "synthetic-safe-response.json").read_text(encoding="utf8"))
    saved["session_handle"] = None
    from iqs_company_agent_lab.receipts import finalize_receipt_digest
    saved["receipt_sha256"] = finalize_receipt_digest(saved)
    monkeypatch.setattr(engine, "preflight", lambda *args: {})
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *args, **kwargs:
        {"decision": "recover_saved_receipt", "saved_receipt": saved})
    fresh = ContextPort(task)
    import iqs_agent_runtime_lab.port
    monkeypatch.setattr(iqs_agent_runtime_lab.port, "create_runtime_port", lambda *args, **kwargs: fresh)
    class Recovered(SyntheticObservations):
        def inspect_attempt(self, ref):
            return {"known": True}
        def attempt_observations(self, **kwargs):
            rows = super().attempt_observations(**kwargs)
            for row in rows:
                row["replayed"] = True
            return rows
    result = engine.resume_shared_engine(task, Recovered(SimpleNamespace(receipts=[saved])), {}, checkpoint,
        tmp_path / "export", session_dir=tmp_path / "resumed", transport_origin="scripted_wire")
    assert result["all_slots_completed"] and fresh.calls == 0
    assert result["runtime_summary"]["new_model_http"] == 0
    assert result["runtime_summary"]["replayed_native_attempts"] == 1
