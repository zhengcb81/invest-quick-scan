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


def test_frozen_bank_equivalence_ignores_only_route_clock_and_id_not_meaning():
    from scripts.dashboard_prepare import _equivalent_frozen_bank
    binding={'entity_id':ENTITY,'identity_revision':3,'perimeter_sha256':'a'*64}
    old_route={'decision_id':'old','decided_at':'2026-10-25T01:00:00Z','as_of':'2026-10-25',
        'identity_ref':'same-original-binding','profile_context':{'verified_facts':[]},'module_decisions':['common']}
    old_manifest={'questions':[{'id':'A','text':'exact','semantic_sha256':'b'*64}],
        'question_count':1,'module_locks':['original-lock'],'route_decision':old_route,
        'route_decision_id':'old','routing_execution':{'checked_at':'old','expected_decision_id':'old','allowed':True}}
    fresh_route={**old_route,'decision_id':'new','decided_at':'2026-10-26T01:00:00Z'}
    fresh={**old_manifest,'route_decision':fresh_route,'route_decision_id':'new',
        'routing_execution':{'checked_at':'new','expected_decision_id':'new','allowed':True}}
    raw=json.dumps(old_manifest).encode();route_raw=json.dumps(old_route).encode()
    snapshot={'decision_id':'old','manifest_raw':raw,'route_raw':route_raw,
        'manifest_raw_sha256':hashlib.sha256(raw).hexdigest(),'route_raw_sha256':hashlib.sha256(route_raw).hexdigest(),
        'metadata':{'binding':binding}}
    _equivalent_frozen_bank(fresh,fresh_route,snapshot,binding,snapshot['manifest_raw_sha256'])
    for kind in ['semantic','extra_question','identity','perimeter','module','as_of','facts','unknown_metadata','expected_hash']:
        manifest=copy.deepcopy(fresh)
        route=manifest['route_decision']
        snap,current=copy.deepcopy(snapshot),copy.deepcopy(binding)
        expected=snapshot['manifest_raw_sha256']
        if kind=='semantic':manifest['questions'][0]['text']='different meaning'
        elif kind=='extra_question':manifest['questions'].append({'id':'B','text':'new'});manifest['question_count']=2
        elif kind=='identity':current['identity_revision']=4
        elif kind=='perimeter':current['perimeter_sha256']='c'*64
        elif kind=='module':manifest['module_locks']=['new-lock']
        elif kind=='as_of':route['as_of']='2026-10-26'
        elif kind=='facts':route['profile_context']['verified_facts']=['different']
        elif kind=='unknown_metadata':manifest['new_contract_field']='must not be discarded'
        else:expected='f'*64
        with pytest.raises(DashboardPrepareError):
            _equivalent_frozen_bank(manifest,route,snap,current,expected)


@pytest.mark.parametrize('fault',['conflicting_hashes','invalid_hash','missing_snapshot','duplicate_snapshot','reader_unavailable','no_active_work'])
def test_reuse_requires_exact_unique_original_work_hash_and_owner_snapshot(tmp_path,monkeypatch,fault):
    from types import SimpleNamespace
    from scripts import dashboard_prepare as api
    monkeypatch.syspath_prepend(str(WIKI))
    import stockwiki.quick_scan_routes as native_routes
    binding={'entity_id':ENTITY,'subject_key':'ASJ_test@1','identity_revision':3,'perimeter_sha256':'a'*64}
    payload={'native':{'binding':binding,'selected_listing':{'security_id':'SEC_test'}},
        'manifest':{'questions':[{'id':'Q','scope':'entity'}]},'route':{'as_of':'2026-10-25'}}
    hashes=['b'*64]
    if fault=='conflicting_hashes':hashes.append('c'*64)
    elif fault=='invalid_hash':hashes=['not-a-sha']
    elif fault=='no_active_work':hashes=[]
    rows=[{'manifest_raw_sha256':h} for h in hashes]
    response={'protocol':'iqs.original_work_bank_bindings/1.0.0','rows':rows,'API_requests':0,'database_writes':0}
    monkeypatch.setattr(api.subprocess,'run',lambda *args,**kwargs:SimpleNamespace(returncode=2 if fault=='reader_unavailable' else 0,stdout=json.dumps(response).encode()))
    snapshots=[] if fault!='duplicate_snapshot' else [{'decision_id':'route_a','manifest_raw_sha256':'b'*64},{'decision_id':'route_b','manifest_raw_sha256':'b'*64}]
    fake=SimpleNamespace(identity_binding=lambda _:binding,snapshots_for_subject=lambda _:snapshots)
    monkeypatch.setattr(native_routes,'QuickScanRouteStore',lambda *args,**kwargs:fake)
    config={'stockqa_root':str(QA),'workspace_root':str(tmp_path),'iqs_root':str(ROOT),
        'prepare':{'admission_config':str(tmp_path/'admission.json'),'state_root':str(tmp_path/'state')}}
    if fault=='no_active_work':
        assert api._reusable_bank(config,payload) is None
    else:
        with pytest.raises(DashboardPrepareError):api._reusable_bank(config,payload)

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
if sys.argv[3]=='revision_2':
    entity['identity_revision']=2
