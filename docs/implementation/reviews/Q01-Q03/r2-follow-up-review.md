# Q01/Q03 r2 independent follow-up review — 2026-09-24

**Decision: the requested Q01/Q03 remediation passes independent offline review at the exact snapshot below. F01, F02, F03 and F04 are resolved for the reproduced cases. No blocking finding remains within this follow-up scope.** This is not a blanket approval of Q02, live-provider behavior, all Q04 code, or unrelated files.

Reviewer: delegated independent question_audit agent. Completed UTC: 2026-09-24T22:12:23.324518+00:00.

## Snapshot and scope

Owner HEAD: `3c685dda28f67a00bd653ad257a121d3b8edebb8`. The existing Q04 working-tree changes remain present. All three supplied remediation hashes matched on initial inspection and after testing:

| Owner file | SHA-256 |
|---|---|
| `src/providers/llm_response_parser.py` | `9d5eb7d58dacfed1dffb605eca504d8a9ec6b6c39a5e2f4341d0a9b6f58aa867` |
| `tests/unit/test_llm_response_parser.py` | `3bf0d736cce8696caa2f70ad201a3c7beea1cda118ce43ec8c10252a174a8259` |
| `tests/integration/test_quick_scan_cli.py` | `e242ec7e6b1ea82c6ad056a644cc091901aceba3633e525ee2093b0d75955843` |

Source review covered the parser and its unit/public-CLI regressions. Other owner files were only read or exercised as dependencies. No StockQA source, tests, configuration, logs, bytecode, user data, index, or commit was changed. The only persistent local file created by this follow-up is this report.

## Independent execution

| Run | Result | Purpose |
|---|---|
| `r2-selected-gitverified` | **166 passed**, exit 0, no skips, 3.54 s pytest time | Six owner test files plus the unchanged r0 and r1 independent counterexample files. |
| `r2-consumer-gitverified` | **1 passed**, exit 0, no skips, 0.84 s pytest time | Existing S02 compose → real StockQA CLI → screening normalization in a fresh process. |

There are **167 distinct passing tests**. The initial runs also passed 166 + 1; they were repeated solely to repair an audit-harness Git observation problem described below. The submitter-reported 276-pass and 222-pass/139-subtest logs were not substituted for independent testing. The unrelated certifi HTTP-client suite was not rerun; its previous ACL limitation remains outside this follow-up.

### Cases and findings

1. **F04 closed — supported structured answer is preserved.** The original r1 `test_valid_existing_structured_description_remains_compatible_through_cli` now passes unchanged. With agreeing outer and nested `scored`/8/`IQS_05`, real public CLI processing returns score 8, success exit, and one mocked transport call. The owner positive test also checks the nested description is preserved exactly. The existing S02 consumer acceptance test separately passes through question composition, provider prompt binding, execution receipts, evidence URLs, answer export and local normalization. Its oracle still requires a genuine score of 8; it was not weakened to accept unknown/null.

2. **F01/F02 remain closed — ambiguity is rejected.** The unchanged r0 real-CLI negatives and r1 strict/Markdown extraction matrix reject inner insufficient-evidence/null with outer 5, inner 8 with outer 5, and inner `IQS_06` with outer `IQS_05`. The native unknown/null positive and valid score-boundary tests also pass. The new helper compares nested status, strict score type/value, and all supplied nested question IDs against the outer/expected identity; it preserves agreement and does not silently adopt a conflicting layer.

3. **F03 closed — duplicate keys cannot promote nested metadata.** Both direct JSON and Markdown-wrapped JSON containing duplicate outer `question_id` and a nested metadata answer with score 9 return `None` in compatibility mode. The unchanged independent r1 direct reproducer passes, as do the owner direct and Markdown fixtures and the public-CLI negative. Direct duplicate parsing now terminates fallback; wrapper extraction consumes a balanced outer object and rejects its duplicate keys rather than considering nested metadata as an answer.

4. **Existing tested compatibility stays intact.** Direct native JSON, surrounding text, Markdown wrappers, braces in a description, valid score boundaries, non-answer JSON prose, nullable unknown, exact question/entity binding in strict quick-scan mode, bounded format repair, partial-answer preservation, search-receipt enforcement, and sync/async tests all pass. Assertions are meaningful behavior checks; the prior independent failure fixtures were reused unchanged.

