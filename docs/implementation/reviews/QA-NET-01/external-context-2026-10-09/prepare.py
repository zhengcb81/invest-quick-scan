"""Freeze known tracked nonsecret source only; never copy owner configuration."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")
HEAD = "42a517c4bd6bc8219f926957c6c332944da3278a"
EXPECTED = (
    "?? .codegraph/\n?? .workbuddy-ai/\n?? nul\n"
    "?? pilot_runs/b2a_2026-10-03/\n?? pilot_runs/g2b_alphabet_2026-10-04/\n"
    "?? pilot_runs/l02_2026-10-04/\n?? progress_update.txt\n"
)


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    status = git("status", "--porcelain=v1").decode().replace("\r\n", "\n")
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert status == EXPECTED, "Reconcile active writer drift first"
    assert not OWN.exists() and not OUT.exists(), "Never reuse another run root"
    raw_archive = git("archive", "--format=tar", HEAD, "src", "tests", "main_with_llm.py", "pyproject.toml", ".gitignore")
    frozen = {}
    with tarfile.open(fileobj=io.BytesIO(raw_archive), mode="r:") as archive:
        for item in archive.getmembers():
            name = PurePosixPath(item.name)
            assert not name.is_absolute() and ".." not in name.parts
            assert item.isfile() or item.isdir()
            if not item.isfile() or item.name.startswith(("tests/live/", "tests/benchmarks/")):
                continue
            assert name.name not in {"llm_apis.json", "spend_authorization.json", "quick_scan_rate_cards.json"}
            blob = archive.extractfile(item).read()
            path = SOURCE / item.name
            assert not path.is_symlink() and path.is_file()
            raw = path.read_bytes()
            assert raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"), item.name
            frozen[item.name] = raw
    assert status == git("status", "--porcelain=v1").decode().replace("\r\n", "\n")
    OWN.mkdir(parents=True)
    OUT.mkdir(parents=True)
    for name, raw in frozen.items():
        target = OWN / "qa" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for name in ("guard", "tmp", "logs"):
        (OWN / name).mkdir()
    (OWN / "guard/sitecustomize.py").write_bytes((IQS / "docs/implementation/intake/G3/2026-10-08-jr2/snapshots/jr2-green-03/executed-guard.py").read_bytes())
    save(OUT / "source-baseline.json", dict(source=str(SOURCE), head=HEAD, status=status))
    save(OUT / "source-snapshot.json", [dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) for name, raw in frozen.items()])
    print(json.dumps(dict(frozen_files=len(frozen), owner_files_written=0, real_credentials_copied=False)))


if __name__ == "__main__":
    main()
