"""The production composition consumes public StockQA contracts only."""
import ast
import importlib
import re
import subprocess
import sys
import textwrap
from types import ModuleType, SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_OWNER_APIS = {
    'stockqa': 'stockqa.company-scan-public-api/1.7.0',
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
    functions = {"__import__": "__import__", "vars": "builtins.vars"}
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
                    if alias.name in {"__import__", "vars"}:
                        functions[alias.asname or alias.name] = (
                            "__import__" if alias.name == "__import__" else "builtins.vars")

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
            if owner == ("module", "builtins") and member == "vars":
                return "function", "builtins.vars"
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
            owner = modules.get(value.value.id)
            if owner == "importlib" and value.attr == "import_module":
                return "function", "importlib.import_module"
            if owner == "builtins" and value.attr == "__import__":
                return "function", "__import__"
            if owner == "builtins" and value.attr == "vars":
                return "function", "builtins.vars"
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
        if owner == "builtins" and member == "vars":
            return "builtins.vars"
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


@pytest.mark.parametrize('filename', ['shared_company_engine.py', 'shared_company_task.py'])
def test_company_composition_never_reads_raw_owner_state(filename):
    tree = ast.parse((ROOT / 'scripts' / filename).read_text(encoding='utf8'))
    forbidden = {'input_raw', 'bundle', 'entries', 'plan', 'proof'}
    violations = [
        (node.lineno, node.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in forbidden
    ]
    assert not violations, violations


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

    assert answer_validation.API_PROTOCOL == 'iqs.answer-validation-api/1.1.0'
    assert 'project_original_semantic_resources' in answer_validation.PUBLIC_API_EXPORTS
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
        'stockqa': 'stockqa.company-scan-public-api/1.7.3',
        'company_agent': 'iqs.company-agent-public-api/2.4.0',
        'agent_runtime': 'iqs.agent-runtime-public-api/1.5.12',
    }
    assert validate_owner_api_protocols(compatible) == compatible


@pytest.mark.parametrize(
    "missing_operation",
    [
        "task_bundle",
        "ensure_safe_output_dir",
        "check_citation_closure",
        "AnswerRejection",
        "parse_answers_payload",
        "loads",
    ],
)
def test_owner_api_version_does_not_admit_facade_missing_required_operation(
    monkeypatch, missing_operation
):
    """Compatible version metadata cannot replace base execution operations."""
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import shared_company_ports as ports

    facades = {
        'src.utils.quick_scan_company_api': ModuleType('stockqa_api'),
        'iqs_company_agent_lab.api': ModuleType('company_agent_api'),
        'iqs_agent_runtime_lab.api': ModuleType('agent_runtime_api'),
    }
    protocol_key = {
        'src.utils.quick_scan_company_api': 'stockqa',
        'iqs_company_agent_lab.api': 'company_agent',
        'iqs_agent_runtime_lab.api': 'agent_runtime',
    }
    owner_key = {
        'src.utils.quick_scan_company_api': 'stockqa',
        'iqs_company_agent_lab.api': 'company_agent',
        'iqs_agent_runtime_lab.api': 'agent_runtime',
    }
    for module_name, module in facades.items():
        module.PUBLIC_API_PROTOCOL = EXPECTED_OWNER_APIS[protocol_key[module_name]]
        required = ports.REQUIRED_OWNER_API_OPERATIONS[owner_key[module_name]]
        module.__all__ = ['PUBLIC_API_PROTOCOL', *required]
        for operation in required:
            setattr(module, operation, lambda: None)

    # Keep the declared protocol compatible while one ordinary execute
    # operation is absent from both the advertised and callable surface.
    company_agent = facades['iqs_company_agent_lab.api']
    company_agent.__all__.remove(missing_operation)
    delattr(company_agent, missing_operation)
    for module_name, module in facades.items():
        monkeypatch.setitem(sys.modules, module_name, module)
    with pytest.raises(ports.OwnerApiProtocolError,
                       match='company_scan_owner_api_operation_unavailable'):
        ports.current_owner_api_protocols()


def test_company_agent_required_operations_match_direct_engine_imports(monkeypatch):
    """Every ordinary-engine facade import is required before execution."""
    import ast

    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import shared_company_ports as ports

    tree = ast.parse((ROOT / 'scripts' / 'shared_company_engine.py').read_text(encoding='utf8'))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == 'iqs_company_agent_lab.api'
        for alias in node.names
    }
    feature_local = {
        # Cold resume, explicit finalization, and report generation are separate
        # entry points. Saved-boundary signaling is loaded only by replay-only.
        'RecoveryMismatch',
        'load_verified_recovery',
        'reconcile_saved_receipt',
        'continue_runner_port',
        'recovery_event_journals',
        'recovery_projection',
        'read_verified_answer_export',
        'generate_report',
        'raise_saved_response_boundary',
    }
    standard_execute_imports = imported - feature_local
    required = set(ports.REQUIRED_OWNER_API_OPERATIONS['company_agent'])
    assert standard_execute_imports == required


