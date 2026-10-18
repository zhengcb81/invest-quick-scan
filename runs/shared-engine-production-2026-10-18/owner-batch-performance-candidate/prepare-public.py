"""Replay the final complete source closure only after every source/overlay hash matches.

No legacy runtime inventory fallback. All writes stay in this owned runtime.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent
lock=json.loads((r/'evidence/final-composite-source-lock.json').read_text(encoding='utf8'))
prefixes={'qa':['src','schemas','tests'],'sw':['stockwiki','schemas','tests'],'company':['src','schemas'],'bridge':['src','schemas'],'iqs':['scripts','schemas','questions','references']}
origins={'qa':r.parents[3]/'StockQAbyLLM','sw':r.parents[3]/'StockWiki','company':r.parents[3]/'iqs-company-agent-lab','bridge':r.parents[3]/'iqs-agent-runtime-lab','iqs':r.parents[2]}
for component,origin in origins.items():
 actual=set(filter(None,subprocess.check_output(['git','-C',str(origin),'ls-files','-z','--',*prefixes[component]]).decode('utf8').split('\0')))
 expected={row['path'] for row in lock['source_files'] if row['component']==component and not (component=='iqs' and row['path'].startswith('docs/'))}
 if actual!=expected:raise RuntimeError('tracked source closure changed; rebase required: '+component)
for row in lock['source_files']:
 src=Path(row['origin'])
 if hashlib.sha256(src.read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('source changed; rebase required: '+row['component']+'/'+row['path'])
for row in lock['overlays']:
 if hashlib.sha256((r/row['component']/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('frozen overlay changed: '+row['path'])
for row in lock['source_files']:
 dest=r/'runtime'/row['component']/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(row['origin']),dest)
for row in lock['overlays']:
 dest=r/'runtime'/row['component']/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/row['component']/row['path'],dest)
(r/'runtime/guard').mkdir(exist_ok=True);shutil.copy2(r/'guard/write_audit.py',r/'runtime/guard/sitecustomize.py')
(r/'runtime/tmp').mkdir(exist_ok=True)
print('exact complete source closure prepared:',len(lock['source_files']),'original files;',len(lock['overlays']),'explicit overlays')
