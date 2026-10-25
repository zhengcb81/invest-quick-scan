"""Versioned question-bank manifest loader for thin scans.

The manifest is the frozen composition produced by scripts/question_sets.py
compose (or compose-route). It binds the module package/release, selected
modules, per-question hashes and construct/core roles. Thin scans that use it
record exactly which bank produced each answer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CORE_PREFIX = "IQS_"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    questions = document.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("bank manifest has no questions")
    package_id = document.get("module_package_id")
    release_id = document.get("module_release_id")
    modules = document.get("modules")
    if not isinstance(package_id, str) or not package_id:
        raise ValueError("bank manifest missing module_package_id")
    if not isinstance(release_id, str) or not release_id:
        raise ValueError("bank manifest missing module_release_id")
    if not isinstance(modules, list) or not modules:
        raise ValueError("bank manifest missing modules")
    records = []
    seen = set()
    for question in questions:
        qid = question.get("id")
        if not isinstance(qid, str) or not qid or qid in seen:
            raise ValueError("bank manifest has missing or duplicate question id")
        seen.add(qid)
        construct = question.get("construct_id")
        core = bool(
            isinstance(construct, str)
            and construct.startswith(CORE_PREFIX)
            and question.get("comparison_role") == "core"
        )
        records.append(
            {
                "id": qid,
                "question": question.get("question") or "",
                "prompt": question.get("prompt") or "",
                "dimension": question.get("dimension"),
                "priority": question.get("priority"),
                "module_id": question.get("module_id"),
                "construct_id": construct,
                "comparison_role": question.get("comparison_role"),
                "scope": question.get("scope"),
                "evidence": question.get("evidence") or [],
                "anchors": question.get("anchors") or {},
                "prompt_sha256": question.get("prompt_sha256"),
                "semantic_sha256": question.get("semantic_sha256"),
                "definition_sha256": question.get("definition_sha256"),
                "core": core,
            }
        )
    return {
        "identity": {
            "manifest_path": str(path),
            "manifest_sha256": file_sha256(path),
            "package_id": package_id,
            "release_id": release_id,
            "modules": list(modules),
            "module_locks": document.get("module_locks") or [],
            "route_decision_id": (document.get("route_decision") or {}).get("decision_id"),
            "as_of": (document.get("profile") or {}).get("as_of"),
            "profile": {
                "company_type": (document.get("profile") or {}).get("company_type"),
                "industry_modules": (document.get("profile") or {}).get("industry_modules"),
                "stage": (document.get("profile") or {}).get("stage"),
                "overlays": (document.get("profile") or {}).get("overlays"),
            },
            "mode": document.get("mode"),
            "max_questions": document.get("max_questions"),
            "question_count": len(records),
            "method_id": document.get("method_id"),
        },
        "questions": records,
    }


def summarize(records: list[dict]) -> dict:
    diagnostic = [r for r in records if r.get("comparison_role") == "diagnostic"
                  or r.get("aggregation") == "diagnostic"]
    core = [r for r in records if r.get("core") and r not in diagnostic]
    context = [r for r in records if not r.get("core") and r not in diagnostic]
    core_scored = [r for r in core if r.get("status") == "scored"]
    context_scored = [r for r in context if r.get("status") == "scored"]

    def mean(rows: list[dict]):
        values = [r["score"] for r in rows if isinstance(r.get("score"), int)]
        return round(sum(values) / len(values), 2) if values else None

    return {
        "method": "draft_unweighted_mean_of_scored_not_official",
        "core_total": len(core),
        "core_scored": len(core_scored),
        "core_mean": mean(core_scored),
        "context_total": len(context),
        "context_scored": len(context_scored),
        "context_mean": mean(context_scored),
        "diagnostic_total": len(diagnostic),
        "diagnostic_scored": sum(r.get("status") == "scored" for r in diagnostic),
    }
