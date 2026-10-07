"""Pure offline reporting of immutable pilot blocks and per-HTTP receipts."""
import argparse
import collections
import json
import statistics
import tempfile
import re
from pathlib import Path

import batching_benchmark as b


def token_cost(receipt, route):
    usage=receipt.get('usage') or {}
    inp,out=usage.get('prompt_tokens'),usage.get('completion_tokens')
    if type(inp) is not int or type(out) is not int or inp<0 or out<0:
        return dict(input_tokens=None,output_tokens=None,reference_usd=None,cached_tokens=None)
    nested=usage.get('prompt_tokens_details') or {}
    cached=usage.get('prompt_cache_hit_tokens',nested.get('cached_tokens'))
    if type(cached) is not int or not 0<=cached<=inp:cached=None
    cfg=b.ROUTES[route]
    cost=((inp-(cached or 0))*cfg['input_rate']+(cached or 0)*cfg['cache_rate']+out*cfg['output_rate'])/1e6
    return dict(input_tokens=inp,output_tokens=out,cached_tokens=cached,
                reference_usd=round(cost,8),pricing='peak_or_undiscounted_reference_not_invoice')


def summarize(run):
    results={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (run/'results').glob('*.json')}
    blocks=[json.loads(p.read_text(encoding='utf-8')) for p in (run/'blocks').glob('*.json')]
    table=[]
    for block in blocks:
        if 'chunks' not in block:continue
        rows=[row for chk in block['chunks'] for row in results[chk].get('answers',[])]
        receipts=[results[c].get('receipt') or {} for c in block['chunks']]
        costs=[token_cost(r,block['route']) for r in receipts]
        x={k:block[k] for k in ('arm','stage','company','route','group_size','requested','valid_rows','scored','wall_s')}
        x.update(evidence_variant=block.get('evidence_variant'),evidence_sha256=block.get('evidence_sha256'),
                 question_ids=block.get('question_ids'),prompt_profile=block.get('prompt_profile','v5'))
        x.update(statuses=dict(collections.Counter(r['status'] for r in rows)),
                 missing_or_invalid=block['requested']-len(rows),
                 normalization_chunks=sum(bool(results[c].get('normalization')) for c in block['chunks']),
                 input_tokens=sum(c['input_tokens'] or 0 for c in costs),output_tokens=sum(c['output_tokens'] or 0 for c in costs),
                 cached_tokens=sum(c['cached_tokens'] or 0 for c in costs),
                 reference_usd=round(sum(c['reference_usd'] or 0 for c in costs),6),
                 usage_missing=sum(c['reference_usd'] is None for c in costs),
                 raw_json_strict_rows=sum(len(results[c].get('answers',[])) for c in block['chunks'] if not results[c].get('normalization')),
                 supplemental_valid_rows=sum(len(results[c].get('item_inspection',{}).get('answers',[])) for c in block['chunks']),
                 rows_by_id={r['question_id']:r for r in rows})
        table.append(x)
    for x in table:
        comparable=('stage','company','route','evidence_variant','evidence_sha256','question_ids','prompt_profile')
        base=next((y for y in table if y['group_size']==1 and all(y[k]==x[k] for k in comparable)),None)
        if base and x is not base:
            paired=[(row,base['rows_by_id'][qid]) for qid,row in x['rows_by_id'].items() if qid in base['rows_by_id']]
            scored=[(a['score'],z['score']) for a,z in paired if a['status']==z['status']=='scored']
            x.update(paired_rows=len(paired),status_agreement=sum(a['status']==z['status'] for a,z in paired),
                     scored_pair_n=len(scored),scored_mae=round(statistics.mean(abs(a-z) for a,z in scored),3) if scored else None,
                     scored_within_one=sum(abs(a-z)<=1 for a,z in scored),
                     speedup_vs_baseline=round(base['wall_s']/x['wall_s'],2),
                     reference_cost_ratio=round(x['reference_usd']/base['reference_usd'],3) if base['reference_usd'] else None)
    for x in table:
        x.pop('rows_by_id')
    repair_chains=[]
    for parent in blocks:
        if parent.get('stage')!='minimax-small5':continue
        follow=next((z for z in blocks if z.get('stage')=='minimax-repair' and z['company']==parent['company']),None)
        initial=[row for c in parent['chunks'] for row in results[c].get('answers',[])]
        recovered=[row for c in parent['chunks'] for row in results[c].get('item_inspection',{}).get('answers',[])]
        repaired=[row for c in (follow['chunks'] if follow else []) for row in results[c].get('answers',[])]
        first_ids={r['question_id'] for r in initial+recovered}
        new_ids={r['question_id'] for r in repaired}
        if first_ids & new_ids:raise ValueError('repair_repeated_valid_item')
        if not (first_ids|new_ids)<=set(parent['question_ids']):raise ValueError('repair_extra_item')
        repair_chains.append(dict(company=parent['company'],requested=parent['requested'],
            strict_initial_rows=len(initial),initial_rows_with_item_validation=len(first_ids),
            retried_items=follow['requested'] if follow else 0,successful_repair_items=len(new_ids),
            final_valid_rows=len(first_ids|new_ids),total_wall_s=round(parent['wall_s']+(follow['wall_s'] if follow else 0),3),
            remaining_invalid=len(set(parent['question_ids'])-(first_ids|new_ids))))
    events=[json.loads(l) for l in (run/'attempts.jsonl').read_text(encoding='utf-8').splitlines()]
    reserve={e['attempt_id']:e for e in events if e['event']=='reserved'}
    finished={e['attempt_id']:e for e in events if e['event']=='finished'}
    ledger=b.Ledger(run)
    by_model={}
    for route in b.ROUTES:
        costs=[token_cost(finished.get(a,{}),route) for a,r in reserve.items() if r.get('route')==route]
        by_model[route]=dict(http_requests=len(costs),input_tokens=sum(c['input_tokens'] or 0 for c in costs),
                             output_tokens=sum(c['output_tokens'] or 0 for c in costs),cached_tokens=sum(c['cached_tokens'] or 0 for c in costs),
                             reference_usd=round(sum(c['reference_usd'] or 0 for c in costs),6),usage_missing=sum(c['reference_usd'] is None for c in costs))
    return dict(schema='b01_improved_report/1',created_at=b.now(),budget=ledger.summary(),
                by_model=by_model,blocks=sorted(table,key=lambda x:x['arm']),repair_chains=repair_chains,
                factual_accuracy='inconclusive_pending_independent_source_and_score_gold',
                price_note='Public-price reference and conservative upper bounds, not actual invoice; MiniMax package quota cannot be inferred from tokens.')


