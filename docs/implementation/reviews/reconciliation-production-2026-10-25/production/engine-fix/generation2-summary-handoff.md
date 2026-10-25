# Generation 2 thin reporter

Final reporter: `real_summary_generation2.py`, SHA-256 `b47392f95962710b94e8dcdcc06a6d137de72e4597e4edb0247e355a836e5f05`.
Final driver: `80ceecfce9099b10e7565862cde3d4961604482a31a650364f9eeacbd811955e`.
The previous `real_summary.py` remains unchanged, SHA-256 `452c281e3660c0c35bbddee0060d80399923496765b56486c5d0264299216721`. Its reviewed read-only path/privacy helpers are reused by exact SHA. The new driver reuses the original eight-table snapshot algorithm and adds a separately named original owner-decision hash.

Execute only after the original driver has produced an actual `runs/r25-live/typed-generation2/result.json`:

```powershell
python -B -X utf8 runs/reconcile-production-2026-10-25/engine-fix/real_summary_generation2.py
```

No result means `not_ready`, exit 3, and no summary file. This does not constitute a successful acceptance. All database access uses the original `ReadOnlyWorkView` (`mode=ro`, `query_only`, no writer migration); socket/subprocess use is denied. The reporter uses original public checkpoint/response/context-use/delivery APIs and `QuickScanCostResolver`; it has no duplicate usage/price algorithm and invokes no dispatch, CLI or paid API.

It checks current source pins against the executed cold pin list and current raw source, safe-validation v2 before the crash, exact before/after/crash/current ledger hashes including owner decisions, original retry control, native receipt/use proof/URL closure, schema-2 checkpoints, standard answer versus original export, double finalization/reuse, ready/delivered state, and original exported/report runtime equality. Answer/context bodies, reasoning, lease tokens and raw private config are excluded.

New generation-2 physical model/search observations, original native usage and original resolver estimates are separate from the shared budget cumulative balance. The price delta subtracts two original driver ledger snapshots. Generation-1 invalid model/native usage and original estimate, its successful search journal fee, and the preserved local AttributeError/unknown operation reconciled as `confirmed_not_sent` at zero remain visible as history. Runtime cash-cost unknown remains unknown; rate-card estimates are not invoices. Ready means sealed waiting for delivery, not a StockWiki ACK. Financial correctness remains unassessed.

## Review fixes and final source binding

The independent reviewer identified that trusting only a task-bundle self-reported hash could publish changed subject/module metadata. The reporter now requires the exact `iqs.company-scan-task/1.0.0` protocol and reuses original `task_from_bundle` and `task_bundle`. Original `validate_scan_task` recomputes the raw task hash, derived-document references and question/module object bindings. Original `input_manifest_sha256` additionally binds the exported run company reference, run ID and cutoff to the validated task. The explicit protocol gate prevents the original legacy loader branch from accepting an old self-reported task hash.

Final bytes `b47392f9...` are independently accepted in `../engine-review/generation2-summary-final.json` and `.md`. The actual driver dependency locks include the original Company `task.py`, `scan_profile.py` and `provenance.py`, in addition to its other locked sources. Actual extraction still requires a real result; source review does not grant production, downstream or financial qualification.

## Preserved verification history

- Initial reporter bytes `37778f687b878d751de3f03989b94202d62a60d8029879b54cf8e7893b21f9b6`: four failure/privacy coordination units passed in 0.28 seconds, recorded in `generation2-summary-offline.xml`, `.txt` and `-cleanup.json`. They cover missing result/no output, missing driver pin, exception-text privacy and URL privacy. Its own `C:/Temp/iqs-g2-unit-y1kihqm_` root was removed. The following metadata-only addition exposed the actual search provider from the original operation context; it did not change validation or pricing.
- Intermediate task-loader fix bytes `bca9157864cfe121b7057fa2e024609665ad1e5ad9d409ee6673f00400b0b7c5`: four changed-subject/module/raw/run-manifest negatives were RED 4F/4P, then GREEN 8P/0.38s, preserved in `generation2-summary-task-red.*` and `generation2-summary-task-green.*`. These eight-pass records belong to this intermediate version, not the final protocol-gated bytes.
- Final reporter bytes `b47392f95962710b94e8dcdcc06a6d137de72e4597e4edb0247e355a836e5f05`: `generation2-summary-task-final.xml` records 9P/0.44s. A separately strengthened legacy negative also recomputes the forged run manifest while retaining the old task self-hash; the explicit scan gate still rejects it. That test-only strengthening records 9P/0.58s in `generation2-summary-task-strengthened.xml`; reporter/driver bytes did not change.

All these tests use isolated synthetic inputs, make zero API calls and do not open/write the actual database. Their cleanup records retain the precise owned temporary roots and removal results. They do not replace actual-result extraction. The delegated author has not executed the reporter main on a real result; root controls the live cold/recover run and its final evidence.
