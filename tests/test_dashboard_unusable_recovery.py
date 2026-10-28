"""Explicit unusable-checkpoint subset; synthetic owned native state, no HTTP."""

import copy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone

import pytest

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT.parent / "StockQAbyLLM"
WIKI = ROOT.parent / "StockWiki"
sys.path[:0] = [str(ROOT / "scripts"), str(QA), str(WIKI)]
from scripts import dashboard_prepare as p
from dashboard_service import validate_config, ProductError
from test_dashboard_prepare import original, ENTITY, tree


def test_explicit_recovery_refs_closed_and_native_projection_is_read_only(
    tmp_path, monkeypatch
):
    ref = {"work_item_id": "WORK_" + "a" * 32, "decision_id": "owd1_" + "b" * 64}
    config = {
        "prepare": {
            "recovery_work_decision_refs": [ref],
            "admission_config": str(tmp_path / "admission.json"),
        }
    }
    (tmp_path / "admission.json").write_text(
        json.dumps(
            {
                "work_store": "original.sqlite",
                "budget_policy_file": "original-policy.json",
            }
        )
    )
    manifest = {
        "questions": [
            {"id": "IQS_04", "scope": "entity"},
            {"id": "IQS_27", "scope": "security"},
        ]
    }
    native = {
        "binding": {"entity_id": "ENT_FIX"},
        "selected_listing": {"security_id": "SEC_FIX"},
    }
    row = {
        "work_item_id": ref["work_item_id"],
        "generation": 2,
        "status": "result_ready",
        "retry_decision_id": ref["decision_id"],
        "retry_purpose": "retry_unusable_checkpoint",
        "target_generation": 3,
        "delivery_required": False,
    }
    calls = []

    def invoke(*args):
        calls.append(args)
        return {
            "protocol": "stockqa.owner_control_projection/1.0.0",
            "entity_id": "ENT_FIX",
            "rows": {"IQS_04": copy.deepcopy(row)},
            "authority": "original_journal_read_not_permission",
            "API_requests": 0,
            "database_writes": 0,
        }

    monkeypatch.setattr(p, "_native_cli", invoke)
    policy = {"protocol": "stockwiki.refresh_owner_policy/1.2.0"}
    out = p._recovery_subset(config, tmp_path, manifest, native, policy)
    assert (
        out["execution_question_ids"] == ["IQS_04"]
        and out["execution_question_count"] == 1
        and out["full_bank_question_count"] == 2
    )
    assert calls[0][1:3] == ("qa", "src.utils.quick_scan_work_decision_inspect_cli")
    for field, value in [
        ("status", "failed"),
        ("retry_purpose", "comparison"),
        ("target_generation", 4),
        ("retry_decision_id", "owd1_" + "c" * 64),
        ("delivery_required", True),
    ]:
        before = row.copy()
        row[field] = value
        with pytest.raises(p.DashboardPrepareError, match="no longer matches"):
            p._recovery_subset(config, tmp_path, manifest, native, policy)
        row.clear()
        row.update(before)
    assert (
        p._recovery_subset(
            {"prepare": {}},
            tmp_path,
            manifest,
            native,
            {"protocol": "stockwiki.refresh_owner_policy/1.1.0"},
        )
        is None
    )
    with pytest.raises(p.DashboardPrepareError):
        p._recovery_subset(
            config,
            tmp_path,
            manifest,
            native,
            {"protocol": "stockwiki.refresh_owner_policy/1.1.0"},
        )
    for bad in [
        [],
        [ref, ref],
        [dict(ref, extra=True)],
        [dict(ref, work_item_id="WORK_OTHER")],
        None,
    ]:
        with pytest.raises((p.DashboardPrepareError, ProductError)):
            validate_config({"prepare": {"recovery_work_decision_refs": bad}}, tmp_path)


def _write(path, value):
    Path(path).write_text(json.dumps(value), encoding="utf-8")


