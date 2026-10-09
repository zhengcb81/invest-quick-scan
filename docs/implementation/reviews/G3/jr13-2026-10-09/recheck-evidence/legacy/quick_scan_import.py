"""W05 C06 exchange-package import entry: verification, decisions, orchestration.

Implements the consumer side of
``docs/implementation/contracts/exchange-and-query.md`` §2 without reaching
into either owner repository: canonical hashing, content-addressed package /
item / payload verification, portable observation validation, and the
published-observation re-derivation against a FROZEN S05 release projection
(``frozen_release`` — prepared by the question-bank owner; this module
re-derives definition/semantic/method/scope bindings from it instead of
trusting self-reported fingerprints).

Deliberate invariants:

* JSON Schema-shaped checks are never treated as content-hash proof: every
  ``payload_sha256`` / ``item_id`` / ``package_id`` is recomputed here and
  mismatch rejects before any store write.
* NaN/Infinity are rejected at parse time; canonical form is UTF-8 JSON,
  sorted keys, no extra spaces, Unicode preserved.
* One model reply can never grant itself qualification: ``accepted_ids``,
  truthy ``search_verified``, elevated ``check_level``,
  ``formal_evidence_accepted``, ``source_manifest`` / ``evidence_span`` all
  reject the item (SC-05/DB-06); accepted observations are stored with
  ``qualification_status='review_pending'`` only (SC-06) — that write happens
  in the store module, not here.
* Unknown questions, partial module bindings, forged published fingerprints,
  scope/security mismatches and timestamp violations reject per-item; a
  rejected item never partially enters the store.
* Logical execution key = producer + provider + request_id + attempt_id +
  question_id + entity/security scope — the store isolates a different
  ``observation_id`` reusing a stored key as
  ``execution_key_id_mismatch`` conflict (DB-03).
* ``analysis_subject`` (when carried) must match the observation's exact
  entity/security/listing scope; when absent the store keeps NULL — legacy
  records are never silently assigned a subject (ID-23).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any

from stockwiki.quick_scan_observations import (
    ObservationImportError,
    QuickScanObservationStore,
)
from stockwiki.quick_scan_store import QuickScanStore

_PACKAGE_KEYS = frozenset(
    {
        "schema_version",
        "producer",
        "consumer",
        "created_at",
        "data_class",
        "required_capabilities",
        "contract_versions",
        "document_payloads_included",
        "items",
        "extensions",
        "package_sha256",
        "package_id",
    }
)
_ITEM_KEYS = frozenset({"item_id", "observation_id", "payload_sha256", "observation"})
_OBSERVATION_KEYS = frozenset("""
    schema_version entity_id security_id segment_id field_id construct_id
    question_id question_version template_version method_id scope cohort
    information_cutoff run_id scan_id inputset_id task_mode comparison_group_id
    observed_at execution answer evidence_review_status observation_id
    listing_id source_binding_ref identity_revision analysis_subject
    analysis_subject_id analysis_subject_revision primary_issuer_id
    module_package_id module_release_id question_definition_sha256
    question_semantic_sha256 cycle_sensitive
    """.split())
_EXECUTION_REQUIRED = (
    "provider",
    "model_resolved",
    "request_id",
    "attempt_id",
    "started_at",
    "answered_at",
    "search_status",
)
_MODULE_BINDING_KEYS = (
    "module_release_id",
    "question_definition_sha256",
    "question_semantic_sha256",
)
_FORBIDDEN_EVIDENCE_KEYS = frozenset(
    {
        "source_manifest",
        "source_manifest_id",
        "source_manifest_ids",
        "evidence_span",
        "evidence_span_id",
        "evidence_span_ids",
        "accepted_ids",
        "raw_document",
        "document_body",
        "document_text",
        "formal_evidence_accepted",
    }
)
_FORBIDDEN_TOP_KEYS = tuple(_FORBIDDEN_EVIDENCE_KEYS)
_FORBIDDEN_CHECK_LEVELS = frozenset(
    {"accepted", "formal_accepted", "independently_checked", "formal_research_accepted"}
)
_METHOD_LOCKED_PREFIX = "module-locked-v1/"
_HEX16 = re.compile(r"[a-f0-9]{16}")


class ImportValidationError(ObservationImportError):
    """A per-item or per-package refusal from the import entry."""


def _reject(code: str, detail: str = "") -> ImportValidationError:
    return ImportValidationError(code, detail)


def _contains_forbidden_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in _FORBIDDEN_EVIDENCE_KEYS:
                return str(key)
            nested = _contains_forbidden_key(child)
            if nested is not None:
                return nested
        return None
    if isinstance(value, list):
        for child in value:
            nested = _contains_forbidden_key(child)
            if nested is not None:
                return nested
        return None
    return None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _reject_constant(token: str) -> Any:
    raise _reject("json_constant_forbidden", token)


def parse_package(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if not isinstance(raw, str):
        raise _reject("package_shape", "package must be JSON text, bytes or object")
    try:
        parsed = json.loads(raw, parse_constant=_reject_constant)
    except ImportValidationError:
        raise
    except ValueError as exc:
        raise _reject("package_json_invalid", str(exc)) from exc
    if not isinstance(parsed, dict):
        raise _reject("package_shape", "package root must be an object")
    return parsed


def verify_package_integrity(package: dict[str, Any]) -> dict[str, Any]:
    """Recompute every content address; any mismatch rejects the package."""
    unknown = sorted(set(package) - _PACKAGE_KEYS)
    if unknown:
        raise _reject("package_unknown_field", ",".join(unknown))
    for key in (
        "schema_version",
        "created_at",
        "data_class",
        "package_sha256",
        "package_id",
        "producer",
        "consumer",
        "contract_versions",
    ):
        if key not in package:
            raise _reject("package_missing_field", key)
    if package["schema_version"] != "1.0.0":
        raise _reject("unsupported_schema", str(package["schema_version"]))
    if package["data_class"] != "lightweight_screening":
        raise _reject("data_class_not_lightweight", str(package["data_class"]))
    if package.get("document_payloads_included") is not False:
        raise _reject("document_payloads_forbidden", str(package.get("document_payloads_included")))
    if package.get("extensions") != []:
        raise _reject("extensions_must_be_empty", json.dumps(package.get("extensions")))
    if not isinstance(package["producer"], dict) or not package["producer"].get("component"):
        raise _reject("producer_invalid", "")
    consumer = package["consumer"]
    if not isinstance(consumer, dict) or consumer.get("namespace") != "quick_scan":
        raise _reject("consumer_invalid", str(consumer))
    items = package.get("items")
    if not isinstance(items, list) or not items or len(items) > 100:
        raise _reject(
            "items_count_out_of_range", str(len(items) if isinstance(items, list) else None)
        )
    for key in (
        "identity_schema",
        "answer_schema",
        "observation_schema",
        "question_catalog",
        "model_policy_schema",
    ):
        if key not in package["contract_versions"]:
            raise _reject("contract_versions_missing", key)
    for item in items:
        if not isinstance(item, dict):
            raise _reject("item_shape", type(item).__name__)
    seed = {
        key: value for key, value in package.items() if key not in {"package_id", "package_sha256"}
    }
    expected_package_hash = canonical_sha256(seed)
    if package["package_sha256"] != expected_package_hash:
        raise _reject("package_hash_mismatch", package["package_id"])
    if package["package_id"] != "pkg_" + expected_package_hash:
        raise _reject("package_id_mismatch", package["package_id"])
    return package


def _verify_item_integrity(item: Any) -> None:
    if not isinstance(item, dict) or set(item) != _ITEM_KEYS:
        raise _reject(
            "item_shape", str(sorted(item) if isinstance(item, dict) else type(item).__name__)
        )
    observation = item["observation"]
    if not isinstance(observation, dict):
        raise _reject("observation_shape", item.get("item_id", ""))
    payload_hash = canonical_sha256(observation)
    if item["payload_sha256"] != payload_hash:
        raise _reject("payload_hash_mismatch", str(item.get("observation_id")))
    seed = {"observation_id": item["observation_id"], "payload_sha256": payload_hash}
    expected_item_id = "itm_" + canonical_sha256(seed)
    if item["item_id"] != expected_item_id:
        raise _reject("item_id_mismatch", str(item.get("item_id")))
    if observation.get("observation_id") != item["observation_id"]:
        raise _reject("observation_id_mismatch", str(item.get("observation_id")))


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise _reject("timestamp_not_utc", label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _reject("timestamp_invalid", label) from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise _reject("timestamp_not_utc", label)
    return parsed


def _validate_subject(observation: dict[str, Any]) -> dict[str, Any] | None:
    subject = observation.get("analysis_subject")
    if subject is None:
        return None
    if not isinstance(subject, dict):
        raise _reject("analysis_subject_shape", observation["observation_id"])
    subject_id = subject.get("analysis_subject_id")
    revision = subject.get("analysis_subject_revision")
    if not isinstance(subject_id, str) or not subject_id:
        raise _reject("analysis_subject_missing_id", observation["observation_id"])
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise _reject("analysis_subject_revision_invalid", str(revision))
    if subject.get("entity_id") != observation["entity_id"]:
        raise _reject("analysis_subject_scope_mismatch", "entity_id")
    if observation.get("security_id") and subject.get("security_id") != observation.get(
        "security_id"
    ):
        raise _reject("analysis_subject_scope_mismatch", "security_id")
    if observation.get("listing_id") and subject.get("listing_id") != observation.get("listing_id"):
        raise _reject("analysis_subject_scope_mismatch", "listing_id")
    if subject.get("security_id") and subject.get("security_id") != observation.get("security_id"):
        raise _reject("analysis_subject_scope_mismatch", "subject_security_unbound")
    if subject.get("listing_id") and subject.get("listing_id") != observation.get("listing_id"):
        raise _reject("analysis_subject_scope_mismatch", "subject_listing_unbound")
    return subject


def _validate_module_binding(observation: dict[str, Any], frozen_release: dict[str, Any]) -> None:
    partial = [key for key in _MODULE_BINDING_KEYS if key in observation]
    published = "module_package_id" in observation
    if partial and not published:
        raise _reject("partial_module_binding", ",".join(partial))
    if not published:
        if observation.get("schema_version") == "1.1.0" or str(
            observation.get("method_id", "")
        ).startswith(_METHOD_LOCKED_PREFIX):
            raise _reject("published_binding_missing", str(observation.get("method_id")))
        return
    missing = [
        key
        for key in (
            "module_package_id",
            "module_release_id",
            "question_definition_sha256",
            "question_semantic_sha256",
        )
        if key not in observation
    ]
    if missing:
        raise _reject("published_binding_incomplete", ",".join(missing))
    if observation["module_package_id"] != frozen_release["module_package_id"]:
        raise _reject("module_package_mismatch", observation["module_package_id"])
    if observation["module_release_id"] != frozen_release["release_id"]:
        raise _reject("module_release_mismatch", observation["module_release_id"])
    if observation.get("template_version") != frozen_release["catalog_version"]:
        raise _reject("catalog_version_mismatch", str(observation.get("template_version")))
    question = frozen_release["questions"].get(observation["question_id"])
    if question is None or question.get("response_kind") != "score":
        raise _reject("question_missing_from_release", observation["question_id"])
    if observation["question_definition_sha256"] != question["definition_sha256"]:
        raise _reject("question_definition_mismatch", observation["question_id"])
    if observation["question_semantic_sha256"] != question["semantic_sha256"]:
        raise _reject("question_semantic_mismatch", observation["question_id"])
    if observation.get("question_version") != question["rubric_version"]:
        raise _reject("rubric_version_mismatch", str(observation.get("question_version")))
    if observation.get("construct_id") != question.get("construct_id"):
        raise _reject("construct_mismatch", str(observation.get("construct_id")))
    if observation["answer"].get("response_kind") != "score":
        raise _reject("published_requires_score_response", "")
    semantic = question["semantic_sha256"]
    method = str(observation.get("method_id", ""))
    if frozen_release.get("semantic_fingerprint_version") == "2.0.0":
        if observation.get("schema_version") != "1.1.0":
            raise _reject("published_requires_schema_1_1", str(observation.get("schema_version")))
        if not isinstance(observation.get("cycle_sensitive"), bool):
            raise _reject("cycle_context_missing", observation["observation_id"])
        pattern = (
            _METHOD_LOCKED_PREFIX + r"core-constructs-v1/" + _HEX16.pattern + "/" + semantic[:16]
        )
        if not re.fullmatch(pattern, method):
            raise _reject("method_semantic_binding_mismatch", method)
    else:
        if not method.endswith("/" + semantic[:16]):
            raise _reject("method_semantic_binding_mismatch", method)


def validate_item(
    package: dict[str, Any],
    item: dict[str, Any],
    *,
    frozen_release: dict[str, Any],
    identity_store: QuickScanStore,
) -> dict[str, Any]:
    """Validate one item; returns an import decision (accepted or rejected)."""
    _verify_item_integrity(item)
    observation = item["observation"]
    answer = observation.get("answer")
    if not isinstance(answer, dict):
        raise _reject("answer_shape", str(observation.get("observation_id")))
    if answer.get("accepted_ids"):
        raise _reject("self_granted_qualification", "accepted_ids")
    if answer.get("search_verified"):
        raise _reject("self_granted_qualification", "search_verified")
    if answer.get("check_level") in _FORBIDDEN_CHECK_LEVELS:
        raise _reject("self_granted_qualification", str(answer.get("check_level")))
    for key in _FORBIDDEN_TOP_KEYS:
        if key in observation:
            raise _reject("forbidden_field", key)
    nested_forbidden = _contains_forbidden_key(observation)
    if nested_forbidden is not None:
        raise _reject("forbidden_field", nested_forbidden)
    unknown = sorted(set(observation) - _OBSERVATION_KEYS)
    if unknown:
        raise _reject("observation_unknown_field", ",".join(unknown))
    for key in (
        "schema_version",
        "entity_id",
        "field_id",
        "question_id",
        "question_version",
        "template_version",
        "method_id",
        "scope",
        "cohort",
        "information_cutoff",
        "run_id",
        "observed_at",
        "execution",
        "answer",
        "observation_id",
    ):
        if key not in observation:
            raise _reject("observation_missing_field", key)
    if observation["schema_version"] not in {"1.0.0", "1.1.0"}:
        raise _reject("unsupported_schema", str(observation["schema_version"]))
    if answer.get("question_id") != observation.get("question_id"):
        raise _reject("answer_question_mismatch", str(observation.get("question_id")))

    question = frozen_release["questions"].get(observation["question_id"])
    if question is None:
        raise _reject("unknown_question", observation["question_id"])
    if observation["field_id"] != question["field_id"]:
        raise _reject("field_identity_mismatch", observation["field_id"])
    _validate_module_binding(observation, frozen_release)
    expected_scope = (
        "segment"
        if observation.get("segment_id") and question["scope"] == "entity"
        else question["scope"]
    )
    if observation["scope"] != expected_scope:
        raise _reject("scope_mismatch", observation["scope"])
    if observation["scope"] == "security" and not observation.get("security_id"):
        raise _reject("scope_requires_security", "security")
    if observation["scope"] == "segment" and not observation.get("segment_id"):
        raise _reject("scope_requires_segment", "segment")

    entity = identity_store.get_entity(observation["entity_id"])
    if entity is None:
        raise _reject("entity_not_found", observation["entity_id"])
    if observation.get("security_id"):
        known = {
            row["security_id"]
            for row in identity_store.securities_for_entity(observation["entity_id"])
        }
        if observation["security_id"] not in known:
            raise _reject("security_scope_invalid", observation["security_id"])
    identity_revision = observation.get("identity_revision")
    if identity_revision is not None and (
        isinstance(identity_revision, bool)
        or not isinstance(identity_revision, int)
        or identity_revision < 1
    ):
        raise _reject("identity_revision_invalid", str(identity_revision))
    _validate_subject(observation)

    execution = observation["execution"]
    if not isinstance(execution, dict):
        raise _reject("execution_shape", observation["observation_id"])
    for key in _EXECUTION_REQUIRED:
        value = execution.get(key)
        if not isinstance(value, str) or not value.strip():
            raise _reject("execution_field_missing", key)
    started = _parse_utc(execution["started_at"], "started_at")
    answered = _parse_utc(execution["answered_at"], "answered_at")
    observed = _parse_utc(observation["observed_at"], "observed_at")
    if answered < started:
        raise _reject("execution_timestamp_order", "answered_at < started_at")
    if observed != answered:
        raise _reject("observed_at_mismatch", observation["observed_at"])
    cutoff = observation["information_cutoff"]
    if not isinstance(cutoff, str):
        raise _reject("information_cutoff_invalid", str(cutoff))
    try:
        cutoff_date = date.fromisoformat(cutoff)
    except ValueError as exc:
        raise _reject("information_cutoff_invalid", cutoff) from exc
    if cutoff_date > answered.date():
        raise _reject("information_cutoff_after_answer", cutoff)

    response_kind = answer.get("response_kind")
    if response_kind not in {"score", "fact"}:
        raise _reject("response_kind_invalid", str(response_kind))
    score = answer.get("score")
    if response_kind == "fact" and score is not None:
        raise _reject("fact_score_not_null", str(score))
    if response_kind == "score":
        if answer.get("status") == "scored":
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
                raise _reject("score_invalid", str(score))
        elif score is not None:
            raise _reject("score_invalid", str(score))

    subject = observation.get("analysis_subject")
    exec_key = canonical_sha256(
        {
            "producer": package["producer"]["component"],
            "provider": execution["provider"],
            "request_id": execution["request_id"],
            "attempt_id": execution["attempt_id"],
            "question_id": observation["question_id"],
            "entity_id": observation["entity_id"],
            "security_id": observation.get("security_id"),
            "analysis_subject_id": (subject or {}).get("analysis_subject_id"),
            "analysis_subject_revision": (subject or {}).get("analysis_subject_revision"),
        }
    )
    return {
        "package_id": package["package_id"],
        "item_id": item["item_id"],
        "observation_id": item["observation_id"],
        "payload_sha256": item["payload_sha256"],
        "exec_key": exec_key,
        "status": "accepted",
        "error_code": None,
        "observation": observation,
    }


def _rejected_decision(
    package: dict[str, Any],
    item: Any,
    error_code: str,
    detail: str = "",
    *,
    fallback_index: int = 0,
) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    observation = item.get("observation") if isinstance(item.get("observation"), dict) else {}
    return {
        "package_id": package.get("package_id", "pkg_unknown"),
        "item_id": str(item.get("item_id") or f"itm_invalid_{fallback_index}"),
        "observation_id": str(
            item.get("observation_id") or observation.get("observation_id") or "obs_unknown"
        ),
        "payload_sha256": str(item.get("payload_sha256") or ""),
        "exec_key": None,
        "status": "rejected",
        "error_code": error_code,
        "_detail": detail,
        "observation": observation,
    }


def import_package(
    observation_store: QuickScanObservationStore,
    package_raw: Any,
    *,
    frozen_release: dict[str, Any],
    identity_store: QuickScanStore,
) -> dict[str, Any]:
    """Verify, decide and persist one exchange package; returns its ACKs.

    Package-level integrity failure rejects the WHOLE package with an
    ``ObservationImportError`` (no partial accept, no ledger writes).
    Item-level validation failures become per-item ``rejected`` ACKs.
    """
    if not isinstance(frozen_release, dict):
        raise _reject("frozen_release_invalid", "manifest must be an object")
    for key in (
        "module_package_id",
        "release_id",
        "catalog_version",
        "semantic_fingerprint_version",
        "questions",
    ):
        if key not in frozen_release:
            raise _reject("frozen_release_missing", key)
    if not isinstance(frozen_release["questions"], dict):
        raise _reject("frozen_release_invalid", "questions must be an object")
    package = parse_package(package_raw)
    try:
        verify_package_integrity(package)
    except ImportValidationError as exc:
        raise ObservationImportError(exc.error_code, exc.detail) from exc

    decisions: list[dict[str, Any]] = []
    for index, item in enumerate(package["items"]):
        try:
            decisions.append(
                validate_item(
                    package,
                    item,
                    frozen_release=frozen_release,
                    identity_store=identity_store,
                )
            )
        except ImportValidationError as exc:
            decisions.append(
                _rejected_decision(
                    package,
                    item,
                    exc.error_code,
                    exc.detail,
                    fallback_index=index,
                )
            )

    acks = observation_store.apply_decisions(decisions, identity_lookup=identity_store)
    summary: dict[str, int] = {}
    for ack in acks:
        summary[ack["status"]] = summary.get(ack["status"], 0) + 1
    return {
        "package_id": package["package_id"],
        "store_id": observation_store.store_id,
        "acks": acks,
        "summary": summary,
    }
