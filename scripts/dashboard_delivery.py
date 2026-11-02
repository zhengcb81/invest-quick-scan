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


_EXPORT = r'''
import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
def offline(event,args):
    if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}: raise RuntimeError('network_forbidden')
sys.addaudithook(offline)
from src.utils.quick_scan_refresh_inspect import delivery_scope_projection
try:
    result = delivery_scope_projection(pathlib.Path(sys.argv[2]), json.load(sys.stdin))
    print(json.dumps(result, ensure_ascii=False))
except Exception:
    print(json.dumps({'error_code':'original_delivery_export_rejected','API_requests':0}));raise SystemExit(2)
'''


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


def read_work_scope(*, bundle, config, call, runtime):
    """Observe native work rows without requiring today's spending policy."""
    ledger, request = _scope_inputs(bundle)
    root = Path(config['stockqa_root'])
    result = call([str(config.get('stockqa_python', sys.executable)), '-B', '-X', 'utf8',
                   '-c', _EXPORT, str(root), str(ledger)], root, runtime,
                  input_value={'entity_id': request['entity_id'], 'question_ids': request['question_ids'],
                      'scope_bindings': request.get('scope_bindings'),
                      **({'confirmation_id': bundle['confirmation_id']} if bundle.get('confirmation_id') else {}),
                      'read_only_scope': True})
    return {**result, 'protocol': 'stockqa.read_only_work_projection/1.0.0',
            'reservation_created': False}


def export_deliveries(*, bundle_id, bundle, config, state_root, call, inspection_work_items):
    key = bundle_id
    # Reading an already sealed result does not require a new spending grant,
    # runtime model config or permission to dispatch again.
    root=Path(config.get('stockqa_root',''))
    if not root.is_absolute() or not (root/'src/utils/quick_scan_work_store.py').is_file():
        raise DashboardExecutionError('delivery_not_configured','原交付代码根缺失。',409)
    for field in ('manifest',):
        if not Path(bundle.get(field,'')).is_absolute() or not Path(bundle[field]).is_file():
            raise DashboardExecutionError('delivery_not_configured','缺少原只读交付输入。',409,{'missing':[field]})
    ledger, request = _scope_inputs(bundle)
    confirmation = bundle.get('confirmation_id')
    if not isinstance(confirmation, str) or not confirmation:
        raise DashboardExecutionError('delivery_original_scope_unavailable', '缺少原confirmation，不能用最新一代工作替代原交付范围。', 409)
    interpreter=str(config.get('stockqa_python',sys.executable))
    state_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='delivery-read-',dir=state_root) as runtime:
        # Each original sealed package is independently exportable. Unfinished
        # questions remain not_exportable, without holding completed answers.
        result=call([interpreter,'-B','-X','utf8','-c',_EXPORT,
            str(root),str(ledger)],root,runtime,input_value={
                'entity_id': request['entity_id'], 'question_ids': request['question_ids'],
                'scope_bindings': request.get('scope_bindings'), 'confirmation_id': confirmation})
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
