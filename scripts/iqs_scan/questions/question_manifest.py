"""Versioned validation of question manifests and their frozen packages.

This is the domain contract consumed by answer construction. It intentionally
does not import the question-set CLI or its normalizer.
"""

from iqs_scan import REPO_ROOT

import hashlib
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

from iqs_scan.foundation import api as module_contract
from . import module_registry
from . import question_library as library
from .question_fingerprints import question_fingerprint
from .question_prompts import (
    render_question,
    render_screening_question,
    renderer_rules_sha256,
    renderer_for_release,
    standard_prompt,
)
from .question_selection import (
    apply_question_budget,
    module_locks,
    published_selection,
    select_questions,
)

ROOT = REPO_ROOT
API_PROTOCOL = "iqs.question-manifest-api/1.1.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "METRIC_CONTRACT_VERSION",
    "archived_facts", "fact_questions", "metric_contract_version_for_schema",
    "metric_mapping", "published_method_id",
    "question_field_id",
    "select_fact_questions", "validate_manifest_metric_contract",
    "validate_published_manifest",
})
METRIC_CONTRACT_VERSION = '1.1.0'
SUPPORTED_METRIC_CONTRACT_VERSIONS = frozenset({'1.0.0', '1.1.0'})


def metric_contract_version_for_schema(schema):
    """Read the metric contract version frozen with a module package.

    Packages created before the explicit marker are contract 1.0.0. Their
    mapping semantics remain unchanged even when the authoring schema advances.
    """
    version = schema.get('x-metric-contract-version', '1.0.0')
    if version not in SUPPORTED_METRIC_CONTRACT_VERSIONS:
        raise ValueError('unsupported metric contract version')
    return version


def question_field_id(question):
    """Return the field used by both frozen questions and their observations."""
    return question.get('field_id', question.get('metric_id'))


def metric_mapping(question, *, metric_schema=None, root=None):
    """Map a routed question to the frozen C02 metric/aggregation contract."""
    local_root = Path(root) if root else ROOT
    schema = metric_schema or library.read_json(local_root / 'schemas/quick_scan/metric.schema.json')
    properties = schema['definitions']['QuestionMetricMapping']['properties']
    generic_diagnostics = 'diagnostic' in properties['dimension']['enum'] and 'framework' in properties
    metric_version = metric_contract_version_for_schema(schema)
    aggregation_roles = schema.get('definitions', {}).get('AggregationRole', {}).get('enum', [])
    supports_context_only = 'context_only' in aggregation_roles
    framework = question.get('framework')
    diagnostic = question.get('aggregation', 'scored') == 'diagnostic'
    if diagnostic:
        contract_dimension = {
            'dupont': 'dupont', 'porter': 'porter', 'recovery': 'recovery_watch'
        }.get(framework, 'diagnostic' if generic_diagnostics else 'recovery_watch')
        aggregation_role = 'diagnostic_only'
    elif (metric_version == '1.1.0'
          and supports_context_only
          and question.get('comparison_role') == 'context'):
        contract_dimension = ('growth' if question['dimension'] == 'growth' else
                              'valuation' if question['dimension'] == 'valuation' else 'quality')
        aggregation_role = 'context_only'
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
    if contract_dimension == 'diagnostic' and framework is not None:
        mapping['framework'] = framework
    Draft7Validator(schema, format_checker=FormatChecker()).validate(mapping)
    return mapping


def validate_manifest_metric_contract(manifest, *, root=None):
    """Return authoritative mappings for a 3.1 manifest; leave older formats readable."""
    if 'metric_contract_version' not in manifest:
        return None
    if manifest.get('metric_contract_version') not in SUPPORTED_METRIC_CONTRACT_VERSIONS:
        raise ValueError('unsupported metric contract version')
    local_root = Path(root) if root else ROOT
    if 'module_package_id' in manifest:
        return validate_published_manifest(manifest, root=local_root)
    catalog, modules = library.load_library(root=local_root)
    authoring_schema = library.read_json(local_root / 'schemas/quick_scan/metric.schema.json')
    if manifest.get('metric_contract_version') != metric_contract_version_for_schema(authoring_schema):
        raise ValueError('metric contract version differs from the active schema')
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


def published_method_id(questions, profile, contexts, package, release, answer_format):
    core = sorted((q['construct_id'], question_fingerprint(q, profile, contexts, package, release,
                                                            answer_format))
                  for q in questions if q['comparison_role'] == 'core')
    return 'core-constructs-v1/' + module_contract.module_digest(core)[:16]


