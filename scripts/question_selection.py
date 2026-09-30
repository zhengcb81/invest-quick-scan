"""Pure selection rules for composed quick-scan question modules.

The CLI and manifest validator depend on this module as a stable domain
boundary. It owns routing-to-question selection, budget trimming and release
locks; it does not own file output or answer normalization.
"""

from pathlib import Path

import module_contract
import question_library as library

ROOT = Path(__file__).resolve().parents[1]


def _select_from_module_ids(profile, mode, modules, selected_modules, mandatory_question_ids=()):
    if mode not in ('quick', 'full'):
        raise ValueError('mode must be quick or full')
    if len(selected_modules) != len(set(selected_modules)) or 'common' not in selected_modules:
        raise ValueError('selection requires one common module and no duplicates')
    if any(module_id not in modules for module_id in selected_modules):
        raise ValueError('selection contains an unpublished module')
    selected_set = set(selected_modules)
    for module_id in selected_modules:
        module = modules[module_id]
        if set(module.get('dependencies', [])) - selected_set:
            raise ValueError(f'{module_id}: missing selected dependency')
        if set(module.get('conflicts', [])) & selected_set:
            raise ValueError(f'{module_id}: selected module conflict')
    chosen = []
    for module_id in selected_modules:
        for original in modules[module_id]['questions']:
            if (mode == 'full' or original['priority'] == 1 or original.get('critical')
                    or original['id'] in mandatory_question_ids):
                chosen.append({**original, 'module_id': module_id})
    # A specialised replacement may be essential even when marked lower priority.
    chosen_ids = {q['id'] for q in chosen}
    for module_id in selected_modules:
        if modules[module_id]['kind'] != 'types':
            continue
        for q in modules[module_id]['questions']:
            if q['id'] not in chosen_ids and any(t in chosen_ids for t in q.get('replaces', [])):
                chosen.append({**q, 'module_id': module_id})
    replacements = {t: q['id'] for q in chosen for t in q.get('replaces', [])}
    if sum(len(q.get('replaces', [])) for q in chosen) != len(replacements):
        raise ValueError('selected modules replace the same core construct twice')
    common_critical = {q['id'] for q in modules['common']['questions'] if q.get('critical')}
    for q in chosen:
        if common_critical.intersection(q.get('replaces', [])):
            q['critical'] = True
    chosen = [q for q in chosen if q['id'] not in replacements]
    chosen.sort(key=lambda q: (selected_modules.index(q['module_id']), q['id']))
    return chosen, selected_modules, replacements


def select_questions(profile, mode, modules, contexts=None, *, root=None):
    library.validate_profile(profile, modules, contexts, root=Path(root) if root else ROOT)
    if mode == 'quick' and len(profile.get('overlays', [])) > 2:
        raise ValueError('more than two material overlays: use full instead of silently omitting risks')
    extensions = [module_id for module_id, module in modules.items()
                  if module['kind'] == 'common_extensions'
                  and module.get('activation', {}).get('mode') == 'automatic'
                  and not module.get('deprecated_in')]
    selected = ['common', *sorted(extensions), *sorted(profile.get('common_extension_modules', [])),
                profile['company_type'], *sorted(profile.get('industry_modules', [])), profile['stage']]
    if profile.get('cycle_sensitive'):
        selected.append('cyclical')
    selected.extend(sorted(profile.get('overlays', [])))
    selected.extend(sorted(profile.get('diagnostic_modules', [])))
    if (profile.get('recovery_review') or profile['stage'] in ('turnaround', 'declining')
            or 'distressed' in profile.get('overlays', [])):
        selected.append('recovery')
    selected.extend(sorted(profile.get('investment_lenses', [])))
    selected = list(dict.fromkeys(selected))
    return _select_from_module_ids(profile, mode, modules, selected)