def test_official_native_runner_isolates_relative_logs_and_guards_nested_python(tmp_path):
    """The runner's temporary network boundary reaches child interpreters too."""
    import sys
    (tmp_path / 'mini' / 'tests').mkdir(parents=True)
    mini_root = tmp_path / 'mini'
    (mini_root / 'tests' / 'test_nested_process.py').write_text(
        '''import subprocess, sys
from pathlib import Path

def test_nested_python_network_guard_and_relative_log_dir():
    script = r"""
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.settimeout(1)
    sock.connect(('203.0.113.10', 80))
except RuntimeError as error:
    print('BLOCKED:' + str(error))
else:
    raise SystemExit('NETWORK_GUARD_MISSING')
loopback = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    loopback.settimeout(1)
    loopback.connect(('127.0.0.1', 1))
except OSError:
    print('LOOPBACK_ALLOWED')
else:
    print('LOOPBACK_ALLOWED')
"""
    child = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True,
                           text=True, timeout=15)
    assert child.returncode == 0, child.stdout + child.stderr
    assert 'BLOCKED:offline_test_network_forbidden' in child.stdout
    assert 'LOOPBACK_ALLOWED' in child.stdout
    logs = Path.cwd() / 'logs'
    logs.mkdir(exist_ok=True)
    (logs / 'stockqa-relative.log').write_text('isolated')
''', encoding='utf8')
    reports = tmp_path / 'reports'
    reports.mkdir()
    sys.path.insert(0, str(ROOT / 'scripts'))
    import run_tests

    result = run_tests.run_group(mini_root, 'native', ['test_nested_process.py'], reports)
    assert result['exit_code'] == 0, (reports / 'native.log').read_text(encoding='utf8')
    assert result['temporary_root_removed'] is True
    assert result['external_network_denied_in_subprocesses'] is True
    assert result['stockqa_relative_logs_isolated'] is True
    assert not (mini_root / 'logs').exists()


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


