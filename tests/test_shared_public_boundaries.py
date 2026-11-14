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
PACKAGE = ROOT / 'scripts' / 'iqs_scan'
EXECUTION = PACKAGE / 'execution'
ANSWERS = PACKAGE / 'answers'

def test_capability_package_owns_code_and_legacy_import_resolves_to_it(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    from iqs_scan.foundation import api
    import module_contract
    from scripts import module_contract as qualified_legacy

    assert api.module_digest({'b': 2, 'a': 1}) == module_contract.digest({'a': 1, 'b': 2})
    assert api.module_digest is module_contract.digest
    assert qualified_legacy is module_contract
    assert Path(module_contract.__file__).resolve().parent == ROOT / 'scripts/iqs_scan/foundation'


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


IMPORTERS = {'__import__', 'importlib.import_module'}
SPECIAL_MEMBERS = {
    ('importlib', 'import_module'): 'importlib.import_module',
    ('builtins', '__import__'): '__import__',
    ('builtins', 'vars'): 'builtins.vars',
}


def _special_operations(value, aliases):
    if isinstance(value, ast.Name):
        return aliases.get(value.id, set())
    if isinstance(value, ast.Attribute):
        owner, member = value.value, value.attr
    elif (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
          and value.func.id == 'getattr' and len(value.args) >= 2
          and isinstance(value.args[1], ast.Constant) and isinstance(value.args[1].value, str)):
        owner, member = value.args[0], value.args[1].value
    elif isinstance(value, ast.Call):
        return {name for importer in _special_operations(value.func, aliases) & IMPORTERS
                if (name := _literal_import_target(value, importer)) in {'importlib', 'builtins'}}
    else:
        return set()
    return {SPECIAL_MEMBERS[(module, member)] for module in _special_operations(owner, aliases)
            if (module, member) in SPECIAL_MEMBERS}


def _dynamic_import_aliases(tree):
    """Track ordinary aliases without reassignments making the scan oscillate."""
    aliases = {name: {name} for name in ('importlib', 'builtins', '__import__')}
    aliases['vars'] = {'builtins.vars'}
    assignments = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {'importlib', 'builtins'}:
                    aliases.setdefault(alias.asname or alias.name, set()).add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == '*':
                    for (module, member), canonical in SPECIAL_MEMBERS.items():
                        if module == node.module:
                            aliases.setdefault(member, set()).add(canonical)
                    continue
                canonical = SPECIAL_MEMBERS.get((node.module, alias.name))
                if canonical:
                    aliases.setdefault(alias.asname or alias.name, set()).add(canonical)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assignments.extend((target.id, node.value) for target in targets if isinstance(target, ast.Name))

    changed = True
    while changed:
        changed = False
        for name, value in assignments:
            added = _special_operations(value, aliases) - aliases.get(name, set())
            if added:
                aliases.setdefault(name, set()).update(added)
                changed = True
    return aliases


def _special_calls(tree):
    aliases = _dynamic_import_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            operations = _special_operations(node.func, aliases)
            if operations:
                yield node, operations


def _call_argument(node, index, name):
    if len(node.args) > index:
        return node.args[index]
    return next((item.value for item in node.keywords if item.arg == name), None)


def _literal_import_target(node, importer, source_package=None):
    target = _call_argument(node, 0, 'name')
    if not isinstance(target, ast.Constant) or not isinstance(target.value, str):
        return None
    name = target.value
    if source_package is None:
        return name
    if importer == '__import__':
        level = _call_argument(node, 4, 'level')
        if level is None:
            return name
        if not isinstance(level, ast.Constant) or not isinstance(level.value, int) or level.value < 0:
            return None
        return importlib.util.resolve_name('.' * level.value + name, source_package)
    if not name.startswith('.'):
        return name
    package = _call_argument(node, 1, 'package')
    if isinstance(package, ast.Name) and package.id == '__package__':
        return importlib.util.resolve_name(name, source_package)
    if isinstance(package, ast.Constant) and isinstance(package.value, str) and package.value:
        return importlib.util.resolve_name(name, package.value)
    return None


def _integration_imports(tree):
    """Return literal imports, including aliased importlib/__import__ calls."""
    modules = {name for _, name, _, _ in _static_imports(tree) if name}
    modules.update(name for node, operations in _special_calls(tree)
                   for importer in operations & IMPORTERS
                   if (name := _literal_import_target(node, importer)) is not None)
    return modules


def _dynamic_import_calls(tree):
    return [(node.lineno, importer) for node, operations in _special_calls(tree)
            for importer in sorted(operations & IMPORTERS)]


@pytest.mark.parametrize('filename,functions', [
    ('shared_company_engine.py', {'_production_answer_semantics',
                                '_validate_native_answer_sources', 'finalize_shared_engine'}),
    ('shared_company_task.py', {'create_company_scan_task', 'create_native_task'}),
])
def test_production_composition_does_not_reach_into_stockqa_private_objects(filename, functions):
    source = EXECUTION / filename
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
    source = EXECUTION / 'shared_company_task.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    foreign_modules = {
        module
        for node in ast.walk(tree)
        for module in _stockqa_imports(node)
    }
    assert foreign_modules == {'src.utils.quick_scan_company_api'}


