# CATL partial preparation: independent read-only diagnosis

Examined preparation `prepare_190b14f7583f4258920faab1ff826765` and original StockWiki / StockQA source. No original CLI, grant, confirm, admission, model, network, database write, or external-repository edit was performed. One SQLite inspection used `mode=ro`, `PRAGMA query_only=ON`, and an explicit read transaction. No API keys, answer bodies, or private reasoning were read.

## Conclusions

1. `subject_contract_output_invalid` does **not** establish invalid company identity, insufficient budget, or policy dialect mismatch. It establishes failure of a child IQS contract result/envelope, whose actual contract rejection reason is discarded twice.
2. The strongest observed explanation is a shared-budget mutation between the stored scope-2 owner preview and an installation recheck. Original records show a real budget/send event inside that exact 57-second window. This is strong supporting evidence, **not conclusive proof of which failing contract operation or read timestamp**: the child transport deletes its temporary input and records neither operation nor safe rejection details on failure.
3. The original QA read-only busy path also loses its reason, but its source path ends with `refresh_owner_preview_rejected`, **not** `subject_contract_output_invalid`. A busy read alone is therefore not a source-supported explanation for this particular observed error.
4. The current dashboard has **no phase-resume route** for this partial preparation. `reconcile` only recovers a complete saved result. For the observed partial, reconcile will keep `automatic_retry:false`; it cannot install scope 2, promote scope 1, or invent `applied.json`. After original inspection, use the original job's abandon action and a new preparation with the existing original unfinished bank/work reused. Do this after the shared native execution has safely settled or been paused/drained through its original controls; do not kill/repost an in-flight request. Abandon preserves every original owner record and registration.

## Observed artifacts and timing

- Scope 1 has `prepared-scope.json`, 33 questions, original admission `registered_with_executor:true`, confirmation `rc2_9f909c5b70c465e816d3931bcb2ebca95019be2248a35503a359ded0526e04ae`.
- Scope 2 `owner-preview.json` is ready, created `2026-10-28T13:17:23.109131Z`, expires `13:32:23.109131Z`, preview `rv1_3ed4fbc56b39e512993daccfc4f3ca9e60d132c1ba594609b845aec7cb4f8588`. Its three items are original pending generation-1 IQS_22 / IQS_23 / IQS_24. Quote: USD 24,529,567 micros remaining, 231 HTTP requests remaining, budget_available true. These times supersede the handoff's approximate 13:22 description.
- `apply-error.json` was recorded `2026-10-28T13:18:20.089467Z`: native module `stockwiki.quick_scan_refresh_owner_cli`, selector `--install-delegation`, exit 2, error `subject_contract_output_invalid`. It lists scope 1 complete and scope 2 only through owner preview. It explicitly prohibits automatic retry.
- In the shared `runs/u25-live/work.sqlite`, `PACK_BUDGET_844dba05420345208586836db41fe93b` has `created_at` and `send_intent_at` `2026-10-28T13:18:05.034069Z`, inside that preview→failure window, on route `mimo-pro-primary`. Its current row is settled (reserved 250,000 micros; actual 20,207 micros; counted request 1; in_flight 0). No completion/reconciliation event timestamp was inside that interval at the inspection.
- Deterministic native grant ID, computed with the original `install` algorithm from the stored owner principal, exact workspace, consumer and scope-2 preview, is `dg1_cf9c52f6831ba17b7852b5b083865a1b0b7da3a79c870635439691f4e7d7a5ba`. Its original delegation file does not exist. The candidate's `applied.json` also does not exist. This establishes absence at inspection, without executing a grant inspection CLI.
- Current owner configuration remains protocol `stockwiki.refresh_owner_policy/1.1.0`, policy version 6, quote schema 1.1.0, TTL 24h. No configuration was modified.

## Exact call chain and error loss

Paths below are relative to the named repository roots.

**IQS `scripts/dashboard_prepare.py`:** 1016–1019 saves the original ready preview; 1020 loads its original immutable record; 1022–1027 creates the native install spec with its exact record hash; 1030 invokes original install; 1031 only writes `grant.json` after success; 1032–1035 only confirms afterward; 1041 only admits afterward. `_native_cli` at 814–850 accepts the native error code and records module, selector and return code, but no nested contract operation/reason.

**StockWiki `stockwiki/quick_scan_refresh_owner_cli.py`:** 321 constructs `DelegatedApprovalService`; 324–325 selects `delegated.install()`. The final exception envelope at 360–397 preserves `.code`/`.error_code`, otherwise falls back to `refresh_owner_preview_rejected`.