def _cross_domain_public_api_violations(tree, source_name, domains, facade_exports,
                                        allowed_edges, local_modules=None):
    """Require cross-domain calls to use an explicitly declared public facade.

    Same-domain implementation modules may collaborate internally. A boundary
    crossing must be listed by source module and target facade, and every used
    operation must be both allowlisted and exported by that facade.
    """
    source_module = Path(source_name).stem
    source_domain = domains.get(source_module)
    if source_domain is None:
        if source_module in (set(domains) if local_modules is None else set(local_modules)):
            return [(source_name, source_module, '<module>', 'local_source_unclassified')]
        return []
    local_modules = set(domains) if local_modules is None else set(local_modules)

    imported = {}
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            target = node.module.rsplit('.', 1)[-1]
            if target in local_modules and target not in domains:
                violations.append((source_name, target, '<module>', 'local_target_unclassified'))
                continue
            if target not in local_modules or domains[target] == source_domain:
                continue
            symbols = {item.name for item in node.names}
            imported.setdefault(target, set()).update(symbols)
        elif isinstance(node, ast.Import):
            for item in node.names:
                target = item.name.rsplit('.', 1)[-1]
                if target in local_modules and target not in domains:
                    violations.append((source_name, target, '<module>', 'local_target_unclassified'))
                    continue
                if target not in local_modules or domains[target] == source_domain:
                    continue
                imported.setdefault(target, set())
                imported[target].add("<module>")

    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                target = item.name.rsplit('.', 1)[-1]
                if target in imported:
                    aliases[item.asname or item.name.split('.')[0]] = target
        elif isinstance(node, ast.ImportFrom) and node.module:
            target = node.module.rsplit('.', 1)[-1]
            if target in imported:
                for item in node.names:
                    aliases[item.asname or item.name] = (target, item.name)

    ambiguous_alias = object()

    def imported_object(value):
        if isinstance(value, ast.Name):
            return aliases.get(value.id)
        if isinstance(value, ast.Call):
            return imported_object(value.func)
        if isinstance(value, ast.IfExp):
            branches = (imported_object(value.body), imported_object(value.orelse))
            known = [branch for branch in branches if branch is not None]
            if not known:
                return None
            if all(branch == known[0] for branch in known) and len(known) == len(branches):
                return known[0]
            return ambiguous_alias
        if isinstance(value, ast.Attribute):
            parent = imported_object(value.value)
            if parent is ambiguous_alias:
                return ambiguous_alias
            if isinstance(parent, str) and parent in imported:
                return (parent, value.attr)
            if isinstance(parent, tuple):
                return (parent[0], f'{parent[1]}.{value.attr}')
        return None

    # Carry imported module and public-object aliases through ordinary
    # assignments (``alias = peer`` and ``service = peer.Service``).
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            resolved = imported_object(value)
            if resolved is None:
                continue
            for target_node in targets:
                if not isinstance(target_node, ast.Name):
                    continue
                existing = aliases.get(target_node.id)
                if existing is None:
                    aliases[target_node.id] = resolved
                    changed = True
                elif existing is not ambiguous_alias and existing != resolved:
                    aliases[target_node.id] = ambiguous_alias
                    changed = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            target = imported_object(node.value)
            if isinstance(target, str) and target in imported:
                imported[target].add(node.attr)
            elif isinstance(target, tuple) and node.attr.startswith('_'):
                violations.append((source_name, target[0], target[1] + '.' + node.attr,
                                   'private_api_member_access_forbidden'))
            elif target is ambiguous_alias:
                violations.append((source_name, '<ambiguous>', ast.unparse(node.value),
                                   'ambiguous_imported_alias'))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == 'getattr' and len(node.args) >= 2
              and isinstance(node.args[1], ast.Constant)
              and isinstance(node.args[1].value, str)):
            target = imported_object(node.args[0])
            if isinstance(target, str) and target in imported:
                imported[target].add(node.args[1].value)
            elif isinstance(target, tuple) and node.args[1].value.startswith('_'):
                violations.append((source_name, target[0],
                                   target[1] + '.' + node.args[1].value,
                                   'private_api_member_access_forbidden'))
            elif target is ambiguous_alias:
                violations.append((source_name, '<ambiguous>', ast.unparse(node.args[0]),
                                   'ambiguous_imported_alias'))

    module_aliases, function_aliases = _dynamic_import_aliases(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Reading a peer module's namespace bypasses the declared export list
        # even when the caller never spells the private attribute in source.
        if (_dynamic_import_name(node.func, module_aliases, function_aliases) == 'builtins.vars'
                and node.args):
            target = imported_object(node.args[0])
            if isinstance(target, str) and target in imported:
                violations.append((source_name, target, '<module_namespace>',
                                   'module_namespace_reflection_forbidden'))
            elif isinstance(target, tuple):
                violations.append((source_name, target[0], '<module_namespace>',
                                   'module_namespace_reflection_forbidden'))
            elif target is ambiguous_alias:
                violations.append((source_name, '<ambiguous>', '<module_namespace>',
                                   'ambiguous_imported_alias'))
        dynamic_name = _dynamic_import_name(node.func, module_aliases, function_aliases)
        if dynamic_name not in {'__import__', 'importlib.import_module'}:
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            violations.append((source_name, '<dynamic>', '<dynamic_import>',
                               'dynamic_import_target_must_be_literal'))
            continue
        imported_name = node.args[0].value.rsplit('.', 1)[-1]
        if imported_name in local_modules and imported_name not in domains:
            violations.append((source_name, imported_name, '<dynamic_import>',
                               'local_target_unclassified'))
        elif imported_name in domains and domains[imported_name] != source_domain:
            violations.append((source_name, imported_name, '<dynamic_import>',
                               'cross_domain_dynamic_import_forbidden'))

    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'getattr' and len(node.args) >= 2
                and not (isinstance(node.args[1], ast.Constant)
                         and isinstance(node.args[1].value, str))):
            target = imported_object(node.args[0])
            if isinstance(target, tuple):
                target = target[0]
            if target in imported:
                violations.append((source_name, target, '<dynamic_getattr>',
                                   'dynamic_public_lookup_forbidden'))
            elif target is ambiguous_alias:
                violations.append((source_name, '<ambiguous>', '<dynamic_getattr>',
                                   'ambiguous_imported_alias'))

    for target, symbols in imported.items():
        exports = set(facade_exports.get(target, ()))
        outer_layers = {'application', 'experiments', 'acceptance'}
        allowed = (exports if source_domain in outer_layers or domains.get(target) == 'foundation'
                   else set(allowed_edges.get((source_module, target), ())))
        for symbol in sorted(symbols):
            if symbol == '<module>':
                if not allowed:
                    violations.append((source_name, target, symbol, 'edge_not_declared'))
                continue
            if symbol not in allowed:
                violations.append((source_name, target, symbol, 'operation_not_declared'))
            elif symbol not in exports:
                violations.append((source_name, target, symbol, 'operation_not_exported'))
    return sorted(set(violations))


