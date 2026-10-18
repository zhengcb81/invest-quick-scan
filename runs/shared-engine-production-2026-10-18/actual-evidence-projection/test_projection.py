"""Actual locked public inputs; synthetic task data grants no owner authority."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from iqs_company_agent_lab.canonical import canonical_json
from iqs_company_agent_lab.evidence import EvidenceBoard
from project_existing_sources import ProjectionRejected, project_existing_sources


ROOT = Path(__file__).resolve().parents[3]
INPUTS = ROOT / "runs/real-contrast-2026-10-16-03/inputs"


@pytest.fixture
def inputs(monkeypatch):
    import socket
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network is forbidden"))
    lock = json.loads((INPUTS.parent / "inputs.lock.json").read_text(encoding="utf-8"))
    refs = {x["path"]: x for x in lock["files"] if x["path"] in {"identity.json", "evidence-board.json"}}
    board = (INPUTS / "evidence-board.json").read_bytes()
    identity = (INPUTS / "identity.json").read_bytes()
    ident = json.loads(identity)
    aid, revision = ident["subject_key"].rsplit("@", 1)
    subject = dict(entity_id=ident["entity_id"], primary_issuer_id=ident["entity_id"],
                   analysis_subject_id=aid, analysis_subject_revision=int(revision), scope="entity")
    company = dict(origin="owner_public", subject={"subject_ref": subject})
    raw = canonical_json(company).encode("utf-8")
    ref = dict(path="native-derived/company.json", bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    task = SimpleNamespace(company_doc=company, company_ref=ref,
                           raw={"information_cutoff": "2026-10-13"},
                           limits={"excerpt_chars_per_source": 2000, "evidence_context_chars": 12000})
    yield task, dict(public_board_raw=board, identity_raw=identity, locked_refs=refs)
    assert (INPUTS / "evidence-board.json").read_bytes() == board
    assert (INPUTS / "identity.json").read_bytes() == identity


def test_actual_nine_sources_preserve_bytes_and_original_intake(inputs):
    task, kwargs = inputs
    document, metadata = project_existing_sources(task, **kwargs)
    original = json.loads(kwargs["public_board_raw"])
    assert len(document["records"]) == len(original["sources"]) == 9
    for before, after in zip(original["sources"], document["records"]):
        assert before["bounded_excerpt"].encode("utf-8") == after["excerpt"].encode("utf-8")
        assert hashlib.sha256(before["bounded_excerpt"].encode("utf-8")).hexdigest() == after["excerpt_sha256"]
        if "excerpt_sha256" in before:
            assert before["excerpt_sha256"] == after["excerpt_sha256"]
        assert before["official_url"] == after["source_url"]
        assert before["publication_date"] == after["published_at"]
        assert before["accessed_at_utc"] == after["retrieved_at_utc"]
        assert after["support_status"] == "unverified"
        assert before["limitations"] == after["limitations"][:len(before["limitations"])]
        assert all(after[x] is None for x in ("period_start", "period_end", "currency", "unit", "accounting_basis"))
    board = EvidenceBoard(2000)
    assert not board.intake(document["records"], task.company_ref)["rejected"]
    assert metadata["omitted_coordinator_fact_count"] == 18
    assert sum(x["excerpt_hash_origin"] == "original_content_hash"
               for x in metadata["source_bindings"]) == 3
    assert metadata["authority_granted"] is metadata["financial_qualification_granted"] is False


@pytest.mark.parametrize("key,value", [
    ("entity_id", "other"), ("primary_issuer_id", "other"),
    ("analysis_subject_revision", 2), ("analysis_subject_id", "other"), ("scope", "segment"),
])
def test_wrong_entity_revision_or_scope_rejected(inputs, key, value):
    task, kwargs = inputs
    task.company_doc["subject"]["subject_ref"][key] = value
    with pytest.raises(ProjectionRejected):
        project_existing_sources(task, **kwargs)


@pytest.mark.parametrize("field", ["public_board_raw", "identity_raw"])
def test_original_raw_input_tampering_rejected(inputs, field):
    task, kwargs = inputs
    kwargs[field] += b" "
    with pytest.raises(ProjectionRejected, match="locked_input"):
        project_existing_sources(task, **kwargs)


@pytest.mark.parametrize("change", ["excerpt", "duplicate", "future_publication", "new_cutoff", "company_ref", "context_cap",
                                    "legacy_hash", "ineligible", "nonboolean_eligibility", "conflicting_alias", "no_digest"])
def test_semantic_rejections_even_after_non_authority_input_hash_reseal(inputs, change):
    task, kwargs = inputs
    doc = json.loads(kwargs["public_board_raw"])
    if change == "excerpt":
        doc["sources"][0]["bounded_excerpt"] += " injected"
    elif change == "duplicate":
        doc["sources"].append(copy.deepcopy(doc["sources"][0]))
    elif change == "future_publication":
        doc["sources"][0]["publication_date"] = "2026-10-14"
    elif change == "new_cutoff":
        task.raw["information_cutoff"] = "2026-10-18"
    elif change == "company_ref":
        task.company_ref["bytes"] += 1
    elif change == "context_cap":
        task.limits["evidence_context_chars"] = 1
    elif change == "legacy_hash":
        doc["sources"][6]["bounded_excerpt"] += " changed"
    elif change == "ineligible":
        doc["sources"][6]["eligible_for_context"] = False
    elif change == "nonboolean_eligibility":
        doc["sources"][6]["eligible_for_context"] = "true"
    elif change == "conflicting_alias":
        doc["sources"][6]["excerpt_sha256"] = "0" * 64
    elif change == "no_digest":
        del doc["sources"][6]["content_hash"]
    raw = json.dumps(doc).encode("utf-8")
    kwargs["public_board_raw"] = raw
    kwargs["locked_refs"] = copy.deepcopy(kwargs["locked_refs"])
    kwargs["locked_refs"]["evidence-board.json"].update(bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ProjectionRejected):
        project_existing_sources(task, **kwargs)


def test_projection_does_not_mutate_task_or_input_contracts(inputs):
    task, kwargs = inputs
    before = copy.deepcopy(vars(task))
    result, meta = project_existing_sources(task, **kwargs)
    result["records"][0]["issuer_ref"]["path"] = "changed"
    assert vars(task) == before
    assert meta["native_company_ref"] == task.company_ref
