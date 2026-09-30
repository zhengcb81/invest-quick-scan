"""Offline question routing, StockQAbyLLM export, and evidence-aware score summaries.

No network, LLM client, credentials, retries, financial downloads or forecasts.
"""
import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from pathlib import Path

from jsonschema import ValidationError

import module_contract
import module_registry
import question_manifest as manifest_contract
import question_library as library
from question_prompts import (
    ANSWER_RULE,  # noqa: F401 - legacy public re-export
    applied_contexts,  # noqa: F401 - legacy public re-export
    render_question,
    render_screening_question as _prompt_renderer,
    renderer_rules_sha256 as _renderer_rules_sha256,
    standard_prompt,
)
from question_fingerprints import question_fingerprint
import question_selection as _selection_contract

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = {
    'business': '商业模式', 'moat': '竞争优势', 'execution': '执行组织',
    'financial': '财务质量', 'governance': '治理配置', 'resilience': '风险韧性',
    'growth': '成长机会', 'valuation': '当前估值',
}
QUALITY_WEIGHTS = dict(zip(list(DIMENSIONS)[:6], [20, 20, 15, 20, 15, 10]))
METRIC_CONTRACT_VERSION = manifest_contract.METRIC_CONTRACT_VERSION
STATUSES = {'scored', 'insufficient_evidence', 'not_applicable', 'search_unavailable'}
SCREENING_PROTOCOL_VERSION = '1.0.0'
SCREENING_STATUSES = {'scored', 'unknown', 'insufficient_evidence', 'not_applicable', 'error'}
RENDERER_VERSION = '1.0.0'


def validate_manifest_metric_contract(manifest):
    """Compatibility wrapper for the stable question-manifest contract."""
    return manifest_contract.validate_manifest_metric_contract(manifest, root=ROOT)


def metric_mapping(question, *, metric_schema=None):
    """Compatibility wrapper for the stable question-manifest metric mapping."""
    return manifest_contract.metric_mapping(question, metric_schema=metric_schema, root=ROOT)
read_json = library.read_json




write_json = library.write_json




def load_library():
    return library.load_library(root=ROOT)



def validate_library():
    catalog, modules = module_registry.validate_source_registry(root=ROOT)
    assert len(modules) == len(catalog['modules']), 'duplicate module IDs'
    ids = set()
    common_ids = {q['id'] for q in modules['common']['questions']}
    for entry in catalog['modules']:
        module = modules[entry['id']]
        assert module['module_id'] == entry['id'] and module['kind'] == entry['kind']
        assert module['kind'] in {'common', 'types', 'industries', 'stages', 'overlays',
                                  'diagnostics', 'common_extensions', 'lenses'}
        assert len(module['questions']) == entry['question_count']
        replaced = set()
        for q in module['questions']:
            assert q['id'] not in ids, f"duplicate question: {q['id']}"
            ids.add(q['id'])
            assert q['dimension'] in DIMENSIONS and q['priority'] in (1, 2)
            assert q['question'].strip() and q['evidence']
            assert q['metric_id'] == 'score.' + q['id'].lower()
            assert q['comparison_role'] in ('core', 'context', 'diagnostic')
            assert q['scope'] in ('entity', 'security', 'segment') and q['rubric_version']
            mapping = metric_mapping(q)
            assert (mapping['aggregation_role'] == 'diagnostic_only') == (
                q.get('aggregation', 'scored') == 'diagnostic')
            expected_construct = q['id'] if module['kind'] == 'common' else next(iter(q.get('replaces', [])), None)
            assert q['construct_id'] == expected_construct
            assert set(q['anchors']) == {'1', '5', '10'}
            assert len(set(q['anchors'].values())) == 3
            assert all(isinstance(v, str) and v.strip() for v in q['anchors'].values())
            assert q.get('aggregation', 'scored') in {'scored', 'diagnostic'}
            for target in q.get('replaces', []):
                assert module['kind'] == 'types' and target in common_ids
                assert target not in replaced, f'duplicate replacement in {module["module_id"]}'
                replaced.add(target)
    assert len(common_ids) == 24 and all(q['priority'] == 1 for q in modules['common']['questions'])
    assert {q['id'] for q in modules['common']['questions'] if q.get('critical')} == {'IQS_12', 'IQS_13', 'IQS_16'}
    factors = {q['factor'] for q in modules['dupont']['questions']}
    assert factors == {'roe', 'net_margin', 'asset_turnover', 'equity_multiplier',
                       'operating_margin', 'interest_burden', 'tax_burden'}
    forces = {q['factor'] for q in modules['porter']['questions']}
    assert forces == {'rivalry', 'entrants', 'substitutes', 'buyers', 'suppliers'}
    assert all(q.get('aggregation') == 'diagnostic' for key in ('dupont', 'porter')
               for q in modules[key]['questions'])
    assert sum(QUALITY_WEIGHTS.values()) == 100
    return {'modules': len(modules), 'questions': len(ids),
            'by_kind': dict(Counter(m['kind'] for m in modules.values()))}


def validate_profile(profile, modules, contexts=None):
    return library.validate_profile(profile, modules, contexts, root=ROOT)


def _select_from_module_ids(profile, mode, modules, selected_modules, mandatory_question_ids=()):
    return _selection_contract._select_from_module_ids(
        profile, mode, modules, selected_modules, mandatory_question_ids)


def select_questions(profile, mode, modules, contexts=None):
    return _selection_contract.select_questions(profile, mode, modules, contexts, root=ROOT)


def select_questions_for_route(profile, mode, modules, selected_module_ids, mandatory_question_ids=()):
    return _selection_contract.select_questions_for_route(
        profile, mode, modules, selected_module_ids, mandatory_question_ids)


def render_screening_question(q, profile, contexts=None):
    return _prompt_renderer(q, profile, contexts)


def export_questions(questions, profile=None, answer_format='legacy', contexts=None):
    categories = {}
    for q in questions:
        category = {'dupont': '追加诊断·杜邦分解', 'porter': '追加诊断·五力'}.get(
            q.get('framework'), DIMENSIONS[q['dimension']])
        prompt = (render_screening_question(q, profile, contexts) if answer_format == 'screening-1'
                  else render_question(q, profile, contexts))
        exported = {'question_id': q['id'], 'text': prompt} if answer_format == 'screening-1' else prompt
        categories.setdefault(category, []).append(exported)
    return [{'category': key, 'questions': values} for key, values in categories.items()]


def renderer_rules_sha256():
    return _renderer_rules_sha256()


def publish_library():
    return module_registry.publish(root=ROOT, renderer_version=RENDERER_VERSION,
                                   router_version='1.0.0',
                                   renderer_rules_sha256=renderer_rules_sha256())


def _apply_question_budget(questions, maximum, mandatory_question_ids=()):
    return _selection_contract.apply_question_budget(questions, maximum, mandatory_question_ids)


def _published_selection(profile, mode, modules, release, route_decision, contexts, package=None):
    return _selection_contract.published_selection(
        profile, mode, modules, release, route_decision, contexts, package, root=ROOT)


def _module_locks(release, selected):
    return _selection_contract.module_locks(release, selected)


