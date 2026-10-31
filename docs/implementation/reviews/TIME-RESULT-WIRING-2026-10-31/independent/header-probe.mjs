import {pathToFileURL} from 'node:url';
import {writeFileSync} from 'node:fs';
const root=process.argv[2];
class N {
 constructor(tag,text=''){this.tag=tag;this.children=[];this.attributes={};this.dataset={};this._text=text;this.events={};this.classList={toggle(){},add(){},remove(){}};}
 setAttribute(k,v){this.attributes[k]=v;}
 addEventListener(k,v){(this.events[k]||=[]).push(v);}
 appendChild(n){this.children.push(n);n.parentNode=this;return n;}
 replaceChildren(...n){this.children=n;this._text='';}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
}
globalThis.document={hidden:false,createElement:t=>new N(t),createTextNode:t=>new N('#text',t)};
globalThis.window={location:{hash:''},history:{replaceState(){}},dispatchEvent(){}};
let calls=[];
const detail={entity:{entity_id:'ENT_FOREIGN',canonical_name:'Foreign declared company'},c06_envelope_validated:true,quality:{quality_verified:true,quality_score:9.99},groups:[{fields:[{entity_id:'ENT_FOREIGN',observation_id:'FOREIGN_OBSERVATION',question_id:'IQS_01',field_id:'score.x',status:'scored',score:10}]}],gaps:[]};
globalThis.fetch=async (url,opts)=>{calls.push({url,method:opts.method});return {ok:true,headers:{get:()=> 'application/json'},json:async()=>({ok:true,data:{protocol:'iqs.company_research_view/1.0.0',entity:detail,temporal_shadow:null}})};};
const mod=path=>import(pathToFileURL(root+'/src/app/'+path).href);
const {store}=await mod('store.js');store.bank={facts:{questions:[]},catalog:{modules:[]}};store.questionIndex={};
const ui=await mod('ui/product.js');
const page=ui.renderResults({query:{id:'ENT_REQUESTED'}});await new Promise(r=>setTimeout(r,25));
const all=n=>[n,...n.children.flatMap(all)];
const sections=all(page).filter(n=>n.tag==='section').map(n=>n.textContent);
const result={scenario:'conflicting requested and envelope entity',main_answer_count:all(page).filter(n=>n.attributes['data-testid']==='production-answer').length,header_text:sections[0],calls,normal_quality_field_present:all(page).some(n=>n.tag==='dt'&&n.textContent==='质量汇总'),normal_c06_field_present:all(page).some(n=>n.tag==='dt'&&n.textContent==='C06 已校验'),identity_conflict_notice_present:page.textContent.includes('返回数据的公司身份冲突'),original_quality_preserved_in_raw:page.textContent.includes('9.99')};
writeFileSync(process.argv[3],JSON.stringify(result,null,2));console.log(JSON.stringify(result));ui.disposeProductPage();
