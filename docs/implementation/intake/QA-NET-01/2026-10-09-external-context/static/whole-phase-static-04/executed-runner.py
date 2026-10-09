"""One Phase111 static/format batch in the existing isolated owned root."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).resolve().parent
OWN = IQS / "runs/n111a"
QA = OWN / "qa"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context/static"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["check", "format"])
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    assert args.label.replace("-", "").isalnum() and not OWN.is_symlink()
    scope = json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"]
    watched = {name: (QA / name).read_bytes() for name in scope if (QA / name).is_file()}
    python = [name for name in watched if name.endswith(".py")]
    root = OUT / args.label
    root.mkdir(parents=True, exist_ok=False)
    (root / "executed-runner.py").write_bytes(Path(__file__).read_bytes())
    (root / "executed-guard.py").write_bytes((OWN / "guard/sitecustomize.py").read_bytes())
    for name, raw in watched.items():
        path = root / "before-source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(QA), str(QA / "src")]),
        E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
        PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", BLACK_CACHE_DIR=str(OWN / "tmp/black-cache"),
        MYPY_CACHE_DIR=str(OWN / "tmp/mypy-cache"), STOCKQA_RUN_LIVE_E2E="0")
    commands = [
        ("isort", ["-m", "isort", "--profile", "black", *([] if args.mode == "format" else ["--check-only"]), *python]),
        ("black", ["-m", "black", "--workers", "1", *([] if args.mode == "format" else ["--check"]), *python]),
    ]
    if args.mode == "check":
        commands.append(("mypy", ["-m", "mypy", "--config-file=pyproject.toml", "--cache-dir=" + str(OWN / "tmp/mypy-cache"), "src/"]))
    receipts = []
    for name, arguments in commands:
        start = time.monotonic()
        command = [sys.executable, "-B", "-X", "utf8", *arguments]
        try:
            result = subprocess.run(command, cwd=QA, env=env, capture_output=True, timeout=180)
            stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
        (root / (name + "-stdout.log")).write_bytes(stdout)
        (root / (name + "-stderr.log")).write_bytes(stderr)
        receipt = {"tool": name, "command": command, "returncode": code, "timeout": timed_out,
            "wall_s": round(time.monotonic() - start, 3)}
        receipts.append(receipt)
        print(json.dumps({k: receipt[k] for k in ("tool", "returncode", "timeout", "wall_s")}), flush=True)
        if timed_out:
            break
    if args.mode == "format" and all(row["returncode"] == 0 for row in receipts):
        # Match the owner's mixed-line-ending hook NOW, before final tests and
        # review, rather than have publication rewrite reviewed bytes later.
        for name in watched:
            path = QA / name
            raw = path.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            if raw != normalized:
                path.write_bytes(normalized)
    after = {name: (QA / name).read_bytes() for name in watched}
    for name, raw in after.items():
        path = root / "after-source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    support = json.loads((OUT.parent / "source-snapshot.json").read_text("utf-8"))
    for record in support:
        if record["path"] not in scope:
            assert hashlib.sha256((QA / record["path"]).read_bytes()).hexdigest() == record["sha256"], record["path"]
    document = {"mode": args.mode, "key_environment_removed": True, "owner_files_written": False,
        "tools": receipts, "before_hashes": {n: hashlib.sha256(raw).hexdigest() for n, raw in watched.items()},
        "after_hashes": {n: hashlib.sha256(raw).hexdigest() for n, raw in after.items()},
        "changed": [n for n in watched if watched[n] != after[n]], "non_scope_support_unchanged": True}
    (root / "process.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"changed": len(document["changed"]), "tools": len(receipts)}), flush=True)
    sys.exit(124 if any(row["timeout"] for row in receipts) else 0 if all(row["returncode"] == 0 for row in receipts) else 1)


if __name__ == "__main__":
    main()