def _question_fingerprint(q, profile, contexts, package, release, answer_format):
    """Compatibility entrypoint; fingerprint ownership is in a lower contract module."""
    return question_fingerprint(q, profile, contexts, package, release, answer_format)


def _published_method_id(questions, profile, contexts, package, release, answer_format):
    return manifest_contract._published_method_id(
        questions, profile, contexts, package, release, answer_format)


def _validate_published_manifest(manifest):
    return manifest_contract._validate_published_manifest(manifest, root=ROOT)


def compose(profile, mode, output_dir, answer_format='legacy', *, package_id=None,
            route_decision=None, max_questions=None, now_utc=None, expected_route_decision_id=None):
    profile = json.loads(json.dumps(profile, ensure_ascii=False))
    for key in ('industry_modules', 'overlays', 'diagnostic_modules',
                'investment_lenses', 'common_extension_modules'):
        if isinstance(profile.get(key), list):
            profile[key] = sorted(profile[key])
    if answer_format not in ('legacy', 'standard-1', 'screening-1'):
        raise ValueError('unknown answer format')
    if answer_format == 'screening-1' and not (
            isinstance(profile.get('entity_id'), str) and profile['entity_id'].strip()):
        raise ValueError('screening requires a verified stable profile entity_id')
    if package_id is None:
        package, modules, release, contexts = module_registry.load_current(root=ROOT)
    else:
        package, modules, release, contexts = module_registry.load_package(package_id, root=ROOT)
    if package['renderer_rules_sha256'] != renderer_rules_sha256():
        raise ValueError('historical renderer implementation unavailable for prompt verification')
    if answer_format == 'standard-1' and not module_registry.observation_ingest_ready(package):
        raise ValueError('module package cannot issue standard observations; historical read only')
    route_v2 = route_decision is not None and route_decision.get('schema_version') == '2.0.0'
    if route_v2:
        import routing as route_engine

        if not isinstance(now_utc, str) or not isinstance(expected_route_decision_id, str):
            raise ValueError('route v2 composition requires current execution time and independent decision identity')
        if route_decision.get('module_package_id') != package['package_id']:
            raise ValueError('route package differs from composed package')
        if profile != route_engine.profile_from_route(route_decision):
            raise ValueError('profile differs from frozen routing context')
        route_engine.validate_route_for_execution(
            route_decision, root=ROOT, now_utc=now_utc,
            expected_decision_id=expected_route_decision_id)
    chosen, selected, replacements = _published_selection(
        profile, mode, modules, release, route_decision, contexts, package)
    mandatory = (route_decision['dispatch_plan']['mandatory_question_ids'] if route_v2 else ())
    chosen, deferred = _apply_question_budget(chosen, max_questions, mandatory)
    metric_reference = 'schemas/quick_scan/metric.schema.json'
    metric_schema = package['format_resources'][metric_reference]
    metric_mappings = [metric_mapping(q, metric_schema=metric_schema) for q in chosen]
    prompts = []
    manifest_questions = []
    for question, mapping in zip(chosen, metric_mappings):
        if answer_format == 'standard-1':
            prompt = standard_prompt(question, profile, contexts=contexts,
                                     resources=package['format_resources'])
        elif answer_format == 'screening-1':
            prompt = render_screening_question(question, profile, contexts)
        else:
            prompt = render_question(question, profile, contexts)
        prompts.append(prompt)
        canonical_question = next(
            item for item in modules[question['module_id']]['questions']
            if item['id'] == question['id'])
        manifest_questions.append({
            **question,
            'metric_contract': mapping,
            'prompt': prompt,
            'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
            'semantic_sha256': _question_fingerprint(
                question, profile, contexts, package, release, answer_format),
            'definition_sha256': module_contract.question_definition_sha256(canonical_question),
        })
    source_hashes = {
        entry['artifact_ref']: entry['artifact_sha256'] for entry in release['modules']
        if entry['module_id'] in selected
    }
    source_hashes['module_package_id'] = package['package_id']
    source_hashes['questions/scoring-contexts.json'] = module_contract.digest(contexts)
    if release['schema_version'] == '2.0.0':
        source_hashes[release['routing_policy_ref']] = release['routing_policy_sha256']
    source_hashes[metric_reference] = module_contract.digest(package['format_resources'][metric_reference])
    if answer_format == 'standard-1':
        for reference in ('schemas/answer-content.schema.json', 'questions/metric-registry.json'):
            source_hashes[reference] = module_contract.digest(package['format_resources'][reference])
    elif answer_format == 'screening-1':
        reference = 'schemas/quick_scan/score.schema.json'
        source_hashes[reference] = module_contract.digest(package['format_resources'][reference])
    manifest = {
        'schema_version': '3.1',
        'template_version': release['catalog_version'],
        'renderer_version': release['renderer_version'],
        'mode': mode,
        'answer_format': answer_format,
        'module_package_id': package['package_id'],
        'module_release_id': release['release_id'],
        'method_id': _published_method_id(
            chosen, profile, contexts, package, release, answer_format),
        'aggregation_policy': 'core-constructs-v1',
        'profile': profile,
        'modules': selected,
        'module_locks': _module_locks(release, selected),
        'replacements': replacements,
        'deferred_questions': deferred,
        'max_questions': max_questions,
        'source_sha256': source_hashes,
        'question_count': len(chosen),
        'quality_weights': QUALITY_WEIGHTS,
        'metric_contract_version': METRIC_CONTRACT_VERSION,
        'question_metric_mappings': metric_mappings,
        'questions': manifest_questions,
    }
    if route_decision is not None:
        manifest['route_decision'] = route_decision
        manifest['route_decision_id'] = route_decision['decision_id']
    if route_v2:
        manifest['routing_execution'] = {
            'checked_at': now_utc,
            'expected_decision_id': expected_route_decision_id,
        }
    if answer_format == 'screening-1':
        manifest['screening_protocol_version'] = SCREENING_PROTOCOL_VERSION
    validate_manifest_metric_contract(manifest)
    output_dir = Path(output_dir)
    if any((output_dir / name).exists() for name in ('questions.json', 'manifest.json')):
        raise ValueError('output already contains a question run; use a fresh directory')
    question_groups = (export_questions(chosen, profile, answer_format, contexts)
                       if answer_format in ('legacy', 'screening-1')
                       else [{'category': '标准化评分', 'questions': prompts}])
    write_json(output_dir / 'questions.json', question_groups)
    write_json(output_dir / 'manifest.json', manifest)
    return {
        'question_count': len(chosen),
        'modules': selected,
        'deferred_question_ids': [item['question_id'] for item in deferred],
        'module_package_id': package['package_id'],
        'output_dir': str(output_dir.resolve()),
    }


def compose_from_route(route_decision, output_dir, *, now_utc, expected_route_decision_id,
                       answer_format='screening-1', max_questions=None):
    """Execute a v2 dispatch without inventing a legacy profile or current time."""
    import routing as route_engine
    return compose(route_engine.profile_from_route(route_decision),
                   route_decision['dispatch_plan']['resolved_mode'], output_dir, answer_format,
                   package_id=route_decision['module_package_id'], route_decision=route_decision,
                   max_questions=max_questions, now_utc=now_utc,
                   expected_route_decision_id=expected_route_decision_id)


