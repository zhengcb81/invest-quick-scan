import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_bank  # noqa: E402


def test_thin_default_cli_covers_dynamic_basic_and_preserves_explicit_legacy(tmp_path):
    import question_sets
    _, modules = question_sets.load_library()
    expected = {q['id'] for module in ('common', 'dupont', 'porter') for q in modules[module]['questions']}
    for mode in ('basic', 'legacy'):
        out = tmp_path/mode
        command = [sys.executable, '-B', '-X', 'utf8', str(ROOT/'scripts/thin_scan.py'),
                   '--company', 'dry-run-only', '--out', str(out), '--dry-run']
        if mode == 'legacy':
            command += ['--questions', str(ROOT/'docs/implementation/questions-24.json')]
        done = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, encoding='utf8', timeout=30)
        assert done.returncode == 0, done.stderr
        doc = json.loads((out/'answers.json').read_text(encoding='utf8'))
        want = expected if mode == 'basic' else {q['id'] for q in json.loads((ROOT/'docs/implementation/questions-24.json').read_text(encoding='utf8'))['questions']}
        assert {a['question_id'] for a in doc['answers']} == want
        assert doc['meta']['calls'] == doc['meta']['searches'] == 0
        assert doc['bank'] is None and doc['importable'] is False
        assert doc['summary']['diagnostic_total'] == (sum(len(modules[m]['questions']) for m in ('dupont', 'porter')) if mode == 'basic' else 0)


def test_thin_compare_preserves_type_core_and_excludes_diagnostic_score(tmp_path, monkeypatch):
    import thin_compare
    import question_sets
    _, modules = question_sets.load_library()
    replacement = next(q for q in modules['bank']['questions'] if q.get('comparison_role') == 'core')
    run = tmp_path/'runs'/'thin-scan-test-2026-10-18'
    run.mkdir(parents=True)
    (run/'answers.json').write_text(json.dumps({'company': 'test', 'meta': {'cost_micros': 0}, 'answers': [
        {'question_id': replacement['id'], 'question': replacement['question'], 'core': True, 'status': 'scored', 'score': 3},
        {'question_id': 'DUPONT_01', 'question': 'diagnostic', 'core': False, 'comparison_role': 'diagnostic', 'status': 'scored', 'score': 10},
    ]}), encoding='utf8')
    out = tmp_path/'compare'
    monkeypatch.setattr(sys, 'argv', ['thin_compare.py', '--runs', str(tmp_path/'runs'), '--out', str(out)])
    assert thin_compare.main() == 0
    page = (out/'compare.html').read_text(encoding='utf8')
    assert '<td>2/2</td><td>3.0</td>' in page
    assert "<td class='s'>10</td>" in page and '核心题草稿均分' in page


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
        [sys.executable, '-B', '-X', 'utf8', str(ROOT / "scripts/thin_scan.py"),
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
