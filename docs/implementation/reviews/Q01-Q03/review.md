# Q01–Q03 independent review — 2026-09-24

**Decision: do not mark Q01–Q03 verified.** Q01 and Q03 need revision for reproduced acceptance failures. Q02 remains pending: its live search requirement was not exercised, and only the unsupported-provider branch of LLM-06 was reproduced. Existing targeted tests passing does not close the failing fixed-oracle cases below.

## Exact scope and safeguards

- Owner repository: `C:/Users/郑曾波/Projects/StockQAbyLLM`; HEAD `3c685dda28f67a00bd653ad257a121d3b8edebb8`, with pre-existing tracked modifications and untracked files. Review binds the working files, not HEAD alone.
- Plan: `1.6.2`; Q01–Q03 packets and SC-01–04 / LLM-01,02,06,07 read before execution. CodeGraph was available; structural context was requested with the explicit StockQA project path.
- No owner source, tests, configuration, credentials, logs, outputs, or user data were modified. All added review code, captured stdout/stderr, XML, hashes and reports are under this review directory.
- Every execution used a fresh system TEMP root, `-B`, `PYTHONDONTWRITEBYTECODE=1`, disabled automatic pytest plugin discovery, explicit asyncio plugin, no pytest cache, explicit TEMP pytest/log/XML locations, and a filesystem audit guard. Provider credentials were removed from the child environment; fixture keys were fabricated. The tests used existing real implementations and replaced only HTTP transport for provider examples.
- External socket connections, DNS calls and child process launches were denied. The sole connection exception was Python's own `socket._fallback_socketpair` called from the exact standard-library `socket.py` for Windows asyncio's internal wake-up pipe; it is not a general localhost or provider allowance.
- Pre/post snapshots cover **2,593 readable filesystem entries**, with per-file SHA-256, size and mtime, plus read-only Git status. Every run reports no added, removed or changed entries and unchanged Git status. The pre-existing inaccessible `.pytest_cache` directory is an explicit observation blind spot; the write guard disallowed writes there. The existing device-like `nul` path was inventoried without opening it. Thus the claim is zero observed drift plus denied external writes, not an assertion that inaccessible cache contents were readable.
- TEMP roots and a hash inventory of their generated files were retained for evidence. No pre-existing file or directory was removed, reset, or cleaned.

See `implementation-snapshot.json` for the relevant source/test/plan hashes, `artifact-index.json` for report artifact hashes, and each `*-execution.json` for the exact Python command, cwd, exit, generated TEMP artifact inventory and external state comparison.

## Executed checks

| Run | Result | Interpretation |
|---|---|---|
| `targeted` | exit 3, 0 tests | Review harness initially denied pytest's default `\\.\nul` log device. Preserved as a harness failure; no product conclusion. |
| `targeted-r2` | exit 1, 107 passed / 13 setup errors | Harness initially denied Windows asyncio's internal socketpair. No tested assertion was changed; the narrowly scoped stdlib exception described above was added. |
| `targeted-final` | exit 0, **120 passed**, 0 skipped | Existing parser, models, answer services, sync/async clients, providers and public CLI tests. |
| `counterexamples` | exit 1, **9 passed / 4 failed**, 0 skipped | Independent fixed-oracle cases through real parser/provider/generator/public CLI, with `Session.post` transport fixture only. These four failures are genuine product/contract failures. |
| `tls-and-consumer` | exit 1, **12 passed / 14 failed**, 0 skipped | All 25 HTTP client tests plus S02 consumer. Thirteen failures are the certifi ACL issue; the additional consumer failure is a logger/module-order issue described separately below. |
| `consumer-standalone` | exit 0, **1 passed**, 0 skipped | Exact S02 test rerun alone: actual StockQA CLI output imports through the local screening consumer and preserves score 8. No expectation relaxed. |

The selected owner test files were `tests/unit/test_llm_response_parser.py`, `test_models.py`, `test_services.py`, `test_llm_client.py`, `test_search_provider.py`, and `tests/integration/test_quick_scan_cli.py`. Coverage reports were disabled by overriding `addopts` solely to avoid owner-repository output; no tests/assertions in these selected files were deselected. This was not the entire StockQA suite or a coverage-gate run.

## Findings requiring revision

### F01 — SC-02 legacy transport 5 becomes a scored answer and enters the CLI average

- Tasks: Q01, Q03. Severity: blocking acceptance failure. Status: open.
- Location: `src/providers/llm_response_parser.py:139` and `:144`; `src/services/answer_generator.py:63`; `src/runners/llm_runner.py:391`.
- Trigger: valid outer identity/question fields, outer `score=5`, and `description` equal to serialized `{"id":"IQS_05","status":"insufficient_evidence","score":null,...}`.
- Expected: either explicit legacy normalization to a nullable answer or rejection from the native path; transport 5 must never be adopted as a score or enter an average.
- Observed through public CLI: `status="scored"`, `score=5`, exit 0, printed average 5.0. The parser treats description as opaque text and defaults a missing outer status to scored.
- Reproduction: `test_acceptance_counterexamples.py::test_sc02_legacy_inner_unknown_transport_five_never_becomes_scored`; exact payload/result and traceback are in `counterexamples-stdout.log` and the run-local result JSON inventory.
- Requested fix: make the selected reply protocol explicit; enforce nested status/score semantics for supported legacy replies, or fail closed when that protocol is not selected. Do not silently treat a recognized inner unknown as a scored native answer.

### F02 — SC-04 nested score and question conflicts are not rejected by StockQA

