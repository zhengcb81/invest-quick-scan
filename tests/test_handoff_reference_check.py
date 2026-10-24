"""Reference-integrity checks catch what shape validation cannot.

Context (2026-10-23): two delivered handoffs passed the shape check while citing
a corrupted commit id, twelve changed_paths that were never written, and a
content_hash matching no file. The schema enforces only minLength 7 on commits, so
none of that is visible to a shape check.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import handoff_reference_check as refs  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                          text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


@pytest.fixture()
def repo(tmp_path):
    """A real git repo with one commit, so commit lookups are meaningful."""
    work = tmp_path / "repo"
    work.mkdir()
    _git(work, "init", "-q")
    _git(work, "config", "user.email", "t@example.com")
    _git(work, "config", "user.name", "t")
    (work / "src").mkdir()
    (work / "src" / "code.py").write_text("print('hi')\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-q", "-m", "initial")
    return work


def _handoff(repo: Path, **overrides) -> dict:
    document = {
        "snapshot": {
            "repository": str(repo),
            "base_commit": _git(repo, "rev-parse", "HEAD"),
            "result_commit": _git(repo, "rev-parse", "HEAD"),
            "snapshot_commit": None,
        },
        "scope": {"changed_paths": ["src/code.py"]},
        "interfaces": [],
    }
    document.update(overrides)
    return document


def test_a_truthful_handoff_has_no_problems(repo, tmp_path):
    handoff = _handoff(repo)
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_corrupted_commit_id_is_reported(repo, tmp_path):
    """A 40-hex string that is not a commit: the exact 2026-10-23 defect."""
    real = _git(repo, "rev-parse", "HEAD")
    corrupted = real[:7] + "57e0cf6d0d22e8fdd5e83ee39a80c0e7c"
    handoff = _handoff(repo)
    handoff["snapshot"]["result_commit"] = corrupted
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    problems = refs.verify_all(handoff, path)

    assert any(p["kind"] == "git_ref_missing" and p["field"] == "snapshot.result_commit"
               for p in problems)


def test_phantom_changed_path_is_reported(repo, tmp_path):
    handoff = _handoff(repo)
    handoff["scope"]["changed_paths"] = ["src/code.py", "review/logs-round2/never-written.log"]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    problems = refs.verify_all(handoff, path)

    missing = [p for p in problems if p["kind"] == "changed_path_missing"]
    assert len(missing) == 1
    assert missing[0]["path"] == "review/logs-round2/never-written.log"


def test_path_present_only_in_history_is_accepted(repo, tmp_path):
    """A file committed then deleted still counts as delivered."""
    doomed = repo / "src" / "gone.py"
    doomed.write_text("x\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "add")
    _git(repo, "rm", "-q", "src/gone.py")
    _git(repo, "commit", "-q", "-m", "remove")

    handoff = _handoff(repo)
    handoff["scope"]["changed_paths"] = ["src/gone.py"]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_produced_interface_hash_must_match_a_file(repo, tmp_path):
    digest = hashlib.sha256((repo / "src" / "code.py").read_bytes()).hexdigest()
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "code", "direction": "produced", "content_hash": digest}]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_unmatched_produced_hash_is_reported(repo, tmp_path):
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "shape", "direction": "produced",
                              "content_hash": "d" * 64}]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    problems = refs.verify_all(handoff, path)

    assert any(p["kind"] == "interface_hash_unmatched" for p in problems)


def test_consumed_interface_is_not_required_to_match_locally(repo, tmp_path):
    """An input read from another repo can never hash to a local file."""
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "roster", "direction": "consumed",
                              "content_hash": "e" * 64}]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_artifact_hash_mismatch_is_reported(repo, tmp_path):
    handoff_dir = tmp_path / "docs" / "handoff"
    handoff_dir.mkdir(parents=True)
    handoff = _handoff(repo)
    path = handoff_dir / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    actual = hashlib.sha256((repo / "src" / "code.py").read_bytes()).hexdigest()
    (handoff_dir / "artifacts.json").write_text(json.dumps({
        "artifacts": [{"path": "src/code.py", "sha256": "f" * 64, "bytes": 1}]
    }), encoding="utf-8")

    problems = refs.check_artifacts_self_hashes(path, repo)

    assert len(problems) == 1
    assert problems[0]["kind"] == "artifact_hash_mismatch"
    assert problems[0]["actual"] == actual


def test_metadata_files_are_exempt_from_self_hashing(repo, tmp_path):
    """handoff.json cannot contain its own hash; requiring it forces churn."""
    handoff_dir = tmp_path / "docs" / "handoff"
    handoff_dir.mkdir(parents=True)
    handoff = _handoff(repo)
    path = handoff_dir / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    (handoff_dir / "artifacts.json").write_text(json.dumps({
        "artifacts": [
            {"path": "handoff.json", "sha256": "0" * 64, "bytes": 1},
            {"path": "artifacts.json", "sha256": "1" * 64, "bytes": 1},
            {"path": "cleanup.json", "sha256": "2" * 64, "bytes": 1},
        ]
    }), encoding="utf-8")

    assert refs.check_artifacts_self_hashes(path, repo) == []


def test_missing_repository_is_reported(tmp_path):
    handoff = {"snapshot": {"repository": str(tmp_path / "nope")},
               "scope": {"changed_paths": []}, "interfaces": []}
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    problems = refs.verify_all(handoff, path)

    assert any(p["kind"] == "repo_not_found" for p in problems)


def test_dotfile_paths_keep_their_leading_dot(repo, tmp_path):
    """'.gitignore' must not be stripped to 'gitignore' by a naive lstrip."""
    (repo / ".gitignore").write_text("*.pyc\n", encoding="utf-8")

    handoff = _handoff(repo)
    handoff["scope"]["changed_paths"] = [".gitignore"]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_interface_hash_resolves_in_a_repo_declared_by_a_check(repo, tmp_path):
    """A cross-repo contract (UI resolver) is found via the handoff's own command."""
    ui = tmp_path / "ui-lab"
    ui.mkdir()
    (ui / "contracts.py").write_text("SHAPE = 1\n", encoding="utf-8")
    digest = hashlib.sha256((ui / "contracts.py").read_bytes()).hexdigest()
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "ui_shape", "direction": "both",
                              "content_hash": digest}]
    handoff["verification"] = {"checks": [
        {"name": "parity", "command": f"python scripts/parity.py --ui-repo {ui}"}]}
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_interface_hash_unmatched_when_no_repo_declares_it(repo, tmp_path):
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "ui_shape", "direction": "both",
                              "content_hash": "a" * 64}]
    handoff["verification"] = {"checks": [
        {"name": "parity", "command": "python scripts/parity.py"}]}
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    problems = refs.verify_all(handoff, path)

    assert any(p["kind"] == "interface_hash_unmatched" for p in problems)


