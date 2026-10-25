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

EXTENSION_KINDS = frozenset({"common_extensions", "lenses", "industries", "stages",
                             "overlays", "diagnostics"})


def core_construct_ids(module: Mapping) -> frozenset[str]:
    """Derive the release's core construct set from the common module data.

    BASIC-BANK-EXPANSION-21（所有者 2026-10-24 裁定）：核心构念集合 = ``common``
    模块中 ``comparison_role == "core"`` 的题。任何代码不得再写死题数或固定 ID 列表；
    基本题库可以按 minor 升版追加/删除诊断扩展题，核心集合只在 major 升版时变化。
    非 common 模块不含核心构念，返回空集合。
    """
    if not isinstance(module, Mapping):
        raise ValueError("core constructs require a module object")
    if module.get("kind") != "common":
        return frozenset()
    return frozenset(question["id"] for question in module.get("questions", [])
                     if question.get("comparison_role") == "core")


def _is_extension_question(question: Mapping) -> bool:
    """A diagnostic extension: scored never, compared never, constructed never."""
    return (question.get("comparison_role") == "diagnostic"
            and question.get("aggregation") == "diagnostic"
            and question.get("construct_id") is None
            and not question.get("replaces"))


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


def validate_module(module: dict, *, core_ids: frozenset[str] | None = None,
                    critical_core_ids: frozenset[str] | None = None) -> None:
    """Validate one scored module's shape and duplicate IDs.

    ``core_ids`` is the released core construct set (see ``core_construct_ids``).
    For the common module it is derived from this module's own data when omitted;
    a type module needs the caller to supply the release's set so a replacement
    cannot target a construct the release does not carry.
    ``critical_core_ids`` carries the common module's declared critical subset;
    a type replacement must preserve that risk flag. Registry/release validators
    derive both sets from the same common module rather than a fixed ID list.
    """
    _validate(MODULE_SCHEMA, module)
    if (module["module_id"] == "common") != (module["kind"] == "common"):
        raise ValueError("common ID and kind must match")
    ids = [q["id"] for q in module["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question ID in module")
    if set(ids) & set(module.get("retired_question_ids", [])):
        raise ValueError("retired question ID cannot be active again")
    if module["kind"] == "common":
        if core_ids is None:
            core_ids = core_construct_ids(module)
        if not core_ids:
            raise ValueError("common module must declare at least one core construct")
    type_replacements: set[str] = set()
    for question in module["questions"]:
        if question.get("critical") and (question.get("comparison_role") == "diagnostic"
                                         or question.get("aggregation") == "diagnostic"):
            raise ValueError("diagnostic question cannot declare a critical risk gate")
        if question["metric_id"] != "score." + question["id"].lower():
            raise ValueError("metric_id must bind the question ID")
        if question.get("supersedes") == question["id"]:
            raise ValueError("question cannot supersede itself")
        if module["kind"] == "common":
            _validate_common_question(question)
        if module["kind"] == "types":
            replacements = question.get("replaces", [])
            if question["comparison_role"] == "core":
                if (len(replacements) != 1
                        or (core_ids is not None and replacements[0] not in core_ids)
                        or question["construct_id"] != replacements[0]):
                    raise ValueError("type core question must replace one frozen core construct")
                if replacements[0] in type_replacements:
                    raise ValueError("duplicate core replacement within one company type")
                if (critical_core_ids is not None and replacements[0] in critical_core_ids
                        and question.get("critical") is not True):
                    raise ValueError("type replacement for critical core must preserve critical=true")
                type_replacements.add(replacements[0])
            elif replacements or question["construct_id"] is not None:
                raise ValueError("type context question cannot replace a core construct")
        if module["kind"] in EXTENSION_KINDS:
            if (question["comparison_role"] == "core" or question.get("replaces")
                    or question["construct_id"] is not None):
                raise ValueError("non-type extension cannot enter core or replace a core construct")


def _validate_common_question(question: Mapping) -> None:
    """The common module holds core constructs plus diagnostic extensions.

    BASIC-BANK-EXPANSION-21 §2.2：核心题必须 ``construct_id == id``、
    ``comparison_role == "core"``、无 ``replaces``；扩展题必须
    ``aggregation == "diagnostic"``、``comparison_role == "diagnostic"``、
    ``construct_id == null``、无 ``replaces``——只做诊断，不进核心固定比较，
    也不进质量汇总。
    """
    if question["comparison_role"] == "core":
        if question["construct_id"] != question["id"] or question.get("replaces"):
            raise ValueError("common question must preserve its core construct")
        if question.get("aggregation") == "diagnostic":
            raise ValueError("core common question cannot be a diagnostic extension")
        return
    if not _is_extension_question(question):
        raise ValueError(
            "common extension question must be a diagnostic extension "
            "(comparison_role=diagnostic, aggregation=diagnostic, construct_id=null, no replaces)"
        )


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
    core_ids = core_construct_ids(modules["common"])
    if not core_ids:
        raise ValueError("common module must declare at least one core construct")
    critical_core_ids = frozenset(q["id"] for q in modules["common"]["questions"]
                                  if q["id"] in core_ids and q.get("critical"))
    question_ids: set[str] = set()
    retired_ids = set(historical_retired_ids)
    for module_id, module in modules.items():
        validate_module(module, core_ids=core_ids, critical_core_ids=critical_core_ids)
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


def _at_least_minor(old: tuple[int, int, int], new: tuple[int, int, int]) -> bool:
    """是否至少升了一个 minor（major 亦算）。"""
    return new[0] > old[0] or (new[0] == old[0] and new[1] > old[1])


def validate_upgrade(old: dict, new: dict) -> None:
    """Keep published questions immutable; allow rule-scope revisions with a minor bump.

    R3-1（所有者 2026-10-24 裁定，方案 B）：``applies_when`` 是可修订的**适用条件说明**——
    它不进入题面、anchors 或答案内容，历史答案的含义不因其变化而改变。因此允许在
    **至少一次 minor 版本升版**的前提下就地修订；题面、anchors 与题 ID 仍绝对不可变
    （同 ID 内容改动一律拒绝）。patch 升版或版本未升时的 scope 变更仍须走
    「后继题 ID」路径（旧规则保留）。

    BASIC-BANK-EXPANSION-21（所有者 2026-10-24 裁定）：基本题库允许自身升级与扩张。
    在 common 中**追加/删除诊断扩展题**只需 minor 升版（删除须留 ``retired_question_ids``
    墓碑，ID 永不复用）；**核心构念**的增删或替换仍须 major + 后继 ID 映射，以保证
    历史答案的可比性（本卡不改变这一点）。
    """
    validate_module(old)
    validate_module(new)
    if (old["module_id"], old["kind"]) != (new["module_id"], new["kind"]):
        raise ValueError("module identity/kind cannot change in place")
    old_version, new_version = _version(old["version"]), _version(new["version"])
    if new_version <= old_version:
        raise ValueError("module version must increase")
    old_questions = {q["id"]: q for q in old["questions"]}
    new_questions = {q["id"]: q for q in new["questions"]}
    old_core, new_core = core_construct_ids(old), core_construct_ids(new)
    if old_core != new_core:
        if new_version[0] <= old_version[0]:
            raise ValueError("core construct change requires a major release with successor IDs")
    if old["applies_when"] != new["applies_when"] and old_questions.keys() & new_questions.keys():
        if not _at_least_minor(old_version, new_version):
            raise ValueError(
                "applicability scope revision requires at least a minor module version bump "
                "(or successor IDs for all questions)"
            )
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
        removed_extensions = {
            qid for qid in removed
            if old["kind"] == "common" and _is_extension_question(old_questions[qid])
        }
        if removed_extensions:
            # Diagnostic retirement needs at least minor plus its tombstone.
            # A simultaneous core change may require a major release, but
            # must not create a successor requirement for diagnostic IDs.
            if not _at_least_minor(old_version, new_version):
                raise ValueError("extension removal requires at least a minor release")
            if new_version[0] > old_version[0] and old_core == new_core:
                raise ValueError(
                    "extension removal requires only a minor release; a major release "
                    "is reserved for core construct changes"
                )
        breaking_removals = removed - removed_extensions
        if breaking_removals:
            if new_version[0] <= old_version[0]:
                raise ValueError("question removal requires a major release")
            superseded = {q.get("supersedes") for q in new["questions"]}
            if not breaking_removals <= superseded:
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
    # The released core construct set comes from the archived common module, so a
    # type replacement can only target a construct this release actually carries.
    core_ids = core_construct_ids(modules["common"])
    if not core_ids:
        raise ValueError("release common module must declare at least one core construct")
    critical_core_ids = frozenset(q["id"] for q in modules["common"]["questions"]
                                  if q["id"] in core_ids and q.get("critical"))
    for module in modules.values():
        validate_module(module, core_ids=core_ids, critical_core_ids=critical_core_ids)
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