Exact F03 reproducer (also tested inside a fenced Markdown wrapper):

```json
{"question_id":"IQS_06","question_id":"IQS_05","score":8,"description":"ambiguous outer","metadata":{"question_id":"IQS_05","score":9,"description":"not the answer"}}
```

Called using `LLMResponseParser().parse_structured_response(content, expected_question_id="IQS_05")`; expected and observed result: `None`.

## Isolation, repository invariance and limitations

Each run used a unique TEMP child as CWD, TEMP/TMP/TMPDIR, pytest basetemp, log directory and XML destination. Python ran with `-B -X utf8`, `sys.dont_write_bytecode=True` and `PYTHONDONTWRITEBYTECODE=1`. Plugin autoload was disabled and `pytest_asyncio.plugin` explicitly loaded. Cacheprovider was disabled. Provider credentials and the live-E2E environment switch were stripped. Only mocked HTTP transport was used.

The reused child audit guard rejected filesystem mutations outside its own TEMP root and prohibited external network, DNS and subprocess calls. Its existing narrow exception only permits the Python standard-library Windows asyncio socketpair self-pipe. Each run recorded three denied `\\.\NUL` write probes; these did not affect test success. No provider/API connection was made.

**Harness correction:** the initial runner snapshot invoked Git without a command-local ownership override. Git returned exit 128 (`dubious ownership`), so equal empty Git stdout was not valid invariance evidence. This was identified from the raw state files, explicitly rejected as evidence, and corrected only in a temporary wrapper using `git -c safe.directory=C:/Users/郑曾波/Projects/StockQAbyLLM --no-optional-locks ...`. No global or repository Git configuration was written. Both suites were then rerun with successful pre/post Git status and HEAD checks.

The final two runs each observed **2,594 filesystem entries** with no added, removed or changed records, successful unchanged Git porcelain status, and unchanged HEAD. The pre-existing unreadable `.pytest_cache` remains an observation blind spot; external writes were still denied by the guard. The pre-existing device-like `nul` was inventoried without opening it. Git also warned that the user global ignore file was inaccessible; the command succeeded and this warning was stable. No pre-existing file was deleted or reset.

### Reproduction commands

The existing local `run_isolated_review.py` was imported by a temporary wrapper, with its REPORT redirected into this review TEMP root and its Git snapshot calls overridden as above. The wrapper itself was invoked with `C:/Miniconda/python.exe -B -X utf8`. Exact final child commands and pytest options:

**r2-selected-gitverified**

```text
["C:\\Miniconda\\python.exe", "-B", "-X", "utf8", "C:\\Users\\郑曾波\\Projects\\invest-quick-scan\\docs\\implementation\\reviews\\Q01-Q03\\run_isolated_review.py", "--child", "C:\\Users\\郑曾波\\AppData\\Local\\Temp\\stockqa-q01q03-r2-review-a7e7e58afdf647d88e0d5623bc4d0c79\\stockqa-readonly-review-r2-selected-gitverified-9uxzc4r4", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\unit\\test_llm_response_parser.py", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\unit\\test_models.py", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\unit\\test_services.py", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\unit\\test_llm_client.py", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\unit\\test_search_provider.py", "C:\\Users\\郑曾波\\Projects\\StockQAbyLLM\\tests\\integration\\test_quick_scan_cli.py", "C:\\Users\\郑曾波\\Projects\\invest-quick-scan\\docs\\implementation\\reviews\\Q01-Q03\\test_acceptance_counterexamples.py", "C:\\Users\\郑曾波\\Projects\\invest-quick-scan\\docs\\implementation\\reviews\\Q01-Q03\\test_r1_followup.py"]
```

Child CWD: `C:\Users\郑曾波\AppData\Local\Temp\stockqa-q01q03-r2-review-a7e7e58afdf647d88e0d5623bc4d0c79\stockqa-readonly-review-r2-selected-gitverified-9uxzc4r4`.

**r2-consumer-gitverified**

