"""Typed request execute/pending/resume/export/report; synthetic, no owner grant."""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
composition = load("typed_replay_composition_helpers", ROOT / "tests/test_shared_company_engine.py")
fixtures = load("typed_replay_scan_fixtures", ROOT.parent / "iqs-company-agent-lab/tests/test_scan_profile.py")
engine = composition.engine
from iqs_company_agent_lab.errors import ProtocolIllegalError
from iqs_company_agent_lab.replay import ReplayEngine
from iqs_company_agent_lab.runner import Runner
from iqs_company_agent_lab.reporter import generate_report
from iqs_company_agent_lab.runtime import SyntheticCrash

RULES = ("[SYNTHETIC ONLY] Copy the exact bound source URL including its query.",)


class ScanContextPort(composition.ContextPort):
    """Original synthetic receipt generator with this scan's exact cutoff."""
    def model_step(self, request):
        self.calls += 1
        self.requests.append(copy.deepcopy(request))
        intent = request["intent"]
        questions = {q["question_id"]: q["question"] for q in request["stable_prefix"]["questions"]}
        answers = [composition.sf.gen_insufficient(questions[q]) for q in intent["question_ids"]]
        for answer in answers:
            answer.update(status="not_applicable", information_as_of=request["dynamic_context"]["information_cutoff"])
        response = composition.sf.answers_respond(answers)
        response["usage"] = composition.sf.usage_block()
        receipt = self._build_model_receipt(intent, response, self._next_attempt_ref("model"))
        self.receipts.append(receipt)
        return receipt


@pytest.mark.parametrize("rules", [RULES, ()])
def test_original_request_hashes_replay_with_same_trusted_rules(rules):
    task = fixtures.scan_task(qs=fixtures.questions(1))
    port = ScanContextPort(task)
    runner = Runner(task, port, answer_semantic_rules=rules)
    runner.run()
    reconstructed = ReplayEngine(task, answer_semantic_rules=rules).replay(runner.journal.events)["state"]
    assert reconstructed.slots == runner.state.slots
    assert reconstructed.all_completed()
    assert port.calls == 1


@pytest.mark.parametrize("changed", [(), ("different trusted rule",)])
def test_omitted_or_changed_rules_cannot_satisfy_original_event_hash(changed):
    task = fixtures.scan_task(qs=fixtures.questions(1))
    port = ScanContextPort(task)
    runner = Runner(task, port, answer_semantic_rules=RULES)
    runner.run()
    with pytest.raises(ProtocolIllegalError, match="runtime context diverges"):
        ReplayEngine(task, answer_semantic_rules=changed).replay(runner.journal.events)
    assert port.calls == 1


def test_typed_pending_resume_export_and_report_reuse_original_hashes_without_new_dispatch(tmp_path, monkeypatch):
    """Composition seams isolate owner admission, never a native positive."""
    task = fixtures.scan_task(qs=fixtures.questions(1))
    def validator(answer, question_id):
        assert answer["question_id"] == question_id
    validator.prompt_rules = RULES
    monkeypatch.setattr(engine, "_production_answer_semantics", lambda *args: validator)
    class CrashPort(ScanContextPort):
        def model_step(self, request):
            receipt = super().model_step(request)
            raise SyntheticCrash("before_commit", receipt["runtime_attempt_ref"], receipt)
    old_port = CrashPort(task)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, composition.SyntheticObservations(old_port), old_port,
            output=tmp_path / "unused-export", session_dir=tmp_path / "cold", transport_origin="scripted_wire")
    checkpoint = tmp_path / "cold/checkpoint.json"
    saved = copy.deepcopy(old_port.receipts[0])
    saved["session_handle"] = None
    from iqs_company_agent_lab.receipts import finalize_receipt_digest
    saved["receipt_sha256"] = finalize_receipt_digest(saved)
    monkeypatch.setattr(engine, "preflight", lambda *args: {})
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *args, **kwargs:
                        dict(decision="recover_saved_receipt", saved_receipt=saved))
    fresh_port = ScanContextPort(task)
    import iqs_agent_runtime_lab.port
    monkeypatch.setattr(iqs_agent_runtime_lab.port, "create_runtime_port", lambda *args, **kwargs: fresh_port)
    class Warm(composition.SyntheticObservations):
        def inspect_attempt(self, ref):
            return dict(known=True)
        def attempt_observations(self, **kwargs):
            rows = super().attempt_observations(**kwargs)
            for row in rows:
                row["replayed"] = True
            return rows
    result = engine.resume_shared_engine(task, Warm(old_port), {}, checkpoint, tmp_path / "export",
        session_dir=tmp_path / "warm", transport_origin="scripted_wire")
    verified, _ = engine._verified_finalization_export(task, tmp_path / "export", RULES)
    report = generate_report(tmp_path / "export", tmp_path / "report", answer_semantic_rules=RULES)
    assert result["all_slots_completed"] and all(slot["execution_status"] == "completed" for slot in verified["slots"])
    assert old_port.calls == 1 and fresh_port.calls == 0
    assert result["runtime_summary"]["new_model_http"] == 0
    assert report["runtime_observations"] == result["runtime_summary"]
    assert result["runtime_summary"]["owner_authority_verified"] is False
    with pytest.raises(ProtocolIllegalError, match="runtime context diverges"):
        generate_report(tmp_path / "export", tmp_path / "wrong-rule-report", answer_semantic_rules=("wrong",))


def test_replay_refuses_invalid_rule_carrier_before_using_events():
    task = fixtures.scan_task(qs=fixtures.questions(1))
    with pytest.raises(ProtocolIllegalError, match="answer_semantic_rules_invalid"):
        ReplayEngine(task, answer_semantic_rules="not a rule list")
