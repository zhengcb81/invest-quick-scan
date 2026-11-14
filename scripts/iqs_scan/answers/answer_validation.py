"""Versioned public answer-validation API owned by IQS.

The shared execution engine delegates frozen answer semantics and resource
resolution here instead of inspecting validator module locations itself.
"""
from __future__ import annotations

from iqs_scan import REPO_ROOT

import copy
import json
from pathlib import Path

API_PROTOCOL = "iqs.answer-validation-api/1.1.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "AnswerSemanticsRejected",
    "original_answer_resources",
    "project_original_semantic_resources",
    "frozen_answer_semantics",
})
SEMANTIC_RESOURCES_PROTOCOL = "iqs.answer-semantic-resources/1.0.0"
_SEMANTIC_RESOURCE_KEYS = (
    "schemas/answer-content.schema.json",
    "questions/metric-registry.json",
)

class AnswerSemanticsRejected(ValueError):
    """The original frozen answer context cannot be validated."""

def original_answer_resources(context, root):
    """Resolve resources already named by the original owner, not current files.

    Production contexts name an immutable module package. Older research
    contexts carry only the two original digests; retain that format by looking
    up matching existing resources, without requiring new fields or rewriting
    the task. An unrelated new registry entry cannot change old semantics.
    """
    from iqs_scan.questions import api as module_registry
    from . import standard_answers

    names = {"answer_schema_sha256": "schemas/answer-content.schema.json",
             "metric_registry_sha256": "questions/metric-registry.json"}
    if not isinstance(context, dict):
        raise AnswerSemanticsRejected("original_answer_context_required")

    def matches(resources):
        return all(standard_answers.digest(resources[name]) == context.get(key)
                   for key, name in names.items())

    ids = {row.get("metadata", {}).get("module_package_id")
           for row in context.get("questions", {}).values() if isinstance(row, dict)} - {None}
    if ids:
        if len(ids) != 1:
            raise AnswerSemanticsRejected("original_answer_resource_package_mismatch")
        package, _, _, _ = module_registry.load_package(next(iter(ids)), root=root)
        resources = package["format_resources"]
        return copy.deepcopy(resources)

    # Legacy research contexts have no package ID. Resource hashes are lookup
    # keys, not a requirement that today's catalog still has the same hash.
    legacy_resources = None
    try:
        resources = {name: standard_answers.read_resource(root / name) for name in names.values()}
        legacy_resources = resources
        if matches(resources):
            return resources
    except (OSError, ValueError, KeyError, TypeError):
        # An unavailable current authoring tree is not a prerequisite for
        # reading an old, independently verified resource package.
        pass
    for path in sorted((root / "questions/releases/packages").glob("pkg_*.json")):
        try:
            package, _, _, _ = module_registry.load_package(path.stem, root=root)
        except (OSError, ValueError, KeyError, TypeError):
            continue  # An unrelated broken package must not hide the original.
        if matches(package["format_resources"]):
            return copy.deepcopy(package["format_resources"])
    # Original research-only contexts did not bind a package. Their descriptive
    # whole-resource hashes were never an admission gate. Keep that old reader
    # when no original archive can be identified, rather than inventing one.
    if legacy_resources is not None:
        return legacy_resources
    raise AnswerSemanticsRejected("original_answer_resources_unavailable")


def _context_package_id(context):
    questions = context.get("questions", {}) if isinstance(context, dict) else None
    if not isinstance(questions, dict):
        raise AnswerSemanticsRejected("original_answer_context_required")
    package_ids = {
        row.get("metadata", {}).get("module_package_id")
        for row in questions.values()
        if isinstance(row, dict) and isinstance(row.get("metadata"), dict)
        and row["metadata"].get("module_package_id") is not None
    }
    if len(package_ids) > 1 or any(not isinstance(value, str) or not value for value in package_ids):
        raise AnswerSemanticsRejected("original_answer_resource_package_mismatch")
    return next(iter(package_ids), None)


def project_original_semantic_resources(context, *, release_root):
    """Resolve the original owner's frozen semantic files into a path-free DTO.

    ``release_root`` is a transient resolver input. It is never returned or
    persisted; callers receive only the two detached JSON resources used by the
    answer validator, their content digests, and the bound observation context.
    """
    from . import standard_answers

    from pathlib import Path

    if not isinstance(context, dict):
        raise AnswerSemanticsRejected("original_answer_context_required")
    try:
        root = Path(release_root)
        if not root.is_absolute():
            raise ValueError("absolute_release_root_required")
        resources = original_answer_resources(context, root)
        selected = {key: copy.deepcopy(resources[key]) for key in _SEMANTIC_RESOURCE_KEYS}
        projected = {
            "protocol": SEMANTIC_RESOURCES_PROTOCOL,
            "context_sha256": standard_answers.digest(context),
            "module_package_id": _context_package_id(context),
            "resource_digests": {
                key: standard_answers.digest(value) for key, value in selected.items()
            },
            "format_resources": selected,
        }
        json.dumps(projected, ensure_ascii=False, sort_keys=True, allow_nan=False)
        return projected
    except AnswerSemanticsRejected:
        raise
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise AnswerSemanticsRejected("original_semantic_resources_unavailable") from error


