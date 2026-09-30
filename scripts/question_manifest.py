"""Versioned validation of question manifests and their frozen packages.

This is the domain contract consumed by answer construction. It intentionally
does not import the question-set CLI or its normalizer.
"""

import hashlib
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

import module_contract
import module_registry
import question_library as library
from question_fingerprints import question_fingerprint
from question_prompts import (
    render_question,
    render_screening_question,
    renderer_rules_sha256,
    standard_prompt,
)
from question_selection import (
    apply_question_budget,
    module_locks,
    published_selection,
    select_questions,
)

ROOT = Path(__file__).resolve().parents[1]
METRIC_CONTRACT_VERSION = '1.0.0'


def metric_mapping(question, *, metric_schema=None, root=None):
    """Map a routed question to the frozen C02 metric/aggregation contract."""
    framework = question.get('framework')
    diagnostic = question.get('aggregation', 'scored') == 'diagnostic'
    if diagnostic:
        contract_dimension = {
            'dupont': 'dupont', 'porter': 'porter', 'recovery': 'recovery_watch'
        }.get(framework, 'recovery_watch')
        aggregation_role = 'diagnostic_only'
    elif question['dimension'] == 'growth':
        contract_dimension, aggregation_role = 'growth', 'growth_core'
    elif question['dimension'] == 'valuation':
        contract_dimension, aggregation_role = 'valuation', 'valuation_core'
    else:
        contract_dimension, aggregation_role = 'quality', 'quality_core'
    replacements = question.get('replaces', [])
    mapping = {
        'question_id': question['id'],
        'primary_metric_ref': question.get('metric_id'),
        'dimension': contract_dimension,
        'aggregation_role': aggregation_role,
        'critical_risk': bool(question.get('critical', False)) if not diagnostic else False,
        'replacement_for': replacements[0] if replacements else None,
        'evidence_demands': {
            'require_durability_conditions': question['dimension'] in ('moat', 'resilience'),
            'require_net_economic_effect': question['dimension'] == 'growth' or framework == 'recovery',
            'counter_evidence_required': True,
        },
    }
    local_root = Path(root) if root else ROOT
    schema = metric_schema or library.read_json(local_root / 'schemas/quick_scan/metric.schema.json')
    Draft7Validator(schema, format_checker=FormatChecker()).validate(mapping)
    return mapping


def validate_manifest_metric_contract(manifest, *, root=None):
    """Return authoritative mappings for a 3.1 manifest; leave older formats readable."""
    if 'metric_contract_version' not in manifest:
        return None
    if manifest.get('metric_contract_version') != METRIC_CONTRACT_VERSION:
        raise ValueError('unsupported metric contract version')
    local_root = Path(root) if root else ROOT
    if 'module_package_id' in manifest:
        return _validate_published_manifest(manifest, root=local_root)
    catalog, modules = library.load_library(root=local_root)
    if manifest.get('template_version') != catalog['version']:
        raise ValueError('metric-enriched manifest must match the loaded question catalog version')
    canonical = {q['id']: (q, module_id) for module_id, module in modules.items()
                 for q in module['questions']}
    mappings = manifest.get('question_metric_mappings')
    questions = manifest.get('questions')
    if not isinstance(mappings, list) or not isinstance(questions, list):
        raise ValueError('metric-enriched manifest requires mappings and questions')
    by_id = {item.get('question_id'): item for item in mappings if isinstance(item, dict)}
    question_ids = [item.get('id') for item in questions if isinstance(item, dict)]
    if (len(question_ids) != len(questions) or len(set(question_ids)) != len(question_ids)
            or len(by_id) != len(mappings) or set(by_id) != set(question_ids)
            or manifest.get('question_count') != len(questions)):
        raise ValueError('question metric mappings must be one-to-one')
    expected_questions, expected_modules, routed_replacements = select_questions(
        manifest.get('profile'), manifest.get('mode'), modules, root=local_root)
    expected_ids = [item['id'] for item in expected_questions]
    if (question_ids != expected_ids or manifest.get('modules') != expected_modules
            or manifest.get('replacements') != routed_replacements):
        raise ValueError('manifest selected question set differs from deterministic routing')
    bound_fields = ('dimension', 'metric_id', 'construct_id', 'comparison_role',
                    'rubric_version', 'scope', 'critical', 'aggregation', 'replaces')
    expected_replacements = {}
    for question in questions:
        canonical_item = canonical.get(question.get('id'))
        if canonical_item is None:
            raise ValueError('manifest contains an unknown question')
        source, expected_module_id = canonical_item
        if question.get('module_id') != expected_module_id:
            raise ValueError(f'manifest question module drift: {question["id"]}')
        for field in bound_fields:
            if question.get(field) != source.get(field):
                raise ValueError(f'manifest question metadata drift: {question["id"]}.{field}')
        expected = metric_mapping(source, root=local_root)
        if by_id.get(question['id']) != expected or question.get('metric_contract') != expected:
            raise ValueError(f'manifest metric mapping drift: {question["id"]}')
        for target in source.get('replaces', []):
            if target in expected_replacements:
                raise ValueError(f'duplicate selected replacement: {target}')
            expected_replacements[target] = source['id']
    if manifest.get('replacements') != expected_replacements:
        raise ValueError('manifest replacement mapping drift')
    return by_id


def _published_method_id(questions, profile, contexts, package, release, answer_format):
    core = sorted((q['construct_id'], question_fingerprint(q, profile, contexts, package, release,
                                                            answer_format))
                  for q in questions if q['comparison_role'] == 'core')
    return 'core-constructs-v1/' + module_contract.digest(core)[:16]


