"""Offline, reproducible arithmetic over diagnostic final answers, not web truth."""
import argparse
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import accuracy_pilot as p
import accuracy_assessment as a


def assess(root,amendments=True):
    ref=p.read(root/'reference.json');cov=p.read(root/'coverage.json');out=[]
    review=root/'independent-review-sidecar.json'
    if amendments and review.exists():
        for change in p.read(review)['amendments']:
            for variant in change['variants']:
                for qid in change['question_ids']:
                    cov[change['company']][variant][qid]+= [change['source_id']]
    for path in sorted((root/'results').glob('*.json')):
        r=p.read(path);gold=[q for q in ref['companies'][r['company']] if q['question_id'] in r['question_ids']]
        values=a.evaluate(r['answers'],gold,cov[r['company']][r['variant']])
        out.append(dict(**r,assessment=values))
    return out


def profiles(rows):
    groups=defaultdict(list)
    for row in rows:
        stage=row['arm'].split('.')[0]
        if stage=='pack':stage='pack_'+row['arm'].split('.')[2]
        groups[stage+'.'+row['route']+'.'+row['variant']].append(row)
    out={}
    for key,group in sorted(groups.items()):
        ev=[i for r in group for i in r['assessment']]
        out[key]=dict(calls_planned=len(group),calls_executed=sum(bool(r.get('receipt')) for r in group),
            valid_chunks=sum(r['state']=='valid' for r in group),not_run_chunks=sum(r['state'].startswith('not_run') for r in group),
            known_facts_planned=sum(i['expected_value'] is not None for i in ev),
            known_facts_answered=sum(i['answered'] and i['expected_value'] is not None for i in ev),
            numeric_exact_correct=sum(i['fact_correct'] for i in ev),citation_supported=sum(i['citation_supported'] for i in ev),
            answered_not_exact=sum(i['answered'] and not i['fact_correct'] for i in ev),
            unsupported_exact=sum(i['fact_correct'] and not i['citation_supported'] for i in ev),
            missing_items=sum(i['missing'] for i in ev),correct_roic_abstentions=sum(i['correct_abstention'] for i in ev),
            sum_request_wall_s=round(sum(r['wall_s'] for r in group),3),
            prompt_tokens=sum((r.get('receipt') or {}).get('usage',{}).get('prompt_tokens',0) for r in group),
            completion_tokens=sum((r.get('receipt') or {}).get('usage',{}).get('completion_tokens',0) for r in group))
    return out


def consensus(rows):
    indexes={(r['company'],r['route'],r['arm'].split('.')[0]):r for r in rows if r['variant']=='enhanced' and r['arm'].split('.')[0] in ['enhanced','repeat']}
    out=[]
    for slug in ['catl','cncb_h','alphabet']:
        for qid in ['F01','F02','F03','F04','F05','F06']:
            samples=[]
            for route in ['deepseek','minimax']:
                for stage in ['enhanced','repeat']:
                    r=indexes.get((slug,route,stage));row=next((x for x in (r or {}).get('answers',[]) if x['question_id']==qid),None)
                    ev=next((x for x in (r or {}).get('assessment',[]) if x['question_id']==qid),None)
                    samples.append(dict(route=route,stage=stage,answer=row,assessment=ev))
            signatures=[p.b.fingerprint({k:s['answer'][k] for k in ['status','value','unit','period','scope']}) if s['answer'] else None for s in samples]
            out.append(dict(company=slug,question_id=qid,all_four_exactly_agree=all(x is not None for x in signatures) and len(set(signatures))==1,
                all_four_cited_supported=all(s['assessment'] and s['assessment']['citation_supported'] for s in samples),samples=samples))
    return out


def report(main,followup,diagnostic):
    one=assess(main);two=assess(followup)
    roots=[main,followup,diagnostic]
    budgets=[p.b.Ledger(r).summary() for r in roots]
    return dict(version='accuracy-report/2',method='decimal tolerance + original pre-model source audit + explicitly appended independent corrections',
        main_profiles=profiles(one),followup_profiles=profiles(two),consensus=consensus(two),
        totals={k:round(sum(x[k] for x in budgets),6) for k in budgets[0]},
        result_input_hashes={label:{str(f.relative_to(r)):p.sha(f) for d in ['results','score-results'] for f in sorted((r/d).glob('*.json'))} for label,r in [('main',main),('followup',followup)]},
        score_results=[p.read(x) for x in sorted((followup/'score-results').glob('*.json'))],
        semantic_audit=p.read(followup/'semantic-review.json'),
        limitations=['Controller narrow numeric reference; not investment-score human gold','3 companies/15 facts, repeated samples correlated',
            'Citation coverage is manual per-source audit, not complete semantic automation','Numeric evaluator does not assess rationale semantics',
            'Origin-only URLs are not precise sources','Unknown processing attempt budget remains reserved','Request sum latency is not end-to-end company wall time'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--main',required=True);ap.add_argument('--followup',required=True);ap.add_argument('--diagnostic',required=True);ap.add_argument('--output',required=True);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    out=report(Path(args.main).resolve(),Path(args.followup).resolve(),Path(args.diagnostic).resolve());target=Path(args.output)
    if args.check:
        if p.read(target)!=out:raise ValueError('report_mismatch')
    else:p.b.write_json(target,out)
    print('accuracy-report/2: '+('matched' if args.check else 'written'))


if __name__=='__main__':main()