_SCRIPTS = ROOT / 'scripts'
# This inventory is deliberately explicit: adding a script without assigning
# it to a layer fails the architecture suite instead of silently defaulting.
EXPECTED_SCRIPT_MODULES = frozenset('''
accuracy_assessment accuracy_followup accuracy_pilot accuracy_report answer_validation
applic_llm_compare applic_llm_probe applic_pipeline_check bank_lint bank_manifest_preflight
batching_benchmark_archive batching_benchmark_report batching_benchmark c06_authority
company_agent_contrast_launcher company_agent_contrast company_agent_research_pilot
compose_company_bank contract_validation coverage_gaps dashboard_batches
dashboard_company_projection dashboard_delivery_jobs dashboard_delivery dashboard_errors
dashboard_execution dashboard_http dashboard_iqs_link dashboard_job_facade dashboard_jobs
dashboard_json dashboard_locks dashboard_membership_request dashboard_owner dashboard_prepare
dashboard_service dashboard_temporal deepseek_search_client deployment_contract exchange_contract
facts_authority_build facts_authority_check facts_compose facts_context_build facts_context_check
facts_pack_check facts_pack_page facts_registry financial_mechanical_check frozen_release_projection
g0_candidate_manifest handoff_reference_check identity_contract_cli implementation_plan json_io
metric_coordinates mimo_json_mode_probe mimo_pilot_extension mimo_pilot_results
mimo_pilot_review_summary mimo_pro_pilot model_config model_invocation provider_transport
model_policy module_contract module_registry
observation_import_preflight observation_profiles observation_provenance_check one_click
open_dashboard owner_admission_subject owner_job_cli parallel_handoff_cli pipeline_review_apply
pipeline_review_pack profile_page profile_readiness query_capabilities_contract
query_capabilities_vendor_contract query_contract_cli query_contract query_facts_contract
query_field_assessment query_pool_assessment_contract query_pool_contract query_pool_scope_contract
query_research_contract query_review_lead_contract query_vendor_contract question_bank
question_fingerprints question_library question_manifest question_prompts question_selection
question_sets refresh_contract_cli refresh_contract roster_status route_store_handoff routing_contract
routing run_answers_page run_tests scan_result_check scan_summary scoring_rubrics
search_checkpoint_binding search_exposure_binding search_exposure_contract search_receipt
shared_company_engine shared_company_ports shared_company_task standard_answers status_report
stockqa_adapter stockwiki_g2b_acceptance stockwiki_mapping_contract subject_context_export
subject_dispatch_cli subject_dispatch_contract task_receipts thin_analyze thin_compare thin_median
thin_retest thin_scan verified_evidence_audit view_quick_scan work_contract
workbench_snapshot_cli workbench_snapshot zai_route_diagnostic
'''.split())

APPLICATION_MODULES = frozenset('''
bank_lint bank_manifest_preflight compose_company_bank coverage_gaps deployment_contract
facts_authority_build facts_authority_check facts_compose facts_context_build facts_context_check
facts_pack_check facts_pack_page facts_registry financial_mechanical_check identity_contract_cli
implementation_plan model_policy observation_provenance_check one_click pipeline_review_apply
profile_page profile_readiness refresh_contract_cli roster_status route_store_handoff
run_answers_page run_tests scan_result_check scan_summary scoring_rubrics status_report
thin_analyze thin_compare thin_median thin_retest thin_scan
'''.split())

DOMAIN_MODULES = {name: 'application' for name in APPLICATION_MODULES}
DOMAIN_MODULES.update({
    **{name: 'question_bank' for name in {
        'question_bank', 'question_fingerprints', 'question_library', 'question_manifest',
        'question_prompts', 'question_selection', 'question_sets', 'module_registry',
        'routing', 'routing_contract', 'metric_coordinates', 'standard_answers',
        'stockqa_adapter', 'frozen_release_projection',
    }},
    'answer_validation': 'answer_semantics',
    **{name: 'orchestration' for name in {
        'shared_company_engine', 'shared_company_ports', 'shared_company_task',
        'owner_admission_subject', 'owner_job_cli', 'subject_dispatch_cli', 'task_receipts',
        'search_checkpoint_binding', 'search_exposure_binding', 'search_exposure_contract',
    }},
    **{path.stem: 'workbench' for path in _SCRIPTS.glob('dashboard_*.py')},
    **{name: 'workbench' for name in {
        'c06_authority', 'open_dashboard',
        'workbench_snapshot', 'workbench_snapshot_cli', 'view_quick_scan',
    }},
    **{name: 'foundation' for name in {
        'json_io', 'module_contract', 'contract_validation', 'observation_profiles',
        'exchange_contract', 'work_contract', 'search_receipt',
    }},
    **{name: 'query_contracts' for name in {
        'query_capabilities_contract', 'query_capabilities_vendor_contract',
        'query_contract_cli', 'query_contract', 'query_facts_contract',
        'query_field_assessment', 'query_pool_assessment_contract', 'query_pool_contract',
        'query_pool_scope_contract', 'query_research_contract',
        'query_review_lead_contract', 'query_vendor_contract', 'refresh_contract',
        'subject_dispatch_contract', 'subject_context_export',
    }},
    **{name: 'provider_execution' for name in {
        'model_config', 'model_invocation', 'provider_transport',
    }},
    **{name: 'experiments' for name in {
        'accuracy_assessment', 'accuracy_followup', 'accuracy_pilot', 'accuracy_report',
        'applic_llm_compare', 'applic_llm_probe', 'applic_pipeline_check',
        'batching_benchmark_archive', 'batching_benchmark_report', 'batching_benchmark',
        'company_agent_contrast_launcher', 'company_agent_contrast',
        'company_agent_research_pilot', 'deepseek_search_client', 'mimo_json_mode_probe',
        'mimo_pilot_extension', 'mimo_pilot_results', 'mimo_pilot_review_summary',
        'mimo_pro_pilot', 'zai_route_diagnostic', 'pipeline_review_pack',
    }},
    **{name: 'acceptance' for name in {
        'stockwiki_g2b_acceptance', 'stockwiki_mapping_contract', 'verified_evidence_audit',
        'observation_import_preflight', 'handoff_reference_check', 'parallel_handoff_cli',
        'g0_candidate_manifest',
    }},
})

