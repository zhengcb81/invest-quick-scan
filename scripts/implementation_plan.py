"""Read-only task packets and structural checks; never run tasks or mark them done."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_DIR = ROOT / "docs" / "implementation"
KINDS = {"contract", "implementation", "review", "live"}
CASE_KINDS = {"positive", "negative", "boundary", "fault", "metamorphic"}
LEVELS = {"contract", "unit", "integration", "fault", "live", "review"}
STAGES = [f"M{i}" for i in range(7)]


def load_package(plan_dir: Path) -> tuple[dict, dict]:
    values = []
    for name in ("tasks.json", "acceptance-cases.json"):
        value = json.loads((plan_dir / name).read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError(f"{name}: expected a JSON object")
        values.append(value)
    return values[0], values[1]


def string_list(value: object) -> bool:
    return (isinstance(value, list) and bool(value)
            and all(isinstance(x, str) and bool(x.strip()) for x in value))


def validate_package(plan: dict, catalog: dict) -> list[str]:
    """Validate the planning graph and oracles, not the future implementation."""
    errors: list[str] = []
    if plan.get("status") != "implementation_plan_not_product_completion":
        errors.append("plan must be labelled as a plan, not product completion")
    if catalog.get("status") != "acceptance_specifications_not_runtime_results":
        errors.append("case catalog must be labelled as specifications")
    if catalog.get("example_only") is not True:
        errors.append("case catalog must explicitly mark fictional examples")
    if plan.get("version") != catalog.get("version") or not plan.get("version"):
        errors.append("plan and case catalog need the same nonempty version")
    tasks, cases = plan.get("tasks"), catalog.get("cases")
    if not isinstance(tasks, list) or not tasks or not all(isinstance(t, dict) for t in tasks):
        return errors + ["tasks must be a nonempty array of objects"]
    if not isinstance(cases, list) or not cases or not all(isinstance(c, dict) for c in cases):
        return errors + ["cases must be a nonempty array of objects"]
    stages = plan.get("stage_order")
    if stages != STAGES:
        errors.append("stage order must explicitly cover M0 through M6")
        stages = STAGES
    repositories = plan.get("repositories", {})
    if not isinstance(repositories, dict) or not repositories:
        errors.append("repositories must be a nonempty object")
        repositories = {}
    for owner, repo in repositories.items():
        if not isinstance(repo, dict) or not all(isinstance(repo.get(k), str) and repo[k].strip()
                                               for k in ("name", "root", "role")):
            errors.append(f"repository {owner}: missing name/root/role")
    invariants = plan.get("invariant_ids", [])
    if not string_list(invariants) or len(invariants) != len(set(invariants)):
        errors.append("invariant IDs must be unique nonempty strings")
        invariants = []
    for field in ("common_read_first", "global_boundaries"):
        if not string_list(plan.get(field)):
            errors.append(f"plan.{field} must be a nonempty string list")

    case_map: dict[str, dict] = {}
    for case in cases:
        cid = case.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Z][A-Z0-9]*-\d{2}", cid):
            errors.append("case has invalid ID")
            continue
        if cid in case_map:
            errors.append(f"duplicate case {cid}")
        case_map[cid] = case
        if (not isinstance(case.get("kind"), str) or case["kind"] not in CASE_KINDS
                or not isinstance(case.get("level"), str) or case["level"] not in LEVELS):
            errors.append(f"{cid}: invalid kind or level")
        if case.get("status") != "specified_not_executed":
            errors.append(f"{cid}: specifications cannot contain claimed test results")
        if not isinstance(case.get("given"), (str, dict, list)) or not case.get("given"):
            errors.append(f"{cid}: missing input/precondition")
        if not isinstance(case.get("when"), str) or not case["when"].strip():
            errors.append(f"{cid}: missing action")
        expected = case.get("then")
        if (not isinstance(expected, list) or not expected
                or any(not isinstance(x, (str, dict, list)) or not x for x in expected)):
            errors.append(f"{cid}: missing explicit expected result")

    task_map: dict[str, dict] = {}
    for task in tasks:
        tid = task.get("id")
        if not isinstance(tid, str) or not re.fullmatch(r"[A-Z]\d{1,2}", tid):
            errors.append("task has invalid ID")
            continue
        if tid in task_map:
            errors.append(f"duplicate task {tid}")
        task_map[tid] = task
        for field in ("title", "test_binding", "rollback"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                errors.append(f"{tid}: missing {field}")
        for field in ("read_first", "allowed_changes", "steps", "deliverables", "case_ids", "invariants", "completion"):
            if not string_list(task.get(field)):
                errors.append(f"{tid}: missing nonempty {field}")
        owner, kind, stage = task.get("owner"), task.get("kind"), task.get("stage")
        if not isinstance(owner, str) or owner not in repositories:
            errors.append(f"{tid}: unknown or multiple owners")
        if not isinstance(kind, str) or kind not in KINDS or stage not in stages:
            errors.append(f"{tid}: invalid task kind or stage")
        if "status" in task:
            errors.append(f"{tid}: completion status belongs in evidence receipts, not this spec")
        deps = task.get("depends_on")
        if (not isinstance(deps, list) or any(not isinstance(d, str) for d in deps)
                or len(deps) != len(set(deps))):
            errors.append(f"{tid}: dependencies must be unique string IDs")
        if string_list(task.get("invariants")):
            for iid in task["invariants"]:
                if iid not in invariants:
                    errors.append(f"{tid}: unknown invariant {iid}")

    used_cases: set[str] = set()
    for tid, task in task_map.items():
        deps = task.get("depends_on")
        if isinstance(deps, list):
            for dep in deps:
                if not isinstance(dep, str) or dep not in task_map:
                    errors.append(f"{tid}: unknown dependency {dep!r}")
                elif task.get("stage") in stages and task_map[dep].get("stage") in stages:
                    if stages.index(task_map[dep]["stage"]) > stages.index(task["stage"]):
                        errors.append(f"{tid}: dependency {dep} points to a later stage")
        case_ids = task.get("case_ids")
        if not string_list(case_ids):
            continue
        if len(case_ids) != len(set(case_ids)):
            errors.append(f"{tid}: repeated case IDs")
        selected = []
        for cid in case_ids:
            if cid not in case_map:
                errors.append(f"{tid}: unknown case {cid}")
            else:
                used_cases.add(cid)
                selected.append(case_map[cid])
        if not any(c.get("kind") in ("negative", "fault") for c in selected):
            errors.append(f"{tid}: needs a negative or fault case")
        if task.get("kind") == "live" and not any(c.get("level") == "live" for c in selected):
            errors.append(f"{tid}: live task needs a live case")
        if task.get("kind") == "review" and not any(c.get("level") == "review" for c in selected):
            errors.append(f"{tid}: review task needs a review case")
    for cid in sorted(set(case_map) - used_cases):
        errors.append(f"orphan acceptance case {cid}")

    visiting, visited = set(), set()

    def walk(tid: str) -> None:
        if tid in visiting:
            errors.append(f"dependency cycle includes {tid}")
            return
        if tid in visited:
            return
        visiting.add(tid)
        deps = task_map[tid].get("depends_on", [])
        for dep in deps if isinstance(deps, list) else []:
            if isinstance(dep, str) and dep in task_map:
                walk(dep)
        visiting.remove(tid)
        visited.add(tid)

    for tid in task_map:
        walk(tid)
    for index in range(len(STAGES)):
        gate = task_map.get(f"G{index}")
        if not gate or gate.get("kind") != "review" or gate.get("stage") != f"M{index}":
            errors.append(f"M{index}: missing review gate G{index}")
    for tid, task in task_map.items():
        ancestors = dependency_ids(task_map, tid)
        if task.get("stage") == "M4" and "G3" not in ancestors:
            errors.append(f"{tid}: full facts work must depend on G3")
    release = plan.get("release_requirements")
    if not isinstance(release, dict):
        return errors + ["missing cross-project release requirements"]
    if release.get("final_gate") != "G6":
        errors.append("complete release must end at G6")
    if release.get("complete_requires_all_tasks") is not True:
        errors.append("complete release must include all tasks")
    required_gates = release.get("required_gates")
    if not string_list(required_gates) or set(required_gates) != {f"G{i}" for i in range(6)}:
        errors.append("release requires G0 through G5, including facts/consumers G4")
    required_tasks = release.get("required_tasks")
    launch_tasks = {"C07"} | {f"X{i:02}" for i in range(1, 13)}
    if not string_list(required_tasks) or not launch_tasks <= set(required_tasks):
        errors.append("release must name all launch delivery tasks C07 and X01-X12")
    elif any(tid not in task_map for tid in required_tasks):
        errors.append("release references an unknown launch task")
    components = release.get("required_components")
    if not string_list(components) or set(components) != set(repositories):
        errors.append("release must include every required component and consumer")
    if release.get("runtime_entry_owner") != "stockwiki" or release.get("runtime_config_owner") != "stockqa":
        errors.append("launch and model configuration ownership must stay StockWiki/StockQA")
    if "G0" in task_map and "C07" not in dependency_ids(task_map, "G0"):
        errors.append("G0 must freeze launch contract C07 before implementation")
    if "G6" in task_map:
        all_predecessors = set(dependency_ids(task_map, "G6"))
        missing = set(task_map) - all_predecessors - {"G6"}
        if missing:
            errors.append(f"G6 leaves unfinished task branches: {', '.join(sorted(missing))}")
    for key, expected_kind, required_case in (("offline_e2e_task", "implementation", "E2E-01"),
                                               ("live_e2e_task", "live", "E2E-03")):
        tid = release.get(key)
        item = task_map.get(tid) if isinstance(tid, str) else None
        if (not item or item.get("kind") != expected_kind or item.get("stage") != "M6"
                or not string_list(item.get("case_ids")) or required_case not in item["case_ids"]):
            errors.append(f"{key} must bind the actual M6 {expected_kind} path and {required_case}")
    return errors


def dependency_ids(task_map: dict, tid: str) -> list[str]:
    found: set[str] = set()
    pending = list(task_map[tid].get("depends_on", [])) if isinstance(task_map[tid].get("depends_on"), list) else []
    while pending:
        dep = pending.pop()
        if not isinstance(dep, str) or dep in found or dep not in task_map:
            continue
        found.add(dep)
        items = task_map[dep].get("depends_on", [])
        if isinstance(items, list):
            pending.extend(items)
    return sorted(found)


def task_packet(plan: dict, catalog: dict, tid: str, plan_dir: Path) -> dict:
    task_map = {t["id"]: t for t in plan["tasks"]}
    if tid not in task_map:
        raise ValueError(f"unknown task {tid}")
    task = task_map[tid]
    register = (plan_dir / "decision-register.md").read_text(encoding="utf-8-sig")
    selected = set(task["invariants"])
    rows = [line for line in register.splitlines()
            if len(line.split("|")) > 2 and line.split("|")[1].strip() in selected]
    described = {line.split("|")[1].strip() for line in rows}
    if described != selected:
        raise ValueError(f"task {tid}: missing invariant definitions {sorted(selected - described)}")
    return {"notice": "Planning packet only. Commands are text; nothing is executed or approved.",
            "plan_version": plan["version"], "repository": plan["repositories"][task["owner"]],
            "common_read_first": plan["common_read_first"], "boundaries": plan["global_boundaries"],
            "task": task, "transitive_dependencies": dependency_ids(task_map, tid),
            "invariant_details": rows,
            "acceptance_cases": [c for c in catalog["cases"] if c["id"] in task["case_ids"]]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("validate")
    listing = sub.add_parser("list")
    listing.add_argument("--stage", choices=STAGES)
    listing.add_argument("--owner", help="Filter by repository ID; no tasks are executed")
    show = sub.add_parser("show")
    show.add_argument("task_id")
    args = parser.parse_args(argv)
    try:
        plan, catalog = load_package(args.plan_dir)
        errors = validate_package(plan, catalog)
        if errors:
            print(json.dumps({"planning_valid": False, "errors": errors}, ensure_ascii=False, indent=2))
            return 1
        if args.action == "validate":
            print(json.dumps({"planning_valid": True, "tasks": len(plan["tasks"]),
                              "acceptance_cases": len(catalog["cases"]),
                              "final_release_gate": plan["release_requirements"]["final_gate"],
                              "product_tests_executed": False}, ensure_ascii=False))
        elif args.action == "list":
            if args.owner and args.owner not in plan["repositories"]:
                raise ValueError(f"unknown owner {args.owner}")
            for task in plan["tasks"]:
                if ((not args.stage or task["stage"] == args.stage)
                        and (not args.owner or task["owner"] == args.owner)):
                    print(f'{task["id"]} | {task["stage"]} | {task["owner"]} | {task["title"]} | deps: {", ".join(task["depends_on"])}')
        else:
            print(json.dumps(task_packet(plan, catalog, args.task_id, args.plan_dir), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Cannot read/validate implementation plan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
