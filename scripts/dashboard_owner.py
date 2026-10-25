"""Local dashboard adapter over StockWiki's original public owner interfaces.

Only server deployment config supplies code/workspace/bundle paths. StockWiki
imports happen in a fresh interpreter; this module does not open SQLite, mint
identities, migrate stores, execute model work, or reinterpret qualifications.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

PROTOCOL = "iqs.dashboard.owner/1.0.0"
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
_ROOTS = ("stockwiki_root", "workspace_root", "iqs_root")
_MAX_BYTES = 16 * 1024 * 1024


class DashboardOwnerError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details=None):
        self.code, self.message, self.status = code, message, status
        self.details = dict(details or {})
        super().__init__(message)

    def as_dict(self):
        return {"code": self.code, "message": self.message,
                "status": self.status, "details": self.details}


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _identifier(value, name):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise DashboardOwnerError("invalid_identifier", f"{name} must be an exact registered identifier")
    return value


def _payload(value, allowed):
    if not isinstance(value, dict):
        raise DashboardOwnerError("invalid_payload", "Expected a JSON object")
    unknown = set(value) - set(allowed)
    if unknown:
        raise DashboardOwnerError("unknown_field", "Unsupported payload field", details={"fields": sorted(unknown)})
    return dict(value)


def _env():
    result = dict(os.environ)
    for key in list(result):
        upper = key.upper()
        if any(term in upper for term in ("API_KEY", "APIKEY", "TOKEN", "SECRET", "PASSWORD")):
            result.pop(key, None)
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "STOCKQA_RUN_LIVE_E2E"):
        result.pop(key, None)
    result.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return result


class OwnerGateway:
    """Trust paths only from deployment config, never request JSON."""
    def __init__(self, config: dict):
        if not isinstance(config, dict):
            raise DashboardOwnerError("deployment_invalid", "Owner deployment must be an object", 503)
        self.config = copy.deepcopy(config)

    def _deployment(self):
        config = copy.deepcopy(self.config)
        missing = [key for key in (*_ROOTS, "stockwiki_python") if not config.get(key)]
        if missing:
            raise DashboardOwnerError("owner_not_configured", "StockWiki owner is not configured", 503,
                                      {"missing": missing})
        for key in _ROOTS:
            config[key] = str(Path(config[key]).expanduser().resolve())
            if not Path(config[key]).is_dir():
                raise DashboardOwnerError("deployment_path_missing", f"Configured {key} does not exist", 503)
        executable = Path(config["stockwiki_python"]).expanduser().resolve()
        if not executable.is_file():
            raise DashboardOwnerError("owner_python_missing", "Configured StockWiki interpreter is absent", 503)
        config["stockwiki_python"] = str(executable)
        if not (Path(config["stockwiki_root"]) / "stockwiki" / "quick_scan_store.py").is_file():
            raise DashboardOwnerError("owner_code_missing", "StockWiki code root is invalid", 503)
        timeout = config.get("timeout_seconds", 30)
        if type(timeout) not in (int, float) or not 1 <= timeout <= 180:
            raise DashboardOwnerError("deployment_invalid", "timeout_seconds must be between 1 and 180", 503)
        return config

    def _call(self, operation, payload=None):
        config = self._deployment()
        request = {"config": config, "operation": operation, "payload": payload or {}}
        try:
            result = subprocess.run([config["stockwiki_python"], "-B", str(Path(__file__).resolve()), "--worker"],
                                    cwd=config["stockwiki_root"], input=json.dumps(request, ensure_ascii=False),
                                    text=True, encoding="utf-8", errors="strict", capture_output=True,
                                    timeout=config.get("timeout_seconds", 30), env=_env())
        except subprocess.TimeoutExpired as error:
            raise DashboardOwnerError("owner_timeout", "StockWiki owner request timed out", 504) from error
        except OSError as error:
            raise DashboardOwnerError("owner_process_unavailable", "Cannot start StockWiki interpreter", 503) from error
        if len(result.stdout.encode("utf-8")) > _MAX_BYTES:
            raise DashboardOwnerError("owner_response_too_large", "StockWiki response exceeded the dashboard limit", 502)
        try:
            response = _json(result.stdout)
            if not isinstance(response, dict) or response.get("protocol") != PROTOCOL:
                raise ValueError("invalid_worker_envelope")
        except (ValueError, UnicodeError) as error:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki worker returned an invalid response", 502) from error
        if response.get("error"):
            value = response["error"]
            raise DashboardOwnerError(value["code"], value["message"], value["status"], value.get("details"))
        if result.returncode != 0:
            raise DashboardOwnerError("owner_process_failed", "StockWiki worker failed", 502)
        return response["result"]

    def status(self):
        try:
            return self._call("status")
        except DashboardOwnerError as error:
            return {"protocol": PROTOCOL, "available": False, "status": "unavailable",
                    "error": error.as_dict(), "network_calls": 0, "llm_calls": 0}

    def search(self, query="", limit=50, offset=0, filters=None, *, conditions=None,
               condition_combine="all", snapshot=None, view="all_relevant"):
        if not isinstance(query, str) or len(query) > 1000:
            raise DashboardOwnerError("query_invalid", "Query must be a string of at most 1000 characters")
        if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or offset < 0:
            raise DashboardOwnerError("pagination_invalid", "limit must be 1–100 and offset must be nonnegative")
        if filters is not None and not isinstance(filters, dict):
            raise DashboardOwnerError("filters_invalid", "Filters must be an object")
        return self._call("search", {"query": query, "limit": limit, "offset": offset, "filters": filters,
                                     "conditions": conditions, "condition_combine": condition_combine,
                                     "snapshot": snapshot, "view": view})

    def coverage(self):
        return self._call("coverage")

    def entity(self, entity_id):
        return self._call("entity", {"entity_id": _identifier(entity_id, "entity_id")})

    def history(self, entity_id):
        return self._call("history", {"entity_id": _identifier(entity_id, "entity_id")})

    def facts(self, entity_id):
        return self._call("facts", {"entity_id": _identifier(entity_id, "entity_id")})

    def universe_list(self, universe_id="default"):
        return self._call("universe_list", {"universe_id": _identifier(universe_id, "universe_id")})

    def universe_preview(self, payload):
        return self._call("universe_preview", _payload(payload, {
            "action", "entity_id", "query", "universe_id", "reason", "priority", "pin"}))

    def universe_apply(self, payload):
        return self._call("universe_apply", _payload(payload, {
            "action", "entity_id", "universe_id", "reason", "priority", "pin", "preview_token"}))

    def delivery_status(self, package_id=None):
        return self._call("delivery_status", {"package_id": _identifier(package_id, "package_id") if package_id else None})

    def import_preview(self, payload):
        return self._call("import_preview", _payload(payload, {"bundle_id"}))

    def import_apply(self, payload):
        return self._call("import_apply", _payload(payload, {"bundle_id", "preview_token"}))


def _original_error(error):
    import sqlite3
    if isinstance(error, DashboardOwnerError):
        return error
    text = str(error)
    code = getattr(error, "error_code", getattr(error, "code", None))
    if isinstance(error, sqlite3.OperationalError) and any(word in text.lower() for word in ("locked", "busy")):
        return DashboardOwnerError("owner_busy", "StockWiki owner is busy; retry later", 503)
    if code == "entity_not_found":
        return DashboardOwnerError(code, text, 404)
    if isinstance(error, sqlite3.Error):
        return DashboardOwnerError("owner_store_unreadable", "StockWiki store cannot be read", 503)
    if isinstance(error, (FileNotFoundError, PermissionError)):
        return DashboardOwnerError("owner_file_unavailable", "A configured owner file is missing or unreadable", 503)
    return DashboardOwnerError(str(code or "owner_rejected"), text[:1500], 400)


def _require_store(store, name):
    if not store.database_path.is_file():
        raise DashboardOwnerError("owner_database_missing", f"StockWiki {name} store is not initialized", 503)


def _bundle(config, bundle_id):
    _identifier(bundle_id, "bundle_id")
    bundles = config.get("bundles", {})
    record = bundles.get(bundle_id) if isinstance(bundles, dict) else None
    if not isinstance(record, dict):
        raise DashboardOwnerError("bundle_not_registered", "Bundle is not registered in server deployment", 404)
    data = {}
    for key in ("package", "release"):
        if not record.get(key):
            raise DashboardOwnerError("bundle_configuration_invalid", "Registered bundle is incomplete", 503)
        path = Path(record[key]).expanduser().resolve(strict=True)
        if not path.is_file() or path.stat().st_size > _MAX_BYTES:
            raise DashboardOwnerError("bundle_file_invalid", "Registered bundle file is unavailable or too large", 503)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        expected = record.get(key + "_sha256")
        if expected is not None and digest != expected:
            raise DashboardOwnerError("bundle_hash_mismatch", "Registered bundle changed", 409)
        data[key], data[key + "_sha256"] = _json(raw.decode("utf-8")), digest
    return data


def _member_display(member, registered):
    """Add human labels by the exact original ID; never resolve identity by name."""
    result = copy.deepcopy(member)
    if registered is None:
        return {**result, "canonical_name": None, "identity_state": None, "securities": [],
                "identity_display_available": False, "identity_display_gap": "entity_not_found"}
    if registered.get("entity_id") != member.get("entity_id"):
        raise DashboardOwnerError("identity_display_mismatch", "Original identity did not match the member ID", 503)
    name = registered.get("canonical_name")
    return {**result, "canonical_name": name if isinstance(name, str) and name.strip() else None,
            "identity_state": registered.get("identity_state"),
            "identity_revision": registered.get("identity_revision"),
            "securities": copy.deepcopy(registered.get("securities", [])),
            "identity_display_available": isinstance(name, str) and bool(name.strip()),
            "identity_display_source": "StockWiki.get_entity"}


def _library_summary(coverage, runtime=None):
    """Counts from original public projections, never full-scan/quality claims."""
    total = coverage.get("total_entities")
    if type(total) is not int or total < 0:
        raise DashboardOwnerError("coverage_projection_invalid", "Original library count is not available", 503)
    summary = {"scope": "owner_library", "total_entities": total,
               "available": runtime is not None, "observed_entities": None, "missing_entities": None,
               "observation_count": None, "scored_field_entries": None, "answered_field_entries": None,
               "score_observations": None, "fact_observations": None,
               "financial_accuracy_proven": False, "full_company_completion_known": False,
               "meaning": "Stored records and current W09 field entries, not completed company scans or qualified answers"}
    if runtime is None:
        return {**summary, "reason": "owner_observation_database_missing"}
    observed, count = runtime.get("distinct_companies"), runtime.get("observations")
    if (type(observed) is not int or type(count) is not int or not 0 <= observed <= total
            or count < observed):
        raise DashboardOwnerError("coverage_projection_invalid", "Original coverage counts are inconsistent", 503)
    fields = coverage.get("by_field", {})
    if not isinstance(fields, dict) or any(not isinstance(row, dict) for row in fields.values()):
        raise DashboardOwnerError("coverage_projection_invalid", "Original field coverage is invalid", 503)
    for row in fields.values():
        if any(type(row.get(key)) is not int or row[key] < 0 for key in ("scored", "answered")):
            raise DashboardOwnerError("coverage_projection_invalid", "Original field counts are invalid", 503)
    summary.update(observed_entities=observed, missing_entities=total-observed, observation_count=count,
                   scored_field_entries=sum(row["scored"] for row in fields.values()),
                   answered_field_entries=sum(row["answered"] for row in fields.values()),
                   source="StockWiki.coverage + StockWiki.project_runtime_status")
    return summary


def _owner_worker(config, operation, payload):
    # Trusted deployment path, isolated interpreter: never contaminate server sys.path.
    sys.path.insert(0, config["stockwiki_root"])
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    from stockwiki.quick_scan_observations import QuickScanObservationStore
    from stockwiki.ui_quick_scan import (build_quick_scan_capabilities, build_quick_scan_search,
                                        build_quick_scan_entity, build_quick_scan_coverage)
    paths = WorkspacePaths.from_root(Path(config["workspace_root"]))
    identity, observations = QuickScanStore(paths), QuickScanObservationStore(paths)
    _require_store(identity, "identity")

    def entity(entity_id):
        value = identity.get_entity(entity_id)
        if value is None:
            raise DashboardOwnerError("entity_not_found", "No registered entity has this ID", 404)
        return value

    def universe(universe_id):
        result = identity.get_universe(universe_id)
        if result is None:
            raise DashboardOwnerError("universe_not_found", "No registered universe has this ID", 404)
        return result

    def universe_id(value="default"):
        value = config.get("universe_id", "default") if value == "default" else value
        return _identifier(value, "universe_id")

    if operation == "status":
        source = build_quick_scan_search(paths, {"page_size": 1})
        return {"protocol": PROTOCOL, "available": True, "status": "available",
                "source_protocol": source["protocol"], "c06_envelope_validated": False,
                "store_id": observations.store_id, "workspace_kind": config.get("workspace_kind", "unclassified"),
                "entity_count": source["total"], "observations_available": observations.database_path.is_file(),
                "capabilities": build_quick_scan_capabilities(paths),
                "registered_bundles": sorted(config.get("bundles", {})),
                "network_calls": 0, "llm_calls": 0, "automatic_migration": False}
    if operation == "search":
        # The public owner owns filters and pagination. Two adjacent pages cover
        # an arbitrary offset without duplicating its selection/rule engine.
        size, offset = payload["limit"], payload["offset"]
        page, start = offset // size + 1, offset % size
        request = {"text": payload["query"], "filters": payload["filters"], "page": page, "page_size": size,
                   "conditions": payload.get("conditions"), "condition_combine": payload.get("condition_combine", "all"),
                   "snapshot": payload.get("snapshot"), "view": payload.get("view", "all_relevant")}
        result = build_quick_scan_search(paths, request)
        rows = result["rows"][start:]
        if start and result["next_page"] is not None:
            request.update(page=page + 1, snapshot=result["snapshot"])
            following = build_quick_scan_search(paths, request)
            rows += following["rows"][:size - len(rows)]
            if following["refresh_recommended"]:
                result["refresh_recommended"] = True
        result.update(rows=rows, offset=offset, limit=size, next_offset=offset + size if offset + size < result["total"] else None)
        return result
    if operation == "coverage":
        result = build_quick_scan_coverage(paths)
        runtime = None
        if observations.database_path.is_file():
            from stockwiki.quick_scan_delivery import project_runtime_status
            runtime = project_runtime_status(observations)
        return {**result, "library_summary": _library_summary(result, runtime)}
    if operation == "entity":
        return build_quick_scan_entity(paths, payload["entity_id"])
    if operation in {"history", "facts"}:
        entity(payload["entity_id"])
        if not observations.database_path.is_file():
            return {"protocol": PROTOCOL, "entity_id": payload["entity_id"], "observations": [], "count": 0,
                    "available": False, "reason": "owner_observation_database_missing",
                    "complete": False, "relations_supported": False, "network_calls": 0, "llm_calls": 0}
        records = observations.observations_for_entity(payload["entity_id"])
        if operation == "facts":
            records = [row for row in records if row["payload"].get("answer", {}).get("response_kind") == "fact"]
        return {"protocol": PROTOCOL, "source_protocol": "stockwiki_observation_store",
                "entity_id": payload["entity_id"], "observations": records, "count": len(records),
                "available": True, "complete": True, "relations_supported": False,
                "meaning": "Stored original observations; not a cross-version comparability decision",
                "network_calls": 0, "llm_calls": 0}
    if operation == "universe_list":
        selected = universe_id(payload.get("universe_id", "default"))
        data = universe(selected)
        members = [_member_display(row, identity.get_entity(row["entity_id"]))
                   for row in identity.list_members(selected)]
        return {"protocol": PROTOCOL, "universe": data, "members": members, "member_count": len(members),
                "network_calls": 0, "llm_calls": 0}
    if operation in {"universe_preview", "universe_apply"}:
        selected = universe_id(payload.get("universe_id", "default"))
        universe(selected)
        if not payload.get("entity_id"):
            query = payload.get("query")
            if not isinstance(query, str) or not query.strip() or len(query) > 1000:
                raise DashboardOwnerError("entity_id_required", "Choose an existing entity ID; names do not authorize identity changes")
            candidates = build_quick_scan_search(paths, {"text": query, "page_size": 100})
            return {"protocol": PROTOCOL, "status": "ambiguous" if candidates["total"] > 1 else "choose_entity" if candidates["total"] else "unresolved",
                    "candidates": candidates["rows"], "can_apply": False, "identity_changed": False}
        if payload.get("query"):
            raise DashboardOwnerError("invalid_payload", "Use either entity_id or a candidate query")
        selected_entity = _identifier(payload["entity_id"], "entity_id")
        record = entity(selected_entity)
        action = payload.get("action", "add")
        if action not in {"add", "remove", "restore", "pin", "unpin"}:
            raise DashboardOwnerError("action_invalid", "Unsupported universe action")
        reason = payload.get("reason", "")
        if not isinstance(reason, str) or len(reason) > 2000 or (action in {"add", "remove", "restore"} and not reason.strip()):
            raise DashboardOwnerError("reason_required", "Provide a nonempty reason of at most 2000 characters")
        priority, pin = payload.get("priority", 0), payload.get("pin", False)
        if type(priority) is not int or type(pin) is not bool:
            raise DashboardOwnerError("invalid_payload", "priority must be an integer and pin must be boolean")
        member = identity.get_member(selected, selected_entity)
        normalized = {"action": action, "entity_id": selected_entity, "universe_id": selected,
                      "reason": reason.strip(), "priority": priority, "pin": pin}
        token = _digest({"operation": "universe", "payload": normalized,
                         "identity_revision": record.get("identity_revision"), "member": member})
        preview = {"protocol": PROTOCOL, "status": "preview", "can_apply": True, "identity_changed": False,
                   "payload": normalized, "entity": record, "member": member, "preview_token": token}
        if ((action == "add" and member and member["membership_status"] != "active")
                or (action in {"remove", "pin", "unpin"} and (not member or member["membership_status"] != "active"))
                or (action == "restore" and (not member or member["membership_status"] != "logically_removed"))):
            preview.update(can_apply=False, reason="membership_state_conflict")
        if operation == "universe_preview":
            return preview
        if payload.get("preview_token") != token:
            raise DashboardOwnerError("preview_stale", "Refresh and review the membership preview before applying", 409)
        if not preview["can_apply"]:
            raise DashboardOwnerError("membership_state_conflict", "This action does not match current membership state", 409)
        from stockwiki.quick_scan_universe import add_member, remove_member, restore_member, set_member_pin
        if action == "add":
            result = add_member(identity, selected, selected_entity, added_reason=reason,
                                priority=priority, manual_pin=pin)
        elif action == "remove":
            result = remove_member(identity, selected, selected_entity, removal_reason=reason)
        elif action == "restore":
            result = restore_member(identity, selected, selected_entity, restoration_reason=reason)
        else:
            result = set_member_pin(identity, selected, selected_entity, pinned=action == "pin")
        return {"protocol": PROTOCOL, "status": "applied", "member": result,
                "identity_changed": False, "network_calls": 0, "llm_calls": 0}
    if operation == "delivery_status":
        _require_store(observations, "observations")
        from stockwiki.quick_scan_delivery import ack_status, project_runtime_status
        return (ack_status(observations, package_id=payload["package_id"]) if payload.get("package_id")
                else project_runtime_status(observations))
    if operation in {"import_preview", "import_apply"}:
        _require_store(observations, "observations")
        bundle_id = payload.get("bundle_id")
        bundle = _bundle(config, bundle_id)
        from stockwiki.quick_scan_import import parse_package, verify_package_integrity, import_package
        package = parse_package(bundle["package"])
        verify_package_integrity(package)
        release = bundle["release"]
        for key in ("module_package_id", "release_id", "catalog_version", "semantic_fingerprint_version", "questions"):
            if key not in release:
                raise DashboardOwnerError("frozen_release_invalid", "Registered frozen release is incomplete")
        token = _digest({"bundle_id": bundle_id, "package_sha256": bundle["package_sha256"],
                         "release_sha256": bundle["release_sha256"]})
        if operation == "import_apply" and payload.get("preview_token") != token:
            raise DashboardOwnerError("preview_stale", "Refresh and review the registered bundle before importing", 409)
        # Subject-bound vendor validation uses only original IQS code. Validator
        # scratch belongs to an owned temporary root, never the owner workspace.
        scratch = Path(config.get("scratch_root", Path(config["iqs_root"]) / "runs"))
        if not scratch.is_dir():
            raise DashboardOwnerError("owner_scratch_missing", "Configured validator scratch root is absent", 503)
        with tempfile.TemporaryDirectory(prefix="iqs-dashboard-owner-", dir=scratch) as temporary:
            from stockwiki.quick_scan_subject_authority import IqsSubjectContract
            from stockwiki.quick_scan_subject_dispatch import SubjectBoundObservationStore
            contract = IqsSubjectContract(Path(config["iqs_root"]), runs_dir=Path(temporary),
                                          release_root=Path(config.get("iqs_release_root", config["iqs_root"])))
            bound_store = SubjectBoundObservationStore(paths, contract=contract)
            preview = bound_store.preview_import(package, frozen_release=release, identity_store=identity)
            if operation == "import_apply":
                if not preview["can_apply"]:
                    raise DashboardOwnerError("owner_import_preview_rejected", "Original owner refused this bundle", 409,
                                              {"items": preview["items"], "store_id": preview["store_id"]})
                receipt = import_package(bound_store, package, frozen_release=release, identity_store=identity)
                accepted = all(ack["status"] in {"accepted", "already_present"} for ack in receipt["acks"])
                return {"protocol": PROTOCOL, "status": "imported" if accepted else "rejected_or_conflict", "receipt": receipt,
                        "financial_accuracy_proven": False, "network_calls": 0, "llm_calls": 0}
            return {"protocol": PROTOCOL, "status": "preview", "bundle_id": bundle_id,
                    "package_id": package["package_id"], "items": preview["items"], "item_count": preview["item_count"],
                    "can_apply": preview["can_apply"], "owner_preview": preview,
                    "preview_token": token, "replay": all(item["exact_ack_replay"] for item in preview["items"]),
                    "financial_accuracy_proven": False,
                    "network_calls": 0, "llm_calls": 0}
    raise DashboardOwnerError("operation_unknown", "Unsupported owner operation", 404)


def _main():
    if sys.argv[1:] != ["--worker"]:
        return 2
    def offline(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            raise RuntimeError("dashboard_owner_network_forbidden")
    sys.addaudithook(offline)
    try:
        raw = sys.stdin.buffer.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            raise DashboardOwnerError("request_too_large", "Owner request exceeds limit")
        request = _json(raw.decode("utf-8"))
        result = _owner_worker(request["config"], request["operation"], request["payload"])
        response, code = {"protocol": PROTOCOL, "result": result}, 0
    except Exception as error:
        response, code = {"protocol": PROTOCOL, "error": _original_error(error).as_dict()}, 2
    print(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(_main())
