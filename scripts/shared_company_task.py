"""Task 3.0 carrier derived from an ORIGINAL admitted native owner.

No synthetic frozen-target loader, consent creation, model call or identity
name join occurs here. Hash references identify exact native input bytes;
they are not authority. Native owner guards remain mandatory on every send.
"""
from __future__ import annotations

import copy
import hashlib
import json


class NativeTaskRejected(ValueError):
    pass


def create_native_task(lifecycle, *, experiment_id, run_id, strategy_id="free_agent",
                       question_ids=None, evidence_board=None, limits=None):
    from iqs_company_agent_lab.canonical import canonical_json, sha256_hex
    from iqs_company_agent_lab.frozenregistration import LIMIT_CAPS, QUESTION_IDS, limits_within_registration
    from iqs_company_agent_lab.task import LoadedTask
    from src.runners.llm_runner import QuickScanWorkLifecycle
    from src.utils.quick_scan_owner_refresh import OwnerRefreshSession
    from src.utils.quick_scan_refresh_execution import ApprovedRefreshSession
    from src.utils.quick_scan_result_outbox import canonical_sha256

    if not isinstance(lifecycle, QuickScanWorkLifecycle):
        raise NativeTaskRejected("original_native_lifecycle_required")
    owner = lifecycle._owner_refresh
    if (not isinstance(owner, ApprovedRefreshSession) or not isinstance(owner.native, OwnerRefreshSession)
            or owner.service.store is not lifecycle._store or owner.native.store is not lifecycle._store
            or not lifecycle._transport_managed):
        raise NativeTaskRejected("original_admitted_native_owner_required")
    owner.check()
    if owner.plan.get("information_cutoff") != "2026-10-13":
        raise NativeTaskRejected("registered_information_cutoff_required")
    if strategy_id != "free_agent":
        # Native contracts need not share the legacy factual-domain ordering.
        # The first native carrier supports the full-pack strategy with search
        # disabled, without falsely assigning native questions to old domains.
        raise NativeTaskRejected("native_full_pack_strategy_required")
    for value in (experiment_id, run_id):
        if not isinstance(value, str) or not value or len(value) > 80 or any(ord(c) < 32 for c in value):
            raise NativeTaskRejected("bounded_experiment_and_run_ids_required")
    selected = list(owner.requested_question_ids if question_ids is None else question_ids)
    if len(selected) != 12 or len(set(selected)) != 12 or not set(selected) <= set(owner.entries):
        raise NativeTaskRejected("exactly_twelve_original_authorized_questions_required")
    context = lifecycle._observation_context
    if (not isinstance(context, dict) or context.get("schema") != "stockqa.quick_scan_observation_context/2.0.0"
            or canonical_sha256(context) != canonical_sha256(owner.native.observation_context)):
        raise NativeTaskRejected("original_native_subject_context_required")
    manifest = owner.bundle["manifest"]
    manifest_rows = {row["id"]: row for row in manifest["questions"]}
    locks = {row["module_id"]: row for row in manifest["module_locks"]}
    questions, subject = [], None
    for qid in selected:
        row = manifest_rows.get(qid)
        binding = (context.get("questions", {}).get(qid) or {}).get("subject_binding") or {}
        body, ref = binding.get("question_contract"), binding.get("subject_ref")
        if (not isinstance(row, dict) or not isinstance(body, dict) or body.get("id") != qid
                or body != row or not isinstance(ref, dict) or owner.entries[qid]["kind"] != "work"
                or row.get("module_id") not in locks):
            raise NativeTaskRejected("full_original_manifest_question_required")
        if subject is not None and ref != subject:
            raise NativeTaskRejected("one_exact_native_subject_required")
        subject = copy.deepcopy(ref)
        version = locks[row["module_id"]].get("version")
        if not isinstance(version, str) or not version:
            raise NativeTaskRejected("original_module_version_required")
        questions.append(dict(question_id=qid, question=copy.deepcopy(body),
            question_object_sha256=sha256_hex(body), module_id=row["module_id"], module_version=version))
    required_inputs = {"manifest.json", "identity.json", "authority.json", "owner-config.json", "questions.json"}
    if set(owner.input_raw) != required_inputs or any(not isinstance(raw, bytes) for raw in owner.input_raw.values()):
        raise NativeTaskRejected("complete_original_native_inputs_required")

    def file_ref(path, raw):
        return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    native_inputs = {name: file_ref("native-input/" + name, raw) for name, raw in owner.input_raw.items()}
    board = copy.deepcopy(evidence_board if evidence_board is not None else {"records": []})
    if not isinstance(board, dict) or not isinstance(board.get("records"), list):
        raise NativeTaskRejected("explicit_evidence_board_required")
    identity = json.loads(owner.input_raw["identity.json"])
    identity_payload = identity.get("payload", {})
    if identity_payload.get("entity_id") != subject["entity_id"]:
        raise NativeTaskRejected("original_identity_subject_required")
    listings = identity_payload.get("listings")
    if (not isinstance(listings, list) or not listings
            or any(not isinstance(row, dict) or not isinstance(row.get("market"), str)
                   or not isinstance(row.get("ticker"), str) or not row["ticker"] for row in listings)):
        raise NativeTaskRejected("original_identity_listings_required")
    company = dict(protocol="iqs.company-agent-lab.company-identity/2.0.0", origin="owner_public",
        company_key=subject["entity_id"], label=identity_payload.get("canonical_name") or subject["entity_id"],
        subject={"issuer_id": subject["primary_issuer_id"], "subject_ref": subject,
                 "share_classes": [{"market": row["market"], "ticker": row["ticker"]} for row in listings]})
    profile = dict(protocol="iqs.native-company-runtime-profile/1.0.0", synthetic=False,
        question_projection=dict(zip(QUESTION_IDS, selected)), provider=owner.plan["provider"],
        model=owner.plan["model"], native_inputs_sha256=sha256_hex(native_inputs))
    selected_limits = copy.deepcopy(LIMIT_CAPS)
    selected_limits["max_search_queries_per_session"] = 0
    if limits is not None:
        if not isinstance(limits, dict):
            raise NativeTaskRejected("bounded_registered_limits_required")
        selected_limits.update(copy.deepcopy(limits))
    if (limits_within_registration(selected_limits)
            or any(type(value) is not int or value < 0 for value in selected_limits.values())
            or selected_limits["max_search_queries_per_session"] != 0):
        raise NativeTaskRejected("bounded_registered_limits_required")
    binding = dict(protocol="iqs.native-company-owner-binding/1.0.0", synthetic=False,
        subject_ref=copy.deepcopy(subject), authority_ref=copy.deepcopy(native_inputs["authority.json"]),
        native_scope={"scope": subject["scope"], "scope_id": subject["scope_id"]},
        original_inputs_sha256=sha256_hex(native_inputs))
    raw = dict(protocol="iqs.company-agent-task/3.0.0", experiment_id=experiment_id, run_id=run_id,
        company_ref=file_ref("native-derived/company.json", canonical_json(company).encode("utf8")),
        information_cutoff=owner.plan["information_cutoff"],
        question_refs=[dict(copy.deepcopy(native_inputs["manifest.json"]), question_id=q["question_id"],
                            question_object_sha256=q["question_object_sha256"]) for q in questions],
        evidence_epoch_ref=file_ref("native-derived/evidence-board.json", canonical_json(board).encode("utf8")),
        strategy_id=strategy_id, limits=selected_limits,
        runtime_profile_ref=file_ref("native-derived/runtime-profile.json", canonical_json(profile).encode("utf8")),
        owner_binding=binding, native_inputs=native_inputs,
        module_locks=copy.deepcopy(manifest["module_locks"]))
    task = LoadedTask(raw, None, questions, company, board, profile,
        {"protocol": "iqs.native-company-targets/1.0.0", "native_manifest_ref": native_inputs["manifest.json"]})
    task.owner_binding = copy.deepcopy(binding)
    owner.check()
    return task
