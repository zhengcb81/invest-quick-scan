"""Independent r1 follow-up: fixed negatives in both modes plus compatibility checks."""
import json
import pytest
from src.providers.llm_response_parser import LLMResponseParser
from test_acceptance_counterexamples import invoke, outer


@pytest.mark.parametrize('mode', ['strict', 'fallback'])
@pytest.mark.parametrize('case', ['unknown', 'score_conflict', 'id_conflict', 'duplicate'])
def test_r0_fixed_cases_fail_closed_in_direct_and_regex_modes(mode, case):
    if case == 'duplicate':
        text = ('{"entity_id":"issuer:review-fixture","company_name":"Fictional Fixture Corp",'
                '"question_id":"IQS_06","question_id":"IQS_05","score":8,"description":"ambiguous"}')
    else:
        inner = dict(id='IQS_06' if case == 'id_conflict' else 'IQS_05',
                     status='insufficient_evidence' if case == 'unknown' else 'scored',
                     score=None if case == 'unknown' else 8)
        text = outer(8 if case == 'id_conflict' else 5, json.dumps(inner))
    if mode == 'fallback':
        text = 'Legacy surrounding text\n```json\n' + text + '\n```\nEnd.'
    result = LLMResponseParser().parse_structured_response(
        text, expected_question_id='IQS_05', expected_entity_id='issuer:review-fixture',
        expected_company_name='Fictional Fixture Corp', strict_json_only=mode == 'strict')
    assert result is None


def test_nonanswer_json_description_is_still_native_prose():
    text = outer(8, json.dumps({'business': 'fictional equipment', 'period': '2026H1'}))
    assert LLMResponseParser().parse_structured_response(text, strict_json_only=True).score == 8


def test_r1_regex_must_not_promote_nested_object_from_duplicate_key_response():
    content = ('{"question_id":"IQS_06","question_id":"IQS_05","score":8,'
               '"description":"ambiguous outer",'
               '"metadata":{"question_id":"IQS_05","score":9,"description":"not the answer"}}')
    assert LLMResponseParser().parse_structured_response(
        content, expected_question_id='IQS_05') is None


def test_valid_existing_structured_description_remains_compatible_through_cli(monkeypatch, tmp_path):
    # This complete, agreeing structured description is the currently documented IQS
    # legacy/screening shape, not an inner/outer conflict. This oracle is unchanged
    # from the pre-r1 consumer success criterion and intentionally detects migration breakage.
    inner = dict(id='IQS_05', status='scored', score=8, confidence='high',
                 rationale='Fictional source supports the assessment', information_as_of='2026-09-24',
                 period_start=None, period_end=None, basis='current',
                 evidence=[dict(claim='Fictional review evidence', title='Offline fixture',
                                url='https://example.invalid/review', published_at=None, period='not_applicable')],
                 counterevidence='Fictional contrary evidence', sensitivity='Fictional downside', metrics={})
    answer, exit_code, calls = invoke(monkeypatch, tmp_path, outer(8, json.dumps(inner), status='scored'))
    assert answer['score'] == 8, 'A valid supported consumer shape must not regress to an unknown answer'
    assert exit_code == 0 and calls == 1