**StockWiki `stockwiki/quick_scan_refresh_delegation.py`:** `install` begins at 374. It performs `_recheck(record)` at 398 and again at 428. The grant is saved only at 447, after both rechecks. `_binding` at 327–352 binds the exact original quote and budget policy byte hash. `confirm` at 480 and 500 repeats the full recheck before publishing confirmation. An actual contract error anywhere inside either install recheck thus happens before a new grant is saved.

**StockWiki `stockwiki/quick_scan_refresh_approval.py`:** `_recheck` 36–51 re-reads policy/principal, invokes `latest=service.preview(record['request'])` at 42, and calls `service.contract.validate_preview(original_preview, owner_state=latest['owner_state'])` at 43–44. It uses the entire freshly generated owner state.

**StockWiki `stockwiki/quick_scan_refresh_preview.py`:** executor inspection at 244 obtains original QA work/budget data. Lines 312–319 copy the quote and wrap budget-state hashes; 339 writes this quote into owner state; 345 calls the IQS `create_preview` contract. Every `_recheck` therefore performs fresh native work/budget reads, followed by original-preview equality validation.

**StockQAbyLLM `src/utils/quick_scan_refresh_inspect.py`:** 193 reads original shared budget status. Lines 321–334 compute the quote from remaining spend/reservations/request count; budget_state_sha256 includes **entire status + selected work + ledger reference**. Lines 411–417 separately hash shared ledger budget status. `quick_scan_work_store.py` 2969–3074 defines status, including spent, reserved, requests, in_flight, unreconciled and quota metadata. Thus another company's native send/reserve/settlement may change the quote/hash even while this company's subject, three items and policy stay unchanged and the remaining budget remains adequate.

**IQS `scripts/refresh_contract.py`:** `create_preview` 321 onward includes owner_state hash (396), exact items and quote (397–408), then hashes the entire preview. `validate_preview` 423–438 regenerates the expected preview using the **old original timestamps** and the **latest owner state**; 433–434 rejects any inequality with `refresh_preview_owner_mismatch`. This is not a threshold-only budget check. A change from 231 to 230 remaining requests, an in-flight count change, or a changed opaque status hash suffices.

**First error loss:** IQS `scripts/refresh_contract_cli.py` 37–41 catches ValueError/TypeError/etc and returns exit 2 with only `refresh_contract_rejected`, discarding `refresh_preview_owner_mismatch` (and all other detailed contract errors).

**Second error loss:** StockWiki `stockwiki/quick_scan_subject_authority.py` 108–135, inherited by `IqsRefreshContract`, maps bad JSON, any nonzero child return, and any invalid validation envelope to `ObservationImportError('subject_contract_output_invalid')`. The name comes from the shared transport class and does not attest a subject problem.

## Why read-only busy is a different path

StockQA `quick_scan_refresh_inspect.py` 56–59 refuses any `-wal`, `-shm` or `-journal` sibling with `refresh_executor_store_busy`; 64–70 uses SQLite mode=ro and query_only. Its CLI `quick_scan_refresh_inspect_cli.py` 47–66 catches this ValueError and exits 2 with generic `refresh_executor_inspection_rejected`. StockWiki owner CLI 216–217 sees nonzero QA exit and raises plain `ValueError('refresh_executor_inspection_unavailable')`; its final catch then emits fallback `refresh_owner_preview_rejected`. Therefore busy is masked, but not through the IQS contract envelope path responsible for `subject_contract_output_invalid`.

Transport timeout has another separate path (`subject_contract_transport_unavailable` in the IQS-contract wrapper; owner preview fallback for the raw QA TimeoutExpired). It should not be conflated with this observed code.

## Can normal concurrent execution make prepare impossible?

Not inevitably: scope 1 completed during this same preparation, and a long native request can leave budget status stable while it is in flight. However a change at **any** of the repeated preview/install/confirm/fresh-admission checks invalidates the exact original volatile quote. Frequent native pack sends or settlement events can make successful preparation very unlikely. This is a liveness/diagnostics weakness, not proof that adequate budget grants permission despite changed binding.

The most conservative operational remedy is a quiet original shared-ledger interval: wait for existing native work to finish, or use original pause/drain controls and wait for in-flight work to settle, then create a fresh preview/prepare. No fake clock, lease edit, preview rewrite, direct checkpoint, CP creation or ambiguous repeated install is warranted.

