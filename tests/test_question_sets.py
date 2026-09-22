"""Behavior checks for routing, evidence handling and the real upstream file contract."""
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import question_sets as qs


class QuestionSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.modules = qs.load_library()
        cls.profile = qs.read_json(ROOT / 'examples/profile.json')

    def make_manifest(self, mode='quick', profile=None):
        profile = copy.deepcopy(profile or self.profile)
        questions, modules, replacements = qs.select_questions(profile, mode, self.modules)
        return {'profile': profile, 'mode': mode, 'modules': modules, 'replacements': replacements,
                'questions': [{**q, 'prompt': qs.render_question(q, profile)} for q in questions]}

    def good_answer(self, q, score=7, status='scored', confidence='high'):
        inner = {'id': q['id'], 'status': status, 'score': score if status == 'scored' else None,
                 'confidence': confidence, 'rationale': 'offline fixture',
                 'evidence': [{'claim': 'fixture claim', 'title': 'fixture',
                               'url': 'https://example.com/evidence', 'published_at': '2026-09-01',
                               'period': 'FY2025'}],
                 'counterevidence': 'fixture contrary evidence',
                 'sensitivity': 'fixture downside', 'metrics': {}}
        return {'score': score if status == 'scored' else 5,
                'description': json.dumps(inner, ensure_ascii=False)}

    def review(self, manifest):
        return {'company': manifest['profile']['company'], 'as_of': manifest['profile']['as_of'],
                'search_verified': True, 'search_basis': 'OFFLINE TEST FIXTURE ONLY',
                'accepted_ids': [q['id'] for q in manifest['questions']]}

    def test_library_and_export_are_consistent(self):
        stats = qs.validate_library()
        exported = qs.read_json(ROOT / 'main_questions.json')
        count = sum(len(category['questions']) for category in exported)
        self.assertEqual(count, len(self.modules['common']['questions']))
        self.assertGreater(stats['questions'], count)
        self.assertTrue(all(isinstance(q, str) for c in exported for q in c['questions']))

    def test_quick_covers_core_judgments_without_automatic_dupont_or_porter(self):
        types = [k for k, m in self.modules.items() if m['kind'] == 'types']
        stages = [k for k, m in self.modules.items() if m['kind'] == 'stages' and k != 'cyclical']
        for company_type in types:
            for stage in stages:
                with self.subTest(company_type=company_type, stage=stage):
                    profile = {**self.profile, 'company_type': company_type, 'stage': stage,
                               'industry_modules': ['industrial'] if company_type in ('operating', 'pre_revenue') else []}
                    chosen, _, replacements = qs.select_questions(profile, 'quick', self.modules)
                    covered = {q['id'] for q in chosen} | set(replacements)
                    self.assertTrue({q['id'] for q in self.modules['common']['questions']} <= covered)
                    self.assertFalse(any(q.get('framework') for q in chosen))
                    self.assertEqual(len(chosen), len({q['id'] for q in chosen}))
                    for original in ('IQS_12', 'IQS_13', 'IQS_16'):
                        effective_id = replacements.get(original, original)
                        self.assertTrue(next(q for q in chosen if q['id'] == effective_id)['critical'])

    def test_bank_replaces_general_cash_and_balance_questions(self):
        profile = {**self.profile, 'company_type': 'bank', 'industry_modules': [],
                   'cycle_sensitive': False, 'overlays': []}
        questions, _, replacements = qs.select_questions(profile, 'quick', self.modules)
        ids = {q['id'] for q in questions}
        self.assertNotIn('IQS_11', ids)
        self.assertNotIn('IQS_16', ids)
        self.assertNotIn('IQS_22', ids)
        self.assertIn('BANK_06', ids)  # lower priority replacement must still be used
        self.assertEqual(replacements['IQS_22'], 'BANK_06')
        self.assertTrue(next(q for q in questions if q['id'] == 'BANK_01')['critical'])

    def test_stage_and_cycle_are_independent(self):
        manifest = self.make_manifest()
        self.assertIn('mature', manifest['modules'])
        self.assertIn('cyclical', manifest['modules'])
        with self.assertRaises(ValueError):
            self.make_manifest(profile={**self.profile, 'stage': 'cyclical'})

    def test_every_module_is_selectable(self):
        for key, module in self.modules.items():
            profile = copy.deepcopy(self.profile)
            if module['kind'] == 'industries':
                profile['industry_modules'] = [key]
            elif module['kind'] == 'overlays':
                profile['overlays'] = [key]
            else:
                continue
            selected, _, _ = qs.select_questions(profile, 'full', self.modules)
            self.assertTrue(all(q['id'] in {s['id'] for s in selected} for q in module['questions']))

    def test_invalid_profile_is_not_silently_routed(self):
        for change in ({'industry_modules': ['missing']}, {'industry_modules': []},
                       {'quote_date': '2026-09-20'}, {'routing_confidence': 'low'},
                       {'cycle_sensitive': 'false'}, {'overlays': ['controlled', 'controlled']},
                       {'routing_sources': []}, {'recovery_review': 'true'},
                       {'recovery_review': True},
                       {'recovery_review': True, 'recovery_rationale': 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.make_manifest(profile={**self.profile, **change})

    def test_material_overlays_cannot_be_silently_dropped(self):
        profile = {**self.profile, 'overlays': ['controlled', 'distressed', 'cross_border']}
        with self.assertRaises(ValueError):
            self.make_manifest(profile=profile)
        manifest = self.make_manifest('full', profile)
        self.assertIn('distressed', manifest['modules'])

    def test_compose_is_reproducible_and_does_not_overwrite_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'a', Path(tmp) / 'b'
            qs.compose(self.profile, 'quick', first)
            qs.compose(self.profile, 'quick', second)
            self.assertEqual((first / 'manifest.json').read_bytes(), (second / 'manifest.json').read_bytes())
            manifest = qs.read_json(first / 'manifest.json')
            exported = qs.read_json(first / 'questions.json')
            self.assertEqual({q['prompt'] for q in manifest['questions']},
                             {q for cat in exported for q in cat['questions']})
            with self.assertRaises(ValueError):
                qs.compose(self.profile, 'full', first)

    def test_missing_data_and_transport_fives_do_not_become_scores(self):
        manifest = self.make_manifest()
        q = manifest['questions'][0]
        answers = {q['prompt']: self.good_answer(q, status='insufficient_evidence')}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertIsNone(result['questions'][0]['score'])
        self.assertIsNone(result['summary']['quality_score'])
        self.assertEqual(result['summary']['all_question_coverage'], 0)

    def test_defaults_or_upstream_score_corruption_are_rejected(self):
        manifest = self.make_manifest()
        q = manifest['questions'][0]
        bad = self.good_answer(q, score=8)
        bad['score'] = 5
        result = qs.normalize(manifest, {q['prompt']: bad}, self.review(manifest))
        self.assertEqual(result['questions'][0]['status'], 'invalid')
        bad = {'score': 5, 'description': 'LLM API未配置。请配置 API密钥。'}
        result = qs.normalize(manifest, {q['prompt']: bad}, self.review(manifest))
        self.assertEqual(result['questions'][0]['status'], 'invalid')

    def test_model_self_report_cannot_verify_search(self):
        manifest = self.make_manifest()
        answers = {q['prompt']: self.good_answer(q) for q in manifest['questions']}
        result = qs.normalize(manifest, answers)
        self.assertIsNone(result['summary']['quality_score'])
        self.assertTrue(all(q['status'] == 'review_pending' for q in result['questions']))
        incomplete_review = {**self.review(manifest), 'search_basis': ''}
        result = qs.normalize(manifest, answers, incomplete_review)
        self.assertIsNone(result['summary']['quality_score'])

    def test_valid_scores_are_separate_from_growth_and_price(self):
        manifest = self.make_manifest()
        answers = {q['prompt']: self.good_answer(q, 2 if q['dimension'] == 'valuation' else
                                                4 if q['dimension'] == 'growth' else 8)
                   for q in manifest['questions']}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertEqual(result['summary']['quality_score'], 8)
        self.assertEqual(result['summary']['growth_score'], 4)
        self.assertEqual(result['summary']['valuation_score'], 2)
        self.assertEqual(result['summary']['quality_coverage'], 1)

    def test_optional_diagnostics_do_not_change_any_dimension_or_quality_score(self):
        profile = {**self.profile, 'diagnostic_modules': ['dupont', 'porter'],
                   'diagnostic_rationale': {'dupont': 'explain ROE change', 'porter': 'explain profit pool'}}
        manifest = self.make_manifest(profile=profile)
        self.assertEqual(sum(q.get('aggregation') == 'diagnostic' for q in manifest['questions']), 12)
        answers = {q['prompt']: self.good_answer(q, 1 if q.get('aggregation') == 'diagnostic' else 8)
                   for q in manifest['questions']}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertEqual(result['summary']['quality_score'], 8)
        self.assertIn('DUPONT_01', result['summary']['weak_points'])
        self.assertTrue(all(d['score'] == 8 for d in result['summary']['dimensions'].values()))

    def test_full_mode_also_requires_a_specific_reason_for_optional_tools(self):
        full = self.make_manifest('full')
        self.assertFalse(any(q.get('framework') for q in full['questions']))
        for extra in ({'diagnostic_modules': ['dupont']}, {'diagnostic_modules': ['other']},
                      {'diagnostic_modules': ['dupont', 'dupont']}):
            with self.assertRaises(ValueError):
                self.make_manifest(profile={**self.profile, **extra})

    def test_critical_failure_cannot_be_averaged_away(self):
        manifest = self.make_manifest()
        answers = {q['prompt']: self.good_answer(q, 2 if q['id'] == 'IQS_13' else 9)
                   for q in manifest['questions']}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertEqual(result['summary']['quality_coverage'], 1)
        self.assertIsNone(result['summary']['quality_score'])
        self.assertEqual(result['summary']['critical_issues'], [
            {'id': 'IQS_13', 'kind': 'material_concern', 'status': 'scored', 'score': 2}])

    def test_critical_unknown_and_inapplicable_are_not_treated_as_cleared(self):
        manifest = self.make_manifest()
        for state in ('missing', 'not_applicable', 'insufficient_evidence'):
            answers = {q['prompt']: self.good_answer(q, 9) for q in manifest['questions']}
            q = next(q for q in manifest['questions'] if q['id'] == 'IQS_12')
            if state == 'missing':
                del answers[q['prompt']]
            else:
                answers[q['prompt']] = self.good_answer(q, status=state)
            result = qs.normalize(manifest, answers, self.review(manifest))
            self.assertIsNone(result['summary']['quality_score'])
            self.assertEqual(result['summary']['critical_issues'][0]['kind'], 'unresolved')

    def test_unaudited_na_cannot_raise_coverage_and_low_confidence_is_not_counted(self):
        manifest = self.make_manifest()
        answers = {q['prompt']: self.good_answer(q, status='not_applicable') for q in manifest['questions']}
        result = qs.normalize(manifest, answers)
        self.assertGreater(result['summary']['dimensions']['financial']['applicable'], 0)
        self.assertEqual(result['summary']['quality_coverage'], 0)
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertEqual(result['summary']['dimensions']['financial']['applicable'], 0)
        self.assertIsNone(result['summary']['quality_score'])
        answers = {q['prompt']: self.good_answer(q, confidence='low') for q in manifest['questions']}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertEqual(result['summary']['quality_coverage'], 0)

    def test_future_evidence_wrong_id_missing_sources_and_boolean_score_fail(self):
        q = self.make_manifest()['questions'][0]
        for mutation in ('date', 'id', 'evidence', 'bool', 'reason'):
            raw = self.good_answer(q)
            inner = json.loads(raw['description'])
            if mutation == 'date':
                inner['evidence'][0]['published_at'] = '2026-09-20'
            elif mutation == 'id':
                inner['id'] = 'WRONG_ID'
            elif mutation == 'evidence':
                inner['evidence'] = []
            elif mutation == 'bool':
                raw['score'] = inner['score'] = True
            else:
                inner['rationale'] = ''
            raw['description'] = json.dumps(inner)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                qs.parse_answer(q, raw, self.profile['as_of'])

    def test_review_from_another_company_or_period_is_rejected(self):
        manifest = self.make_manifest()
        for patch in ({'company': 'another'}, {'as_of': '2025-09-19'}, {'accepted_ids': ['WRONG']}):
            with self.assertRaises(ValueError):
                qs.normalize(manifest, {}, {**self.review(manifest), **patch})

    def test_coverage_cannot_hide_an_entire_missing_quality_dimension(self):
        manifest = self.make_manifest('full')
        answers = {q['prompt']: self.good_answer(q) for q in manifest['questions'] if q['dimension'] != 'governance'}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertIsNone(result['summary']['quality_score'])
        self.assertIsNone(result['summary']['dimensions']['governance']['score'])

    def test_actual_stockqa_loader_parser_and_score_path_offline(self):
        repo = Path(os.environ.get('STOCKQA_REPO', str(ROOT.parent / 'StockQAbyLLM')))
        if not (repo / 'src/config/json_config_manager.py').exists():
            self.skipTest('StockQAbyLLM not present; set STOCKQA_REPO for real contract checks')
        old_cwd = Path.cwd()
        sys.path.insert(0, str(repo))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)  # upstream logger writes here, never into the external repository
                loader = importlib.import_module('src.config.json_config_manager').JSONConfigManager
                parser = importlib.import_module('src.providers.llm_response_parser').LLMResponseParser
                models = importlib.import_module('src.core.models')
                generator = importlib.import_module('src.services.answer_generator').AnswerGenerator
                questions = loader(str(ROOT / 'main_questions.json')).load_questions()
                self.assertEqual(len(questions), len(self.modules['common']['questions']))
                q = self.make_manifest()['questions'][0]
                raw = self.good_answer(q, score=8)
                score, description = parser().parse_response(json.dumps(raw))
                self.assertEqual(score, 8)
                self.assertEqual(json.loads(description)['score'], 8)
                # Capture observed upstream behavior without changing its implementation.
                answer = generator().generate_answer(models.Question('offline test'), [
                    models.SearchResult(title='test', snippet=description, score=8)])
                self.assertIn(answer.score, (5, 8))
                print(f'\nUpstream offline check: provider score=8, AnswerGenerator score={answer.score}')
                if answer.score == 5:
                    with self.assertRaises(ValueError):
                        qs.parse_answer(q, {'score': answer.score, 'description': answer.text}, self.profile['as_of'])
                # Close external file loggers before deleting the Windows temp directory.
                import logging
                for logger in logging.Logger.manager.loggerDict.values():
                    if isinstance(logger, logging.Logger):
                        for handler in list(logger.handlers):
                            if isinstance(handler, logging.FileHandler) and str(tmp) in handler.baseFilename:
                                handler.close()
                                logger.removeHandler(handler)
                os.chdir(old_cwd)
        finally:
            os.chdir(old_cwd)
            sys.path.remove(str(repo))

    def recovery_manifest(self, **changes):
        return self.make_manifest(profile={**self.profile, 'recovery_review': True,
            'recovery_rationale': 'OFFLINE: temporary operating weakness, not a real company', **changes})

    def recovery_result(self, scores=None, manifest=None, reviewed=True):
        manifest = manifest or self.recovery_manifest()
        scores = scores or {}
        answers = {q['prompt']: self.good_answer(q, scores.get(q['id'], 8))
                   for q in manifest['questions']}
        return qs.normalize(manifest, answers, self.review(manifest) if reviewed else None)

    def test_recovery_routes_without_misclassifying_mature_cyclical_company(self):
        ordinary = self.make_manifest()
        self.assertNotIn('recovery', ordinary['modules'])
        for patch in ({'stage': 'turnaround'}, {'stage': 'declining'},
                      {'overlays': ['distressed']}, {'recovery_review': True,
                       'recovery_rationale': 'cyclical trough with retained advantages'}):
            with self.subTest(patch=patch):
                manifest = self.make_manifest(profile={**self.profile, **patch})
                self.assertIn('recovery', manifest['modules'])
                self.assertEqual(sum(q['module_id'] == 'recovery' for q in manifest['questions']), 4)
        manifest = self.recovery_manifest(diagnostic_modules=['recovery'],
                                          diagnostic_rationale={'recovery': 'assess recovery'})
        self.assertEqual(manifest['profile']['stage'], 'mature')
        self.assertEqual(manifest['modules'].count('recovery'), 1)
        self.assertEqual(len(manifest['questions']), len({q['id'] for q in manifest['questions']}))

    def test_low_current_scores_can_have_recovery_potential_without_score_uplift(self):
        manifest = self.recovery_manifest()
        scores = {q['id']: 4 for q in manifest['questions']}
        scores.update({q: 8 for q in ('IQS_05', 'IQS_12', 'IQS_13', 'IQS_16',
                                     'CYCLICAL_02', 'RECOVERY_01', 'RECOVERY_02', 'RECOVERY_04')})
        scores['RECOVERY_03'] = 3
        result = self.recovery_result(scores, manifest)
        watch = result['recovery_watch']
        self.assertEqual(watch['status'], 'potential_watch')
        self.assertIn('catalyst_unproven', watch['flags'])
        self.assertTrue(any(q['id'] == 'IQS_05' for q in watch['strengths']))
        self.assertIn(manifest['replacements'].get('IQS_11', 'IQS_11'), watch['weak_current_ids'])
        without_diagnostics = [r for r in result['questions'] if r['module_id'] != 'recovery']
        self.assertEqual(result['summary']['quality_score'], qs.summarize(without_diagnostics)['quality_score'])
        self.assertLess(result['summary']['quality_score'], 6)
        self.assertFalse(watch['quality_gate_overridden'])
        scores['RECOVERY_03'] = 7
        repaired = self.recovery_result(scores, manifest)
        self.assertEqual(repaired['recovery_watch']['status'], 'recovery_evidence_watch')
        self.assertEqual(repaired['summary']['quality_score'], result['summary']['quality_score'])

    def test_recovery_cannot_conceal_survival_governance_or_equity_risks(self):
        for weak in ('IQS_12', 'IQS_13', 'IQS_16', 'CYCLICAL_02', 'RECOVERY_04'):
            with self.subTest(weak=weak):
                result = self.recovery_result({weak: 2})
                self.assertEqual(result['recovery_watch']['status'], 'high_risk_watch')
                self.assertFalse(result['recovery_watch']['quality_gate_overridden'])
                if weak in ('IQS_12', 'IQS_13', 'IQS_16'):
                    self.assertIsNone(result['summary']['quality_score'])
        for weak in ('RECOVERY_01', 'RECOVERY_02'):
            self.assertEqual(self.recovery_result({weak: 2})['recovery_watch']['status'],
                             'structural_risk_watch')

    def test_recovery_uses_effective_type_specific_survival_question(self):
        manifest = self.recovery_manifest(company_type='bank', industry_modules=[], cycle_sensitive=False)
        survival = manifest['replacements']['IQS_16']
        result = self.recovery_result({survival: 2}, manifest)
        self.assertEqual(result['recovery_watch']['status'], 'high_risk_watch')
        self.assertIn(survival, result['recovery_watch']['criteria'])
        self.assertNotIn('IQS_16', result['recovery_watch']['criteria'])

    def test_unreviewed_missing_and_low_confidence_cannot_become_recovery_candidates(self):
        manifest = self.recovery_manifest()
        result = self.recovery_result(manifest=manifest, reviewed=False)
        self.assertEqual(result['recovery_watch']['status'], 'needs_verification')
        self.assertEqual(result['recovery_watch']['strengths'], [])
        for state in ('missing', 'not_applicable', 'insufficient_evidence', 'low_confidence'):
            answers = {q['prompt']: self.good_answer(q, 8) for q in manifest['questions']}
            q = next(q for q in manifest['questions'] if q['id'] == 'RECOVERY_01')
            if state == 'missing':
                del answers[q['prompt']]
            elif state == 'low_confidence':
                answers[q['prompt']] = self.good_answer(q, 8, confidence='low')
            else:
                answers[q['prompt']] = self.good_answer(q, status=state)
            result = qs.normalize(manifest, answers, self.review(manifest))
            self.assertEqual(result['recovery_watch']['status'], 'needs_verification')
            self.assertIn('RECOVERY_01', result['recovery_watch']['missing_or_unusable_ids'])

    def test_mixed_profile_suggests_review_without_claiming_a_turnaround(self):
        manifest = self.make_manifest()
        cash_question = manifest['replacements'].get('IQS_11', 'IQS_11')
        result = self.recovery_result({cash_question: 3, 'IQS_05': 9}, manifest)
        self.assertEqual(result['recovery_watch']['status'], 'review_suggested')
        self.assertEqual(result['recovery_watch']['flags'], ['mixed_strength_and_weakness'])
        self.assertEqual(result['recovery_watch']['criteria'], {})
        ordinary = self.recovery_result(manifest=manifest)
        self.assertEqual(ordinary['recovery_watch']['status'], 'not_assessed')


if __name__ == '__main__':
    unittest.main()
