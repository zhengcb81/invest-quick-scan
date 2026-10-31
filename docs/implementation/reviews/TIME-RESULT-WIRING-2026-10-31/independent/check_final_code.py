from pathlib import Path
import json,subprocess,hashlib,os
root=Path.cwd();out=root/'runs/close-support31/wiring-independent';C='c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2';U='03d6b9aa3d45011f09bc77ef69e62b4a1d21e00e';M='7b420282320da7f1b44455d71447201dbf505b0b27876dc4a4cc8bd91fc9fe2a'
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
def git(repo,*a):return subprocess.check_output(['git','-C',str(repo),*a],env=env)
def sha(b):return hashlib.sha256(b).hexdigest()
path='docs/implementation/reviews/TIME-RESULT-WIRING-2026-10-31/installed-code-manifest.json';raw=git(root,'show',C+':'+path);assert sha(raw)==M
manifest=json.loads(raw);checks=[]
for row in manifest['files']:
 repo=root if row['repo']=='invest-quick-scan' else root.parent/row['repo'];commit=C if row['repo']=='invest-quick-scan' else U
 blob=git(repo,'show',commit+':'+row['path']);assert sha(blob)==row['sha256'] and len(blob)==row['bytes'],row['path'];work=(repo/row['path']).read_bytes();assert work==blob or work.replace(b'\r\n',b'\n')==blob,row['path']
 checks.append({'repo':row['repo'],'path':row['path'],'git_sha256_matches':True,'bytes_match':True,'installed_worktree_exact':work==blob,'installed_worktree_eol_normalized_matches':work.replace(b'\r\n',b'\n')==blob})
pins=json.loads(git(root,'show',C+':docs/implementation/time-result-source-pins.json'));verified=[]
for row in pins['artifacts']:
 blob=git(root.parent/row['repo'],'show',row['commit']+':'+row['source']);assert sha(blob)==row['source_sha256']
 target=root/row['target'] if row['target'].startswith('scripts/') else root.parent/'iqs-question-bank-ui-lab'/row['target']
 result=target.read_bytes();assert sha(result)==row['target_sha256']
 if row['transform']=='absolute package imports to relative only':assert result==blob.replace(b'from iqs_time_semantics.',b'from .')
 elif row['transform']=='none':assert result==blob
 else:
  assert row['source']=='src/result_trust_panel.js'
  old='缺少信息日期，原规则无法判定'.encode();new='原规则缺少信息日期或有效期；所示资料日期仍按原值保留'.encode()
  if result!=blob.replace(old,new):
   import difflib
   delta=''.join(difflib.unified_diff(blob.decode().splitlines(keepends=True),result.decode().splitlines(keepends=True)))
   (out/'result-wording-diff.patch').write_text(delta,encoding='utf8')
   changed=[x for x in difflib.ndiff(blob.decode().splitlines(),result.decode().splitlines()) if x.startswith(('- ','+ '))];assert len(changed)==2 and all('missing_date:' in x for x in changed),changed
  verified.append({'target':row['target'],'source_sha_matches':True,'target_sha_matches':True,'only_missing_date_wording_changed':True});continue
 verified.append({'target':row['target'],'source_sha_matches':True,'target_sha_matches':True,'transform_exact':True})
obj={'iqs_code_commit':C,'ui_code_commit':U,'manifest_git_blob_sha256':M,'manifest_files':checks,'pins':verified,'iqs_head_at_check':git(root,'rev-parse','HEAD').decode().strip(),'ui_head_at_check':git(root.parent/'iqs-question-bank-ui-lab','rev-parse','HEAD').decode().strip()}
(out/'final-code-checks.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'manifest_files':len(checks),'pure_vendor_pins':len(verified),'iqs_C':C,'ui_C':U}))
