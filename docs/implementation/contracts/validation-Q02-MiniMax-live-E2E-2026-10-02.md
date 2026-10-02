# Q02 MiniMax live search E2E record

Date: 2026-10-02 (UTC)
Owner repository: StockQAbyLLM, branch `master`, HEAD `82f1794d873cf4b68dc3a2d5a8e7af03df4cfa54` (parent `ced1faa`). The live passes were executed against the `ced1faa` source content; `82f1794` differs only by two test files and a one-line parser docstring (`前`→`前后`), which is behavior-neutral.
Status: **Q02 verified for this content after independent review (`approved`). This does not close G1, the wider live-sample gate, or cross-repository integration.**

## Run

- Commands (from a unique temporary working directory, `PYTHONPATH` to the owner repo, `-p no:base_url --no-cov`):
  - `python -B -X utf8 -m pytest "C:/Users/郑曾波/Projects/StockQAbyLLM/tests/live/test_live_quick_scan.py::test_live_minimax_anthropic_search_runs_public_company_through_cli_and_cleans_local_artifacts" ...` → **1 passed**
  - `python -B -X utf8 -m pytest "...::test_live_minimax_search_runs_public_company_through_cli_and_cleans_local_artifacts" ...` → **1 passed in 28.20s**
- Opt-in: `STOCKQA_RUN_LIVE_E2E=1`; key read from the existing `MINIMAX_API_KEY` environment variable, never printed or saved.
- Request: one public CLI quick-scan question for Microsoft Corporation, Entity `issuer:US5949181045`, provider `minimax`, model `MiniMax-M3`, `--require-search`, against `https://api.minimaxi.com/v1/responses` and the Anthropic-compatible messages endpoint.
- Assertions (per test): exact entity name; `provider=="minimax"`; `requested_model`/`actual_model=="MiniMax-M3"`; `response_id`, `attempt_id` present; `request_id` null-or-present-per-vendor; `search_status=="executed"` with bound search receipt and ≥1 source URL; answer status in allowed set with consistent score; temp-dir artifacts cleaned.
- Isolation: each run used a fresh `TemporaryDirectory`, asserted cwd restored, no lasting files or downloads; StockQA Git status stayed at the 4 preserved untracked entries (` .codegraph/`, `.workbuddy-ai/`, `nul`, `progress_update.txt`) before and after.

## Fix iterations and cost tally

Four live rounds plus seven minimal single-call probes (each declared before execution) located and closed four independent defects; all payload claims were verified against official MiniMax docs (`guides/server-tools.md`, `api-reference/responses-create.md`, `api-reference/text-chat-anthropic.md`):

1. Anthropic `tool_choice={"type":"tool",...}` violated the official enum (only `auto`/`none`) → `{type:"auto"}`.
2. Chinese system line concatenated into Responses `input` suppressed `web_search` (3/3 zero-search runs with it vs 4/4 searching without) → moved to the official `instructions` field (payload now exactly `{model, instructions, input, tools}`; locked by contract test).
3. Prompt: explicit search mandate + JSON-first final-message rule (vendor preamble shrunk 1297→139 chars).
4. Models still emit prose before the JSON → strict parser upgraded (Q02+Q03 joint batch) to "exactly ONE complete top-level JSON object + full identity/score bindings", preserving all Q03 fail-closed properties (duplicate keys, nested/outer conflicts, wrong bindings, 0/multi-candidate rejection).
5. Official server-tools timeout guidance → live test timeouts raised (config 300s / subprocess 360s).

Total: approximately 20 single-question MiniMax API calls across all probe/live iterations (≈11 live E2E invocations + 9 probes), aggregate magnitude of cents (RMB) at official pricing; exact billing is the owner's MiniMax console. No other network or paid API was used.

## Offline regression on the same content

- Full offline suite: **854 passed, 4 skipped** (the 4 skips are the env-gated live E2E tests: openai/minimax×2/mimo without `STOCKQA_RUN_LIVE_E2E=1`).
- Gates: mypy 0 errors (46 files), bandit 0 findings, black/isort clean, ruff clean on all changed files.
- The full pre-commit chain (whitespace/yaml/json/toml, black, isort, mypy, pylint ≥9, detect-secrets, bandit, pip-audit, pytest unit) passed at both commits.

## Exact source snapshot (SHA-256, uppercase)

| StockQAbyLLM file | SHA-256 | note |
|---|---|---|
| `src/providers/llm_client.py` | `B38E1B76EB930CCCCB50D5C383CB10E07C4A0404ED0A91371F5C2A0D3D3C9EDA` | same at ced1faa and 82f1794 |
| `src/providers/base_llm_provider.py` | `37C75414D85BFB0455AAD711731CCEE2E534E132D36CE75D2E5E467F04104306` | same at ced1faa and 82f1794 |
| `src/providers/llm_response_parser.py` (live-tested) | `6D39FF263496088CD2D1A30FFF3959CD6D4C140290E3DB945A33D7328363999E` | ced1faa version |
| `src/providers/llm_response_parser.py` (current) | `D3EE74412EB0E7A40E71664513F7B01019DD9EE2C6EDD74FDFF1CF3DB512DE2C` | 82f1794: docstring-only delta |
| `src/providers/llm_provider.py` | `956FFAED9D87ED39A1F80D5589A21EA388610D4D03B86AD26D63E5D5FD340427` | |
| `src/core/qa_engine.py` | `B0000663295BDE179DBC5B8D3B0DDF51550D418E92B4C30C2E269B480F1E85A0` | |
| `tests/live/test_live_quick_scan.py` | `6EFA73CBFF6AC1EC57AE06E021E0CDBC8DD75E21B38C44FAD4D4B4769FF48090` | timeouts 300/360 for both minimax tests |

## Independent review

Single focused read-only review over `ced1faa` returned `changes_requested` (one medium: the minimax `instructions`/`input` payload split had no contract test; two low: strict docstring wording, zero-candidate case). Fixed in `82f1794` (payload-lock contract test, zero-candidate test, docstring). The same review session re-verified: mutation probes confirmed the new test fails on both the old concatenated payload and a prefixed-input variant; 171 tests over the three touched files; full offline suite 854 passed; ruff/black clean → **final verdict `approved`**, with an explicit statement that the LLM-02/LLM-11 case→test mapping (227 selected tests) plus these live results satisfy the Q02 completion criteria.

## Scope notes

- Case statuses in `acceptance-cases.json` remain `specified_not_executed` per repo discipline (status fields are not execution ledgers); execution evidence lives here and in `progress.md`.
- This record does not certify other providers, other models, pricing universality, or any G1/cross-repo milestone.
