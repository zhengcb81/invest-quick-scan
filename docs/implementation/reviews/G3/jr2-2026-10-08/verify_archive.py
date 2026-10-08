"""Verify this finite delivery's hashes/JSON/AST/links and build its raw index."""
import ast
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
REVIEW = Path(__file__).resolve().parent
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not (IQS / "runs/jr2-2026-10-08-01").exists()
    release = json.loads((OUT / "approval-for-publish.json").read_text("utf-8"))
    manifest_path = OUT / "snapshots" / release["snapshot_label"] / "source.json"
    assert sha(manifest_path.read_bytes()) == release["reviewed_source_sha256"]
    manifest = json.loads(manifest_path.read_text("utf-8"))
    final = json.loads((OUT / "verification/jr2-green-03/process.json").read_text("utf-8"))
    assert final["returncode"] == 0 and not final["timeout"] and final["executed_source_unchanged"]
    assert final["executed_source_hashes"] == {row["path"]: row["sha256"] for row in manifest["changed_files"]}
    for label in ("jr2-green-02", "jr2-green-03"):
        snap = OUT / "snapshots" / label
        body = json.loads((snap / "source.json").read_text("utf-8"))
        for row in body["changed_files"]:
            data = (snap / "source" / row["path"]).read_bytes()
            assert sha(data) == row["sha256"] and len(data) == row["bytes"]
    junit = ET.parse(OUT / "verification/jr2-green-03/junit.xml").getroot()
    cases = list(junit.iter("testcase"))
    assert len(cases) == 136 and not list(junit.iter("failure")) and not list(junit.iter("error")) and not list(junit.iter("skipped"))
    rows, json_count, python_count, links = [], 0, 0, 0
    for root in (REVIEW, OUT):
        for path in sorted(root.rglob("*")):
            assert not path.is_symlink()
            if not path.is_file() or path == REVIEW / "artifacts.json":
                continue
            data = path.read_bytes()
            if path.suffix == ".json":
                json.loads(data)
                json_count += 1
            elif path.suffix == ".py":
                ast.parse(data, filename=str(path))
                python_count += 1
            elif path.suffix == ".md":
                text = data.decode("utf-8-sig")
                for target in re.findall(r"\]\(([^)]+)\)", text):
                    if target.startswith(("https:", "http:", "#")):
                        continue
                    referenced = (path.parent / target.split("#")[0]).resolve()
                    assert referenced.is_relative_to(IQS) and referenced.exists(), "Missing local link: " + target
                    links += 1
            rows.append(dict(path=path.relative_to(IQS).as_posix(), bytes=len(data), sha256=sha(data)))
    body = dict(schema="jr2_delivery_artifacts/1", artifacts=rows,
        verification=dict(json_files=json_count, python_ast_files=python_count, local_links=links,
            final_junit_instances=136, jr2_instances=sum("test_jr2_" in case.attrib["name"] for case in cases),
            raw_index_excludes_itself=True))
    (REVIEW / "artifacts.json").write_text(json.dumps(body, ensure_ascii=False, indent=2)+"\n", "utf-8")
    print(json.dumps(dict(artifacts=len(rows), json=json_count, ast=python_count, links=links,
                         final_junit=136, jr2=body["verification"]["jr2_instances"])))


if __name__ == "__main__":
    main()
