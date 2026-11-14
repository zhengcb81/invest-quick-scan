// Exercise the current UI's public modules against the live, isolated IQS HTTP service.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const [uiRoot, origin] = process.argv.slice(2);
assert.ok(uiRoot && origin, 'usage: workbench_public_http.mjs <ui-root> <iqs-origin>');
const nativeFetch = globalThis.fetch;
const requests = [];
globalThis.fetch = async (input, options = {}) => {
  const path = String(input);
  const method = options.method || 'GET';
  requests.push({path, method});
  return nativeFetch(new URL(path, origin), options);
};

const storeUrl = pathToFileURL(`${uiRoot}/src/app/store.js`).href;
const apiUrl = pathToFileURL(`${uiRoot}/src/app/product_api.js`).href;
const firstStore = await import(`${storeUrl}?integration=first-open`);
const firstApi = await import(`${apiUrl}?integration=first-open`);
await firstStore.load({partial: true});
assert.equal(firstStore.store.snapshotSources.bank.status, 'available',
  JSON.stringify({sources: firstStore.store.snapshotSources, warnings: firstStore.store.snapshotWarnings}));
assert.equal(firstStore.store.snapshotSources.roster.status, 'unavailable');
assert.equal(firstStore.store.answersSource.status, 'partial');
assert.equal(firstStore.store.answers.runs.length, 1);
assert.equal(firstStore.store.answers.runs[0].binding.state, 'unbound');
assert.ok(firstStore.store.snapshotWarnings.some(value => value.includes('integration partial')));

await firstApi.connect();
const formalBefore = await firstApi.request('results');
assert.equal(formalBefore.rows[0].canonical_name, 'FORMAL_OWNER_RECORD');

// A new module instance models closing and reopening the UI page.
const secondStore = await import(`${storeUrl}?integration=reopen`);
const secondApi = await import(`${apiUrl}?integration=reopen`);
await secondStore.load({partial: true});
assert.equal(secondStore.store.snapshotSources.bank.status, 'available');
assert.equal(secondStore.store.snapshotSources.roster.status, 'unavailable');
assert.equal(secondStore.store.answersSource.status, 'partial');
await secondApi.connect();
const formalAfter = await secondApi.request('results');
assert.deepEqual(formalAfter.rows, formalBefore.rows,
  'snapshot reload must leave formal result rows unchanged');
assert.equal(formalAfter.total, formalBefore.total);
assert.deepEqual(formalAfter.snapshot, formalBefore.snapshot);

assert.equal(requests.filter(item => item.path === '/generated/snapshot.json').length, 2);
assert.equal(requests.filter(item => item.path.startsWith('/generated/')).length, 2,
  'the UI reads exactly one snapshot per page open');
assert.ok(requests.every(item => item.method === 'GET'), 'the read-only UI flow sends no mutations');
assert.ok(requests.some(item => item.path === '/api/product/results'));
console.log(JSON.stringify({passed: true, snapshot_reads: 2, product_writes: 0,
  formal_result_preserved: true, requests}));