```text
["C:\\Miniconda\\python.exe", "-B", "-X", "utf8", "C:\\Users\\郑曾波\\Projects\\invest-quick-scan\\docs\\implementation\\reviews\\Q01-Q03\\run_isolated_review.py", "--child", "C:\\Users\\郑曾波\\AppData\\Local\\Temp\\stockqa-q01q03-r2-review-a7e7e58afdf647d88e0d5623bc4d0c79\\stockqa-readonly-review-r2-consumer-gitverified-gpi7fr75", "C:\\Users\\郑曾波\\Projects\\invest-quick-scan\\tests\\test_question_sets.py::QuestionSetTests::test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline"]
```

Child CWD: `C:\Users\郑曾波\AppData\Local\Temp\stockqa-q01q03-r2-review-a7e7e58afdf647d88e0d5623bc4d0c79\stockqa-readonly-review-r2-consumer-gitverified-gpi7fr75`.

Common pytest options (followed by the selectors in the commands above):

```text
-c C:/Users/郑曾波/Projects/StockQAbyLLM/pyproject.toml -o addopts= -p no:cacheprovider -p pytest_asyncio.plugin --strict-markers --strict-config -ra -v --basetemp <unique-CWD>/pytest --junitxml <unique-CWD>/junit.xml --log-file <unique-CWD>/pytest.log
```

Read-only `git diff --check -- src/providers/llm_response_parser.py tests/unit/test_llm_response_parser.py tests/integration/test_quick_scan_cli.py` also exited 0.

## Evidence hashes

Raw test logs/state manifests were generated only under the unique TEMP root. Their hashes and decisive results are retained here; the temporary copies are removed during cleanup. Existing r0/r1 review artifacts remain untouched.

| Evidence | SHA-256 |
|---|---|
| `r2-selected-stdout.log` | `b4e0cc57235d3c45c1a397cb997f597c61efdfae087f36ee0e3529713e2a1ec0` |
| `r2-selected-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2-selected-pre-state.json` | `91b1c7e53504d6a9dc569e4a6e59e9dd1ee30b06980092f953c753cd17c52411` |
| `r2-selected-post-state.json` | `91b1c7e53504d6a9dc569e4a6e59e9dd1ee30b06980092f953c753cd17c52411` |
| `r2-selected-execution.json` | `681eb0c564716f99254657608d9633a07b037baee94860dd55cc341b67884226` |
| `r2-selected-junit.xml` | `b35cbcac2dd87cf206062337478326ae6f5a67cce39a95091a843152354f88b7` |
| `r2-selected-guard-events.json` | `84ab063e442992daf4a6f3898b3a798afed613f93af78542387669f1a7b4c8b3` |
| `r2-consumer-stdout.log` | `7be0c6476bfd7db46e1bd0d82cd16b42aaee1327ac311717d670d43293e81efe` |
| `r2-consumer-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2-consumer-pre-state.json` | `91b1c7e53504d6a9dc569e4a6e59e9dd1ee30b06980092f953c753cd17c52411` |
| `r2-consumer-post-state.json` | `91b1c7e53504d6a9dc569e4a6e59e9dd1ee30b06980092f953c753cd17c52411` |
| `r2-consumer-execution.json` | `320992e2e45619443faa6f442ea24c983c00c4759cd48256a6b5af5013fc5a69` |
| `r2-consumer-junit.xml` | `7f752c7edb901e31b07c8a8e91b7834dcada31b676fb5d522f94ad77fac5b6eb` |
| `r2-consumer-guard-events.json` | `84ab063e442992daf4a6f3898b3a798afed613f93af78542387669f1a7b4c8b3` |
| `r2-selected-gitverified-stdout.log` | `0b0a249c61083ce4fe1525c2c2ca6f4598a03de8b18ffd986b9cdab7f881a688` |
| `r2-selected-gitverified-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2-selected-gitverified-pre-state.json` | `7dcea7142d34c9fbcc25074ef7bd365f81d32c7354bbf957908e5930a6108202` |
| `r2-selected-gitverified-post-state.json` | `7dcea7142d34c9fbcc25074ef7bd365f81d32c7354bbf957908e5930a6108202` |
| `r2-selected-gitverified-execution.json` | `971458ba1f151cf130e4620e5bdaf72f6858d2031e731e89cdd5b0e0a59cd5b2` |
| `r2-selected-gitverified-junit.xml` | `e28cda981b3cb33f142d487a479286427dfd2acba9f241513cc257152a8bcdf7` |
| `r2-selected-gitverified-guard-events.json` | `84ab063e442992daf4a6f3898b3a798afed613f93af78542387669f1a7b4c8b3` |
| `r2-consumer-gitverified-stdout.log` | `d0c141c48de9f5ba6c61386fc004cf1f0bf1f82b0886b6f802478b06f8172b35` |
| `r2-consumer-gitverified-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2-consumer-gitverified-pre-state.json` | `7dcea7142d34c9fbcc25074ef7bd365f81d32c7354bbf957908e5930a6108202` |
| `r2-consumer-gitverified-post-state.json` | `7dcea7142d34c9fbcc25074ef7bd365f81d32c7354bbf957908e5930a6108202` |
| `r2-consumer-gitverified-execution.json` | `a7d952479ca22490752d77a6446d051eb4533312aaed47725817b8b44983560e` |
| `r2-consumer-gitverified-junit.xml` | `27fbc30351bd711fbc72a76f24e3ea6391ba4a644b02631253720e74fecb9adc` |
| `r2-consumer-gitverified-guard-events.json` | `84ab063e442992daf4a6f3898b3a798afed613f93af78542387669f1a7b4c8b3` |

