"""Reviewer-authored mechanical rebind; no test or acceptance inference.

Coordinator may execute after editing its PWF. Attribution stays explicit.
Only this review's own output directory is written.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time

RUN=Path(__file__).resolve().parent;IQS=RUN.parents[1];PROJECTS=IQS.parent
REPOS={'QUERY-ENTITY-07':'iqs-query-identity-lab','SOURCE-TIME-07':'iqs-search-source-lab','RESUME-CHAOS-06':'iqs-resume-chaos-lab','REVIEW-CAL-06':'iqs-review-calibration-lab','RETRIEVAL-AUDIT-07':'iqs-search-annotation-lab'}
def sha(data):return hashlib.sha256(data).hexdigest()
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--executed-by',required=True);parser.add_argument('--output',default='current-bindings.json');args=parser.parse_args()
    target=(RUN/args.output).resolve();assert target.parent==RUN.resolve()
    packages=[]
    for package,repo in REPOS.items():
        root=PROJECTS/repo;head=git(root,'rev-parse','HEAD').decode().strip();assert not git(root,'status','--porcelain','--untracked-files=no').strip(),repo
        rows=[]
        for raw in git(root,'ls-files','-z').split(b'\0'):
            if not raw:continue
            rel=raw.decode('utf-8');data=(root/rel).read_bytes();rows.append({'path':rel,'raw_sha256':sha(data),'bytes':len(data)})
        assert head==git(root,'rev-parse','HEAD').decode().strip(),repo
        packages.append({'package_id':package,'repo':repo,'commit':head,'tracked_files':rows})
    docs=[]
    for rel in ('task_plan.md','progress.md','findings.md','docs/implementation/reviews/remaining-packages-live-status-2026-10-17.json','docs/implementation/experiments/remaining-packages-acceptance-2026-10-17.md'):
        raw=(IQS/rel).read_bytes();docs.append({'path':rel,'bytes':len(raw),'raw_sha256':sha(raw)})
    result={'protocol':'iqs.independent-mechanical-package-binding/1.0.0','script_author':'/root/remaining_acceptance18','executed_by':args.executed_by,'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'script_sha256':sha(Path(__file__).read_bytes()),'scope':'Mechanical source/PWF snapshot; independent acceptance verdict is a separate artifact.','packages':packages,'documents':docs}
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'packages':len(packages),'tracked_files':sum(len(p['tracked_files']) for p in packages),'documents':len(docs),'output':str(target)}))