DOMAIN_PUBLIC_EDGES = {
    ('dashboard_prepare', 'module_registry'): {'load_package', 'FACT_BANK_RESOURCE'},
    ('dashboard_prepare', 'question_sets'): {'compose_from_route'},
    ('dashboard_prepare', 'routing'): {'resolve_route_decision'},
    ('dashboard_prepare', 'refresh_contract'): {'validate_route_targets'},
    ('dashboard_prepare', 'frozen_release_projection'): {'create_question_config'},
    ('c06_authority', 'module_registry'): {'load_package', 'observation_ingest_ready'},
    ('c06_authority', 'question_manifest'): {'validate_manifest_metric_contract'},
    ('c06_authority', 'standard_answers'): {'digest', 'observation_metadata'},
    ('c06_authority', 'subject_context_export'): {'attach_subject_context'},
    ('dashboard_delivery', 'frozen_release_projection'): {'create_projection'},
    ('frozen_release_projection', 'module_registry'): {'load_package', 'observation_ingest_ready'},
    ('frozen_release_projection', 'question_manifest'): {'validate_manifest_metric_contract'},
    ('frozen_release_projection', 'standard_answers'): {'question_field_id'},
    ('workbench_snapshot', 'question_library'): {
        'read_json', 'load_library', 'ALWAYS_APPLICABLE_DIAGNOSTICS',
    },
    ('answer_validation', 'module_registry'): {'load_package'},
    ('answer_validation', 'standard_answers'): {
        'digest', 'read_resource', 'ANSWER_VALIDATION_API_PROTOCOL', 'validate_content',
    },
    ('answer_validation', 'question_prompts'): {
        'SEMANTIC_RULES_API_PROTOCOL', 'typed_semantic_rules',
        'legacy_typed_semantic_rules',
    },
    ('shared_company_engine', 'answer_validation'): {
        'API_PROTOCOL', 'PUBLIC_API_EXPORTS', 'AnswerSemanticsRejected',
        'frozen_answer_semantics', 'project_original_semantic_resources',
    },
    ('query_contract', 'standard_answers'): {'validate_content', 'validate_visible_channels'},
    ('refresh_contract', 'query_contract'): {
        'index_subject_refs', 'parse_utc_timestamp', 'profile_query_schema',
    },
    ('subject_dispatch_contract', 'query_contract'): {'validate_original_semantics'},
    ('subject_dispatch_cli', 'query_contract'): {'load_document'},
    ('subject_dispatch_cli', 'query_vendor_contract'): {'original_observation'},
    ('subject_dispatch_cli', 'subject_dispatch_contract'): {
        'bind_original', 'digest', 'validate_dispatch_request', 'validate_receipt',
    },
    ('subject_dispatch_cli', 'frozen_release_projection'): {
        'create_execution_profile', 'create_projection', 'create_question_config',
    },
    ('query_field_assessment', 'work_contract'): {'freshness_status', 'parse_utc'},
}

API_PROTOCOL_FIELDS = {
    'json_io': 'API_PROTOCOL',
    'module_contract': 'API_PROTOCOL',
    'contract_validation': 'API_PROTOCOL',
    'observation_profiles': 'API_PROTOCOL',
    'exchange_contract': 'API_PROTOCOL',
    'work_contract': 'API_PROTOCOL',
    'search_receipt': 'API_PROTOCOL',
    'question_bank': 'API_PROTOCOL',
    'question_manifest': 'API_PROTOCOL',
    'module_registry': 'API_PROTOCOL',
    'question_library': 'API_PROTOCOL',
    'question_sets': 'API_PROTOCOL',
    'routing': 'API_PROTOCOL',
    'metric_coordinates': 'API_PROTOCOL',
    'frozen_release_projection': 'API_PROTOCOL',
    'refresh_contract': 'API_PROTOCOL',
    'query_contract': 'API_PROTOCOL',
    'subject_dispatch_contract': 'API_PROTOCOL',
    'query_vendor_contract': 'API_PROTOCOL',
    'subject_context_export': 'API_PROTOCOL',
    'standard_answers': 'ANSWER_VALIDATION_API_PROTOCOL',
    'question_prompts': 'SEMANTIC_RULES_API_PROTOCOL',
    'answer_validation': 'API_PROTOCOL',
    'model_config': 'API_PROTOCOL',
    'model_invocation': 'API_PROTOCOL',
    'provider_transport': 'API_PROTOCOL',
}


