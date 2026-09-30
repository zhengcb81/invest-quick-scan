"""Build and verify the complete immutable file set for a G0 review candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/implementation/reviews/G0/candidate-snapshot.json"
PATTERNS = (
    "SKILL.md", "question_sets.py", "task_plan.md", "progress.md", "findings.md",
    "config/**/*.json", "questions/**/*.json", "templates/**/*.json",
    "schemas/**/*.json", "scripts/*.py", "tests/test_*.py", "tests/fixtures/**/*", "examples/**/*.json",
    "docs/stock-pool-design.md", "docs/universe-and-operations-design.md",
    "docs/implementation/**/*.json", "docs/implementation/**/*.md",
    "docs/implementation/**/*.log",
)
EXCLUDED = {
    "docs/implementation/reviews/G0/candidate-snapshot.json",
    "docs/implementation/reviews/G0/independent-final-review.md",
    "docs/implementation/reviews/G0/independent-final-review.json",
    # Mutable planning journals are updated after a gate closes; the fixed plan,
    # acceptance catalog and review packet remain bound in the candidate.
    "task_plan.md", "progress.md", "findings.md",
    # A legacy G0 receipt is immutable history, not part of the active review packet.
    "docs/implementation/contracts/receipt-G0.json",
    # A legacy detached validator output is immutable history, not part of the active packet.
    "docs/implementation/contracts/validation-G0-final-r1-2026-09-26.json",
}


def _read_plan() -> dict:
    return json.loads((ROOT / "docs/implementation/tasks.json").read_text(encoding="utf-8"))


def _downstream_task_ids(plan: dict) -> set[str]:
    """Return tasks scheduled after G0, whose logs/reviews are generated later."""
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("plan tasks must be a list")
    if any(not isinstance(task, dict) for task in tasks):
        raise ValueError("plan tasks must be objects")
    ids = [task.get("id") for task in tasks]
    if any(not isinstance(task_id, str) or not task_id.strip() for task_id in ids):
        raise ValueError("plan task IDs must be non-empty strings")
    if len(ids) != len(set(ids)) or "G0" not in ids:
        raise ValueError("plan task IDs must be unique and include G0")
    children = {task_id: set() for task_id in ids}
    for task in tasks:
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list):
            raise ValueError("task dependencies must be a list")
        if any(not isinstance(dependency, str) or not dependency.strip() for dependency in dependencies):
            raise ValueError("task dependency IDs must be non-empty strings")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError("task dependencies must be unique")
        for dependency in dependencies:
            if dependency not in children:
                raise ValueError("task dependency references an unknown task ID")
            children[dependency].add(task["id"])
    downstream = set()
    pending = list(children["G0"])
    while pending:
        task_id = pending.pop()
        if task_id == "G0":
            raise ValueError("task dependency cycle includes G0")
        if task_id in downstream:
            continue
        downstream.add(task_id)
        pending.extend(children[task_id] - downstream)
    return downstream


def scope_exclusions(plan: dict) -> list[str]:
    """Exclude post-G0 validation logs and reviews from the frozen G0 snapshot."""
    exclusions = set(EXCLUDED)
    for task_id in _downstream_task_ids(plan):
        exclusions.add(f"docs/implementation/contracts/validation-{task_id}-*")
        exclusions.add(f"docs/implementation/reviews/{task_id}/**")
    return sorted(exclusions)


def _is_excluded(relative: str, exclusions: list[str]) -> bool:
    for pattern in exclusions:
        if pattern.endswith("/**"):
            prefix = pattern[:-2]
            if relative.startswith(prefix):
                return True
        elif pattern.endswith("-*"):
            prefix = pattern[:-1]
            if relative.startswith(prefix) and "/" not in relative[len(prefix):]:
                return True
        elif relative == pattern:
            return True
    return False


def scope_paths(plan: dict | None = None) -> list[str]:
    plan = plan if plan is not None else _read_plan()
    exclusions = scope_exclusions(plan)
    paths: set[str] = set()
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                if not _is_excluded(relative, exclusions):
                    paths.add(relative)
    return sorted(paths)


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper()


def _g0_read_first_paths(plan: dict) -> set[str]:
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        return set()
    task = next((item for item in tasks if isinstance(item, dict) and item.get("id") == "G0"), None)
    if task is None or not isinstance(task.get("read_first"), list):
        return set()
    return {path for path in task["read_first"] if isinstance(path, str)}


def render() -> dict:
    plan = _read_plan()
    exclusions = scope_exclusions(plan)
    return {
        "manifest_type": "G0_frozen_for_independent_review",
        "created_date": datetime.now(timezone.utc).date().isoformat(),
        "plan_version": plan["version"],
        "scope_patterns": list(PATTERNS),
        "scope_exclusions": exclusions,
        "artifact_hashes": {path: sha256(path) for path in scope_paths(plan)},
        "notice": (
            "This manifest freezes the complete declared G0 review scope. "
            "It grants no production readiness; G0 remains pending until an independent reviewer passes it."
        ),
    }


def verify(manifest: dict) -> list[str]:
    errors: list[str] = []
    plan = _read_plan()
    exclusions = scope_exclusions(plan)
    expected = set(scope_paths(plan))
    recorded = set(manifest.get("artifact_hashes", {}))
    if missing := sorted(expected - recorded):
        errors.append("missing from manifest: " + ", ".join(missing))
    if extra := sorted(recorded - expected):
        errors.append("outside declared scope: " + ", ".join(extra))
    for path in sorted(expected & recorded):
        if manifest["artifact_hashes"][path] != sha256(path):
            errors.append(f"hash mismatch: {path}")
    required_inputs = _g0_read_first_paths(plan)
    if not required_inputs:
        errors.append("G0 read_first inputs are missing or malformed")
    if missing_inputs := sorted(required_inputs - expected):
        errors.append("G0 read_first inputs outside declared scope: " + ", ".join(missing_inputs))
    if missing_inputs := sorted(required_inputs - recorded):
        errors.append("G0 read_first inputs missing from manifest: " + ", ".join(missing_inputs))
    if manifest.get("manifest_type") != "G0_frozen_for_independent_review":
        errors.append("manifest is not frozen for independent review")
    if manifest.get("plan_version") != plan.get("version"):
        errors.append("manifest plan version does not match current plan")
    if manifest.get("scope_patterns") != list(PATTERNS):
        errors.append("manifest scope patterns do not match current declaration")
    if manifest.get("scope_exclusions") != exclusions:
        errors.append("manifest scope exclusions do not match current declaration")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("render", "verify"))
    args = parser.parse_args()
    if args.operation == "render":
        print(json.dumps(render(), ensure_ascii=False, indent=2))
        return 0
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = verify(manifest)
    print(json.dumps({"scope_files": len(scope_paths()), "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
