# Q10 Producer Result Outbox Validation — 2026-09-27

## Scope

This evidence covers only the authorized StockQA producer-side Q10 slice: durable result-delivery outbox, immutable C06 package handling, checkpoint binding, send-intent/uncertain state, and exact ACK persistence. It does not certify the StockWiki receiver or production cross-repository delivery.

StockQA files reviewed and tested:

| File | SHA-256 |
|---|---|
| `src/utils/quick_scan_result_outbox.py` | `B64CB1E1CE55D67417B64B08D2CA76B5DBB87F74D5FC6C06FFB9DA4C015B1467` |
| `src/utils/quick_scan_work_store.py` | `859F7E4CD1266915BB8E301FE208164C09776C2C22E14EA69D0B515BE6266CE8` |
| `tests/unit/test_quick_scan_work_store.py` | `38309B07029A7DDA409343DBD038A730E4EFE7D6D03E0B234933CEFCDA2C402B` |
| `tests/unit/test_quick_scan_result_outbox.py` | `98D3C4E742D94C2442D74BC135AB8512047002572E84D41C3F07D12FE0A0F805` |

Git reported the four authorized paths as untracked at validation time. No unrelated StockQA file was modified for this Q10 evidence-binding correction.

## Validation

- Focused StockQA unit batch: **79 passed** across `test_quick_scan_work_store.py` and `test_quick_scan_result_outbox.py`. Pytest cache and coverage plugins were disabled; project `addopts` were cleared. `ResourceWarning` and `PytestUnraisableExceptionWarning` were treated as errors. The test used a unique temporary root below `invest-quick-scan`, checked its containment before cleanup, and removed it on exit.
- `ruff check --no-cache`: passed on the four files above.
- `black --check --no-cache`: passed on the four files above. Black's in-place formatter was not used on StockQA because cross-repository writes are restricted; the `black --diff` output was applied manually and the final check passed.
- A dynamic synthetic observation built from a real temporary SQLite work store passed the local C06 full ExchangePackage JSON Schema and semantic/integrity validator. The temporary directory was automatically removed.
- No LLM, Brave, Tavily, or other external API was called; no documents were downloaded.

## Review finding and correction

The first independent Q10 review found that an adapter could replace `answer.evidence[].url` with a URL absent from the checkpoint's saved search receipt and recompute all package hashes. The producer now requires every evidence URL to exactly match one URL from canonical `checkpoint.payload.provenance.source_urls`. Evidence may use a subset of those recorded URLs. It rejects malformed evidence rows and missing/blank source URL entries.

The local C06 `validate_content` contract also requires every successful answer to carry evidence. The producer therefore rejects an empty evidence array for `scored` answers while allowing it for `insufficient_evidence` answers.

Regression cases mutate a source URL and recompute payload, item, and package addresses before asserting rejection; another removes all evidence from a scored answer and asserts rejection. In both cases the existing delivery stays blocked and the work item remains `result_ready`.

The independent exact-hash follow-up matched all four hashes above and reported **no P0–P2 findings**. It confirmed that subset evidence is accepted only when every URL belongs to the checkpoint source list, and that empty evidence is rejected for `scored` but may be used for `insufficient_evidence`.

## Remaining Q10 boundary

StockQA still requires a verified adapter capable of constructing the complete C06 Observation without inventing missing cohort, catalog/template version, cutoff, or evidence metadata. The public runner is not yet wired to package, dispatch, reconcile, and consume a real StockWiki W05 ACK. No authoritative receiver-side reconciliation path was tested. Therefore this result establishes producer-side outbox primitives only; Q10 remains partial and must not be represented as a completed cross-repository import workflow.
