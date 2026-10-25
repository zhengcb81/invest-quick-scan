"""Async delivery references over immutable original outbox packages, no LLM queue."""
from __future__ import annotations

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
    from .dashboard_locks import control_lock, ControlBusyError
except ImportError:
    from dashboard_locks import control_lock, ControlBusyError


class DeliveryJobError(ValueError):
    def __init__(self, code, message, status=409):
        super().__init__(message)
        self.code,self.status=code,status


def _now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def _digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')).hexdigest()


class DeliveryJobs:
    def __init__(self, execution, state_root, deployment_sha256, deliver_scope, resolve_batch):
        self.execution,self.state_root=execution,Path(state_root)
        self.deployment_sha256,self.deliver_scope,self.resolve_batch=deployment_sha256,deliver_scope,resolve_batch
        self.session=uuid.uuid4().hex; self._threads={}

    def _path(self,job_id):
        if not isinstance(job_id,str) or not re.fullmatch('deliveryjob_[a-f0-9]{32}',job_id):
            raise DeliveryJobError('delivery_job_invalid','交付任务ID无效。',400)
        return self.state_root/(job_id+'.json')

    def _read(self,path):
        for attempt in range(8):
            try:
                raw=path.read_bytes()
                if len(raw)>16*1024*1024: raise ValueError('large')
                value=json.loads(raw.decode('utf8'))
                if (value.get('protocol')!='iqs.delivery_job/1.0.0' or value.get('job_id')!=path.stem
                    or value.get('deployment_sha256')!=self.deployment_sha256
                    or not isinstance(value.get('entries'),list) or not value['entries']):
                    raise ValueError('invalid')
                return value
            except PermissionError:
                if attempt<7: time.sleep(.01);continue
                raise DeliveryJobError('delivery_reference_busy','交付记录暂不可读；不会按空任务重做。') from None
            except FileNotFoundError:
                raise DeliveryJobError('delivery_job_unknown','没有该交付任务。',404) from None
            except (OSError,ValueError,TypeError,AttributeError):
                raise DeliveryJobError('delivery_reference_invalid','交付引用损坏或目标已变，先核原状态。') from None

    def _write(self,path,value):
        raw=json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)
        if len(raw.encode('utf8'))>16*1024*1024:
            raise DeliveryJobError('delivery_reference_too_large','交付引用超过上限；原ACK保留，不能写入不可恢复记录。')
        temporary=path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
        try:
            with temporary.open('x',encoding='utf8',newline='\n') as stream:
                stream.write(raw)
                stream.flush();os.fsync(stream.fileno())
            for attempt in range(8):
                try: os.replace(temporary,path);break
                except PermissionError:
                    if attempt==7: raise
                    time.sleep(.01)
        finally: temporary.unlink(missing_ok=True)

    def submit(self,payload):
        if not isinstance(payload,dict) or set(payload) not in ({'bundle_id'},{'batch_id'}):
            raise DeliveryJobError('delivery_selection_invalid','只能选择原执行包或公司批。',400)
        if 'batch_id' in payload:
            batch=self.resolve_batch(payload['batch_id'])
            original=batch['entries']
            candidates=[row for row in original if row['state']=='owner_ready']
            if not candidates: raise DeliveryJobError('delivery_batch_not_ready','该批次尚无原ready范围可交付。')
        else:
            original=candidates=[{'bundle_id':payload['bundle_id']}]
        entries=[]
        for row in candidates:
            registration=self.execution.bundle_registration(row['bundle_id'])
            if row.get('bundle_fingerprint',registration['bundle_fingerprint'])!=registration['bundle_fingerprint']:
                raise DeliveryJobError('delivery_bundle_changed','原批次输入已变，不能交付到另一范围。')
            entries.append({**registration,'state':'selected'})
        selection={'target':self.deployment_sha256,'selection':payload,
            'entries':[(row['bundle_id'],row['bundle_fingerprint']) for row in entries]}
        job_id='deliveryjob_'+_digest(selection)[:32];path=self._path(job_id)
        self.state_root.mkdir(parents=True,exist_ok=True)
        try:
            with control_lock(self.state_root/'delivery-control.lock'):
                if path.exists(): return {'attached':True,'job':self.get(job_id),'API_requests':0}
                record={'protocol':'iqs.delivery_job/1.0.0','job_id':job_id,'deployment_sha256':self.deployment_sha256,
                    'selection':payload,'entries':entries,'state':'running','session':self.session,
                    'created_at':_now(),'partial_batch_selection':len(candidates)!=len(original),
                    'model_calls':0,'financial_accuracy_proven':False}
                self._write(path,record)
                self._launch(job_id)
                return {'attached':False,'job':record,'status':'accepted','API_requests':0}
        except ControlBusyError:
            raise DeliveryJobError('delivery_control_busy','另一交付操作正在登记，请刷新。') from None

    def _launch(self,job_id):
        current=self._threads.get(job_id)
        if current is not None and current.is_alive(): return
        thread=threading.Thread(target=self._run,args=(job_id,),daemon=True)
        self._threads[job_id]=thread;thread.start()

    def _run(self,job_id):
        path=self._path(job_id)
        try:
            with control_lock(path.with_suffix('.lock')):
                record=self._read(path)
                record.update(state='running',session=self.session)
                self._write(path,record)
                for entry in record['entries']:
                    if entry['state']=='delivered': continue
                    try:
                        current=self.execution.bundle_registration(entry['bundle_id'])
                        if current['bundle_fingerprint']!=entry['bundle_fingerprint']:
                            raise DeliveryJobError('delivery_bundle_changed','交付输入发生变化。')
                        entry.update(state='importing')
                        self._write(path,record)
                        outcome=self.deliver_scope(entry['bundle_id'])
                        items=outcome.get('items',[])
                        summary={'status':outcome['status'],'package_count':len(items),
                            'delivered_packages':sum(row.get('ack_reconciliation',{}).get('status')=='delivered' for row in items),
                            'error_codes':sorted({str(row['error_code'])[:100] for row in items if row.get('error_code')})[:20],
                            'details_owner':'Original StockWiki ACK and StockQA outbox; not copied to this job'}
                        entry.update(state='delivered' if outcome['status']=='delivered' else 'pending',
                            outcome=summary,observed_at=_now())
                    except Exception as exc:
                        entry.update(state='pending',error_code=getattr(exc,'code','delivery_interrupted'),observed_at=_now())
                    self._write(path,record)
                record.update(state='completed' if all(row['state']=='delivered' for row in record['entries']) else 'partial',finished_at=_now())
                self._write(path,record)
        except (ControlBusyError,OSError,DeliveryJobError):
            pass  # Durable running/importing becomes an explicit resume reference.
        finally: self._threads.pop(job_id,None)

    def get(self,job_id):
        record=self._read(self._path(job_id));thread=self._threads.get(job_id)
        if record['state']=='running' and (record['session']!=self.session or thread is None or not thread.is_alive()):
            record['state']='needs_original_inspection'
        record['allowed_actions']=['resume','abandon'] if record['state'] in {'partial','needs_original_inspection'} else []
        record['counts']={'scopes':len(record['entries']),'delivered_scopes':sum(row['state']=='delivered' for row in record['entries'])}
        record['notice']='交付只复用原封存字节与ACK；completed表示所选范围已对账，不等于全池或金融审查通过。'
        return record

    def list(self):
        paths=sorted(self.state_root.glob('deliveryjob_*.json'),key=lambda p:p.stat().st_mtime,reverse=True) if self.state_root.exists() else []
        return {'jobs':[self.get(path.stem) for path in paths[:50]],'total':len(paths),'API_requests':0}

    def active(self):
        return any(self.get(path.stem)['state'] in {'running','partial','needs_original_inspection'} for path in self.state_root.glob('deliveryjob_*.json')) if self.state_root.exists() else False

    def control(self,job_id,action):
        if action not in {'resume','abandon'}: raise DeliveryJobError('delivery_action_invalid','不支持该交付操作。',400)
        path=self._path(job_id)
        try:
            with control_lock(path.with_suffix('.lock')):
                record=self._read(path)
                if record['state'] in {'completed','abandoned'}: return self.get(job_id)
                if action=='abandon':
                    record.update(state='abandoned',abandoned_at=_now())
                else:
                    for row in record['entries']:
                        current=self.execution.bundle_registration(row['bundle_id'])
                        if current['bundle_fingerprint']!=row['bundle_fingerprint']:
                            raise DeliveryJobError('delivery_bundle_changed','原交付范围已变，不能恢复。')
                    record.update(state='running',session=self.session)
                self._write(path,record)
            if action=='resume': self._launch(job_id)
            return self.get(job_id)
        except ControlBusyError:
            raise DeliveryJobError('delivery_still_running','原交付仍在进行，请等其安全完成，不重复派发。') from None
