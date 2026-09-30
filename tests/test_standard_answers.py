import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import question_sets as qs
import standard_answers as sa


def content(q, fact=False):
    evidence = [{'id': 'e1', 'title': '虚构示例，不是实际公司证据',
                 'url': 'https://example.invalid/company', 'published_at': '2026-09-01',
                 'claim': '仅用于离线验证标准输出。'}]
    return dict(question_id=q['id'], response_kind='fact' if fact else 'score',
                status='answered' if fact else 'scored', score=None if fact else 8,
                summary='虚构示例：核心客户持续采购，但客户集中仍需关注。',
                information_as_of='2026-09-01', period_start='2026-01-01', period_end='2026-06-30',
                basis='current', trend='stable', confidence='medium', metrics=[],
                items=[dict(name='示例工业客户（虚构）', canonical_entity_id=None, aliases=[],
                            relation=q['relations'][0], segment='示例分部', role='customer',
                            commercial_stage='commercial', description='虚构客户关系，未提供交易规模。',
                            valid_from='2026-01-01', valid_to=None, taxonomy_id=None,
                            metrics=[], evidence_ids=['e1'], confidence='medium')] if fact else [],
                evidence=evidence, counterevidence='虚构示例：尚缺分客户采购历史。',
                watch_triggers=['跟踪客户复购和供货状态'], missing_fields=['客户收入占比'],
                coverage={'status': 'partial', 'reason': '离线样例仅覆盖少量字段，不代表完整公司画像。'})


def fixture(fact=False):
    profile = {**qs.read_json(ROOT / 'examples/profile.json'), 'entity_id': 'EXAMPLE_ENTITY_A',
               'security_id': 'EXAMPLE_SECURITY_A', 'as_of': '2026-09-22'}
    if fact:
        _, selected = sa.select_facts(profile)
        q = next(q for q in selected if q['id'] == 'FACT_10')
    else:
        _, modules = qs.load_library()
        q = {**modules['common']['questions'][0], 'module_id': 'common'}
    q = {**q, 'prompt': sa.standard_prompt(q, profile)}
    manifest = dict(answer_format='standard-1', template_version='1.0.0' if fact else '3.0.0',
                    method_id='facts-1' if fact else 'core-constructs-v1/context-1', profile=profile, questions=[q])
    receipt = dict(manifest_sha256=sa.digest(manifest), run_id='EXAMPLE_RUN_A', scan_id='EXAMPLE_SCAN_A',
                   inputset_id='EXAMPLE_INPUT_V1', task_mode='comparison', comparison_group_id='EXAMPLE_GROUP',
                   requests={q['id']: dict(provider='EXAMPLE_PROVIDER', model_requested='EXAMPLE_MODEL_A',
                       model_resolved='EXAMPLE_MODEL_A', model_revision='fixture-1',
                       request_id='EXAMPLE_REQUEST', attempt_id='EXAMPLE_ATTEMPT',
                       started_at='2026-09-22T09:00:00Z', answered_at='2026-09-22T09:01:00Z',
                       search_status='executed', search_receipt_id='OFFLINE_FIXTURE_NOT_SEARCH_PROOF',
                       prompt_sha256=hashlib.sha256(q['prompt'].encode()).hexdigest())})
    return manifest, {q['id']: content(q, fact)}, receipt


