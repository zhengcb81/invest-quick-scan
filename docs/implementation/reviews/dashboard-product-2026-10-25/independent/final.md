# Independent major-node review: passed

Reviewer `/root/review_ui_product27` is a different agent from coordinator `/root`. Product source was reviewed read-only; the reviewer wrote only owned evidence and temporary fixtures. All temporary fixture directories were deleted after the checks. No paid API or real production-store mutation was performed by this reviewer.

The final 40-file byte manifest is `reviewed-source-inputs.json`, aggregate SHA256 `4518b9510e0b2c07cc04305349c812b744d3ebda74064c95ab87f4a593ca69ed`. Source fixes after this manifest would require review of the changed bytes. The coordinator must bind identical Git blobs to the final commits rather than inventing a commit before it exists.

## Findings closed

- Quality/recovery/pending views and frozen paging now reach the original StockWiki grammar. Thin snapshot references are bounded, selection-bound and reject stale or changed selection.
- Task controls use the real `run_id`, display separate process and launcher state, and do not claim that a process exit proves business completion.
- Import bundles are independent of execution registrations; actual manual-pin and membership-reason DTOs are rendered.
- Setup checks the original execution references even on first access; exited processes permit setup, unknown/running processes block workspace changes.
- HTTP rejects bad Host/Origin/CSRF, duplicate/nonfinite/malformed JSON and deeply nested bodies. The real initial nested-body counterexample now passes after an explicit iterative depth bound of 64.
- The real unknown-process counterexample is closed at the mutation boundary: needs_original_inspection plus non-readonly original work cannot resume, even by direct POST. The same independent probe changed from one actual fake subprocess invocation to zero and `original_process_unknown`.
- Exact ACKs now return to the original StockQA outbox after independent receiver binding. Foreign stores, changed hashes and wrong observation/work mappings are rejected by the original API; partial acceptance can retry with the original exact ACKs without reapplying completed work. Rejected/conflicting receipt branches are also reconciled without claiming delivered.
- Explicit `available=false` is respected even if registration exists. Existing model revision, counterevidence and original record details are visible without deriving new conclusions.
- Missing original model policy returns an unenabled template and remains editable; reading it does not save or enable a second policy. Actual save still uses the original StockQA validator and revision guard.

## Independently verified results

Final execution and HTTP tests: **35 passed / 30.25 seconds**. Final real frontend ESM scenarios: **9 passed / 3.720 seconds**. Stable original owner gateway: **11 passed**, and original StockWiki readonly import preview: **8 passed / 2.62 seconds**. The original StockQA ACK probe and the persisted-unknown-process red/green probe also passed. Counts from intermediate runs are not added again as distinct tests.

Open findings: **none for the reviewed implementation scope**. This is a source/functional boundary review, not financial qualification or proof that every company has answers. Registered-bundle execution is available; automatic whole-pool planning and dispatch are still explicitly unsupported. The coordinator's real browser/retained-package acceptance and README/PWF consolidation remain separate deliverables and must be reported truthfully.