def routing_question(company, ticker, exchange, as_of):
    date.fromisoformat(as_of)
    _, modules = load_library()
    choices = {kind: {key: m['name'] for key, m in modules.items() if m['kind'] == kind}
               for kind in ('types', 'industries', 'stages', 'overlays')}
    question = (f'[ROUTE_01] 截至{as_of}，{company}（{exchange}:{ticker}）的公司分类结论有多可靠？'
        '请实际联网核实法定实体、证券、主要经营利润或资产来源，再选择类型、行业、成长阶段和重要属性。'
        '只评价分类证据充分度：1=实体或业务有重大歧义；5=部分证据但主要类别仍不稳；'
        '10=实体与实质业务均有明确一致的官方证据。阶段早晚不代表评分高低。'
        '先金融/地产/控股/商业化前/一般经营类型，按业务实质选0至2个行业；'
        'operating和pre_revenue至少1个行业，不匹配用other；成长阶段恰好1个且不能选cyclical，'
        '周期性另设cycle_sensitive布尔值和cycle_position。重要属性按实际暴露选择。'
        '另给recovery_review布尔值和recovery_rationale：周期下行/低谷/初步修复、'
        '暂时经营困难或衰退性质待辨别时设true并说明依据，不要求先证明反转成功。'
        '纯周期低谷可保持mature阶段，不必误标turnaround；仅股价下跌不足以触发。'
        '多业务控股应说明分部覆盖缺口。类型、行业、阶段和属性备选为：'
        + json.dumps(choices, ensure_ascii=False)
        + '。返回外层{"score":整数,"description":字符串}；description为JSON对象序列化字符串，'
        '包含id=ROUTE_01、status、score、confidence、rationale、evidence，以及routing对象。'
        'routing包含company/ticker/exchange/security_class/as_of/company_type/industry_modules/stage/'
        'cycle_sensitive/cycle_position/recovery_review/recovery_rationale/overlays/'
        'routing_confidence/routing_rationale/routing_sources，'
        '有依据才添加reporting_currency/quote_currency/quote_date/accounting_standard/fiscal_year_end。'
        'evidence和routing_sources每项至少title/url/published_at，evidence另含claim和period。'
        '无法搜索时status=search_unavailable，内score=null、外score=5仅供兼容；'
        '有歧义标insufficient_evidence，禁止假装已分类。正式使用前由运行者核验routing。')
    return [{'category': '路由可信度（不进入公司评分）', 'questions': [question]}]


def valid_url(value):
    return library.valid_url(value)



def parse_answer(q, raw, as_of):
    if not isinstance(raw, dict) or type(raw.get('score')) is not int or not 1 <= raw['score'] <= 10:
        raise ValueError('missing or invalid outer integer score')
    if not isinstance(raw.get('description'), str):
        raise ValueError('description must be a serialized JSON string')
    result = json.loads(raw['description'])
    if not isinstance(result, dict) or result.get('id') != q['id']:
        raise ValueError('inner ID does not match question')
    if result.get('status') not in STATUSES or result.get('confidence') not in ('high', 'medium', 'low'):
        raise ValueError('invalid status or confidence')
    if not isinstance(result.get('rationale'), str) or not result['rationale'].strip():
        raise ValueError('rationale is required')
    if result['status'] != 'scored':
        if result.get('score') is not None or raw['score'] != 5:
            raise ValueError('unscored response requires null inner score and outer transport value 5')
        return result
    score = result.get('score')
    if type(score) is not int or not 1 <= score <= 10 or score != raw['score']:
        raise ValueError('invalid score or upstream score transmission mismatch')
    evidence = result.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('scored answer requires evidence')
    for item in evidence:
        if not isinstance(item, dict) or not valid_url(item.get('url')):
            raise ValueError('invalid evidence URL')
        if not all(isinstance(item.get(k), str) and item[k].strip()
                   for k in ('claim', 'title', 'published_at', 'period')):
            raise ValueError('evidence requires claim/title/published_at/period')
        if item['published_at'] != 'unknown':
            if date.fromisoformat(item['published_at']) > date.fromisoformat(as_of):
                raise ValueError('source was published after the information cutoff')
    if not all(isinstance(result.get(k), str) and result[k].strip()
               for k in ('counterevidence', 'sensitivity')):
        raise ValueError('counterevidence and sensitivity are required')
    if not isinstance(result.get('metrics'), dict):
        raise ValueError('metrics must be an object, empty if unavailable')
    return result


def summarize(records, policy='legacy-all-questions'):
    if policy not in ('legacy-all-questions', 'core-constructs-v1'):
        raise ValueError('unknown aggregation policy')
    base_records = records
    if policy == 'core-constructs-v1':
        base_records = [r for r in records if r.get('comparison_role') == 'core']
        constructs = [r.get('construct_id') for r in base_records]
        if len(constructs) != 24 or set(constructs) != {f'IQS_{i:02}' for i in range(1, 25)}:
            raise ValueError('fixed comparison requires exactly one row per core construct')
    dimensions = {}
    for dimension in DIMENSIONS:
        applicable = [r for r in base_records if r['dimension'] == dimension
                      and r.get('aggregation', 'scored') != 'diagnostic'
                      and r['status'] != 'not_applicable']
        valid = [r for r in applicable if r['status'] == 'scored' and r['score'] is not None]
        coverage = len(valid) / len(applicable) if applicable else 0
        dimensions[dimension] = {'name': DIMENSIONS[dimension], 'valid': len(valid),
            'applicable': len(applicable), 'coverage': round(coverage, 4),
            'score': round(sum(r['score'] for r in valid) / len(valid), 2)
            if valid and coverage >= 0.7 else None}
    quality_total = sum(dimensions[d]['applicable'] for d in QUALITY_WEIGHTS)
    quality_valid = sum(dimensions[d]['valid'] for d in QUALITY_WEIGHTS)
    coverage = quality_valid / quality_total if quality_total else 0
    quality = None
    if coverage >= 0.8 and all(dimensions[d]['score'] is not None for d in QUALITY_WEIGHTS):
        quality = round(sum(dimensions[d]['score'] * w for d, w in QUALITY_WEIGHTS.items()) / 100, 2)
    critical_issues = [
        {'id': r['id'], 'kind': 'material_concern' if r['status'] == 'scored' and r['score'] <= 3
         else 'unresolved', 'status': r['status'], 'score': r['score']}
        for r in records if r.get('critical') and (r['status'] != 'scored' or r['score'] <= 3)
    ]
    if critical_issues:
        quality = None
    all_applicable = [r for r in records if r['status'] != 'not_applicable']
    all_valid = [r for r in all_applicable if r['status'] == 'scored']
    return {'aggregation_policy': policy, 'dimensions': dimensions, 'quality_score': quality,
            'quality_coverage': round(coverage, 4),
            'all_question_coverage': round(len(all_valid) / len(all_applicable), 4) if all_applicable else 0,
            'growth_score': dimensions['growth']['score'],
            'valuation_score': dimensions['valuation']['score'],
            'critical_issues': critical_issues,
            'weak_points': [r['id'] for r in records if r['score'] is not None and r['score'] <= 3]}


