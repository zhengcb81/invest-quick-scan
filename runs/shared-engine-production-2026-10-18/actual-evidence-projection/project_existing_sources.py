"""Explicit, no-I/O research input adapter; grants no execution authority.

Reuse Company EvidenceBoard validation. Preserve only original bounded source
excerpts. The older coordinator fact summaries have no explicit fact/source
edges and therefore are not silently turned into source-supported claims.
"""
from __future__ import annotations

import copy
import hashlib


class ProjectionRejected(ValueError):
    pass


def project_existing_sources(task, *, public_board_raw, identity_raw, locked_refs):
    from iqs_company_agent_lab.canonical import canonical_json, sha256_hex, sha256_text
    from iqs_company_agent_lab.evidence import EvidenceBoard
    from iqs_company_agent_lab.strictjson import loads

    for name, raw in (("evidence-board.json", public_board_raw), ("identity.json", identity_raw)):
        ref = locked_refs[name]
        if (type(raw) is not bytes or len(raw) != ref["bytes"]
                or hashlib.sha256(raw).hexdigest() != ref["raw_sha256"]):
            raise ProjectionRejected("original_locked_input_changed")
    original, identity = loads(public_board_raw.decode("utf-8")), loads(identity_raw.decode("utf-8"))
    company, subject = task.company_doc, task.company_doc.get("subject", {}).get("subject_ref", {})
    if (company.get("origin") != "owner_public" or subject.get("scope") != "entity"
            or subject.get("entity_id") != identity.get("entity_id")
            or subject.get("primary_issuer_id") != identity.get("entity_id")
            or identity.get("subject_key") != (str(subject.get("analysis_subject_id")) + "@"
                                              + str(subject.get("analysis_subject_revision")))):
        raise ProjectionRejected("explicit_native_entity_revision_mapping_required")
    ref = task.company_ref
    raw_company = canonical_json(company).encode("utf-8")
    if ref.get("sha256") != hashlib.sha256(raw_company).hexdigest() or ref.get("bytes") != len(raw_company):
        raise ProjectionRejected("native_derived_company_reference_changed")
    if original.get("cutoff") != task.raw.get("information_cutoff"):
        raise ProjectionRejected("new_cutoff_requires_explicit_new_evidence_registration")
    if not isinstance(original.get("sources"), list) or not original["sources"]:
        raise ProjectionRejected("original_bounded_sources_required")
    records, bindings, seen = [], [], set()
    for source in original["sources"]:
        sid, excerpt = source["source_id"], source["bounded_excerpt"]
        excerpt_sha = sha256_text(excerpt)
        original_excerpt_sha = source.get("excerpt_sha256")
        original_content_hash = source.get("content_hash")
        if original_excerpt_sha is None and original_content_hash is None:
            raise ProjectionRejected("original_excerpt_digest_required")
        if (sid in seen or any(value is not None and value != excerpt_sha
                               for value in (original_excerpt_sha, original_content_hash))):
            raise ProjectionRejected("duplicate_source_or_excerpt_hash_changed")
        if "eligible_for_context" in source and source["eligible_for_context"] is not True:
            raise ProjectionRejected("original_source_ineligible_for_context")
        seen.add(sid)
        limitations = copy.deepcopy(source["limitations"])
        limitations += [
            "Source excerpt only; no financial qualification or native search-proof checkpoint.",
            "Accounting scope, period, unit, currency and basis are unspecified in this source record; do not infer them from other records.",
            "Original coordinator fact summaries are omitted because explicit fact-to-source edges are absent.",
        ]
        record = dict(evidence_id=sid, issuer_ref=copy.deepcopy(ref), scope="unknown",
                      period_start=None, period_end=None, unit=None, currency=None,
                      accounting_basis=None, source_url=source["official_url"],
                      published_at=source["publication_date"], retrieved_at_utc=source["accessed_at_utc"],
                      excerpt=excerpt, excerpt_sha256=excerpt_sha,
                      claim_kind="fact", support_status="unverified", supersedes_id=None,
                      limitations=limitations)
        records.append(record)
        bindings.append(dict(evidence_id=sid, original_source_sha256=sha256_hex(source),
                             original_excerpt_sha256=original_excerpt_sha,
                             original_content_hash=original_content_hash,
                             original_eligible_for_context=source.get("eligible_for_context"),
                             excerpt_hash_origin=("original_source" if original_excerpt_sha is not None
                                                  else "original_content_hash"),
                             projected_record_sha256=sha256_hex(record)))
    board = EvidenceBoard(int(task.limits["excerpt_chars_per_source"]))
    result = board.intake(records, ref)
    if result["rejected"] or len(result["accepted"]) != len(records):
        raise ProjectionRejected("original_company_evidence_intake_rejected")
    if sum(len(x["excerpt"]) for x in records) > task.limits["evidence_context_chars"]:
        raise ProjectionRejected("original_context_limit_exceeded_never_silently_truncate")
    document = {"records": records}
    provenance = dict(protocol="iqs.existing-public-source-projection/1.0.0",
        input_refs=copy.deepcopy(locked_refs), native_subject_ref=copy.deepcopy(subject),
        native_company_ref=copy.deepcopy(ref), information_cutoff=task.raw["information_cutoff"],
        source_bindings=bindings, projected_document_sha256=sha256_hex(document),
        omitted_coordinator_fact_count=len(original.get("facts", [])),
        actual_new_search_requests=0, authority_granted=False,
        financial_qualification_granted=False, native_search_proof_granted=False)
    return document, provenance
