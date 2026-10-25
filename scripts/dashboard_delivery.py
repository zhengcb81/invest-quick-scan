"""Publish original sealed outbox bytes for the local UI; never seal or score."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

try:
    from .dashboard_execution import DashboardExecutionError
except ImportError:
    from dashboard_execution import DashboardExecutionError


_EXPORT = r'''
import hashlib,json,pathlib,sys
sys.path.insert(0,sys.argv[1])
def offline(event,args):
    if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}: raise RuntimeError('network_forbidden')
sys.addaudithook(offline)
from src.utils.quick_scan_work_store import QuickScanWorkStore
request=json.load(sys.stdin)
try:
    path=pathlib.Path(sys.argv[2])
    if not path.is_file(): raise ValueError('ledger_missing')
    store=QuickScanWorkStore(path);items=[]
    for work_id in request['work_ids']:
        work=store.get_item(work_id)
        if work['entity_id']!=request['entity_id'] or work['question_id'] not in request['question_ids']:
            raise ValueError('original_work_scope_mismatch')
        row=store.get_result_delivery(work_id)
        if row is None or row['state'] not in {'ready','delivered','send_uncertain'} or row['package_bytes'] is None:
            items.append({'work_item_id':work_id,'status':'not_exportable','reason':None if row is None else row.get('block_code') or row['state']})
            continue
        raw=row['package_bytes']
        items.append({'work_item_id':work_id,'status':'exportable','observation_id':row['observation_id'],
            'package_id':row['package_id'],'package_json':raw.decode('utf8'),
            'package_bytes_sha256':hashlib.sha256(raw).hexdigest(),'delivery_state':row['state']})
    print(json.dumps({'items':items,'API_requests':0,'network_calls':0},ensure_ascii=False))
except Exception:
    print(json.dumps({'error_code':'original_delivery_export_rejected','API_requests':0}));raise SystemExit(2)
'''


def _immutable(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream: stream.write(raw)
    except FileExistsError:
        if path.read_bytes()!=raw:
            raise DashboardExecutionError('delivery_archive_changed','原封存包归档已变化，不能覆盖。',409)


def export_deliveries(execution, payload):
    key,bundle=execution._select(payload)
    # Reading an already sealed result does not require a new spending grant,
    # runtime model config or permission to dispatch again.
    root=Path(execution.config.get('stockqa_root',''))
    if not root.is_absolute() or not (root/'src/utils/quick_scan_work_store.py').is_file():
        raise DashboardExecutionError('delivery_not_configured','原交付代码根缺失。',409)
    for field in ('admission_config','inspection_request','manifest'):
        if not Path(bundle.get(field,'')).is_absolute() or not Path(bundle[field]).is_file():
            raise DashboardExecutionError('delivery_not_configured','缺少原只读交付输入。',409,{'missing':[field]})
    admission=json.loads(Path(bundle['admission_config']).read_text(encoding='utf-8-sig'))
    for field in ('work_store','budget_policy_file'):
        if not Path(admission.get(field,'')).is_absolute() or not Path(admission[field]).is_file():
            raise DashboardExecutionError('delivery_not_configured','原账本或策略不存在；不会创建空库。',409)
    request=json.loads(Path(bundle['inspection_request']).read_text(encoding='utf-8-sig'))
    if request.get('entity_id')!=bundle.get('entity_id'):
        raise DashboardExecutionError('delivery_entity_mismatch','交付请求与原实体不一致。',409)
    interpreter=str(execution.config.get('stockqa_python',sys.executable))
    command=[interpreter,'-B','-X','utf8','-m','src.utils.quick_scan_refresh_inspect_cli',
        '--ledger',admission['work_store'],'--policy',admission['budget_policy_file'],
        '--request',bundle['inspection_request'],'--schema-version',bundle.get('inspection_schema_version','1.0.0')]
    if bundle.get('inspection_schema_version') in {'1.4.0','1.5.0'}:
        command.extend(['--admission-config',bundle['admission_config']])
    execution.state_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='delivery-read-',dir=execution.state_root) as runtime:
        inspection=execution._call(command,root,runtime)
        rows=execution.inspection_work_items(inspection)
        if (inspection.get('protocol')!='stockqa.refresh_inspection/'+bundle.get('inspection_schema_version','1.0.0')
            or inspection.get('reservation_created') is not False or not isinstance(rows,list) or not rows
            or any(not isinstance(row,dict) or row.get('status') not in {'result_ready','delivered'} for row in rows)):
            raise DashboardExecutionError('delivery_not_ready','原执行范围尚未全部ready；不会重新封存或发模型请求。',409)
        work_ids=[row.get('work_item_id') for row in rows]
        if any(not isinstance(work,str) for work in work_ids) or len(set(work_ids))!=len(work_ids):
            raise DashboardExecutionError('delivery_work_mapping_missing','原检查器未提供唯一逐题work引用。',409)
        result=execution._call([interpreter,'-B','-X','utf8','-c',_EXPORT,
            str(root),str(admission['work_store'])],root,runtime,input_value={
            'entity_id':bundle['entity_id'],'question_ids':request['question_ids'],'work_ids':work_ids})
    from frozen_release_projection import create_projection
    manifest=json.loads(Path(bundle['manifest']).read_text(encoding='utf-8-sig'))
    release=create_projection(manifest,root=Path(execution.config['iqs_release_root']))
    raw_release=(json.dumps(release,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf8')
    release_sha=hashlib.sha256(raw_release).hexdigest()
    archive=execution.state_root/'deliveries'
    release_path=archive/('release-'+release_sha+'.json')
    _immutable(release_path,raw_release)
    registrations={};items=[]
    for row in result['items']:
        public={k:v for k,v in row.items() if k!='package_json'}
        if row['status']=='exportable':
            raw=row['package_json'].encode('utf8');digest=hashlib.sha256(raw).hexdigest()
            if digest!=row['package_bytes_sha256']:
                raise DashboardExecutionError('delivery_byte_hash_mismatch','原封存包字节哈希不匹配。',409)
            name='outbox-'+digest[:48]
            path=archive/(digest+'.json');_immutable(path,raw)
            registrations[name]={'entity_id':bundle['entity_id'],'package':str(path.resolve()),'package_sha256':digest,
                'release':str(release_path.resolve()),'release_sha256':release_sha,
                'work_store':str(admission['work_store']), 'work_item_ids':{row['observation_id']:row['work_item_id']}}
            public['bundle_id']=name
        items.append(public)
    return {'status':'exported' if len(registrations)==len(items) else 'partial','import_bundles':registrations,
        'items':items,'API_requests':0,'model_calls':0,'financial_accuracy_proven':False,
        'notice':'只复制原outbox已封存的精确字节；未重新评分、补齐或改写原包。'}
