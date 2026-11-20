"""Recovery and immutable evidence for the IQS native coverage checker."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/company_coverage/answers-partial-24of38.json"
OWNER = "invest-quick-scan"
ORIGINAL_RUN = "thin-bank-catl-full-2026-10-22/final"


def _digest(value):
    body = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha256(body.encode("ascii")).hexdigest()


def _key(kind, *scope):
    return _digest([kind, OWNER, *scope])


def _request(kind, scope, payload, *, method="submit"):
    key = _key(kind, *scope)
    return dict(
        schema_version="feedback-action/1",
        owner=OWNER,
        kind=kind,
        method=method,
        action_id=key,
        request_digest=_digest([OWNER, kind, key, payload]),
        payload=payload,
    )


@pytest.fixture
def saved_run(tmp_path, monkeypatch):
    root = tmp_path / "runs"
    run = root / ORIGINAL_RUN
    run.mkdir(parents=True)
    shutil.copyfile(FIXTURE, run / "answers.json")
    (run / "run-log.json").write_text("[]", encoding="utf-8")
    (run / "index.html").write_text("<html></html>", encoding="utf-8")
    out = tmp_path / "native.jsonl"
    monkeypatch.setenv("RESEARCH_FEEDBACK_OUT", str(out))
    monkeypatch.setenv("RESEARCH_FEEDBACK_ATTEMPT_ID", "scan-result-check")
    monkeypatch.delenv("RESEARCH_FEEDBACK_RUN_ID", raising=False)
    monkeypatch.setenv("IQS_FEEDBACK_RUNS_ROOT", str(root))
    return root, run, out


def _program(name, *args, request=None):
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-X",
            "utf8",
            str(ROOT / "scripts" / name),
            *map(str, args),
        ],
        cwd=ROOT,
        input=json.dumps(request) if request else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _observe(run, out, *, previous=None):
    args = ["--run", run]
    if previous:
        args += ["--previous-check", previous]
    check = _program("scan_result_check.py", *args)
    assert check.returncode == 1, check.stderr
    assert json.loads(check.stdout)["coverage"] == "partial"
    return json.loads(out.read_text(encoding="utf-8").splitlines()[-1])


def _native_call(root, db, command, *args, request=None, expect=0):
    process = _program(
        "iqs_feedback_owner.py",
        "--db",
        db,
        "--runs-root",
        root,
        command,
        *args,
        request=request,
    )
    assert process.returncode == expect, process.stderr or process.stdout
    return json.loads(process.stdout)


def _input(row):
    key = _digest(
        [
            row["owner"],
            row["origin_owner"],
            row["run_id"],
            row["attempt_id"],
            row["step_id"],
            row["check_id"],
        ]
    )
    return key, {"occurrence_id": key, "observation": row}


def _archived_check(path):
    # Native pre-F2 revision printed these values from the same frozen run.
    path.write_text(
        json.dumps({"question_count": 24, "scored": 15, "ok": True, "usable": True}),
        encoding="utf-8",
    )
    return path


def test_producer_distinguishes_honest_partial_from_archived_misclaim_and_keeps_exit_code(
    tmp_path,
    saved_run,
    monkeypatch,
):
    _, run, out = saved_run
    check = _observe(run, out)
    assert (check["run_id"], check["attempt_id"]) == (ORIGINAL_RUN, "scan-result-check")
    assert check["actual"] == check["expected"] == "partial-marked"
    assert check["disposition"] == "expected"
    previous = _archived_check(tmp_path / "previous.json")
    check = _observe(run, out, previous=previous)
    assert check["actual"] == "complete-claimed"
    assert check["disposition"] == "deviation"
    assert check["evidence_ref"].endswith(sha256(FIXTURE.read_bytes()).hexdigest())

    saved = out.read_bytes()
    monkeypatch.delenv("RESEARCH_FEEDBACK_OUT")
    completed = _program(
        "scan_result_check.py", "--run", run, "--previous-check", previous
    )
    assert completed.returncode == 1
    assert out.read_bytes() == saved


def test_concurrent_repair_then_restart_reads_the_exact_two_lost_replies(
    tmp_path, saved_run
):
    root, run, out = saved_run
    immutable = {path: path.read_bytes() for path in run.iterdir()}
    observation = _observe(
        run, out, previous=_archived_check(tmp_path / "previous.json")
    )
    key, payload = _input(observation)
    db = tmp_path / "owner.sqlite"

    def native(command, *args, request=None, expect=0):
        return _native_call(root, db, command, *args, request=request, expect=expect)

    assert native("get-action", key) == {}
    assert not db.exists()
    triage = native("triage", request=_request("triage", [key], payload))["result"]
    assert triage["decision"] == "repair"
    assert triage["gate_review"]["decision"] == "narrow"
    issue, generation = triage["issue_ref"], triage["generation"]
    repair = _request(
        "repair", [issue, generation], dict(issue_ref=issue, generation=generation)
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        repair_replies = list(
            pool.map(lambda _: native("repair", request=repair), range(2))
        )
    assert repair_replies[0] == repair_replies[1]

    # The caller discards both repair replies. A new process reads the durable result.
    repaired = native("get-action", repair["action_id"])["receipt"]
    assert repaired["request"] == repair
    fixed = repaired["result"]["fixed_version"]
    published = native("get-coverage", repair["action_id"])["coverage"]
    assert published["run_id"] == ORIGINAL_RUN
    assert published["attempt_id"] == "scan-result-check"
    assert (published["coverage"], published["usable"]) == ("partial", False)
    assert (published["question_count"], published["manifest_question_count"]) == (
        24,
        38,
    )
    assert published["missing_question_count"] == 14
    assert published["historical_cost_state"] == "unknown"
    assert (
        published["new_searches"]
        == published["new_model_calls"]
        == published["new_cost_micros"]
        == 0
    )

    scope = [key, OWNER, issue, fixed]
    replay = _request(
        "replay",
        scope,
        dict(
            **payload,
            issue_ref=issue,
            issue_owner=OWNER,
            original_occurrence_id=key,
            fixed_version=fixed,
            acquisition="reuse_only",
        ),
    )
    verified = native("replay", request=replay)["result"]
    assert verified["verdict"] == "verified"
    report = _request(
        "report",
        [*scope, "verified"],
        dict(
            occurrence_id=key,
            original_occurrence_id=key,
            origin_owner=OWNER,
            fixed_version=fixed,
            issue_ref=issue,
            verdict="verified",
            evidence_ref=verified["evidence_ref"],
        ),
    )
    native("report", request=report)
    report_receipt = native("get-action", report["action_id"])["receipt"]
    assert report_receipt["request"] == report
    assert report_receipt["result"]["recorded"] is True
    assert native("report", request=report)["result"] == report_receipt["result"]

    wrong = {**report["payload"], "evidence_ref": "iqs:other"}
    conflict = _request("report", [*scope, "verified"], wrong)
    assert native("report", request=conflict, expect=2)["code"] == "action_conflict"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM actions").fetchone()[0] == 4
    assert {path: path.read_bytes() for path in run.iterdir()} == immutable


def test_reconciliation_reads_original_and_preserves_unknown_cost_and_missing_state(
    tmp_path, saved_run
):
    root, run, out = saved_run
    key, payload = _input(_observe(run, out))
    db = tmp_path / "owner.sqlite"
    action = _request("reconcile", [key], payload, method="lookup")
    before = _native_call(root, db, "reconcile", request=action)
    assert before == {
        "state": "done",
        "result": {
            "status": "cost_unknown",
            "job_status": "succeeded",
            "cost_state": "unknown",
            "evidence_ref": payload["observation"]["evidence_ref"],
            "recorded_search_cost_micros": None,
            "new_model_calls": 0,
            "new_searches": 0,
            "new_cost_micros": 0,
        },
    }
    assert not db.exists()
    (run / "answers.json").unlink()
    after = _native_call(root, db, "reconcile", request=action)
    assert after["result"]["job_status"] == "unconfirmed"
    assert after["result"]["cost_state"] == "unknown"
    assert not db.exists()


def test_out_of_scope_observation_never_writes_a_coverage_result(tmp_path, saved_run):
    root, run, out = saved_run
    observation = _observe(
        run, out, previous=_archived_check(tmp_path / "previous.json")
    )
    observation["evidence_ref"] = observation["evidence_ref"].replace(
        "/runs/", "/runs/../"
    )
    key, payload = _input(observation)
    db = tmp_path / "owner.sqlite"
    triage = _native_call(
        root, db, "triage", request=_request("triage", [key], payload)
    )["result"]
    assert triage["decision"] == "needs_evidence"
    assert (
        _native_call(root, db, "get-coverage", _key("repair", "F2-IQS-0001", key)) == {}
    )


def test_observation_write_failure_keeps_native_partial_output(saved_run):
    _, run, out = saved_run
    out.mkdir()
    completed = _program("scan_result_check.py", "--run", run)
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["usable"] is False
    assert "feedback observation write failed" in completed.stderr
