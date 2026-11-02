"""Read-only replay preserves completed slots without another model call."""
import copy

import pytest

from test_shared_answer_semantics import engine, helpers, original, native_bound


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


@pytest.mark.parametrize("change", ["schema", "canonical_unit"])
def test_recovery_uses_original_resources_after_current_resources_evolve(original, monkeypatch, change):
    import module_registry
    import standard_answers
    from test_shared_answer_semantics import metric
    task, qid, answer, context = original
    package, _, _, _ = module_registry.load_current(root=standard_answers.ROOT)
    context.update(answer_schema_sha256=standard_answers.digest(package["format_resources"]["schemas/answer-content.schema.json"]),
                   metric_registry_sha256=standard_answers.digest(package["format_resources"]["questions/metric-registry.json"]))
    old_reader = standard_answers.library.read_json
    registry = old_reader(standard_answers.ROOT / "questions/metric-registry.json")
    metric_id, spec = next(iter(registry["metrics"].items()))
    row = metric()
    row.update(metric_id=metric_id, unit=spec["unit"],
               currency="CNY" if spec["unit"] in {"currency", "currency_per_share"} else None)
    answer["metrics"] = [row]
    engine._frozen_answer_semantics(task, context)(copy.deepcopy(answer), qid)

    def evolved(path):
        data = copy.deepcopy(old_reader(path))
        if change == "schema" and path.name == "answer-content.schema.json":
            data["required"].append("new_future_field")
        if change == "canonical_unit" and path.name == "metric-registry.json":
            data["metrics"][metric_id]["unit"] = "percent" if spec["unit"] != "percent" else "ratio"
        return data

    monkeypatch.setattr(standard_answers.library, "read_json", evolved)
    before = copy.deepcopy(answer)
    engine._frozen_answer_semantics(task, context)(answer, qid)
    assert answer == before


def test_owner_package_resources_remain_bound_and_current_file_is_not_read(original, monkeypatch):
    import module_registry
    import standard_answers
    task, qid, answer, context = original
    package, _, _, _ = module_registry.load_current(root=standard_answers.ROOT)
    context["questions"] = {qid: {"metadata": {"module_package_id": package["package_id"]}}}
    monkeypatch.setattr(standard_answers.library, "read_json", lambda _: pytest.fail("current resource read"))
    engine._frozen_answer_semantics(task, context)(copy.deepcopy(answer), qid)
    wrong = copy.deepcopy(context)
    wrong["answer_schema_sha256"] = "f" * 64
    engine._frozen_answer_semantics(task, wrong)(copy.deepcopy(answer), qid)


def test_historical_resource_lookup_skips_missing_current_and_unrelated_bad_archive(original, monkeypatch, tmp_path):
    import shutil
    import module_registry
    import standard_answers
    task, qid, answer, context = original
    package, _, _, _ = module_registry.load_current(root=standard_answers.ROOT)
    context.update(answer_schema_sha256=standard_answers.digest(package["format_resources"]["schemas/answer-content.schema.json"]),
                   metric_registry_sha256=standard_answers.digest(package["format_resources"]["questions/metric-registry.json"]))
    root = tmp_path / "release"
    shutil.copytree(standard_answers.ROOT / "questions/releases", root / "questions/releases")
    shutil.copytree(standard_answers.ROOT / "schemas", root / "schemas")
    (root / "schemas/answer-content.schema.json").unlink()
    (root / "questions/releases/packages" / ("pkg_" + "0" * 64 + ".json")).write_text("broken", encoding="utf8")
    before = copy.deepcopy(answer)
    engine._frozen_answer_semantics(task, context, release_root=root)(answer, qid)
    assert answer == before


def test_production_selects_original_owner_release_root(native_bound, monkeypatch, tmp_path):
    import json
    import shutil
    import module_registry
    import standard_answers
    from types import SimpleNamespace
    import src.utils.quick_scan_company_context as company_context
    task, qid, answer, services, _, _ = native_bound
    original_inputs = company_context.company_scan_inputs(services.lifecycle)
    package, _, _, _ = module_registry.load_current(root=standard_answers.ROOT)
    context = copy.deepcopy(original_inputs.observation_context)
    context["questions"][qid]["metadata"]["module_package_id"] = package["package_id"]
    release_root = tmp_path / "separate-release"
    shutil.copytree(standard_answers.ROOT / "questions/releases", release_root / "questions/releases")
    shutil.copytree(standard_answers.ROOT / "schemas", release_root / "schemas")
    seen = []
    original_loader = module_registry.load_package
    def load_original(package_id, *, root):
        seen.append(root)
        assert root == release_root
        return original_loader(package_id, root=root)
    monkeypatch.setattr(module_registry, "load_package", load_original)
    monkeypatch.setattr(company_context, "company_scan_inputs", lambda _: SimpleNamespace(
        observation_context=context,
        input_raw={"owner-config.json": json.dumps({"iqs_release_root": str(release_root)}).encode()}))
    callback = engine._production_answer_semantics(task, services)
    callback.base_semantic_validator(copy.deepcopy(answer), qid)
    assert seen == [release_root]


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