if sys.argv[3] in {'compact', 'null_country'}:
    # Real owner lexical dialect, synthetic issuer/evidence only. The compact
    # spelling is intentionally not a UUIDv4; source-master hashes also occur.
    ref='BIND_bdcbad655ea67df3f9ded4c9b1bf836a'
    entity['securities'][0]['source_binding_ref']=ref
    bindings[0]['binding_ref']=ref
if sys.argv[3]=='null_country':
    entity['incorporation_country']=None
if sys.argv[3]=='multi':
    secondary=dict(entity['securities'][0],security_id='SEC_2c3b5e4f-0000-4b2c-9d3e-000000000002',ticker='ACMB',source_binding_ref='BND_fixture_acme_2')
    entity['securities'].append(secondary)
    bindings.append(dict(bindings[0],security_id=secondary['security_id'],ticker=secondary['ticker'],binding_ref=secondary['source_binding_ref'],source_record_id='urn:company-wiki:source:fixture-acme-class-b'))
partial={'kind':'verified_issuer','receipt_id':entity['verified_issuer_receipt_id'],
'entity_id':entity['entity_id'],'identity_revision':entity['identity_revision'],'recorded_at':recorded_at,
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
                               getattr(request, "param", None) if getattr(request, "param", None) in
                               {"fresh_today", "compact", "null_country", "revision_2"} else "single"],
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


@pytest.mark.parametrize("original", ["compact"], indirect=True)
def test_snapshot_accepts_native_compact_g2b_without_rewriting_identity_or_historical_contracts(original):
    from scripts import contract_validation as cv
    gateway, base, _ = original
    historical_files = [ROOT / "schemas/quick_scan/identity.schema.json",
                        ROOT / "schemas/quick_scan/identity-wire-profile.schema.json"]
    historical = {str(path): path.read_bytes() for path in historical_files}
    legacy_schema = copy.deepcopy(cv.IDENTITY_SCHEMA)
    before = tree(base / "owner")
    native = gateway._worker("snapshot", {"entity_id": ENTITY, "owner_snapshot_as_of": "2026-10-25T00:00:00Z",
        "scope_as_of": None, "scope_selector": "existing"})
    request, context = native["identity"], native["identity"]["trusted_context"]
    cv.validate_entity(request["payload"], trusted_identity_receipts=context["identity_receipts"],
        trusted_source_bindings=context["source_bindings"], trusted_market_registry=context["market_registry"],
        wire_profile="stockwiki-g2b/1.1.0")
    ref = "BIND_bdcbad655ea67df3f9ded4c9b1bf836a"
    assert native["selected_listing"]["source_binding_ref"] == ref
    assert list(context["source_bindings"]) == [ref]
    assert set(native) == {"identity", "subjects", "binding", "anchor", "subject_gap", "bootstrap",
        "owner_snapshot_as_of", "scope_as_of", "selected_listing", "listing_binding"}
    # New read-profile support must not mutate frozen schemas or relax the
    # legacy/default and 1.0 validation of this same native compact payload.
    for profile in (None, "stockwiki-g2b/1.0.0"):
        with pytest.raises((ValueError, cv.JsonSchemaValidationError)):
            cv.validate_entity(request["payload"], trusted_identity_receipts=context["identity_receipts"],
                trusted_source_bindings=context["source_bindings"], trusted_market_registry=context["market_registry"],
                wire_profile=profile)
    assert cv.IDENTITY_SCHEMA == legacy_schema
    assert {str(path): path.read_bytes() for path in historical_files} == historical
    assert tree(base / "owner") == before


