"""Validate the user-editable policy template offline; StockQA owns all execution."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]


def validate_policy(policy):
    schema = json.loads((ROOT / 'schemas/model-policy.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(policy)
    json.dumps(policy, allow_nan=False)
    groups = {g['id']: g for g in policy['quota_groups']}
    if len(groups) != len(policy['quota_groups']):
        raise ValueError('duplicate quota group')
    models = policy['models']
    if len({m['id'] for m in models}) != len(models):
        raise ValueError('duplicate model route id')
    seen = set()
    for m in models:
        if m['quota_group'] not in groups:
            raise ValueError('unknown quota group')
        if m['max_in_flight'] > groups[m['quota_group']]['max_in_flight']:
            raise ValueError('model concurrency exceeds shared quota group')
        if m['enabled']:
            if any('REPLACE_' in m[k] or not m[k].strip() for k in ('provider_config_ref', 'model')):
                raise ValueError('enabled model still contains placeholders')
            route = (m['provider_config_ref'], m['model'])
            if route in seen:
                raise ValueError('duplicate enabled provider/model route')
            seen.add(route)
    if policy['configured'] and (not seen or policy['budget']['max_cost'] <= 0 or policy['budget']['max_requests'] <= 0):
        raise ValueError('configured policy requires enabled models and positive explicit budgets')
    if policy['configured'] and policy['budget']['max_cost_per_attempt'] > policy['budget']['max_cost']:
        raise ValueError('per-attempt cost cap cannot exceed the total budget')
    comparison = policy['comparison']
    if comparison['enabled']:
        if not policy['configured']:
            raise ValueError('comparison requires a configured policy')
        if comparison['max_cost'] > policy['budget']['max_cost']:
            raise ValueError('comparison cost cap cannot exceed the shared total budget')
        if comparison['max_requests'] > policy['budget']['max_requests']:
            raise ValueError('comparison request cap cannot exceed the shared total budget')
        if comparison['max_models_per_question'] > len(seen):
            raise ValueError('comparison requests more models than enabled routes')
    return {'valid': True, 'configured': policy['configured'],
            'ordered_routes': [m['id'] for m in models if m['enabled']],
            'runtime_verified': False, 'network_used': False,
            'notice': 'Only structural configuration validation; StockQA must verify provider/search/quota capability.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True)
    args = p.parse_args()
    try:
        result = validate_policy(json.loads(Path(args.input).read_text(encoding='utf-8-sig')))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ValidationError as exc:
        location = '/'.join(str(part) for part in exc.absolute_path) or '(root)'
        p.exit(2, f'Error: invalid configuration at {location}; rule={exc.validator}. Input values omitted.\n')
    except Exception as exc:
        p.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
