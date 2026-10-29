// Synthetic controller regression. Original assertions retained; imports rebased.
import {resolve as r1Resolve} from 'node:path';
import {pathToFileURL as r1URL} from 'node:url';
const R1_ROOT = process.env.IQS_R1_COMPONENT_ROOT || "C:/Users/郑曾波/Projects/iqs-comparison-view-lab";
import {test} from 'node:test';
import assert from 'node:assert/strict';
const {createComparisonClient} = await import(r1URL(r1Resolve(R1_ROOT, "src/compare_client.js")).href);
const {projectRecords,buildMatrixModel,createSelection,mountComparison} = await import(r1URL(r1Resolve(R1_ROOT, "src/compare_view.js")).href);
const {installDom,mountHost} = await import(r1URL(r1Resolve(R1_ROOT, "tests/lib/dom-shim.mjs")).href);
const settle=async(n=30)=>{for(let i=0;i<n;i++)await new Promise(resolve=>setTimeout(resolve,0));};
const row=(overrides={})=>({entity_id:'E1',observation_id:'OBS_1',question_id:'Q1',module_package_id:'pkg_old',status:'scored',score:8,information_as_of:'2026-09-30',information_cutoff:'2026-09-30',observed_at:'2026-10-01T00:00:00Z',provider:'P1',model_resolved:'same-model-name',model_revision:'r1',summary:'original-reason-must-be-visible-unique',...overrides});

test('C28-01 actual original history payload retains reported_score and nested answer/execution metadata',async()=>{
 const native={observation_id:'OBS_NATIVE',entity_id:'E1',question_id:'Q1',answer_status:'scored',reported_score:8,provider:'P1',model_resolved:'same-model-name',information_cutoff:'2026-09-30',observed_at:'2026-10-01T00:00:00Z',payload:{question_id:'Q1',module_package_id:'pkg_native',question_version:'2.0.0',answer:{status:'scored',score:8,summary:'native-reason',information_as_of:'2026-09-29',coverage:{status:'sufficient'},confidence:'high',missing_fields:[]},execution:{model_revision:'native-revision'}}};
 const client=createComparisonClient(async()=>({protocol:'iqs.product/1.0.0',available:true,complete:true,entity_id:'E1',observations:[native]}));const out=await client.readHistory('E1');assert.equal(out.records.length,1);
 const r=out.records[0];assert.deepEqual({score:r.score,information_as_of:r.information_as_of,module_package_id:r.module_package_id,question_version:r.question_version,model_revision:r.model_revision,coverage:r.coverage,missing_fields:r.missing_fields},{score:8,information_as_of:'2026-09-29',module_package_id:'pkg_native',question_version:'2.0.0',model_revision:'native-revision',coverage:{status:'sufficient'},missing_fields:[]});
});

test('C28-02 delivered client and actual mount preserve the expandable original reason',async()=>{
 const original=row();const dom=installDom();const host=mountHost(dom.document);const request=async endpoint=>endpoint.startsWith('entity?')?{entity:{entity_id:'E1',canonical_name:'Fixture'},groups:[{key:'common',fields:[original]}],gaps:[]}:{available:true,rows:[]};const view=mountComparison(host,{client:createComparisonClient(request),connectionIdentity:{id:'A'},options:{initialSelection:{entity_ids:['E1']}}});
 try{await settle();const cell=host.querySelector('.iqs-compare__cell');assert.ok(cell);cell.click();assert.ok(host.querySelector('.iqs-compare__detail-body').textContent.includes(original.summary),'actual createComparisonClient->mount path must make original reason reachable');}finally{view.dispose();dom.restore();}
});

test('C28-03 explicit new-package observation choice cannot be hidden by the first old-package row',()=>{
 const old=row({observation_id:'OBS_OLD',score:3,module_package_id:'pkg_old'}),updated=row({observation_id:'OBS_NEW',score:9,module_package_id:'pkg_new',question_version:'2.0.0'});const records=projectRecords([old,updated]).records;
 const selection=createSelection({entity_ids:['E1'],observation_choices:[{entity_id:'E1',question_id:'Q1',observation_ids:['OBS_NEW']}]});const matrix=buildMatrixModel({records,selection,bank:null});const cell=matrix.rows[0].cells.E1;assert.deepEqual({state:cell.state,score:cell.score,observation_ids:cell.observation_ids},{state:'single',score:9,observation_ids:['OBS_NEW']});
});

test('C28-04 model axis keeps different providers with the same model name separately visible',()=>{
 const records=projectRecords([row({observation_id:'P1_OBS',provider:'P1',score:3}),row({observation_id:'P2_OBS',provider:'P2',score:9})]).records;const matrix=buildMatrixModel({records,selection:createSelection({mode:'model_axis',entity_ids:['E1']}),bank:null});assert.equal(matrix.columns.length,2,'two distinct provider/model sources require independent model-axis columns, not a single multiple cell');assert.deepEqual(matrix.columns.map(c=>c.provider).sort(),['P1','P2']);
});

