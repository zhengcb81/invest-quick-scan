"""Publish original sealed outbox bytes for the local UI; never seal or score."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

try:
    from .dashboard_errors import DashboardExecutionError
except ImportError:
    from dashboard_errors import DashboardExecutionError


DELIVERY_REQUEST_PROTOCOL = 'stockqa.delivery_scope_request/1.0.0'
DELIVERY_RESPONSE_PROTOCOL = 'stockqa.delivery_scope_response/1.0.0'
DELIVERY_COMMAND = 'src.utils.quick_scan_delivery_scope_cli'


def _immutable(path, raw, *, expected_digest=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    derived = expected_digest is not None
    if derived and (hashlib.sha256(raw).hexdigest()!=expected_digest
        or path.name not in {expected_digest+'.json','release-'+expected_digest+'.json'}):
        raise DashboardExecutionError('delivery_byte_hash_mismatch','原字节与派生缓存的内容地址不匹配。',409)
    if path.exists():
        if path.read_bytes()==raw:
            return
        if not derived:
            raise DashboardExecutionError('delivery_archive_changed','原封存包归档已变化，不能覆盖。',409)
    temporary = None
    try:
        # Publish only complete bytes. A crash writing a cache must not leave a
        # truncated final name that permanently blocks the original outbox.
        with tempfile.NamedTemporaryFile(prefix=path.name+'.', suffix='.tmp', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if derived:
            # This is a reproducible cache of already verified original bytes,
            # not authority. Repair a legacy torn file at this exact address.
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes()!=raw:
                    raise DashboardExecutionError('delivery_archive_changed','原封存包归档已变化，不能覆盖。',409)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _scope_inputs(bundle):
    for field in ('admission_config', 'inspection_request'):
        path = Path(bundle.get(field, ''))
        if not path.is_absolute() or not path.is_file():
            raise DashboardExecutionError('delivery_not_configured', '缺少原只读交付输入。', 409, {'missing': [field]})
    admission = json.loads(Path(bundle['admission_config']).read_text(encoding='utf-8-sig'))
    ledger = Path(admission.get('work_store', ''))
    if not ledger.is_absolute() or not ledger.is_file():
        raise DashboardExecutionError('delivery_not_configured', '原账本不存在；不会创建空库。', 409)
    request = json.loads(Path(bundle['inspection_request']).read_text(encoding='utf-8-sig'))
    if request.get('entity_id') != bundle.get('entity_id'):
        raise DashboardExecutionError('delivery_entity_mismatch', '交付请求与原实体不一致。', 409)
    return ledger, request


def describe_delivery_scope(bundle):
    """Describe the immutable scope behind a registered delivery."""
    ledger, request = _scope_inputs(bundle)
    manifest = Path(bundle.get('manifest', ''))
    if not manifest.is_absolute() or not manifest.is_file():
        raise DashboardExecutionError('delivery_not_configured', '缺少原manifest，不能核实交付范围。', 409)
    question_ids = request.get('question_ids')
    if (not isinstance(question_ids, list) or not question_ids
            or any(not isinstance(qid, str) or not qid for qid in question_ids)
            or len(question_ids) != len(set(question_ids))):
        raise DashboardExecutionError('delivery_work_mapping_missing', '原交付题目范围无效。', 409)
    return {
        'entity_id': bundle['entity_id'], 'work_store': str(ledger.resolve()),
        'manifest': str(manifest.resolve()), 'question_ids': sorted(question_ids),
        'confirmation_id': bundle.get('confirmation_id'),
        'scope_bindings': request.get('scope_bindings') or {
            qid: {'scope': 'entity', 'scope_id': bundle['entity_id']} for qid in question_ids},
    }


def _project_delivery(*, config, ledger, request, call, operation, confirmation=None):
    root = Path(config.get('stockqa_root', ''))
    if not root.is_absolute() or not root.is_dir():
        raise DashboardExecutionError('delivery_not_configured', '原交付代码根缺失。', 409)
    command = [str(config.get('stockqa_python', sys.executable)), '-B', '-X', 'utf8',
               '-m', DELIVERY_COMMAND, '--ledger', str(ledger)]
    scope = {'entity_id': request['entity_id'], 'question_ids': request['question_ids'],
             'scope_bindings': request.get('scope_bindings')}
    if confirmation is not None:
        scope['confirmation_id'] = confirmation
    response = call(command, root, root, input_value={
        'protocol': DELIVERY_REQUEST_PROTOCOL, 'operation': operation, 'scope': scope,
    })
    result = response.get('result') if isinstance(response, dict) else None
    if (not isinstance(result, dict) or response.get('protocol') != DELIVERY_RESPONSE_PROTOCOL
        or response.get('status') != 'ok' or response.get('operation') != operation
        or any(type(response.get(counter)) is not int or response[counter] != 0
               for counter in ('API_requests', 'network_calls'))
        or any(not isinstance(result.get(field), list)
               or not all(isinstance(row, dict) for row in result[field])
               for field in ('items', 'work_items', 'consumers'))):
        raise DashboardExecutionError('owner_delivery_contract_invalid', '原交付查询响应与公开协议不一致。', 409)
    return {**result, 'API_requests': 0, 'network_calls': 0}


def read_delivery_receivers(*, bundle, config, call, state_root=None):
    """Read the receiver of the original confirmation without binding it."""
    ledger, request = _scope_inputs(bundle)
    confirmation = bundle.get('confirmation_id')
    if not isinstance(confirmation, str) or not confirmation:
        raise DashboardExecutionError('delivery_original_scope_unavailable', '缺少原confirmation，不能猜测原交付目标。', 409)
    return _project_delivery(config=config, ledger=ledger, request=request, call=call,
                             operation='receivers', confirmation=confirmation)


def read_work_scope(*, bundle, config, call, runtime=None):
    """Observe native work rows without requiring today's spending policy."""
    ledger, request = _scope_inputs(bundle)
    result = _project_delivery(config=config, ledger=ledger, request=request, call=call,
                               operation='inspect', confirmation=bundle.get('confirmation_id') or None)
    return {**result, 'protocol': 'stockqa.read_only_work_projection/1.0.0',
            'reservation_created': False}