def select_questions_for_route(profile, mode, modules, selected_module_ids, mandatory_question_ids=()):
    """S06 seam: a verified partial route may contain common and known risks only."""
    priority = {'common': 0, 'common_extensions': 1, 'types': 2, 'industries': 3,
                'stages': 4, 'overlays': 5, 'diagnostics': 6, 'lenses': 7}
    ordered = sorted(selected_module_ids, key=lambda module_id: (
        priority.get(modules[module_id]['kind'], 99), module_id))
    return _select_from_module_ids(profile, mode, modules, ordered, mandatory_question_ids)


def apply_question_budget(questions, maximum, mandatory_question_ids=()):
    if set(mandatory_question_ids) - {q['id'] for q in questions}:
        raise ValueError('selected questionnaire omits a mandatory routed question')
    if maximum is None:
        return questions, []
    if type(maximum) is not int or maximum < 1:
        raise ValueError('max_questions must be a positive integer')
    required = [q for q in questions if q.get('comparison_role') == 'core' or q.get('critical')
                or q['id'] in mandatory_question_ids]
    if len(required) > maximum:
        raise ValueError('question budget below mandatory core and critical-risk coverage')
    optional = [q for q in questions if q not in required]
    kept_ids = {q['id'] for q in required + optional[:maximum - len(required)]}
    kept = [q for q in questions if q['id'] in kept_ids]
    deferred = [{'question_id': q['id'], 'module_id': q['module_id'],
                 'reason': 'question_count_budget'} for q in questions if q['id'] not in kept_ids]
    return kept, deferred


def published_selection(profile, mode, modules, release, route_decision, contexts, package=None,
                        *, root=None):
    local_root = Path(root) if root else ROOT
    if route_decision is None:
        if release['schema_version'] == '2.0.0':
            raise ValueError('routing policy v2 requires a frozen route decision')
        return select_questions(profile, mode, modules, contexts, root=local_root)
    if route_decision.get('schema_version') == '2.0.0':
        import routing as route_engine

        route_engine.validate_route_snapshot(route_decision, root=local_root)
        if (package is None or route_decision['module_package_id'] != package['package_id']
                or profile != route_engine.profile_from_route(route_decision)):
            raise ValueError('route package or profile differs from frozen routing context')
        if mode != route_decision['dispatch_plan']['resolved_mode']:
            raise ValueError('requested mode differs from frozen routing dispatch')
        if route_decision['dispatch_plan']['status'] not in {'ready', 'ready_common_and_risk'}:
            raise ValueError(route_decision['dispatch_plan']['status'])
        selected = route_decision['dispatch_plan'].get('eligible_module_ids',
                    [item['module_id'] for item in route_decision['module_decisions'] if item['decision'] == 'selected'])
        return select_questions_for_route(profile, mode, modules, selected,
                                           route_decision['dispatch_plan']['mandatory_question_ids'])
    module_contract.validate_route_decision(route_decision, release)
    if route_decision['entity_id'] != profile.get('entity_id') or route_decision['as_of'] != profile.get('as_of'):
        raise ValueError('route decision identity/cutoff differs from profile')
    selected_items = [item for item in route_decision['module_decisions']
                      if item['decision'] == 'selected']
    for item in selected_items:
        module_id = item['module_id']
        if modules[module_id]['kind'] == 'lenses':
            reasons = profile.get('lens_rationale', {})
            if (item['basis'] != 'manual' or module_id not in profile.get('investment_lenses', [])
                    or not isinstance(reasons, dict) or not isinstance(reasons.get(module_id), str)
                    or not reasons[module_id].strip()):
                raise ValueError(f'{module_id}: manual lens requires explicit user selection and rationale')
    selected = [item['module_id'] for item in selected_items]
    return select_questions_for_route(profile, mode, modules, selected)


def module_locks(release, selected):
    by_id = {entry['module_id']: entry for entry in release['modules']}
    return [{key: by_id[module_id][key] for key in ('module_id', 'version', 'artifact_ref', 'artifact_sha256')}
            for module_id in selected]