def _validated_question_replacements(manifest):
    """Validate replacements against both manifest metadata and canonical routing."""
    questions = manifest.get('questions')
    declared = manifest.get('replacements', {})
    if not isinstance(questions, list) or not isinstance(declared, dict):
        return {}, False
    question_ids = set()
    replacements = {}
    for question in questions:
        if not isinstance(question, dict) or not isinstance(question.get('id'), str):
            return {}, False
        question_id = question['id']
        if question_id in question_ids:
            return {}, False
        question_ids.add(question_id)
        targets = question.get('replaces', [])
        if (not isinstance(targets, list) or any(not isinstance(target, str) or not target
                                                for target in targets)
                or len(targets) != len(set(targets))):
            return {}, False
        for target in targets:
            if target in replacements:
                return {}, False
            replacements[target] = question_id
    if (any(not isinstance(source, str) or not isinstance(target, str)
            for source, target in declared.items()) or replacements != declared):
        return {}, False
    recovery_base_ids = ('IQS_06', 'IQS_08', 'IQS_11', 'IQS_16', 'IQS_20')
    if any(base_id not in question_ids and base_id not in replacements
           for base_id in recovery_base_ids):
        return {}, False
    if 'metric_contract_version' in manifest:
        try:
            validate_manifest_metric_contract(manifest)
        except (KeyError, TypeError, ValueError):
            return {}, False
        return replacements, True

    # Older manifests remain readable, but their two mutable replacement copies are
    # not independent evidence. Verify them against the current canonical route when
    # that exact question catalog is available; otherwise retain the old answers but
    # withhold a "verified" recovery mapping.
    if 'module_package_id' in manifest:
        return {}, False
    try:
        catalog, modules = load_library()
        if manifest.get('template_version') != catalog['version']:
            return {}, False
        expected_questions, expected_modules, expected_replacements = select_questions(
            manifest.get('profile'), manifest.get('mode'), modules)
    except (KeyError, TypeError, ValueError):
        return {}, False
    if (manifest.get('modules') != expected_modules
            or manifest.get('replacements') != expected_replacements
            or len(questions) != len(expected_questions)):
        return {}, False
    for actual, expected in zip(questions, expected_questions):
        if (actual.get('id') != expected.get('id')
                or actual.get('module_id') != expected.get('module_id')
                or actual.get('replaces', []) != expected.get('replaces', [])):
            return {}, False
    return replacements, True


def recovery_watch(records, manifest, summary):
    """Expose recovery leads without changing scores or overriding evidence/risk gates."""
    by_id = {r['id']: r for r in records}
    replacements, replacement_mapping_verified = _validated_question_replacements(manifest)

    def effective(question_id):
        return replacements.get(question_id, question_id)

    def score(question_id):
        record = by_id.get(question_id, {})
        return record.get('score') if record.get('status') == 'scored' else None

    strengths = [{'id': r['id'], 'question': r['question'], 'score': r['score']}
                 for r in records if r['status'] == 'scored' and r['score'] >= 8
                 and r['dimension'] in QUALITY_WEIGHTS
                 and r.get('aggregation', 'scored') != 'diagnostic']
    weak_current = [effective(q) for q in ('IQS_06', 'IQS_08', 'IQS_11', 'IQS_20')
                    if score(effective(q)) is not None and score(effective(q)) <= 4]
    diagnostic_ids = ['RECOVERY_01', 'RECOVERY_02', 'RECOVERY_03', 'RECOVERY_04']
    result = {'policy_version': 'recovery-watch-1', 'status': 'not_assessed',
              'flags': [], 'strengths': strengths, 'weak_current_ids': weak_current,
              'critical_issues': summary['critical_issues'], 'quality_gate_overridden': False,
              'criteria': {}, 'missing_or_unusable_ids': []}
    if not replacement_mapping_verified:
        result['flags'].append('replacement_mapping_unverified')
        result['status'] = 'needs_verification'
    if not any(q in by_id for q in diagnostic_ids):
        if replacement_mapping_verified and strengths and weak_current:
            result.update(status='review_suggested', flags=['mixed_strength_and_weakness'])
        return result

    runway_ids = [effective('IQS_16')] + [q for q in
                  ('TURNAROUND_02', 'CYCLICAL_02', 'DISTRESSED_01') if q in by_id]
    required = diagnostic_ids + runway_ids
    result['criteria'] = {q: {'score': score(q), 'status': by_id.get(q, {}).get('status', 'missing')}
                          for q in required}
    result['missing_or_unusable_ids'] = [q for q in required if score(q) is None]
    for q, flag in zip(diagnostic_ids, ('structural_impairment_risk', 'core_assets_impaired',
                                       'catalyst_unproven', 'equity_capture_risk')):
        if score(q) is not None and score(q) <= 3:
            result['flags'].append(flag)
    if any(score(q) is not None and score(q) <= 3 for q in runway_ids):
        result['flags'].append('funding_before_recovery_risk')
    critical = summary['critical_issues']
    if any(c['kind'] == 'material_concern' for c in critical):
        result['flags'].append('critical_material_concern')
    if any(c['kind'] == 'unresolved' for c in critical):
        result['flags'].append('critical_unresolved')

    if set(result['flags']) & {'equity_capture_risk', 'funding_before_recovery_risk',
                              'critical_material_concern'}:
        result['status'] = 'high_risk_watch'
    elif set(result['flags']) & {'structural_impairment_risk', 'core_assets_impaired'}:
        result['status'] = 'structural_risk_watch'
    elif result['missing_or_unusable_ids'] or 'critical_unresolved' in result['flags']:
        result['status'] = 'needs_verification'
    elif (score('RECOVERY_01') >= 6 and score('RECOVERY_02') >= 7
          and score('RECOVERY_04') >= 6 and all(score(q) >= 6 for q in runway_ids)):
        result['status'] = ('recovery_evidence_watch' if score('RECOVERY_03') >= 6
                            else 'potential_watch')
    else:
        result['status'] = 'weak_case_watch'
    if not replacement_mapping_verified and result['status'] not in {
            'high_risk_watch', 'structural_risk_watch'}:
        result['status'] = 'needs_verification'
    return result


def _stable_sha256(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _screening_date(value, field, cutoff, allow_null=False, allow_future=False):
    if value is None and allow_null:
        return None
    if not isinstance(value, str):
        raise ValueError(f'{field} must be an ISO date')
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f'{field} must use YYYY-MM-DD')
    if parsed > date.fromisoformat(cutoff) and not allow_future:
        raise ValueError(f'{field} is after the information cutoff')
    return value


def _screening_timestamp(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} is required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError(f'{field} must include a timezone')
    return parsed


def _screening_receipt(entity_id, question_id, observation_id):
    body = {'entity_id': entity_id, 'question_id': question_id,
            'observation_id': observation_id, 'authorized_check_level': 'screening_audited',
            'issuer': 'iqs', 'status': 'active'}
    receipt_id = 'RCP_IQS_' + _stable_sha256(body)[:24]
    record = {'receipt_id': receipt_id, **body}
    record['receipt_sha256'] = _stable_sha256(record)
    return receipt_id, record