@pytest.mark.parametrize("original", ["null_country"], indirect=True)
def test_native_verified_missing_country_is_refused_before_route_and_without_owner_writes(original, monkeypatch):
    gateway, base, _ = original
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import routing
    routes = []
    def route_must_not_run(*args, **kwargs):
        routes.append(True)
        raise AssertionError("Invalid native identity reached question routing")
    monkeypatch.setattr(routing, "resolve_route_decision", route_must_not_run)
    before = tree(base / "owner")
    ledger = (base / "work.sqlite").read_bytes()
    with pytest.raises(DashboardPrepareError) as error:
        gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    assert error.value.code == "owner_identity_contract_invalid"
    assert "original identity attributes" in error.value.message
    assert error.value.details["required_action"] == "repair_original_identity_and_create_new_preview"
    assert routes == [] and not Path(gateway.options["state_root"]).exists()
    assert tree(base / "owner") == before and (base / "work.sqlite").read_bytes() == ledger


@pytest.mark.parametrize("original", ["compact"], indirect=True)
def test_snapshot_maps_native_contract_shape_and_semantic_failures_to_stable_repair_action(original, monkeypatch):
    from scripts.dashboard_prepare import _snapshot
    gateway, base, config = original
    selection = {"entity_id": ENTITY, "owner_snapshot_as_of": "2026-10-25T00:00:00Z",
                 "scope_as_of": None, "scope_selector": "existing"}
    # Start with a genuine owner-serialized DTO. Only corrupted transport
    # copies below are injected; no store, receipt or authority is repaired.
    native = gateway._worker("snapshot", selection)["identity"]
    monkeypatch.syspath_prepend(str(WIKI))
    import stockwiki.identity_g2b as g2b
    import stockwiki.identity_snapshot as owner_snapshot
    def selection_must_not_run(*args, **kwargs):
        raise AssertionError("Invalid contract reached original listing selection")
    monkeypatch.setattr(owner_snapshot, "resolve_listing_binding", selection_must_not_run)
    malformed = copy.deepcopy(native)
    malformed["trusted_context"].pop("source_bindings")
    mismatched = copy.deepcopy(native)
    receipt = next(iter(mismatched["trusted_context"]["identity_receipts"].values()))
    receipt["identity_revision"] += 1
    unregistered_mic = copy.deepcopy(native)
    unregistered_mic["trusted_context"]["market_registry"] = {"US": ["XHKG"]}
    before = tree(base / "owner")
    for invalid in (malformed, mismatched, unregistered_mic):
        frozen = copy.deepcopy(invalid)
        monkeypatch.setattr(g2b, "build_identity_request", lambda *args, **kwargs: invalid)
        with pytest.raises(DashboardPrepareError) as error:
            _snapshot(config, selection)
        assert error.value.code == "owner_identity_contract_invalid" and error.value.status == 409
        assert error.value.details == {"required_action": "repair_original_identity_and_create_new_preview"}
        assert invalid == frozen and tree(base / "owner") == before


