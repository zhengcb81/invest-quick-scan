"""F2-IQS-FEEDBACK: per-question coverage and mixed-scale lineage feedback.

The owner publishes one immutable company snapshot. This lane re-derives, from
that public evidence only, which frozen questions were actually observed, which
scale group each belongs to, and whether the snapshot's own completeness claim
agrees with the references it binds. A partial result must stay partial; a
contradictory claim must be reported, never smoothed into "complete".

Fixtures under ``tests/fixtures/company_coverage`` are derived from the real
36-question V2 owner request saved by MANIFEST-DELIVERY-01; only the omissions
used to exercise the feedback are injected, and the one modelled fixture says so
in its own name. No company run, owner read or registry write happens here.
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
RESULT_CHECKS = {'coverage-claim', 'scale-lineage', 'question-status',
                 'missing-questions', 'release-binding', 'owner-absence'}


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
    assert coverage['unexpected_question_ids'] == []
    assert coverage['scale_versions'] == ['1.0.0', '2.0.0']
    assert coverage['missing_scale_versions'] == []
    assert coverage['undeclared_scale_versions'] == []
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


def test_an_honestly_declared_empty_group_stays_a_legal_partial_result():
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
    # The declaration is honest, so the snapshot is consistent with itself.
    assert coverage['claim_matches_refs'] is True
    assert coverage['missing_scale_versions'] == []
    # The dropped group is still published: a reader sees which scale is empty.
    response = projection.project_result(owner_payload(result))
    published = [group for group in response['coverage']['groups'] if group['empty']]
    assert [(group['rubric_version'], group['aggregation_role']) for group in published] == [
        ('2.0.0', 'quality_core')
    ]


def test_a_scale_the_snapshot_declares_without_any_group_is_partial():
    """Every group of a declared rubric removed while the scales still list it.

    A single group removed next to a surviving group of the same rubric is not
    decidable from the public snapshot alone (see the handoff's known limits).
    """
    result = snapshot('result-complete-mixed.json')
    dropped = [group for group in result['lineage_groups']
               if group['rubric_version'] == '2.0.0']
    dropped_ids = {group['lineage_group_id'] for group in dropped}
    result['lineage_groups'] = [group for group in result['lineage_groups']
                                if group['lineage_group_id'] not in dropped_ids]
    result['observation_refs'] = [reference for reference in result['observation_refs']
                                  if reference['lineage_group_id'] not in dropped_ids]
    result['completeness'] = {'manifest_question_count': 31, 'observed_count': 31,
                              'missing_question_ids': []}

    coverage = coverage_api.derive_coverage(result)

    assert coverage['scale_versions'] == ['1.0.0', '2.0.0']
    assert coverage['missing_scale_versions'] == ['2.0.0']
    assert coverage['missing_question_ids'] == []
    assert coverage['verdict'] == 'partial'


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


def test_a_reference_outside_the_frozen_release_is_counted_separately():
    result = snapshot('result-complete-mixed.json')
    extra = dict(result['observation_refs'][0], question_id='NOT_IN_RELEASE',
                 observation_id='obs_' + 'e' * 64)
    result['observation_refs'].append(extra)

    coverage = coverage_api.derive_coverage(result)

    assert coverage['unexpected_question_ids'] == ['NOT_IN_RELEASE']
    # The stray reference never inflates the result into "more than complete".
    assert coverage['observed_count'] == 36
    assert coverage['claim_matches_refs'] is True
    assert coverage['verdict'] == 'complete'


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


def test_a_settled_receipt_without_an_observation_is_never_called_completed():
    result = snapshot('result-partial-35of36.json')

    coverage = coverage_api.derive_coverage(result, receipts=receipts())

    statuses = {question['question_id']: question['status'] for question in coverage['questions']}
    # PORTER_05 has no bound observation: the receipt's "completed" means the
    # attempt settled, not that the answer was saved.
    assert statuses['PORTER_05'] == 'settled_unsaved'
    assert 'PORTER_05' in coverage['receipt_conflicts']
    assert coverage['verdict'] == 'partial'


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
    response = projection.project_result(owner_payload(result),
                                         question_receipts=supplied)
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
    assert rows['scale-lineage']['actual'] == 'scales-addressable'
    assert rows['scale-lineage']['disposition'] == 'expected'
    assert rows['release-binding']['actual'] == 'refs-bind-frozen-questions'
    assert set(rows) == RESULT_CHECKS


def test_feedback_reports_a_complete_mixed_scale_result_as_expected():
    rows = _by_check(_rows(snapshot('result-complete-mixed.json')))

    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'
    assert rows['scale-lineage']['actual'] == 'scales-addressable'
    assert rows['question-status']['actual'] == 'statuses-published'
    assert rows['missing-questions']['actual'] == 'missing-kept'
    assert rows['release-binding']['actual'] == 'refs-bind-frozen-questions'
    assert all(row['disposition'] == 'expected' for row in rows.values()), rows


def test_an_honestly_declared_empty_group_is_disclosed_not_blamed():
    rows = _by_check(_rows(snapshot('result-group-dropped.json')))

    # A declared gap is legal partial data: the projection discloses it through
    # coverage.groups[].empty and does not report a deviation against anyone.
    assert rows['scale-lineage']['actual'] == 'scales-addressable'
    assert rows['scale-lineage']['disposition'] == 'expected'
    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'
    assert rows['missing-questions']['actual'] == 'missing-kept'
    assert all(row['disposition'] == 'expected' for row in rows.values()), rows


def test_a_scale_without_a_group_is_reported_against_the_owner():
    result = snapshot('result-complete-mixed.json')
    dropped = [group for group in result['lineage_groups']
               if group['rubric_version'] == '2.0.0']
    dropped_ids = {group['lineage_group_id'] for group in dropped}
    result['lineage_groups'] = [group for group in result['lineage_groups']
                                if group['lineage_group_id'] not in dropped_ids]
    result['observation_refs'] = [reference for reference in result['observation_refs']
                                  if reference['lineage_group_id'] not in dropped_ids]
    result['completeness'] = {'manifest_question_count': 31, 'observed_count': 31,
                              'missing_question_ids': []}

    rows = _by_check(_rows(result))

    assert rows['scale-lineage']['actual'] == 'scale-without-group'
    assert rows['scale-lineage']['disposition'] == 'deviation'
    assert rows['scale-lineage']['owner'] == 'stockwiki'
    assert rows['scale-lineage']['issue_key'] == 'stockwiki-company-result-scale-lineage'
    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'


def test_a_reference_outside_every_group_is_reported_as_a_lineage_break():
    result = snapshot('result-complete-mixed.json')
    result['observation_refs'][0]['lineage_group_id'] = 'lg_' + '9' * 20

    rows = _by_check(_rows(result))

    assert rows['scale-lineage']['actual'] == 'scale-without-group'
    assert rows['scale-lineage']['disposition'] == 'deviation'


def test_a_reference_outside_the_release_is_reported_against_the_owner():
    result = snapshot('result-complete-mixed.json')
    result['observation_refs'].append(dict(result['observation_refs'][0],
                                           question_id='NOT_IN_RELEASE',
                                           observation_id='obs_' + 'e' * 64))

    rows = _by_check(_rows(result))

    assert rows['release-binding']['actual'] == 'refs-outside-release'
    assert rows['release-binding']['disposition'] == 'deviation'
    assert rows['release-binding']['owner'] == 'stockwiki'
    # The stray reference does not turn a complete result into a partial one.
    assert rows['coverage-claim']['actual'] == 'claim-matches-refs'


def test_a_v2_result_without_its_groups_is_not_treated_as_a_v1_result():
    result = snapshot('result-complete-mixed.json')
    result.pop('lineage_groups')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['assessment_protocol'] == 'stockwiki.company_assessment/2'
    assert coverage['group_issue'] == 'lineage-groups-missing'
    assert coverage['verdict'] == 'unknown'
    assert _by_check(_rows(result))['scale-lineage']['actual'] == 'scale-without-group'


def test_a_v1_result_without_groups_stays_a_declared_completeness_read():
    result = snapshot('result-complete-mixed.json')
    result.pop('lineage_groups')
    result.pop('assessment_protocol')
    result.pop('scale_versions')

    coverage = coverage_api.derive_coverage(result)

    assert coverage['basis'] == 'declared-completeness'
    assert coverage['group_issue'] is None
    assert coverage['verdict'] == 'complete'


def test_a_projection_that_drops_a_declared_gap_is_reported():
    envelope = projection.project_result(owner_payload(snapshot('result-partial-35of36.json')))
    envelope['coverage']['missing_question_ids'] = []

    rows = _by_check(feedback.observations(envelope, read='result'))

    assert rows['missing-questions']['actual'] == 'missing-dropped'
    assert rows['missing-questions']['disposition'] == 'deviation'
    assert rows['missing-questions']['issue_key'] == 'iqs-company-result-missing-questions-dropped'


def test_the_four_question_states_are_published_for_a_modelled_run():
    result = snapshot('result-modelled-run-states.json')
    supplied = receipts('receipts-modelled-run-states.json')

    response = projection.project_result(owner_payload(result),
                                         question_receipts=supplied)
    statuses = {question['question_id']: question['status']
                for question in response['coverage']['questions']}

    assert statuses['IQS_01'] == 'completed'
    assert statuses['PORTER_01'] == 'provider_filtered'
    assert statuses['PORTER_02'] == 'provider_filtered'
    assert statuses['DUPONT_04'] == 'provider_truncated'
    assert statuses['DUPONT_05'] == 'provider_truncated'
    assert statuses['IQS_22'] == 'settled_unsaved'
    # A question with no receipt and no observation is not guessed.
    assert statuses['IQS_03'] == 'unknown'
    assert response['coverage']['verdict'] == 'partial'
    rows = _by_check(feedback.observations(response, read='result', receipts=supplied))
    assert rows['question-status']['actual'] == 'statuses-published'
    assert rows['question-status']['disposition'] == 'expected'


def test_a_history_read_reports_its_own_check_and_no_false_absence():
    items = [{'result_id': 'cas_' + '4' * 20, 'status': 'formal',
              'information_cutoff': '2026-11-08', 'registered_at': '2026-11-16T00:00:00Z',
              'questionnaire_version': '3.2.1', 'scale_version': None,
              'manifest_question_count': 36, 'observed_count': 35,
              'aggregate_score': None,
              'aggregate_score_reason': 'company_aggregate_authority_missing'}]
    response = projection.project_history(history_payload(items), limit=20, offset=0)

    rows = feedback.observations(response, read='history')

    assert [row['check_id'] for row in rows] == ['history-coverage']
    assert rows[0]['actual'] == 'items-marked'
    assert rows[0]['disposition'] == 'expected'
    assert rows[0]['step_id'] == f'company-history/{ENTITY}'


def test_a_history_item_without_counts_is_reported_as_unmarked():
    items = [{'result_id': 'cas_' + '5' * 20, 'status': 'formal',
              'information_cutoff': '2026-11-08', 'registered_at': '2026-11-16T00:00:00Z',
              'questionnaire_version': '3.2.1', 'scale_version': None,
              'aggregate_score': None,
              'aggregate_score_reason': 'company_aggregate_authority_missing'}]
    response = projection.project_history(history_payload(items), limit=20, offset=0)

    rows = feedback.observations(response, read='history')

    assert rows[0]['actual'] == 'items-unmarked'
    assert rows[0]['disposition'] == 'deviation'
    assert rows[0]['issue_key'] == 'iqs-company-history-coverage-unmarked'


def test_feedback_keeps_a_reasoned_absence_as_expected():
    rows = _by_check(feedback.observations(
        projection.project_result(absence_payload()), read='result'))

    assert rows['owner-absence']['actual'] == 'reason-named'
    assert rows['owner-absence']['disposition'] == 'expected'
    for check_id in ('coverage-claim', 'scale-lineage', 'question-status',
                     'missing-questions', 'release-binding'):
        assert rows[check_id]['disposition'] == 'unknown'
        assert rows[check_id]['actual'] == 'no-result'


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
    assert {row['check_id'] for row in rows} == RESULT_CHECKS
    # Identity is derived from the public read, not from a wall clock.
    assert rows == _rows(snapshot('result-partial-35of36.json'))


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
    assert len(lines) == 6
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
    assert len(rows) == 6
    assert all(row['run_id'] == 'scan-real-1' for row in rows)
    claimed = next(row for row in rows if row['check_id'] == 'coverage-claim')
    assert claimed['actual'] == 'complete-claimed'
    assert claimed['disposition'] == 'deviation'
    # The business read is unchanged by the observation write.
    again = projection.read_company_assessment(
        config, 'company_result', {'entity_id': ENTITY})
    assert again['owner_payload'] == envelope['owner_payload']


def test_the_public_read_uses_the_supplied_receipts_in_its_published_coverage(tmp_path):
    config = _cli_deployment(tmp_path)
    result = snapshot('result-modelled-run-states.json')
    supplied = receipts('receipts-modelled-run-states.json')
    reply = {**owner_payload(result)['owner_payload'], 'entity_id': ENTITY, 'action': 'read'}
    _cli_reply(config, ['read'], stdout=json.dumps(reply))
    out = tmp_path / 'read.jsonl'
    monkeypatch_env = {'RESEARCH_FEEDBACK_OUT': str(out)}
    import os
    previous = os.environ.get('RESEARCH_FEEDBACK_OUT')
    os.environ.update(monkeypatch_env)
    try:
        envelope = projection.read_company_assessment(
            config, 'company_result', {'entity_id': ENTITY},
            question_receipts=supplied)
        published = projection.project_result(envelope, question_receipts=supplied)
    finally:
        if previous is None:
            os.environ.pop('RESEARCH_FEEDBACK_OUT', None)
        else:
            os.environ['RESEARCH_FEEDBACK_OUT'] = previous

    statuses = {question['question_id']: question['status']
                for question in published['coverage']['questions']}
    assert statuses['PORTER_01'] == 'provider_filtered'
    assert statuses['DUPONT_04'] == 'provider_truncated'
    assert statuses['IQS_22'] == 'settled_unsaved'
    # The rows are computed from the same receipt-aware coverage, so a receipt
    # never produces a false "statuses-missing".
    rows = _by_check(feedback.observations(published, read='result', receipts=supplied))
    assert rows['question-status']['disposition'] == 'expected'


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
    assert len(rows) == 6
    assert {row['run_id'] for row in rows} == {'replay-1'}
    claim = next(row for row in rows if row['check_id'] == 'coverage-claim')
    assert claim['actual'] == 'complete-claimed'


def test_the_replay_tool_classifies_a_modelled_run_with_its_receipts(tmp_path):
    import company_result_feedback as tool

    out = tmp_path / 'tool.jsonl'
    code = tool.main([
        '--inject-result', str(FIXTURES / 'result-modelled-run-states.json'),
        '--receipts', str(FIXTURES / 'receipts-modelled-run-states.json'),
        '--out', str(out)])

    assert code == 0
    rows = [json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]
    assert {row['disposition'] for row in rows} == {'expected'}


def test_the_replay_tool_reports_a_refused_read_without_writing(tmp_path):
    import company_result_feedback as tool

    out = tmp_path / 'tool.jsonl'
    code = tool.main([
        '--stockwiki-root', str(tmp_path), '--workspace-root', str(tmp_path),
        '--entity', ENTITY, '--out', str(out)])

    assert code == 2
    assert not out.exists()