def _resources_from_projection(context, projection):
    from . import standard_answers

    expected_fields = {
        "protocol", "context_sha256", "module_package_id", "resource_digests",
        "format_resources",
    }
    if not isinstance(projection, dict) or set(projection) != expected_fields:
        raise AnswerSemanticsRejected("original_semantic_resources_projection_invalid")
    if (
        projection.get("protocol") != SEMANTIC_RESOURCES_PROTOCOL
        or projection.get("context_sha256") != standard_answers.digest(context)
        or projection.get("module_package_id") != _context_package_id(context)
    ):
        raise AnswerSemanticsRejected("original_semantic_context_mismatch")
    resources = projection.get("format_resources")
    digests = projection.get("resource_digests")
    if (
        not isinstance(resources, dict)
        or set(resources) != set(_SEMANTIC_RESOURCE_KEYS)
        or not isinstance(digests, dict)
        or set(digests) != set(_SEMANTIC_RESOURCE_KEYS)
        or any(not isinstance(resources[key], dict) for key in _SEMANTIC_RESOURCE_KEYS)
        or any(
            not isinstance(digests[key], str)
            or digests[key] != standard_answers.digest(resources[key])
            for key in _SEMANTIC_RESOURCE_KEYS
        )
    ):
        raise AnswerSemanticsRejected("original_semantic_resources_digest_mismatch")
    return copy.deepcopy(resources)


def frozen_answer_semantics(task, context, *, release_root=None, semantic_resources=None):
    """Validate original questions; whole registry hashes are provenance only.

    Adding an unrelated metric or schema annotation must not invalidate an
    already received answer. Actual question, unit and evidence semantics are
    still validated below, without changing the original body or hash record.
    """
    from . import standard_answers
    from iqs_scan.questions import api as question_prompts

    if semantic_resources is not None:
        if release_root is not None:
            raise AnswerSemanticsRejected("ambiguous_original_semantic_resources")
        resources = _resources_from_projection(context, semantic_resources)
    else:
        root = Path(release_root) if release_root is not None else REPO_ROOT
        resources = original_answer_resources(context, root)
    schema = resources["schemas/answer-content.schema.json"]
    registry = resources["questions/metric-registry.json"]
    from iqs_company_agent_lab.api import task_from_snapshot, task_snapshot

    if not isinstance(task, dict) or task.get("protocol") != "iqs.company-agent-task-contract/1.1.0":
        task = task_snapshot(task)
    try:
        task_from_snapshot(task)
    except (TypeError, ValueError) as error:
        raise AnswerSemanticsRejected("original_semantic_task_contract_invalid") from error
    task_questions = task.get("questions")
    question_ids = task.get("question_ids")
    raw = task.get("raw")
    if not isinstance(task_questions, list) or not isinstance(question_ids, list) or not isinstance(raw, dict):
        raise AnswerSemanticsRejected("original_semantic_task_contract_required")
    questions = {row["question_id"]: copy.deepcopy(row["question"])
                 for row in task_questions if isinstance(row, dict)
                 and isinstance(row.get("question_id"), str)
                 and isinstance(row.get("question"), dict)}
    if (len(questions) != len(task_questions)
        or set(questions) != set(question_ids)
        or any(question.get("id") != qid for qid, question in questions.items())):
        raise AnswerSemanticsRejected("original_semantic_question_contract_required")
    cutoff = raw.get("information_cutoff")
    if not isinstance(cutoff, str) or not cutoff:
        raise AnswerSemanticsRejected("original_semantic_information_cutoff_required")

    def validate_original(answer, question_id):
        if question_id not in questions or answer.get("question_id") != question_id:
            raise ValueError("original semantic question mismatch")
        before = copy.deepcopy(answer)
        standard_answers.validate_content(answer, questions[question_id], cutoff,
                                          answer_schema=schema, metric_registry=registry)
        if answer != before:
            raise ValueError("original semantic validator changed answer")

    validate_original.prompt_rules = tuple(question_prompts.typed_semantic_rules(q)
                                            for q in questions.values())
    validate_original.legacy_prompt_rules = tuple(question_prompts.legacy_typed_semantic_rules(q)
                                                   for q in questions.values())
    return validate_original