@pytest.mark.parametrize("original", ["revision_2"], indirect=True)
def test_original_identity_revision_refresh_keeps_subject_and_history_and_uses_original_cas(original):
    gateway, base, config = original
    subject_key = "ASJ_33333333-3333-4333-8333-333333333333@1"
    source = r'''
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path[:0]=[sys.argv[1],str(Path(sys.argv[1])/'tests')]
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.identity_import import import_entity
from stockwiki.identity_receipts import IdentityReceiptStore
from stockwiki.quick_scan_routes import QuickScanRouteStore
from stockwiki.quick_scan_route_validation import IqsRouteValidator,RouteStoreError
from test_identity_g2b_export import _binding
request=json.loads(sys.stdin.buffer.read())
paths=WorkspacePaths.from_root(Path(request['workspace']))
identity=QuickScanStore(paths)
routes=QuickScanRouteStore(identity,validator=IqsRouteValidator(Path(sys.argv[2]),runs_dir=Path(request['runs']),release_root=Path(sys.argv[2])))
now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
before=hashlib.sha256(identity.database_path.read_bytes()).hexdigest()
if request['operation']=='upgrade':
    entity=identity.get_entity(request['entity_id'])
    assert entity['identity_revision']==2
    entity['identity_revision']=3;entity['verified_issuer_receipt_id']='IVR_fixture_revision_3'
    receipt={'kind':'verified_issuer','receipt_id':entity['verified_issuer_receipt_id'],'entity_id':entity['entity_id'],
        'identity_revision':3,'recorded_at':now,'same_legal_issuer':True,'evidence_ref':'https://example.invalid/reviewed-revision-3'}
    imported=import_entity(identity,IdentityReceiptStore(paths),{'entity':entity,'source_bindings':[_binding()],'issuer_receipt':receipt},at=now)
    assert imported['receipt_recorded'],imported
    try:
        routes.get_for_execution(subject_key=request['subject_key'],scope='entity',scope_id=entity['entity_id'],now_utc=now)
    except RouteStoreError as exc:
        result={'old_execution_refused':exc.code}
    else:
        raise AssertionError('Stale identity route became executable')
else:
    directory=Path(request['directory']);route=json.loads((directory/'route.json').read_text(encoding='utf-8'))
    routes.record_snapshot((directory/'route.json').read_bytes(),(directory/'manifest.json').read_bytes(),
        subject_key=request['subject_key'],expected_decision_id=route['decision_id'])
    try:
        result=routes.set_current(route['decision_id'],subject_key=request['subject_key'],
            expected_current_decision_id=request['expected_current'],now_utc=now)
    except RouteStoreError as exc:
        result={'error_code':exc.code,'identity_database_unchanged':hashlib.sha256(identity.database_path.read_bytes()).hexdigest()==before}
binding=routes.identity_binding(request['subject_key'])
result.update(binding={k:binding[k] for k in ('subject_key','identity_revision','perimeter_sha256','route_identity_ref')},
    snapshots={row['decision_id']:{k:row[k] for k in ('route_raw_sha256','manifest_raw_sha256','metadata_sha256')}
        for row in routes.snapshots_for_subject(request['subject_key'])})
print(json.dumps(result))
'''
    def original_route(operation, directory=None, expected_current=None):
        request = {"operation": operation, "workspace": config["workspace_root"], "entity_id": ENTITY,
            "subject_key": subject_key, "runs": str(base / "route-validation"),
            "directory": str(directory) if directory else None, "expected_current": expected_current}
        done = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", source, str(WIKI), str(ROOT)],
            cwd=base, env=_env(), input=json.dumps(request).encode("utf-8"), capture_output=True, timeout=90)
        assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
        return json.loads(done.stdout)
    first = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    first_dir = Path(gateway.options["state_root"]) / "candidates" / first["preview_id"]
    old = original_route("activate", first_dir)
    assert old["status"] == "activated" and old["binding"]["identity_revision"] == 2
    upgrade = original_route("upgrade")
    assert upgrade["old_execution_refused"] == "route_identity_changed"
    before = tree(base / "owner")
    refreshed = gateway.bank_preview({"entity_id": ENTITY, "as_of": "2026-10-25"})
    assert refreshed["can_apply"] and tree(base / "owner") == before
    new_dir = Path(gateway.options["state_root"]) / "candidates" / refreshed["preview_id"]
    native = json.loads((new_dir / "native.json").read_text(encoding="utf-8"))
    assert native["binding"]["identity_revision"] == 3
    assert native["binding"]["subject_key"] == old["binding"]["subject_key"] == subject_key
    assert native["binding"]["perimeter_sha256"] == old["binding"]["perimeter_sha256"]
    assert native["anchor"] == {"decision_id": old["decision_id"], "anchor_version": 1}
    current = original_route("activate", new_dir, old["decision_id"])
    assert current["status"] == "activated" and current["version"] == 2
    assert current["binding"] == upgrade["binding"]
    assert current["snapshots"][old["decision_id"]] == old["snapshots"][old["decision_id"]]
    # A competing session already changed current. Even the same fresh
    # candidate cannot bypass the original expected-current CAS comparison.
    conflict = original_route("activate", new_dir, old["decision_id"])
    assert conflict["error_code"] == "route_current_conflict" and conflict["identity_database_unchanged"]
    assert conflict["snapshots"] == current["snapshots"]


