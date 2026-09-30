# S06 / MOD-19 confidence-anchor review

Read-only review of the current local worktree on 2026-09-27. No tests were run, no live API was used, and no external repository was accessed.

## Findings

**P2 — W15 acceptance does not yet exercise retrieval of the independent execution anchor.** The W15 task step requires dispatch callers to load an independently stored `expected decision_id`, and the S06 route tests verify that the execution API rejects a missing or mismatched ID. However, W15's `MOD-07.A01` acceptance assertion only checks snapshot round-trip fidelity and historical compatibility. It does not require the StockWiki store/dispatch path to retrieve the ID from trusted storage and reject a resealed snapshot before dispatch. Add that behavior to the W15 owner case so the implementation cannot satisfy the case by merely persisting route JSON and echoing its embedded ID.

**P2 — U04 acceptance does not cover historical missing-confidence rendering.** The U04 task step says router 2.0/2.1 snapshots with no confidence fields must be shown as historically unrecorded, without inference or invented values. `MOD-13.A01` covers current router 2.2 confidence labeling, model/time, low-score candidates, verified facts, and zero model calls, but contains no historical snapshot scenario. Add a browser assertion for a 2.0/2.1 record with absent confidence fields and require an explicit “not recorded” presentation with no synthesized company-quality score.

No P0/P1 implementation issue was found in the reviewed anchor changes. `validate_route_for_execution` now rejects a missing expected ID and compares a supplied value against the route's recomputed decision ID through `validate_recorded_route_execution`. The `compose-route` CLI requires the expected-ID argument, and the tests cover missing and mismatched IDs. As the code comments state, the API cannot prove where the caller obtained that value; W15 must source it from its own trusted store rather than from the pending route object.

The new MOD-19 A06 regression test covers the coordinated reseal case: it changes a selected `searched_llm` item to `deterministic`, lowers both route and execution scores, updates derived coverage/status, reseals the content hash, confirms that the snapshot remains internally readable, and verifies that execution rejects it against the original caller-held ID. This correctly tests the boundary that a content hash is not provenance authentication.

Router 2.1 compatibility remains limited to a synthesized compatibility-path snapshot; there is no preserved historical 2.1 route fixture. The plan and MOD-19 assertion now state this limitation explicitly. Router 2.0 has a preserved fixture.

## Reviewed file hashes

SHA-256 at review time:

| File | SHA-256 |
|---|---|
| `scripts/routing.py` | `f7e84c0eda38d42f1e57720ca9e3e7ab41e651fef19801ee2c4fa8c13add36e2` |
| `scripts/question_sets.py` | `515775284dad1fdb014c9cd883d078a623085bd37e6640dc4a52ce446c689433` |
| `schemas/quick_scan/route-decision.schema.json` | `9c4035dab03d2810b926eaf5ece214494a2984d8f63ede25c84605119a3086e4` |
| `tests/test_routing.py` | `8916abfe0ce49903c470c4e58d086195182e61afe0fad0db800594c514cbb3ae` |
| `tests/test_question_sets.py` | `a97b0fb4766f139b42a09a0a5763a110783865e337ab3ddc8e4714321dbd1c86` |
| `tests/test_implementation_plan.py` | `79ed16c9fd15ae24a6cf0bcca1a0c45d8d1bf60eb123fd790a6ecb644b77df5d` |
| `docs/implementation/tasks.json` | `d5cb14a879503db21ecea642d5fc0274972b1048e118987e04ffd9f17939baa2` |
| `docs/implementation/acceptance-cases.json` | `31cabedb3b414f366f7cf7f6e34b666d20d145bf7af64505ce62e44769dc43f6` |
| `references/routing.md` | `afebd5f88e1432e2589ca344fa0ad37d1b14d31a936acf62be5ab022e918267c` |
