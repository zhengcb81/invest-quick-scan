#!/usr/bin/env python3
"""Read-only verifier for sealed task-receipt v2 evidence.

The command only reads explicitly registered local roots and emits a JSON
validation sidecar to stdout. It never executes commands stored in a receipt,
changes a receipt/status, contacts the network, or emits evidence contents.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # Fail closed at validation time if the runtime lacks the contract validator.
    Draft202012Validator = None  # type: ignore[assignment,misc]


HASH_ALGORITHM = "canonical-json-sha256-v1"
SIDECAR_VERSION = "task-receipt-validation/1"
MAX_JSON_BYTES = 20 * 1024 * 1024
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
SENSITIVE_SEGMENTS = {
    ".git", ".env", "secrets", "secret", "company-wiki", "companies",
    "raw", "financial_reports", "web_body", "web_bodies", "web_cache",
    "web_results", "downloads", "credentials",
}
SNAPSHOT_SUFFIXES = {".py", ".json", ".md", ".yaml", ".yml", ".toml", ".txt", ".ps1", ".sh"}
HEX_SHA256 = re.compile(r"^[a-f0-9]{64}$")
SELECTOR_SECRET = re.compile(
    r"(?i)(?:sk-[a-z0-9_-]{12,}|(?:api[_-]?key|access[_-]?token|secret(?:[_-]?key)?|password|credential|bearer)[\s_:=.-]+[a-z0-9+/=_-]{8,}|[a-z0-9+/]{40,})"
)
SENSITIVE_FILE_NAMES = {
    "llm_apis.json", "provider-settings.toml", "provider_settings.toml",
    "credentials.json", "credentials.toml", "api_keys.json", "api_keys.toml",
}


class ReceiptError(Exception):
    """Safe-to-report validation failure; messages never contain file data."""


def canonical_json_bytes(value: Any) -> bytes:
    """Frozen cross-run canonicalization: UTF-8, sorted keys, compact, no NaN."""
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReceiptError("canonical_json_invalid") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _json_from_bytes(data: bytes, label: str) -> Any:
    if len(data) > MAX_JSON_BYTES:
        raise ReceiptError(f"{label}_too_large")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ReceiptError("json_duplicate_key")
            value[key] = item
        return value

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"{label}_invalid_json") from exc


def _validate_schema(receipt: Any) -> None:
    if Draft202012Validator is None:
        raise ReceiptError("json_schema_validator_unavailable")
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "quick_scan" / "task-receipt.schema.json"
    try:
        schema = _json_from_bytes(schema_path.read_bytes(), "receipt_schema")
        errors = list(Draft202012Validator(schema).iter_errors(receipt))
    except (OSError, ValueError, TypeError) as exc:
        raise ReceiptError("receipt_schema_unavailable") from exc
    if errors:
        # Do not expose schema instance values or receipt contents in CLI output.
        raise ReceiptError("receipt_schema_invalid")


def _root_map(items: list[str]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise ReceiptError("root_registration_invalid")
        root_id, raw_path = item.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", root_id) or not raw_path:
            raise ReceiptError("root_registration_invalid")
        if root_id in roots:
            raise ReceiptError("root_registration_duplicate")
        try:
            path = Path(raw_path).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ReceiptError("registered_root_missing") from exc
        if not path.is_dir():
            raise ReceiptError("registered_root_not_directory")
        if any(part.casefold() in SENSITIVE_SEGMENTS for part in path.parts):
            raise ReceiptError("sensitive_root_rejected")
        roots[root_id] = path
    if not roots:
        raise ReceiptError("registered_root_required")
    return roots


def _safe_relative(relative: Any) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ReceiptError("path_invalid")
    if relative.startswith("/") or "//" in relative or any(part in {"", "."} for part in relative.split("/")):
        raise ReceiptError("path_escape_rejected")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ReceiptError("path_escape_rejected")
    if any(part.casefold() in SENSITIVE_SEGMENTS for part in path.parts):
        raise ReceiptError("sensitive_path_rejected")
    basename = path.name.casefold()
    if (basename in SENSITIVE_FILE_NAMES or basename.startswith(".env") or
            basename.endswith((".pem", ".key"))):
        raise ReceiptError("sensitive_path_rejected")
    return path.parts


def resolve_ref(ref: Any, roots: dict[str, Path], *, max_bytes: int = MAX_EVIDENCE_BYTES) -> Path:
    if not isinstance(ref, dict):
        raise ReceiptError("rooted_path_invalid")
    root_id, relative = ref.get("root_id"), ref.get("path")
    if not isinstance(root_id, str) or root_id not in roots:
        raise ReceiptError("root_not_registered")
    parts = _safe_relative(relative)
    root = roots[root_id]
    candidate = root.joinpath(*parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ReceiptError("evidence_file_missing") from exc
    try:
        resolved_relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ReceiptError("path_escape_rejected") from exc
    # Check the resolved target as well as its lexical alias. An in-root
    # symlink can otherwise hide a path into a protected subtree.
    _safe_relative(resolved_relative.as_posix())
    if not resolved.is_file():
        raise ReceiptError("evidence_not_regular_file")
    try:
        stat = resolved.stat()
        if stat.st_nlink > 1:
            raise ReceiptError("hardlink_evidence_rejected")
        if stat.st_size > max_bytes:
            raise ReceiptError("evidence_file_too_large")
    except OSError as exc:
        raise ReceiptError("evidence_file_unreadable") from exc
    return resolved


def _task_change_patterns(task: dict[str, Any]) -> list[str]:
    allowed = task.get("allowed_changes")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(item, str) for item in allowed):
        raise ReceiptError("task_allowed_changes_invalid")
    patterns: list[str] = []
    for declaration in allowed:
        # Plans may attach human-readable notes in parentheses and combine
        # related paths with the Chinese conjunction used in this plan.
        paths = declaration.split("（", 1)[0].split("(", 1)[0].strip().split("与")
        for pattern in paths:
            normalized = pattern.strip()
            if normalized:
                patterns.append(normalized)
    return patterns


def _matches_task_change(path: str, task: dict[str, Any]) -> bool:
    for pattern in _task_change_patterns(task):
        if pattern.endswith("/") and path.startswith(pattern):
            return True
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def _check_ref_purpose(ref: Any, purpose: str | None, *, task: dict[str, Any] | None = None,
                       task_id: str | None = None, allowed_paths: set[str] | None = None) -> None:
    if not isinstance(ref, dict):
        raise ReceiptError("rooted_path_invalid")
    parts = _safe_relative(ref.get("path"))
    relative = "/".join(parts)
    if purpose == "control":
        # Receipt, plan and case catalog are explicit operator-selected inputs.
        return
    if purpose == "snapshot":
        if task is None or not _matches_task_change(relative, task):
            raise ReceiptError("snapshot_path_not_allowlisted")
        name = parts[-1].casefold()
        if (relative.startswith("docs/implementation/contracts/validation-") or
                name.startswith("receipt-") or name.endswith("-self-check.json")):
            raise ReceiptError("snapshot_artifact_type_rejected")
        return
    if purpose == "test_log":
        expected_prefix = f"docs/implementation/contracts/validation-{task_id}-" if task_id else None
        if (expected_prefix is None or not relative.startswith(expected_prefix) or
                not relative.casefold().endswith(".log") or len(parts) != 4):
            raise ReceiptError("test_log_path_rejected")
        return
    if purpose == "review_report":
        expected_prefix = f"docs/implementation/reviews/{task_id}/" if task_id else None
        if (expected_prefix is None or not relative.startswith(expected_prefix) or
                not relative.casefold().endswith(".json")):
            raise ReceiptError("review_report_path_rejected")
        return
    if purpose in {"historical_manifest", "historical_context_file"}:
        if allowed_paths is None or relative not in allowed_paths:
            raise ReceiptError("historical_context_path_not_allowlisted")
        return
    if purpose == "dependency_receipt":
        expected = f"docs/implementation/contracts/receipt-{task_id}.json" if task_id else None
        if relative != expected:
            raise ReceiptError("dependency_receipt_path_rejected")
        return
    raise ReceiptError("reference_purpose_invalid")


def read_ref(ref: Any, roots: dict[str, Path], *, purpose: str | None = None,
             task: dict[str, Any] | None = None, task_id: str | None = None,
             allowed_paths: set[str] | None = None, expected_hash: bool = True,
             max_bytes: int = MAX_EVIDENCE_BYTES) -> bytes:
    # Enforce artifact class and task scope before path resolution or opening.
    _check_ref_purpose(ref, purpose, task=task, task_id=task_id, allowed_paths=allowed_paths)
    path = resolve_ref(ref, roots, max_bytes=max_bytes)
    # A safe-looking lexical alias may resolve to a different, ordinary path
    # inside the same root. Reapply the artifact policy to the resolved target.
    root_id = ref.get("root_id")
    try:
        resolved_relative = path.relative_to(roots[root_id]).as_posix()
    except (KeyError, TypeError, ValueError) as exc:
        raise ReceiptError("path_escape_rejected") from exc
    resolved_ref = dict(ref)
    resolved_ref["path"] = resolved_relative
    _check_ref_purpose(resolved_ref, purpose, task=task, task_id=task_id,
                       allowed_paths=allowed_paths)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ReceiptError("evidence_file_unreadable") from exc
    expected = ref.get("sha256") if expected_hash and isinstance(ref, dict) else None
    if expected is not None and (not isinstance(expected, str) or sha256_bytes(data) != expected):
        raise ReceiptError("evidence_hash_mismatch")
    return data


def _load_ref(ref: dict[str, Any], roots: dict[str, Path], label: str) -> Any:
    return _json_from_bytes(read_ref(ref, roots, purpose="control", expected_hash=False,
                                    max_bytes=MAX_JSON_BYTES), label)


def _assertion_ids(case: dict[str, Any]) -> list[str]:
    assertions = case.get("assertions")
    if assertions is not None:
        if not isinstance(assertions, list):
            raise ReceiptError("catalog_assertions_invalid")
        ids = [a.get("id") if isinstance(a, dict) else None for a in assertions]
    else:
        then = case.get("then")
        if not isinstance(then, list):
            raise ReceiptError("catalog_then_invalid")
        ids = [f"{case.get('id')}.T{index:02d}" for index in range(1, len(then) + 1)]
    if not ids or any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ReceiptError("catalog_assertion_ids_invalid")
    return ids


def _dependency_ancestors(task: dict[str, Any], plan: dict[str, Any]) -> set[str]:
    task_id = task.get("id")
    plan_tasks = plan.get("tasks") if isinstance(plan, dict) else None
    if not isinstance(task_id, str) or not task_id or not isinstance(plan_tasks, list):
        raise ReceiptError("case_owner_dependency_invalid")
    by_id: dict[str, dict[str, Any]] = {}
    for item in plan_tasks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ReceiptError("case_owner_dependency_invalid")
        if item["id"] in by_id:
            raise ReceiptError("case_owner_dependency_invalid")
        by_id[item["id"]] = item
    if task_id not in by_id or by_id[task_id] != task:
        raise ReceiptError("case_owner_dependency_invalid")

    ancestors: set[str] = set()
    state: dict[str, int] = {}

    def visit(dependency_id: str) -> None:
        if dependency_id == task_id or state.get(dependency_id) == 1:
            raise ReceiptError("case_owner_dependency_invalid")
        if state.get(dependency_id) == 2:
            return
        dependency_task = by_id.get(dependency_id)
        if dependency_task is None:
            raise ReceiptError("case_owner_dependency_invalid")
        dependencies = dependency_task.get("depends_on", [])
        if (not isinstance(dependencies, list) or
                any(not isinstance(item, str) or not item for item in dependencies) or
                len(dependencies) != len(set(dependencies))):
            raise ReceiptError("case_owner_dependency_invalid")
        state[dependency_id] = 1
        ancestors.add(dependency_id)
        for parent_id in dependencies:
            visit(parent_id)
        state[dependency_id] = 2

    dependencies = task.get("depends_on", [])
    if (not isinstance(dependencies, list) or
            any(not isinstance(item, str) or not item for item in dependencies) or
            len(dependencies) != len(set(dependencies))):
        raise ReceiptError("case_owner_dependency_invalid")
    for dependency_id in dependencies:
        visit(dependency_id)
    return ancestors


def _task_case_bundle(task: dict[str, Any], cases: dict[str, Any],
                      plan: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(cases, dict):
        raise ReceiptError("case_catalog_invalid")
    task_ids = task.get("case_ids")
    if (not isinstance(task_ids, list) or not task_ids or
            any(not isinstance(item, str) or not item for item in task_ids) or
            len(task_ids) != len(set(task_ids))):
        raise ReceiptError("task_case_ids_invalid")
    catalog_cases = cases.get("cases", [])
    if not isinstance(catalog_cases, list):
        raise ReceiptError("case_catalog_invalid")
    by_id: dict[str, dict[str, Any]] = {}
    for case in catalog_cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ReceiptError("case_catalog_invalid")
        if case["id"] in by_id:
            raise ReceiptError("case_catalog_duplicate_id")
        by_id[case["id"]] = case
    plan_tasks = plan.get("tasks") if isinstance(plan, dict) else None
    if not isinstance(plan_tasks, list):
        raise ReceiptError("case_owner_dependency_invalid")
    plan_task_ids: set[str] = set()
    for item in plan_tasks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ReceiptError("case_owner_dependency_invalid")
        if item["id"] in plan_task_ids:
            raise ReceiptError("case_owner_dependency_invalid")
        plan_task_ids.add(item["id"])
    ancestors: set[str] | None = None
    result = []
    for case_id in sorted(task_ids):
        case = by_id.get(case_id)
        if case is None:
            raise ReceiptError("owner_case_missing")
        owner_id = case.get("owner_task")
        if not isinstance(owner_id, str) or not owner_id:
            raise ReceiptError("case_owner_unknown")
        if owner_id != task.get("id"):
            if owner_id not in plan_task_ids:
                raise ReceiptError("case_owner_unknown")
            if ancestors is None:
                ancestors = _dependency_ancestors(task, plan)
            if owner_id not in ancestors:
                raise ReceiptError("case_owner_not_dependency")
        result.append({key: case.get(key) for key in (
            "id", "given", "when", "then", "assertions", "requires_tasks", "owner_task", "status"
        )})
    return result


def _owned_case_bundle(task: dict[str, Any], cases: dict[str, Any],
                       plan: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task.get("id")
    referenced_cases = _task_case_bundle(task, cases, plan)
    referenced_owned = sorted(
        case["id"] for case in referenced_cases if case.get("owner_task") == task_id
    )
    catalog_cases = cases.get("cases", [])
    declared_owned = sorted(
        case["id"] for case in catalog_cases
        if isinstance(case, dict) and case.get("owner_task") == task_id
    )
    if declared_owned != referenced_owned:
        raise ReceiptError("owner_case_set_mismatch")
    result = [case for case in referenced_cases if case.get("owner_task") == task_id]
    all_assertion_ids: list[str] = []
    for case in result:
        all_assertion_ids.extend(_assertion_ids(case))
    if len(all_assertion_ids) != len(set(all_assertion_ids)):
        raise ReceiptError("catalog_assertion_ids_duplicate")
    return result


def _referenced_case_bundle(task: dict[str, Any], cases: dict[str, Any],
                            plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [case for case in _task_case_bundle(task, cases, plan)
            if case.get("owner_task") != task.get("id")]


def _hashes(plan: dict[str, Any], catalog: dict[str, Any], task: dict[str, Any],
            plan_bytes: bytes, catalog_bytes: bytes) -> dict[str, str]:
    return {
        "plan_sha256": sha256_bytes(plan_bytes),
        "case_catalog_sha256": sha256_bytes(catalog_bytes),
        "task_spec_sha256": canonical_sha256(task),
        "owned_case_bundle_sha256": canonical_sha256(_owned_case_bundle(task, catalog, plan)),
        "referenced_case_bundle_sha256": canonical_sha256(_referenced_case_bundle(task, catalog, plan)),
        "global_boundaries_sha256": canonical_sha256(plan.get("global_boundaries")),
    }


def _block(blockers: list[dict[str, Any]], code: str, **context: str) -> None:
    entry = {"code": code}
    entry.update({key: value for key, value in context.items() if value})
    if entry not in blockers:
        blockers.append(entry)


def _selector_is_safe(selector: Any) -> bool:
    """Selectors are auditable labels, but must not become a secret-exfiltration channel."""
    return (isinstance(selector, str) and bool(selector.strip()) and len(selector) <= 1024 and
            not any(ord(char) < 32 for char in selector) and SELECTOR_SECRET.search(selector) is None)


def _path_is_safe_to_display(path: str) -> bool:
    """Check path segments for secrets without treating ordinary separators as token characters."""
    return (bool(path) and len(path) <= 1024 and not any(ord(char) < 32 for char in path) and
            all(SELECTOR_SECRET.search(part) is None for part in path.split("/")))


def _snapshot(core: dict[str, Any], roots: dict[str, Path], blockers: list[dict[str, Any]],
              task: dict[str, Any]) -> str | None:
    entries = core.get("implementation_snapshot")
    if not isinstance(entries, list) or not entries:
        _block(blockers, "implementation_snapshot_missing")
        return None
    seen: set[tuple[str, str]] = set()
    normalized: list[dict[str, str]] = []
    for entry in entries:
        try:
            if not isinstance(entry, dict) or not HEX_SHA256.fullmatch(str(entry.get("sha256", ""))):
                raise ReceiptError("snapshot_entry_invalid")
            parts = _safe_relative(entry.get("path"))
            if Path(parts[-1]).suffix.casefold() not in SNAPSHOT_SUFFIXES:
                raise ReceiptError("snapshot_file_type_rejected")
            key = (entry.get("root_id"), entry.get("path"))
            if key in seen:
                raise ReceiptError("snapshot_duplicate_path")
            seen.add(key)
            data = read_ref(entry, roots, purpose="snapshot", task=task)
            normalized.append({"root_id": key[0], "path": key[1], "sha256": sha256_bytes(data)})
        except ReceiptError as exc:
            _block(blockers, str(exc))
    normalized.sort(key=lambda item: (item["root_id"], item["path"]))
    digest = canonical_sha256(normalized) if len(normalized) == len(entries) else None
    if digest and core.get("implementation_snapshot_sha256") != digest:
        _block(blockers, "implementation_snapshot_hash_mismatch")
    return digest


def _review(core: dict[str, Any], roots: dict[str, Path], current_snapshot: str | None,
            task_id: str,
            blockers: list[dict[str, Any]]) -> None:
    review = core.get("independent_review")
    if not isinstance(review, dict):
        _block(blockers, "independent_review_missing")
        return
    try:
        report_bytes = read_ref(review.get("report"), roots, purpose="review_report", task_id=task_id)
        report = _json_from_bytes(report_bytes, "review_report")
    except ReceiptError as exc:
        _block(blockers, str(exc))
        return
    required = ("reviewer_id", "reviewer_role", "independent", "separation_basis", "outcome", "implementation_snapshot_sha256", "open_findings")
    if not isinstance(report, dict) or any(report.get(key) != review.get(key) for key in required):
        _block(blockers, "review_report_binding_mismatch")
        return
    if any(key in report for key in ("receipt_sha256", "receipt_core_sha256", "sidecar_sha256", "validation_sidecar_sha256")):
        _block(blockers, "review_cycle_reference_rejected")
    if review.get("reviewer_id") == core.get("implementation_author_id"):
        _block(blockers, "reviewer_not_independent")
    if review.get("independent") is not True or not review.get("separation_basis"):
        _block(blockers, "reviewer_not_independent")
    if review.get("outcome") != "approved":
        _block(blockers, "review_not_approved")
    if review.get("implementation_snapshot_sha256") != current_snapshot or current_snapshot is None:
        _block(blockers, "review_stale")
    findings = review.get("open_findings")
    if not isinstance(findings, list):
        _block(blockers, "review_findings_invalid")
    elif any(isinstance(item, dict) and item.get("severity") in {"P0", "P1", "P2"} for item in findings):
        _block(blockers, "review_has_open_p0_p2")


def _validate_assertion(assertion: Any, expected_id: str, roots: dict[str, Path],
                        blockers: list[dict[str, Any]], case_id: str,
                        task_id: str, audit: dict[str, Any] | None = None) -> bool:
    context = {"case_id": case_id, "assertion_id": expected_id}
    if not isinstance(assertion, dict) or assertion.get("assertion_id") != expected_id:
        _block(blockers, "assertion_missing_duplicate_or_unexpected", **context)
        return False
    valid = True
    if assertion.get("status") != "passed":
        _block(blockers, "assertion_not_passed", **context)
        valid = False
    if assertion.get("test_stage") not in {"unit", "contract", "integration", "e2e", "review"}:
        _block(blockers, "test_stage_invalid", **context)
        valid = False
    if not _selector_is_safe(assertion.get("selector")):
        code = "test_selector_missing" if not isinstance(assertion.get("selector"), str) or not assertion["selector"].strip() else "test_selector_unsafe"
        _block(blockers, code, **context)
        valid = False
    if not isinstance(assertion.get("command"), str) or not assertion["command"].strip():
        _block(blockers, "reproducible_command_missing", **context)
        valid = False
    if assertion.get("exit_code") != 0:
        _block(blockers, "test_exit_code_nonzero_or_missing", **context)
        valid = False
    if type(assertion.get("skip_count")) is not int or assertion.get("skip_count") != 0:
        _block(blockers, "test_skipped_or_skip_count_invalid", **context)
        valid = False
    if audit is not None:
        evidence = audit.get("log_evidence")
        if not isinstance(evidence, dict):
            _block(blockers, "test_log_reference_invalid", **context)
            valid = False
        elif evidence.get("error_code"):
            _block(blockers, str(evidence["error_code"]), **context)
            valid = False
    else:
        log = assertion.get("log")
        try:
            if not isinstance(log, dict) or not HEX_SHA256.fullmatch(str(log.get("sha256", ""))):
                raise ReceiptError("test_log_reference_invalid")
            log_data = read_ref(log, roots, purpose="test_log", task_id=task_id)
            if not log_data.strip():
                raise ReceiptError("test_log_empty")
        except ReceiptError as exc:
            _block(blockers, str(exc), **context)
            valid = False
    isolation = assertion.get("isolation")
    if (not isinstance(isolation, dict) or isolation.get("isolated") is not True or
            isolation.get("cleanup_verified") is not True or
            not isinstance(isolation.get("run_id"), str) or not isolation.get("run_id", "").strip() or
            not isinstance(isolation.get("cleanup_summary"), str) or not isolation.get("cleanup_summary", "").strip()):
        _block(blockers, "isolation_or_cleanup_unverified", **context)
        valid = False
    network = assertion.get("network")
    if (not isinstance(network, dict) or network.get("mode") not in {"none", "stubbed", "live"} or
            type(network.get("request_count")) is not int or network.get("request_count", -1) < 0 or
            not isinstance(network.get("evidence"), str) or not network.get("evidence", "").strip()):
        _block(blockers, "network_evidence_missing", **context)
        valid = False
    fee = network.get("fees_usd") if isinstance(network, dict) else None
    if fee is not None and (not isinstance(fee, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", fee)):
        _block(blockers, "network_fee_invalid", **context)
        valid = False
    return valid


def _audit_assertion(assertion: Any, expected_id: str, roots: dict[str, Path],
                     task_id: str) -> dict[str, Any]:
    """Build a safe sidecar projection; never expose the recorded command or log body."""
    result: dict[str, Any] = {
        "assertion_id": expected_id, "status": "missing", "test_stage": None,
        "selector": None, "exit_code": None, "skip_count": None,
        "log_evidence": None, "checks": {},
    }
    if not isinstance(assertion, dict) or assertion.get("assertion_id") != expected_id:
        result["status"] = "missing_or_duplicate"
        return result

    status = assertion.get("status")
    stage = assertion.get("test_stage")
    selector = assertion.get("selector")
    exit_code = assertion.get("exit_code")
    skip_count = assertion.get("skip_count")
    result.update({
        "reported_status": status if status in {"passed", "failed", "not_run", "not_applicable"} else "invalid",
        "test_stage": stage if stage in {"unit", "contract", "integration", "e2e", "review"} else None,
        "selector": selector if _selector_is_safe(selector) else None,
        "exit_code": exit_code if type(exit_code) is int else None,
        "skip_count": skip_count if type(skip_count) is int else None,
    })
    selector_valid = _selector_is_safe(selector)
    stage_valid = stage in {"unit", "contract", "integration", "e2e", "review"}
    command_recorded = isinstance(assertion.get("command"), str) and bool(assertion["command"].strip())
    exit_zero = exit_code == 0
    skip_zero = type(skip_count) is int and skip_count == 0
    isolation = assertion.get("isolation")
    isolation_valid = (isinstance(isolation, dict) and isolation.get("isolated") is True and
                       isolation.get("cleanup_verified") is True and
                       isinstance(isolation.get("run_id"), str) and bool(isolation.get("run_id", "").strip()) and
                       isinstance(isolation.get("cleanup_summary"), str) and bool(isolation.get("cleanup_summary", "").strip()))
    network = assertion.get("network")
    network_valid = (isinstance(network, dict) and network.get("mode") in {"none", "stubbed", "live"} and
                     type(network.get("request_count")) is int and network.get("request_count", -1) >= 0 and
                     isinstance(network.get("evidence"), str) and bool(network.get("evidence", "").strip()) and
                     (network.get("fees_usd") is None or
                      (isinstance(network.get("fees_usd"), str) and
                       re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", network["fees_usd"]) is not None)))

    evidence: dict[str, Any] = {"root_id": None, "path": None, "expected_sha256": None,
                                "actual_sha256": None, "hash_valid": False,
                                "nonempty": False, "error_code": None}
    log = assertion.get("log")
    readable = False
    nonempty = False
    hash_valid = False
    try:
        if not isinstance(log, dict):
            raise ReceiptError("test_log_reference_invalid")
        root_id = log.get("root_id")
        if isinstance(root_id, str) and root_id in roots:
            evidence["root_id"] = root_id
        parts = _safe_relative(log.get("path"))
        display_path = "/".join(parts)
        if not _path_is_safe_to_display(display_path):
            raise ReceiptError("test_log_path_unsafe")
        evidence["path"] = display_path
        expected = log.get("sha256")
        if isinstance(expected, str) and HEX_SHA256.fullmatch(expected):
            evidence["expected_sha256"] = expected
        else:
            raise ReceiptError("test_log_reference_invalid")
        data = read_ref(log, roots, purpose="test_log", task_id=task_id, expected_hash=False)
        actual = sha256_bytes(data)
        readable = True
        nonempty = bool(data.strip())
        hash_valid = actual == expected
        evidence.update({"actual_sha256": actual, "hash_valid": hash_valid, "nonempty": nonempty})
        if not hash_valid:
            raise ReceiptError("evidence_hash_mismatch")
        if not nonempty:
            raise ReceiptError("test_log_empty")
    except ReceiptError as exc:
        evidence["error_code"] = str(exc)

    result["log_evidence"] = evidence
    result["checks"] = {
        "test_stage_valid": stage_valid,
        "selector_present": selector_valid,
        "command_recorded": command_recorded,
        "exit_code_zero": exit_zero,
        "skip_count_zero": skip_zero,
        "log_readable": readable,
        "log_nonempty": nonempty,
        "log_hash_valid": hash_valid,
        "isolation_verified": isolation_valid,
        "network_evidence_present": network_valid,
    }
    validation_status = "passed" if status == "passed" and all(result["checks"].values()) else "blocked"
    result["status"] = validation_status
    result["validation_status"] = validation_status
    return result


def _is_known_legacy_receipt(receipt: dict[str, Any]) -> bool:
    """Accept only pre-versioned legacy receipts or the declared v1 envelope."""
    return "schema_version" not in receipt or receipt.get("schema_version") == "1.0"


def _dependency_map(core: dict[str, Any], task: dict[str, Any], roots: dict[str, Path],
                    plan: dict[str, Any], catalog: dict[str, Any], blockers: list[dict[str, Any]],
                    visiting: set[str]) -> None:
    dependencies = task.get("depends_on", [])
    historical = task.get("historical_context_dependencies", [])
    if (not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies) or
            len(dependencies) != len(set(dependencies)) or not isinstance(historical, list) or
            any(not isinstance(item, str) for item in historical) or not set(historical).issubset(set(dependencies))):
        _block(blockers, "task_dependency_declaration_invalid")
        return
    records = core.get("dependency_evidence")
    if not isinstance(records, list):
        _block(blockers, "dependency_evidence_missing")
        return
    ids = [item.get("task_id") if isinstance(item, dict) else None for item in records]
    if len(ids) != len(set(ids)) or set(ids) != set(dependencies):
        _block(blockers, "dependency_evidence_set_mismatch")
        return
    for dep_id in dependencies:
        item = next((x for x in records if isinstance(x, dict) and x.get("task_id") == dep_id), None)
        if item is None:
            _block(blockers, "dependency_evidence_missing", task_id=dep_id)
            continue
        if dep_id in historical:
            if item.get("kind") != "historical_context" or item.get("status") != "context_only":
                _block(blockers, "historical_dependency_misrepresented", task_id=dep_id)
                continue
            try:
                approved_edges = [
                    edge for edge in plan.get("historical_context_edges", [])
                    if isinstance(edge, dict) and edge.get("task_id") == task.get("id") and edge.get("dependency_task_id") == dep_id
                ]
                if len(approved_edges) != 1:
                    raise ReceiptError("historical_context_edge_not_allowlisted")
                if item.get("evidence", {}).get("path") != approved_edges[0].get("manifest_path"):
                    raise ReceiptError("historical_context_manifest_path_mismatch")
                manifest_data = read_ref(item.get("evidence"), roots, purpose="historical_manifest",
                                         allowed_paths={approved_edges[0]["manifest_path"]})
                manifest = _json_from_bytes(manifest_data, "historical_context_manifest")
                if not isinstance(manifest, dict) or manifest.get("dependency_task_id") != dep_id or manifest.get("status") != "context_only":
                    raise ReceiptError("historical_context_manifest_invalid")
                entries = manifest.get("files")
                if not isinstance(entries, list) or not entries:
                    raise ReceiptError("historical_context_manifest_empty")
                if dep_id == "P00":
                    expected_paths = {
                        "docs/implementation/baselines/baseline-report-2026-09-22.md",
                        "docs/implementation/baselines/receipt-P00.json",
                    }
                    actual_paths = []
                    for entry in entries:
                        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                            raise ReceiptError("historical_context_manifest_entry_invalid")
                        actual_paths.append(entry["path"])
                    if set(actual_paths) != expected_paths or len(actual_paths) != len(expected_paths):
                        raise ReceiptError("historical_context_file_set_mismatch")
                if manifest.get("eligibility_effect") != "does_not_satisfy_current_dependency_or_close_gate":
                    raise ReceiptError("historical_context_effect_invalid")
                old_receipts = []
                for entry in entries:
                    data = read_ref(entry, roots, purpose="historical_context_file",
                                    allowed_paths=expected_paths if dep_id == "P00" else None)
                    if Path(str(entry.get("path", ""))).name == f"receipt-{dep_id}.json":
                        old_receipts.append(_json_from_bytes(data, "legacy_dependency_receipt"))
                if (len(old_receipts) != 1 or not isinstance(old_receipts[0], dict) or
                        old_receipts[0].get("task_id") != dep_id or not _is_known_legacy_receipt(old_receipts[0])):
                    raise ReceiptError("historical_dependency_receipt_not_legacy")
            except ReceiptError as exc:
                _block(blockers, str(exc), task_id=dep_id)
            continue
        if item.get("kind") != "current_receipt" or item.get("status") != "eligible_to_close":
            _block(blockers, "current_dependency_not_verified", task_id=dep_id)
            continue
        # The ordinary dependency evidence is recursively verified from the current plan.
        try:
            raw = read_ref(item.get("evidence"), roots, purpose="dependency_receipt", task_id=dep_id)
            child = _json_from_bytes(raw, "dependency_receipt")
            expected_digest = item["evidence"].get("sha256")
            if sha256_bytes(raw) != expected_digest:
                raise ReceiptError("dependency_receipt_hash_mismatch")
            if not isinstance(child, dict) or not isinstance(child.get("core"), dict) or child["core"].get("task_id") != dep_id:
                raise ReceiptError("dependency_task_identity_mismatch")
            result = _verify_loaded(child, plan, catalog, roots, None, visiting)
            if not result.get("eligible_to_close"):
                _block(blockers, "current_dependency_not_eligible", task_id=dep_id)
        except (ReceiptError, KeyError) as exc:
            _block(blockers, str(exc) if isinstance(exc, ReceiptError) else "dependency_evidence_invalid", task_id=dep_id)


def _verify_loaded(receipt: Any, plan: dict[str, Any], catalog: dict[str, Any], roots: dict[str, Path],
                   plan_hashes: tuple[bytes, bytes] | None, visiting: set[str]) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "2.0":
        return {"eligible_to_close": False, "status": "legacy_historical", "blockers": []}
    core = receipt.get("core")
    if not isinstance(core, dict):
        return {"eligible_to_close": False, "status": "blocked", "blockers": [{"code": "receipt_core_invalid"}]}
    try:
        _validate_schema(receipt)
    except ReceiptError as exc:
        _block(blockers, str(exc))
        return {"eligible_to_close": False, "status": "blocked", "blockers": blockers,
                "core_sha256": canonical_sha256(core)}
    core_hash = canonical_sha256(core)
    if receipt.get("core_sha256") != core_hash:
        _block(blockers, "receipt_core_hash_mismatch")
    task_id = core.get("task_id")
    if not isinstance(task_id, str):
        _block(blockers, "task_id_missing")
        task = {}
    else:
        if task_id in visiting:
            _block(blockers, "dependency_cycle", task_id=task_id)
            return {"eligible_to_close": False, "status": "blocked", "blockers": blockers,
                    "core_sha256": core_hash, "case_results": []}
        plan_tasks = plan.get("tasks", [])
        matching_tasks = [item for item in plan_tasks if isinstance(item, dict) and item.get("id") == task_id] if isinstance(plan_tasks, list) else []
        task = matching_tasks[0] if len(matching_tasks) == 1 else {}
        if isinstance(plan_tasks, list) and len(matching_tasks) > 1:
            _block(blockers, "plan_task_id_duplicate", task_id=task_id)
    if not task:
        _block(blockers, "task_not_in_current_plan")
        return {"eligible_to_close": False, "status": "blocked", "blockers": blockers, "core_sha256": core_hash}
    visiting = set(visiting)
    visiting.add(task_id)
    hashes: dict[str, str] | None = None
    try:
        hashes = _hashes(plan, catalog, task, *(plan_hashes or (b"", b"")))
        for key in ("task_spec_sha256", "owned_case_bundle_sha256", "global_boundaries_sha256"):
            if core.get(key) != hashes[key]:
                _block(blockers, f"{key}_stale")
    except ReceiptError as exc:
        _block(blockers, str(exc))
    # Provenance hashes are intentionally ignored for freshness: unrelated plan/catalog edits must not stale this task.
    audit_cases: list[dict[str, Any]] = []
    audit_by_assertion: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        # Receipts record results for every case listed on this downstream task,
        # including upstream-owned cases used as regression checks. Only the
        # owner's cases participate in the owned-case freshness hash.
        expected_cases = _task_case_bundle(task, catalog, plan)
        referenced_cases = [case for case in expected_cases if case.get("owner_task") != task_id]
        referenced_case_hash = core.get("referenced_case_bundle_sha256")
        if referenced_cases and not isinstance(referenced_case_hash, str):
            _block(blockers, "referenced_case_bundle_sha256_missing")
        elif (referenced_case_hash is not None and hashes is not None and
              referenced_case_hash != hashes.get("referenced_case_bundle_sha256")):
            _block(blockers, "referenced_case_bundle_sha256_stale")
        expected_by_id = {item["id"]: item for item in expected_cases}
        results = core.get("case_results")
        if not isinstance(results, list):
            raise ReceiptError("case_results_invalid")
        received_ids = [item.get("case_id") if isinstance(item, dict) else None for item in results]
        if len(received_ids) != len(set(received_ids)) or set(received_ids) != set(expected_by_id):
            _block(blockers, "case_result_set_mismatch")
        for expected_case_id in sorted(expected_by_id):
            matching_case_results = [item for item in results if isinstance(item, dict) and item.get("case_id") == expected_case_id]
            if len(matching_case_results) != 1:
                audit_cases.append({
                    "case_id": expected_case_id,
                    "reported_status": "missing" if not matching_case_results else "duplicate",
                    "status": "blocked",
                    "assertions": [{
                        "assertion_id": assertion_id, "status": "missing_or_duplicate",
                        "test_stage": None, "selector": None, "exit_code": None,
                        "skip_count": None, "log_evidence": None, "checks": {},
                    } for assertion_id in _assertion_ids(expected_by_id[expected_case_id])],
                })
                continue
            case_result = matching_case_results[0]
            case_assertions = case_result.get("assertions")
            audit_assertions = []
            if isinstance(case_assertions, list):
                for expected_assertion_id in _assertion_ids(expected_by_id[expected_case_id]):
                    candidates = [item for item in case_assertions if isinstance(item, dict) and item.get("assertion_id") == expected_assertion_id]
                    if len(candidates) == 1:
                        audit_assertion = _audit_assertion(candidates[0], expected_assertion_id, roots, task_id)
                        audit_by_assertion[(expected_case_id, expected_assertion_id)] = audit_assertion
                        if audit_assertion.get("validation_status") != "passed" and audit_assertion.get("reported_status") == "passed":
                            _block(blockers, "assertion_audit_check_failed", case_id=expected_case_id,
                                   assertion_id=expected_assertion_id)
                        audit_assertions.append(audit_assertion)
                    else:
                        audit_assertions.append({
                            "assertion_id": expected_assertion_id,
                            "status": "missing" if not candidates else "duplicate",
                            "test_stage": None, "selector": None, "exit_code": None,
                            "skip_count": None, "log_evidence": None, "checks": {},
                        })
            else:
                audit_assertions = [{
                    "assertion_id": assertion_id, "status": "missing", "test_stage": None,
                    "selector": None, "exit_code": None, "skip_count": None,
                    "log_evidence": None, "checks": {},
                } for assertion_id in _assertion_ids(expected_by_id[expected_case_id])]
            case_validated = (case_result.get("status") == "passed" and bool(audit_assertions) and
                              all(item.get("validation_status") == "passed" for item in audit_assertions))
            audit_cases.append({"case_id": expected_case_id,
                                "reported_status": case_result.get("status", "invalid"),
                                "status": "passed" if case_validated else "blocked",
                                "assertions": audit_assertions})
        for case_result in results:
            if not isinstance(case_result, dict) or case_result.get("case_id") not in expected_by_id:
                _block(blockers, "unexpected_case_result")
                continue
            case_id = case_result["case_id"]
            expected_assertions = _assertion_ids(expected_by_id[case_id])
            assertions = case_result.get("assertions")
            if not isinstance(assertions, list):
                _block(blockers, "assertion_results_invalid", case_id=case_id)
                continue
            assertion_ids = [item.get("assertion_id") if isinstance(item, dict) else None for item in assertions]
            if len(assertion_ids) != len(set(assertion_ids)) or assertion_ids != expected_assertions:
                _block(blockers, "assertion_result_set_mismatch", case_id=case_id)
            if case_result.get("status") != "passed":
                _block(blockers, "case_not_passed", case_id=case_id)
            for expected_id in expected_assertions:
                candidates = [item for item in assertions if isinstance(item, dict) and item.get("assertion_id") == expected_id]
                if len(candidates) != 1:
                    _block(blockers, "assertion_missing_duplicate_or_unexpected", case_id=case_id, assertion_id=expected_id)
                    continue
                _validate_assertion(candidates[0], expected_id, roots, blockers, case_id, task_id,
                                    audit_by_assertion.get((case_id, expected_id)))
    except ReceiptError as exc:
        _block(blockers, str(exc))
    snapshot_hash = _snapshot(core, roots, blockers, task)
    _review(core, roots, snapshot_hash, task_id, blockers)
    _dependency_map(core, task, roots, plan, catalog, blockers, visiting)
    return {
        "eligible_to_close": not blockers,
        "status": "eligible_to_close" if not blockers else "blocked",
        "blockers": blockers,
        "core_sha256": core_hash,
        "case_results": audit_cases,
    }


def verify_receipt(receipt_ref: dict[str, Any], plan_ref: dict[str, Any], catalog_ref: dict[str, Any],
                   roots: dict[str, Path], *, evaluated_at: str | None = None) -> dict[str, Any]:
    """Verify a receipt and return a detached sidecar-shaped result; performs no writes."""
    try:
        raw_receipt = read_ref(receipt_ref, roots, purpose="control", expected_hash=False,
                               max_bytes=MAX_JSON_BYTES)
        receipt = _json_from_bytes(raw_receipt, "receipt")
        if not isinstance(receipt, dict):
            raise ReceiptError("receipt_invalid")
        if receipt.get("schema_version") != "2.0":
            if not _is_known_legacy_receipt(receipt):
                raise ReceiptError("receipt_schema_version_unsupported")
            return {
                "schema_version": SIDECAR_VERSION,
                "status": "legacy_historical",
                "eligible_to_close": False,
                "receipt_sha256": sha256_bytes(raw_receipt),
                "validator_sha256": sha256_bytes(Path(__file__).read_bytes()),
                "evaluated_at_utc": evaluated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "blockers": [],
            }
        plan_bytes = read_ref(plan_ref, roots, purpose="control", expected_hash=False, max_bytes=MAX_JSON_BYTES)
        catalog_bytes = read_ref(catalog_ref, roots, purpose="control", expected_hash=False, max_bytes=MAX_JSON_BYTES)
        plan = _json_from_bytes(plan_bytes, "plan")
        catalog = _json_from_bytes(catalog_bytes, "case_catalog")
        if not isinstance(plan, dict) or not isinstance(catalog, dict):
            raise ReceiptError("plan_or_catalog_invalid")
        result = _verify_loaded(receipt, plan, catalog, roots, (plan_bytes, catalog_bytes), set())
        result.update({
            "schema_version": SIDECAR_VERSION,
            "receipt_sha256": sha256_bytes(raw_receipt),
            "validator_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "evaluated_at_utc": evaluated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })
        return result
    except ReceiptError as exc:
        return {
            "schema_version": SIDECAR_VERSION,
            "status": "blocked",
            "eligible_to_close": False,
            "blockers": [{"code": str(exc)}],
            "validator_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "evaluated_at_utc": evaluated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def _cli_ref(raw: str) -> dict[str, str]:
    if ":" not in raw:
        raise argparse.ArgumentTypeError("path references use ROOT_ID:relative/forward/slash/path")
    root_id, path = raw.split(":", 1)
    try:
        _safe_relative(path)
    except ReceiptError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return {"root_id": root_id, "path": path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="verify a sealed receipt without writing files")
    verify.add_argument("--receipt", required=True, type=_cli_ref)
    verify.add_argument("--plan", required=True, type=_cli_ref)
    verify.add_argument("--cases", required=True, type=_cli_ref)
    verify.add_argument("--root", action="append", default=[], metavar="ID=PATH",
                        help="explicitly register a local repository/evidence root; repeat as needed")
    args = parser.parse_args(argv)
    try:
        roots = _root_map(args.root)
        result = verify_receipt(args.receipt, args.plan, args.cases, roots)
    except ReceiptError as exc:
        result = {
            "schema_version": SIDECAR_VERSION, "status": "blocked", "eligible_to_close": False,
            "blockers": [{"code": str(exc)}],
            "validator_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return 0 if result.get("eligible_to_close") else 1


if __name__ == "__main__":
    raise SystemExit(main())
