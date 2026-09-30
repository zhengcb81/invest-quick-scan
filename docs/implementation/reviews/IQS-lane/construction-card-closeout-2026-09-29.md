# IQS harness lane construction card closeout

Date: 2026-09-29  
Card: `company-wiki/docs/plans/narrative-evidence-pilot-2026-09-26/harness_lanes/invest_quick_scan.md`  
Read-only card SHA-256: `516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`  
Scope: IQS-owned steps 1–4 complete; cross-project step 5 remains open until StockWiki provides its real producer snapshot/mapping DTO and golden.

## Card step crosswalk

| Step | Result | Evidence / boundary |
|---|---|---|
| 1. Inspect worktree and planning state; preserve existing work | Complete | PWF has no selected `PLAN_ID`/`PWF_PLAN_ROOT` or `.planning` directory, so the root `task_plan.md` is the legacy plan. The original inventory records 792 paths (47 tracked modifications, 745 untracked). The delta records 843 current paths at capture (47 tracked modifications, 796 untracked): 53 new paths, 22 existing paths with changed hashes, and two missing active receipt artifacts whose archived copies match the original hashes. No unrelated work was reset, deleted, or attributed to this card. Ignored files are not in Git status; `.pytest_cache` could not be enumerated due to access denial. See [baseline inventory](worktree-inventory-2026-09-29.md), [baseline JSON](worktree-inventory-2026-09-29.json), and [delta JSON](worktree-inventory-delta-2026-09-29.json). The delta was captured before itself, this report, and final planning-note edits. |
| 2. Deliver Identity Package 2.2.0 public validator | Complete locally | Entity 2.1.0 and AnalysisSubject 1.0.0 are validated through a bounded, read-only JSON CLI. Duplicate keys and oversized input fail closed; valid/invalid/unsupported inputs exit 0/2/3; output is one structured line and does not echo the input. Contract and subprocess tests cover identity/security/source-binding mismatches. The CLI is a local consumer validator and does not fabricate a producer-positive StockWiki golden. Key hashes are listed below. |
| 3. Retire recursive task-receipt v2/P01 sign-off machinery | Complete locally | The active task-receipt runner/contract/schema/example and recursive sign-off tests were retired; the CLI now reports retirement. Existing evidence was preserved read-only and pinned by the unchanged archive manifest (`562FE14079642F7EB0FE728DF69355226D6F584E9BB1ED574E1AD656FD5CED1A`): 186 entries (5 source artifacts, 1 retired plan snapshot, 180 historical evidence files). A direct test checks retirement behavior and historical bytes. Product provider/search/dispatch/import receipts remain distinct and active. C01–C07 old receipt refresh remains paused and is not a closure condition. |
| 4. Simplify deployment authorization and audit trusted fields | Complete locally | `verify_live` now names `execute_one_live_search_probe`, caps work at one model request and one search, and limits input/output to 4,096/1,024 tokens. It requires active release/policy revisions and available budget. This contract test makes no network call. The field-by-field audit found no identity/source/work/attempt/search/import/content proof safe to remove: the fields bind distinct owner records or time points. Negative tests retain wrong issuer/security/period/hash/join and forged-trust failures. The local validator checks supplied owner-shaped values; it cannot authenticate their producer or prove StockWiki/StockQA provenance. |
| 5. Verify against StockWiki's actual serializer and identity golden | Pending external producer artifact | Read-only inspection found the identity/security/source-binding store, but no public identity snapshot/mapping DTO serializer or real golden in the scoped StockWiki source/test paths. Synthetic IQS fixtures do not satisfy this step. No StockWiki files or production DB were changed. G2b remains open until the StockWiki owner artifact exists and is tested through its public interface. |

## Identity package file hashes

| Artifact | SHA-256 |
|---|---|
| `docs/implementation/contracts/identity.md` | `9408E7445F65B70425C0285EDC51A0D210A986C9BCF7699F89C7EFE52895FC04` |
| `schemas/quick_scan/identity.schema.json` | `671292A60BF1656B73009877A59C49C8585935B11D42B7FEF5E021FC275FC2E3` |
| `schemas/quick_scan/identity-cli-request.schema.json` | `D63AFDF4420D1432FC3CB0BE2F6F27C3FF3D1524E17A6FBFFD1A3A3C2A51EFFC` |
| `scripts/contract_validation.py` | `D8BF3008358865782DD212B28EB0D544910CF9CB9564FB149F9C5EFF25D33D3F` |
| `scripts/identity_contract_cli.py` | `D716C618F47793E83B0E8757BE0EA103F09813E8B39222894E46A60C2F374CEB` |
| `tests/test_identity_contract.py` | `F1B002AE9F5FA8BE3BA643BFEC2F8D1150EADC808C27EE12E593F5D28A94A231` |
| `tests/test_identity_contract_cli.py` | `BB143076BB2FC171E204D190340DD6C655B849F15CB3FD829BD09B08862E8DEF` |
| `tests/test_identity_bound_work_observation.py` | `586895F814AB7BE1D6CF2FECA50DEB4F3EB5D8FAA250939557CA9D5349ECA806` |
| `tests/test_g0_regressions.py` | `E027EC666713266C814F8F8CF8B3134E774FFC774E2D2635EAA49F2DEC2305B3` |
| `tests/test_deployment_contract.py` | `F13359D1346105EEC053457D407F04E67CB29E5803848C10C96D7A016DA92E4B` |
| `tests/test_task_receipts.py` | `9193FF455017944D8F73FB97D1D5C9F134FAB9788AA3EBC2978CE89F6D9FC51A` |
| `tests/test_task_receipt_retirement.py` | `50C5C21D2A9D55E0D839E518C8B39F22CF892C07C99F00C8B339F97FF7B3BBB1` |

## Final validation

- The card-specific isolated batch passed **205 tests and 351 subtests**, with no skips: identity contract/owner binding, G0 security regressions, public CLI subprocesses, task-receipt retirement, deployment/provider failure, freshness/jobs, provider/budget, G0 manifest, and plan checks.
- Raw output: [`validation-IQS-card-closeout-2026-09-29.txt`](../../contracts/validation-IQS-card-closeout-2026-09-29.txt).
- Plan validation: **107 tasks, 366 acceptance cases, final gate G6; valid**.
- Pytest used a unique TEMP/TMP and basetemp; the test-owned temporary root was removed and verified absent. No network call, live API request, company-data download, or external-repository write occurred.
- `git diff --check` and a final validation of the planning structure are recorded in the active progress log after this report was added.

The IQS-owned card work is complete through step 4. The full cross-project card cannot be called complete while step 5/G2b is waiting on a real StockWiki producer artifact.
