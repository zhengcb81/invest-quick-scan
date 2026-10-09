"""Export only the accepted nonsecret QA source bytes into an exclusive root."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/model-resolution-2026-10-09-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"
SOURCE = "C:/Users/郑曾波/Projects/StockQAbyLLM"
HEAD = "86b1e8ab1221e085f08718ed31d18e792e526d34"


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", SOURCE, *args])


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    old = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
    baseline = json.loads((old / "source-baseline.json").read_text("utf-8"))
    expected = json.loads((old / "source-snapshot.json").read_text("utf-8"))
    reviewed = json.loads((old / "snapshots/jr2-green-03/source.json").read_text("utf-8"))
    catalog = {row["path"]: row.copy() for row in expected}
    for row in reviewed["changed_files"]:
        assert row["path"] in catalog
        catalog[row["path"]].update(bytes=row["bytes"], sha256=row["sha256"])
    status = git("status", "--porcelain=v1").decode()
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert status == baseline["status"], "Reconcile any writer drift before export"
    assert not OWN.exists() and not OUT.exists(), "Never reuse an occupied test root"
    export = git("archive", "--format=tar", HEAD, "src", "tests", "main_with_llm.py", "pyproject.toml")
    frozen = {}
    with tarfile.open(fileobj=io.BytesIO(export), mode="r:") as archive:
        for entry in archive.getmembers():
            path = PurePosixPath(entry.name)
            assert not path.is_absolute() and ".." not in path.parts
            assert entry.isdir() or entry.isfile()
            if not entry.isfile() or entry.name not in catalog:
                continue
            raw = archive.extractfile(entry).read()
            lf = raw.replace(b"\r\n", b"\n")
            matches = [data for data in (raw, lf, lf.replace(b"\n", b"\r\n"))
                       if hashlib.sha256(data).hexdigest() == catalog[entry.name]["sha256"]]
            assert matches, "Fixed accepted hash not found: " + entry.name
            assert len(matches[0]) == catalog[entry.name]["bytes"]
            frozen[entry.name] = matches[0]
    assert set(frozen) == set(catalog)
    # Small safe tracked metadata required for exact tracking of the new schema.
    ignore = git("show", HEAD + ":.gitignore")
    OWN.mkdir(parents=True)
    OUT.mkdir(parents=True)
    for name, raw in frozen.items():
        target = OWN / "qa" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (OWN / "qa/.gitignore").write_bytes(ignore)
    for name in ("guard", "tmp", "logs"):
        (OWN / name).mkdir()
    (OWN / "guard/sitecustomize.py").write_bytes(
        (IQS / "docs/implementation/intake/G3/2026-10-08-jr2/snapshots/jr2-green-03/executed-guard.py").read_bytes()
    )
    save(OUT / "source-baseline.json", dict(source=SOURCE, head=HEAD, result=HEAD, status=status))
    save(OUT / "source-snapshot.json", list(catalog.values()))
    save(OUT / "extra-baseline.json", [dict(path=".gitignore", bytes=len(ignore), sha256=hashlib.sha256(ignore).hexdigest())])
    print(json.dumps(dict(frozen_qa_files=len(frozen), metadata_files=1, external_written=False)))


if __name__ == "__main__":
    main()