def published_fixture(*, entity_id='EXAMPLE_ENTITY_A', company='示例工业设备股份有限公司（虚构）',
                      ticker='EXAMPLE'):
    profile = {**fixture()[0]['profile'], 'entity_id': entity_id, 'company': company,
               'ticker': ticker}
    with tempfile.TemporaryDirectory(prefix='iqs-published-standard-') as tmp:
        qs.compose(profile, 'quick', tmp, 'standard-1')
        manifest = qs.read_json(Path(tmp) / 'manifest.json')
    question = manifest['questions'][0]
    receipt = dict(manifest_sha256=sa.digest(manifest), run_id='EXAMPLE_RUN_A',
                   scan_id='EXAMPLE_SCAN_A', inputset_id='EXAMPLE_INPUT_V1',
                   task_mode='comparison', comparison_group_id='EXAMPLE_GROUP',
                   requests={question['id']: dict(provider='EXAMPLE_PROVIDER', model_requested='EXAMPLE_MODEL_A',
                       model_resolved='EXAMPLE_MODEL_A', model_revision='fixture-1',
                       request_id='EXAMPLE_REQUEST', attempt_id='EXAMPLE_ATTEMPT',
                       started_at='2026-09-22T09:00:00Z', answered_at='2026-09-22T09:01:00Z',
                       search_status='executed', search_receipt_id='OFFLINE_FIXTURE_NOT_SEARCH_PROOF',
                       prompt_sha256=hashlib.sha256(question['prompt'].encode()).hexdigest())})
    return manifest, {question['id']: content(question)}, receipt


def rehash(record):
    record['observation_id'] = 'obs_' + sa.digest({k: v for k, v in record.items() if k != 'observation_id'})
    return record


