from pathlib import Path
import copy,hashlib,json,os,subprocess,sys
RUN=Path(__file__).resolve().parent;W=RUN/'isolated';mode=sys.argv[1]
lab=W/mode;sys.path.insert(0,str(lab/'src'))
def read(p):return json.loads(p.read_text('utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT')}
env.update(PYTHONPATH=str(lab/'src'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',HTTP_PROXY='http://127.0.0.1:9',HTTPS_PROXY='http://127.0.0.1:9',ALL_PROXY='http://127.0.0.1:9',NO_PROXY='')
records=[]
def cli(name,args,expected):
    p=subprocess.run([sys.executable,'-B','-m','iqs_'+('review_calibration' if mode=='review' else 'retrieval_audit'),*args],cwd=W,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
    (RUN/(name+'.stdout.txt')).write_text(p.stdout,encoding='utf-8');(RUN/(name+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    records.append({'probe':name,'exit_code':p.returncode,'expected_exit_code':expected,'traceback': 'Traceback' in p.stderr,'stdout_sha256':digest(RUN/(name+'.stdout.txt')),'stderr_sha256':digest(RUN/(name+'.stderr.txt'))})
    assert p.returncode==expected and 'Traceback' not in p.stderr,(name,p.returncode,p.stderr)
    return json.loads(p.stdout) if p.stdout.strip() else None
if mode=='review':
    from iqs_review_calibration import envelopes
    from iqs_review_calibration.errors import CalibrationError
    book=read(W/'review-casebook.json');assignment=read(W/'review-assigned/public/assignment.json');private=read(W/'review-assigned/private/map.json')
    ctx={**book['expected_context'],'evidence_board_sha256':book['source_context']['evidence_board_sha256']}
    assert ctx['evidence_board_sha256'] is not None
    for name,value in [('casebook',book),('public_assignment',assignment),('private_map',private)]:
        envelopes.validate(value,expected_context=ctx)
        for mutation in ('missing_board','wrong_board','wrong_reason'):
            d=copy.deepcopy(value)
            if mutation=='missing_board':d['source_context'].update(evidence_board_sha256=None,evidence_board_reason='not_supplied_by_caller')
            elif mutation=='wrong_board':d['source_context']['evidence_board_sha256']='1'*64
            else:d['source_context']['evidence_board_reason']='fabricated reason'
            d['stable_business_sha256']=envelopes.business_hash(d);d['content_sha256']=envelopes.content_hash(d)
            try:envelopes.validate(d,expected_context=ctx)
            except CalibrationError:records.append({'probe':name+'_'+mutation,'result':'typed_rejection_after_both_hashes_recomputed'})
            else:raise AssertionError((name,mutation,'accepted'))
    common=['--inputs',str(W/'review-inputs-locked'),'--lock',str(W/'review-lock/inputs.lock.json'),'--expected-lock-sha256',digest(W/'review-lock/inputs.lock.json')]
    malformed=copy.deepcopy(book);malformed['source_context']['evidence_board_sha256']='1'*64
    malformed['stable_business_sha256']=envelopes.business_hash(malformed);malformed['content_sha256']=envelopes.content_hash(malformed)
    write(W/'forged-board.json',malformed)
    cli('review-cli-forged-board',['validate',*common,'--casebook',str(W/'forged-board.json')],2)
    sys.path.insert(0,str(lab/'tests'))
    from conftest import labels_from_map,fingerprint
    labels=labels_from_map(assignment,private);write(W/'labels.json',labels)
    cli('review-cli-compare',['compare',*common,'--casebook',str(W/'review-casebook.json'),'--assignment',str(W/'review-assigned/public/assignment.json'),'--private-map',str(W/'review-assigned/private/map.json'),'--judgments',str(W/'labels.json'),'--output',str(W/'review-compared')],0)
    report=read(W/'review-compared/calibration-report.json');envelopes.validate(report,expected_context=ctx)
    assert report['judgment_summary']['match']==58
    records.append({'probe':'modern_compare','summary':report['judgment_summary'],'qualification':report['qualification']})
    # Forge both public payload and its map hashes; concrete casebook projection must still bind.
    changed=copy.deepcopy(assignment);changed['cases'][0]['answer']['summary']='A fabricated replacement answer.'
    changed['stable_business_sha256']=envelopes.business_hash(changed);changed['content_sha256']=envelopes.content_hash(changed)
    mp=copy.deepcopy(private);mp['public_assignment_fingerprint']=fingerprint(changed);mp['business_assignment_sha256']=envelopes.business_hash(changed)
    mp['entries'][changed['cases'][0]['anon_case_id']]['public_slot_fingerprint']=fingerprint(changed['cases'][0])
    mp['stable_business_sha256']=envelopes.business_hash(mp);mp['content_sha256']=envelopes.content_hash(mp)
    labels['assignment_fingerprint']=fingerprint(changed)
    for name,v in [('forged-assignment',changed),('forged-map',mp),('rebound-labels',labels)]:write(W/(name+'.json'),v)
    cli('review-cli-rebound-payload',['compare',*common,'--casebook',str(W/'review-casebook.json'),'--assignment',str(W/'forged-assignment.json'),'--private-map',str(W/'forged-map.json'),'--judgments',str(W/'rebound-labels.json'),'--output',str(W/'forged-compare-output')],2)
    assert not (W/'forged-compare-output').exists()
else:
    from iqs_retrieval_audit.context import load_lock,build_expected_context
    from iqs_retrieval_audit.compare import compare_annotations
    from iqs_retrieval_audit.assignment import make_assignment
    from iqs_retrieval_audit.canonical import with_content_hash
    from iqs_retrieval_audit.rubricmodel import source_url_key,duplicate_fingerprint_groups
    lockpath=lab/'inputs/input-lock.json';lock,raw=load_lock(lockpath,digest(lockpath),inputs_dir=lockpath.parent);ctx=build_expected_context(lock,raw)
    rubric=read(lab/'content/rubric.json');private=read(lab/'content/fixtures/private-map.json');assignment=read(lab/'content/fixtures/public-assignment.json');a=read(lab/'content/fixtures/annotations_a.json');b=read(lab/'content/fixtures/annotations_b.json')
    report=compare_annotations(assignment,private,a,b,rubric,expected_context=ctx)
    ai={(r['target_id'],r['source_id']):r for r in a['items']};bi={(r['target_id'],r['source_id']):r for r in b['items']}
    old_compared=0
    for t in private['targets']:
        for e in t['expected']['source_expectations']:
            sid=next(r['public_source_id'] for r in private['sources'] if r['public_target_id']==t['public_target_id'] and r['original_source_id']==e['original_source_id'] and r['occurrence_index']==0)
            pair=(t['public_target_id'],sid)
            if pair not in ai or pair not in bi:continue
            for dim in e['dimension_values']:
                if ai[pair]['dimensions'][dim]['value']==bi[pair]['dimensions'][dim]['value']:old_compared+=1
    exclusions=report['extensions']['iqs.retrieval.calibration_adjudication']['excluded']
    assert len(exclusions)==2 and report['post_hoc_calibration_review']['compared']==old_compared-2
    records.append({'probe':'independent_denominator_recomputation','legacy_equal_annotation_dimensions':old_compared,'new_post_hoc_compared':report['post_hoc_calibration_review']['compared'],'excluded':exclusions,'agreement_counts':report['agreement_counts']})
    index={'planned_pairs':[('t','a'),('t','b')],'sources':{'a':{'url':'https://Site.invalid/Report?Unit=USD'},'b':{'url':'https://site.invalid/report?unit=usd'}}}
    assert duplicate_fingerprint_groups(index)==[]
    index['sources']['b']['url']='https://SITE.invalid/Report?Unit=USD#table'
    assert duplicate_fingerprint_groups(index)==[['a','b']]
    records.append({'probe':'case_sensitive_url_duplicate_counter','different_path_query_not_merged':True,'host_case_fragment_merged':True})
    common=['--lock',str(lockpath),'--expected-lock-sha256',raw,'--bundle',str(lab/'content/retrieval-bundle.json'),'--rubric',str(lab/'content/rubric.json')]
    for tag,number in [('overflow','1e999'),('oversized_integer','1'*5000)]:
        bad=W/(tag+'.json');bad.write_text('{"x":'+number+'}',encoding='utf-8')
        args=common.copy();args[args.index('--bundle')+1]=str(bad)
        cli('retrieval-cli-'+tag,['validate',*args],2)
    # End-to-end empty retrieval, with distinct authored target-level rationales.
    bundle=read(lab/'content/retrieval-bundle.json');bundle['is_synthetic']=False;bundle['tasks']=bundle['tasks'][:1]
    t=bundle['tasks'][0];t['source_items']=[];t['private_metadata'].update(pair_id=None,variant='standalone',expected=None)
    out=make_assignment(with_content_hash(bundle),rubric,seed='independent18-empty',expected_context=ctx)
    assignment=out['public_assignment'];target=assignment['targets'][0]
    def empty_ann(original,who):
        d=copy.deepcopy(original);d['completion_status']='complete';d['items']=[]
        d['assignment_binding']={'public_assignment_content_sha256':assignment['content_sha256'],'seed_commitment':assignment['anonymization']['seed_commitment']}
        level=copy.deepcopy(d['target_level'][0]);level['target_id']=target['target_id']
        level['coverage']={'status':'uncovered','rationale':who+': no evidence retrieved.','dimensions':[{'required_dimension_id':x['dimension_id'],'status':'uncovered','supporting_source_ids':[],'rationale':who+': no source covers dimension.'} for x in target['required_dimensions']]}
        level['target_dimensions']['conflict_handling']={'value':'not_applicable','rationale':who+': no sources to compare.','quote':None,'basis':None,'unknown_reason':None,'not_assessable_reason':None,'not_applicable_reason':who+': source set empty.'}
        d['target_level']=[level];return with_content_hash(d)
    for name,v in [('empty-assignment',assignment),('empty-map',out['private_map']),('empty-a',empty_ann(a,'A')),('empty-b',empty_ann(b,'B'))]:write(W/(name+'.json'),v)
    cli('retrieval-cli-empty-compare',['compare','--lock',str(lockpath),'--expected-lock-sha256',raw,'--assignment',str(W/'empty-assignment.json'),'--private-map',str(W/'empty-map.json'),'--annotations-a',str(W/'empty-a.json'),'--annotations-b',str(W/'empty-b.json'),'--rubric',str(lab/'content/rubric.json'),'--output',str(W/'empty-compared')],0)
    report=read(W/'empty-compared/reports/audit-report.json')
    assert report['status']=='ok' and report['target_counts']['targets_received']==1 and report['target_counts']['source_items_planned']==0 and report['agreement_counts']=={'agree':2,'disagree':0,'not_comparable':0}
    records.append({'probe':'empty_retrieval_public_cli','status':report['status'],'target_counts':report['target_counts'],'agreement_counts':report['agreement_counts'],'qualification':report['qualification']})
write(RUN/(mode+'-independent-probes.json'),{'reviewer':'/root/remaining_acceptance18','results':records})
print(json.dumps({'mode':mode,'probes':len(records),'passed':True}))
