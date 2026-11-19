"""F2-IQS-FEEDBACK: per-question coverage and mixed-scale lineage feedback.

The owner publishes one immutable company snapshot. This lane re-derives, from
that public evidence only, which frozen questions were actually observed, which
scale group each belongs to, and whether the snapshot's own completeness claim
agrees with the references it binds. A partial result must stay partial; a
contradictory claim must be reported, never smoothed into "complete".

Fixtures under ``tests/fixtures/company_coverage`` are derived from the real
36-question V2 owner request saved by MANIFEST-DELIVERY-01; only the omissions
used to exercise the feedback are injected. No company run, owner read or
registry write happens here.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import company_result_coverage as coverage_api  # noqa: E402
import dashboard_company_feedback as feedback  # noqa: E402
import dashboard_company_projection as projection  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'company_coverage'
ENTITY = 'ENT_99deceb6-f58a-48b1-bd6b-437621015d76'


def snapshot(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def receipts(name='receipts-manifest-delivery-01.json'):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def owner_payload(result, entity_id=ENTITY):
    return {
        'protocol': projection.PROJECTION_PROTOCOL,
        'projection_version': projection.PROJECTION_VERSION,
        'entity_id': entity_id,
        'read': 'result',
        'owner_payload': {
            'protocol': projection.OWNER_PROTOCOL,
            'schema_version': projection.OWNER_SCHEMA_VERSION,
            'store_id': 'qsobs_x',
            'registry_store_id': 'qsca_x',
            'result': result,
            'reason_code': None,
            'network_calls': 0,
            'llm_calls': 0,
        },
        'network_calls': 0,
        'llm_calls': 0,
    }


def absence_payload(name='owner-read-not-registered.json'):
    owner_read = snapshot(name)
    return {
        'protocol': projection.PROJECTION_PROTOCOL,
        'projection_version': projection.PROJECTION_VERSION,
        'entity_id': owner_read['entity_id'],
        'read': 'result',
        'owner_payload': {key: value for key, value in owner_read.items() if key != 'action'},
        'network_calls': 0,
        'llm_calls': 0,
    }


def history_payload(items, entity_id=ENTITY, limit=20, offset=0):
    return {
        'protocol': projection.PROJECTION_PROTOCOL,
        'projection_version': projection.PROJECTION_VERSION,
        'entity_id': entity_id,
        'read': 'history',
        'owner_payload': {
            'protocol': projection.OWNER_PROTOCOL,
            'schema_version': projection.OWNER_SCHEMA_VERSION,
            'registry_store_id': 'qsca_x',
            'registry_state': 'available',
            'items': items,
            'page': {'limit': limit, 'offset': offset, 'total': len(items)},
            'network_calls': 0,
            'llm_calls': 0,
        },
        'network_calls': 0,
        'llm_calls': 0,
    }


# -- derivation ---------------------------------------------------------------


def test_complete_mixed_scale_result_keeps_every_group_scale():
    result = snapshot('result-complete-mixed.json')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['protocol'] == coverage_api.COVERAGE_PROTOCOL
    assert coverage['verdict'] == 'complete'
    assert coverage['claim_matches_refs'] is True
    assert coverage['basis'] == 'lineage-groups'
    assert coverage['manifest_question_count'] == 36
    assert coverage['observed_count'] == 36
    assert coverage['missing_question_ids'] == []
    assert coverage['scale_versions'] == ['1.0.0', '2.0.0']
    pairs = {(group['rubric_version'], group['aggregation_role']) for group in coverage['groups']}
    assert pairs == {
        ('1.0.0', 'diagnostic_only'), ('1.0.0', 'growth_core'),
        ('1.0.0', 'quality_core'), ('1.0.0', 'valuation_core'),
        ('2.0.0', 'growth_core'), ('2.0.0', 'quality_core'),
    }
    assert sum(group['question_count'] for group in coverage['groups']) == 36
    assert all(group['empty'] is False for group in coverage['groups'])
    # Each question carries the scale of the group it was frozen in.
    group_by_question = {
        question_id: group
        for group in coverage['groups']
        for question_id in group['question_ids']
    }
    for question in coverage['questions']:
        group = group_by_question[question['question_id']]
        assert question['rubric_version'] == group['rubric_version']
        assert question['aggregation_role'] == group['aggregation_role']
        assert question['lineage_group_id'] == group['lineage_group_id']
        assert question['status'] == 'completed'


def test_partial_35_of_36_is_partial_and_keeps_the_missing_question():
    result = snapshot('result-partial-35of36.json')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['verdict'] == 'partial'
    assert coverage['claim_matches_refs'] is True
    assert coverage['missing_question_ids'] == ['PORTER_05']
    assert coverage['declared']['missing_question_ids'] == ['PORTER_05']
    assert coverage['observed_count'] == 35
    statuses = {question['question_id']: question['status'] for question in coverage['questions']}
    assert statuses['PORTER_05'] == 'unknown'
    assert statuses['IQS_01'] == 'completed'


def test_a_complete_claim_over_a_partial_reference_set_is_not_forwarded_as_complete():
    result = snapshot('result-partial-claiming-complete.json')

    coverage = coverage_api.derive_coverage(result)

    assert len(result['observation_refs']) == 35
    assert result['completeness'] == {'manifest_question_count': 36,
                                      'observed_count': 36,
                                      'missing_question_ids': []}
    assert coverage['verdict'] == 'partial'
    assert coverage['claim_matches_refs'] is False
    assert coverage['missing_question_ids'] == ['PORTER_05']
    assert coverage['declared']['missing_question_ids'] == []
    # The owner snapshot itself stays the owner's own statement.
    response = projection.project_result(owner_payload(result))
    assert response['company_result'] == result
    assert response['coverage']['verdict'] == 'partial'
    assert response['coverage']['claim_matches_refs'] is False


def test_a_dropped_lineage_group_is_reported_as_an_empty_group():
    result = snapshot('result-group-dropped.json')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['verdict'] == 'partial'
    empty = [group for group in coverage['groups'] if group['empty']]
    assert [(group['rubric_version'], group['aggregation_role']) for group in empty] == [
        ('2.0.0', 'quality_core')
    ]
    assert empty[0]['observed_count'] == 0
    assert sorted(empty[0]['missing_question_ids']) == ['IQS_05', 'IQS_06', 'IQS_18']
    assert coverage['missing_question_ids'] == ['IQS_05', 'IQS_06', 'IQS_18']
    assert coverage['scale_versions'] == ['1.0.0', '2.0.0']
    # The dropped group is still published: a reader sees which scale is empty.
    response = projection.project_result(owner_payload(result))
    published = [group for group in response['coverage']['groups'] if group['empty']]
    assert [(group['rubric_version'], group['aggregation_role']) for group in published] == [
        ('2.0.0', 'quality_core')
    ]


def test_single_scale_result_is_complete_and_names_its_one_scale():
    result = snapshot('result-single-scale.json')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['verdict'] == 'complete'
    assert coverage['scale_versions'] == ['2.0.0']
    assert len(coverage['groups']) == 1
    assert coverage['groups'][0]['rubric_version'] == '2.0.0'
    assert coverage['groups'][0]['aggregation_role'] == 'quality_core'
    assert coverage['missing_question_ids'] == []


def test_question_and_group_order_do_not_change_coverage_identity():
    result = snapshot('result-complete-mixed.json')
    shuffled = json.loads(json.dumps(result))
    shuffled['observation_refs'] = list(reversed(shuffled['observation_refs']))
    for group in shuffled['lineage_groups']:
        group['question_ids'] = list(reversed(group['question_ids']))
    shuffled['lineage_groups'] = list(reversed(shuffled['lineage_groups']))

    assert coverage_api.derive_coverage(shuffled) == coverage_api.derive_coverage(result)


def test_receipts_separate_filtered_truncated_settled_and_not_run():
    result = {
        'result_id': 'cas_' + '3' * 20,
        'status': 'formal',
        'entity_id': ENTITY,
        'completeness': {'manifest_question_count': 5, 'observed_count': 1,
                         'missing_question_ids': ['Q2', 'Q3', 'Q4', 'Q5']},
        'observation_refs': [{'observation_id': 'obs_' + 'a' * 64, 'question_id': 'Q1',
                              'payload_sha256': 'b' * 64}],
        'scale_version': '1.0.0',
        'scale_versions': ['1.0.0'],
        'assessment_protocol': 'stockwiki.company_assessment/2',
        'lineage_groups': [{'lineage_group_id': 'lg_' + '1' * 20,
                            'rubric_version': '1.0.0',
                            'aggregation_role': 'quality_core',
                            'question_ids': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']}],
    }
    supplied = {'questions': {
        'Q1': {'status': 'completed', 'answer_state': 'scored'},
        'Q2': {'status': 'settled_unsaved', 'answer_state': 'insufficient_evidence'},
        'Q3': {'status': 'provider_filtered', 'answer_state': None},
        'Q4': {'status': 'provider_truncated', 'answer_state': None},
        'Q5': {'status': 'not_run', 'answer_state': None},
    }}

    coverage = coverage_api.derive_coverage(result, receipts=supplied)

    statuses = {question['question_id']: question['status'] for question in coverage['questions']}
    assert statuses == {'Q1': 'completed', 'Q2': 'settled_unsaved',
                        'Q3': 'provider_filtered', 'Q4': 'provider_truncated',
                        'Q5': 'not_run'}
    assert coverage['status_counts'] == {'completed': 1, 'settled_unsaved': 1,
                                         'provider_filtered': 1, 'provider_truncated': 1,
                                         'not_run': 1}
    assert coverage['verdict'] == 'partial'
    assert coverage['unclassified_question_ids'] == []
    answers = {question['question_id']: question.get('answer_state')
               for question in coverage['questions']}
    assert answers['Q1'] == 'scored'


def test_receipts_for_an_unknown_question_or_word_are_refused():
    result = snapshot('result-single-scale.json')
    with pytest.raises(ValueError):
        coverage_api.derive_coverage(
            result, receipts={'questions': {'NOT_A_QUESTION': {'status': 'not_run'}}})
    with pytest.raises(ValueError):
        coverage_api.derive_coverage(
            result, receipts={'questions': {'IQS_01': {'status': 'invented'}}})


def test_an_observation_overrides_a_receipt_that_says_it_was_never_saved():
    result = snapshot('result-single-scale.json')
    supplied = {'questions': {
        'IQS_01': {'status': 'settled_unsaved'},
        'IQS_02': {'status': 'completed', 'answer_state': 'scored'},
    }}

    coverage = coverage_api.derive_coverage(result, receipts=supplied)

    statuses = {question['question_id']: question['status'] for question in coverage['questions']}
    assert statuses == {'IQS_01': 'completed', 'IQS_02': 'completed'}
    assert coverage['receipt_conflicts'] == ['IQS_01']


def test_a_reasoned_absence_keeps_its_reason_and_invents_no_coverage():
    response = projection.project_result(absence_payload())

    assert response['company_result'] is None
    assert response['reason_code'] == 'company_result_not_registered'
    assert response['coverage'] is None


def test_history_page_marks_each_partial_item_and_keeps_the_page_bounds():
    complete = snapshot('result-single-scale.json')
    partial = snapshot('result-partial-35of36.json')
    items = [
        {'result_id': complete['result_id'], 'status': 'formal',
         'information_cutoff': '2026-11-08', 'registered_at': '2026-11-16T00:00:00Z',
         'questionnaire_version': '3.2.1', 'scale_version': '2.0.0',
         'manifest_question_count': 2, 'observed_count': 2,
         'aggregate_score': None, 'aggregate_score_reason': 'company_aggregate_authority_missing'},
        {'result_id': partial['result_id'], 'status': 'formal',
         'information_cutoff': '2026-11-08', 'registered_at': '2026-11-16T00:00:00Z',
         'questionnaire_version': '3.2.1', 'scale_version': None,
         'manifest_question_count': 36, 'observed_count': 35,
         'aggregate_score': None, 'aggregate_score_reason': 'company_aggregate_authority_missing'},
    ]

    response = projection.project_history(history_payload(items), limit=20, offset=0)

    assert response['page'] == {'limit': 20, 'offset': 0, 'total': 2}
    assert response['coverage']['verdict'] == 'partial'
    verdicts = {item['result_id']: item['verdict'] for item in response['coverage']['items']}
    assert verdicts == {complete['result_id']: 'complete',
                        partial['result_id']: 'partial'}
    missing = {item['result_id']: item['missing_question_count']
               for item in response['coverage']['items']}
    assert missing == {complete['result_id']: 0, partial['result_id']: 1}


# -- feedback projection ------------------------------------------------------


def _rows(result, *, supplied=None):
    response = projection.project_result(owner_payload(result))
    return feedback.observations(response, read='result', receipts=supplied)


def _by_check(rows):
    return {row['check_id']: row for row in rows}


def test_feedback_reports_a_partial_result_and_a_false_complete_claim():
    rows = _by_check(_rows(snapshot('result-partial-claiming-complete.json')))

    claim = rows['coverage-claim']
    assert claim['expected'] == 'claim-matches-refs'
    assert claim['actual'] == 'complete-claimed'
    assert claim['disposition'] == 'deviation'
    assert claim['issue_key'] == 'stockwiki-company-result-completeness-claim'
    # The contradiction lives in the owner snapshot: that owner has to fix it.
    assert claim['owner'] == 'stockwiki'
    assert claim['origin_owner'] == 'invest-quick-scan'
    assert rows['missing-questions']['actual'] == 'missing-kept'
    assert rows['missing-questions']['disposition'] == 'expected'
    assert rows['multi-group-lineage']['actual'] == 'no-group-loss'
    assert rows['multi-group-lineage']['disposition'] == 'expected'
    assert rows['multi-group-lineage']['owner'] == 'invest-quick-scan'


def test_feedback_reports_a_complete_mixed_scale_result_as_expected():
    rows = _by_check(_rows(snapshot('result-complete-mixed.json')))

    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'
    assert rows['multi-group-lineage']['actual'] == 'no-group-loss'
    assert rows['question-status']['actual'] == 'statuses-published'
    assert rows['missing-questions']['actual'] == 'missing-kept'
    assert all(row['disposition'] == 'expected' for row in rows.values()), rows


def test_feedback_discloses_a_dropped_group_without_calling_it_complete():
    rows = _by_check(_rows(snapshot('result-group-dropped.json')))

    assert rows['multi-group-lineage']['actual'] == 'group-lost'
    assert rows['multi-group-lineage']['disposition'] == 'deviation'
    assert rows['multi-group-lineage']['issue_key'] == 'iqs-company-result-group-lost'
    assert rows['multi-group-lineage']['owner'] == 'invest-quick-scan'
    # The owner declared those three questions missing, so its claim is honest.
    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'
    assert rows['missing-questions']['actual'] == 'missing-kept'


def test_an_injected_question_outside_every_group_is_reported_as_group_loss():
    result = snapshot('result-complete-mixed.json')
    result['observation_refs'][0]['lineage_group_id'] = 'lg_' + '9' * 20

    rows = _by_check(_rows(result))

    assert rows['multi-group-lineage']['actual'] == 'group-lost'
    assert rows['multi-group-lineage']['disposition'] == 'deviation'


def test_feedback_keeps_a_reasoned_absence_as_expected():
    rows = _by_check(feedback.observations(
        projection.project_result(absence_payload()), read='result'))

    assert rows['owner-absence']['actual'] == 'reason-named'
    assert rows['owner-absence']['disposition'] == 'expected'
    assert rows['coverage-claim']['disposition'] == 'unknown'
    assert rows['coverage-claim']['actual'] == 'no-result'
    assert rows['question-status']['disposition'] == 'unknown'


def test_feedback_rows_carry_the_public_schema_and_a_stable_step_identity():
    rows = _rows(snapshot('result-partial-35of36.json'))
    required = ('schema_version', 'owner', 'run_id', 'attempt_id', 'step_id',
                'check_id', 'expected', 'actual')
    for row in rows:
        assert all(isinstance(row.get(key), str) and row[key] for key in required), row
        assert row['schema_version'] == 'feedback-observation/1'
        assert row['owner'] in {'invest-quick-scan', 'stockwiki'}
        assert row['step_id'] == f'company-result/{ENTITY}'
        assert row['disposition'] in {'expected', 'deviation', 'unknown'}
        assert row['version'] == projection.PROJECTION_VERSION
    assert {row['check_id'] for row in rows} == {
        'coverage-claim', 'multi-group-lineage', 'question-status',
        'missing-questions', 'owner-absence'}
    # Identity is derived from the public read, not from a wall clock.
    assert rows == _rows(snapshot('result-partial-35of36.json'))


def test_a_projection_that_drops_a_declared_gap_is_reported():
    envelope = projection.project_result(owner_payload(snapshot('result-partial-35of36.json')))
    envelope['coverage']['missing_question_ids'] = []

    rows = _by_check(feedback.observations(envelope, read='result'))

    assert rows['missing-questions']['actual'] == 'missing-dropped'
    assert rows['missing-questions']['disposition'] == 'deviation'
    assert rows['missing-questions']['issue_key'] == 'iqs-company-result-missing-questions-dropped'


def test_feedback_uses_the_native_run_and_attempt_identity(tmp_path):
    out = tmp_path / 'observations.jsonl'
    environ = {'RESEARCH_FEEDBACK_OUT': str(out),
               'RESEARCH_FEEDBACK_RUN_ID': 'scan-abc123',
               'RESEARCH_FEEDBACK_ATTEMPT_ID': 'attempt-2'}
    context = feedback.context_from_env(environ, version=projection.PROJECTION_VERSION)
    assert context is not None

    envelope = projection.project_result(owner_payload(snapshot('result-partial-35of36.json')))
    assert feedback.observe(envelope, read='result', environ=environ,
                            version=projection.PROJECTION_VERSION) is True

    lines = out.read_text(encoding='utf-8').splitlines()
    assert len(lines) == 5
    for line in lines:
        row = json.loads(line)
        assert row['run_id'] == 'scan-abc123'
        assert row['attempt_id'] == 'attempt-2'


def test_feedback_is_off_without_an_output_and_survives_an_unwritable_one(tmp_path):
    assert feedback.context_from_env({}) is None
    assert feedback.context_from_env({'RESEARCH_FEEDBACK_OUT': '  '}) is None
    blocked = tmp_path / 'blocked'
    blocked.mkdir()
    context = feedback.context_from_env(
        {'RESEARCH_FEEDBACK_OUT': str(blocked)}, version=projection.PROJECTION_VERSION)
    assert context is not None
    envelope = projection.project_result(owner_payload(snapshot('result-complete-mixed.json')))
    # A directory where the file should be: the write fails, the caller goes on.
    assert feedback.emit(context, feedback.observations(envelope, read='result')) is False
    assert feedback.observe(envelope, read='result',
                            environ={'RESEARCH_FEEDBACK_OUT': str(blocked)}) is False


# -- the public read entry ----------------------------------------------------


def _cli_deployment(tmp_path):
    code_root = tmp_path / 'owner-code'
    code_root.mkdir()
    workspace_root = tmp_path / 'owner-data'
    workspace_root.mkdir()
    return {'stockwiki_root': str(code_root), 'workspace_root': str(workspace_root),
            'stockwiki_python': sys.executable, 'timeout_seconds': 30}


def _cli_reply(config, args, *, stdout='', returncode=0):
    script = Path(config['stockwiki_root']) / 'dashboard_company_assessment_cli.py'
    expected = [*args[:1], '--root', config['workspace_root'], '--entity', ENTITY,
                '--require-identity', *args[1:]]
    script.write_text(
        'import sys\n'
        f'assert sys.argv[1:] == {expected!r}\n'
        f'sys.stdout.write({stdout!r})\n'
        f'raise SystemExit({returncode})\n', encoding='utf-8')


def test_the_public_read_emits_observations_and_keeps_its_business_output(tmp_path, monkeypatch):
    config = _cli_deployment(tmp_path)
    result = snapshot('result-partial-claiming-complete.json')
    reply = {**owner_payload(result)['owner_payload'], 'entity_id': ENTITY, 'action': 'read'}
    _cli_reply(config, ['read'], stdout=json.dumps(reply))
    out = tmp_path / 'feedback' / 'read.jsonl'
    monkeypatch.setenv('RESEARCH_FEEDBACK_OUT', str(out))
    monkeypatch.setenv('RESEARCH_FEEDBACK_RUN_ID', 'scan-real-1')
    monkeypatch.setenv('RESEARCH_FEEDBACK_ATTEMPT_ID', 'attempt-1')

    envelope = projection.read_company_assessment(
        config, 'company_result', {'entity_id': ENTITY})

    assert envelope['owner_payload']['result'] == result
    rows = [json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 5
    assert all(row['run_id'] == 'scan-real-1' for row in rows)
    claimed = next(row for row in rows if row['check_id'] == 'coverage-claim')
    assert claimed['actual'] == 'complete-claimed'
    assert claimed['disposition'] == 'deviation'
    # The business read is unchanged by the observation write.
    again = projection.read_company_assessment(
        config, 'company_result', {'entity_id': ENTITY})
    assert again['owner_payload'] == envelope['owner_payload']


def test_an_unwritable_observation_output_does_not_change_the_public_read(tmp_path, monkeypatch):
    config = _cli_deployment(tmp_path)
    reply = {**owner_payload(snapshot('result-single-scale.json'))['owner_payload'],
             'entity_id': ENTITY, 'action': 'read'}
    _cli_reply(config, ['read'], stdout=json.dumps(reply))
    (tmp_path / 'dir-as-file').mkdir()
    monkeypatch.setenv('RESEARCH_FEEDBACK_OUT', str(tmp_path / 'dir-as-file'))

    envelope = projection.read_company_assessment(
        config, 'company_result', {'entity_id': ENTITY})

    assert envelope['owner_payload']['result']['result_id'] == 'cas_' + '2' * 20


# -- the replay tool ----------------------------------------------------------


def test_the_replay_tool_records_a_temporary_public_response(tmp_path):
    import company_result_feedback as tool

    out = tmp_path / 'tool.jsonl'
    code = tool.main([
        '--inject-result', str(FIXTURES / 'result-partial-claiming-complete.json'),
        '--out', str(out), '--run-id', 'replay-1', '--attempt-id', 'attempt-1'])

    assert code == 0
    rows = [json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 5
    assert {row['run_id'] for row in rows} == {'replay-1'}
    claim = next(row for row in rows if row['check_id'] == 'coverage-claim')
    assert claim['actual'] == 'complete-claimed'


def test_the_replay_tool_reports_a_refused_read_without_writing(tmp_path):
    import company_result_feedback as tool

    out = tmp_path / 'tool.jsonl'
    code = tool.main([
        '--stockwiki-root', str(tmp_path), '--workspace-root', str(tmp_path),
        '--entity', ENTITY, '--out', str(out)])

    assert code == 2
    assert not out.exists()
