# Shared-engine budget scope and repaired driver — round 3

- Reviewer `/root/fix_bank21`; production author `/root/inspect_production`; controller/driver author `/root`.
- Read-only production review; no API call or original state mutation by this reviewer.

## Production budget-scope correction

The original ordinary Q09 lifecycle marked its own reservation while the native research SDK required its own durable budget binding. The conflict caused the actual software E2E to stop before model dispatch; it was not fixed by deleting the SDK guard.

The inspected correction makes `research_budget_managed` an explicit keyword defaulting to `False`. The normal Q09 path retains its own-reservation behavior. The research path requires transport management, an original ApprovedRefreshSession with an original native OwnerRefreshSession, both stores identical to the lifecycle store, and present budget/route data. It omits only the ordinary own-reservation marker. OwnerResearchServices still verifies the original approved policy projection and route, rechecks frozen inputs, enters this scope, then binds the native research durable budget. `require_budgeted_research_send` still rejects absent durable budget binding and incompatible ordinary reservation flags.

Independent final StockQA mapper/inspection rerun: **36 passed in 2.68s** (`stockqa-finalization-round03.txt`). The narrow unit owner objects are explicitly doubles; they do not qualify admission. No budget-scope bypass was found in the actual approved-service execution path.

## Driver issues from round 2 closed in source

The reviewer reread the updated `run_live.py` and confirmed:

1. Complete external-operation and native-response rows now have canonical hashes alongside budget hashes. An independent temporary-SQLite probe mutating either record body without changing row count detects both mutations: `ledger-probe-results.json`, **passed**. It makes zero network requests and cleans its temporary directory.
2. Both first and repeated finalization must report `completed` and every observed delivery state must be `ready` or `delivered`.
3. Source pins must be nonempty, unique and cover the driver, engine/task/owner/SDK/lifecycle sources and run/deployment/budget/search/rate/authority inputs.
4. Writable deployment state, input bundle and budget locations are resolved within the exact isolated root; links are refused before public execution preparation.
5. The pin-list file's exact SHA is carried in the cold proof and must be unchanged during recovery, preventing a regenerated pin list from silently approving changed code between phases.

No further static API-execution blocker was found in that version. Actual run inputs/pins were not yet finalized at this review point, so these source checks do not count as the live experiment passing.

## Independent source-observation check

The reviewer separately hashed all **8** executed/current files in the author's pre-E2E source observation. All actual files match their recorded SHA and their counterpart exactly: `round03-source-verification.json`. This verifies the candidate source pairing; it does not turn a pending E2E into a success.

## Remaining acceptance

The original-software searched singleton scored/checkpoint/delivery positive is still running in its explicit isolated runtime. Final owner input/source pins and cold/recovery artifacts must be reviewed afterward. Singleton proof limits, financial accuracy remaining unassessed and no automatic StockWiki ACK assertion still apply.
