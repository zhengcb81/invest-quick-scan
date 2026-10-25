# Shared-engine finalization independent review — round 1

- Reviewer: `/root/fix_bank21`; production author: `/root/inspect_production`.
- Scope: main `scripts/shared_company_engine.py` finalization helpers; StockQA `OwnerResearchServices.restore_finalization_handle`; related new unit/native software tests; controller `prepare_live.py` read-only inspection.
- No production source, original database, roster, or model/provider configuration was modified by this reviewer. No network/model call was made.
- This is engineering review evidence. It does not grant production readiness or establish financial accuracy.

## Independently rerun checks

1. `python -B -m pytest tests/test_shared_company_engine_finalization.py -q` → **10 passed in 4.80s**; `main-finalization-units.txt`.
2. StockQA `python -B -m pytest tests/unit/test_owner_finalization.py tests/unit/test_owner_native_inspection.py -q -p no:cacheprovider` → **30 passed in 6.54s**; `stockqa-finalization-units.txt`.

The first suite uses mapper doubles and a verified-export substitute, so it proves glue conditions only. The second uses temporary real work-store SQLite but replaces the admitted-input guard for its narrow mapper fixture. Neither is presented as a genuine owner admission positive.

## Source findings

- `_verified_finalization_export` binds the original task bundle, checkpoint history/replay, run slots, question ordering, information cutoff, original journals, evidence board and independently recomputed runtime summary.
- `_native_final_answer` requires exactly one byte-equivalent structured answer for the selected question from safe original content/tool output; the finalizer also locates the exact native receipt in that question's original work member.
- `restore_finalization_handle` obtains only the original token/epoch from an existing successful member, rejects foreign/expired/replaced leases and conflicting handles, and changes memory only. Native commit independently checks the lease again.
- Reuse checks checkpoint attempt, saved full standard answer and native provider attempt; no lease restoration is attempted for an already matching checkpoint. Partial publication retry now has a dedicated test: the first checkpoint persists, retry reuses it and saves only the remaining member.
- No direct HTTP call, dispatch, budget grant, lease renewal or re-claim was introduced by the inspected finalization path.

## Coverage feedback / actual boundary

The author confirmed that existing external-context-use binding supports singleton work, and cannot provide a legitimate searched multi-question native pack positive in this change. The reviewer requested explicit partial-publication retry coverage (added and independently passed above) and a negative check that a native pack without the required search proof cannot be finalized. Genuine searched singleton software E2E remains the required positive; the author is running it in an isolated original-software runtime. This round does **not** count that pending E2E as passed.

## Controller-preparation observation

At review time the current `prepare_live.py` allowed only `scan.sqlite`, `analysis_subjects.sqlite`, `identity_receipts.sqlite` and `market_registry.sqlite` to be copied. However, existing `live/readonly-source-copy.json` listed six databases including `scan_observations.sqlite` and `scan_observations.backup-before-primary-fix.sqlite`. The controller confirmed this was the earlier refused preparation iteration: workspace-bound observation ACK identity was rejected, the two isolated observation copies were removed precisely and the original migration created a fresh empty observation store; cleanup/migration evidence is `live/fresh-observation-store.json`. The original copy record remains unchanged as historical evidence. The current script is the repaired preparation version, not the exact initially executed bytes. Capture has subsequently passed; preview is still being diagnosed. No modification was attempted by the reviewer.

## Round-1 conclusion

No direct bypass was found in the scoped finalization/restore source. Unit and mapper checks pass independently. Complete-round signoff is pending the actual original-software searched singleton E2E and the controller's live driver/artifact review; financial accuracy remains unassessed.
