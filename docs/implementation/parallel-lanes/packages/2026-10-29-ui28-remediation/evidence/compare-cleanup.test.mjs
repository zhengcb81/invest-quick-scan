// Synthetic controller regression. Original assertions retained; imports rebased.
import {resolve as r1Resolve} from 'node:path';
import {pathToFileURL as r1URL} from 'node:url';
const R1_ROOT = process.env.IQS_R1_COMPONENT_ROOT || "C:/Users/郑曾波/Projects/iqs-comparison-view-lab";
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';import cp from 'node:child_process';import os from 'node:os';import {EventEmitter} from 'node:events';import {syncBuiltinESMExports} from 'node:module';
const {removeDirWithRetry} = await import(r1URL(r1Resolve(R1_ROOT, "tests/browser/cdp.mjs")).href);
test('C28-06 cleanup rejects a sibling-prefix escape before any destructive process/filesystem call',async()=>{
 const original={existsSync:fs.existsSync,rmSync:fs.rmSync,spawn:cp.spawn,tmpdir:os.tmpdir};const calls=[];
 try{
  fs.existsSync=()=>true;fs.rmSync=(path)=>{calls.push({kind:'rmSync_intercepted',path});};os.tmpdir=()=> 'C:\\owned\\temp';
  cp.spawn=(command,args)=>{calls.push({kind:'spawn_intercepted',command,args});const emitter=new EventEmitter();queueMicrotask(()=>emitter.emit('close',0));return emitter;};syncBuiltinESMExports();
  let rejected=false;try{await removeDirWithRetry('C:\\owned\\temp-sibling\\victim',1);}catch{rejected=true;}
  console.log('SAFE_STUB_TRACE',JSON.stringify({rejected,intercepted_calls:calls,actual_spawn_calls:0,actual_filesystem_deletes:0}));
  assert.ok(rejected && calls.length===0,'resolved strict descendant containment must reject sibling-prefix path before any destructive cmd/rm call');
 }finally{Object.assign(fs,{existsSync:original.existsSync,rmSync:original.rmSync});cp.spawn=original.spawn;os.tmpdir=original.tmpdir;syncBuiltinESMExports();}
});
