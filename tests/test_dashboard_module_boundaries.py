"""Workspace modules communicate through the named public Python interface."""

import ast
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TIME_PACKAGE = "iqs_temporal_vendor"


def _time_exports():
    module = ast.parse((SCRIPTS / TIME_PACKAGE / "__init__.py").read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in statement.targets
        ):
            return set(ast.literal_eval(statement.value))
    raise AssertionError(f"{TIME_PACKAGE} must declare its public exports")


TIME_EXPORTS = _time_exports()


def _owner(name, dashboard_modules):
    parts = name.removeprefix("scripts.").split(".")
    if parts[0] in dashboard_modules or parts[0] == TIME_PACKAGE:
        return parts[0]
    return None


def _private_edges(source, *, dashboard_modules):
    """Check direct imports and simple local references without executing code."""
    tree = ast.parse(source)
    scope_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
    scopes = {tree: tree}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            scopes[child] = parent if isinstance(parent, scope_types) else scopes[parent]
    references = {scope: set() for scope in set(scopes.values())}
    shadowed = {
        scope: {arg.arg for arg in ast.iter_child_nodes(scope.args) if isinstance(arg, ast.arg)}
        for scope in references if hasattr(scope, "args")
    }
    violations = set()

    def is_owner_reference(expression, scope):
        name = ast.unparse(expression)
        while True:
            if any(name == alias or name.startswith(alias + ".") for alias in references[scope]):
                return True
            if scope is tree or name.split(".")[0] in shadowed.get(scope, ()):
                return False
            scope = scopes[scope]

    for node in ast.walk(tree):
        local = references[scopes[node]]
        if isinstance(node, ast.Import):
            for alias in node.names:
                owner = _owner(alias.name, dashboard_modules)
                if owner:
                    local.add(alias.asname or alias.name)
                if owner == TIME_PACKAGE:
                    violations.add((node.lineno, alias.name))
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                module = node.module or ""
                owner = _owner(module, dashboard_modules)
                if owner:
                    if (alias.name.startswith("_") or alias.name == "*"
                        or (owner == TIME_PACKAGE and (
                            module.removeprefix("scripts.") != owner or alias.name not in TIME_EXPORTS))):
                        violations.add((node.lineno, f"{module}.{alias.name}"))
                path = ".".join(part for part in (module, alias.name) if part)
                if not owner and _owner(path, dashboard_modules) == TIME_PACKAGE:
                    violations.add((node.lineno, path))
                if _owner(path, dashboard_modules):
                    local.add(alias.asname or alias.name)

    # A simple constructor or alias assignment is still a reference to the owner.
    for node in sorted(ast.walk(tree), key=lambda node: getattr(node, "lineno", 0)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        value = node.value.func if isinstance(node.value, ast.Call) else node.value
        if is_owner_reference(value, scopes[node]):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            references[scopes[node]].update(target.id for target in targets if isinstance(target, ast.Name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            target, member = node.value, node.attr
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "getattr" and len(node.args) >= 2
              and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)):
            target, member = node.args[0], node.args[1].value
        else:
            continue
        if member.startswith("_") and is_owner_reference(target, scopes[node]):
            violations.add((node.lineno, f"{ast.unparse(target)}.{member}"))
    return sorted(violations)


@pytest.mark.parametrize("source", [
    "from dashboard_delivery import _scope_inputs as read",
    "from .dashboard_delivery import _EXPORT",
    "from scripts.dashboard_delivery import *",
    "from . import dashboard_delivery as delivery\ndelivery._scope_inputs(bundle)",
    "import scripts.dashboard_delivery\nscripts.dashboard_delivery._scope_inputs(bundle)",
    "import dashboard_delivery as delivery\ngetattr(delivery, '_scope_inputs')(bundle)",
    "import dashboard_delivery as delivery\nalias = delivery\nalias._scope_inputs(bundle)",
    "from dashboard_delivery import Gateway\ngateway = Gateway(config)\ngateway._select(bundle)",
    "from iqs_temporal_vendor.assess import _clock_reading",
    "from iqs_temporal_vendor.policy import candidate_policy",
    "from iqs_temporal_vendor import policy",
    "from scripts import iqs_temporal_vendor",
])
def test_private_interface_violation_is_detected(source):
    assert len(_private_edges(source, dashboard_modules={"dashboard_delivery"})) == 1


def test_public_calls_and_module_local_private_helpers_are_allowed():
    source = """from dashboard_delivery import describe_delivery_scope
import dashboard_delivery as delivery
from iqs_temporal_vendor import explain_observation_clocks

def _local_helper(bundle):
    delivery.read_work_scope(bundle)
    return describe_delivery_scope(bundle)

def _own_implementation(delivery):
    return delivery._local_helper()

_local_helper(bundle)
"""
    assert _private_edges(source, dashboard_modules={"dashboard_delivery"}) == []


def test_dashboard_uses_public_interfaces():
    files = sorted(SCRIPTS.glob("dashboard_*.py")) + [SCRIPTS / "open_dashboard.py"]
    modules = {path.stem for path in files}
    violations = [
        f"{path.name}:{line}: {symbol}"
        for path in files
        for line, symbol in _private_edges(path.read_text(encoding="utf-8-sig"), dashboard_modules=modules)
    ]
    assert not violations, "Dashboard must use public interfaces:\n" + "\n".join(violations)


def _owner_implementation_references(source):
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            names = []
        for name in names:
            if name.split(".")[0] in {"stockwiki", "src"}:
                violations.append((node.lineno, name))
        if isinstance(node, ast.Constant) and node.value == "-c":
            violations.append((node.lineno, "inline Python owner transport"))
    return sorted(violations)


@pytest.mark.parametrize("source", [
    "from stockwiki.quick_scan_store import QuickScanStore",
    "import src.utils.quick_scan_work_store",
    "args = [python, '-c', OWNER_SCRIPT]",
])
def test_owner_implementation_transport_is_detected(source):
    assert len(_owner_implementation_references(source)) == 1


@pytest.mark.parametrize("filename", [
    "dashboard_owner.py", "dashboard_company_projection.py", "dashboard_delivery.py",
    "dashboard_execution.py", "dashboard_prepare.py",
])
def test_migrated_owner_clients_only_call_public_commands(filename):
    path = SCRIPTS / filename
    violations = _owner_implementation_references(path.read_text(encoding="utf-8-sig"))
    assert not violations, "\n".join(f"{filename}:{line}: {name}" for line, name in violations)