def _parse_screening_content(question, answer, cutoff):
    if not isinstance(answer.get('description'), str):
        raise ValueError('description must contain the screening JSON object')
    content = json.loads(answer['description'])
    if not isinstance(content, dict):
        raise ValueError('description must decode to an object')
    forbidden = {'accepted_ids', 'search_verified', 'check_level', 'check_level_receipt_id'}
    if forbidden.intersection(content):
        raise ValueError('model output cannot self-grant screening or formal acceptance')
    required = {'id', 'status', 'score', 'confidence', 'rationale', 'information_as_of',
                'period_start', 'period_end', 'basis', 'evidence', 'counterevidence', 'sensitivity', 'metrics'}
    if set(content) != required or content.get('id') != question['id']:
        raise ValueError('screening content fields or question ID do not match the manifest')
    if content['status'] not in SCREENING_STATUSES - {'error'}:
        raise ValueError('invalid screening content status')
    if content['status'] == 'scored':
        if type(content['score']) is not int or not 1 <= content['score'] <= 10:
            raise ValueError('scored content requires a strict integer from 1 to 10')
    elif content['score'] is not None:
        raise ValueError('non-scored content requires a null score')
    if (not isinstance(content['rationale'], str) or not content['rationale'].strip()
            or not isinstance(content['counterevidence'], str) or not content['counterevidence'].strip()
            or not isinstance(content['sensitivity'], str) or not content['sensitivity'].strip()):
        raise ValueError('rationale, counterevidence and sensitivity are required')
    if content['confidence'] not in ('high', 'medium', 'low'):
        raise ValueError('invalid confidence')
    if content['basis'] not in ('current', 'trailing', 'normalized', 'stress', 'forward', 'not_applicable'):
        raise ValueError('invalid answer basis')
    if _screening_date(content['information_as_of'], 'information_as_of', cutoff) != cutoff:
        raise ValueError('answer information date differs from the manifest cutoff')
    allow_future_period = content['basis'] == 'forward'
    start = _screening_date(content['period_start'], 'period_start', cutoff, allow_null=True,
                            allow_future=allow_future_period)
    end = content['period_end']
    if end is not None:
        if not isinstance(end, str):
            raise ValueError('period_end must be an ISO date or null')
        parsed_end = date.fromisoformat(end)
        if parsed_end.isoformat() != end:
            raise ValueError('period_end must use YYYY-MM-DD')
        if parsed_end > date.fromisoformat(cutoff) and content.get('basis') != 'forward':
            raise ValueError('historical period_end is after the information cutoff')
    if (start is None) != (end is None):
        raise ValueError('period_start and period_end must both be dates or both be null')
    if start and start > end:
        raise ValueError('period_start is after period_end')
    if not isinstance(content['evidence'], list):
        raise ValueError('evidence must be an array')
    if content['status'] == 'scored' and not content['evidence']:
        raise ValueError('scored content requires source evidence')
    for item in content['evidence']:
        if not isinstance(item, dict) or set(item) != {'claim', 'title', 'url', 'published_at', 'period'}:
            raise ValueError('evidence must contain claim/title/url/published_at/period')
        if (not all(isinstance(item.get(key), str) and item[key].strip()
                    for key in ('claim', 'title', 'url', 'period')) or not valid_url(item['url'])):
            raise ValueError('evidence contains an invalid source reference')
        _screening_date(item['published_at'], 'evidence.published_at', cutoff, allow_null=True)
    if not isinstance(content['metrics'], dict):
        raise ValueError('metrics must be an object')
    _stable_sha256(content)
    return content


