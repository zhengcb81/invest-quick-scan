"""Company-level sequencing over registered StockQA bundles.

These records contain selection order and original execution references only.
They are not a question queue, a budget ledger, or an authority on answer quality.
Reads never launch work. A restarted coordinator requires an explicit resume and
an original-owner inspection before it can dispatch another company.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid

try:
    from .dashboard_execution import _process_recovery_evidence
except ImportError:
    from dashboard_execution import _process_recovery_evidence


# One byte bound for both sides of the atomic record protocol. Synthetic
# 5,000-scope engineering DTOs, including completed launch references, are
# exercised below this limit; raw owner work/answer payloads never belong here.
MAX_RECORD_BYTES = 16 * 1024 * 1024


class DashboardBatchError(ValueError):
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
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate_json_key")
            value[key] = item
        return value
    for attempt in range(8):
        try:
            raw = path.read_bytes()
            break
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(min(0.005 * 2 ** attempt, 0.04))
    if len(raw) > MAX_RECORD_BYTES:
        raise ValueError("batch_record_too_large")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def _write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_RECORD_BYTES:
        # Reject before touching any persisted bytes. A record the reader cannot
        # restore must never replace the previous complete crash-recovery state.
        raise ValueError("batch_record_too_large")
    pending = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    try:
        with pending.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows indexers/AV can briefly hold a reader without FILE_SHARE_DELETE.
        # Retry only the same atomic rename; never repeat an execution call.
        for attempt in range(8):
            try:
                os.replace(pending, path)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(min(0.005 * 2 ** attempt, 0.04))
    finally:
        pending.unlink(missing_ok=True)


class BatchGateway:
    """Thin ordered coordinator. Concurrency is deployment-controlled, not HTTP input.

    ``autostart=False`` permits deterministic unit tests; production uses a small
    daemon that polls original process references. No daemon starts on a read or
    merely by constructing a gateway, including after a service restart.
    """
    PROTOCOL = "iqs.dashboard_batch_reference/1.0.0"
    _ACTIVE = {"launching", "running", "attached"}
    _STATES = {"running", "draining", "paused", "blocked", "owner_ready", "needs_original_inspection", "abandoned"}

    def __init__(self, execution, state_root, *, max_concurrency=1,
                 poll_interval=0.5, autostart=True):
        if type(max_concurrency) is not int or not 1 <= max_concurrency <= 4:
            raise DashboardBatchError("batch_concurrency_invalid", "公司并发必须为部署配置中的1至4整数")
        if isinstance(poll_interval, bool) or not isinstance(poll_interval, (int, float)) or not 0.01 <= poll_interval <= 30:
            raise DashboardBatchError("batch_poll_invalid", "轮询间隔无效")
        self.execution, self.state_root = execution, Path(state_root)
        self.max_concurrency, self.poll_interval = max_concurrency, poll_interval
        self.autostart = bool(autostart)
        self._session = uuid.uuid4().hex
        self._lock, self._previews, self._threads = threading.RLock(), {}, {}
        self._memory_lock = threading.RLock()
        self._pending_workers = set()
        self._worker_errors = {}
        self._stop = threading.Event()

    @contextmanager
    def _mutation(self):
        self.state_root.mkdir(parents=True, exist_ok=True)
        path = self.state_root / "batch-control.lock"
        stream = path.open("a+b")
        locked = False
        try:
            # Take the nonblocking kernel lock BEFORE the local mutation lock.
            # Controls must fail busy promptly while another thread awaits a
            # native owner process, rather than waiting behind its long I/O.
            if os.name == "nt":
                import msvcrt
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    raise DashboardBatchError("batch_control_busy", "另一公司批控制正在进行；请先刷新状态", 409) from None
            else:
                import fcntl
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise DashboardBatchError("batch_control_busy", "另一公司批控制正在进行；请先刷新状态", 409) from None
            locked = True
            if path.stat().st_size == 0:
                # Windows permits locking beyond EOF. Initialize only AFTER
                # claiming byte zero, avoiding two empty-file writers racing
                # with one another's newly acquired byte lock.
                stream.write(b"0")
                stream.flush()
            with self._lock:
                yield
        finally:
            try:
                if locked:
                    if os.name == "nt":
                        stream.seek(0)
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            finally:
                stream.close()

    def _records(self):
        if not self.state_root.is_dir():
            return []
        records = []
        for path in sorted(self.state_root.glob("batch-*.json")):
            try:
                record = _read(path)
                entries = record.get("entries")
                if (record.get("protocol") != self.PROTOCOL
                    or re.fullmatch(r"batch-[a-f0-9]{32}", str(record.get("batch_id", ""))) is None
                    or path.stem != record["batch_id"] or record.get("state") not in self._STATES
                    or not isinstance(entries, list) or not entries or len(entries) > 5000
                    or type(record.get("max_concurrency")) is not int
                    or not 1 <= record["max_concurrency"] <= 4
                    or any(not isinstance(entry, dict) or not self._valid_reference(entry) for entry in entries)):
                    raise ValueError("batch_record_invalid")
                if [row["bundle_id"] for row in self._ordered_groups(entries)] != [row["bundle_id"] for row in entries]:
                    raise ValueError("batch_scope_order_changed")
                expected = _digest([[row["bundle_id"], row["entity_id"], row["bundle_fingerprint"]] for row in entries])
                if record.get("selection_sha256") != expected:
                    raise ValueError("batch_selection_changed")
                records.append(record)
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                raise DashboardBatchError("batch_record_corrupt", "公司批记录损坏；先核原owner，不能按空批重新派发", 409) from None
        return records

    @staticmethod
    def _valid_reference(entry):
        return (isinstance(entry.get("bundle_id"), str)
            and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", entry["bundle_id"]) is not None
            and isinstance(entry.get("entity_id"), str) and bool(entry["entity_id"].strip())
            and re.fullmatch(r"[a-f0-9]{64}", str(entry.get("bundle_fingerprint", ""))) is not None
            and entry.get("state") in {"selected", "launching", "running", "attached", "owner_ready", "blocked", "failed"}
            and (entry.get("run_id") is None or re.fullmatch(r"run-[a-f0-9]{32}", str(entry["run_id"])) is not None))

    def _path(self, batch_id):
        if not isinstance(batch_id, str) or re.fullmatch(r"batch-[a-f0-9]{32}", batch_id) is None:
            raise DashboardBatchError("batch_unknown", "没有该公司批", 404)
        return self.state_root / (batch_id + ".json")

    def _record(self, batch_id):
        self._path(batch_id)
        found = [value for value in self._records() if value["batch_id"] == batch_id]
        if not found:
            raise DashboardBatchError("batch_unknown", "没有该公司批", 404)
        return found[0]

    def _save(self, record):
        record["updated_at"] = _now()
        record["cursor"] = next((index for index, row in enumerate(record["entries"]) if row["state"] != "owner_ready"), len(record["entries"]))
        _write(self._path(record["batch_id"]), record)

    def _inspect(self, bundle_id, expected=None):
        result = self.execution.preview({"bundle_id": bundle_id})
        if (not isinstance(result, dict) or type(result.get("can_start")) is not bool
            or result.get("API_requests") != 0
            or re.fullmatch(r"[a-f0-9]{64}", str(result.get("bundle_fingerprint", ""))) is None
            or result.get("bundle_id") != bundle_id or not isinstance(result.get("entity_id"), str)):
            raise DashboardBatchError("execution_contract_incomplete", "原执行预览缺少稳定输入指纹或无收费检查证明", 409)
        result = {**result, **self._metadata(result), "owner_inspected": True}
        if expected and (result["bundle_fingerprint"] != expected["bundle_fingerprint"] or result["entity_id"] != expected["entity_id"]
            or self._metadata(result) != self._metadata(expected)):
            raise DashboardBatchError("batch_bundle_changed", "原执行包或公司身份已变更；不能恢复旧批，请重新登记并预览", 409)
        return result

    def _registered(self, bundle_id):
        value = self.execution.bundle_registration(bundle_id)
        if (not isinstance(value, dict) or value.get("bundle_id") != bundle_id
            or not isinstance(value.get("entity_id"), str) or not value["entity_id"].strip()
            or re.fullmatch(r"[a-f0-9]{64}", str(value.get("bundle_fingerprint", ""))) is None):
            raise DashboardBatchError("execution_registration_invalid", "原只读登记引用不完整；本地编排不是原owner费用准入", 409)
        return {**value, **self._metadata(value), "owner_inspected": False}

    def _registration(self, entry):
        value = self._registered(entry["bundle_id"])
        if (value["entity_id"] != entry["entity_id"] or value["bundle_fingerprint"] != entry["bundle_fingerprint"]
            or self._metadata(value) != self._metadata(entry)):
            raise DashboardBatchError("batch_bundle_changed", "冻结原输入或scope绑定发生变化；旧范围不能派发，请登记新准备批", 409)
        return value

    @staticmethod
    def _metadata(entry):
        fields = ("company_preparation_id", "scope", "scope_id", "security_id", "expected_scope_bindings")
        metadata = {key: entry.get(key) for key in fields}
        if all(value is None for value in metadata.values()):
            return metadata  # Legacy single-bundle registrations stay readable.
        prepared = metadata["company_preparation_id"]
        expected = metadata["expected_scope_bindings"]
        if (not isinstance(prepared, str) or re.fullmatch(r"prepare_[a-f0-9]{32}", prepared) is None
            or not isinstance(expected, list) or not expected or len(expected) > 2):
            raise DashboardBatchError("batch_scope_metadata_invalid", "原准备批次或完整scope绑定声明无效", 409)
        bindings = []
        for binding in expected:
            if (not isinstance(binding, dict) or set(binding) != {"scope", "scope_id"}
                or binding["scope"] not in {"entity", "security"} or not isinstance(binding["scope_id"], str)
                or not binding["scope_id"].strip() or len(binding["scope_id"]) > 300
                or binding["scope"] == "entity" and binding["scope_id"] != entry["entity_id"]
                or binding["scope"] == "security" and binding["scope_id"] == entry["entity_id"]):
                raise DashboardBatchError("batch_scope_metadata_invalid", "原准备批的公司/证券scope绑定无效", 409)
            bindings.append(dict(binding))
        if len({row["scope"] for row in bindings}) != len(bindings):
            raise DashboardBatchError("batch_duplicate_scope", "一个公司准备批不能混入多个挂牌证券或重复scope", 409)
        current = {"scope": metadata["scope"], "scope_id": metadata["scope_id"]}
        if current not in bindings:
            raise DashboardBatchError("batch_scope_metadata_invalid", "当前原包不属于声明的完整scope范围", 409)
        security = next((row["scope_id"] for row in bindings if row["scope"] == "security"), None)
        if metadata["security_id"] is not None and metadata["security_id"] != security:
            raise DashboardBatchError("batch_security_mismatch", "不得混用不同挂牌证券的估值scope", 409)
        metadata["expected_scope_bindings"] = sorted(bindings, key=lambda row: (row["scope"] != "entity", row["scope_id"]))
        return metadata

    @classmethod
    def _ordered_groups(cls, entries):
        groups, preparations = {}, {}
        for entry in entries:
            metadata = cls._metadata(entry)
            prepared = metadata["company_preparation_id"]
            if prepared is not None:
                if prepared in preparations and preparations[prepared] != entry["entity_id"]:
                    raise DashboardBatchError("batch_preparation_identity_mismatch", "一个原准备批不能对应多个公司", 409)
                preparations[prepared] = entry["entity_id"]
            groups.setdefault(entry["entity_id"], []).append(entry)
        ordered = []
        for rows in groups.values():
            metadata = [cls._metadata(row) for row in rows]
            if all(item["company_preparation_id"] is None for item in metadata):
                if len(rows) != 1:
                    raise DashboardBatchError("batch_duplicate_entity", "同公司只可组合同一原准备批的互补scope；多地挂牌不能重复扫描", 409)
                ordered.extend(rows)
                continue
            if (any(item["company_preparation_id"] is None for item in metadata)
                or len({item["company_preparation_id"] for item in metadata}) != 1):
                raise DashboardBatchError("batch_duplicate_entity", "同公司不同原准备批不能拼接为一组", 409)
            expected = metadata[0]["expected_scope_bindings"]
            if any(item["expected_scope_bindings"] != expected for item in metadata):
                raise DashboardBatchError("batch_scope_group_mismatch", "同一原准备批的完整scope声明不一致", 409)
            actual = [(item["scope"], item["scope_id"]) for item in metadata]
            if len(set(actual)) != len(actual):
                raise DashboardBatchError("batch_duplicate_scope", "同一公司准备批不能重复选择scope", 409)
            if set(actual) != {(item["scope"], item["scope_id"]) for item in expected}:
                raise DashboardBatchError("batch_scope_group_incomplete", "必须选择同一公司准备批的全部scope，不能遗漏证券或实体题目", 409)
            ordered.extend(sorted(rows, key=lambda row: (row.get("scope") != "entity", row.get("scope_id", ""))))
        return ordered

    @staticmethod
    def _thin(preview):
        return {key: preview.get(key) for key in ("bundle_id", "entity_id", "bundle_fingerprint", "can_start",
            "readonly_recovery", "inspection_sha256", "blocked_reasons", "company_preparation_id", "scope", "scope_id",
            "security_id", "expected_scope_bindings", "owner_inspected")}

    @staticmethod
    def _inspection_summary(preview):
        # The entry already freezes identity, registration hashes and the full
        # scope group. Keep only the last observed owner status, not a second
        # copy of those fields for every scope in a multi-thousand-scope pool.
        return {key: preview.get(key) for key in (
            "can_start", "readonly_recovery", "inspection_sha256", "blocked_reasons")}

    @staticmethod
    def _ready(preview):
        return preview.get("can_start") is True and preview.get("readonly_recovery") is True

    @staticmethod
    def _selection(payload):
        if not isinstance(payload, dict) or set(payload) != {"bundle_ids"}:
            raise DashboardBatchError("batch_selection_invalid", "只允许按顺序选择已登记执行包")
        selected = payload["bundle_ids"]
        if (not isinstance(selected, list) or not 1 <= len(selected) <= 5000
            or any(not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value) is None for value in selected)
            or len(set(selected)) != len(selected)):
            raise DashboardBatchError("batch_selection_invalid", "请选择1至5000个不重复的已登记执行包")
        return selected

    def _remember_preview(self, value):
        with self._memory_lock:
            self._previews[value["preview_id"]] = value
            while len(self._previews) > 128:
                self._previews.pop(next(iter(self._previews)))
        return value

    def registration_preview(self, payload):
        """Freeze local registrations only; no owner CLI, quote or work mutation."""
        selected = self._selection(payload)
        registrations = self._ordered_groups([self._registered(bundle_id) for bundle_id in selected])
        entries = [{**self._thin(value), "can_start": None, "readonly_recovery": None,
            "inspection_sha256": None, "blocked_reasons": [], "owner_inspected": False} for value in registrations]
        return self._remember_preview({"preview_id": "batch-preview-" + uuid.uuid4().hex,
            "preview_kind": "registration", "entries": entries, "owner_inspected": False,
            "coordinator_can_register": True, "owner_admission_confirmed": False,
            "can_start": True, "company_count": len({row["entity_id"] for row in entries}),
            "scope_count": len(entries), "all_selected_ready": False, "max_concurrency": self.max_concurrency,
            "API_requests": 0, "database_writes": 0,
            "notice": "仅本地编排预览和冻结输入hash，可登记公司顺序；未检查原owner费用、额度或答案状态。每个scope实际派发前才执行原owner准入检查。"})

    def preview(self, payload):
        """Legacy eager owner preview; product pool UI uses registration_preview."""
        selected = self._selection(payload)
        previews = self._ordered_groups([self._inspect(bundle_id) for bundle_id in selected])
        preview_id = "batch-preview-" + uuid.uuid4().hex
        entries = [self._thin(item) for item in previews]
        value = {"preview_id": preview_id, "entries": entries, "can_start": any(item["can_start"] for item in entries),
            "company_count": len({item["entity_id"] for item in entries}), "scope_count": len(entries),
            "all_selected_ready": all(item["can_start"] for item in entries), "max_concurrency": self.max_concurrency,
            "preview_kind": "owner_inspection", "owner_inspected": True,
            "API_requests": 0, "database_writes": 0, "notice": "仅原owner预检；未预留费用。启动后逐公司重新检查，已ready复用，未知或额度不足保留阻断。"}
        return self._remember_preview(value)

    def _public(self, record):
        result = dict(record)
        result["entries"] = [dict(row) for row in record["entries"]]
        result.pop("owner_session", None)
        worker_error = self._worker_errors.get(record["batch_id"])
        if record["state"] in {"running", "draining"} and (record.get("owner_session") != self._session or self._stop.is_set() or worker_error):
            result["persisted_state"] = record["state"]
            result["state"] = "needs_original_inspection"
            result["recovery_notice"] = "服务实例已变化；读取不会续跑，需明确恢复并核原owner。"
        if worker_error:
            result["coordinator_error"] = worker_error
        result["counts"] = {key: sum(row["state"] == key for row in record["entries"])
            for key in ("selected", "launching", "running", "attached", "owner_ready", "blocked", "failed")}
        result["counts_unit"] = "scope_references"
        result["scope_counts"] = {"total": len(record["entries"]), **result["counts"]}
        groups = {}
        for entry in record["entries"]:
            groups.setdefault(entry["entity_id"], []).append(entry)
        result["company_groups"] = []
        for entity_id, entries in groups.items():
            state = "owner_ready" if all(row["state"] == "owner_ready" for row in entries) else (
                "blocked" if any(self._uncertain(row) for row in entries) else "running" if any(row["state"] in self._ACTIVE for row in entries)
                else "failed" if any(row["state"] == "failed" for row in entries)
                else "blocked" if any(row["state"] == "blocked" for row in entries) else "selected")
            result["company_groups"].append({"entity_id": entity_id, "company_preparation_id": entries[0].get("company_preparation_id"),
                "scope_count": len(entries), "ready_scope_count": sum(row["state"] == "owner_ready" for row in entries),
                "expected_scope_bindings": entries[0].get("expected_scope_bindings"),
                "bundle_ids": [row["bundle_id"] for row in entries], "state": state, "complete": state == "owner_ready"})
        result["company_counts"] = {"total": len(groups), **{state: sum(row["state"] == state for row in result["company_groups"])
            for state in ("owner_ready", "running", "selected", "blocked", "failed")}}
        result["allowed_actions"] = (["pause", "resume", "abandon"] if result["state"] not in {"owner_ready", "abandoned"} else [])
        result["work_state_owner"] = "StockQAbyLLM"
        result["projection_observed_at"] = record.get("updated_at")
        result["projection_is_dispatch_permission"] = False
        result["financial_accuracy_verified"] = False
        result["notice"] = "owner_ready只表示原owner已有答案；不代表已导入、金融审查通过或所有公司已扫描。"
        return result

    def list(self, limit=50, offset=0):
        if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or offset < 0:
            raise DashboardBatchError("batch_pagination_invalid", "每页需为1至100条，偏移需为非负整数")
        # Record replacement is atomic. GET reads the last complete projection;
        # it must never wait on the mutation lock across native owner I/O.
        records = sorted(self._records(), key=lambda row: (row["created_at"], row["batch_id"]), reverse=True)
        values = [self._public(record) for record in records[offset:offset + limit]]
        return {"protocol": "iqs.dashboard_batches/1.0.0", "batches": values,
            "total": len(records), "limit": limit, "offset": offset, "API_requests": 0}

    def get(self, batch_id):
        """Read one atomic persisted projection; no native inspection or locks."""
        return self._public(self._record(batch_id))

    def status(self):
        return {**self.list(), "supports": {"ordered_registered_bundles": True, "pause_scope": "scope_or_company_boundary",
            "resume": True, "complete_company_requires_all_scopes": True, "read_launches_work": False}, "max_concurrency": self.max_concurrency,
            "available": True, "execution_preflight_required": True,
            "work_state_owner": "StockQAbyLLM", "automatic_restart_dispatch": False}

    def _tasks(self, entries, *, include_selected=False):
        selected = [row for row in entries if include_selected or row["state"] in self._ACTIVE]
        if not selected:
            return []
        # Normal ticks query at most the active company references. A not-yet
        # launched company is looked up separately just before its dispatch.
        tasks, offset, expected_total = [], 0, None
        while True:
            result = self.execution.tasks(bundle_ids=[row["bundle_id"] for row in selected],
                inspect_owner=False, limit=2000, offset=offset)
            if not isinstance(result, dict) or not isinstance(result.get("tasks"), list) or result.get("API_requests") != 0:
                raise DashboardBatchError("execution_tasks_invalid", "原执行引用不可用；批派发已停止", 409)
            page = result["tasks"]
            total = result.get("total", len(page))
            if (any(not isinstance(row, dict) for row in page) or type(total) is not int or total < 0
                or expected_total is not None and expected_total != total):
                raise DashboardBatchError("execution_tasks_invalid", "原执行引用结构或分页快照已变化；批派发已停止", 409)
            if total > 5000:
                raise DashboardBatchError("execution_tasks_truncated", "原启动引用超过本次可核范围；不能把截断列表当作无历史后重新派发", 409)
            expected_total = total
            tasks.extend(page)
            run_ids = [row["run_id"] for row in tasks if row.get("run_id") is not None]
            if len(run_ids) != len(set(run_ids)):
                raise DashboardBatchError("execution_tasks_invalid", "原启动引用分页存在重复；请刷新，不能猜测丢失的引用", 409)
            following = result.get("next_offset")
            if following is None and len(tasks) == total:
                return tasks
            if type(following) is not int or not page or following != offset + len(page) or following >= total:
                raise DashboardBatchError("execution_tasks_truncated", "原启动引用分页不完整；不能按空历史重新派发", 409)
            offset = following

    def start(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"preview_id"} or not isinstance(payload["preview_id"], str):
            raise DashboardBatchError("batch_start_invalid", "启动只接受已预览的公司批")
        with self._mutation():
            if self._stop.is_set():
                raise DashboardBatchError("batch_service_closed", "该工作台实例已关闭", 409)
            selection = self._previews.get(payload["preview_id"])
            if not selection:
                raise DashboardBatchError("batch_preview_required", "请在当前服务先预览公司批", 409)
            entries = selection["entries"]
            selection_hash = _digest([[row["bundle_id"], row["entity_id"], row["bundle_fingerprint"]] for row in entries])
            records = self._records()
            prior = next((row for row in records if row["selection_sha256"] == selection_hash), None)
            if prior:
                return {"status": "attached", "batch": self._public(prior), "process_started": False}
            chosen_entities = {row["entity_id"] for row in entries}
            if any(row["entity_id"] in chosen_entities and (row["state"] in self._ACTIVE
                or row["state"] == "selected" and other["state"] in {"running", "draining", "paused", "needs_original_inspection"}
                or self._uncertain(row)) for other in records if other['state'] != 'abandoned' for row in other["entries"]):
                raise DashboardBatchError("batch_entity_active", "所选公司已有运行或未知启动引用；先核原批，不能另建并发范围", 409)
            # A local pool preview is not budget authority. Recheck its hashes
            # without starting thousands of native inspector processes; each
            # actual scope launch still uses _step's fresh owner preflight.
            local = selection.get("preview_kind") == "registration"
            checked = [self._registration(row) if local else self._inspect(row["bundle_id"], row) for row in entries]
            record = {"protocol": self.PROTOCOL, "batch_id": "batch-" + uuid.uuid4().hex,
                "selection_sha256": selection_hash, "created_at": _now(), "state": "running",
                "owner_session": self._session, "max_concurrency": self.max_concurrency,
                "work_completion_authoritative": False, "entries": [],
                "registration_preview_owner_inspected": not local, "owner_admission_confirmed": False,
                "admission_strategy": "per_scope_original_owner_preflight"}
            for value in checked:
                state = "selected" if local else "owner_ready" if self._ready(value) else "selected" if value["can_start"] else "blocked"
                thin = self._thin(value)
                if local:
                    thin.update(can_start=None, readonly_recovery=None, inspection_sha256=None, owner_inspected=False)
                record["entries"].append({**thin, "state": state, "run_id": None,
                    "blocked_reasons": [] if state != "blocked" else value.get("blocked_reasons", ["owner_blocked"])})
            self._settle(record)
            self._save(record)
        self._launch_worker(record["batch_id"])
        return {"status": "created", "batch": self._public(record), "process_started": None,
            "company_dispatch_scheduled": record["state"] == "running", "paid_dispatch_started": None,
            "notice": "公司批已登记；每次真实启动仍由原执行器再次准入。"}

    def _attach(self, entry, tasks):
        matches = [row for row in tasks if row.get("bundle_id") == entry["bundle_id"]]
        if entry.get("run_id"):
            matches = [row for row in matches if row.get("run_id") == entry["run_id"]]
        if len(matches) > 1:
            raise DashboardBatchError("batch_run_ambiguous", "原启动引用不唯一；不能猜测需要恢复哪次执行", 409)
        if not matches:
            return None
        task = matches[0]
        if (task.get("bundle_fingerprint") != entry["bundle_fingerprint"]
            or task.get("entity_id") != entry["entity_id"]
            or re.fullmatch(r"run-[a-f0-9]{32}", str(task.get("run_id", ""))) is None):
            raise DashboardBatchError("batch_run_scope_mismatch", "原启动引用与冻结公司范围不一致", 409)
        entry["run_id"] = task["run_id"]
        entry["process_state"] = task.get("process_state")
        if task.get("process_state") in {"running", "starting"}:
            entry.update(state="running", blocked_reasons=[])
            return task
        preview = self._inspect(entry["bundle_id"], entry)
        entry["last_inspection"] = self._inspection_summary(preview)
        if self._ready(preview):
            entry.update(state="owner_ready", blocked_reasons=[])
        elif task.get("process_state") == "needs_original_inspection":
            entry.update(state="blocked", blocked_reasons=["original_process_unknown"])
        elif task.get("process_state") in {"process_exited", "launch_failed"}:
            entry.update(state="failed", blocked_reasons=["process_exited_without_owner_ready"], exit_code=task.get("exit_code"))
        else:
            entry.update(state="blocked", blocked_reasons=["original_process_state_invalid"])
        return task

    def _refresh_existing(self, entry, tasks):
        if self._attach(entry, tasks) is not None:
            return
        if entry.get("run_id") or entry["state"] in self._ACTIVE:
            preview = self._inspect(entry["bundle_id"], entry)
            entry["last_inspection"] = self._inspection_summary(preview)
            if self._ready(preview):
                entry.update(state="owner_ready", blocked_reasons=[])
            else:
                entry.update(state="blocked", blocked_reasons=["launch_reference_unknown"])

    @staticmethod
    def _failure(entry, error):
        entry.update(state="blocked", blocked_reasons=[getattr(error, "code", "original_owner_unavailable")])

    @staticmethod
    def _proved_prelaunch_refusal(entry, proof, code=None):
        """A bound original no-start proof is control evidence, never dispatch authority."""
        return (isinstance(proof, dict)
            and proof.get('protocol') == 'iqs.prelaunch_refusal/1.0.0'
            and proof.get('phase') == 'before_process_reference'
            and proof.get('new_process_started') is False
            and proof.get('code') in {'preview_required', 'execution_not_ready', 'preview_changed'}
            and (code is None or proof['code'] == code)
            and entry.get('launch_intent_profile') == 'iqs.dashboard_launch_intent/1.1.0'
            and proof.get('bundle_id') == entry.get('bundle_id')
            and proof.get('bundle_fingerprint') == entry.get('bundle_fingerprint')
            and re.fullmatch('[a-f0-9]{32}', str(proof.get('launch_attempt_id', ''))) is not None
            and proof['launch_attempt_id'] == entry.get('launch_attempt_id')
            and type(proof.get('API_requests')) is int and proof['API_requests'] == 0
            and type(proof.get('database_writes')) is int and proof['database_writes'] == 0)

    @staticmethod
    def _uncertain(entry):
        return bool(entry.get("launch_uncertain") and entry["state"] != "owner_ready" or
            set(entry.get("blocked_reasons") or []) & {"launch_reference_unknown", "original_process_unknown",
                "owner_work_unknown", "owner_work_uncertain", "batch_run_ambiguous", "batch_run_scope_mismatch",
                "execution_tasks_invalid", "execution_tasks_truncated"})

    @staticmethod
    def _prior_ready(entries, index):
        return all(row["state"] == "owner_ready" for row in entries[:index] if row["entity_id"] == entries[index]["entity_id"])

    @classmethod
    def _settle(cls, record):
        entries = record["entries"]
        if any(cls._uncertain(row) for row in entries):
            record["state"] = "blocked"
        elif any(row["state"] in cls._ACTIVE for row in entries):
            record["state"] = "running"
        elif all(row["state"] == "owner_ready" for row in entries):
            record["state"] = "owner_ready"
        elif any(row["state"] == "selected" and cls._prior_ready(entries, index) for index, row in enumerate(entries)):
            record["state"] = "running"
        else:
            record["state"] = "blocked"

    def _step(self, batch_id):
        """One locked orchestration step; tests can advance it without a timer."""
        with self._mutation():
            record = self._record(batch_id)
            if record.get("owner_session") != self._session or record["state"] not in {"running", "draining"} or self._stop.is_set() or batch_id in self._worker_errors:
                return False
            try:
                tasks = self._tasks(record["entries"])
            except Exception as error:
                record.update(state="blocked", blocked_reasons=[getattr(error, "code", "original_owner_unavailable")])
                self._save(record)
                return False
            for entry in record["entries"]:
                if entry["state"] in self._ACTIVE or entry.get("run_id") and entry["state"] not in {"owner_ready", "blocked", "failed"}:
                    try:
                        self._refresh_existing(entry, tasks)
                    except Exception as error:
                        self._failure(entry, error)
            active = sum(entry["state"] in self._ACTIVE for entry in record["entries"])
            if record["state"] == "draining":
                if not active:
                    record["state"] = "paused"
                self._save(record)
                return record["state"] == "draining"
            if any(self._uncertain(entry) for entry in record["entries"]):
                record["state"] = "blocked"
                self._save(record)
                return False
            other_entities = {entry["entity_id"] for other in self._records() if other["batch_id"] != batch_id and other['state'] != 'abandoned'
                for entry in other["entries"] if entry["state"] in self._ACTIVE or self._uncertain(entry)}
            for index, entry in enumerate(record["entries"]):
                if active + len(other_entities) >= min(record["max_concurrency"], self.max_concurrency):
                    break
                if entry["state"] != "selected":
                    continue
                if not self._prior_ready(record["entries"], index):
                    continue
                if entry["entity_id"] in other_entities:
                    continue
                try:
                    selected_tasks = self._tasks([entry], include_selected=True)
                    if self._attach(entry, selected_tasks) is not None:
                        active += entry["state"] in self._ACTIVE
                        if self._uncertain(entry):
                            break
                        continue
                    fresh = self._inspect(entry["bundle_id"], entry)
                    entry["last_inspection"] = self._inspection_summary(fresh)
                    if self._ready(fresh):
                        entry.update(state="owner_ready", blocked_reasons=[])
                        continue
                    if not fresh["can_start"]:
                        entry.update(state="blocked", blocked_reasons=fresh.get("blocked_reasons") or ["owner_blocked"])
                        if self._uncertain(entry):
                            # A local pool preview intentionally did not inspect
                            # this scope. Newly discovered original uncertainty
                            # must stop later companies in THIS same step too.
                            record["state"] = "blocked"
                            break
                        continue
                    if self._stop.is_set():
                        record["state"] = "paused"
                        self._save(record)
                        return False
                    # A prior negative launch proof cannot authorize a later
                    # crash window. Clear it BEFORE persisting this new intent.
                    entry.pop('prelaunch_refusal',None)
                    entry.pop('launch_preflight_reconciliation',None)
                    entry.pop('legacy_prelaunch_reconciliation_deferred',None)
                    entry.update(state="launching", launch_requested_at=_now(),
                        launch_intent_profile='iqs.dashboard_launch_intent/1.1.0',
                        launch_attempt_id=uuid.uuid4().hex)
                    self._save(record)  # Crash on either side of start is an unknown, never an automatic re-send.
                    result = self.execution.start({"bundle_id": entry["bundle_id"], "preview_id": fresh["preview_id"]})
                    run = result.get("run") if isinstance(result, dict) else None
                    if not isinstance(run, dict):
                        raise DashboardBatchError("execution_start_invalid", "原启动未返回可核对引用", 409)
                    self._attach(entry, [run])
                    active += entry["state"] in self._ACTIVE
                except Exception as error:
                    self._failure(entry, error)
                    classifier=getattr(self.execution,'prelaunch_refusal',None)
                    proof=classifier(error,entry) if classifier is not None else None
                    if (isinstance(getattr(error,'code',None), str)
                        and self._proved_prelaunch_refusal(entry, proof, code=error.code)):
                        entry.update(prelaunch_refusal=proof,launch_uncertain=False)
                        entry['blocked_reasons']=list(dict.fromkeys([getattr(error,'code','original_owner_unavailable')]
                            +proof.get('blocked_reasons',[])))
                        # Another scope may settle/reserve between our two native
                        # previews. A bound first-party no-start proof permits ONE
                        # fresh preflight on the next tick, never a paid resend.
                        # The normal launch path rechecks tasks/scope/permissions
                        # and clears this proof before persisting a new intent.
                        refreshes = entry.get('preview_refresh_retries', 0)
                        if (error.code == 'preview_changed'
                            and proof.get('blocked_reasons') == []
                            and not entry.get('run_id')
                            and type(refreshes) is int and refreshes == 0):
                            entry.update(state='selected', blocked_reasons=[],
                                preview_refresh_retries=1)
                    # If launch was attempted but its response was lost, retain an explicit uncertainty marker.
                    elif entry.get("launch_requested_at") and not entry.get("run_id"):
                        entry["launch_uncertain"] = True
                self._save(record)
                if self._uncertain(entry):
                    record["state"] = "blocked"
                    break
            self._settle(record)
            self._save(record)
            return record["state"] == "running"

    def _launch_worker(self, batch_id):
        if not self.autostart or self._stop.is_set():
            return
        with self._memory_lock:
            prior = self._threads.get(batch_id)
            if prior and prior.is_alive():
                self._pending_workers.add(batch_id)
                return
            def work():
                try:
                    while not self._stop.is_set():
                        try:
                            if not self._step(batch_id):
                                break
                        except DashboardBatchError as error:
                            if error.code != "batch_control_busy":
                                self._worker_errors[batch_id] = {"code": error.code, "message": "批协调已停止；先核原owner后明确恢复。"}
                                break
                        except Exception:
                            self._worker_errors[batch_id] = {"code": "batch_coordinator_io_failed", "message": "本机协调记录未能安全更新；不会自动重发，需核原owner。"}
                            break
                        if self._stop.wait(self.poll_interval):
                            break
                finally:
                    with self._memory_lock:
                        if self._threads.get(batch_id) is threading.current_thread():
                            self._threads.pop(batch_id, None)
                        again = batch_id in self._pending_workers and not self._stop.is_set()
                        self._pending_workers.discard(batch_id)
                    if again:
                        self._launch_worker(batch_id)
            thread = threading.Thread(target=work, name=batch_id, daemon=True)
            self._threads[batch_id] = thread
            thread.start()

    def control(self, batch_id, action):
        if action not in {"pause", "resume", "abandon"}:
            raise DashboardBatchError("batch_control_unsupported", "只支持暂停、明确恢复或结束已停编排", 409)
        with self._mutation():
            record = self._record(batch_id)
            if action == 'abandon':
                return self._abandon(record)
            if record['state'] == 'abandoned':
                raise DashboardBatchError('batch_abandoned', '该编排已结束；原工作与结果保留，须重新准备同一范围。', 409)
            if action == "pause":
                active = any(row["state"] in self._ACTIVE for row in record["entries"])
                if record["state"] != "owner_ready":
                    record.update(state="draining" if active else "paused", pause_requested_at=_now())
                self._save(record)
                return {"batch": self._public(record), "process_started": False, "pause_scope": "scope_or_company_boundary",
                    "notice": "停止派发后续scope，当前原执行器安全完成；同公司未完成scope保留待续，不中断在途HTTP。"}
            if self._stop.is_set():
                raise DashboardBatchError("batch_service_closed", "该工作台实例已关闭", 409)
            if record["state"] == "owner_ready":
                return {"batch": self._public(record), "process_started": False}
            if (record["state"] == "running" and record.get("owner_session") == self._session
                and batch_id not in self._worker_errors and self._threads.get(batch_id)
                and self._threads[batch_id].is_alive()):
                return {"batch": self._public(record), "process_started": False}
            pending = [row for row in record["entries"] if row["state"] != "owner_ready"]
            tasks = self._tasks(pending, include_selected=True)
            task_bundles = {row.get("bundle_id") for row in tasks}
            # Ready answers remain immutable history, never permission to launch.
            # Check their frozen local registration bytes without spawning one
            # original inspector process per completed scope in a large pool.
            fresh, registration_only = [], set()
            for entry in record["entries"]:
                unstarted = (entry["state"] == "selected" and not entry.get("run_id")
                    and not entry.get("launch_requested_at") and not entry.get("launch_uncertain")
                    and entry["bundle_id"] not in task_bundles)
                if entry["state"] == "owner_ready" or unstarted:
                    try:
                        self._registration(entry)
                    except Exception as error:
                        record.update(state="blocked", blocked_reasons=[getattr(error, "code", "execution_registration_unavailable")])
                        self._save(record)
                        raise
                    fresh.append(None)
                    if unstarted:
                        registration_only.add(entry["bundle_id"])
                else:
                    fresh.append(self._inspect(entry["bundle_id"], entry))
            for entry, inspected in zip(record["entries"], fresh):
                if entry["state"] == "owner_ready" or entry["bundle_id"] in registration_only:
                    continue
                if (entry.get('launch_uncertain') and not entry.get('run_id')
                    and entry['bundle_id'] not in task_bundles):
                    legacy_candidate=('launch_intent_profile' not in entry
                        and 'launch_attempt_id' not in entry
                        and entry.get('blocked_reasons') in [['preview_required'],['execution_not_ready'],['preview_changed']])
                    reconcile=getattr(self.execution,'inspect_legacy_prelaunch',None)
                    proof=reconcile(dict(entry)) if reconcile is not None else None
                    if (legacy_candidate and isinstance(proof,dict) and proof.get('protocol')=='iqs.prelaunch_reconciliation/1.0.0'
                        and proof.get('status')=='local_refusal_reconciled'
                        and proof.get('bundle_id')==entry['bundle_id']
                        and proof.get('bundle_fingerprint')==entry['bundle_fingerprint']
                        and proof.get('launch_requested_at')==entry.get('launch_requested_at')
                        and entry.get('blocked_reasons')==[proof.get('recorded_code')]
                        and re.fullmatch('[a-f0-9]{64}',str(proof.get('current_preflight_sha256',''))) is not None
                        and proof.get('original_references_absent') is True
                        and proof.get('past_HTTP_history_attested') is False
                        and type(proof.get('API_requests')) is int and proof['API_requests']==0
                        and type(proof.get('database_writes')) is int and proof['database_writes']==0):
                        entry.pop('legacy_prelaunch_reconciliation_deferred',None)
                        entry.update(launch_uncertain=False,launch_preflight_reconciliation=proof)
                    elif legacy_candidate:
                        # A deferred original proof is still unknown. Preserve
                        # its original prewrite reason for a later EXPLICIT
                        # reconciliation; never turn a refusal into permission.
                        entry['last_inspection']=self._inspection_summary(inspected)
                        entry['legacy_prelaunch_reconciliation_deferred']=True
                        continue
                if entry.get("run_id") or entry["state"] in self._ACTIVE or entry.get("launch_uncertain") or entry["bundle_id"] in task_bundles:
                    if self._attach(entry, tasks) is None:
                        if self._ready(inspected):
                            entry.update(state="owner_ready", blocked_reasons=[])
                        else:
                            entry.update(state="blocked", blocked_reasons=["launch_reference_unknown"])
                    if entry["state"] == "running":
                        raise DashboardBatchError("batch_still_draining", "原公司进程仍在运行；等待边界，不能换实例重复派发", 409)
                elif self._ready(inspected):
                    entry.update(state="owner_ready", blocked_reasons=[])
                elif entry["state"] == "failed":
                    entry["blocked_reasons"] = ["process_exited_without_owner_ready"]
                elif inspected["can_start"]:
                    entry.update(state="selected", blocked_reasons=[])
                else:
                    entry.update(state="blocked", blocked_reasons=inspected.get("blocked_reasons") or ["owner_blocked"])
            record.update(owner_session=self._session, resumed_at=_now())
            self._worker_errors.pop(batch_id, None)
            self._settle(record)
            self._save(record)
        self._launch_worker(batch_id)
        return {"batch": self._public(record), "process_started": None,
            "company_dispatch_scheduled": record["state"] == "running", "paid_dispatch_started": None,
            "owner_inspection_deferred_scope_count": len(registration_only),
            "notice": "已核冻结原输入；未启动scope仅恢复编排，费用和额度在实际派发前由原owner重验；失败或未知请求不会自动重发。"}

    def _abandon(self, record):
        """End only this sequencer after fresh original work/process checks.

        Keep every entry and original work/attempt/answer/fee untouched. This
        is never a cancellation of an HTTP or permission to retry unknown work.
        The caller holds the batch kernel lock; also fence product launches.
        """
        if record['state'] == 'abandoned':
            return {'status': 'already_abandoned', 'batch': self._public(record), 'API_requests': 0, 'process_started': False}
        if record['state'] not in {'paused', 'draining', 'blocked', 'needs_original_inspection'}:
            raise DashboardBatchError('batch_abandon_pause_required', '先暂停原批次，不能结束活动编排。', 409)

        def stopped():
            tasks = self._tasks(record['entries'], include_selected=True)
            evidence = []
            for entry in record['entries']:
                matches = [task for task in tasks if task.get('bundle_id') == entry['bundle_id']]
                if entry.get('run_id'):
                    matches = [task for task in matches if task.get('run_id') == entry['run_id']]
                no_start_proved = (not entry.get('run_id') and entry.get('launch_uncertain') is False
                    and self._proved_prelaunch_refusal(entry, entry.get('prelaunch_refusal')))
                if len(matches) > 1 or (not matches and (entry.get('run_id') or entry.get('launch_requested_at') or entry.get('launch_uncertain')) and not no_start_proved):
                    raise DashboardBatchError('batch_abandon_reference_unresolved', '原启动引用仍不明确，不能释放公司编排。', 409)
                if not matches:
                    continue
                task = matches[0]
                if (task.get('bundle_fingerprint') != entry['bundle_fingerprint'] or task.get('entity_id') != entry['entity_id']
                    or re.fullmatch(r'run-[a-f0-9]{32}', str(task.get('run_id', ''))) is None
                    or task.get('process_state') not in {'running', 'starting', 'needs_original_inspection', 'process_exited', 'launch_failed'}):
                    raise DashboardBatchError('batch_abandon_reference_unresolved', '原启动引用范围不匹配。', 409)
                if task['run_id'] in getattr(self.execution, '_processes', {}):
                    raise DashboardBatchError('batch_abandon_process_unresolved', '原执行进程仍在本机运行。', 409)
                proof = _process_recovery_evidence(task, False)
                if proof not in {'known_local_exit', 'absent', 'original_pid_reused'}:
                    raise DashboardBatchError('batch_abandon_process_unresolved', '原进程尚未证明已退出，不能结束编排。', 409)
                evidence.append({'run_id': task['run_id'], 'evidence': proof})
            return evidence

        with self.execution._control_lock('batch-abandon'):
            stopped()
            inspections = []
            for entry in record['entries']:
                preview = self._inspect(entry['bundle_id'], entry)
                work = preview.get('inspection', {}).get('work_items')
                work = list(work.values()) if isinstance(work, dict) else work
                if (not isinstance(work, list) or not work or any(not isinstance(item, dict)
                    or item.get('status') not in {'pending', 'failed', 'result_ready', 'delivered'} for item in work)):
                    raise DashboardBatchError('batch_abandon_work_unresolved', '原工作仍有leased/uncertain或检查不完整，不能释放编排。', 409)
                inspections.append({'bundle_id': entry['bundle_id'], 'inspection_sha256': preview['inspection_sha256']})
            process_evidence = stopped()  # Recheck after potentially slow original I/O.
            record.update(state='abandoned', abandoned_at=_now(), abandonment_evidence={
                'selection_sha256': record['selection_sha256'], 'processes': process_evidence, 'inspections': inspections,
                'original_work_preserved': True, 'dispatch_authority': False})
            self._save(record)
        return {'status': 'abandoned', 'batch': self._public(record), 'API_requests': 0, 'process_started': False,
                'notice': '仅结束本次编排；原工作、结果、费用与历史保留。新准备仍由原owner复用或拒绝原工作，不会重置未知请求。'}

    def close(self):
        """Stop this sequencer only. Native child processes and their HTTP continue."""
        self._stop.set()
        deadline = time.monotonic() + 1.0
        with self._memory_lock:
            threads = list(self._threads.values())
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=max(0, deadline - time.monotonic()))

    shutdown = close
