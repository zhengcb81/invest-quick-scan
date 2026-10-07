"""Offline B01 provenance/archival helpers. No credentials or network."""
import argparse
import hashlib
import json
from pathlib import Path

import batching_benchmark as b
import batching_benchmark_report as report


def replay_inputs(run):
    companies=json.loads((run/'companies.json').read_text(encoding='utf-8'))
    qmap={q['question_id']:q for q in json.loads((run/'questions.json').read_text(encoding='utf-8'))}
    # Legacy probe profiles reconstructed explicitly; all actual payload hashes
    # must match. Do not claim the initial orchestrator's source was archived.
    old=b.SYSTEM.replace('"status":"insufficient_evidence",\n"score":null,"confidence":"low","rationale":"证据不足的具体原因",',
        '"status":"scored|insufficient_evidence|not_applicable|unknown",\n"score":1到10的整数或null,"confidence":"high|medium|low","rationale":"<=100字",')
    old=old.replace('以上仅结构示意；status只能为scored/insufficient_evidence/not_applicable/unknown，confidence只能为high/medium/low。\n','')
    old=old.replace('scored的score为1到10整数且必须有非空事实claims及对应证据。','scored必须有非空事实claims及对应证据。')
    profiles={'v1_v2':old,'v3_v4':b.SYSTEM,'v5':b.SYSTEM,'v6':b.SYSTEM+b.SCOPED_RULES}
    verified=[]
    ledger=b.Ledger(run)
    if ledger.summary()['unresolved_attempts']:raise ValueError('unresolved_before_archive')
    for aid,event in ledger.reserved.items():
        if event['kind']!='model':continue
        slug=next(s for s,c in companies.items() if c['entity_id']==event['entity_id'])
        c=companies[slug];identity={k:v for k,v in c.items() if k not in ('issuer_domains','aliases','name')}
        variant=event['arm'].rsplit('.',1)[1]
        evidence=json.loads((run/'evidence'/(slug+'-'+variant+'.json')).read_text(encoding='utf-8'))
        questions=[qmap[q] for q in event['question_ids']]
        matched=None
        for version,system in profiles.items():
            data=dict(identity=identity,information_cutoff=b.CUTOFF,untrusted_evidence=evidence,questions=questions)
            if version in ('v5','v6'):
                data.update(required_answer_count=len(questions),exact_ordered_question_ids=event['question_ids'],
                    completion_check='输出前核对answers长度等于required_answer_count，并逐项核对以上全部题号；缺证据的题也必须有完整unknown项。')
            prompt=json.dumps(data,ensure_ascii=False,separators=(',',':'))
            if b.fingerprint(dict(system=system,prompt=prompt))!=event['prompt_sha256']:continue
            body=dict(model=event['requested_model'],messages=[dict(role='system',content=system),dict(role='user',content=prompt)],**event['parameters'])
            if (b.fingerprint(body)!=event['request_body_sha256']
                    or b.fingerprint(evidence)!=event['evidence_sha256']
                    or b.fingerprint(questions)!=event['questions_sha256']):
                raise ValueError('actual_payload_binding_mismatch')
            matched=version;break
        if matched is None:raise ValueError('prompt_profile_replay_mismatch')
        verified.append(dict(attempt_id=aid,version=matched,prompt_sha256=event['prompt_sha256'],body_sha256=event['request_body_sha256']))
    return dict(model_attempts=len(verified),all_matched=True,verified=verified,
        reconstructed_legacy_probe_profiles=True,initial_orchestrator_source_snapshot='not_saved; original hash only'),profiles


def write_jsonl(path,rows):
    path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n' for x in rows),encoding='utf-8')


def archive(run,dest):
    run=run.resolve();dest=dest.resolve()
    if not run.is_relative_to(b.ROOT/'runs') or run==b.ROOT/'runs':raise ValueError('not_owned_run')
    allowed=b.ROOT/'docs/implementation/experiments/artifacts'
    if not dest.is_relative_to(allowed) or dest==allowed:raise ValueError('not_owned_archive')
    if (run/'orchestrator.lock').exists():raise ValueError('active_run')
    if dest.exists():raise ValueError('archive_already_exists')
    replay,profiles=replay_inputs(run)
    analysis=report.summarize(run)
    sources=[]
    # Source pointers/fragment hashes only: no source snippets in durable data.
    for p in sorted((run/'evidence').glob('*.json')):
        if any(token in p.name for token in ('query-','-rejected','candidate-')):continue
        items=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(items,list):continue
        sources.append(dict(pool=p.name,file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            content_sha256=b.fingerprint(items),sources=[{**{k:x.get(k) for k in ('source_id','url','title','published_at','retrieved_at','document_family','source_scope')},
                'snippet_sha256':hashlib.sha256(x.get('snippet','').encode()).hexdigest(),'snippet_chars':len(x.get('snippet',''))} for x in items]))
    results=[]
    for p in sorted((run/'results').glob('*.json')):
        r=json.loads(p.read_text(encoding='utf-8'))
        r.pop('parse_excerpt',None)
        results.append(r)
    dest.mkdir(parents=True)
    b.write_json(dest/'analysis.json',analysis)
    b.write_json(dest/'provenance-check.json',replay)
    b.write_json(dest/'prompt-profiles.json',profiles)
    b.write_json(dest/'source-index.json',sources)
    write_jsonl(dest/'results.jsonl',results)
    write_jsonl(dest/'ledger.jsonl',b.Ledger(run).events)
    b.write_json(dest/'blocks.json',[json.loads(p.read_text(encoding='utf-8')) for p in sorted((run/'blocks').glob('*.json'))])
    metadata={}
    for name in ('run-manifest.json','runtime-manifest.json','questions.json','companies.json',
                 'budget-original.json','budget.json','extension-preregistration.json','model-input-lock.json',
                 'model-input-lock-v2.json','model-input-lock-v3.json','model-input-lock-v4.json','model-input-lock-v5.json',
                 'targeted-input-lock.json','scoped-input-lock.json','cache-resume-proof.json',
                 'blind-claim-private-mapping.json','blind-extension-private-mapping.json',
                 'blind-candidate-private-mapping.json','answer-audit-summary.json'):
        p=run/name
        if p.exists():metadata[name]=json.loads(p.read_text(encoding='utf-8'))
    b.write_json(dest/'inputs-manifest.json',metadata)
    owned=[str(p.relative_to(run)) for p in sorted(run.rglob('*')) if p.is_file()]
    # Cleanup itself is manual, with absolute-root/path verification; no broad
    # auto-delete or external directory access here.
    b.write_json(dest/'archive-manifest.json',dict(created_at=b.now(),run_path=str(run),scope='minimal normalized experiment data; no source snippets/keys/raw API responses/reasoning',
        source_context_after_review='disposable; payload replay verified before removal; future fresh retrieval is not identical input',
        retained_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.iterdir())},
        owned_run_files=owned,budget=analysis['budget']))
    return dict(files=len(list(dest.iterdir())),results=len(results),verified_model_payloads=replay['model_attempts'],budget=analysis['budget'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True);parser.add_argument('--dest',required=True)
    args=parser.parse_args();print(json.dumps(archive(Path(args.run),Path(args.dest)),ensure_ascii=False))


if __name__=='__main__':main()
