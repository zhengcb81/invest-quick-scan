"""One controller-owned real activation; delegates execution to original APIs.

No model HTTP, new fee ledger, identity fabrication or old-attempt settlement.
Partial activation must be inspected, never automatically restarted from scratch.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
QA, SW = ROOT.parent / "StockQAbyLLM", ROOT.parent / "StockWiki"
sys.path[:0] = [str(QA), str(SW), str(ROOT / "scripts")]
OWNER = ROOT / "runs/c16b/native-owner-alphabet-01/owner-workspace"
LEDGER = ROOT / "runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"
RELEASE = ROOT / "runs/c16b/iqs-release"
OUT = BASE / "actual-native-alphabet-01"
SAFE_ENV = {k: v for k, v in os.environ.items() if k.upper() in {
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA",
    "LOCALAPPDATA", "SYSTEMDRIVE", "TEMP", "TMP"}}
SAFE_ENV.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                PYTHONPATH=os.pathsep.join((str(SW), str(QA))))


def read(path):
    from src.utils.quick_scan_result_outbox import strict_json_loads
    return strict_json_loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def call(label, args, *, cwd=SW):
    # All argv below are fixed first-party modules/scripts, never shell strings.
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


def database_state(path):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        rows = {name: sorted(repr(tuple(r)) for r in db.execute('SELECT * FROM "' + name.replace('"', '""') + '"'))
                for name in names}
        return rows


def main():
    # These engineering signoffs are verified before touching actual state.
    final = read(ROOT / "docs/implementation/reviews/native-continuation-2026-10-18/final.json")
    if not str(final.get("status", "")).startswith("passed") or final.get("open_findings") != []:
        raise ValueError("native_continuation_whole_node_not_accepted")
    if OUT.exists():
        raise ValueError("inspect_partial_actual_activation_do_not_restart")
    # Preparation performs no network, including subprocesses (which receive no keys).
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

    prep = read(BASE / "real-native-smoke-preparation.json")
    prior_policy_path = OWNER / "config/quick_scan_refresh.json"
    prior_policy_raw = prior_policy_path.read_bytes()
    prior_policy = read(prior_policy_path)
    if current_principal() != prior_policy["owner_principal"]:
        raise ValueError("native_os_owner_changed")
    observation = read(BASE / "original-exposure-route-observation.json")
    if sha(LEDGER) != observation["database_sha256"]:
        raise ValueError("original_native_ledger_changed")
    budget_file = Path(prep["original_native_budget_policy"]["path"])
    if sha(budget_file) != prep["original_native_budget_policy"]["sha256"]:
        raise ValueError("original_budget_configuration_changed")
    budget = read(budget_file)
    route = next(r for r in budget["routes"] if r["id"] == "mimo-pro-t2")
    import psutil
    matched_workers, unreadable = [], 0
    historical = [str((ROOT / p).resolve()).casefold() for p in (
        "runs/company-agent-owner-2026-10-15-01", "runs/real-contrast-2026-10-16-03")]
    for process in psutil.process_iter(["pid", "name"]):
        if "python" not in (process.info["name"] or "").casefold():
            continue
        try:
            if process.pid == os.getpid():
                continue
            working = Path(process.cwd()).resolve()
            cwd_key = str(working).casefold()
            argument_paths = []
            for argument in process.cmdline():
                try:
                    candidate = Path(argument)
                    candidate = candidate if candidate.is_absolute() else working / candidate
                    argument_paths.append(str(candidate.resolve()).casefold())
                except (OSError, ValueError):
                    continue
            def under_original(path):
                return any(path == p or path.startswith(p + os.sep) for p in historical)
            if under_original(cwd_key) or any(under_original(p) for p in argument_paths):
                matched_workers.append(process.pid)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            unreadable += 1
    if matched_workers or unreadable:
        raise ValueError("original_local_worker_state_not_quiescent")
    paths = WorkspacePaths.from_root(OWNER)
    routes = QuickScanRouteStore(QuickScanStore(paths), validator=IqsRouteValidator(ROOT,
        runs_dir=BASE / "activation-route-validation", release_root=RELEASE, process_env=SAFE_ENV))
    selector = prior_policy["routes"][0]
    binding = routes.identity_binding(selector["subject_key"])
    if binding != read(ROOT / "runs/c16b/native-owner-alphabet-01/inputs/subject-binding.json"):
        raise ValueError("actual_identity_binding_changed")
    member = routes.identity.get_member(prior_policy["universe_id"], binding["entity_id"])
    if member["membership_status"] != "active" or member["scan_enabled"] is not True:
        raise ValueError("actual_company_not_enabled")
    current = routes.get_for_execution(subject_key=selector["subject_key"], scope=selector["scope"],
                                       scope_id=selector["scope_id"], now_utc=utc())
    old_decision = "route_983a38a1dbef645348e59039769f544b5b0a2eac957fa9ba9276baaa2d96f04a"
    new_decision = "route_afb4bdc99c158423968c2e6c0e3da1dd57ccf2888377abfbcc80bde074410304"
    if current["expected_decision_id"] != old_decision or current["anchor_version"] != 1:
        raise ValueError("original_current_route_changed")
    staged = routes.get_snapshot(new_decision)
    if staged is None or staged["manifest_raw_sha256"] != prep["manifest_raw_sha256"]:
        raise ValueError("original_recorded_snapshot_not_matching")
    from src.utils.quick_scan_result_outbox import strict_json_loads
    frozen_manifest = strict_json_loads(staged["manifest_raw"].decode("utf-8"))
    question_map = {q["id"]: q for q in frozen_manifest["questions"]}
    if (len(prep["question_ids"]) != 12 or len(set(prep["question_ids"])) != 12
        or {qid: digest(question_map[qid]) for qid in prep["question_ids"]}
            != prep["original_question_body_sha256"]
        or frozen_manifest["profile"]["as_of"] != prep["information_cutoff"]
        or route != prep["desired_model_route"]):
        raise ValueError("actual_question_cutoff_or_model_route_changed")
    OUT.mkdir()
    (OUT / "backup").mkdir()
    (OUT / "backup/owner-policy.raw.json").write_bytes(prior_policy_raw)
    write(OUT / "worker-observation.json", dict(observed_at=utc(), matched_local_original_workers=matched_workers,
        unreadable_python_processes=unreadable, remote_provider_outcomes_still_unknown=True))
    if any(Path(str(LEDGER) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("original_native_ledger_busy")
    (OUT / "backup/original-ledger.raw.sqlite").write_bytes(LEDGER.read_bytes())
    before_rows = database_state(LEDGER)
    for label, source in (("original-ledger", LEDGER), ("original-scan", OWNER / "data/quick_scan/scan.sqlite")):
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(OUT / "backup" / (label + ".sqlite"))) as dst:
                src.backup(dst)
    write(OUT / "before.json", dict(observed_at=utc(), ledger_sha256=sha(LEDGER),
        owner_policy_sha256=sha(prior_policy_path), old_route=old_decision, backup_complete=True))
    store = QuickScanWorkStore(LEDGER)
    after_rows = database_state(LEDGER)
    if any(after_rows.get(name) != rows for name, rows in before_rows.items()):
        raise ValueError("migration_changed_old_rows")
    write(OUT / "migration.json", dict(all_original_table_rows_preserved=True,
        new_tables_empty=all(not rows for name, rows in after_rows.items() if name not in before_rows),
        original_requests=100))
    activated = routes.set_current(new_decision, subject_key=selector["subject_key"],
                                  expected_current_decision_id=old_decision, now_utc=utc())
    write(OUT / "route-activation.json", activated)
    inputs = OUT / "inputs"
    inputs.mkdir()
    bundle = inputs / ("subject_" + digest(prep["native_subject_ref"]))
    bundle.mkdir()
    (OUT / "admission-runs").mkdir()
    (OUT / "owner-transport").mkdir()
    (bundle / "manifest.json").write_bytes(staged["manifest_raw"])
    original_identity = ROOT / "runs/c16b/native-owner-alphabet-01/inputs/identity.original-envelope.json"
    (bundle / "identity.json").write_bytes(original_identity.read_bytes())
    write(OUT / "subject-binding.json", binding)
    manifest = read(bundle / "manifest.json")
    security_id = manifest["profile"]["security_id"]
    entity = routes.identity.get_entity(binding["entity_id"])
    security = next(s for s in entity["securities"] if s["security_id"] == security_id)
    listing = resolve_listing_binding(routes.identity, entity_id=binding["entity_id"], security_id=security_id,
        listing_id=listing_id_for_security(security), identity_revision=binding["identity_revision"], as_of=utc())
    write(OUT / "listing-bindings.json", {security_id: listing})
    run_id = prep["desired_controls"]["cohort_id"]
    write(OUT / "run.json", dict(run_id=run_id, scan_id=run_id + "_SCAN", inputset_id=run_id + "_INPUT",
                                task_mode="comparison", comparison_group_id=run_id))
    write(OUT / "versions.json", dict(identity_schema="2.1.0", answer_schema="1.0.0", observation_schema="1.2.0",
        question_catalog=manifest["template_version"], model_policy_schema="2.0.0"))
    build = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    write(OUT / "producer.json", dict(component_version="iqs-shared-native-20261018", build_id=build))
    call("authority", [ROOT / "scripts/c06_authority.py", "--manifest", bundle / "manifest.json",
        "--identity", bundle / "identity.json", "--run", OUT / "run.json", "--versions", OUT / "versions.json",
        "--producer", OUT / "producer.json", "--subject-binding", OUT / "subject-binding.json",
        "--listing-bindings", OUT / "listing-bindings.json", "--release-root", RELEASE,
        "--observation-schema-version", "1.2.0", "--output", bundle / "authority.json"], cwd=ROOT)
    write(OUT / "questions-input.json", {"manifest": manifest})
    questions = call("questions", [ROOT / "scripts/subject_dispatch_cli.py", "--operation", "questions",
        "--release-root", RELEASE, "--input", OUT / "questions-input.json"], cwd=ROOT)["result"]
    write(bundle / "questions.json", questions)
    owner_config = dict(protocol="stockqa.owner_refresh_config/1.0.0", stockwiki_code_root=str(SW),
        stockwiki_workspace_root=str(OWNER), iqs_code_root=str(ROOT), iqs_release_root=str(RELEASE),
        subject_key=selector["subject_key"], scope=selector["scope"], scope_id=selector["scope_id"],
        ttl_hours=24, runs_dir=str(OUT / "owner-transport"))
    write(bundle / "owner-config.json", owner_config)
    owner_client = OwnerRefreshClient(bundle / "owner-config.json", process_env=SAFE_ENV)
    from src.utils.quick_scan_question_manifest import load_question_manifest
    identity = load_identity_snapshot(str(bundle / "identity.json"), expected_entity_id=binding["entity_id"])
    native_plan = owner_client.prepare(load_question_manifest(bundle / "manifest.json"), store,
        identity=identity, provider="mimo", model=route["model"], now=utc(),
        observation_context=read(bundle / "authority.json")["observation_context"]).plan
    selected_plans = [r for r in native_plan["fields"] if r["field_id"] in prep["question_ids"]]
    if len(selected_plans) != 12 or any(r["decision"] != "dispatch_new_work" for r in selected_plans):
        raise ValueError("actual_native_plan_is_not_twelve_new_works")
    generations = {r["generation"] for r in selected_plans}
    if len(generations) != 1:
        raise ValueError("native_single_cell_requires_same_actual_generation")
    write(OUT / "original-native-plan.json", native_plan)
    deployment = dict(protocol="stockqa.refresh_admission_config/1.0.0", stockwiki_code_root=str(SW),
        stockwiki_workspace_root=str(OWNER), iqs_code_root=str(ROOT), iqs_release_root=str(RELEASE),
        execution_inputs_root=str(inputs), work_store=str(LEDGER), budget_policy_file=str(budget_file),
        consumer_id="invest-quick-scan", runs_dir=str(OUT / "admission-runs"))
    write(OUT / "admission-config.json", deployment)
    query = dict(message_type="request", schema_version="2.6.0", request_id=run_id + "_QUERY",
        consumer_id="invest-quick-scan", operation="get_profiles", requested_at=utc(), payload=dict(
            subject_refs=[prep["native_subject_ref"]], field_ids=[q["metric_id"] for q in manifest["questions"]
                if q["id"] in prep["question_ids"]], information_cutoff=prep["information_cutoff"],
            include_history=True, model_filter=None, snapshot_id=None))
    write(OUT / "query.json", query)
    captured = call("capture", ["-m", "stockwiki.quick_scan_query_v2_cli", "--root", OWNER,
        "--iqs-code-root", ROOT, "--request", OUT / "query.json"])
    query["payload"]["snapshot_id"] = captured["result"]["watermark"]["snapshot_id"]
    request = dict(protocol="iqs.refresh_request/1.4.0", operation="request_refresh", request_id=run_id + "_REFRESH",
        consumer_id="invest-quick-scan", requested_at=utc(), source_query=query,
        subject_refs=query["payload"]["subject_refs"], field_ids=query["payload"]["field_ids"],
        origin_task_id=run_id, reason="bounded real summary and exact cache recovery experiment",
        cohort_id=run_id, continuation_decision_ref=run_id + "_ACCEPT_RETAINED_S1_PAIR", question_ids=prep["question_ids"])
    clock = datetime.now(timezone.utc)
    control = dict(protocol="stockqa.owner_budget_continuation/1.0.0", mode="explicit_repeat_exposure",
        reference_scope="unknown_reference_scope", purpose="independent_comparison", consumer_id="invest-quick-scan",
        cohort_id=run_id, ledger_path=str(LEDGER), snapshot=exposure_snapshot(LEDGER, budget, [
            "DISPATCH_86004529874040469881f32f71aa5a55", "DISPATCH_a11c198286874b70a7fa6de11af144ee"]),
        future_request_core=future_request_core(request), cells=[dict(cell_id=run_id + "_CELL1",
            question_ids=prep["question_ids"], question_body_sha256=prep["original_question_body_sha256"],
            subject_ref=prep["native_subject_ref"], provider="mimo", model=route["model"], route_id=route["id"],
            quota_group=route["quota_group"], generation=next(iter(generations)), manifest_raw_sha256=sha(bundle / "manifest.json"),
            controls=dict(thinking_enabled=True, max_output_tokens=16384, strategy_id="free_agent",
                search_policy_sha256=digest(NO_EXTERNAL_SEARCH_POLICY), replicate_ordinal=1))], max_new_http_requests=1,
        valid_from=(clock-timedelta(seconds=30)).isoformat().replace("+00:00", "Z"),
        expires_at=(clock+timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
        no_retry_original_intents=True, unknown_cash_remains_unknown=True, retained_original_requests=True,
        original_process_stopped=True, stop_evidence_ref="actual-native-alphabet-01/worker-observation.json", additional_risk_hold_micros=0)
    policy = copy.deepcopy(prior_policy)
    policy.update(protocol="stockwiki.refresh_owner_policy/1.4.0", policy_id=run_id + "_POLICY",
        policy_version=prior_policy["policy_version"]+1, field_ids=query["payload"]["field_ids"],
        provider="mimo", model=route["model"])
    policy["qa"].update(work_store=str(LEDGER), budget_policy_file=str(budget_file), policy_id=budget["policy_id"],
        route_id=route["id"], provider_config_ref=route["provider_config_ref"], quote_schema_version="1.4.0",
        admission_config=str(OUT / "admission-config.json"))
    policy["budget_exposure_acceptance"] = dict(continuation_decision_ref=request["continuation_decision_ref"], control=control)
    import refresh_contract
    refresh_contract.validate_policy(policy)
    write(OUT / "owner-policy.installed.json", policy)
    write(OUT / "refresh-request.json", request)
    if prior_policy_path.read_bytes() != prior_policy_raw:
        raise ValueError("owner_policy_changed_concurrently")
    pending = prior_policy_path.with_suffix(".json.native-smoke-pending")
    write(pending, policy)
    os.replace(pending, prior_policy_path)
    base = ["-m", "stockwiki.quick_scan_refresh_owner_cli", "--root", OWNER,
            "--iqs-code-root", ROOT, "--iqs-release-root", RELEASE]
    preview = call("preview", [*base, "--request", OUT / "refresh-request.json"])
    if preview["status"] != "ready":
        raise ValueError("actual_original_preview_not_ready")
    record = RefreshRecordStore(paths).load(preview["preview_id"])
    profile = dict(profile_id="iqs-root-controller", harness="Codex", principal=current_principal(),
                   source_commit=build, purpose="authorized real native summary/cache recovery")
    write(OUT / "controller-profile.json", profile)
    install = dict(protocol="stockwiki.refresh_delegation_install/1.0.0", workspace_root=str(OWNER),
        preview_id=preview["preview_id"], preview_record_sha256=record["record_sha256"], agent=dict(
            profile_id=profile["profile_id"], profile_sha256=digest(profile), harness_ref="Codex current root controller"),
        authorization_reference="user-2026-10-18-continue-PWF-real-summary-cache-full-authorization",
        expires_at=control["expires_at"])
    install_path = OWNER / "config/quick_scan_delegation_install.json"
    if install_path.exists():
        (OUT / "backup/prior-delegation-install.json").write_bytes(install_path.read_bytes())
    install_pending = install_path.with_suffix(".json.native-smoke-pending")
    write(install_pending, install)
    os.replace(install_pending, install_path)
    grant = call("delegated-install", [*base, "--install-delegation"])
    confirmed = call("delegated-confirm", [*base, "--confirm-delegated", preview["preview_id"],
        "--delegation-id", grant["grant_id"], "--idempotency-key", run_id + "_ACTION"])
    admitted = RefreshAdmissionService(OUT / "admission-config.json", process_env=SAFE_ENV).admit(confirmed["confirmation_id"])
    write(OUT / "admission-result.json", admitted)
    preparation = read(BASE / "actual-evidence-projection/preparation-lock.json")
    pins = []
    for directory in (ROOT / "scripts", QA / "src", SW / "stockwiki", ROOT.parent / "iqs-company-agent-lab/src",
                      ROOT.parent / "iqs-agent-runtime-lab/src"):
        for source in sorted(directory.rglob("*.py")):
            pins.append(dict(path=str(source), sha256=sha(source)))
    pins.append(dict(path=str(BASE / "actual-evidence-projection/project_existing_sources.py"),
                     sha256=sha(BASE / "actual-evidence-projection/project_existing_sources.py")))
    write(OUT / "run-config.json", dict(protocol="iqs.real-admitted-smoke-config/1.0.0", source_pins=pins,
        run_root=str(OUT), deployment=str(OUT / "admission-config.json"), confirmation_id=confirmed["confirmation_id"],
        bundle=str(bundle), budget_policy_file=str(budget_file), route_id=route["id"], run_id=run_id,
        experiment_id="shared-native-real-summary-20261018", public_input_refs=preparation["original_refs"],
        public_board=str(ROOT / "runs/real-contrast-2026-10-16-03/inputs/evidence-board.json"),
        public_identity=str(ROOT / "runs/real-contrast-2026-10-16-03/inputs/identity.json")))
    write(OUT / "activation-complete.json", dict(status="genuine_native_admitted_no_model_send",
        confirmation_id=confirmed["confirmation_id"], route_version=activated["version"],
        original_legacy_rows_retained=True, new_model_http=0, financial_qualification=False))
    print(json.dumps(dict(status="actual_native_admitted", model_http=0)))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import traceback
        print(json.dumps(dict(status="stopped_inspect_partial_state_do_not_resend", error_type=type(error).__name__,
            locations=[dict(file=r.filename, line=r.lineno, function=r.name) for r in traceback.extract_tb(error.__traceback__)])))
        raise SystemExit(2) from None
