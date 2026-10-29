// Synthetic adjacency regressions; imports only rebased, no real owner calls.
import {resolve as closeResolve} from 'node:path';
import {pathToFileURL as closeURL} from 'node:url';
const CLOSE_ROOT=process.env.IQS_R1_COMPONENT_ROOT || 'C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab';
import test from 'node:test';
import assert from 'node:assert/strict';
const {createUniverseImportMachine,parseUniverseFile} = await import(closeURL(closeResolve(CLOSE_ROOT,"src/iqs-universe-import/index.js")).href);
const {createFakeAdapter,ownerError,ZHONGWEI_A,ZHONGWEI_B} = await import(closeURL(closeResolve(CLOSE_ROOT,"tests/js/helpers/fake-adapter.js")).href);
const connectionIdentity={universe_id:'default',as_of:'2026-10-28',connection_ref:'r1-root-independent'};
const upload=()=>parseUniverseFile(new TextEncoder().encode('中微公司,,CN\n'),{format:'csv',encoding:'utf-8',columnMapping:{has_header:false,name:'0',ticker:'1',market:'2',security_type:null},displayName:'synthetic.csv'});
function select(m,id,entity='ent-zw-a',security='sec-zw-a'){return m.selectCandidate(id,{entity_id:entity,security_id:security,selection_reason:'explicit synthetic confirmation'});}

test('R1-ADJ-01: preview must revalidate selection after asynchronous digest, not only before it',async()=>{
 const a=createFakeAdapter({preview:async args=>({can_apply:true,blocked_reasons:[],preview_token:'token-'+args.entity_id,payload:{request:{...args}}})});
 const m=createUniverseImportMachine({adapter:a,connectionIdentity});await m.loadUpload(upload());const id=m.rowIds()[0];await m.resolveRow(id);select(m,id);
 const subtle=globalThis.crypto.subtle;const original=subtle.digest.bind(subtle);let release,enter;const gate=new Promise(r=>release=r);const entered=new Promise(r=>enter=r);
 subtle.digest=async(...args)=>{enter();await gate;return original(...args);};
 try{
  const pending=m.previewRow(id);await entered;
  try{select(m,id,'ent-zw-b','sec-zw-b');}catch{}
  release();await pending;const row=m.getRow(id);
  if(row.owner_preview!==null)assert.equal(row.owner_preview.payload.request.entity_id,row.selected_entity_id,'the hash await must not attach candidateA preview to selected candidateB');
 }finally{release();subtle.digest=original;}
});

test('R1-ADJ-02: a resolve response started before timeout must not erase unknown across save/remount',async()=>{
 let delay=false,release,enter;const gate=new Promise(r=>release=r);const entered=new Promise(r=>enter=r);let posts=0;
 const a=createFakeAdapter({resolve:async()=>{if(delay){enter();await gate;}return {state:'ambiguous',candidates:[ZHONGWEI_A,ZHONGWEI_B],truncated:false};},apply:async()=>{posts++;throw ownerError('timeout');}});
 const m=createUniverseImportMachine({adapter:a,connectionIdentity});await m.loadUpload(upload());const id=m.rowIds()[0];await m.resolveRow(id);select(m,id);await m.previewRow(id);
 delay=true;const pendingResolve=m.resolveRow(id);await entered;await m.confirmRow(id);assert.equal(m.getRow(id).state,'unknown');release();await pendingResolve;
 const saved=m.getDraft();const b=createFakeAdapter();const next=createUniverseImportMachine({adapter:b,connectionIdentity});await next.loadDraft(saved);
 let refused=false;try{await next.resolveRow(id);select(next,id);await next.previewRow(id);await next.confirmRow(id);}catch{refused=true;}
 assert.equal(b.calls.filter(c=>c.method==='applyMember').length,0,'stale read must not launder unknown attribution and enable a second POST before inspection');
 assert.equal(posts,1);assert.equal(a.calls.concat(b.calls).filter(c=>c.method==='inspectMember').length,0);
});