def main():
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--run');group.add_argument('--archive')
    args=p.parse_args()
    if args.archive:obj=summarize_archive(Path(args.archive).resolve())
    else:
        run=Path(args.run).resolve();obj=summarize(run);b.write_json(run/'analysis.json',obj)
    print(json.dumps({k:v for k,v in obj.items() if k!='blocks'},ensure_ascii=False))


def summarize_archive(path):
    """Recompute minimal archive stats offline; source context is unnecessary."""
    manifest=json.loads((path/'archive-manifest.json').read_text(encoding='utf-8'))
    required={'analysis.json','results.jsonl','ledger.jsonl','blocks.json','inputs-manifest.json'}
    if not required<=set(manifest['retained_files']):raise ValueError('archive_missing_files')
    for name,sha in manifest['retained_files'].items():
        if Path(name).name!=name or b.hashlib.sha256((path/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('archive_path_or_hash_mismatch')
    meta=json.loads((path/'inputs-manifest.json').read_text(encoding='utf-8'))
    lock=meta.get('model-input-lock-v5.json')
    if lock and lock['routes_sha256']!=b.fingerprint(b.ROUTES):raise ValueError('historical_pricing_route_drift')
    with tempfile.TemporaryDirectory(dir=b.ROOT) as tmp:
        run=Path(tmp);(run/'results').mkdir();(run/'blocks').mkdir()
        seen=set()
        for line in (path/'results.jsonl').read_text(encoding='utf-8').splitlines():
            item=json.loads(line);cid=item['chunk_id']
            if not isinstance(cid,str) or not re.fullmatch(r'CHK_[A-Za-z0-9]{1,64}',cid) or cid in seen:
                raise ValueError('archive_chunk_invalid_or_duplicate')
            seen.add(cid);b.write_json(run/'results'/(cid+'.json'),item)
        for i,block in enumerate(json.loads((path/'blocks.json').read_text(encoding='utf-8'))):
            b.write_json(run/'blocks'/(str(i)+'.json'),block)
        (run/'attempts.jsonl').write_bytes((path/'ledger.jsonl').read_bytes())
        result=summarize(run)
    expected=json.loads((path/'analysis.json').read_text(encoding='utf-8'))
    for key in ('budget','by_model','blocks','repair_chains'):
        if result[key]!=expected[key]:raise ValueError('archive_statistics_mismatch')
    result['archive_statistics_verified']=True
    return result


if __name__=='__main__':main()