def _check_screening_execution(answer, execution, content, result, cutoff,
                               expected_input_question_sha256):
    if not isinstance(execution, dict):
        raise ValueError('execution receipt is missing')
    if answer.get('check_level') != 'unverified_model_output' or answer.get('check_level_receipt_id') is not None:
        raise ValueError('upstream answer cannot self-grant a check level')
    for key in ('response_id', 'attempt_id', 'prompt_sha256', 'actual_model',
                'search_receipt_id', 'provider', 'input_question_sha256'):
        if not isinstance(execution.get(key), str) or not execution[key].strip():
            raise ValueError(f'execution receipt is missing {key}')
    request_id = execution.get('request_id')
    if ('request_id' not in execution
            or (request_id is None and execution['provider'] != 'minimax')
            or (request_id is not None
                and (not isinstance(request_id, str) or not request_id.strip()))):
        raise ValueError('execution receipt has an invalid request_id for its provider')
    if execution['input_question_sha256'] != expected_input_question_sha256:
        raise ValueError('executed question hash does not match the manifest prompt')
    if len(execution['prompt_sha256']) != 64 or any(ch not in '0123456789abcdef' for ch in execution['prompt_sha256'].lower()):
        raise ValueError('execution prompt hash is malformed')
    provider = result.get('provider')
    if (not isinstance(provider, dict) or 'name' not in provider
            or 'requested_model' not in provider):
        raise ValueError('scan provider envelope is incomplete')
    batch_provider, batch_model = provider['name'], provider['requested_model']
    for label, value in (('name', batch_provider), ('requested_model', batch_model)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f'scan provider {label} is invalid')
    if batch_provider is not None and execution['provider'] != batch_provider:
        raise ValueError('execution provider does not match the scan envelope')
    requested_model = execution.get('requested_model')
    if requested_model is not None and (not isinstance(requested_model, str) or not requested_model.strip()):
        raise ValueError('execution requested model is invalid')
    if batch_model is not None and requested_model is not None and requested_model != batch_model:
        raise ValueError('execution requested model does not match the scan envelope')
    if batch_provider is None and not requested_model:
        raise ValueError('mixed-provider execution is missing its requested model')
    if (execution.get('response_status') != 'completed'
            or type(execution.get('http_status_code')) is not int
            or execution['http_status_code'] != 200):
        raise ValueError('provider response did not complete successfully')
    if execution.get('search_status') != 'executed':
        raise ValueError('search was not verified as executed')
    attempts = execution.get('attempts')
    if not isinstance(attempts, list) or not attempts or not isinstance(attempts[-1], dict):
        raise ValueError('execution receipt has no final attempt record')
    final_attempt = attempts[-1]
    if 'request_id' not in final_attempt:
        raise ValueError('final attempt has no request_id field')
    for key in ('attempt_id', 'request_id', 'response_id', 'actual_model', 'prompt_sha256',
                'search_receipt_id', 'search_status', 'response_status', 'http_status_code'):
        if final_attempt.get(key) != execution.get(key):
            raise ValueError(f'final attempt receipt does not match {key}')
    final_provider = final_attempt.get('provider')
    if final_provider is not None and final_provider != execution['provider']:
        raise ValueError('final attempt provider does not match the execution receipt')
    if request_id is None and final_provider != 'minimax':
        raise ValueError('MiniMax response without request ID lacks final provider evidence')
    final_requested_model = final_attempt.get('requested_model')
    if final_requested_model is not None and final_requested_model != requested_model:
        raise ValueError('final attempt requested model does not match the execution receipt')
    outcome = execution.get('dispatch_outcome')
    # A direct single-provider StockQA attempt may carry only a config alias;
    # route identity starts with an actual route ID, ordinal, or trace.
    route_keys = ('route_id', 'route_ordinal', 'route_trace')
    has_route_marker = any(
        isinstance(attempt, dict) and any(key in attempt for key in route_keys)
        for attempt in attempts
    )
    modern_route = has_route_marker or outcome is not None or batch_provider is None
    if modern_route:
        # Standalone legacy receipts can lack route metadata. A cascade (or
        # any receipt that carries modern route markers) cannot use that
        # compatibility branch by selectively omitting its final identity.
        if (not isinstance(final_provider, str) or not final_provider.strip()
                or not isinstance(final_requested_model, str) or not final_requested_model.strip()):
            raise ValueError('modern execution lacks final provider or requested model')
    if has_route_marker or batch_provider is None:
        # provider_config_ref is a configuration alias, not endpoint identity.
        if (not isinstance(final_attempt.get('provider_config_ref'), str)
                or not final_attempt['provider_config_ref'].strip()
                or not isinstance(final_attempt.get('route_id'), str)
                or not final_attempt['route_id'].strip()
                or type(final_attempt.get('route_ordinal')) is not int
                or final_attempt['route_ordinal'] < 1):
            raise ValueError('final attempt lacks a verified route')
    if 'route_trace' in final_attempt:
        trace = final_attempt['route_trace']
        if (not isinstance(trace, list) or not trace or not isinstance(trace[-1], dict)):
            raise ValueError('final attempt route trace is malformed')
        accepted_route = trace[-1]
        if (accepted_route.get('decision') != 'accepted_answer'
                or accepted_route.get('route_id') != final_attempt['route_id']
                or accepted_route.get('ordinal') != final_attempt['route_ordinal']
                or accepted_route.get('requested_model') != final_requested_model
                or accepted_route.get('provider_config_ref') != final_attempt['provider_config_ref']):
            raise ValueError('final attempt route trace contradicts accepted execution')
    if outcome is not None:
        if (not isinstance(outcome, dict)
                or outcome.get('scope') != 'provider_dispatch'
                or outcome.get('state') != 'completed'
                or outcome.get('wait_reason') is not None
                or outcome.get('resume_condition') is not None):
            raise ValueError('provider dispatch did not complete')
    elif modern_route:
        raise ValueError('modern execution has no completed dispatch outcome')
    if final_attempt.get('response_status') != 'completed' or final_attempt.get('search_status') != 'executed':
        raise ValueError('final attempt did not complete with verified search')
    _screening_timestamp(execution.get('answered_at'), 'answered_at')
    observed = _screening_timestamp(result.get('observed_at'), 'observed_at')
    if _screening_timestamp(execution['answered_at'], 'answered_at') > observed:
        raise ValueError('answer timestamp is after scan completion')
    source_urls = execution.get('source_urls')
    if (not isinstance(source_urls, list) or not source_urls or len(source_urls) != len(set(source_urls))
            or any(not valid_url(url) for url in source_urls)):
        raise ValueError('execution receipt has no valid source URLs')
    calls = execution.get('web_search_calls')
    if not isinstance(calls, list):
        raise ValueError('execution receipt has no completed web search with sources')
    completed_calls = [call for call in calls if isinstance(call, dict)
                       and call.get('status') == 'completed'
                       and call.get('action_type') == 'search'
                       and isinstance(call.get('id'), str)
                       and isinstance(call.get('source_urls'), list) and call['source_urls']]
    bound_calls = [call for call in completed_calls
                   if call['id'] == execution['search_receipt_id']]
    if len(bound_calls) != 1:
        raise ValueError('search receipt ID does not identify one completed web search call')
    final_attempt_calls = final_attempt.get('web_search_calls')
    if not isinstance(final_attempt_calls, list):
        raise ValueError('final attempt has no web search call records')
    bound_attempt_calls = [call for call in final_attempt_calls if isinstance(call, dict)
                           and call.get('id') == execution['search_receipt_id']
                           and call.get('status') == 'completed'
                           and call.get('action_type') == 'search'
                           and isinstance(call.get('source_urls'), list) and call['source_urls']]
    if len(bound_attempt_calls) != 1:
        raise ValueError('final attempt does not contain the receipt-linked completed search call')
    if bound_attempt_calls[0] != bound_calls[0]:
        raise ValueError('final attempt and scan envelope search call records differ')
    search_urls = bound_calls[0]['source_urls']
    if (len(search_urls) != len(set(search_urls))
            or any(not valid_url(url) for url in search_urls)
            or not set(search_urls) <= set(source_urls)):
        raise ValueError('bound search call sources do not match the execution receipt')
    evidence_urls = {item['url'] for item in content['evidence']}
    if evidence_urls and not evidence_urls <= set(search_urls):
        raise ValueError('answer evidence is not bound to the receipt-linked search sources')
    if content['status'] == 'scored':
        if not evidence_urls:
            raise ValueError('answer evidence is not bound to the receipt-linked search sources')
    return source_urls


