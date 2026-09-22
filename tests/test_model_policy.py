"""The editable template is configuration, never proof of a working provider."""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('model_policy', ROOT / 'scripts/model_policy.py')
mp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mp)


class ModelPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'examples/model-policy.template.json').read_text(encoding='utf-8'))

    def configured_policy(self):
        p = copy.deepcopy(self.policy)
        p['configured'] = True
        p['budget'].update(max_cost=10, max_requests=20)
        for i, model in enumerate(p['models']):
            model.update(enabled=True, provider_config_ref=f'user_config_{i}', model=f'user_model_{i}')
        return p

    def test_unconfigured_template_never_claims_runtime_verified(self):
        result = mp.validate_policy(self.policy)
        self.assertTrue(result['valid'])
        self.assertFalse(result['configured'])
        self.assertFalse(result['runtime_verified'])
        self.assertFalse(result['network_used'])
        self.assertEqual(result['ordered_routes'], [])

    def test_user_array_order_is_preserved_without_mutating_input(self):
        p = self.configured_policy()
        p['models'] = [p['models'][2], p['models'][0], p['models'][1]]
        before = copy.deepcopy(p)
        self.assertEqual(mp.validate_policy(p)['ordered_routes'], ['third_choice', 'first_choice', 'second_choice'])
        self.assertEqual(p, before)

    def test_configured_requires_real_routes_and_explicit_positive_budgets(self):
        changes = [lambda p: p['budget'].update(max_cost=0),
                   lambda p: p['budget'].update(max_requests=0),
                   lambda p: p['models'][0].update(model='REPLACE_WITH_MODEL_A'),
                   lambda p: [m.update(enabled=False) for m in p['models']]]
        for change in changes:
            with self.subTest(change=change):
                p = self.configured_policy()
                change(p)
                with self.assertRaises(ValueError):
                    mp.validate_policy(p)

    def test_duplicate_routes_or_groups_and_unknown_group_rejected(self):
        changes = [lambda p: p['quota_groups'].append(copy.deepcopy(p['quota_groups'][0])),
                   lambda p: p['models'][1].update(id=p['models'][0]['id']),
                   lambda p: p['models'][1].update(provider_config_ref=p['models'][0]['provider_config_ref'], model=p['models'][0]['model']),
                   lambda p: p['models'][0].update(quota_group='missing')]
        for change in changes:
            with self.subTest(change=change):
                p = self.configured_policy()
                change(p)
                with self.assertRaises(ValueError):
                    mp.validate_policy(p)

    def test_account_concurrency_and_integer_types_are_checked(self):
        p = self.configured_policy()
        p['models'][0]['max_in_flight'] = 3
        with self.assertRaisesRegex(ValueError, 'shared quota group'):
            mp.validate_policy(p)
        for value in (True, 0, 1.5):
            with self.subTest(value=value):
                p = self.configured_policy()
                p['dispatch']['max_in_flight_total'] = value
                with self.assertRaises(ValidationError):
                    mp.validate_policy(p)

    def test_secrets_racing_and_restart_budget_reset_rejected(self):
        changes = [lambda p: p['models'][0].update(api_key='FICTIONAL_NOT_A_SECRET'),
                   lambda p: p['dispatch'].update(speculative_racing=True),
                   lambda p: p['budget'].update(reset_on_restart=True),
                   lambda p: p['fallback'].update(on_low_score='try_next')]
        for change in changes:
            with self.subTest(change=change):
                p = self.configured_policy()
                change(p)
                with self.assertRaises(ValidationError):
                    mp.validate_policy(p)

    def test_shared_five_hour_hint_does_not_assume_every_account_has_it(self):
        p = self.configured_policy()
        self.assertEqual(p['models'][0]['quota_group'], p['models'][2]['quota_group'])
        self.assertEqual(p['quota_groups'][0]['window_seconds_hint'], 18000)
        self.assertIsNone(p['quota_groups'][1]['window_seconds_hint'])
        p['quota_groups'][0]['window_seconds_hint'] = None
        self.assertTrue(mp.validate_policy(p)['valid'])
        self.assertNotIn('remaining_quota', mp.validate_policy(p))

    def test_nonfinite_budget_cannot_be_serialized_into_live_configuration(self):
        p = self.configured_policy()
        p['budget']['max_cost'] = float('inf')
        with self.assertRaises(ValueError):
            mp.validate_policy(p)

    def test_cli_validation_error_does_not_echo_accidental_secret(self):
        p = self.configured_policy()
        p['models'][0]['api_key'] = 'FICTIONAL_ACCIDENTALLY_INCLUDED_SECRET'
        output = io.StringIO()
        # The schema is real; only the CLI input file read is replaced.
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            if path.name == 'invalid-policy.json':
                return json.dumps(p)
            return original_read(path, *args, **kwargs)
        with patch('sys.argv', ['model_policy.py', '--input', 'invalid-policy.json']), patch.object(Path, 'read_text', read), contextlib.redirect_stderr(output):
            with self.assertRaises(SystemExit) as error:
                mp.main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('invalid configuration', output.getvalue())
        self.assertNotIn(p['models'][0]['api_key'], output.getvalue())


if __name__ == '__main__':
    unittest.main()
