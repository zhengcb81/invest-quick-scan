# Q02 MiniMax Anthropic fail-closed hardening validation

Date: 2026-09-27  
Scope: StockQA current-snapshot parser hardening and one bounded live CLI attempt. This report records partial evidence only; Q02 is not closed.

## Changes validated

- `src/providers/llm_client.py` now accepts a present Anthropic `base_resp.status_code` only when it is exactly an integer zero. Boolean `false` is rejected even though Python compares it equal to zero.
- The parser now rejects a response containing an unrecognized `server_tool_use` (for example, `web_fetch`) even when a correlated, completed `web_search` with source URLs is also present.
- `tests/unit/test_llm_client.py` covers both regressions and asserts an unverified search status with no search receipt ID.
- `tests/live/test_live_quick_scan.py` now decodes captured child-process output as UTF-8 with replacement for malformed bytes. This changes test-harness decoding only; it does not change the request, question, retry count, or acceptance contract.

The provider's synchronous and asynchronous paths use the same parser and reject unverified search responses as `insufficient_evidence`. The existing CLI integration path does not score such a response.

## Automated validation

- Isolated suite for `tests/unit/test_llm_client.py`, `tests/unit/test_llm_provider.py`, and `tests/integration/test_quick_scan_cli.py`: **160 passed**, with warnings treated as errors. Tests ran from a unique temporary root under the authorized `invest-quick-scan` workspace. Live/API key environment variables were removed for this suite.
- Focused Anthropic regression group: **17 passed** before the final 160-test batch.
- Ruff and Black `--check --no-cache` passed for the changed parser and its unit tests.
- After the live-harness decoding fix, the live test module collected offline as **4 expected skips** with the live flag absent; Ruff passed. A whole-file Black check still reports formatting differences in unrelated pre-existing live test blocks; those blocks were not reformatted.
- Test roots were removed in `finally`; a post-run check found no `.q02-*` sandbox directories. No reports, logs, answers, or downloaded company documents were retained by the live test attempt.

## Independent review

The initial read-only core review matched the seven-file Q02 snapshot before the live-harness-only UTF-8 decode change. It ran **8 focused unit/CLI cases** and verified that unknown search receipts are rejected by dispatch. A follow-up review matched the final seven-file snapshot, checked that the UTF-8 decode-only change does not alter requests or retries, and found no P0–P2 issue. Reviewers did not call a live API.

## Live attempt

One authorized single-question MiniMax-M3 public CLI attempt was run with no format repair. It ended with `ConnectionError` before an HTTP response. The result was `error` / `unverified` with no HTTP status, request ID, response ID, search call, source URL, or score. It is not evidence of successful web search. Because the transport receipt cannot prove that no request bytes reached the provider, the outcome is treated as unknown and was not retried.

The first pytest invocation failed during collection because its temporary config did not register the `live` marker; no API request was made in that invocation. The next invocation reached the child CLI, but pytest decoded its UTF-8 subprocess output using the host's GBK locale. The test harness was corrected and reviewed. No additional live invocation followed.

## Final seven-file SHA-256 snapshot

| File | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `CB87F24F0226EB90A91836AFC1FB52E3A29C0FE59343DC97122B6D2FB463F373` |
| `src/providers/llm_provider.py` | `03B6D303311F211FF4D0AA7FD95C8BDA749446CDD558EE51812BCADCB737FCAF` |
| `src/providers/async_llm_provider.py` | `CD0A56C7025D48F26038217F3BEE0ED228ECA42939F3F9092D21027667051F8F` |
| `tests/unit/test_llm_client.py` | `0E8955C80A2F4AB41B41CC2805973C32C6E19EF73DFE29488DA60AD249524014` |
| `tests/unit/test_llm_provider.py` | `1A4656711F00A86F21E3BDFA197B9369238818DBEB117560451B1C20F8032EF3` |
| `tests/integration/test_quick_scan_cli.py` | `BA4817474BEBF3BAFA7415471B578DAF826285D6385450D9E3AE54E407D20E15` |
| `tests/live/test_live_quick_scan.py` | `5FBCCB176EAAF0800DBE5CDC36BA1E30DB138B0540FE4FA96A58AF12E129846C` |

## Remaining gate

Q02 remains partial because the current snapshot has no verified live receipt proving the same-response search call, completion, requested model, and source chain. Do not treat the earlier hash-mismatched live success as current evidence. A new live attempt requires a supported endpoint/account state and a separately bounded decision; do not blindly repeat this unknown-outcome attempt.