def _stage(base, label, **extra):
    with (
        ROOT
        / "runs/resume-ui-live-2026-10-26/unusable-checkpoint-capability/native-stages.jsonl"
    ).open("a", encoding="utf-8") as f:
        f.write(
            json.dumps({"stage": label, "temporary_root": str(base), **extra}) + "\n"
        )


def _native(config, kind, module, args):
    try:
        result = p._native_cli(config, kind, module, args)
        if "--work-decision-request" in args:
            # Keep synthetic inputs/reply inside the owned fixture, whose cleanup
            # removes them; repeated tests must not overwrite shared run artifacts.
            out = Path(config["workspace_root"]).parent / "native-public-artifacts"
            out.mkdir(exist_ok=True)
            (out / "work-decision-input.json").write_bytes(
                Path(args[args.index("--work-decision-request") + 1]).read_bytes()
            )
            _write(out / "work-decision-reply.json", result)
        return result
    except p.DashboardPrepareError as error:
        _stage(
            Path(config["workspace_root"]).parent,
            "native_refusal",
            code=error.code,
            details=error.details,
        )
        raise


def test_native_control_artifacts_are_owned_by_each_temporary_fixture(tmp_path, monkeypatch):
    import tempfile

    monkeypatch.setattr(p, "_native_cli", lambda *args: {"status": "recorded"})
    owned_roots = []
    for index in range(2):
        with tempfile.TemporaryDirectory(dir=tmp_path) as directory:
            base = Path(directory)
            owned_roots.append(base)
            request = base / "request.json"
            _write(request, {"synthetic_input": index})
            result = _native(
                {"workspace_root": str(base / "workspace")},
                "stockwiki", "synthetic", ["--work-decision-request", str(request)],
            )
            artifacts = base / "native-public-artifacts"
            assert result == {"status": "recorded"}
            assert json.loads((artifacts / "work-decision-input.json").read_text()) == {
                "synthetic_input": index
            }
            assert json.loads((artifacts / "work-decision-reply.json").read_text()) == result
        assert not base.exists()
    assert owned_roots[0] != owned_roots[1]


def _apply_recording_refusal(gateway, preview, base, stage):
    """Keep bounded native diagnostics before the owned fixture is cleaned."""
    try:
        return gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    except p.DashboardPrepareError as error:
        _stage(base, stage, code=error.code, status=error.status, details=error.details)
        raise AssertionError(
            f"{stage}: {error.code}; {json.dumps(error.details, sort_keys=True)}"
        ) from error


