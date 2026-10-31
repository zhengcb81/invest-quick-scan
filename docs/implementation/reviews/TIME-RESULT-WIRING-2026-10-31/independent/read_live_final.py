from pathlib import Path
import json,hashlib,urllib.request,copy
from datetime import datetime,timezone
root=Path.cwd();out=root/'runs/close-support31/wiring-independent';proof=json.loads((root/'runs/close-support31/real-view-proof.json').read_bytes());cfg=json.loads((root/'config/dashboard.local.json').read_bytes());workspace=Path(cfg['workspace_root']).resolve()
def sha(b):return hashlib.sha256(b).hexdigest()
def tree():
 rows=[(str(p.relative_to(workspace)).replace('\\','/'),sha(p.read_bytes())) for p in sorted(workspace.rglob('*')) if p.is_file()]
 return {'file_count':len(rows),'aggregate_sha256':sha(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode())}
def get(path):
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766/'+path,headers={'Accept':'application/json'}),timeout=30) as response:return response.read()
def read(path):
 x=json.loads(get('api/product/'+path));assert x['ok'] is True;return x['data']
before=tree();rows=[]
for item in proof['companies']:
 eid=item['entity_id'];old=read('entity?id='+eid);new=read('entity-view?id='+eid);a=copy.deepcopy(old);b=copy.deepcopy(new['entity']);a.pop('generated_at_utc',None);b.pop('generated_at_utc',None);assert a==b
 fields=[r for g in old['groups'] for r in g['fields']];s=new['temporal_shadow'];assert s['current_context_verified'] is False and s['reuse_authorized'] is False and s['production_reuse_applied'] is False
 assert all(r['current_context_verified'] is False and r['reuse_authorized'] is False for r in s['records'])
 rows.append({'entity_id':eid,'record_count':len(fields),'question_count':len(set(r['question_id'] for r in fields)),'legacy_and_new_entity_equal_except_generation':True,'clock_only_records':sum('clock_only_assessment' in r for r in s['records']),'captured_context_records':sum('captured_context_assessment' in r for r in s['records']),'unbound_records':sum('time_policy_definition_unbound' in r['reason_codes'] for r in s['records']),'no_reuse_permission':True})
static=[]
for rel in ['ui/result_trust_host.js','vendor/result-trust/result_trust_panel.js']:
 body=get(rel);expected=(root.parent/'iqs-question-bank-ui-lab/src/app'/rel).read_bytes();assert body==expected,rel
 static.append({'path':rel,'http_body_sha256':sha(body),'matches_installed_committed_ui_bytes':True})
after=tree();assert before==after
result={'iqs_C':'c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2','ui_C':'03d6b9aa3d45011f09bc77ef69e62b4a1d21e00e','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'origin':'http://127.0.0.1:8766','get_only':True,'companies':rows,'served_static_files':static,'native_workspace_before':before,'native_workspace_after':after,'native_workspace_unchanged':True,'answer_bodies_saved':False,'csrf_values_read_or_printed':False,'paid_api_calls':0,'production_source_written':False}
(out/'final-live-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'company_counts':[(r['record_count'],r['question_count'],r['clock_only_records'],r['unbound_records']) for r in rows],'native_file_count':before['file_count'],'native_unchanged':True,'served_static_matches':2}))
