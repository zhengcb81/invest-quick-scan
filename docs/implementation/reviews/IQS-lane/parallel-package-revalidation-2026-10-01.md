# QA-04 / SW-IDENT acceptance revalidation

Observed: 2026-10-01. This report supersedes neither the original owner handoffs nor the 2026-09-30 acceptance report. It records fresh checks against the current shared working trees.

## QA-04 — behavior passes; delivery remains partial

StockQA is at `master@3c685dda28f67a00bd653ad257a121d3b8edebb8` with 55 dirty paths shared across prior work. No commit was created. The owner handoff remains `status=partial`, `result_commit=null`, and carries old source hashes. Its file SHA-256 is `392d15497af13ef753440d4d04cca336ce2a6ee16e627745f11ac6e4ab2599b7`; it is ignored by StockQA `.gitignore` (`*.json`). The IQS public handoff CLI returns `valid`, which checks only handoff shape and declared scope; this does not establish that its test/hash claims match the current tree.

The previously identified next-run receipt gap is covered by one additional assertion in StockQA `tests/integration/test_quick_scan_cli.py`: all attempts in both questions must omit `policy_transition` when the saved policy is deferred to the next run. No production code was changed in this revalidation. Current SHA-256 values are:

| File | SHA-256 |
|---|---|
| `src/utils/llm_integration.py` | `e44878d0b6ed9390a55d8210920952e9f16c89c1c49e1d7cbe34e516b9f6a21e` |
| `tests/unit/test_llm_integration.py` | `913eaba45191cfae73e69577f31680a8ddf8066f2045e64ea6173952bf1a5f75` |
| `tests/integration/test_quick_scan_cli.py` | `291d843b90426b4adf55a78d17a15c24bed9ae56618e405d26889aa2229ab516` |
| `q04_handoff.json` | `392d15497af13ef753440d4d04cca336ce2a6ee16e627745f11ac6e4ab2599b7` |

From a disposable temporary working directory, the six-file owner batch (`test_llm_integration.py`, `test_quick_scan_cli.py`, `test_qa_pipeline.py`, `test_qa_engine.py`, `test_llm_config.py`, `test_quick_scan_work_transport.py`) passed **246 tests**. Ruff passed for the touched runtime and integration-test files. The first attempt from the StockQA root could not create its relative `logs/` file under the external-repository sandbox; rerunning from the temporary cwd passed. The final temporary root was absent afterward, and StockQA's status output was byte-for-byte unchanged at 55 paths. No live API, network request, paid call, or company-document download ran.

The tests support QA-04 runtime behavior, including LLM-10 and PAR-11. Delivery closure is still pending a reviewable current handoff/commit: the worktree contains unrelated shared changes and the old receipt does not bind the just-verified test hash. The coordinator must not stage or commit the shared StockQA tree as a shortcut.

## SW-IDENT — producer regressions pass; W01–W03 and full G2b remain partial

StockWiki is at `master@b4f3846bb3e331f5661edee974a7d0b76dbf9664` (`Merge W04 operating MIC validation`). Its only working-tree status path remains the pre-existing untracked `.claude/`; it was not opened or modified. The new W04 commit adds operating-MIC relationship validation and related tests; no SW-IDENT source was changed during this revalidation.

The StockWiki handoff SHA remains `baee5595ac95528c14134e4f862299adc717c27e376d434529a1121015f460ac`, with `status=partial` and `result_commit=1cabb47`. The IQS public handoff CLI rejects it as `invalid / changed_path_out_of_scope`: `changed_paths` names `stockwiki/quick_scan_evidence.py` and `tests/test_quick_scan_evidence.py`, but the declared `authorized_paths` omits both. Its written authorization reference does not repair that machine-checkable mismatch. The current commit also moves beyond the handoff's recorded result snapshot.

On the current HEAD, an isolated focused batch covering `test_identity_mapping.py`, `test_identity_snapshot.py`, `test_identity_receipts.py`, `test_identity_g2b_export.py`, `test_quick_scan_evidence.py`, `test_market_registry.py`, and `tests/e2e/test_g2b_iqs_cli.py` passed **113 tests**. This includes the public StockWiki-export to IQS-CLI E2E and MIC relationship cases. Pytest's basetemp and the E2E home/temp roots were under a unique disposable directory; all were deleted. StockWiki status output was byte-for-byte unchanged (`.claude/` only). No network, API, paid call, or live market-data download ran.

Current SHA-256 values: handoff `baee5595ac95528c14134e4f862299adc717c27e376d434529a1121015f460ac`; `stockwiki/quick_scan_evidence.py` `2b48d1f14e97f05b703dc1d865b1810ed557b66aad979e53879f94ac666e7525`; `stockwiki/identity_mapping.py` `fac474253c6c529debef1011fa00dcecd07b2de2a9ff886e1d059c2736b6b043`; `stockwiki/market_registry.py` `b3333e0fb9dafac599b900884a9082d9ea975798c98984d31beac0597b633db9`.

This confirms the previously accepted provisional Entity/mapping interface slice still passes on the newer producer commit. It does not close W01–W03 or full G2b: the handoff itself records missing candidate ingestion/unresolved scan queue, bare-ticker ambiguity, public universe CLI/identity-event history, and verified/multi-listing/AnalysisSubject owner examples. The evidence store remains a storage component without production resolver/scan integration.

## Acceptance state

- QA-04: runtime cases pass on the identified shared snapshot; delivery remains `partial` until its owner handoff is refreshed to current hashes and a safely isolated snapshot is available.
- SW-IDENT: current producer regression batch passes; handoff is machine-invalid and W01–W03/full G2b remain `partial`.
- TH-01 / IN-02: their prior `prestudy_complete` acceptance is unchanged; T01 / T02 implementation remains `not_started`.
