"""Prepare company banks through original owner interfaces, without model calls.

Bank preview writes only immutable IQS candidates. Explicit apply records the
original owner route/capture/consent and admits it to StockQA's existing ledger.
It never fabricates identity/scope authority or creates a budget, model client or
work queue. Explicit issuer-only apply uses the original owner bootstrap API.
"""
from __future__ import annotations

from iqs_scan import REPO_ROOT

import copy
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid

from .dashboard_json import decode_owner_json

ROOT = REPO_ROOT
DEFAULT_PACKAGE = "pkg_0151a1e3b23fe462476b1d7329211d8887a79c161eb765a1e64c7dcda1b60d9a"
PROTOCOL = "iqs.dashboard-preparation/1.0.0"
MAX_BYTES = 16 * 1024 * 1024
_OWNER_COMMAND = "stockwiki.quick_scan_prepare_cli"
_OWNER_REQUEST = "stockwiki.quick_scan_prepare_request/1.0.0"
_OWNER_REPLY = "stockwiki.quick_scan_prepare_reply/1.0.0"


class DashboardPrepareError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.details = details or {}


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _snapshot_sha(value):
    material = copy.deepcopy(value)
    # The original resolver independently checks CURRENT validity on both
    # reads. Its wall-clock read timestamp is provenance, not mutable identity.
    # Keep all listing/source validity intervals and all original bytes frozen.
    if isinstance(material.get("listing_binding"), dict):
        material["listing_binding"].pop("as_of", None)
    return _sha(material)


