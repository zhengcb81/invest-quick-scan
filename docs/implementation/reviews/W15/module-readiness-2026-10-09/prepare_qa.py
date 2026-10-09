"""Read-only freeze of current tracked public executor source into W15."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[5]
OWN = ROOT / "runs/w15a/qa"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")


def main():
    baseline = json.loads((OUT / "source-preflight-02.json").read_text(encoding="utf-8"))["StockQAbyLLM"]
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    def git(*args):
        return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args], env=env)
    head = git("rev-parse", "HEAD").decode().strip()
    status = git("status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n")
    assert head == baseline["head"]["output"].strip()
    assert status == baseline["status"]["output"]
    assert not OWN.exists() and not (OUT / "executor-input-01.json").exists()
    frozen = {}
    raw_archive = git("archive", "--format=tar", head, "src", "tests", "main_with_llm.py", "pyproject.toml", ".gitignore")
    with tarfile.open(fileobj=io.BytesIO(raw_archive), mode="r:") as archive:
        for item in archive.getmembers():
            name = PurePosixPath(item.name)
            assert not name.is_absolute() and ".." not in name.parts
            assert item.isfile() or item.isdir()
            if not item.isfile() or item.name.startswith(("tests/live/", "tests/benchmarks/")):
                continue
            assert name.name not in {"llm_apis.json", "spend_authorization.json", "quick_scan_rate_cards.json"}
            blob = archive.extractfile(item).read()
            source = SOURCE / item.name
            assert source.is_file() and not source.is_symlink()
            raw = source.read_bytes()
            assert raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"), item.name
            frozen[item.name] = raw
    assert status == git("status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n")
    assert head == git("rev-parse", "HEAD").decode().strip()
    OWN.mkdir()
    for name, raw in frozen.items():
        target = OWN / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    report = dict(protocol="iqs.w15_public_executor_input/1.0.0", head=head,
                  source=str(SOURCE), original_status=status, source_files_written=0,
                  secrets_copied=False, unknown_files_read=False,
                  artifacts=[dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                             for name, raw in sorted(frozen.items())])
    (OUT / "executor-input-01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(frozen_files=len(frozen), source_files_written=0, secrets_copied=False)))


if __name__ == "__main__":
    main()
