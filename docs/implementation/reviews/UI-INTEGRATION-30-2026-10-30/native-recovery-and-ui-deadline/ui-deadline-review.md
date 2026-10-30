# UI request deadlines: independent bounded review

**Passed; open findings []**. Reviewer `/root/accept_compare28`, independent of implementation author `/root`.

Static Git delta against63f4627 contains exactly five paired changed lines. After removing only the new timeout expressions, every changed line equals its original line byte-for-byte: batch resume180s (pause/abandon stay30s), task resume180s (inspect/retire stay150s), tasks preview150s, tasks start180s, import preview120s. No endpoint, method, body, retry, permission, lifecycle or result interpretation changes occur. Raw pins and diff SHA are in final-review.json.

Independently executed: Node syntax **1P** and two original no-retry scenarios **2P** (`api`, `snapshot-write-timeout`) against stable actual source bytes, in owned cwd with credentials stripped and native-network denial. API scenario verifies preconnect POST denial, original error propagation and no duplicate writes. Write-timeout scenario emits exactly one batch-resume POST, then marks the snapshot stale/disables unsafe actions instead of retrying. Both use the original fake-DOM/fetch harness, not actual8766/owner calls. Root's broader47P suite is separate author evidence and is not claimed as independently rerun here.

The original request helper still uses one fetch with CSRF/same-origin, AbortController and finally clearTimeout. Longer budgets fit the observed90–110s preflight windows. If the new finite deadline is exceeded, the UI still treats the result as uncertain: abort does not prove backend cancellation, and explicit original-state inspection remains necessary. This review does not claim a live150/180-second elapsed test or unlimited backend completion.

No source writes, real UI/model/API requests, servers, profiles, temporary DBs or retained child processes. Test source/static fixtures were read-only; answer data was not copied into the report. All owned subprocesses exited. Logs, original harness, static diff and network guard remain as evidence.

TTL design and command templates requested in the same task are at ../ttl-closeout-preparation/README.md. They distinguish the historical-cutoff expired refresh from a separately legitimate cutoff30 fresh-reuse experiment; no confirmations/admissions/paid requests were executed.
