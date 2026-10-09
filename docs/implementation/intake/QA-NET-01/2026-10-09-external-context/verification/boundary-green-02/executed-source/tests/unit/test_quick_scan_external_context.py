"""External retrieval safety regressions before enabling the production path.

Only synthetic provider data and private pytest paths are used. These assert
behavior of existing functions, so RED is a product gap, not a missing import.
"""
import json

import pytest

from src.config.quick_scan_search_policy import SearchPolicyRejected, load_search_policy
from src.providers.external_search_parsers import unwrap_json_text
from src.providers.search_capability import verify_evidence_binding
from src.utils.quick_scan_evidence import build_evidence_package
from tests.unit.test_qa_net01_search_boundary import _policy_document


def _policy(tmp_path, monkeypatch, mutate):
    monkeypatch.setenv("BRAVE_API_KEY", "synthetic-test-only")
    document = _policy_document()
    mutate(document)
    path = tmp_path / "search-policy.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return load_search_policy(path)


@pytest.mark.parametrize("reference", [None, "", "   "])
def test_confirmed_storage_requires_a_nonempty_entitlement_reference(tmp_path, monkeypatch, reference):
    policy = _policy(tmp_path, monkeypatch, lambda d: d["external_routes"][0]["storage_rights"].update(entitlement_ref=reference))
    assert policy.admitted == ()
    assert any(r["reason"] == "storage_rights_unconfirmed" for r in policy.rejections)


@pytest.mark.parametrize("field", ["selection", "retrieval", "budget"])
def test_unknown_execution_fields_cannot_be_silently_ignored(tmp_path, monkeypatch, field):
    with pytest.raises(SearchPolicyRejected):
        _policy(tmp_path, monkeypatch, lambda d: d[field].update(future_unapproved_override=True))


@pytest.mark.parametrize("raw", ['{"results": [], "results": [1]}', '{"results": [], "value": NaN}', '{"results": [], "value": 1e400}'])
def test_ambiguous_or_nonfinite_search_json_is_refused(raw):
    with pytest.raises(ValueError):
        unwrap_json_text(raw)


def test_object_input_does_not_bypass_search_response_byte_bound():
    with pytest.raises(ValueError):
        unwrap_json_text({"results": [{"snippet": "x" * 4096}]}, max_bytes=1024)


def test_query_target_alone_does_not_certify_a_candidate_company():
    package = build_evidence_package(
        [{"url": "https://example.com/another-issuer", "title": "Other issuer", "snippet": "Other issuer has margins of 99%", "published_at": "2026-10-01", "query": "target margins"}],
        entity_id="ENT_target", as_of="2026-10-08", retrieved_at="2026-10-08T12:00:00Z",
        adapter_version="fixture/1", request_id="search-1", query_bindings={"target margins": ["IQS_01"]}, question_ids=["IQS_01"],
    )
    assert not any(e["eligible"] for e in package["entries"])
    assert package["question_context"]["IQS_01"]["sources"] == []


def test_entity_and_question_must_be_bound_by_the_same_evidence_entry():
    verdict = verify_evidence_binding(
        [{"entity_id": "ENT_target", "question_ids": ["other"], "published_at": "2026-10-01"},
         {"entity_id": "ENT_other", "question_ids": ["IQS_01"], "published_at": "2026-10-01"}],
        entity_id="ENT_target", question_ids=["IQS_01"], as_of="2026-10-08",
    )
    assert verdict.ok is False


def test_company_limit_bounds_retained_evidence_not_only_selected_snippets():
    candidates = [{"url": f"https://example.com/{i}", "entity_id": "ENT_target", "title": "T" * 500, "snippet": "S" * 500, "publisher": "P" * 100, "published_at": "2026-10-01", "query": "target margins"} for i in range(20)]
    package = build_evidence_package(candidates, entity_id="ENT_target", as_of="2026-10-08", retrieved_at="2026-10-08T12:00:00Z", adapter_version="fixture/1", request_id="search-1", query_bindings={"target margins": ["IQS_01"]}, question_ids=["IQS_01"], company_limit=1200)
    retained = sum(len(e.get("title") or "") + len(e.get("short_snippet") or "") + len(e.get("publisher") or "") for e in package["entries"])
    assert retained <= 1200
    assert package["stats"]["context_chars"] <= 1200
