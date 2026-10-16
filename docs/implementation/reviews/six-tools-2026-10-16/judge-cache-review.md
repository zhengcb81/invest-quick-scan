# RESEARCH-JUDGE-03 / CACHE-PLAN-03 independent acceptance review

Scope: frozen `source/` packages, offline direct API counterexamples against frozen T0 inputs. No network, paid calls, keys, external-repository modifications, or source/candidate writes during discovery. Baseline expands six sessions to 72 slots, with four committed answers. Detailed original observations are in `judge-cache-scratch/source-counterexamples.json`; rerun with `python -B runs/six-tools-acceptance-2026-10-16-01/reviews/judge-cache-scratch/reproduce.py source`.

## Confirmed substantive defects (original source)

1. **J1 [P1] committed answer is not bound to revision hash** — `src/iqs_research_judge/adapt.py`, revision validation and committed-answer assembly. Change only `result.answers[0].summary` of a real T0 session, retaining all revision bodies/hashes: adaptation accepts two inconsistent final texts. Recommendation: verify final committed object against highest revision hash/body; require question identity consistency.
2. **J2 [P1] wrong blind private map silently loses judgments** — `src/iqs_research_judge/compare.py:58` and `blind.py` private-map construction. Import one valid judgment against seed A; compare using seed B's private map. It succeeds, reports one judged slot but zero mapped coverage. Recommendation: bind private map to canonical bundle fingerprint and enforce exact judged/pending partition of its slots before joining.
3. **J3 [P1] event-only receipt disappears** — `src/iqs_research_judge/metering_isolated.py:79`. With empty result receipts and one real receipt in `receipt_observed`, observed HTTP=0 and all usage/cost disappear. Recommendation: union result/event receipts by attempt_id, reject conflicting content, preserve receiptless failures separately.
4. **J4 [P1] missing cached usage becomes exact cheap estimate** — `metering_isolated.py` pricing loop uses `usage.get('cached_input_tokens') or 0`. With 100 uncached/100 output and absent cached field, it publishes a precise USD0.000075. Partial totals also imply a complete cache denominator. Recommendation: null incomplete totals/ratio/cost and expose known subtotal/coverage separately; price only matching historical date/provider/model.
5. **C1 [P1] unknown overall usage/cost/time becomes zero** — `iqs_cache_planner/measure.py` aggregation/output. One receipt with usage=null and no session wall yields total_input_tokens=0, output=0, session duration=0, recomputed USD0.000000 and cost-per-answer=0. The per-receipt unknown marker does not repair the falsely precise aggregates. Recommendation: keep explicitly named known subtotals, null incomplete aggregates and derived ratios; distinguish committed count from validated legal answers.
6. **C2 [P1] wrong provider/model receives historical DeepSeek price** — `measure.py` per-receipt pricing ignores rate-card provider/model. Synthetic unrelated provider/model produces precise 76 micro-USD under the DeepSeek card. Recommendation: enforce rate scope; absent or mismatched metadata must remain unpriced. Validate finite nonnegative rates and scoped UTC calendar rather than defaulting historical scope to any date.
7. **C3 [P1] expired prefix contributes to reusable lower/upper bounds** — `iqs_cache_planner/prefixes.py`, `det_share` and bounds assembly. Two identical expired company prefixes are flagged non-reusable but yield 15 shareable reuse bytes and lower=upper=15 even with min_block_bytes=10000. Recommendation: calculate eligible reuse separately, exclude expired/changed evidence/question versions; min-block must constrain upper bound, lower stays zero without actual routing/TTL timing evidence. Multiple scenarios are currently silently reduced to scenarios[0].

## Additional comparison concern

`compare.py` places strategy_id inside the equality key, so no different strategy can ever pair, even with identical company/evidence/questions/model/repeat/phase. Separate treatment identity from experimental controls: explicitly matched different treatments may be presented as controlled contrasts, while direct ranking remains refused unless the coordinator explicitly authorizes a cross-treatment ranking and complete real financial judgments exist. Unknown config must not establish an equal known control.

