# Test timing and layer audit (read only)

This audit ran no tests and made no paid/network requests or source changes. Current disk has 97 test files, while the CodeGraph directory response had 73; the proposed suite inventory covers the current 97, once each.

## What is actually evidenced

- The prior 78-minute / 1065 passed, 4 skipped, 761 subtests outcome exists in the PWF text. Its original duration/JUnit artifact was not located. The old statement attributing most time to routing/module registry is a source-based hypothesis, not a measured decomposition. Do not assign percentages.
- Historical cache contains 1224 node ids: 1096 under tests and 128 under runs. This proves accidental/explicit historical candidate discovery has occurred; cache is mutable historical evidence, not a new default collection run. Limit default discovery to product tests so frozen copies under runs/docs never become active test inputs.
- Native real-owner/software E2E is measured at 645.111 testcase seconds / 648.869 suite seconds in the preserved XML. Nearby engineering suites measure 63 cases/5.888 seconds and 57 cases/7.035 seconds. These are different scopes and versions; they establish that a 10-minute native check need not run for a small pure-code edit, not a controlled optimization claim.
- JUnit testcase time includes setup/call/teardown by default, and does not split collection. Future runner output should retain pytest --durations so phase attribution is available.

## Layering recommendation

`proposed-suites.json` is a static boundary classification, not a promised speed SLA: fast 49 files; integration 45 files; local producer E2E 1; native cross-repository E2E 2. Root is implementing the explicit runner. All files must be accounted for without duplicates; new unclassified tests fail suite verification.

- Routine edits: fast plus the affected integration/module files.
- A coherent feature/contract boundary: relevant integration and producer E2E once, with one independent review.
- Native shared owner/SDK/checkpoint/delivery changes: native E2E in its existing explicitly owned runtime, separately and serially. The two native modules alter os.environ and sys.path at import, so do not mix into the normal process or apply blanket pytest-xdist.
- Paid real-provider acceptance remains a deliberate separate operation, not default pytest; test_live_e2e_sandbox is offline isolation tests and must not be mislabeled paid live.
- Full offline coverage remains available explicitly at major releases/milestones. Splitting must not delete tests or declare a partial run a full green.

## Other root causes and future optimization boundary

RoutingFixture.setUp copies authoring questions and publishes a complete immutable package per test. ModuleRegistryTests.setUp similarly copies authoring inputs; many cases invoke publish/compose repeatedly. Those are real isolation and mutation checks: do not collapse all to a shared mutable global fixture merely to save time. A later focused change may share only immutable verified base bytes and preserve a per-case writable copy.

The existing `runs/reconcile-production-2026-10-25/performance-investigation/report.md` already documents nested public owner CLI and repeated whole-package validation. Its 9 full loads / repeated policy CLI spawn are static normal-path counts, not observed per-function timing. Any pure validation caching optimization must keep grant/revocation, current anchor/identity, budget, lease and execution permission checks live; do not cache authorization decisions. That production optimization is separate from this test-dispatch change.

Parallelism is safe only after per-process work roots, independent temp/baseline ownership and global-import state boundaries are established. Do not launch two native tests against the same precreated owner/ledger.

## Artifacts

- proposed-suites.json: static complete inventory.
- historical-timing.json: exact historical XML paths, hashes and times.
- collection-cache-observation.json: exact cache hashes, counts and selected candidate node examples.

No test/full-run speed improvement is claimed by this audit.
