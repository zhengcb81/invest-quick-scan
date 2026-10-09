"""Behavior checks for routing, evidence handling and the real upstream file contract."""
import copy
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import question_sets as qs


def _stockqa_bytecode_snapshot(repo):
    roots = (repo / '__pycache__', repo / 'src')
    snapshot = {}
    for root in roots:
        if root.is_dir():
            for path in root.rglob('*.pyc'):
                if path.is_file():
                    snapshot[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _cleanup_stockqa_import_state(*, tmp, temp_context, old_cwd, old_argv, old_sys_path,
                                  preexisting_src_modules, preexisting_main,
                                  old_dont_write_bytecode, old_bytecode_env):
    import logging

    temp_root = Path(tmp).resolve()
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in list(logger.handlers):
                if isinstance(handler, logging.FileHandler):
                    try:
                        if Path(handler.baseFilename).resolve().is_relative_to(temp_root):
                            handler.close()
                            logger.removeHandler(handler)
                    except (OSError, RuntimeError):
                        handler.close()
                        logger.removeHandler(handler)
    for name in [name for name in sys.modules
                 if (name == 'src' or name.startswith('src.'))
                 and name not in preexisting_src_modules]:
        sys.modules.pop(name, None)
    if preexisting_main is None:
        sys.modules.pop('main_with_llm', None)
    else:
        sys.modules['main_with_llm'] = preexisting_main
    os.chdir(old_cwd)
    sys.argv[:] = old_argv
    sys.path[:] = old_sys_path
    sys.dont_write_bytecode = old_dont_write_bytecode
    if old_bytecode_env is None:
        os.environ.pop('PYTHONDONTWRITEBYTECODE', None)
    else:
        os.environ['PYTHONDONTWRITEBYTECODE'] = old_bytecode_env
    temp_context.cleanup()


class QuestionSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.modules = qs.load_library()
        cls.profile = qs.read_json(ROOT / 'examples/profile.json')

    def make_manifest(self, mode='quick', profile=None):
        profile = copy.deepcopy(profile or self.profile)
        questions, modules, replacements = qs.select_questions(profile, mode, self.modules)
        return {'template_version': self.catalog['version'], 'profile': profile, 'mode': mode,
                'modules': modules, 'replacements': replacements,
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

    def make_screening_manifest(self, profile=None):
        profile = {**copy.deepcopy(profile or self.profile), 'entity_id': 'ENTITY_FIXTURE'}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'scan'
            qs.compose(profile, 'quick', output, answer_format='screening-1')
            manifest = qs.read_json(output / 'manifest.json')
            questions = qs.read_json(output / 'questions.json')
        return manifest, questions

    def make_screening_bundle(self, manifest, scores=None, confidences=None, statuses=None):
        scores, confidences, statuses = scores or {}, confidences or {}, statuses or {}
        as_of = manifest['profile']['as_of']
        observed_at = '2026-09-24T12:01:00Z'
        prior_year = str(int(as_of[:4]) - 1)
        answers, receipts = {}, {}
        for question in manifest['questions']:
            qid = question['id']
            status = statuses.get(qid, 'scored')
            score = None if status != 'scored' else scores.get(qid, 8)
            url = f'https://example.com/source/{qid.lower()}'
            prompt_sha256 = hashlib.sha256(question['prompt'].encode('utf-8')).hexdigest()
            search_call = {'id': f'search-{qid}', 'status': 'completed', 'action_type': 'search',
                           'source_urls': [url]}
            attempt = {
                'request_id': f'req-{qid}', 'response_id': f'resp-{qid}',
                'attempt_id': f'attempt-{qid}', 'actual_model': 'fixture-model',
                'prompt_sha256': prompt_sha256, 'search_status': 'executed',
                'response_status': 'completed', 'search_receipt_id': f'search-{qid}',
                'http_status_code': 200,
                'source_urls': [url], 'web_search_calls': [search_call],
            }
            content = {
                'id': qid, 'status': status, 'score': score,
                'confidence': confidences.get(qid, 'high'),
                'rationale': 'offline screening fixture', 'information_as_of': as_of,
                'period_start': f'{prior_year}-01-01', 'period_end': f'{prior_year}-12-31', 'basis': 'current',
                'evidence': [{'claim': 'fixture supports the stated claim', 'title': 'Fixture source',
                             'url': url, 'published_at': f'{prior_year}-08-01', 'period': f'FY{prior_year}'}],
                'counterevidence': 'fixture contrary evidence', 'sensitivity': 'fixture downside',
                'metrics': {},
            }
            answers[qid] = {
                'question_id': qid, 'status': status, 'score': score,
                'description': json.dumps(content, ensure_ascii=False),
                'source_urls': [url], 'published_date': None, 'information_as_of': None,
                'check_level': 'unverified_model_output', 'check_level_receipt_id': None,
            }
            receipts[qid] = {
                'provider': 'openai', 'request_id': f'req-{qid}', 'response_id': f'resp-{qid}',
                'attempt_id': f'attempt-{qid}', 'actual_model': 'fixture-model',
                'prompt_sha256': prompt_sha256,
                'input_question_sha256': prompt_sha256,
                'answered_at': observed_at, 'response_status': 'completed', 'http_status_code': 200,
                'search_status': 'executed',
                'search_receipt_id': f'search-{qid}', 'source_urls': [url],
                'web_search_calls': [search_call], 'attempts': [attempt],
            }
        result = {
            'schema_version': 'stockqa.quick_scan_result/1.0.0',
            'entity': {'entity_id': manifest['profile']['entity_id'], 'name': manifest['profile']['company']},
            'observed_at': observed_at,
            'provider': {'name': 'openai', 'requested_model': 'fixture-model'},
            'answers': answers, 'execution_receipts': receipts,
        }
        return {
            'schema_version': 'invest-quick-scan.screening-import/1.0.0',
            'manifest_sha256': qs._stable_sha256(manifest),
            'input_question_sha256': {
                q['id']: hashlib.sha256(q['prompt'].encode('utf-8')).hexdigest()
                for q in manifest['questions']
            },
            'result': result,
        }

    def mark_screening_route(self, bundle, qid, *, provider, requested_model,
                             route_id, route_ordinal=1):
        """Add the executor's final-route identity to one offline receipt."""
        receipt = bundle['result']['execution_receipts'][qid]
        receipt.update(provider=provider, requested_model=requested_model,
                       actual_model=requested_model,
                       dispatch_outcome={'scope': 'provider_dispatch', 'state': 'completed',
                                         'wait_reason': None, 'resume_condition': None})
        trace = [{'provider_config_ref': f'config-{provider}', 'route_id': route_id,
                  'requested_model': requested_model, 'ordinal': route_ordinal,
                  'decision': 'accepted_answer'}]
        receipt['attempts'][-1].update(provider=provider, requested_model=requested_model,
                                       provider_config_ref=f'config-{provider}',
                                       route_id=route_id, route_ordinal=route_ordinal,
                                       actual_model=requested_model, route_trace=trace)
        return receipt

    def test_library_and_export_are_consistent(self):
        stats = qs.validate_library()
        exported = qs.read_json(ROOT / 'main_questions.json')
        count = sum(len(category['questions']) for category in exported)
        self.assertEqual(count, len(self.modules['common']['questions']))
        self.assertEqual(exported, qs.export_questions(sorted(
            self.modules['common']['questions'], key=lambda question: question['id'])))
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

    def test_s01_manifest_embeds_frozen_metric_and_action_layer(self):
        profile = {**self.profile, 'diagnostic_modules': ['dupont', 'porter'],
                   'diagnostic_rationale': {'dupont': 'explain returns', 'porter': 'explain profit pool'}}
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(profile, 'quick', tmp)
            manifest = qs.read_json(Path(tmp) / 'manifest.json')
        self.assertEqual(manifest['metric_contract_version'], '1.0.0')
        self.assertEqual(len(manifest['question_metric_mappings']), manifest['question_count'])
        by_id = {item['question_id']: item for item in manifest['question_metric_mappings']}
        self.assertEqual(by_id['IQS_22']['aggregation_role'], 'valuation_core')
        self.assertEqual(next(q for q in manifest['questions'] if q['id'] == 'IQS_22')['scope'], 'security')
        for question_id in ('DUPONT_01', 'PORTER_01'):
            self.assertEqual(by_id[question_id]['aggregation_role'], 'diagnostic_only')
            self.assertFalse(by_id[question_id]['critical_risk'])

    def test_s01_type_replacements_keep_construct_and_scope(self):
        bank = {**self.profile, 'company_type': 'bank', 'industry_modules': [],
                'cycle_sensitive': False, 'overlays': []}
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(bank, 'quick', tmp)
            manifest = qs.read_json(Path(tmp) / 'manifest.json')
        by_id = {item['question_id']: item for item in manifest['question_metric_mappings']}
        self.assertEqual(by_id['BANK_03']['replacement_for'], 'IQS_11')
        self.assertEqual(by_id['BANK_06']['replacement_for'], 'IQS_22')
        self.assertEqual(next(q for q in manifest['questions'] if q['id'] == 'BANK_06')['scope'], 'security')
        self.assertTrue(by_id['BANK_01']['critical_risk'])

    def test_sc10_all_company_types_and_lifecycle_stages_keep_fixed_metric_manifest(self):
        """SC-10: The full type×lifecycle routing grid retains one mapped row per core construct."""
        company_types = ('operating', 'bank', 'insurer', 'capital_markets',
                         'property_owner', 'property_developer', 'holding', 'pre_revenue')
        lifecycle_stages = ('commercialization', 'declining', 'mature',
                            'scaling', 'turnaround', 'validation')
        with tempfile.TemporaryDirectory() as tmp:
            for company_type in company_types:
                for stage in lifecycle_stages:
                    with self.subTest(company_type=company_type, stage=stage):
                        profile = {**self.profile, 'company_type': company_type, 'stage': stage,
                                   'industry_modules': ['other'] if company_type in ('operating', 'pre_revenue') else [],
                                   'cycle_sensitive': False, 'overlays': [],
                                   'diagnostic_modules': [], 'diagnostic_rationale': {},
                                   'recovery_review': False}
                        output = Path(tmp) / f'{company_type}-{stage}'
                        qs.compose(profile, 'quick', output)
                        manifest = qs.read_json(output / 'manifest.json')
                        core = [q for q in manifest['questions'] if q.get('comparison_role') == 'core']
                        self.assertEqual({q.get('construct_id') for q in core},
                                         {f'IQS_{index:02}' for index in range(1, 25)})
                        self.assertEqual(len(core), 24)
                        self.assertEqual(len({q['id'] for q in manifest['questions']}),
                                         manifest['question_count'])
                        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)),
                                         manifest['question_count'])
                        self.assertFalse(any(q['module_id'] in ('dupont', 'porter')
                                             for q in manifest['questions']))

            cyclical = {**self.profile, 'company_type': 'operating', 'industry_modules': ['other'],
                        'stage': 'mature', 'cycle_sensitive': True,
                        'cycle_position': 'OFFLINE FIXTURE: trough', 'overlays': [],
                        'diagnostic_modules': [], 'diagnostic_rationale': {},
                        'recovery_review': False}
            output = Path(tmp) / 'mature-cycle-sensitive'
            qs.compose(cyclical, 'quick', output)
            manifest = qs.read_json(output / 'manifest.json')
            self.assertEqual(manifest['profile']['stage'], 'mature')
            self.assertTrue(manifest['profile']['cycle_sensitive'])
            self.assertIn('mature', manifest['modules'])
            self.assertIn('cyclical', manifest['modules'])

    def test_s01_context_questions_cannot_change_core_construct_summary(self):
        core = [{'id': f'IQS_{index:02}', 'construct_id': f'IQS_{index:02}',
                 'comparison_role': 'core', 'dimension': 'business',
                 'aggregation': 'scored', 'status': 'scored', 'score': 5,
                 'critical': False} for index in range(1, 25)]
        context = [{'id': 'BANK_05', 'construct_id': None, 'comparison_role': 'context',
                    'dimension': 'moat', 'aggregation': 'scored', 'status': 'scored',
                    'score': 10, 'critical': False}]
        without = qs.summarize(core, 'core-constructs-v1')
        with_context = qs.summarize(core + context, 'core-constructs-v1')
        self.assertEqual(without, with_context)

    def test_matrix_07_quick_full_context_preserves_core_risk_and_recovery_output(self):
        """MATRIX-07: Actual quick/full manifests keep the fixed core score and recovery diagnostics separate."""
        profile = {**self.profile, 'recovery_review': True,
                   'recovery_rationale': 'OFFLINE FIXTURE: test temporary weakness with retained advantages'}
        results = {}
        manifests = {}
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('quick', 'full'):
                output = Path(tmp) / mode
                qs.compose(profile, mode, output)
                manifest = qs.read_json(output / 'manifest.json')
                manifests[mode] = manifest
                core = [q for q in manifest['questions'] if q.get('comparison_role') == 'core']
                self.assertEqual(len(core), 24)
                self.assertEqual({q.get('construct_id') for q in core},
                                 {f'IQS_{index:02}' for index in range(1, 25)})
                self.assertEqual(manifest['aggregation_policy'], 'core-constructs-v1')
                self.assertEqual(sum(q['module_id'] == 'recovery' for q in manifest['questions']), 4)

                answers = {
                    q['prompt']: self.good_answer(q, 5 if q.get('comparison_role') == 'core' else 10)
                    for q in manifest['questions']
                }
                results[mode] = qs.normalize(manifest, answers, self.review(manifest))

        self.assertNotEqual(manifests['quick']['question_count'], manifests['full']['question_count'])
        for mode, result in results.items():
            with self.subTest(mode=mode):
                self.assertEqual(result['summary']['quality_score'], 5)
                self.assertEqual(result['summary']['aggregation_policy'], 'core-constructs-v1')
                self.assertTrue(all(dimension['score'] == 5
                                    for dimension in result['summary']['dimensions'].values()))
                self.assertEqual(result['recovery_watch']['policy_version'], 'recovery-watch-1')
                self.assertEqual(result['recovery_watch']['status'], 'weak_case_watch')
                self.assertTrue(result['recovery_watch']['criteria'])
                self.assertFalse(result['recovery_watch']['quality_gate_overridden'])
        self.assertEqual(results['quick']['summary']['dimensions'],
                         results['full']['summary']['dimensions'])

        # A critical core failure remains visible even when every added context/diagnostic answer is 10.
        quick = manifests['quick']
        critical = next(q for q in quick['questions']
                        if q.get('comparison_role') == 'core' and q.get('critical'))
        risk_answers = {
            q['prompt']: self.good_answer(q, 3 if q['id'] == critical['id']
                                          else 5 if q.get('comparison_role') == 'core' else 10)
            for q in quick['questions']
        }
        risk_result = qs.normalize(quick, risk_answers, self.review(quick))
        self.assertIsNone(risk_result['summary']['quality_score'])
        self.assertIn({'id': critical['id'], 'kind': 'material_concern',
                       'status': 'scored', 'score': 3}, risk_result['summary']['critical_issues'])
        self.assertEqual(risk_result['recovery_watch']['critical_issues'],
                         risk_result['summary']['critical_issues'])
        self.assertIn('critical_material_concern', risk_result['recovery_watch']['flags'])

    def test_s01_metric_mapping_is_authoritative_and_metadata_cannot_drift(self):
        profile = {**self.profile, 'diagnostic_modules': ['dupont'],
                   'diagnostic_rationale': {'dupont': 'explain returns'}}
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(profile, 'quick', tmp)
            original = qs.read_json(Path(tmp) / 'manifest.json')
        attacks = []
        mapping_drift = copy.deepcopy(original)
        mapping_drift['question_metric_mappings'][0].update(
            dimension='fact', aggregation_role='diagnostic_only', critical_risk=False)
        attacks.append(mapping_drift)
        critical_drift = copy.deepcopy(original)
        next(q for q in critical_drift['questions'] if q['id'] == 'DUPONT_01')['critical'] = True
        attacks.append(critical_drift)
        scope_drift = copy.deepcopy(original)
        next(q for q in scope_drift['questions'] if q['id'] == 'IQS_22')['scope'] = 'entity'
        attacks.append(scope_drift)
        embedded_drift = copy.deepcopy(original)
        next(q for q in embedded_drift['questions'] if q['id'] == 'IQS_01')[
            'metric_contract']['aggregation_role'] = 'diagnostic_only'
        attacks.append(embedded_drift)
        for attack in attacks:
            with self.subTest(attack=attacks.index(attack)), self.assertRaises(ValueError):
                qs.normalize(attack, {}, self.review(attack))

    def test_s01_legacy_manifest_remains_readable_without_new_mapping(self):
        legacy = self.make_manifest()
        legacy.pop('template_version')
        self.assertNotIn('metric_contract_version', legacy)
        original = copy.deepcopy(legacy)
        answers = {q['prompt']: self.good_answer(q, 5) for q in legacy['questions']}
        result = qs.normalize(legacy, answers, self.review(legacy))
        self.assertEqual(result['template_version'], 'unknown')
        self.assertEqual(result['summary']['aggregation_policy'], 'legacy-all-questions')
        self.assertEqual(legacy, original, 'reading legacy data must not rewrite its input manifest')

    def test_s01_legacy_recovery_watch_flags_unverified_replacement_mapping(self):
        bank = {**self.profile, 'company_type': 'bank', 'industry_modules': [],
                'cycle_sensitive': False, 'overlays': []}
        legacy = self.make_manifest(profile=bank)
        self.assertNotIn('metric_contract_version', legacy)
        self.assertTrue(legacy['replacements'])
        original_answers = {q['prompt']: self.good_answer(q, 5) for q in legacy['questions']}
        baseline = qs.normalize(legacy, original_answers, self.review(legacy))

        base_id, actual_id = next(iter(legacy['replacements'].items()))
        wrong = copy.deepcopy(legacy)
        unrelated_id = next(q['id'] for q in wrong['questions']
                            if q['id'] not in {base_id, actual_id})
        wrong['replacements'][base_id] = unrelated_id
        coordinated_rewrite = copy.deepcopy(legacy)
        source_question = next(q for q in coordinated_rewrite['questions'] if q['id'] == actual_id)
        target_question = next(q for q in coordinated_rewrite['questions']
                               if q['id'] not in coordinated_rewrite['replacements'].values()
                               and not q.get('replaces'))
        source_question['replaces'].remove(base_id)
        target_question.setdefault('replaces', []).append(base_id)
        coordinated_rewrite['replacements'][base_id] = target_question['id']
        missing_question_metadata = copy.deepcopy(legacy)
        mapped_question = next(q for q in missing_question_metadata['questions']
                               if q['id'] == actual_id)
        mapped_question.pop('replaces')

        unknown_catalog = copy.deepcopy(legacy)
        unknown_catalog['template_version'] = 'retired-catalog'
        for attack in (wrong, coordinated_rewrite, missing_question_metadata, unknown_catalog):
            with self.subTest(attack=attack):
                answers = {q['prompt']: self.good_answer(q, 5) for q in attack['questions']}
                result = qs.normalize(attack, answers, self.review(attack))
                self.assertEqual(result['summary'], baseline['summary'])
                self.assertEqual(result['recovery_watch']['status'], 'needs_verification')
                self.assertIn('replacement_mapping_unverified', result['recovery_watch']['flags'])

    def test_s01_replacement_and_module_routing_cannot_drift(self):
        bank = {**self.profile, 'company_type': 'bank', 'industry_modules': [],
                'cycle_sensitive': False, 'overlays': []}
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(bank, 'quick', tmp)
            original = qs.read_json(Path(tmp) / 'manifest.json')
        wrong_replacement = copy.deepcopy(original)
        wrong_replacement['replacements']['IQS_16'] = 'IQS_01'
        wrong_module = copy.deepcopy(original)
        next(q for q in wrong_module['questions'] if q['id'] == 'BANK_01')['module_id'] = 'common'
        for attack in (wrong_replacement, wrong_module):
            with self.assertRaises(ValueError):
                qs.normalize(attack, {}, self.review(attack))

    def test_s01_selected_question_and_mapping_sets_are_closed(self):
        bank = {**self.profile, 'company_type': 'bank', 'industry_modules': [],
                'cycle_sensitive': False, 'overlays': [], 'diagnostic_modules': ['dupont'],
                'diagnostic_rationale': {'dupont': 'explain returns'}}
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(bank, 'full', tmp)
            original = qs.read_json(Path(tmp) / 'manifest.json')
        duplicate = copy.deepcopy(original)
        source = next(q for q in duplicate['questions'] if q['id'] == 'BANK_05')
        target_index = next(index for index, q in enumerate(duplicate['questions']) if q['id'] == 'MATURE_01')
        duplicate['questions'][target_index] = copy.deepcopy(source)
        deleted = copy.deepcopy(original)
        deleted['questions'] = [q for q in deleted['questions'] if q['id'] != 'DUPONT_01']
        deleted['question_metric_mappings'] = [m for m in deleted['question_metric_mappings']
                                               if m['question_id'] != 'DUPONT_01']
        deleted['question_count'] -= 1
        unused_mapping = copy.deepcopy(original)
        unused_mapping['question_metric_mappings'].append(
            copy.deepcopy(unused_mapping['question_metric_mappings'][0]))
        for attack in (duplicate, deleted, unused_mapping):
            with self.assertRaises(ValueError):
                qs.normalize(attack, {}, self.review(attack))

    def test_s03_advantage_prompts_include_scope_conditions_and_falsifiers(self):
        manifest = self.make_manifest('quick')
        selected = {question['id']: question for question in manifest['questions']}
        expected_constructs = {'IQS_05': 'IQS_05', 'IQS_18': 'IQS_18'}
        required_phrases = {
            'IQS_05': ('明确业务与时间范围', '成立所依赖的条件', '推翻优势判断的反证'),
            'IQS_18': ('一至两项实质变化', '当前利润/资产敞口', '观察期限'),
        }
        for question_id, construct_id in expected_constructs.items():
            with self.subTest(question_id=question_id):
                question = selected[question_id]
                self.assertEqual(question['construct_id'], construct_id)
                self.assertEqual(question['rubric_version'], '2.0.0')
                prompt = question['prompt']
                for phrase in required_phrases[question_id]:
                    self.assertIn(phrase, prompt)
                mapping = qs.metric_mapping(question)
                self.assertTrue(mapping['evidence_demands']['require_durability_conditions'])
                self.assertTrue(mapping['evidence_demands']['counter_evidence_required'])

    def test_s03_growth_prompts_require_net_effect_after_legacy_loss_and_financing(self):
        manifest = self.make_manifest('quick')
        selected = {question['id']: question for question in manifest['questions']}
        for question_id in ('IQS_20', 'IQS_21'):
            with self.subTest(question_id=question_id):
                question = selected[question_id]
                self.assertEqual(question['construct_id'], question_id)
                self.assertEqual(question['rubric_version'], '2.0.0')
                mapping = qs.metric_mapping(question)
                self.assertTrue(mapping['evidence_demands']['require_net_economic_effect'])
                self.assertIn('存量业务', question['prompt'])
                self.assertIn('摊薄', question['prompt'])
                self.assertIn('净', question['prompt'])

    def test_s03_pre_revenue_replacement_keeps_growth_construct_and_net_economics(self):
        profile = {**self.profile, 'company_type': 'pre_revenue',
                   'industry_modules': ['healthcare'], 'stage': 'commercialization'}
        manifest = self.make_manifest('quick', profile)
        question = next(question for question in manifest['questions']
                        if question['id'] == 'PRE_REVENUE_04')
        mapping = qs.metric_mapping(question)
        self.assertEqual(question['construct_id'], 'IQS_20')
        self.assertEqual(question['rubric_version'], '2.0.0')
        self.assertEqual(mapping['replacement_for'], 'IQS_20')
        self.assertEqual(mapping['aggregation_role'], 'growth_core')
        self.assertTrue(mapping['evidence_demands']['require_net_economic_effect'])
        self.assertIn('付费客户', question['prompt'])
        self.assertIn('融资摊薄', question['prompt'])

    def test_s03_does_not_add_unapproved_bridge_questions_or_auto_diagnostics(self):
        diagnostic_modules = {key for key, module in self.modules.items()
                              if module['kind'] == 'diagnostics'}
        self.assertEqual(diagnostic_modules, {'dupont', 'porter', 'recovery'})
        for mode in ('quick', 'full'):
            manifest = self.make_manifest(mode)
            self.assertFalse(any(question.get('framework') for question in manifest['questions']))
            self.assertEqual(sum(question['comparison_role'] == 'core'
                                 for question in manifest['questions']), 24)

    def test_s03_current_manifest_rejects_an_unsupported_older_template_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            qs.compose(self.profile, 'quick', tmp)
            previous = qs.read_json(Path(tmp) / 'manifest.json')
        previous['template_version'] = '3.1.0'
        with self.assertRaisesRegex(ValueError, 'must match the loaded question catalog version'):
            qs.normalize(previous, {}, self.review(previous))

    def test_s03_archived_metric_manifest_reads_from_immutable_package_without_live_sources(self):
        package_id = qs.read_json(ROOT / 'questions/releases/current.json')['package_id']
        with tempfile.TemporaryDirectory(prefix='iqs-s03-archive-') as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'questions/releases', root / 'questions/releases')
            baseline_path = root / 'schemas/quick_scan/module-legacy-baseline.json'
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / 'schemas/quick_scan/module-legacy-baseline.json', baseline_path)
            output = root / 'output'
            with mock.patch.object(qs, 'ROOT', root):
                qs.compose(self.profile, 'quick', output, package_id=package_id)
                manifest = qs.read_json(output / 'manifest.json')
                self.assertFalse((root / 'questions/catalog.json').exists())
                self.assertFalse((root / 'questions/common.json').exists())
                answers = {q['prompt']: self.good_answer(q, 7) for q in manifest['questions']}
                result = qs.normalize(manifest, answers, self.review(manifest))
                self.assertEqual(result['summary']['quality_score'], 7)
                self.assertEqual(result['questions'][0]['score'], 7)

                # An archived answer remains attached to the exact released
                # question definition. A changed prompt or rubric cannot
                # reinterpret that saved score under the same question ID.
                for field, value in (('prompt', manifest['questions'][0]['prompt'] + ' 改写'),
                                     ('rubric_version', '99.0.0')):
                    with self.subTest(field=field):
                        altered = copy.deepcopy(manifest)
                        altered['questions'][0][field] = value
                        with self.assertRaisesRegex(
                                ValueError,
                                'manifest question (definition differs from archive|'
                                'prompt or semantic fingerprint mismatch)'):
                            qs.normalize(altered, answers, self.review(altered))

                wrong_catalog_version = copy.deepcopy(manifest)
                wrong_catalog_version['template_version'] = '3.1.0'
                with self.assertRaisesRegex(ValueError, 'must match the loaded question catalog version'):
                    qs.normalize(wrong_catalog_version, answers, self.review(wrong_catalog_version))

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

    def test_screening_protocol_is_explicit_and_never_uses_legacy_review_ids(self):
        manifest, exported = self.make_screening_manifest()
        self.assertEqual(manifest['answer_format'], 'screening-1')
        self.assertEqual(manifest['screening_protocol_version'], '1.0.0')
        self.assertTrue(all(isinstance(q, dict) and q['question_id']
                            for group in exported for q in group['questions']))
        self.assertIn('screening-1协议', exported[0]['questions'][0]['text'])
        bundle = self.make_screening_bundle(manifest)
        with self.assertRaisesRegex(ValueError, 'never legacy accepted_ids'):
            qs.normalize(manifest, bundle, {'accepted_ids': [q['id'] for q in manifest['questions']]})
        result = qs.normalize(manifest, bundle)
        first = result['questions'][0]
        self.assertEqual(first['reported_score'], 8)
        self.assertEqual(first['score'], 8)
        self.assertEqual(first['screening_status'], 'screening_checked')
        self.assertEqual(first['check_level'], 'screening_audited')
        self.assertIn(first['check_level_receipt_id'], result['check_level_receipts'])
        self.assertEqual(result['formal_research_status'], 'not_accepted')
        with tempfile.TemporaryDirectory() as tmp:
            profile_without_identity = {key: value for key, value in self.profile.items()
                                        if key != 'entity_id'}
            with self.assertRaisesRegex(ValueError, 'verified stable profile entity_id'):
                qs.compose(profile_without_identity, 'quick', Path(tmp) / 'missing-identity',
                           answer_format='screening-1')

    def test_screening_import_rejects_identity_question_period_and_search_mismatches(self):
        manifest, _ = self.make_screening_manifest()
        base = self.make_screening_bundle(manifest)
        with self.subTest('entity'):
            bad = copy.deepcopy(base)
            bad['result']['entity']['entity_id'] = 'OTHER_ENTITY'
            with self.assertRaisesRegex(ValueError, 'entity does not match'):
                qs.normalize_screening(manifest, bad)
        mutations = {
            'question': lambda b, q: b['result']['answers'][q].update(question_id='IQS_WRONG'),
            'search': lambda b, q: b['result']['execution_receipts'][q].update(search_status='unverified'),
            'non-integer HTTP status': lambda b, q: b['result']['execution_receipts'][q].update(
                http_status_code=200.0),
            'sources': lambda b, q: b['result']['execution_receipts'][q].update(search_receipt_id=None),
            'unbound search receipt': lambda b, q: b['result']['execution_receipts'][q].update(
                search_receipt_id='unrelated-search-id'),
            'missing attempt chain': lambda b, q: b['result']['execution_receipts'][q].pop('attempts'),
            'mismatched final attempt': lambda b, q: b['result']['execution_receipts'][q]['attempts'][-1].update(
                attempt_id='different-attempt'),
            'mismatched final attempt HTTP status': lambda b, q: b['result']['execution_receipts'][q]['attempts'][-1].update(
                http_status_code=201),
            'wrong executed question hash': lambda b, q: b['result']['execution_receipts'][q].update(
                input_question_sha256='0' * 64),
        }
        # Use a truly after-cutoff historical period rather than a date string typo.
        future_year = str(int(manifest['profile']['as_of'][:4]) + 1)
        mutations['period'] = lambda b, q: b['result']['answers'][q].update(
            description=json.dumps({**json.loads(b['result']['answers'][q]['description']),
                                   'period_end': f'{future_year}-01-01'}, ensure_ascii=False))
        def evidence_outside_receipt_linked_search(bundle, question_id):
            outside_url = f'https://example.com/unsearched/{question_id.lower()}'
            answer = bundle['result']['answers'][question_id]
            content = json.loads(answer['description'])
            content['evidence'][0]['url'] = outside_url
            answer['description'] = json.dumps(content, ensure_ascii=False)
            answer['source_urls'].append(outside_url)
            bundle['result']['execution_receipts'][question_id]['source_urls'].append(outside_url)
        mutations['evidence outside receipt-linked search'] = evidence_outside_receipt_linked_search
        qid = manifest['questions'][0]['id']
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                bad = copy.deepcopy(base)
                mutate(bad, qid)
                imported = qs.normalize_screening(manifest, bad)
                row = next(row for row in imported['questions'] if row['id'] == qid)
                self.assertEqual(row['reported_score'], 8)
                self.assertIsNone(row['score'])
                self.assertEqual(row['screening_status'], 'unusable')
                self.assertEqual(row['check_level'], 'unverified_model_output')

    def test_screening_accepts_minimax_completed_search_without_http_request_id(self):
        manifest, _ = self.make_screening_manifest()
        bundle = self.make_screening_bundle(manifest)
        qid = manifest['questions'][0]['id']
        bundle['result']['provider'] = {'name': 'minimax', 'requested_model': 'MiniMax-M3'}
        for question in manifest['questions']:
            receipt = bundle['result']['execution_receipts'][question['id']]
            receipt.update(provider='minimax', requested_model='MiniMax-M3', actual_model='MiniMax-M3')
            receipt['dispatch_outcome'] = None
            receipt['attempts'][-1].update(provider='minimax', provider_config_ref='minimax',
                                           actual_model='MiniMax-M3')
        receipt = bundle['result']['execution_receipts'][qid]
        receipt['request_id'] = None
        receipt['attempts'][-1]['request_id'] = None
        imported = qs.normalize_screening(manifest, bundle)
        row = next(row for row in imported['questions'] if row['id'] == qid)
        self.assertEqual((row['screening_status'], row['score']), ('screening_checked', 8))
        self.assertIn(row['check_level_receipt_id'], imported['check_level_receipts'])
        self.assertIsNone(row['execution']['request_id'])

    def test_screening_accepts_mixed_actual_providers_with_null_batch_provider(self):
        manifest, _ = self.make_screening_manifest()
        bundle = self.make_screening_bundle(manifest)
        q0, q1 = [q['id'] for q in manifest['questions'][:2]]
        bundle['result']['provider'] = {'name': None, 'requested_model': None}
        for question in manifest['questions']:
            self.mark_screening_route(bundle, question['id'], provider='openai',
                                      requested_model='fixture-model', route_id='route-openai')
        receipt = self.mark_screening_route(bundle, q1, provider='minimax',
                                            requested_model='MiniMax-M3', route_id='route-minimax')
        receipt['request_id'] = None
        receipt['attempts'][-1]['request_id'] = None
        imported = qs.normalize_screening(manifest, bundle)
        rows = {row['id']: row for row in imported['questions']}
        self.assertEqual(imported['provenance_status'], 'screening_checked')
        self.assertEqual((rows[q0]['screening_status'], rows[q0]['score']), ('screening_checked', 8))
        self.assertEqual((rows[q1]['screening_status'], rows[q1]['score']), ('screening_checked', 8))
        self.assertEqual(rows[q0]['execution']['provider'], 'openai')
        self.assertEqual(rows[q1]['execution']['provider'], 'minimax')

    def test_screening_new_route_receipts_reject_forged_evidence_or_execution(self):
        manifest, _ = self.make_screening_manifest()
        qid = manifest['questions'][0]['id']

        def mixed_bundle():
            bundle = self.make_screening_bundle(manifest)
            bundle['result']['provider'] = {'name': None, 'requested_model': None}
            for q in manifest['questions']:
                self.mark_screening_route(bundle, q['id'], provider='openai',
                                          requested_model='fixture-model', route_id='route-openai')
            return bundle

        def fake_evidence(bundle):
            content = json.loads(bundle['result']['answers'][qid]['description'])
            content['evidence'][0]['url'] = 'https://example.com/not-in-search'
            bundle['result']['answers'][qid]['description'] = json.dumps(content)

        mutations = {
            'forged evidence': fake_evidence,
            'missing final attempt': lambda b: b['result']['execution_receipts'][qid].update(attempts=[]),
            'wrong actual provider': lambda b: b['result']['execution_receipts'][qid]['attempts'][-1].update(
                provider='minimax'),
            'null OpenAI request ID': lambda b: (
                b['result']['execution_receipts'][qid].update(request_id=None),
                b['result']['execution_receipts'][qid]['attempts'][-1].update(request_id=None)),
            'null MiniMax request without final provider': lambda b: (
                b['result']['execution_receipts'][qid].update(provider='minimax', request_id=None),
                b['result']['execution_receipts'][qid]['attempts'][-1].update(provider=None, request_id=None)),
            'missing final route': lambda b: b['result']['execution_receipts'][qid]['attempts'][-1].pop(
                'route_id'),
            'wrong requested model': lambda b: b['result']['execution_receipts'][qid]['attempts'][-1].update(
                requested_model='another-model'),
            'unknown actual model': lambda b: b['result']['execution_receipts'][qid].update(actual_model=None),
            'noncompleted dispatch': lambda b: b['result']['execution_receipts'][qid].update(
                dispatch_outcome={'scope': 'provider_dispatch', 'state': 'uncertain',
                                  'wait_reason': 'provider_response_unknown',
                                  'resume_condition': 'reconcile_same_attempt_before_retry'}),
            'route trace contradicts completion': lambda b: b['result']['execution_receipts'][qid][
                'attempts'][-1]['route_trace'][-1].update(decision='provider_failure'),
            'unverified search': lambda b: b['result']['execution_receipts'][qid].update(
                search_status='unverified'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                bundle = mixed_bundle()
                mutate(bundle)
                imported = qs.normalize_screening(manifest, bundle)
                row = next(row for row in imported['questions'] if row['id'] == qid)
                self.assertEqual(row['screening_status'], 'unusable')
                self.assertIsNone(row['score'])
                self.assertEqual(row['check_level'], 'unverified_model_output')
                self.assertNotIn(row.get('check_level_receipt_id'), imported['check_level_receipts'])

    def test_screening_modern_single_provider_requires_complete_final_route(self):
        manifest, _ = self.make_screening_manifest()
        qid = manifest['questions'][0]['id']

        legacy = self.make_screening_bundle(manifest)
        direct_attempt = legacy['result']['execution_receipts'][qid]['attempts'][-1]
        direct_attempt.update(provider='openai', provider_config_ref='openai')
        legacy['result']['execution_receipts'][qid]['dispatch_outcome'] = None
        legacy_row = next(row for row in qs.normalize_screening(manifest, legacy)['questions']
                          if row['id'] == qid)
        self.assertEqual((legacy_row['screening_status'], legacy_row['score']), ('screening_checked', 8))

        def modern_bundle():
            bundle = self.make_screening_bundle(manifest)
            for q in manifest['questions']:
                self.mark_screening_route(bundle, q['id'], provider='openai',
                                          requested_model='fixture-model', route_id='route-openai')
            return bundle

        def strip_final_route_after_prior_route(bundle):
            receipt = bundle['result']['execution_receipts'][qid]
            receipt['attempts'].insert(0, copy.deepcopy(receipt['attempts'][-1]))
            for key in ('route_id', 'route_ordinal', 'route_trace'):
                receipt['attempts'][-1].pop(key)
            receipt['dispatch_outcome'] = None

        mutations = {
            'missing completed dispatch': lambda b: b['result']['execution_receipts'][qid].update(
                dispatch_outcome=None),
            'missing final actual provider': lambda b: b['result']['execution_receipts'][qid][
                'attempts'][-1].pop('provider'),
            'missing final requested model': lambda b: b['result']['execution_receipts'][qid][
                'attempts'][-1].pop('requested_model'),
            'prior route cannot be disguised as direct call': strip_final_route_after_prior_route,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                bundle = modern_bundle()
                mutate(bundle)
                imported = qs.normalize_screening(manifest, bundle)
                row = next(row for row in imported['questions'] if row['id'] == qid)
                self.assertEqual(row['screening_status'], 'unusable')
                self.assertIsNone(row['score'])
                self.assertNotIn(row.get('check_level_receipt_id'), imported['check_level_receipts'])

    def test_screening_ignores_model_self_approval_and_legacy_strict_stays_pending(self):
        manifest, _ = self.make_screening_manifest()
        bundle = self.make_screening_bundle(manifest)
        qid = manifest['questions'][0]['id']
        answer = bundle['result']['answers'][qid]
        answer['accepted_ids'] = [qid]
        answer['check_level'] = 'formal_research_accepted'
        answer['check_level_receipt_id'] = 'RCP_MODEL_FORGED'
        imported = qs.normalize_screening(manifest, bundle)
        row = next(row for row in imported['questions'] if row['id'] == qid)
        self.assertEqual(row['reported_score'], 8)
        self.assertIsNone(row['score'])
        self.assertEqual(row['check_level'], 'unverified_model_output')
        self.assertEqual(row['formal_research_status'], 'not_accepted')
        self.assertEqual(row['screening_status'], 'unusable')

        bundle = self.make_screening_bundle(manifest)
        answer = bundle['result']['answers'][qid]
        content = json.loads(answer['description'])
        content['accepted_ids'] = [qid]
        answer['description'] = json.dumps(content, ensure_ascii=False)
        imported = qs.normalize_screening(manifest, bundle)
        row = next(row for row in imported['questions'] if row['id'] == qid)
        self.assertEqual(row['reported_score'], 8)
        self.assertIsNone(row['score'])
        self.assertEqual(row['formal_research_status'], 'not_accepted')
        self.assertEqual(row['screening_status'], 'unusable')

        legacy = self.make_manifest()
        answers = {q['prompt']: self.good_answer(q, score=8) for q in legacy['questions']}
        old = qs.normalize(legacy, answers)
        self.assertTrue(all(row['status'] == 'review_pending' for row in old['questions']))
        self.assertFalse(any('accepted_ids' in row for row in old['questions']))

    def test_screening_low_confidence_and_na_remain_out_of_valid_coverage(self):
        manifest, _ = self.make_screening_manifest()
        q0, q1 = manifest['questions'][:2]
        bundle = self.make_screening_bundle(
            manifest, confidences={q0['id']: 'low'}, statuses={q1['id']: 'not_applicable'})
        imported = qs.normalize_screening(manifest, bundle)
        rows = {row['id']: row for row in imported['questions']}
        self.assertEqual(rows[q0['id']]['status'], 'low_confidence')
        self.assertIsNone(rows[q0['id']]['score'])
        self.assertEqual(rows[q1['id']]['reported_status'], 'not_applicable')
        self.assertEqual(rows[q1['id']]['status'], 'unknown')
        self.assertFalse(rows[q1['id']]['is_audited_na'])
        self.assertLess(imported['summary']['all_question_coverage'], 1)

    def test_screening_recovery_watch_preserves_low_current_quality_and_strong_assets(self):
        profile = {**self.profile, 'recovery_review': True,
                   'recovery_rationale': 'fixture: cyclical downturn with retained assets'}
        manifest, _ = self.make_screening_manifest(profile)
        scores = {q['id']: 4 for q in manifest['questions']}
        scores.update({qid: 8 for qid in ('IQS_05', 'IQS_12', 'IQS_13', 'IQS_16',
                                          'CYCLICAL_02', 'RECOVERY_01', 'RECOVERY_02', 'RECOVERY_04')})
        scores['RECOVERY_03'] = 3
        imported = qs.normalize_screening(manifest, self.make_screening_bundle(manifest, scores=scores))
        self.assertEqual(imported['recovery_watch']['status'], 'potential_watch')
        self.assertIn('catalyst_unproven', imported['recovery_watch']['flags'])
        self.assertLess(imported['summary']['quality_score'], 6)
        self.assertFalse(imported['recovery_watch']['quality_gate_overridden'])
        self.assertEqual(imported['formal_research_status'], 'not_accepted')

    def test_coverage_cannot_hide_an_entire_missing_quality_dimension(self):
        manifest = self.make_manifest('full')
        answers = {q['prompt']: self.good_answer(q) for q in manifest['questions'] if q['dimension'] != 'governance'}
        result = qs.normalize(manifest, answers, self.review(manifest))
        self.assertIsNone(result['summary']['quality_score'])
        self.assertIsNone(result['summary']['dimensions']['governance']['score'])

    def test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline(self):
        repo = Path(os.environ.get('STOCKQA_REPO', str(ROOT.parent / 'StockQAbyLLM')))
        self.assertTrue((repo / 'src/config/json_config_manager.py').exists(),
                        'StockQAbyLLM is required for S02 contract acceptance; configure STOCKQA_REPO')
        old_cwd = Path.cwd()
        old_argv = sys.argv[:]
        old_sys_path = sys.path[:]
        old_dont_write_bytecode = sys.dont_write_bytecode
        old_bytecode_env = os.environ.get('PYTHONDONTWRITEBYTECODE')
        bytecode_before = _stockqa_bytecode_snapshot(repo)
        preexisting_src_modules = {name for name in sys.modules if name == 'src' or name.startswith('src.')}
        preexisting_main = sys.modules.get('main_with_llm')
        sys.dont_write_bytecode = True
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        sys.path.insert(0, str(repo))
        try:
            temp_context = tempfile.TemporaryDirectory(prefix='iqs-stockqa-s02-')
            tmp = temp_context.name
            try:
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
                # The real Q01 path must preserve the provider's score exactly.
                answer = generator().generate_answer(models.Question('offline test'), [
                    models.SearchResult(title='test', snippet=description, score=8)])
                self.assertEqual(answer.score, 8)

                profile = {**copy.deepcopy(self.profile), 'entity_id': 'ENTITY_FIXTURE'}
                run_dir = Path(tmp) / 'composed-screening'
                qs.compose(profile, 'quick', run_dir, answer_format='screening-1')
                manifest = qs.read_json(run_dir / 'manifest.json')
                config_path = run_dir / 'questions.json'
                result_path = Path(tmp) / 'stockqa-result.json'
                config_json = json.loads(config_path.read_text(encoding='utf-8'))
                self.assertTrue(all(isinstance(item, dict) and item.get('question_id') and item.get('text')
                                    for group in config_json for item in group['questions']))
                Path(tmp, 'llm_apis.json').write_text(json.dumps({
                    'default_provider': 'openai',
                    'providers': {'openai': {'api_key': 'TEST_KEY_LOCAL_ONLY',
                                             'base_url': 'https://api.openai.com/v1/responses',
                                             'model': 'fixture-model', 'max_retries': 1,
                                             'format_repair_budget': 0}},
                }), encoding='utf-8')
                spend_path = Path(tmp, 'spend_authorization.json')
                spend_path.write_text(json.dumps({
                    'schema_version': '1.0.0', 'currency': 'USD', 'hard_cap': 25,
                    'pricing_snapshot_ref': 'synthetic-offline-cli-pricing/1',
                    'authorized_at': '2026-10-06T00:00:00Z',
                }), encoding='utf-8')
                client_module = importlib.import_module('src.providers.llm_client')
                main_cli = importlib.import_module('main_with_llm')

                class OfflineResponse:
                    def __init__(self, payload, request_id):
                        self.status_code = 200
                        self.headers = {'x-request-id': request_id}
                        self.payload = payload
                        self.content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                        self.text = self.content.decode('utf-8')

                    def raise_for_status(self):
                        return None

                    def json(self):
                        return self.payload

                class OfflineSession:
                    def __init__(self):
                        self.prompts = []

                    def post(self, endpoint, *, headers, timeout, **kwargs):
                        json_body = kwargs['json']
                        prompt = json_body['input']
                        self.prompts.append(prompt)
                        question_match = re.search(r'Target question_id: ([A-Z0-9_]+)', prompt)
                        if question_match is None:
                            raise AssertionError('StockQA omitted the bound question ID')
                        qid = question_match.group(1)
                        expected = next(item for item in manifest['questions'] if item['id'] == qid)
                        if expected['prompt'] not in prompt:
                            raise AssertionError('StockQA sent a different prompt than the manifest')
                        url = f'https://example.com/source/{qid.lower()}'
                        content = {
                            'id': qid, 'status': 'scored', 'score': 8, 'confidence': 'high',
                            'rationale': 'offline CLI fixture', 'information_as_of': profile['as_of'],
                            'period_start': None, 'period_end': None, 'basis': 'current',
                            'evidence': [{'claim': 'fixture source supports the score', 'title': 'Fixture source',
                                          'url': url, 'published_at': None, 'period': 'not_applicable'}],
                            'counterevidence': 'fixture counterevidence', 'sensitivity': 'fixture downside',
                            'metrics': {},
                        }
                        response_content = json.dumps({
                            'question_id': qid, 'entity_id': profile['entity_id'],
                            'company_name': profile['company'], 'status': 'scored', 'score': 8,
                            'description': json.dumps(content, ensure_ascii=False),
                        }, ensure_ascii=False)
                        payload = {
                            'id': f'resp-{qid}', 'status': 'completed', 'model': 'fixture-model',
                            'output': [
                                {'id': f'search-{qid}', 'type': 'web_search_call', 'status': 'completed',
                                 'action': {'type': 'search', 'sources': [{'url': url}]}},
                                {'type': 'message', 'content': [{'type': 'output_text', 'text': response_content}]},
                            ],
                        }
                        return OfflineResponse(payload, f'req-{qid}')

                offline_session = OfflineSession()

                sys.argv = ['main_with_llm.py', '--company', profile['company'], '--provider', 'openai',
                            '--config', str(config_path), '--output', str(result_path),
                            '--require-search', '--entity-id', profile['entity_id'],
                            '--spend-authorization', str(spend_path)]
                try:
                    cli_stdout, cli_stderr = io.StringIO(), io.StringIO()
                    with mock.patch.object(client_module.http_client_manager, 'get_sync_session',
                                           return_value=offline_session), \
                         contextlib.redirect_stdout(cli_stdout), \
                         contextlib.redirect_stderr(cli_stderr):
                        cli_status = main_cli.main()
                    self.assertTrue(result_path.is_file(), {
                        'cli_status': cli_status, 'mock_http_calls': len(offline_session.prompts),
                        'stdout_tail': cli_stdout.getvalue()[-1800:],
                        'stderr_tail': cli_stderr.getvalue()[-1800:],
                    })
                    quick_scan = qs.read_json(result_path)
                    self.assertEqual(cli_status, 0, {
                        question_id: receipt.get('failure_type')
                        for question_id, receipt in quick_scan['execution_receipts'].items()
                        if receipt.get('failure_type')
                    })
                    self.assertEqual(len(offline_session.prompts), manifest['question_count'])
                    self.assertEqual(quick_scan['schema_version'], 'stockqa.quick_scan_result/1.0.0')
                    self.assertEqual(set(quick_scan['answers']), {item['id'] for item in manifest['questions']})
                    first_receipt = next(iter(quick_scan['execution_receipts'].values()))
                    self.assertEqual(first_receipt['http_status_code'], 200)
                    self.assertTrue(first_receipt['input_question_sha256'])
                    self.assertEqual(first_receipt['attempts'][-1]['http_status_code'], 200)
                    bundle = {
                        'schema_version': 'invest-quick-scan.screening-import/1.0.0',
                        'manifest_sha256': qs._stable_sha256(manifest),
                        'input_question_sha256': {
                            item['id']: hashlib.sha256(item['prompt'].encode('utf-8')).hexdigest()
                            for item in manifest['questions']
                        },
                        'result': quick_scan,
                    }
                    screened = qs.normalize(manifest, bundle)
                    self.assertEqual(screened['summary']['quality_score'], 8, {
                        'screening_error': screened['questions'][0].get('screening_error'),
                    })
                    self.assertTrue(all(item['score'] == 8 for item in screened['questions']))
                    self.assertTrue(all(item['screening_status'] == 'screening_checked'
                                        for item in screened['questions']))
                    self.assertTrue(all(item['check_level'] == 'screening_audited'
                                        for item in screened['questions']))
                    self.assertTrue(all(item['formal_research_status'] == 'not_accepted'
                                        for item in screened['questions']))
                finally:
                    sys.argv = old_argv
            finally:
                _cleanup_stockqa_import_state(
                    tmp=tmp, temp_context=temp_context, old_cwd=old_cwd, old_argv=old_argv,
                    old_sys_path=old_sys_path, preexisting_src_modules=preexisting_src_modules,
                    preexisting_main=preexisting_main,
                    old_dont_write_bytecode=old_dont_write_bytecode,
                    old_bytecode_env=old_bytecode_env,
                )
        finally:
            os.chdir(old_cwd)
            sys.argv = old_argv
            sys.path[:] = old_sys_path
            sys.dont_write_bytecode = old_dont_write_bytecode
            if old_bytecode_env is None:
                os.environ.pop('PYTHONDONTWRITEBYTECODE', None)
            else:
                os.environ['PYTHONDONTWRITEBYTECODE'] = old_bytecode_env
        self.assertEqual(_stockqa_bytecode_snapshot(repo), bytecode_before,
                         'the StockQA source tree must have no new or changed bytecode')

    def test_stockqa_import_cleanup_restores_state_after_failure(self):
        repo = Path(os.environ.get('STOCKQA_REPO', str(ROOT.parent / 'StockQAbyLLM')))
        self.assertTrue((repo / 'src/config/json_config_manager.py').exists(),
                        'StockQAbyLLM is required for S02 cleanup acceptance; configure STOCKQA_REPO')
        old_cwd = Path.cwd()
        old_argv = sys.argv[:]
        old_sys_path = sys.path[:]
        old_dont_write_bytecode = sys.dont_write_bytecode
        old_bytecode_env = os.environ.get('PYTHONDONTWRITEBYTECODE')
        bytecode_before = _stockqa_bytecode_snapshot(repo)
        preexisting_src_modules = {name for name in sys.modules if name == 'src' or name.startswith('src.')}
        preexisting_main = sys.modules.get('main_with_llm')
        temp_context = tempfile.TemporaryDirectory(prefix='iqs-stockqa-s02-failure-')
        tmp = temp_context.name
        try:
            sys.path.insert(0, str(repo))
            sys.dont_write_bytecode = True
            os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
            os.chdir(tmp)
            sys.argv = ['main_with_llm.py', '--forced-failure-fixture']
            importlib.import_module('src.config.json_config_manager')
            raise RuntimeError('simulated public CLI failure after external imports')
        except RuntimeError as exc:
            self.assertEqual(str(exc), 'simulated public CLI failure after external imports')
        finally:
            _cleanup_stockqa_import_state(
                tmp=tmp, temp_context=temp_context, old_cwd=old_cwd, old_argv=old_argv,
                old_sys_path=old_sys_path, preexisting_src_modules=preexisting_src_modules,
                preexisting_main=preexisting_main,
                old_dont_write_bytecode=old_dont_write_bytecode,
                old_bytecode_env=old_bytecode_env,
            )
        self.assertFalse(Path(tmp).exists())
        self.assertEqual(Path.cwd(), old_cwd)
        self.assertEqual(sys.argv, old_argv)
        self.assertEqual(sys.path, old_sys_path)
        self.assertEqual(sys.dont_write_bytecode, old_dont_write_bytecode)
        self.assertEqual(os.environ.get('PYTHONDONTWRITEBYTECODE'), old_bytecode_env)
        self.assertEqual(_stockqa_bytecode_snapshot(repo), bytecode_before,
                         'the StockQA source tree must have no new or changed bytecode after failure')

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


_route_fixture_spec = importlib.util.spec_from_file_location('_iqs_routing_fixture', ROOT / 'tests/test_routing.py')
_route_fixture_module = importlib.util.module_from_spec(_route_fixture_spec)
_route_fixture_spec.loader.exec_module(_route_fixture_module)


class RouteCompositionTests(_route_fixture_module.RoutingFixture):
    """S06 true composition/CLI paths, separate from S02 response regressions."""
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(qs, 'ROOT', self.root)
        patcher.start(); self.addCleanup(patcher.stop)

    def compose_route(self, route, name='run', **kwargs):
        output = self.root / 'outputs' / name
        result = qs.compose_from_route(route, output, now_utc=kwargs.pop('now_utc', self.now),
                    expected_route_decision_id=kwargs.pop('expected_route_decision_id', route['decision_id']), **kwargs)
        manifest = qs.read_json(output / 'manifest.json')
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), result['question_count'])
        self.assertEqual(sum(q['comparison_role'] == 'core' for q in manifest['questions']), 24)
        return manifest

    def cli(self, arguments, expected_code=0):
        out, error = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, 'argv', ['question_sets.py', *map(str, arguments)]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(error):
            if expected_code:
                with self.assertRaises(SystemExit) as caught:
                    qs.main()
                self.assertEqual(caught.exception.code, expected_code)
            else:
                qs.main()
        return out.getvalue(), error.getvalue()

    def native(self, candidates, *, status='scored', score=8):
        return {'question_id': 'ROUTE_02', 'entity_id': self.identity['entity_id'],
                'company_name': self.identity['company'], 'status': status, 'score': score,
                'description': json.dumps({'schema_version': '2.0.0', 'question_id': 'ROUTE_02',
                                            'candidates': candidates})}

    def test_s06_t1_real_quick_full_and_method_preserve_24_core(self):
        quick = self.compose_route(self.route(), 'quick')
        full = self.compose_route(self.route(input_changes={'requested_mode': 'full'}), 'full')
        self.assertEqual(quick['question_count'], 28)
        self.assertEqual(full['question_count'], 34)
        self.assertEqual(quick['method_id'], full['method_id'])
        self.assertEqual(quick['replacements'], {'IQS_03': 'OPERATING_02', 'IQS_11': 'OPERATING_01'})

    def test_s06_t2_mature_trough_composes_recovery_without_changing_core(self):
        facts = self.normal('mature') + [self.fact('cyclical', cycle_position='trough')]
        quick = self.compose_route(self.route(facts), 'quick')
        full = self.compose_route(self.route(facts, input_changes={'requested_mode': 'full'}), 'full')
        self.assertEqual((quick['question_count'], full['question_count']), (34, 42))
        self.assertEqual(quick['profile']['stage'], 'mature')
        self.assertEqual(quick['method_id'], full['method_id'])
        self.assertEqual(len([q for q in quick['questions'] if q['module_id'] == 'recovery']), 4)
        self.assertTrue(all(q['comparison_role'] == 'diagnostic' for q in quick['questions'] if q['module_id'] == 'recovery'))

    def test_s06_t3_budget30_exports_all_six_risk_questions_budget24_writes_nothing(self):
        decision = self.route(self.normal() + [self.fact('distressed', evidence_type='covenant_breach')])
        self.assertEqual(self.compose_route(decision, 'complete')['question_count'], 34)
        with self.assertRaisesRegex(ValueError, 'budget below mandatory'):
            self.compose_route(decision, 'invalid24', max_questions=24)
        self.assertFalse((self.root / 'outputs/invalid24').exists())
        manifest = self.compose_route(decision, 'budget30', max_questions=30)
        required = set(decision['dispatch_plan']['mandatory_question_ids'])
        self.assertEqual(manifest['question_count'], 30)
        self.assertTrue(required <= {q['id'] for q in manifest['questions']})
        self.assertTrue(required.isdisjoint(q['question_id'] for q in manifest['deferred_questions']))
        self.assertEqual(len(manifest['deferred_questions']), 4)

    def test_s06_t4_full_three_industries_requires_compatible_scope_and_no_legacy_relaxation(self):
        facts = self.normal() + [self.fact(m, materiality={'revenue_share': .3}) for m in ('industrial', 'software')]
        blocked = self.route(facts)
        with self.assertRaisesRegex(ValueError, 'requires_full_or_segments'):
            self.compose_route(blocked, 'blocked')
        self.assertFalse((self.root / 'outputs/blocked').exists())
        full = self.route(facts, input_changes={'requested_mode': 'full', 'compatible_business_scope': True})
        manifest = self.compose_route(full)
        self.assertTrue({'industrial', 'semiconductors', 'software'} <= set(manifest['modules']))
        legacy_profile = {**qs.read_json(ROOT / 'examples/profile.json'), 'industry_modules': ['industrial', 'semiconductors', 'software']}
        with self.assertRaisesRegex(ValueError, 'invalid number or duplicate industry_modules'):
            qs.validate_profile(legacy_profile, qs.load_library()[1])

    def test_s06_t5_common_only_and_known_distress_standard_output_keep_unknown_profile(self):
        common = self.compose_route(self.route([]), 'common', answer_format='standard-1')
        self.assertEqual(common['question_count'], 24)
        self.assertNotIn('company_type', common['profile'])
        risk = self.compose_route(self.route([self.fact('distressed', evidence_type='default')]), 'risk')
        self.assertEqual(risk['question_count'], 30)
        self.assertEqual(set(risk['modules']), {'common', 'distressed', 'recovery'})

    def test_s06_public_export_cannot_bypass_route_profile_id_or_clock(self):
        decision = self.route()
        profile = _route_fixture_module.routing.profile_from_route(decision)
        output = self.root / 'bypass'
        with self.assertRaisesRegex(ValueError, 'requires a frozen route'):
            qs.compose(profile, 'quick', output, package_id=self.package_id)
        with self.assertRaisesRegex(ValueError, 'current execution time and independent'):
            qs.compose(profile, 'quick', output, package_id=self.package_id, route_decision=decision)
        with self.assertRaisesRegex(ValueError, 'profile differs'):
            qs.compose({**profile, 'cycle_sensitive': True}, 'quick', output, package_id=self.package_id,
                       route_decision=decision, now_utc=self.now, expected_route_decision_id=decision['decision_id'])
        with self.assertRaisesRegex(ValueError, 'independently stored'):
            self.compose_route(decision, 'wrong-id', expected_route_decision_id='route_' + '0' * 64)
        self.assertFalse(output.exists())

    def test_s06_real_manifest_keeps_historical_ttl_but_reexport_at_expiry_is_blocked(self):
        approval = {'module_id': 'semiconductors', 'decision': 'selected', 'actor': 'fixture-user',
                    'reason': 'Reviewed', 'valid_until': '2026-09-21T00:00:00Z'}
        decision = self.route(user_policy={'manual_overrides': [approval]})
        manifest = self.compose_route(decision)
        with self.assertRaisesRegex(ValueError, 'expired at execution'):
            self.compose_route(decision, 'expired', now_utc='2026-09-21T00:00:00Z')
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), manifest['question_count'])
        for mutation in ('drop_route', 'drop_expected', 'late_clock'):
            forged = copy.deepcopy(manifest)
            if mutation == 'drop_route':
                del forged['route_decision']; del forged['route_decision_id']
                del forged['routing_execution']
            elif mutation == 'drop_expected':
                forged['routing_execution']['expected_decision_id'] = None
            else:
                forged['routing_execution']['checked_at'] = '2026-09-21T00:00:00Z'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                qs.validate_manifest_metric_contract(forged)

    def test_s06_native_cli_request_resolve_compose_preserves_model_and_identity(self):
        identity_path = self.root / 'identity.json'; qs.write_json(identity_path, self.identity)
        out = self.root / 'request'
        self.cli(['routing-v2-request', '--identity', identity_path, '--module-package-id', self.package_id, '--out-dir', out])
        request = qs.read_json(out / 'route-request.json')
        exported = qs.read_json(out / 'questions.json')[0]['questions'][0]
        self.assertEqual(exported['question_id'], 'ROUTE_02')
        self.assertEqual(hashlib.sha256(exported['text'].encode()).hexdigest(), request['prompt_sha256'])
        self.assertIn('NEVER a company investment score', exported['text'])
        self.assertIn('threshold is 7', exported['text'])
        answer_path = self.root / 'candidate.json'; qs.write_json(answer_path, self.native(self.normal()))
        receipt_path = self.root / 'receipt.json'; qs.write_json(receipt_path, self.receipt())
        route_path = self.root / 'decision.json'
        self.cli(['resolve-route', '--input', identity_path, '--module-package-id', self.package_id,
                  '--candidate', answer_path, '--execution-receipt', receipt_path, '--now-utc', self.now, '--output', route_path])
        decision = qs.read_json(route_path)
        self.assertEqual(decision['execution']['model_resolved'], 'fixture-v1')
        self.assertEqual(decision['classification_confidence']['score'], 8)
        self.assertEqual(decision['execution']['classification_score'], 8)
        self.assertEqual(self.item(decision, 'operating')['basis'], 'searched_llm')
        output = self.root / 'run'
        self.cli(['compose-route', '--route-decision', route_path, '--now-utc', self.now,
                  '--expected-route-decision-id', decision['decision_id'], '--out-dir', output])
        manifest = qs.read_json(output / 'manifest.json')
        self.assertEqual(manifest['question_count'], 28)
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), 28)
        self.assertEqual(manifest['route_decision_id'], decision['decision_id'])

    def test_s06_stockqa_public_result_cli_adapts_and_composes_by_public_contract(self):
        identity_path = self.root / 'public-result-identity.json'
        qs.write_json(identity_path, self.identity)
        route_request = _route_fixture_module.routing.build_route_request(
            self.identity, package_id=self.package_id, root=self.root)
        candidate = {'schema_version': '2.0.0', 'question_id': 'ROUTE_02',
                     'candidates': self.normal()}
        answer = {
            'question_id': 'ROUTE_02', 'status': 'scored', 'score': 8,
            'description': json.dumps(candidate, ensure_ascii=False),
            'source_urls': [f['sources'][0]['url'] for f in candidate['candidates']],
            'published_date': None, 'information_as_of': None,
            'check_level': 'unverified_model_output', 'check_level_receipt_id': None,
        }
        answer_sha256 = hashlib.sha256(_route_fixture_module.mc.canonical_bytes(answer)).hexdigest()
        question_receipt = {
            'answer_sha256': answer_sha256, 'answered_at': '2026-09-20T11:59:00Z',
            'input_question_sha256': route_request['prompt_sha256'], 'provider': 'openai',
            'requested_model': 'requested-model', 'actual_model': 'resolved-model',
            'request_id': 'request-public-1', 'attempt_id': 'attempt-public-1',
            'search_receipt_id': 'search-public-1', 'search_status': 'executed',
            'web_search_calls': [{'id': 'search-public-1', 'status': 'completed',
                                  'action_type': 'search',
                                  'source_urls': answer['source_urls']}],
        }
        result_path = self.root / 'stockqa-result.json'
        qs.write_json(result_path, {
            'schema_version': 'stockqa.quick_scan_result/1.0.0',
            'entity': {'entity_id': self.identity['entity_id'], 'name': self.identity['company']},
            'observed_at': '2026-09-20T12:00:00Z',
            'provider': {'name': 'openai', 'requested_model': 'requested-model'},
            'answers': {'ROUTE_02': answer},
            'execution_receipts': {'ROUTE_02': question_receipt},
        })
        decision_path = self.root / 'public-result-decision.json'
        self.cli(['resolve-route', '--input', identity_path, '--module-package-id', self.package_id,
                  '--candidate', result_path, '--now-utc', self.now, '--output', decision_path])
        decision = qs.read_json(decision_path)
        self.assertEqual(decision['execution']['answer_sha256'], answer_sha256)
        self.assertEqual(decision['execution']['model_requested'], 'requested-model')
        self.assertEqual(decision['execution']['model_resolved'], 'resolved-model')

        output = self.root / 'public-result-composed'
        self.cli(['compose-route', '--route-decision', decision_path, '--now-utc', self.now,
                  '--expected-route-decision-id', decision['decision_id'], '--out-dir', output])
        manifest = qs.read_json(output / 'manifest.json')
        self.assertEqual(manifest['route_decision_id'], decision['decision_id'])
        self.assertEqual(manifest['question_count'], 28)

    def test_mod19_native_cli_persists_low_classification_confidence_and_keeps_verified_route(self):
        identity_path = self.root / 'identity-low.json'
        qs.write_json(identity_path, {**self.identity, 'verified_facts': self.normal()})
        candidate_path = self.root / 'candidate-low.json'
        candidate = self.fact('concentrated')
        native_answer = self.native([candidate], score=6)
        qs.write_json(candidate_path, native_answer)
        receipt_path = self.root / 'receipt-low.json'
        answer_sha256 = hashlib.sha256(_route_fixture_module.mc.canonical_bytes(native_answer)).hexdigest()
        receipt = self.receipt(classification_score=6, answer_sha256=answer_sha256)
        qs.write_json(receipt_path, receipt)
        route_path = self.root / 'decision-low.json'
        self.cli(['resolve-route', '--input', identity_path, '--module-package-id', self.package_id,
                  '--candidate', candidate_path, '--execution-receipt', receipt_path,
                  '--now-utc', self.now, '--output', route_path])
        decision = qs.read_json(route_path)
        self.assertEqual(decision['classification_confidence']['score'], 6)
        self.assertEqual(decision['classification_confidence']['minimum_score'], 7)
        self.assertEqual(self.item(decision, 'concentrated')['reason_code'], 'overall_confidence_below_threshold')
        self.assertEqual(self.selected(decision), {'common', 'operating', 'semiconductors', 'scaling'})
        composed = self.compose_route(decision, 'low-confidence-route')
        self.assertTrue({'common', 'operating', 'semiconductors', 'scaling'} <= set(composed['modules']))

    def test_s06_native_cli_unknown_module_and_ambiguous_response_fail_before_output(self):
        engine = _route_fixture_module.routing
        answer = self.native(self.normal())
        for changed in ({**answer, 'entity_id': 'OTHER'}, {**answer, 'status': 'unknown', 'score': 5},
                        {**answer, 'score': True}, {**answer, 'description': '{"question_id":"ROUTE_02","question_id":"X"}'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                engine.parse_route_response(changed, self.identity)
        duplicate_outer = json.dumps(answer)[:-1] + ',"question_id":"ROUTE_02"}'
        with self.assertRaises(ValueError):
            engine.parse_route_response(duplicate_outer, self.identity)
        candidates = self.normal(); candidates[1]['module_id'] = 'ai_super_chip'
        input_path = self.root / 'input.json'; qs.write_json(input_path, self.identity)
        native_answer = self.native(candidates)
        answer_path = self.root / 'candidate.json'; qs.write_json(answer_path, native_answer)
        answer_sha256 = hashlib.sha256(_route_fixture_module.mc.canonical_bytes(native_answer)).hexdigest()
        receipt_path = self.root / 'receipt.json'; qs.write_json(
            receipt_path, self.receipt(answer_sha256=answer_sha256))
        output = self.root / 'should-not-exist.json'
        _, error = self.cli(['resolve-route', '--input', input_path, '--module-package-id', self.package_id,
                  '--candidate', answer_path, '--execution-receipt', receipt_path, '--now-utc', self.now,
                  '--output', output], expected_code=2)
        self.assertIn('unknown route module', error)
        self.assertFalse(output.exists())

    def test_mod19_resolve_cli_requires_independent_previous_decision_id(self):
        previous = self.route()
        previous_path = self.root / 'previous.json'; qs.write_json(previous_path, previous)
        facts = self.normal()
        facts[1]['materiality'] = {
            'revenue_share': .12, 'gross_profit_share': .12, 'invested_capital_share': .12}
        input_path = self.root / 'input-with-hysteresis.json'
        qs.write_json(input_path, {**self.identity, 'verified_facts': facts})
        output = self.root / 'must-not-write.json'
        _, error = self.cli(['resolve-route', '--input', input_path,
            '--module-package-id', self.package_id, '--previous-decision', previous_path,
            '--now-utc', self.now, '--output', output], expected_code=2)
        self.assertIn('caller-held identity is required', error)
        self.assertFalse(output.exists())

        output = self.root / 'with-verified-prior.json'
        self.cli(['resolve-route', '--input', input_path,
            '--module-package-id', self.package_id, '--previous-decision', previous_path,
            '--expected-previous-decision-id', previous['decision_id'],
            '--now-utc', self.now, '--output', output])
        resolved = qs.read_json(output)
        self.assertIn('semiconductors', self.selected(resolved))
        self.assertEqual(resolved['previous_decision_id'], previous['decision_id'])

    def test_s06_first_stage_package_keeps_exact_historical_request_prompt(self):
        old_package = 'pkg_5c7facbfd9b772130e3fb5150d2c4d390083e72570b28c82cc4ab67151fd881f'
        request = _route_fixture_module.routing.build_route_request(self.identity, package_id=old_package, root=ROOT)
        self.assertEqual(request['request_protocol'], 'candidate-only-1')
        self.assertEqual(request['prompt_sha256'], '6b35db51280523a71a860d82152054f95ce565cc534da0ca85cd1f05ba056740')

    def test_s06_uncertain_primary_axis_does_not_borrow_confidence_from_known_industry(self):
        facts = self.normal(); facts[0]['confidence'] = 'low'
        decision = self.route(facts)
        self.assertIn('semiconductors', self.selected(decision), 'preserve sourced classification evidence')
        self.assertEqual(decision['dispatch_plan']['eligible_module_ids'], ['common'])
        self.assertEqual(set(self.compose_route(decision, 'uncertain')['modules']), {'common'})
        facts = self.normal() + [self.fact('bank'), self.fact('distressed', evidence_type='covenant_breach')]
        conflicted = self.route(facts)
        self.assertEqual(set(conflicted['dispatch_plan']['eligible_module_ids']), {'common', 'distressed', 'recovery'})
        self.assertEqual(set(self.compose_route(conflicted, 'conflict')['modules']), {'common', 'distressed', 'recovery'})
        forged = copy.deepcopy(decision)
        forged['dispatch_plan']['eligible_module_ids'] = sorted(self.selected(decision))
        forged = _route_fixture_module.mc.seal_route_decision(forged)
        with self.assertRaisesRegex(ValueError, 'bypass unresolved primary axes'):
            self.compose_route(forged, 'forged')


if __name__ == '__main__':
    unittest.main()