def export_deliveries(*, bundle_id, bundle, config, state_root, call, inspection_work_items):
    # Reading an already sealed result does not require a new spending grant,
    # runtime model config or permission to dispatch again.
    for field in ('manifest',):
        if not Path(bundle.get(field,'')).is_absolute() or not Path(bundle[field]).is_file():
            raise DashboardExecutionError('delivery_not_configured','缺少原只读交付输入。',409,{'missing':[field]})
    ledger, request = _scope_inputs(bundle)
    confirmation = bundle.get('confirmation_id')
    if not isinstance(confirmation, str) or not confirmation:
        raise DashboardExecutionError('delivery_original_scope_unavailable', '缺少原confirmation，不能用最新一代工作替代原交付范围。', 409)
    # Each original sealed package is independently exportable. Unfinished
    # questions remain not_exportable, without holding completed answers.
    result = _project_delivery(config=config, ledger=ledger, request=request, call=call,
                               operation='export', confirmation=confirmation)
    from frozen_release_projection import create_projection
    manifest=json.loads(Path(bundle['manifest']).read_text(encoding='utf-8-sig'))
    release=create_projection(manifest,root=Path(config['iqs_release_root']))
    raw_release=(json.dumps(release,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf8')
    release_sha=hashlib.sha256(raw_release).hexdigest()
    archive=state_root/'deliveries'
    release_path=archive/('release-'+release_sha+'.json')
    _immutable(release_path,raw_release,expected_digest=release_sha)
    registrations={};items=[]
    for row in result['items']:
        public={k:v for k,v in row.items() if k!='package_json'}
        if row['status']=='exportable':
            raw=row['package_json'].encode('utf8');digest=hashlib.sha256(raw).hexdigest()
            if digest!=row['package_bytes_sha256']:
                raise DashboardExecutionError('delivery_byte_hash_mismatch','原封存包字节哈希不匹配。',409)
            name='outbox-'+digest[:48]
            path=archive/(digest+'.json');_immutable(path,raw,expected_digest=digest)
            registrations[name]={'entity_id':bundle['entity_id'],'package':str(path.resolve()),'package_sha256':digest,
                'release':str(release_path.resolve()),'release_sha256':release_sha,
                'work_store':str(ledger), 'work_item_ids':{row['observation_id']:row['work_item_id']}}
            public['bundle_id']=name
        items.append(public)
    referenced=[row['question_id'] for row in items if row['status']=='referenced']
    return {'status':'exported' if len(registrations)+len(referenced)==len(items) else 'partial','import_bundles':registrations,
        'referenced_question_ids':referenced,
        'items':items,'API_requests':0,'model_calls':0,'financial_accuracy_proven':False,
        'notice':'只复制原outbox已封存的精确字节；未重新评分、补齐或改写原包。'}