- Tasks: Q01, Q03. Severity: blocking acceptance failure. Status: open.
- Location: `src/providers/llm_response_parser.py:90` / `:139`; `src/services/answer_generator.py:79`.
- Triggers: (a) outer score 5 / serialized inner score 8; (b) outer question IQS_05 / serialized inner question IQS_06 with score 8.
- Expected: explicit invalid result, nullable adopted score, and retained failure metadata; no choosing an outer score/ID to resolve a conflict.
- Observed: (a) scored/5; (b) scored/8, both exit 0. `parsed_score` checks only the already parsed outer value, not the conflicting inner structure.
- Reproductions: `test_sc04_inner_outer_score_mismatch_is_not_a_scored_answer` and `test_sc04_wrong_inner_question_id_is_not_a_scored_answer` in the independent probe file.
- Requested fix: bind all supported protocol identity/status/score layers before returning a successful `ParsedLLMAnswer`. Keep native plain-text descriptions and explicitly selected legacy structured descriptions distinguishable.
- Boundary of impact: the downstream screening consumer has its own fail-closed checks and its good eight-score path passed. This review does **not** claim these counterexamples bypassed the final screening acceptance or formal research gate. They nevertheless violate the fixed upstream task cases and are visibly scored/averaged by the public StockQA CLI.

### F03 — LLM-07 duplicate conflicting JSON IDs silently choose the last ID

- Task: Q03 (shared parser also affects Q01). Severity: important acceptance failure. Status: open.
- Location: `src/providers/llm_response_parser.py:90`.
- Trigger: a single native response containing `"question_id":"IQS_06","question_id":"IQS_05"`, with the remaining fields matching IQS_05.
- Expected: reject an ambiguous structured response; if a format repair is authorized, consume only that bounded budget. Never synthesize success by selecting the last duplicate key.
- Observed: default `json.loads` discards the first ID; CLI exports scored/8, exit 0, one HTTP fixture call, and prints an average of 8.0.
- Reproduction: `test_llm07_conflicting_duplicate_json_question_ids_do_not_choose_last`.
- Requested fix: reject duplicate object keys before semantic validation, including conflicting score/status/entity fields, and cover both sync and async shared-parser paths. Do not merely deduplicate after JSON decoding.

## Case disposition

| Case | Disposition | Evidence and remaining boundary |
|---|---|---|
| SC-01 | passed offline | Native parser/provider/generator/CLI exact 8; standalone actual CLI-to-screening consumer exact 8. No `(5,8)` assertion. |
| SC-02 | **failed** | Native nullable path passes, legacy inner unknown/outer transport 5 fails in the public CLI (F01). |
| SC-03 | passed offline | Existing strict boundary tests cover bool, 0, 11, fraction, numeric string, NaN string and valid 1/5/10; seven invalid values were independently rerun through the CLI and remained unscored. |
| SC-04 | **failed** | Native explicit wrong-ID rejection passes; nested score and nested identity conflicts fail (F02). |
| LLM-01 | **pending live** | Offline requests contain real Responses search-tool fields and parsed execution metadata. No real provider call, official live response, cost receipt or live source verification was run in this read-only review. |
| LLM-02 | passed offline | Missing tool execution receipt yields nullable insufficient evidence in sync, async and CLI paths despite model text/URLs. |
| LLM-06 | **partial / pending** | Unsupported endpoint/provider is rejected before HTTP. The combined requirement also demands all-model exhaustion → `retry_wait` and global bad-request dispatch policy; those multi-model runtime semantics were not reproduced by Q01–Q03 selected tests and are not established by a single-provider unsupported-capability test. |
| LLM-07 | **failed / partial** | Wrong issuer/ID, malformed surrounding text, bounded one repair and preserving an already successful item pass. Duplicate conflicting JSON identity fails (F03); do not mark the whole case passed. |

## Environment and test-order limitations (not masked)

All 13 failing assertions in `tests/unit/test_http_client.py` stop when `httpx` calls `ssl.create_default_context(cafile=certifi.where())`, raising `PermissionError: [Errno 13] Permission denied` at `C:/Miniconda/Lib/ssl.py:717`; the CA file is `C:/Miniconda/Lib/site-packages/certifi/cacert.pem`. No certificate change, `verify=False`, alternative CA, skip, assertion weakening, or package modification was used. The remaining 12 tests in that file pass. Exact selectors/tracebacks are in `tls-and-consumer-junit.xml` and `tls-and-consumer-stdout.log`.

The S02 consumer check, when run **after** those HTTP tests in the same process, encounters a distinct `FileNotFoundError`: `src.utils.logger` was already imported with a relative `LOG_DIR`, and after the consumer test changes cwd to its own temporary directory a newly configured logger tries to open a nonexistent `logs/stock_qa_20260924.log`. The exact same consumer selector passes in a fresh isolated process. This is documented test-order sensitivity; it is not grouped with the certifi failures and not used to excuse F01–F03. A follow-up can make logger initialization or the test's run-local setup robust without writing to owner directories.

The final targeted run's guard recorded three attempted writes to the Windows null device from tooling; they were denied, the tests still passed, and no persistent external path was opened for writing. No provider network call occurred. Full-owner-suite, live search, multi-model runtime and release-gate claims remain out of scope/pending.

## Reproduction and handoff

Run only from the writable invest-quick-scan repository using a new label to avoid overwriting captured evidence:

```powershell
python -B -X utf8 docs/implementation/reviews/Q01-Q03/run_isolated_review.py replay-counterexamples C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/Q01-Q03/test_acceptance_counterexamples.py
```

The independent probes deliberately retain the fixed acceptance expectations and currently return four failures. An authorized owner implementation turn should fix F01–F03 and bind regression tests to the exact native/legacy protocol distinctions, rerun the existing 120 checks and these probes, then request a new review of the resulting per-file snapshot. Do not modify this review's failing expectations to match the current implementation. Q02 stays pending until its missing runtime/live evidence is available and authorized.
