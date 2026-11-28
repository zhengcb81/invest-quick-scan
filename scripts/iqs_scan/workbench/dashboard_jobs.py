"""Async original-owner bank preparation references, never a model-work queue."""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import nullcontext
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid

from ..foundation.api import (
    operation_scope, read_owned_operation_failure, record_operation_checkpoint, record_operation_failure,
    replace_after_readers_close,
)
from .dashboard_locks import control_lock, ControlBusyError


DEFAULT_RECORD_LOCK_TIMEOUT_SECONDS = 1.0


class DashboardJobError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details or {}


def _now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class PreparationJobs:
    def __init__(
        self, preparer, state_root, on_prepared, *, diagnostic_root=None,
        record_lock_timeout_seconds=DEFAULT_RECORD_LOCK_TIMEOUT_SECONDS,
    ):
        self.preparer, self.state_root, self.on_prepared = preparer, Path(state_root), on_prepared
        self.diagnostic_root = Path(diagnostic_root or state_root)
        self.record_lock_timeout_seconds = record_lock_timeout_seconds
        self.session = uuid.uuid4().hex
        self._threads = {}
        self._mutex = threading.RLock()

    @staticmethod
    def has_records(state_root):
        return next(Path(state_root).glob('prepjob_*.json'), None) is not None

    def _path(self, job_id):
        if not isinstance(job_id, str) or not re.fullmatch('prepjob_[a-f0-9]{32}', job_id):
            raise DashboardJobError('job_id_invalid', '准备任务ID无效。')
        return self.state_root/(job_id+'.json')

    def _read(self, path):
        try:
            for attempt in range(8):
                try:
                    raw = path.read_bytes()
                    break
                except PermissionError:
                    if attempt == 7: raise
                    time.sleep(min(.005 * 2 ** attempt, .04))
            if len(raw) > 16*1024*1024:
                raise ValueError('large job')
            record = json.loads(raw.decode('utf8'))
            if record.get('protocol') != 'iqs.preparation_job/1.0.0' or record.get('job_id') != path.stem:
                raise ValueError('invalid reference')
            return record
        except FileNotFoundError:
            raise DashboardJobError('preparation_job_unknown', '没有该准备任务。', 404) from None
        except (OSError, ValueError, TypeError, AttributeError):
            raise DashboardJobError('preparation_job_corrupt', '准备引用损坏；不能按空记录重新提交。', 409) from None

    def _write(self, path, record):
        temporary = path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
        try:
            with temporary.open('x', encoding='utf8', newline='\n') as stream:
                json.dump(record, stream, ensure_ascii=False, allow_nan=False, indent=2)
                stream.flush(); os.fsync(stream.fileno())
            replace_after_readers_close(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def submit(self, payload):
        if (not isinstance(payload, dict) or set(payload) != {'preview_id', 'preview_token'}
            or not re.fullmatch('prepare_[a-f0-9]{32}', str(payload.get('preview_id')))
            or not re.fullmatch('[a-f0-9]{64}', str(payload.get('preview_token')))):
            raise DashboardJobError('preparation_selection_invalid', '请选择完整原预览和确认指纹。')
        job_id = 'prepjob_'+payload['preview_id'].removeprefix('prepare_')
        path = self._path(job_id)
        new_job = not path.exists()
        if new_job:
            self.preparer.validate_selection(payload)
        try:
            with self._mutex:
                with control_lock(self.state_root/'jobs.lock'):
                    if path.exists():
                        record = self._read(path)
                        if record['preview_token'] != payload['preview_token']:
                            raise DashboardJobError('preview_mismatch', '同一预览的确认指纹不一致。', 409)
                        return {'attached': True, 'job': self.get(job_id), 'API_requests': 0}
                    # Attaching an existing exact job is a read, not a new apply.
                    # Only a new job needs today's preparation prerequisites.
                    if not new_job:
                        self.preparer.validate_selection(payload)
                    record = {'protocol':'iqs.preparation_job/1.0.0', 'job_id': job_id,
                        **payload, 'state':'preparing', 'created_at':_now(), 'session':self.session,
                        'model_dispatch_started': False}
                    self._write(path, record)
                thread = threading.Thread(target=self._run, args=(path, record, dict(payload)), daemon=True)
                self._threads[job_id] = thread
                thread.start()
                return {'attached': False, 'job': dict(record), 'API_requests': 0}
        except ControlBusyError:
            raise DashboardJobError('preparation_control_busy', '另一准备操作正在记录，请刷新状态。', 409) from None

    def _register(self, record, result, *, lock_held=False):
        # Background work can wait briefly without holding the service mutex.
        # Foreground mutations still fail fast while the registration callback owns the lock.
        claim = nullcontext() if lock_held else control_lock(
            self.state_root / "jobs.lock", timeout_seconds=self.record_lock_timeout_seconds,
        )
        with claim:
            current = self._read(self._path(record['job_id']))
            if current['state'] == 'registered':
                return 'registered'
            if not lock_held and (current['session'] != record['session'] or current['state'] == 'registration_pending'):
                return current['state']
            if current['state'] == 'abandoned':
                current.update(result=result, prepared_at=_now(), registration_performed=False)
                self._write(self._path(record['job_id']), current)
                return 'abandoned'
            record = {**current, 'state':'registration_in_progress', 'result':result,
                      'prepared_at':_now(), 'session':self.session}
            self._write(self._path(record['job_id']), record)
            try:
                record['registration'] = self.on_prepared(result)
                record['state'] = 'registered'
            except Exception as exc:
                code = getattr(exc, 'code', 'registration_failed')
                record.update(state='registration_pending', registration_error=code,
                              failure_diagnostic=self._diagnose(exc, record, "prepare.register", code))
            self._write(self._path(record['job_id']), record)
            return record['state']

    def _diagnose(self, error, record, stage, code):
        with operation_scope(record["job_id"], record["session"], recoverable=True):
            return record_operation_failure(error, stage, directory=self.diagnostic_root, code=code)

    def _run(self, path, record, payload):
        with operation_scope(record["job_id"], record["session"], recoverable=True):
            self._run_original(path, record, payload)

    def _run_original(self, path, record, payload):
        started = time.monotonic_ns()
        outcome = "failed"
        evidence = "iqs:preparation/" + record["job_id"]
        record_operation_checkpoint("prepare.job", "started", directory=self.diagnostic_root, evidence_ref=evidence)
        try:
            result = self.preparer.apply(payload)
            record_operation_checkpoint("prepare.apply", "completed", directory=self.diagnostic_root)
            registered = self._register(record, result)
            outcome = {"registered": "completed", "abandoned": "refused"}.get(registered, "failed")
        except Exception as exc:
            code = getattr(exc, "code", "preparation_interrupted")
            diagnostic = self._diagnose(exc, record, "prepare.apply", code)
            try:
                with control_lock(self.state_root / "jobs.lock", timeout_seconds=self.record_lock_timeout_seconds):
                    current = self._read(path)
                    if current['session'] == record['session'] and current['state'] in {
                        'preparing', 'registration_in_progress',
                    }:
                        current.update(
                            state='needs_original_inspection', finished_at=_now(),
                            error_code=code, failure_diagnostic=diagnostic,
                            message='未自动重试；先核对原准备记录，再明确处理。',
                        )
                        self._write(path, current)
            except ControlBusyError:
                # The original diagnostic is durable and get() reads it by job and session.
                # Keep the locked record untouched. A concurrent recovery may own it.
                pass
        finally:
            record_operation_checkpoint("prepare.job", outcome, directory=self.diagnostic_root,
                                        elapsed_ms=(time.monotonic_ns() - started) // 1_000_000)
            with self._mutex:
                self._threads.pop(record['job_id'], None)

    def get(self, job_id):
        with self._mutex:
            record = self._read(self._path(job_id))
            thread = self._threads.get(job_id)
            detached = record['session'] != self.session or thread is None or not thread.is_alive()
        if record['state'] in {'preparing', 'registration_in_progress'} and detached:
            stages = ("prepare.register", "prepare.apply") if record['state'] == 'registration_in_progress' else (
                "prepare.apply", "prepare.worker", "prepare.owner",
            )
            diagnostic = read_owned_operation_failure(self.diagnostic_root, job_id, record['session'], *stages)
            record.update(state='needs_original_inspection', message='准备作业已停止或由另一进程持有，请先核对原记录。',
                          error_code=diagnostic["observation"]["actual"] if diagnostic else "worker_state_unknown")
            if diagnostic:
                record['failure_diagnostic'] = diagnostic
        record['allowed_actions'] = (['reconcile', 'abandon'] if record['state'] in {
            'needs_original_inspection', 'owner_prepared', 'registration_pending'} else [])
        if record['state'] in {'preparing','needs_original_inspection'} and hasattr(self.preparer,'preparation'):
            try:
                record['original_preparation']=self.preparer.preparation(record['preview_id'])
            except Exception as exc:
                record['phase_read_error'] = getattr(exc, 'code', 'preparation_phase_unavailable')
        return record

    def list(self):
        if not self.state_root.exists():
            return {'jobs': [], 'API_requests': 0}
        paths = sorted(self.state_root.glob('prepjob_*.json'), key=lambda path: path.stat().st_mtime, reverse=True)
        return {'jobs':[self.get(path.stem) for path in paths[:50]], 'total':len(paths), 'API_requests':0}

    def active(self):
        return any(self._read(path)['state'] in {'preparing','registration_in_progress','needs_original_inspection','owner_prepared','registration_pending'}
            for path in self.state_root.glob('prepjob_*.json')) if self.state_root.exists() else False

    def _terminal_preparation(self, path):
        record = self._read(path)
        if record['state'] in {'abandoned', 'registered'}:
            return {**record, 'allowed_actions': []}
        return None

    def reconcile(self, job_id):
        path = self._path(job_id)
        # A committed terminal record is already the answer. A worker may
        # still be unwinding its lock or writing diagnostics after publishing.
        if (terminal := self._terminal_preparation(path)) is not None:
            return terminal
        try:
            with self._mutex, control_lock(self.state_root/'jobs.lock'):
                if job_id in self._threads:
                    if (terminal := self._terminal_preparation(path)) is not None:
                        return terminal
                    raise DashboardJobError('preparation_still_running', '当前准备仍在进行，不重复提交。', 409)
                record = self.get(job_id)
                if record['state'] == 'registration_in_progress':
                    raise DashboardJobError('preparation_registering', '正在登记原准备结果，请等待后刷新。', 409)
                if record['state'] in {'abandoned', 'registered'}:
                    return record
                if record.get('result') is not None:
                    self._register(record, record['result'], lock_held=True)
                    return self.get(job_id)
                native = self.preparer.preparation(record['preview_id'])
                if native.get('status') != 'prepared' or not isinstance(native.get('result'), dict):
                    return {**record, 'original_preparation':native, 'automatic_retry':False}
                self._register(record, native['result'], lock_held=True)
                return self.get(job_id)
        except ControlBusyError:
            if (terminal := self._terminal_preparation(path)) is not None:
                return terminal
            raise DashboardJobError('preparation_control_busy', '另一准备操作正在记录，请刷新状态。', 409) from None

    def abandon(self, job_id):
        try:
            with self._mutex, control_lock(self.state_root/'jobs.lock'):
                if job_id in self._threads:
                    raise DashboardJobError('preparation_still_running', '当前准备仍在进行；等待安全结束后再处理。', 409)
                record = self.get(job_id)
                if record['state'] == 'registration_in_progress':
                    raise DashboardJobError('preparation_registering', '原准备结果正在登记，不能同时放弃或切换目标。', 409)
                if record['state'] == 'registered':
                    raise DashboardJobError('already_registered', '原准备已登记；请在执行包中处理，不删除原记录。', 409)
                record.update(state='abandoned', abandoned_at=_now(), allowed_actions=[],
                    notice='仅停止等待或自动登记，保留原owner已写记录，不回滚、不取消原任务。')
                self._write(self._path(job_id), record)
                return record
        except ControlBusyError:
            raise DashboardJobError('preparation_control_busy', '另一准备操作正在记录，请刷新状态。', 409) from None
