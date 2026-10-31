from pathlib import Path
import sys,json,shutil,hashlib
root=Path.cwd();out=root/'runs/close-support31/wiring-independent';snap=out/'snapshot-round02'
sys.path[:0]=[str(snap/'scripts'),str(snap/'tests'),str(root/'tests'),str(root.parent/'StockWiki'),str(root)]
from test_dashboard_temporal import specimen,view
import dashboard_temporal as temporal
cases=[]
for key in ['groups_null','fields_null','execution_text']:
 d,raw=specimen()
 if key=='groups_null':d['groups']=None
 elif key=='fields_null':d['groups'][0]['fields']=None
 else:
  raw['payload']['execution']='legacy-unknown';raw['payload_sha256']=temporal._sha(raw['payload']);d['groups'][0]['fields'][0]['payload_sha256']=raw['payload_sha256']
 v=view(d,raw);assert v['entity'] is d and v['temporal_shadow']['reuse_authorized'] is False
 cases.append({'case':key,'readable':True,'records':v['temporal_shadow']['records'],'reason_codes':v['temporal_shadow'].get('reason_codes',[])})
(out/'backend-edge-probes-round02.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf8')
ui=out/'host-dom-round02'
if not (ui/'src/app').exists():shutil.copytree(root.parent/'iqs-question-bank-ui-lab/src/app',ui/'src/app')
shutil.copytree(snap/'ui/src/app',ui/'src/app',dirs_exist_ok=True)
(ui/'package.json').write_text('{"type":"module"}',encoding='utf8')
print(json.dumps({'readable_scenarios':len(cases)}))