For this live session, root reports that original UI batch `batch-e427...` is now draining, while Tencent's current 33-question entity scope continues to safe completion. The proposed authorized sequence is: wait for its safe completion and a quiet budget snapshot; inspect the CATL original partial and known absent scope-2 grant; abandon the old preparation job through its original UI; create a complete new two-scope CATL preparation using the original retained work/bank; then resume the original batch and start CATL separately through original controls. Keep the existing original three-request concurrency setting. The quiet preparation interval is this run's safe operation order to preserve immutable authorization, not a diagnosis of inadequate budget or invalid identity.

## Current partial-preparation recovery contract

IQS `dashboard_prepare.py` 635–645 returns saved `applied.json` if complete, but rejects an `apply-started.json` without complete result as `preparation_partial`. Lines 666–680 make status `prepared` only from complete `applied.json`; individual prepared scopes remain `partial`. The all-scope `applied.json` is published only at 987 after the whole scope loop. Line 972 also stamps scope-1 bundle with both expected scopes, so promoting it alone would omit explicitly required security scope.

IQS `dashboard_jobs.py` 172–193 reconcile registers an existing complete result or `native.status=='prepared'` with result; otherwise it returns `automatic_retry:false`. It never re-enters apply or resumes a native phase. Original abandon at 195–210 only ends waiting/auto-registration and preserves original owner changes. A subsequent fresh preparation can use original bank reuse (`dashboard_prepare.py` 917–930) and native ledger attachment to existing logical work. Do not fabricate a result, delete `apply-started`, re-run `_prepare_scope` directly, or use scope-1 bundle as a complete company preparation.

If a product-level phase resume is desired later, it needs a new explicit owner-inspected operation: prove prior process completion, load and verify immutable prepared-scope artifacts, inspect original grant/confirmation/admission state, preserve ambiguity as blocked, create a **fresh** preview for the unfinished scope, and run original native paths under current checks. This is new functionality; it is not exposed by the current `reconcile` button.

## Minimal isolated tests and safe fix recommendations (design only)

1. Pure contract fixture: take a synthetic valid request/owner-state, create original preview, then independently alter only max_http_requests or budget_state_sha256. `validate_preview` should reject with `refresh_preview_owner_mismatch`; unchanged state should pass; now after real expiry should reject. No real store or owner authorization needed.
2. Delegation service fixture: use synthetic in-memory preview service whose successive `_recheck` latest state changes only shared-budget hash. Verify install refuses and the synthetic grant store receives zero saves. Test both the first and second recheck, unchanged-state success, and changed identity/policy refusal. Never call original live install.
3. Transport diagnostic fixture: fake subprocess completion containing the fixed IQS rejection envelope. Today this yields `subject_contract_output_invalid`; preserve that outward compatibility if required while carrying an **allowlisted** structured cause (contract operation, stable rejection code, input digest), without full input/output/stderr. Separately test malformed output remains invalid and cannot be mistaken for a legitimate rejection. The first diagnostic improvement must retain a stable safe code in the IQS CLI instead of discarding it; otherwise the outer layer cannot reconstruct it.
4. QA busy fixture: a private disposable fixture DB with a private sibling journal sentinel should cause QA inspect refusal, not any write or migration; test the owner wrapper's separate receipt path. Diagnostics should preserve `refresh_executor_store_busy` as a safe allowlisted native read refusal rather than reporting an opaque subject-contract error.
5. Dashboard partial fixture: `apply-started` + one prepared scope + other scope preview + no `applied` must remain partial after reconcile and must not call native install/confirm/admission; abandon must retain artifacts. A complete saved result should reconcile without repeating native owner mutations.

The minimal safe code change is **diagnostic propagation and a clear shared-budget-changed refusal**, with no permission or equality relaxation. An eventual change from exact volatile quote equality to a signed/immutable spend ceiling plus current conservative capacity validation would change the trust contract and needs deliberate original-owner schema/design work. It is not a safe ad-hoc fix during this live run.

## Limits of this diagnosis

The original failed subprocess operation/input and detailed reason were not persisted; its temporary contract directory was deleted. Exact equality code plus the send event establishes a very plausible failure mechanism, not historical certainty. Other contract operations reached during recheck (request/policy/create-preview), malformed envelopes, or other owner-state drift also yield this same generic code. The current available artifacts cannot distinguish them conclusively. Add bounded safe rejection diagnostics and prove the mechanism with an isolated fixture before attributing the historical event as a confirmed single root cause.
