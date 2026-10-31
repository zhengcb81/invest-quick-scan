from pathlib import Path
import json,hashlib,subprocess,os
root=Path.cwd();out=root/'runs/close-support31/wiring-independent';snap=out/'snapshot-round01'
pins=json.loads((snap/'wiring-source-pins.json').read_bytes());checks=[]
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
for row in pins['artifacts']:
 original=subprocess.check_output(['git','-C',str(root.parent/row['repo']),'show',row['commit']+':'+row['source']],env=env)
 target=snap/(row['target'] if row['target'].startswith('scripts/') else 'ui/'+row['target'])
 expected=original.replace(b'from iqs_time_semantics.',b'from .') if row['transform']=='absolute package imports to relative only' else original
 check={'path':row['target'],'source_git_blob_sha_matches_pin':hashlib.sha256(original).hexdigest()==row['source_sha256'],'target_sha_matches_pin':hashlib.sha256(target.read_bytes()).hexdigest()==row['target_sha256'],'transformation_exact':target.read_bytes()==expected}
 assert all(v for k,v in check.items() if k!='path'),check
 checks.append(check)
lock=root/'questions/releases/locks/modrel_997312ab027300898b17a8943efaf95f3531c764f2ed5d3877c4954507b010df.json'
bound=json.loads((snap/'scripts/iqs_temporal_vendor/question-bindings.json').read_bytes());assert bound['release_lock_sha256']==hashlib.sha256(lock.read_bytes()).hexdigest()
expected={q['question_id']:{'definition_sha256':q['definition_sha256'],'module_id':m['module_id'],'module_release_id':json.loads(lock.read_bytes())['release_id']} for m in json.loads(lock.read_bytes())['modules'] for q in m['question_semantics']}
assert bound['bindings']==expected
(out/'round01-pins.json').write_text(json.dumps({'artifacts':checks,'question_bindings_exact_to_real_lock':True,'question_count':len(expected)},indent=2),encoding='utf8');print(json.dumps({'pinned_artifacts_verified':len(checks),'question_bindings':len(expected)}))
