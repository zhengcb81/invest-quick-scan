"""The production composition consumes public StockQA contracts only."""
import ast
import importlib
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_OWNER_APIS = {
    'stockqa': 'stockqa.company-scan-public-api/1.5.0',
    'company_agent': 'iqs.company-agent-public-api/2.3.0',
    'agent_runtime': 'iqs.agent-runtime-public-api/1.4.0',
}


def _stockqa_imports(node):
    if isinstance(node, ast.ImportFrom):
        names = [node.module or '']
    elif isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
    else:
        names = []
    return {name for name in names if name.split('.')[0] == 'src'}


def _dynamic_import_aliases(tree):
    """Map common importlib/builtins aliases to their canonical call names."""
    modules = {"importlib": "importlib", "builtins": "builtins"}
    functions = {"__import__": "__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"importlib", "builtins"}:
                    modules[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        functions[alias.asname or alias.name] = "importlib.import_module"
            elif node.module == "builtins":
                for alias in node.names:
                    if alias.name == "__import__":
                        functions[alias.asname or alias.name] = "__import__"

    def binding(value):
        if isinstance(value, ast.Name):
            if value.id in modules:
                return "module", modules[value.id]
            if value.id in functions:
                return "function", functions[value.id]
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "getattr"
            and len(value.args) >= 2
            and isinstance(value.args[1], ast.Constant)
            and isinstance(value.args[1].value, str)
        ):
            owner = binding(value.args[0])
            member = value.args[1].value
            if owner == ("module", "importlib") and member == "import_module":
                return "function", "importlib.import_module"
            if owner == ("module", "builtins") and member == "__import__":
                return "function", "__import__"
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
            owner = modules.get(value.value.id)
            if owner == "importlib" and value.attr == "import_module":
                return "function", "importlib.import_module"
            if owner == "builtins" and value.attr == "__import__":
                return "function", "__import__"
        return None

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            resolved = binding(node.value)
            if resolved is None:
                continue
            kind, canonical = resolved
            aliases = modules if kind == "module" else functions
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and aliases.get(target.id) != canonical:
                    aliases[target.id] = canonical
                    changed = True
    return modules, functions


def _dynamic_import_name(function, modules, functions):
    if isinstance(function, ast.Name):
        return functions.get(function.id)
    if (isinstance(function, ast.Attribute) and function.attr == "import_module"
            and isinstance(function.value, ast.Name)
            and modules.get(function.value.id) == "importlib"):
        return "importlib.import_module"
    if (isinstance(function, ast.Call) and isinstance(function.func, ast.Name)
            and function.func.id == "getattr" and len(function.args) >= 2
            and isinstance(function.args[1], ast.Constant)
            and isinstance(function.args[1].value, str)):
        owner = modules.get(ast.unparse(function.args[0]))
        member = function.args[1].value
        if owner == "importlib" and member == "import_module":
            return "importlib.import_module"
        if owner == "builtins" and member == "__import__":
            return "__import__"
    return None


def _integration_imports(tree):
    """Return literal imports, including aliased importlib/__import__ calls."""
    modules = set()
    module_aliases, function_aliases = _dynamic_import_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            function = _dynamic_import_name(node.func, module_aliases, function_aliases)
            if (function in {'__import__', 'importlib.import_module'}
                    and node.args and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                modules.add(node.args[0].value)
    return modules


def _dynamic_import_calls(tree):
    module_aliases, function_aliases = _dynamic_import_aliases(tree)
    return [
        (node.lineno, _dynamic_import_name(node.func, module_aliases, function_aliases))
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _dynamic_import_name(node.func, module_aliases, function_aliases)
        in {'__import__', 'importlib.import_module'}
    ]


@pytest.mark.parametrize('filename,functions', [
    ('shared_company_engine.py', {'_production_answer_semantics',
                                '_validate_native_answer_sources', 'finalize_shared_engine'}),
    ('shared_company_task.py', {'create_company_scan_task', 'create_native_task'}),
])
def test_production_composition_does_not_reach_into_stockqa_private_objects(filename, functions):
    source = ROOT / 'scripts' / filename
    tree = ast.parse(source.read_text(encoding='utf8'))
    violations = []
    for function in tree.body:
        if not isinstance(function, ast.FunctionDef) or function.name not in functions:
            continue
        for node in ast.walk(function):
            if (isinstance(node, ast.Attribute) and node.attr.startswith('_')
                and ast.unparse(node.value) in {'services', 'services.lifecycle', 'lifecycle'}):
                violations.append((function.name, node.lineno, node.attr))
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'getattr' and len(node.args) > 1
                and ast.unparse(node.args[0]) in {'services', 'services.lifecycle', 'lifecycle'}
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str) and node.args[1].value.startswith('_')):
                violations.append((function.name, node.lineno, node.args[1].value))
    assert not violations, violations


