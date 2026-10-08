"""Dynamically confirm concentrated independent-review findings; no production writes."""
import json
import os
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from iqs_evidence_lab import cli
from iqs_evidence_lab.hashing import read_json
from iqs_evidence_lab.semantic import check_sources

LAB=Path(os.environ['E97_LAB_ROOT'])
OUT=LAB/'.controller-followup'
OUT.mkdir(exist_ok=False)

def save(name,body):
    (OUT/name).write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def fixture(name,case):
    body=read_json(LAB/'fixtures/synthetic/FX-001.json')
    body.update(fixture_id='FX-998',title='Synthetic controller boundary, never human gold',why='Explicit acceptance boundary',case=case,expect=[])
    path=OUT/(name+'.json')
    path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return path

def replay_record(path,target_name,check):
    target=OUT/target_name
    code=cli.main(['replay','--input',str(path),'--output',str(target)])
    rows=[] if not target.exists() else [r for r in read_json(target/'diagnostics.json')['records'] if r['check']==check]
    return {'exit':code,'rows':rows,'published':target.exists()}

def test_custom_nonoverlapping_ranges_never_publish_consistency_pass():
    case={'expected':{'period':{'kind':'custom','year':2026,'start':'2026-01-01','end':'2026-03-31'}},
          'observed':{'period':{'kind':'custom','year':2026,'start':'2026-04-01','end':'2026-06-30'}}}
    result=replay_record(fixture('custom-period-input',case),'custom-period-output','semantic.period')
    save('custom-public-result.json',result)
    assert result['exit']==0 and result['rows']
    assert all(r['outcome']!='pass' for r in result['rows'])

def test_missing_historical_answer_hash_cannot_authorize_tampered_answer():
    body=read_json(LAB/'fixtures/historical/FX-032.json')
    body['provenance'].pop('answer_sha256')
    body['case']['answer']['score']=1
    body['case']['answer']['rationale']='Controller changed historical answer without authorization'
    path=OUT/'historical-missing-binding-input.json'
    path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target=OUT/'historical-missing-binding-output'
    code=cli.main(['replay','--input',str(path),'--output',str(target)])
    save('historical-missing-binding-result.json',{'exit':code,'published':target.exists(),
         'summary':read_json(target/'summary.json') if target.exists() else None})
    assert code==4 and not target.exists(), 'Modified historical answer without a binding was published'

def test_numeric_overflow_is_rejected_by_actual_fixture_replay():
    path=fixture('overflow-input',{'expected':{'direction':1},'observed':{'direction':'OVERFLOW_TOKEN'}})
    raw=path.read_text('utf-8').replace('"OVERFLOW_TOKEN"','1e400')
    path.write_text(raw,encoding='utf-8')
    result=replay_record(path,'overflow-output','semantic.direction')
    save('overflow-public-result.json',result)
    assert result['exit']==4 and not result['published'], 'Non-finite observed direction produced a public pass'

def test_unknown_source_window_does_not_mean_all_sources_conflict():
    case={'observed':{'period':'2026'},'sources':[{'url':'https://example.com/report-a','period':'2025'},
                                                  {'url':'https://example.com/report-b'}]}
    rows=check_sources(case)
    result=next(r for r in rows if r.check=='source.url_window')
    save('mixed-source-window.json',{'input':case,'result':asdict(result)})
    assert result.outcome=='abstain', 'Unknown source was excluded from an all-conflict judgment'

def test_every_synthetic_fx021_record_keeps_synthetic_source_type():
    doc=read_json(LAB/'.controller-fixture-FX-021/diagnostics.json')
    rows=[r for r in doc['records'] if r['support_source_type']!='synthetic']
    save('synthetic-source-kind.json',{'fixture_id':'FX-021','wrongly_labeled_records':rows})
    assert not rows, 'Synthetic duplicate-json record mislabeled as historical'

def test_draft_reference_fee_upper_bound_covers_its_generation_cap():
    config=read_json(LAB/'docs/handoff/EVID-LAB-01/experiment-proposal.config.json')
    cap=config['generation']['output_limit']
    formula=config['token_reference_formula']
    corrected=Decimal(0)
    for model in ('deepseek_flash','mimo_pro'):
        row=formula[model]
        corrected += (Decimal(row['input_cap_tokens_per_request'])*Decimal(str(row['uncached_input_usd_per_m']))
                    +Decimal(cap)*Decimal(str(row['output_usd_per_m'])))*Decimal(row['requests'])/Decimal(1000000)
    declared=Decimal(str(formula['worst_case_usd_total']))
    save('draft-fee-cap.json',{'generation_cap':cap,'formula_output_caps':[formula[m]['output_cap_tokens_per_request'] for m in ('deepseek_flash','mimo_pro')],
         'declared_usd':str(declared),'cap_bound_usd':str(corrected),'execution_enabled':config['execution_enabled']})
    assert declared>=corrected, 'Declared cost cap understates the frozen generation limit'
