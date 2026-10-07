"""Synthetic offline metadata fixtures; actual IQS published release/compiler.

No fixture here certifies a StockWiki identity or an actual company answer.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import c06_authority as exporter
import standard_answers as sa
from test_standard_answers import published_fixture


RUN = {'run_id': 'fixture-run', 'scan_id': 'fixture-scan', 'inputset_id': 'fixture-input',
       'task_mode': 'comparison', 'comparison_group_id': 'fixture-group'}
VERSIONS = {'identity_schema': '2.2.0', 'answer_schema': '1.0.0',
            'observation_schema': '1.1.0', 'question_catalog': '3.2.0',
            'model_policy_schema': '2.0.0'}
PRODUCER = {'component_version': 'fixture-v2', 'build_id': 'offline-context-fixture'}


class C06AuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.answers, cls.receipts = published_fixture(
            entity_id='ENT_CONTEXT_FIXTURE', company='Fixture Corp', ticker='FIXTURE')
        cls.manifest['profile']['security_id'] = 'SEC_CONTEXT_FIXTURE'
        # Recompose after changing identity, rather than rehashing a tampered manifest.
        import question_sets as qs
        with tempfile.TemporaryDirectory(prefix='iqs-context-compose-') as own:
            qs.compose(cls.manifest['profile'], 'quick', own, 'standard-1')
            cls.manifest = qs.read_json(Path(own) / 'manifest.json')
        cls.versions = {**VERSIONS, 'question_catalog': cls.manifest['template_version']}
        cls.receipts = {**cls.receipts, **RUN, 'manifest_sha256': sa.digest(cls.manifest)}
        q = cls.manifest['questions'][0]
        cls.receipts['requests'][q['id']]['prompt_sha256'] = hashlib.sha256(q['prompt'].encode()).hexdigest()

    def create(self, manifest=None, **changes):
        args = dict(manifest_file_sha256='a' * 64, identity_snapshot_sha256='b' * 64,
                    run_context=RUN, contract_versions=self.versions, producer=PRODUCER)
        args.update(changes)
        source = manifest if manifest is not None else self.manifest
        return exporter.create_authority(copy.deepcopy(source), **args)

    def test_export_metadata_matches_existing_public_observation_builder(self):
        authority = self.create()
        complete = sa.build_observations(self.manifest, self.answers, self.receipts)['observations'][0]
        q = self.manifest['questions'][0]
        context = authority['observation_context']['questions'][q['id']]
        metadata = context['metadata']
        for key, value in metadata.items():
            self.assertEqual(value, complete[key], key)
        self.assertEqual(metadata['field_id'], q['metric_id'])
        self.assertEqual(metadata['question_definition_sha256'], q['definition_sha256'])
        self.assertEqual(metadata['question_semantic_sha256'], q['semantic_sha256'])
        self.assertEqual(metadata['information_cutoff'], self.manifest['profile']['as_of'])
        self.assertEqual(metadata['run_id'], RUN['run_id'])
        self.assertNotIn('observation_id', metadata)
        self.assertNotIn('execution', metadata)
        self.assertNotIn('answer', metadata)
        self.assertNotIn('observed_at', metadata)

    def test_export_carries_exact_prompt_and_manifest_bindings(self):
        context = self.create()['observation_context']
        self.assertEqual(context['manifest_content_sha256'], sa.digest(self.manifest))
        self.assertEqual(context['manifest_file_sha256'], 'a' * 64)
        self.assertEqual(context['identity_snapshot_sha256'], 'b' * 64)
        registry = json.loads((ROOT / 'questions/metric-registry.json').read_text(encoding='utf-8'))
        self.assertEqual(context['metric_registry_sha256'], sa.digest(registry))
        self.assertEqual(set(context['questions']), {q['id'] for q in self.manifest['questions']})
        for q in self.manifest['questions']:
            bound = context['questions'][q['id']]
            self.assertEqual(bound['frozen_prompt_sha256'], q['prompt_sha256'])
            self.assertEqual(bound['work_prompt_sha256'], hashlib.sha256(q['prompt'].strip().encode()).hexdigest())

    def test_tampered_published_question_rejected(self):
        for key in ('prompt', 'semantic_sha256', 'definition_sha256', 'metric_id'):
            bad = copy.deepcopy(self.manifest)
            bad['questions'][0][key] = 'changed'
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.create(bad)

    def test_missing_and_conflicting_run_context_rejected(self):
        for key in RUN:
            bad = {k: v for k, v in RUN.items() if k != key}
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.create(run_context=bad)
        for bad in ({**RUN, 'task_mode': 'primary'}, {**RUN, 'task_mode': 'comparison', 'comparison_group_id': None},
                    {**RUN, 'run_id': ''}, {**RUN, 'scan_id': False}, {**RUN, 'extra': 'not-allowed'}):
            with self.subTest(run=bad), self.assertRaises(ValueError):
                self.create(run_context=bad)

    def test_version_and_hash_contradictions_rejected(self):
        for changes in ({'manifest_file_sha256': 'not-a-hash'}, {'identity_snapshot_sha256': ''},
                        {'contract_versions': {**self.versions, 'question_catalog': 'wrong'}},
                        {'contract_versions': {**self.versions, 'observation_schema': '1.0.0'}},
                        {'producer': {**PRODUCER, 'build_id': 'x' * 161}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.create(**changes)

    def test_export_detaches_caller_objects_and_is_deterministic(self):
        first = self.create()
        self.assertEqual(first, self.create())
        first['observation_context']['questions'][self.manifest['questions'][0]['id']]['metadata']['cohort']['industries'].append('changed')
        self.assertNotEqual(first, self.create())

    def test_screening_manifest_not_relabelled_as_standard(self):
        bad = copy.deepcopy(self.manifest)
        bad['answer_format'] = 'screening-1'
        with self.assertRaises(ValueError):
            self.create(bad)

    def test_missing_security_scope_is_not_invented(self):
        import question_sets as qs
        profile = copy.deepcopy(self.manifest['profile'])
        profile.pop('security_id')
        with tempfile.TemporaryDirectory(prefix='iqs-context-unbound-') as own:
            qs.compose(profile, 'quick', own, 'standard-1')
            bad = qs.read_json(Path(own) / 'manifest.json')
        if not any(q['scope'] == 'security' for q in bad['questions']):
            self.fail('fixture must include a real released security-scoped question')
        with self.assertRaisesRegex(ValueError, 'security scope requires'):
            self.create(bad)

    def test_duplicate_json_input_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='iqs-context-duplicate-') as own:
            path = Path(own) / 'ambiguous.json'
            for text in ('{"run_id":"first","run_id":"second"}',
                         '{"nested":{"score":1,"score":9}}'):
                path.write_text(text, encoding='utf-8')
                with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'duplicate'):
                    exporter._read(path)

    def test_failed_atomic_publish_leaves_no_target_or_staging_file(self):
        with tempfile.TemporaryDirectory(prefix='iqs-context-publish-fault-') as own:
            root = Path(own)
            with patch.object(exporter.os, 'link', side_effect=OSError('synthetic publish failure')):
                with self.assertRaises(OSError):
                    exporter._publish(root / 'out.json', {'fixture': 'no answer'})
            self.assertEqual(list(root.iterdir()), [])

    def test_primary_context_remains_primary_and_has_no_comparison_group(self):
        authority = self.create(run_context={**RUN, 'task_mode': 'primary', 'comparison_group_id': None})
        for value in authority['observation_context']['questions'].values():
            self.assertEqual(value['metadata']['task_mode'], 'primary')
            self.assertIsNone(value['metadata']['comparison_group_id'])

    def test_public_cli_is_atomic_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='iqs-context-cli-') as own:
            root = Path(own)
            paths = {}
            for name, body in (('manifest', self.manifest), ('identity', {'fixture': 'not identity attestation'}),
                               ('run', RUN), ('versions', self.versions), ('producer', PRODUCER)):
                path = root / (name + '.json')
                path.write_text(json.dumps(body, ensure_ascii=False), encoding='utf-8')
                paths[name] = path
            output = root / 'authority.json'
            argv = sum(([f'--{name}', str(path)] for name, path in paths.items()), []) + ['--output', str(output)]
            self.assertEqual(exporter.main(argv), 0)
            original = output.read_bytes()
            result = json.loads(original)
            self.assertEqual(result['observation_context']['manifest_file_sha256'], hashlib.sha256(paths['manifest'].read_bytes()).hexdigest())
            self.assertEqual(result['observation_context']['identity_snapshot_sha256'], hashlib.sha256(paths['identity'].read_bytes()).hexdigest())
            self.assertEqual(exporter.main(argv), 2)
            self.assertEqual(output.read_bytes(), original)
            paths['run'].write_text('{}', encoding='utf-8')
            failed = root / 'invalid-authority.json'
            argv[-1] = str(failed)
            self.assertEqual(exporter.main(argv), 2)
            self.assertFalse(failed.exists())


if __name__ == '__main__':
    unittest.main()