def normalize_screening(manifest, bundle):
    """Import Q01-Q03 output without converting raw claims into legacy accepted_ids."""
    if manifest.get('answer_format') != 'screening-1' or manifest.get('screening_protocol_version') != SCREENING_PROTOCOL_VERSION:
        raise ValueError('screening-1 manifest required; legacy strict uses normalize()')
    if not isinstance(bundle, dict) or bundle.get('schema_version') != 'invest-quick-scan.screening-import/1.0.0':
        raise ValueError('screening import bundle schema is missing or unsupported')
    if bundle.get('manifest_sha256') != _stable_sha256(manifest):
        raise ValueError('screening bundle belongs to another manifest')
    questions = manifest.get('questions')
    if not isinstance(questions, list) or not questions:
        raise ValueError('screening manifest has no questions')
    expected_input_hashes = {q['id']: hashlib.sha256(q['prompt'].encode('utf-8')).hexdigest()
                             for q in questions}
    if bundle.get('input_question_sha256') != expected_input_hashes:
        raise ValueError('screening input questions differ from the manifest')
    profile = manifest.get('profile', {})
    entity_id = profile.get('entity_id')
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValueError('screening requires a verified profile entity_id')
    cutoff = profile.get('as_of')
    date.fromisoformat(cutoff)
    result = bundle.get('result')
    if not isinstance(result, dict) or result.get('schema_version') != 'stockqa.quick_scan_result/1.0.0':
        raise ValueError('StockQA quick-scan result schema is missing or unsupported')
    entity = result.get('entity')
    if (not isinstance(entity, dict) or entity.get('entity_id') != entity_id
            or entity.get('name') != profile.get('company')):
        raise ValueError('StockQA result entity does not match the manifest')
    _screening_timestamp(result.get('observed_at'), 'observed_at')
    answers, receipts = result.get('answers'), result.get('execution_receipts')
    if not isinstance(answers, dict) or not isinstance(receipts, dict):
        raise ValueError('StockQA result requires answers and execution_receipts objects')
    known = {q['id']: q for q in questions}
    if set(answers) - set(known) or set(receipts) - set(known) or set(receipts) != set(answers):
        raise ValueError('StockQA question IDs and execution receipt IDs must match the manifest')
    mappings = validate_manifest_metric_contract(manifest)
    records, issued_receipts = [], {}
    for qid, question in known.items():
        answer, execution = answers.get(qid), receipts.get(qid)
        mapping = mappings[qid]
        aggregation = 'diagnostic' if mapping['aggregation_role'] == 'diagnostic_only' else question.get('aggregation', 'scored')
        record = {k: question[k] for k in ('id', 'dimension', 'question', 'module_id')}
        record.update({k: question[k] for k in ('metric_id', 'construct_id', 'comparison_role', 'rubric_version', 'scope') if k in question})
        record.update({'aggregation': aggregation, 'critical': mapping['critical_risk'],
                       'reported_score': None, 'reported_status': None, 'score': None,
                       'status': 'missing', 'screening_status': 'missing',
                       'formal_research_status': 'not_accepted', 'check_level': 'unverified_model_output',
                       'check_level_receipt_id': None, 'confidence': None,
                       'information_as_of': None, 'period_start': None, 'period_end': None})
        if answer is None:
            records.append(record)
            continue
        if not isinstance(answer, dict):
            answer = {}
        record['reported_score'] = answer.get('score')
        record['reported_status'] = answer.get('status')
        record['answer'] = answer
        record['execution'] = execution
        try:
            if answer.get('question_id') != qid:
                raise ValueError('answer question ID does not match its manifest key')
            status, reported_score = answer.get('status'), answer.get('score')
            if status not in SCREENING_STATUSES:
                raise ValueError('invalid upstream answer status')
            if status == 'scored':
                if type(reported_score) is not int or not 1 <= reported_score <= 10:
                    raise ValueError('scored upstream answer requires a strict 1-10 integer')
            elif reported_score is not None:
                raise ValueError('non-scored upstream answer must have a null score')
            content = _parse_screening_content(question, answer, cutoff)
            if content['status'] != status or content['score'] != reported_score:
                raise ValueError('inner and outer status/score do not match')
            source_urls = _check_screening_execution(
                answer, execution, content, result, cutoff, expected_input_hashes[qid]
            )
            if status == 'scored' and answer.get('information_as_of') not in (None, cutoff):
                raise ValueError('upstream information date differs from the manifest cutoff')
            if answer.get('source_urls') is not None and (
                    not isinstance(answer['source_urls'], list)
                    or set(answer['source_urls']) != set(source_urls)):
                raise ValueError('answer and execution source URL lists differ')
            published_date = _screening_date(answer.get('published_date'), 'published_date', cutoff,
                                              allow_null=True)
            observation_id = 'screen_' + _stable_sha256(
                {'manifest_sha256': bundle['manifest_sha256'], 'question_id': qid,
                 'answer': answer, 'execution': execution})[:32]
            receipt_id, trusted_receipt = _screening_receipt(entity_id, qid, observation_id)
            parsed = {'question_id': qid, 'status': status, 'score': reported_score,
                      'description': content['rationale'], 'source_urls': source_urls,
                      'published_date': published_date,
                      'information_as_of': content['information_as_of'],
                      'check_level': 'screening_audited', 'check_level_receipt_id': receipt_id}
            from contract_validation import validate_parsed_answer
            validate_parsed_answer(parsed, trusted_check_level_receipts={receipt_id: trusted_receipt},
                                   expected_entity_id=entity_id, expected_observation_id=observation_id)
            issued_receipts[receipt_id] = trusted_receipt
            record.update({'screening_status': 'screening_checked', 'check_level': 'screening_audited',
                           'check_level_receipt_id': receipt_id, 'confidence': content['confidence'],
                           'information_as_of': content['information_as_of'],
                           'period_start': content['period_start'], 'period_end': content['period_end'],
                           'answer_content': content, 'observation_id': observation_id})
            if status == 'scored' and content['confidence'] == 'low':
                record.update({'status': 'low_confidence', 'score': None})
            elif status == 'scored':
                record.update({'status': 'scored', 'score': reported_score})
            elif status == 'not_applicable':
                record.update({'status': 'unknown', 'score': None,
                               'screening_status': 'needs_na_review', 'is_audited_na': False})
            else:
                record.update({'status': status, 'score': None})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            record.update({'status': 'unknown', 'score': None, 'screening_status': 'unusable',
                           'screening_error': str(exc)})
        records.append(record)
    summary = summarize(records, manifest.get('aggregation_policy', 'legacy-all-questions'))
    checked_count = len(issued_receipts)
    provenance_status = ('screening_checked' if checked_count == len(questions)
                         else 'partially_checked' if checked_count else 'unusable')
    return {'schema_version': 'screening-1.0.0', 'profile': profile, 'mode': manifest['mode'],
            'provenance_status': provenance_status,
            'observed_at': result['observed_at'], 'questions': records, 'summary': summary,
            'check_level_receipts': issued_receipts,
            'missing_question_ids': [q['id'] for q in questions if q['id'] not in answers],
            'recovery_watch': recovery_watch(records, manifest, summary),
            'formal_research_status': 'not_accepted',
            'notice': 'screening分数仅供海选；正式深研接受和原文事实审核仍由各自拥有者完成。'}


