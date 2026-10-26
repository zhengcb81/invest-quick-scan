"""Local product control plane over the existing two owners.

No model client, question queue, scoring formula, or private database access.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, urlsplit
from dashboard_locks import control_lock, ControlBusyError

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = {'api_key', 'apikey', 'api_secret', 'secret', 'password', 'authorization',
               'access_token', 'refresh_token', 'probe_token'}
PATH_KEYS = {'stockwiki_root', 'stockwiki_python', 'stockqa_root', 'stockqa_python',
             'workspace_root', 'runtime_dir', 'state_root', 'model_policy_path', 'iqs_release_root'}
BUNDLE_PATHS = {'questions', 'manifest', 'identity_snapshot', 'c06_authority', 'owner_config',
                'admission_config', 'spend_authorization', 'inspection_request', 'search_policy',
                'runtime_dir', 'package', 'release', 'work_store'}
BUNDLE_KEYS = BUNDLE_PATHS | {'entity_id', 'company', 'provider', 'confirmation_id',
    'inspection_schema_version', 'pack_size', 'thinking', 'max_output_tokens', 'security_scope_id',
    'package_sha256', 'release_sha256', 'work_item_ids', 'company_preparation_id', 'scope', 'scope_id', 'security_id', 'expected_scope_bindings', 'recovery_subset', 'execution_question_ids', 'execution_question_count'}
CONFIG_KEYS = PATH_KEYS | {'schema_version', 'universe_id', 'execution_bundles', 'import_bundles',
                          'timeout_seconds', 'workspace_kind', 'workspace_label', 'prepare', 'batch'}
PREPARE_KEYS = {'state_root', 'admission_config', 'module_package_id', 'producer',
    'authorization_reference', 'agent', 'runtime_dir', 'spend_authorization', 'search_policy',
    'pack_size', 'thinking', 'max_output_tokens', 'routing_profiles', 'worker_timeout_seconds', 'native_timeout_seconds', 'delegation_ttl_seconds', 'recovery_work_decision_refs'}
PREPARE_PATHS = {'state_root', 'admission_config', 'runtime_dir', 'spend_authorization', 'search_policy'}


class ProductError(Exception):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details or {}


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
    real_owner = root / 'runs/r25-live/owner-workspace'
    historical = root / 'runs/c16b/native-owner-alphabet-01/owner-workspace'
    import sys
    stockqa = root.parent/'StockQAbyLLM'
    llm = stockqa/'llm_apis.json'
    return {'schema_version': '1.0.0', 'stockwiki_root': str(root.parent/'StockWiki'),
        'stockqa_root': str(root.parent/'StockQAbyLLM'), 'stockwiki_python': sys.executable,
        'stockqa_python': sys.executable, 'workspace_root': str(real_owner if real_owner.is_dir() else historical),
        'workspace_kind': 'isolated_research', 'workspace_label': '现有真实运行工作区；非金融合格声明',
        'state_root': str(root/'runs/dashboard-runtime'),
        'runtime_dir': str(stockqa) if llm.is_file() else '', 'model_policy_path': str(llm) if llm.is_file() else '',
        'iqs_release_root': str(root/'runs/c16b/iqs-release'), 'universe_id': 'default',
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
            for key in BUNDLE_PATHS & bundle.keys():
                item = bundle[key]
                if not isinstance(item, str) or not item or '\0' in item or '://' in item:
                    raise ProductError('invalid_bundle_path', f'{name}.{key}须为本机文件引用。')
                path = Path(item)
                normalized[name][key] = str((Path(root)/path if not path.is_absolute() else path).resolve())
        result[kind] = normalized
    if type(result['timeout_seconds']) not in (int, float) or not 1 <= result['timeout_seconds'] <= 600:
        raise ProductError('invalid_timeout', '超时范围为1至600秒。')
    for key in ('universe_id', 'workspace_kind', 'workspace_label'):
        if not isinstance(result[key], str) or not result[key] or len(result[key]) > 256:
            raise ProductError('invalid_config', f'{key}必须是非空短文本。')
    options = result['prepare']
    if not isinstance(options, dict) or set(options)-PREPARE_KEYS:
        raise ProductError('invalid_prepare_config', '公司准备配置包含未知字段。')
    if 'delegation_ttl_seconds' in options and (type(options['delegation_ttl_seconds']) is not int
            or not 900 <= options['delegation_ttl_seconds'] <= 86400):
        raise ProductError('invalid_prepare_config', '新原执行确认有效期须为900至86400秒；不更新已有确认。')
    if 'recovery_work_decision_refs' in options:
        from dashboard_prepare import _recovery_refs, DashboardPrepareError
        try:
            _recovery_refs({'prepare': options})
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
    def __init__(self, root=ROOT, config_path=None, ui_root=None, owner_factory=None, execution_factory=None, prepare_factory=None):
        self.root = Path(root).resolve()
        self.config_path = Path(config_path or self.root/'config/dashboard.local.json').resolve()
        self.ui_root = Path(ui_root or self.root.parent/'iqs-question-bank-ui-lab').resolve()
        self.csrf_token = secrets.token_urlsafe(32)
        self._lock = threading.RLock()
        self._owner_factory, self._execution_factory = owner_factory, execution_factory
        self._prepare_factory = prepare_factory
        self._config_revision = None
        self._owner = self._execution = None
        self._prepare = self._batch = self._jobs = self._delivery = None
        self._snapshots = {}
        self._load()

    def _load(self):
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
            self._assert_inactive()
            if self._batch is not None:
                self._batch.close()
        self.config = config
        self._config_revision = revision
        self._owner = None
        if additive:
            if self._execution is not None:
                self._execution.bundles = self.config['execution_bundles']
                self._execution.config.update(self.config, bundles=self.config['execution_bundles'])
        else:
            self._execution = self._prepare = self._jobs = self._batch = self._delivery = None
        self._snapshots.clear()

    @staticmethod
    def _append_only(old, new):
        maps = {'execution_bundles', 'import_bundles'}
        return ({k:v for k,v in old.items() if k not in maps} == {k:v for k,v in new.items() if k not in maps}
            and all(all(new[key].get(name) == row for name, row in old[key].items()) for key in maps))

    def _assert_inactive(self):
        state=Path(self.config['state_root'])
        if self._jobs is None and any((state/'preparation-jobs').glob('prepjob_*.json')):
            self._preparation_jobs()
        if self._delivery is None and any((state/'delivery-jobs').glob('deliveryjob_*.json')):
            self._delivery_jobs()
        if self._batch is None and any((state/'batches').glob('batch-*.json')):
            self._batches()
        if self._execution is not None:
            execution = self._execution
            refs = execution.active_references() if hasattr(execution, 'active_references') else execution.tasks(inspect_owner=False, limit=2000)
            if any(row.get('process_state') in {'running', 'starting', 'needs_original_inspection'} for row in refs.get('items', refs.get('tasks', []))):
                raise ProductError('execution_active', '运行期间不切换工作区；请等待当前公司安全结束。', 409)
        if self._batch is not None:
            offset = 0
            while True:
                page = self._batch.list(limit=100, offset=offset)
                if any(row.get('state') in {'running','draining','needs_original_inspection'} for row in page['batches']):
                    raise ProductError('batch_active', '批扫描尚未安全结束；先暂停并核对原任务。', 409)
                offset += len(page['batches'])
                if offset >= page['total'] or not page['batches']: break
        if self._jobs is not None and self._jobs.active():
            raise ProductError('preparation_active', '准备结果尚未处理；先查看或核对原准备记录。', 409)
        if self._delivery is not None and self._delivery.active():
            raise ProductError('delivery_active','交付或恢复尚未处理，先核对原ACK或显式放弃等待。',409)

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
            from dashboard_delivery_jobs import DeliveryJobs
            frozen={k:v for k,v in self.config.items() if k not in {'execution_bundles','import_bundles'}}
            digest=hashlib.sha256(json.dumps(frozen,sort_keys=True,ensure_ascii=False).encode('utf8')).hexdigest()
            self._delivery=DeliveryJobs(self._gateway('execution'),Path(self.config['state_root'])/'delivery-jobs',digest,
                lambda bundle_id:self._deliver_scope(bundle_id),lambda batch_id:self._batches().get(batch_id))
        return self._delivery

    def _deliver_scope(self, bundle_id):
        # Capture trusted local references briefly; all slow native I/O runs
        # OUTSIDE the service lock. Active delivery jobs forbid target switches.
        with self._lock:
            config={**self.config,'iqs_root':str(self.root),'bundles':dict(self.config['execution_bundles'])}
        from dashboard_execution import ExecutionGateway
        from dashboard_owner import OwnerGateway
        execution=(self._execution_factory or ExecutionGateway)(config)
        exported=execution.export_delivery({'bundle_id':bundle_id})
        outcomes=[]
        for name,bundle in exported['import_bundles'].items():
            try:
                owner=(self._owner_factory or OwnerGateway)({**config,'bundles':{name:bundle}})
                preview=owner.import_preview({'bundle_id':name})
                result=self._apply_import(owner,bundle,{'bundle_id':name,'preview_token':preview['preview_token']},execution=execution,workspace=config['workspace_root'])
                outcomes.append({'bundle_id':name,'status':result.get('status'),
                    'package_id':result.get('receipt',{}).get('package_id'),
                    'ack_reconciliation':result.get('ack_reconciliation')})
            except Exception as exc:
                outcomes.append({'bundle_id':name,'status':'pending','error_code':getattr(exc,'code','delivery_interrupted')})
        delivered=bool(outcomes) and exported['status']=='exported' and all(row.get('ack_reconciliation',{}).get('status')=='delivered' for row in outcomes)
        return {'status':'delivered' if delivered else 'partial' if outcomes else 'pending','items':outcomes,
            'API_requests':0,'financial_accuracy_proven':False}

    def _register_prepared(self, result, deployment):
        with self._lock:
            self._load()
            if deployment != {k:v for k,v in self.config.items() if k not in {'execution_bundles','import_bundles'}}:
                raise ProductError('preparation_target_changed', '原准备已保留，但工作区或策略已变化，不能登记到新目标。', 409)
            rows = result.get('execution_bundles')
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
            return {'bundle_ids':ids, 'question_count_total':result.get('question_count_total'), 'API_requests':0}

    def _save_config(self, config):
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
        self._load()

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

    def _apply_import(self, owner, bundle, body, *, execution=None, workspace=None):
        execution=execution or self._gateway('execution')
        mapped = bool(bundle.get('work_store') and bundle.get('work_item_ids'))
        if mapped:
            preview=owner.import_preview({'bundle_id':body.get('bundle_id')})
            if body.get('preview_token') != preview.get('preview_token') or not preview.get('can_apply'):
                raise ProductError('preview_stale','请重新预览原接收目标再导入。',409)
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

    def _drafts(self, entity_id):
        path = self.ui_root/'src/generated/answers.json'
        if not path.is_file():
            return []
        document = json.loads(path.read_text(encoding='utf8'))
        return [run for run in document.get('runs', []) if run.get('entity_id') == entity_id]

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
        execution = self._gateway('execution')
        running = execution.active_references() if hasattr(execution, 'active_references') else execution.tasks(inspect_owner=False, limit=2000)
        if any(item.get('process_state') in {'running', 'starting', 'needs_original_inspection'}
               for item in running.get('items', running.get('tasks', []))):
            raise ProductError('execution_active', '运行期间不切换工作区；请等待当前公司安全结束。', 409)
        self._assert_inactive()
        self._save_config(config)
        return self._setup()

    def dispatch(self, method, target, body=None):
        """Return an HTTP status and JSON envelope; authentication is transport-owned."""
        started = time.monotonic()
        try:
            with self._lock:
                self._load()
                result = self._dispatch(method, target, {} if body is None else body)
            return 200, {'ok': True, 'data': redact(result), 'elapsed_ms': round((time.monotonic()-started)*1000)}
        except Exception as exc:
            known = isinstance(exc, ProductError) or hasattr(exc, 'code')
            return getattr(exc, 'status', 500) if known else 500, {'ok': False, 'error': {
                'code': getattr(exc, 'code', 'internal_error'),
                'message': str(exc)[:500] if known else '本地组件处理失败，请检查doctor与组件状态。',
                'details': redact(getattr(exc, 'details', {}))}}

    def _dispatch(self, method, target, body):
        parsed = urlsplit(target)
        path = parsed.path.removeprefix('/api/product/').rstrip('/')
        query = {k: values[-1] for k, values in parse_qs(parsed.query).items()}
        if not parsed.path.startswith('/api/product/'):
            raise ProductError('not_found', '未找到接口。', 404)
        if not isinstance(body, dict):
            raise ProductError('invalid_body', '请求内容必须是JSON对象。')
        if method == 'GET':
            if path == 'delivery/jobs':
                return self._delivery_jobs().list()
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
                    'read_has_model_calls': False}
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
                self._snapshots = {k: v for k, v in self._snapshots.items() if now-v['time'] < 900}
                token = query.get('snapshot_token')
                snapshot = None
                if token:
                    saved = self._snapshots.get(token)
                    if saved is None or saved['fingerprint'] != fingerprint:
                        raise ProductError('snapshot_expired', '筛选快照已过期或条件已变化，请从第一页刷新。', 409)
                    snapshot = saved['snapshot']
                elif offset:
                    raise ProductError('snapshot_required', '翻页须使用第一页返回的筛选快照。', 409)
                result = self._gateway('owner').search(selection['query'], limit, offset,
                    filters=filters, conditions=conditions or None, condition_combine=combine,
                    view=selection['view'], snapshot=snapshot)
                if isinstance(result, dict) and isinstance(result.get('snapshot'), dict):
                    if not token:
                        if len(self._snapshots) >= 128:
                            self._snapshots.pop(next(iter(self._snapshots)))
                        token = secrets.token_urlsafe(24)
                    self._snapshots[token] = {'snapshot': result['snapshot'], 'fingerprint': fingerprint, 'time': now}
                    result['snapshot_token'] = token
                return result
            if path == 'coverage':
                return self._gateway('owner').coverage()
            if path in {'entity', 'history', 'facts'}:
                entity_id = query.get('id', query.get('entity_id', ''))
                if not entity_id:
                    raise ProductError('entity_required', '请选择已注册公司。')
                result = getattr(self._gateway('owner'), path)(entity_id)
                if path == 'entity':
                    result['draft_runs'] = self._drafts(entity_id)
                    result['draft_source_label'] = '历史薄草稿，与当前owner观察分开'
                return result
            if path == 'universe':
                return self._gateway('owner').universe_list(query.get('universe_id', self.config['universe_id']))
            if path == 'delivery':
                return self._gateway('owner').delivery_status(query.get('package_id'))
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
                return getattr(self._gateway('owner'), action)(body)
            if path in {'tasks/preview', 'tasks/start'}:
                return getattr(self._gateway('execution'), path.split('/')[1])(body)
            match = re.fullmatch(r'tasks/([A-Za-z0-9_.-]{1,128})/(inspect|pause|resume|retire)', path)
            if match:
                if match[2] == 'retire' and body:
                    raise ProductError('invalid_body', '退役原启动引用无需额外参数。')
                return self._gateway('execution').control(*match.groups())
        raise ProductError('method_or_route_not_allowed', '该接口或方法不支持。', 405)
