"""Independent ESM negatives over actual UI source; no real browser/API/files changed."""
import ast
import json
from pathlib import Path
import shutil
import subprocess

UI = Path('C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab')
HERE = Path(__file__).resolve().parent
tree = ast.parse((UI/'tests/test_product_ui.py').read_text(encoding='utf-8'))
harness = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HARNESS' for t in n.targets))
extra = r'''
if(scenario==='independent-terminal-flow'){
 const done={registered:1,tasks:[{process_state:'process_exited',launcher_state:'running',work_completion_authoritative:false}],deliveries:[{state:'completed',counts:{scopes:2,delivered_scopes:2},entries:[{state:'delivered'},{state:'delivered'}]}]};
 const recommendation=core.operationRecommendation(done);
 assert.equal(recommendation.step,3,'Original delivery-job completed must recommend delivered-results review, not another paid scan');
 assert.ok(/签收|结果/.test(recommendation.title+' '+recommendation.next));
 const partial=core.operationRecommendation({...done,deliveries:[{state:'partial',counts:{scopes:2,delivered_scopes:1}}]});assert.equal(partial.step,3);assert.ok(/接续|未完成/.test(partial.next));
 const unknown=core.operationRecommendation({...done,tasks:[{process_state:'needs_original_inspection'}]});assert.equal(unknown.step,2);assert.ok(/核/.test(unknown.next));
}else if(scenario==='independent-safe-boundaries'){
 const external=['https://evil.example/#/results','#/results-extra?query=a','#/results?evil=1','#/results?query=ok\\evil'];
 for(const route of external)assert.equal(core.safeResultsReturn(route),'#/results');
 const valid='#/results?query=%E5%AE%81%E5%BE%B7&view=pending&offset=50&snapshot_token=original';assert.equal(core.safeResultsReturn(valid),valid);
 const rows=[{entity_id:'ENT_A',canonical_name:'中微公司',securities:[{ticker:'688012'}]},{entity_id:'ENT_B',canonical_name:'中微半导体',securities:[{ticker:'688380'}]}];
 assert.deepEqual(core.matchingEntities(rows,'688380').map(x=>x.entity_id),['ENT_B']);assert.deepEqual(core.matchingEntities(rows,'中微').map(x=>x.entity_id),['ENT_A','ENT_B']);
 assert.equal(core.knownScore({status:'insufficient_evidence',score:5}),'—');assert.equal(core.actionAllowed({state:'unknown'},'resume',{resume:true}),false);
 assert.equal(core.safeEvidenceURL('data:text/html,attack'),null);assert.equal(core.safeEvidenceURL('file:///C:/private'),null);
}else if(scenario==='independent-settings-inflight'){
 const {load}=await import(moduleURL('store.js'));await load();await api.connect();
 const ui=await import(moduleURL('ui/product.js'));const page=ui.renderSettings();await new Promise(resolve=>setTimeout(resolve,20));
 const flat=node=>[node,...node.children.flatMap(flat)],find=predicate=>flat(page).find(predicate);
 const model=find(n=>n.attributes['aria-label']==='模型名称 1'),save=find(n=>n.tag==='button'&&n.textContent==='校验并保存设置');
 model.value='FIRST_SAVED_VALUE';await model.fire('input');
 const baseFetch=globalThis.fetch;let release,sent;
 globalThis.fetch=async(url,opts={})=>{if(String(url).endsWith('/settings')&&opts.method==='PUT'){sent=JSON.parse(opts.body);return new Promise(resolve=>{release=()=>resolve({ok:true,status:200,headers:{get:()=> 'application/json'},json:async()=>({ok:true,data:{policy:sent.policy,revision_sha256:'new-revision'}})});});}return baseFetch(url,opts);};
 const pending=save.fire('click');await new Promise(resolve=>setTimeout(resolve,5));
 if(!model.disabled){model.value='SECOND_UNSAVED_VALUE';await model.fire('input');}
 release();await pending;
 if(model.value==='SECOND_UNSAVED_VALUE')assert.ok(page.textContent.includes('未保存'),'An edit made while save is in flight must not be falsely labelled saved');
 ui.disposeProductPage();
}else if(scenario==='independent-clear-new-field'){
 const {connectionFields}=await import(moduleURL('ui/product_forms.js'));let changed;
 const form=connectionFields({prepare:{extension:'KEEP_UNKNOWN'}},value=>changed=value);
 const flat=node=>[node,...node.children.flatMap(flat)];
 const field=flat(form.node).find(n=>n.attributes['aria-label']==='原准入配置文件');
 field.value='C:/TEMP/UNWANTED-PATH';await field.fire('input');assert.equal(form.value().prepare.admission_config,'C:/TEMP/UNWANTED-PATH');
 field.value='';await field.fire('input');assert.ok(!form.value().prepare.admission_config,'Clearing a newly added optional path must clear the outgoing draft, not retain a hidden old value');
 assert.equal(form.value().prepare.extension,'KEEP_UNKNOWN');assert.ok(!changed.prepare.admission_config);
}else if(scenario==='independent-full-return-context'){
 const {load}=await import(moduleURL('store.js'));await load();await api.connect();
 const ui=await import(moduleURL('ui/product.js')),conditions=JSON.stringify([{field:'score.iqs_01',op:'>=',value:8},{field:'score.iqs_05',op:'!=',value:2}]),filters=JSON.stringify({market:'HK',industry:'半导体',security_type:'equity'});
 data.results.snapshot_token='original-fixed-snapshot';data.results.total=120;
 const route={query:{query:'宁德',view:'pending',offset:'50',conditions,condition_combine:'any',filters}};
 const page=ui.renderResults(route);await new Promise(resolve=>setTimeout(resolve,20));const flat=n=>[n,...n.children.flatMap(flat)];
 const detail=flat(page).find(n=>n.attributes.href?.startsWith('#/results?id=')),back=new URLSearchParams(detail.attributes.href.split('?')[1]).get('return'),params=new URLSearchParams(back.split('?')[1]);
 for(const [key,value]of Object.entries(route.query))assert.equal(params.get(key),value,key);assert.equal(params.get('snapshot_token'),'original-fixed-snapshot');assert.equal(params.get('limit'),'50');
 ui.disposeProductPage();const detailPage=ui.renderResults({query:{id:entity,return:back}});assert.equal(flat(detailPage).find(n=>n.textContent==='← 返回结果库').attributes.href,back);ui.disposeProductPage();
}else if(scenario==='independent-clear-root-path'){
 const {connectionFields}=await import(moduleURL('ui/product_forms.js'));
 const form=connectionFields({workspace_root:'C:/CUSTOM_RESULTS',stockwiki_root:'C:/CUSTOM_OWNER',prepare:{extension:'KEEP'}},()=>{});
 const flat=node=>[node,...node.children.flatMap(flat)];
 const field=flat(form.node).find(n=>n.attributes['aria-label']==='结果工作区目录');field.value='';await field.fire('input');
 assert.ok(Object.hasOwn(form.value(),'workspace_root'),'Clearing an explicit root path must not remove its key and silently reconnect default original workspace');assert.equal(form.value().workspace_root,'');assert.equal(form.value().stockwiki_root,'C:/CUSTOM_OWNER');
}else if(scenario==='core'){
'''
assert "if(scenario==='core'){" in harness
harness = harness.replace("if(scenario==='core'){",extra,1)
results=[]
for scenario in ['independent-terminal-flow','independent-safe-boundaries','independent-settings-inflight','independent-clear-new-field','independent-full-return-context','independent-clear-root-path']:
    result=subprocess.run([shutil.which('node'),'--input-type=module','-',str(UI),scenario],input=harness,text=True,encoding='utf-8',capture_output=True,timeout=30)
    results.append({'scenario':scenario,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
(HERE/'negative-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'scenario':r['scenario'],'passed':r['returncode']==0} for r in results]))
raise SystemExit(any(r['returncode'] for r in results))
