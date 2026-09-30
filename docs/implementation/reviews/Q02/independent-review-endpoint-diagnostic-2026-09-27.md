# Q02 MiniMax Anthropic endpoint diagnostic — independent review

Date: 2026-09-27

## Scope and conclusion

This read-only review covers only `StockQAbyLLM/tests/live/test_live_quick_scan.py` and its request/response contract with `StockQAbyLLM/src/providers/llm_client.py`. Both requested SHA-256 hashes matched before inspection. No live test, network request, or API-key lookup was performed.

The Anthropic endpoint path and payload are consistent with the client allowlist for the preserved `.cn` default and the supported `.io` override. The temporary directory and emitted failure summary are designed to keep the key and raw response body out of pytest diagnostics. However, the live-test module currently has a Python indentation error and cannot be imported/collected. There is also an overconstrained assertion on an optional request ID.

This report is only a test/endpoint diagnostic. It does not mean Q02 passed or is closed. The supplied observations of `.cn` returning a completed response without a search event and `.io` returning 401 were not revalidated.

## Findings

### P1 — The live-test module cannot be parsed

In `test_live_quick_scan.py`, the Anthropic test's docstring at line 304 is indented eight spaces, while the following function-body statement at line 305 is indented four. Static Python AST parsing of this exact snapshot raises `IndentationError: unindent does not match any outer indentation level` at line 305. The endpoint assignment at lines 340–343 is also indented more deeply than the surrounding statements in the temporary-directory suite. Since parsing fails before decorators or skip conditions run, pytest cannot collect this module's tests.

Evidence: [test_live_quick_scan.py:303](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:303), [test_live_quick_scan.py:304](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:304), [test_live_quick_scan.py:305](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:305), [test_live_quick_scan.py:340](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:340).

### P2 — The test rejects a valid optional request ID

The test requires `receipt["request_id"] is None` at line 439. The client models this field as optional and populates it from an `x-request-id` response header when present, so a successful endpoint response carrying that header would fail the live test despite satisfying the transport contract.

Evidence: [test_live_quick_scan.py:439](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:439), [llm_client.py:47](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:47), [llm_client.py:116](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:116), [llm_client.py:376](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:376).

### P3 — A safe tool error code is reduced to a boolean in diagnostics

The Anthropic parser preserves an allowlisted `web_search_tool_result` error code on the call record, but the live test's safe summary emits only `has_error_code`. If a 200/completed response contains a failed search tool result, the failure summary distinguishes “code present” from “no code” but does not identify which recognized code occurred. The summary can include this allowlisted code without printing response prose or credentials.

Evidence: [llm_client.py:364](/C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:364), [tests/live/test_live_quick_scan.py:403](/C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py:403).

## Checks that look sound

- The `.cn` default is passed through to `LLMClient`; the endpoint override is read from the named environment variable. The client restricts Anthropic Messages routing to supported HTTPS MiniMax hosts and the `/anthropic/v1/messages` path. The request uses the API-key header, Anthropic version header, a single web-search tool, and `max_uses: 1`. The parser requires the result's `tool_use_id` to match the exact search call ID before marking search as executed.
- The test writes its temporary question/config/output files under `TemporaryDirectory`, runs the CLI with a sandbox working directory, and checks cleanup after the context exits. The child process captures stdout/stderr and does not include them in the pytest failure summary. The summary contains status fields and counts rather than raw response content; the error description is truncated and the exact configured key string is redacted before inclusion.
- No test suite or live request was run during this review. The reported 17 offline tests and 45/274 regression results were supplied context, not independently re-executed here.

