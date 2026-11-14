"""Local product control plane over the existing two owners.

No model client, question queue, scoring formula, or private database access.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from dashboard_locks import control_lock, ControlBusyError
from dashboard_owner import valid_timeout_seconds, TIMEOUT_SECONDS_MAX
from dashboard_membership_request import (
    apply_keyed_membership,
    membership_history as read_membership_history,
    membership_request_read as read_membership_request,
)
from dashboard_job_facade import (LIMITS_REF_REGISTRY, MAPPING_VERSION, WIRE_PROTOCOL,
                                  OWNER_JOB_ID_PATTERN as JOB_ID_PATTERN)

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = {'api_key', 'apikey', 'api_secret', 'secret', 'password', 'authorization',
               'access_token', 'refresh_token', 'probe_token'}
PATH_KEYS = {'stockwiki_root', 'stockwiki_python', 'stockqa_root', 'stockqa_python',
             'workspace_root', 'runtime_dir', 'state_root', 'model_policy_path', 'iqs_release_root'}
BUNDLE_PATHS = {'questions', 'manifest', 'identity_snapshot', 'c06_authority', 'owner_config',
                'admission_config', 'spend_authorization', 'inspection_request', 'search_policy',
                'runtime_dir', 'package', 'release', 'work_store', 'shared_company_config'}
BUNDLE_KEYS = BUNDLE_PATHS | {'entity_id', 'company', 'provider', 'confirmation_id',
    'inspection_schema_version', 'pack_size', 'thinking', 'max_output_tokens', 'work_lease_seconds', 'security_scope_id',
    'package_sha256', 'release_sha256', 'work_item_ids', 'company_preparation_id', 'scope', 'scope_id', 'security_id', 'expected_scope_bindings', 'recovery_subset', 'execution_question_ids', 'execution_question_count'}
CONFIG_KEYS = PATH_KEYS | {'schema_version', 'universe_id', 'execution_bundles', 'import_bundles',
                          'timeout_seconds', 'workspace_kind', 'workspace_label', 'prepare', 'batch',
                          'dashboard_origin'}
# Optional loopback origin used only to build safe links back to this UI.
DASHBOARD_ORIGIN_KEY = 'dashboard_origin'
PREPARE_KEYS = {'state_root', 'admission_config', 'module_package_id', 'producer',
    'authorization_reference', 'agent', 'runtime_dir', 'spend_authorization', 'search_policy',
    'pack_size', 'thinking', 'max_output_tokens', 'work_lease_seconds', 'routing_profiles', 'worker_timeout_seconds', 'native_timeout_seconds', 'delegation_ttl_seconds', 'recovery_work_decision_refs', 'shared_company_config'}
PREPARE_PATHS = {'state_root', 'admission_config', 'runtime_dir', 'spend_authorization', 'search_policy', 'shared_company_config'}


class ProductError(Exception):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details or {}


def _pin_company_result_route(iqs_link, snapshot):
    """Attach one validated owner snapshot's exact identity and scope to results."""
    routes = iqs_link.get('routes') if isinstance(iqs_link, dict) else None
    route = routes.get('results') if isinstance(routes, dict) else None
    result_id = snapshot.get('result_id') if isinstance(snapshot, dict) else None
    if not isinstance(route, str) or not isinstance(result_id, str) or not result_id:
        return iqs_link
    parts = urlsplit(route)
    route_path, _, route_query = parts.fragment.partition('?')
    params = parse_qs(route_query, keep_blank_values=True)
    params['result_id'] = [result_id]
    listing_id = snapshot.get('listing_id')
    if isinstance(listing_id, str) and listing_id:
        params['listing'] = [listing_id]
    subject_id = snapshot.get('analysis_subject_id')
    if isinstance(subject_id, str) and subject_id:
        params['subject'] = [subject_id]
        supported = iqs_link.get('supported_context')
        if isinstance(supported, list) and 'subject' not in supported:
            # The result page enforces exact subject scope from this pinned
            # owner snapshot even if legacy observation history has no subject.
            supported.append('subject')
    fragment = route_path + '?' + urlencode(params, doseq=True)
    routes['results'] = parts._replace(fragment=fragment).geturl()
    return iqs_link


