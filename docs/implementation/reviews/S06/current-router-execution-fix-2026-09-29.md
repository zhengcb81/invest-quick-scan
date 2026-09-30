# S06 current-router execution gate follow-up

Date: 2026-09-29  
Scope: read-only review of the local S06 route-composition and renderer failure-closed fixes.

## Change under review

New v2 route composition now uses `validate_route_for_execution`; archived manifest reading continues to use `validate_recorded_route_execution`. The renderer refusal regression patches the `renderer_rules_sha256` binding in `question_manifest`, where the helper is now owned, and enters through the public manifest-contract facade.

## Independent review result

The independent reviewer found no P0–P2 defects in the reviewed route composition, route validators, published selection/manifest validation, and focused regression tests. It confirmed that new execution checks the package, frozen profile and caller-supplied decision ID, then enforces current router eligibility; router 2.0/2.1 decisions cannot write a new composition. Historical manifest reads validate against the recorded decision and original `checked_at` rather than granting new execution eligibility. The renderer test patch reaches the actual rule-hash owner through the public validation path.

The reviewer noted a remaining fixture limitation: the router 2.0 historical fixture is frozen, while the router 2.1 route decision is synthesized in an isolated package. There is no separate manifest-level golden for an actual router 2.1 archived artifact. This does not invalidate the fail-closed new-execution gate, but real router 2.1 historical compatibility remains unproven until an owner-produced sample is available.

## Verification

The S06 focused offline batch passed **57 tests, 0 skipped** in 209.44 seconds. It covered routing, StockQA adapter contracts, dependency closure, route composition, and the historical renderer refusal regression. Output is preserved in [`validation-S06-current-fix-2026-09-29.txt`](../../contracts/validation-S06-current-fix-2026-09-29.txt). The run used a unique TEMP/TMP and pytest basetemp, all removed and verified absent after completion; no model, search, network, or external repository was used.

Plan validation passed with 107 tasks, 366 acceptance cases, and final gate G6. This is local S06 evidence only: StockQA→StockWiki transaction ACK, real router 2.1 archived sample, and authorized cross-repository E2E remain open. No task-receipt refresh was performed because the engineering receipt v2/P01 workflow was retired in Phase 43.