class StandardAnswerTests(unittest.TestCase):
    def record(self, fact=False):
        return sa.build_observations(*fixture(fact))['observations'][0]

    def test_fact_library_covers_types_industries_and_stages(self):
        self.assertEqual(sa.validate_fact_library()['questions'], 61)
        _, modules = qs.load_library()
        profile = fixture()[0]['profile']
        for kind, key in [('types', 'company_type'), ('industries', 'industry_modules'), ('stages', 'stage')]:
            for name, m in modules.items():
                if m['kind'] != kind or name == 'cyclical': continue
                p = {**profile, key: [name] if kind == 'industries' else name}
                _, selected = sa.select_facts(p)
                self.assertIn('FACT_' + name.upper(), {q['id'] for q in selected})

    def test_facts_export_uses_existing_question_file_shape_and_no_fake_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            sa.compose_facts(fixture()[0]['profile'], 'quick', tmp)
            exported = qs.read_json(Path(tmp) / 'questions.json')
            self.assertTrue(all(isinstance(q, str) for group in exported for q in group['questions']))
            self.assertIn('不使用score/description外层兼容包装', exported[0]['questions'][0])
            with self.assertRaises(ValueError): sa.compose_facts(fixture()[0]['profile'], 'full', tmp)

    def test_fact_scores_wrong_relations_and_unbound_names_rejected(self):
        m, a, r = fixture(True)
        for mutation in ('score', 'relation', 'evidence'):
            bad = copy.deepcopy(a); answer = next(iter(bad.values()))
            if mutation == 'score': answer['score'] = 5
            elif mutation == 'relation': answer['items'][0]['relation'] = 'made_up_relationship'
            else: answer['items'][0]['evidence_ids'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): sa.build_observations(m, bad, r)

    def test_model_self_report_and_long_documents_rejected(self):
        m, a, r = fixture()
        for key, value in [('model', 'self-claimed-model'), ('summary', 'x' * 801)]:
            bad = copy.deepcopy(a); next(iter(bad.values()))[key] = value
            with self.assertRaises(Exception): sa.build_observations(m, bad, r)

    def test_future_sources_and_invalid_dates_rejected(self):
        m, a, r = fixture()
        for value in ('2026-09-23', 'not-a-date'):
            bad = copy.deepcopy(a); next(iter(bad.values()))['evidence'][0]['published_at'] = value
            with self.assertRaises(Exception): sa.build_observations(m, bad, r)

    def test_receipts_bind_manifest_and_exact_prompt(self):
        m, a, r = fixture()
        for mutation in ('manifest', 'prompt', 'missing'):
            bad = copy.deepcopy(r)
            if mutation == 'manifest': bad['manifest_sha256'] = '0' * 64
            elif mutation == 'prompt': next(iter(bad['requests'].values()))['prompt_sha256'] = '0' * 64
            else: bad['requests'] = {}
            with self.assertRaises(ValueError): sa.build_observations(m, a, bad)

    def test_no_executed_search_receipt_cannot_produce_success(self):
        m, a, r = fixture()
        for key, value in [('search_status', 'unverified'), ('search_receipt_id', None)]:
            bad = copy.deepcopy(r); next(iter(bad['requests'].values()))[key] = value
            with self.assertRaises(ValueError): sa.build_observations(m, a, bad)

    def test_observation_is_immutable_and_reimport_does_not_refresh_timestamp(self):
        m, a, r = fixture()
        first = sa.build_observations(m, a, r)['observations'][0]
        second = sa.build_observations(m, a, r)['observations'][0]
        self.assertEqual(first, second)
        second['answer']['score'] = 9
        with self.assertRaises(ValueError): sa.validate_observation(second)

    def test_timestamp_order_and_utc_required(self):
        m, a, r = fixture()
        for value in ('2026-09-22T08:59:00Z', '2026-09-22T17:01:00+08:00'):
            bad = copy.deepcopy(r); next(iter(bad['requests'].values()))['answered_at'] = value
            with self.assertRaises(ValueError): sa.build_observations(m, a, bad)

    def test_three_axes_do_not_confuse_models_and_business_changes(self):
        a = self.record(); b = copy.deepcopy(a)
        b['entity_id'] = 'EXAMPLE_ENTITY_B'; rehash(b)
        self.assertTrue(sa.compare(a, b, 'company')['comparable'])
        self.assertFalse(sa.compare(a, b, 'time')['comparable'])
        b = copy.deepcopy(a); b['execution']['model_resolved'] = 'EXAMPLE_MODEL_B'; b['answer']['score'] = 6; rehash(b)
        self.assertEqual(sa.compare(a, b, 'model')['score_difference'], -2)
        self.assertFalse(sa.compare(a, b, 'time')['comparable'])
        b['task_mode'] = 'primary'; rehash(b)
        self.assertFalse(sa.compare(a, b, 'model')['comparable'])

    def test_unresolved_model_and_rubric_drift_disable_score_difference(self):
        a = self.record()
        for key, value in [('question_version', '9.0.0'), ('method_id', 'new-method')]:
            b = copy.deepcopy(a); b[key] = value; rehash(b)
            self.assertIsNone(sa.compare(a, b, 'time')['score_difference'])
        b = copy.deepcopy(a); b['execution']['model_resolved'] = None; rehash(b)
        self.assertIn('resolved_model_unknown', sa.compare(a, b, 'model')['reasons'])

    def test_fact_unknown_is_not_an_empty_assertion(self):
        m, a, r = fixture(True); answer = next(iter(a.values())); answer['items'] = []
        with self.assertRaises(ValueError): sa.build_observations(m, a, r)
        answer['status'] = 'insufficient_evidence'; answer['coverage']['status'] = 'unknown'
        result = sa.build_observations(m, a, r)
        self.assertIsNone(result['observations'][0]['answer']['score'])

    def test_standard_scoring_requires_receipts_not_legacy_normalizer(self):
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(fixture()[0]['profile'], 'quick', tmp, 'standard-1')
            m = qs.read_json(Path(tmp) / 'manifest.json')
            self.assertIn('questions/scoring-contexts.json', m['source_sha256'])
            with self.assertRaises(ValueError): qs.normalize(m, {})

    def test_core_quality_does_not_change_with_supplemental_question_count(self):
        results = []
        for mode in ('quick', 'full'):
            with tempfile.TemporaryDirectory() as tmp:
                qs.compose(fixture()[0]['profile'], mode, tmp)
                m = qs.read_json(Path(tmp) / 'manifest.json')
                answers = {}
                for q in m['questions']:
                    score = 5 if q['comparison_role'] == 'core' else 10
                    inner = dict(id=q['id'], status='scored', score=score, confidence='high', rationale='fixture',
                                 evidence=[dict(claim='fixture', title='fixture', url='https://example.invalid/',
                                                published_at='2026-09-01', period='2026H1')],
                                 counterevidence='fixture', sensitivity='fixture', metrics={})
                    answers[q['prompt']] = dict(score=score, description=json.dumps(inner))
                review = dict(company=m['profile']['company'], as_of=m['profile']['as_of'], search_verified=True,
                              search_basis='OFFLINE FIXTURE', accepted_ids=[q['id'] for q in m['questions']])
                results.append(qs.normalize(m, answers, review)['summary']['quality_score'])
        self.assertEqual(results, [5, 5])

    def test_subtype_is_routed_and_incompatible_subtype_rejected(self):
        p = {**fixture()[0]['profile'], 'industry_modules': ['semiconductors'], 'business_subtype': 'fabless'}
        _, modules = qs.load_library(); selected, _, _ = qs.select_questions(p, 'quick', modules)
        self.assertIn('自有工厂利用率不适用', qs.render_question(selected[0], p))
        with self.assertRaises(ValueError): qs.select_questions({**p, 'business_subtype': 'hospital'}, 'quick', modules)

    def test_compatibility_export_matches_current_source(self):
        _, modules = qs.load_library()
        self.assertEqual(qs.read_json(ROOT / 'main_questions.json'),
                         qs.export_questions(sorted(modules['common']['questions'], key=lambda q: q['id'])))

    def test_same_name_fact_prompts_preserve_entity_and_listing_identity(self):
        m, _, _ = fixture(True); q = m['questions'][0]
        other = {**m['profile'], 'entity_id': 'OTHER_ENTITY', 'ticker': 'OTHER_TICKER'}
        self.assertNotEqual(sa.standard_prompt(q, m['profile']), sa.standard_prompt(q, other))
        self.assertIn('OTHER_TICKER', sa.standard_prompt(q, other))

    def test_information_date_and_period_cadence_must_align(self):
        a = self.record(); b = copy.deepcopy(a)
        b['answer']['information_as_of'] = '2025-09-01'; rehash(b)
        self.assertIn('information_as_of_changed', sa.compare(a, b, 'model')['reasons'])
        b = copy.deepcopy(a); b['answer']['period_start'] = '2025-01-01'; b['answer']['period_end'] = '2025-12-31'; rehash(b)
        self.assertIsNone(sa.compare(a, b, 'time')['score_difference'])
        b = copy.deepcopy(a); b['execution']['model_revision'] = None; rehash(b)
        self.assertTrue(any('model_revision_unknown' in w for w in sa.compare(a, b, 'model')['warnings']))

    def test_prompt_definition_change_cannot_hide_behind_same_version_label(self):
        m, a, r = fixture(); first = sa.build_observations(m, a, r)['observations'][0]
        m['questions'][0]['question'] += ' 新增不同判断条件。'
        q = m['questions'][0]; q['prompt'] = sa.standard_prompt(q, m['profile'])
        r['manifest_sha256'] = sa.digest(m)
        r['requests'][q['id']]['prompt_sha256'] = hashlib.sha256(q['prompt'].encode()).hexdigest()
        second = sa.build_observations(m, a, r)['observations'][0]
        self.assertIn('method_id_changed', sa.compare(first, second, 'time')['reasons'])

    def test_published_same_method_is_comparable_across_company_identity(self):
        first = sa.build_observations(*published_fixture())['observations'][0]
        second = sa.build_observations(*published_fixture(
            entity_id='EXAMPLE_ENTITY_B', company='另一家虚构工业设备公司', ticker='EXAMPLE_B'))['observations'][0]
        self.assertNotEqual(first['execution']['prompt_sha256'], second['execution']['prompt_sha256'])
        self.assertEqual(first['method_id'], second['method_id'])
        self.assertTrue(sa.compare(first, second, 'company')['comparable'])

    def test_published_manifest_forgery_fails_before_observation_even_with_new_receipt_hash(self):
        manifest, answers, receipts = published_fixture()
        forged = copy.deepcopy(manifest)
        question = forged['questions'][0]
        question['question'] += ' 伪造额外的评分条件。'
        question['prompt'] = sa.standard_prompt(question, forged['profile'])
        question['prompt_sha256'] = hashlib.sha256(question['prompt'].encode()).hexdigest()
        forged_receipts = copy.deepcopy(receipts)
        forged_receipts['manifest_sha256'] = sa.digest(forged)
        forged_receipts['requests'][question['id']]['prompt_sha256'] = question['prompt_sha256']
        with self.assertRaises(ValueError):
            sa.build_observations(forged, answers, forged_receipts)

    def test_published_observation_rejects_forged_or_removed_package_binding(self):
        record = sa.build_observations(*published_fixture())['observations'][0]
        self.assertEqual(record['schema_version'], '1.1.0')
        self.assertTrue(record['method_id'].startswith('module-locked-v1/'))
        with self.assertRaisesRegex(ValueError, 'independently stored observation ID'):
            sa.validate_observation(record, require_published=True)
        self.assertEqual(sa.validate_observation(record, require_published=True,
                         expected_observation_id=record['observation_id']), record)
        forged = copy.deepcopy(record)
        forged['module_package_id'] = 'pkg_' + '0' * 64
        rehash(forged)
        with self.assertRaisesRegex(ValueError, 'module package unavailable'):
            sa.validate_observation(forged)
        stripped = copy.deepcopy(record)
        del stripped['module_release_id']
        rehash(stripped)
        with self.assertRaisesRegex(ValueError, 'complete module package binding'):
            sa.validate_observation(stripped)

        false_semantic = copy.deepcopy(record)
        false_semantic['question_semantic_sha256'] = 'f' * 64
        false_semantic['method_id'] = false_semantic['method_id'][:-16] + 'f' * 16
        rehash(false_semantic)
        with self.assertRaisesRegex(ValueError, 'semantic fingerprint'):
            sa.validate_observation(false_semantic)

        all_binding_removed = copy.deepcopy(record)
        for key in ('module_package_id', 'module_release_id',
                    'question_definition_sha256', 'question_semantic_sha256'):
            del all_binding_removed[key]
        rehash(all_binding_removed)
        with self.assertRaisesRegex(ValueError, 'published observation missing package binding'):
            sa.validate_observation(all_binding_removed)

        rewritten = copy.deepcopy(record)
        rewritten['answer']['score'] = 7
        rehash(rewritten)
        with self.assertRaisesRegex(ValueError, 'immutable stored identity'):
            sa.validate_observation(rewritten, require_published=True,
                                    expected_observation_id=record['observation_id'])

        legacy = self.record()
        self.assertEqual(sa.validate_observation(legacy), legacy)
        with self.assertRaisesRegex(ValueError, 'published ingest'):
            sa.validate_observation(legacy, require_published=True,
                                    expected_observation_id=legacy['observation_id'])

    def test_canonical_units_and_unmapped_metric_comparison(self):
        m, a, r = fixture(); answer = next(iter(a.values()))
        metric = dict(metric_id='operating.repeat_purchase_share', value=82, unit='percent', currency=None,
                      unit_detail=None, period_start='2026-01-01', period_end='2026-06-30', basis='current',
                      definition='同一期间的重复采购客户占比', evidence_ids=['e1'])
        answer['metrics'] = [metric]
        first = sa.build_observations(m, a, r)['observations'][0]
        metric['unit'] = 'ratio'
        with self.assertRaises(ValueError): sa.build_observations(m, a, r)
        metric.update(metric_id='custom.repeat_ratio', unit='ratio')
        custom = sa.build_observations(m, a, r)['observations'][0]
        self.assertFalse(sa.compare(custom, custom, 'time')['metrics'][0]['comparable'])
        self.assertTrue(sa.compare(first, first, 'time')['metrics'][0]['comparable'])


if __name__ == '__main__':
    unittest.main()
