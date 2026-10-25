"""Run explicit, complete test partitions without collecting archived copies."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("fast", "integration", "e2e", "native")
PROFILES = (*GROUPS, "offline", "all")
NATIVE_ENV = ("IQS_C06_OWN", "IQS_C06_COMPOSITION_CODE_ROOT", "IQS_C06_COMPANY_ROOT", "IQS_C06_BRIDGE_ROOT")
CHILD = """import sys
def deny(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.sendto'}:
        raise RuntimeError('offline_test_network_forbidden')
sys.addaudithook(deny)
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
"""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_suite_manifest_key:" + key)
        result[key] = value
    return result


def load_suites(root, manifest_path):
    root, manifest_path = Path(root), Path(manifest_path)
    document = json.loads(manifest_path.read_text(encoding="utf8"), object_pairs_hook=unique_object)
    suites = document["suites"]
    if type(document.get("version")) is not int or document["version"] != 1 or not isinstance(suites, dict) or set(suites) != set(GROUPS):
        raise ValueError("test_suite_manifest_version_or_groups_invalid")
    seen = set()
    for group, files in suites.items():
        if not isinstance(files, list) or not files:
            raise ValueError("test_suite_must_be_nonempty:" + group)
        for name in files:
            if (not isinstance(name, str) or "/" in name or "\\" in name
                or not name.startswith("test_") or not name.endswith(".py")):
                raise ValueError("test_suite_file_must_be_a_test_basename")
            if name in seen:
                raise ValueError("test_file_assigned_more_than_once:" + name)
            seen.add(name)
    actual = {path.relative_to(root / "tests").as_posix() for path in (root / "tests").rglob("test_*.py")}
    if seen != actual:
        raise ValueError("test_suite_coverage_mismatch:" + json.dumps({
            "unassigned": sorted(actual - seen), "missing": sorted(seen - actual)}))
    return suites


def selection(profile, suites):
    names = GROUPS if profile == "all" else GROUPS[:-1] if profile == "offline" else (profile,)
    return {name: list(suites[name]) for name in names}


def require_native_environment(environment):
    if environment.get("IQS_C06_RUN_INTEGRATION") != "1" or any(
        not environment.get(name) or not Path(environment[name]).is_dir() for name in NATIVE_ENV):
        raise ValueError("native_requires_existing_explicit_owned_runtime:" + ",".join(NATIVE_ENV))


def clean_environment(temporary, native=False):
    environment = {key: value for key, value in os.environ.items()
        if not any(part in key.casefold() for part in ("api_key", "api-key", "token", "secret", "password"))
        and key not in {"STOCKQA_RUN_LIVE_E2E", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"}}
    environment.update(TEMP=str(temporary), TMP=str(temporary), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    if not native:
        environment.pop("IQS_C06_RUN_INTEGRATION", None)
    return environment


def run_group(root, name, files, output, temp_root=None):
    """One fresh process; network is denied, real API experiments are separate."""
    root, output = Path(root), Path(output)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="iqs-tests-", dir=temp_root) as temporary:
        owned = Path(temporary)
        if owned.resolve().parent != Path(temp_root or tempfile.gettempdir()).resolve():
            raise ValueError("test_temporary_root_outside_selected_parent")
        environment = clean_environment(owned, native=name == "native")
        arguments = ["-q", "-p", "no:cacheprovider", "--durations=20",
            "--basetemp", str(owned / "pytest"), "--junitxml", str(output / (name + ".xml")),
            *[str(root / "tests" / file) for file in files]]
        with (output / (name + ".log")).open("xb") as stream:
            completed = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", CHILD, *arguments],
                cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
            exit_code = completed.returncode
    result = dict(name=name, files=files, exit_code=exit_code,
        elapsed_seconds=round(time.perf_counter() - started, 3), temporary_root_removed=not owned.exists(),
        api_keys_removed=True, network_denied_in_pytest_process=True,
        log=str(output / (name + ".log")))
    xml = output / (name + ".xml")
    if xml.exists():
        suites = ET.parse(xml).getroot()
        rows = [suites] if suites.tag == "testsuite" else list(suites.findall("testsuite")) if suites.tag == "testsuites" else []
        if not rows:
            result.update(exit_code=2, status="invalid_junit", test_counts_unknown=True)
            return result
        result["junit"] = {field: sum(int(row.get(field, "0")) for row in rows)
                           for field in ("tests", "failures", "errors", "skipped")}
        if any(value < 0 for value in result["junit"].values()) or (exit_code == 0 and (
            result["junit"]["tests"] == 0 or result["junit"]["failures"] or result["junit"]["errors"])):
            result.update(exit_code=2, status="junit_exit_mismatch")
    elif exit_code == 0:
        result.update(exit_code=2, status="junit_missing", test_counts_unknown=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILES, default="fast", nargs="?")
    parser.add_argument("--plan", action="store_true", help="List files only; do not import tests or start a process")
    parser.add_argument("--temp-root", type=Path, help="Existing short temporary parent on Windows; only a unique child is removed")
    options = parser.parse_args(argv)
    try:
        manifest = ROOT / "tests/suites.json"
        suites = load_suites(ROOT, manifest)
        selected = selection(options.profile, suites)
        if options.plan:
            print(json.dumps(dict(profile=options.profile, files=selected,
                file_count=sum(map(len, selected.values())), all_file_count=sum(map(len, suites.values()))), indent=2))
            return 0
        if options.temp_root is not None and not options.temp_root.is_dir():
            raise ValueError("test_temporary_parent_must_exist")
        if "native" in selected:
            require_native_environment(os.environ)
        output = ROOT / "runs/test-reports" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
        output.mkdir(parents=True, exist_ok=False)
        results = []
        for group, files in selected.items():
            # Native modules clear process globals at import. Never collect
            # these two modules together or alongside ordinary test modules.
            partitions = [("native-" + Path(file).stem, [file]) for file in files] if group == "native" else [(group, files)]
            for name, partition in partitions:
                # Keep the native label for environment setup while giving
                # each process distinct log/XML names.
                try:
                    if group == "native":
                        child_output = output / name
                        child_output.mkdir()
                        result = run_group(ROOT, "native", partition, child_output, options.temp_root)
                    else:
                        result = run_group(ROOT, name, partition, output, options.temp_root)
                except (OSError, ET.ParseError) as error:
                    result = dict(name=name, files=partition, exit_code=2,
                        status="runner_error", reason=str(error), test_counts_unknown=True)
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                if result["exit_code"]:
                    break
            if results[-1]["exit_code"]:
                break
        report = dict(profile=options.profile, planned_files=selected, results=results,
            suite_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            all_selected_partitions_executed=len(results) == sum(len(v) if k == "native" else 1 for k, v in selected.items()),
            paid_live_experiments_included=False, output_directory=str(output))
        (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        return next((row["exit_code"] for row in results if row["exit_code"]), 0)
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps(dict(status="blocked", reason=str(error))), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