def redact(value):
    if isinstance(value, dict):
        return {str(key): ('[redacted]' if str(key).lower() in SECRET_KEYS else redact(item))
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


def _reject_credentials(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                raise ProductError('inline_credentials_forbidden', '密钥只放环境变量，不通过界面保存。')
            _reject_credentials(item)
    elif isinstance(value, list):
        for item in value:
            _reject_credentials(item)


def defaults(root):
    root = Path(root).resolve()
    import sys
    stockqa = root.parent/'StockQAbyLLM'
    llm = stockqa/'llm_apis.json'
    return {'schema_version': '1.0.0', 'stockwiki_root': str(root.parent/'StockWiki'),
        'stockqa_root': str(root.parent/'StockQAbyLLM'), 'stockwiki_python': sys.executable,
        'stockqa_python': sys.executable, 'workspace_root': '',
        'workspace_kind': 'unconfigured', 'workspace_label': '待连接公司快扫工作区',
        'state_root': str(root/'runs/dashboard-runtime'),
        'runtime_dir': str(stockqa) if llm.is_file() else '', 'model_policy_path': str(llm) if llm.is_file() else '',
        'iqs_release_root': '', 'universe_id': 'default',
        'execution_bundles': {}, 'import_bundles': {}, 'prepare': {},
        'batch': {'max_concurrency': 1}, 'timeout_seconds': 60}


def validate_config(value, root):
    if not isinstance(value, dict) or set(value)-CONFIG_KEYS:
        raise ProductError('invalid_config', '连接配置必须是模板中声明的字段。')
    _reject_credentials(value)
    result = {**defaults(root), **value}
    if result['schema_version'] != '1.0.0':
        raise ProductError('unsupported_config_version', '不支持该连接配置版本。')
    for key in PATH_KEYS:
        item = result.get(key)
        if item is None:
            continue
        if not isinstance(item, str) or '\0' in item or len(item)>4096 or '://' in item:
            raise ProductError('invalid_path', f'{key}必须为本机路径。')
        if item:
            path = Path(item)
            result[key] = str((Path(root)/path if not path.is_absolute() else path).resolve())
    for kind in ('execution_bundles', 'import_bundles'):
        if not isinstance(result[kind], dict) or len(result[kind]) > 5000:
            raise ProductError('invalid_bundles', '注册输入必须是以bundle_id为键的对象。')
        normalized = {}
        for name, bundle in result[kind].items():
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', name):
                raise ProductError('invalid_bundle_id', '输入包ID格式无效。')
            if not isinstance(bundle, dict) or set(bundle)-BUNDLE_KEYS:
                raise ProductError('invalid_bundle', '输入包包含未知字段，不能提交命令或脚本。')
            normalized[name] = dict(bundle)
            if 'work_lease_seconds' in bundle and (type(bundle['work_lease_seconds']) is not int
                    or not 1 <= bundle['work_lease_seconds'] <= 86400):
                raise ProductError('invalid_work_lease', '新工作租约须为1至86400整秒；不更新已有租约。')
            for key in BUNDLE_PATHS & bundle.keys():
                item = bundle[key]
                if not isinstance(item, str) or not item or '\0' in item or '://' in item:
                    raise ProductError('invalid_bundle_path', f'{name}.{key}须为本机文件引用。')
                path = Path(item)
                normalized[name][key] = str((Path(root)/path if not path.is_absolute() else path).resolve())
        result[kind] = normalized
    if not valid_timeout_seconds(result['timeout_seconds']):
        raise ProductError('invalid_timeout', f'超时范围为1至{TIMEOUT_SECONDS_MAX}秒。')
    for key in ('universe_id', 'workspace_kind', 'workspace_label'):
        if not isinstance(result[key], str) or not result[key] or len(result[key]) > 256:
            raise ProductError('invalid_config', f'{key}必须是非空短文本。')
    origin = result.get('dashboard_origin')
    if origin is not None:
        from dashboard_iqs_link import normalize_loopback_origin
        normalized_origin = normalize_loopback_origin(origin)
        if normalized_origin is None:
            raise ProductError('invalid_dashboard_origin',
                               'dashboard_origin 必须是本机 http(s) origin，例如 http://127.0.0.1:8899。')
        result['dashboard_origin'] = normalized_origin
    options = result['prepare']
    if not isinstance(options, dict) or set(options)-PREPARE_KEYS:
        raise ProductError('invalid_prepare_config', '公司准备配置包含未知字段。')
    if 'work_lease_seconds' in options and (type(options['work_lease_seconds']) is not int
            or not 1 <= options['work_lease_seconds'] <= 86400):
        raise ProductError('invalid_work_lease', '新工作租约须为1至86400整秒；不更新已有租约。')
    if 'delegation_ttl_seconds' in options and (type(options['delegation_ttl_seconds']) is not int
            or not 900 <= options['delegation_ttl_seconds'] <= 86400):
        raise ProductError('invalid_prepare_config', '新原执行确认有效期须为900至86400秒；不更新已有确认。')
    if 'recovery_work_decision_refs' in options:
        from dashboard_prepare import parse_recovery_refs, DashboardPrepareError
        try:
            parse_recovery_refs(options)
        except DashboardPrepareError as error:
            raise ProductError('invalid_prepare_config', '恢复模式须显式选择唯一的原工作与原控制决策引用。') from error
    result['prepare'] = dict(options)
    for key,lower,upper in [('worker_timeout_seconds',60,3600),('native_timeout_seconds',30,900)]:
        if key in options and (type(options[key]) is not int or not lower<=options[key]<=upper):
            raise ProductError('invalid_prepare_timeout',f'prepare.{key}超出允许范围。')
    if options.get('native_timeout_seconds',300)>options.get('worker_timeout_seconds',900):
        raise ProductError('invalid_prepare_timeout','native阶段超时不能大于完整准备超时。')
    for key in PREPARE_PATHS & options.keys():
        item = options[key]
        if not isinstance(item, str) or not item or '\0' in item or '://' in item:
            raise ProductError('invalid_prepare_path', f'prepare.{key}必须是本机路径。')
        path = Path(item)
        result['prepare'][key] = str((Path(root)/path if not path.is_absolute() else path).resolve())
    batch = result['batch']
    if (not isinstance(batch, dict) or set(batch)-{'max_concurrency'}
        or type(batch.get('max_concurrency', 1)) is not int or not 1 <= batch.get('max_concurrency', 1) <= 4):
        raise ProductError('invalid_batch_config', '公司并发须为1至4；题目预算仍由原账本控制。')
    return result


class DashboardService:
    def __init__(self, root=ROOT, config_path=None, owner_factory=None, execution_factory=None, prepare_factory=None):
        self.root = Path(root).resolve()
        self.config_path = Path(config_path or self.root/'config/dashboard.local.json').resolve()
        self.csrf_token = secrets.token_urlsafe(32)
        self._lock = threading.RLock()
        self._commands_in_flight = 0
        self._owner_factory, self._execution_factory = owner_factory, execution_factory
        self._prepare_factory = prepare_factory
        self._config_revision = None
        self._owner = self._execution = None
        self._prepare = self._batch = self._jobs = self._delivery = None
        self._snapshots = {}
        self._load()

    def _load(self, *, inactive_checked_config=None, keep_active_revision=False):
        raw = self.config_path.read_bytes() if self.config_path.is_file() else b''
        revision = hashlib.sha256(raw).hexdigest()
        if revision == self._config_revision:
            return
        try:
            supplied = json.loads(raw.decode('utf-8-sig')) if raw else {}
        except (ValueError, UnicodeError) as exc:
            raise ProductError('config_invalid_json', '连接配置不是有效UTF-8 JSON。') from exc
        config = validate_config(supplied, self.root)
        old = getattr(self, 'config', None)
        additive = old is not None and self._append_only(old, config)
        if old is not None and not additive:
            if keep_active_revision and self._commands_in_flight:
                return
            if config != inactive_checked_config:
                self._assert_inactive(next_config=config)
            if self._batch is not None:
                self._batch.close()
        self.config = config
        self._config_revision = revision
        self._owner = None
        if additive:
            if self._execution is not None and old['execution_bundles'] != config['execution_bundles']:
                self._execution.replace_registered_bundles(config['execution_bundles'])
        else:
            self._execution = self._prepare = self._jobs = self._batch = self._delivery = None
        self._snapshots.clear()

    @staticmethod
    def _append_only(old, new):
        maps = {'execution_bundles', 'import_bundles'}
        return ({k:v for k,v in old.items() if k not in maps} == {k:v for k,v in new.items() if k not in maps}
            and all(all(new[key].get(name) == row for name, row in old[key].items()) for key in maps))

    def _assert_inactive(self, *, next_config=None):
        if self._commands_in_flight:
            raise ProductError('execution_active', '原操作正在处理，请等当前操作结束再切换工作区。', 409)
        from dashboard_batches import BatchGateway
        from dashboard_delivery_jobs import DeliveryJobs
        from dashboard_execution import ExecutionGateway
        from dashboard_jobs import PreparationJobs
        state=Path(self.config['state_root'])
        if self._execution is None and ExecutionGateway.has_records(state):
            self._gateway('execution')
        if self._jobs is None and PreparationJobs.has_records(state/'preparation-jobs'):
            self._preparation_jobs()
        if self._delivery is None and DeliveryJobs.has_records(state/'delivery-jobs'):
            self._delivery_jobs()
        if self._batch is None and BatchGateway.has_records(state/'batches'):
            self._batches()
        if self._execution is not None:
            execution = self._execution
            refs = execution.active_references() if hasattr(execution, 'active_references') else execution.tasks(inspect_owner=False, limit=2000)
            if any(row.get('process_state') in {'running', 'starting', 'needs_original_inspection'} for row in refs.get('items', refs.get('tasks', []))):
                raise ProductError('execution_active', '运行期间不切换工作区；请等待当前公司安全结束。', 409)
        if self._batch is not None and self._batch.active():
            raise ProductError('batch_active', '批扫描尚未安全结束；先暂停并核对原任务。', 409)
        if self._jobs is not None and self._jobs.active():
            raise ProductError('preparation_active', '准备结果尚未处理；先查看或核对原准备记录。', 409)
        if self._delivery is not None:
            target=None
            if (next_config is not None and next_config['state_root']==self.config['state_root']
                and all(all(next_config[key].get(name)==row for name,row in self.config[key].items())
                    for key in ('execution_bundles','import_bundles'))):
                from dashboard_delivery_jobs import delivery_deployment_fingerprint
                target=delivery_deployment_fingerprint({**next_config,'iqs_root':str(self.root)})
            if self._delivery.active(compatible_target_sha256=target):
                raise ProductError('delivery_active','交付仍在运行或目标将变化；请等当前操作结束或保留原接收设置。',409)

    def _preparer(self):
        if self._prepare is None:
            from dashboard_prepare import PrepareGateway
            self._prepare = (self._prepare_factory or PrepareGateway)({**self.config, 'iqs_root':str(self.root)})
        return self._prepare

    def _batches(self):
        if self._batch is None:
            from dashboard_batches import BatchGateway
            self._batch = BatchGateway(self._gateway('execution'), Path(self.config['state_root'])/'batches',
                max_concurrency=self.config['batch'].get('max_concurrency',1))
        return self._batch

    def _preparation_jobs(self):
        if self._jobs is None:
            from dashboard_jobs import PreparationJobs
            frozen = {k:v for k,v in self.config.items() if k not in {'execution_bundles','import_bundles'}}
            self._jobs = PreparationJobs(self._preparer(), Path(self.config['state_root'])/'preparation-jobs',
                lambda result: self._register_prepared(result, frozen))
        return self._jobs

    def _delivery_jobs(self):
        if self._delivery is None:
            from dashboard_delivery_jobs import (DeliveryJobs, delivery_deployment_fingerprint,
                LEGACY_DEPLOYMENT_PROFILE, PREVIOUS_DEPLOYMENT_PROFILE, STABLE_DEPLOYMENT_PROFILE)
            digest=delivery_deployment_fingerprint({**self.config,'iqs_root':str(self.root)})
            previous={profile:delivery_deployment_fingerprint(self.config,profile=profile)
                for profile in (LEGACY_DEPLOYMENT_PROFILE,PREVIOUS_DEPLOYMENT_PROFILE)}
            self._delivery=DeliveryJobs(self._gateway('execution'),Path(self.config['state_root'])/'delivery-jobs',digest,
                self._deliver_scope,self._delivery_batch,
                fingerprint_profile=STABLE_DEPLOYMENT_PROFILE,deployment_fingerprints=previous,
                receiver_status=self._gateway('owner').status)
        return self._delivery

    def _delivery_batch(self, batch_id):
        with self._lock:
            batch = self._batches()
        return batch.get(batch_id)

    def _job_facade(self):
        """Bind the durable job projection to this request's frozen deployment."""
        from dashboard_job_facade import OwnerJobFacade
        return OwnerJobFacade(
            Path(self.config['state_root'])/'owner-jobs',
            execution=lambda: self._gateway('execution'),
            preparation_jobs=self._preparation_jobs,
            delivery_jobs=self._delivery_jobs,
            batches=self._batches,
            universe_id=self.config['universe_id'])

    def _deliver_scope(self, bundle_id):
        # Capture trusted local references briefly; all slow native I/O runs
        # OUTSIDE the service lock. Active delivery jobs forbid target switches.
        with self._lock:
            config={**self.config,'iqs_root':str(self.root),'bundles':dict(self.config['execution_bundles'])}
        from dashboard_execution import ExecutionGateway
        from dashboard_owner import OwnerGateway
        execution=(self._execution_factory or ExecutionGateway)(config)
        owner_factory=self._owner_factory or OwnerGateway
        outcomes=[];recovered=set();referenced=[];original=[]
        # Read accepted ACKs before rebuilding optional UI export archives. A
        # process may have died after receiver commit but before local ACK save.
        # Native StockQA still validates the exact original package and target.
        if callable(getattr(execution,'delivery_receivers',None)):
            try:
                snapshot=execution.delivery_receivers(bundle_id)
                referenced=[row['question_id'] for row in snapshot.get('items',[]) if row.get('status')=='referenced']
                original=snapshot.get('consumers',[])
                owner=owner_factory({**config,'bundles':{}})
                receiver=owner.status()
                target={'component':'StockWiki','namespace':'quick_scan','store_id':receiver.get('store_id')}
                groups={}
                for row in original:
                    if (receiver.get('available') and target['store_id'] and row.get('consumer')==target
                        and row.get('package_id') and row.get('observation_id') and row.get('work_store')):
                        groups.setdefault((row['work_store'],row['package_id']),[]).append(row)
                for (ledger,package_id),rows in groups.items():
                    try:
                        mapping={row['observation_id']:row['work_item_id'] for row in rows}
                        acks=[row['ack'] for row in owner.delivery_status(package_id).get('receipts',[])
                            if isinstance(row.get('ack'),dict) and row['ack'].get('observation_id') in mapping
                            and row['ack'].get('status') in {'accepted','already_present'}]
                        if not acks: continue
                        result=execution.acknowledge_delivery({'work_store':ledger,'work_item_ids':mapping},{'acks':acks})
                        done={row['work_item_id'] for row in result.get('items',[]) if row.get('state')=='delivered'}
                        if result.get('status')=='delivered': done.update(mapping.values())
                        recovered.update(done)
                        if set(mapping.values()) <= done:
                            outcomes.append({'package_id':package_id,'status':'already_present',
                                'ack_reconciliation':result})
                    except Exception:
                        # Missing/unusable ACKs retain the established import
                        # path; a successful sibling ACK is already durable.
                        continue
            except Exception:
                pass
        if original and all(row['work_item_id'] in recovered for row in original):
            return {'status':'delivered','items':outcomes,'referenced_question_ids':referenced,
                'API_requests':0,'financial_accuracy_proven':False}
        try:
            exported=execution.export_delivery({'bundle_id':bundle_id})
        except Exception as exc:
            if not recovered: raise
            outcomes.append({'status':'pending','error_code':getattr(exc,'code','delivery_interrupted')})
            return {'status':'partial','items':outcomes,'referenced_question_ids':referenced,
                'API_requests':0,'financial_accuracy_proven':False}
        for name,bundle in exported['import_bundles'].items():
            if bundle.get('work_item_ids') and set(bundle['work_item_ids'].values()) <= recovered:
                continue
            try:
                owner=owner_factory({**config,'bundles':{name:bundle}})
                result=self._apply_import(owner,bundle,{'bundle_id':name},execution=execution,
                    workspace=config['workspace_root'],automatic=True)
                outcomes.append({'bundle_id':name,'status':result.get('status'),
                    'package_id':result.get('receipt',{}).get('package_id'),
                    'ack_reconciliation':result.get('ack_reconciliation')})
            except Exception as exc:
                outcomes.append({'bundle_id':name,'status':'pending','error_code':getattr(exc,'code','delivery_interrupted')})
        referenced=exported.get('referenced_question_ids',[])
        reference_only=(bool(referenced) and not exported['import_bundles']
            and len(exported['items'])==len(referenced)
            and all(row.get('status')=='referenced' for row in exported['items']))
        delivered=(bool(outcomes) or reference_only) and exported['status']=='exported' and all(row.get('ack_reconciliation',{}).get('status')=='delivered' for row in outcomes)
        return {'status':'delivered' if delivered else 'partial' if outcomes else 'pending','items':outcomes,
            'referenced_question_ids':referenced,
            'API_requests':0,'financial_accuracy_proven':False}

    def _register_prepared(self, result, deployment):
        with self._lock:
            self._load()
            if deployment != {k:v for k,v in self.config.items() if k not in {'execution_bundles','import_bundles'}}:
                raise ProductError('preparation_target_changed', '原准备已保留，但工作区或策略已变化，不能登记到新目标。', 409)
            rows = result.get('execution_bundles')
            cached=result.get('cached_scopes',[])
            count=result.get('cached_question_count',0)
            if result.get('status')=='cached':
                valid_scopes=(isinstance(cached,list) and bool(cached) and all(isinstance(scope,dict)
                    and isinstance(scope.get('items'),list) and isinstance(scope.get('subject_ref'),dict)
                    and type(scope.get('question_count')) is int and scope['question_count']==len(scope['items']) for scope in cached))
                items=[item for scope in cached for item in scope['items']] if valid_scopes else []
                ids=[item.get('question_id') for item in items if isinstance(item,dict)]
                if (rows!=[] or not cached or type(count) is not int or count<=0 or len(items)!=count
                    or type(result.get('question_count_total')) is not int or result['question_count_total']!=count or len(ids)!=count
                    or any(not isinstance(q,str) or not q for q in ids)
                    or len(set(ids))!=count
                    or any(not isinstance(item.get('observation_id'),str) or not item['observation_id'] for item in items)):
                    raise ProductError('preparation_result_invalid','缓存完成需要逐题原观察引用，空范围不能算成功。',409)
                return {'bundle_ids':[],'question_count_total':count,'cached_question_count':count,'API_requests':0}
            if result.get('status') != 'prepared' or not isinstance(rows, list) or not rows:
                raise ProductError('preparation_result_invalid', '原准备没有完整的执行范围集合。', 409)
            config = {**self.config, 'execution_bundles':dict(self.config['execution_bundles'])}
            ids = []
            for row in rows:
                name, bundle = row['bundle_id'], row['execution_bundle']
                if name in ids or name in config['execution_bundles'] and config['execution_bundles'][name] != bundle:
                    raise ProductError('prepared_bundle_conflict', '同ID原执行包已存在且内容不同。', 409)
                ids.append(name)
                config['execution_bundles'][name] = bundle
            config = validate_config(config, self.root)
            self._save_config(config)
            return {'bundle_ids':ids, 'question_count_total':result.get('question_count_total'),
                **({'cached_question_count':count} if count else {}),'API_requests':0}

    def _save_config(self, config, *, inactive_checked=False):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with control_lock(self.config_path.with_name(self.config_path.name+'.lock')):
                current = self.config_path.read_bytes() if self.config_path.is_file() else b''
                if hashlib.sha256(current).hexdigest() != self._config_revision:
                    raise ProductError('stale_setup', '连接配置已变化，请刷新重试；原准备不会重做。', 409)
                temporary = self.config_path.with_name(self.config_path.name+'.'+secrets.token_hex(8)+'.tmp')
                try:
                    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
                    os.replace(temporary, self.config_path)
                finally:
                    temporary.unlink(missing_ok=True)
        except ControlBusyError:
            raise ProductError('setup_busy','另一个服务正在保存连接，刷新后重试；原准备结果保留。',409) from None
        # The locked setup path already checked inactivity before writing.
        # A different externally loaded configuration must still be checked.
        self._load(inactive_checked_config=config if inactive_checked else None)

    def bind_runtime_origin(self, origin):
        """G-IQS-01: record the address this process actually bound.

        The launcher only knows the port after `find_free_port`, so the origin
        cannot come from configuration alone. An explicit `dashboard_origin`
        still wins: a deliberately fixed deployment address must never be
        replaced by discovery. An unusable value is ignored rather than stored.
        """
        from dashboard_iqs_link import normalize_loopback_origin
        value = normalize_loopback_origin(origin)
        self._runtime_origin = value
        return value

    def _iqs_origin(self):
        """Configured origin first, then the bound runtime address."""
        return self.config.get(DASHBOARD_ORIGIN_KEY) or getattr(self, '_runtime_origin', None)

    @staticmethod
    def _is_formal_scored_observation(row):
        """True only for a published, scored (non-`fact`) observation row.

        The owner's `history` returns raw SQLite rows. `response_kind` is NOT a
        column on `quick_scan_observation`; it lives at
        `payload.answer.response_kind` (see `dashboard_owner.py`, which reads it
        the same way). Reading a top-level key here would silently never match,
        so the nested location is authoritative and the flat one is only a
        fallback for a future projection that flattens it.
        """
        if not isinstance(row, dict):
            return False
        if row.get('publication_status') != 'published':
            return False
        answer = (row.get('payload') or {}).get('answer') if isinstance(row.get('payload'), dict) else None
        kind = answer.get('response_kind') if isinstance(answer, dict) else None
        if kind is None:
            kind = row.get('response_kind')
        return kind != 'fact'

    def _iqs_link(self, entity_id, return_to):
        """G-IQS-01: publish the frozen IQSLink for the current owner state.

        Only an explicitly configured loopback Dashboard origin is used, so no
        port is ever hardcoded. The observation context is advertised only when
        the owner can actually address a formal observation for THIS entity.

        SCOPING (review REV2-02): the frozen `IQSLink` has no field naming the
        entity it describes, yet `observation` is decided per entity. The DTO is
        therefore ENTITY-SCOPED BY CONSTRUCTION and must never be cached or
        reused across entities: a caller that asks about company A must not
        apply that answer to company B. When no entity id is supplied no
        per-entity read is performed, so the `observation` context is not
        advertised at all rather than being claimed owner-wide.
        """
        from dashboard_iqs_link import (
            FALLBACK_RETURN,
            capability,
            company_return_entity,
            safe_entity_id,
        )
        origin = self._iqs_origin()
        count = None
        state = 'unconfigured'
        has_subject = False
        # REV5-01: the bounded-identifier rule is enforced at the boundary rather
        # than left as an unused helper. A malformed id must not be passed to the
        # owner as though it were addressable.
        entity_id = safe_entity_id(entity_id)
        # B03: a company-scoped return that names a DIFFERENT company than the
        # link being composed is cross-scope injection; collapse it to the plain
        # fallback instead of echoing it back to the caller.
        if return_to and company_return_entity(return_to) not in (None, entity_id):
            return_to = FALLBACK_RETURN
        if entity_id and origin:
            state = 'unreadable'
            try:
                history = self._gateway('owner').history(entity_id)
            except Exception:
                # An unreadable owner is NOT "no observations"; the state stays
                # `unreadable` so the count is never mistaken for a real zero.
                history = None
            if isinstance(history, dict) and history.get('available') is False:
                # The owner explicitly reports that it cannot serve this
                # entity's observations (`owner_observation_database_missing`).
                # That is "cannot read", not "has none".
                history = None
            rows = history.get('observations') if isinstance(history, dict) else None
            if isinstance(rows, list):
                state = 'counted'
                # REV3-03/REV4-01: a `fact` row is stored reference information,
                # not a scored formal result, so it must not enable the
                # observation context. Counting it would publish a capability
                # the UI then refuses -- the exact failure this card prevents.
                formal = [row for row in rows if self._is_formal_scored_observation(row)]
                count = len(formal)
                # REV4-03: `subject` is only addressable when a formal row
                # actually carries an analysis_subject_id (the column exists but
                # is NULL for legacy rows).
                has_subject = any(row.get('analysis_subject_id') for row in formal)
        value = capability(base_origin=origin, observation_count=count,
                           observation_state=state, has_subject=has_subject,
                           return_to=return_to)
        # The frozen `IQSLink` is `additionalProperties: false`; adding any key
        # here would break the Dashboard contract, so the exact deep link is
        # composed by the UI from `routes.results` + the observation id.
        return value

    def _read_company_result(self, entity_id, result_id):
        """Read an owner result and distinguish a missing pin from an unavailable store."""
        import dashboard_company_projection as projection

        owner_payload = self._gateway('owner').company_result(entity_id, result_id)
        try:
            response = projection.project_result(owner_payload)
        except projection.ProjectionError as error:
            raise ProductError(error.code, error.message, error.status) from None
        if result_id is not None:
            result = response['company_result']
            if result is None:
                reason = response['reason_code']
                if reason in {'observation_store_missing', 'observation_store_unavailable'}:
                    raise ProductError(reason, '观察库暂时不可用，无法读取固定的公司结果。', 503)
                raise ProductError('company_result_not_found',
                                   '固定的公司结果不存在或不属于该实体。', 404)
            if result['result_id'] != result_id:
                raise ProductError('company_result_pin_mismatch',
                                   '公司结果所有者返回的结果ID与请求固定ID不一致。', 502)
        return response

    def _company_assessment_result(self, entity_id, result_id, return_to):
        """Return the owner snapshot with its entity-scoped IQS link."""
        response = self._read_company_result(entity_id, result_id)
        response['iqs_link'] = self._iqs_link(entity_id, return_to)
        if result_id is not None:
            response['iqs_link'] = _pin_company_result_route(
                response['iqs_link'], response['company_result'])
        return response

    def _company_assessment_history(self, entity_id, limit, offset):
        """B03: GET `company/history` - bounded owner company result history."""
        import dashboard_company_projection as projection

        owner_payload = self._gateway('owner').company_history(entity_id, limit, offset)
        try:
            return projection.project_history(owner_payload, limit=limit, offset=offset)
        except projection.ProjectionError as error:
            raise ProductError(error.code, error.message, error.status) from None

    def _gateway(self, kind):
        attr = '_owner' if kind == 'owner' else '_execution'
        gateway = getattr(self, attr)
        if gateway is not None:
            return gateway
        config = {**self.config, 'iqs_root': str(self.root)}
        config['bundles'] = config['import_bundles'] if kind == 'owner' else config['execution_bundles']
        factory = self._owner_factory if kind == 'owner' else self._execution_factory
        if factory is None:
            if kind == 'owner':
                from dashboard_owner import OwnerGateway
                factory = OwnerGateway
            else:
                from dashboard_execution import ExecutionGateway
                factory = ExecutionGateway
        gateway = factory(config)
        setattr(self, attr, gateway)
        return gateway

    def _apply_import(self, owner, bundle, body, *, execution=None, workspace=None, automatic=False):
        execution=execution or self._gateway('execution')
        mapped = bool(bundle.get('work_store') and bundle.get('work_item_ids'))
        if mapped or automatic:
            preview=owner.import_preview({'bundle_id':body.get('bundle_id')})
            if automatic:
                body={**body,'preview_token':preview.get('preview_token')}
            if body.get('preview_token') != preview.get('preview_token'):
                raise ProductError('preview_stale','请重新预览原接收目标再导入。',409)
        if mapped:
            status=owner.status()
            if not status.get('available') or not status.get('store_id'):
                raise ProductError('receiver_unavailable','无法核实原StockWiki接收目标。',409)
            target={'component':'StockWiki','namespace':'quick_scan','store_id':status['store_id']}
            execution.bind_delivery_consumer(bundle,target,'dashboard-owner-status:'+(workspace or self.config['workspace_root']))
        result=owner.import_apply(body)
        if isinstance(result.get('receipt'),dict):
            if mapped:
                try:
                    result['ack_reconciliation']=execution.acknowledge_delivery(bundle,result['receipt'])
                except Exception as exc:
                    result['ack_reconciliation']={'status':'pending','error_code':getattr(exc,'code','ack_reconciliation_failed'),
                        'notice':'StockWiki已产生回执；原StockQA未确认，重试会复用原回执。'}
            else:
                result['ack_reconciliation']={'status':'not_configured','notice':'没有原StockQA账本映射，不能宣称执行器delivered。'}
        return result

    def _safe_status(self, kind):
        try:
            return self._gateway(kind).status()
        except Exception as exc:
            return {'available': False, 'blocked_reasons': [getattr(exc, 'code', 'owner_unavailable')],
                    'message': str(exc)[:500]}

    def _request_view(self, target):
        """Capture one deployment and its existing adapters before slow I/O.

        This lightweight request view never saves or reloads configuration. The
        original adapters retain their task/process state; config replacement
        cannot redirect an in-flight read into another workspace.
        """
        path = urlsplit(target).path.removeprefix('/api/product/').rstrip('/')
        if path in {'status', 'doctor'}:
            for kind in ('owner', 'execution'):
                try:
                    self._gateway(kind)
                except Exception:
                    pass  # _safe_status reports this adapter's error in the view.
        elif (path in {'results', 'coverage', 'entity-view', 'entity', 'history', 'facts', 'universe', 'delivery'}
                or path.startswith(('universe/', 'import/'))):
            self._gateway('owner')
            if path == 'import/apply':
                self._gateway('execution')
        elif (path in {'settings', 'tasks'} or path.startswith('tasks/')) and path != 'tasks/deliver':
            self._gateway('execution')
        elif path in {'prepare/status', 'prepare/preview'}:
            self._preparer()
        elif path in {'prepare/jobs', 'prepare/apply'} or path.startswith('prepare/jobs/'):
            self._preparation_jobs()
        elif path == 'tasks/deliver' or path.startswith('delivery/jobs') or re.fullmatch(r'batches/[^/]+/deliver', path):
            self._delivery_jobs()
        elif path == 'jobs' or path.startswith('jobs/'):
            if path.startswith('jobs/prepjob_'):
                self._preparation_jobs()
            elif path.startswith('jobs/deliveryjob_'):
                self._delivery_jobs()
            elif path.startswith('jobs/batch-'):
                self._batches()
            else:
                self._gateway('execution')
        elif path == 'batches' or path.startswith('batches/'):
            self._batches()
        view = copy.copy(self)
        view.config = copy.deepcopy(self.config)
        return view

    def _setup(self, body=None):
        if body is None:
            return {'config': self.config, 'revision_sha256': self._config_revision, 'editable': True,
                    'config_path': str(self.config_path), 'credential_values_returned': False}
        if set(body) != {'config', 'revision_sha256'}:
            raise ProductError('invalid_setup_request', '提交config与revision_sha256。')
        current = self.config_path.read_bytes() if self.config_path.is_file() else b''
        if body['revision_sha256'] != hashlib.sha256(current).hexdigest():
            raise ProductError('stale_setup', '连接配置已变化，请刷新后再保存。', 409)
        config = validate_config(body['config'], self.root)
        if current and config == self.config:
            return self._setup()  # No write, reconfiguration or interruption.
        self._gateway('execution')  # Include persisted references on first access.
        self._assert_inactive(next_config=config)
        self._save_config(config, inactive_checked=True)
        return self._setup()

    def dispatch(self, method, target, body=None):
        """Return an HTTP status and JSON envelope; authentication is transport-owned."""
        started = time.monotonic()
        registered = False
        body = {} if body is None else body
        try:
            path = urlsplit(target).path.rstrip('/')
            with self._lock:
                self._load(keep_active_revision=method == 'GET')
                if method == 'PUT' and path == '/api/product/setup':
                    result = self._dispatch(method, target, body)
                    view = None
                else:
                    view = self._request_view(target)
                    read_only_post = method == 'POST' and path.removeprefix('/api/product/') in {
                        'prepare/preview', 'tasks/preview', 'batches/preview', 'universe/preview', 'import/preview'}
                    if method != 'GET' and not read_only_post:
                        self._commands_in_flight += 1
                        registered = True
            if view is not None:
                result = view._dispatch(method, target, body)
            return 200, {'ok': True, 'data': redact(result), 'elapsed_ms': round((time.monotonic()-started)*1000)}
        except Exception as exc:
            known = isinstance(exc, ProductError) or hasattr(exc, 'code')
            return getattr(exc, 'status', 500) if known else 500, {'ok': False, 'error': {
                'code': getattr(exc, 'code', 'internal_error'),
                'message': str(exc)[:500] if known else '本地组件处理失败，请检查doctor与组件状态。',
                'details': redact(getattr(exc, 'details', {}))}}
        finally:
            if registered:
                with self._lock:
                    self._commands_in_flight -= 1

    def _dispatch(self, method, target, body):
        parsed = urlsplit(target)
        path = parsed.path.removeprefix('/api/product/').rstrip('/')
        query = {k: values[-1] for k, values in parse_qs(parsed.query).items()}
        raw_query = parse_qs(parsed.query, keep_blank_values=True)
        if not parsed.path.startswith('/api/product/'):
            raise ProductError('not_found', '未找到接口。', 404)
        if not isinstance(body, dict):
            raise ProductError('invalid_body', '请求内容必须是JSON对象。')
        if method == 'GET':
            if path == 'delivery/jobs':
                return self._delivery_jobs().list()
            if path == 'jobs':
                return self._job_facade().list_jobs(cursor=query.get('cursor'),
                    limit=query.get('limit', 50))
            # Keep the public command-binding fallback reachable: adapters may
            # first probe an owner_job_id and, on owner_job_id_invalid, resolve
            # the same value as a Dashboard command_id through jobs/commands/.
            # The facade remains the authority that validates owner job IDs.
            match = re.fullmatch(r'jobs/([A-Za-z0-9][A-Za-z0-9._:\-]{0,127})', path)
            if match:
                return self._job_facade().get_status(match[1])
            match = re.fullmatch(r'jobs/commands/([A-Za-z0-9][A-Za-z0-9._:\-]{0,127})', path)
            if match:
                return self._job_facade().get_command(match[1])
            if path == 'prepare/status':
                return self._preparer().status()
            if path == 'prepare/jobs':
                return self._preparation_jobs().list()
            match = re.fullmatch(r'prepare/jobs/(prepjob_[a-f0-9]{32})', path)
            if match:
                return self._preparation_jobs().get(match[1])
            if path == 'batches':
                try:
                    return self._batches().list(limit=int(query.get('limit',50)), offset=int(query.get('offset',0)))
                except ValueError as exc:
                    if hasattr(exc, 'code'): raise
                    raise ProductError('invalid_query','批任务分页无效。') from None
            if path == 'status':
                owner, execution = self._safe_status('owner'), self._safe_status('execution')
                owner['registered_import_bundles'] = [{'bundle_id': name, 'entity_id': item.get('entity_id')}
                    for name, item in self.config['import_bundles'].items()]
                return {'api_version': '1.0.0', 'csrf_token': self.csrf_token,
                    'owner': owner, 'execution': execution, 'data': {'workspace_kind': self.config['workspace_kind'],
                    'workspace_label': self.config['workspace_label'], 'workspace_root': self.config['workspace_root']},
                    'read_has_model_calls': False,
                    # OWNERPKG-INVEST-QUICK-SCAN-01: the public job façade rides
                    # the same origin, transport guards and envelope as this
                    # control plane; this block is its route discovery record.
                    'owner_job_facade': {'wire_protocol': WIRE_PROTOCOL,
                        'mapping_version': MAPPING_VERSION,
                        'routes': {'submit': 'POST jobs/submit',
                                   'status': 'GET jobs/{owner_job_id}',
                                   'actions': 'GET jobs/{owner_job_id} via job_view.allowed_actions',
                                   'act': 'POST jobs/{owner_job_id}/{cancel|resume|retry|reconcile}',
                                   'list': 'GET jobs?cursor&limit',
                                   'command_binding': 'GET jobs/commands/{command_id}'},
                        'limits_ref_registry': sorted(key for key in LIMITS_REF_REGISTRY if key),
                        'job_id_kinds': [kind for kind in ('run', 'prepjob', 'deliveryjob', 'batch')]}}
            if path == 'setup':
                return self._setup()
            if path == 'settings':
                return self._gateway('execution').settings()
            if path == 'tasks':
                try:
                    limit, offset = int(query.get('limit', 50)), int(query.get('offset', 0))
                except ValueError:
                    raise ProductError('invalid_query', '任务分页无效。')
                return self._gateway('execution').tasks(inspect_owner=False, limit=limit, offset=offset)
            if path == 'doctor':
                owner, execution = self._safe_status('owner'), self._safe_status('execution')
                checks = [{'id': 'StockWiki', 'status': 'available' if owner.get('available') else 'blocked',
                    'message': '原身份与观察库可读' if owner.get('available') else owner.get('error', {}).get('code', 'owner_unavailable')},
                    {'id': 'StockQA', 'status': 'available' if execution.get('available') else 'blocked',
                     'message': '已登记原执行包部署文件可用，仍需逐包原预检' if execution.get('available') else '没有完整登记的执行包；先按部署说明准备原输入'},
                    {'id': 'model_policy', 'status': 'present' if self.config.get('model_policy_path') and Path(self.config['model_policy_path']).is_file() else 'missing',
                     'message': '仅检查原配置文件存在；模型顺序/预算由设置和原预检校验'}]
                blocked = [check['id'] for check in checks if check['status'] in {'blocked', 'missing'}]
                return {'owner': owner, 'execution': execution, 'checks': checks,
                    'ready': not blocked, 'blocked_reasons': blocked, 'paid_connectivity_tested': False,
                    'environment_presence': {name: bool(os.environ.get(name)) for name in (
                        'MIMO_API_KEY', 'MIMO_PLAN_API_KEY', 'MINIMAX_API_KEY', 'DEEPSEEK_API_KEY',
                        'ZAI_API_KEY', 'BRAVE_API_KEY', 'TAVILY_API_KEY')},
                    'configuration': self._setup(), 'API_requests': 0, 'network_calls': 0}
            if path == 'results':
                try:
                    limit, offset = int(query.get('limit', 50)), int(query.get('offset', 0))
                    filters = json.loads(query.get('filters', '{}'))
                    conditions = json.loads(query.get('conditions', '[]'))
                    combine = query.get('condition_combine', 'all')
                    if not isinstance(filters, dict) or not isinstance(conditions, list) or len(conditions) > 100 or combine not in {'all', 'any'} or not 1 <= limit <= 100 or offset < 0:
                        raise ValueError('bounds')
                except (ValueError, TypeError):
                    raise ProductError('invalid_query', '分页或筛选条件无效。')
                selection = {'query': query.get('query', ''), 'filters': filters, 'conditions': conditions,
                    'condition_combine': combine, 'view': query.get('view', 'all_relevant'), 'limit': limit}
                fingerprint = hashlib.sha256(json.dumps(selection, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                now = time.monotonic()
                token = query.get('snapshot_token')
                snapshot = None
                with self._lock:
                    for key in list(self._snapshots):
                        if now-self._snapshots[key]['time'] >= 900:
                            self._snapshots.pop(key)
                    if token:
                        saved = self._snapshots.get(token)
                        if (saved is None or saved['fingerprint'] != fingerprint
                                or saved.get('config_revision') != self._config_revision):
                            raise ProductError('snapshot_expired', '筛选快照已过期或条件已变化，请从第一页刷新。', 409)
                        snapshot = saved['snapshot']
                    elif offset:
                        raise ProductError('snapshot_required', '翻页须使用第一页返回的筛选快照。', 409)
                result = self._gateway('owner').search(selection['query'], limit, offset,
                    filters=filters, conditions=conditions or None, condition_combine=combine,
                    view=selection['view'], snapshot=snapshot)
                if isinstance(result, dict) and isinstance(result.get('snapshot'), dict):
                    with self._lock:
                        if not token:
                            if len(self._snapshots) >= 128:
                                self._snapshots.pop(next(iter(self._snapshots)))
                            token = secrets.token_urlsafe(24)
                        self._snapshots[token] = {'snapshot': result['snapshot'], 'fingerprint': fingerprint,
                            'config_revision': self._config_revision, 'time': now}
                    result['snapshot_token'] = token
                return result
            if path == 'coverage':
                return self._gateway('owner').coverage()
            if path == 'entity-view':
                entity_id = query.get('id', query.get('entity_id', ''))
                if not entity_id:
                    raise ProductError('entity_required', '请选择已注册公司。')
                result = self._gateway('owner').entity_view(entity_id)
                return result
            if path in {'entity', 'history', 'facts'}:
                entity_id = query.get('id', query.get('entity_id', ''))
                if not entity_id:
                    raise ProductError('entity_required', '请选择已注册公司。')
                result = getattr(self._gateway('owner'), path)(entity_id)
                if path == 'entity':
                    # G-IQS-01: the frozen `IQSLink` travels with the entity so
                    # a consumer reads one declaration instead of guessing. An
                    # unconfigured or unreadable owner still yields an explicit
                    # link whose `unavailable`/`unreadable` reason says which
                    # it was, rather than a null the UI would misread as "no
                    # declaration".
                    #
                    # B03 LIVE-OWNER-VERIFY-REPAIR-01: this declaration must be
                    # present on the entity route. Without it the Dashboard
                    # `get_result` composition falls back to the legacy partial
                    # declaration and the composed deep link loses the latest
                    # company result's `result_id` pin, the first-observation
                    # anchor and the return context. The declaration is
                    # entity-scoped by construction (see `_iqs_link`), so it is
                    # rebuilt for THIS entity on every read and never cached
                    # across entities.
                    result['iqs_link'] = self._iqs_link(entity_id, query.get('return'))
                return result
            if path == 'universe':
                return self._gateway('owner').universe_list(query.get('universe_id', self.config['universe_id']))
            if path == 'universe/request':
                allowed = {'universe_id', 'idempotency_key', 'request_id'}
                if set(query) - allowed or any(len(raw_query.get(key, [])) > 1 for key in allowed):
                    raise ProductError('invalid_query', '成员请求查询参数无效。')
                payload = {key: query[key] for key in allowed if key in query}
                return read_membership_request(self._gateway('owner'), payload)
            if path == 'universe/history':
                allowed = {'universe_id', 'entity_id', 'limit', 'after_version', 'version_pin'}
                if set(query) - allowed or any(len(raw_query.get(key, [])) > 1 for key in allowed):
                    raise ProductError('invalid_query', '成员历史查询参数无效。')
                try:
                    limit_raw = query.get('limit', '50')
                    if (not limit_raw.isascii() or not limit_raw.isdecimal() or len(limit_raw) > 3):
                        raise ValueError('limit')
                    limit = int(limit_raw)
                    def optional_version(name):
                        value = query.get(name)
                        if value is None:
                            return None
                        if not value.isascii() or not value.isdecimal() or len(value) > 12:
                            raise ValueError(name)
                        return int(value)
                    after_version = optional_version('after_version')
                    version_pin = optional_version('version_pin')
                except ValueError:
                    raise ProductError('invalid_query', '成员历史分页或版本参数无效。') from None
                return read_membership_history(self._gateway('owner'), {
                    'universe_id': query.get('universe_id', self.config['universe_id']),
                    'entity_id': query.get('entity_id'), 'limit': limit,
                    'after_version': after_version, 'version_pin': version_pin})
            if path == 'delivery':
                return self._gateway('owner').delivery_status(query.get('package_id'))
            if path == 'link':
                entity_id = query.get('id', query.get('entity_id', ''))
                result_values = raw_query.get('result', [])
                result_id_values = raw_query.get('result_id', [])
                supplied_pin = bool(result_values or result_id_values)
                if (len(result_values) > 1 or len(result_id_values) > 1
                        or (result_values and result_id_values)
                        or (supplied_pin and (result_values + result_id_values)[0] == '')):
                    raise ProductError('invalid_query', '公司结果ID必须唯一且非空。')
                result_pin = ((result_values or result_id_values)[0]
                              if supplied_pin else None)
                pin_data = self._read_company_result(entity_id, result_pin) if result_pin else None
                result = self._iqs_link(entity_id, query.get('return'))
                if pin_data is not None:
                    result = _pin_company_result_route(
                        result, pin_data['company_result'])
                return result
            if path == 'company/result':
                entity_id = query.get('id', query.get('entity_id', ''))
                if not entity_id:
                    raise ProductError('entity_required', '请选择已注册公司。')
                result_ids = raw_query.get('result_id', [])
                if len(result_ids) > 1 or (result_ids and result_ids[0] == ''):
                    raise ProductError('invalid_query', '公司结果ID必须唯一且非空。')
                result_id = result_ids[0] if result_ids else None
                return self._company_assessment_result(entity_id, result_id, query.get('return'))
            if path == 'company/history':
                entity_id = query.get('id', query.get('entity_id', ''))
                if not entity_id:
                    raise ProductError('entity_required', '请选择已注册公司。')
                try:
                    limit, offset = int(query.get('limit', 20)), int(query.get('offset', 0))
                except ValueError:
                    raise ProductError('invalid_query', '公司结果分页无效。')
                if not 1 <= limit <= 50 or offset < 0:
                    raise ProductError('invalid_query', '公司结果分页无效。')
                return self._company_assessment_history(entity_id, limit, offset)
        elif method == 'PUT':
            if path == 'setup':
                return self._setup(body)
            if path == 'settings':
                _reject_credentials(body)
                return self._gateway('execution').save_settings(body)
        elif method == 'POST':
            if path == 'tasks/deliver':
                return self._delivery_jobs().submit(body)
            match=re.fullmatch(r'batches/([A-Za-z0-9_.-]{1,128})/deliver',path)
            if match:
                if body: raise ProductError('invalid_body','选择原公司批即可。')
                return self._delivery_jobs().submit({'batch_id':match[1]})
            match=re.fullmatch(r'delivery/jobs/(deliveryjob_[a-f0-9]{32})/(resume|abandon)',path)
            if match:
                if body: raise ProductError('invalid_body','交付恢复无需额外参数。')
                return self._delivery_jobs().control(*match.groups())
            if path == 'tasks/export-delivery':
                exported=self._gateway('execution').export_delivery(body)
                return exported
            if path == 'prepare/preview':
                return self._preparer().bank_preview(body)
            if path == 'prepare/apply':
                return self._preparation_jobs().submit(body)
            match = re.fullmatch(r'prepare/jobs/(prepjob_[a-f0-9]{32})/(reconcile|abandon)', path)
            if match:
                if body: raise ProductError('invalid_body','恢复准备无需额外参数。')
                return getattr(self._preparation_jobs(),match[2])(match[1])
            if path == 'batches/preview':
                return self._batches().registration_preview(body)
            if path == 'batches/start':
                return self._batches().start(body)
            match = re.fullmatch(r'batches/([A-Za-z0-9_.-]{1,128})/(pause|resume|abandon)', path)
            if match:
                if body: raise ProductError('invalid_body','批任务控制无需额外参数。')
                return self._batches().control(*match.groups())
            if path in {'universe/preview', 'universe/apply', 'import/preview', 'import/apply'}:
                action = path.replace('/', '_')
                if path == 'import/apply':
                    bundle = self.config['import_bundles'].get(body.get('bundle_id'), {})
                    return self._apply_import(self._gateway('owner'),bundle,body)
                if path == 'universe/apply' and body.get('idempotency_key') is not None:
                    return apply_keyed_membership(self._gateway('owner'), body)
                return getattr(self._gateway('owner'), action)(body)
            if path == 'jobs/submit':
                return self._job_facade().submit_run_scan(body)
            match = re.fullmatch(rf'jobs/({JOB_ID_PATTERN})/(cancel|resume|retry|reconcile)', path)
            if match:
                if not isinstance(body, dict) or set(body) != {'idempotency_key'} \
                        or not isinstance(body.get('idempotency_key'), str):
                    raise ProductError('invalid_body', 'job动作体必须是{idempotency_key}。')
                return self._job_facade().act(match[1],
                    {'action': match[2], 'idempotency_key': body['idempotency_key']})
            if path in {'tasks/preview', 'tasks/start'}:
                return getattr(self._gateway('execution'), path.split('/')[1])(body)
            match = re.fullmatch(r'tasks/([A-Za-z0-9_.-]{1,128})/(inspect|pause|resume|retire|seal)', path)
            if match:
                if match[2] in {'retire','seal'} and body:
                    raise ProductError('invalid_body', '该原启动控制无需额外参数。')
                return self._gateway('execution').control(*match.groups())
        raise ProductError('method_or_route_not_allowed', '该接口或方法不支持。', 405)
