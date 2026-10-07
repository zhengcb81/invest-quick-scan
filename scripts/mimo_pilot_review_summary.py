"""Offline join of blinded judgments to immutable actual answers, never a gold score."""
import argparse
import collections
import json
from pathlib import Path
import batching_benchmark as b


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Recompute and compare the retained join without modifying it.')
    args=parser.parse_args()
    archive=b.ROOT/'docs/implementation/experiments/artifacts/mimo-pro-pilot-2026-10-07-01'
    metadata=json.loads((archive/'inputs-manifest.json').read_text(encoding='utf-8'))
    records=[]
    for phase,expected in [('primary',196),('extension',130)]:
        report=b.ROOT/('docs/implementation/reviews/B01/mimo-pilot-'+phase+'-source-support-2026-10-07.json')
        obj=json.loads(report.read_text(encoding='utf-8'))
        if obj['summary'].get('complete') is False:raise ValueError('audit_not_complete')
        judgments={j['review_id']:j for j in obj['judgments']}
        mapping=metadata['blind-'+phase+'-private-mapping.json']
        if len(judgments)!=expected or len(judgments)!=len(obj['judgments']) or set(judgments)!={x['review_id'] for x in mapping}:
            raise ValueError('audit_duplicate_missing_or_extra')
        originals={}
        for run_name in {x['run'] for x in mapping}:
            source=b.ROOT/'docs/implementation/experiments/artifacts'/run_name/'results.jsonl'
            for line in source.read_text(encoding='utf-8').splitlines():
                result=json.loads(line)
                for answer in result.get('answers',[]):originals[(run_name,result['chunk_id'],answer['question_id'])]=answer
        for link in mapping:
            answer=originals[(link['run'],link['chunk_id'],link['question_id'])]
            judgment=judgments[link['review_id']]
            if b.fingerprint(answer)!=link['answer_sha256'] or judgment['answer_sha256']!=link['answer_sha256']:
                raise ValueError('judgment_answer_hash_mismatch')
            if judgment['claim_support'] not in ('supported','partial','unsupported','no_claims') or judgment['score_basis'] not in ('supported','insufficient','not_scored'):
                raise ValueError('judgment_enum')
            if (answer['status']=='scored')==(judgment['score_basis']=='not_scored'):raise ValueError('judgment_scored_state_mismatch')
            records.append(dict(phase=phase,arm=link['arm'],question_id=link['question_id'],status=answer['status'],
                                score=answer['score'],**judgment))
    grouped=collections.defaultdict(list)
    for item in records:
        parts=item['arm'].split('.')
        grouped[(parts[0],parts[2],parts[3])].append(item)
    rows=[]
    for (stage,route,group),items in sorted(grouped.items()):
        rows.append(dict(stage=stage,route=route,group=group,n=len(items),
            claims=dict(collections.Counter(x['claim_support'] for x in items)),basis=dict(collections.Counter(x['score_basis'] for x in items)),
            scored=sum(x['status']=='scored' for x in items),high_scores=sum(x['score'] is not None and x['score']>=8 for x in items),
            high_score_basis_supported=sum(x['score'] is not None and x['score']>=8 and x['score_basis']=='supported' for x in items),
            unscored_with_claim_issues=sum(x['status']!='scored' and x['claim_support'] in ('partial','unsupported') for x in items)))
    out=dict(schema='mimo_pilot_source_support_join/1',created_at=b.now(),reviewed=len(records),expected=326,
        claims=dict(collections.Counter(x['claim_support'] for x in records)),basis=dict(collections.Counter(x['score_basis'] for x in records)),
        score_scopes='supported means limited source-backed direction/band, never validated exact 1-10 score',
        method_note='Two blinded agents reviewed disjoint primary/extension partitions using the same instructions; inter-rater calibration not measured. Pro on/off crosses these partitions.',
        not_human_or_world_gold=True,by_arm=rows)
    target=b.ROOT/'docs/implementation/reviews/B01/mimo-pilot-source-support-join-2026-10-07.json'
    if args.check:
        retained=json.loads(target.read_text(encoding='utf-8'))
        out['created_at']=retained['created_at']
        if out!=retained:raise ValueError('retained_join_statistics_mismatch')
    else:
        b.write_json(target,out)
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
