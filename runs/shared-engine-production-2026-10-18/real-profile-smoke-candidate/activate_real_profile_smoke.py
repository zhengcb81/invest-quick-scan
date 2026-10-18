"""One-shot ORIGINAL public CATL onboarding and native1.5 admission.

Not invoked until the complete source/controller node is independently reviewed
and delivered. A partial activation must be inspected, never auto-restarted.
No generation, fee settlement, alternate identity store or grant implementation.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[1]
QA, SW = ROOT.parent / "StockQAbyLLM", ROOT.parent / "StockWiki"
COMPANY = ROOT.parent / "iqs-company-agent-lab"
OWNER = ROOT / "runs/c16b/native-owner-alphabet-01/owner-workspace"
LEDGER = ROOT / "runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"
RELEASE = ROOT / "runs/c16b/iqs-release"
OUT = BASE / "actual-native-catl-profile-01"
PREP = BASE / "next-real-identity-preparation"
IDS = ["IQS_12", "IQS_16"]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import controller_delivery as delivery
ENTITY = "ENT_99ebb735-f072-41e4-8545-823bc012614f"
SAFE_ENV = {k: v for k, v in os.environ.items() if k.upper() in {
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA",
    "LOCALAPPDATA", "SYSTEMDRIVE", "TEMP", "TMP"}}
SAFE_ENV.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                PYTHONPATH=os.pathsep.join((str(SW), str(QA), str(COMPANY / "src"))))


def read(path):
    from src.utils.quick_scan_result_outbox import strict_json_loads
    return strict_json_loads(Path(path).read_text(encoding="utf8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf8"))
        stream.flush(); os.fsync(stream.fileno())


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def call(label, args, *, cwd=SW):
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", *map(str, args)],
        cwd=cwd, env=SAFE_ENV, capture_output=True, timeout=180, check=False)
    (OUT / (label + ".stdout.json")).write_bytes(result.stdout)
    (OUT / (label + ".stderr.log")).write_bytes(result.stderr)
    write(OUT / (label + ".process.json"), dict(returncode=result.returncode,
        stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(result.stderr).hexdigest(), observed_at=utc()))
    if result.returncode:
        raise ValueError("original_public_command_refused_" + label)
    return read(OUT / (label + ".stdout.json"))


def original_budget_rows():
    with closing(sqlite3.connect(LEDGER.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        return {row["budget_attempt_id"]: dict(row) for row in db.execute("SELECT * FROM quick_scan_budget_attempt")}


def main():
    sys.path[:0] = [str(QA), str(SW), str(COMPANY / "src"), str(ROOT / "scripts")]
    # An engineering review is required here but is NOT owner permission.
    # Actual permission still comes from original namespace/quote/rc2/admission.
    delivered = delivery.verify_deployment()
    delivery.verify_question_definitions()
    if OUT.exists():
        raise ValueError("inspect_partial_actual_activation_do_not_restart")
    def offline(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            raise RuntimeError("activation_has_no_network")
    sys.addaudithook(offline)
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    from stockwiki.quick_scan_routes import QuickScanRouteStore
    from stockwiki.quick_scan_route_validation import IqsRouteValidator
    from stockwiki.quick_scan_refresh_principal import current_principal
    from stockwiki.quick_scan_refresh_records import RefreshRecordStore
    from stockwiki.identity_snapshot import resolve_listing_binding, listing_id_for_security
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    from src.utils.quick_scan_owner_refresh import OwnerRefreshClient
    from src.utils.quick_scan_owner_budget_continuation import exposure_snapshot, future_request_core, digest, NO_EXTERNAL_SEARCH_POLICY
    from src.runners.llm_runner import load_identity_snapshot
    from src.utils.quick_scan_refresh_admission import RefreshAdmissionService
    from src.utils.quick_scan_question_manifest import load_question_manifest
    from iqs_company_agent_lab.scan_profile import build_scan_profile, scan_limits
    import refresh_contract

    policy_path = OWNER / "config/quick_scan_refresh.json"
    old_policy_raw, old_policy = policy_path.read_bytes(), read(policy_path)
    if current_principal() != old_policy["owner_principal"]:
        raise ValueError("original_native_os_owner_changed")
    identity_prep = read(PREP / "preparation.json")
    if (identity_prep["status"] != "draft_not_applied_not_a_stockwiki_golden"
            or sha(OWNER / "data/quick_scan/scan.sqlite") != identity_prep["original_db_sha256_before"]):
        raise ValueError("original_identity_source_changed")
    budget_path = Path(old_policy["qa"]["budget_policy_file"])
    if sha(budget_path) != "2a0060e15576a82212c6e1dd86ffc427e2669ff31187f64017ea913637f5dedb":
        raise ValueError("original_budget_configuration_changed")
    budget = read(budget_path)
    route = next(row for row in budget["routes"] if row["id"] == "mimo-pro-t2")
    before_budget = original_budget_rows()
    if len(before_budget) != 101 or sum(row["status"] != "settled" for row in before_budget.values()) != 3:
        raise ValueError("inspect_changed_original_101_attempt_state")
    import psutil
    workers, unreadable = [], 0
    historical = [str((ROOT / path).resolve()).casefold() for path in (
        "runs/company-agent-owner-2026-10-15-01", "runs/real-contrast-2026-10-16-03")]
    for process in psutil.process_iter(["pid", "name"]):
        if process.pid == os.getpid() or "python" not in (process.info["name"] or "").casefold():
            continue
        try:
            working = Path(process.cwd()).resolve()
            paths = [working]
            for argument in process.cmdline():
                candidate = Path(argument)
                paths.append((candidate if candidate.is_absolute() else working / candidate).resolve())
            if any(str(path).casefold() == origin or str(path).casefold().startswith(origin + os.sep)
                   for path in paths for origin in historical):
                workers.append(process.pid)
        except (OSError, ValueError, psutil.AccessDenied, psutil.NoSuchProcess):
            unreadable += 1
    if workers or unreadable:
        raise ValueError("original_local_worker_state_not_quiescent")
    sources = {"original-ledger": LEDGER, **{name: OWNER / "data/quick_scan" / (name + ".sqlite")
        for name in ("scan", "identity_receipts", "analysis_subjects", "market_registry")}}
    if any(Path(str(path) + suffix).exists() for path in sources.values() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("original_databases_busy")
    OUT.mkdir(); (OUT / "backup").mkdir()
    (OUT / "backup/owner-policy.raw.json").write_bytes(old_policy_raw)
    for name, source in sources.items():
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(OUT / "backup" / (name + ".sqlite"))) as dst:
                src.backup(dst)
    write(OUT / "before.json", dict(observed_at=utc(), ledger_sha256=sha(LEDGER),
        databases={key: sha(path) for key, path in sources.items()}, original_requests=101,
        original_unresolved=3, owner_policy_sha256=hashlib.sha256(old_policy_raw).hexdigest()))
    write(OUT / "worker-observation.json", dict(observed_at=utc(), matched_local_original_workers=workers,
        unreadable_python_processes=unreadable, remote_provider_outcomes_still_unknown=True))

    # Stamp the ACTUAL owner operation now; do not call a draft's preparation
    # time the time a receipt was recorded into the original owner database.
    entity_payload = read(PREP / "entity-import.candidate.json")
    subject_payload = read(PREP / "analysis-subject-import.candidate.json")
    entity_payload["issuer_receipt"]["recorded_at"] = utc()
    subject_payload["perimeter_receipt"]["recorded_at"] = utc()
    write(OUT / "actual-entity-import.json", entity_payload)
    write(OUT / "actual-subject-import.json", subject_payload)
    imported = call("entity-import", ["-m", "stockwiki.cli", "--root", OWNER, "entity-import", "--file", OUT / "actual-entity-import.json"])
    if imported.get("phase_status") != "entity_saved_receipt_recorded" or imported.get("receipt_recorded") is not True:
        raise ValueError("inspect_original_entity_receipt_partial_state")
    call("subject-import", ["-m", "stockwiki.cli", "--root", OWNER, "analysis-subject-import", "--file", OUT / "actual-subject-import.json"])
    identity = call("identity-export", ["-m", "stockwiki.cli", "--root", OWNER, "identity-export-g2b",
                                      "--entity-id", ENTITY, "--as-of", utc()])
    if identity["payload"]["identity_revision"] != 3 or identity["payload"]["identity_state"] != "verified":
        raise ValueError("original_serializer_identity_revision_required")
    subject = subject_payload["analysis_subject"]
    key = subject["analysis_subject_id"] + "@1"
    paths = WorkspacePaths.from_root(OWNER)
    validator = IqsRouteValidator(ROOT, runs_dir=OUT / "route-validation", release_root=RELEASE, process_env=SAFE_ENV)
    routes = QuickScanRouteStore(QuickScanStore(paths), validator=validator)
    binding = routes.identity_binding(key)
    member = routes.identity.get_member(old_policy["universe_id"], ENTITY)
    if member is None:
        call("universe-add", ["-m", "stockwiki.cli", "--root", OWNER, "universe-add",
            "--universe-id", old_policy["universe_id"], "--entity-id", ENTITY,
            "--reason", "user-authorized selected real CATL two-question profile experiment"])
        member = routes.identity.get_member(old_policy["universe_id"], ENTITY)
    if member["membership_status"] != "active" or member["scan_enabled"] is not True:
        raise ValueError("original_canonical_company_not_scan_enabled")
    security = identity["payload"]["securities"][0]
    write(OUT / "route-input.json", dict(entity_id=ENTITY, identity_ref=binding["route_identity_ref"],
        company=identity["payload"]["canonical_name"], ticker="300750", exchange="XSHE", as_of="2026-10-18",
        security_id=security["security_id"], requested_mode="quick", compatible_business_scope=True, verified_facts=[]))
    package = read(RELEASE / "questions/releases/current.json")["package_id"]
    call("resolve-route", [RELEASE / "scripts/question_sets.py", "resolve-route", "--input", OUT / "route-input.json",
        "--module-package-id", package, "--now-utc", utc(), "--output", OUT / "route.json"], cwd=RELEASE)
    decision = read(OUT / "route.json")
    if decision["dispatch_plan"]["status"] != "ready_common_and_risk" or decision["dispatch_plan"]["eligible_module_ids"] != ["common"]:
        raise ValueError("honest_common_only_fallback_required")
    call("compose-route", [RELEASE / "scripts/question_sets.py", "compose-route", "--route-decision", OUT / "route.json",
        "--expected-route-decision-id", decision["decision_id"], "--now-utc", utc(), "--answer-format", "standard-1",
        "--max-questions", "24", "--out-dir", OUT / "composed"], cwd=RELEASE)
    manifest_path = OUT / "composed/manifest.json"
    manifest = read(manifest_path)
    delivery.verify_question_definitions(manifest)
    routes.record_snapshot((OUT / "route.json").read_bytes(), manifest_path.read_bytes(), subject_key=key,
                           expected_decision_id=decision["decision_id"])
    routes.set_current(decision["decision_id"], subject_key=key, expected_current_decision_id=None, now_utc=utc())
    native_subject = dict(entity_id=ENTITY, scope="entity", scope_id=ENTITY,
        analysis_subject_id=subject["analysis_subject_id"], analysis_subject_revision=1,
        primary_issuer_id=ENTITY, perimeter_sha256=binding["perimeter_sha256"], security_id=None, listing_id=None, segment_id=None)
    inputs = OUT / "inputs"; inputs.mkdir()
    bundle = inputs / ("subject_" + digest(native_subject)); bundle.mkdir()
    (OUT / "admission-runs").mkdir(); (OUT / "owner-transport").mkdir()
    (bundle / "manifest.json").write_bytes(manifest_path.read_bytes())
    (bundle / "identity.json").write_bytes((OUT / "identity-export.stdout.json").read_bytes())
    write(OUT / "subject-binding.json", binding)
    actual_security = next(row for row in routes.identity.get_entity(ENTITY)["securities"] if row["security_id"] == security["security_id"])
    listing = resolve_listing_binding(routes.identity, entity_id=ENTITY, security_id=security["security_id"],
        listing_id=listing_id_for_security(actual_security), identity_revision=3, as_of=utc())
    write(OUT / "listing-bindings.json", {security["security_id"]: listing})
    run_id = "NATIVE_PROFILE_20261018_CATL_MIMO2"
    write(OUT / "run.json", dict(run_id=run_id, scan_id=run_id + "_SCAN", inputset_id=run_id + "_INPUT",
        task_mode="comparison", comparison_group_id=run_id))
    write(OUT / "versions.json", dict(identity_schema="2.1.0", answer_schema="1.0.0", observation_schema="1.2.0",
        question_catalog=manifest["template_version"], model_policy_schema="2.0.0"))
    build = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True).stdout.decode("ascii").strip()
    write(OUT / "producer.json", dict(component_version="iqs-profile-native-20261018", build_id=build))
    call("authority", [ROOT / "scripts/c06_authority.py", "--manifest", bundle / "manifest.json", "--identity", bundle / "identity.json",
        "--run", OUT / "run.json", "--versions", OUT / "versions.json", "--producer", OUT / "producer.json",
        "--subject-binding", OUT / "subject-binding.json", "--listing-bindings", OUT / "listing-bindings.json",
        "--release-root", RELEASE, "--observation-schema-version", "1.2.0", "--output", bundle / "authority.json"], cwd=ROOT)
    write(OUT / "questions-input.json", {"manifest": manifest})
    questions = call("questions", [ROOT / "scripts/subject_dispatch_cli.py", "--operation", "questions",
        "--release-root", RELEASE, "--input", OUT / "questions-input.json"], cwd=ROOT)["result"]
    write(bundle / "questions.json", questions)
    write(bundle / "owner-config.json", dict(protocol="stockqa.owner_refresh_config/1.0.0", stockwiki_code_root=str(SW),
        stockwiki_workspace_root=str(OWNER), iqs_code_root=str(ROOT), iqs_release_root=str(RELEASE), subject_key=key,
        scope="entity", scope_id=ENTITY, ttl_hours=24, runs_dir=str(OUT / "owner-transport")))
    store = QuickScanWorkStore(LEDGER)
    owner_client = OwnerRefreshClient(bundle / "owner-config.json", process_env=SAFE_ENV)
    native_plan = owner_client.prepare(load_question_manifest(bundle / "manifest.json"), store,
        identity=load_identity_snapshot(str(bundle / "identity.json"), expected_entity_id=ENTITY), provider="mimo",
        model=route["model"], now=utc(), observation_context=read(bundle / "authority.json")["observation_context"]).plan
    selected = [row for row in native_plan["fields"] if row["field_id"] in IDS]
    if len(selected) != 2 or any(row["decision"] != "dispatch_new_work" for row in selected):
        raise ValueError("actual_original_two_new_works_required")
    generations = {row["generation"] for row in selected}
    if len(generations) != 1:
        raise ValueError("actual_original_single_generation_required")
    write(OUT / "original-native-plan.json", native_plan)
    limits = scan_limits(dict(max_model_requests_per_session=1, max_search_queries_per_session=0))
    by_id = {row["id"]: row for row in manifest["questions"]}
    versions = {row["module_id"]: row["version"] for row in manifest["module_locks"]}
    bound = [dict(question_id=q, question=by_id[q], question_object_sha256=digest(by_id[q]),
                  module_id=by_id[q]["module_id"], module_version=versions[by_id[q]["module_id"]]) for q in IDS]
    group = (ENTITY, None, "entity", ENTITY, binding["perimeter_sha256"])
    profile = build_scan_profile(bound, information_cutoff="2026-10-18", route_id=route["id"],
        group_keys={q: group for q in IDS}, pack_by="module", max_questions_per_pack=2, limits=limits)
    if profile["packs"] != [IDS]:
        raise ValueError("one_actual_original_profile_pack_required")
    deployment = dict(protocol="stockqa.refresh_admission_config/1.0.0", stockwiki_code_root=str(SW),
        stockwiki_workspace_root=str(OWNER), iqs_code_root=str(ROOT), iqs_release_root=str(RELEASE),
        execution_inputs_root=str(inputs), work_store=str(LEDGER), budget_policy_file=str(budget_path),
        consumer_id="invest-quick-scan", runs_dir=str(OUT / "admission-runs"))
    write(OUT / "admission-config.json", deployment)
    fields = [by_id[q]["metric_id"] for q in IDS]
    query = dict(message_type="request", schema_version="2.6.0", request_id=run_id + "_QUERY",
        consumer_id="invest-quick-scan", operation="get_profiles", requested_at=utc(), payload=dict(subject_refs=[native_subject],
        field_ids=fields, information_cutoff="2026-10-18", include_history=True, model_filter=None, snapshot_id=None))
    write(OUT / "query.json", query)
    captured = call("capture", ["-m", "stockwiki.quick_scan_query_v2_cli", "--root", OWNER,
        "--iqs-code-root", ROOT, "--request", OUT / "query.json"])
    query["payload"]["snapshot_id"] = captured["result"]["watermark"]["snapshot_id"]
    request = dict(protocol="iqs.refresh_request/1.5.0", operation="request_refresh", request_id=run_id + "_REFRESH",
        consumer_id="invest-quick-scan", requested_at=utc(), source_query=query, subject_refs=[native_subject], field_ids=fields,
        origin_task_id=run_id, reason="user-authorized real two-question accuracy/safe-summary/keyless recovery experiment",
        cohort_id=run_id, continuation_decision_ref=run_id + "_ACCEPT_RETAINED_S1", question_ids=IDS,
        execution_profile_sha256=digest(profile))
    clock = datetime.now(timezone.utc)
    control = dict(protocol="stockqa.owner_budget_continuation/1.1.0", mode="explicit_repeat_exposure",
        reference_scope="unknown_reference_scope", purpose="independent_comparison", consumer_id="invest-quick-scan",
        cohort_id=run_id, ledger_path=str(LEDGER), snapshot=exposure_snapshot(LEDGER, budget, dialect="1.5.0"),
        future_request_core=future_request_core(request), cells=[dict(cell_id=run_id + "_CELL1", question_ids=IDS,
            question_body_sha256={q: digest(by_id[q]) for q in IDS}, subject_ref=native_subject, provider="mimo", model=route["model"],
            route_id=route["id"], quota_group=route["quota_group"], generation=next(iter(generations)),
            manifest_raw_sha256=sha(bundle / "manifest.json"), execution_profile=profile, execution_profile_sha256=digest(profile),
            controls=dict(thinking_enabled=True, max_output_tokens=16384, strategy_id="module_packs",
                search_policy_sha256=digest(NO_EXTERNAL_SEARCH_POLICY), replicate_ordinal=1))], max_new_http_requests=1,
        valid_from=(clock-timedelta(seconds=30)).isoformat().replace("+00:00", "Z"),
        expires_at=(clock+timedelta(hours=3)).isoformat().replace("+00:00", "Z"), no_retry_original_intents=True,
        unknown_cash_remains_unknown=True, retained_original_requests=True, original_process_stopped=True,
        stop_evidence_ref="actual-native-catl-profile-01/worker-observation.json", additional_risk_hold_micros=0)
    policy = copy.deepcopy(old_policy)
    policy.update(protocol="stockwiki.refresh_owner_policy/1.5.0", policy_id=run_id + "_POLICY",
        policy_version=old_policy["policy_version"]+1, field_ids=fields, routes=[dict(subject_key=key, scope="entity",
        scope_id=ENTITY, subject_ref=native_subject)], provider="mimo", model=route["model"])
    policy["qa"].update(quote_schema_version="1.5.0", admission_config=str(OUT / "admission-config.json"))
    policy["budget_exposure_acceptance"] = dict(continuation_decision_ref=request["continuation_decision_ref"], control=control)
    refresh_contract.validate_policy(policy)
    write(OUT / "owner-policy.installed.json", policy); write(OUT / "refresh-request.json", request)
    if policy_path.read_bytes() != old_policy_raw:
        raise ValueError("original_owner_policy_changed_concurrently")
    pending = policy_path.with_suffix(".json.profile-smoke-pending")
    write(pending, policy); os.replace(pending, policy_path)
    public = ["-m", "stockwiki.quick_scan_refresh_owner_cli", "--root", OWNER,
              "--iqs-code-root", ROOT, "--iqs-release-root", RELEASE]
    preview = call("preview", [*public, "--request", OUT / "refresh-request.json"])
    if preview["status"] != "ready":
        raise ValueError("actual_original_preview_not_ready")
    record = RefreshRecordStore(paths).load(preview["preview_id"])
    controller = dict(profile_id="iqs-root-controller", harness="Codex", principal=current_principal(),
        source_commit=build, purpose="authorized actual CATL profile/summary/keyless recovery")
    write(OUT / "controller-profile.json", controller)
    install = dict(protocol="stockwiki.refresh_delegation_install/1.0.0", workspace_root=str(OWNER),
        preview_id=preview["preview_id"], preview_record_sha256=record["record_sha256"], agent=dict(
            profile_id=controller["profile_id"], profile_sha256=digest(controller), harness_ref="Codex current root controller"),
        authorization_reference="user-2026-10-18-all-followup-authority-PWF-real-summary-cache",
        expires_at=control["expires_at"])
    install_path = OWNER / "config/quick_scan_delegation_install.json"
    if install_path.exists():
        (OUT / "backup/prior-delegation-install.json").write_bytes(install_path.read_bytes())
    install_pending = install_path.with_suffix(".json.profile-smoke-pending")
    write(install_pending, install); os.replace(install_pending, install_path)
    grant = call("delegated-install", [*public, "--install-delegation"])
    confirmed = call("delegated-confirm", [*public, "--confirm-delegated", preview["preview_id"],
        "--delegation-id", grant["grant_id"], "--idempotency-key", run_id + "_ACTION"])
    admitted = RefreshAdmissionService(OUT / "admission-config.json", process_env=SAFE_ENV).admit(confirmed["confirmation_id"])
    write(OUT / "admission-result.json", admitted)
    if original_budget_rows() != before_budget:
        raise ValueError("original_budget_attempt_rows_changed_before_send")
    board_path = Path(__file__).with_name("prepared-public-board.json")
    board_meta = read(Path(__file__).with_name("prepared-public-board.provenance.json"))
    if sha(board_path) != board_meta["board_raw_sha256"] or board_meta["private_gold_read_by_builder"] is not False:
        raise ValueError("independently_allowlisted_public_board_changed")
    bridge_path = OUT / "public-identity-bridge.json"
    write(bridge_path, dict(entity_id=binding["entity_id"], subject_key=binding["subject_key"]))
    refs = {name: dict(path=path.name, bytes=path.stat().st_size, raw_sha256=sha(path)) for name, path in (
        ("evidence-board.json", board_path), ("identity.json", bridge_path))}
    write(OUT / "run-config.json", dict(protocol="iqs.real-profile-smoke-config/1.0.0",
        deployment_proof=delivered["proof_ref"],
        run_root=str(OUT), deployment=str(OUT / "admission-config.json"), confirmation_id=confirmed["confirmation_id"],
        bundle=str(bundle), budget_policy_file=str(budget_path), route_id=route["id"], run_id=run_id,
        experiment_id="shared-profile-real-summary-20261018", native_subject_ref=native_subject, question_ids=IDS,
        public_input_refs=refs, public_board=str(board_path), public_identity=str(bridge_path),
        information_cutoff="2026-10-18", execution_profile=profile, limits=limits, owner_batch_claim=True,
        thinking_enabled=True, max_output_tokens=16384, pack_by="module", max_questions_per_pack=2))
    write(OUT / "activation-complete.json", dict(status="genuine_native_profile_admitted_no_model_send",
        confirmation_id=confirmed["confirmation_id"], actual_owner_subject_key=key, original_requests_retained=101,
        original_unresolved_retained=3, new_model_http=0, financial_qualification=False))
    print(json.dumps(dict(status="actual_native_profile_admitted", model_http=0)))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import traceback
        print(json.dumps(dict(status="stopped_inspect_partial_state_do_not_resend", error_type=type(error).__name__,
            stack_locations_only=[dict(file=row.filename, line=row.lineno, function=row.name)
                                  for row in traceback.extract_tb(error.__traceback__)])))
        raise SystemExit(2) from None
