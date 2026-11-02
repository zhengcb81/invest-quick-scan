"""Legacy reports use only explicit databases; all artifacts live in disposable roots."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import one_click


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _cli(script, *arguments, cwd):
    env = {
        key: value for key, value in os.environ.items()
        if not any(part in key.upper() for part in ("API_KEY", "APIKEY", "TOKEN", "SECRET", "PASSWORD"))
    }
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / script), *map(str, arguments)],
        cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


def _workspace(root, label):
    workspace = root / label
    data = workspace / "data/quick_scan"
    data.mkdir(parents=True)
    entity = "ENT_" + label
    url = "https://example.invalid/" + label
    payload = {
        "entity_id": entity, "observation_id": "OBS_" + label,
        "question_id": "<IQS_1>", "information_cutoff": "2026-10-18",
        "execution": {"search_receipt_id": "SEARCH_SHARED", "search_status": "executed"},
        "answer": {
            "question_id": "<IQS_1>", "response_kind": "score",
            "status": "insufficient_evidence", "score": None,
            "evidence": [{"id": "S1", "url": url, "title": "Synthetic <source>"}],
            "metrics": [], "missing_fields": [],
        },
    }
    with closing(sqlite3.connect(data / "scan.sqlite")) as connection:
        connection.executescript("""
            CREATE TABLE quick_scan_entity(entity_id, canonical_name, identity_state, identity_revision);
            CREATE TABLE quick_scan_security(security_id, entity_id, market, ticker, listing_status);
            CREATE TABLE quick_scan_source_binding(binding_ref, entity_id, source_namespace);
        """)
        connection.execute("INSERT INTO quick_scan_entity VALUES (?,?,?,?)", (entity, label, "verified", 1))
        connection.execute("INSERT INTO quick_scan_security VALUES (?,?,?,?,?)", ("SEC_" + label, entity, "US", label, "active"))
        connection.commit()
    with closing(sqlite3.connect(data / "scan_observations.sqlite")) as connection:
        connection.execute("CREATE TABLE quick_scan_observation(observation_id, entity_id, question_id, observed_at, information_cutoff, payload_json)")
        connection.execute("INSERT INTO quick_scan_observation VALUES (?,?,?,?,?,?)", (
            payload["observation_id"], entity, payload["question_id"], "2026-10-18", "2026-10-18", json.dumps(payload),
        ))
        connection.commit()
    with closing(sqlite3.connect(data / "analysis_subjects.sqlite")) as connection:
        connection.execute("CREATE TABLE analysis_subject(primary_issuer_id)")
        connection.commit()
    work = workspace / "work.sqlite"
    with closing(sqlite3.connect(work)) as connection:
        connection.execute("CREATE TABLE quick_scan_external_result(operation_id, receipt_json)")
        connection.execute("INSERT INTO quick_scan_external_result VALUES (?,?)", (
            "SEARCH_SHARED", json.dumps({"entries": [{"url": url}]}),
        ))
        connection.commit()
    return workspace, work


def _hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*.sqlite")}


def test_one_click_relative_paths_belong_to_caller_not_child_process(tmp_path):
    with tempfile.TemporaryDirectory(prefix='relative-', dir=tmp_path) as directory:
        caller = Path(directory)
        workspace, work = _workspace(caller, 'B')
        before = _hashes(caller)
        result = _cli('one_click.py', '--workspace', 'B', '--work', 'B/work.sqlite',
                      '--out', 'report', '--links', 'absent-links.json', cwd=caller)
        assert result.returncode == 0, result.stderr
        document = json.loads((caller / 'report/provenance-check/check.json').read_text('utf8'))
        assert document['observations_database'] == str((workspace / 'data/quick_scan/scan_observations.sqlite').resolve())
        assert document['work_database'] == str(work.resolve())
        assert document['pass'] == 1
        assert (caller / 'report/financial-check/check.html').is_file()
        assert _hashes(caller) == before


@pytest.mark.parametrize("label", ["A", "B"])
def test_one_click_binds_provenance_and_artifacts_to_selected_workspace(tmp_path, monkeypatch, label):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        a, _ = _workspace(root, "A")
        b, _ = _workspace(root, "B")
        workspace = a if label == "A" else b
        work = workspace / "work.sqlite"
        before = _hashes(root)
        monkeypatch.setattr(one_click, "ROOT", root)
        monkeypatch.setattr(one_click, "SCRIPTS", SCRIPTS)
        out = root / "report"
        one_click.main(["--workspace", str(workspace), "--work", str(work), "--out", str(out), "--links", str(root / "absent-links.json")])
        provenance = json.loads((out / "provenance-check/check.json").read_text(encoding="utf-8"))
        financial = json.loads((out / "financial-check/check.json").read_text(encoding="utf-8"))
        assert provenance["status"] == "completed"
        assert provenance["observations_database"] == str((workspace / "data/quick_scan/scan_observations.sqlite").resolve())
        assert provenance["work_database"] == str(work.resolve())
        assert provenance["pass"] == 1 and provenance["fail"] == 0
        assert provenance["results"][0]["entity_id"] == "ENT_" + label
        assert financial["workspace"] == str(workspace)
        assert (out / "financial-check/check.html").is_file()
        assert (out / "profiles" / ("ENT_" + label + ".html")).is_file()
        assert str(workspace) in (out / "index.html").read_text(encoding="utf-8")
        assert _hashes(root) == before
    assert not root.exists()


def test_one_click_without_work_is_explicitly_skipped_and_preflight_is_historical(tmp_path, monkeypatch):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        workspace, _ = _workspace(root, "B")
        # A valid old experiment must still be ignored, not silently used as a
        # fallback for the selected B workspace.
        old_observations = root / "runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/scan_observations.sqlite"
        old_work = root / "runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"
        for destination, source in (
            (old_observations, workspace / "data/quick_scan/scan_observations.sqlite"),
            (old_work, workspace / "work.sqlite"),
        ):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        before = _hashes(root)
        historical = root / "docs/implementation/reviews/observation-preflight-2026-10-18/check.json"
        historical.parent.mkdir(parents=True)
        historical.write_text(json.dumps({"packages": 7, "pass": 7, "fail": 0}), encoding="utf-8")
        monkeypatch.setattr(one_click, "ROOT", root)
        monkeypatch.setattr(one_click, "SCRIPTS", SCRIPTS)
        out = root / "report"
        one_click.main(["--workspace", str(workspace), "--out", str(out), "--links", str(root / "absent.json")])
        report = json.loads((out / "provenance-check/check.json").read_text(encoding="utf-8"))
        assert report["status"] == "skipped"
        assert report["reason"] == "work_store_not_configured"
        assert report["pass"] is None and report["observations"] is None
        assert report["results"] == []
        page = (out / "index.html").read_text(encoding="utf-8")
        assert "引用溯源未执行" in page and "--work" in page
        assert "历史观察导入检查" in page and "2026-10-18" in page
        assert "不代表所选工作区" in page
        assert "B" in (out / "profiles/ENT_B.html").read_text(encoding="utf-8")
        assert _hashes(root) == before
    assert not root.exists()


def test_provenance_cli_requires_explicit_databases_without_creating_them(tmp_path):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        result = _cli("observation_provenance_check.py", "--json", root / "check.json", cwd=root)
        assert result.returncode == 2
        assert "--observations" in result.stderr and "--work" in result.stderr
        assert "required" in result.stderr
        assert list(root.iterdir()) == []


def test_provenance_cli_uses_exact_pair_and_preserves_database_bytes(tmp_path):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        _, work_a = _workspace(root, "A")
        workspace_b, work_b = _workspace(root, "B")
        observations = workspace_b / "data/quick_scan/scan_observations.sqlite"
        before = _hashes(root)
        for name, work, expected in (("matching", work_b, "pass"), ("different", work_a, "fail")):
            output = root / name
            result = _cli("observation_provenance_check.py", "--observations", observations, "--work", work,
                          "--json", output / "check.json", "--html", output / "nested/check.html", cwd=root)
            assert result.returncode == 0, result.stderr
            report = json.loads((output / "check.json").read_text(encoding="utf-8"))
            assert report["results"][0]["result"] == expected
            assert report["work_database"] == str(work.resolve())
            page = (output / "nested/check.html").read_text(encoding="utf-8")
            assert "&lt;IQS_1&gt;" in page and "<IQS_1>" not in page
            assert str(work) in page
        assert _hashes(root) == before
        assert not list(root.rglob("*-journal"))


@pytest.mark.parametrize("mode", ["receipt_missing", "research_only"])
def test_provenance_unavailable_receipt_or_no_receipt_is_never_a_pass(tmp_path, mode):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        workspace, work = _workspace(root, "B")
        observations = workspace / "data/quick_scan/scan_observations.sqlite"
        if mode == "receipt_missing":
            with closing(sqlite3.connect(work)) as connection:
                connection.execute("DELETE FROM quick_scan_external_result")
                connection.commit()
        else:
            with closing(sqlite3.connect(observations)) as connection:
                payload = json.loads(connection.execute("SELECT payload_json FROM quick_scan_observation").fetchone()[0])
                payload["execution"] = {}
                connection.execute("UPDATE quick_scan_observation SET payload_json=?", (json.dumps(payload),))
                connection.commit()
        before = _hashes(root)
        result = _cli("observation_provenance_check.py", "--observations", observations, "--work", work,
                      "--json", root / "check.json", cwd=root)
        assert result.returncode == 0, result.stderr
        report = json.loads((root / "check.json").read_text(encoding="utf-8"))
        assert report["pass"] == 0 and report[mode] == 1
        assert report["results"][0]["result"] == mode
        assert _hashes(root) == before


def test_provenance_explicit_missing_work_does_not_fall_back_or_create_a_database(tmp_path):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        workspace, _ = _workspace(root, "B")
        missing = root / "absent/work.sqlite"
        result = _cli("observation_provenance_check.py", "--observations",
                      workspace / "data/quick_scan/scan_observations.sqlite", "--work", missing,
                      "--json", root / "check.json", cwd=root)
        assert result.returncode == 2 and "work database missing" in result.stderr
        assert not missing.exists() and not (root / "check.json").exists()


def test_financial_cli_writes_requested_html_and_keeps_source_readonly(tmp_path):
    with tempfile.TemporaryDirectory(prefix="legacy-", dir=tmp_path) as temporary:
        root = Path(temporary)
        workspace, _ = _workspace(root, "B")
        before = _hashes(root)
        (root / "json").mkdir()
        result = _cli("financial_mechanical_check.py", "--workspace", workspace,
                      "--json", root / "json/check.json", "--html", root / "html/check.html", cwd=root)
        assert result.returncode == 0, result.stderr
        report = json.loads((root / "json/check.json").read_text(encoding="utf-8"))
        page = (root / "html/check.html").read_text(encoding="utf-8")
        assert report["observations"] == 1 and report["mechanical_pass"] == 1
        assert str(workspace) in page and "&lt;IQS_1&gt;" in page
        assert "not a financial review" in page
        assert _hashes(root) == before