def _read(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_BYTES:
        raise DashboardPrepareError("input_too_large", "Preparation input exceeds its limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def _new(path, value):
    return _new_raw(path, _bytes(value) + b"\n")


def _new_raw(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != raw:
            raise DashboardPrepareError("immutable_input_conflict", "An immutable preparation input already exists", 409)


def _env():
    value = {key: val for key, val in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE", "TEMP", "TMP", "TMPDIR"}}
    value.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return value


def parse_recovery_refs(options):
    """Validate the optional recovery selection and return detached references."""
    if "recovery_work_decision_refs" not in options:
        return None
    refs = options["recovery_work_decision_refs"]
    if not isinstance(refs, list) or not 1 <= len(refs) <= 500:
        raise DashboardPrepareError("recovery_refs_invalid", "Recovery needs exact original work-decision references", 409)
    seen = set()
    for row in refs:
        if (not isinstance(row, dict) or set(row) != {"work_item_id", "decision_id"}
            or re.fullmatch(r"WORK_[a-f0-9]{32}", str(row.get("work_item_id", ""))) is None
            or re.fullmatch(r"owd1_[a-f0-9]{64}", str(row.get("decision_id", ""))) is None
            or row["work_item_id"] in seen):
            raise DashboardPrepareError("recovery_refs_invalid", "Recovery references must be exact and unique", 409)
        seen.add(row["work_item_id"])
    return copy.deepcopy(refs)


def _ordered_route_targets(policy):
    """Use the original explicit owner choice; older approvals stay single-model."""
    if policy.get("protocol") != "stockwiki.refresh_owner_policy/1.6.0":
        return None
    try:
        # IQS's original contract modules import their peers as CLI modules.
        # Support both dashboard package imports and the existing worker CLI.
        from iqs_scan.query.api import validate_route_targets
        targets = validate_route_targets(policy.get("ordered_route_targets"),
                                         provider=policy["provider"], model=policy["model"])
        if any(targets[0][key] != policy["qa"][key]
               for key in ("route_id", "provider_config_ref")):
            raise ValueError("refresh_ordered_primary_mismatch")
    except (KeyError, TypeError, ValueError) as error:
        raise DashboardPrepareError("native_prepare_owner_policy_invalid",
                                    "Original owner model order is invalid", 409) from error
    return targets


def _recovery_subset(config, directory, manifest, native, policy):
    refs = parse_recovery_refs(config.get("prepare", {}))
    dialect = policy["protocol"].split("/")[-1]
    if refs is None and dialect in {"1.0.0", "1.1.0", "1.6.0"}:
        return None
    if refs is None or dialect not in {"1.2.0", "1.3.0"}:
        raise DashboardPrepareError("recovery_policy_refs_required", "Explicit controlled policy and original finite retry references must be selected together", 409)
    admission = _read(config["prepare"]["admission_config"])
    entity = native["binding"]["entity_id"]
    selected = native["selected_listing"]["security_id"]
    scopes = {q["id"]: {"scope": q["scope"], "scope_id": selected if q["scope"] == "security" else entity} for q in manifest["questions"]}
    query = {"entity_id": entity, "question_ids": list(scopes), "scope_bindings": scopes}
    path = directory / "recovery-projection-request.json"
    _new(path, query)
    projection = _native_cli(config, "qa", "src.utils.quick_scan_work_decision_inspect_cli", [
        "--ledger", admission["work_store"], "--policy", admission["budget_policy_file"], "--owner-controls", str(path)])
    if (projection.get("protocol") != "stockqa.owner_control_projection/1.0.0"
        or projection.get("entity_id") != entity or projection.get("authority") != "original_journal_read_not_permission"
        or type(projection.get("API_requests")) is not int or projection["API_requests"] != 0
        or type(projection.get("database_writes")) is not int or projection["database_writes"] != 0
        or not isinstance(projection.get("rows"), dict)):
        raise DashboardPrepareError("recovery_projection_invalid", "Original read-only recovery projection is unavailable", 409)
    by_work = {row["work_item_id"]: (qid, row) for qid, row in projection["rows"].items() if isinstance(row, dict) and isinstance(row.get("work_item_id"), str)}
    items = []
    purposes = set()
    eligible_states = ({"comparison": {"result_ready", "delivered"}} if dialect == "1.3.0" else
                       {"retry_unusable_checkpoint": {"result_ready"}, "retry_unusable_answer": {"failed"}})
    for ref in refs:
        match = by_work.get(ref["work_item_id"])
        if match is None:
            continue  # Explicit global references may include another company.
        qid, row = match
        if (qid not in scopes or row.get("retry_decision_id") != ref["decision_id"]
            or not isinstance(row.get("retry_purpose"), str) or row.get("retry_purpose") not in eligible_states
            or not isinstance(row.get("status"), str)
            or row.get("status") not in eligible_states.get(row.get("retry_purpose"), set())
            or type(row.get("generation")) is not int or row["generation"] < 1
            or type(row.get("target_generation")) is not int or row["target_generation"] != row["generation"] + 1
            or row.get("delivery_required") is not False):
            raise DashboardPrepareError("recovery_source_changed", "An exact original finite retry decision no longer matches", 409)
        purposes.add(row["retry_purpose"])
        items.append({"question_id": qid, **ref, "source_generation": row["generation"], "target_generation": row["target_generation"], "purpose": row["retry_purpose"]})
    if not items:
        raise DashboardPrepareError("recovery_source_missing", "No selected original recovery decision belongs to this exact company and bank", 409)
    items.sort(key=lambda row: row["question_id"])
    legacy = purposes == {"retry_unusable_checkpoint"}
    if legacy:
        for item in items:
            item.pop("purpose")
    return {"protocol": "iqs.dashboard-recovery-subset/" + ("1.0.0" if legacy else "1.1.0"),
        "purpose": "retry_unusable_checkpoint" if legacy else "native_controlled_retry",
        "execution_question_ids": [row["question_id"] for row in items], "execution_question_count": len(items),
        "full_bank_question_count": len(manifest["questions"]), "items": items}


def _delegation_ttl_seconds(config):
    """Duration for a NEW exact-scope native grant; never renew an old one."""
    value = config.get('prepare', {}).get('delegation_ttl_seconds', 3600)
    if type(value) is not int or not 900 <= value <= 86400:
        raise DashboardPrepareError('preparation_delegation_duration_invalid',
            'Use a finite native grant duration of 900–86400 seconds', 503)
    return value


def _timeouts(config):
    _delegation_ttl_seconds(config)
    options = config.get("prepare", {})
    if 'work_lease_seconds' in options and (type(options['work_lease_seconds']) is not int
            or not 1 <= options['work_lease_seconds'] <= 86400):
        raise DashboardPrepareError('preparation_work_lease_invalid',
            'New work leases require 1–86400 integer seconds; existing leases are never renewed', 503)
    worker = options.get("worker_timeout_seconds", 900)
    native = options.get("native_timeout_seconds", 300)
    if (type(worker) is not int or not 60 <= worker <= 3600 or
            type(native) is not int or not 30 <= native <= 900 or native > worker):
        raise DashboardPrepareError("preparation_timeouts_invalid",
            "Use worker timeout 60–3600s, native timeout 30–900s, native no greater than worker", 503)
    return worker, native


def _read_continuation_bank(config, binding, *, admission_config=None, ledger=None):
    if (admission_config is None) == (ledger is None):
        raise ValueError('exactly_one_original_bank_selector_required')
    selector = ('--ledger', ledger) if admission_config is None else ('--admission-config', admission_config)
    command = [config.get('stockqa_python') or sys.executable, '-B', '-X', 'utf8', '-m',
               'src.utils.quick_scan_continuation_bank_cli', selector[0], str(selector[1])]
    done = subprocess.run(command, input=_bytes({
        'protocol': 'stockqa.continuation_bank_request/1.0.0', 'binding': binding,
    }), capture_output=True, env=_env(), cwd=config['stockqa_root'],
        timeout=_timeouts(config)[1], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if done.returncode or len(done.stdout) > MAX_BYTES:
        raise ValueError('invalid_original_binding_read')
    result = decode_owner_json(done.stdout)
    if (not isinstance(result, dict) or result.get('protocol') != 'iqs.original_work_bank_bindings/1.0.0'
        or any(type(result.get(counter)) is not int or result[counter] != 0
               for counter in ('API_requests', 'database_writes'))
        or not isinstance(result.get('rows'), list)
        or not all(isinstance(row, dict) for row in result['rows'])):
        raise ValueError('invalid_original_binding_read')
    return result['rows']


def _equivalent_frozen_bank(manifest, route, snapshot, binding, expected_hash):
    """Exact original bytes plus a closed comparison of routing-only volatility.

    This proves candidate equivalence, not execution permission. Original owner
    validation and current-anchor CAS still run before original admission.
    """
    invalid = DashboardPrepareError("existing_work_bank_changed",
        "Unfinished original work requires its exact frozen bank; inspect the original work instead of rebinding it", 409)
    try:
        raw, route_raw = snapshot['manifest_raw'], snapshot['route_raw']
        old, old_route = json.loads(raw), json.loads(route_raw)
        if (hashlib.sha256(raw).hexdigest() != expected_hash
            or snapshot['manifest_raw_sha256'] != expected_hash
            or hashlib.sha256(route_raw).hexdigest() != snapshot['route_raw_sha256']
            or _bytes(snapshot['metadata']['binding']) != _bytes(binding)
            or old['route_decision'] != old_route
            or old['route_decision_id'] != snapshot['decision_id']
            or old_route['decision_id'] != snapshot['decision_id']
            or manifest['route_decision'] != route or manifest['route_decision_id'] != route['decision_id']):
            raise invalid
        def without(value, keys):
            return {k:v for k,v in value.items() if k not in keys}
        if (_bytes(without(old, {'route_decision','route_decision_id','routing_execution'}))
            != _bytes(without(manifest, {'route_decision','route_decision_id','routing_execution'}))
            or _bytes(without(old_route, {'decision_id','decided_at'}))
            != _bytes(without(route, {'decision_id','decided_at'}))
            or _bytes(without(old['routing_execution'], {'checked_at','expected_decision_id'}))
            != _bytes(without(manifest['routing_execution'], {'checked_at','expected_decision_id'}))):
            raise invalid
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, DashboardPrepareError):
            raise
        raise invalid from error


def _reusable_bank(config, payload):
    """Only original active-work hashes select a unique original owner snapshot."""
    native, manifest, route = payload['native'], payload['manifest'], payload['route']
    binding = native['binding']
    scopes = {}
    for q in manifest['questions']:
        scope = q['scope']
        if scope not in {'entity','security'}:
            raise DashboardPrepareError('existing_work_scope_not_supported','Original scope requires explicit preparation',409)
        scopes[q['id']] = {'scope':scope,'scope_id':binding['entity_id'] if scope=='entity' else native['selected_listing']['security_id']}
    request = {k:binding[k] for k in ('entity_id','subject_key','perimeter_sha256','identity_revision')}
    request.update(information_cutoff=route['as_of'],scope_bindings=scopes)
    refs = parse_recovery_refs(config.get("prepare", {}))
    if refs is not None:
        request['controlled_work_refs'] = refs
    try:
        rows = _read_continuation_bank(config, request, admission_config=config['prepare']['admission_config'])
    except (OSError,ValueError,subprocess.TimeoutExpired) as error:
        raise DashboardPrepareError('existing_work_binding_unavailable',
            'Original unfinished-work bindings are unavailable; inspect the owner before preparing',409) from error
    if not rows:
        return None
    hashes={row.get('manifest_raw_sha256') for row in rows}
    if len(hashes)!=1 or any(not isinstance(h,str) or re.fullmatch('[a-f0-9]{64}',h) is None for h in hashes):
        raise DashboardPrepareError('existing_work_manifest_conflict','Original active work requires incompatible frozen banks',409)
    expected_hash=next(iter(hashes))
    found = _owner_prepare(config, 'frozen_bank', {'binding':binding,'manifest_sha256':expected_hash,'now_utc':_now()})
    snapshot = _snapshot_bytes(found['snapshot'])
    _equivalent_frozen_bank(manifest,route,snapshot,binding,expected_hash)
    if 'validation_error' in found:
        _raise_owner_prepare_error(found['validation_error'])
    if found.get('authorized') is not True:
        raise DashboardPrepareError('existing_work_route_not_executable','Original route cannot currently be executed',409)
    return {'decision_id':snapshot['decision_id'],'manifest_raw_sha256':expected_hash,
        'route_raw_sha256':snapshot['route_raw_sha256'],'work_bindings_sha256':_sha(rows),
        'work_count':len(rows),'manifest_raw':snapshot['manifest_raw'].decode('utf-8'),
        'route_raw':snapshot['route_raw'].decode('utf-8')}


def _cached_scope_result(owner_state, questions, subject_ref, *, cache_clock="information_as_of"):
    """Only native all-reuse decisions are a zero-dispatch completion."""
    quote=owner_state.get('quote',{})
    if any(type(quote.get(key)) is not int or quote[key]!=0 for key in ('max_cost_micros','max_http_requests')):
        return None
    items=owner_state.get('items')
    wanted={q['id'] for q in questions}
    if not isinstance(items,list) or not wanted or len(items)!=len(wanted):return None
    projected=[]
    for item in items:
        if (not isinstance(item,dict) or item.get('question_id') not in wanted
            or item.get('subject_ref')!=subject_ref or item.get('decision')!='reuse'
            or not isinstance(item.get('reuse_observation_id'),str) or not item['reuse_observation_id']):return None
        projected.append({'question_id':item['question_id'],'observation_id':item['reuse_observation_id']})
    if {r['question_id'] for r in projected}!=wanted:return None
    return {'subject_ref':copy.deepcopy(subject_ref),'question_count':len(projected),'items':projected,
        **({'cache_clock':cache_clock} if cache_clock=='successful_scan' else {})}


def _cache_preview(config,payload):
    """Original W06/C06 reads without quote, grant, runtime keys or admission."""
    native,manifest,route=payload['native'],payload['manifest'],payload['route']
    binding=native.get('binding')
    if binding is None or config.get('prepare',{}).get('recovery_work_decision_refs') is not None:
        return None
    now = _now()
    selected = set(payload['question_ids'])
    questions = [question for question in manifest['questions'] if question['id'] in selected]
    if len(questions) != len(selected):
        raise DashboardPrepareError('question_subset_invalid','Selected question is not part of this company bank',409)
    plan = _owner_prepare(config, 'cache_plan', {'binding':binding,'questions':questions,'now_utc':now})
    if plan is None:
        return None
    snapshot = _snapshot_bytes(plan['snapshot'])
    try:
        _equivalent_frozen_bank(manifest,route,snapshot,binding,snapshot['manifest_raw_sha256'])
    except DashboardPrepareError as error:
        if error.code=='existing_work_bank_changed':
            return None
        raise
    if 'plan_error' in plan:
        _raise_owner_prepare_error(plan['plan_error'])
    rows = plan.get('rows')
    if (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)
        or [row.get('question_id') for row in rows] != [q['id'] for q in questions]):
        raise DashboardPrepareError('native_response_invalid','Original cache plan did not bind every selected question',502)
    scopes, grouped = {}, {}
    for original, question in zip(rows, questions, strict=True):
        qid, ref, field = original['question_id'], original.get('subject_ref'), original.get('field')
        scope = 'segment' if route.get('scope') == 'segment' and question['scope'] == 'entity' else question['scope']
        security_id, listing_id, segment_id = None, None, None
        if scope == 'entity':
            scope_id = binding['entity_id']
        elif scope == 'security':
            listing = native['selected_listing']
            scope_id = security_id = listing['security_id']
            listing_id = listing['listing_id']
        elif scope == 'segment':
            scope_id = segment_id = route.get('segment_id')
        else:
            scope_id = None
        if (not isinstance(ref, dict) or not isinstance(field, dict) or not isinstance(scope_id, str)
            or ref.get('scope') != scope or ref.get('scope_id') != scope_id
            or ref.get('primary_issuer_id') != binding['entity_id']
            or (ref.get('security_id'), ref.get('listing_id'), ref.get('segment_id')) != (security_id, listing_id, segment_id)
            or type(ref.get('analysis_subject_revision')) is not int
            or any(ref.get(key) != binding.get(key) for key in ('entity_id','analysis_subject_id','analysis_subject_revision','perimeter_sha256'))
            or field.get('field_id') != qid or field.get('decision') != 'reuse'
            or not isinstance(field.get('reuse_observation_id'), str) or not field['reuse_observation_id']):
            raise DashboardPrepareError('native_response_invalid','Original cache plan returned a different question or scope',502)
        scopes[qid] = {'scope':scope,'scope_id':scope_id}
        row=grouped.setdefault(_sha(ref),{'subject_ref':ref,'question_count':0,'items':[]})
        row['items'].append({'question_id':qid,'observation_id':field['reuse_observation_id'],
            **({key:field[key] for key in ('information_as_of','cache_started_at','cache_valid_until') if key in field}
               if plan.get('cache_clock')=='successful_scan' else {})})
        row['question_count']+=1
    request={k:binding[k] for k in ('entity_id','subject_key','perimeter_sha256','identity_revision')}
    request.update(information_cutoff=route['as_of'],scope_bindings=scopes)
    try:
        if _read_continuation_bank(config, request, ledger=plan['work_store']):
            return None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    return {'status':'cached','entity_id':binding['entity_id'],'execution_bundles':[],'cached_scopes':list(grouped.values()),'checked_at':now,
        'cached_question_count':len(selected),'question_count_total':len(selected),'API_requests':0,'dispatch_started':False,
        **({'cache_clock':'successful_scan'} if plan.get('cache_clock')=='successful_scan' else {}),
        'financial_accuracy_proven':False,'owner_state_changed':False,'information_cutoff':route['as_of']}


def _phase_artifacts(directory):
    """Names only: never copy captured answers, runtime files or credentials."""
    directory = Path(directory)
    phases = ["bootstrap.json", "final/manifest.json"]
    for scope in sorted(directory.glob("scope-*")):
        if scope.is_dir() and not scope.is_symlink():
            phases.extend(scope.name + "/" + name for name in (
                "query.json", "capture.json", "refresh.json", "owner-preview.json", "grant.json",
                "confirmation.json", "admission.json", "inspection-request.json", "prepared-scope.json"))
    return [name for name in phases if (directory / name).is_file()]


def _safe_root(value, label, *, exists=True):
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise DashboardPrepareError("preparation_not_configured", f"Configure an absolute {label}", 503)
    path = Path(value)
    for parent in (path, *path.parents):
        try:
            metadata = parent.lstat()
        except FileNotFoundError:
            continue
        if parent.is_symlink() or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise DashboardPrepareError("preparation_path_redirected", "Preparation paths may not use links", 503)
    if exists and not path.exists():
        raise DashboardPrepareError("preparation_not_configured", f"Configured {label} does not exist", 503)
    return path


@contextmanager
def _apply_guard(config, preview_id):
    """An OS lock serializes the original fixed owner install-file namespace.

    Kernel release on process death permits unrelated company preparation.
    Candidate apply-started markers still prevent blind retry of partial work.
    """
    try:
        from .dashboard_locks import control_lock, ControlBusyError
    except ImportError:
        from .dashboard_locks import control_lock, ControlBusyError
    try:
        with control_lock(_control_path(config)):
            yield
    except ControlBusyError:
        raise DashboardPrepareError("owner_preparation_busy", "Another preparation currently owns this product's original owner namespace", 409) from None


def _control_path(config):
    return Path(config["iqs_root"]) / "runs/dashboard-preparation-locks" / (_sha(str(Path(config["workspace_root"]).resolve())) + ".lock")


class PrepareGateway:
    """Trusted deployment plus untrusted entity selection; zero paid dispatch."""
    def __init__(self, config):
        self.config = copy.deepcopy(config or {})
        self.options = self.config.get("prepare", {})
        self._lock = threading.RLock()

    def _deployment(self):
        for key in ("iqs_root", "stockwiki_root", "workspace_root"):
            _safe_root(self.config.get(key), key)
        options = self.options
        if not isinstance(options, dict):
            raise DashboardPrepareError("preparation_not_configured", "prepare must be an object", 503)
        state = _safe_root(str(options.get("state_root") or Path(self.config["iqs_root"]) / "runs/dashboard-preparation"), "prepare.state_root", exists=False)
        if not state.is_relative_to(Path(self.config["iqs_root"]).resolve()):
            raise DashboardPrepareError("preparation_not_configured", "Preparation state must belong to IQS", 503)
        return state

    def _worker(self, operation, payload):
        self._deployment()
        timeout = 60 if operation == "snapshot" else _timeouts(self.config)[0]
        try:
            completed = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/dashboard_prepare.py"), "--worker"],
                cwd=self.config["iqs_root"], env=_env(), input=_bytes({"operation": operation,
                "config": self.config, "payload": payload}), capture_output=True, timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            raise DashboardPrepareError("preparation_timeout_unknown" if operation == "apply" else "owner_snapshot_timeout",
                "Original operation timed out; inspect its immutable journal before retrying", 504,
                {"operation": operation, "exception_type": "TimeoutExpired", "timeout_seconds": timeout,
                 "outcome_unknown": operation == "apply", "automatic_retry_allowed": False}) from None
        except OSError as error:
            raise DashboardPrepareError("owner_process_unavailable", "Original preparation process could not be started", 503,
                {"operation": operation, "exception_type": type(error).__name__}) from None
        if len(completed.stdout) > MAX_BYTES:
            raise DashboardPrepareError("owner_response_invalid", "Original owner response exceeds its limit", 502)
        try:
            response = decode_owner_json(completed.stdout.decode("utf-8"))
        except (UnicodeError, ValueError, RecursionError) as error:
            raise DashboardPrepareError("owner_response_invalid", "Original owner did not return its preparation envelope", 502) from error
        if not response.get("ok"):
            error = response.get("error", {})
            raise DashboardPrepareError(error.get("code", "owner_preparation_rejected"), error.get("message", "Original owner refused preparation"), error.get("status", 409), error.get("details"))
        if completed.returncode:
            raise DashboardPrepareError("owner_preparation_failed", "Original owner preparation process failed", 502)
        return response["data"]

    def status(self):
        try:
            self._deployment()
            owner_policy = _owner_prepare(self.config, 'policy', {})
            gaps = self._execution_gaps(owner_policy=owner_policy)
            return {"available": True, "bank_preview_available": True, "native_prepare_configured": not gaps,
                    "gaps": gaps, "module_package_id": self.options.get("module_package_id", DEFAULT_PACKAGE),
                    "profiles": [{"profile_id": key, "entity_id": row.get("entity_id"), "label": row.get("label", key)}
                                 for key, row in self.options.get("routing_profiles", {}).items()],
                    "API_requests": 0, "dispatch_started": False}
        except DashboardPrepareError as error:
            return {"available": False, "bank_preview_available": False, "gaps": [error.code], "API_requests": 0}

    def _execution_gaps(self, *, owner_policy=None):
        missing = []
        try:
            if owner_policy is None:
                owner_policy = _owner_prepare(self.config, 'policy', {})
            if owner_policy['sha256'] is None:
                missing.append("native_prepare_owner_policy_missing")
            else:
                original_policy = owner_policy['policy']
                protocol = original_policy.get("protocol") if isinstance(original_policy, dict) else None
                if not isinstance(protocol, str) or not protocol.startswith("stockwiki.refresh_owner_policy/"):
                    missing.append("native_prepare_owner_policy_invalid")
                elif protocol not in {"stockwiki.refresh_owner_policy/1.0.0", "stockwiki.refresh_owner_policy/1.1.0", "stockwiki.refresh_owner_policy/1.2.0", "stockwiki.refresh_owner_policy/1.3.0", "stockwiki.refresh_owner_policy/1.6.0"}:
                    missing.append("native_prepare_owner_dialect_not_supported")
                elif (protocol in {"stockwiki.refresh_owner_policy/1.2.0", "stockwiki.refresh_owner_policy/1.3.0"}) != (parse_recovery_refs(self.config.get("prepare", {})) is not None):
                    missing.append("recovery_policy_refs_required")
                else:
                    _ordered_route_targets(original_policy)
        except (OSError, ValueError, TypeError, KeyError):
            missing.append("native_prepare_owner_policy_invalid")
        for key in ("admission_config", "runtime_dir", "spend_authorization"):
            value = self.options.get(key)
            if not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).exists():
                missing.append("prepare." + key)
        if isinstance(self.options.get("runtime_dir"), str) and not (Path(self.options["runtime_dir"]) / "llm_apis.json").is_file():
            missing.append("prepare.runtime_llm_config")
        try:
            _timeouts(self.config)
        except DashboardPrepareError:
            missing.append("prepare.timeouts")
        source = self.config.get("stockqa_root")
        if not isinstance(source, str) or not (Path(source) / "main_with_llm.py").is_file():
            missing.append("stockqa_root")
        producer = self.options.get("producer")
        if not isinstance(producer, dict) or set(producer) != {"component_version", "build_id"} or any(not isinstance(value, str) or not value for value in producer.values()):
            missing.append("prepare.producer")
        if not isinstance(self.options.get("authorization_reference"), str) or not self.options.get("authorization_reference"):
            missing.append("prepare.authorization_reference")
        agent = self.options.get("agent")
        if not isinstance(agent, dict) or set(agent) != {"profile_id", "profile_sha256", "harness_ref"} or not re.fullmatch("[a-f0-9]{64}", str(agent.get("profile_sha256", ""))):
            missing.append("prepare.agent")
        return missing

    def _configuration_binding(self, selection, *, owner_policy=None):
        """Bind this preparation, not append-only UI bundle registrations."""
        keys = ("iqs_root", "stockwiki_root", "stockwiki_python", "stockqa_root", "stockqa_python",
                "workspace_root", "iqs_release_root")
        options = {key: value for key, value in self.options.items() if key != "routing_profiles"}
        profile_id = selection.get("profile_id")
        profile = self.options.get("routing_profiles", {}).get(profile_id) if profile_id else None
        selected_profile = {key: profile.get(key) for key in ("entity_id", "verified_facts", "user_policy")} if profile else None
        if owner_policy is None:
            owner_policy = _owner_prepare(self.config, 'policy', {})
        files = {owner_policy['path']:owner_policy['sha256']}
        paths = []
        for key in ("admission_config", "spend_authorization", "search_policy", "shared_company_config"):
            if self.options.get(key):
                paths.append(Path(self.options[key]))
        if self.options.get("runtime_dir"):
            paths.append(Path(self.options["runtime_dir"]) / "llm_apis.json")
        if self.options.get("admission_config") and Path(self.options["admission_config"]).is_file():
            admission = _read(self.options["admission_config"])
            if admission.get("budget_policy_file"):
                paths.append(Path(admission["budget_policy_file"]))
        for path in paths:
            files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return _sha({"deployment": {key: self.config.get(key) for key in keys},
                     "options": options, "selected_profile": selected_profile, "native_input_file_hashes": files})

    def bank_preview(self, payload):
        if not isinstance(payload, dict) or set(payload) - {"entity_id", "as_of", "mode", "subject_key", "profile_id", "scope_selector", "security_id", "question_ids"}:
            raise DashboardPrepareError("selection_invalid", "Select only an entity, cutoff, mode and registered profile")
        entity_id, as_of = payload.get("entity_id"), payload.get("as_of")
        if not isinstance(entity_id, str) or not re.fullmatch(r"ENT_[A-Za-z0-9_-]{1,100}", entity_id):
            raise DashboardPrepareError("entity_id_required", "Select an exact registered entity ID")
        try:
            cutoff = date.fromisoformat(as_of)
        except (ValueError, TypeError):
            raise DashboardPrepareError("cutoff_invalid", "Select an ISO information cutoff date") from None
        if cutoff > datetime.now(timezone.utc).date():
            raise DashboardPrepareError("cutoff_invalid", "Information cutoff cannot be in the future")
        mode = payload.get("mode", "quick")
        if mode not in {"quick", "full"}:
            raise DashboardPrepareError("mode_invalid", "Select quick or full")
        scope_selector = payload.get("scope_selector", "existing")
        if scope_selector not in {"existing", "issuer_only"} or (scope_selector == "issuer_only" and payload.get("subject_key")):
            raise DashboardPrepareError("scope_selection_invalid", "Select an existing subject or the explicit issuer-only scope")
        profile_id = payload.get("profile_id")
        subset=payload.get('question_ids')
        if subset is not None and (not isinstance(subset,list) or not subset or any(not isinstance(q,str) or not q for q in subset)
            or len(set(subset))!=len(subset)):
            raise DashboardPrepareError('question_subset_invalid','Select a nonempty, unique question subset from this company bank')
        if subset is not None and parse_recovery_refs(self.config.get("prepare", {})) is not None:
            raise DashboardPrepareError('question_subset_recovery_conflict','A question subset cannot replace an original controlled-recovery selection')
        profile = self.options.get("routing_profiles", {}).get(profile_id, {}) if profile_id else {}
        if profile_id and (not profile or profile.get("entity_id") != entity_id):
            raise DashboardPrepareError("profile_not_registered", "This company has no such trusted routing profile")
        state = self._deployment()
        # Authority is selected now, independently of the answer information
        # cutoff. Freeze the complete server instant, including its time of day;
        # today's issuer receipt may have been verified after UTC midnight.
        owner_snapshot_as_of = _now()
        native = self._worker("snapshot", {"entity_id": entity_id, "as_of": as_of,
            "owner_snapshot_as_of": owner_snapshot_as_of,
            "scope_as_of": owner_snapshot_as_of if scope_selector == "issuer_only" else None,
            "subject_key": payload.get("subject_key"), "scope_selector": scope_selector, "security_id": payload.get("security_id")})
        from iqs_scan.questions import api as module_registry
        from iqs_scan.questions import api as routing
        from iqs_scan.questions import api as question_sets
        identity, binding = native["identity"], native["binding"]
        issuer = identity["payload"]
        listings = [row for row in issuer["listings"] if row.get("listing_status") in {"active", "suspended"}]
        if not listings:
            raise DashboardPrepareError("active_listing_missing", "No current original listing can anchor this bank", 409)
        listing = native["selected_listing"]
        route_input = {"entity_id": entity_id, "identity_ref": binding["route_identity_ref"] if binding else "stockwiki.identity-export-g2b:" + _sha(identity),
                       "company": issuer["canonical_name"], "ticker": listing["ticker"], "exchange": listing["exchange_raw"],
                       "as_of": as_of, "security_id": listing["security_id"], "requested_mode": mode, "verified_facts": profile.get("verified_facts", [])}
        now, preview_id = _now(), "prepare_" + uuid.uuid4().hex
        directory = state / "candidates" / preview_id
        package_id = self.options.get("module_package_id", DEFAULT_PACKAGE)
        code_root = Path(self.config["iqs_root"])
        fact_ids = None
        if subset:
            package, _, _, _ = module_registry.load_package(package_id, root=code_root)
            fact_bank = package['format_resources'].get(module_registry.FACT_BANK_RESOURCE, {})
            fact_ids = [q['id'] for q in fact_bank.get('questions', []) if q['id'] in subset] or None
        route = routing.resolve_route_decision(route_input, package_id=package_id,
            user_policy=profile.get("user_policy"), now_utc=now, root=code_root)
        directory.mkdir(parents=True, exist_ok=False)
        try:
            proposed = directory / "proposed-bank"
            question_sets.compose_from_route(route, proposed, now_utc=now,
                expected_route_decision_id=route["decision_id"], answer_format="standard-1",
                **({'fact_question_ids': fact_ids} if fact_ids else {}))
            _new(proposed / "route.json", route)
            manifest = _read(proposed / "manifest.json")
            if subset is not None and set(subset)-{q['id'] for q in manifest['questions']}:
                raise DashboardPrepareError('question_subset_invalid','Selected question is not part of this company bank')
            requested=[q['id'] for q in manifest['questions'] if subset is None or q['id'] in subset]
            cached=self._worker('cache_preview',{'native':native,'manifest':manifest,'route':route,
                'question_ids':requested}) if binding is not None else None
            owner_policy = _owner_prepare(self.config, 'policy', {})
            gaps = self._execution_gaps(owner_policy=owner_policy)
            if cached is not None:gaps=[]
            reused = self._worker("bank_reuse", {"native": native, "manifest": manifest, "route": route}) if binding is not None and not gaps and cached is None else None
            _new_raw(directory / "manifest.json", reused['manifest_raw'].encode('utf-8') if reused else (proposed / "manifest.json").read_bytes())
            _new_raw(directory / "questions.json", (proposed / "questions.json").read_bytes())
            _new(directory / "identity.json", identity)
            _new_raw(directory / "route.json", reused['route_raw'].encode('utf-8') if reused else (proposed / "route.json").read_bytes())
            _new(directory / "native.json", native)
            manifest = _read(directory / "manifest.json")
            route = _read(directory / "route.json")
            recovery = _recovery_subset(self.config, directory, manifest, native, owner_policy['policy']) if not gaps and cached is None else None
            if issuer["identity_state"] != "verified":
                gaps.append("route_identity_unverified")
            if binding is None and native.get("bootstrap") is None:
                gaps.append(native.get("subject_gap", "subject_authority_missing"))
            if len(listings) > 1 and not payload.get("security_id"):
                gaps.append("security_selection_required")
            record = {"protocol": PROTOCOL, "preview_id": preview_id, "created_at": now,
                      "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
                      "selection": payload, "snapshot_sha256": _snapshot_sha(native),
                      "config_sha256": self._configuration_binding(payload, owner_policy=owner_policy),
                      "owner_snapshot_as_of": native["owner_snapshot_as_of"], "scope_as_of": native["scope_as_of"],
                      "files": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                for name in ("identity.json", "route.json", "native.json", "manifest.json", "questions.json",
                                    "proposed-bank/route.json", "proposed-bank/manifest.json", "proposed-bank/questions.json")},
                      "bank_reuse": {k:v for k,v in reused.items() if k not in {'manifest_raw','route_raw'}} if reused else None,
                      "bank": {"entity_id": entity_id, "company": issuer["canonical_name"], "identity_state": issuer["identity_state"],
                               "information_cutoff": as_of, "mode": mode, "module_package_id": manifest["module_package_id"],
                               "modules": manifest["modules"], "question_count": len(manifest["questions"]),
                               "question_ids": [row["id"] for row in manifest["questions"]],
                               "classification_status": route["status"], "coverage_gaps": route["dispatch_plan"]["coverage_gaps"]},
                      "subject_candidates": native["subjects"], "gaps": sorted(set(gaps)), "can_prepare": not gaps,
                      "entity_id": entity_id, "question_count": len(manifest["questions"]),
                      "questions": [{"id": row["id"], "module_id": row["module_id"], "question": row.get("text", row.get("question", ""))} for row in manifest["questions"]],
                      "available_subjects": native["subjects"],
                      "available_listings": listings, "selected_security": listing,
                      "selected_subject": ({"key": binding["subject_key"], "scope_kind": binding["subject"]["scope_kind"]} if binding else
                                           {"key": native["bootstrap"]["subject_key"], "scope_kind": "standalone_issuer"} if native.get("bootstrap") else None),
                      "blocked_reasons": sorted(set(gaps)), "can_apply": not gaps}
            record["recovery_subset"] = recovery
            record['cache_only_available']=cached is not None
            if cached is not None:
                # The original read already returned these observation IDs.
                # Viewing them needs neither confirmation nor an apply job.
                record['cached_result']=cached
            record["execution_question_ids"] = recovery["execution_question_ids"] if recovery else requested
            record["execution_question_count"] = len(record["execution_question_ids"])
            if self.options.get('shared_company_config'):
                _new_raw(directory/'shared-company-config.json', Path(self.options['shared_company_config']).read_bytes())
                record['files']['shared-company-config.json'] = hashlib.sha256((directory/'shared-company-config.json').read_bytes()).hexdigest()
            if recovery:
                record["files"]["recovery-projection-request.json"] = hashlib.sha256((directory / "recovery-projection-request.json").read_bytes()).hexdigest()
            record["preview_token"] = _sha(record)
            _new(directory / "preview.json", record)
        except Exception:
            # A failed candidate remains an explicit unfinished local artifact,
            # never an admitted bundle; do not delete another process's state.
            raise
        return {**record, "owner_database_writes": 0, "API_requests": 0, "dispatch_started": False,
                "meaning": "Bank candidate only; prepare applies original owner route, capture and consent"}

    def _validated_selection(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"preview_id", "preview_token"}:
            raise DashboardPrepareError("selection_invalid", "Apply only an exact preparation preview")
        preview_id = payload.get("preview_id")
        if not isinstance(preview_id, str) or not re.fullmatch("prepare_[a-f0-9]{32}", preview_id):
            raise DashboardPrepareError("preview_unknown", "Preparation preview is not registered", 404)
        directory = self._deployment() / "candidates" / preview_id
        _safe_root(str(directory), "candidate directory", exists=False)
        if not (directory / "preview.json").is_file():
            raise DashboardPrepareError("preview_unknown", "Preparation preview is not registered", 404)
        record = _read(directory / "preview.json")
        if payload["preview_token"] != record["preview_token"] or record["preview_token"] != _sha({k: v for k, v in record.items() if k != "preview_token"}):
            raise DashboardPrepareError("preview_stale", "Review the exact bank preview again", 409)
        if record["config_sha256"] != self._configuration_binding(record["selection"]) or any(hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest for name, digest in record["files"].items()):
            raise DashboardPrepareError("preview_stale", "Preparation inputs or deployment changed", 409)
        if not (directory / "applied.json").exists():
            native = _read(directory / "native.json")
            if (not isinstance(native.get("owner_snapshot_as_of"), str) or
                    (record["selection"].get("scope_selector") == "issuer_only" and
                     native.get("scope_as_of") != native["owner_snapshot_as_of"])):
                raise DashboardPrepareError("preview_stale", "This candidate predates frozen owner time; create a new bank preview", 409)
            # Local elapsed time is not authority. Apply rechecks the current
            # owner snapshot; original confirmations enforce their own expiry.
            if not record["can_prepare"]:
                raise DashboardPrepareError("preparation_blocked", "Original preparation prerequisites are missing", 409, {"gaps": record["gaps"]})
        return directory, record

    def validate_selection(self, payload):
        """Read-only preflight for async submission; never occupy a bad token."""
        directory, record = self._validated_selection(payload)
        return {"preview_id": record["preview_id"], "valid": True,
                "status": self.preparation(record["preview_id"])["status"], "API_requests": 0, "owner_database_writes": 0}

    def apply(self, payload):
        with self._lock:
            directory, record = self._validated_selection(payload)
            preview_id = record["preview_id"]
            result_path = directory / "applied.json"
            if result_path.exists():
                # Execution must still run its original current permission read.
                return {**_read(result_path), "replayed": True}
            if (directory / "apply-started.json").exists():
                raise DashboardPrepareError("preparation_partial", "An earlier preparation may have changed original owner state; inspect its journal before an explicit recovery", 409,
                    {"preview_id": preview_id, "recovery": "Read preparation status and original immutable phase artifacts; never automatically repeat confirmation or admission"})
            frozen_native = _read(directory / "native.json")
            native = self._worker("snapshot", {"entity_id": record["bank"]["entity_id"], "as_of": record["bank"]["information_cutoff"],
                                             "owner_snapshot_as_of": frozen_native["owner_snapshot_as_of"], "scope_as_of": frozen_native.get("scope_as_of"),
                                             "subject_key": frozen_native["binding"]["subject_key"] if frozen_native["binding"] else None,
                                             "scope_selector": record["selection"].get("scope_selector", "existing"), "security_id": frozen_native["selected_listing"]["security_id"]})
            if _snapshot_sha(native) != record["snapshot_sha256"]:
                raise DashboardPrepareError("preview_stale", "Original identity, subject or route anchor changed", 409)
            with _apply_guard(self.config, preview_id):
                _new(directory / "apply-started.json", {"preview_id": preview_id, "started_at": _now(),
                     "preview_token": record["preview_token"], "API_requests": 0})
                try:
                    result = self._worker("apply", {"directory": str(directory)})
                except DashboardPrepareError as error:
                    _new(directory / "apply-error.json", {"failed_at": _now(), "code": error.code,
                        "details": error.details, "completed_phases": _phase_artifacts(directory),
                        "automatic_retry_allowed": False})
                    raise
                _new(result_path, result)
                return result

    def preparation(self, preview_id):
        """Read preparation artifacts only; never confirm, admit or dispatch."""
        if not isinstance(preview_id, str) or not re.fullmatch("prepare_[a-f0-9]{32}", preview_id):
            raise DashboardPrepareError("preview_unknown", "Preparation preview is not registered", 404)
        directory = self._deployment() / "candidates" / preview_id
        if not (directory / "preview.json").is_file():
            raise DashboardPrepareError("preview_unknown", "Preparation preview is not registered", 404)
        result = directory / "applied.json"
        if result.is_file():
            return {"status": "prepared", "result": _read(result), "API_requests": 0, "owner_database_writes": 0}
        stages = _phase_artifacts(directory)
        return {"status": "partial" if (directory / "apply-started.json").is_file() else "not_applied",
                "preview_id": preview_id, "completed_phases": stages, "automatic_retry_allowed": False,
                "last_error": _read(directory / "apply-error.json") if (directory / "apply-error.json").is_file() else None,
                "API_requests": 0, "owner_database_writes": 0}


def _snapshot(config, payload):
    reply = _owner_prepare(config, 'snapshot', {**payload, 'now_utc': _now(),
        'authorization_reference': config.get('prepare', {}).get('authorization_reference', '')})
    if not isinstance(reply, dict) or set(reply) not in ({'identity', 'selection'}, {'identity', 'selection_error'}):
        raise DashboardPrepareError('native_response_invalid', 'Original owner did not return its identity snapshot', 502)
    identity = reply['identity']
    try:
        from . import contract_validation as cv
    except ImportError:
        from iqs_scan.foundation import api as cv
    # The exact G2b identity is validated by the consuming IQS contract before
    # any listing, subject, route anchor or owner selection refusal is used.
    try:
        context = identity['trusted_context']
        cv.validate_entity(identity['payload'], trusted_identity_receipts=context['identity_receipts'],
            trusted_source_bindings=context['source_bindings'], trusted_market_registry=context['market_registry'],
            wire_profile='stockwiki-g2b/1.1.0')
    except (ValueError, KeyError, TypeError, AttributeError, cv.JsonSchemaValidationError):
        raise DashboardPrepareError('owner_identity_contract_invalid',
            'Complete or correct the original identity attributes and evidence, then create a new bank preview', 409,
            {'required_action': 'repair_original_identity_and_create_new_preview'}) from None
    issuer = identity['payload']
    if issuer.get('entity_id') != payload['entity_id']:
        raise DashboardPrepareError('native_response_invalid', 'Original owner returned a different entity', 502)
    if 'selection_error' in reply:
        _raise_owner_prepare_error(reply['selection_error'])
    selection = reply['selection']
    if not isinstance(selection, dict) or set(selection) != {
        'subjects', 'binding', 'anchor', 'subject_gap', 'bootstrap', 'owner_snapshot_as_of',
        'scope_as_of', 'selected_listing', 'listing_binding',
    }:
        raise DashboardPrepareError('native_response_invalid', 'Original owner did not return a scope selection', 502)
    listing, listing_binding, binding = selection['selected_listing'], selection['listing_binding'], selection['binding']
    bound_listing = listing_binding.get('listing') if isinstance(listing_binding, dict) else None
    if (not isinstance(listing, dict) or listing not in issuer['listings']
        or (payload.get('security_id') and listing.get('security_id') != payload['security_id'])
        or selection['owner_snapshot_as_of'] != payload['owner_snapshot_as_of']
        or selection['scope_as_of'] != payload.get('scope_as_of')
        or (binding is not None and (not isinstance(binding, dict) or binding.get('entity_id') != issuer['entity_id']
            or type(binding.get('identity_revision')) is not int
            or binding.get('identity_revision') != issuer.get('identity_revision')))
        or (listing_binding is not None and (not isinstance(bound_listing, dict)
            or listing_binding.get('entity_id') != issuer['entity_id']
            or type(listing_binding.get('identity_revision')) is not int
            or listing_binding.get('identity_revision') != issuer.get('identity_revision')
            or any(bound_listing.get(key) != listing.get(key) for key in ('entity_id','security_id','listing_id'))))):
        raise DashboardPrepareError('native_response_invalid', 'Original owner scope did not match the requested identity', 502)
    return {'identity': identity, **selection}


def _snapshot_bytes(snapshot):
    try:
        return {**snapshot, 'manifest_raw':snapshot['manifest_raw'].encode('utf-8'),
                'route_raw':snapshot['route_raw'].encode('utf-8')}
    except (KeyError, AttributeError, TypeError) as error:
        raise DashboardPrepareError('native_response_invalid','Original owner snapshot bytes are missing',502) from error


def _raise_owner_prepare_error(error):
    if (not isinstance(error, dict) or not isinstance(error.get('code'), str)
        or not isinstance(error.get('message'), str) or type(error.get('status')) is not int
        or not 400 <= error['status'] <= 599 or not isinstance(error.get('details'), dict)):
        raise DashboardPrepareError('native_response_invalid', 'Original owner returned an invalid refusal', 502)
    raise DashboardPrepareError(error['code'], error['message'], error['status'], error['details'])


def _owner_prepare(config, operation, payload, *, iqs_release_root=None):
    arguments = ['--root', config['workspace_root'], '--iqs-code-root', config['iqs_root'],
                 '--iqs-release-root', iqs_release_root or config.get('iqs_release_root') or config['iqs_root']]
    return _native_cli(config, 'wiki', _OWNER_COMMAND, arguments, owner_operation=operation,
        timeout_override=60 if operation in {'snapshot', 'policy'} else None,
        input_value={'protocol':_OWNER_REQUEST,'operation':operation,'payload':payload})


def _route_command(config, action, subject_key, arguments, *, release_root):
    result = _native_cli(config, 'wiki', 'stockwiki.quick_scan_routes_cli',
        ['--root', config['workspace_root'], 'quick-scan-route-' + action, '--iqs-code-root', config['iqs_root'],
         '--iqs-release-root', release_root, '--subject-key', subject_key, *arguments])
    if (result.get('protocol') != 'stockwiki.route_store_cli/1.0.0' or result.get('action') != action
        or result.get('status') != 'ok' or result.get('paid_dispatch_started') is not False):
        raise DashboardPrepareError('native_response_invalid', 'Original owner route response did not match the operation', 502)
    return result['payload']


def _native_cli(config, kind, module, arguments, *, input_value=None, owner_operation=None, timeout_override=None):
    code_root = config["stockwiki_root" if kind == "wiki" else "stockqa_root"]
    interpreter = config.get("stockwiki_python" if kind == "wiki" else "stockqa_python") or sys.executable
    env = _env()
    env["PYTHONPATH"] = code_root
    cwd = config.get("prepare", {}).get("runtime_dir", code_root) if kind == "qa" else code_root
    timeout = _timeouts(config)[1] if timeout_override is None else timeout_override
    stage = [value for value in arguments if value in {"--request", "--install-delegation", "--install-delegation-stdin", "--confirm-delegated", "--confirmation-id", "--input-locations"}]
    details = {"native_module": module, "native_selectors": stage, "timeout_seconds": timeout}
    try:
        done = subprocess.run([interpreter, "-B", "-X", "utf8", "-m", module, *arguments], cwd=cwd, env=env,
                              input=_bytes(input_value) if input_value is not None else None,
                              capture_output=True, timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise DashboardPrepareError("native_preparation_timeout_unknown",
            "Original native stage timed out; inspect the recorded phases before an explicit recovery", 504,
            {**details, "exception_type": "TimeoutExpired", "outcome_unknown": True,
             "automatic_retry_allowed": False}) from None
    except OSError as error:
        raise DashboardPrepareError("native_transport_unavailable", "Original native process could not be started", 503,
            {**details, "exception_type": type(error).__name__}) from None
    details["native_returncode"] = done.returncode
    if len(done.stdout) > MAX_BYTES:
        raise DashboardPrepareError("native_response_invalid", "Original native response exceeds its limit", 502)
    try:
        result = decode_owner_json(done.stdout.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise DashboardPrepareError("native_response_invalid", "Original native command did not return JSON", 502,
            {**details, "exception_type": type(error).__name__}) from None
    if not isinstance(result, dict):
        raise DashboardPrepareError("native_response_invalid", "Original native command did not return an object", 502, details)
    if owner_operation is not None:
        key = 'error' if done.returncode else 'result'
        allowed_absent = owner_operation in {'cache_plan','frozen_snapshot'}
        if (set(result) != {'protocol','operation',key} or result['protocol'] != _OWNER_REPLY
            or result['operation'] != owner_operation or done.returncode not in {0,2}
            or (key == 'result' and not isinstance(result[key], dict)
                and (result[key] is not None or not allowed_absent))):
            raise DashboardPrepareError('native_response_invalid', 'Original preparation response did not match the operation', 502, details)
        if key == 'error':
            _raise_owner_prepare_error(result[key])
        return result[key]
    if done.returncode:
        code = result.get("error_code", result.get("reason"))
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", code):
            code = "native_preparation_rejected"
        raise DashboardPrepareError(code, "Original native command refused preparation", 409,
            {**details, "native_error_code": code})
    return result


def _apply(config, payload):
    options, directory = config["prepare"], Path(payload["directory"])
    record, native = _read(directory / "preview.json"), _read(directory / "native.json")
    manifest, route = _read(directory / "manifest.json"), _read(directory / "route.json")
    cached=_cache_preview(config,{'native':native,'manifest':manifest,'route':route,
        'question_ids':record['execution_question_ids']})
    if cached is not None:
        result={**cached,'protocol':PROTOCOL,'full_bank_question_count':record['bank']['question_count'],
            'company':record['bank']['company'],
            'execution_question_ids':record['execution_question_ids'],'execution_question_count':len(record['execution_question_ids']),
            'recovery_subset':None,'meaning':'Original fresh observations reused; no new executor work, grant, confirmation or paid admission'}
        _new(directory/'applied.json',result)
        return result
    if record.get('cache_only_available'):
        raise DashboardPrepareError('cache_no_longer_reusable','Original cached answers changed or expired; preview again before any new work',409)
    admission = _read(options["admission_config"])
    policy = _owner_prepare(config, 'policy', {})['policy']
    recovery = _recovery_subset(config, directory, manifest, native, policy)
    if recovery != record.get("recovery_subset"):
        raise DashboardPrepareError("recovery_source_changed", "Original recovery controls changed after the bank preview", 409)
    expected = {"stockwiki_code_root": config["stockwiki_root"], "stockwiki_workspace_root": config["workspace_root"],
                "iqs_code_root": config["iqs_root"], "iqs_release_root": config.get("iqs_release_root", config["iqs_root"])}
    if any(Path(admission[key]).resolve() != Path(value).resolve() for key, value in expected.items()) or Path(policy["qa"]["work_store"]).resolve() != Path(admission["work_store"]).resolve() or Path(policy["qa"]["budget_policy_file"]).resolve() != Path(admission["budget_policy_file"]).resolve():
        raise DashboardPrepareError("native_deployment_mismatch", "Original admission and owner deployment differ", 409)
    # A later company scan needs fresh immutable input directories, while
    # keeping the SAME original work/budget ledger. Do not overwrite an older
    # subject_hash bundle or enlarge/reset its budget to make a refresh pass.
    admission = copy.deepcopy(admission)
    for key, folder in (("execution_inputs_root", "native-inputs"), ("runs_dir", "admission-runs")):
        (directory / folder).mkdir(parents=True, exist_ok=True)
        admission[key] = str(directory / folder)
    admission_path = directory / "admission-config.json"
    _new(admission_path, admission)
    config = copy.deepcopy(config)
    config["prepare"]["admission_config"] = str(admission_path)
    options = config["prepare"]
    binding = native["binding"]
    frozen_dir = directory
    if native.get("bootstrap"):
        applied = _owner_prepare(config, 'bootstrap_apply', {'entity_id':record['bank']['entity_id'],
            'scope_as_of':native['scope_as_of'], 'authorization_reference':options['authorization_reference'],
            'expected_preview_sha256':native['bootstrap']['preview_sha256']}, iqs_release_root=expected['iqs_release_root'])
        bootstrap, binding = applied['bootstrap'], applied['binding']
        if binding.get('entity_id') != record['bank']['entity_id'] or binding.get('subject_key') != bootstrap.get('subject_key'):
            raise DashboardPrepareError('native_response_invalid','Original issuer bootstrap did not return the selected subject',502)
        _new(directory / "bootstrap.json", bootstrap)
        # A draft subject was never a trust root. After ORIGINAL owner apply,
        # freeze a new final route/bank linked to the untouched initial preview.
        from iqs_scan.questions import api as routing
        from iqs_scan.questions import api as question_sets
        final_input = {key: route["profile_context"][key] for key in ("entity_id", "company", "ticker", "exchange", "as_of", "security_id")}
        final_input.update(identity_ref=binding["route_identity_ref"], requested_mode=record["bank"]["mode"])
        selected_profile = options.get("routing_profiles", {}).get(record["selection"].get("profile_id"), {})
        final_input["verified_facts"] = selected_profile.get("verified_facts", [])
        route = routing.resolve_route_decision(final_input, package_id=record["bank"]["module_package_id"],
            user_policy=selected_profile.get("user_policy"), now_utc=_now(), root=Path(config["iqs_root"]))
        frozen_dir = directory / "final"
        question_sets.compose_from_route(route, frozen_dir, now_utc=_now(),
            expected_route_decision_id=route["decision_id"], answer_format="standard-1",
            **({'fact_question_ids': manifest['fact_question_ids']} if 'fact_question_ids' in manifest else {}))
        _new(frozen_dir / "route.json", route)
        _new_raw(frozen_dir / "identity.json", (directory / "identity.json").read_bytes())
        _new(frozen_dir / "preparation-lineage.json", {"draft_preview_id": record["preview_id"], "draft_preview_token": record["preview_token"],
            "draft_manifest_sha256": record["files"]["manifest.json"], "original_bootstrap_preview_sha256": native["bootstrap"]["preview_sha256"],
            "subject_key": binding["subject_key"], "scope_semantics": bootstrap.get("scope_semantics"), "authority_from_draft": False})
        manifest = _read(frozen_dir / "manifest.json")
        if [row["id"] for row in manifest["questions"]] != record["bank"]["question_ids"]:
            raise DashboardPrepareError("prepared_bank_changed", "The original applied scope changed the previewed question selection", 409)
    if (directory / "proposed-bank/manifest.json").exists() and native.get('binding'):
        latest = _reusable_bank(config, {'native': native,
            'manifest': _read(directory / 'proposed-bank/manifest.json'),
            'route': _read(directory / 'proposed-bank/route.json')})
        latest_meta = {k:v for k,v in latest.items() if k not in {'manifest_raw','route_raw'}} if latest else None
        if latest_meta != record.get('bank_reuse'):
            raise DashboardPrepareError('preview_stale','Original unfinished-work bank bindings changed',409)
    if record.get('bank_reuse'):
        original = _owner_prepare(config, 'frozen_snapshot', {'subject_key':binding['subject_key'],
            'decision_id':route['decision_id']}, iqs_release_root=expected['iqs_release_root'])
        original = _snapshot_bytes(original) if original else None
        if (original is None or original['decision_id'] != route['decision_id']
            or original['route_raw'] != (frozen_dir/'route.json').read_bytes()
            or original['manifest_raw'] != (frozen_dir/'manifest.json').read_bytes()):
            raise DashboardPrepareError('existing_work_snapshot_required','Original frozen bank is missing or changed',409)
    else:
        _route_command(config, 'record', binding['subject_key'], ['--route', str(frozen_dir/'route.json'),
            '--manifest', str(frozen_dir/'manifest.json'), '--expected-decision-id', route['decision_id']],
            release_root=expected['iqs_release_root'])
    prior = (native['anchor'] or {}).get('decision_id')
    _route_command(config, 'activate', binding['subject_key'], ['--expected-decision-id', route['decision_id'],
        '--now-utc', _now(), *(['--expected-current-decision-id', prior] if prior else ['--expect-no-current'])],
        release_root=expected['iqs_release_root'])
    # Identified transport, metadata and exact original identity bytes are
    # generated from the frozen release, never manually assembled answers.
    from . import c06_authority
    from iqs_scan.questions.api import create_question_config
    run_id = "dashboard-" + record["preview_id"][8:]
    authority = c06_authority.create_authority(manifest,
        manifest_file_sha256=hashlib.sha256((frozen_dir / "manifest.json").read_bytes()).hexdigest(),
        identity_snapshot_sha256=hashlib.sha256((frozen_dir / "identity.json").read_bytes()).hexdigest(),
        run_context={"run_id": run_id, "scan_id": run_id + "-scan", "inputset_id": run_id + "-input", "task_mode": "primary", "comparison_group_id": None},
        contract_versions={"identity_schema": "2.1.0", "answer_schema": "1.0.0", "observation_schema": "1.2.0", "question_catalog": manifest["template_version"], "model_policy_schema": "2.0.0"},
        producer=options["producer"], subject_binding=binding,
        listing_bindings={native["selected_listing"]["security_id"]: native["listing_binding"]},
        root=Path(expected["iqs_release_root"]), observation_schema_version="1.2.0")
    grouped = {}
    for question in manifest["questions"]:
        if question["id"] not in record['execution_question_ids']:
            continue
        ref = authority["observation_context"]["questions"][question["id"]]["subject_binding"]["subject_ref"]
        grouped.setdefault(_sha(ref), {"ref": ref, "questions": []})["questions"].append(question)
    executions, cached_scopes, scope_records = [], [], []
    locations = _native_cli(config, 'qa', 'src.utils.quick_scan_refresh_admission_cli',
        ['--config', options['admission_config'], '--input-locations'],
        input_value=[group['ref'] for group in grouped.values()])['locations']
    if not isinstance(locations, list) or len(locations) != len(grouped):
        raise DashboardPrepareError('native_response_invalid', 'Original admission did not return every input location', 502)
    question_config = create_question_config(manifest, root=Path(expected['iqs_release_root']))
    for index, (group, target) in enumerate(zip(grouped.values(), locations, strict=True), 1):
        subject_ref = group["ref"]
        owner_config = {"protocol": "stockqa.owner_refresh_config/1.0.0", **expected, "subject_key": binding["subject_key"],
                        "scope": "entity", "scope_id": record["bank"]["entity_id"], "ttl_hours": policy["ttl_hours"], "runs_dir": str(directory / "owner-transport")}
        Path(owner_config["runs_dir"]).mkdir(parents=True, exist_ok=True)
        _new_raw(target['manifest'], (frozen_dir / 'manifest.json').read_bytes())
        _new_raw(target['identity_snapshot'], (frozen_dir / 'identity.json').read_bytes())
        _new(target['c06_authority'], authority)
        _new(target['owner_config'], owner_config)
        _new(target['questions'], question_config)
        scope_dir = directory / ("scope-" + str(index) + "-" + subject_ref["scope"])
        scope_dir.mkdir(parents=True, exist_ok=True)
        item = _prepare_scope(config, scope_dir, record, manifest, group["questions"], target, subject_ref, policy,
                              admission, expected, run_id + "-" + str(index))
        scope_records.append((scope_dir,item))
        (cached_scopes if item.get('status')=='cached' else executions).append(item)
    expected_scopes=[{'scope':item['subject_ref']['scope'],'scope_id':item['subject_ref']['scope_id']} for item in executions]
    for item in executions:item['execution_bundle']['expected_scope_bindings']=copy.deepcopy(expected_scopes)
    for scope_dir,item in scope_records:_new(scope_dir/'prepared-scope.json',item)
    first = executions[0] if executions else None
    result = {"protocol": PROTOCOL, "status": "prepared" if executions else 'cached', "execution_bundles": executions,
              'cached_scopes':cached_scopes,'cached_question_count':sum(item['question_count'] for item in cached_scopes),
              **({'cache_clock':'successful_scan'} if policy.get('cache_clock')=='successful_scan' else {}),
              'pending_question_count':sum(item['question_count'] for item in executions),
              "question_count_total": len(record['execution_question_ids']),
              "recovery_subset": recovery, "execution_question_ids": record["execution_question_ids"],
              "execution_question_count": record["execution_question_count"], "full_bank_question_count": record["bank"]["question_count"],
              "API_requests": 0, "dispatch_started": False, "financial_accuracy_proven": False,
              "owner_state_changed": True, "meaning": "All question scopes registered with native owner; execution still requires original current checks"}
    if first is not None:
        result.update(bundle_id=first['bundle_id'],bundle=first['execution_bundle'],execution_bundle=first['execution_bundle'],
            confirmation_id=first['confirmation_id'],admission=first['admission'])

    # The child publishes before writing stdout. Lost HTTP/process responses can
    # reconcile this exact result without repeating any original owner writes.
    _new(directory / "applied.json", result)
    return result


def _prepare_scope(config, directory, record, manifest, selected_questions, target, subject_ref, policy, admission, expected, run_id):
    options = config["prepare"]
    dialect = policy["protocol"].split("/")[-1]
    targets = _ordered_route_targets(policy)
    field_ids = sorted({row.get("field_id", row.get("metric_id")) for row in selected_questions})
    query = {"message_type": "request", "schema_version": "2.6.0" if dialect in {"1.1.0", "1.2.0", "1.3.0", "1.6.0"} else "2.0.0", "request_id": run_id + "-query",
             "consumer_id": admission["consumer_id"], "operation": "get_profiles", "requested_at": _now(),
             "payload": {"subject_refs": [subject_ref], "field_ids": field_ids, "information_cutoff": record["bank"]["information_cutoff"],
                         "include_history": True, "model_filter": None, "snapshot_id": None}}
    _new(directory / "query.json", query)
    common = ["--root", config["workspace_root"], "--iqs-code-root", config["iqs_root"]]
    capture = _native_cli(config, "wiki", "stockwiki.quick_scan_query_v2_cli", [*common, "--request", str(directory / "query.json")])
    _new(directory / "capture.json", capture)
    if capture["result"]["status"] == "unavailable" or capture["result"]["missing_subject_refs"]:
        raise DashboardPrepareError("source_snapshot_unavailable", "Original C06 snapshot is unavailable", 409)
    query["payload"]["snapshot_id"] = capture["result"]["watermark"]["snapshot_id"]
    request = {"protocol": "iqs.refresh_request/" + dialect, "operation": "request_refresh", "request_id": run_id + "-refresh",
               "consumer_id": admission["consumer_id"], "requested_at": _now(), "source_query": query, "subject_refs": [subject_ref],
               "field_ids": field_ids, "origin_task_id": run_id, "reason": "User-selected dashboard bank; original owner admission only"}
    recovery = record.get("recovery_subset")
    scope_refs = [{"work_item_id": row["work_item_id"], "decision_id": row["decision_id"]} for row in recovery["items"] if row["question_id"] in {q["id"] for q in selected_questions}] if recovery else None
    if recovery:
        request.update(cohort_id=run_id, work_decision_refs=scope_refs)
    _new(directory / "refresh.json", request)
    owner_common = [*common, "--iqs-release-root", expected["iqs_release_root"]]
    preview = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli", [*owner_common, "--request", str(directory / "refresh.json")])
    _new(directory / "owner-preview.json", preview)
    original = _owner_prepare(config, "refresh_record", {"preview_id": preview["preview_id"]},
                              iqs_release_root=expected["iqs_release_root"])
    if original.get("preview_id") != preview["preview_id"]:
        raise DashboardPrepareError("native_preview_scope_mismatch", "Owner returned another refresh preview", 502)
    cached=_cached_scope_result(original['owner_state'],selected_questions,subject_ref,
        cache_clock=policy.get('cache_clock','information_as_of'))
    if cached is not None:return {'status':'cached',**cached}
    if preview.get("status") != "ready":
        raise DashboardPrepareError("native_preview_not_ready", "Original owner preview is not ready", 409, {"preview": preview})
    install = {"protocol": "stockwiki.refresh_delegation_install/1.0.0", "workspace_root": str(Path(config["workspace_root"]).resolve()), "preview_id": preview["preview_id"],
               "preview_record_sha256": original["record_sha256"], "agent": options["agent"], "authorization_reference": options["authorization_reference"],
               "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=_delegation_ttl_seconds(config))).isoformat().replace("+00:00", "Z")}
    grant = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli",
                        [*owner_common, "--install-delegation-stdin"], input_value=install)
    _new(directory / "grant.json", grant)
    confirmation = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli", [*owner_common, "--confirm-delegated", preview["preview_id"],
        "--delegation-id", grant["grant_id"], "--idempotency-key", run_id])
    _new(directory / "confirmation.json", confirmation)
    admitted = _native_cli(config, "qa", "src.utils.quick_scan_refresh_admission_cli", ["--config", options["admission_config"], "--confirmation-id", confirmation["confirmation_id"]])
    _new(directory / "admission.json", admitted)
    if admitted.get("registered_with_executor") is not True:
        raise DashboardPrepareError("native_admission_not_registered", "Original executor did not register this confirmation", 409)
    inspect = {"entity_id": record["bank"]["entity_id"], "question_ids": [row["id"] for row in selected_questions],
               "scope_bindings": {row["id"]: {"scope": subject_ref["scope"], "scope_id": subject_ref["scope_id"]} for row in selected_questions},
               "policy_id": policy["qa"]["policy_id"], "route_id": policy["qa"]["route_id"], "provider_config_ref": policy["qa"]["provider_config_ref"], "model": policy["model"]}
    if targets is not None:
        inspect["ordered_route_targets"] = targets
    if recovery:
        inspect.update(cohort_id=run_id, work_decision_refs=scope_refs)
    _new(directory / "inspection-request.json", inspect)
    bundle = {"entity_id": record["bank"]["entity_id"], "company": record["bank"]["company"], "provider": policy["provider"],
              "company_preparation_id": record["preview_id"], "scope": subject_ref["scope"],
              "scope_id": subject_ref["scope_id"], "security_id": subject_ref["security_id"],
              "confirmation_id": confirmation["confirmation_id"],
              **{key: target[key] for key in ('questions', 'manifest', 'identity_snapshot', 'c06_authority', 'owner_config')},
              "admission_config": options["admission_config"], "inspection_request": str(directory / "inspection-request.json"), "inspection_schema_version": dialect,
              "spend_authorization": options["spend_authorization"], "runtime_dir": options["runtime_dir"], "pack_size": options.get("pack_size", 1),
              "thinking": options.get("thinking", True), "max_output_tokens": options.get("max_output_tokens", 8192)}
    if recovery:
        bundle.update(recovery_subset=copy.deepcopy(recovery))
    if recovery or record.get('selection',{}).get('question_ids') is not None:
        bundle.update(execution_question_ids=[q['id'] for q in selected_questions], execution_question_count=len(selected_questions))
    if options.get("search_policy"):
        bundle["search_policy"] = options["search_policy"]
    if options.get('shared_company_config'):
        bundle['shared_company_config'] = str(directory.parent/'shared-company-config.json')
    if 'work_lease_seconds' in options:
        bundle['work_lease_seconds'] = options['work_lease_seconds']
    if subject_ref["scope"] == "security":
        bundle["security_scope_id"] = subject_ref["security_id"]
    return {"bundle_id": run_id, "execution_bundle": bundle, "subject_ref": subject_ref, "question_count": len(selected_questions), "confirmation_id": confirmation["confirmation_id"], "admission": admitted}

def worker_main():
    if sys.argv[1:] != ["--worker"]:
        return 2
    def offline(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            raise RuntimeError("preparation_network_forbidden")
    sys.addaudithook(offline)
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise DashboardPrepareError("request_too_large", "Preparation request exceeds its limit")
        request = decode_owner_json(raw.decode("utf-8"))
        config = request["config"]
        if request["operation"] == "snapshot":
            result = _snapshot(config, request["payload"])
        elif request["operation"] == "bank_reuse":
            result = _reusable_bank(config, request["payload"])
        elif request['operation']=='cache_preview':
            result = _cache_preview(config,request['payload'])
        elif request["operation"] == "apply":
            result = _apply(config, request["payload"])
        else:
            raise DashboardPrepareError('operation_invalid','Unknown preparation worker operation')
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        code = getattr(error, "code", getattr(error, "error_code", "native_preparation_rejected"))
        details = {"exception_type": type(error).__name__, **(error.details if isinstance(error, DashboardPrepareError) else {})}
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", str(error)):
            details["native_reason"] = str(error)
        request_value = locals().get("request")
        if isinstance(request_value, dict) and request_value.get("operation") == "apply":
            directory = request_value.get("payload", {}).get("directory")
            if isinstance(directory, str):
                details["completed_phases"] = _phase_artifacts(directory)
        print(json.dumps({"ok": False, "error": {"code": code, "message": str(error) if isinstance(error, DashboardPrepareError) else "Original preparation rejected its input", "status": getattr(error, "status", 409),
             "details": details}}))
        return 2
