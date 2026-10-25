# Independent UI product review, round 1

Reviewer: `/root/review_ui_product27`; implementer/coordinator: `/root`. Read-only product review; only review evidence and isolated test fixtures are written in this directory. No paid API, real identity change or real database import was performed by the reviewer.

Scope: root dashboard service/transport/owner/execution/launcher, UI product pages/API client/native server, StockWiki public import preview and their focused tests. The review uses actual original owner DTOs and public contracts, including the path-bound observation-store identity and PRE/POST dispatch contract. It does not grant financial qualification or full-cohort coverage.

## Findings raised and implementation feedback

1. Results `view` and original frozen `snapshot` were dropped at the service/gateway boundary. Quality/recovery/pending controls did not affect selection; paging could span new snapshots. Coordinator and owner agent added original forwarding plus bounded thin snapshot references. Final regression pending.
2. Task controls preferred `bundle_id` over actual `run_id`, producing nonexistent task-control routes. The normal process fields were not rendered. Frontend agent corrected ID priority and added native DTO coverage.
3. The import selector read execution registrations instead of independent import registrations, making a valid import-only bundle invisible. Frontend agent corrected the source and added native DTO coverage.
4. Completed tasks retained launcher_state=running, preventing setup changes forever; fresh services skipped the active-task guard entirely before their first gateway load. Coordinator corrected the guard to inspect actual running/starting/unknown process state using the gateway.
5. Native member manual_pin and added/removal/restoration reason fields were not rendered. Frontend agent corrected native field names.
6. Deeply nested JSON needs an explicit depth bound. Catching decoder RecursionError alone is insufficient: under the current pytest recursion limit a 1100-level body parses, then recursive response handling returns 500. HTTP isolated regression reproduced this: 12 passed, 1 failed. Open until bounded validation is rerun.
7. Import returns actual StockWiki ACK but, at this review point, does not feed exact ACK into the original StockQA outbox. The standalone import/view feature is real, but it must not be described as a complete product dispatch-to-delivered workflow until the original ACK consumer is connected or the missing functionality is explicitly retained as incomplete.
8. **P1: persisted unknown-process resume bypass.** `tasks()` correctly withholds resume for process_state=needs_original_inspection and non-readonly original work, but `control(..., 'resume')` checks only running/starting. The independent `review_unknown_resume.py` counterexample produced `allowed_actions_before=[inspect]`, `readonly_recovery=false`, yet `control_process_started=true` and one actual fake-owner process invocation. Such a state is produced by the gateway's own finish-error branch, so this is not merely arbitrary metadata corruption. Require the same unknown-state guard at the mutation boundary. No paid calls were made.

## Independently executed checks

- Root owner + execution focused tests: **26 passed in 29.99 seconds**. `owner-execution.junit.xml`.
- Frontend real Node ESM scenarios: **9 passed in 2.191 seconds**, including the new native DTO case. Invoked `python -B -X utf8 -m unittest discover -s ../iqs-question-bank-ui-lab/tests -p test_product_ui.py -v`.
- StockWiki original public readonly import preview: **8 passed in 2.62 seconds** from StockWiki cwd. `stockwiki-preview.junit.xml`.
- Root HTTP boundary: **12 passed, 1 failed in 7.34 seconds**; only the explicit nesting counterexample failed. `http.junit.xml`.

The first owner/execution attempt used a nonexistent basetemp parent, yielding fixture setup errors; creating the owned parent produced the successful rerun above. The first native preview invocation from IQS cwd lacked StockWiki on sys.path; the intended native cwd rerun passed. These are test-invocation corrections, not product failures.

## Scope still being integrated

Coordinator is exercising the actual retained CATL ready package, original target workspace and exact ACK; no copied-store positive is fabricated. Original paid request ceiling remains exhausted and unchanged. This review must be revisited after final integration changes. The current review is **not a final pass**.
