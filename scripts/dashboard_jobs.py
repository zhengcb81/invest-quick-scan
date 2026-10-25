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

try:
    from .dashboard_locks import control_lock, ControlBusyError
except ImportError:
    from dashboard_locks import control_lock, ControlBusyError


class DashboardJobError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details or {}


def _now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class PreparationJobs:
    def __init__(self, preparer, state_root, on_prepared):
        self.preparer, self.state_root, self.on_prepared = preparer, Path(state_root), on_prepared
        self.session = uuid.uuid4().hex
        self._threads = {}
        self._mutex = threading.RLock()

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
            for attempt in range(8):
                try:
                    os.replace(temporary, path)
                    break
                except PermissionError:
                    if attempt == 7: raise
                    time.sleep(min(.005 * 2 ** attempt, .04))
        finally:
            temporary.unlink(missing_ok=True)

    def submit(self, payload):
        if (not isinstance(payload, dict) or set(payload) != {'preview_id', 'preview_token'}
            or not re.fullmatch('prepare_[a-f0-9]{32}', str(payload.get('preview_id')))
            or not re.fullmatch('[a-f0-9]{64}', str(payload.get('preview_token')))):
            raise DashboardJobError('preparation_selection_invalid', '请选择完整原预览和确认指纹。')
        job_id = 'prepjob_'+payload['preview_id'].removeprefix('prepare_')
        path = self._path(job_id)
        self.preparer.validate_selection(payload)
        try:
            with self._mutex, control_lock(self.state_root/'jobs.lock'):
                if path.exists():
                    record = self._read(path)
                    if record['preview_token'] != payload['preview_token']:
                        raise DashboardJobError('preview_mismatch', '同一预览的确认指纹不一致。', 409)
                    return {'attached': True, 'job': self.get(job_id), 'API_requests': 0}
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
        # Mutations take this kernel lock NONBLOCKING. Keeping the claim
        # through the callback cannot deadlock a service request: another
        # request gets control_busy and releases its service lock immediately.
        # A process death releases the lock for explicit saved-result recovery.
        with (nullcontext() if lock_held else control_lock(self.state_root/'jobs.lock')):
            current = self._read(self._path(record['job_id']))
            if current.get('state') == 'abandoned':
                current.update(result=result, prepared_at=_now(), registration_performed=False)
                self._write(self._path(record['job_id']), current)
                return
            record = {**current, 'state':'registration_in_progress', 'result':result,
                      'prepared_at':_now(), 'session':self.session}
            self._write(self._path(record['job_id']), record)
            try:
                record['registration'] = self.on_prepared(result)
                record['state'] = 'registered'
            except Exception as exc:
                record.update(state='registration_pending', registration_error=getattr(exc, 'code', 'registration_failed'))
            self._write(self._path(record['job_id']), record)

    def _run(self, path, record, payload):
        try:
            result = self.preparer.apply(payload)
            self._register(record, result)
        except Exception as exc:
            for attempt in range(8):
                try:
                    with control_lock(self.state_root/'jobs.lock'):
                        current = self._read(path)
                        if current.get('state') == 'abandoned': return
                        current.update(state='needs_original_inspection', finished_at=_now(),
                            error_code=getattr(exc, 'code', 'preparation_interrupted'),
                            message='未自动重试；先核对原准备记录，再明确处理。')
                        self._write(path,current)
                    break
                except ControlBusyError:
                    if attempt==7: break  # Keep durable state, never redo apply.
                    time.sleep(.01)
        finally:
            with self._mutex:
                self._threads.pop(record['job_id'], None)

    def get(self, job_id):
        record = self._read(self._path(job_id))
        thread=self._threads.get(job_id)
        if record['state'] in {'preparing','registration_in_progress'} and (
                record['session'] != self.session or thread is None or not thread.is_alive()):
            record.update(state='needs_original_inspection', message='服务已重启，未自动重做准备。')
        record['allowed_actions'] = (['reconcile', 'abandon'] if record['state'] in {
            'needs_original_inspection', 'owner_prepared', 'registration_pending'} else [])
        if record['state'] in {'preparing','needs_original_inspection'} and hasattr(self.preparer,'preparation'):
            try:
                record['original_preparation']=self.preparer.preparation(record['preview_id'])
            except Exception as exc:
                record['phase_read_error']=getattr(exc,'code','preparation_phase_unavailable')
        return record

    def list(self):
        if not self.state_root.exists():
            return {'jobs': [], 'API_requests': 0}
        paths = sorted(self.state_root.glob('prepjob_*.json'), key=lambda path: path.stat().st_mtime, reverse=True)
        return {'jobs':[self.get(path.stem) for path in paths[:50]], 'total':len(paths), 'API_requests':0}

    def active(self):
        return any(self.get(path.stem)['state'] in {'preparing','registration_in_progress','needs_original_inspection','owner_prepared','registration_pending'}
            for path in self.state_root.glob('prepjob_*.json')) if self.state_root.exists() else False

    def reconcile(self, job_id):
        try:
            with self._mutex, control_lock(self.state_root/'jobs.lock'):
                if job_id in self._threads:
                    raise DashboardJobError('preparation_still_running', '当前准备仍在进行，不重复提交。', 409)
                record = self.get(job_id)
                if record['state'] == 'registration_in_progress':
                    raise DashboardJobError('preparation_registering', '正在登记原准备结果，请等待后刷新。', 409)
                if record['state'] == 'abandoned':
                    return record
                if record['state'] == 'registered':
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
