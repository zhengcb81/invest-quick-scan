"""Local product gateway to the original StockQA executor, never a work queue.

The server registers immutable owner bundles. Browser input only selects one;
native inspection and execution keep authority over work, budgets and recovery.
The small local records below describe launched processes, not completed work.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from contextlib import contextmanager
import uuid

try:
    from .dashboard_locks import control_lock, ControlBusyError
except ImportError:
    from dashboard_locks import control_lock, ControlBusyError


class DashboardExecutionError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.details = details or {}


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _probe_process(pid):
    """Read-only Win32 evidence, never a signal or permission to retry work.

    Only ERROR_INVALID_PARAMETER for a valid PID proves that PID is absent.
    Any extant handle (including a possibly reused/exited PID), access denial,
    missing ID, unsupported platform or failed API call remains non-authorizing.
    """
    if type(pid) is not int or not 1 <= pid <= 0xffffffff or sys.platform != 'win32':
        return 'unknown'
    try:
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        ctypes.set_last_error(0)
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return 'absent' if ctypes.get_last_error() == 87 else 'unknown'
        evidence = 'unknown'
        try:
            code = wintypes.DWORD()
            if kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                evidence = 'present' if code.value == 259 else 'present_exited'
        finally:
            if not kernel.CloseHandle(handle):
                evidence = 'unknown'
        return evidence
    except Exception:
        return 'unknown'


def _process_recovery_evidence(record, readonly_recovery):
    """One rule for UI action projection and fresh explicit resume checks."""
    if record.get('process_state') not in {'running', 'starting', 'needs_original_inspection'}:
        return 'known_local_exit'
    if readonly_recovery is True:
        return 'original_checkpoints_only'
    evidence = _probe_process(record.get('pid'))
    if evidence in {'present', 'present_exited'}:
        # A pause record was persisted only after observing that launch's PID.
        # A process created later cannot be the original process. Never use an
        # old pause from before a subsequent resume as an observation boundary.
        try:
            launch = record.get('resumed_at') or record['started_at']
            observed = record['pause_requested_at']
            if (isinstance(launch, str) and launch.endswith('Z') and isinstance(observed, str) and observed.endswith('Z')
                and datetime.fromisoformat(observed.replace('Z', '+00:00')) >= datetime.fromisoformat(launch.replace('Z', '+00:00'))
                and _process_created_after(record.get('pid'), observed) is True):
                return 'original_pid_reused'
        except (KeyError, TypeError, ValueError, OverflowError):
            pass
    return evidence


def _process_created_after(pid, observed_at):
    """Read process creation FILETIME on one Win32 handle; no process mutation."""
    if type(pid) is not int or not 1 <= pid <= 0xffffffff or sys.platform != 'win32':
        return None
    try:
        if not isinstance(observed_at, str) or not observed_at.endswith('Z'):
            return None
        observed = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
        delta = observed - datetime(1601, 1, 1, tzinfo=timezone.utc)
        ticks = (delta.days * 86400 + delta.seconds) * 10000000 + delta.microseconds * 10
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        result = None
        try:
            created, exited, kernel_time, user_time = [wintypes.FILETIME() for _ in range(4)]
            if kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel_time), ctypes.byref(user_time)):
                actual = (created.dwHighDateTime << 32) | created.dwLowDateTime
                result = actual > ticks
        finally:
            if not kernel.CloseHandle(handle):
                result = None
        return result
    except Exception:
        return None


def _read(path):
    raw = Path(path).read_bytes()
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("input_too_large")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def _write(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(",", ":")).encode()).hexdigest()


_STOPPED_EVIDENCE = {'known_local_exit', 'absent', 'original_pid_reused'}


def _valid_retirement(record):
    proof = record.get('retirement')
    fields = {'protocol', 'observed_at', 'process_evidence', 'bundle_fingerprint',
              'work_inspection_sha256', 'work_item_count', 'work_status_counts', 'proof_sha256'}
    if not isinstance(proof, dict) or set(proof) != fields:
        return False
    try:
        moment = proof['observed_at']
        if (proof['protocol'] != 'iqs.dashboard_stopped_reference/1.0.0'
            or not isinstance(moment, str) or not moment.endswith('Z')
            or datetime.fromisoformat(moment.replace('Z', '+00:00')).utcoffset() is None
            or proof['process_evidence'] not in _STOPPED_EVIDENCE
            or proof['bundle_fingerprint'] != record['bundle_fingerprint']
            or re.fullmatch('[a-f0-9]{64}', str(proof['work_inspection_sha256'])) is None
            or type(proof['work_item_count']) is not int or proof['work_item_count'] < 1
            or not isinstance(proof['work_status_counts'], dict)
            or not proof['work_status_counts']
            or set(proof['work_status_counts']) - {'pending', 'failed', 'result_ready', 'delivered'}
            or any(type(count) is not int or count < 1 for count in proof['work_status_counts'].values())
            or sum(proof['work_status_counts'].values()) != proof['work_item_count']
            or proof['proof_sha256'] != _digest({k:v for k,v in proof.items() if k != 'proof_sha256'})):
            return False
        return True
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


_POLICY_HELPER = r'''
import contextlib, hashlib, json, pathlib, sys
source, target, mode = sys.argv[1:]
sys.path.insert(0, source)
try:
    with contextlib.redirect_stdout(sys.stderr):
        from src.config.llm_config import LLMConfig
        path = pathlib.Path(target)
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8-sig"))
        policy = document.get("quick_scan_model_policy")
        if mode == "save":
            request = json.load(sys.stdin)
            if request["revision_sha256"] != hashlib.sha256(raw).hexdigest():
                raise RuntimeError("settings_changed")
            policy = request["policy"]
            LLMConfig(str(path)).save_quick_scan_model_policy(policy)
        else:
            if policy is not None:
                LLMConfig._validate_quick_scan_policy(policy)
        revision = hashlib.sha256(path.read_bytes()).hexdigest()
        providers = document.get("providers")
        choices = []
        if isinstance(providers, dict):
            for name, value in sorted(providers.items()):
                if not isinstance(name, str) or not name or len(name) > 200 or not isinstance(value, dict):
                    continue
                model = value.get("model", "")
                choices.append({"provider_config_ref": name,
                    "model": model if isinstance(model, str) and len(model) <= 200 else "",
                    "enabled": value.get("enabled") is True})
    print(json.dumps({"policy": policy, "revision_sha256": revision,
        "provider_config_refs": [row["provider_config_ref"] for row in choices],
        "provider_choices": choices, "provider_metadata_available": isinstance(providers, dict),
        "effective": "next_run", "API_requests": 0}, ensure_ascii=False, allow_nan=False))
except Exception as error:
    print(json.dumps({"error_code": "settings_changed" if str(error) == "settings_changed" else "owner_policy_rejected"}))
    raise SystemExit(2)
'''


_REGISTERED_PERMISSIONS_HELPER = r'''
import contextlib, json, sys
source, config_path, confirmation_id = sys.argv[1:]
sys.path.insert(0, source)
try:
    with contextlib.redirect_stdout(sys.stderr):
        from src.utils.quick_scan_refresh_admission import RefreshAdmissionService
        proof, _, _ = RefreshAdmissionService(config_path).read_registered(confirmation_id)
        if proof["confirmation"]["confirmation_id"] != confirmation_id:
            raise ValueError("original_confirmation_mismatch")
    result = {"protocol": "iqs.dashboard_registered_permissions/1.0.0",
        "status": "passed", "confirmation_id": confirmation_id,
        "permission_authenticated": True, "API_requests": 0}
    code = 0
except Exception as error:
    reason = getattr(error, "reason", "owner_confirmation_permissions_rejected")
    import re
    if not isinstance(reason, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,159}", reason) is None:
        reason = "owner_confirmation_permissions_rejected"
    result = {"error_code": reason, "API_requests": 0}
    code = 2
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
raise SystemExit(code)
'''


class ExecutionGateway:
    def __init__(self, config):
        self.config = dict(config or {})
        self.bundles = self.config.get("bundles", {})
        if not isinstance(self.bundles, dict):
            raise DashboardExecutionError("execution_config_invalid", "bundles必须是对象")
        self.state_root = Path(self.config.get("state_root", Path(__file__).resolve().parents[1] / "runs/dashboard-execution"))
        self._lock, self._processes, self._previews = threading.RLock(), {}, {}
        self._owner_snapshots = {}

    def _select(self, payload, *, launching=False):
        if not isinstance(payload, dict) or set(payload) - ({"bundle_id", "entity_id", "preview_id"} if launching else {"bundle_id", "entity_id"}):
            raise DashboardExecutionError("selection_invalid", "只允许选择已注册的公司和执行包")
        bundle_id = payload.get("bundle_id")
        if bundle_id is None:
            choices = [key for key, bundle in self.bundles.items() if bundle.get("entity_id") == payload.get("entity_id")]
            if len(choices) != 1:
                raise DashboardExecutionError("bundle_selection_required", "该公司需要选择一个已配置执行包", 409)
            bundle_id = choices[0]
        if not isinstance(bundle_id, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", bundle_id) is None or bundle_id not in self.bundles:
            raise DashboardExecutionError("bundle_unknown", "未注册的执行包", 404)
        bundle = self.bundles[bundle_id]
        if not isinstance(bundle, dict) or payload.get("entity_id", bundle.get("entity_id")) != bundle.get("entity_id"):
            raise DashboardExecutionError("entity_mismatch", "公司身份与执行包不一致", 409)
        return bundle_id, bundle

    def _deployment(self, bundle):
        missing = []
        root = Path(self.config.get("stockqa_root", ""))
        runtime = Path(bundle.get("runtime_dir", self.config.get("runtime_dir", "")))
        if not root.is_absolute() or not (root / "main_with_llm.py").is_file():
            missing.append("stockqa_root")
        if not runtime.is_absolute() or not runtime.is_dir():
            missing.append("runtime_dir")
        fields = ("questions", "manifest", "identity_snapshot", "c06_authority", "owner_config", "admission_config", "spend_authorization", "inspection_request")
        for field in fields:
            path = Path(bundle.get(field, ""))
            if not path.is_absolute() or not path.is_file():
                missing.append(field)
        for field in ("entity_id", "company", "provider", "confirmation_id"):
            if not isinstance(bundle.get(field), str) or not bundle[field].strip():
                missing.append(field)
        if not (runtime / "llm_apis.json").is_file():
            missing.append("runtime_llm_config")
        configured = self.config.get("model_policy_path")
        if configured and Path(configured).resolve() != (runtime / "llm_apis.json").resolve():
            missing.append("model_policy_runtime_mismatch")
        pack, tokens = bundle.get("pack_size", 1), bundle.get("max_output_tokens", 8192)
        if type(pack) is not int or not 1 <= pack <= 30 or type(tokens) is not int or not 1 <= tokens <= 32768 or type(bundle.get("thinking", True)) is not bool:
            missing.append("generation_controls")
        admission = None
        if "admission_config" not in missing:
            try:
                admission = _read(bundle["admission_config"])
                for field in ("work_store", "budget_policy_file"):
                    path = Path(admission.get(field, ""))
                    if not path.is_absolute() or not path.is_file():
                        missing.append("admission_" + field)
            except (OSError, ValueError, TypeError, AttributeError):
                missing.append("admission_config_invalid")
        if "identity_snapshot" not in missing:
            try:
                identity=_read(bundle['identity_snapshot'])
                values=[identity.get('entity_id')]
                if isinstance(identity.get('payload'),dict): values.append(identity['payload'].get('entity_id'))
                values=[value for value in values if value is not None]
                if not values or any(value!=bundle.get('entity_id') for value in values):
                    missing.append("identity_entity_mismatch")
            except (OSError, ValueError, TypeError, AttributeError):
                missing.append("identity_invalid")
        if "inspection_request" not in missing:
            try:
                if _read(bundle["inspection_request"]).get("entity_id") != bundle.get("entity_id"):
                    missing.append("inspection_entity_mismatch")
            except (OSError, ValueError, TypeError, AttributeError):
                missing.append("inspection_request_invalid")
        if bundle.get("search_policy") and (not Path(bundle["search_policy"]).is_absolute() or not Path(bundle["search_policy"]).is_file()):
            missing.append("search_policy")
        return root, runtime, admission, sorted(set(missing))

    def _fingerprint(self, bundle):
        inputs = {}
        for name in ("questions", "manifest", "identity_snapshot", "c06_authority", "owner_config", "admission_config", "spend_authorization", "inspection_request", "search_policy"):
            if name in bundle:
                try:
                    raw = Path(bundle[name]).read_bytes()
                    inputs[name] = hashlib.sha256(raw).hexdigest()
                except OSError:
                    inputs[name] = "unavailable"
        return _digest({"registration": bundle, "input_bytes": inputs})

    def _environment(self, root, *, paid=False):
        env = dict(os.environ)
        if not paid:
            for key in list(env):
                if re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD|LIVE_E2E)", key, re.I):
                    env.pop(key, None)
        env.update(PYTHONPATH=str(root), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        return env

    def _call(self, command, root, runtime, *, input_value=None):
        try:
            result = subprocess.run(command, cwd=runtime, env=self._environment(root),
                input=json.dumps(input_value) if input_value is not None else None,
                capture_output=True, text=True, encoding="utf-8", timeout=130,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            output = json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise DashboardExecutionError("owner_transport_unavailable", "原执行器暂不可用；未重发模型请求", 503) from None
        if result.returncode or not isinstance(output, dict) or output.get("API_requests") != 0:
            raise DashboardExecutionError(output.get("error_code", "owner_inspection_rejected") if isinstance(output, dict) else "owner_inspection_rejected", "原执行器拒绝请求；未发出模型调用", 409)
        return output

    def status(self):
        entries = []
        for key, bundle in self.bundles.items():
            _, _, _, missing = self._deployment(bundle)
            grouping = {name: bundle[name] for name in ('company_preparation_id', 'scope', 'scope_id', 'security_id', 'expected_scope_bindings') if name in bundle}
            entries.append({**grouping, "bundle_id": key, "entity_id": bundle.get("entity_id"), "company": bundle.get("company"),
                            "status": "needs_configuration" if missing else "configured_not_inspected", "missing": missing})
        return {"protocol": "iqs.dashboard_execution/1.0.0", "available": any(not entry['missing'] for entry in entries),
                "configured": bool(entries), "bundles": entries, "registered_bundles": entries,
                "supports": {"preview": True, "start_registered_bundle": True, "inspect": True,
                             "pause": True, "resume": True, "pause_scope": "company_boundary", "automatic_pool_dispatch": False},
                "task_state_owner": "StockQAbyLLM", "API_requests": 0}

    def bundle_registration(self, bundle_id):
        """Read immutable local inputs without spawning an owner inspection."""
        key, bundle = self._select({"bundle_id": bundle_id})
        grouping = {name: bundle[name] for name in ('company_preparation_id', 'scope', 'scope_id', 'security_id', 'expected_scope_bindings') if name in bundle}
        return {**grouping, "bundle_id": key, "entity_id": bundle.get("entity_id"),
                "bundle_fingerprint": self._fingerprint(bundle), "API_requests": 0}

    @staticmethod
    def inspection_work_items(inspection):
        """Current native DTO is keyed by question ID; retain raw DTO for hashes."""
        value=inspection.get('work_items')
        if isinstance(value,dict):
            if any(not isinstance(key,str) or not key or not isinstance(row,dict)
                or row.get('question_id',key)!=key for key,row in value.items()):
                raise DashboardExecutionError('owner_inspection_contract_invalid','原逐题检查映射无效。',409)
            return [{**row,'question_id':key} for key,row in value.items()]
        if isinstance(value,list) and all(isinstance(row,dict) for row in value):
            return value  # Historical transport fixtures; never rewrite native bytes.
        raise DashboardExecutionError('owner_inspection_contract_invalid','原执行检查缺少逐题映射。',409)

    @classmethod
    def work_progress_projection(cls, inspection, *, observed_at, cached):
        """Display only native work states from an explicitly dated snapshot.

        No process flag, score, budget, cached label or exit code is progress
        evidence. This projection is never used for admission or execution.
        """
        empty = {'status_counts': None, 'counts': None,
            'status_counts_source': None, 'status_counts_observed_at': observed_at,
            'status_counts_is_cached_projection': cached,
            'progress_label': '原进度无法核实，请核原状态。'}
        labels = {'result_ready': '已保存', 'leased': '在途', 'pending': '待问',
                  'uncertain': '待核实', 'failed': '失败', 'delivered': '已交付', 'missing': '原工作缺失'}
        try:
            rows = cls.inspection_work_items(inspection)
            if not rows or any(row.get('status') not in labels for row in rows):
                return empty
            counts = {}
            for row in rows:
                counts[row['status']] = counts.get(row['status'], 0) + 1
        except (DashboardExecutionError, TypeError, AttributeError):
            return empty
        parts = '、'.join(label + str(counts[state]) for state, label in labels.items() if counts.get(state))
        marker = '缓存快照' if cached else '本次核实快照'
        moment = observed_at if isinstance(observed_at, str) and observed_at else '时间未记录'
        return {'status_counts': counts, 'counts': dict(counts),
            'status_counts_source': inspection.get('protocol'), 'status_counts_observed_at': observed_at,
            'status_counts_is_cached_projection': cached,
            'progress_label': f'原scope工作快照：{parts}（共{len(rows)}题；{marker}；核实于{moment}）'}

    def _registered_permissions(self, bundle, root, runtime):
        """Read original registered consent/current authority, never admit new work.

        The original reader owns receipt/deployment/input checks. It may create
        and clean temporary validation copies in its configured runs directory;
        this is not a claim of zero filesystem activity.
        """
        command = [str(self.config.get("stockqa_python", sys.executable)), "-B", "-X", "utf8",
                   "-c", _REGISTERED_PERMISSIONS_HELPER, str(root),
                   bundle["admission_config"], bundle["confirmation_id"]]
        try:
            result = self._call(command, root, runtime)
        except DashboardExecutionError as error:
            return {"status": "blocked", "reason": error.code}
        if (result.get("protocol") != "iqs.dashboard_registered_permissions/1.0.0"
            or result.get("status") != "passed"
            or result.get("confirmation_id") != bundle["confirmation_id"]
            or result.get("permission_authenticated") is not True
            or type(result.get("API_requests")) is not int or result["API_requests"] != 0):
            return {"status": "blocked", "reason": "owner_permissions_contract_invalid"}
        return {"status": "passed", "confirmation_id": bundle["confirmation_id"],
                "inspection_mode": "current_permissions", "registered_action_checked": True}

    def _inspect_work(self, bundle, root, runtime, admission):
        """Original fixed read-only ledger inspection, not consent or dispatch."""
        command = [str(self.config.get("stockqa_python", sys.executable)), "-B", "-X", "utf8", "-m",
                   "src.utils.quick_scan_refresh_inspect_cli", "--ledger", admission["work_store"],
                   "--policy", admission["budget_policy_file"], "--request", bundle["inspection_request"],
                   "--schema-version", bundle.get("inspection_schema_version", "1.0.0")]
        if bundle.get("inspection_schema_version") in {"1.4.0", "1.5.0"}:
            command.extend(["--admission-config", bundle["admission_config"]])
        inspection = self._call(command, root, runtime)
        if (inspection.get("protocol") != "stockqa.refresh_inspection/" + bundle.get("inspection_schema_version", "1.0.0")
            or inspection.get("reservation_created") is not False
            or not isinstance(inspection.get("quote"), dict)):
            raise DashboardExecutionError("owner_inspection_contract_invalid", "原执行器返回了不匹配的预览结构", 409)
        return inspection

    def _retirement_work(self, bundle):
        root, runtime, admission, missing = self._deployment(bundle)
        if missing:
            raise DashboardExecutionError('retirement_inspection_unavailable', '原范围部署不完整，不能登记已停止事实', 409)
        inspection = self._inspect_work(bundle, root, runtime, admission)
        return self._retirement_work_summary(bundle, inspection)

    def _retirement_work_summary(self, bundle, inspection):
        """Validate original scope metadata; cached UI evidence never controls writes."""
        work = self.inspection_work_items(inspection)
        expected = _read(bundle['inspection_request']).get('question_ids')
        actual = [row.get('question_id') for row in work]
        if (type(inspection.get('API_requests')) is not int or inspection['API_requests'] != 0
            or not isinstance(expected, list) or not expected or any(not isinstance(qid, str) or not qid for qid in expected)
            or len(set(expected)) != len(expected) or any(not isinstance(qid, str) for qid in actual)
            or len(actual) != len(set(actual)) or set(actual) != set(expected)
            or any(row.get('status') not in {'pending', 'failed', 'result_ready', 'delivered'} for row in work)):
            raise DashboardExecutionError('retirement_work_unknown', '原范围含在途、未知或缺少题目，不能退役启动引用', 409)
        counts = {}
        for row in work:
            counts[row['status']] = counts.get(row['status'], 0) + 1
        return {'work_inspection_sha256': _digest(inspection), 'work_item_count': len(work), 'work_status_counts': counts}

    def preview(self, payload):
        key, bundle = self._select(payload)
        grouping = {name: bundle[name] for name in ('company_preparation_id', 'scope', 'scope_id', 'security_id', 'expected_scope_bindings') if name in bundle}
        root, runtime, admission, missing = self._deployment(bundle)
        if missing:
            return {**grouping, "bundle_id": key, "entity_id": bundle.get("entity_id"), "status": "blocked", "missing": missing,
                    "bundle_fingerprint": self._fingerprint(bundle),
                    "blocked_reasons": missing, "preview_id": None, "can_start": False, "API_requests": 0}
        inspection = self._inspect_work(bundle, root, runtime, admission)
        quote = inspection.get("quote", {})
        work = self.inspection_work_items(inspection)
        unknown = any(row.get("status") in {"uncertain", "leased"} for row in work)
        readonly = bool(work) and all(row.get("status") in {"result_ready", "delivered"} for row in work)
        permissions = self._registered_permissions(bundle, root, runtime)
        ready = not unknown and (quote.get("budget_available") is True or readonly) and permissions['status'] == 'passed'
        preview_id = "preview-" + uuid.uuid4().hex
        self._previews[preview_id] = {"bundle_id": key, "bundle_fingerprint": self._fingerprint(bundle), "inspection_sha256": _digest(inspection)}
        while len(self._previews) > 128:
            self._previews.pop(next(iter(self._previews)))
        blocked = []
        if unknown:
            blocked.append("owner_work_unknown")
        elif quote.get("budget_available") is not True and not readonly:
            blocked.append("owner_budget_or_original_work_blocked")
        if permissions['status'] != 'passed':
            blocked.append(permissions['reason'])
        return {**grouping, "bundle_id": key, "entity_id": bundle["entity_id"], "status": "ready" if ready else "blocked",
                "bundle_fingerprint": self._previews[preview_id]['bundle_fingerprint'],
                "preview_id": preview_id, "inspection_sha256": _digest(inspection), "readonly_recovery": readonly,
                "can_start": ready, "missing": blocked,
                "blocked_reasons": blocked, "inspection": inspection, "API_requests": 0, "database_writes": 0,
                "permissions_check": permissions,
                "required_action": ("fresh_same_scope_owner_preparation" if permissions.get('reason') in {
                    'delegation_expired_or_future', 'delegation_revoked'}
                    else "inspect_original_owner_permissions") if permissions['status'] != 'passed' else None,
                "notice": "预览不预留费用；原owner同时检查已登记确认的当前权限。权限失效须重新准备同一scope，不能扩预算或重发旧任务。执行前仍会再次核验。"}

    def _records(self):
        if not self.state_root.is_dir():
            return []
        values = []
        for path in sorted(self.state_root.glob("run-*.json")):
            try:
                value = _read(path)
                if (isinstance(value, dict) and value.get("protocol") == "iqs.dashboard_process_reference/1.0.0"
                    and re.fullmatch(r"run-[a-f0-9]{32}", str(value.get("run_id", "")))
                    and path.stem == value["run_id"]
                    and isinstance(value.get("bundle_id"), str)
                    and re.fullmatch(r"[a-f0-9]{64}", str(value.get("bundle_fingerprint", "")))
                    and value.get("process_state") in {"starting", "running", "process_exited", "launch_failed", "needs_original_inspection", "observed_stopped"}
                    and value.get("launcher_state") in {"running", "draining", "paused", "retired"}
                    and ((value.get('process_state') == 'observed_stopped') == (value.get('launcher_state') == 'retired'))
                    and (value.get('launcher_state') != 'retired' or _valid_retirement(value))):
                    values.append(value)
                else:
                    raise ValueError("invalid_process_reference")
            except (OSError, ValueError):
                raise DashboardExecutionError("process_reference_corrupt", "启动记录损坏；先核对原owner，不能按空任务重新派发", 409) from None
        return values

    def active_references(self):
        """Complete local safety check without inspecting every historical work item."""
        return {'tasks': [row for row in self._records() if row['process_state'] in {
            'running', 'starting', 'needs_original_inspection'}], 'API_requests': 0}

    def tasks(self, *, bundle_ids=None, run_ids=None, inspect_owner=True, limit=50, offset=0):
        if (type(limit) is not int or not 1 <= limit <= 2000 or type(offset) is not int or offset < 0
            or any(value is not None and (not isinstance(value, list) or len(value) > 5000 or
                any(not isinstance(item, str) for item in value)) for value in (bundle_ids, run_ids))):
            raise DashboardExecutionError('task_query_invalid', '任务筛选或分页无效')
        values = self._records()
        if bundle_ids is not None:
            values = [row for row in values if row['bundle_id'] in bundle_ids]
        if run_ids is not None:
            values = [row for row in values if row['run_id'] in run_ids]
        values.sort(key=lambda row: row.get('started_at', ''), reverse=True)
        total = len(values)
        values = values[offset:offset+limit]
        for value in values:
            if value["process_state"] in {"running", "starting"} and value["run_id"] not in self._processes:
                value.update(process_state="needs_original_inspection", recovery="inspect_original_owner_no_automatic_resend")
            value["work_completion_authoritative"] = False
            value['process_state_notice'] = '本地启动记录不是操作系统存活证明；恢复时重新检查原进程和原owner。'
            value.update(status_counts=None, counts=None, status_counts_source=None,
                status_counts_observed_at=None, status_counts_is_cached_projection=None,
                progress_label='原进度未读取，请核原状态。')
            actions = ["inspect"]
            if value.get("launcher_state") not in {"paused", "retired"}:
                actions.append("pause")  # Stops future companies, never interrupts an HTTP.
            try:
                if inspect_owner:
                    preview = self.preview({"bundle_id": value["bundle_id"]})
                    observed_at = _now()
                    self._owner_snapshots[value['run_id']] = {'preview': preview, 'observed_at': observed_at}
                    value['inspection_observed_at'] = observed_at
                    value['inspection_is_cached_projection'] = False
                elif value['run_id'] in self._owner_snapshots:
                    snapshot = self._owner_snapshots[value['run_id']]
                    preview = snapshot['preview']
                    value['inspection_observed_at'] = snapshot['observed_at']
                    value['inspection_is_cached_projection'] = True
                else:
                    value.update(inspection_status='not_requested', allowed_actions=actions)
                    continue
                value["owner_preview"] = preview
                value["inspection_status"] = "available"
                value.update(self.work_progress_projection(preview.get('inspection'),
                    observed_at=value.get('inspection_observed_at'),
                    cached=value.get('inspection_is_cached_projection') is True))
                stopped_evidence = None
                if (value.get("launcher_state") in {"paused", "draining"}
                    and value["run_id"] not in self._processes
                    and value["bundle_fingerprint"] == self._fingerprint(self.bundles[value["bundle_id"]])
                    and preview["can_start"]):
                    evidence = _process_recovery_evidence(value, preview.get('readonly_recovery'))
                    if preview.get('readonly_recovery') is False:
                        stopped_evidence = evidence
                    value['process_recovery_evidence'] = evidence
                    if evidence in {'known_local_exit', 'original_checkpoints_only', 'absent', 'original_pid_reused'}:
                        actions.append("resume")
                if (isinstance(preview.get('inspection'), dict)
                    and value.get('launcher_state') != 'retired' and value['run_id'] not in self._processes
                    and value['bundle_fingerprint'] == self._fingerprint(self.bundles[value['bundle_id']])):
                    try:
                        self._retirement_work_summary(self.bundles[value['bundle_id']], preview['inspection'])
                        if stopped_evidence is None:
                            stopped_evidence = _process_recovery_evidence(value, False)
                        if stopped_evidence in _STOPPED_EVIDENCE:
                            actions.append('retire')
                    except DashboardExecutionError:
                        pass
            except DashboardExecutionError as error:
                value.update(inspection_status="unavailable", inspection_error=error.code,
                    progress_label='原进度无法核实，请核原状态。')
            value["allowed_actions"] = actions
        return {"protocol": "iqs.dashboard_process_references/1.0.0", "tasks": values, 'total': total,
                'offset': offset, 'limit': limit, 'next_offset': offset+limit if offset+limit < total else None, "API_requests": 0}

    def _command(self, bundle, root, output):
        command = [str(self.config.get("stockqa_python", sys.executable)), "-B", "-X", "utf8", str(root / "main_with_llm.py")]
        flags = {"company": "company", "entity_id": "entity-id", "provider": "provider", "questions": "config", "identity_snapshot": "identity-snapshot",
                 "manifest": "question-manifest", "c06_authority": "c06-authority", "owner_config": "quick-scan-owner-config",
                 "admission_config": "refresh-admission-config", "confirmation_id": "refresh-confirmation-id", "spend_authorization": "spend-authorization"}
        for field, flag in flags.items():
            command.extend(["--" + flag, str(bundle[field])])
        command.extend(["--require-search", "--output", str(output), "--question-pack-size", str(bundle.get("pack_size", 1)),
                        "--thinking-enabled", str(bundle.get("thinking", True)).lower(), "--max-output-tokens", str(bundle.get("max_output_tokens", 8192))])
        if bundle.get("search_policy"):
            command.extend(["--search-policy", str(bundle["search_policy"])])
        if bundle.get("security_scope_id"):
            command.extend(["--security-scope-id", str(bundle["security_scope_id"])])
        return command

    def start(self, payload):
        key, bundle = self._select(payload, launching=True)
        with self._lock:
            self.state_root.mkdir(parents=True, exist_ok=True)
            with self._control_lock('start'):
                prior = [row for row in self._records() if row["bundle_id"] == key]
                if prior:
                    record = prior[-1]
                    if record['launcher_state'] == 'retired':
                        raise DashboardExecutionError('run_retired', '该启动引用已退役；保留历史，新执行须原同scope准备', 409)
                    if record["bundle_fingerprint"] != self._fingerprint(bundle):
                        raise DashboardExecutionError("bundle_changed", "执行包已改变；保留原任务，请登记新包后执行", 409)
                    if record["process_state"] in {"running", "starting"} and record["run_id"] not in self._processes:
                        record.update(process_state="needs_original_inspection", recovery="inspect_original_owner_no_automatic_resend")
                    return {"status": "attached", "run": record, "process_started": False, "paid_dispatch_started": None}
                selected = self._previews.get(payload.get("preview_id"))
                if not selected or selected["bundle_id"] != key or selected["bundle_fingerprint"] != self._fingerprint(bundle):
                    raise DashboardExecutionError("preview_required", "请先预览当前公司执行计划", 409)
                preview = self.preview({"bundle_id": key})
                if not preview["can_start"]:
                    raise DashboardExecutionError("execution_not_ready", "执行前置未满足", 409, preview)
                if selected["inspection_sha256"] != preview["inspection_sha256"]:
                    raise DashboardExecutionError("preview_changed", "原任务或费用状态已变化；请查看更新后的预览", 409, preview)
                root, runtime, _, _ = self._deployment(bundle)
                run_id = "run-" + uuid.uuid4().hex
                folder = self.state_root / run_id
                folder.mkdir()
                record = {"protocol": "iqs.dashboard_process_reference/1.0.0", "run_id": run_id, "bundle_id": key,
                          "bundle_fingerprint": self._fingerprint(bundle), "entity_id": bundle["entity_id"], "started_at": _now(),
                          "process_state": "starting", "launcher_state": "running", "launch_attempt": 1,
                          "pause_scope": "company_boundary", "work_completion_authoritative": False,
                          "result_path": str(folder / "result.json"), "log_path": str(folder / "process.log")}
                path = self.state_root / (run_id + ".json")
                _write(path, record)  # A crash now requires inspection, never blind resend.
                try:
                    process = subprocess.Popen(self._command(bundle, root, folder / "result.json"), cwd=runtime,
                        env=self._environment(root, paid=True), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace",
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                except OSError:
                    record.update(process_state="launch_failed", finished_at=_now(), exit_code=None)
                    _write(path, record)
                    raise DashboardExecutionError("launch_failed", "本机无法启动原执行器；请检查部署", 503) from None
                record.update(process_state="running", pid=process.pid)
                _write(path, record)
                self._processes[run_id] = process
                threading.Thread(target=self._finish, args=(process, path, record), daemon=True).start()
                return {"status": "started", "run": record, "process_started": True, "paid_dispatch_started": None}

    def _finish(self, process, path, record):
        secret_values = [value for key, value in os.environ.items() if re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, re.I) and len(value) >= 8]
        written = 0
        try:
            with Path(record["log_path"]).open("w", encoding="utf-8") as log:
                for line in process.stdout:
                    for secret in secret_values:
                        line = line.replace(secret, "[REDACTED]")
                    line = re.sub(r"(?i)(?:sk-|Bearer\s+)[A-Za-z0-9_.-]{12,}", "[REDACTED]", line)
                    if written < 1024 * 1024:
                        safe = line[:1024 * 1024 - written]
                        log.write(safe)
                        log.flush()
                        written += len(safe)
            exit_code = process.wait()
            record.update(process_state="process_exited", finished_at=_now(), exit_code=exit_code,
                          completion_notice="进程退出不代表已评分、已导入或金融结论已通过；请读取原owner状态")
        except Exception:
            record.update(process_state="needs_original_inspection", finished_at=_now())
        finally:
            with self._lock:
                try:
                    # A second server instance can request drain while this
                    # child exits. Merge under the SAME cross-process lock.
                    for attempt in range(200):
                        try:
                            with self._control_lock('finish'):
                                current = _read(path)
                                if current.get('process_state') == 'observed_stopped' and current.get('launcher_state') == 'retired':
                                    break  # Another original control already observed this launch stopped.
                                known_failure = (record.get('process_state') == 'process_exited'
                                    and type(record.get('exit_code')) is int and record['exit_code'] != 0)
                                record['launcher_state'] = 'paused' if known_failure or current.get('launcher_state') == 'draining' else current.get('launcher_state', 'running')
                                _write(path, record)
                            break
                        except DashboardExecutionError as error:
                            if error.code != 'launch_in_progress' or attempt == 199:
                                raise
                            time.sleep(0.01)
                finally:
                    self._processes.pop(record["run_id"], None)

    def control(self, run_id, action):
        with self._lock, self._control_lock(action):
            records = [row for row in self._records() if row["run_id"] == run_id]
            if not records:
                raise DashboardExecutionError("run_unknown", "没有该启动记录", 404)
            record = records[0]
            if action == "inspect":
                preview = self.preview({"bundle_id": record["bundle_id"]})
                self._owner_snapshots[run_id] = {'preview': preview, 'observed_at': _now()}
                return {"run": record, "preview": preview}
            path = self.state_root / (run_id + ".json")
            if record['launcher_state'] == 'retired':
                if action == 'retire':
                    return {'status': 'already_retired', 'run': record, 'process_started': False, 'API_requests': 0}
                raise DashboardExecutionError('run_retired', '该启动引用已退役；仅可查看原状态和历史', 409)
            if action == 'retire':
                if run_id in self._processes:
                    raise DashboardExecutionError('company_still_draining', '当前公司尚未安全退出；不能退役启动引用', 409)
                _, bundle = self._select({'bundle_id': record['bundle_id']})
                if record['bundle_fingerprint'] != self._fingerprint(bundle):
                    raise DashboardExecutionError('bundle_changed', '原执行包已变化，先核对原范围', 409)
                work = self._retirement_work(bundle)
                evidence = _process_recovery_evidence(record, False)
                if evidence not in _STOPPED_EVIDENCE:
                    raise DashboardExecutionError('original_process_unknown', '未能确认原启动已停止，不能退役引用', 409)
                if record['bundle_fingerprint'] != self._fingerprint(bundle):
                    raise DashboardExecutionError('bundle_changed', '核对期间原执行包发生变化，未退役启动引用', 409)
                proof = {'protocol': 'iqs.dashboard_stopped_reference/1.0.0', 'observed_at': _now(),
                    'process_evidence': evidence, 'bundle_fingerprint': record['bundle_fingerprint'], **work}
                proof['proof_sha256'] = _digest(proof)
                record.update(process_state='observed_stopped', launcher_state='retired', retirement=proof,
                    work_completion_authoritative=False,
                    completion_notice='仅确认旧启动已停止；原工作、答案、费用和权限未改变。新执行仍须原同scope准备。')
                _write(path, record)
                return {'status': 'retired', 'run': record, 'process_started': False, 'API_requests': 0,
                    'owner_database_writes': 0, 'paid_dispatch_started': False}
            if action == "pause":
                state = "draining" if record["process_state"] in {"running", "starting"} else "paused"
                record.update(launcher_state=state, pause_scope="company_boundary", pause_requested_at=_now())
                _write(path, record)
                return {"run": record, "state": state, "pause_scope": "company_boundary", "process_started": False,
                        "notice": "停止本次启动的后续公司派发；当前公司的在途调用继续安全完成"}
            if action == "resume":
                if record["launcher_state"] not in {"paused", "draining"}:
                    raise DashboardExecutionError("run_not_paused", "该启动没有处于暂停边界", 409)
                if run_id in self._processes:
                    raise DashboardExecutionError("company_still_draining", "当前公司尚未安全退出；不会并发重发", 409)
                key, bundle = self._select({"bundle_id": record["bundle_id"]})
                if record["bundle_fingerprint"] != self._fingerprint(bundle):
                    raise DashboardExecutionError("bundle_changed", "原执行包已变化，不能恢复旧启动", 409)
                preview = self.preview({"bundle_id": key})
                if not preview["can_start"]:
                    raise DashboardExecutionError("resume_blocked", "原任务状态尚不支持安全恢复", 409, preview)
                # The UI's earlier projection is never authority: re-probe
                # under the original control lock after fresh owner checks.
                evidence = _process_recovery_evidence(record, preview.get('readonly_recovery'))
                if evidence not in {'known_local_exit', 'original_checkpoints_only', 'absent', 'original_pid_reused'}:
                    raise DashboardExecutionError("original_process_unknown", "未能确认原进程已不存在；仅允许原检查点的只读恢复", 409)
                root, runtime, _, _ = self._deployment(bundle)
                attempt = record.get("launch_attempt", 1) + 1
                if evidence in {'absent', 'original_pid_reused'}:
                    record['recovered_process_observation'] = {'pid': record['pid'],
                        'state': evidence, 'observed_at': _now(), 'source': 'win32_readonly_probe'}
                record.update(launch_attempt=attempt, result_path=str(self.state_root / run_id / f"result-{attempt}.json"),
                              log_path=str(self.state_root / run_id / f"process-{attempt}.log"), process_state="starting",
                              launcher_state="running", resumed_at=_now())
                _write(path, record)
                try:
                    process = subprocess.Popen(self._command(bundle, root, record["result_path"]), cwd=runtime,
                        env=self._environment(root, paid=True), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                except OSError:
                    record.update(process_state="launch_failed", launcher_state="paused")
                    _write(path, record)
                    raise DashboardExecutionError("launch_failed", "无法恢复原执行器", 503) from None
                record.update(process_state="running", pid=process.pid)
                _write(path, record)
                self._processes[run_id] = process
                threading.Thread(target=self._finish, args=(process, path, record), daemon=True).start()
                return {"run": record, "state": "running", "process_started": True, "paid_dispatch_started": None,
                        "notice": "仅恢复同一原owner登记范围；原执行器复用已保存答案，未知HTTP不重发"}
            raise DashboardExecutionError("control_unsupported", "不支持该控制动作", 409, {"action": action, "supported": ["inspect", "pause", "resume", "retire"]})

    @contextmanager
    def _control_lock(self, action):
        if action == "inspect" or not self.state_root.is_dir():
            yield
            return
        try:
            with control_lock(self.state_root / 'start.lock'):
                yield
        except ControlBusyError:
            raise DashboardExecutionError('launch_in_progress', '另一控制操作正在核对原任务', 409) from None

    def _settings_path(self):
        path = Path(self.config.get("model_policy_path", ""))
        runtime = Path(self.config.get("runtime_dir", ""))
        root = Path(self.config.get("stockqa_root", ""))
        if not path.is_absolute() or not path.is_file() or path.resolve() != (runtime / "llm_apis.json").resolve() or not (root / "src/config/llm_config.py").is_file():
            raise DashboardExecutionError("model_policy_unconfigured", "尚未指定原StockQA运行配置；不会另存第二份策略", 409)
        return path, root, runtime

    def settings(self):
        try:
            path, root, runtime = self._settings_path()
        except DashboardExecutionError as error:
            return {"configured": False, "reason": error.code, "policy": None, "API_requests": 0}
        result = self._call([str(self.config.get("stockqa_python", sys.executable)), "-B", "-X", "utf8", "-c", _POLICY_HELPER,
                             str(root), str(path), "read"], root, runtime)
        if result.get('policy') is None:
            template = Path(self.config.get('iqs_root', Path(__file__).resolve().parents[1]))/'examples/model-policy.template.json'
            result['policy'] = _read(template)
            return {**result, 'configured': False, 'editable': True, 'needs_initial_policy': True,
                'reason': 'original_policy_missing', 'policy_owner': 'StockQAbyLLM',
                'credential_values_returned': False}
        return {"configured": True, **result, "policy_owner": "StockQAbyLLM", "credential_values_returned": False}

    def save_settings(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"policy", "revision_sha256"} or not re.fullmatch(r"[a-f0-9]{64}", str(payload.get("revision_sha256"))):
            raise DashboardExecutionError("settings_input_invalid", "请提交完整策略及读取时的版本指纹")
        # Reject credentials before they can enter a child process or its logs.
        encoded = json.dumps(payload, allow_nan=False)
        if len(encoded) > 256 * 1024 or re.search(r'"[^"\\]*(?:api.?key|secret|password|credential|authorization)[^"\\]*"\s*:', encoded, re.I):
            raise DashboardExecutionError("settings_secret_forbidden", "策略不得包含密钥值；密钥继续由环境变量提供")
        path, root, runtime = self._settings_path()
        with self._lock:
            return self._call([str(self.config.get("stockqa_python", sys.executable)), "-B", "-X", "utf8", "-c", _POLICY_HELPER,
                               str(root), str(path), "save"], root, runtime, input_value=payload)

    def acknowledge_delivery(self, bundle, receipt):
        """Pass exact StockWiki ACKs to registered original work; no new queue/state."""
        root = Path(self.config.get('stockqa_root', ''))
        ledger = Path(bundle.get('work_store', ''))
        mapping = bundle.get('work_item_ids')
        if (not root.is_absolute() or not (root/'src/utils/quick_scan_work_store.py').is_file()
            or not ledger.is_absolute() or not ledger.is_file() or not isinstance(mapping, dict) or not mapping):
            raise DashboardExecutionError('ack_owner_unconfigured', '缺少原StockQA账本及逐观察work引用', 409)
        acks = receipt.get('acks') if isinstance(receipt, dict) else None
        if (not isinstance(acks, list) or not acks or len(acks) != len(mapping)
            or {ack.get('observation_id') for ack in acks if isinstance(ack, dict)} != set(mapping)):
            raise DashboardExecutionError('ack_scope_mismatch', '回执与已登记观察范围不一致', 409)
        helper = r'''
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
from src.utils.quick_scan_work_store import QuickScanWorkStore
request=json.load(sys.stdin)
def offline(event,args):
    if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}: raise RuntimeError('network_forbidden')
sys.addaudithook(offline)
try:
    store=QuickScanWorkStore(pathlib.Path(sys.argv[2]))
    rows=[]
    for ack in request['receipt']['acks']:
        work=request['work_item_ids'][ack['observation_id']]
        result=store.apply_result_delivery_ack(work,ack)
        rows.append({'work_item_id':work,'observation_id':ack['observation_id'],'state':result['state']})
    print(json.dumps({'status':'delivered' if all(r['state']=='delivered' for r in rows) else 'owner_rejected',
        'items':rows,'API_requests':0,'network_calls':0}))
except Exception:
    print(json.dumps({'error_code':'original_ack_rejected','API_requests':0}));raise SystemExit(2)
'''
        return self._call([str(self.config.get('stockqa_python', sys.executable)), '-B', '-X', 'utf8', '-c', helper,
            str(root), str(ledger)], root, ledger.parent, input_value={'receipt': receipt, 'work_item_ids': mapping})

    def export_delivery(self, payload):
        try:
            from .dashboard_delivery import export_deliveries
        except ImportError:
            from dashboard_delivery import export_deliveries
        return export_deliveries(self, payload)

    def bind_delivery_consumer(self, bundle, target, source_ref):
        """Freeze the receiver from its independent public DTO BEFORE importing."""
        root = Path(self.config.get('stockqa_root', ''))
        ledger = Path(bundle.get('work_store', ''))
        mapping = bundle.get('work_item_ids')
        if (not root.is_absolute() or not (root/'src/utils/quick_scan_work_store.py').is_file()
            or not ledger.is_absolute() or not ledger.is_file() or not isinstance(mapping, dict) or not mapping):
            raise DashboardExecutionError('ack_owner_unconfigured', '缺少原StockQA账本及逐观察work引用', 409)
        helper = r'''
import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from src.utils.quick_scan_work_store import QuickScanWorkStore
request=json.load(sys.stdin)
def offline(event,args):
    if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}: raise RuntimeError('network_forbidden')
sys.addaudithook(offline)
try:
    store=QuickScanWorkStore(pathlib.Path(sys.argv[2]));rows=[]
    for observation,work in request['work_item_ids'].items():
        delivery=store.get_result_delivery(work)
        if delivery['observation_id']!=observation: raise ValueError('observation_scope_mismatch')
        binding=store.bind_result_delivery_consumer(work,request['target'],source_ref=request['source_ref'])
        rows.append({'work_item_id':work,'binding_sha256':binding['binding_sha256']})
    print(json.dumps({'status':'bound','items':rows,'API_requests':0,'network_calls':0}))
except Exception:
    print(json.dumps({'error_code':'original_consumer_binding_rejected','API_requests':0}));raise SystemExit(2)
'''
        return self._call([str(self.config.get('stockqa_python', sys.executable)), '-B', '-X', 'utf8', '-c', helper,
            str(root), str(ledger)], root, ledger.parent,
            input_value={'work_item_ids': mapping, 'target': target, 'source_ref': source_ref})
