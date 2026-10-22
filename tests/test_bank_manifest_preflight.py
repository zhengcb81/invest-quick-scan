"""Pre-flight catches the failure modes that made the 2026-10-19 run invisible."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bank_manifest_preflight as preflight  # noqa: E402


def _question(qid: str, role: str = "core", module: str = "common") -> dict:
    prompt = f"prompt for {qid}"
    import hashlib
    return {
        "id": qid, "question": f"q {qid}", "module_id": module,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "semantic_sha256": "a" * 64, "definition_sha256": "b" * 64,
        "comparison_role": role,
    }


def _manifest(tmp_path: Path, **overrides) -> Path:
    document = {
        "module_package_id": "pkg_test", "module_release_id": "modrel_test",
        "modules": ["common"], "module_locks": [{"module_id": "common", "version": "3.0.0"}],
        "questions": [_question("Q1"), _question("Q2", role="context")],
    }
    document.update(overrides)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_a_healthy_manifest_passes(tmp_path):
    report = preflight.preflight(_manifest(tmp_path))
    assert report["ok"], report["problems"]
    assert report["question_count"] == 2
    assert report["core_count"] == 1 and report["context_count"] == 1


def test_empty_question_list_is_rejected(tmp_path):
    report = preflight.preflight(_manifest(tmp_path, questions=[]))
    assert not report["ok"]
    assert any("no questions" in p for p in report["problems"])


def test_prompt_hash_mismatch_is_rejected(tmp_path):
    document = json.loads(_manifest(tmp_path).read_text(encoding="utf-8"))
    document["questions"][0]["prompt"] = "tampered prompt"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    report = preflight.preflight(path)
    assert not report["ok"]
    assert any("does not match its prompt" in p for p in report["problems"])


def test_duplicate_ids_are_rejected(tmp_path):
    report = preflight.preflight(_manifest(tmp_path, questions=[_question("Q1"), _question("Q1")]))
    assert not report["ok"]
    assert any("duplicate question ids" in p for p in report["problems"])


def test_module_without_a_lock_is_rejected(tmp_path):
    report = preflight.preflight(_manifest(tmp_path, modules=["common", "auto"]))
    assert not report["ok"]
    assert any("without a lock" in p for p in report["problems"])


def test_missing_comparison_role_is_rejected(tmp_path):
    document = json.loads(_manifest(tmp_path).read_text(encoding="utf-8"))
    del document["questions"][0]["comparison_role"]
    path = tmp_path / "norole.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    report = preflight.preflight(path)
    assert not report["ok"]
    assert any("comparison_role" in p for p in report["problems"])


def test_missing_identity_fields_are_rejected(tmp_path):
    document = json.loads(_manifest(tmp_path).read_text(encoding="utf-8"))
    del document["module_package_id"]
    path = tmp_path / "nopkg.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    report = preflight.preflight(path)
    assert not report["ok"]
    assert any("module_package_id" in p for p in report["problems"])


def test_cli_exit_codes(tmp_path):
    good = _manifest(tmp_path / "good" if (tmp_path / "good").mkdir() is None else tmp_path)
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/bank_manifest_preflight.py"),
         "--manifest", str(good)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"questions": []}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/bank_manifest_preflight.py"),
         "--manifest", str(bad)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 2, result.stdout + result.stderr


def test_credential_check_reports_missing_keys(monkeypatch):
    """A missing key must fail the preflight instead of producing an empty run."""
    for name in ("DEEPSEEK_API_KEY", "MIMO_API_KEY", "MINIMAX_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    report = preflight.check_credentials(user_scope=False)

    assert not report["ok"]
    assert "DEEPSEEK_API_KEY" in report["missing"]
    assert all(entry["present"] is False for entry in report["checked"])


def test_credential_check_passes_when_keys_are_present(monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "MIMO_API_KEY", "MINIMAX_API_KEY"):
        monkeypatch.setenv(name, "present")

    report = preflight.check_credentials(user_scope=False)

    assert report["ok"], report["missing"]
    assert report["missing"] == []
    assert report["checked"], "the report must list what it looked for"


def test_cli_fails_when_credentials_are_requested_and_absent(tmp_path, monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "MIMO_API_KEY", "MINIMAX_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    manifest = _manifest(tmp_path)

    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/bank_manifest_preflight.py"),
         "--manifest", str(manifest), "--check-credentials"],
        capture_output=True, text=True, encoding="utf-8",
        env={k: v for k, v in __import__("os").environ.items()
             if k not in ("DEEPSEEK_API_KEY", "MIMO_API_KEY", "MINIMAX_API_KEY")})

    assert result.returncode == 2, result.stdout + result.stderr
    assert "missing credentials" in result.stdout
