# Native publish/delivery lock contention: source-only diagnosis

The prior WAL repair remains valid. The new reported C failure is a real SQLite locking refusal, not evidence that the sidecar-existence bug returned. This diagnosis does not replay any real database operation or paid API.

## Confirmed critical-section risks

1. `quick_scan_saved_research_publication.py:312-419` holds one outer `store._transaction()` across the whole publication cohort. At line316 it calls `_authorize` again; that dispatches `StockWikiWorkDecisionAuthority.authorize -> inspect_confirmation -> _read_native_inspection` to the original owner subprocess (timeout80; current/fresh native inspection can be required). Nested store calls use SAVEPOINT and keep the outer writer lock.
2. The same outer transaction loops all members, writes checkpoint/side tables, builds complete C06 packages and binds original outbox consumers. `_complete_package` rebuilds/checks durable context and package, then `prepare_result_delivery` repeats checkpoint/full observation checks inside nested transactions. These protect integrity but extend the full cohort critical section.
3. `begin_result_delivery` at work_store.py:5777-5786 also calls `require_publisher` under its transaction. For schema3 without a preauthorized grant, require_publisher:594 re-enters native `_authorize`. The existing exact preauthorized_grant path is intentionally narrower and cannot be replaced by an unvalidated cached approval.
4. StockWiki `apply_decisions` at observations.py:416-420 calls SubjectBoundObservationStore._apply_one, which validates original receipt and bind_original via offline CLI after original insertion while holding its **separate** observation database transaction. This cannot directly prove which process locked the QA ledger.
5. QA strict schema/data validation scans original delivery/response/checkpoint rows. In rollback mode, long readers can delay a writer commit; its PENDING transition can block new readers. This is a plausible amplification to measure, not a proven historical attribution.

## Important distinction

BEGIN IMMEDIATE normally obtains RESERVED and permits readers. No explicit BEGIN EXCLUSIVE or journal/cache-spill reconfiguration was found in this work-store source. The controller's actual `PRAGMA user_version -> database is locked` trace demonstrates real contention, but source scope alone does not establish the blocking PID or whether commit PENDING, EXCLUSIVE, hot rollback or cache spill occupied the reader window. An 80-second configured subprocess timeout is not an observed hold time. The older generic preview failure likewise has insufficient retained information for a unique retrospective cause.

## Smallest safe action now

Allow M entity publication/delivery to finish, then repeat C's original native preflight and resume from existing immutable work. Serialize same-ledger write/admission/publication stages, while independent model HTTP stages may remain parallel under original budget/leases. No repeated model call, journal deletion, foreign-process kill, immutable=1, production journal-mode switch or timeout escalation is required to complete this acceptance.

## Follow-up root repair

First add metadata-only timings for BEGIN wait, transaction hold, commit and native validation phases. Keep answers, config, keys and SQL bound values out of the trace.

Then move pure schema/context/package derivation outside the write critical section. Bind the result to exact immutable input hashes/revisions/lease epochs and perform a short compare-and-swap plus group commit. **Keep the existing whole-cohort atomic checkpoint/outbox promise**; splitting 33 members into independent commits changes the contract. A changed source must reject the entire operation.

Do not merely delete the in-lock `_authorize`: current permissions and revocation must remain real native authority. Existing preauthorized_grant handling can be reused only under its exact original request/grant/source conditions; moving all remote checks outside may need an explicit versioned owner capability protocol. Test authority/source drift and crash boundaries before weakening any guard.

Future isolated cases should measure writer availability while a slow preflight validator waits, source/authority drift refusal, intact cohort atomicity, real rollback/WAL contention and zero duplicate paid attempts. No new implementation or tests were run in this source-only diagnostic.

Source heads at inspection: StockQA `4bb11b1b97b4d76cd28597fdf75a52412de34e29`; StockWiki `8cd239e346289a5af5b825bdb03c675ba576d2fa`. QA known_outcome_journal.py and work_decision_inspect.py had tracked edits; they were preserved and their actual relevant source bytes are pinned in report.json. CodeGraph structural lookup returned older IQS intake snapshots, so exact known current source files were read directly. No source or database writes occurred; only these owned diagnosis files were created.
