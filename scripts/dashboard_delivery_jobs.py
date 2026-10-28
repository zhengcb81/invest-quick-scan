"""Async delivery references over immutable original outbox packages, no LLM queue."""
from __future__ import annotations

from datetime import datetime, timezone
import copy
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


LEGACY_DEPLOYMENT_PROFILE='iqs.delivery-deployment/1.0.0'
STABLE_DEPLOYMENT_PROFILE='iqs.delivery-deployment/1.1.0'


def delivery_deployment_fingerprint(config):
    """Preparation retry selection is not a delivery destination or permission."""
    frozen=copy.deepcopy({k:v for k,v in config.items() if k not in {'execution_bundles','import_bundles'}})
    if isinstance(frozen.get('prepare'),dict):
        frozen['prepare'].pop('recovery_work_decision_refs',None)
    return hashlib.sha256(json.dumps(frozen,sort_keys=True,ensure_ascii=False).encode('utf8')).hexdigest()


class DeliveryJobs:
    def __init__(self, execution, state_root, deployment_sha256, deliver_scope, resolve_batch,
                 *, fingerprint_profile=LEGACY_DEPLOYMENT_PROFILE):
        self.execution,self.state_root=execution,Path(state_root)
        self.deployment_sha256,self.deliver_scope,self.resolve_batch=deployment_sha256,deliver_scope,resolve_batch
        if fingerprint_profile not in {LEGACY_DEPLOYMENT_PROFILE,STABLE_DEPLOYMENT_PROFILE}:
            raise ValueError('delivery_deployment_profile_invalid')
        self.fingerprint_profile=fingerprint_profile
        self.session=uuid.uuid4().hex; self._threads={}

    def _path(self,job_id):
        if not isinstance(job_id,str) or not re.fullmatch('deliveryjob_[a-f0-9]{32}',job_id):
            raise DeliveryJobError('delivery_job_invalid','交付任务ID无效。',400)
        return self.state_root/(job_id+'.json')

    def _read(self,path,*,allow_completed_history=False):
        for attempt in range(8):
            try:
                raw=path.read_bytes()
                if len(raw)>16*1024*1024: raise ValueError('large')
                value=json.loads(raw.decode('utf8'))
                if (value.get('protocol')!='iqs.delivery_job/1.0.0' or value.get('job_id')!=path.stem
                    or value.get('state') not in {'running','partial','completed','abandoned'}
                    or not isinstance(value.get('entries'),list) or not value['entries']
                    or any(not isinstance(row,dict) or row.get('state') not in {'selected','importing','pending','delivered'}
                        or re.fullmatch('[A-Za-z0-9_.-]{1,100}',str(row.get('bundle_id',''))) is None
                        or re.fullmatch('[a-f0-9]{64}',str(row.get('bundle_fingerprint',''))) is None
                        for row in value['entries'])):
                    raise ValueError('invalid')
                profile=value.get('deployment_fingerprint_profile',LEGACY_DEPLOYMENT_PROFILE)
                if profile not in {LEGACY_DEPLOYMENT_PROFILE,STABLE_DEPLOYMENT_PROFILE}:
                    raise ValueError('unknown_profile')
                if value['state']=='completed' and not self._completed_history(value):
                    raise ValueError('invalid_completed_summary')
                same_target=(value.get('deployment_sha256')==self.deployment_sha256
                    and profile==self.fingerprint_profile)
                verified=True
                if value['state']=='completed':
                    for entry in value['entries']:
                        try:
                            current=self.execution.bundle_registration(entry['bundle_id'])
                            verified=verified and current['bundle_fingerprint']==entry['bundle_fingerprint']
                        except Exception:
                            verified=False
                if not same_target or not verified:
                    if not allow_completed_history or not self._completed_history(value):
                        raise ValueError('changed_target_or_bundle')
                    value.update(persisted_state=value['state'],state='historical_read_only',
                        read_only_history=True,current_target_verified=False,allowed_actions=[])
                    value['history_bundle_references_verified']=verified
                return value
            except PermissionError:
                if attempt<7: time.sleep(.01);continue
                raise DeliveryJobError('delivery_reference_busy','交付记录暂不可读；不会按空任务重做。') from None
            except FileNotFoundError:
                raise DeliveryJobError('delivery_job_unknown','没有该交付任务。',404) from None
            except (OSError,ValueError,TypeError,AttributeError):
                raise DeliveryJobError('delivery_reference_invalid','交付引用损坏或目标已变，先核原状态。') from None

    @staticmethod
    def _completed_history(value):
        """Stored summaries are history, never a fresh original-owner ACK proof."""
        if value.get('state')!='completed' or re.fullmatch('[a-f0-9]{64}',str(value.get('deployment_sha256',''))) is None:
            return False
        for row in value['entries']:
            if (not isinstance(row,dict) or row.get('state')!='delivered'
                or re.fullmatch('[A-Za-z0-9_.-]{1,100}',str(row.get('bundle_id',''))) is None
                or re.fullmatch('[a-f0-9]{64}',str(row.get('bundle_fingerprint',''))) is None):
                return False
            summary=row.get('outcome')
            if (not isinstance(summary,dict) or summary.get('status')!='delivered'
                or type(summary.get('package_count')) is not int
                or type(summary.get('delivered_packages')) is not int
                or summary['package_count']<0 or summary['delivered_packages']!=summary['package_count']):
                return False
        return True

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
        if self.fingerprint_profile!=LEGACY_DEPLOYMENT_PROFILE:
            selection['deployment_fingerprint_profile']=self.fingerprint_profile
        job_id='deliveryjob_'+_digest(selection)[:32];path=self._path(job_id)
        self.state_root.mkdir(parents=True,exist_ok=True)
        try:
            with control_lock(self.state_root/'delivery-control.lock'):
                if path.exists(): return {'attached':True,'job':self.get(job_id),'API_requests':0}
                record={'protocol':'iqs.delivery_job/1.0.0','job_id':job_id,'deployment_sha256':self.deployment_sha256,
                    'deployment_fingerprint_profile':self.fingerprint_profile,
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
        record=self._read(self._path(job_id),allow_completed_history=True);thread=self._threads.get(job_id)
        if record['state']=='running' and (record['session']!=self.session or thread is None or not thread.is_alive()):
            record['state']='needs_original_inspection'
        record['allowed_actions']=['resume','abandon'] if record['state'] in {'partial','needs_original_inspection'} else []
        record['counts']={'scopes':len(record['entries']),'delivered_scopes':sum(row['state']=='delivered' for row in record['entries'])}
        record['notice']='交付只复用原封存字节与ACK；completed表示所选范围已对账，不等于全池或金融审查通过。'
        if record.get('read_only_history'):
            record['notice']='配置已变，此处仅保留历史签收摘要；当前部署未重验原ACK，不能据此恢复、导入或认定当前范围完成。'
        return record

    def list(self):
        paths=list(self.state_root.glob('deliveryjob_*.json')) if self.state_root.exists() else []
        metadata_errors=set()
        timestamps={}
        for path in paths:
            try:
                timestamps[path]=path.stat().st_mtime
            except OSError:
                metadata_errors.add(path)
                timestamps[path]=float('inf')
        paths.sort(key=lambda p:(timestamps[p],p.name),reverse=True)
        jobs=[]
        for path in paths[:50]:
            try:
                if path in metadata_errors:
                    raise DeliveryJobError('delivery_reference_unreadable','交付引用元数据暂不可读。')
                jobs.append(self.get(path.stem))
            except DeliveryJobError as error:
                jobs.append({'job_id':path.stem,'state':'needs_original_inspection',
                    'reference_error':error.code,'allowed_actions':[],
                    'current_target_verified':False,'notice':'该引用不可读取或目标已变；不隐藏其他记录，不自动重做。'})
        return {'jobs':jobs,'total':len(paths),'API_requests':0}

    def active(self):
        if not self.state_root.exists():return False
        for path in self.state_root.glob('deliveryjob_*.json'):
            try:
                if self.get(path.stem)['state'] in {'running','partial','needs_original_inspection'}:return True
            except DeliveryJobError:
                return True
        return False

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
