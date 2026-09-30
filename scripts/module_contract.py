"""S04 offline reference rules for immutable question-module releases.

This module does not route companies, dispatch questions, read credentials, or
persist scan results. S05/S06 and the external owners implement those paths.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "quick_scan"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


MODULE_SCHEMA = _schema("question-module.schema.json")
RELEASE_SCHEMA = _schema("module-release.schema.json")
ROUTE_SCHEMA = _schema("route-decision.schema.json")
CORE_IDS = frozenset(f"IQS_{index:02}" for index in range(1, 25))


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key in module archive: {key}")
        result[key] = value
    return result


def _version(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))


def _validate(schema: dict, value: object) -> None:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def validate_module(module: dict) -> None:
    """Validate one scored module's shape and duplicate IDs."""
    _validate(MODULE_SCHEMA, module)
    if (module["module_id"] == "common") != (module["kind"] == "common"):
        raise ValueError("common ID and kind must match")
    ids = [q["id"] for q in module["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question ID in module")
    if set(ids) & set(module.get("retired_question_ids", [])):
        raise ValueError("retired question ID cannot be active again")
    if module["kind"] == "common" and set(ids) != CORE_IDS:
        raise ValueError("common must contain exactly the frozen 24 core question IDs")
    type_replacements: set[str] = set()
    for question in module["questions"]:
        if question["metric_id"] != "score." + question["id"].lower():
            raise ValueError("metric_id must bind the question ID")
        if question.get("supersedes") == question["id"]:
            raise ValueError("question cannot supersede itself")
        if module["kind"] == "common" and (
                question["comparison_role"] != "core" or question["construct_id"] != question["id"]
                or question.get("replaces")):
            raise ValueError("common question must preserve its core construct")
        if module["kind"] == "types":
            replacements = question.get("replaces", [])
            if question["comparison_role"] == "core":
                if (len(replacements) != 1 or replacements[0] not in CORE_IDS
                        or question["construct_id"] != replacements[0]):
                    raise ValueError("type core question must replace one frozen core construct")
                if replacements[0] in type_replacements:
                    raise ValueError("duplicate core replacement within one company type")
                type_replacements.add(replacements[0])
            elif replacements or question["construct_id"] is not None:
                raise ValueError("type context question cannot replace a core construct")
        if module["kind"] in {"common_extensions", "lenses", "industries", "stages", "overlays", "diagnostics"}:
            if (question["comparison_role"] == "core" or question.get("replaces")
                    or question["construct_id"] is not None):
                raise ValueError("non-type extension cannot enter core or replace a core construct")


def _validate_dependency_graph(modules: Mapping[str, dict]) -> None:
    """Validate references and acyclicity for one complete module collection."""
    graph = {}
    for module_id, module in modules.items():
        deps = module.get("dependencies", [])
        conflicts = module.get("conflicts", [])
        if module_id in deps or module_id in conflicts or set(deps) & set(conflicts):
            raise ValueError(f"{module_id}: self or dependency/conflict contradiction")
        if (set(deps) | set(conflicts)) - modules.keys():
            raise ValueError(f"{module_id}: unknown dependency or conflict")
        graph[module_id] = deps
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(module_id: str) -> None:
        if module_id in visiting:
            raise ValueError("module dependency cycle")
        if module_id in done:
            return
        visiting.add(module_id)
        for dep in graph[module_id]:
            visit(dep)
        visiting.remove(module_id)
        done.add(module_id)

    for module_id in graph:
        visit(module_id)


def validate_registry(modules: Mapping[str, dict], contexts: Mapping[str, object],
                      *, legacy_ids: frozenset[str] = frozenset(),
                      historical_retired_ids: frozenset[str] = frozenset()) -> None:
    """Fail before export if any newly registered module lacks its full context."""
    if not modules or "common" not in modules:
        raise ValueError("registry requires the common module")
    question_ids: set[str] = set()
    retired_ids = set(historical_retired_ids)
    for module_id, module in modules.items():
        validate_module(module)
        if module_id != module["module_id"]:
            raise ValueError("module ID differs from registry key")
        for question in module["questions"]:
            if question["id"] in question_ids:
                raise ValueError("duplicate question ID across modules")
            question_ids.add(question["id"])
        retired_ids.update(module.get("retired_question_ids", []))
        if module_id in legacy_ids:
            continue
        if not module.get("activation"):
            raise ValueError(f"{module_id}: new module requires activation evidence")
        if not module.get("introduced_in") or "dependencies" not in module or "conflicts" not in module:
            raise ValueError(f"{module_id}: new module requires lifecycle/dependency metadata")
        if module["kind"] == "lenses" and module["activation"]["mode"] != "manual":
            raise ValueError("investment lenses require explicit user selection")
        kind_contexts = contexts.get(module["kind"])
        if not isinstance(kind_contexts, Mapping) or not isinstance(
                kind_contexts.get(module_id), str) or not kind_contexts[module_id].strip():
            raise ValueError(f"{module_id}: missing scoring context")
    if question_ids & retired_ids:
        raise ValueError("retired question ID reused across modules")
    _validate_dependency_graph(modules)


def question_definition_sha256(question: dict) -> str:
    """Hash a released question definition, excluding unrelated modules."""
    return digest(question)


def effective_semantic_sha256(question: dict, *, applied_contexts: list[str],
                              renderer_version: str) -> str:
    """Reference fingerprint; S05 binds it to actual rendered prompt/rules."""
    _version(renderer_version)
    if not all(isinstance(item, str) and item.strip() for item in applied_contexts):
        raise ValueError("effective contexts must be nonempty strings")
    semantic_keys = ("id", "dimension", "question", "evidence", "anchors", "metric_id",
                     "construct_id", "comparison_role", "rubric_version", "scope", "replaces",
                     "aggregation", "critical", "framework", "factor", "supersedes")
    semantics = {key: question[key] for key in semantic_keys if key in question}
    return digest({"question_semantics": semantics,
                   "applied_contexts": applied_contexts,
                   "renderer_version": renderer_version})


def validate_upgrade(old: dict, new: dict) -> None:
    """Keep published questions and their applicability scope immutable in place."""
    validate_module(old)
    validate_module(new)
    if (old["module_id"], old["kind"]) != (new["module_id"], new["kind"]):
        raise ValueError("module identity/kind cannot change in place")
    old_version, new_version = _version(old["version"]), _version(new["version"])
    if new_version <= old_version:
        raise ValueError("module version must increase")
    old_questions = {q["id"]: q for q in old["questions"]}
    new_questions = {q["id"]: q for q in new["questions"]}
    if old["applies_when"] != new["applies_when"] and old_questions.keys() & new_questions.keys():
        raise ValueError("module applicability scope change requires successor IDs for all questions")
    removed = old_questions.keys() - new_questions.keys()
    old_retired = set(old.get("retired_question_ids", []))
    new_retired = set(new.get("retired_question_ids", []))
    if new_retired != old_retired | removed:
        raise ValueError("retired question tombstones must accumulate exactly")
    if new_questions.keys() & old_retired:
        raise ValueError("retired question ID cannot be reused")
    successors = [new_questions[qid]["supersedes"] for qid in new_questions.keys() - old_questions.keys()
                  if "supersedes" in new_questions[qid]]
    if len(successors) != len(set(successors)) or not set(successors) <= old_questions.keys():
        raise ValueError("successor mapping must uniquely reference an old question")
    if removed:
        if new_version[0] <= old_version[0]:
            raise ValueError("question removal requires a major release")
        superseded = {q.get("supersedes") for q in new["questions"]}
        if not removed <= superseded:
            raise ValueError("removed questions require explicit successor mapping")
    added = new_questions.keys() - old_questions.keys()
    if added and new_version[0] == old_version[0] and new_version[1] <= old_version[1]:
        raise ValueError("new questions require a minor or major release")
    for qid in old_questions.keys() & new_questions.keys():
        before, after = old_questions[qid], new_questions[qid]
        if before != after:
            raise ValueError(f"{qid}: published question content is immutable; use a new ID")


def seal_release(body: dict) -> dict:
    """Assign a content-addressed ID; callers still need validate_release."""
    release = copy.deepcopy(body)
    release.pop("release_id", None)
    if isinstance(release.get("modules"), list):
        release["modules"] = sorted(release["modules"], key=lambda item: item["module_id"])
    release["release_id"] = "modrel_" + digest(release)
    _validate(RELEASE_SCHEMA, release)
    return release


def _validate_release_identity(release: dict) -> None:
    _validate(RELEASE_SCHEMA, release)
    body = {key: value for key, value in release.items() if key != "release_id"}
    if release["release_id"] != "modrel_" + digest(body):
        raise ValueError("module release content hash mismatch")
    entries = release["modules"]
    module_ids = [entry["module_id"] for entry in entries]
    if module_ids != sorted(module_ids) or len(module_ids) != len(set(module_ids)):
        raise ValueError("module release requires sorted unique module IDs")
    if sum(entry["module_id"] == "common" and entry["kind"] == "common" for entry in entries) != 1:
        raise ValueError("module release requires exactly one common core module")
    if any((entry["module_id"] == "common") != (entry["kind"] == "common") for entry in entries):
        raise ValueError("common module ID and kind must match")
    refs = [entry["artifact_ref"] for entry in entries]
    if len(refs) != len(set(refs)):
        raise ValueError("module release archive references must be unique")
    question_ids = [q["question_id"] for entry in entries for q in entry["question_semantics"]]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("module release question IDs must be globally unique")
    if set(question_ids) & set(release["retired_question_ids"]):
        raise ValueError("retired question ID reused in release lock")


def validate_release(release: dict, artifact_loader: Callable[[str], bytes]) -> dict[str, dict]:
    """Check archive bytes and question definitions against the immutable lock."""
    _validate_release_identity(release)
    modules = {}
    all_questions: set[str] = set()
    for item in release["modules"]:
        module_id = item["module_id"]
        if module_id in modules:
            raise ValueError("duplicate module in release")
        try:
            raw = artifact_loader(item["artifact_ref"])
        except (OSError, KeyError) as exc:
            raise ValueError("module archive unavailable") from exc
        if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != item["artifact_sha256"]:
            raise ValueError("module archive hash mismatch")
        module = json.loads(raw, object_pairs_hook=_unique_object)
        if module_id != module.get("module_id") or item["version"] != module.get("version") or item["kind"] != module.get("kind"):
            raise ValueError("module archive identity/version mismatch")
        validate_module(module)
        actual = {q["id"]: (q["rubric_version"], question_definition_sha256(q))
                  for q in module["questions"]}
        locked = {q["question_id"]: (q["rubric_version"], q["definition_sha256"])
                  for q in item["question_semantics"]}
        if (len(actual) != len(module["questions"])
                or len(locked) != len(item["question_semantics"]) or locked != actual):
            raise ValueError("module question semantics mismatch")
        if all_questions & locked.keys():
            raise ValueError("duplicate question ID across release modules")
        all_questions.update(locked)
        modules[module_id] = module
    if "common" not in modules:
        raise ValueError("release requires common module")
    module_retired = {qid for module in modules.values() for qid in module.get("retired_question_ids", [])}
    if not module_retired <= set(release["retired_question_ids"]):
        raise ValueError("release lock omits module retirement tombstones")
    _validate_dependency_graph(modules)
    return modules


def seal_route_decision(body: dict) -> dict:
    decision = copy.deepcopy(body)
    decision.pop("decision_id", None)
    decision["decision_id"] = "route_" + digest(decision)
    _validate(ROUTE_SCHEMA, decision)
    return decision


def validate_route_decision(decision: dict, release: dict, *, package: dict | None = None) -> None:
    """Validate provenance and immutable identity; S06 adds routing policy."""
    _validate_release_identity(release)
    _validate(ROUTE_SCHEMA, decision)
    body = {key: value for key, value in decision.items() if key != "decision_id"}
    if decision["decision_id"] != "route_" + digest(body):
        raise ValueError("route decision content hash mismatch")
    if decision["release_id"] != release["release_id"] or decision["router_version"] != release["router_version"]:
        raise ValueError("route decision uses a different module release/router")
    v2 = decision["schema_version"] == "2.0.0"
    if v2:
        if (package is None or decision["module_package_id"] != package.get("package_id")
                or package.get("release_id") != release["release_id"]
                or release["schema_version"] != "2.0.0"
                or decision["routing_policy_sha256"] != release["routing_policy_sha256"]):
            raise ValueError("route v2 requires its verified package and routing policy")
        profile = decision["profile_context"]
        if (profile["entity_id"] != decision["entity_id"] or profile["as_of"] != decision["as_of"]
                or profile["segment_id"] != decision["segment_id"]
                or (decision["scope"] == "segment") != (decision["segment_id"] is not None)):
            raise ValueError("route identity or scope differs from frozen profile context")
    elif release["schema_version"] != "1.0.0":
        raise ValueError("legacy route cannot represent routing policy v2")
    available = {item["module_id"]: item["version"] for item in release["modules"]}
    seen = set()
    as_of = date.fromisoformat(decision["as_of"])
    decided_at = datetime.fromisoformat(decision["decided_at"].replace("Z", "+00:00"))
    if decided_at.tzinfo is None or decided_at.utcoffset() != timezone.utc.utcoffset(decided_at):
        raise ValueError("decided_at must be UTC")
    if decided_at.date() < as_of:
        raise ValueError("decision time cannot precede information cutoff")
    for item in decision["module_decisions"]:
        module_id = item["module_id"]
        if module_id in seen or available.get(module_id) != item["module_version"]:
            raise ValueError("unknown/duplicate module or version in route decision")
        seen.add(module_id)
        for source in item["sources"]:
            if v2 and source["entity_id"] != decision["entity_id"]:
                raise ValueError("route source belongs to another entity")
            if source["published_at"] != "unknown" and date.fromisoformat(source["published_at"]) > as_of:
                raise ValueError("route source published after information cutoff")
        if item["basis"] == "manual":
            expires = datetime.fromisoformat(item["manual_override"]["valid_until"].replace("Z", "+00:00"))
            if expires.tzinfo is None or expires.utcoffset() != timezone.utc.utcoffset(expires) or expires <= decided_at:
                raise ValueError("manual route override expired or not UTC")
    if seen != set(available):
        raise ValueError("route decision must account for every released module")
    if not v2 and decision["status"] == "resolved" and any(
            item["decision"] == "uncertain" for item in decision["module_decisions"]):
        raise ValueError("resolved route cannot contain uncertain modules")
    if not any(item["module_id"] == "common" and item["decision"] == "selected"
               for item in decision["module_decisions"]):
        raise ValueError("common module must be selected")
