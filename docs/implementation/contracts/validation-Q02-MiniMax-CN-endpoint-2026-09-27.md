# Q02 MiniMax CN endpoint and live CLI diagnostic

Date: 2026-09-27

## Scope

The user had already authorized StockQAbyLLM changes with advance reporting. This pass wrote only the following four files:

| File | Purpose | SHA-256 |
|---|---|---|
| `src/providers/llm_client.py` | Allowlist the documented Mainland Anthropic Messages host `api.minimaxi.com`; reject the invalid `api.minimax.cn` host. Keep the documented global host. | `C762F12D44251682BFEE43DE5CA1AD2A4C64C1C4F73B25BD91776BE3813F7D88` |
| `tests/unit/test_llm_client.py` | Update regional route fixtures and assert supported/rejected host behavior. Remove one duplicate positive fixture. | `0DBDD8FF46C93C6F5575FF54809D403F645BCB77AC8BD858AD922115851CD4A7` |
| `tests/integration/test_quick_scan_cli.py` | Update valid MiniMax Anthropic CLI endpoint fixtures. | `F9597744B051581843D999E9050DDD9AB81DF8600CFB58953F8CA83EDD27AF5B` |
| `tests/live/test_live_quick_scan.py` | Use the documented Mainland endpoint by default; include secret-redacted evidence in provider assertions and include safe reasons for `insufficient_evidence`. | `398EC188D835F4DAE3EA6C2D1CD97E2A6B6B1B73CF6DE2130D19B3B28201A4EB` |

The workspace already contained many unrelated changes before this pass. No reset, checkout, or cleanup was performed on those files.

## Verification

Offline focused provider/CLI regression, executed from a fresh temporary directory with all API keys and live opt-in removed:

```text
tests/unit/test_llm_client.py tests/unit/test_llm_provider.py tests/integration/test_quick_scan_cli.py -k "mimo or minimax_anthropic"
34 passed, 125 deselected
```

Live harness helpers, with live-marked tests excluded and no keys or live opt-in:

```text
tests/live/test_live_quick_scan.py -m "not live"
2 passed, 4 deselected
```

An offline exact public CLI run used the same temporary provider configuration and a deterministic stub for the HTTP send. It resolved provider `minimax`, model `MiniMax-M3`, URL `https://api.minimaxi.com/anthropic/v1/messages`, reported `supports_web_search=true`, and generated a stubbed successful search receipt. This verifies local route construction and receipt wiring only; it is not live evidence.

Both pytest runs used isolated temp roots. The roots were removed and verified absent. The pre-existing StockQA `.coverage` SHA-256 was unchanged. API keys were neither printed nor written to files. `git diff --check` on the four authorized StockQA paths passed; Git emitted only pre-existing global ignore-file permission warnings.

## Live attempts and result

Two post-correction invocations of the single MiniMax Anthropic public-CLI E2E returned CLI exit code 0 but failed the E2E acceptance assertions before any HTTP request was dispatched. The final redacted summary was:

```json
{
  "answer_status": "insufficient_evidence",
  "answer_error": "当前提供商或端点不支持可验证的联网搜索。",
  "provider": null,
  "search_status": "unavailable",
  "attempts": [],
  "http_status_code": null,
  "request_id_present": false,
  "response_id_present": false,
  "search_call_count": 0,
  "source_count": 0
}
```

This is neither a successful live search nor a server-side refusal: no request, response, search event, source, or provider receipt was recorded. The result is inconsistent with the exact offline CLI route check, so the live runtime configuration discrepancy remains unresolved. No further identical live retries were sent.

## Conclusion

Q02 / LLM-01 remains partial. The endpoint correction and offline regressions are supported by the current files, but neither this offline CLI stub nor historical live evidence closes the current-hash live search gate. Continue with no-network diagnosis of the test subprocess configuration. If a later live attempt is justified, change one controlled input, preserve sandbox cleanup, and require one response-bound verified search receipt.
