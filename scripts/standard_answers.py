"""Offline structured prompts, receipt-bound observations and comparison checks.

No network, model calls, production storage, scheduling or automatic evidence approval.
"""
import argparse
import copy
from datetime import date, datetime, timezone
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
import question_sets as qs

ROOT = qs.ROOT


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=4)
def validator(name):
    registry = Registry()
    for file in ('answer-content.schema.json', 'observation.schema.json'):
        schema = qs.read_json(ROOT / 'schemas' / file)
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    return Draft202012Validator(qs.read_json(ROOT / 'schemas' / name),
                               registry=registry, format_checker=FormatChecker())


def validate_content(answer, question, cutoff):
    validator('answer-content.schema.json').validate(answer)
    if answer['question_id'] != question['id']:
        raise ValueError('answer question mismatch')
    kind = question.get('response_kind', 'score')
    if answer['response_kind'] != kind:
        raise ValueError('answer kind mismatch')
    successful = answer['status'] in ('scored', 'answered')
    if kind == 'fact':
        if answer['score'] is not None or answer['status'] == 'scored':
            raise ValueError('facts must not carry a score')
        if any(i['relation'] not in question['relations'] for i in answer['items']):
            raise ValueError('fact relation not allowed for field')
        if len(answer['items']) > question['max_items']:
            raise ValueError('fact item limit exceeded')
    elif answer['items'] or answer['status'] == 'answered':
        raise ValueError('score answer must use score/metrics, not fact rows')
    if kind == 'score' and ((answer['status'] == 'scored') != (answer['score'] is not None)):
        raise ValueError('score/status mismatch')
    if not successful and (answer['score'] is not None or answer['items'] or answer['metrics']):
        raise ValueError('unavailable answer cannot carry asserted values')
    if successful and not answer['evidence']:
        raise ValueError('successful answer needs evidence')
    if kind == 'fact' and successful and not answer['items']:
        raise ValueError('fact answer needs structured rows; unknown is not an empty asserted list')
    for value in (answer['information_as_of'], answer['period_end']):
        if value and value > cutoff:
            raise ValueError('answer information after cutoff')
    if answer['period_start'] and answer['period_end'] and answer['period_start'] > answer['period_end']:
        raise ValueError('reversed period')
    ids = [e['id'] for e in answer['evidence']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate evidence id')
    for e in answer['evidence']:
        if not qs.valid_url(e['url']) or (e['published_at'] and e['published_at'] > cutoff):
            raise ValueError('invalid URL or future source')
    values = answer['metrics'] + [m for i in answer['items'] for m in i['metrics']]
    for item in answer['items']:
        if not item['evidence_ids'] or not set(item['evidence_ids']) <= set(ids):
            raise ValueError('fact row missing evidence binding')
        if item['valid_from'] and item['valid_to'] and item['valid_from'] > item['valid_to']:
            raise ValueError('reversed relationship validity')
    for group in [answer['metrics']] + [i['metrics'] for i in answer['items']]:
        if len({m['metric_id'] for m in group}) != len(group):
            raise ValueError('duplicate metric id')
    for m in values:
        registry = qs.read_json(ROOT / 'questions/metric-registry.json')['metrics']
        if m['metric_id'] in registry:
            if m['unit'] != registry[m['metric_id']]['unit']:
                raise ValueError('canonical metric unit mismatch')
        elif not m['metric_id'].startswith('custom.'):
            raise ValueError('unknown metric must use custom namespace')
        if m['value'] is not None and (not m['evidence_ids'] or not set(m['evidence_ids']) <= set(ids)):
            raise ValueError('numeric metric missing evidence binding')
        if m['unit'] in ('currency', 'currency_per_share') and m['currency'] is None:
            raise ValueError('currency metric requires currency')
        if m['unit'] == 'other' and not m['unit_detail']:
            raise ValueError('other unit needs definition')
        if m['period_start'] and m['period_end'] and m['period_start'] > m['period_end']:
            raise ValueError('reversed metric period')
        if m['period_end'] and m['period_end'] > cutoff and m['basis'] != 'forward':
            raise ValueError('future historical metric')
    digest(answer)  # Reject NaN/Infinity that JSON parsers may otherwise accept.
    return answer


def validate_fact_library():
    bank = qs.read_json(ROOT / 'questions/facts.json')
    _, modules = qs.load_library()
    ids, fields = set(), set()
    for q in bank['questions']:
        if q['id'] in ids or q['field_id'] in fields or not q['field_id'].startswith('facts.'):
            raise ValueError('duplicate/invalid fact identity')
        ids.add(q['id']); fields.add(q['field_id'])
        if not q['question'] or not q['relations'] or q['priority'] not in (1, 2) or not 1 <= q['max_items'] <= 20:
            raise ValueError('incomplete fact question')
        for kind in ('types', 'industries', 'stages'):
            if any(key not in modules or modules[key]['kind'] != kind for key in q['applies'].get(kind, [])):
                raise ValueError('invalid fact route')
    for kind in ('types', 'industries', 'stages'):
        covered = {key for q in bank['questions'] for key in q['applies'].get(kind, [])}
        required = {key for key, module in modules.items() if module['kind'] == kind and key != 'cyclical'}
        if covered != required:
            raise ValueError('missing type/industry/stage fact coverage')
    return {'questions': len(ids), 'version': bank['version']}


def standard_prompt(question, profile):
    schema = qs.read_json(ROOT / 'schemas/answer-content.schema.json')
    # Emit the exact schema once per independent request; no unstated external resource dependency.
    identity = {k: profile[k] for k in ('company', 'entity_id', 'ticker', 'exchange', 'security_id',
                'security_class', 'segment_id', 'as_of', 'company_type', 'industry_modules', 'stage',
                'business_subtype', 'cycle_sensitive', 'cycle_position') if k in profile}
    base = qs.render_question(question, profile).split(qs.ANSWER_RULE)[0] if question.get('response_kind') != 'fact' else (
        f"[{question['id']}] 对象与口径={json.dumps(identity, ensure_ascii=False)}。{question['question']}\n"
        f"关系只可用{question['relations']}；最多{question['max_items']}条。")
    return (base + '\n实际联网搜索，仅用截止日前可得来源。不要下载公司文档。'
            '只输出符合下列schema的JSON；不使用score/description外层兼容包装。'
            'response_kind=' + question.get('response_kind', 'score') + '。'
            '事实不评分且score=null；未披露用insufficient_evidence，不等同不存在。'
            '已知部分可以answered+coverage.partial，并列缺项；关系和数值逐条绑定evidence_ids。'
            'canonical_entity_id/taxonomy_id只有已知主档映射才填，否则null，不自行创造。'
            '时间和模型由执行器另附，不在答案中自报执行回执。'
            'metrics使用明确单位、币种、期间和current/normalized/stress/forward口径；禁止混用。\n'
            + json.dumps(schema, ensure_ascii=False, separators=(',', ':'))
            + '\n数值指标尽量使用以下固定ID/单位/定义；没有数据则metrics=[]。其他指标只用custom.*，不可自动数值比较：'
            + json.dumps(qs.read_json(ROOT / 'questions/metric-registry.json')['metrics'], ensure_ascii=False, separators=(',', ':')))


def select_facts(profile, mode='quick'):
    _, modules = qs.load_library()
    qs.validate_profile(profile, modules)
    if mode not in ('quick', 'full'):
        raise ValueError('unknown mode')
    bank = qs.read_json(ROOT / 'questions/facts.json')
    chosen = []
    recovery = (profile.get('recovery_review') or profile['stage'] in ('turnaround', 'declining')
                or 'distressed' in profile.get('overlays', []))
    for q in bank['questions']:
        a = q['applies']
        applies = (a.get('all') or profile['company_type'] in a.get('types', [])
                   or bool(set(profile.get('industry_modules', [])) & set(a.get('industries', []))))
        applies = applies or profile['stage'] in a.get('stages', [])
        applies = applies or (a.get('cycle_sensitive') and profile.get('cycle_sensitive'))
        applies = applies or (a.get('recovery') and recovery)
        if applies and (mode == 'full' or q['priority'] == 1):
            chosen.append({**q, 'response_kind': 'fact', 'scope': 'entity',
                           'rubric_version': bank['version'], 'construct_id': None})
    return bank, chosen


def compose_facts(profile, mode, output_dir):
    bank, chosen = select_facts(profile, mode)
    output_dir = Path(output_dir)
    if any((output_dir / n).exists() for n in ('questions.json', 'manifest.json')):
        raise ValueError('use a fresh output directory')
    manifest = {'schema_version': '3.0', 'template_version': bank['version'], 'answer_format': 'standard-1',
                'method_id': 'facts-1/' + hashlib.sha256((ROOT / 'schemas/answer-content.schema.json').read_bytes()
                              + (ROOT / 'questions/metric-registry.json').read_bytes()).hexdigest()[:16],
                'mode': mode, 'profile': profile,
                'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                  ('questions/facts.json', 'schemas/answer-content.schema.json', 'questions/metric-registry.json')},
                'questions': [{**q, 'prompt': standard_prompt(q, profile)} for q in chosen]}
    qs.write_json(output_dir / 'manifest.json', manifest)
    qs.write_json(output_dir / 'questions.json', [{'category': '非评分事实',
                                                 'questions': [q['prompt'] for q in manifest['questions']]}])
    return {'fact_questions': len(chosen), 'output_dir': str(output_dir.resolve()), 'network_used': False}


def validate_observation(record):
    validator('observation.schema.json').validate(record)
    if record['answer']['response_kind'] == 'fact':
        known = {q['id']: {**q, 'response_kind': 'fact'} for q in qs.read_json(ROOT / 'questions/facts.json')['questions']}
    else:
        _, modules = qs.load_library()
        known = {q['id']: q for module in modules.values() for q in module['questions']}
    question = known.get(record['question_id'])
    if not question or record['field_id'] != question.get('field_id', question.get('metric_id')):
        raise ValueError('unknown or mismatched field identity')
    validate_content(record['answer'], question, record['information_cutoff'])
    e = record['execution']
    start, end = (datetime.fromisoformat(e[k].replace('Z', '+00:00')) for k in ('started_at', 'answered_at'))
    if start.utcoffset().total_seconds() != 0 or end.utcoffset().total_seconds() != 0:
        raise ValueError('execution timestamps must be UTC')
    if end < start or record['observed_at'] != e['answered_at']:
        raise ValueError('execution timestamp mismatch')
    if record['information_cutoff'] > end.date().isoformat():
        raise ValueError('cutoff cannot be later than answer time')
    if record['scope'] == 'security' and not record['security_id']:
        raise ValueError('security scope requires security identity')
    if record['scope'] == 'segment' and not record['segment_id']:
        raise ValueError('segment scope requires segment identity')
    if record['answer']['question_id'] != record['question_id']:
        raise ValueError('envelope question mismatch')
    if e['search_status'] == 'executed' and not e['search_receipt_id']:
        raise ValueError('search execution requires external receipt reference')
    if record['answer']['status'] in ('scored', 'answered') and e['search_status'] != 'executed':
        raise ValueError('cannot accept successful content without search execution receipt')
    if record['task_mode'] == 'comparison' and not record['comparison_group_id']:
        raise ValueError('comparison request needs explicit group')
    content = {k: v for k, v in record.items() if k != 'observation_id'}
    if record['observation_id'] != 'obs_' + digest(content):
        raise ValueError('immutable observation hash mismatch')
    return record


def build_observations(manifest, answers, receipts):
    if manifest.get('answer_format') != 'standard-1':
        raise ValueError('standard manifest required; never relabel legacy records')
    profile = manifest['profile']
    if not profile.get('entity_id'):
        raise ValueError('verified entity_id required from identity owner')
    if receipts.get('manifest_sha256') != digest(manifest):
        raise ValueError('receipt belongs to another manifest')
    known = {q['id']: q for q in manifest['questions']}
    if set(answers) - set(known) or set(answers) != set(receipts['requests']):
        raise ValueError('each submitted answer needs exactly one matching execution receipt')
    records = []
    for qid, answer in answers.items():
        q = known[qid]
        validate_content(answer, q, profile['as_of'])
        execution = receipts['requests'][qid]
        if execution['prompt_sha256'] != hashlib.sha256(q['prompt'].encode()).hexdigest():
            raise ValueError('execution prompt mismatch')
        record = dict(schema_version='1.0.0', entity_id=profile['entity_id'],
                      security_id=profile.get('security_id') if q['scope'] == 'security' else None,
                      segment_id=profile.get('segment_id'), field_id=q.get('field_id', q.get('metric_id')),
                      construct_id=q.get('construct_id'), question_id=qid,
                      question_version=q['rubric_version'], template_version=manifest['template_version'],
                      method_id=manifest['method_id'] + '/' + digest({k: v for k, v in q.items() if k != 'prompt'})[:16],
                      scope='segment' if profile.get('segment_id') and q['scope'] == 'entity' else q['scope'],
                      cohort=dict(company_type=profile['company_type'], industries=sorted(profile.get('industry_modules', [])),
                                  stage=profile['stage'], subtype=profile.get('business_subtype')),
                      information_cutoff=profile['as_of'], run_id=receipts['run_id'], scan_id=receipts['scan_id'],
                      inputset_id=receipts['inputset_id'], task_mode=receipts['task_mode'],
                      comparison_group_id=receipts['comparison_group_id'], observed_at=execution['answered_at'],
                      execution=execution, answer=answer, evidence_review_status='unreviewed')
        # Detach from caller-owned mutable answers/receipts before creating an immutable snapshot.
        record = copy.deepcopy(record)
        record['observation_id'] = 'obs_' + digest(record)
        records.append(validate_observation(record))
    return {'schema_version': '1.0.0', 'assembled_at': datetime.now(timezone.utc).isoformat(),
            'manifest_sha256': digest(manifest), 'observations': records,
            'missing_question_ids': sorted(set(known) - set(answers)),
            'notice': 'Structural checks only; independent source review and StockWiki import still required.'}


def period_shape(value):
    start, end = value['period_start'], value['period_end']
    if start is None and end is None:
        return ('not_given',)
    if start is None or end is None:
        return ('incomplete', start, end)
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    bucket = next((label for bound, label in ((40, 'month'), (110, 'quarter'), (200, 'half'), (380, 'year'))
                   if days <= bound), 'other')
    return (bucket, end[5:7], days if bucket == 'other' else None)


def compare(left, right, axis):
    for record in (left, right):
        validate_observation(record)
    if axis not in ('company', 'time', 'model'):
        raise ValueError('unknown comparison axis')
    reasons = []
    for key in ('field_id', 'question_version', 'method_id', 'scope', 'cohort'):
        if left[key] != right[key]:
            reasons.append(key + '_changed')
    for key in ('response_kind', 'basis'):
        if left['answer'][key] != right['answer'][key]:
            reasons.append(key + '_changed')
    def model(r):
        e = r['execution']
        return (e['provider'], e['model_resolved'], e['model_revision'])
    if not left['execution']['model_resolved'] or not right['execution']['model_resolved']:
        reasons.append('resolved_model_unknown')
    if axis != 'model' and model(left) != model(right):
        reasons.append('model_changed')
    if axis != 'time':
        for key in ('information_cutoff',):
            if left[key] != right[key]: reasons.append(key + '_changed')
        for key in ('period_start', 'period_end', 'information_as_of'):
            if left['answer'][key] != right['answer'][key]: reasons.append(key + '_changed')
    elif period_shape(left['answer']) != period_shape(right['answer']):
        reasons.append('period_cadence_or_alignment_changed')
    if axis != 'company':
        for key in ('entity_id', 'security_id', 'segment_id'):
            if left[key] != right[key]: reasons.append(key + '_changed')
    if axis == 'model':
        if (left['task_mode'] != 'comparison' or right['task_mode'] != 'comparison'
                or not left['comparison_group_id'] or left['comparison_group_id'] != right['comparison_group_id']
                or left['inputset_id'] != right['inputset_id']):
            reasons.append('uncontrolled_model_comparison')
    a, b = left['answer'], right['answer']
    if not a['information_as_of'] or not b['information_as_of']:
        reasons.append('information_date_unknown')
    if a['status'] not in ('scored', 'answered') or b['status'] not in ('scored', 'answered'):
        reasons.append('unavailable_answer')
    if a['confidence'] == 'low' or b['confidence'] == 'low':
        reasons.append('low_confidence')
    warnings = ['结构可比不等于来源已核验；不输出平均分或真值。']
    if left['execution']['model_revision'] is None or right['execution']['model_revision'] is None:
        warnings.append('model_revision_unknown: 无法排除模型别名背后的版本变化')
    if a['items'] or b['items']:
        warnings.append('事实行及内嵌指标仅并排展示；顶层可比性不代表所有关系/数值已逐行对齐')
    if {e['url'] for e in a['evidence']} != {e['url'] for e in b['evidence']}:
        warnings.append('evidence_set_changed: 检索来源变化与模型差异可能混杂')
    # Keep typed metrics visible; never silently subtract unlike units or fiscal periods.
    metric_rows = []
    am = {m['metric_id']: m for m in a['metrics']}; bm = {m['metric_id']: m for m in b['metrics']}
    for key in sorted(set(am) | set(bm)):
        x, y = am.get(key), bm.get(key)
        compatible = bool(not key.startswith('custom.') and x and y and all(x[k] == y[k] for k in
                          ('unit', 'currency', 'unit_detail', 'basis', 'definition')))
        if axis != 'time' and x and y:
            compatible = compatible and all(x[k] == y[k] for k in ('period_start', 'period_end'))
        elif x and y:
            compatible = compatible and period_shape(x) == period_shape(y)
        metric_rows.append({'metric_id': key, 'left': x, 'right': y, 'comparable': compatible and not reasons})
    return {'axis': axis, 'comparable': not reasons, 'reasons': reasons, 'warnings': warnings,
            'left_observation_id': left['observation_id'], 'right_observation_id': right['observation_id'],
            'score_difference': b['score'] - a['score'] if not reasons and a['score'] is not None and b['score'] is not None else None,
            'metrics': metric_rows, 'left_items': a['items'], 'right_items': b['items']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate-library')
    facts = sub.add_parser('compose-facts')
    facts.add_argument('--profile', required=True); facts.add_argument('--mode', choices=('quick', 'full'), default='quick')
    facts.add_argument('--out-dir', required=True)
    build = sub.add_parser('build')
    for key in ('manifest', 'answers', 'receipts', 'output'): build.add_argument('--' + key, required=True)
    diff = sub.add_parser('compare')
    for key in ('left', 'right', 'axis', 'output'): diff.add_argument('--' + key, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'validate-library': result = validate_fact_library()
        elif args.command == 'compose-facts': result = compose_facts(qs.read_json(args.profile), args.mode, args.out_dir)
        elif args.command == 'build':
            result = build_observations(qs.read_json(args.manifest), qs.read_json(args.answers), qs.read_json(args.receipts))
            if Path(args.output).exists(): raise ValueError('do not overwrite observations')
            qs.write_json(args.output, result)
        else:
            result = compare(qs.read_json(args.left), qs.read_json(args.right), args.axis)
            qs.write_json(args.output, result)
        print(json.dumps({'command': args.command, 'ok': True, 'network_used': False}, ensure_ascii=False))
    except Exception as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