def test_artifact_hash_from_result_commit_survives_a_later_rewrite(repo, tmp_path):
    """A follow-up package may rewrite a shared file; the old handoff stays valid.

    The handoff describes the tree at result_commit. Judging its declared hashes
    against today's worktree turns every later refactor into a false failure.
    """
    handoff_dir = tmp_path / "docs" / "handoff"
    handoff_dir.mkdir(parents=True)
    handoff = _handoff(repo)
    path = handoff_dir / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    committed = hashlib.sha256((repo / "src" / "code.py").read_bytes()).hexdigest()
    (handoff_dir / "artifacts.json").write_text(json.dumps({
        "artifacts": [{"path": "src/code.py", "sha256": committed, "bytes": 1}]
    }), encoding="utf-8")

    (repo / "src" / "code.py").write_text("print('rewritten')\n", encoding="utf-8")

    assert refs.check_artifacts_self_hashes(
        path, repo, commit=handoff["snapshot"]["result_commit"]) == []
    assert refs.verify_all(handoff, path) == []


def test_interface_hash_from_result_commit_survives_a_later_rewrite(repo, tmp_path):
    committed = hashlib.sha256((repo / "src" / "code.py").read_bytes()).hexdigest()
    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "code", "direction": "produced",
                              "content_hash": committed}]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    (repo / "src" / "code.py").write_text("print('rewritten')\n", encoding="utf-8")

    assert refs.verify_all(handoff, path) == []


def test_artifact_hash_matching_neither_worktree_nor_commit_is_still_reported(repo, tmp_path):
    """The commit fallback must not become a blanket pass."""
    handoff_dir = tmp_path / "docs" / "handoff"
    handoff_dir.mkdir(parents=True)
    handoff = _handoff(repo)
    path = handoff_dir / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    (handoff_dir / "artifacts.json").write_text(json.dumps({
        "artifacts": [{"path": "src/code.py", "sha256": "f" * 64, "bytes": 1}]
    }), encoding="utf-8")

    problems = refs.check_artifacts_self_hashes(
        path, repo, commit=handoff["snapshot"]["result_commit"])

    assert [p["kind"] for p in problems] == ["artifact_hash_mismatch"]


def test_raw_blob_hash_is_accepted_for_a_crlf_checkout(repo, tmp_path):
    """Generators differ: some hash the raw blob, some the worktree bytes.

    With core.autocrlf the two differ only by newlines. The check is about which
    content was delivered, so either form must resolve.
    """
    (repo / "src" / "code.py").write_text("print('hi')\r\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "crlf")
    raw = subprocess.run(["git", "show", "HEAD:src/code.py"], cwd=repo,
                         capture_output=True).stdout
    filtered = subprocess.run(["git", "cat-file", "--filters", "HEAD:src/code.py"],
                              cwd=repo, capture_output=True).stdout
    if raw == filtered:
        pytest.skip("checkout does not rewrite newlines")

    handoff = _handoff(repo)
    handoff["interfaces"] = [{"name": "code", "direction": "produced",
                              "content_hash": hashlib.sha256(raw).hexdigest()}]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")

    assert refs.verify_all(handoff, path) == []
