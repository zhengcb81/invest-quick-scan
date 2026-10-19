import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_bank  # noqa: E402


def _manifest(path: Path) -> Path:
    document = {
        "module_package_id": "pkg_test",
        "module_release_id": "modrel_test",
        "modules": ["common", "auto"],
        "mode": "quick",
        "max_questions": 3,
        "module_locks": [{"module_id": "common", "version": "3.0.0"}],
        "questions": [
            {
                "id": "IQS_01", "question": "q1", "dimension": "business", "priority": 1,
                "module_id": "common", "construct_id": "IQS_01", "comparison_role": "core",
                "scope": "entity", "evidence": ["e1"], "anchors": {"1": "a", "5": "b", "10": "c"},
                "prompt_sha256": "a" * 64, "semantic_sha256": "b" * 64, "definition_sha256": "c" * 64,
            },
            {
                "id": "IQS_02", "question": "q2", "dimension": "business", "priority": 1,
                "module_id": "common", "construct_id": "IQS_02", "comparison_role": "core",
                "scope": "entity", "evidence": ["e2"], "anchors": {"1": "a", "5": "b", "10": "c"},
                "prompt_sha256": "d" * 64, "semantic_sha256": "e" * 64, "definition_sha256": "f" * 64,
            },
            {
                "id": "AUTO_01", "question": "q3", "dimension": "moat", "priority": 1,
                "module_id": "auto", "construct_id": None, "comparison_role": "context",
                "scope": "entity", "evidence": ["e3"], "anchors": {"1": "a", "5": "b", "10": "c"},
                "prompt_sha256": "1" * 64, "semantic_sha256": "2" * 64, "definition_sha256": "3" * 64,
            },
        ],
    }
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_manifest_records_bank_identity_and_core(tmp_path):
    bank = question_bank.load_manifest(_manifest(tmp_path / "manifest.json"))
    assert bank["identity"]["package_id"] == "pkg_test"
    assert bank["identity"]["question_count"] == 3
    assert bank["identity"]["mode"] == "quick"
    assert [q["core"] for q in bank["questions"]] == [True, True, False]
    assert bank["questions"][2]["module_id"] == "auto"
    assert len(bank["identity"]["manifest_sha256"]) == 64


def test_summarize_splits_core_and_context():
    rows = [
        {"core": True, "status": "scored", "score": 6},
        {"core": True, "status": "insufficient_evidence", "score": None},
        {"core": False, "status": "scored", "score": 8},
    ]
    summary = question_bank.summarize(rows)
    assert summary["core_total"] == 2
    assert summary["core_scored"] == 1
    assert summary["core_mean"] == 6
    assert summary["context_total"] == 1
    assert summary["context_scored"] == 1
    assert summary["context_mean"] == 8


def test_manifest_rejects_duplicate_ids(tmp_path):
    path = _manifest(tmp_path / "manifest.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    document["questions"][1]["id"] = document["questions"][0]["id"]
    path.write_text(json.dumps(document), encoding="utf-8")
    try:
        question_bank.load_manifest(path)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate question id was accepted")


def test_thin_scan_dry_run_binds_bank(tmp_path):
    manifest = _manifest(tmp_path / "manifest.json")
    out = tmp_path / "out"
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts/thin_scan.py"),
         "--company", "测试公司", "--out", str(out), "--dry-run",
         "--bank-manifest", str(manifest)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    assert done.returncode == 0, done.stderr
    document = json.loads((out / "answers.json").read_text(encoding="utf-8"))
    assert document["bank"]["package_id"] == "pkg_test"
    assert document["summary"]["core_total"] == 2
    assert document["summary"]["context_total"] == 1
    assert document["answers"][2]["module_id"] == "auto"
    assert document["answers"][0]["definition_sha256"] == "c" * 64


def test_build_prompt_verifies_manifest_hash(tmp_path):
    import hashlib
    import thin_scan

    prompt = "[IQS_01] test prompt"
    question = {
        "id": "IQS_01",
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }
    built, mode, verified = thin_scan.build_prompt(question, "测试公司", [], "2026-10-19", True)
    assert mode == "manifest_full"
    assert verified is True
    assert prompt in built
    question["prompt_sha256"] = "0" * 64
    try:
        thin_scan.build_prompt(question, "测试公司", [], "2026-10-19", True)
    except ValueError as error:
        assert "hash mismatch" in str(error)
    else:
        raise AssertionError("prompt hash mismatch was accepted")


def test_normalize_bank_answer_reads_engine_schema():
    import json as _json
    import thin_scan

    raw = {
        "score": 7,
        "description": _json.dumps({
            "status": "scored",
            "score": 7,
            "rationale": "理由",
            "evidence": [{"url": "https://example.com/a", "claim": "c"}],
        }),
    }
    answer = thin_scan.normalize_bank_answer(raw)
    assert answer["status"] == "scored"
    assert answer["score"] == 7
    assert answer["summary"] == "理由"
    assert answer["evidence"] == ["https://example.com/a"]


def test_compose_gate_requires_industry_for_operating():
    import compose_company_bank

    assert compose_company_bank.coverage_gap({"company_type": "operating", "industry_modules": []}) == [
        "industry_unresolved_for_operating"]
    assert compose_company_bank.coverage_gap({"company_type": "operating", "industry_modules": ["auto"]}) == []
    assert compose_company_bank.coverage_gap({"company_type": "bank", "industry_modules": []}) == []