def _script_inventory_violations(actual_modules, expected_modules, domain_modules,
                                 application_modules):
    actual_modules = set(actual_modules)
    expected_modules = set(expected_modules)
    domain_modules = dict(domain_modules)
    violations = []
    violations.extend((name, 'script_not_in_inventory')
                      for name in actual_modules - expected_modules)
    violations.extend((name, 'inventory_entry_missing_from_scripts')
                      for name in expected_modules - actual_modules)
    violations.extend((name, 'script_has_no_domain')
                      for name in actual_modules - set(domain_modules))
    violations.extend((name, 'domain_assignment_not_in_inventory')
                      for name in set(domain_modules) - expected_modules)
    actual_application = {name for name, domain in domain_modules.items()
                          if domain == 'application'}
    violations.extend((name, 'application_layer_not_explicit')
                      for name in actual_application ^ set(application_modules))
    return sorted(violations)


def _declared_public_api(path):
    tree = ast.parse(path.read_text(encoding='utf8'))
    exports = set()
    protocol = None
    protocol_field = API_PROTOCOL_FIELDS.get(path.stem)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {target.id for target in targets if isinstance(target, ast.Name)}
        value = node.value
        if 'PUBLIC_API_EXPORTS' in names:
            if isinstance(value, (ast.Set, ast.List, ast.Tuple)):
                exports.update(item.value for item in value.elts
                               if isinstance(item, ast.Constant) and isinstance(item.value, str))
            elif (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                  and value.func.id in {'frozenset', 'set', 'tuple', 'list'}
                  and value.args and isinstance(value.args[0], (ast.Set, ast.List, ast.Tuple))):
                exports.update(item.value for item in value.args[0].elts
                               if isinstance(item, ast.Constant) and isinstance(item.value, str))
        if protocol_field and protocol_field in names and isinstance(value, ast.Constant):
            protocol = value.value
    return protocol, exports


def _defined_module_symbols(path):
    """Names that a module actually binds, without importing it or running I/O."""
    tree = ast.parse(path.read_text(encoding='utf8'))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                names.update(child.id for child in ast.walk(target)
                             if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store))
    return names


def test_cross_domain_script_imports_use_declared_versioned_public_operations():
    scripts = _SCRIPTS
    script_paths = sorted(scripts.glob('*.py'))
    local_modules = {path.stem for path in script_paths}
    inventory_violations = _script_inventory_violations(
        local_modules, EXPECTED_SCRIPT_MODULES, DOMAIN_MODULES, APPLICATION_MODULES)
    assert not inventory_violations, '\n'.join(map(repr, inventory_violations))
    facade_exports = {}
    protocols = {}
    for module in API_PROTOCOL_FIELDS:
        path = scripts / f'{module}.py'
        protocol, exports = _declared_public_api(path)
        facade_exports[module] = exports
        protocols[module] = protocol
    violations = []
    for source in script_paths:
        tree = ast.parse(source.read_text(encoding='utf8'))
        violations.extend(_cross_domain_public_api_violations(
            tree, source.name, DOMAIN_MODULES, facade_exports, DOMAIN_PUBLIC_EDGES,
            local_modules,
        ))
    assert not violations, '\n'.join(map(repr, violations))
    for module, protocol_field in API_PROTOCOL_FIELDS.items():
        assert re.fullmatch(r'[A-Za-z0-9_.-]+/\d+\.\d+\.\d+', protocols.get(module, '')), (
            f'{module} must publish a semantic-versioned API protocol')
        assert protocol_field in facade_exports[module]
        assert 'PUBLIC_API_EXPORTS' in facade_exports[module]
        bound = _defined_module_symbols(scripts / f'{module}.py')
        missing = facade_exports[module] - bound
        assert not missing, f'{module} declares names it does not bind: {sorted(missing)}'


def test_script_inventory_rejects_unclassified_and_implicitly_application_modules():
    assert _script_inventory_violations(
        actual_modules={'known_script', 'new_script'},
        expected_modules={'known_script', 'new_script'},
        domain_modules={'known_script': 'application', 'new_script': 'application'},
        application_modules={'known_script'},
    ) == [('new_script', 'application_layer_not_explicit')]


