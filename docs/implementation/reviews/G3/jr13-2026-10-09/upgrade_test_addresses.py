"""Upgrade only approved unit fixtures, retaining address/hash/scope negatives."""
from pathlib import Path
import ast
import hashlib
import io
import re
import tokenize

IQS=Path(__file__).resolve().parents[5]
SW=IQS/"runs/r13a/sw"

def normalize(text):
    lines=text.splitlines(keepends=True)
    offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    changes=[]
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type!=tokenize.STRING:continue
        try:value=ast.literal_eval(token.string)
        except (ValueError,SyntaxError):continue
        if isinstance(value,str) and re.fullmatch(r"(?:obs|pkg|itm)_[A-Za-z0-9_]+",value) and not re.fullmatch(r"(?:obs|pkg|itm)_[a-f0-9]{64}",value):
            kind=value.split('_',1)[0]
            address=kind+'_'+hashlib.sha256(value.encode()).hexdigest()
            begin=offsets[token.start[0]-1]+token.start[1]
            end=offsets[token.end[0]-1]+token.end[1]
            changes.append((begin,end,repr(address)))
    for begin,end,value in reversed(changes):text=text[:begin]+value+text[end:]
    return text,len(changes)

def main():
    rows=[]
    for name in ['tests/test_quick_scan_observations.py','tests/test_quick_scan_delivery.py']:
        path=SW/name
        text=path.read_text('utf-8')
        # Explicit new malformed-address negatives remain verbatim.
        marker='@pytest.mark.parametrize("field,value", ['
        limit=text.index(marker) if marker in text else len(text)
        fixed,count=normalize(text[:limit])
        text=fixed+text[limit:]
        if name.endswith('observations.py'):
            text=text.replace('import copy\n','import copy\nimport hashlib\n',1)
            needle='    observation = {'
            assert text.count(needle)==1
            text=text.replace(needle,'''    # This shared helper is also consumed by backup tests with old labels.
    # Normalize synthetic fixture addresses, never product/company identity.
    if not re.fullmatch(r"obs_[a-f0-9]{64}", observation_id):
        observation_id = "obs_" + hashlib.sha256(observation_id.encode()).hexdigest()
    observation = {''')
            text=text.replace('import json\n','import json\nimport re\n',1)
        path.write_text(text,encoding='utf-8')
        rows.append({'path':name,'upgraded_literal_labels':count,'real_company_data':False})
    print(rows)

if __name__=='__main__':main()