def test_task_factory_imports_only_the_owner_company_scan_contract():
    source = ROOT / 'scripts/shared_company_task.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    foreign_modules = {
        module
        for node in ast.walk(tree)
        for module in _stockqa_imports(node)
    }
    assert foreign_modules == {'src.utils.quick_scan_company_api'}


def test_engine_uses_the_owner_port_instead_of_the_store_or_runner():
    source = ROOT / 'scripts/shared_company_engine.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    violations = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == 'services'):
            violations.append((node.lineno, node.attr))
        for module in _stockqa_imports(node) - {'src.utils.quick_scan_company_api'}:
            violations.append((node.lineno, module))
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == 'services' and node.attr in {'store', 'owner', 'lifecycle', 'questions'}):
            violations.append((node.lineno, node.attr))
    assert not violations, violations


@pytest.mark.parametrize('filename', ['shared_company_engine.py', 'shared_company_task.py'])
def test_company_composition_uses_only_versioned_public_owner_facades(filename):
    tree = ast.parse((ROOT / 'scripts' / filename).read_text(encoding='utf8'))
    modules = _integration_imports(tree)
    external = {
        name for name in modules
        if name.split('.')[0] in {'iqs_company_agent_lab', 'iqs_agent_runtime_lab', 'src'}
    }
    assert external <= {
        'iqs_company_agent_lab.api',
        'iqs_agent_runtime_lab.api',
        'src.utils.quick_scan_company_api',
    }, sorted(external)
    assert not _dynamic_import_calls(tree)


def test_company_composition_does_not_discover_peer_modules_by_file_layout():
    paths = [ROOT / 'scripts' / name for name in ('shared_company_engine.py', 'answer_validation.py')]
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf8'))
        violations.extend(
            (path.name, node.lineno, ast.unparse(node.value))
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and node.attr == '__file__'
            and ast.unparse(node.value) in {'standard_answers', 'question_prompts'}
        )
    assert not violations, violations


def test_answer_validation_peers_publish_the_versioned_semantics_used_by_the_consumer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import answer_validation
    import standard_answers
    import question_prompts
    import shared_company_engine

    assert answer_validation.API_PROTOCOL == 'iqs.answer-validation-api/1.0.0'
    assert standard_answers.ANSWER_VALIDATION_API_PROTOCOL == 'iqs.standard-answer-validation/1.0.0'
    assert question_prompts.SEMANTIC_RULES_API_PROTOCOL == 'iqs.question-prompt-semantics/1.0.0'
    assert shared_company_engine._answer_validation_api() is answer_validation


@pytest.mark.parametrize('peer', ['standard_answers', 'question_prompts'])
def test_frozen_semantics_rejects_missing_or_incompatible_collaborator_protocol(monkeypatch, peer):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import answer_validation

    standard_protocol = 'iqs.standard-answer-validation/1.0.0'
    prompt_protocol = 'iqs.question-prompt-semantics/1.0.0'
    standards = ModuleType('standard_answers')
    prompts = ModuleType('question_prompts')
    standards.ANSWER_VALIDATION_API_PROTOCOL = standard_protocol
    prompts.SEMANTIC_RULES_API_PROTOCOL = prompt_protocol
    if peer == 'standard_answers':
        standards.ANSWER_VALIDATION_API_PROTOCOL = 'iqs.standard-answer-validation/9.0.0'
    else:
        prompts.SEMANTIC_RULES_API_PROTOCOL = 'iqs.question-prompt-semantics/9.0.0'
    monkeypatch.setitem(sys.modules, 'standard_answers', standards)
    monkeypatch.setitem(sys.modules, 'question_prompts', prompts)

    with pytest.raises(answer_validation.AnswerSemanticsRejected,
                       match='original_standard_answer_validator_required'):
        answer_validation.frozen_answer_semantics(None, {}, release_root=ROOT)


