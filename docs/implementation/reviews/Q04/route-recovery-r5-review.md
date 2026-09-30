# Q04 post-r4 route-recovery review (r5)

- Reviewer: `/root/q02_retry_design` (independent, read-only follow-up)
- Review date: 2026-09-25
- Review result: `needs_revision`
- Review scope: authorized route-recovery implementation and unit/CLI tests only; no file edits by the reviewer.
- Historical snapshot under review:
  - `StockQAbyLLM/src/utils/llm_integration.py`: `4380658FE7E43CAF6CC339D79F6B3F8EB84757FA25A28F5CF27025964C200186`
  - `StockQAbyLLM/tests/unit/test_llm_integration.py`: `B8FA6202DE435F4BD9D383D16658BF3A690BA14DB934F60D8586756F890CD21B`
  - `StockQAbyLLM/tests/integration/test_quick_scan_cli.py`: `0D61D7856707D3F20F0F7425C7F2A41389839F36E365D2772F434FF07FFAEF6A`

## Findings

1. **P1 — dispatch outcome omitted from public JSON.** The cascade stores `execution.dispatch_outcome` on `SearchResult.metadata`, but the `SearchResult.to_dict()` serializer in `src/core/models.py` selects receipt fields and omits that outcome. The public CLI result therefore cannot tell its caller whether a question is `uncertain`, `setup_required`, or waiting to retry. Fix requires the serializer owner and regression tests; this file was outside the reviewed and currently authorized external write scope.
2. **P1 integration limitation — retry recommendation is not scheduling.** `retry_wait_recommended` with `scheduled: false` is honest, but cooldowns are in-process only. Durable `next_retry_at`, restart recovery, and a retry owner remain unimplemented; keep LLM-06 persistence open.
3. **P2 — Retry-After sequence differed from C05.** The reviewed implementation skipped the limited route immediately even for short Retry-After values, while C05 requires a bounded wait/retry before falling through. A new test-first change is now in progress to wait only for a short interval, retry the route once, and preserve prompt fallback for long cooldowns.

## Review validation

- Independent isolated unit and CLI test suite: 75 passed.
- Tests used mocked HTTP and no real provider/network request.
- No new attempt-cap breach found in the reviewed CLI path; the provider runner constrains internal retries.

This report applies only to the three historical hashes above. Later Retry-After changes require a separate follow-up review. The P1 serializer issue must not be treated as fixed by this report.