def _synthetic_response(store, bundle, qid, *, compact=False):
    """Original lifecycle APIs; known HTTP is a synthetic receipt, zero sockets."""
    from src.utils import quick_scan_subject_journal as sj
    from src.utils.quick_scan_subject_owner import register
    from src.utils.quick_scan_c06_authority import load_c06_authority
    from src.utils.quick_scan_question_manifest import load_question_manifest
    from tests.unit.test_quick_scan_question_pack_store import _prepare, _receipt
    from tests.unit.test_quick_scan_observation_context import content

    authority = load_c06_authority(bundle["c06_authority"])
    context = authority["observation_context"]
    owner_config = json.loads(Path(bundle["owner_config"]).read_bytes())
    from src.utils.quick_scan_owner_refresh import OwnerRefreshSession
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    from stockwiki.quick_scan_routes import QuickScanRouteStore
    from stockwiki.quick_scan_route_validation import IqsRouteValidator

    paths = WorkspacePaths.from_root(Path(owner_config["stockwiki_workspace_root"]))
    routes = QuickScanRouteStore(
        QuickScanStore(paths),
        validator=IqsRouteValidator(
            ROOT, runs_dir=Path(owner_config["runs_dir"]), release_root=ROOT
        ),
    )
    current = routes.get_for_execution(
        subject_key=owner_config["subject_key"],
        scope=owner_config["scope"],
        scope_id=owner_config["scope_id"],
        now_utc=p._now(),
    )
    items = store.find_work_items(entity_id=bundle["entity_id"], question_ids=[qid])[
        qid
    ]
    item = max(items, key=lambda x: x["generation"])
    wid = item["work_item_id"]
    lease = store.claim(wid, lease_seconds=300)
    store.freeze_observation_context_before_send(wid, lease, context)
    policy = json.loads(
        Path(
            json.loads(Path(bundle["admission_config"]).read_bytes())[
                "budget_policy_file"
            ]
        ).read_bytes()
    )
    route = policy["routes"][0]
    import uuid

    pack = _prepare(
        store,
        [{"work_item_id": wid, "lease": lease}],
        route_id=route["id"],
        provider=route["provider_config_ref"],
        model_requested=route["model"],
        execution_attempt_id=str(uuid.uuid4()),
    )
    member = pack["members"][0]
    with store._transaction() as con:
        orig = store._item(con, wid)
        attempt = con.execute(
            "SELECT * FROM attempt WHERE attempt_id=?", (member["attempt_id"],)
        ).fetchone()
        request = sj.dispatch_request(
            orig,
            attempt,
            sj.bound_context(con, orig),
            execution_attempt_id=pack["execution_attempt_id"],
            provider_actual="mimo",
            provider_prompt_sha256=pack["provider_prompt_sha256"],
        )
    pre = register(owner_config, current, request, process_env=p._env())
    store.persist_subject_dispatch_receipt(
        wid, lease, member["attempt_id"], pre, expected_request=request
    )
    store.mark_question_pack_send_intent(
        pack["pack_id"],
        budget_policy=policy,
        budget_route={
            "route_id": route["id"],
            "provider": route["provider_config_ref"],
            "model_requested": route["model"],
            "quota_group": route["quota_group"],
        },
    )
    receipt = _receipt(
        request_id=None,
        actual_model=route["model"],
        requested_model=route["model"],
        attempt_id=pack["execution_attempt_id"],
        response_status="completed",
        completed_at=p._now(),
        source_urls=["https://example.org/source"],
    )
    store.record_question_pack_outcome(
        pack["pack_id"],
        outcome="response_available",
        execution_receipt=receipt,
        http_status_code=200,
        actual_cost=0.02,
        cost_source_ref="synthetic-zero-HTTP-bookkeeping",
    )
    body = content()
    body.update(
        question_id=qid,
        information_as_of=context["questions"][qid]["metadata"]["information_cutoff"],
    )
    body["summary"] = "Synthetic supported fixture; no financial conclusion."
    body["evidence"][0]["url"] = "https://example.org/source"
    store.save_answer_checkpoint(
        wid,
        lease,
        member["attempt_id"],
        answer={
            "entity_id": bundle["entity_id"],
            "question_id": qid,
            "status": "scored",
            "score": 8,
            "description": body["summary"],
        },
        execution_receipt=receipt,
        observation_context=context,
        standard_answer=None if compact else body,
    )
    if compact:
        store.mark_result_delivery_blocked(wid, "c06_standard_answer_unavailable")
    return wid, authority, routes, paths


def _deliver(store, wid, authority, routes, paths, base):
    from src.utils.quick_scan_delivery_seal import seal_result_delivery
    from stockwiki.quick_scan_subject_authority import IqsSubjectContract
    from stockwiki.quick_scan_subject_dispatch import SubjectBoundObservationStore
    from stockwiki.quick_scan_import import import_package

    assert seal_result_delivery(store, wid, authority=authority)["action"] == "sealed"
    delivery = store.get_result_delivery(wid)
    owner = SubjectBoundObservationStore(
        paths,
        contract=IqsSubjectContract(
            ROOT,
            release_root=ROOT,
            runs_dir=base / "contract-runs",
            process_env=p._env(),
        ),
    )
    manifest = json.loads(Path(base / "frozen-manifest.json").read_bytes())
    frozen = owner.contract.release_projection(manifest)
    imported = import_package(
        owner,
        delivery["package"],
        frozen_release=frozen,
        identity_store=routes.identity,
    )
    assert imported["summary"] == {"accepted": 1}
    store.bind_result_delivery_consumer(
        wid,
        {
            "component": "StockWiki",
            "namespace": "quick_scan",
            "store_id": owner.store_id,
        },
        source_ref="synthetic-native-owner-config",
    )
    assert (
        store.apply_result_delivery_ack(wid, imported["acks"][0])["state"]
        == "delivered"
    )
    return delivery["package_sha256"]