def test_shared_engine_rejects_an_unsupported_answer_validation_protocol(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import answer_validation
    import shared_company_engine

    monkeypatch.setattr(answer_validation, 'API_PROTOCOL', 'iqs.answer-validation-api/9.0.0')
    with pytest.raises(shared_company_engine.SharedEngineRejected,
                       match='answer_validation_api_version_unsupported'):
        shared_company_engine._answer_validation_api()


def test_missing_owner_public_api_is_normalized_before_preflight_imports(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import builtins
    import shared_company_engine as engine

    original_import = builtins.__import__
    def fail_owner_import(name, *args, **kwargs):
        if name == 'iqs_company_agent_lab.api':
            raise ModuleNotFoundError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fail_owner_import)
    with pytest.raises(engine.SharedEngineRejected, match='company_scan_owner_api_unavailable'):
        engine.preflight(object(), object(), {})


def test_missing_stockqa_runtime_facade_is_normalized(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import builtins
    import shared_company_engine as engine

    original_import = builtins.__import__
    def fail_stockqa_import(name, *args, **kwargs):
        if name == 'src.utils.quick_scan_company_api':
            raise ModuleNotFoundError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fail_stockqa_import)
    with pytest.raises(engine.SharedEngineRejected, match='stockqa_company_runtime_api_unavailable'):
        engine._company_runtime(object())


def test_owner_api_version_negotiation_accepts_only_declared_compatible_versions(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    from shared_company_ports import (
        OwnerApiProtocolError,
        required_owner_api_protocols,
        validate_owner_api_protocols,
    )

    assert required_owner_api_protocols() == EXPECTED_OWNER_APIS
    assert validate_owner_api_protocols(EXPECTED_OWNER_APIS) == EXPECTED_OWNER_APIS
    with pytest.raises(OwnerApiProtocolError, match='owner_api_set_mismatch'):
        validate_owner_api_protocols({**EXPECTED_OWNER_APIS, 'unregistered': '1.0.0'})
    with pytest.raises(OwnerApiProtocolError, match='owner_api_version_unsupported'):
        validate_owner_api_protocols({**EXPECTED_OWNER_APIS, 'stockqa': 'stockqa.internal/9.9.9'})


def test_owner_api_version_negotiation_accepts_backward_compatible_minor_and_patch_releases():
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from shared_company_ports import validate_owner_api_protocols

    compatible = {
        'stockqa': 'stockqa.company-scan-public-api/1.6.3',
        'company_agent': 'iqs.company-agent-public-api/2.4.0',
        'agent_runtime': 'iqs.agent-runtime-public-api/1.5.12',
    }
    assert validate_owner_api_protocols(compatible) == compatible


@pytest.mark.parametrize('owner,version', [
    ('stockqa', 'stockqa.company-scan-public-api/1.1.9'),
    ('stockqa', 'stockqa.company-scan-public-api/1.4.9'),
    ('stockqa', 'stockqa.company-scan-public-api/2.0.0'),
    ('company_agent', 'iqs.company-agent-public-api/1.9.9'),
    ('company_agent', 'iqs.company-agent-public-api/2.2.9'),
    ('agent_runtime', 'iqs.agent-runtime-public-api/1.3.9'),
    ('agent_runtime', 'iqs.agent-runtime-public-api/2.0.0'),
    ('agent_runtime', 'iqs.agent-runtime-public-api/1.x.0'),
])
def test_owner_api_version_negotiation_rejects_incompatible_releases(owner, version):
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from shared_company_ports import OwnerApiProtocolError, validate_owner_api_protocols
    protocols = {**EXPECTED_OWNER_APIS, owner: version}
    with pytest.raises(OwnerApiProtocolError, match='owner_api_version_unsupported'):
        validate_owner_api_protocols(protocols)


def test_dynamic_internal_import_expression_is_detected_even_without_a_literal_module_name():
    tree = ast.parse("importlib.import_module('iqs_company_agent_lab.' + module_name)")
    assert _dynamic_import_calls(tree) == [(1, 'importlib.import_module')]


@pytest.mark.parametrize('source,expected', [
    ("from importlib import import_module as load\n"
     "load('iqs_company_agent_lab.runner')", 'iqs_company_agent_lab.runner'),
    ("import importlib as importer\n"
     "importer.import_module('iqs_agent_runtime_lab.receiptmap')",
     'iqs_agent_runtime_lab.receiptmap'),
    ("from builtins import __import__ as load\n"
     "load('src.utils.quick_scan_work_store')", 'src.utils.quick_scan_work_store'),
])
def test_aliased_dynamic_imports_are_classified_at_owner_boundaries(source, expected):
    tree = ast.parse(source)
    assert expected in _integration_imports(tree)
    assert _dynamic_import_calls(tree)


def test_assignment_aliased_importers_are_classified_at_owner_boundaries():
    source = (
        "import importlib as loader_module\n"
        "factory = loader_module.import_module\n"
        "second_factory = factory\n"
        "second_factory('src.utils.quick_scan_work_store')\n"
    )
    tree = ast.parse(source)
    assert "src.utils.quick_scan_work_store" in _integration_imports(tree)
    assert _dynamic_import_calls(tree)


def test_getattr_aliased_importers_are_classified_at_owner_boundaries():
    source = (
        "import importlib as importer\n"
        "loader = getattr(importer, 'import_module')\n"
        "module = loader('src.utils.quick_scan_work_store')\n"
        "module._hidden()\n"
    )
    tree = ast.parse(source)
    assert "src.utils.quick_scan_work_store" in _integration_imports(tree)
    assert _dynamic_import_calls(tree)


@pytest.mark.parametrize('source,expected', [
    ("import importlib as importer\ngetattr(importer, 'import_module')('src.utils.quick_scan_work_store')",
     'src.utils.quick_scan_work_store'),
    ("import builtins as loader\ngetattr(loader, '__import__')('iqs_company_agent_lab.runner')",
     'iqs_company_agent_lab.runner'),
])
def test_direct_getattr_import_calls_are_classified_at_owner_boundaries(source, expected):
    tree = ast.parse(source)
    assert expected in _integration_imports(tree)
    assert _dynamic_import_calls(tree)


def test_local_private_scanner_catches_dynamic_attribute_lookup():
    tree = ast.parse(
        "import shared_company_task as peer\ngetattr(peer, '_implementation_detail')"
    )
    assert _local_private_reference_violations(
        tree, {'peer': 'shared_company_task'}, {'shared_company_task'}
    )


def _root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.value if isinstance(node, (ast.Attribute, ast.Subscript)) else node.func
    return node.id if isinstance(node, ast.Name) else None


def _local_private_reference_violations(tree, module_aliases, local_modules,
                                        source_name='<memory>'):
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.rsplit('.', 1)[-1]
            if module in local_modules:
                for item in node.names:
                    if item.name.startswith('_'):
                        violations.append((source_name, node.lineno, module, item.name))
        elif (isinstance(node, ast.Attribute) and node.attr.startswith('_')
              and isinstance(node.value, ast.Name) and node.value.id in module_aliases):
            violations.append((source_name, node.lineno,
                               module_aliases[node.value.id], node.attr))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == 'getattr' and len(node.args) >= 2
              and isinstance(node.args[0], ast.Name)
              and node.args[0].id in module_aliases
              and isinstance(node.args[1], ast.Constant)
              and isinstance(node.args[1].value, str)
              and node.args[1].value.startswith('_')):
            violations.append((source_name, node.lineno,
                               module_aliases[node.args[0].id], node.args[1].value))
    return sorted(set(violations))


def _local_private_api_violations():
    scripts = ROOT / 'scripts'
    local_modules = {path.stem for path in scripts.glob('*.py')}
    violations = []
    for source in scripts.glob('*.py'):
        tree = ast.parse(source.read_text(encoding='utf8'))
        module_aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    root = item.name.split('.')[0]
                    if root in local_modules:
                        module_aliases[item.asname or root] = root
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.rsplit('.', 1)[-1]
                if module in local_modules:
                    for item in node.names:
                        if item.name.startswith('_'):
                            violations.append((source.name, node.lineno, module, item.name))
        violations.extend(_local_private_reference_violations(
            tree, module_aliases, local_modules, source.name
        ))
    return sorted(set(violations))


def test_iqs_script_modules_call_peer_modules_only_through_public_names():
    assert not _local_private_api_violations()


def test_company_composition_never_reads_owner_task_or_runner_implementation_fields():
    paths = (
        ROOT / 'scripts/shared_company_engine.py',
        ROOT / 'scripts/shared_company_task.py',
        ROOT / 'scripts/answer_validation.py',
    )
    implementation_fields = {
        'raw', 'questions', 'question_ids', 'company_doc', 'company_ref',
        'evidence_board_doc', 'runtime_profile', 'owner_binding', 'owner_control_binding',
        'limits', 'state', 'journal',
    }
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or node.attr not in implementation_fields:
                continue
            if _root_name(node.value) in {'task', 'runner', 'runner_ref', 'runtime'}:
                violations.append((path.name, node.lineno, ast.unparse(node)))
            if (isinstance(node.value, ast.Attribute) and node.value.attr == 'task'
                    and _root_name(node.value.value) in {'runtime', 'services'}):
                violations.append((path.name, node.lineno, ast.unparse(node)))
    assert not violations, violations


def test_company_composition_does_not_import_concrete_owner_task_or_runner_types():
    paths = (
        ROOT / 'scripts/shared_company_engine.py',
        ROOT / 'scripts/shared_company_task.py',
        ROOT / 'scripts/answer_validation.py',
    )
    forbidden = {'LoadedTask', 'Runner', 'EventJournal', 'RuntimeBridgePort'}
    violations = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name in forbidden:
                        violations.append((path.name, node.lineno, node.module, alias.name))
    assert not violations, violations


def test_shared_engine_capabilities_report_consumer_minimum_versions_without_provider_imports(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import shared_company_engine as engine
    import shared_company_ports

    declared = {
        'stockqa': 'stockqa.company-scan-public-api/9.1.0',
        'company_agent': 'iqs.company-agent-public-api/9.2.0',
        'agent_runtime': 'iqs.agent-runtime-public-api/9.3.0',
    }
    monkeypatch.setattr(shared_company_ports, 'required_owner_api_protocols', lambda: declared)

    result = engine.capabilities()

    assert result['required_owner_api_protocols'] == declared
    assert result['protocol'] == 'iqs.shared-company-engine/1.0.0'
    # V1 capability fields remain as legacy-profile metadata for existing
    # StockQA readers; they are not the admission rule for generic task DTOs.
    assert result['registered_question_count'] == 12
    assert result['registered_cutoff'] == '2026-10-13'
    assert result['question_pack_provider'] == 'mimo'
    assert {'original_Runner', 'original_RuntimeBridgePort'} <= set(result['requires'])


def test_preflight_uses_task_scope_not_legacy_question_count_or_cutoff(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    engine = importlib.import_module('shared_company_engine')

    def package(name):
        value = ModuleType(name)
        value.__path__ = []
        monkeypatch.setitem(sys.modules, name, value)
        return value

    package('iqs_company_agent_lab')
    company_api = ModuleType('iqs_company_agent_lab.api')
    company_api.task_pack_sizes = lambda _task: [2, 1]
    monkeypatch.setitem(sys.modules, 'iqs_company_agent_lab.api', company_api)

    package('iqs_agent_runtime_lab')
    runtime_api = ModuleType('iqs_agent_runtime_lab.api')
    runtime_api.validate_session_config = lambda _config: config
    monkeypatch.setitem(sys.modules, 'iqs_agent_runtime_lab.api', runtime_api)

    package('src')
    package('src.utils')
    stockqa_api = ModuleType('src.utils.quick_scan_company_api')
    monkeypatch.setitem(sys.modules, 'src.utils.quick_scan_company_api', stockqa_api)

    contract = {
        'protocol': 'iqs.company-agent-task-contract/1.1.0',
        'company_doc': {'origin': 'owner_public'},
        'owner_binding': {'entity_id': 'entity:test'},
        'raw': {
            'protocol': 'iqs.company-agent-task/1.0.0',
            'information_cutoff': '2026-11-09',
        },
        'question_ids': ['Q_A', 'Q_B', 'Q_C'],
    }
    controls = []
    runtime = SimpleNamespace(
        model='mimo-v2.6-flash',
        provider='mimo',
        has_native_session=lambda: False,
        supports_intent_recovery=lambda: True,
        attempt_observations=lambda **kwargs: [],
        check_admission=lambda: None,
        assert_execution_controls=lambda **kwargs: controls.append(kwargs),
    )
    config = {
        'logical_clock': False,
        'planned_model': 'mimo-v2.6-flash',
        'max_output_tokens': 4096,
    }
    service = object()

    monkeypatch.setattr(engine, '_current_owner_api_protocols', lambda: {})
    monkeypatch.setattr(engine, '_task_contract', lambda _task: contract)
    monkeypatch.setattr(engine, '_production_answer_semantics', lambda *_args: None)
    stockqa_api.create_company_research_runtime = lambda actual_service, *, task_contract: (
        runtime if actual_service is service and task_contract is contract
        else pytest.fail('owner facade must receive the original service and task DTO')
    )

    assert engine.preflight(object(), service, {}) == config
    assert controls == [{
        'pack_size': 2,
        'thinking_enabled': True,
        'max_output_tokens': 4096,
    }]
