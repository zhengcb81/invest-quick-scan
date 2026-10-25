# Shared-engine finalization / live-driver review — round 2

- Reviewer: `/root/fix_bank21`; production author: `/root/inspect_production`; live driver owner: `/root`.
- Review remains read-only for product code. No API, search, original SQLite write, or production mutation was performed by this reviewer.

## New production hunks checked

StockQA `commit_standard_answers` now reuses an existing checkpoint only when the saved full body, work member, native receipt and provider attempt agree, then asks the original lifecycle to reseal its delivery. It neither claims a new lease nor sends a model request. The main finalizer uses this seam for both new and reused checkpoints and exposes real delivery states.

The reviewer identified an unconditional `status=completed` despite delivery sealing remaining absent/blocked. The author fixed this: `completed` now requires all original delivery states to be `ready` or `delivered`; otherwise the result explicitly reports `checkpointed_delivery_pending` and the pending question IDs. A `ready` package is sealed and waiting for delivery; it is not an assertion of a StockWiki ACK.

## Independent rerun after those production changes

- Main finalization suite: **11 passed in 3.48s** — `main-finalization-round02.txt`.
- StockQA mapper + native-input inspection suites: **31 passed in 6.33s** — `stockqa-finalization-round02.txt`.
- Source assertions and units include partial multi-question checkpoint save followed by a storage failure, same original answer retry, completed checkpoint reuse, altered saved answer refusal, stale/foreign lease refusal, and checkpoint-with-failed-seal remaining pending until resealed.
- These are still engineering unit/mapper checks. They do not independently prove public owner admission or financial accuracy; actual original-software searched singleton E2E remains pending its separate evidence.

## Live driver review feedback sent before actual API execution

The initial `run_live.py` had the correct original authority passed to the lifecycle, an original external retrieval policy, the original cost resolver, enabled thinking asserted at the real SDK wire, a crash boundary after durable safe native observation, and network denial/key removal during recovery. The original work-store DDL confirms `actual_cost_micros` is the correct budget column.

The reviewer requested these concrete corrections before treating the live result as acceptance:

1. Hash complete canonical rows of native responses and external operations, not only their counts; the initial script hashed only budget rows. Keep hashes only, never copy prompt/response bodies to thin evidence.
2. Require both finalization results to be `completed` with each delivery state `ready`/`delivered`; a checkpoint alone must not make the driver emit a successful production finalization result.
3. Require a nonempty source-pin set covering the driver, reviewed finalization sources and actual run/budget/search/rate inputs. A caller-provided empty list must not bypass frozen-source checks.
4. Resolve and enforce the isolation boundary for writable deployment/workspace/work-store/runs/input paths before public `prepare_execution`; read-only source code/release paths may remain external. The initial top-level `isolated=true`/`run_root==BASE` check alone did not enforce those subordinate paths.

The controller is implementing those driver changes. This report does not pre-count them as fixed or a live run as passed.

## Operational boundary

The original external-context-use proof supports singleton work. This round can qualify only the searched singleton shared-engine→original-owner path. Native multi-question packs without that genuine search proof must remain research-only / refused for formal checkpoints. The author confirmed this constraint; no searched pack positive is fabricated.

## Status

Scoped finalization source and its updated unit/mapper cases passed independent checks. Final driver, actual original-software E2E and real live/recovery artifacts require the next review round. Financial accuracy and full-project production readiness remain unassessed.
