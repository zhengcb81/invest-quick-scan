"""Prepare company banks through original owner interfaces, without model calls.

Bank preview writes only immutable IQS candidates. Explicit apply records the
original owner route/capture/consent and admits it to StockQA's existing ledger.
It never fabricates identity/scope authority or creates a budget, model client or
work queue. Explicit issuer-only apply uses the original owner bootstrap API.
"""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = "pkg_0151a1e3b23fe462476b1d7329211d8887a79c161eb765a1e64c7dcda1b60d9a"
PROTOCOL = "iqs.dashboard-preparation/1.0.0"
MAX_BYTES = 16 * 1024 * 1024


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


def _timeouts(config):
    options = config.get("prepare", {})
    worker = options.get("worker_timeout_seconds", 900)
    native = options.get("native_timeout_seconds", 300)
    if (type(worker) is not int or not 60 <= worker <= 3600 or
            type(native) is not int or not 30 <= native <= 900 or native > worker):
        raise DashboardPrepareError("preparation_timeouts_invalid",
            "Use worker timeout 60–3600s, native timeout 30–900s, native no greater than worker", 503)
    return worker, native


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
        from dashboard_locks import control_lock, ControlBusyError
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
        interpreter = self.config.get("stockwiki_python") or sys.executable
        timeout = 60 if operation == "snapshot" else _timeouts(self.config)[0]
        try:
            completed = subprocess.run([interpreter, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                cwd=self.config["stockwiki_root"], env=_env(), input=_bytes({"operation": operation,
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
            response = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeError, ValueError) as error:
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
            gaps = self._execution_gaps()
            return {"available": True, "bank_preview_available": True, "native_prepare_configured": not gaps,
                    "gaps": gaps, "module_package_id": self.options.get("module_package_id", DEFAULT_PACKAGE),
                    "profiles": [{"profile_id": key, "entity_id": row.get("entity_id"), "label": row.get("label", key)}
                                 for key, row in self.options.get("routing_profiles", {}).items()],
                    "API_requests": 0, "dispatch_started": False}
        except DashboardPrepareError as error:
            return {"available": False, "bank_preview_available": False, "gaps": [error.code], "API_requests": 0}

    def _execution_gaps(self):
        missing = []
        owner_policy = Path(self.config["workspace_root"]) / "config/quick_scan_refresh.json"
        if not owner_policy.is_file():
            missing.append("native_prepare_owner_policy_missing")
        else:
            try:
                original_policy = _read(owner_policy)
                protocol = original_policy.get("protocol") if isinstance(original_policy, dict) else None
                if not isinstance(protocol, str) or not protocol.startswith("stockwiki.refresh_owner_policy/"):
                    missing.append("native_prepare_owner_policy_invalid")
                elif protocol not in {"stockwiki.refresh_owner_policy/1.0.0", "stockwiki.refresh_owner_policy/1.1.0"}:
                    missing.append("native_prepare_owner_dialect_not_supported")
            except (OSError, ValueError, TypeError):
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

    def _configuration_binding(self, selection):
        """Bind this preparation, not append-only UI bundle registrations."""
        keys = ("iqs_root", "stockwiki_root", "stockwiki_python", "stockqa_root", "stockqa_python",
                "workspace_root", "iqs_release_root")
        options = {key: value for key, value in self.options.items() if key != "routing_profiles"}
        profile_id = selection.get("profile_id")
        profile = self.options.get("routing_profiles", {}).get(profile_id) if profile_id else None
        selected_profile = {key: profile.get(key) for key in ("entity_id", "verified_facts", "user_policy")} if profile else None
        files = {}
        paths = [Path(self.config["workspace_root"]) / "config/quick_scan_refresh.json"]
        for key in ("admission_config", "spend_authorization", "search_policy"):
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
        if not isinstance(payload, dict) or set(payload) - {"entity_id", "as_of", "mode", "subject_key", "profile_id", "scope_selector", "security_id"}:
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
        sys.path.insert(0, str(Path(self.config["iqs_root"]) / "scripts"))
        import routing
        import question_sets
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
        route = routing.resolve_route_decision(route_input, package_id=self.options.get("module_package_id", DEFAULT_PACKAGE),
            user_policy=profile.get("user_policy"), now_utc=now, root=Path(self.config["iqs_root"]))
        directory.mkdir(parents=True, exist_ok=False)
        try:
            question_sets.compose_from_route(route, directory, now_utc=now,
                expected_route_decision_id=route["decision_id"], answer_format="standard-1")
            _new(directory / "identity.json", identity)
            _new(directory / "route.json", route)
            _new(directory / "native.json", native)
            manifest = _read(directory / "manifest.json")
            gaps = self._execution_gaps()
            if issuer["identity_state"] != "verified":
                gaps.append("route_identity_unverified")
            if binding is None and native.get("bootstrap") is None:
                gaps.append(native.get("subject_gap", "subject_authority_missing"))
            if len(listings) > 1 and not payload.get("security_id"):
                gaps.append("security_selection_required")
            record = {"protocol": PROTOCOL, "preview_id": preview_id, "created_at": now,
                      "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
                      "selection": payload, "snapshot_sha256": _snapshot_sha(native), "config_sha256": self._configuration_binding(payload),
                      "owner_snapshot_as_of": native["owner_snapshot_as_of"], "scope_as_of": native["scope_as_of"],
                      "files": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                for name in ("identity.json", "route.json", "native.json", "manifest.json", "questions.json")},
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
            if _now() >= record["expires_at"]:
                raise DashboardPrepareError("preview_expired", "Preparation preview expired", 409)
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


def _preview_route_anchor(routes, *, subject_key, entity_id, now_utc):
    """Read the original current ID solely as an expected-current CAS target.

    A stale identity-bound route is never executable authority. The original
    owner history permits a NEW validated route to replace it on explicit
    apply, preserving the old immutable snapshot and subject revision.
    """
    try:
        value = routes.get_current_anchor(subject_key=subject_key, scope="entity", scope_id=entity_id, now_utc=now_utc)
    except Exception as error:
        code = getattr(error, "code", None)
        if code == "route_current_unavailable":
            return None
        if code != "route_identity_changed":
            raise
        history = routes.current_history(subject_key=subject_key, scope="entity", scope_id=entity_id)
        invalid = DashboardPrepareError("owner_route_rebind_unavailable",
            "Original route history needs inspection before preparing a new identity revision", 409)
        if not isinstance(history, list) or not history:
            raise invalid
        previous = None
        for version, row in enumerate(history, 1):
            if (not isinstance(row, dict) or type(row.get("version")) is not int or row["version"] != version
                    or (row.get("subject_key"), row.get("scope"), row.get("scope_id")) != (subject_key, "entity", entity_id)
                    or not isinstance(row.get("decision_id"), str)
                    or not re.fullmatch(r"route_[a-f0-9]{64}", row["decision_id"])
                    or "previous_decision_id" not in row or row["previous_decision_id"] != previous):
                raise invalid
            previous = row["decision_id"]
        row = history[-1]
        # The original public getter verifies immutable route/manifest/metadata
        # hashes. A missing/corrupt snapshot must not become an empty anchor.
        snapshot = routes.get_snapshot(row["decision_id"])
        if (not isinstance(snapshot, dict) or snapshot.get("decision_id") != row["decision_id"]
                or (snapshot.get("subject_key"), snapshot.get("scope"), snapshot.get("scope_id"), snapshot.get("entity_id"))
                != (subject_key, "entity", entity_id, entity_id)):
            raise invalid
        return {"decision_id": row["decision_id"], "anchor_version": row["version"]}
    return {"decision_id": value["expected_decision_id"], "anchor_version": value["anchor_version"]}


def _snapshot(config, payload):
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    from stockwiki.identity_g2b import build_identity_request
    from stockwiki.identity_receipts import IdentityReceiptStore
    from stockwiki.market_registry import MarketRegistryStore
    from stockwiki.ui_quick_scan import build_quick_scan_entity
    from stockwiki.quick_scan_routes import QuickScanRouteStore
    from stockwiki.quick_scan_route_validation import IqsRouteValidator
    paths = WorkspacePaths.from_root(Path(config["workspace_root"]))
    identity = QuickScanStore(paths)
    # G2b auxiliary stores have legacy lazy-initialization methods; refuse a
    # missing original database before invoking them so preview stays read-only.
    for store in (identity, IdentityReceiptStore(paths), MarketRegistryStore(paths)):
        if not store.database_path.is_file():
            raise DashboardPrepareError("owner_identity_source_missing", "Original identity sources are not initialized", 503)
    owner_snapshot_as_of = payload.get("owner_snapshot_as_of")
    scope_as_of = payload.get("scope_as_of")
    if not isinstance(owner_snapshot_as_of, str) or (payload.get("scope_selector") == "issuer_only" and scope_as_of != owner_snapshot_as_of):
        raise DashboardPrepareError("preview_stale", "Original owner time is not frozen; create a new bank preview", 409)
    request = build_identity_request(identity, IdentityReceiptStore(paths), MarketRegistryStore(paths),
                                    entity_id=payload["entity_id"], as_of=owner_snapshot_as_of)
    try:
        from . import contract_validation as cv
    except ImportError:
        import contract_validation as cv
    # Validate the exact native owner DTO before selecting a listing, subject
    # or question route. A verified label alone cannot satisfy this contract;
    # missing attributes must be repaired at the original owner, never filled
    # into an immutable preview or promoted by a caller-supplied assertion.
    try:
        context = request["trusted_context"]
        cv.validate_entity(request["payload"],
            trusted_identity_receipts=context["identity_receipts"],
            trusted_source_bindings=context["source_bindings"],
            trusted_market_registry=context["market_registry"],
            wire_profile="stockwiki-g2b/1.1.0")
    except (ValueError, KeyError, TypeError, AttributeError, cv.JsonSchemaValidationError):
        raise DashboardPrepareError("owner_identity_contract_invalid",
            "Complete or correct the original identity attributes and evidence, then create a new bank preview", 409,
            {"required_action": "repair_original_identity_and_create_new_preview"}) from None
    listings = [row for row in request["payload"]["listings"] if row.get("listing_status") in {"active", "suspended"}]
    if payload.get("security_id"):
        listings = [row for row in listings if row["security_id"] == payload["security_id"]]
    if not listings:
        raise DashboardPrepareError("security_not_registered", "Choose a current original security of this entity", 409)
    listing = sorted(listings, key=lambda row: (row["market"], row["listing_id"]))[0]
    listing_binding = None
    if request["payload"]["identity_state"] == "verified":
        from stockwiki.identity_snapshot import resolve_listing_binding
        listing_binding = resolve_listing_binding(identity, entity_id=payload["entity_id"], security_id=listing["security_id"],
            listing_id=listing["listing_id"], identity_revision=request["payload"]["identity_revision"], as_of=_now())
    detail = build_quick_scan_entity(paths, payload["entity_id"])
    subjects = detail.get("subjects", [])
    bootstrap, bootstrap_gap = None, None
    if payload.get("scope_selector") == "issuer_only" and request["payload"]["identity_state"] == "verified":
        try:
            from stockwiki.quick_scan_issuer_bootstrap import IssuerScopeBootstrap, IssuerBootstrapError
        except ImportError:
            bootstrap_gap = "issuer_bootstrap_unavailable"
        else:
            try:
                bootstrap = IssuerScopeBootstrap(paths).preview(entity_id=payload["entity_id"],
                    scope_as_of=scope_as_of, authorization_ref=config.get("prepare", {}).get("authorization_reference", ""))
            except IssuerBootstrapError as error:
                bootstrap_gap = error.error_code
        # A prior explicit apply can already have created this exact legal
        # issuer scope. Read its real anchor so another preparation uses CAS
        # against that existing owner state, rather than assuming no anchor.
        selected = [row for row in subjects if bootstrap and
                    row["analysis_subject_id"] + "@" + str(row["analysis_subject_revision"]) == bootstrap["subject_key"]]
    elif payload.get("subject_key"):
        selected = [row for row in subjects if row["analysis_subject_id"] + "@" + str(row["analysis_subject_revision"]) == payload["subject_key"]]
        if len(selected) != 1:
            raise DashboardPrepareError("subject_not_registered", "Choose an original subject of this entity", 409)
    else:
        selected = subjects if len(subjects) == 1 else []
    binding, anchor, gap = None, None, bootstrap_gap or ("subject_selection_required" if len(subjects) > 1 else "subject_authority_missing")
    if selected and request["payload"]["identity_state"] == "verified":
        key = selected[0]["analysis_subject_id"] + "@" + str(selected[0]["analysis_subject_revision"])
        routes = QuickScanRouteStore(identity, validator=IqsRouteValidator(Path(config["iqs_root"]), runs_dir=paths.runs_dir,
            release_root=Path(config.get("iqs_release_root", config["iqs_root"]))))
        binding = routes.identity_binding(key)
        anchor = _preview_route_anchor(routes, subject_key=key, entity_id=payload["entity_id"], now_utc=_now())
        gap = None
    return {"identity": request, "subjects": subjects, "binding": binding, "anchor": anchor, "subject_gap": gap, "bootstrap": bootstrap,
            "owner_snapshot_as_of": owner_snapshot_as_of, "scope_as_of": scope_as_of,
            "selected_listing": listing, "listing_binding": listing_binding}


def _native_cli(config, kind, module, arguments):
    code_root = config["stockwiki_root" if kind == "wiki" else "stockqa_root"]
    interpreter = config.get("stockwiki_python" if kind == "wiki" else "stockqa_python") or sys.executable
    env = _env()
    env["PYTHONPATH"] = code_root
    cwd = config.get("prepare", {}).get("runtime_dir", code_root) if kind == "qa" else code_root
    timeout = _timeouts(config)[1]
    stage = [value for value in arguments if value in {"--request", "--install-delegation", "--confirm-delegated", "--confirmation-id"}]
    details = {"native_module": module, "native_selectors": stage, "timeout_seconds": timeout}
    try:
        done = subprocess.run([interpreter, "-B", "-X", "utf8", "-m", module, *arguments], cwd=cwd, env=env,
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
        result = json.loads(done.stdout.decode("utf-8"))
    except (UnicodeError, ValueError) as error:
        raise DashboardPrepareError("native_response_invalid", "Original native command did not return JSON", 502,
            {**details, "exception_type": type(error).__name__}) from None
    if not isinstance(result, dict):
        raise DashboardPrepareError("native_response_invalid", "Original native command did not return an object", 502, details)
    if done.returncode:
        code = result.get("error_code", result.get("reason"))
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", code):
            code = "native_preparation_rejected"
        raise DashboardPrepareError(code, "Original native command refused preparation", 409,
            {**details, "native_error_code": code})
    return result


def _apply(config, payload):
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    from stockwiki.quick_scan_routes import QuickScanRouteStore
    from stockwiki.quick_scan_route_validation import IqsRouteValidator
    from stockwiki.quick_scan_refresh_records import RefreshRecordStore
    options, directory = config["prepare"], Path(payload["directory"])
    record, native = _read(directory / "preview.json"), _read(directory / "native.json")
    manifest, route = _read(directory / "manifest.json"), _read(directory / "route.json")
    admission = _read(options["admission_config"])
    paths = WorkspacePaths.from_root(Path(config["workspace_root"]))
    policy = _read(paths.config_dir / "quick_scan_refresh.json")
    dialect = policy["protocol"].split("/")[-1]
    if dialect not in {"1.0.0", "1.1.0"}:
        raise DashboardPrepareError("registered_control_scope_required", "This owner policy requires an exact original work/exposure control; no fallback to a new generation is allowed", 409)
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
    routes = QuickScanRouteStore(QuickScanStore(paths), validator=IqsRouteValidator(Path(config["iqs_root"]), runs_dir=directory / "validation",
        release_root=Path(expected["iqs_release_root"])))
    frozen_dir = directory
    if native.get("bootstrap"):
        from stockwiki.quick_scan_issuer_bootstrap import IssuerScopeBootstrap
        bootstrap = IssuerScopeBootstrap(paths).apply(entity_id=record["bank"]["entity_id"],
            scope_as_of=native["scope_as_of"], authorization_ref=options["authorization_reference"],
            expected_preview_sha256=native["bootstrap"]["preview_sha256"])
        _new(directory / "bootstrap.json", bootstrap)
        binding = routes.identity_binding(bootstrap["subject_key"])
        # A draft subject was never a trust root. After ORIGINAL owner apply,
        # freeze a new final route/bank linked to the untouched initial preview.
        sys.path.insert(0, str(Path(config["iqs_root"]) / "scripts"))
        import routing
        import question_sets
        final_input = {key: route["profile_context"][key] for key in ("entity_id", "company", "ticker", "exchange", "as_of", "security_id")}
        final_input.update(identity_ref=binding["route_identity_ref"], requested_mode=record["bank"]["mode"])
        selected_profile = options.get("routing_profiles", {}).get(record["selection"].get("profile_id"), {})
        final_input["verified_facts"] = selected_profile.get("verified_facts", [])
        route = routing.resolve_route_decision(final_input, package_id=record["bank"]["module_package_id"],
            user_policy=selected_profile.get("user_policy"), now_utc=_now(), root=Path(config["iqs_root"]))
        frozen_dir = directory / "final"
        question_sets.compose_from_route(route, frozen_dir, now_utc=_now(), expected_route_decision_id=route["decision_id"], answer_format="standard-1")
        _new(frozen_dir / "route.json", route)
        _new_raw(frozen_dir / "identity.json", (directory / "identity.json").read_bytes())
        _new(frozen_dir / "preparation-lineage.json", {"draft_preview_id": record["preview_id"], "draft_preview_token": record["preview_token"],
            "draft_manifest_sha256": record["files"]["manifest.json"], "original_bootstrap_preview_sha256": native["bootstrap"]["preview_sha256"],
            "subject_key": binding["subject_key"], "scope_semantics": bootstrap.get("scope_semantics"), "authority_from_draft": False})
        manifest = _read(frozen_dir / "manifest.json")
        if [row["id"] for row in manifest["questions"]] != record["bank"]["question_ids"]:
            raise DashboardPrepareError("prepared_bank_changed", "The original applied scope changed the previewed question selection", 409)
    routes.record_snapshot((frozen_dir / "route.json").read_bytes(), (frozen_dir / "manifest.json").read_bytes(),
                          subject_key=binding["subject_key"], expected_decision_id=route["decision_id"])
    routes.set_current(route["decision_id"], subject_key=binding["subject_key"],
                       expected_current_decision_id=(native["anchor"] or {}).get("decision_id"), now_utc=_now())
    # Identified transport, metadata and exact original identity bytes are
    # generated from the frozen release, never manually assembled answers.
    sys.path.insert(0, str(Path(config["iqs_root"]) / "scripts"))
    import c06_authority
    from frozen_release_projection import create_question_config
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
        ref = authority["observation_context"]["questions"][question["id"]]["subject_binding"]["subject_ref"]
        grouped.setdefault(_sha(ref), {"ref": ref, "questions": []})["questions"].append(question)
    executions = []
    expected_scopes = [{"scope": group["ref"]["scope"], "scope_id": group["ref"]["scope_id"]} for group in grouped.values()]
    for index, group in enumerate(grouped.values(), 1):
        subject_ref = group["ref"]
        target = Path(admission["execution_inputs_root"]) / ("subject_" + _sha(subject_ref))
        target.mkdir(parents=True, exist_ok=True)
        owner_config = {"protocol": "stockqa.owner_refresh_config/1.0.0", **expected, "subject_key": binding["subject_key"],
                        "scope": "entity", "scope_id": record["bank"]["entity_id"], "ttl_hours": policy["ttl_hours"], "runs_dir": str(directory / "owner-transport")}
        Path(owner_config["runs_dir"]).mkdir(parents=True, exist_ok=True)
        for name in ("manifest.json", "identity.json"):
            _new_raw(target / name, (frozen_dir / name).read_bytes())
        for name, value in {"authority.json": authority, "owner-config.json": owner_config,
                            "questions.json": create_question_config(manifest, root=Path(expected["iqs_release_root"]))}.items():
            _new(target / name, value)
        scope_dir = directory / ("scope-" + str(index) + "-" + subject_ref["scope"])
        scope_dir.mkdir(parents=True, exist_ok=True)
        item = _prepare_scope(config, scope_dir, record, manifest, group["questions"], target, subject_ref, policy,
                              admission, paths, expected, run_id + "-" + str(index))
        item["execution_bundle"]["expected_scope_bindings"] = copy.deepcopy(expected_scopes)
        _new(scope_dir / "prepared-scope.json", item)
        executions.append(item)
    first = executions[0]
    result = {"protocol": PROTOCOL, "status": "prepared", "bundle_id": first["bundle_id"], "bundle": first["execution_bundle"],
              "execution_bundle": first["execution_bundle"], "execution_bundles": executions,
              "question_count_total": sum(item["question_count"] for item in executions),
              "confirmation_id": first["confirmation_id"], "admission": first["admission"],
              "API_requests": 0, "dispatch_started": False, "financial_accuracy_proven": False,
              "owner_state_changed": True, "meaning": "All question scopes registered with native owner; execution still requires original current checks"}

    # The child publishes before writing stdout. Lost HTTP/process responses can
    # reconcile this exact result without repeating any original owner writes.
    _new(directory / "applied.json", result)
    return result


def _prepare_scope(config, directory, record, manifest, selected_questions, target, subject_ref, policy, admission, paths, expected, run_id):
    from stockwiki.quick_scan_refresh_records import RefreshRecordStore
    options = config["prepare"]
    dialect = policy["protocol"].split("/")[-1]
    field_ids = sorted({row.get("field_id", row["metric_id"]) for row in selected_questions})
    query = {"message_type": "request", "schema_version": "2.6.0" if dialect == "1.1.0" else "2.0.0", "request_id": run_id + "-query",
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
    _new(directory / "refresh.json", request)
    owner_common = [*common, "--iqs-release-root", expected["iqs_release_root"]]
    preview = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli", [*owner_common, "--request", str(directory / "refresh.json")])
    _new(directory / "owner-preview.json", preview)
    if preview.get("status") != "ready":
        raise DashboardPrepareError("native_preview_not_ready", "Original owner preview is not ready", 409, {"preview": preview})
    original = RefreshRecordStore(paths).load(preview["preview_id"])
    install = {"protocol": "stockwiki.refresh_delegation_install/1.0.0", "workspace_root": str(paths.root), "preview_id": preview["preview_id"],
               "preview_record_sha256": original["record_sha256"], "agent": options["agent"], "authorization_reference": options["authorization_reference"],
               "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")}
    # This is the original fixed local owner install file. Its previous bytes
    # are restored after install/confirm; immutable original grants remain.
    install_path = paths.config_dir / "quick_scan_delegation_install.json"
    old = install_path.read_bytes() if install_path.exists() else None
    try:
        install_path.write_bytes(_bytes(install) + b"\n")
        grant = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli", [*owner_common, "--install-delegation"])
        _new(directory / "grant.json", grant)
        confirmation = _native_cli(config, "wiki", "stockwiki.quick_scan_refresh_owner_cli", [*owner_common, "--confirm-delegated", preview["preview_id"],
            "--delegation-id", grant["grant_id"], "--idempotency-key", run_id])
        _new(directory / "confirmation.json", confirmation)
    finally:
        if install_path.exists() and install_path.read_bytes() == _bytes(install) + b"\n":
            if old is None:
                install_path.unlink()
            else:
                install_path.write_bytes(old)
    admitted = _native_cli(config, "qa", "src.utils.quick_scan_refresh_admission_cli", ["--config", options["admission_config"], "--confirmation-id", confirmation["confirmation_id"]])
    _new(directory / "admission.json", admitted)
    if admitted.get("registered_with_executor") is not True:
        raise DashboardPrepareError("native_admission_not_registered", "Original executor did not register this confirmation", 409)
    inspect = {"entity_id": record["bank"]["entity_id"], "question_ids": [row["id"] for row in selected_questions],
               "scope_bindings": {row["id"]: {"scope": subject_ref["scope"], "scope_id": subject_ref["scope_id"]} for row in selected_questions},
               "policy_id": policy["qa"]["policy_id"], "route_id": policy["qa"]["route_id"], "provider_config_ref": policy["qa"]["provider_config_ref"], "model": policy["model"]}
    _new(directory / "inspection-request.json", inspect)
    bundle = {"entity_id": record["bank"]["entity_id"], "company": record["bank"]["company"], "provider": policy["provider"],
              "company_preparation_id": record["preview_id"], "scope": subject_ref["scope"],
              "scope_id": subject_ref["scope_id"], "security_id": subject_ref["security_id"],
              "confirmation_id": confirmation["confirmation_id"], "questions": str(target / "questions.json"), "manifest": str(target / "manifest.json"),
              "identity_snapshot": str(target / "identity.json"), "c06_authority": str(target / "authority.json"), "owner_config": str(target / "owner-config.json"),
              "admission_config": options["admission_config"], "inspection_request": str(directory / "inspection-request.json"), "inspection_schema_version": dialect,
              "spend_authorization": options["spend_authorization"], "runtime_dir": options["runtime_dir"], "pack_size": options.get("pack_size", 1),
              "thinking": options.get("thinking", True), "max_output_tokens": options.get("max_output_tokens", 8192)}
    if options.get("search_policy"):
        bundle["search_policy"] = options["search_policy"]
    if subject_ref["scope"] == "security":
        bundle["security_scope_id"] = subject_ref["security_id"]
    return {"bundle_id": run_id, "execution_bundle": bundle, "subject_ref": subject_ref, "question_count": len(selected_questions), "confirmation_id": confirmation["confirmation_id"], "admission": admitted}

def _main():
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
        request = json.loads(raw.decode("utf-8"))
        config = request["config"]
        sys.path.insert(0, config["stockwiki_root"])
        result = _snapshot(config, request["payload"]) if request["operation"] == "snapshot" else _apply(config, request["payload"])
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


if __name__ == "__main__":
    raise SystemExit(_main())
