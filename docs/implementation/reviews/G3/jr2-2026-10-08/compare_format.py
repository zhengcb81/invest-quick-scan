"""Bounded AST/import-scope evidence for the owner formatter's seven files."""
import ast
import collections
import hashlib
import json
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/jr2-2026-10-08-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
OLD = OUT / "snapshots/jr2-green-02"


class RemoveImports(ast.NodeTransformer):
    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None


def imports(node, scope=()):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        scope += ((type(node).__name__, node.name),)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return [(scope, type(node).__name__, getattr(node, "level", None),
                 getattr(node, "module", None), name.name, name.asname) for name in node.names]
    result = []
    for child in ast.iter_child_nodes(node):
        result.extend(imports(child, scope))
    return result


def main():
    manifest = json.loads((OLD / "source.json").read_text("utf-8"))
    rows = []
    for item in manifest["changed_files"]:
        name = item["path"]
        before = (OLD / "source" / name).read_bytes()
        after = (OWN / "qa" / name).read_bytes()
        tree_before = ast.parse(before)
        tree_after = ast.parse(after)
        imports_equal = collections.Counter(imports(tree_before)) == collections.Counter(imports(tree_after))
        body_equal = ast.dump(RemoveImports().visit(tree_before)) == ast.dump(RemoveImports().visit(tree_after))
        assert imports_equal and body_equal, "Formatter changed code/import scope: " + name
        rows.append(dict(path=name, before_sha256=hashlib.sha256(before).hexdigest(),
            after_sha256=hashlib.sha256(after).hexdigest(), body_ast_equal=True,
            imported_bindings_and_scopes_equal=True))
    result = dict(schema="jr2_owner_format_provenance/1", files=rows,
        limit="Import order changes are disclosed; AST/scope equivalence is supplemented by final affected regression, not a universal semantic proof")
    with (OUT / "format-provenance.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(files=len(rows), body_ast_equal=True, import_scope_equal=True)))


if __name__ == "__main__":
    main()
