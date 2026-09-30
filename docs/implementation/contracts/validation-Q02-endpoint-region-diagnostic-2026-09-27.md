# Q02 MiniMax endpoint/credential diagnostic — 2026-09-27

## Scope

This records a bounded diagnostic of the MiniMax Anthropic Messages search route after a completed HTTP response lacked search evidence. It is not a Q02 acceptance receipt and does not establish reliable live search.

## Snapshot

- StockQA `src/providers/llm_client.py` SHA-256: `C57136BDDAF1E77A1295BF99A30BED069748F3698FFD7DC36EDA7D69FF4CB77C`.
- StockQA `tests/live/test_live_quick_scan.py` SHA-256 after independent-review fixes: `CC1423ECC7E5F24AE26ACF2F08067B3613F5AE9BDAE22AF6D8B5A9E8D10BA95F`.
- The live test accepts `STOCKQA_MINIMAX_ANTHROPIC_BASE_URL` to select a key-compatible regional endpoint; absent that variable, it uses the existing `.cn` endpoint. It captures child output as UTF-8 and limits failure summaries to status, failure type, provider error code, call counts, and source counts.

## Results

- Isolated Anthropic client/CLI regression batch: **17 passed, 93 deselected**. The live-test module also passed AST parsing, and its exact live selector was collected without execution. Both test batches ran from unique temporary workspaces with coverage addopts disabled; all roots were removed afterward.
- One authorized public-CLI request to `https://api.minimax.cn/anthropic/v1/messages` returned HTTP 200 and `completed`, but no completed `web_search` call or source URLs. The public CLI marked search `unverified` and returned no score.
- Two bounded public-CLI requests to the official global host `https://api.minimax.io/anthropic/v1/messages` returned HTTP 401 with no search receipt. The configured credential therefore cannot currently be used on that host. No response body or credential was retained or printed.
- Each live run used an isolated temporary workspace and the test's `TemporaryDirectory`; the workspaces were removed after both passing and failing runs. No API key was written into the temporary config or any project file.

## Interpretation and next step

MiniMax's [official Server Tools guide](https://platform.minimax.io/docs/guides/server-tools) documents web search through Anthropic Messages and Responses, with a versioned `web_search_20250305` tool declaration and correlated search/result blocks in the response. The current `.cn` credential/route pair accepts the request but did not search in the latest run; the `.io` route rejects the credential with 401. A regional credential/endpoint mismatch is plausible, but these observations do not prove its cause. Keep search verification fail-closed. Do not repeat live calls until a supported endpoint/credential pair is available or another single controlled request-shape change is justified. Q02 remains partial.

The first independent read-only review found a test-module indentation error (P1), a brittle assertion on the optional request ID (P2), and an unnecessarily lossy safe error-code summary (P3). All three were fixed. The second review confirmed both hashes, closed the three findings, and found no new P0–P2 issues; report SHA-256 `F5D7DC9413F6248DC9C87218558CB9665353F5C0E4EC8C33B506462D127A8113`. Neither review ran live calls, accessed the network, or read the API key. Q02 remains partial because a stable verified live search receipt is still unresolved.