8. **J5 [P1] wrong accounting identity auto-passes** — `src/iqs_research_judge/reference_score.py:165`. The real CAPOI25 reference is "Google Cloud segment revenue, not operating income". A structured assertion using the same value 58705 but metric/definition "operating income" returns supported because that phrase occurs in the negated clause. Currency and periods can also be omitted. The independent counterexample is now included in source-counterexamples.json; the corrected candidate returns not_assessable and requires explicit dimensions/full accounting identity.

Precise additional original locations: J1 adapt.py:187; J2 compare.py:58 / blind.py:330; J3 metering_isolated.py:92; J4 metering_isolated.py:157; C1 measure.py:315,342,362; C2 measure.py:268; C3 prefixes.py:94,189.

## Candidate correction evidence

Both candidates are now package version **1.0.1**. Public carrier protocol IDs remain 1.0.0; corrected schemas allow null incomplete aggregates and add explicit subtotal/uncertainty fields. JUDGE private maps require regenerated canonical bundle bindings. This is a tightening of invalid-input validation and unknown semantics, not a claim that old incomplete maps still work. Each candidate has `docs/coordinator-acceptance-2026-10-16.md`; old handoff files remain byte-identical to frozen source.

Candidate direct-API evidence: `judge-cache-scratch/candidate-counterexamples.json`:

| Counterexample | Corrected outcome |
|---|---|
| altered committed answer | AdaptError, latest revision hash conflict |
| wrong-seed private map | ComparisonError, bundle binding mismatch |
| event-only receipt | one observed HTTP and 200 total input tokens |
| absent cached usage | input/cache ratio/cost null; known priced subtotal separately zero |
| Cloud revenue mislabeled as operating income | not_assessable |
| receipt usage absent | total input/output, complete cost and session-duration sum null |
| unrelated provider/model | unpriced, explicit rate-scope mismatch |
| two expired prefixes with 10000-byte min block | reusable byte subtotal and lower/upper bounds zero |

Additional meaningful regressions cover tampered pending slots, duplicate receipt conflicts, reviewer-forged computed checks, complete real scalar dimensions, future reference publication, matched different-strategy controls with direct-ranking refusal, finite nonnegative rates, explicit unknown SDK send state and multiple-scenario rejection. Repeated same session refs now refuse rather than collapse private anonymous slots; old synthetic blind seed fixtures were corrected to use distinct session identities. Synthetic event receipts were corrected to equal the result receipt for the same physical attempt; conflicting copies now fail.

Final isolated package runs: **JUDGE 65 passed; CACHE 77 passed**, exit 0, 0 skips/failures. Commands, write roots, timings and finally cleanup are in `judge-cache-scratch/regression-results.json`; full logs and JUnit XML are retained under that same unique review prefix. Network was denied by the coordinator guard; credential environment variables were not inherited. The test temporary roots were resolved inside the review root before deletion and no longer exist. The original source counterexample remains the RED evidence, not an interpretation of test counts.

Exact candidate changed-file inventory with byte lengths/SHA256: `judge-cache-scratch/modified-files.json` (21 JUDGE files, 13 CACHE files). This includes patch versions, `.codegraph/` ignores, current documentation, current output schemas, meaningful regression tests and five regenerated synthetic JUDGE examples. No external lab repository, frozen source, shared input or original handoff was modified. No commit was created by this reviewer; consolidated CAS/commit belongs to the coordinator.

## Remaining scope limits

Accepted-input-session scope is explicit. Three T1 session files generate 36 target slots; this does not certify a six-session/72-slot registered cohort or manufacture results for three unstarted sessions. Winner remains null without complete real judgments and permitted comparison controls.

The four T0 receiptless RuntimeError SDK failures are unconfirmed send states. The frozen trace does not establish a lost HTTP count or prove pre-send exclusion; the known 21 receipts and USD0.100300 receipt estimate remain valid. CACHE now retains lost_contact_sends=null, receiptless_sdk_failures=4 and complete_session_estimate_micros=null, while keeping the known priced receipt subtotal.

CACHE's legacy legal_answers denominator reflects committed answer objects from the original driver; it does not independently run the full frozen answer validator. This limitation is disclosed in its current acceptance document. Rate-card model identity is enforced when declared; callers should pass the frozen historical rate card with its explicit model. No actual financial judgment, production owner, G3/F05 closure, provider cache-hit measurement, current pricing or paid experiment is certified by this work.