def test_preview_route_rebind_rejects_invalid_original_history_and_snapshot_shapes():
    from types import SimpleNamespace
    from scripts.dashboard_prepare import _preview_route_anchor
    subject = "ASJ_33333333-3333-4333-8333-333333333333@1"
    decision = "route_" + "a" * 64
    row = {"subject_key": subject, "scope": "entity", "scope_id": ENTITY, "version": 1,
           "decision_id": decision, "previous_decision_id": None}
    snapshot = {"decision_id": decision, "subject_key": subject, "scope": "entity", "scope_id": ENTITY, "entity_id": ENTITY}
    def stale(**kwargs):
        raise DashboardPrepareError("route_identity_changed", "Synthetic stale original route")
    bad_histories = [None, [], [None], [dict(row, version=True)], [dict(row, version=2)],
        [dict(row, subject_key="ASJ_OTHER@1")], [dict(row, scope_id="ENT_OTHER")], [dict(row, scope="segment")],
        [dict(row, decision_id="../route_" + "a" * 64)], [dict(row, previous_decision_id=decision)],
        [row, dict(row, version=2, decision_id="route_" + "b" * 64, previous_decision_id=None)]]
    bad_snapshots = [None, {}, dict(snapshot, decision_id="route_" + "b" * 64),
        dict(snapshot, subject_key="ASJ_OTHER@1"), dict(snapshot, entity_id="ENT_OTHER"), dict(snapshot, scope="segment")]
    for history, candidate in [(item, snapshot) for item in bad_histories] + [([row], item) for item in bad_snapshots]:
        routes = SimpleNamespace(get_current_anchor=stale, current_history=lambda **kwargs: history,
            get_snapshot=lambda expected: candidate)
        with pytest.raises(DashboardPrepareError) as error:
            _preview_route_anchor(routes, subject_key=subject, entity_id=ENTITY, now_utc="2026-10-25T00:00:00Z")
        assert error.value.code == "owner_route_rebind_unavailable"


def test_preview_route_anchor_preserves_non_identity_refusals_and_never_grants_execution():
    from types import SimpleNamespace
    from scripts.dashboard_prepare import _preview_route_anchor
    subject = "ASJ_33333333-3333-4333-8333-333333333333@1"
    def unexpected(*args, **kwargs):
        raise AssertionError("Unexpected history, snapshot or execution call")
    routes = SimpleNamespace(get_current_anchor=lambda **kwargs: {"expected_decision_id": "route_" + "a" * 64, "anchor_version": 2},
        current_history=unexpected, get_snapshot=unexpected, get_for_execution=unexpected)
    selection = {"subject_key": subject, "entity_id": ENTITY, "now_utc": "2026-10-25T00:00:00Z"}
    assert _preview_route_anchor(routes, **selection) == {"decision_id": "route_" + "a" * 64, "anchor_version": 2}
    for code in ("route_current_unavailable", "route_current_corrupted", "route_snapshot_corrupted", "route_time_before_activation", "unknown_guard"):
        refusal = DashboardPrepareError(code, "Synthetic original refusal")
        def original_refusal(**kwargs):
            raise refusal
        routes.get_current_anchor = original_refusal
        if code == "route_current_unavailable":
            assert _preview_route_anchor(routes, **selection) is None
        else:
            with pytest.raises(DashboardPrepareError) as error:
                _preview_route_anchor(routes, **selection)
            assert error.value is refusal
    routes.get_current_anchor = lambda **kwargs: (_ for _ in ()).throw(DashboardPrepareError("route_identity_changed", "Synthetic"))
    routes.current_history = lambda **kwargs: [{"subject_key": subject, "scope": "entity", "scope_id": ENTITY, "version": 1,
        "decision_id": "route_" + "a" * 64, "previous_decision_id": None}]
    damaged = DashboardPrepareError("route_snapshot_corrupted", "Synthetic original hash guard")
    def corrupted_snapshot(expected):
        raise damaged
    routes.get_snapshot = corrupted_snapshot
    with pytest.raises(DashboardPrepareError) as error:
        _preview_route_anchor(routes, **selection)
    assert error.value is damaged


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


