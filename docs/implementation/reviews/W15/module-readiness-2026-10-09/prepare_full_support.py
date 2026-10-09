"""Read-only admission of one omitted tracked SW test-support program."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
SOURCE=Path("C:/Users/郑曾波/Projects/StockWiki")
TARGET=ROOT/"runs/w15a/sw/runs/regenerate_wiki.py"
OUT=ROOT/"docs/implementation/intake/W15/module-readiness-2026-10-09/full-support-input-01.json"
env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT","WINDIR","PATH","PATHEXT","COMSPEC","USERPROFILE","APPDATA","LOCALAPPDATA","SYSTEMDRIVE"}}
env.update(GIT_OPTIONAL_LOCKS="0",GIT_TERMINAL_PROMPT="0")


def git(*args):
    return subprocess.check_output(["git","--no-optional-locks","-C",str(SOURCE),*args],env=env)


def main():
    assert git("rev-parse","HEAD").decode().strip()=="6c46f03b486d215d696d32bee618793bc7fcb410"
    assert git("status","--porcelain=v1","-uall")==b""
    assert git("ls-files","--error-unmatch","runs/regenerate_wiki.py").decode().strip()=="runs/regenerate_wiki.py"
    source=SOURCE/"runs/regenerate_wiki.py"
    raw=source.read_bytes()
    blob=git("show","HEAD:runs/regenerate_wiki.py")
    assert raw.replace(b"\r\n",b"\n")==blob.replace(b"\r\n",b"\n")
    assert not TARGET.exists() and not OUT.exists()
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(raw)
    assert source.read_bytes()==raw and git("status","--porcelain=v1","-uall")==b""
    OUT.write_text(json.dumps(dict(path="runs/regenerate_wiki.py",execution_sha256=hashlib.sha256(raw).hexdigest(),
                   Git_blob_sha256=hashlib.sha256(blob).hexdigest(),source_files_written=0,support_only_not_candidate=True),indent=2)+"\n",encoding="utf-8")
    print("Admitted exact tracked support; source unchanged; no suite executed.")


if __name__=="__main__":main()
