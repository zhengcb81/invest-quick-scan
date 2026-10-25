"""The prompt must not starve the model of the evidence it was given.

Regression context (2026-10-22): the search provider returned 1363-1541 character
summaries, but build_prompt() truncated each to 300 characters before handing it
to the model. The substantive numbers (warranty length, parts-to-vehicle ratio)
sat in the second half, so all 24 questions came back insufficient_evidence with
"the retrieval provided no verifiable structural evidence" while the evidence was
in fact present. Truncation must be generous enough to carry the source, bounded
so the prompt stays within a sane budget.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import thin_scan  # noqa: E402


def test_default_basic_coverage_includes_all_framework_questions():
    import question_sets
    _, modules = question_sets.load_library()
    questions = thin_scan.default_basic_questions()
    expected = {q['id'] for name in ('common', 'dupont', 'porter') for q in modules[name]['questions']}
    assert {q['id'] for q in questions} == expected
    assert len(questions) == len(expected)
    assert all(not q['core'] for q in questions if q['module_id'] in ('dupont', 'porter'))


def test_default_basic_coverage_grows_from_library_without_a_fixed_limit(monkeypatch):
    import copy
    import question_sets
    catalog, original = question_sets.load_library()
    modules = copy.deepcopy(original)
    extra = {**modules['common']['questions'][0], 'id': 'EXPANDED_CORE', 'construct_id': 'EXPANDED_CORE'}
    modules['common']['questions'].append(extra)
    monkeypatch.setattr(question_sets, 'load_library', lambda: (catalog, modules))
    assert 'EXPANDED_CORE' in {q['id'] for q in thin_scan.default_basic_questions()}


def test_diagnostics_are_completed_but_never_change_summary_means():
    import question_bank
    result = question_bank.summarize([
        {'question_id': 'IQS_01', 'core': True, 'status': 'scored', 'score': 3},
        {'question_id': 'IND_01', 'core': False, 'status': 'scored', 'score': 4},
        {'question_id': 'DUPONT_01', 'core': False, 'comparison_role': 'diagnostic', 'status': 'scored', 'score': 10},
        {'question_id': 'PORTER_01', 'core': False, 'aggregation': 'diagnostic', 'status': 'scored', 'score': 10},
    ])
    assert result['core_mean'] == 3 and result['context_mean'] == 4
    assert result['diagnostic_total'] == result['diagnostic_scored'] == 2


def test_not_applicable_requires_retrieved_basis_and_never_gets_a_score():
    source = {'url': 'https://example.com/bank', 'title': 'Bank profile', 'date': '2026-01-01'}
    result, problems = thin_scan.clean_answer(
        {'status': 'not_applicable', 'score': 9, 'summary': '普通企业周转率不适用于该银行',
         'evidence': [source['url']]}, [source])
    assert result['status'] == 'not_applicable' and result['score'] is None and not problems
    missing, problems = thin_scan.clean_answer(
        {'status': 'not_applicable', 'score': None, 'summary': '没有资料', 'evidence': []}, [source])
    assert missing['status'] == 'insufficient_evidence' and missing['score'] is None
    assert 'not_applicable_without_basis' in problems


def _source(url: str, summary: str) -> dict:
    return {"url": url, "title": "t", "summary": summary, "date": "2026-10-15", "site": "s"}


def _question() -> dict:
    return {"id": "IQS_01", "question": "q?", "prompt": "BASE PROMPT"}


def test_long_source_summary_is_not_truncated_to_300_chars():
    """A 1400-char summary must reach the model essentially intact."""
    summary = "A" * 700 + "WARRANTY_13_YEARS" + "B" * 700
    prompt, _, _ = thin_scan.build_prompt(
        _question(), "宁德时代", [_source("https://example.com/a", summary)], "2026-10-22", True)

    assert "WARRANTY_13_YEARS" in prompt, "the substantive tail was cut off"
    assert len(summary) < 1500


def test_each_source_is_bounded_so_the_prompt_stays_finite():
    """Generous, but still bounded: one huge page cannot blow the budget."""
    huge = "C" * 50_000
    prompt, _, _ = thin_scan.build_prompt(
        _question(), "co", [_source("https://example.com/a", huge)], "2026-10-22", True)

    assert prompt.count("C") <= thin_scan.SOURCE_SUMMARY_LIMIT
    assert thin_scan.SOURCE_SUMMARY_LIMIT >= 1000


def test_more_sources_are_included_than_a_single_one():
    sources = [_source(f"https://example.com/{i}", f"UNIQUE_SOURCE_{i}_" + "x" * 800) for i in range(5)]
    prompt, _, _ = thin_scan.build_prompt(_question(), "co", sources, "2026-10-22", True)

    included = sum(1 for i in range(5) if f"UNIQUE_SOURCE_{i}_" in prompt)
    assert included >= 3, f"only {included} of 5 sources reached the prompt"


def test_manifest_prompt_hash_is_still_verified():
    """Widening the evidence budget must not weaken the hash check."""
    import hashlib

    question = {"id": "Q", "prompt": "BASE"}
    question["prompt_sha256"] = hashlib.sha256(b"BASE").hexdigest()
    prompt, mode, verified = thin_scan.build_prompt(
        question, "co", [_source("https://example.com/a", "text")], "2026-10-22", True)

    assert mode == "manifest_full" and verified is True
    assert prompt.startswith("BASE")


def test_hash_mismatch_is_still_rejected():
    question = {"id": "Q", "prompt": "BASE", "prompt_sha256": "0" * 64}
    try:
        thin_scan.build_prompt(question, "co", [_source("https://example.com/a", "t")], "2026-10-22", True)
    except ValueError as error:
        assert "prompt hash mismatch" in str(error)
    else:
        raise AssertionError("a tampered manifest prompt was accepted")


def test_bank_mode_budget_leaves_room_for_reasoning():
    """RED regression: 2400 max_tokens was consumed entirely by reasoning.

    deepseek-flash spent all 2400 tokens on reasoning_content (5218 chars) and
    returned empty content with finish_reason=length, so ask_model reported
    model_not_json. Across 24 questions that produced 24 zeros. The budget must
    cover reasoning plus the JSON answer.
    """
    assert thin_scan.BANK_MAX_TOKENS >= 12000, "reasoning models need headroom above reasoning"
    assert thin_scan.FLAT_MAX_TOKENS >= 1200
    assert thin_scan.BANK_MAX_TOKENS > thin_scan.FLAT_MAX_TOKENS


def test_empty_content_with_length_finish_is_reported_distinctly(monkeypatch):
    """An exhausted budget must not be reported as malformed JSON."""
    monkeypatch.setenv("STUB_KEY", "test-key")

    def fake_post(url, key, body, timeout):
        return 200, {"choices": [{"message": {"content": "", "reasoning_content": "thinking..."},
                                  "finish_reason": "length"}],
                     "usage": {"completion_tokens": body.get("max_tokens")}}

    monkeypatch.setattr(thin_scan, "post_json", fake_post)
    provider = {"id": "stub", "model": "m", "endpoint": "https://example.invalid/chat",
                "key_env": "STUB_KEY"}

    answer = thin_scan.ask_model(provider, "prompt")

    assert answer.get("error") == "model_truncated_no_content"


def test_reasoning_only_response_is_not_silently_accepted(monkeypatch):
    """reasoning_content must never be treated as the answer."""
    monkeypatch.setenv("STUB_KEY", "test-key")

    def fake_post(url, key, body, timeout):
        return 200, {"choices": [{"message": {"content": "", "reasoning_content": '{"score": 9}'},
                                  "finish_reason": "length"}]}

    monkeypatch.setattr(thin_scan, "post_json", fake_post)
    provider = {"id": "stub", "model": "m", "endpoint": "https://example.invalid/chat",
                "key_env": "STUB_KEY"}

    answer = thin_scan.ask_model(provider, "prompt")

    assert "error" in answer, "a score hidden in reasoning must not be accepted"
