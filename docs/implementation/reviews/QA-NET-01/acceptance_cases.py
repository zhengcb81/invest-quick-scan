"""QA-NET-01 owner remediation cases: desired behavior, intentionally RED.

Run only with guarded_tests.py against its frozen, isolated source export.
Fixtures are synthetic; HTTP is stubbed by the owner's existing harness.
This is not a production identity golden or a paid/live test.
"""
import importlib.util
import json
import os
from pathlib import Path

RUNTIME = Path(os.environ["IQS_QA_NET_RUNTIME"]).resolve()

def helper(name, relative):
    spec = importlib.util.spec_from_file_location(name, RUNTIME / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

CLI = helper("iqs_owner_cli_cases", "tests/integration/test_qa_net01_cli_e2e.py")
MANIFEST = helper("iqs_owner_manifest_cases", "tests/unit/test_qa_net01_question_manifest.py")
SEAL = helper("iqs_owner_seal_cases", "tests/unit/test_qa_net01_c06_seal.py")

def test_admitted_external_mode_must_not_silently_send_native(monkeypatch, tmp_path, capsys):
    files = CLI._setup(tmp_path, with_authority=False)
    policy = tmp_path / "external.json"
    policy.write_text(json.dumps(CLI._search_policy()), encoding="utf-8")
    monkeypatch.setenv("BRAVE_API_KEY", "offline-fixture-key")
    code, session = CLI._run(monkeypatch, tmp_path, files, manifest=False,
                             with_authority=False, extra=["--search-policy", str(policy)])
    captured = capsys.readouterr()
    assert session.post.call_count == 0, "External adapter absent: native HTTP must remain 0"
    assert code != 0, "Absent production external path must fail closed"

def test_changed_prompt_waits_for_uncertain_prior_attempt(tmp_path):
    from src.core.models import Question
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    from src.utils.quick_scan_question_manifest import load_question_manifest, plan_manifest_dispatch
    store = QuickScanWorkStore(tmp_path / "work.sqlite")
    lifecycle = MANIFEST._lifecycle(store)
    question = Question(text="旧版题面", question_id="IQS_01")
    handle = lifecycle.before_question(question)
    assert handle["claimed"] is True
    store.record_attempt_outcome(handle["work_item_id"], handle["lease"],
                                 handle["attempt_id"], outcome="unknown")
    doc = MANIFEST._manifest(["IQS_01"], prompts={"IQS_01": "新版题面"})
    loaded = load_question_manifest(MANIFEST._write_manifest(tmp_path, doc))
    plan = plan_manifest_dispatch(loaded, store, entity_id=MANIFEST.UUID_ENTITY,
                                 identity_snapshot_sha256=MANIFEST.IDENTITY["identity_snapshot_sha256"],
                                 bindings=MANIFEST._bindings(loaded))
    assert plan["model_calls_planned"] == 0, "Uncertain old attempt must reconcile before new generation"
    assert plan["questions"][0]["action"] == "reconcile"

def test_new_module_keeps_old_answers_hydratable_with_fresh_output(monkeypatch, tmp_path, capsys):
    original = [dict(q) for q in CLI.QUESTIONS]
    files = CLI._setup(tmp_path)
    code, cold = CLI._run(monkeypatch, tmp_path, files)
    capsys.readouterr()
    assert code == 0 and cold.post.call_count == 2
    monkeypatch.setattr(CLI, "QUESTIONS", original + [{"question_id": "IQS_03", "text": "新增模块题面"}])
    files = CLI._setup(tmp_path)
    published = tmp_path / "questions-module-v2.json"
    published.write_bytes(files["questions"].read_bytes())
    files["questions"] = published
    files["output"] = tmp_path / "new-module-output.json"
    # The owner's cold-run fixture cycles the full old list. For an increment
    # only IQS_03 is sent; supply that one synthetic answer at the HTTP boundary.
    original_response = CLI.HARNESS._response
    def new_question_response(*args, **kwargs):
        content = json.loads(kwargs["content"])
        content["question_id"] = "IQS_03"
        kwargs["content"] = json.dumps(content, ensure_ascii=False)
        return original_response(*args, **kwargs)
    monkeypatch.setattr(CLI.HARNESS, "_response", new_question_response)
    code, warm = CLI._run(monkeypatch, tmp_path, files)
    captured = capsys.readouterr()
    assert CLI._plans(captured.out)[-1]["counts"] == {"dispatch": 1, "reuse": 2}
    assert code == 0 and warm.post.call_count == 1
    answers = json.loads(files["output"].read_text(encoding="utf-8"))["answers"]
    assert all(answers[q["question_id"]]["status"] == "scored" for q in original), (
        "Adding a module must not break immutable routing binding of successful old questions", answers)

def test_completed_generation_two_restarts_without_reverting_to_one(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(CLI, "QUESTIONS", [{"question_id": "IQS_01", "text": "第一版题面"}])
    files = CLI._setup(tmp_path)
    published = tmp_path / "questions-generation-v1.json"
    published.write_bytes(files["questions"].read_bytes())
    files["questions"] = published
    code, first = CLI._run(monkeypatch, tmp_path, files)
    capsys.readouterr()
    assert code == 0 and first.post.call_count == 1
    monkeypatch.setattr(CLI, "QUESTIONS", [{"question_id": "IQS_01", "text": "第二版题面"}])
    files = CLI._setup(tmp_path)
    published = tmp_path / "questions-generation-v2.json"
    published.write_bytes(files["questions"].read_bytes())
    files["questions"] = published
    files["output"] = tmp_path / "generation-two.json"
    code, refreshed = CLI._run(monkeypatch, tmp_path, files)
    captured = capsys.readouterr()
    assert CLI._plans(captured.out)[-1]["questions"][0]["generation"] == 2
    assert code == 0 and refreshed.post.call_count == 1
    files["output"] = tmp_path / "generation-two-resume.json"
    code, resumed = CLI._run(monkeypatch, tmp_path, files)
    captured = capsys.readouterr()
    plan = CLI._plans(captured.out)[-1]
    assert plan["questions"][0]["generation"] == 2 and plan["questions"][0]["action"] == "reuse"
    assert code == 0 and resumed.post.call_count == 0
    answer = json.loads(files["output"].read_text(encoding="utf-8"))["answers"]["IQS_01"]
    assert answer["status"] == "scored", "Reuse must hydrate generation2 rather than attach generation1"

def test_fallback_actual_model_is_not_lost_at_checkpoint(tmp_path):
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    store = QuickScanWorkStore(tmp_path / "work.sqlite")
    authority = SEAL.load_c06_authority(SEAL._write_authority(tmp_path))
    lifecycle = SEAL._lifecycle(store, authority=authority)
    handle = lifecycle.before_question(SEAL._q("IQS_05"))
    result = SEAL._result("IQS_05")
    result.answer.metadata["actual_model"] = "fallback-fixture-model"
    lifecycle.after_question(handle, result)
    checkpoint = store.get_answer_checkpoint(handle["work_item_id"])
    assert checkpoint is not None, "Qualified fallback receipt must not be discarded as unknown"
    delivery = store.get_result_delivery(handle["work_item_id"])
    assert delivery is not None and delivery["state"] == "ready"

def test_actual_not_applicable_answer_is_not_redispatched(tmp_path):
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    from src.utils.quick_scan_question_manifest import load_question_manifest, plan_manifest_dispatch
    store = QuickScanWorkStore(tmp_path / "work.sqlite")
    lifecycle = SEAL._lifecycle(store, authority=None)
    handle = lifecycle.before_question(SEAL._q("IQS_05"))
    result = SEAL._result("IQS_05")
    result.answer.status = "not_applicable"
    result.answer.score = None
    lifecycle.after_question(handle, result)
    assert store.get_answer_checkpoint(handle["work_item_id"])["payload"]["answer"]["status"] == "not_applicable"
    doc = MANIFEST._manifest(["IQS_05"], prompts={"IQS_05": SEAL._q("IQS_05").text})
    loaded = load_question_manifest(MANIFEST._write_manifest(tmp_path, doc))
    plan = plan_manifest_dispatch(loaded, store, entity_id=SEAL.UUID_ENTITY,
                                 identity_snapshot_sha256=SEAL.IDENTITY["identity_snapshot_sha256"],
                                 bindings=MANIFEST._bindings(loaded))
    assert plan["model_calls_planned"] == 0
    assert plan["questions"][0]["action"] == "skip_not_applicable"
