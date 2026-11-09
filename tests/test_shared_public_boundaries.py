"""The production composition consumes public StockQA contracts only."""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _stockqa_imports(node):
    if isinstance(node, ast.ImportFrom):
        names = [node.module or '']
    elif isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
    else:
        names = []
    return {name for name in names if name.split('.')[0] == 'src'}


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
    assert foreign_modules == {'src.utils.quick_scan_company_context'}


def test_engine_uses_the_owner_port_instead_of_the_store_or_runner():
    source = ROOT / 'scripts/shared_company_engine.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    violations = []
    for node in ast.walk(tree):
        for module in _stockqa_imports(node) - {'src.utils.quick_scan_company_runtime'}:
            violations.append((node.lineno, module))
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == 'services' and node.attr in {'store', 'owner', 'lifecycle', 'questions'}):
            violations.append((node.lineno, node.attr))
    assert not violations, violations
