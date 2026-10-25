"""Original owner preparation in owned disposable namespaces; no paid calls.

Identity evidence is deliberately synthetic example.invalid data. These cases
prove interface composition and isolation, never financial or real-company gold.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import pytest

from scripts.dashboard_prepare import DashboardPrepareError, PrepareGateway, _env, _new, _apply_guard, _control_path, _native_cli, _timeouts, _sha, _snapshot_sha

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT.parent / "StockWiki"
QA = ROOT.parent / "StockQAbyLLM"
ENTITY = "ENT_1b2a4d3e-0000-4a1b-8c2d-000000000001"


def tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


@pytest.fixture()
def original(request):
    setup_started = time.perf_counter()
    if not (WIKI / "stockwiki/identity_g2b.py").is_file() or not (QA / "src/utils/quick_scan_refresh_admission.py").is_file():
        pytest.skip("Explicit integration dependencies: original sibling StockWiki and StockQA")
    # State belongs to IQS; every owner/ledger/runtime is still disposable.
    with tempfile.TemporaryDirectory(prefix="dashboard-prepare-test-", dir=ROOT / "runs") as own:
        base = Path(own)
        source = r'''
import json,sys
from pathlib import Path
from datetime import datetime,timedelta,timezone
sys.path[:0]=[sys.argv[1],str(Path(sys.argv[1])/'tests')]
from test_identity_g2b_export import _entity,_binding,_fixture_csv,_provisional_receipt
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.identity_import import import_entity
from stockwiki.identity_receipts import IdentityReceiptStore
from stockwiki.market_registry import MarketRegistryStore
from stockwiki.quick_scan_analysis import AnalysisSubjectStore,perimeter_sha256
from stockwiki.quick_scan_subject_dispatch import SubjectBoundObservationStore
from stockwiki.quick_scan_universe import add_member
from stockwiki.quick_scan_refresh_principal import current_principal
base=Path(sys.argv[2]);paths=WorkspacePaths.from_root(base/'owner')
identity=QuickScanStore(paths);identity.migrate();receipts=IdentityReceiptStore(paths);receipts.migrate()
recorded_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat().replace('+00:00','Z') if sys.argv[3]=='fresh_today' else '2026-09-29T00:00:00Z'
entity=_entity('verified');bindings=[_binding()]
if sys.argv[3]=='multi':
    secondary=dict(entity['securities'][0],security_id='SEC_2c3b5e4f-0000-4b2c-9d3e-000000000002',ticker='ACMB',source_binding_ref='BND_fixture_acme_2')
    entity['securities'].append(secondary)
    bindings.append(dict(bindings[0],security_id=secondary['security_id'],ticker=secondary['ticker'],binding_ref=secondary['source_binding_ref'],source_record_id='urn:company-wiki:source:fixture-acme-class-b'))
partial={'kind':'verified_issuer','receipt_id':entity['verified_issuer_receipt_id'],
'entity_id':entity['entity_id'],'identity_revision':1,'recorded_at':recorded_at,
'same_legal_issuer':True,'evidence_ref':'https://example.invalid/issuer-only-synthetic'}
result=import_entity(identity,receipts,{'entity':entity,'source_bindings':bindings,'issuer_receipt':partial},at=recorded_at)
assert result['receipt_recorded'],result
(base/'issuer-receipt.json').write_text(json.dumps(partial),encoding='utf-8')
MarketRegistryStore(paths).import_official_csv(_fixture_csv(),source_url='https://example.invalid/mic-fixture',fetched_at='2026-09-29T00:00:00Z')
identity.create_universe('TEST','Synthetic engineering universe');add_member(identity,'TEST',entity['entity_id'],added_reason='Synthetic test only')
subjects=AnalysisSubjectStore(paths);subjects.migrate()
subject={'analysis_subject_schema_version':'1.0.0','analysis_subject_id':'ASJ_33333333-3333-4333-8333-333333333333',
'analysis_subject_revision':1,'display_name':'Synthetic legal issuer only','primary_issuer_id':entity['entity_id'],
'anchor_listing_id':None,'scope_kind':'standalone_issuer','scope_as_of':'2026-09-29T00:00:00Z','perimeter_coverage':'not_applicable',
'memberships':[{'entity_id':entity['entity_id'],'role':'primary_issuer','valid_from':None,'valid_to':None,'evidence_ref':partial['evidence_ref']}]}
receipt={'receipt_id':'PRC_SYNTHETIC_ONLY','status':'verified','analysis_subject_id':subject['analysis_subject_id'],
'analysis_subject_revision':1,'primary_issuer_id':entity['entity_id'],'evidence_ref':partial['evidence_ref'],
'perimeter_sha256':perimeter_sha256(subject),'decision_ref':'isolated-test-issuer-scope','recorded_at':'2026-09-29T00:00:00Z'}
subjects.import_subject(identity,{'analysis_subject':subject,'perimeter_receipt':receipt})
SubjectBoundObservationStore(paths,contract=None).migrate()
(base/'principal.json').write_text(json.dumps({'principal':current_principal()}),encoding='utf-8')
'''
        done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", source, str(WIKI), str(base),
                               "multi" if getattr(request, "param", False) is True else
                               "fresh_today" if getattr(request, "param", None) == "fresh_today" else "single"],
                              cwd=base, env=_env(), capture_output=True, timeout=60)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
        policy = {"configured": True, "policy_id": "isolated-dashboard-new-scope", "policy_version": "1.0.0",
            "budget": {"currency": "USD", "max_cost": 10, "max_cost_per_attempt": .1, "max_in_flight_total": 1, "max_requests": 100},
            "cost_policy": {"pricing_basis": "user_cap", "pricing_ref": None, "reserve_before_dispatch": True, "unknown_actual_cost_action": "retain_reservation_and_pause"},
            "dispatch": {"max_in_flight_total": 1}, "quota_groups": [{"id": "test", "max_in_flight": 1}],
            "routes": [{"eligible": True, "id": "test-route", "max_in_flight": 1, "model": "mimo-v2.6-pro", "provider_config_ref": "mimo", "quota_group": "test", "unavailable_reason": None}]}
        (base / "runtime").mkdir()
        for name in ("inputs", "admission-runs"):
            (base / name).mkdir()
        _new(base / "budget.json", policy)
        _new(base / "spend.json", {"status": "synthetic-no-paid-dispatch"})
        _new(base / "runtime/llm_apis.json", {"fixture": "No credentials; execution is not invoked"})
        qa_setup = r'''
import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from src.utils.quick_scan_work_store import QuickScanWorkStore
base=Path(sys.argv[2]);store=QuickScanWorkStore(base/'work.sqlite')
store.configure_quick_scan_budget(json.loads((base/'budget.json').read_text(encoding='utf-8')))
'''
        done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", qa_setup, str(QA), str(base)],
                              cwd=base / "runtime", env=_env(), capture_output=True, timeout=60)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
        admission = {"protocol": "stockqa.refresh_admission_config/1.0.0", "consumer_id": "invest-quick-scan",
            "stockwiki_code_root": str(WIKI), "stockwiki_workspace_root": str(base / "owner"), "iqs_code_root": str(ROOT),
            "iqs_release_root": str(ROOT), "execution_inputs_root": str(base / "inputs"), "work_store": str(base / "work.sqlite"),
            "budget_policy_file": str(base / "budget.json"), "runs_dir": str(base / "admission-runs")}
        _new(base / "admission.json", admission)
        owner_policy = {"protocol": "stockwiki.refresh_owner_policy/1.1.0", "policy_id": "synthetic-dashboard-owner", "policy_version": 1,
            "owner_principal": json.loads((base / "principal.json").read_text(encoding="utf-8"))["principal"], "allowed_consumer_ids": ["invest-quick-scan"],
            "universe_id": "TEST", "field_ids": [], "routes": [], "route_resolution": "current_owner_members", "field_permission": "current_manifest",
            "provider": "mimo", "model": "mimo-v2.6-pro", "ttl_hours": 24,
            "qa": {"code_root": str(QA), "work_store": str(base / "work.sqlite"), "budget_policy_file": str(base / "budget.json"),
                   "policy_id": policy["policy_id"], "route_id": "test-route", "provider_config_ref": "mimo", "quote_schema_version": "1.1.0"}}
        _new(base / "owner/config/quick_scan_refresh.json", owner_policy)
        config = {"iqs_root": str(ROOT), "iqs_release_root": str(ROOT), "stockwiki_root": str(WIKI), "stockwiki_python": sys.executable,
            "stockqa_root": str(QA), "stockqa_python": sys.executable, "workspace_root": str(base / "owner"),
            "prepare": {"state_root": str(base / "preparation"), "admission_config": str(base / "admission.json"),
                "runtime_dir": str(base / "runtime"), "spend_authorization": str(base / "spend.json"),
                "authorization_reference": "synthetic-test-user-authorization-not-real-company-golden",
                "agent": {"profile_id": "isolated-fixture", "profile_sha256": "a" * 64, "harness_ref": "pytest-engineering-only"},
                "producer": {"component_version": "dashboard-preparation-test", "build_id": "synthetic-offline-only"}}}
        try:
            gateway = PrepareGateway(config)
            gateway.fixture_setup_seconds = time.perf_counter() - setup_started
            yield gateway, base, config
        finally:
            # Unique owner workspace means this lock belongs only to this
            # disposable fixture. Never unlink a production/shared lock.
            lock = _control_path(config)
            lock.unlink(missing_ok=True)
            try:
                lock.parent.rmdir()
            except OSError:
                pass


def test_preview_all_36_uses_original_serializer_and_keeps_original_databases_unchanged(original):
    gateway, base, _ = original
    before = tree(base / "owner")
    result = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25", "mode": "quick"})
    assert result["question_count"] == 36 and len(result["questions"]) == 36
    assert result["bank"]["modules"] == ["common", "dupont", "porter"]
    assert result["can_apply"] and result["owner_database_writes"] == result["API_requests"] == 0
    assert result["selected_subject"]["scope_kind"] == "standalone_issuer"
    assert tree(base / "owner") == before
    assert gateway.preparation(result["preview_id"])["status"] == "not_applied"


def test_native_fresh_prepare_registers_36_original_work_items_without_http_and_replays_exact_result(original):
    gateway, base, _ = original
    preview_started = time.perf_counter()
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    preview_seconds = time.perf_counter() - preview_started
    apply_started = time.perf_counter()
    try:
        result = gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    except DashboardPrepareError as error:
        pytest.fail(f"Original prepare refused: {error.code}; {error.details}")
    apply_seconds = time.perf_counter() - apply_started
    assert result["status"] == "prepared" and result["API_requests"] == 0
    assert result["dispatch_started"] is False and result["financial_accuracy_proven"] is False
    assert sum(len(item["admission"]["registration"]["items"]) for item in result["execution_bundles"]) == 36
    assert [item["question_count"] for item in result["execution_bundles"]] == [33, 3]
    assert [item["execution_bundle"]["scope"] for item in result["execution_bundles"]] == ["entity", "security"]
    assert all(item["execution_bundle"]["company_preparation_id"] == preview["preview_id"] for item in result["execution_bundles"])
    assert result["execution_bundle"] == result["bundle"]
    from scripts.dashboard_execution import ExecutionGateway
    for item in result["execution_bundles"]:
        bundle = item["execution_bundle"]
        command = ExecutionGateway({"stockqa_python": sys.executable})._command(bundle, QA, base / "not-dispatched-output")
        if bundle["scope"] == "security":
            assert command[command.index("--security-scope-id") + 1] == bundle["security_id"]
        else:
            assert "--security-scope-id" not in command
        assert bundle["expected_scope_bindings"] == result["execution_bundles"][0]["execution_bundle"]["expected_scope_bindings"]
        assert json.loads(Path(bundle["manifest"]).read_text(encoding="utf-8"))["question_count"] == 36
    snapshot = tree(base)
    replay = gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    assert replay == {**result, "replayed": True}
    assert gateway.preparation(preview["preview_id"])["result"] == result
    assert tree(base) == snapshot
    assert not (base / "owner/config/quick_scan_delegation_install.json").exists()
    # Product preview must consume the actual native keyed work-items DTO,
    # not only an illustrative list response from a transport fixture.
    executor = ExecutionGateway({"stockqa_root": str(QA), "stockqa_python": sys.executable,
        "state_root": str(base / "execution"), "bundles": {item["bundle_id"]: item["execution_bundle"]
        for item in result["execution_bundles"]}})
    original_ledger_sha = hashlib.sha256((base / "work.sqlite").read_bytes()).hexdigest()
    inspected = []
    for item in result["execution_bundles"]:
        started = time.perf_counter()
        current = executor.preview({"bundle_id": item["bundle_id"], "entity_id": ENTITY})
        assert current["can_start"] is True and current["readonly_recovery"] is False
        assert current["API_requests"] == current["database_writes"] == 0
        rows = ExecutionGateway.inspection_work_items(current["inspection"])
        assert len(rows) == item["question_count"]
        assert all(row["status"] == "pending" for row in rows)
        inspected.append({"scope": item["subject_ref"]["scope"], "question_count": len(rows),
            "can_start": current["can_start"], "readonly_recovery": current["readonly_recovery"],
            "preview_seconds": time.perf_counter() - started})
    assert hashlib.sha256((base / "work.sqlite").read_bytes()).hexdigest() == original_ledger_sha
    report = {"status": "passed", "synthetic_engineering_only": True, "financial_accuracy_proven": False,
        "fixture_setup_seconds": gateway.fixture_setup_seconds, "bank_preview_seconds": preview_seconds,
        "apply_seconds": apply_seconds, "execution_previews": inspected, "API_requests": 0,
        "work_ledger_unchanged_by_execution_preview": True,
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (ROOT / "scripts/dashboard_prepare.py", Path(__file__))}}
    (ROOT / "runs/dashboard-prepare28-native-stage-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def test_configuration_binding_is_composable_but_binds_target_scope_policy_and_selected_profile(original):
    gateway, _, config = original
    selection = {"entity_id": ENTITY, "as_of": "2026-10-25"}
    initial = gateway._configuration_binding(selection)
    appended = copy.deepcopy(config)
    appended.update(execution_bundles={"another": {"entity_id": "ENT_ANOTHER"}}, import_bundles={"another": {}}, workspace_label="Display only")
    appended["prepare"]["routing_profiles"] = {"other": {"entity_id": "ENT_ANOTHER", "verified_facts": []}}
    assert PrepareGateway(appended)._configuration_binding(selection) == initial
    for key, value in (("workspace_root", str(ROOT)), ("iqs_release_root", str(ROOT / "runs"))):
        changed = copy.deepcopy(config); changed[key] = value
        assert PrepareGateway(changed)._configuration_binding(selection) != initial
    changed = copy.deepcopy(config); changed["prepare"]["thinking"] = False
    assert PrepareGateway(changed)._configuration_binding(selection) != initial
    changed = copy.deepcopy(appended)
    changed["prepare"]["routing_profiles"]["other"]["entity_id"] = ENTITY
    selected = {**selection, "profile_id": "other"}
    selected_hash = PrepareGateway(changed)._configuration_binding(selected)
    assert selected_hash != initial
    changed["prepare"]["routing_profiles"]["other"]["label"] = "Changed display only"
    assert PrepareGateway(changed)._configuration_binding(selected) == selected_hash
    changed["prepare"]["routing_profiles"]["other"]["verified_facts"] = [{"fact": "changed source-bound profile fact"}]
    assert PrepareGateway(changed)._configuration_binding(selected) != selected_hash


@pytest.mark.parametrize("original", [True], indirect=True)
def test_multiple_original_share_classes_require_an_exact_original_security_selection(original):
    gateway, base, _ = original
    before = tree(base / "owner")
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    assert preview["question_count"] == 36 and len(preview["available_listings"]) == 2
    assert not preview["can_apply"] and "security_selection_required" in preview["blocked_reasons"]
    secondary = "SEC_2c3b5e4f-0000-4b2c-9d3e-000000000002"
    selected = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25", "security_id": secondary})
    assert selected["can_apply"] and selected["selected_security"]["security_id"] == secondary
    candidate = Path(gateway.options["state_root"]) / "candidates" / selected["preview_id"]
    native = json.loads((candidate / "native.json").read_text(encoding="utf-8"))
    assert native["listing_binding"]["security"]["security_id"] == secondary
    with pytest.raises(DashboardPrepareError) as error:
        gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25", "security_id": "SEC_FOREIGN"})
    assert error.value.code == "security_not_registered"
    assert tree(base / "owner") == before


def test_unknown_identity_unregistered_profile_browser_paths_and_future_cutoff_are_rejected(original):
    gateway, base, _ = original
    before = tree(base / "owner")
    for request in ({"entity_id": ENTITY, "as_of": "2026-10-25", "path": "untrusted"},
                    {"entity_id": ENTITY, "as_of": "2026-10-25", "scope_as_of": "2020-01-01T00:00:00Z"},
                    {"entity_id": ENTITY, "as_of": "2026-10-25", "owner_snapshot_as_of": "2020-01-01T00:00:00Z"},
                    {"entity_id": "Company name", "as_of": "2026-10-25"},
                    {"entity_id": ENTITY, "as_of": "2999-01-01"},
                    {"entity_id": ENTITY, "as_of": "2026-10-25", "profile_id": "browser-made-up"}):
        with pytest.raises(DashboardPrepareError):
            gateway.bank_preview(request)
    assert tree(base / "owner") == before


def test_inline_secrets_are_not_inherited_and_unapplied_or_partial_queries_never_write(original, monkeypatch):
    gateway, base, _ = original
    monkeypatch.setenv("MIMO_API_KEY", "synthetic-must-not-inherit")
    assert "MIMO_API_KEY" not in _env()
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    directory = Path(gateway.options["state_root"]) / "candidates" / preview["preview_id"]
    _new(directory / "apply-started.json", {"synthetic": "interrupted-before-native-confirmation"})
    before = tree(base)
    assert gateway.preparation(preview["preview_id"])["status"] == "partial"
    with pytest.raises(DashboardPrepareError) as error:
        gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    assert error.value.code == "preparation_partial"
    assert tree(base) == before


def test_exact_token_is_checked_before_async_submit_and_other_bundles_do_not_stale_it(original):
    gateway, base, config = original
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    changed = copy.deepcopy(config)
    changed.update(execution_bundles={"another-company": {"entity_id": "ENT_ANOTHER"}})
    updated = PrepareGateway(changed)
    request = {key: preview[key] for key in ("preview_id", "preview_token")}
    before = tree(base)
    assert updated.validate_selection(request)["valid"] is True
    with pytest.raises(DashboardPrepareError) as error:
        updated.validate_selection({**request, "preview_token": "wrong"})
    assert error.value.code == "preview_stale"
    with pytest.raises(DashboardPrepareError) as error:
        updated.validate_selection({"preview_id": "prepare_" + "0" * 32, "preview_token": "unknown"})
    assert error.value.code == "preview_unknown" and error.value.status == 404
    assert tree(base) == before


def test_verified_without_subject_and_provisional_still_get_36_without_promoting_authority(original):
    gateway, base, config = original
    # Only a disposable source fixture is removed; this is never a production
    # subject deletion or a strategy for repairing missing original authority.
    subjects = base / "owner/data/quick_scan/analysis_subjects.sqlite"
    assert subjects.is_relative_to(base)
    subjects.unlink()
    before = tree(base / "owner")
    result = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    assert result["question_count"] == 36 and "subject_authority_missing" in result["blocked_reasons"]
    assert not result["can_apply"] and tree(base / "owner") == before
    source = "import sys;from pathlib import Path;sys.path[:0]=[sys.argv[1],str(Path(sys.argv[1])/'tests')];from test_identity_g2b_export import _setup;_setup(Path(sys.argv[2]))"
    provisional = base / "provisional-owner"
    done = subprocess.run([sys.executable, "-B", "-c", source, str(WIKI), str(provisional)], env=_env(), capture_output=True, timeout=30)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    changed = copy.deepcopy(config); changed["workspace_root"] = str(provisional)
    before = tree(provisional)
    result = PrepareGateway(changed).bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    assert result["question_count"] == 36 and result["bank"]["identity_state"] == "provisional"
    assert not result["can_apply"] and "route_identity_unverified" in result["blocked_reasons"]
    assert tree(provisional) == before


def test_explicit_original_issuer_bootstrap_is_readonly_until_apply_and_keeps_draft_immutable(original):
    gateway, base, _ = original
    if not (WIKI / "stockwiki/quick_scan_issuer_bootstrap.py").is_file():
        pytest.skip("Original owner issuer bootstrap is not published")
    from datetime import datetime, timezone
    cutoff = datetime.now(timezone.utc).date().isoformat()
    before = tree(base / "owner")
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": cutoff, "scope_selector": "issuer_only"})
    assert preview["question_count"] == 36 and preview["can_apply"]
    assert tree(base / "owner") == before
    directory = Path(gateway.options["state_root"]) / "candidates" / preview["preview_id"]
    draft = {name: (directory / name).read_bytes() for name in ("preview.json", "manifest.json", "route.json", "identity.json")}
    started = time.perf_counter()
    try:
        result = gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    except DashboardPrepareError as error:
        fields = {"native_module", "native_selectors", "native_returncode", "native_error_code",
                  "exception_type", "timeout_seconds", "completed_phases", "native_reason", "outcome_unknown"}
        thin = {"status": "failed", "code": error.code,
            "details": {key: value for key, value in error.details.items() if key in fields},
            "completed_phases": gateway.preparation(preview["preview_id"])["completed_phases"],
            "elapsed_apply_seconds": time.perf_counter() - started, "API_requests": 0,
            "prepare_source_sha256": hashlib.sha256((ROOT / "scripts/dashboard_prepare.py").read_bytes()).hexdigest()}
        (ROOT / "runs/dashboard-prepare28-bootstrap-stage-report.json").write_text(json.dumps(thin, indent=2), encoding="utf-8")
        pytest.fail(f"Original bootstrap chain refused: {error.code}; {thin['details']}; phases={thin['completed_phases']}")
    assert result["status"] == "prepared" and result["question_count_total"] == 36
    assert result["API_requests"] == 0 and result["dispatch_started"] is False
    assert (directory / "final/preparation-lineage.json").is_file()
    assert json.loads((directory / "bootstrap.json").read_text(encoding="utf-8"))["scope_semantics"]["consolidated_scope_verified"] is False
    assert all((directory / name).read_bytes() == raw for name, raw in draft.items())
    report = {"status": "passed", "synthetic_engineering_only": True, "financial_accuracy_proven": False,
        "apply_seconds": time.perf_counter() - started,
        "scope_question_counts": [item["question_count"] for item in result["execution_bundles"]],
        "completed_phases": gateway.preparation(preview["preview_id"])["result"]["status"],
        "API_requests": 0, "prepare_source_sha256": hashlib.sha256((ROOT / "scripts/dashboard_prepare.py").read_bytes()).hexdigest()}
    (ROOT / "runs/dashboard-prepare28-bootstrap-stage-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def test_existing_original_issuer_only_scope_retains_its_real_route_anchor(original, monkeypatch):
    gateway, base, config = original
    from datetime import datetime, timezone
    scope_as_of = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    cutoff = scope_as_of[:10]
    seed = r'''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_issuer_bootstrap import IssuerScopeBootstrap
service=IssuerScopeBootstrap(WorkspacePaths.from_root(Path(sys.argv[2])))
selection=dict(entity_id=sys.argv[3],scope_as_of=sys.argv[4],authorization_ref=sys.argv[5])
preview=service.preview(**selection)
print(json.dumps(service.apply(**selection,expected_preview_sha256=preview['preview_sha256'])))
'''
    done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", seed, str(WIKI),
        config["workspace_root"], ENTITY, scope_as_of, config["prepare"]["authorization_reference"]],
        cwd=base, env=_env(), capture_output=True, timeout=60)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    subject_key = json.loads(done.stdout)["subject_key"]
    candidate = gateway.bank_preview({"entity_id": ENTITY, "as_of": cutoff, "subject_key": subject_key})
    directory = Path(gateway.options["state_root"]) / "candidates" / candidate["preview_id"]
    activate = r'''
import json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,sys.argv[1])
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.quick_scan_routes import QuickScanRouteStore
from stockwiki.quick_scan_route_validation import IqsRouteValidator
directory=Path(sys.argv[4]);paths=WorkspacePaths.from_root(Path(sys.argv[2]))
routes=QuickScanRouteStore(QuickScanStore(paths),validator=IqsRouteValidator(Path(sys.argv[3]),runs_dir=directory/'validation',release_root=Path(sys.argv[3])))
route=json.loads((directory/'route.json').read_text(encoding='utf-8'))
routes.record_snapshot((directory/'route.json').read_bytes(),(directory/'manifest.json').read_bytes(),subject_key=sys.argv[5],expected_decision_id=route['decision_id'])
routes.set_current(route['decision_id'],subject_key=sys.argv[5],expected_current_decision_id=None,now_utc=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'))
'''
    done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", activate, str(WIKI),
        config["workspace_root"], str(ROOT), str(directory), subject_key], cwd=base, env=_env(), capture_output=True, timeout=60)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    before = tree(base / "owner")
    # The same trusted server instant resolves an already persisted scope;
    # the browser never supplies or rewrites an authority timestamp.
    monkeypatch.setattr("scripts.dashboard_prepare._now", lambda: scope_as_of)
    selected = gateway.bank_preview({"entity_id": ENTITY, "as_of": cutoff, "scope_selector": "issuer_only"})
    native = json.loads((Path(gateway.options["state_root"]) / "candidates" / selected["preview_id"] / "native.json").read_text(encoding="utf-8"))
    assert selected["can_apply"] and native["binding"]["subject_key"] == subject_key
    assert native["anchor"]["decision_id"] == json.loads((directory / "route.json").read_text(encoding="utf-8"))["decision_id"]
    assert tree(base / "owner") == before


@pytest.mark.parametrize("original", ["fresh_today"], indirect=True)
def test_current_owner_time_is_frozen_for_fresh_receipt_and_historical_answer_cutoff(original, monkeypatch):
    gateway, base, config = original
    from datetime import datetime, timezone
    before = tree(base / "owner")
    historical_cutoff = "2020-01-01"
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": historical_cutoff, "scope_selector": "issuer_only"})
    assert preview["can_apply"] and preview["bank"]["information_cutoff"] == historical_cutoff
    directory = Path(gateway.options["state_root"]) / "candidates" / preview["preview_id"]
    native = json.loads((directory / "native.json").read_text(encoding="utf-8"))
    stamp = preview["scope_as_of"]
    assert stamp == preview["owner_snapshot_as_of"] == native["scope_as_of"]
    assert stamp == native["bootstrap"]["analysis_subject"]["scope_as_of"]
    assert stamp[:10] == datetime.now(timezone.utc).date().isoformat() and stamp[:10] != historical_cutoff
    assert stamp[11:] != "00:00:00Z"
    receipt = json.loads((base / "issuer-receipt.json").read_text(encoding="utf-8"))
    assert receipt["recorded_at"][:10] == stamp[:10] and receipt["recorded_at"] <= stamp
    assert tree(base / "owner") == before
    real_worker = gateway._worker
    seen = []
    def apply_until_first_route_write(operation, payload):
        if operation == "snapshot":
            seen.append(payload)
            return real_worker(operation, payload)
        # Invoke the actual adapter and original owner bootstrap, then stop
        # before route activation/capture/consent/admission. Never fake ready.
        source = r'''
import json,sys
from pathlib import Path
request=json.load(sys.stdin);config=request['config']
sys.path[:0]=[config['stockwiki_root'],str(Path(config['iqs_root'])/'scripts')]
from dashboard_prepare import _apply
from stockwiki.quick_scan_routes import QuickScanRouteStore
class StopBeforeRoute(Exception):pass
def stop(*args,**kwargs):raise StopBeforeRoute()
def offline(event,args):
    if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}:raise RuntimeError('test_network_forbidden')
sys.addaudithook(offline)
QuickScanRouteStore.record_snapshot=stop
try:_apply(config,request['payload'])
except StopBeforeRoute:print(json.dumps({'stopped_before_route':True}))
else:raise RuntimeError('test_expected_route_boundary_stop')
'''
        done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", source],
            input=json.dumps({"config": config, "payload": payload}).encode("utf-8"),
            cwd=base, env=_env(), capture_output=True, timeout=90)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
        assert json.loads(done.stdout)["stopped_before_route"] is True
        raise DashboardPrepareError("test_stopped_before_route", "Synthetic engineering boundary stop", 409)
    monkeypatch.setattr(gateway, "_worker", apply_until_first_route_write)
    with pytest.raises(DashboardPrepareError) as error:
        gateway.apply({key: preview[key] for key in ("preview_id", "preview_token")})
    assert error.value.code == "test_stopped_before_route" and len(seen) == 1
    assert seen[0]["scope_as_of"] == seen[0]["owner_snapshot_as_of"] == stamp
    actual = json.loads((directory / "bootstrap.json").read_text(encoding="utf-8"))
    assert actual["analysis_subject"]["scope_as_of"] == stamp
    assert actual["identity_request_sha256"] == native["bootstrap"]["identity_request_sha256"]
    assert actual["network_calls"] == actual["llm_calls"] == 0
    assert gateway.preparation(preview["preview_id"])["status"] == "partial"
    assert not (directory / "scope-1-entity").exists() and not (directory / "applied.json").exists()


def test_kernel_preparation_lock_releases_after_crash_and_stale_file_is_not_authority(original):
    _, _, config = original
    path = _control_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"0")
    code = "import sys,os;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from dashboard_locks import control_lock\nwith control_lock(Path(sys.argv[2])):os._exit(71)"
    result = subprocess.run([sys.executable, "-B", "-c", code, str(ROOT / "scripts"), str(path)],
                            env=_env(), capture_output=True, timeout=15)
    assert result.returncode == 71 and path.exists()
    with _apply_guard(config, "prepare_" + "a" * 32):
        with pytest.raises(DashboardPrepareError) as error:
            with _apply_guard(config, "prepare_" + "b" * 32):
                pass
        assert error.value.code == "owner_preparation_busy"
    with _apply_guard(config, "prepare_" + "c" * 32):
        pass


def test_native_failure_diagnostics_and_timeout_bounds_do_not_expose_transport_contents(monkeypatch):
    from types import SimpleNamespace
    config = {"stockqa_root": str(QA), "prepare": {"runtime_dir": str(ROOT)}}
    assert _timeouts(config) == (900, 300)
    for worker, native in ((59, 30), (3601, 30), (900, 29), (900, 901), (60, 90), (True, 30)):
        with pytest.raises(DashboardPrepareError, match="timeout"):
            _timeouts({"prepare": {"worker_timeout_seconds": worker, "native_timeout_seconds": native}})
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("SECRET_SENTINEL", kwargs["timeout"])
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(DashboardPrepareError) as error:
        _native_cli(config, "qa", "src.utils.quick_scan_refresh_admission_cli", ["--confirmation-id", "synthetic"])
    assert error.value.code == "native_preparation_timeout_unknown"
    assert error.value.details["exception_type"] == "TimeoutExpired"
    assert error.value.details["native_selectors"] == ["--confirmation-id"]
    assert error.value.details["timeout_seconds"] == 300 and error.value.details["automatic_retry_allowed"] is False
    assert "SECRET_SENTINEL" not in str(error.value.details)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=2,
        stdout=b'{"error_code":"original_guard_rejected","untrusted":"SECRET_SENTINEL"}'))
    with pytest.raises(DashboardPrepareError) as error:
        _native_cli(config, "qa", "src.utils.quick_scan_refresh_admission_cli", ["--confirmation-id", "synthetic"])
    assert error.value.code == "original_guard_rejected" and error.value.details["native_returncode"] == 2
    assert error.value.details["native_error_code"] == "original_guard_rejected"
    assert "SECRET_SENTINEL" not in str(error.value.details)


def test_apply_timeout_persists_partial_journal_for_readonly_diagnosis_without_retry(original, monkeypatch):
    gateway, base, _ = original
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    original_worker = gateway._worker
    calls = []
    def timed(operation, payload):
        if operation != "apply":
            return original_worker(operation, payload)
        calls.append(operation)
        raise DashboardPrepareError("native_preparation_timeout_unknown", "Original native stage timed out", 504,
            {"native_module": "synthetic-stage", "exception_type": "TimeoutExpired", "timeout_seconds": 300,
             "outcome_unknown": True, "automatic_retry_allowed": False})
    monkeypatch.setattr(gateway, "_worker", timed)
    selection = {key: preview[key] for key in ("preview_id", "preview_token")}
    with pytest.raises(DashboardPrepareError) as error:
        gateway.apply(selection)
    assert error.value.code == "native_preparation_timeout_unknown"
    status = gateway.preparation(preview["preview_id"])
    assert status["status"] == "partial" and status["last_error"]["details"]["native_module"] == "synthetic-stage"
    before = tree(base)
    with pytest.raises(DashboardPrepareError) as error:
        gateway.apply(selection)
    assert error.value.code == "preparation_partial" and calls == ["apply"]
    assert tree(base) == before


def test_advanced_original_owner_dialect_is_a_preapply_gap_without_touching_original_work(original):
    gateway, base, _ = original
    policy_file = base / "owner/config/quick_scan_refresh.json"
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    assert not gateway._execution_gaps()
    data = tree(base / "owner/data")
    ledger = hashlib.sha256((base / "work.sqlite").read_bytes()).hexdigest()
    for dialect in ("1.2.0", "1.3.0", "1.4.0", "1.5.0"):
        policy["protocol"] = "stockwiki.refresh_owner_policy/" + dialect
        policy_file.write_text(json.dumps(policy), encoding="utf-8")
        assert "native_prepare_owner_dialect_not_supported" in gateway._execution_gaps()
    assert tree(base / "owner/data") == data
    assert hashlib.sha256((base / "work.sqlite").read_bytes()).hexdigest() == ledger


def test_unapplied_legacy_local_candidate_requires_new_preview_without_rebuilding_authority(original):
    gateway, base, _ = original
    preview = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    directory = Path(gateway.options["state_root"]) / "candidates" / preview["preview_id"]
    # Reconstruct only the older LOCAL UI candidate representation. This is
    # not a StockWiki receipt, confirmation, golden or admitted work record.
    native_file = directory / "native.json"
    native = json.loads(native_file.read_text(encoding="utf-8"))
    native.pop("owner_snapshot_as_of"); native.pop("scope_as_of")
    native_file.write_text(json.dumps(native), encoding="utf-8")
    record = json.loads((directory / "preview.json").read_text(encoding="utf-8"))
    record.pop("owner_snapshot_as_of"); record.pop("scope_as_of")
    record["files"]["native.json"] = hashlib.sha256(native_file.read_bytes()).hexdigest()
    record["snapshot_sha256"] = _snapshot_sha(native)
    record["preview_token"] = _sha({key: value for key, value in record.items() if key != "preview_token"})
    (directory / "preview.json").write_text(json.dumps(record), encoding="utf-8")
    before = tree(base / "owner")
    with pytest.raises(DashboardPrepareError) as error:
        gateway.validate_selection({key: record[key] for key in ("preview_id", "preview_token")})
    assert error.value.code == "preview_stale"
    with pytest.raises(DashboardPrepareError) as error:
        gateway.apply({key: record[key] for key in ("preview_id", "preview_token")})
    assert error.value.code == "preview_stale"
    assert not (directory / "apply-started.json").exists() and tree(base / "owner") == before
