# Q02 MiniMax Anthropic endpoint diagnostic — independent review r2

Date: 2026-09-27

## Scope and conclusion

This read-only follow-up covers only `StockQAbyLLM/tests/live/test_live_quick_scan.py` and its request/response contract with `StockQAbyLLM/src/providers/llm_client.py`. Both requested SHA-256 hashes matched before inspection. Static AST parsing succeeds for both files. No live test, network request, environment lookup, or API-key access was performed.

The three reported fixes cover the prior findings. The endpoint override retains the `.cn` default and is passed to the client allowlist; the optional request ID is now accepted as absent or a nonempty string; the failure summary now includes only the parser's allowlisted tool error code. I found no new P0–P2 issues in this scope.

This report is limited to the test and endpoint diagnostic. It does not mean Q02 passed or is closed. Parent-reported pytest collection and focus-test results were not independently re-executed here.

## Prior findings rechecked

- **P1 indentation/parse failure — closed.** The Anthropic test body, endpoint assignment, and subprocess keyword arguments are consistently indented. Static AST parsing succeeds. Relevant lines: [test_live_quick_scan.py:303](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:303), [test_live_quick_scan.py:340](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:340), [test_live_quick_scan.py:375](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:375).
- **P2 optional request ID assertion — closed.** The test accepts either `None` or a nonempty string, matching the client's optional header-derived value. [test_live_quick_scan.py:439](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:439) [llm_client.py:116](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:116)
- **P3 error-code summary — closed.** The test summary now includes `call.get("error_code")`; the Anthropic parser only attaches values from its fixed error-code allowlist, so this adds useful failure detail without including response prose. [test_live_quick_scan.py:403](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:403) [llm_client.py:304](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:304) [llm_client.py:364](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:364)

## Contract and privacy checks

The live test uses the environment override when supplied and preserves the `.cn` default. The client supports the Anthropic Messages path on the allowlisted `.cn` and `.io` hosts for MiniMax-M3. The payload uses the API-key header, Anthropic version header, forced web search, and `max_uses: 1`. The response parser verifies the call/result ID relationship, completed search status, response/model fields, source URLs, and nonempty answer before reporting `search_status=executed`.

The child config leaves its API-key field blank and the child inherits the environment for credential lookup. The test does not include captured stdout/stderr or raw source URLs in its failure summary. It redacts the exact key string from a truncated error description and emits status, error type/code, IDs as presence flags, and counts. Temporary files are created inside `TemporaryDirectory`; cleanup is handled when the context exits, including on exceptions.

No test suite or live request was run during this review. The reported 17 focus tests and one live-test collection result are supplied evidence, not independent verification.

