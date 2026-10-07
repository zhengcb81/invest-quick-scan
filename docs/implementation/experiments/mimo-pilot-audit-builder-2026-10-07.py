"""Create one blind source-support audit packet; no API, keys, or source changes."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b


def build(phase):
    parent=ROOT/'runs/mimo-pro-pilot-2026-10-07-01'
    roots=[parent] if phase=='primary' else [ROOT/'runs/mimo-pro-pilot-2026-10-07-thinking-all',
                                            ROOT/'runs/mimo-pro-pilot-2026-10-07-jsonoff']
    companies=json.loads((parent/'companies.json').read_text(encoding='utf-8'))
    qmap={q['question_id']:q for q in json.loads((parent/'questions.json').read_text(encoding='utf-8'))}
    packets={s:dict(company=c['canonical_name'],ticker=c['ticker'],questions=list(qmap.values()),
                   evidence=json.loads((parent/'evidence'/(s+'-targeted.json')).read_text(encoding='utf-8')),answers=[])
             for s,c in companies.items()}
    unique={};mapping=[]
    for run in roots:
        for f in sorted((run/'results').glob('*.json')):
            result=json.loads(f.read_text(encoding='utf-8'))
            if result['state']!='valid' or result['arm'].startswith('pilot-repeat.'):continue
            slug=next(s for s,c in companies.items() if c['entity_id']==result['entity_id'])
            for answer in result['answers']:
                sha=b.fingerprint(answer);uid='R'+b.fingerprint(dict(company=slug,answer=answer))[:16]
                if uid not in unique:
                    packets[slug]['answers'].append(dict(review_id=uid,answer_sha256=sha,answer=answer))
                    unique[uid]=sha
                mapping.append(dict(review_id=uid,answer_sha256=sha,run=run.name,chunk_id=result['chunk_id'],
                                    arm=result['arm'],question_id=answer['question_id']))
    import random
    for packet in packets.values():random.Random(97).shuffle(packet['answers'])
    b.write_json(parent/('blind-'+phase+'-source-support.json'),dict(schema='blind_pilot_source_support/1',
                 instructions='Only cited supplied snippets; judge exact issuer, time, units, scope, factual claim support and score basis. Unknown is valid, not wrong merely because unscored. No model/group labels. Not human/world gold.',
                 packets=list(packets.values())))
    b.write_json(parent/('blind-'+phase+'-private-mapping.json'),mapping)
    return dict(phase=phase,valid_answer_instances=len(mapping),unique_answers=len(unique),
                by_company={k:len(v['answers']) for k,v in packets.items()})


if __name__=='__main__':print(json.dumps(build(sys.argv[1])))
