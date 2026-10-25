# Generation 3: exact original URL copying, same native production path

This is a new experimental generation, not a reinterpretation of the two unsuccessful saved answers. The original generation-1 score/fact semantic failure, generation-2 URL-copy failure, all saved responses/receipts/fees and executed source locks remain unchanged. Both failed runs have zero formal checkpoints, standard answers or deliveries. The generation-2 readonly diagnosis is `generation2-safe-diagnosis.json`; no answer/context text is included.

## Root cause and scope of change

Generation 2 passed the original IQS semantics: score/scored, zero fact items, five metrics, four citations. StockQA correctly rejected two citation URLs. They matched a provided page path but omitted original query parameters (`trk`, and `lang`/`type`). Dates were within cutoff. Stripping queries can change page meaning, so neither the saved answer nor the exact-source validator was altered.

Readonly reconstruction used the original external-context builder/binder, the current unchanged lease and the original default real `time.time`. Its context hash `e6606976...` matched the actual use proof. All five provided URLs, including three with queries, remained verbatim in the original binding encoding. Original work-attempt combined-system/prompt hash, native messages-text hash and request-payload/saved-output binding all matched in their correct domains. The original pinned SDK appends that encoding unchanged and verifies its presence before physical send. A fake active owner was not manufactured to invoke the guarded renderer. The original database hash was unchanged throughout. Earlier diagnosis clock/owner-boundary and hash-domain mistakes are retained as separate thin JSON, not described as product failures.

Only new-request `typed_semantic_rules` change. Both score/fact instructions require `evidence[].url` to be copied exactly from the actual provided `sources[].url`, including query/fragment and `lang/type/trk`; no cleaning, completing or inventing URLs. Usually two directly supporting sources suffice, without a hard count/filter. Unknown dates remain null and inadequate evidence remains inadequate. Original `standard_prompt`, original question objects and renderer fingerprint `6b221598394f5c23a5f724c0b9bac895bcb44eee87c9189285eb605a6ebf21fe` stay unchanged. No URL rewriting or looser source qualification was added.

## Root-controlled original native continuation

The root waits for the real generation-2 lease expiry, then uses the original known-response resolution/retry-decision/admission APIs to obtain source generation 2 -> target generation 3. No early lease release, clock rollback, private handle injection, deleted history or new budget is permitted. The existing shared budget cumulative priced amount before generation 3 is obtained from the actual cold snapshot (root observed 19129 micros, a rate-card estimate rather than invoice).

Default new paths are `runs/r25-live/typed-generation3/` and `run_generation3.py`. Config requires generation 3, source work generation 2, the original matching retry decision and at most one model request. The driver explicitly binds original public singleton/thinking-enabled/16384 execution controls before factory checks and reuses them in task/runtime.

The new search policy preserves the original generation-2 policy bytes/query ID/TTL. Cache reuse is decided by the existing native coordinator; no receipt is copied and no cache flag/TTL/operation is fabricated. If the original cache keys require a fresh generation-specific operation, original budget/request guards apply. Actual new search HTTP is never hardcoded as one.

Cold sends at most one model post through the original SDK and records a fixed safe failure code on rejection, never arbitrary exception/model text. It crashes with exit 86 only after the same production v2 semantic/source gate passes. Otherwise the safe answer remains invalid, with no automatic repair or formal success. A new keyless/network-denied process resumes the original safe response, finalizes twice and requires ready/delivered and exact reuse with original ledger/context/decision hashes unchanged. Ready is not downstream ACK or financial correctness.

## New thin reporter

`real_summary_generation3.py` retains the original strict read-only store, original task-loader/run-manifest checks and original resolver/snapshot algorithms. Missing actual result returns `not_ready`/3 and creates no summary. It follows immutable original `owner_control.source_work_item_id` backwards through generation 2 and generation 1, listing both invalid model safes, both successful historical searches and the original local unknown reconciled `confirmed_not_sent` at zero.

For sources reused by a new answer, receipt HTTP/fees remain attributed to the historical operation. The reporter compares original operation creation time to cold-start time and original ledger operation-count deltas, reports a known subset and marks totals unknown if not complete. It never calls a historical receipt's HTTP a new send merely because the new answer uses it. New generation-3 model/native usage and original resolver estimate, new-cost ledger delta and shared cumulative budget are separate. Cash unknown stays unknown; estimates remain non-invoice. No body, reasoning, context or lease token is published.

## Source and test evidence

Author source freeze is `generation3-authored-sources.json` (prompt, new test, new driver/reporter and their coordination tests). Any root formatting/source change must be explicitly re-frozen before paid execution. Original generation-2 driver `80ce...`, reporter `b473...` and source pins `6137...` are unchanged.

- URL prompt RED 2F/1P -> GREEN 3P: `generation3-url-rules-red.*` / `generation3-url-rules-green.*`. A first wrong test path produced no tests and is separately preserved in `generation3-url-rules-path-error.*`, not counted as the RED phase.
- The existing actual request-construction capture test passed, `generation3-url-actual-request.*`: new rules reach the original Runner stable prefix, whose hash updates while original questions remain equal.
- Driver coordination: `generation3-driver-offline.*`, 12P/0.57s, synthetic original-control predicate only, not an admission positive.
- Reporter coordination: `generation3-summary-offline.*`, 12P/0.52s, including exact task loader, legacy rejection, historical two-generation chain and old receipt/new HTTP separation.
- The root-requested single combined regression of the original v2-green 54 cases plus the new URL three is recorded separately in `generation3-combined57.*` when complete. It does not repeat the driver/reporter coordination units.

All author tests use their own short `C:/Temp` root, remove keys, and clean that exact root. No actual owner database was written and zero APIs were invoked by this author. Whole-node independent review is requested from `fix_bank21` together with `review_bank21`'s original control helpers; it does not substitute for the root's later actual cold/recovery/summary evidence.

Whole-node review found the initially assumed history key was wrong. The final reporter uses only actual original owner_control.source_work_item_id, without an alias fallback. generation3-owner-control-dto-observed.json is a read-only public actual DTO projection with unchanged DB hashes, explicitly not permission. Its exact field is used in synthetic history tests: real field succeeds, wrong source_work_id alias and a broken link reject. RED 2F/12P and GREEN 14P are preserved separately in generation3-summary-real-dto-red.*/-green.*. Original initial 12P matched the wrong assumed field and is retained as intermediate evidence, not claimed final.
