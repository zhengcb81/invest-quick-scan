"""Build the company-coverage fixtures from this repo's saved delivery evidence.

Provenance: `docs/implementation/parallel-lanes/packages/2026-11-15-iqs-manifest-delivery-01/delivery/`
holds the real 36-question V2 owner request, its source projection and the
public read of the same workspace. The fixtures below are DERIVED from those
bytes; only the omissions used to exercise the feedback are injected. Nothing
here is a new company run, a new owner read or a new registry write.

Run from the repository root:

    python -B tests/fixtures/company_coverage/build_fixtures.py

The outputs are committed so the tests stay hermetic and fast; re-running the
builder must reproduce them byte for byte.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DELIVERY = (ROOT / "docs" / "implementation" / "parallel-lanes" / "packages"
            / "2026-11-15-iqs-manifest-delivery-01" / "delivery")
OUT = Path(__file__).resolve().parent
REGISTERED_AT = "2026-11-16T00:00:00Z"
INFORMATION_CUTOFF = "2026-11-08"


def _read(name):
    return json.loads((DELIVERY / name).read_text(encoding="utf-8"))


def _digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _request():
    request = _read("register-request-v2.json")
    manifest = request["manifest"]
    groups = manifest["lineage_groups"]
    group_by_question = {
        question_id: group
        for group in groups
        for question_id in group["question_ids"]
    }
    return request, manifest, group_by_question


def _public_ref(reference, manifest, group_by_question):
    """One public observation reference in the owner's own published shape."""
    question_id = reference["question_id"]
    question = manifest["source_release"]["questions"][question_id]
    group = group_by_question[question_id]
    return {
        "observation_id": reference["observation_id"],
        "question_id": question_id,
        "field_id": question.get("field_id"),
        "response_kind": question.get("response_kind"),
        "payload_sha256": reference["payload_sha256"],
        "run_id": None,
        "scan_id": None,
        "question_version": None,
        "source_release_sha256": reference["source_release_sha256"],
        "lineage_group_id": reference["lineage_group_id"],
        "aggregation_role": group["aggregation_role"],
        "question_definition_sha256": reference["question_definition_sha256"],
        "question_semantic_sha256": reference["question_semantic_sha256"],
        "construct_id": question.get("construct_id"),
    }


def _snapshot(*, kept_question_ids, declared_missing, result_salt,
              declared_observed=None):
    request, manifest, group_by_question = _request()
    refs = [_public_ref(reference, manifest, group_by_question)
            for reference in request["observations"]
            if reference["question_id"] in set(kept_question_ids)]
    rubrics = sorted({group["rubric_version"] for group in manifest["lineage_groups"]})
    return {
        "result_id": "cas_" + _digest({"salt": result_salt,
                                       "refs": [ref["observation_id"] for ref in refs]})[:20],
        "status": "formal",
        "status_reasons": [],
        "completeness_basis": "release_authority",
        "authority_sha256": manifest["lineage_provenance_sha256"],
        "entity_id": request["entity_id"],
        "listing_id": None,
        "analysis_subject_id": None,
        "analysis_subject_revision": None,
        "information_cutoff": INFORMATION_CUTOFF,
        "registered_at": REGISTERED_AT,
        "registry_sequence": 1,
        "questionnaire_version": manifest["source_release"]["catalog_version"],
        "scale_version": rubrics[0] if len(rubrics) == 1 else None,
        "module_package_id": manifest["source_release"]["module_package_id"],
        "module_release_id": manifest["source_release"]["release_id"],
        "completeness": {
            "manifest_question_count": len(group_by_question),
            "observed_count": (len(refs) if declared_observed is None
                               else declared_observed),
            "missing_question_ids": sorted(declared_missing),
        },
        "qualification": {
            "receipted_observation_count": 0,
            "unreceipted_observation_count": len(refs),
            "receipts": {},
        },
        "aggregate_score": None,
        "aggregate_score_reason": "company_aggregate_authority_missing",
        "observation_refs": refs,
        "verification": {"observation_store": "verified",
                         "mismatched_observation_ids": []},
        "honesty": {"financial_accuracy_proven": False,
                    "formal_research_accepted": False},
        "assessment_protocol": manifest["protocol"],
        "source_release_sha256": manifest["source_release_sha256"],
        "lineage_provenance_sha256": manifest["lineage_provenance_sha256"],
        "scale_versions": rubrics,
        "lineage_groups": [
            {
                "lineage_group_id": group["lineage_group_id"],
                "rubric_version": group["rubric_version"],
                "aggregation_role": group["aggregation_role"],
                "question_ids": list(group["question_ids"]),
            }
            for group in manifest["lineage_groups"]
        ],
    }