def fact_questions(bank):
    """Return the same canonical definitions for draft, release and observation reads."""
    return [{**q, 'response_kind': 'fact', 'scope': 'entity',
             'rubric_version': bank['version'], 'construct_id': None}
            for q in bank['questions']]


def select_fact_questions(bank, profile, mode):
    recovery = (profile.get('recovery_review') or profile.get('stage') in ('turnaround', 'declining')
                or 'distressed' in profile.get('overlays', []))
    selected = []
    for question in fact_questions(bank):
        applies = question['applies']
        relevant = (applies.get('all') or profile.get('company_type') in applies.get('types', [])
                    or bool(set(profile.get('industry_modules', [])) & set(applies.get('industries', [])))
                    or profile.get('stage') in applies.get('stages', [])
                    or (applies.get('cycle_sensitive') and profile.get('cycle_sensitive'))
                    or (applies.get('recovery') and recovery))
        if relevant and (mode == 'full' or question['priority'] == 1):
            selected.append(question)
    return selected


def archived_facts(package, profile, mode, ids):
    """Verify the requested opt-in against the original archived bank and route profile."""
    if not isinstance(ids, list) or not ids or any(not isinstance(qid, str) for qid in ids):
        raise ValueError('fact question selection must be a nonempty ID list')
    bank = package['format_resources'].get(module_registry.FACT_BANK_RESOURCE)
    if bank is None:
        raise ValueError('released package has no fact bank')
    selected = [q for q in select_fact_questions(bank, profile, mode) if q['id'] in ids]
    if len({q['id'] for q in selected}) != len(selected) or ids != [q['id'] for q in selected]:
        raise ValueError('fact question selection differs from the applicable archived bank order')
    return selected


