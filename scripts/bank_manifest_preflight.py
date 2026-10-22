"""Pre-flight checks for a composed bank manifest.

Why this exists: the 2026-10-19 "37-question complete bank run" was recorded as
"still running in the background" while its output directory stayed empty. The
compose step had rejected the profile earlier (an operating company needs at
least one industry module) and nothing verified that a runnable manifest existed
before the scan was declared underway. These checks make that failure loud and
cheap: no network, no credentials, no model calls.

Usage:
    python -B -X utf8 scripts/bank_manifest_preflight.py --manifest <path>
Exit codes: 0 = runnable, 2 = manifest is not runnable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REQUIRED_QUESTION_FIELDS = ("id", "question", "module_id", "prompt", "prompt_sha256")
HASH_FIELDS = ("prompt_sha256", "semantic_sha256", "definition_sha256")


def preflight(manifest_path: Path) -> dict:
    document = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    problems: list[str] = []
    warnings: list[str] = []

    questions = document.get("questions")
    if not isinstance(questions, list) or not questions:
        return {"ok": False, "problems": ["manifest has no questions"],
                "question_count": 0, "module_count": 0, "modules": []}

    modules = document.get("modules") or []
    if not isinstance(modules, list) or not modules:
        problems.append("manifest declares no modules")

    # Every question needs the identity fields the scan records.
    for question in questions:
        qid = question.get("id") or "<missing id>"
        for field in REQUIRED_QUESTION_FIELDS:
            if not question.get(field):
                problems.append(f"{qid}: missing {field}")
        for field in HASH_FIELDS:
            value = question.get(field)
            if not value:
                problems.append(f"{qid}: missing {field}")
            elif len(value) != 64:
                problems.append(f"{qid}: {field} is not a sha256")

    # The prompt hash must describe the prompt text actually shipped.
    for question in questions:
        prompt, expected = question.get("prompt"), question.get("prompt_sha256")
        if not prompt or not expected:
            continue
        actual = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if actual != expected:
            problems.append(f"{question['id']}: prompt_sha256 does not match its prompt")

    # Duplicate ids would silently overwrite answers.
    ids = [q.get("id") for q in questions]
    duplicates = sorted({i for i in ids if i and ids.count(i) > 1})
    if duplicates:
        problems.append("duplicate question ids: " + ", ".join(duplicates))

    # Every selected module must be pinned by a lock.
    locked = {lock.get("module_id") for lock in (document.get("module_locks") or [])}
    unlocked = [m for m in modules if m not in locked]
    if unlocked:
        problems.append("modules without a lock: " + ", ".join(unlocked))

    # Core/context split drives the reported core score; both must be labelled.
    roles = {q.get("comparison_role") for q in questions}
    if None in roles:
        problems.append("some questions have no comparison_role")
    if "core" not in roles:
        problems.append("no question is marked core; the scan would report nothing")
    if "context" not in roles:
        warnings.append("no context questions; every question counts toward the core score")

    deferred = document.get("deferred_questions") or []
    if deferred:
        warnings.append(f"{len(deferred)} question(s) deferred by the composer")

    # Replacements are intentional: a type/industry module can substitute its own
    # question for a generic one (e.g. OPERATING_01 replaces IQS_11) so the core
    # count stays fixed. Report them, and verify each target actually shipped.
    replacements = document.get("replacements") or {}
    if isinstance(replacements, dict) and replacements:
        shipped = set(ids)
        for replaced, replacement in sorted(replacements.items()):
            if replacement not in shipped:
                problems.append(f"replacement {replacement} (for {replaced}) is not in the manifest")
        report_replacements = dict(replacements)
    else:
        report_replacements = {}

    for field in ("module_package_id", "module_release_id"):
        if not document.get(field):
            problems.append(f"manifest lacks {field}")

    return {
        "ok": not problems,
        "problems": problems,
        "warnings": warnings,
        "question_count": len(questions),
        "core_count": sum(1 for q in questions if q.get("comparison_role") == "core"),
        "context_count": sum(1 for q in questions if q.get("comparison_role") == "context"),
        "module_count": len(modules),
        "modules": modules,
        "replacements": report_replacements,
        "package_id": document.get("module_package_id"),
        "release_id": document.get("module_release_id"),
    }


def check_credentials(*, user_scope: bool = False) -> dict:
    """Report whether the configured search and model keys are resolvable.

    A missing key used to surface only as an all-questions-insufficient run with
    exit 0. Checking up front makes the blocker explicit and free.

    Windows keeps user variables out of an already-running process, so `user_scope`
    also reads HKCU\\Environment — that is where this machine actually stores them.
    """
    import os

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import model_config

    def user_env() -> dict:
        if not user_scope:
            return {}
        try:
            import winreg
        except ImportError:
            return {}
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                values, index = {}, 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    values[name] = value
                    index += 1
                return values
        except OSError:
            return {}

    scope = user_env()
    report: dict[str, object] = {"checked": [], "missing": []}
    for kind, entries in (("search", model_config.search()), ("model", model_config.models())):
        for entry in entries:
            name = entry["key_env"]
            present = bool(os.environ.get(name) or scope.get(name))
            report["checked"].append({"kind": kind, "id": entry["id"], "key_env": name, "present": present})
            if not present:
                report["missing"].append(name)
    report["missing"] = sorted(set(report["missing"]))
    report["ok"] = not report["missing"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline pre-flight for a composed bank manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--check-credentials", action="store_true",
                        help="also verify the search/model API keys resolve (offline)")
    parser.add_argument("--user-scope-env", action="store_true",
                        help="with --check-credentials, also read HKCU\\Environment")
    args = parser.parse_args()
    if not args.manifest.is_file():
        print(json.dumps({"ok": False, "problems": ["manifest not found"]}, ensure_ascii=False))
        return 2
    report = preflight(args.manifest)
    if args.check_credentials:
        report["credentials"] = check_credentials(user_scope=args.user_scope_env)
        if not report["credentials"]["ok"]:
            report["ok"] = False
            report["problems"].append(
                "missing credentials: " + ", ".join(report["credentials"]["missing"]))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