def _single_scale_snapshot():
    """A legal one-rubric result: two questions, one group, nothing missing."""
    request, _, _ = _request()
    questions = {
        "IQS_01": {"field_id": "score.iqs_01", "response_kind": "score",
                   "construct_id": "CUSTOMER_VALUE", "rubric_version": "2.0.0"},
        "IQS_02": {"field_id": "score.iqs_02", "response_kind": "score",
                   "construct_id": "UNIT_ECONOMICS", "rubric_version": "2.0.0"},
    }
    refs = []
    for index, (question_id, question) in enumerate(sorted(questions.items()), start=1):
        refs.append({
            "observation_id": "obs_" + f"{index:064x}",
            "question_id": question_id,
            "field_id": question["field_id"],
            "response_kind": "score",
            "payload_sha256": f"{index + 10:064x}",
            "run_id": None,
            "scan_id": None,
            "question_version": None,
            "source_release_sha256": "f" * 64,
            "lineage_group_id": "lg_" + "1" * 20,
            "aggregation_role": "quality_core",
            "question_definition_sha256": "a" * 64,
            "question_semantic_sha256": "b" * 64,
            "construct_id": question["construct_id"],
        })
    return {
        "result_id": "cas_" + "2" * 20,
        "status": "formal",
        "status_reasons": [],
        "completeness_basis": "release_authority",
        "authority_sha256": "c" * 64,
        "entity_id": request["entity_id"],
        "listing_id": "LST_1",
        "analysis_subject_id": None,
        "analysis_subject_revision": None,
        "information_cutoff": INFORMATION_CUTOFF,
        "registered_at": REGISTERED_AT,
        "registry_sequence": 1,
        "questionnaire_version": "3.2.1",
        "scale_version": "2.0.0",
        "module_package_id": "pkg_" + "d" * 64,
        "module_release_id": "modrel_" + "e" * 64,
        "completeness": {"manifest_question_count": 2, "observed_count": 2,
                         "missing_question_ids": []},
        "qualification": {"receipted_observation_count": 2,
                          "unreceipted_observation_count": 0, "receipts": {}},
        "aggregate_score": None,
        "aggregate_score_reason": "company_aggregate_authority_missing",
        "observation_refs": refs,
        "verification": {"observation_store": "verified",
                         "mismatched_observation_ids": []},
        "honesty": {"financial_accuracy_proven": False,
                    "formal_research_accepted": False},
        "assessment_protocol": "stockwiki.company_assessment/2",
        "source_release_sha256": "f" * 64,
        "lineage_provenance_sha256": "c" * 64,
        "scale_versions": ["2.0.0"],
        "lineage_groups": [{
            "lineage_group_id": "lg_" + "1" * 20,
            "rubric_version": "2.0.0",
            "aggregation_role": "quality_core",
            "question_ids": ["IQS_01", "IQS_02"],
        }],
    }


def _receipts():
    """Per-question terminal states recorded in the delivery STATUS.md.

    Words come from the same worktree's run log: `scored` and
    `insufficient_evidence` are persisted observations; `content_filter`,
    `length` and `search_unverified` are the provider-side terminal states the
    owner protocol had to close before the question could be re-issued.
    """
    request, _, _ = _request()
    observed = {reference["question_id"] for reference in request["observations"]}
    statuses = {}
    for question_id in sorted(observed):
        statuses[question_id] = {"status": "completed", "answer_state": None,
                                 "observation_id": None}
    # PORTER_01/02: provider content filter closed by a work decision, then
    # re-issued; both finally landed as observations.
    for question_id in ("PORTER_01", "PORTER_02"):
        statuses[question_id]["answer_state"] = "insufficient_evidence"
        statuses[question_id]["provider_terminal"] = "content_filter"
    # DUPONT_04/05: truncated responses, re-issued at a larger output bound.
    for question_id in ("DUPONT_04", "DUPONT_05"):
        statuses[question_id]["answer_state"] = "insufficient_evidence"
        statuses[question_id]["provider_terminal"] = "length"
    # DUPONT_06/07: three unverified searches before a successful fourth.
    for question_id in ("DUPONT_06", "DUPONT_07"):
        statuses[question_id]["answer_state"] = "insufficient_evidence"
        statuses[question_id]["provider_terminal"] = "search_unverified"
    return {"source": "2026-11-15-iqs-manifest-delivery-01/STATUS.md",
            "questions": statuses}


