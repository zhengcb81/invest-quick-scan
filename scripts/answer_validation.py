"""Versioned public answer-validation API owned by IQS.

The shared execution engine delegates frozen answer semantics and resource
resolution here instead of inspecting validator module locations itself.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

API_PROTOCOL = "iqs.answer-validation-api/1.0.0"

class AnswerSemanticsRejected(ValueError):
    """The original frozen answer context cannot be validated."""

def original_answer_resources(context, root):
    """Resolve resources already named by the original owner, not current files.

    Production contexts name an immutable module package. Older research
    contexts carry only the two original digests; retain that format by looking
    up matching existing resources, without requiring new fields or rewriting
    the task. An unrelated new registry entry cannot change old semantics.
    """
    import module_registry
    import standard_answers

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
        resources = {name: standard_answers.library.read_json(root / name) for name in names.values()}
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


def frozen_answer_semantics(task, context, *, release_root=None):
    """Validate original questions; whole registry hashes are provenance only.

    Adding an unrelated metric or schema annotation must not invalidate an
    already received answer. Actual question, unit and evidence semantics are
    still validated below, without changing the original body or hash record.
    """
    import sys

    scripts = Path(__file__).resolve().parent
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import standard_answers
    import question_prompts

    if (getattr(standard_answers, "ANSWER_VALIDATION_API_PROTOCOL", None)
            != "iqs.standard-answer-validation/1.0.0"
            or getattr(question_prompts, "SEMANTIC_RULES_API_PROTOCOL", None)
            != "iqs.question-prompt-semantics/1.0.0"):
        raise AnswerSemanticsRejected("original_standard_answer_validator_required")
    root = Path(release_root) if release_root is not None else scripts.parent
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
