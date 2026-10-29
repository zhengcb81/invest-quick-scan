// Synthetic startup rejection; no browser start. Finally cleans the uniquely created probe root.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {resolve as closeResolve,dirname as closeDirname} from 'node:path';
import {pathToFileURL as closeURL} from 'node:url';
import {rmSync as closeRemove,realpathSync as closeRealpath} from 'node:fs';
const CLOSE_ROOT=process.env.IQS_R1_COMPONENT_ROOT || 'C:/Users/郑曾波/Projects/iqs-comparison-view-lab';
const {BrowserSession}=await import(closeURL(closeResolve(CLOSE_ROOT,'tests/browser/cdp.mjs')).href);
test('launch rejection cleans its owned profile and closes the partially-started session',async()=>{
 const root=mkdtempSync(join(tmpdir(),'accept-launch-failure-'));
 const originalStart=BrowserSession.prototype.start;
 const originalClose=BrowserSession.prototype.close;
 let closeCalls=0;
 BrowserSession.prototype.start=async function(){throw new Error('synthetic_browser_start_rejected');};
 BrowserSession.prototype.close=async function(){closeCalls++;return originalClose.call(this);};
 try {
  await assert.rejects(BrowserSession.launch({executablePath:'synthetic-no-spawn',tempRoot:root}),/synthetic_browser_start_rejected/);
  const profiles=readdirSync(root).filter(p=>p.startsWith('profile-'));
  console.log(JSON.stringify({kind:'safe_boundary_stub',actual_browser_processes_spawned:0,close_calls:closeCalls,profile_leftovers:profiles.map(p=>join(root,p)),owned_root:root}));
  assert.equal(closeCalls,1,'launch must close a partially-started session when start rejects');
  assert.equal(profiles.filter(p=>existsSync(join(root,p))).length,0,'failed launch must release its profile');
 } finally {BrowserSession.prototype.start=originalStart;BrowserSession.prototype.close=originalClose; if(existsSync(root)){const target=closeRealpath(root),parent=closeRealpath(tmpdir());if(closeDirname(target)!==parent)throw new Error('owned_startup_probe_cleanup_outside_parent');closeRemove(target,{recursive:true,force:true});}}
});
