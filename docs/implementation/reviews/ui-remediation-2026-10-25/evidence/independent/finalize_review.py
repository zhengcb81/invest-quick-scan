"""Bind independent UI engineering review to the exact frozen source and test evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'runs/ui-remediation-2026-10-25'
HERE = Path(__file__).resolve().parent
UI = ROOT.parent/'iqs-question-bank-ui-lab'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def junit(path):
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=='testsuite' else list(root.iter('testsuite'))
    stats={key:sum(int(s.get(key,'0')) for s in suites) for key in ('tests','failures','errors','skipped')}
    assert stats['failures']==stats['errors']==stats['skipped']==0,stats
    return stats
declared={}
for relative,key in [('foundation/verification.json','source_sha256'),('content/implementation.json','files'),('product/source-lock.json','files')]:
    for path,sha in read(BASE/relative)[key].items():
        assert path not in declared,(path,relative)
        assert digest(UI/path)==sha,('source_changed_since_implementation_freeze',path)
        declared[path]=sha
assert len(declared)==17
sources=[{'repository':'iqs-question-bank-ui-lab','path':p,'sha256':sha} for p,sha in sorted(declared.items())]
for path in ['scripts/dashboard_owner.py','scripts/dashboard_execution.py','tests/test_dashboard_owner.py','tests/test_dashboard_execution.py']:
    sources.append({'repository':'invest-quick-scan','path':path,'sha256':digest(ROOT/path)})
assert len(sources)==21
negatives=read(HERE/'negative-results.json')
assert len(negatives)==6 and all(row['returncode']==0 for row in negatives)
frontend=junit(HERE/'final-frontend-tests.xml');backend=junit(HERE/'backend-tests.xml')
assert frontend['tests']==43 and backend['tests']==8
checks={p:digest(HERE/p) for p in ['review.md','finalize_review.py','review_negative.py','negative-results-before-fix.json','negative-results-root-clear-before-fix.json','negative-results.json','frontend-tests.xml','final-frontend-tests.xml','backend-tests.xml']}
report={
 'schema_version':'1.0.0','status':'passed','reviewer_agent':'/root/review_ui_whole',
 'recorded_at':datetime.now(timezone.utc).isoformat(),'review_scope':'UI engineering remediation of UX-01..10 and VD-01..12; source, original-owner integration and independent ESM boundaries',
 'source_count':len(sources),'source_sha256':sources,'open_findings':[],
 'closed_findings':['IR-01','IR-02','IR-03','IR-04','IR-05'],
 'tests':{'final_frontend':frontend,'backend_original_owner':backend,'independent_adversarial_and_return_scenarios':6},
 'evidence_sha256':checks,
 'browser_evidence_owner':'central controller /root; read browser-notes.md and browser-verification.json separately; not browser actions personally performed by reviewer',
 'limits':['No live paid model/search or production DB/settings/list/budget writes by this review',
 'No financial-accuracy, full-company completion or production owner admission qualification granted',
 'Mobile/tablet evidence uses real same-origin fixed iframes; child document scrollWidth, physical phone, outer browser resize, screen reader and 200% zoom not certified'],
 'cleanup':{'owned_temporary_database_root':'runs/urv','exists_after_review':(ROOT/'runs/urv').exists(),'source_copies_created':False,'paid_requests':0,'production_writes':0},
}
assert report['cleanup']['exists_after_review'] is False
(HERE/'final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'source_count':len(sources),'open_findings':[],'tests':report['tests']}))
