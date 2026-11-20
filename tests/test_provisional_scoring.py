"""Scoring judgment and evidence confidence are independent public dimensions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from iqs_scan.questions import question_prompts as prompts
from test_standard_answers import fixture, sa


def test_current_score_rules_request_tentative_judgment_and_explicit_gaps():
    manifest, _, _ = fixture()
    question = manifest['questions'][0]
    rules = prompts.typed_semantic_rules(question)
    assert '暂定' in rules
    assert 'confidence=low' in rules
    assert 'missing_fields' in rules
    assert '编造' in rules
    assert prompts.legacy_typed_semantic_rules(question) != rules


def test_new_renderer_retains_the_original_renderer_and_fact_semantics():
    manifest, _, _ = fixture()
    profile, question = manifest['profile'], manifest['questions'][0]
    old = prompts.renderer_for_release('1.0.0',
        '6b221598394f5c23a5f724c0b9bac895bcb44eee87c9189285eb605a6ebf21fe')
    current = prompts.renderer_for_release(prompts.RENDERER_VERSION,
                                          prompts.renderer_rules_sha256())
    assert prompts.RENDERER_VERSION != '1.0.0'
    assert current.standard_prompt(question, profile).startswith(old.standard_prompt(question, profile))
    assert '暂定' not in old.standard_prompt(question, profile)
    assert '暂定' in current.standard_prompt(question, profile)
    manifest, _, _ = fixture(fact=True)
    profile, question = manifest['profile'], manifest['questions'][0]
    assert current.standard_prompt(question, profile) == old.standard_prompt(question, profile)
    assert prompts.typed_semantic_rules(question) == prompts.legacy_typed_semantic_rules(question)


def test_low_confidence_score_comparison_keeps_delta_with_a_warning():
    manifest, answers, receipt = fixture()
    for answer in answers.values():
        answer['confidence'] = 'low'
    record = sa.build_observations(manifest, answers, receipt)['observations'][0]
    comparison = sa.compare(record, record, 'time')
    assert comparison['comparable']
    assert comparison['score_difference'] == 0
    assert any('low_confidence' in warning for warning in comparison['warnings'])
