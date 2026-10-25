"""Compare pre-expansion code and final code against unchanged real bank data."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types

EVIDENCE=Path(__file__).resolve().parent
ROOT=EVIDENCE.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
baseline='f606fa9^'
if '--baseline' in sys.argv:
 for name in ('module_contract','routing','scoring_rubrics','question_sets'):
  relative='scripts/'+name+'.py'
  source=subprocess.check_output(['git','-C',str(ROOT),'show',baseline+':'+relative])
  module=types.ModuleType(name);module.__file__=str(ROOT/relative);sys.modules[name]=module
  exec(compile(source,str(ROOT/relative),'exec'),module.__dict__)
import question_sets as qs
import module_contract as mc
import module_registry as registry
profile=qs.read_json(ROOT/'examples/profile.json')
profiles={'example':profile,
 'bank':dict(profile,company_type='bank',industry_modules=[],cycle_sensitive=False,diagnostic_modules=[]),
 'cyclical':dict(profile,cycle_sensitive=True,cycle_position='trough')}
out={'cases':{}}
with tempfile.TemporaryDirectory(prefix='compat-',dir=EVIDENCE) as temporary:
 for label,p in profiles.items():
  for mode in ('quick','full'):
   target=Path(temporary)/(label+'-'+mode)
   qs.compose(p,mode,target)
   manifest=qs.read_json(target/'manifest.json')
   rows=[dict(q,status='scored',score=8) for q in manifest['questions']]
   out['cases'][label+'-'+mode]={
    'manifest_sha256':hashlib.sha256((target/'manifest.json').read_bytes()).hexdigest(),
    'questions_sha256':hashlib.sha256((target/'questions.json').read_bytes()).hexdigest(),
    'method_id':manifest['method_id'],'question_count':len(manifest['questions']),
    'summary_sha256':mc.digest(qs.summarize(rows,'core-constructs-v1'))}
 stats=qs.validate_library()
 out['library_shared_fields']={k:v for k,v in stats.items() if k not in ('core_constructs','common_questions')}
 out['library_added_fields']={k:stats[k] for k in ('core_constructs','common_questions') if k in stats}
print(json.dumps(out,ensure_ascii=False))