def test_fresh_preparation_reuses_exact_original_work_bank_after_current_route_churn(original):
    gateway, base, config = original
    selection={'entity_id':ENTITY,'as_of':'2026-10-25','mode':'quick'}
    first=gateway.bank_preview(selection)
    initial=gateway.apply({k:first[k] for k in ('preview_id','preview_token')})
    first_dir=Path(gateway.options['state_root'])/'candidates'/first['preview_id']
    original_manifest=(first_dir/'manifest.json').read_bytes()
    original_route=json.loads((first_dir/'route.json').read_text())
    repeated=gateway.bank_preview(selection)
    assert repeated['bank_reuse']['decision_id']==original_route['decision_id']
    assert repeated['bank_reuse']['work_count']==36
    # Simulate the earlier product bug using only ORIGINAL route record/CAS.
    # This preserves a real newer current snapshot/history, not hand-written SQL.
    proposed=Path(gateway.options['state_root'])/'candidates'/repeated['preview_id']/'proposed-bank'
    source=r'''
import json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,sys.argv[1])
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.quick_scan_routes import QuickScanRouteStore
from stockwiki.quick_scan_route_validation import IqsRouteValidator
r=json.load(sys.stdin);paths=WorkspacePaths.from_root(Path(r['workspace']))
routes=QuickScanRouteStore(QuickScanStore(paths),validator=IqsRouteValidator(Path(sys.argv[2]),runs_dir=Path(r['runs']),release_root=Path(sys.argv[2])))
subject=r['subject_key'];now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
if r['operation']=='activate':
 d=Path(r['directory']);route=json.loads((d/'route.json').read_text())
 routes.record_snapshot((d/'route.json').read_bytes(),(d/'manifest.json').read_bytes(),subject_key=subject,expected_decision_id=route['decision_id'])
 result=routes.set_current(route['decision_id'],subject_key=subject,expected_current_decision_id=r['expected'],now_utc=now)
else:
 current=routes.get_for_execution(subject_key=subject,scope='entity',scope_id=r['entity_id'],now_utc=now)
 result={'decision_id':current['expected_decision_id'],'history':[x['decision_id'] for x in routes.current_history(subject_key=subject,scope='entity',scope_id=r['entity_id'])]}
print(json.dumps(result))
'''
    def owner(operation,**extra):
        request={'operation':operation,'workspace':config['workspace_root'],
            'subject_key':first['selected_subject']['key'],'entity_id':ENTITY,'runs':str(base/'reuse-native-validation'),**extra}
        done=subprocess.run([sys.executable,'-B','-X','utf8','-c',source,str(WIKI),str(ROOT)],
            input=json.dumps(request).encode(),cwd=base,env=_env(),capture_output=True,timeout=90)
        assert done.returncode==0,done.stderr.decode('utf-8','replace')
        return json.loads(done.stdout)
    churn=owner('activate',directory=str(proposed),expected=original_route['decision_id'])
    assert churn['decision_id']!=original_route['decision_id']
    fresh=gateway.bank_preview(selection)
    fresh_dir=Path(gateway.options['state_root'])/'candidates'/fresh['preview_id']
    assert fresh['bank_reuse']['decision_id']==original_route['decision_id']
    assert (fresh_dir/'manifest.json').read_bytes()==original_manifest
    final=gateway.apply({k:fresh[k] for k in ('preview_id','preview_token')})
    ids=lambda result: sorted(x['work_item_id'] for group in result['execution_bundles'] for x in group['admission']['registration']['items'])
    assert ids(final)==ids(initial) and len(ids(final))==36
    current=owner('read')
    assert current['history']==[original_route['decision_id'],churn['decision_id'],original_route['decision_id']]
    assert current['decision_id']==original_route['decision_id']
    check=r'''
import contextlib,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1]);bundles=json.load(sys.stdin)
with contextlib.redirect_stdout(sys.stderr):
 from src.utils.quick_scan_refresh_execution import prepare_execution
 results=[]
 for b in bundles:
  paths={k:b[v] for k,v in {'manifest.json':'manifest','identity.json':'identity_snapshot','authority.json':'c06_authority','owner-config.json':'owner_config','questions.json':'questions'}.items()}
  session=prepare_execution(b['admission_config'],b['confirmation_id'],input_paths=paths)
  results.append({'scope':b['scope'],'count':len(session.entries),'all_original_pending':all(w['status']=='pending' for w in session.work.values()),'API_requests':0})
print(json.dumps(results))
'''
    before=(base/'work.sqlite').read_bytes()
    checked=subprocess.run([sys.executable,'-B','-X','utf8','-c',check,str(QA)],
        input=json.dumps([x['execution_bundle'] for x in final['execution_bundles']]).encode(),
        cwd=base/'runtime',env=_env(),capture_output=True,timeout=180)
    assert checked.returncode==0,checked.stderr.decode('utf-8','replace')
    scopes=json.loads(checked.stdout)
    assert [(x['scope'],x['count']) for x in scopes]==[('entity',33),('security',3)]
    assert all(x['all_original_pending'] and x['API_requests']==0 for x in scopes)
    assert (base/'work.sqlite').read_bytes()==before


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
        expected = "recovery_policy_refs_required" if dialect == "1.2.0" else "native_prepare_owner_dialect_not_supported"
        assert expected in gateway._execution_gaps()
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