def test_cross_domain_scanner_rejects_unlisted_public_helpers_but_accepts_facade_exports():
    domains = {'question_sets': 'question_bank', 'question_bank_api': 'question_bank',
               'workbench_snapshot': 'workbench'}
    exports = {'question_bank_api': {'compose_questions'}}
    edges = {('workbench_snapshot', 'question_bank_api'): {'compose_questions'}}
    same_domain = ast.parse('from question_sets import internal_helper')
    public_facade = ast.parse('from question_bank_api import compose_questions')

    assert _cross_domain_public_api_violations(
        same_domain, 'question_sets.py', domains, exports, edges
    ) == []
    assert _cross_domain_public_api_violations(
        public_facade, 'workbench_snapshot.py', domains, exports, edges
    ) == []

    unlisted = ast.parse('from question_sets import public_but_unreviewed_helper')
    assert _cross_domain_public_api_violations(
        unlisted, 'workbench_snapshot.py', domains, exports, edges
    ) == [('workbench_snapshot.py', 'question_sets', 'public_but_unreviewed_helper',
           'operation_not_declared')]
    unexported = ast.parse('from question_bank_api import undeclared_export')
    assert _cross_domain_public_api_violations(
        unexported, 'workbench_snapshot.py', domains, exports,
        {('workbench_snapshot', 'question_bank_api'): {'undeclared_export'}}
    ) == [('workbench_snapshot.py', 'question_bank_api', 'undeclared_export',
           'operation_not_exported')]
    dynamic = ast.parse(
        "import importlib\nimportlib.import_module('question_sets')"
    )
    assert _cross_domain_public_api_violations(
        dynamic, 'workbench_snapshot.py', domains, exports, edges
    ) == [('workbench_snapshot.py', 'question_sets', '<dynamic_import>',
           'cross_domain_dynamic_import_forbidden')]
    alias_dynamic = ast.parse(
        "from importlib import import_module as load\nload('question_sets')"
    )
    assert _cross_domain_public_api_violations(
        alias_dynamic, 'workbench_snapshot.py', domains, exports, edges
    ) == [('workbench_snapshot.py', 'question_sets', '<dynamic_import>',
           'cross_domain_dynamic_import_forbidden')]
    unclassified = ast.parse('from hidden_script import private_helper')
    assert _cross_domain_public_api_violations(
        unclassified, 'workbench_snapshot.py', domains, exports, edges,
        local_modules={*domains, 'hidden_script'},
    ) == [('workbench_snapshot.py', 'hidden_script', '<module>',
           'local_target_unclassified')]
    unclassified_source = ast.parse('from question_bank_api import compose_questions')
    assert _cross_domain_public_api_violations(
        unclassified_source, 'hidden_script.py', domains, exports, edges,
        local_modules={*domains, 'hidden_script'},
    ) == [('hidden_script.py', 'hidden_script', '<module>',
           'local_source_unclassified')]


@pytest.mark.parametrize('source', [
    'import question_bank_api as peer\nvars(peer)["_storage"]',
    'import question_bank_api as peer\nfrom builtins import vars as namespace\nnamespace(peer)',
    'import builtins as builtin_helpers\nimport question_bank_api as peer\n'
    'getattr(builtin_helpers, "vars")(peer)',
])
def test_cross_domain_scanner_rejects_module_namespace_reflection(source):
    domains = {'question_bank_api': 'question_bank', 'workbench_snapshot': 'workbench'}
    exports = {'question_bank_api': {'PUBLIC_API_EXPORTS', 'compose_questions'}}
    assert _cross_domain_public_api_violations(
        ast.parse(source), 'workbench_snapshot.py', domains, exports,
        {('workbench_snapshot', 'question_bank_api'): {'compose_questions'}},
    ) == [('workbench_snapshot.py', 'question_bank_api', '<module_namespace>',
           'module_namespace_reflection_forbidden')]


def test_cross_domain_scanner_rejects_assigned_module_aliases():
    domains = {'question_bank_api': 'question_bank', 'workbench_snapshot': 'workbench'}
    exports = {'question_bank_api': {'PUBLIC_API_EXPORTS', 'compose_questions'}}
    source = ast.parse(
        'import question_bank_api as peer\nalias = peer\nsecond = alias\nsecond._private()')
    assert _cross_domain_public_api_violations(
        source, 'workbench_snapshot.py', domains, exports,
        {('workbench_snapshot', 'question_bank_api'): {'compose_questions'}},
    ) == [('workbench_snapshot.py', 'question_bank_api', '_private',
           'operation_not_declared')]


def test_cross_domain_scanner_fails_closed_on_ambiguous_module_aliases():
    domains = {
        'question_bank_api': 'question_bank',
        'query_contract_api': 'query_contracts',
        'workbench_snapshot': 'workbench',
    }
    exports = {
        'question_bank_api': {'PUBLIC_API_EXPORTS', 'compose_questions'},
        'query_contract_api': {'PUBLIC_API_EXPORTS', 'validate_request'},
    }
    source = ast.parse(
        'import question_bank_api as first\n'
        'import query_contract_api as second\n'
        'selected = first\nselected = second\nselected.call()')
    assert _cross_domain_public_api_violations(
        source, 'workbench_snapshot.py', domains, exports,
        {('workbench_snapshot', 'question_bank_api'): {'compose_questions'},
         ('workbench_snapshot', 'query_contract_api'): {'validate_request'}},
    ) == [('workbench_snapshot.py', '<ambiguous>', 'selected',
           'ambiguous_imported_alias')]


