# Q02 MiMo live search E2E record

Date: 2026-09-30 (UTC)
Owner repository: StockQAbyLLM, branch `master`, HEAD `3c685dda28f67a00bd653ad257a121d3b8edebb8`; the tested implementation was the working tree, not that HEAD alone.
Status: **Q02 first-provider implementation acceptance verified for this exact StockQA working-tree snapshot after independent review. This does not close G1, the wider live-sample gate, or cross-repository integration.**

## Run

- Command: `python -B -X utf8 -m pytest -p no:cacheprovider -o addopts= --rootdir=. -q tests/live/test_live_quick_scan.py::test_live_mimo_search_runs_public_company_through_cli_and_cleans_local_artifacts`
- Opt-in: `STOCKQA_RUN_LIVE_E2E=1`; the key was read from the existing `MIMO_API_KEY` environment variable and was not printed or saved.
- Request: one public CLI quick-scan question for Microsoft Corporation, Entity `issuer:US5949181045`, using `mimo-v2.6-flash` at `https://api.xiaomimimo.com/v1` with required web search.
- Result: **1 passed in 13.63s**, CLI exit code 0. The test asserted the exact entity name, provider and actual model, response ID, `search_status="executed"`, search receipt bound to that response ID, at least one source URL, URL-citation evidence basis, and a UTC answer timestamp. It accepts either a scored answer or `insufficient_evidence`; it does not treat the score as evidence that search ran.
- Isolation: the test's `TemporaryDirectory` was asserted absent after completion. Git status contained 55 entries both immediately before and after the test; the test created no lasting file or download.
- Two preceding sandbox attempts failed before receiving an HTTP response with sanitized `ConnectionError` (7.73s and 7.20s). They produced no provider response or search receipt. The successful run used the authorized non-sandboxed test invocation.

## Exact tested source snapshot

| StockQAbyLLM file | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `C762F12D44251682BFEE43DE5CA1AD2A4C64C1C4F73B25BD91776BE3813F7D88` |
| `src/providers/base_llm_provider.py` | `7B257DB4E58A3A500C289A11842BBF1D01DE62C825CCCC314BCFD2B23F8720F7` |
| `src/providers/llm_provider.py` | `03B6D303311F211FF4D0AA7FD95C8BDA749446CDD558EE51812BCADCB737FCAF` |
| `src/core/qa_engine.py` | `2C7889354069FFBA02D9B7C3F98E53882DBBB4A2CCE1A2F800A8A30A69189991` |
| `tests/live/test_live_quick_scan.py` | `C3CB590C3E2A3D597EC9B2B13F03673EF81189EB04D2F9907BA6099817B86906` |

## Offline regression on the same working tree

- From a unique temporary working directory, with `PYTHONPATH` pointing to the owner repository, disabled the unrelated `base_url` pytest plugin and project coverage/cache outputs, and set `--basetemp` inside that unique temporary root.
- Ran `tests/unit/test_llm_client.py`, `tests/unit/test_llm_provider.py`, and `tests/integration/test_quick_scan_cli.py`: **159 passed in 17.45s**. No network/API calls were part of this batch.
- The temporary working/basetest root no longer existed after the command; StockQA Git status remained 55 entries before and after.
- Initial attempts were blocked only by environment setup: the logger tried writing `logs/` under the read-only repository, an auto-loaded third-party `base_url` fixture conflicted with a test parameter, and pytest's default temp root was not writable. The final command explicitly isolates CWD and `--basetemp`, disables `base_url`, `cacheprovider`, and project addopts. Those collection/setup errors are not counted as product-test failures.

The live test's temporary result was removed by its own isolation guard, so this record contains only assertions observed in the passing test, not raw provider output, source URLs, request IDs, token usage, or a calculated charge. No claim is made about exact price. The live run proves a completed MiMo search and citation on this source snapshot; MiniMax live-search status remains outside this task-level acceptance.

## Independent review and acceptance interpretation

- A separate read-only review checked the five SHA-256 values above against the current StockQA working tree. It confirmed the successful run is bound to those exact bytes, confirmed the selected offline coverage for LLM-02 and LLM-11, and found no P0/P1 code defect.
- The reviewer suggested three P2 test-strengthening opportunities for a future test-only change: assert exact equality between answer URLs and the executed search receipt URLs; assert the search-call ID equals the receipt ID; and record/allowlist the effective endpoint host. It also suggested a negative fixture for answer text containing a URL without a provider citation annotation. These are coverage improvements, not defects demonstrated by this run. No duplicate live request was made.
- The reviewer noted that the old `receipt-Q02.json` and `acceptance-cases.json` still show historical/specification statuses. Cross-checking the active IQS rules resolves this: task-receipt v2 was retired on 2026-09-29, so the old receipt remains read-only; `acceptance-cases.json` explicitly says it contains specifications, not runtime results, so its `specified_not_executed` values remain unchanged. Current execution evidence belongs in `progress.md` and this batch record. Neither historical artifact is refreshed or used as a current gate.
- On that basis, the Q02 task's LLM-02/LLM-11 checks, the live first-provider search evidence, and exact-snapshot independent review satisfy the current task-level acceptance. This does not establish that the cited sources support each claim, that the score is correct, that another model/provider will search, or that the measured call's price is known. The StockQA working tree remains uncommitted and includes unrelated/pre-existing changes; this record does not claim an external-repository commit.
