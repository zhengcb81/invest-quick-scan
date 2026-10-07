"""Offline final statistics for the three-company adaptive experiment."""
import collections
import json
import statistics
from pathlib import Path

import batching_benchmark as b
import batching_benchmark_report as report


def collect(root):
    result=report.summarize(root)
    rows={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (root/'results').glob('*.json')}
    blocks=[json.loads(p.read_text(encoding='utf-8')) for p in (root/'blocks').glob('*.json')]
    return dict(root=root,report=result,rows=rows,blocks=blocks)


def aggregate(data,blocks):
    chunks=[data['rows'][c] for block in blocks for c in block['chunks']]
    costs=[report.token_cost(r.get('receipt') or {},r['route'],data['routes']) for r in chunks]
    reason_counts=[(r.get('receipt') or {}).get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens') for r in chunks]
    valid=[r for r in chunks if r['state']=='valid']
    return dict(requested=sum(x['requested'] for x in blocks),valid_rows=sum(len(r['answers']) for r in valid),
                raw_strict_rows=sum(len(r['answers']) for r in valid if not r.get('normalization')),
                scored=sum(q['status']=='scored' for r in valid for q in r['answers']),
                median_company_seconds=round(statistics.median(x['wall_s'] for x in blocks),3),
                sum_block_seconds=round(sum(x['wall_s'] for x in blocks),3),
                reference_usd=round(sum(x['reference_usd'] or 0 for x in costs),8),
                input_tokens=sum(x['input_tokens'] or 0 for x in costs),output_tokens=sum(x['output_tokens'] or 0 for x in costs),
                cached_tokens=sum(x['cached_tokens'] or 0 for x in costs),cached_usage_missing=sum(x['cached_tokens'] is None for x in costs),
                reasoning_tokens_reported=sum(n for n in reason_counts if type(n) is int),
                reasoning_usage_missing=sum(type(n) is not int for n in reason_counts),
                failures=dict(collections.Counter(r.get('parse_error') or r.get('exception_type') or r['state'] for r in chunks if r['state']!='valid')),
                actual_models=sorted({(r.get('receipt') or {}).get('actual_model','unknown') for r in chunks}),
                finish_reasons=dict(collections.Counter((r.get('receipt') or {}).get('finish_reason') for r in chunks)))


def main():
    roots=[b.ROOT/'runs'/name for name in ('mimo-pro-pilot-2026-10-07-01','mimo-pro-pilot-2026-10-07-thinking-all','mimo-pro-pilot-2026-10-07-jsonoff')]
    datasets=[collect(root) for root in roots]
    for d in datasets:
        snapshot=d['root']/'route-snapshot.json'
        d['routes']=json.loads(snapshot.read_text(encoding='utf-8')) if snapshot.exists() else b.ROUTES
    main_data,thinking,diagnostic=datasets
    matrix={}
    for route in ('mimo','mimo_pro','deepseek'):
        matrix[route]={str(g):aggregate(main_data,[x for x in main_data['blocks'] if x['stage']=='pilot-matrix' and x['route']==route and x['group_size']==g]) for g in (1,5,10)}
    equal_cap={}
    for route in ('mimo','mimo_pro','deepseek','minimax'):
        off=aggregate(thinking,[x for x in thinking['blocks'] if x['stage']=='paired-off' and x['route']==route])
        on_data=main_data if route=='mimo_pro' else thinking
        on_stage='pilot-thinking' if route=='mimo_pro' else 'paired-on'
        on=aggregate(on_data,[x for x in on_data['blocks'] if x['stage']==on_stage and x['route']==route])
        equal_cap[route]=dict(off=off,on=on)
    diag={r:aggregate(diagnostic,[x for x in diagnostic['blocks'] if x['route']==r+'_nojson']) for r in ('mimo','mimo_pro')}
    repeat={r:aggregate(main_data,[x for x in main_data['blocks'] if x['stage']=='pilot-repeat' and x['route']==r]) for r in ('mimo','mimo_pro','deepseek')}
    budgets=[d['report']['budget'] for d in datasets]
    out=dict(schema='mimo_pilot_final/1',created_at=b.now(),companies=3,questions_each=10,matrix=matrix,equal_cap_thinking=equal_cap,
             json_off_adaptive=diag,independent_repeat_g10=repeat,
             aggregate_budget={k:round(sum(d[k] for d in budgets),6) for k in budgets[0]},
             model_token_reference_usd=round(sum(x['reference_usd'] for d in datasets for x in d['report']['by_model'].values()),8),
             scope='single-day three-company source-context experiment; not production scan or factual gold',
             pricing_snapshot='docs/implementation/experiments/mimo-pilot-pricing-2026-10-07.json',
             pricing_note='peak/undiscounted frozen reference; DeepSeek off-peak and MiniMax discount references may be half; package actual cash unknown')
    b.write_json(roots[0]/'final-statistics.json',out)
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
