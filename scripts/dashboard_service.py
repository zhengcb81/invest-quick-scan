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
    'package_sha256', 'release_sha256', 'work_item_ids'}
CONFIG_KEYS = PATH_KEYS | {'schema_version', 'universe_id', 'execution_bundles', 'import_bundles',
                          'timeout_seconds', 'workspace_kind', 'workspace_label'}


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
        'execution_bundles': {}, 'import_bundles': {}, 'timeout_seconds': 60}


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
    return result


class DashboardService:
    def __init__(self, root=ROOT, config_path=None, ui_root=None, owner_factory=None, execution_factory=None):
        self.root = Path(root).resolve()
        self.config_path = Path(config_path or self.root/'config/dashboard.local.json').resolve()
        self.ui_root = Path(ui_root or self.root.parent/'iqs-question-bank-ui-lab').resolve()
        self.csrf_token = secrets.token_urlsafe(32)
        self._lock = threading.RLock()
        self._owner_factory, self._execution_factory = owner_factory, execution_factory
        self._config_revision = None
        self._owner = self._execution = None
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
        self.config = validate_config(supplied, self.root)
        self._config_revision = revision
        self._owner = self._execution = None
        self._snapshots.clear()

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
        running = self._gateway('execution').tasks()
        if any(item.get('process_state') in {'running', 'starting', 'needs_original_inspection'}
               for item in running.get('items', running.get('tasks', []))):
            raise ProductError('execution_active', '运行期间不切换工作区；请等待当前公司安全结束。', 409)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.config_path.with_name(self.config_path.name+'.'+secrets.token_hex(8)+'.tmp')
        try:
            temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
            os.replace(temporary, self.config_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        self._load()
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
                return self._gateway('execution').tasks()
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
            if path in {'universe/preview', 'universe/apply', 'import/preview', 'import/apply'}:
                action = path.replace('/', '_')
                if path == 'import/apply':
                    bundle = self.config['import_bundles'].get(body.get('bundle_id'), {})
                    if bundle.get('work_store') and bundle.get('work_item_ids'):
                        # Receiver identity comes from the independent original owner,
                        # never from an incoming ACK or generated model answer.
                        preview = self._gateway('owner').import_preview({'bundle_id': body.get('bundle_id')})
                        if body.get('preview_token') != preview.get('preview_token') or not preview.get('can_apply'):
                            raise ProductError('preview_stale', '请重新预览原接收目标再导入。', 409)
                        status = self._gateway('owner').status()
                        if not status.get('available') or not status.get('store_id'):
                            raise ProductError('receiver_unavailable', '无法核实原StockWiki接收目标。', 409)
                        target = {'component': 'StockWiki', 'namespace': 'quick_scan', 'store_id': status['store_id']}
                        source = 'dashboard-owner-status:' + self.config['workspace_root']
                        self._gateway('execution').bind_delivery_consumer(bundle, target, source)
                result = getattr(self._gateway('owner'), action)(body)
                if path == 'import/apply' and isinstance(result.get('receipt'), dict):
                    bundle = self.config['import_bundles'].get(body.get('bundle_id'), {})
                    if bundle.get('work_store') and bundle.get('work_item_ids'):
                        try:
                            result['ack_reconciliation'] = self._gateway('execution').acknowledge_delivery(bundle, result['receipt'])
                        except Exception as exc:
                            result['ack_reconciliation'] = {'status': 'pending', 'error_code': getattr(exc, 'code', 'ack_reconciliation_failed'),
                                'notice': 'StockWiki已产生回执；原StockQA未确认，重试导入会复用原回执。'}
                    else:
                        result['ack_reconciliation'] = {'status': 'not_configured',
                            'notice': 'StockWiki已入库；此包未登记原StockQA账本引用，不能称作执行器已交付。'}
                return result
            if path in {'tasks/preview', 'tasks/start'}:
                return getattr(self._gateway('execution'), path.split('/')[1])(body)
            match = re.fullmatch(r'tasks/([A-Za-z0-9_.-]{1,128})/(inspect|pause|resume)', path)
            if match:
                return self._gateway('execution').control(*match.groups())
        raise ProductError('method_or_route_not_allowed', '该接口或方法不支持。', 405)
