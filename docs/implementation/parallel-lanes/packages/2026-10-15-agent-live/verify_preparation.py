"""Read-only preparation checks; not worker acceptance or financial approval."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path)
    parser.add_argument('--owner-input-root', type=Path)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    root = base.parents[4]
    lock = json.loads((base/'inputs.lock.json').read_text(encoding='utf-8'))
    inputs = (args.input_root or Path(lock['default_input_root'])).resolve()
    manifest = json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    seen = set()
    total_bytes = 0
    for item in lock['files']:
        ref = (item['repository'], item['path'])
        assert ref not in seen, ref
        seen.add(ref)
        p = inputs/item['repository']/item['path']
        assert p.resolve().is_relative_to(inputs), p
        name = str(p.absolute())
        p = Path(name if name.startswith('\\\\?\\') else '\\\\?\\'+name)
        blob = p.read_bytes()
        assert len(blob) == item['bytes'] and hashlib.sha256(blob).hexdigest() == item['sha256'], ref
        total_bytes += len(blob)
    spec = importlib.util.spec_from_file_location('iqs_handoff_preparation', root/'scripts/parallel_handoff_cli.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected_ids = {'AGENT-RUN-02','AGENT-REF-02','AGENT-EVAL-02'}
    assert {p['id'] for p in manifest['packages']} == expected_ids
    scopes = [Path(p['write_scope']).resolve() for p in manifest['packages']]
    assert all(not a.is_relative_to(b) and not b.is_relative_to(a)
               for index,a in enumerate(scopes) for b in scopes[index+1:])
    expected_questions = ['IQS_01','IQS_02','IQS_04','IQS_05','IQS_06','IQS_07','IQS_10','IQS_11','IQS_12','IQS_16','IQS_18','IQS_20']
    for package in manifest['packages']:
        package_id = package['id']
        targets = json.loads((base/(package_id+'.targets.json')).read_text(encoding='utf-8'))
        assert targets['question_ids'] == expected_questions
        assert targets['company_keys'] == ['catl','cncb_h','alphabet']
        assert len(targets['slots']) == 36
        assert {(s['company_key'],s['question_id']) for s in targets['slots']} == {
            (c,q) for c in targets['company_keys'] for q in expected_questions}
        original_ref = targets['original_targets_ref']
        original_path = inputs/original_ref['repository']/original_ref['path']
        original = json.loads(original_path.read_text(encoding='utf-8'))
        question_hashes = {q['question_id']:q['question_object_sha256'] for q in original['records']}
        assert all(s['question_object_sha256'] == question_hashes[s['question_id']]
                   for s in targets['slots'])
        assert targets['qualification_granted'] is False
        assert package['model_api_enabled'] is False and package['paid_search_enabled'] is False
        code, result = module.validate_handoff(base/(package_id+'.handoff.template.json'),package_id,base/'manifest.json')
        assert code == 0, result
    for p in base.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'): continue
            assert (p.parent/link.split('#')[0]).is_file(),(p.name,link)
    owner_lock = json.loads((base/'owner-alignment.inputs.lock.json').read_text(encoding='utf-8'))
    owner_root = (args.owner_input_root or Path(owner_lock['default_input_root'])).resolve()
    for item in owner_lock['files']:
        p=owner_root/item['path']
        assert p.resolve().is_relative_to(owner_root)
        blob=p.read_bytes()
        assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['sha256']
    projection=json.loads((owner_root/'question-projection.json').read_text(encoding='utf-8'))
    assert projection['execution_ready'] is False and projection['qualification_granted'] is False
    assert len(projection['slots'])==12
    assert {s['benchmark_question_id'] for s in projection['slots']}==set(expected_questions)
    replacement=next(s for s in projection['slots'] if s['benchmark_question_id']=='IQS_11')
    assert replacement['effective_question_id']=='OPERATING_01'
    assert replacement['effective_field_id']=='score.operating_01' and replacement['construct_id']=='IQS_11'
    print(json.dumps({'status':'valid','scope':'preparation_only_not_worker_acceptance',
        'packages':sorted(expected_ids),'input_files':len(seen),'input_bytes':total_bytes,
        'slots_per_package':36,'template_shape_checks':3,'worker_roots_created':0,
        'paid_calls':0,'financial_qualification':False,'owner_diagnostic_files':len(owner_lock['files']),
        'owner_diagnostic_not_execution_ready':True}))


if __name__ == '__main__':
    main()