def validate_published_manifest(manifest, *, root):
    package, modules, release, contexts = module_registry.load_package(
        manifest['module_package_id'], root=root)
    renderer = renderer_for_release(release['renderer_version'], package['renderer_rules_sha256'])
    if (manifest.get('module_release_id') != release['release_id']
            or manifest.get('template_version') != release['catalog_version']
            or manifest.get('renderer_version') != release['renderer_version']):
        raise ValueError('manifest must match the loaded question catalog version in its frozen release')
    expected_hashes = {entry['artifact_ref']: entry['artifact_sha256'] for entry in release['modules']
                       if entry['module_id'] in manifest.get('modules', [])}
    expected_hashes['module_package_id'] = package['package_id']
    expected_hashes['questions/scoring-contexts.json'] = module_contract.module_digest(contexts)
    if release['schema_version'] == '2.0.0':
        expected_hashes[release['routing_policy_ref']] = release['routing_policy_sha256']
    metric_reference = 'schemas/quick_scan/metric.schema.json'
    metric_schema = package['format_resources'][metric_reference]
    if manifest.get('metric_contract_version') != metric_contract_version_for_schema(metric_schema):
        raise ValueError('metric contract version differs from the frozen schema')
    expected_hashes[metric_reference] = module_contract.module_digest(metric_schema)
    if manifest.get('answer_format') == 'standard-1':
        for reference in ('schemas/answer-content.schema.json', 'questions/metric-registry.json'):
            expected_hashes[reference] = module_contract.module_digest(package['format_resources'][reference])
    elif manifest.get('answer_format') == 'screening-1':
        reference = 'schemas/quick_scan/score.schema.json'
        expected_hashes[reference] = module_contract.module_digest(package['format_resources'][reference])
    profile, mode = manifest.get('profile'), manifest.get('mode')
    facts = []
    if 'fact_question_ids' in manifest:
        if manifest.get('answer_format') != 'standard-1':
            raise ValueError('fact questions require standard-1')
        facts = archived_facts(package, profile, mode, manifest['fact_question_ids'])
        resource = module_registry.FACT_BANK_RESOURCE
        expected_hashes[resource] = module_contract.module_digest(package['format_resources'][resource])
    if manifest.get('source_sha256') != expected_hashes:
        raise ValueError('manifest source hashes differ from released files')
    route_decision = manifest.get('route_decision')
    if (route_decision is None and 'route_decision_id' in manifest) or (
            route_decision is not None and manifest.get('route_decision_id') != route_decision.get('decision_id')):
        raise ValueError('manifest route decision identity mismatch')
    selection_policy = manifest.get('selection_policy')
    if selection_policy not in (None, 'basic-required-v1'):
        raise ValueError('unsupported question selection policy')
    if selection_policy == 'basic-required-v1' and profile.get('diagnostic_exclusions'):
        raise ValueError('new scan cannot exclude basic diagnostics')
    expected, selected, replacements = published_selection(
        profile, mode, modules, release, route_decision, contexts, package, root=root,
        historical_profile_defaults=selection_policy is None)
    if selection_policy == 'basic-required-v1':
        required = {q['id'] for mid in library.ALWAYS_APPLICABLE_DIAGNOSTICS
                    for q in modules[mid]['questions']}
        if not required <= {q['id'] for q in expected}:
            raise ValueError('new scan selection omits mandatory basic diagnostics')
    mandatory = ()
    if route_decision is not None and route_decision.get('schema_version') == '2.0.0':
        from . import routing as route_engine

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
    budget_policy = manifest.get('budget_policy')
    if budget_policy not in (None, 'basic-required-v1'):
        raise ValueError('unsupported question budget policy')
    expected, deferred = apply_question_budget(
        expected, manifest.get('max_questions'), mandatory,
        protect_basic=budget_policy == 'basic-required-v1', reserved=len(facts))
    if (manifest.get('modules') != selected or manifest.get('replacements') != replacements
            or manifest.get('module_locks') != module_locks(release, selected)
            or manifest.get('deferred_questions') != deferred):
        raise ValueError('manifest selection, module lock, or deferred questions drift')
    expected_mappings = [metric_mapping(q, metric_schema=package['format_resources'][metric_reference])
                         for q in expected]
    if {q['id'] for q in expected} & {q['id'] for q in facts}:
        raise ValueError('fact and score question identities overlap')
    expected = expected + facts
    questions = manifest.get('questions')
    if (not isinstance(questions, list) or len(questions) != len(expected)
            or manifest.get('question_count') != len(expected)):
        raise ValueError('manifest question count differs from released selection')
    mappings = manifest.get('question_metric_mappings')
    if mappings != expected_mappings:
        raise ValueError('manifest metric mapping differs from released questions')
    answer_format = manifest.get('answer_format')
    if answer_format not in ('legacy', 'standard-1', 'screening-1'):
        raise ValueError('unknown released answer format')
    if answer_format == 'standard-1':
        expected_prompts = [renderer.standard_prompt(q, profile, contexts=contexts,
                                            resources=package['format_resources']) for q in expected]
    elif answer_format == 'screening-1':
        expected_prompts = [renderer.render_screening_question(q, profile, contexts) for q in expected]
    else:
        expected_prompts = [renderer.render_question(q, profile, contexts) for q in expected]
    extras = {'metric_contract', 'prompt', 'prompt_sha256', 'semantic_sha256', 'definition_sha256'}
    for observed, source, mapping, expected_prompt in zip(questions, expected,
            expected_mappings + [None] * len(facts), expected_prompts, strict=True):
        if not isinstance(observed, dict) or {k: v for k, v in observed.items() if k not in extras} != source:
            raise ValueError('manifest question definition differs from archive')
        if observed.get('metric_contract') != mapping or (mapping is None and 'metric_contract' in observed):
            raise ValueError('manifest question metric contract differs from archive')
        definition = source if mapping is None else next(
            q for q in modules[source['module_id']]['questions'] if q['id'] == source['id'])
        prompt = observed.get('prompt')
        if (not isinstance(prompt, str) or prompt != expected_prompt
                or observed.get('prompt_sha256') != hashlib.sha256(prompt.encode('utf-8')).hexdigest()
                or observed.get('definition_sha256') != module_contract.question_definition_sha256(definition)
                or observed.get('semantic_sha256') != question_fingerprint(
                    source, profile, contexts, package, release, answer_format)):
            raise ValueError('manifest question prompt or semantic fingerprint mismatch')
    if manifest.get('method_id') != published_method_id(
            [q for q in expected if q.get('response_kind', 'score') == 'score'],
            profile, contexts, package, release, answer_format):
        raise ValueError('manifest core method fingerprint mismatch')
    return {item['question_id']: item for item in expected_mappings}


# Compatibility aliases for older callers; peer modules use public names.
_published_method_id = published_method_id
_validate_published_manifest = validate_published_manifest
