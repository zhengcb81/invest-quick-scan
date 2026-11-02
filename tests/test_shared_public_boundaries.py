"""The production composition consumes public StockQA contracts only."""
import ast
from pathlib import Path

import pytest


@pytest.mark.parametrize('filename,functions', [
    ('shared_company_engine.py', {'_production_answer_semantics',
                                '_validate_native_answer_sources', 'finalize_shared_engine'}),
    ('shared_company_task.py', {'create_company_scan_task'}),
])
def test_production_composition_does_not_reach_into_stockqa_private_objects(filename, functions):
    source = Path(__file__).resolve().parents[1] / 'scripts' / filename
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