@pytest.mark.skipif(
    os.environ.get("IQS_RUN_NATIVE_RECOVERY") != "1",
    reason="explicit original three-owner native recovery chain",
)
# One complete owned native chain; intentionally not part of the cheap default lane.
def test_native_control_subset_admission_ack_then_normal_11_reuses_full_bank(original):
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    from stockwiki.quick_scan_work_decision_owner import WorkDecisionPreviewStore
    from stockwiki.paths import WorkspacePaths

    gateway, base, config = original
    # One original workspace proves both warm reuse and normal expiry. A
    # yesterday cutoff is fresh under the fixture's72h policy, then stale
    # under24h; no production clock, answer, history or policy is rewritten.
    as_of = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    policy_path = base / "owner/config/quick_scan_refresh.json"
    policy = json.loads(policy_path.read_bytes())
    policy["ttl_hours"] = 72  # Synthetic fixture only; never a production policy.
    _write(policy_path, policy)
    gateway = p.PrepareGateway(config)
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": as_of})
    _stage(base, "initial_preview")
    initial = _apply_recording_refusal(gateway, preview, base, "initial_apply_refusal")
    _stage(base, "initial_native_36_registered")
    bundle = next(
        x["execution_bundle"]
        for x in initial["execution_bundles"]
        if x["execution_bundle"]["scope"] == "entity"
    )
    (base / "frozen-manifest.json").write_bytes(Path(bundle["manifest"]).read_bytes())
    store = QuickScanWorkStore(base / "work.sqlite")
    keep, auth, routes, paths = _synthetic_response(store, bundle, "IQS_03")
    keep_package = _deliver(store, keep, auth, routes, paths, base)
    old, auth, routes, paths = _synthetic_response(
        store, bundle, "IQS_04", compact=True
    )
    original_checkpoint = copy.deepcopy(store.get_answer_checkpoint(old))
    original_delivery = copy.deepcopy(store.get_result_delivery(old))
    _stage(base, "known_settled_compact_and_prior_delivered")
    policy = json.loads(policy_path.read_bytes())
    policy["protocol"] = "stockwiki.refresh_owner_policy/1.2.0"
    policy["qa"]["quote_schema_version"] = "1.2.0"
    _write(policy_path, policy)
    intent = {
        "kind": "retry_decision",
        "work_item_id": old,
        "idempotency_key": "native-unusable-recovery",
        "purpose": "retry_unusable_checkpoint",
        "retry_after_seconds": 0,
        "comparison_controls": None,
    }
    _write(base / "retry-intent.json", intent)
    derived = _native(
        config,
        "qa",
        "src.utils.quick_scan_work_decision_inspect_cli",
        [
            "--ledger",
            str(store.path),
            "--policy",
            str(base / "budget.json"),
            "--intent",
            str(base / "retry-intent.json"),
        ],
    )
    permission = json.loads(
        Path(bundle["inspection_request"]).parent.joinpath("refresh.json").read_bytes()
    )
    field = derived["subject_dispatch_receipt"]["receipt"]["dispatch_request"][
        "field_id"
    ]
    original_query = copy.deepcopy(permission["source_query"])
    permission["field_ids"] = [field]
    assert (
        permission["source_query"] == original_query
        and len(original_query["payload"]["field_ids"]) == 33
        and original_query["payload"]["snapshot_id"]
    )
    outer = {
        "protocol": "stockwiki.work_decision_request/1.2.0",
        "consumer_id": "invest-quick-scan",
        "decision_request": derived["request"],
        "permission_request": permission,
    }
    _write(base / "retry-owner.json", outer)
    common = [
        "--root",
        config["workspace_root"],
        "--iqs-code-root",
        str(ROOT),
        "--iqs-release-root",
        str(ROOT),
    ]
    wp = _native(
        config,
        "wiki",
        "stockwiki.quick_scan_refresh_owner_cli",
        common + ["--work-decision-request", str(base / "retry-owner.json")],
    )
    record = WorkDecisionPreviewStore(paths).load(wp["preview_id"])
    fixed = paths.config_dir / "quick_scan_work_delegation_install.json"
    assert not fixed.exists()
    _write(
        fixed,
        {
            "protocol": "stockwiki.work_delegation_install/1.0.0",
            "workspace_root": str(paths.root),
            "preview_id": wp["preview_id"],
            "preview_record_sha256": record["record_sha256"],
            "agent": config["prepare"]["agent"],
            "authorization_reference": "synthetic-exact-checkpoint-recovery",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
        },
    )
    try:
        grant = _native(
            config,
            "wiki",
            "stockwiki.quick_scan_refresh_owner_cli",
            common + ["--install-work-delegation"],
        )
        consent = _native(
            config,
            "wiki",
            "stockwiki.quick_scan_refresh_owner_cli",
            common
            + [
                "--confirm-work-decision-delegated",
                wp["preview_id"],
                "--delegation-id",
                grant["grant_id"],
                "--idempotency-key",
                "native-unusable-recovery",
            ],
        )
    finally:
        fixed.unlink()
    decision = _native(
        config,
        "qa",
        "src.utils.quick_scan_work_decision_apply_cli",
        [
            "--ledger",
            str(store.path),
            "--policy",
            str(base / "budget.json"),
            "--owner-code-root",
            str(WIKI),
            "--owner-workspace",
            str(paths.root),
            "--iqs-code-root",
            str(ROOT),
            "--iqs-release-root",
            str(ROOT),
            "--consumer-id",
            "invest-quick-scan",
            "--confirmation-id",
            consent["confirmation_id"],
            "--refresh-schema-version",
            "1.2.0",
        ],
    )["decision"]
    config["prepare"]["recovery_work_decision_refs"] = [
        {"work_item_id": old, "decision_id": decision["decision_id"]}
    ]
    gateway = p.PrepareGateway(
        config
    )  # Explicit trusted configuration reload; the old gateway remains immutable.
    recovery = gateway.bank_preview({"entity_id": ENTITY, "as_of": as_of})
    assert (
        recovery["question_count"] == 36
        and len(recovery["questions"]) == 36
        and recovery["execution_question_ids"] == ["IQS_04"]
        and recovery["execution_question_count"] == 1
    )
    _stage(base, "controlled_preview_1_of_36")
    result = _apply_recording_refusal(gateway, recovery, base, "recovery_apply_refusal")
    assert (
        result["question_count_total"] == 1
        and len(result["execution_bundles"]) == 1
        and result["full_bank_question_count"] == 36
    )
    recovery_bundle = result["execution_bundle"]
    assert recovery_bundle["inspection_schema_version"] == "1.2.0"
    from scripts.dashboard_execution import ExecutionGateway

    eg = ExecutionGateway(
        {
            "stockqa_root": str(QA),
            "stockqa_python": sys.executable,
            "state_root": str(base / "execution"),
            "bundles": {result["bundle_id"]: recovery_bundle},
        }
    )
    ro_before = store.path.read_bytes()
    execution = eg.preview({"bundle_id": result["bundle_id"], "entity_id": ENTITY})
    assert execution["can_start"] is True, execution
    assert store.path.read_bytes() == ro_before
    _stage(
        base,
        "controlled_native_admission_and_prepare_execution",
        execution_question_ids=result["execution_question_ids"],
        full_bank_question_count=result["full_bank_question_count"],
        registration=result["admission"]["registration"],
    )
    fresh, authority, routes, paths = _synthetic_response(
        store, recovery_bundle, "IQS_04"
    )
    assert store.get_item(fresh)["generation"] == store.get_item(old)["generation"] + 1
    new_package = _deliver(store, fresh, authority, routes, paths, base)
    assert (
        store.get_item(old)["status"] == "result_ready"
        and store.get_answer_checkpoint(old) == original_checkpoint
        and store.get_result_delivery(old) == original_delivery
    )
    assert store.get_result_delivery(keep)["package_sha256"] == keep_package
    _stage(
        base,
        "controlled_original_package_import_exact_ack",
        old_work_item_id=old,
        target_work_item_id=fresh,
        old_checkpoint_sha256=original_checkpoint["payload_sha256"],
        old_outbox_state=original_delivery["state"],
        target_generation=store.get_item(fresh)["generation"],
        target_package_sha256=new_package,
        target_observation_id=store.get_result_delivery(fresh)["observation_id"],
        peer_work_item_id=keep,
        peer_package_sha256=keep_package,
        peer_observation_id=store.get_result_delivery(keep)["observation_id"],
    )
    policy["protocol"] = "stockwiki.refresh_owner_policy/1.1.0"
    policy["qa"]["quote_schema_version"] = "1.1.0"
    _write(policy_path, policy)
    config["prepare"].pop("recovery_work_decision_refs")
    gateway = p.PrepareGateway(config)
    normal = gateway.bank_preview({"entity_id": ENTITY, "as_of": as_of})
    assert (
        normal["recovery_subset"] is None and normal["execution_question_count"] == 36
    )
    ordinary = _apply_recording_refusal(gateway, normal, base, "ordinary_apply_refusal")
    entity = next(
        x
        for x in ordinary["execution_bundles"]
        if x["subject_ref"]["scope"] == "entity"
    )
    registration = entity["admission"]["registration"]
    serialized = json.dumps(registration)
    assert (
        "owner_control" not in serialized and new_package not in serialized
    )  # references use observation payload identities
    refs = {r["question_id"]: r for r in registration["observation_references"]}
    assert set(refs) == {"IQS_03", "IQS_04"}
    assert (
        refs["IQS_04"]["observation_id"]
        == store.get_result_delivery(fresh)["observation_id"]
    )
    assert (
        refs["IQS_03"]["observation_id"]
        == store.get_result_delivery(keep)["observation_id"]
    )
    assert all(
        r["question_id"] not in {"IQS_03", "IQS_04"} for r in registration["items"]
    )
    assert store.get_item(old)["status"] == "result_ready"
    assert (
        len(store.find_work_items(entity_id=ENTITY, question_ids=["IQS_04"])["IQS_04"])
        == 2
    )
    _stage(
        base,
        "ordinary_11_full_bank_reuses_delivered_recovery",
        registration=registration,
    )
    # A normal owner policy can later require a refresh. The source remains
    # immutable; exact acknowledged successor lineage must not deadlock it.
    policy["ttl_hours"] = 24
    _write(policy_path, policy)
    gateway = p.PrepareGateway(config)
    expired = gateway.bank_preview({"entity_id": ENTITY, "as_of": as_of})
    refreshed = _apply_recording_refusal(gateway, expired, base, "expired_ordinary_apply_refusal")
    entity_refresh = next(
        row for row in refreshed["execution_bundles"] if row["subject_ref"]["scope"] == "entity"
    )
    refreshed_registration = entity_refresh["admission"]["registration"]
    items = {row["question_id"]: row for row in refreshed_registration["items"]}
    assert items["IQS_04"]["generation"] == 3
    assert items["IQS_03"]["generation"] == 2
    assert not {"IQS_03", "IQS_04"} & {
        row["question_id"] for row in refreshed_registration["observation_references"]
    }
    from src.utils.quick_scan_owner_refresh_journal import guard_send

    with closing(store._connect()) as connection:
        guard_send(connection, store.get_item(items["IQS_04"]["work_item_id"]))
    assert store.get_answer_checkpoint(old) == original_checkpoint
    assert store.get_result_delivery(old) == original_delivery
    assert store.get_result_delivery(fresh)["package_sha256"] == new_package
    assert store.get_result_delivery(fresh)["state"] == "delivered"
    _stage(base, "ordinary_11_expired_successor_refreshes_normally", registration=refreshed_registration)
