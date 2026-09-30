# Q12–S02 independent review

- Reviewer: `/root/g0_independent_review`
- Review date: 2026-09-24
- Decision: **verified for the reviewed offline/local contract scope**
- Scope note: this report labels the narrow StockQA receipt-field extension **Q12** (temporarily called **Q03R** during the audit). It does **not** review or verify the implementation-plan **Q04** model/provider-priority cascade.

## Reviewed snapshots

### StockQAbyLLM — Q12

| File | SHA-256 |
|---|---|
| `src/core/models.py` | `3A2659B5A67E79F6CADD54571F87FA0AFE1E34B4D03FBE52EF667EF101456136` |
| `src/providers/llm_client.py` | `F06F4AD74C2A159575DF85596CAE2247CCB53ACCD98CA05DE6B25B01B24E68BE` |
| `tests/unit/test_llm_client.py` | `29C7ECC54C9C32C8AEE6939F07BEA30F8F88FB5350679A78B26C92BF048BF32B` |
| `tests/unit/test_models.py` | `18CBD10F47E9DA821E8E542CB69E3D4CB57161229DC29E8CC8E5EDEB62AEE603` |
| `tests/integration/test_quick_scan_cli.py` | `A9DC89C1DB656EB275EF4565E218AFC742F9DB26180D0B8B2CCC3D1ACDFC36FF` |

### invest-quick-scan — S02 downstream closure

| File | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `9702F21AA8F3C2ADC6BB39135B84700A8F93F3E80109DD2DFCDEF1105DEEB045` |
| `tests/test_question_sets.py` | `2FF8090C17B2AA89EC96C708302EFDF895D3797BD759ED986AD2110970F98FE0` |
| `references/stockqa-integration.md` | `A4D1193F769729B4952A24AD21F2694352182F63BA6B3D195FF7BA22C78F04DA` |

## Findings

No blocking or non-blocking code findings remained in the reviewed scope.

Q12 computes `input_question_sha256` from the actual `Question.text`. The synchronous and asynchronous Responses paths copy the real HTTP status into top-level execution metadata and the successful attempt receipt. The serialized receipt adds hashes and status fields without persisting the prompt text, response body, authorization header, or API key. Existing failure receipts remain sanitized.

S02 requires a true integer HTTP status of `200` and closes the final attempt against the top-level request, response, model, prompt hash, search receipt, search status, response status, and HTTP status. Independent mutations setting the final-attempt HTTP status to `201`, `true`, and `"200"` all produced `score=null` with `screening_status=unusable`.

The isolated integration test exercises the real StockQA Responses parser, client, provider, runner, public CLI serializer, and S02 importer while stubbing only `Session.post`. It produced score `8` and `screening_checked` for the selected questions. No live provider request was made.

## Independent test evidence

| Scope | Result |
|---|---|
| StockQA relevant expanded targeted set | `83 passed` |
| StockQA suite excluding `tests/unit/test_http_client.py` | `461 passed, 1 skipped` |
| invest-quick-scan `tests/test_question_sets.py` | `45 passed, 92 subtests passed` |
| invest-quick-scan full `tests` suite | `220 passed, 128 subtests passed` |

Tests ran with bytecode and pytest cache disabled and with temporary output under a writable isolated directory. The unfiltered StockQA suite was not rerun because its 13 known failures arise from sandbox denial while reading the Miniconda certifi CA bundle in unrelated HTTP-client tests. The skipped live test remains unexecuted and is not live-provider evidence. The independent local full run did not reproduce the previously observed Windows GBK subprocess warning.

## Decision limits

Q12 and the corresponding S02 downstream path are verified for the reviewed offline/local contract and integration scope. Real OpenAI search execution remains outside this review. The model/provider-priority cascade assigned to implementation-plan Q04 is wholly outside this report and remains unverified here.
