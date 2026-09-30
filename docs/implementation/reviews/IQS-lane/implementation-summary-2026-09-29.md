# IQS harness lane local implementation status

Date: 2026-09-30  
Local repository: `master`; the completed local checkpoint is commit `eb462d48321f3247eabf18daa57a4d4606405ca4` (based on `25b8d14316c06390450e5a1d8883583bfd039d0d`).  
Plan: 1.10.15 — 107 tasks, 366 acceptance cases, 54 invariants, final gate G6.  
Construction card: `company-wiki/docs/plans/narrative-evidence-pilot-2026-09-26/harness_lanes/invest_quick_scan.md`, read-only SHA-256 `516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`.

## Scope and result

All writes for this lane stayed inside `invest-quick-scan`. The company-wiki card was read only; StockWiki, StockQA, company-wiki and the other external repositories were not written. The initial worktree inventory recorded 792 pre-existing changed paths (47 tracked modifications, 745 untracked); those user changes and historic artifacts were preserved. No live API, company-data download, or production run was performed. C01–C07 receipt refresh remains paused by the user's instruction.

Local write scope covered the identity CLI and its request/schema tests; the task-receipt retirement stub, archive, migration tests, and active plan/handoff docs; the deployment schema/example/decision/tests; the trusted-proof regression and audit; and batch validation reports. Key entry points are `scripts/identity_contract_cli.py`, `scripts/deployment_contract.py`, `schemas/quick_scan/identity.schema.json`, `schemas/quick_scan/identity-cli-request.schema.json`, `schemas/quick_scan/deployment.schema.json`, `tests/test_identity_contract_cli.py`, `tests/test_deployment_contract.py`, and `tests/test_identity_bound_work_observation.py`. This list identifies the main local interfaces; it does not authorize writes outside the repository.

The local implementation is complete through the deployment and trusted-field review. Cross-repository producer compatibility remains open until StockWiki supplies a versioned identity snapshot/mapping DTO and real positive golden through its public interface. Local synthetic fixtures do not satisfy that gate.

## Implemented

- Added the bounded, read-only Identity Package 2.2.0 JSON CLI. It validates Entity 2.1.0 and AnalysisSubject 1.0.0, rejects duplicate JSON keys and oversized input, returns exit 0/2/3 for valid/invalid/unsupported input, emits one structured line, and does not echo request contents.
- Retired the active task receipt v2/P01 recursive sign-off workflow. The old engine, specification, schema, example, and tests are archived with SHA-256 pins. Existing P00/P01 historical records remain in place and unmodified; the CLI is a small retirement notice, and product search/dispatch/import receipts remain active. An independent review found that merely iterating the preservation manifest would not detect deleted entries; a regression now pins the manifest SHA, all 186 entries and their kind counts.
- Replaced deployment `explicit_user_confirmation` and `approval_ref` with the named `execute_one_live_search_probe` external action and an enforceable cap of one model request, one search request, at most 4,096 input tokens and 1,024 output tokens. Authorization also requires the request's release and policy revisions to match the active ones and budget status to be available. This decision authorizes a bounded action only; it starts no network or paid call. An independent review caught an integration fixture that copied the requested policy revision into the active-policy field; the fixture now supplies that field independently and verifies stale requests are blocked.
- Audited the current-score gate's identity, work, attempt, search, import and content proofs. No field was proven redundant: each joins a different owner record or point in time. Added field-mutation negative coverage. The audit documents that this local validator checks owner-shaped values but does not authenticate that the caller fetched them from StockWiki or StockQA; provenance remains an owner integration contract, not a locally proven fact.
- Removed active-document requirements for per-task recursive receipts and changed handoff guidance to batch logs and major milestone review. Historical review documents were preserved unchanged; Phase 12 is explicitly marked superseded so its old C01 receipt-refresh checkbox cannot be mistaken for current work.

## Identity package hashes

| Artifact | SHA-256 |
|---|---|
| `schemas/quick_scan/identity.schema.json` | `671292A60BF1656B73009877A59C49C8585935B11D42B7FEF5E021FC275FC2E3` |
| `schemas/quick_scan/identity-cli-request.schema.json` | `D63AFDF4420D1432FC3CB0BE2F6F27C3FF3D1524E17A6FBFFD1A3A3C2A51EFFC` |
| `scripts/identity_contract_cli.py` | `D716C618F47793E83B0E8757BE0EA103F09813E8B39222894E46A60C2F374CEB` |
| `tests/test_identity_contract_cli.py` (synthetic request fixtures and subprocess oracles) | `BB143076BB2FC171E204D190340DD6C655B849F15CB3FD829BD09B08862E8DEF` |

The receipt-retirement `preservation-manifest.json` SHA-256 is `562FE14079642F7EB0FE728DF69355226D6F584E9BB1ED574E1AD656FD5CED1A`; it pins 186 entries: five archived implementation/spec/test sources, one retired plan snapshot, and 180 pre-existing historical evidence files.

## Verification

- `tests/test_implementation_plan.py`: 80 passed; plan validator: 107 tasks / 366 cases / G6, valid.
- Final post-review offline lane regression: 105 passed, 298 subtests; this includes the deployment contract, identity/proof and freshness cases, public request-to-decision integration, identity and retired-CLI subprocess tests, G0 manifest checks, and producer-chain local golden E2E.
- Focused G0 manifest plus receipt-retirement suite after the review fixes: 16 passed, 186 subtests, with pytest cache disabled.
- All pytest groups used isolated temporary roots; every root was removed and checked after completion. The combined lane and plan runs emitted non-blocking `PytestCacheWarning`s because the repository cache directory was not writable; the final G0/retirement rerun disabled that cache plugin and passed without the warning. Tests made no network calls and created no downloads.
- TDD evidence for the deployment change: the valid new-shape authorization and schema cases failed against the old boolean/reference contract, then passed after replacing the contract. Diagnostic red runs are retained alongside final batch outputs under `docs/implementation/contracts/validation-IQS-LANE-*.txt`.
- `git diff --check` passed after this report was added (exit 0); Git emitted only line-ending normalization notices for existing mixed-ending files.

## Remaining gate

StockWiki has not yet supplied the real identity snapshot/mapping DTO or producer golden, so no cross-repository positive compatibility claim is made. Once the owner publishes that versioned artifact, test it through the owner's public API and compare it with the IQS read-only consumer contract before closing G2b. Historical task receipts must not be refreshed to substitute for this gate.
