// Synthetic controller regression. Original assertions retained; imports rebased.
import {resolve as r1Resolve} from 'node:path';
import {pathToFileURL as r1URL} from 'node:url';
const R1_ROOT = process.env.IQS_R1_COMPONENT_ROOT || "C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab";
import test from 'node:test';
import assert from 'node:assert/strict';
const {createUniverseImportMachine,parseUniverseFile} = await import(r1URL(r1Resolve(R1_ROOT, "src/iqs-universe-import/index.js")).href);
const {createFakeAdapter, ownerError} = await import(r1URL(r1Resolve(R1_ROOT, "tests/js/helpers/fake-adapter.js")).href);
const connectionIdentity={universe_id:'default',as_of:'2026-10-28',connection_ref:'independent-acceptance'};
const upload=(txt)=>parseUniverseFile(new TextEncoder().encode(txt),{format:'csv',encoding:'utf-8',columnMapping:{has_header:false,name:"0",ticker:"1",market:"2",security_type:null},displayName:'synthetic.csv'});
async function setup(overrides={},txt='中微公司,688012,CN\n中微半导体,688380,CN\n'){
 const a=createFakeAdapter(overrides);const m=createUniverseImportMachine({adapter:a,connectionIdentity});await m.loadUpload(upload(txt));await m.resolveRows(m.rowIds());return {a,m};
}
async function preview(m,id,entity,security){m.selectCandidate(id,{entity_id:entity,security_id:security,selection_reason:'explicit synthetic selection'});await m.previewRow(id);}
const ack=(args)=>({status:'applied',idempotent_replay:false,payload:{status:'applied',member:{entity_id:args.entity_id,membership_status:'active',version:1}},member:{entity_id:args.entity_id,membership_status:'active',version:1}});

test('ACCEPT-U01: omitted sole security must not bypass expired listing check',async()=>{
 const {m}=await setup({},'旧挂牌,600000,CN\n');const id=m.rowIds()[0];
 assert.throws(()=>m.selectCandidate(id,{entity_id:'ent-old',selection_reason:'checked'}),undefined);
});

test('ACCEPT-U02: distinct rows must not dispatch concurrent writes',async()=>{
 let release,firstEntered;const gate=new Promise(r=>release=r);const firstStarted=new Promise(r=>firstEntered=r);let entered=0;
 const {a,m}=await setup({apply:async args=>{entered++;if(entered===1)firstEntered();await gate;return ack(args)}});const [x,y]=m.rowIds();
 await preview(m,x,'ent-zw-a','sec-zw-a');await preview(m,y,'ent-zw-b','sec-zw-b');
 const first=m.confirmRow(x);await firstStarted;const second=m.confirmRow(y).catch(e=>({error:e.code}));
 await new Promise(setImmediate);const concurrent=entered;release();await Promise.all([first,second]);
 assert.equal(concurrent,1,'single-member mutation is globally serial; different row must be refused/deferred');
});

test('ACCEPT-U03: a new upload cannot discard a pending mutation draft',async()=>{
 let release,enter;const gate=new Promise(r=>release=r);const entered=new Promise(r=>enter=r);
 const {m}=await setup({apply:async args=>{enter();await gate;return ack(args)}});const x=m.rowIds()[0];await preview(m,x,'ent-zw-a','sec-zw-a');const pending=m.confirmRow(x);await entered;
 const originalHash=m.getDraft().source_ref.raw_sha256;const replacement=m.loadUpload(upload('不同文件,688380,CN\n')).catch(()=>null);await new Promise(setImmediate);const beforeRelease=m.getDraft().source_ref.raw_sha256;release();await Promise.all([pending,replacement]);assert.equal(beforeRelease,originalHash,'in-flight upload replacement must refuse or queue before destroying original acknowledgement ownership');
});

test('ACCEPT-U04: unknown result cannot be reset and re-POSTed before original inspect',async()=>{
 let calls=0;const {a,m}=await setup({apply:async args=>{calls++;if(calls===1)throw ownerError('timeout');return ack(args)}});const x=m.rowIds()[0];await preview(m,x,'ent-zw-a','sec-zw-a');await m.confirmRow(x);assert.equal(m.getDraft().rows[0].state,'unknown');
 let blocked=false;try{await m.resolveRow(x);await preview(m,x,'ent-zw-a','sec-zw-a');await m.confirmRow(x);}catch{blocked=true}
 assert.equal(calls,1,'unknown must stay inspect-first even if user clicks candidate/preview again');assert.equal(a.calls.filter(c=>c.method==='inspectMember').length,0);
});

test('ACCEPT-U05: stale preview cannot attach old candidate token to new selection',async()=>{
 let release,enter;const gate=new Promise(r=>release=r);const entered=new Promise(r=>enter=r);
 const {m}=await setup({preview:async args=>{enter();await gate;return {can_apply:true,blocked_reasons:[],preview_token:'token-for-'+args.entity_id,payload:{request:{...args}}}}},'中微公司,,CN\n');const x=m.rowIds()[0];
 m.selectCandidate(x,{entity_id:'ent-zw-a',security_id:'sec-zw-a',selection_reason:'first'});const pending=m.previewRow(x);await entered;
 try{m.selectCandidate(x,{entity_id:'ent-zw-b',security_id:'sec-zw-b',selection_reason:'changed'});}catch{}release();await pending;
 const row=m.getDraft().rows[0];if(row.owner_preview!==null)assert.equal(row.owner_preview.payload.request.entity_id,row.selected_entity_id,'old async preview must be discarded or remain attached only to its original selection');
});
