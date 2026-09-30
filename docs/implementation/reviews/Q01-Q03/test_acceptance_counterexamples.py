"""Independent fixed-oracle Q01/Q03 acceptance probes; mock HTTP transport only."""
import json
from unittest.mock import Mock
import pytest
import main_with_llm


def invoke(monkeypatch, tmp_path, content):
    (tmp_path / 'logs').mkdir()
    questions = tmp_path / 'questions.json'
    questions.write_text(json.dumps({'categories': [{'category': 'review', 'questions': [
        {'question_id': 'IQS_05', 'text': 'Fictional issuer moat; this is an offline review fixture.'}]}]}), encoding='utf-8')
    (tmp_path / 'llm_apis.json').write_text(json.dumps({'default_provider': 'openai', 'providers': {
        'openai': {'enabled': True, 'api_key': 'offline-review-fixture', 'model': 'fixture-model',
                   'base_url': 'https://api.openai.com/v1/responses', 'max_retries': 1,
                   'format_repair_budget': 0}}}), encoding='utf-8')
    response = Mock()
    response.headers = {'x-request-id': 'req_review_fixture'}
    response.status_code = 200
    response.json.return_value = {'id': 'resp_review_fixture', 'status': 'completed', 'model': 'fixture-model',
        'output': [{'type': 'web_search_call', 'id': 'ws_review_fixture', 'status': 'completed',
                    'action': {'type': 'search', 'sources': [{'type': 'url', 'url': 'https://example.invalid/review'}]}},
                   {'type': 'message', 'content': [{'type': 'output_text', 'text': content}]}]}
    session = Mock()
    session.post.return_value = response
    manager = Mock()
    manager.get_sync_session.return_value = session
    monkeypatch.setattr('src.providers.llm_client.http_client_manager', manager)
    monkeypatch.chdir(tmp_path)
    output = tmp_path / 'result.json'
    monkeypatch.setattr('sys.argv', ['main_with_llm.py', '--company', 'Fictional Fixture Corp',
        '--entity-id', 'issuer:review-fixture', '--provider', 'openai', '--config', str(questions),
        '--output', str(output), '--require-search'])
    exit_code = main_with_llm.main()
    result = json.loads(output.read_text(encoding='utf-8'))
    return result['answers']['IQS_05'], exit_code, session.post.call_count


def outer(score, description, **extra):
    return json.dumps({'entity_id': 'issuer:review-fixture', 'company_name': 'Fictional Fixture Corp',
                       'question_id': 'IQS_05', 'score': score, 'description': description, **extra})


def test_sc01_real_cli_preserves_native_eight(monkeypatch, tmp_path):
    answer, exit_code, calls = invoke(monkeypatch, tmp_path, outer(8, 'Fictional native answer'))
    assert answer['score'] == 8
    assert answer['status'] == 'scored'
    assert exit_code == 0 and calls == 1


def test_sc02_real_cli_preserves_native_unknown_null(monkeypatch, tmp_path):
    answer, _, calls = invoke(monkeypatch, tmp_path, outer(None, 'Evidence missing', status='insufficient_evidence'))
    assert answer['score'] is None and answer['status'] == 'insufficient_evidence'
    assert calls == 1


def test_sc02_legacy_inner_unknown_transport_five_never_becomes_scored(monkeypatch, tmp_path):
    inner = json.dumps({'id': 'IQS_05', 'status': 'insufficient_evidence', 'score': None,
                        'confidence': 'medium', 'rationale': 'No disclosed evidence'})
    answer, _, _ = invoke(monkeypatch, tmp_path, outer(5, inner))
    assert answer['score'] is None, 'SC-02: legacy transport 5 must never become the formal score'
    assert answer['status'] != 'scored'


def test_sc04_inner_outer_score_mismatch_is_not_a_scored_answer(monkeypatch, tmp_path):
    inner = json.dumps({'id': 'IQS_05', 'status': 'scored', 'score': 8,
                        'confidence': 'medium', 'rationale': 'Fictional inner eight'})
    answer, _, _ = invoke(monkeypatch, tmp_path, outer(5, inner))
    assert answer['score'] is None, 'SC-04: outer 5 / inner 8 must fail closed'


def test_sc04_wrong_inner_question_id_is_not_a_scored_answer(monkeypatch, tmp_path):
    inner = json.dumps({'id': 'IQS_06', 'status': 'scored', 'score': 8,
                        'confidence': 'medium', 'rationale': 'Fictional answer to a different question'})
    answer, _, _ = invoke(monkeypatch, tmp_path, outer(8, inner))
    assert answer['score'] is None, 'SC-04: conflicting nested question identity must fail closed'


def test_llm07_conflicting_duplicate_json_question_ids_do_not_choose_last(monkeypatch, tmp_path):
    text = ('{"entity_id":"issuer:review-fixture","company_name":"Fictional Fixture Corp",'
            '"question_id":"IQS_06","question_id":"IQS_05","score":8,"description":"ambiguous ID"}')
    answer, _, calls = invoke(monkeypatch, tmp_path, text)
    assert answer['score'] is None, 'LLM-07: repeated conflicting IDs must be rejected, not overwritten by json.loads'
    assert calls == 1


@pytest.mark.parametrize('score', [True, False, 0, 11, 1.5, '8', 'NaN'])
def test_sc03_invalid_score_real_cli_is_never_adopted(monkeypatch, tmp_path, score):
    answer, _, calls = invoke(monkeypatch, tmp_path, outer(score, 'Invalid value fixture'))
    assert answer['score'] is None and answer['status'] != 'scored'
    assert calls == 1