| Reviewed supporting file | SHA-256 |
|---|---|
| `invest-quick-scan/docs/implementation/reviews/Q01-Q03/run_isolated_review.py` | `232a7f12b28e692970d5c9f194777fbb774449fa51afed1e1d944f709013daa0` |
| `invest-quick-scan/docs/implementation/reviews/Q01-Q03/test_acceptance_counterexamples.py` | `262ded2365b5e62c362ce7828a2785cebbda4f1a2f54a86789af558acec784ca` |
| `invest-quick-scan/docs/implementation/reviews/Q01-Q03/test_r1_followup.py` | `023372a5ea94b55b23f6d898d12480b2f077d9e4244f945e5aa61d4db3ba35a5` |
| `invest-quick-scan/tests/test_question_sets.py` | `2ff8090c17b2aa89ec96c708302efdf895d3797bd759ed986ad2110970f98fe0` |
| `StockQAbyLLM/tests/unit/test_models.py` | `18cbd10f47e9da821e8e542cb69e3d4cb57161229dc29e8cc8e5edeb62aee603` |
| `StockQAbyLLM/tests/unit/test_services.py` | `c4d99935e48ad2f065dcef547b4b0444524090f40c7bd6181fd2f755e6179ff8` |
| `StockQAbyLLM/tests/unit/test_llm_client.py` | `29c7ecc54c9c32c8aee6939f07bea30f8f88fb5350679a78b26c92bf048bf32b` |
| `StockQAbyLLM/tests/unit/test_search_provider.py` | `24204047e9e52a9621aacd210b4af85f968c45dcb9bb569101f6e87f67c17739` |
| `StockQAbyLLM/src/runners/llm_runner.py` | `579cde5a1fb21604e0a2bdca5667c880e45e78864602e2bd664f23a2dbedd2a4` |
| `StockQAbyLLM/src/services/answer_generator.py` | `b59840da063d00d7bcaab4ba960b88797f6466a4ead868ba0a7110e4d8fd44f4` |
| `TEMP/run_gitverified.py` | `118ea3f12559b322816e09b7745ae477e3158791c671faadef85ae7a2f400890` |

Final Git porcelain stdout SHA-256: `5b6bcd360b6e5c3b0f800ef5c8fd50f8b023b37e321d64a6c4fa411b800ce9fd` (identical in both final pre/post pairs).

## Cleanup

Review-owned TEMP root: `C:\Users\郑曾波\AppData\Local\Temp\stockqa-q01q03-r2-review-a7e7e58afdf647d88e0d5623bc4d0c79`. Cleanup confirmation is appended only after native PowerShell verifies this exact root is below the system TEMP directory and removes it successfully.

Cleanup verified: the exact review-owned TEMP root was removed; no pre-existing TEMP directory, StockQA file, or previous review artifact was removed.