def normalize(manifest, answers, review=None):
    if manifest.get('answer_format') == 'screening-1':
        if review is not None:
            raise ValueError('screening-1 uses execution checks, never legacy accepted_ids review')
        return normalize_screening(manifest, answers)
    if manifest.get('answer_format') == 'standard-1':
        raise ValueError('standard answers require standard_answers.py build with execution receipts')
    if not isinstance(answers, dict):
        raise ValueError('answers must map exact exported question strings to score/description')
    authoritative_mappings = validate_manifest_metric_contract(manifest)
    review = review or {}
    profile = manifest['profile']
    accepted = review.get('accepted_ids', [])
    if not isinstance(accepted, list) or not all(isinstance(v, str) for v in accepted):
        raise ValueError('accepted_ids must be a list of question IDs')
    known = {q['id'] for q in manifest['questions']}
    if set(accepted) - known or len(accepted) != len(set(accepted)):
        raise ValueError('duplicate or unknown accepted ID')
    if accepted and (review.get('company') != profile['company'] or review.get('as_of') != profile['as_of']):
        raise ValueError('review company/cutoff mismatch')
    search_verified = review.get('search_verified') is True and bool(review.get('search_basis'))
    records = []
    for q in manifest['questions']:
        record = {k: q[k] for k in ('id', 'dimension', 'question', 'module_id')}
        record.update({k: q[k] for k in ('metric_id', 'construct_id', 'comparison_role', 'rubric_version', 'scope') if k in q})
        mapping = authoritative_mappings.get(q['id']) if authoritative_mappings else None
        aggregation = ('diagnostic' if mapping and mapping['aggregation_role'] == 'diagnostic_only'
                       else q.get('aggregation', 'scored'))
        critical = mapping['critical_risk'] if mapping else q.get('critical', False)
        record.update({'aggregation': aggregation, 'score': None,
                       'critical': critical, 'reported_score': None, 'status': 'missing'})
        raw = answers.get(q['prompt'])
        if raw is not None:
            try:
                parsed = parse_answer(q, raw, profile['as_of'])
                record['answer'] = parsed
                record['reported_score'] = parsed['score']
                status = parsed['status']
                if status in ('scored', 'not_applicable'):
                    if q['id'] not in accepted or not search_verified:
                        status = 'review_pending'
                    elif status == 'scored' and parsed['confidence'] == 'low':
                        status = 'low_confidence'
                record['status'] = status
                if status == 'scored':
                    record['score'] = parsed['score']
            except (ValueError, TypeError, KeyError) as exc:
                record.update({'status': 'invalid', 'error': str(exc)})
        records.append(record)
    expected_prompts = {q['prompt'] for q in manifest['questions']}
    summary = summarize(records, manifest.get('aggregation_policy', 'legacy-all-questions'))
    return {'schema_version': manifest.get('schema_version', '2.1'), 'profile': profile, 'mode': manifest['mode'],
            'provenance_status': 'legacy_unattributed', 'model': None, 'answered_at': None,
            'template_version': manifest.get('template_version', 'unknown'),
            'search_verified': search_verified, 'questions': records, 'summary': summary,
            'recovery_watch': recovery_watch(records, manifest, summary),
            'unexpected_answer_count': len(set(answers) - expected_prompts),
            'limitation': '分数取决于已审核证据和所选模板，不是跨行业排名或买卖建议。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    common = sub.add_parser('common')
    common.add_argument('--output', required=True)
    routing = sub.add_parser('routing')
    for key in ('company', 'ticker', 'exchange', 'as-of', 'output'):
        routing.add_argument('--' + key, required=True)
    compile_cmd = sub.add_parser('compose')
    compile_cmd.add_argument('--profile', required=True)
    compile_cmd.add_argument('--mode', choices=('quick', 'full'), default='quick')
    compile_cmd.add_argument('--out-dir', required=True)
    compile_cmd.add_argument('--answer-format', choices=('legacy', 'standard-1', 'screening-1'), default='legacy')
    compile_cmd.add_argument('--module-package-id')
    compile_cmd.add_argument('--route-decision')
    compile_cmd.add_argument('--max-questions', type=int)
    compile_cmd.add_argument('--now-utc')
    compile_cmd.add_argument('--expected-route-decision-id')
    sub.add_parser('publish-modules')
    publish_routing = sub.add_parser('publish-routing')
    publish_routing.add_argument('--activate', action='store_true')
    route_request = sub.add_parser('routing-v2-request')
    for key in ('identity', 'module-package-id', 'out-dir'):
        route_request.add_argument('--' + key, required=True)
    route_resolve = sub.add_parser('resolve-route')
    for key in ('input', 'module-package-id', 'now-utc', 'output'):
        route_resolve.add_argument('--' + key, required=True)
    for key in ('candidate', 'execution-receipt', 'user-policy', 'previous-decision'):
        route_resolve.add_argument('--' + key)
    route_resolve.add_argument('--expected-previous-decision-id')
    route_compose = sub.add_parser('compose-route')
    for key in ('route-decision', 'now-utc', 'expected-route-decision-id', 'out-dir'):
        route_compose.add_argument('--' + key, required=True)
    route_compose.add_argument('--answer-format', choices=('legacy', 'standard-1', 'screening-1'), default='screening-1')
    route_compose.add_argument('--max-questions', type=int)
    norm = sub.add_parser('normalize')
    for key in ('manifest', 'answers', 'output'):
        norm.add_argument('--' + key, required=True)
    norm.add_argument('--review')
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            result = validate_library()
            if (ROOT / 'questions/releases/current.json').exists():
                package, released_modules, release, _ = module_registry.load_current(root=ROOT)
                result.update({'published_package_id': package['package_id'],
                               'published_release_id': release['release_id'],
                               'published_modules': len(released_modules)})
        elif args.command == 'common':
            _, modules = load_library()
            questions = modules['common']['questions']
            questions = sorted(questions, key=lambda q: q['id'])
            write_json(args.output, export_questions(questions))
            result = {'questions': len(questions), 'output': args.output}
        elif args.command == 'routing':
            write_json(args.output, routing_question(args.company, args.ticker, args.exchange, args.as_of))
            result = {'output': args.output}
        elif args.command == 'compose':
            result = compose(read_json(args.profile), args.mode, args.out_dir, args.answer_format,
                             package_id=args.module_package_id,
                             route_decision=module_registry._read_json(Path(args.route_decision)) if args.route_decision else None,
                             max_questions=args.max_questions, now_utc=args.now_utc,
                             expected_route_decision_id=args.expected_route_decision_id)
        elif args.command == 'publish-modules':
            result = publish_library()
        elif args.command == 'publish-routing':
            import routing as route_engine
            result = route_engine.publish_routing_package(root=ROOT, renderer_version=RENDERER_VERSION,
                renderer_rules_sha256=renderer_rules_sha256(), activate=args.activate)
        elif args.command == 'routing-v2-request':
            import routing as route_engine
            request = route_engine.build_route_request(module_registry._read_json(Path(args.identity)),
                                                       package_id=args.module_package_id, root=ROOT)
            if request['request_protocol'] not in {
                    'stockqa-route-confidence-1', 'stockqa-route-confidence-2', 'stockqa-route-confidence-3'}:
                raise ValueError('candidate-only historical route protocol cannot issue native provider requests')
            output = Path(args.out_dir)
            if any((output / name).exists() for name in ('questions.json', 'route-request.json')):
                raise ValueError('routing output already exists; use a fresh directory')
            write_json(output / 'questions.json', request['questions'])
            write_json(output / 'route-request.json', request)
            result = {'question_id': 'ROUTE_02', 'prompt_sha256': request['prompt_sha256'], 'out_dir': str(output)}
        elif args.command == 'resolve-route':
            import routing as route_engine
            inputs = module_registry._read_json(Path(args.input))
            route_response = (Path(args.candidate).read_text(encoding='utf-8-sig')
                              if args.candidate else None)
            execution_receipt = (module_registry._read_json(Path(args.execution_receipt))
                                 if args.execution_receipt else None)
            result = route_engine.resolve_route_decision(inputs, package_id=args.module_package_id,
                route_response=route_response,
                execution_receipt=execution_receipt,
                user_policy=module_registry._read_json(Path(args.user_policy)) if args.user_policy else None,
                previous_decision=module_registry._read_json(Path(args.previous_decision)) if args.previous_decision else None,
                expected_previous_decision_id=args.expected_previous_decision_id,
                now_utc=args.now_utc, root=ROOT)
            if Path(args.output).exists():
                raise ValueError('route output already exists; decisions are immutable')
            write_json(args.output, result)
            result = {'decision_id': result['decision_id'], 'status': result['status'],
                      'dispatch_status': result['dispatch_plan']['status'], 'output': args.output}
        elif args.command == 'compose-route':
            result = compose_from_route(module_registry._read_json(Path(args.route_decision)), args.out_dir,
                now_utc=args.now_utc, expected_route_decision_id=args.expected_route_decision_id,
                answer_format=args.answer_format, max_questions=args.max_questions)
        else:
            output = normalize(read_json(args.manifest), read_json(args.answers),
                               read_json(args.review) if args.review else None)
            write_json(args.output, output)
            result = output['summary']
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, AssertionError, ValidationError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
