"""IQS client for StockWiki's public dashboard owner commands."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .dashboard_json import decode_owner_json

PROTOCOL = "iqs.dashboard.owner/1.0.0"
REQUEST_PROTOCOL = "stockwiki.quick_scan_dashboard_request/1.0.0"
REPLY_PROTOCOL = "stockwiki.quick_scan_dashboard_reply/1.0.0"
MEMBERSHIP_REQUEST_PROTOCOL = "stockwiki.membership_request/1.0.0"
OWNER_COMMAND = "stockwiki.quick_scan_dashboard_cli"
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
_ROOTS = ("stockwiki_root", "workspace_root")
_MAX_BYTES = 16 * 1024 * 1024
TIMEOUT_SECONDS_MAX = 600


def valid_timeout_seconds(value):
    """One deployment timeout rule shared with the settings validator."""
    return type(value) in (int, float) and 1 <= value <= TIMEOUT_SECONDS_MAX


class DashboardOwnerError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details=None):
        self.code, self.message, self.status = code, message, status
        self.details = dict(details or {})
        super().__init__(message)

    def as_dict(self):
        return {"code": self.code, "message": self.message,
                "status": self.status, "details": self.details}


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
        timeout = config.get("timeout_seconds", 30)
        if not valid_timeout_seconds(timeout):
            raise DashboardOwnerError("deployment_invalid", f"timeout_seconds must be between 1 and {TIMEOUT_SECONDS_MAX}", 503)
        return config

    def _call(self, operation, payload=None):
        if payload is None:
            payload = {}
        elif not isinstance(payload, dict):
            raise DashboardOwnerError("invalid_payload", "Expected a JSON object")
        config = self._deployment()
        if operation in {"company_result", "company_history"}:
            from .dashboard_company_projection import ProjectionError, read_company_assessment
            try:
                return read_company_assessment(config, operation, payload, environment=_env())
            except ProjectionError as error:
                raise DashboardOwnerError(error.code, error.message, error.status) from error
        wire_operation = "entity_view_inputs" if operation == "entity_view" else operation
        reply = self._owner_command(config, wire_operation, payload)
        if operation == "status":
            return {**reply, "registered_bundles": sorted(config.get("bundles", {}))}
        if operation == "entity_view":
            return _temporal_view(reply, payload["entity_id"])
        if operation == "entity":
            _require_entity_detail(reply, payload["entity_id"])
        if operation in {"history", "facts"}:
            _require_entity_records(reply, payload["entity_id"])
        return reply

    def _owner_command(self, config, operation, payload):
        code = Path(config["stockwiki_root"])
        if not (code / "stockwiki/quick_scan_dashboard_cli.py").is_file():
            raise DashboardOwnerError("owner_code_missing", "StockWiki dashboard command is missing", 503)
        command = [config["stockwiki_python"], "-B", "-X", "utf8", "-m", OWNER_COMMAND,
                   "--root", config["workspace_root"]]
        for key in ("universe_id", "workspace_kind"):
            if config.get(key):
                command.extend(("--" + key.replace("_", "-"), config[key]))
        if operation in {"import_preview", "import_apply"}:
            command.extend(_bundle_arguments(config, payload.get("bundle_id")))
        request = {"protocol": REQUEST_PROTOCOL, "operation": operation, "payload": payload}
        try:
            wire = json.dumps(request, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as error:
            raise DashboardOwnerError("invalid_payload", "Expected a serializable JSON object") from error
        try:
            result = subprocess.run(command, cwd=code, input=wire,
                                    text=True, encoding="utf-8", errors="strict", capture_output=True,
                                    timeout=config.get("timeout_seconds", 30), env=_env())
        except subprocess.TimeoutExpired as error:
            raise DashboardOwnerError("owner_timeout", "StockWiki owner request timed out", 504) from error
        except OSError as error:
            raise DashboardOwnerError("owner_process_unavailable", "Cannot start StockWiki interpreter", 503) from error
        except UnicodeError as error:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki returned invalid UTF-8", 502) from error
        if len(result.stdout.encode("utf-8")) > _MAX_BYTES:
            raise DashboardOwnerError("owner_response_too_large", "StockWiki response exceeded the dashboard limit", 502)
        try:
            response = decode_owner_json(result.stdout)
            if (not isinstance(response, dict) or response.get("protocol") != REPLY_PROTOCOL
                or response.get("operation") != operation):
                raise ValueError("invalid_owner_envelope")
            key = "result" if result.returncode == 0 else "error"
            if set(response) != {"protocol", "operation", key} or not isinstance(response[key], dict):
                raise ValueError("invalid_owner_envelope")
            if key == "error":
                value = response[key]
                if (not isinstance(value.get("code"), str) or not isinstance(value.get("message"), str)
                    or type(value.get("status")) is not int or not 400 <= value["status"] <= 599
                    or not isinstance(value.get("details"), dict)):
                    raise ValueError("invalid_owner_error")
        except (ValueError, RecursionError) as error:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki worker returned an invalid response", 502) from error
        if key == "error":
            value = response["error"]
            raise DashboardOwnerError(value["code"], value["message"], value["status"], value.get("details"))
        return response["result"]

    def _membership_request_command(self, operation, payload):
        """Use StockWiki's fixed public membership-request CLI only.

        The executable path and workspace root come from trusted deployment
        configuration. Business JSON cannot choose a module, command, or path.
        """
        allowed_fields = {
            "apply": {"action", "universe_id", "entity_id", "reason", "priority", "pin",
                      "idempotency_key", "expected_member_version", "expected_identity_revision"},
            "lookup": {"universe_id", "idempotency_key", "request_id"},
            "history": {"universe_id", "entity_id", "limit", "after_version", "version_pin"},
        }
        if operation not in allowed_fields:
            raise DashboardOwnerError("owner_operation_unknown", "Unsupported membership operation", 404)
        payload = _payload(payload, allowed_fields[operation])
        config = self._deployment()
        code = Path(config["stockwiki_root"])
        cli = code / "dashboard_membership_request_cli.py"
        if not cli.is_file():
            raise DashboardOwnerError(
                "owner_membership_request_unsupported",
                "The configured StockWiki release does not provide the membership request protocol",
                503, {"required_protocol": "stockwiki.membership_request/1.0.0"})
        command = [config["stockwiki_python"], "-B", "-X", "utf8", str(cli), operation,
                   "--root", config["workspace_root"]]
        try:
            wire = json.dumps(payload, ensure_ascii=False, allow_nan=False)
            result = subprocess.run(command, cwd=code, input=wire, text=True, encoding="utf-8",
                                    errors="strict", capture_output=True,
                                    timeout=config.get("timeout_seconds", 30), env=_env())
        except (ValueError, TypeError, RecursionError) as error:
            raise DashboardOwnerError("invalid_payload", "Expected a serializable JSON object") from error
        except subprocess.TimeoutExpired as error:
            raise DashboardOwnerError("owner_timeout", "StockWiki membership request timed out", 504) from error
        except OSError as error:
            raise DashboardOwnerError("owner_process_unavailable", "Cannot start StockWiki interpreter", 503) from error
        except UnicodeError as error:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki returned invalid UTF-8", 502) from error
        if len(result.stdout.encode("utf-8")) > _MAX_BYTES or len(result.stderr.encode("utf-8")) > 16_384:
            raise DashboardOwnerError("owner_response_too_large", "StockWiki response exceeded the dashboard limit", 502)
        try:
            if result.returncode == 0:
                response = decode_owner_json(result.stdout)
                if (not isinstance(response, dict)
                        or response.get("protocol") != MEMBERSHIP_REQUEST_PROTOCOL):
                    raise ValueError("invalid_membership_response")
                if operation == "apply":
                    valid = (isinstance(response.get("canonical_payload"), dict)
                             and isinstance(response.get("request_id"), str))
                elif operation == "lookup":
                    valid = response.get("status") in {"found", "not_found"}
                    if response.get("status") == "found":
                        valid = isinstance(response.get("request"), dict)
                else:
                    valid = isinstance(response.get("items"), list)
                if not valid:
                    raise ValueError("invalid_membership_response")
                return response
            error_response = decode_owner_json(result.stderr)
            if (not isinstance(error_response, dict)
                    or error_response.get("schema_version") != "stockwiki.membership_request/1.0.0"
                    or not isinstance(error_response.get("error_code"), str)):
                raise ValueError("invalid_membership_error")
        except (ValueError, RecursionError) as error:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki membership CLI returned an invalid response", 502) from error
        code = error_response["error_code"]
        status = {
            "membership_request_invalid": 400,
            "unknown_request_field": 400,
            "request_not_json": 400,
            "request_not_object": 400,
            "idempotency_key_conflict": 409,
            "membership_state_conflict": 409,
            "member_version_conflict": 409,
            "identity_revision_conflict": 409,
            "membership_history_pin_unavailable": 409,
            "entity_not_found": 404,
            "universe_not_found": 404,
            "membership_request_not_found": 404,
            "internal_refused": 503,
        }.get(code, 400)
        raise DashboardOwnerError(code, "StockWiki refused the membership request", status,
                                  {"owner_protocol": "stockwiki.membership_request/1.0.0"})

    def membership_request_capability(self):
        """Report code-level protocol availability without opening owner data."""
        try:
            config = self._deployment()
            available = (Path(config["stockwiki_root"]) / "dashboard_membership_request_cli.py").is_file()
        except DashboardOwnerError:
            available = False
        return {"protocol": "stockwiki.membership_request/1.0.0", "supported": available,
                "reason": None if available else "owner_membership_request_unsupported"}

    def membership_request_apply(self, payload):
        return self._membership_request_command("apply", payload)

    def membership_request_read(self, payload):
        return self._membership_request_command("lookup", payload)

    def membership_history(self, payload):
        return self._membership_request_command("history", payload)

    def status(self):
        try:
            return {**self._call("status"), "membership_request": self.membership_request_capability()}
        except DashboardOwnerError as error:
            return {"protocol": PROTOCOL, "available": False, "status": "unavailable",
                    "membership_request": self.membership_request_capability(),
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

    def entity_view(self, entity_id):
        return self._call("entity_view", {"entity_id": _identifier(entity_id, "entity_id")})

    def history(self, entity_id):
        return self._call("history", {"entity_id": _identifier(entity_id, "entity_id")})

    def facts(self, entity_id):
        return self._call("facts", {"entity_id": _identifier(entity_id, "entity_id")})

    def company_result(self, entity_id, result_id=None):
        """B03: one immutable company assessment snapshot (read-only)."""
        return self._call("company_result", {
            "entity_id": _identifier(entity_id, "entity_id"),
            "result_id": _identifier(result_id, "result_id") if result_id else None})

    def company_history(self, entity_id, limit=20, offset=0):
        """B03: bounded history of registered company results (read-only)."""
        if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or offset < 0:
            raise DashboardOwnerError("pagination_invalid", "limit must be 1-50 and offset must be nonnegative")
        return self._call("company_history", {"entity_id": _identifier(entity_id, "entity_id"),
                                              "limit": limit, "offset": offset})

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


def _bundle_arguments(config, bundle_id):
    _identifier(bundle_id, "bundle_id")
    bundles = config.get("bundles", {})
    record = bundles.get(bundle_id) if isinstance(bundles, dict) else None
    if not isinstance(record, dict):
        raise DashboardOwnerError("bundle_not_registered", "Bundle is not registered in server deployment", 404)
    if not config.get("iqs_root") or not record.get("package") or not record.get("release"):
        raise DashboardOwnerError("bundle_configuration_invalid", "Registered bundle is incomplete", 503)
    arguments = ["--iqs-code-root", str(Path(config["iqs_root"]).expanduser().resolve()),
                 "--bundle-id", bundle_id]
    if config.get("iqs_release_root"):
        arguments.extend(("--iqs-release-root", str(Path(config["iqs_release_root"]).expanduser().resolve())))
    for key in ("package", "release"):
        arguments.extend(("--" + key, str(Path(record[key]).expanduser().resolve())))
        if record.get(key + "_sha256") is not None:
            arguments.extend(("--" + key + "-sha256", str(record[key + "_sha256"])))
    return arguments


def _require_entity_detail(detail, entity_id):
    invalid = DashboardOwnerError("owner_response_invalid", "StockWiki returned a different entity", 502)
    entity = detail.get("entity")
    groups = detail.get("groups", [])
    if (not isinstance(entity, dict) or entity.get("entity_id") != entity_id
        or detail.get("entity_id", entity_id) != entity_id or not isinstance(groups, list)):
        raise invalid
    for group in groups:
        if not isinstance(group, dict) or group.get("entity_id", entity_id) != entity_id:
            raise invalid
        fields = group.get("fields", [])
        if (not isinstance(fields, list) or any(not isinstance(field, dict)
            or field.get("entity_id", entity_id) != entity_id for field in fields)):
            raise invalid


def _require_entity_records(reply, entity_id):
    rows = reply.get("observations")
    if reply.get("entity_id") != entity_id or not isinstance(rows, list):
        raise DashboardOwnerError("owner_response_invalid", "StockWiki returned a different entity history", 502)
    for row in rows:
        if not isinstance(row, dict) or row.get("entity_id") != entity_id:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki returned a different entity history", 502)
        payload = row.get("payload")
        if isinstance(payload, dict) and payload.get("entity_id", entity_id) != entity_id:
            raise DashboardOwnerError("owner_response_invalid", "StockWiki returned a different entity history", 502)


def _temporal_view(reply, entity_id):
    from datetime import datetime, timezone

    from .dashboard_temporal import build_entity_view
    if (set(reply) != {"entity_id", "detail", "observations"} or reply["entity_id"] != entity_id
        or not isinstance(reply["detail"], dict) or not isinstance(reply["observations"], dict)
        or any(not isinstance(row, dict) or row.get("entity_id") != entity_id
               or row.get("observation_id") != key for key, row in reply["observations"].items())):
        raise DashboardOwnerError("owner_response_invalid", "StockWiki returned invalid entity view inputs", 502)
    _require_entity_detail(reply["detail"], entity_id)
    return build_entity_view(reply["detail"], reply["observations"].get, entity_id=entity_id,
                             now_utc=datetime.now(timezone.utc).isoformat())


def worker_main():
    """Forward the old worker invocation used by a dashboard already running."""
    if sys.argv[1:] != ["--worker"]:
        return 2
    try:
        raw = sys.stdin.buffer.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            raise DashboardOwnerError("request_too_large", "Owner request exceeds limit")
        request = decode_owner_json(raw.decode("utf-8"))
        gateway = OwnerGateway(request["config"])
        result = gateway._call(request["operation"], request["payload"])
        response, code = {"protocol": PROTOCOL, "result": result}, 0
    except DashboardOwnerError as error:
        response, code = {"protocol": PROTOCOL, "error": error.as_dict()}, 2
    except (ValueError, KeyError, TypeError, RecursionError):
        error = DashboardOwnerError("invalid_payload", "Expected a legacy dashboard request")
        response, code = {"protocol": PROTOCOL, "error": error.as_dict()}, 2
    print(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return code
