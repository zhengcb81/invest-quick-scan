"""OWNERPKG-INVEST-QUICK-SCAN-01: public owner job façade over the existing gates.

Dashboard submits a frozen ``CommandRequest`` (run_scan); this module binds it
to the ALREADY-registered execution bundle and dispatches through the existing
``ExecutionGateway.start`` chain — spend_authorization, admission, preview and
per-launch owner checks stay exactly where they were. This module adds no
second execution path, no budget logic and no scan engine: it keeps a durable
command ledger, projects the four native job kinds (run-*/prepjob_*/deliveryjob_*/
batch-*) into the Dashboard ``JobView`` shape, owns command-level idempotency
and the bounded public job catalog, and writes down the authoritative
allowed-actions mapping (see docs/implementation/owner-job-facade-contract.md).

Honesty boundaries kept verbatim from the product:
- ``paid_dispatch_started=None`` means the cost state is UNKNOWN; no caller,
  Dashboard or bypass, may turn it into ``known``.
- pause is a company/scope boundary drain, NOT a cancel; retry is forbidden;
  reconcile re-reads original owner state and never resends anything.
- ``thin_scan.py`` (draft, no budget gate) is deliberately unreachable from
  here; only formal, registered-bundle scans can be submitted.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from .dashboard_errors import DashboardExecutionError
    from .dashboard_locks import control_lock, ControlBusyError
except ImportError:
    from dashboard_errors import DashboardExecutionError
    from dashboard_locks import control_lock, ControlBusyError

try:
    from .dashboard_iqs_link import company_return_entity, safe_entity_id, safe_return_to
except ImportError:
    from dashboard_iqs_link import company_return_entity, safe_entity_id, safe_return_to


OWNER_ID = "invest-quick-scan"
PROTOCOL = "iqs.owner_command/1.0.0"
# The public CLI/HTTP wire protocol name for this façade (BUILD-PACKAGE §5.1).
WIRE_PROTOCOL = "iqs-job/1"
# Version of the allowed-actions / recovery mapping contract. Bump when the
# authoritative table in docs/implementation/owner-job-facade-contract.md moves.
MAPPING_VERSION = "iqs.owner_job_actions/1.0.0"

DASHBOARD_ACTIONS = ("cancel", "resume", "retry", "reconcile")
RECOVERY_DURABLE = "durable_owner_job"
RECOVERY_SHORT_REQUEST = "short_request_only"
RECOVERY_UNAVAILABLE = "unavailable"

# G-m8-COMMON-03: limits_ref may only name a DEPLOYED owner configuration key.
# The registry is exact — an unknown key is refused, never guessed.
LIMITS_REF_REGISTRY = {
    None: "bundle.spend_authorization",
    "iqs.bundle.spend_authorization": "bundle.spend_authorization",
}

_COMMAND_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_IDEMPOTENCY_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,255}")
OWNER_JOB_ID_PATTERN = r"run-[a-f0-9]{32}|prepjob_[a-f0-9]{32}|deliveryjob_[a-f0-9]{32}|batch-[a-f0-9]{32}"
_OWNER_JOB_ID = {
    "run": re.compile(r"run-[a-f0-9]{32}"),
    "prepjob": re.compile(r"prepjob_[a-f0-9]{32}"),
    "deliveryjob": re.compile(r"deliveryjob_[a-f0-9]{32}"),
    "batch": re.compile(r"batch-[a-f0-9]{32}"),
}
# Batch states whose blocked_reasons mark genuinely UNKNOWN original state
# (mirrors BatchGateway._uncertain's reason set).
_BATCH_UNCERTAIN_REASONS = {"launch_reference_unknown", "original_process_unknown",
    "owner_work_unknown", "owner_work_uncertain", "batch_run_ambiguous",
    "batch_run_scope_mismatch", "execution_tasks_invalid", "execution_tasks_truncated"}
# Original work states that count as finished scan answers.
_WORK_TERMINAL_SAVED = {"result_ready", "delivered"}
_WORK_UNKNOWN = {"uncertain", "leased"}

MAX_PAGE_LIMIT = 100
# Bounded catalog windows (mirroring the native list caps; never a claim about
# total history beyond them).
_RUN_PAGE_SIZE = 2000
_RUN_MAX_PAGES = 5
_MAX_RECORD_BYTES = 16 * 1024 * 1024


class OwnerJobError(Exception):
    """A façade-level refusal the transport reports as a 4xx envelope."""

    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.details = details or {}


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _read(path):
    raw = Path(path).read_bytes()
    if len(raw) > _MAX_RECORD_BYTES:
        raise ValueError("record_too_large")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    record = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    if not isinstance(record, dict):
        raise ValueError("record_not_object")
    return record


def _write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > _MAX_RECORD_BYTES:
        raise ValueError("record_too_large")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(uuid.uuid4().hex + ".pending")
    try:
        with pending.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(8):
            try:
                os.replace(pending, path)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                import time
                time.sleep(min(0.005 * 2 ** attempt, 0.04))
    finally:
        pending.unlink(missing_ok=True)


def _owner_kind(owner_job_id):
    for kind, pattern in _OWNER_JOB_ID.items():
        if isinstance(owner_job_id, str) and pattern.fullmatch(owner_job_id):
            return kind
    return None


def _api_error(code, message, correlation_id, *, retryable=False, next_actions=None):
    """Frozen Dashboard ApiError shape (contracts/openapi.yaml)."""
    return {"code": str(code)[:200], "message": str(message)[:500], "owner": OWNER_ID,
        "retryable": bool(retryable),
        "next_actions": [str(action)[:100] for action in (next_actions or [])][:10],
        "correlation_id": str(correlation_id or "")[:200]}


class OwnerJobFacade:
    """Durable command ledger + JobView projection; dispatch stays in the owner gateways.

    ``execution``/``preparation_jobs``/``delivery_jobs``/``batches`` are zero-arg
    provider callables so the façade never caches a gateway across a
    configuration switch (the service rebuilds them per request view).
    """

    def __init__(self, state_root, *, execution, preparation_jobs, delivery_jobs, batches,
                 universe_id=None):
        self.state_root = Path(state_root)
        self._execution = execution
        self._preparation_jobs = preparation_jobs
        self._delivery_jobs = delivery_jobs
        self._batches = batches
        self._universe_id = universe_id

    # ------------------------------------------------------------------ paths
    @property
    def _commands_root(self):
        return self.state_root / "commands"

    @property
    def _idem_root(self):
        return self.state_root / "idempotency"

    @property
    def _observations_root(self):
        return self.state_root / "observations"

    @property
    def _actions_root(self):
        return self.state_root / "actions"

    def _lock_path(self, kind, key):
        return self.state_root / "locks" / (kind + "-" + _digest(key)[:32] + ".lock")

    # ------------------------------------------------------------ validation
    @staticmethod
    def _validate_command_request(command):
        """Frozen Dashboard CommandRequest shape; unknown fields refused."""
        required = {"command_id", "idempotency_key", "owner", "company",
                    "requested_action", "explicit_scope", "as_of", "limits_ref"}
        if not isinstance(command, dict) or set(command) != required:
            raise OwnerJobError("command_invalid",
                "命令必须是完整CommandRequest字段且不含未知字段。", details={
                    "expected_fields": sorted(required)})
        if not isinstance(command["command_id"], str) or not _COMMAND_ID.fullmatch(command["command_id"]):
            raise OwnerJobError("command_id_invalid", "command_id格式无效。")
        if not isinstance(command["idempotency_key"], str) or not _IDEMPOTENCY_KEY.fullmatch(command["idempotency_key"]):
            raise OwnerJobError("idempotency_key_invalid", "idempotency_key格式无效。")
        if command["owner"] != OWNER_ID or command["requested_action"] != "run_scan":
            raise OwnerJobError("command_owner_mismatch",
                "本owner只接受invest-quick-scan的run_scan命令。")
        as_of = command["as_of"]
        if as_of is not None and (not isinstance(as_of, str) or len(as_of) > 64
                or re.fullmatch(r"\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?"
                                r"(Z|[+-]\d{2}:\d{2})?)?", as_of) is None):
            raise OwnerJobError("as_of_invalid", "as_of必须是日期、时间戳或null。")
        limits_ref = command["limits_ref"]
        if limits_ref is not None and limits_ref not in LIMITS_REF_REGISTRY:
            raise OwnerJobError("limits_ref_unknown",
                "limits_ref没有对应的已部署owner配置键；不猜测授权或金额。",
                details={"accepted": sorted(k for k in LIMITS_REF_REGISTRY if k)})
        company = command["company"]
        company_fields = {"entity_id", "listing_id", "analysis_subject_id",
                          "resolution_status", "display_name"}
        if not isinstance(company, dict) or set(company) != company_fields:
            raise OwnerJobError("company_invalid", "company必须是完整CompanyKey。")
        # The owner publishes bounded identifiers; a malformed entity id is not
        # addressable and must not reach the bundle selection as a guess.
        if safe_entity_id(company["entity_id"]) != company["entity_id"]:
            raise OwnerJobError("company_invalid", "company.entity_id不是owner可寻址的标识。")
        for key in ("listing_id", "analysis_subject_id"):
            value = company[key]
            if value is not None and safe_entity_id(value) != value:
                raise OwnerJobError("company_invalid", f"company.{key}不是owner可寻址的标识。")
        if not isinstance(company["display_name"], str) or not company["display_name"] \
                or len(company["display_name"]) > 256:
            raise OwnerJobError("company_invalid", "company.display_name无效。")
        if company["resolution_status"] != "resolved":
            raise OwnerJobError("company_unresolved",
                "只有resolved公司身份可以提交formal扫描；模糊身份不能选包。", 409)
        scope = command["explicit_scope"]
        scope_fields = {"scope_version", "scan_kind", "universe_id", "questionnaire_version"}
        if not isinstance(scope, dict) or not scope_fields <= set(scope) <= scope_fields | {"bundle_id"}:
            raise OwnerJobError("scope_invalid", "explicit_scope必须是完整ScanScope。")
        if "bundle_id" in scope and (not isinstance(scope["bundle_id"], str)
                or re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", scope["bundle_id"]) is None):
            raise OwnerJobError("scope_invalid", "explicit_scope.bundle_id格式无效。")
        if scope["scope_version"] != "1":
            raise OwnerJobError("scope_version_unsupported", "只支持scope_version=1。")
        if scope["scan_kind"] != "formal":
            # 红线3：草稿路径不得被job面暴露为formal；job面只提交formal。
            raise OwnerJobError("draft_scan_not_exposable",
                "job面只接受scan_kind=formal；草稿扫描不经此面、也不得标记为formal。", 409)
        for key in ("universe_id", "questionnaire_version"):
            value = scope[key]
            if value is not None and (not isinstance(value, str)
                    or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value)):
                raise OwnerJobError("scope_invalid", f"explicit_scope.{key}格式无效。")

    def _validate_return_to(self, return_to, entity_id):
        if return_to is None:
            return None
        validated = safe_return_to(return_to)
        if validated != return_to:
            raise OwnerJobError("return_to_invalid",
                "return_to必须逐字通过iqs.dashboard.owner/1.0.0白名单；不静默改写。")
        named = company_return_entity(return_to)
        if named is not None and named != entity_id:
            raise OwnerJobError("return_to_invalid",
                "return_to指向的公司与命令公司不一致（跨scope注入）。")
        return validated

    # ------------------------------------------------------------- ledger I/O
    def _command_path(self, command_id):
        """Digest-named ledger file; the raw command_id never touches the filesystem.

        The Dashboard contract puts no pattern on command_id, so the record is
        addressed by its content digest (32 hex, the same MAX_PATH-safe
        convention as the action ledger) while the file body keeps the raw id.
        """
        if not isinstance(command_id, str) or not _COMMAND_ID.fullmatch(command_id):
            raise OwnerJobError("command_id_invalid", "command_id格式无效。")
        return self._commands_root / (_digest({"command_id": command_id})[:32] + ".json")

    def _load_command(self, command_id):
        path = self._command_path(command_id)
        try:
            record = _read(path)
        except FileNotFoundError:
            raise OwnerJobError("command_unknown", "没有该命令记录。", 404) from None
        except (OSError, ValueError, TypeError, AttributeError):
            raise OwnerJobError("command_corrupt",
                "命令记录损坏；原文件保留，不按空记录重发。", 409) from None
        if (record.get("protocol") != PROTOCOL or record.get("command_id") != command_id):
            raise OwnerJobError("command_corrupt", "命令记录协议不匹配。", 409)
        return record

    def _save_command(self, record):
        record["updated_at"] = _now()
        _write(self._command_path(record["command_id"]), record)

    def _command_by_idempotency(self, idempotency_key):
        digest = _digest({"idempotency_key": idempotency_key})
        path = self._idem_root / (digest + ".json")
        try:
            index = _read(path)
            if (index.get("protocol") != PROTOCOL or index.get("idempotency_key_digest") != digest
                    or not isinstance(index.get("command_id"), str)):
                raise ValueError("idempotency_index_invalid")
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError, AttributeError):
            raise OwnerJobError("idempotency_index_corrupt",
                "幂等索引损坏；提交被拒绝，不冒新命令。", 409) from None
        try:
            record = self._load_command(index["command_id"])
        except OwnerJobError as error:
            # The index is written only AFTER the command record exists, so a
            # dangling index means the record was removed out of band; the key
            # must stay blocked rather than mint a fresh command.
            raise OwnerJobError("idempotency_index_dangling",
                "幂等索引指向的命令记录缺失；提交被拒绝，请核对owner-jobs目录。", 409,
                details={"command_id": index.get("command_id"),
                         "index_error": error.code}) from None
        if record.get("idempotency_key") != idempotency_key:
            raise OwnerJobError("idempotency_index_corrupt", "幂等索引与原命令不匹配。", 409)
        return record

    def _bind_idempotency(self, idempotency_key, command_id):
        _write(self._idem_root / (_digest({"idempotency_key": idempotency_key}) + ".json"),
               {"protocol": PROTOCOL, "idempotency_key_digest": _digest({"idempotency_key": idempotency_key}),
                "command_id": command_id, "bound_at": _now()})

    # ------------------------------------------------------------- submission
    def submit_run_scan(self, body):
        """G-m8-IQS-01: the new Dashboard entrance INTO the existing chain.

        Body = {"command_request": <CommandRequest>, "return_to": <optional>}.
        The native gateway resolves the exact registration, checks its owner
        permissions and starts it. This method keeps command-level idempotency
        and records the binding.
        """
        if not isinstance(body, dict) or set(body) - {"command_request", "return_to"} \
                or "command_request" not in body:
            raise OwnerJobError("submit_body_invalid",
                "提交体必须是{command_request, return_to?}。")
        command = body["command_request"]
        self._validate_command_request(command)
        entity_id = command["company"]["entity_id"]
        return_to = self._validate_return_to(body.get("return_to"), entity_id)
        scope = command["explicit_scope"]
        configured_universe = self._universe_id() if callable(self._universe_id) else self._universe_id
        if scope["universe_id"] is not None and scope["universe_id"] != configured_universe:
            raise OwnerJobError("universe_mismatch",
                "命令universe_id与已部署名单不一致；owner不改写命令的scope。", 409,
                details={"configured_universe_id": configured_universe})
        if scope["questionnaire_version"] is not None:
            # 诚实登记：owner当前没有已部署的题库版本键，无法核验就拒绝，
            # 不把声明当已验证（owner侧发布版本键后扩展此注册表）。
            raise OwnerJobError("questionnaire_version_unverifiable",
                "owner未部署题库版本键，非空questionnaire_version无法核验；请提交null表示当前题库。",
                details={"reason": "no_deployed_questionnaire_version_key"})
        try:
            return self._submit_locked(command, entity_id, return_to, scope)
        except ControlBusyError:
            raise OwnerJobError("facade_busy",
                "另一命令或动作正在记录；请重试，不并发落账。", 409) from None

    def _submit_locked(self, command, entity_id, return_to, scope):
        with (control_lock(self._lock_path("key", command["idempotency_key"])),
              control_lock(self._lock_path("command", command["command_id"]))):
            existing = self._command_by_idempotency(command["idempotency_key"])
            if existing is not None:
                # G-m8-IQS-04: same key → same owner_job_id, no second submit,
                # hence no second billing. A DIFFERENT body under the same key
                # is a client bug and is refused, never silently honoured.
                mismatch = [key for key, value in (
                    ("command_id", command["command_id"]),
                    ("entity_id", entity_id), ("scan_scope", scope),
                    ("return_to", return_to), ("limits_ref", command["limits_ref"]),
                    ("as_of", command["as_of"]), ("company", command["company"]))
                    if existing.get(key) != value]
                if mismatch:
                    raise OwnerJobError("idempotency_key_reuse_mismatch",
                        "同一idempotency_key对应了不同命令内容；拒绝，不混用语义。", 409,
                        details={"fields": mismatch,
                                 "command_id": existing["command_id"]})
                if existing.get("state") not in {"submitting", "needs_original_inspection"}:
                    # Bound or terminal: replay the durable record read-only.
                    return {"attached": True, "command": self._public_command(existing),
                            "job_view": self._job_view_for_command(existing),
                            "API_requests": 0}
                # Crash window: the intent is durable but no run is bound. The
                # replay RE-DRIVES the same recorded intent through the same
                # chain — safe because the native start attaches to any prior
                # run of the same bundle and never launches a second process.
                record = existing
            else:
                if self._command_path(command["command_id"]).exists():
                    # A crash between the intent write and the idempotency
                    # index write leaves an unbound orphan. The record itself
                    # carries the key, so an exact replay ADOPTS it (bind the
                    # index, re-drive); anything else stays a hard refusal.
                    orphan = self._load_command(command["command_id"])
                    adoptable = (orphan.get("state") == "submitting"
                                 and orphan.get("idempotency_key") == command["idempotency_key"]
                                 and [key for key, value in (
                                     ("entity_id", entity_id), ("scan_scope", scope),
                                     ("return_to", return_to), ("limits_ref", command["limits_ref"]),
                                     ("as_of", command["as_of"]), ("company", command["company"]))
                                     if orphan.get(key) != value] == [])
                    if not adoptable:
                        raise OwnerJobError("command_id_reused",
                            "command_id已存在；同命令请复用同一idempotency_key。", 409)
                    self._bind_idempotency(command["idempotency_key"], command["command_id"])
                    record = existing = orphan
                else:
                    record = {"protocol": PROTOCOL, "command_id": command["command_id"],
                        "idempotency_key": command["idempotency_key"], "kind": "run_scan",
                        "owner_job_id": None, "owner_kind": None, "entity_id": entity_id,
                        "company": command["company"], "scan_scope": scope,
                        "as_of": command["as_of"], "limits_ref": command["limits_ref"],
                        "limits_target": LIMITS_REF_REGISTRY[command["limits_ref"]],
                        "return_to": return_to, "state": "submitting",
                        "created_at": _now(), "updated_at": _now(),
                        "submission": None, "error": None}
                    self._save_command(record)  # Intent is durable BEFORE any dispatch.
                    self._bind_idempotency(command["idempotency_key"], command["command_id"])
            execution = self._execution()
            if record["state"] == "needs_original_inspection":
                started = self._read_start_reference(execution, record)
                if started is None:
                    return self._submission_reply(record, attached=True)
            else:
                if "registration" not in record:
                    company = record["company"]
                    try:
                        registration = execution.resolve_job_bundle(
                            bundle_id=scope.get("bundle_id"), entity_id=entity_id,
                            listing_id=company["listing_id"],
                            analysis_subject_id=company["analysis_subject_id"], as_of=record["as_of"])
                    except DashboardExecutionError as exc:
                        self._refuse_submission(record, exc)
                    record["registration"] = {key: registration[key] for key in
                        ("bundle_id", "entity_id", "bundle_fingerprint")}
                    self._save_command(record)
                try:
                    started = execution.start(record["registration"])
                except DashboardExecutionError as exc:
                    if exc.code == "launch_in_progress":
                        raise OwnerJobError("facade_busy", "原启动引用正在处理，请使用同一命令重试。", 409) from None
                    if exc.prelaunch_not_started:
                        self._refuse_submission(record, exc)
                    return self._unknown_submission(record, attached=existing is not None)
                except Exception:
                    return self._unknown_submission(record, attached=existing is not None)
            run = started.get("run") if isinstance(started, dict) else None
            if not self._matches_start_reference(record, run):
                return self._unknown_submission(record, attached=existing is not None)
            record.update(owner_job_id=run["run_id"], owner_kind="run",
                state="submitted", submission={
                    "process_started": started.get("process_started"),
                    # Verbatim product semantics: launch proof only, never a
                    # paid-dispatch or completion proof.
                    "paid_dispatch_started": started.get("paid_dispatch_started"),
                    "work_completion_authoritative": False,
                    "bundle_id": run.get("bundle_id"),
                    "bundle_fingerprint": run.get("bundle_fingerprint"),
                    "started_at": run.get("started_at")})
            self._save_command(record)
            return self._submission_reply(record, attached=existing is not None)

    def _refuse_submission(self, record, error):
        record.update(state="refused",
            error={"code": error.code, "message": error.message}, finished_at=_now())
        self._save_command(record)
        raise OwnerJobError("submission_refused", "原owner明确拒绝启动；本次未开始派发。",
            error.status, details={"command_id": record["command_id"],
                                   "refusal_code": error.code}) from None

    def _unknown_submission(self, record, *, attached):
        record.update(state="needs_original_inspection", error={"code": "start_reference_unknown",
            "message": "原启动结果未知。请查询命令，或使用原命令与幂等键查回原启动引用。"})
        self._save_command(record)
        return self._submission_reply(record, attached=attached)

    def _submission_reply(self, record, *, attached):
        return {"attached": attached, "command": self._public_command(record),
                "job_view": self._job_view_for_command(record), "API_requests": 0}

    @staticmethod
    def _matches_start_reference(record, run):
        return (isinstance(run, dict) and _owner_kind(run.get("run_id")) == "run"
                and not run.get("reference_error") and all(run.get(key) == value
                for key, value in record.get("registration", {}).items()))

    def _read_start_reference(self, execution, record):
        registration = record.get("registration")
        if registration is None:
            return None
        try:
            response = execution.tasks(bundle_ids=[registration["bundle_id"]],
                                       inspect_owner=False, limit=2)
            rows = response["tasks"]
            if len(rows) != 1 or not self._matches_start_reference(record, rows[0]):
                return None
        except (DashboardExecutionError, OSError, TypeError, KeyError):
            return None
        return {"run": rows[0], "process_started": False, "paid_dispatch_started": None}

    # ----------------------------------------------------------- native reads
    def _run_reference(self, run_id):
        """Light durable read of one run reference; no owner I/O."""
        try:
            result = self._execution().tasks(run_ids=[run_id], inspect_owner=False, limit=1, offset=0)
        except Exception as exc:
            raise OwnerJobError("run_reference_unavailable",
                "原启动引用不可读；不猜测状态。", 409,
                details={"error_code": str(getattr(exc, "code", "unavailable"))[:200]}) from None
        rows = [row for row in result.get("tasks", []) if isinstance(row, dict) and row.get("run_id") == run_id]
        return rows[0] if rows else None

    def _native_record(self, kind, owner_job_id):
        if kind == "run":
            return self._run_reference(owner_job_id)
        try:
            if kind == "prepjob":
                return self._preparation_jobs().get(owner_job_id)
            if kind == "deliveryjob":
                return self._delivery_jobs().get(owner_job_id)
            if kind == "batch":
                return self._batches().get(owner_job_id)
        except OwnerJobError:
            raise
        except Exception as exc:
            code = getattr(exc, "code", "owner_job_unavailable")
            status = getattr(exc, "status", 409)
            if code in {"preparation_job_unknown", "delivery_job_unknown", "batch_unknown"}:
                return None
            raise OwnerJobError("owner_job_unavailable", "原任务引用暂不可读；不猜测状态。",
                status, details={"error_code": str(code)[:200]}) from None
        return None

    # ------------------------------------------------------------- projection
    def _cost_state(self, kind, record):
        """G-m8-COMMON-03: owner-native cost projection.

        There is NO owner-native per-job cost amount in this product surface
        (the budget ledger is the original StockQA store; the product only ever
        exposes paid_dispatch_started=None). Therefore ``known`` is NEVER
        emitted here: run/batch dispatch paid work whose cost is unknown;
        preparation and delivery are 0-model, no-new-spend paths.
        """
        return "unknown" if kind in {"run", "batch"} else "not_applicable"

    def _recovery_capability(self, kind, owner_job_id):
        if owner_job_id is None:
            return RECOVERY_UNAVAILABLE  # Refused/unchained command: no durable job exists.
        return RECOVERY_DURABLE  # All four native kinds are durable owner references.

    def _actions_for(self, kind, status, record, native):
        """Authoritative mapping; the full table lives in the contract document.

        cancel: never mapped (pause drains at boundaries; retire only registers
        a stopped reference). retry: forbidden (owner refuses automatic
        resend). resume: only where a native resume exists and the projection
        shows a resumable state. reconcile: read-only owner re-check, allowed
        whenever the status is unknown; for a known status it stays available
        as a refresh except where nothing remains to check.
        """
        if status == "unknown":
            return ["reconcile"]  # status_known=false → exactly ['reconcile'].
        if kind is None:
            # Command-level states without a bound owner job: refused is final
            # (a new execution is a NEW command through the full chain), and a
            # terminal succeeded/cancelled command has nothing to act on.
            return []
        if status in {"succeeded", "cancelled"}:
            return []
        if status == "queued":
            # queued == batch deliberately paused by the owner (resume
            # continues). A submitting command (kind run, no job yet) offers
            # nothing: the caller replays the SAME idempotency key to resolve.
            return ["resume", "reconcile"] if kind == "batch" else []
        if status == "failed":
            if kind == "run":
                launcher = (native or {}).get("launcher_state")
                if launcher in {"paused", "draining"}:
                    return ["resume", "reconcile"]
                return ["reconcile"]
            if kind in {"deliveryjob", "batch"}:
                return ["resume", "reconcile"]
            return ["reconcile"]  # prepjob: registration recovery stays workbench-side.
        # Known running (nothing to re-check) and other known states.
        return []

    def _run_status(self, record):
        """Project one run reference WITHOUT owner I/O (light, durable only)."""
        if record is None:
            return "unknown", None, None
        process_state = record.get("process_state")
        started_at = record.get("started_at")
        updated_at = record.get("finished_at") or record.get("started_at")
        if process_state in {"starting", "running"}:
            return "running", started_at, updated_at
        if process_state == "launch_failed":
            return "failed", started_at, updated_at
        if process_state == "observed_stopped" and record.get("launcher_state") == "retired":
            proof = record.get("retirement")
            counts = proof.get("work_status_counts") if isinstance(proof, dict) else None
            if isinstance(counts, dict) and counts:
                # A validated retirement proof is durable owner evidence.
                if set(counts) <= _WORK_TERMINAL_SAVED:
                    return "succeeded", started_at, record.get("finished_at") or updated_at
                return "failed", started_at, record.get("finished_at") or updated_at
        # process_exited / needs_original_inspection / retired without proof:
        # local exit is NOT completion; without a fresh owner check the status
        # is genuinely unknown.
        return "unknown", started_at, updated_at

    def _observed_run_status(self, run_id):
        """Cached reconcile observation (owner inspection summary), if any."""
        path = self._observations_root / (run_id + ".json")
        try:
            return _read(path)
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def _status_from_work_counts(self, counts):
        if not isinstance(counts, dict) or not counts:
            return "unknown"
        if set(counts) & _WORK_UNKNOWN:
            return "unknown"
        if set(counts) <= _WORK_TERMINAL_SAVED:
            return "succeeded"
        return "failed"

    def _prepjob_status(self, record):
        if record is None:
            return "unknown"
        state = record.get("state")
        if state in {"preparing", "registration_in_progress"}:
            return "running"
        if state == "registered":
            return "succeeded"
        if state == "abandoned":
            return "cancelled"
        if state in {"owner_prepared", "registration_pending"}:
            return "failed"  # Original work exists but bundles are not registered here.
        return "unknown"  # needs_original_inspection and anything unrecognized.

    def _deliveryjob_status(self, record):
        if record is None:
            return "unknown"
        state = record.get("state")
        if record.get("read_only_history"):
            return "unknown"  # Original receiver unverifiable; read-only history.
        if state == "running":
            return "running"
        if state == "completed":
            return "succeeded"
        if state == "partial":
            return "failed"
        if state == "abandoned":
            return "cancelled"
        return "unknown"

    def _batch_status(self, record):
        if record is None:
            return "unknown"
        state = record.get("state")
        if state == "needs_original_inspection" or record.get("recovery_notice"):
            return "unknown"
        if state in {"running", "draining"}:
            return "running"
        if state == "paused":
            return "queued"  # Accepted, deliberately not dispatching; resume continues.
        if state == "owner_ready":
            return "succeeded"
        if state == "abandoned":
            return "cancelled"
        if state == "blocked":
            reasons = set()
            for entry in record.get("entries", []) or []:
                reasons.update(entry.get("blocked_reasons") or [])
            if reasons & _BATCH_UNCERTAIN_REASONS or record.get("coordinator_error"):
                return "unknown"
            return "failed"
        return "unknown"

    def _error_for(self, kind, status, record, native):
        if status == "failed":
            if kind == "run":
                code = (native or {}).get("exit_code")
                return {"code": "run_incomplete_or_failed",
                        "message": "原owner检查显示扫描未完成；不做自动重发，恢复走原owner规则。",
                        "exit_code": code}
            if kind == "prepjob":
                error = (record or {}).get("registration_error") or (record or {}).get("error_code")
                return {"code": error or "preparation_incomplete",
                        "message": "原准备未完成本工作台登记；登记恢复属原工作台动作，不经此面自动重发。"}
            if kind == "deliveryjob":
                codes = sorted({str(entry.get("error_code"))[:100]
                    for entry in (record or {}).get("entries", []) or [] if entry.get("error_code")})[:20]
                return {"code": "delivery_partial", "message": "交付部分未完成；resume在原目标核验后接续。",
                        "entry_error_codes": codes}
            if kind == "batch":
                reasons = sorted({str(reason)[:100]
                    for entry in (record or {}).get("entries", []) or []
                    for reason in (entry.get("blocked_reasons") or [])})[:20]
                return {"code": "batch_blocked", "message": "批编排被原owner状态阻断；先核原owner，不能盲重派。",
                        "blocked_reasons": reasons}
        if status == "unknown":
            return {"code": "status_unknown",
                    "message": "原状态未知；先reconcile核原owner，不盲重发。"}
        return None

    def _job_view(self, *, command_id, owner_job_id, kind, status, status_known,
                  started_at, updated_at, error=None, native=None):
        record = native if isinstance(native, dict) else {}
        error_payload = None
        if error is not None:
            error_payload = _api_error(error.get("code", "owner_job_error"),
                error.get("message", "原任务未成功。"), command_id or owner_job_id or "",
                retryable=False,
                next_actions=[action for action in self._actions_for(kind, status, record, native)])
        return {
            "command_id": command_id or "",
            "owner": OWNER_ID,
            "owner_job_id": owner_job_id,
            "status": status,
            "status_known": bool(status_known),
            "allowed_actions": self._actions_for(kind, status, record, native),
            "started_at": started_at,
            "updated_at": updated_at or _now(),
            "cost": None,
            "cost_state": self._cost_state(kind, record),
            "error": error_payload,
            "recovery_capability": self._recovery_capability(kind, owner_job_id),
        }

    def _job_view_for_command(self, record):
        """Project the command's bound job; a refused command has no owner job."""
        owner_job_id, kind = record.get("owner_job_id"), record.get("owner_kind")
        if record.get("state") == "submitting":
            return self._job_view(command_id=record["command_id"], owner_job_id=None,
                kind="run", status="queued", status_known=True,
                started_at=record.get("created_at"), updated_at=record["updated_at"],
                error=None)
        if record.get("state") == "refused":
            error = record.get("error") or {}
            return self._job_view(command_id=record["command_id"], owner_job_id=None,
                kind=None, status="failed", status_known=True,
                started_at=record.get("created_at"), updated_at=record["updated_at"],
                error={"code": error.get("code", "submission_refused"),
                       "message": "原owner拒绝启动；本次命令未产生新派发（见拒绝码）。"})
        if record.get("state") == "needs_original_inspection" and not owner_job_id:
            return self._job_view(command_id=record["command_id"], owner_job_id=None,
                kind="run", status="unknown", status_known=False,
                started_at=record.get("created_at"), updated_at=record["updated_at"])
        if owner_job_id and kind:
            return self.project_job(owner_job_id, command_id=record["command_id"],
                command_record=record)[0]
        # Anything else on the ledger is a ledger-shaped bug: refuse, never fake.
        raise OwnerJobError("command_record_invalid", "命令记录缺少可投影的任务绑定。", 409)

    def project_job(self, owner_job_id, *, command_id="", command_record=None):
        """Unified JobView projection over the four native job kinds (G-m8-IQS-02)."""
        kind = _owner_kind(owner_job_id)
        if kind is None:
            raise OwnerJobError("owner_job_id_invalid", "owner_job_id格式无效。")
        native = self._native_record(kind, owner_job_id)
        annotation = {"owner_job_id": owner_job_id, "owner_kind": kind,
                      "command_bound": bool(command_id),
                      # Product-wide constant: local references/summaries are
                      # never authority on work completion; owner inspection is.
                      "work_completion_authoritative": False}
        if native is None:
            if command_record is not None:
                stored = command_record.get("submission") or {}
                started_at = stored.get("started_at")
            else:
                started_at = None
            view = self._job_view(command_id=command_id, owner_job_id=owner_job_id,
                kind=kind, status="unknown", status_known=False,
                started_at=started_at, updated_at=None)
            annotation["notice"] = "原任务引用不存在或不可读；不按空历史重发。"
            return view, annotation
        if kind == "run":
            status, started_at, updated_at = self._run_status(native)
            observed = self._observed_run_status(owner_job_id)
            if status == "unknown" and observed is not None:
                # A previous reconcile cached a dated owner inspection. It is
                # only usable while the process reference has not moved on.
                still_stopped = native.get("process_state") in {
                    "process_exited", "needs_original_inspection", "observed_stopped"}
                if (still_stopped and observed.get("launch_attempt") == native.get("launch_attempt")
                        and observed.get("observed_at") and observed.get("work_status_counts")):
                    cached_status = self._status_from_work_counts(observed["work_status_counts"])
                    if cached_status != "unknown":
                        status = cached_status
                        updated_at = observed["observed_at"]
                        annotation["status_source"] = "cached_owner_inspection"
                        annotation["status_observed_at"] = observed["observed_at"]
            if status == "unknown":
                annotation["status_source"] = "requires_reconcile"
        elif kind == "prepjob":
            status = self._prepjob_status(native)
            started_at, updated_at = native.get("created_at"), native.get("finished_at") or native.get("prepared_at") or native.get("created_at")
        elif kind == "deliveryjob":
            status = self._deliveryjob_status(native)
            started_at, updated_at = native.get("created_at"), native.get("finished_at") or native.get("created_at")
        else:
            status = self._batch_status(native)
            started_at, updated_at = native.get("created_at"), native.get("updated_at") or native.get("created_at")
        owner_error = self._error_for(kind, status, native, native)
        # The frozen Dashboard ApiError carries no free-form details; the
        # owner-native evidence travels beside it in the annotation instead of
        # being dropped or stuffed into the envelope.
        if owner_error is not None and set(owner_error) - {"code", "message"}:
            annotation["owner_error_details"] = {
                key: value for key, value in owner_error.items() if key not in {"code", "message"}}
        view = self._job_view(command_id=command_id, owner_job_id=owner_job_id, kind=kind,
            status=status, status_known=status != "unknown",
            started_at=started_at, updated_at=updated_at,
            error=owner_error, native=native)
        return view, annotation

    # ----------------------------------------------------------------- reads
    def get_status(self, owner_job_id):
        view, annotation = self.project_job(owner_job_id)
        annotation["mapping_version"] = MAPPING_VERSION
        return {"protocol": WIRE_PROTOCOL, "job_view": view, "annotation": annotation,
                "API_requests": 0}

    def allowed_actions(self, owner_job_id):
        view, annotation = self.project_job(owner_job_id)
        return {"protocol": WIRE_PROTOCOL, "owner_job_id": owner_job_id,
                "status": view["status"], "status_known": view["status_known"],
                "allowed_actions": view["allowed_actions"],
                "recovery_capability": view["recovery_capability"],
                "mapping_version": MAPPING_VERSION, "API_requests": 0}

    def get_command(self, command_id):
        """G-m8-IQS-05: the durable command_id <-> owner_job_id binding."""
        record = self._load_command(command_id)
        if record["state"] == "needs_original_inspection":
            observed = self._read_start_reference(self._execution(), record)
            if observed is not None:
                # Expose a positively identified reference on GET without
                # changing the durable record or dispatching anything.
                record.update(owner_job_id=observed["run"]["run_id"], owner_kind="run")
        view = self._job_view_for_command(record)
        return {"protocol": WIRE_PROTOCOL, "command": self._public_command(record),
                "job_view": view, "mapping_version": MAPPING_VERSION, "API_requests": 0}

    def _public_command(self, record):
        return {"command_id": record["command_id"], "idempotency_key": record["idempotency_key"],
                "kind": record.get("kind"), "entity_id": record.get("entity_id"),
                "owner_job_id": record.get("owner_job_id"), "owner_kind": record.get("owner_kind"),
                "state": record.get("state"), "scan_scope": record.get("scan_scope"),
                "limits_ref": record.get("limits_ref"), "limits_target": record.get("limits_target"),
                "return_to": record.get("return_to"), "as_of": record.get("as_of"),
                "created_at": record.get("created_at"), "updated_at": record.get("updated_at"),
                "submission": record.get("submission"), "error": record.get("error")}

    # ------------------------------------------------------------------ act
    def act(self, owner_job_id, body):
        """G-m8-IQS-03: Dashboard actions onto native controls; no new semantics.

        Body = {"action": cancel|resume|retry|reconcile, "idempotency_key"}.
        Action idempotency: the same (owner_job_id, action, idempotency_key)
        replays the recorded result without re-acting.
        """
        kind = _owner_kind(owner_job_id)
        if kind is None:
            raise OwnerJobError("owner_job_id_invalid", "owner_job_id格式无效。")
        if not isinstance(body, dict) or set(body) != {"action", "idempotency_key"}:
            raise OwnerJobError("action_body_invalid",
                "动作体必须是{action, idempotency_key}。")
        action = body["action"]
        idempotency_key = body["idempotency_key"]
        if action not in DASHBOARD_ACTIONS:
            raise OwnerJobError("action_unknown", "不支持的Dashboard动作。")
        if not isinstance(idempotency_key, str) or not _IDEMPOTENCY_KEY.fullmatch(idempotency_key):
            raise OwnerJobError("idempotency_key_invalid", "idempotency_key格式无效。")
        # Serialise check-record-act so two concurrent acts with the same key
        # cannot both reach the native control before either result is
        # recorded. The kernel lock is nonblocking: a loser waits briefly and
        # then replays the recorded result — a busy timeout is the only 409.
        deadline = time.monotonic() + 5.0
        while True:
            try:
                with control_lock(self._lock_path("job", owner_job_id)):
                    replay = self._recorded_action(owner_job_id, action, idempotency_key)
                    if replay is not None:
                        view, annotation = self.project_job(owner_job_id)
                        return {"protocol": WIRE_PROTOCOL, "replayed": True,
                                "action_result": replay["action_result"],
                                "job_view": view, "annotation": annotation, "API_requests": 0}
                    result = self._dispatch_action(kind, owner_job_id, action)
                    self._record_action(owner_job_id, action, idempotency_key, result)
                break
            except ControlBusyError:
                if time.monotonic() >= deadline:
                    raise OwnerJobError("facade_busy",
                        "另一命令或动作正在记录；请重试，不并发落账。", 409) from None
                time.sleep(0.01)
        view, annotation = self.project_job(owner_job_id)
        return {"protocol": WIRE_PROTOCOL, "replayed": False, "action_result": result,
                "job_view": view, "annotation": annotation, "API_requests": 0}

    def _dispatch_action(self, kind, owner_job_id, action):
        if action == "cancel":
            # 契约写死：pause是公司/scope边界排空，不等价cancel；retire只是登记
            # 停止引用。Dashboard cancel在IQS没有等价的原生动作，显式拒绝。
            raise OwnerJobError("cancel_unsupported",
                "IQS没有与cancel等价的原生动作：pause只做边界排空、不中断在途请求；"
                "retire只登记已停止引用。请改用reconcile核原状态。", 409,
                details={"mapping_version": MAPPING_VERSION})
        if action == "retry":
            # 契约写死：retry被明确禁止（inspect_original_owner_no_automatic_resend）。
            # 新执行只能是走完整授权链的新命令提交，由原owner重新准入并可能拒绝。
            raise OwnerJobError("retry_forbidden",
                "禁止自动重发。未知/失败任务先reconcile核原owner；新执行须以新命令重新提交完整授权链。",
                409, details={"mapping_version": MAPPING_VERSION,
                              "owner_rule": "inspect_original_owner_no_automatic_resend"})
        if action == "reconcile":
            # reconcile只核原owner状态，不自动重发、不完成登记、不改预算。
            return self._reconcile(kind, owner_job_id)
        if action == "resume":
            return self._resume(kind, owner_job_id)
        raise OwnerJobError("action_unknown", "不支持的Dashboard动作。")

    def _reconcile(self, kind, owner_job_id):
        if kind == "run":
            try:
                inspected = self._execution().control(owner_job_id, "inspect")
            except Exception as exc:
                code = getattr(exc, "code", "owner_inspection_unavailable")
                if code == "run_unknown":
                    return {"action": "reconcile", "outcome": "reference_absent",
                            "notice": "原启动引用不存在；不重发。"}
                raise OwnerJobError("reconcile_unavailable",
                    "原状态核查暂不可用；保持unknown。", getattr(exc, "status", 409),
                    details={"error_code": str(code)[:200]}) from None
            preview = inspected.get("preview") if isinstance(inspected, dict) else None
            inspection = preview.get("inspection") if isinstance(preview, dict) else None
            counts = self._work_counts(inspection)
            native_run = inspected.get("run") if isinstance(inspected, dict) else None
            observation = {"observed_at": _now(), "source": "execution_inspect",
                           "launch_attempt": native_run.get("launch_attempt") if isinstance(native_run, dict) else None,
                           "inspection_sha256": preview.get("inspection_sha256") if isinstance(preview, dict) else None,
                           "work_status_counts": counts}
            self._save_observation(owner_job_id, observation)
            status = self._status_from_work_counts(counts)
            return {"action": "reconcile", "outcome": "inspected", "status_after": status,
                    "observed_at": observation["observed_at"],
                    "work_status_counts": counts,
                    "notice": "只读核查完成；未重发任何请求，未预留或增加费用。"}
        # prepjob/deliveryjob/batch: durable re-read (restarted-session
        # detection happens inside their get()); nothing is re-dispatched.
        native = self._native_record(kind, owner_job_id)
        if native is None:
            return {"action": "reconcile", "outcome": "reference_absent",
                    "notice": "原任务引用不存在；不重发。"}
        return {"action": "reconcile", "outcome": "reread",
                "notice": "已重读持久引用；未重发任何请求。"}

    @staticmethod
    def _work_counts(inspection):
        items = None
        if isinstance(inspection, dict):
            items = inspection.get("work_items")
        if isinstance(items, dict):
            rows = list(items.values())
        elif isinstance(items, list):
            rows = items
        else:
            return {}
        counts = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            state = row.get("status")
            if isinstance(state, str) and state:
                counts[state] = counts.get(state, 0) + 1
        return counts

    def _resume(self, kind, owner_job_id):
        if kind == "prepjob":
            raise OwnerJobError("resume_unsupported",
                "原准备没有resume动作；未完成登记属原工作台的显式reconcile/abandon。", 409,
                details={"mapping_version": MAPPING_VERSION})
        if kind == "run":
            call = lambda: self._execution().control(owner_job_id, "resume")
        elif kind == "deliveryjob":
            call = lambda: self._delivery_jobs().control(owner_job_id, "resume")
        else:
            call = lambda: self._batches().control(owner_job_id, "resume")
        try:
            result = call()
        except Exception as exc:
            code = getattr(exc, "code", "resume_refused")
            raise OwnerJobError("resume_refused",
                "原owner拒绝恢复；保持当前状态，不并发重发。", getattr(exc, "status", 409),
                details={"error_code": str(code)[:200]}) from None
        return {"action": "resume", "outcome": "requested",
                "notice": "恢复请求已交原owner链路；原owner复用已保存答案，未知HTTP不重发。",
                "result_digest": _digest(result) if isinstance(result, dict) else None}

    def _action_path(self, owner_job_id, action, idempotency_key):
        # 32 hex keeps action files well under the Windows MAX_PATH budget
        # (the same 32-char digest convention as the delivery job ids).
        return self._actions_root / owner_job_id / (
            f"{action}-{_digest({'owner_job_id': owner_job_id, 'action': action,
                                 'idempotency_key': idempotency_key})[:32]}.json")

    def _recorded_action(self, owner_job_id, action, idempotency_key):
        path = self._action_path(owner_job_id, action, idempotency_key)
        try:
            record = _read(path)
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError, AttributeError):
            raise OwnerJobError("action_record_unavailable", "原动作记录不可读，需核对原任务。", 409) from None
        if record.get("protocol") != PROTOCOL or record.get("action") != action \
                or record.get("owner_job_id") != owner_job_id \
                or record.get("idempotency_key") != idempotency_key \
                or not isinstance(record.get("action_result"), dict):
            raise OwnerJobError("action_record_unavailable", "原动作记录不匹配，需核对原任务。", 409)
        return record

    def _record_action(self, owner_job_id, action, idempotency_key, result):
        path = self._action_path(owner_job_id, action, idempotency_key)
        if path.exists():
            return  # Kernel lock held by the caller; first writer wins.
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, {"protocol": PROTOCOL, "owner_job_id": owner_job_id,
                      "action": action, "idempotency_key": idempotency_key,
                      "action_result": result, "recorded_at": _now()})

    def _save_observation(self, owner_job_id, observation):
        self._observations_root.mkdir(parents=True, exist_ok=True)
        _write(self._observations_root / (owner_job_id + ".json"),
               {"protocol": PROTOCOL, "owner_job_id": owner_job_id, **observation})

    # ------------------------------------------------------------------ list
    def list_jobs(self, cursor=None, limit=50):
        """G-m8-IQS-04: bounded public JobPage over the four native catalogs.

        The catalog is a bounded window (runs paged to 2000x5, preparation and
        delivery lists capped at 50, batches at 100 by their own modules).
        ``cursor`` is an opaque position token in that window; it is NOT a
        stability guarantee across mutating writes. Every item is annotated
        with ``work_completion_authoritative`` (false product-wide).
        """
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            raise OwnerJobError("page_invalid", "limit必须是整数。") from None
        if not 1 <= limit <= MAX_PAGE_LIMIT:
            raise OwnerJobError("page_invalid", f"limit须为1至{MAX_PAGE_LIMIT}。")
        offset = 0
        if cursor is not None:
            if not isinstance(cursor, str) or not cursor.startswith("v1:"):
                raise OwnerJobError("cursor_invalid", "cursor无效；请从第一页重新列出。")
            try:
                offset = int(base64.urlsafe_b64decode(cursor[3:].encode("ascii")).decode("ascii"))
            except (ValueError, UnicodeError, TypeError):
                raise OwnerJobError("cursor_invalid", "cursor无效；请从第一页重新列出。") from None
            if offset < 0:
                raise OwnerJobError("cursor_invalid", "cursor无效；请从第一页重新列出。")
        self._catalog_degraded = False
        rows = self._collect_rows()
        rows.sort(key=lambda row: (row["updated_at"] or "", row["sort_key"]), reverse=True)
        total = len(rows)
        window = rows[offset:offset + limit]
        bound = {}
        for row in window:
            if row["source"] == "command" and row["record"].get("owner_job_id"):
                bound.setdefault(row["record"]["owner_job_id"], row["record"]["command_id"])
        items, annotations = [], []
        for row in window:
            try:
                if row["source"] == "command":
                    record = row["record"]
                    view = self._job_view_for_command(record)
                    annotations.append({"owner_job_id": record.get("owner_job_id"),
                        "owner_kind": record.get("owner_kind") or "command",
                        "command_id": record["command_id"],
                        "command_bound": record.get("owner_job_id") is not None,
                        "work_completion_authoritative": False,
                        "command_state": record.get("state")})
                else:
                    view, annotation = self.project_job(row["owner_job_id"],
                        command_id=bound.get(row["owner_job_id"], ""))
                    annotations.append(annotation)
            except OwnerJobError as error:
                # One unreadable row must not hide the rest or fake a status.
                self._catalog_degraded = True
                view, annotation = self._unreachable_row(row, error)
            items.append(view)
            annotations[-1]["command_id"] = annotations[-1].get("command_id",
                bound.get(row.get("owner_job_id"), ""))
        next_cursor = None
        if offset + limit < total:
            next_cursor = "v1:" + base64.urlsafe_b64encode(
                str(offset + limit).encode("ascii")).decode("ascii")
        snapshot = _digest({"universe": self._universe_id() if callable(self._universe_id) else self._universe_id,
                            "total": total, "max_updated_at": rows[0]["updated_at"] if rows else None})
        return {"protocol": WIRE_PROTOCOL,
                "items": items,
                "annotations": annotations,
                "page": {"next_cursor": next_cursor, "snapshot_id": snapshot,
                         "total": total,
                         "total_status": "exact" if self._catalog_fully_visible() else "estimate"},
                "work_completion_authoritative_default": False,
                "mapping_version": MAPPING_VERSION, "API_requests": 0}

    @staticmethod
    def _unreachable_row(row, error):
        owner_job_id = row.get("owner_job_id")
        view = {"command_id": "", "owner": OWNER_ID, "owner_job_id": owner_job_id,
                "status": "unknown", "status_known": False, "allowed_actions": ["reconcile"],
                "started_at": None, "updated_at": _now(), "cost": None,
                "cost_state": "unknown",
                "error": _api_error(error.code, error.message, owner_job_id or ""),
                "recovery_capability": RECOVERY_DURABLE if owner_job_id else RECOVERY_UNAVAILABLE}
        annotation = {"owner_job_id": owner_job_id,
                      "owner_kind": _owner_kind(owner_job_id) or "command",
                      "command_bound": False, "work_completion_authoritative": False,
                      "reference_error": error.code}
        return view, annotation

    def _collect_rows(self):
        """Bounded merged window over commands + four native catalogs."""
        rows = []
        bound_ids = set()
        if self._commands_root.is_dir():
            for path in sorted(self._commands_root.glob("*.json")):
                try:
                    record = _read(path)
                except (OSError, ValueError, TypeError, AttributeError):
                    self._catalog_degraded = True
                    continue
                if record.get("protocol") != PROTOCOL:
                    self._catalog_degraded = True
                    continue
                if record.get("owner_job_id"):
                    bound_ids.add(record["owner_job_id"])
                rows.append({"source": "command", "owner_job_id": record.get("owner_job_id"),
                             "sort_key": record["command_id"],
                             "updated_at": record.get("updated_at"), "record": record})
        for kind in _OWNER_JOB_ID:
            for row_id, row in self._native_window(kind).items():
                if row_id in bound_ids:
                    continue  # Bound jobs project once, through their command.
                rows.append({"source": "native", "owner_job_id": row_id,
                             "sort_key": row_id,
                             "updated_at": row.get("updated_at") or row.get("created_at"),
                             "record": row})
        return rows

    def _native_window(self, kind):
        """Bounded native id->record window for one kind, tolerant to errors."""
        window = {}
        try:
            if kind == "run":
                gateway = self._execution()
                for page in range(_RUN_MAX_PAGES):
                    result = gateway.tasks(inspect_owner=False, limit=_RUN_PAGE_SIZE, offset=page * _RUN_PAGE_SIZE)
                    for row in result.get("tasks", []):
                        if isinstance(row, dict) and isinstance(row.get("run_id"), str):
                            window[row["run_id"]] = row
                    if result.get("next_offset") is None:
                        break
            elif kind == "prepjob":
                for job in self._preparation_jobs().list().get("jobs", []):
                    if isinstance(job, dict) and isinstance(job.get("job_id"), str):
                        window[job["job_id"]] = job
            elif kind == "deliveryjob":
                for job in self._delivery_jobs().list().get("jobs", []):
                    if isinstance(job, dict) and isinstance(job.get("job_id"), str):
                        window[job["job_id"]] = job
            elif kind == "batch":
                listing = self._batches().list(limit=100, offset=0)
                for batch in listing.get("batches", []):
                    if isinstance(batch, dict) and isinstance(batch.get("batch_id"), str):
                        window[batch["batch_id"]] = batch
        except Exception:
            # A single unavailable catalog must not fake emptiness: the page
            # reports the bounded window of the remaining readable catalogs,
            # and total_status drops to 'estimate'.
            self._catalog_degraded = True
        return window

    def _catalog_fully_visible(self):
        return not getattr(self, "_catalog_degraded", False)