@pytest.mark.parametrize('source', [
    'from public_facade import Service as Peer\nPeer._private()',
    'from public_facade import Service\nService._private()',
    'from public_facade import Service\nservice = Service()\nservice._private()',
    'from public_facade import Service\ngetattr(Service, "_private")()',
    'import public_facade as peer\nservice = peer.Service\nservice._private()',
    'from public_facade import Service as Peer\ngetattr(Peer, "_private")()',
    'import public_facade as peer\nservice = peer.Service()\nservice._private()',
    'from public_facade import Service as Peer\nservice = Peer()\nservice._private()',
])
def test_cross_domain_scanner_rejects_private_members_of_imported_objects(source):
    domains = {'public_facade': 'question_bank', 'consumer': 'workbench'}
    exports = {'public_facade': {'PUBLIC_API_EXPORTS', 'Service'}}
    assert _cross_domain_public_api_violations(
        ast.parse(source), 'consumer.py', domains, exports,
        {('consumer', 'public_facade'): {'Service'}},
    ) == [('consumer.py', 'public_facade', 'Service._private',
           'private_api_member_access_forbidden')]


@pytest.mark.parametrize('source', [
    'import public_facade as peer\n'
    'service = peer.Service() if enabled else local_service\nservice._private()',
    'from public_facade import Service as Peer\n'
    'service = Peer() if enabled else Peer()\nservice._private()',
])
def test_cross_domain_scanner_tracks_conditional_public_object_construction(source):
    domains = {'public_facade': 'question_bank', 'consumer': 'workbench'}
    exports = {'public_facade': {'PUBLIC_API_EXPORTS', 'Service'}}
    violations = _cross_domain_public_api_violations(
        ast.parse(source), 'consumer.py', domains, exports,
        {('consumer', 'public_facade'): {'Service'}},
    )
    assert violations
    assert violations[0][0] == 'consumer.py'
    assert violations[0][-1] in {
        'private_api_member_access_forbidden', 'ambiguous_imported_alias',
    }


@pytest.mark.parametrize('filename', [
    'test_company_scan_native_e2e.py',
    'test_shared_company_engine_native_e2e.py',
])
def test_native_e2e_allowlisted_environment_does_not_mutate_pytest_process(filename):
    path = ROOT / 'tests' / filename
    script = textwrap.dedent('''
        import os, pytest, runpy, sys
        from collections.abc import Mapping

        class ReadOnlyEnvironment(Mapping):
            def __init__(self, source): self._source = source
            def __getitem__(self, key): return self._source[key]
            def __iter__(self): return iter(self._source)
            def __len__(self): return len(self._source)
            def _blocked(self, *args, **kwargs):
                raise AssertionError("test module attempted to mutate its parent environment")
            __setitem__ = __delitem__ = clear = update = pop = popitem = setdefault = __ior__ = _blocked

        os.environ = ReadOnlyEnvironment(os.environ)
        os.putenv = os.unsetenv = lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("test module attempted an OS environment mutation"))
        for filename in sys.argv[1:]:
            try:
                runpy.run_path(filename, run_name="iqs_test_import_boundary")
            except pytest.skip.Exception:
                pass
    ''')
    result = subprocess.run(
        [sys.executable, '-B', '-c', script, str(path)], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
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
    assert result['protocol'] == 'iqs.shared-company-engine/1.1.0'
    # Historical sample values remain display-only; owner capability admission
    # describes the executable contract without embedding a provider or count.
    assert result['legacy_sample_profile'] == {
        'registered_question_count': 12,
        'cutoff': '2026-10-13',
        'provider': 'mimo',
        'pack_size_range': [1, 12],
    }
    assert 'registered_question_count' not in result
    assert 'registered_cutoff' not in result
    assert 'question_pack_provider' not in result
    assert result['company_scan']['pack_size_range'] == 'owner_admitted_positive_range'
    assert result['company_scan']['provider_selection'] == 'original_stockqa_endpoint_capabilities'
    assert {'original_Runner', 'original_RuntimeBridgePort'} <= set(result['requires'])


@pytest.mark.parametrize('owner_controls_available', [True, False])
def test_preflight_uses_task_scope_and_defers_endpoint_capabilities_to_owner(
        monkeypatch, owner_controls_available):
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
    owner_events = []

    def check_admission():
        owner_events.append('admission')

    def assert_execution_controls(**kwargs):
        owner_events.append('execution_controls')
        controls.append(kwargs)
        if not owner_controls_available:
            raise ValueError('owner_native_controls_unavailable')

    runtime = SimpleNamespace(
        model='model-with-an-opaque-owner-name',
        provider='provider-selected-by-stockqa',
        has_native_session=lambda: False,
        supports_intent_recovery=lambda: True,
        attempt_observations=lambda **kwargs: [],
        check_admission=check_admission,
        assert_execution_controls=assert_execution_controls,
    )
    config = {
        'logical_clock': False,
        'planned_model': 'model-with-an-opaque-owner-name',
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

    if owner_controls_available:
        assert engine.preflight(object(), service, {}) == config
    else:
        with pytest.raises(ValueError, match='owner_native_controls_unavailable'):
            engine.preflight(object(), service, {})
    assert controls == [{
        'pack_size': 2,
        'thinking_enabled': True,
        'max_output_tokens': 4096,
    }]
    assert owner_events == ['admission', 'execution_controls']
