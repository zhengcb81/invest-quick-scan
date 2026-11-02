"""Read-only replay preserves completed slots without another model call."""
import copy

import pytest

from test_shared_answer_semantics import engine, helpers, original


def test_unrelated_registry_extension_does_not_reject_original_answer(original, monkeypatch):
    import standard_answers
    task, qid, answer, context = original
    old_reader = standard_answers.library.read_json

    def extended(path):
        data = old_reader(path)
        if path.name == "metric-registry.json":
            data = copy.deepcopy(data)
            data["metrics"]["new.unrelated_metric"] = {"unit": "ratio"}
        return data

    monkeypatch.setattr(standard_answers.library, "read_json", extended)
    callback = engine._frozen_answer_semantics(task, context)
    before = copy.deepcopy(answer)
    callback(answer, qid)
    assert answer == before


def test_read_only_boundary_finishes_without_fabricating_a_model_receipt():
    from iqs_company_agent_lab.runner import Runner
    from iqs_company_agent_lab.runtime import SavedResponseBoundary

    task = helpers.make_task("fixed3", "readonly-boundary")

    class ReadOnlyPort:
        def model_step(self, envelope):
            raise SavedResponseBoundary()

        def search(self, envelope):
            pytest.fail("read-only must not search")

        def inspect_attempt(self, reference):
            return None

        def request_resume(self, reference):
            return None

    runner = Runner(task, ReadOnlyPort())
    runner.run()
    assert runner.state.finished_reason == "saved_responses_exhausted"
    assert not any(e["event_type"] == "receipt_model" for e in runner.journal.events)
    assert any(e["event_type"] == "runtime_declined" for e in runner.journal.events)
    assert all(s["execution_status"] != "completed" for s in runner.state.slots)


def test_unknown_pending_member_does_not_hide_previously_completed_members(tmp_path, monkeypatch):
    # Composition boundary only; original owner/SQLite proof is exercised by
    # test_paid_partial_cold_native_e2e, rather than by this observation double.
    import test_shared_company_engine as fixture
    import iqs_agent_runtime_lab.port
    engine = fixture.engine
    task = fixture.helpers.make_task("fixed3", "readonly-earlier-members")

    class Interrupted(fixture.ContextPort):
        def model_step(self, envelope):
            if self.calls:
                raise RuntimeError("no response for the next member")
            return super().model_step(envelope)

    old = Interrupted(task)
    with pytest.raises(engine.SharedEngineInterrupted):
        engine._execute_with_port(task, fixture.SyntheticObservations(old), old,
            output=tmp_path / "unused", session_dir=tmp_path / "original",
            transport_origin="scripted_wire")
    checkpoint = tmp_path / "original/checkpoint.json"
    before = checkpoint.read_bytes()
    monkeypatch.setattr(engine, "preflight", lambda *a: {})
    monkeypatch.setattr(engine, "inspect_native_recovery", lambda *a, **k:
        {"decision": "pause_for_inspection", "saved_receipt": None})
    fresh = fixture.ContextPort(task)
    monkeypatch.setattr(iqs_agent_runtime_lab.port, "create_runtime_port", lambda *a, **k: fresh)

    class ReadOnly(fixture.SyntheticObservations):
        def inspect_attempt(self, ref):
            return {"known": True}
        def recover_intent(self, intent):
            return {"decision": "pause_for_inspection", "saved_receipt": None}
        def attempt_observations(self, **kwargs):
            return [{**row, "replayed": True} for row in super().attempt_observations(**kwargs)]

    result = engine.resume_shared_engine(task, ReadOnly(old), {}, checkpoint, tmp_path / "partial",
        session_dir=tmp_path / "resumed", transport_origin="scripted_wire", replay_only=True)
    assert fresh.calls == 0 and not result["all_slots_completed"]
    assert sum(row["execution_status"] == "completed" for row in result["run"]["slots"]) == 3
    assert result["runtime_summary"]["new_model_http"] == 0
    assert checkpoint.read_bytes() == before