def _dump(name, value):
    (OUT / name).write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")


def _answers_fixture():
    """A real thin-scan run reduced to the fields the checker reads.

    Source: `runs/thin-bank-catl-full-2026-10-22/final/answers.json` in this
    worktree (not tracked by Git). 24 questions were answered against a
    38-question bank; per-question statuses, scores and the presence of an
    evidence URL are preserved verbatim, while the model prose is dropped.
    """
    source = ROOT / "runs" / "thin-bank-catl-full-2026-10-22" / "final" / "answers.json"
    document = json.loads(source.read_text(encoding="utf-8"))
    answers = []
    for answer in document["answers"]:
        evidence = answer.get("evidence") or []
        answers.append({
            "question_id": answer.get("question_id"),
            "status": answer.get("status"),
            "score": answer.get("score"),
            "evidence": [{"url": item.get("url")} for item in evidence if isinstance(item, dict)],
            "problems": list(answer.get("problems") or []),
        })
    return {
        "_derived_from": "runs/thin-bank-catl-full-2026-10-22/final/answers.json",
        "_bodies_dropped": "model summaries and evidence titles are removed",
        "company": document.get("company"),
        "draft": document.get("draft"),
        "verified": document.get("verified"),
        "as_of": document.get("as_of"),
        "importable": document.get("importable"),
        "provenance": document.get("provenance"),
        "bank": {"package_id": document["bank"].get("package_id"),
                 "release_id": document["bank"].get("release_id"),
                 "question_count": document["bank"].get("question_count"),
                 "max_questions": document["bank"].get("max_questions"),
                 "mode": document["bank"].get("mode")},
        "meta": {"calls": document["meta"].get("calls"),
                 "searches": document["meta"].get("searches")},
        "answers": answers,
    }


def main():
    request, manifest, group_by_question = _request()
    all_ids = sorted(group_by_question)
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. The complete mixed-scale result: 36/36 across six lineage groups.
    _dump("result-complete-mixed.json",
          _snapshot(kept_question_ids=all_ids, declared_missing=[], result_salt="complete"))

    # 2. An honest partial: one question was never observed and the owner says so.
    partial_ids = [question_id for question_id in all_ids if question_id != "PORTER_05"]
    _dump("result-partial-35of36.json",
          _snapshot(kept_question_ids=partial_ids, declared_missing=["PORTER_05"],
                    result_salt="partial"))

    # 3. The same 35 references while the owner still claims 36/36: the injected
    #    contradiction the feedback must report instead of forwarding as complete.
    _dump("result-partial-claiming-complete.json",
          _snapshot(kept_question_ids=partial_ids, declared_missing=[],
                    result_salt="claiming-complete",
                    declared_observed=len(all_ids)))

    # 4. A whole lineage group dropped (2.0.0 / quality_core, three questions).
    dropped = sorted(question_id for question_id, group in group_by_question.items()
                     if (group["rubric_version"], group["aggregation_role"])
                     == ("2.0.0", "quality_core"))
    kept = [question_id for question_id in all_ids if question_id not in dropped]
    _dump("result-group-dropped.json",
          _snapshot(kept_question_ids=kept, declared_missing=dropped,
                    result_salt="group-dropped"))

    # 5. A legal single-scale control.
    _dump("result-single-scale.json", _single_scale_snapshot())

    # 6. Per-question receipts for the offline classification.
    _dump("receipts-manifest-delivery-01.json", _receipts())

    # 7. The real public read of the same workspace: no registered result.
    read_after = json.loads((DELIVERY / "read-after.json").read_text(encoding="utf-8"))
    _dump("owner-read-not-registered.json", json.loads(read_after["stdout"]))

    # 8. A real thin-scan run whose answers cover 24 of the bank's 38 questions.
    _dump("answers-partial-24of38.json", _answers_fixture())

    print("fixtures written:", sorted(path.name for path in OUT.glob("*.json")))


if __name__ == "__main__":
    main()