@pytest.mark.parametrize('filename', ['shared_company_engine.py', 'shared_company_task.py'])
def test_company_composition_never_reads_raw_owner_state(filename):
    tree = ast.parse((EXECUTION / filename).read_text(encoding='utf8'))
    forbidden = {'input_raw', 'bundle', 'entries', 'plan', 'proof'}
    violations = [
        (node.lineno, node.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in forbidden
    ]
    assert not violations, violations


def test_engine_uses_the_owner_port_instead_of_the_store_or_runner():
    source = EXECUTION / 'shared_company_engine.py'
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
    tree = ast.parse((EXECUTION / filename).read_text(encoding='utf8'))
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
    paths = [EXECUTION / 'shared_company_engine.py', ANSWERS / 'answer_validation.py']
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


def test_owner_compatibility_module_uses_the_packaged_answer_semantics(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import answer_validation
    from iqs_scan.answers import api
    from iqs_scan.execution import shared_company_engine

    assert answer_validation.API_PROTOCOL == 'iqs.answer-validation-api/1.1.0'
    assert Path(answer_validation.__file__).resolve() == ROOT / 'scripts/answer_validation.py'
    assert answer_validation.project_original_semantic_resources is api.project_original_semantic_resources

    def unavailable(*args, **kwargs):
        raise api.AnswerSemanticsRejected('original_semantic_resources_unavailable')

    monkeypatch.setattr(api, 'frozen_answer_semantics', unavailable)
    with pytest.raises(shared_company_engine.SharedEngineRejected,
                       match='original_semantic_resources_unavailable'):
        shared_company_engine._frozen_answer_semantics(None, {})


def test_missing_owner_public_api_is_normalized_before_preflight_imports(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import shared_company_engine as engine

    original_import = importlib.import_module

    def fail_owner_import(name, package=None):
        if name == 'iqs_company_agent_lab.api':
            raise ModuleNotFoundError(name)
        return original_import(name, package)

    monkeypatch.setattr(importlib, 'import_module', fail_owner_import)
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

    tree = ast.parse((EXECUTION / 'shared_company_engine.py').read_text(encoding='utf8'))
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


def _static_imports(tree, source_package=None):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                yield node.lineno, item.name, None, item.asname or item.name
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ''
            if node.level and source_package:
                name = importlib.util.resolve_name('.' * node.level + name, source_package)
            for item in node.names:
                yield node.lineno, name, item.name, item.asname or item.name


def _dotted_reference(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_reference(node.value)
        if parent:
            return f'{parent}.{node.attr}'
    return None


def _cross_domain_public_api_violations(tree, source_name, domains, facade_exports,
                                        allowed_edges, local_modules=None, *, imports=None,
                                        source_package=None, special_calls=None):
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

    def local_module(name):
        return name if name in local_modules else name.rsplit('.', 1)[-1]

    ambiguous_alias = object()
    imported = {}
    aliases = {}
    violations = []
    bindings = _static_imports(tree) if imports is None else imports
    for _, name, operation, binding in bindings:
        target = local_module(name)
        if target in local_modules and target not in domains:
            violations.append((source_name, target, '<module>', 'local_target_unclassified'))
            continue
        if target not in local_modules or domains[target] == source_domain:
            continue
        imported.setdefault(target, set()).add(operation or '<module>')
        value = (target, operation) if operation else target
        aliases[binding] = value if aliases.get(binding, value) == value else ambiguous_alias

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
            qualified = aliases.get(_dotted_reference(value))
            if qualified is not None:
                return qualified
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

    calls = _special_calls(tree) if special_calls is None else special_calls
    for node, operations in calls:
        # Reading a peer module's namespace bypasses the declared export list
        # even when the caller never spells the private attribute in source.
        if 'builtins.vars' in operations and node.args:
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
        for importer in operations & IMPORTERS:
            name = _literal_import_target(node, importer, source_package)
            if name is None:
                violations.append((source_name, '<dynamic>', '<dynamic_import>',
                                   'dynamic_import_target_must_be_literal'))
                continue
            imported_name = local_module(name)
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


# Depend on the public API of a lower capability. Repository commands
# and experiments can compose capabilities at the edge of the application.
CAPABILITY_DEPENDENCIES = {
    'foundation': set(),
    'questions': {'foundation'},
    'answers': {'foundation', 'questions'},
    'query': {'foundation', 'answers'},
    'providers': set(),
    'execution': {'foundation', 'questions', 'answers', 'query', 'providers'},
    'workbench': {'foundation', 'questions', 'answers', 'query', 'execution'},
    'tools': {'foundation', 'questions', 'answers', 'query', 'providers', 'execution', 'workbench'},
    'experiments': {'foundation', 'questions', 'answers', 'query', 'providers', 'execution'},
    'acceptance': {'foundation', 'questions', 'answers', 'query', 'workbench'},
}

# These imports belong to a different checkout deliberately selected by the
# registered experiment, not this repository's execution or research service.
REGISTERED_EXPERIMENT_MODULES = {
    'company_agent_contrast_launcher.py': {'company_agent_contrast', 'company_agent_research_pilot', 'standard_answers'},
    'company_agent_contrast.py': {'standard_answers'},
    'company_agent_research_pilot.py': {'standard_answers'},
}


def _capability_edge_violations(source, owner, exports, legacy, *, source_package=None):
    tree = ast.parse(source)
    source_package = source_package or f'iqs_scan.{owner}'
    violations = []
    public_imports = []

    def classify(line, name, operation, binding):
        canonical = name.removeprefix('scripts.')
        if (canonical in legacy or name == 'scripts' or name.startswith('scripts.iqs_scan')
                or canonical == 'iqs_scan' and operation != 'REPO_ROOT'):
            violations.append((line, name, operation, 'use_capability_api'))
            return
        parts = canonical.split('.')
        if parts[0] != 'iqs_scan' or len(parts) < 2 or parts[1] == owner:
            return
        domain = parts[1]
        api = f'iqs_scan.{domain}.api'
        if domain not in CAPABILITY_DEPENDENCIES[owner]:
            violations.append((line, name, operation, 'dependency_direction'))
        elif binding is None:
            violations.append((line, name, operation, 'cross_domain_dynamic_import_forbidden'))
        elif canonical == api and domain in exports:
            public_imports.append((line, api, operation, binding))
        elif canonical == f'iqs_scan.{domain}' and operation == 'api' and domain in exports:
            public_imports.append((line, api, None, binding))
        else:
            violations.append((line, name, operation, 'use_capability_api'))

    imports = list(_static_imports(tree, source_package))
    for line, name, operation, binding in imports:
        classify(line, name, operation, binding)

    # An unaliased dotted import also binds the package root in Python.
    if any(name.startswith('iqs_scan.') and name == binding and operation is None
           for _, name, operation, binding in imports):
        qualified_facades = {name for _, name, operation, binding in public_imports
                             if operation is None and name == binding}
        parents = {node.value for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for node in ast.walk(tree):
            if node in parents or not isinstance(getattr(node, 'ctx', None), ast.Load):
                continue
            name = _dotted_reference(node)
            if not name or (name != 'iqs_scan' and not name.startswith('iqs_scan.')):
                continue
            if name == 'iqs_scan.REPO_ROOT' or name.startswith(f'iqs_scan.{owner}.'):
                continue
            if not any(name == api or name.startswith(f'{api}.') for api in qualified_facades):
                violations.append((node.lineno, name, None, 'use_capability_api'))

    calls = list(_special_calls(tree))
    for node, operations in calls:
        for importer in operations & IMPORTERS:
            name = _literal_import_target(node, importer, source_package)
            if name is not None:
                classify(node.lineno, name, None, None)

    # Reuse the common alias/member checks with the real, fully qualified facade names.
    facade_owners = {f'iqs_scan.{domain}.api': domain for domain in exports}
    facade_owners['consumer'] = owner
    facade_exports = {name: exports[domain] for name, domain in facade_owners.items() if name != 'consumer'}
    allowed = {('consumer', name): names for name, names in facade_exports.items()
               if facade_owners[name] in CAPABILITY_DEPENDENCIES[owner]}
    violations.extend(_cross_domain_public_api_violations(
        tree, 'consumer.py', facade_owners, facade_exports, allowed,
        imports=public_imports, source_package=source_package, special_calls=calls))
    return violations


def test_capability_source_uses_versioned_public_interfaces():
    domains = {directory.name for directory in PACKAGE.iterdir()
               if directory.is_dir() and (directory / '__init__.py').is_file()}
    assert domains == set(CAPABILITY_DEPENDENCIES)
    exports = {}
    for domain in sorted(domains):
        path = PACKAGE / domain / 'api.py'
        if not path.is_file():
            continue
        tree = ast.parse(path.read_bytes())
        declarations = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {'__all__', 'API_PROTOCOL'}
        }
        names = declarations['__all__']
        assert len(names) == len(set(names)), path
        assert set(names) <= _defined_module_symbols(path), path
        if 'API_PROTOCOL' in declarations:
            assert re.fullmatch(r'[a-zA-Z0-9_.-]+/\d+\.\d+\.\d+', declarations['API_PROTOCOL']), path
        else:
            # The answer facade inherits the already published owner version.
            assert domain == 'answers' and 'API_PROTOCOL' in names
        exports[domain] = frozenset(names)

    legacy = {path.stem for path in (ROOT / 'scripts').glob('*.py')} - {'__init__'}
    violations = []
    for domain in sorted(domains):
        for path in (PACKAGE / domain).rglob('*.py'):
            allowed_legacy = REGISTERED_EXPERIMENT_MODULES.get(path.name, set()) if domain == 'experiments' else set()
            violations.extend((path.relative_to(PACKAGE), violation) for violation in
                              _capability_edge_violations(
                                  path.read_text(encoding='utf8'), domain, exports, legacy - allowed_legacy,
                                  source_package='.'.join(('iqs_scan', *path.relative_to(PACKAGE).parts[:-1]))))
    assert not violations, '\n'.join(map(str, violations))


@pytest.mark.parametrize('source', [
    'from iqs_scan.questions.question_sets import compose',
    'from iqs_scan.questions import question_sets',
    'from iqs_scan.questions.api import _private',
    'from iqs_scan.questions import api as peer\npeer._private()',
    'from iqs_scan.questions import api\napi.unadvertised()',
    'from iqs_scan.experiments import api',
    'from ..questions.question_sets import compose',
    'import question_sets',
    'from scripts import question_sets',
    'from importlib import import_module\nimport_module("question_sets")',
    'import importlib\nimportlib.import_module("iqs_scan.questions.question_sets")',
    'import importlib as imp\nimp.import_module("..questions.question_sets", __package__)',
    'from importlib import import_module\nimport_module(name=".question_sets", package="iqs_scan.questions")',
    'import builtins as bi\nbi.__import__("iqs_scan.questions.question_sets")',
    '__import__("questions.question_sets", globals(), level=2)',
    'import importlib\nloader = importlib.import_module\nloader = __import__\nloader("question_sets")',
    'module = __import__("importlib")\nmodule.import_module("iqs_scan.questions.question_sets")',
    'from importlib import *\nimport_module("iqs_scan.questions.question_sets")',
    'import importlib\nimportlib.import_module("iqs_scan.questions.api")',
    'import iqs_scan.questions.api\niqs_scan.questions.api._private()',
    'import iqs_scan.questions.api\npeer = iqs_scan.questions.api\npeer._private()',
    'import iqs_scan.questions.api\niqs_scan.questions.question_sets.compose()',
    'import iqs_scan.questions.api\npeer = iqs_scan.questions\npeer.question_sets.compose()',
    'from ..questions import api as peer\npeer._private()',
    'from ..questions.api import compose_questions as compose\ncompose._private()',
    'from scripts import iqs_scan\niqs_scan.questions.question_sets.compose()',
    'from scripts.iqs_scan.questions import api',
    'import iqs_scan\niqs_scan.questions.question_sets.compose()',
])
def test_capability_edges_reject_implementation_imports_and_reverse_direction(source):
    assert _capability_edge_violations(
        source, 'workbench', {'questions': {'compose_questions'}}, {'question_sets'})


def test_capability_edges_allow_public_facade_and_same_domain_implementation():
    assert not _capability_edge_violations(
        'from .dashboard_http import product_handler\n'
        'from iqs_scan.questions import api as questions\n'
        'from ..questions.api import compose_questions\n'
        'import iqs_scan.questions.api\n'
        'questions.compose_questions()\niqs_scan.questions.api.compose_questions()', 'workbench',
        {'questions': {'compose_questions'}}, {'question_sets'})


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


def test_company_composition_never_reads_owner_task_or_runner_implementation_fields():
    paths = (
        EXECUTION / 'shared_company_engine.py',
        EXECUTION / 'shared_company_task.py',
        ANSWERS / 'answer_validation.py',
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
        EXECUTION / 'shared_company_engine.py',
        EXECUTION / 'shared_company_task.py',
        ANSWERS / 'answer_validation.py',
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
