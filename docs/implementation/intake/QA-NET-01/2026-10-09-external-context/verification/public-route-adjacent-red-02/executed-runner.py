"""Freeze and run the IQS consumer batch under the existing private guard."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
INPUTS = ("scripts/stockqa_adapter.py", "scripts/routing.py", "schemas/quick_scan/route-decision.schema.json",
    "tests/test_external_search_result_contract.py", "tests/test_stockqa_adapter.py", "tests/test_routing.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--affected", action="store_true")
    parser.add_argument("--producer", action="store_true")
    parser.add_argument("--select")
    args = parser.parse_args()
    assert args.label.replace("-", "").isalnum()
    dest = OUT / "verification" / args.label
    dest.mkdir(parents=True, exist_ok=False)
    log = OWN / "logs" / args.label
    log.mkdir(parents=True, exist_ok=False)
    frozen = {}
    private = {}
    for name in INPUTS:
        raw = (IQS / name).read_bytes()
        path = dest / "executed-iqs-source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        frozen[name] = hashlib.sha256(raw).hexdigest()
    (dest / "executed-runner.py").write_bytes(Path(__file__).read_bytes())
    (dest / "executed-guard.py").write_bytes((OWN / "guard/sitecustomize.py").read_bytes())
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(IQS / "scripts"), str(IQS / "tests")]),
        E97_OWNED_ROOT=str(OWN), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
        PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    tests = ["tests/test_external_search_result_contract.py"]
    if args.producer:
        env["PYTHONPATH"] = os.pathsep.join([str(OWN / "guard"), str(OWN / "qa"), str(OWN / "qa/src")])
        names = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))["files"]
        for name in names:
            if not (OWN / "qa" / name).is_file(): continue
            raw = (OWN / "qa" / name).read_bytes()
            path = dest / "executed-source" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            private[name] = hashlib.sha256(raw).hexdigest()
        tests = ["tests/unit/test_quick_scan_external_context.py", "tests/unit/test_models.py"]
        if args.affected:
            tests += ["tests/unit/test_external_search_provider.py", "tests/unit/test_quick_scan_cost_resolver.py",
                "tests/unit/test_quick_scan_work_store.py", "tests/unit/test_quick_scan_budget.py",
                "tests/unit/test_qa_net01_search_boundary.py", "tests/unit/test_llm_client.py",
                "tests/unit/test_quick_scan_work_transport.py", "tests/unit/test_quick_scan_c06_complete_seal.py",
                "tests/unit/test_qa_net01_c06_seal.py", "tests/unit/test_llm_provider.py",
                "tests/unit/test_llm_runner.py", "tests/unit/test_llm_integration.py"]
    elif args.affected:
        tests += ["tests/test_stockqa_adapter.py", "tests/test_routing.py", "tests/test_question_sets.py"]
        name = tests[-1]
        raw = (IQS / name).read_bytes()
        path = dest / "executed-iqs-source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        frozen[name] = hashlib.sha256(raw).hexdigest()
    command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", *tests, "-q", "-o", "addopts=",
        "-p", "no:cacheprovider", "--basetemp=" + str(OWN / "tmp" / args.label),
        "--junitxml=" + str(log / "junit.xml")]
    if args.producer: command += ["-p", "pytest_asyncio.plugin"]
    if args.select: command += ["-k", args.select]
    start = time.monotonic()
    try:
        process = subprocess.run(command, cwd=OWN / "qa" if args.producer else IQS, env=env, capture_output=True, timeout=300)
        stdout, stderr, code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
    (dest / "stdout.log").write_bytes(stdout)
    (dest / "stderr.log").write_bytes(stderr)
    if (log / "junit.xml").is_file(): (dest / "junit.xml").write_bytes((log / "junit.xml").read_bytes())
    receipt = dict(command=command, returncode=code, timeout=timed_out, wall_s=round(time.monotonic()-start, 3),
        key_environment_removed=True, executed_iqs_source_hashes=frozen,
        executed_source_hashes=private,
        executed_source_unchanged=(all(hashlib.sha256((IQS / n).read_bytes()).hexdigest() == sha for n, sha in frozen.items())
            and all(hashlib.sha256((OWN / "qa" / n).read_bytes()).hexdigest() == sha for n, sha in private.items())),
        owner_files_written=False, paid_calls=0)
    (dest / "process.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("returncode", "timeout", "wall_s", "executed_source_unchanged")}))
    sys.exit(code if code is not None else 124)


if __name__ == "__main__": main()
