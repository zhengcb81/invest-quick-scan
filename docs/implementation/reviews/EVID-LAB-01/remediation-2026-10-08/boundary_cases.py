"""Focused acceptance boundaries around this remediation; synthetic/private only."""
import json
import os
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest
from iqs_evidence_lab import cli
from iqs_evidence_lab.errors import NonFiniteJSONError
from iqs_evidence_lab.fixtures import archive_provenance_verifier
from iqs_evidence_lab.hashing import canonical_fingerprint, read_json, strict_loads
from iqs_evidence_lab.semantic import check_dimension

LAB = Path(os.environ['E97_LAB_ROOT'])
OUT = LAB / '.controller-extra'
OUT.mkdir(exist_ok=False)

def save(name, body):
    (OUT/name).write_text(json.dumps(body,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def test_custom_explicit_date_ranges_cannot_be_called_equal():
    expected={'kind':'custom','year':2026,'start':'2026-01-01','end':'2026-03-31'}
    observed={'kind':'custom','year':2026,'start':'2026-04-01','end':'2026-06-30'}
    result=check_dimension('period',expected,observed)
    save('custom-period.json',{'expected':expected,'observed':observed,'result':asdict(result)})
    assert result.outcome in {'fail','abstain'}, 'Explicit nonoverlapping date ranges passed'

def test_numeric_overflow_is_not_an_admissible_finite_json_value():
    text='{"value":1e400}'
    try:
        result=strict_loads(text)
    except NonFiniteJSONError:
        save('numeric-overflow.json',{'input':text,'rejected':True})
        return
    save('numeric-overflow.json',{'input':text,'rejected':False,'result_repr':repr(result)})
    pytest.fail('A strict finite JSON loader returned Infinity from numeric overflow')

def test_changing_both_retained_answer_and_self_hash_still_rejected():
    fixture=read_json(LAB/'fixtures/historical/FX-031.json')
    answer=fixture['case']['chunk']['answers'][0]
    answer['score']=1 if answer.get('score')!=1 else 9
    answer['rationale']='synthetic tampering; not a historical answer'
    fixture['provenance']['chunk_sha256']=canonical_fingerprint(fixture['case']['chunk'])
    problems=archive_provenance_verifier(fixture)
    save('forged-self-hash.json',{'problems':problems})
    assert problems, 'A new self digest defeated actual archive provenance'

def test_final_rename_failure_cleans_staging_and_same_path_is_retryable():
    target=OUT/'rename-failed'
    original=os.rename
    def fail(source,destination,*args,**kwargs):
        if Path(destination)==target: raise OSError('controller final rename failure')
        return original(source,destination,*args,**kwargs)
    with patch.object(os,'rename',fail):
        code=cli.main(['replay','--input','index','--output',str(target)])
    assert code==1 and not target.exists()
    assert not list(cli.STAGING_ROOT.glob('staging-*'))
    assert cli.main(['replay','--input','index','--output',str(target)])==0
    save('rename-failure.json',{'failed_exit':code,'staging_clean':True,'same_path_retry_exit':0})

def test_target_created_during_publish_is_preserved_on_this_windows_host():
    target=OUT/'publish-race'
    original=os.rename
    marker='pre-existing target belongs to another publisher'
    def race(source,destination,*args,**kwargs):
        if Path(destination)==target:
            target.mkdir()
            (target/'owner.txt').write_text(marker,encoding='utf-8')
        return original(source,destination,*args,**kwargs)
    with patch.object(os,'rename',race):
        code=cli.main(['replay','--input','index','--output',str(target)])
    assert code==3
    assert (target/'owner.txt').read_text('utf-8')==marker
    assert sorted(p.name for p in target.iterdir())==['owner.txt']
    assert not list(cli.STAGING_ROOT.glob('staging-*'))
    save('publish-race.json',{'exit':code,'prior_target_preserved':True,'staging_clean':True,'platform':os.name})
