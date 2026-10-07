"""One-off, pre-model source selection; no network/keys/financial inference."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b

DROP={
 'catl':{'TF07abbf98ed':'other issuer prospectus','TFc336884e37':'2021 finance proposal, outside current comparison',
         'TF4e927ed593':'glossary only','TF5a98cc6cae':'garbled title/identity boilerplate',
         'BF98fc690f80':'empty cover','BF3ceb8bcd1e':'empty cover','BF3d52f4b5f4':'contents only'},
 'cncb_h':{'TFc4d0fb4c18':'CITIC00267, different issuer','TF3d3ff03e18':'CITIC00267, different issuer',
           'BF59ca7eb4f0':'disclaimer only','BF6191467041':'no description'},
 'alphabet':{'BF44323f28a1':'privacy/navigation','BF8d38ad9976':'privacy/navigation',
             'BF4323abc071':'mislabelled sitemap/historical founders text'},
}

def select(run):
    if (run/'pilot-selection.json').exists():
        raise ValueError('selection_already_frozen')
    ledger=b.Ledger(run)
    if ledger.summary()['model_requests'] or ledger.summary()['unresolved_attempts']:
        raise ValueError('selection_after_send_or_unknown')
    changes=[]
    for slug in DROP:
        p=run/'evidence'/(slug+'-targeted.json')
        before=p.read_bytes();items=json.loads(before)
        (run/'evidence'/(slug+'-raw-before-selection.json')).write_bytes(before)
        chosen=[];rejected=[];size=2
        for item in items:
            reason=DROP[slug].get(item['source_id'])
            if 'network of automated tools' in item['snippet'] or 'undeclared automated tools' in item['snippet']:
                reason='SEC crawler access boilerplate, not company evidence'
            if reason:
                rejected.append({'source_id':item['source_id'],'reason':reason})
                continue
            parsed=urlsplit(item['url']);host=parsed.hostname or ''
            if host in ('www.hkexnews.hk','www1.hkexnews.hk'):
                host='hkexnews.hk'
            item={**item,'document_family':hashlib.sha256((host+parsed.path).encode()).hexdigest()[:16],
                  'source_scope':'third_party_credit_rating' if '评级' in item['title'] else 'issuer_disclosure_not_independently_confirmed',
                  'published_at':item.get('published_at')}
            n=len(json.dumps(item,ensure_ascii=False,separators=(',',':')))
            if size+n+1>16000:
                rejected.append({'source_id':item['source_id'],'reason':'frozen context character cap'})
                continue
            chosen.append(item);size+=n+1
        b.write_json(p,chosen)
        prefix='' if slug=='cncb_h' else slug+'-'
        lock_path=run/(prefix+'targeted-input-lock.json')
        old=lock_path.read_bytes();(run/(prefix+'targeted-input-lock-before-selection.json')).write_bytes(old)
        new=json.loads(old);new.update(file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
          preselection_file_sha256=hashlib.sha256(before).hexdigest(),selection='pre-model fixed exclusion; no answers seen')
        b.write_json(lock_path,new)
        changes.append({'company':slug,'input_count':len(items),'retained':len(chosen),
                        'rejected':rejected,'context_chars':size,'file_sha256':new['file_sha256']})
    result={'created_at':b.now(),'before_first_model_http':True,'changes':changes,
            'selection_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    b.write_json(run/'pilot-selection.json',result)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    run=Path(sys.argv[1]).resolve()
    if run.parent!=ROOT/'runs' or not run.name.startswith('mimo-pro-pilot-'):
        raise ValueError('not_owned_root')
    select(run)