def _validate_published_manifest(manifest, *, root):
    package, modules, release, contexts = module_registry.load_package(
        manifest['module_package_id'], root=root)
    if package['renderer_rules_sha256'] != renderer_rules_sha256():
        raise ValueError('historical renderer implementation unavailable for prompt verification')
    if (manifest.get('module_release_id') != release['release_id']
            or manifest.get('template_version') != release['catalog_version']
            or manifest.get('renderer_version') != release['renderer_version']):
        raise ValueError('manifest must match the loaded question catalog version in its frozen release')
    expected_hashes = {entry['artifact_ref']: entry['artifact_sha256'] for entry in release['modules']
                       if entry['module_id'] in manifest.get('modules', [])}
    expected_hashes['module_package_id'] = package['package_id']
    expected_hashes['questions/scoring-contexts.json'] = module_contract.digest(contexts)
    if release['schema_version'] == '2.0.0':
        expected_hashes[release['routing_policy_ref']] = release['routing_policy_sha256']
    metric_reference = 'schemas/quick_scan/metric.schema.json'
    expected_hashes[metric_reference] = module_contract.digest(package['format_resources'][metric_reference])
    if manifest.get('answer_format') == 'standard-1':
        for reference in ('schemas/answer-content.schema.json', 'questions/metric-registry.json'):
            expected_hashes[reference] = module_contract.digest(package['format_resources'][reference])
    elif manifest.get('answer_format') == 'screening-1':
        reference = 'schemas/quick_scan/score.schema.json'
        expected_hashes[reference] = module_contract.digest(package['format_resources'][reference])
    if manifest.get('source_sha256') != expected_hashes:
        raise ValueError('manifest source hashes differ from released files')
    profile, mode = manifest.get('profile'), manifest.get('mode')
    route_decision = manifest.get('route_decision')
    if (route_decision is None and 'route_decision_id' in manifest) or (
            route_decision is not None and manifest.get('route_decision_id') != route_decision.get('decision_id')):
        raise ValueError('manifest route decision identity mismatch')
    expected, selected, replacements = published_selection(
        profile, mode, modules, release, route_decision, contexts, package, root=root)
    mandatory = ()
    if route_decision is not None and route_decision.get('schema_version') == '2.0.0':
        import routing as route_engine

        execution = manifest.get('routing_execution')
        if not isinstance(execution, dict) or set(execution) != {'checked_at', 'expected_decision_id'}:
            raise ValueError('route v2 manifest requires its original execution validation receipt')
        if execution['expected_decision_id'] != route_decision['decision_id']:
            raise ValueError('route execution receipt lacks the independent expected decision identity')
        route_engine.validate_recorded_route_execution(
            route_decision, root=root, now_utc=execution['checked_at'],
            expected_decision_id=execution['expected_decision_id'])
        mandatory = route_decision['dispatch_plan']['mandatory_question_ids']
    elif 'routing_execution' in manifest:
        raise ValueError('legacy manifest cannot claim v2 routing execution')
    expected, deferred = apply_question_budget(expected, manifest.get('max_questions'), mandatory)
    if (manifest.get('modules') != selected or manifest.get('replacements') != replacements
            or manifest.get('module_locks') != module_locks(release, selected)
            or manifest.get('deferred_questions') != deferred):
        raise ValueError('manifest selection, module lock, or deferred questions drift')
    questions = manifest.get('questions')
    if (not isinstance(questions, list) or len(questions) != len(expected)
            or manifest.get('question_count') != len(expected)):
        raise ValueError('manifest question count differs from released selection')
    mappings = manifest.get('question_metric_mappings')
    expected_mappings = [metric_mapping(q, metric_schema=package['format_resources'][metric_reference])
                         for q in expected]
    if mappings != expected_mappings:
        raise ValueError('manifest metric mapping differs from released questions')
    answer_format = manifest.get('answer_format')
    if answer_format not in ('legacy', 'standard-1', 'screening-1'):
        raise ValueError('unknown released answer format')
    if answer_format == 'standard-1':
        expected_prompts = [standard_prompt(q, profile, contexts=contexts,
                                            resources=package['format_resources']) for q in expected]
    elif answer_format == 'screening-1':
        expected_prompts = [render_screening_question(q, profile, contexts) for q in expected]
    else:
        expected_prompts = [render_question(q, profile, contexts) for q in expected]
    extras = {'metric_contract', 'prompt', 'prompt_sha256', 'semantic_sha256', 'definition_sha256'}
    for observed, source, mapping, expected_prompt in zip(questions, expected,
                                                           expected_mappings, expected_prompts):
        if not isinstance(observed, dict) or {k: v for k, v in observed.items() if k not in extras} != source:
            raise ValueError('manifest question definition differs from archive')
        if observed.get('metric_contract') != mapping:
            raise ValueError('manifest question metric contract differs from archive')
        prompt = observed.get('prompt')
        if (not isinstance(prompt, str) or prompt != expected_prompt
                or observed.get('prompt_sha256') != hashlib.sha256(prompt.encode('utf-8')).hexdigest()
                or observed.get('definition_sha256') != module_contract.question_definition_sha256(
                    next(q for q in modules[source['module_id']]['questions'] if q['id'] == source['id']))
                or observed.get('semantic_sha256') != question_fingerprint(
                    source, profile, contexts, package, release, answer_format)):
            raise ValueError('manifest question prompt or semantic fingerprint mismatch')
    if manifest.get('method_id') != _published_method_id(
            expected, profile, contexts, package, release, answer_format):
        raise ValueError('manifest core method fingerprint mismatch')
    return {item['question_id']: item for item in expected_mappings}
