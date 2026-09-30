# Current repository and interface baseline (P00 revalidation)

**As of:** 2026-09-26 (read-only snapshot)  
**Task:** P00 / BASE-01, BASE-02  
**Owner:** `iqs`  
**Scope:** Current local contracts and the four named repositories. This is a source, interface, and offline-test baseline; it is not a production search or investment-quality validation.

## Outcome

BASE-01 and BASE-02 pass for this snapshot. The original 2026-09-22 baseline report and its legacy receipt remain unchanged and hash-locked by P01. This report separates historical defects from current behavior, records the working-tree state because all repositories are dirty, and uses only read-only source/index inspection plus local offline commands. No company filing, company document, web page, or raw model response was downloaded or stored; no live model/API request was made; no external repository file was changed.

## Repository snapshots

Git status counts were captured at P00 entry, before adding the P00 report and logs, from `git status --short`. They include unrelated and pre-existing work and are not attributed to this P00 pass. `HEAD` alone is not a complete source identity for any of these dirty worktrees, so the relevant current source files are also hash-listed below.

| Repository | `HEAD` | Tracked changes | Untracked entries | Use in this design |
|---|---|---:|---:|---|
| `invest-quick-scan` | `25b8d14316c06390450e5a1d8883583bfd039d0d` | 43 | 292 | Versioned question modules, scoring and fact prompt composition, standard output and local contracts. |
| `StockQAbyLLM` | `3c685dda28f67a00bd653ad257a121d3b8edebb8` | 28 | 14 | Question execution, LLM/web-search adapters, response parsing, provider routing and durable work primitives. |
| `StockWiki` | `f5b8526c78ef0bc7df27885da043ce5a2534fffb` | 653 | 276 | Authoritative research workspace and the currently added quick-scan identity/universe SQLite base. |
| `company-wiki` | `bf0c8b27e83c3ee7e533c6031fefad8e27e5e121` | 9 | 7 | Read-only listed-security identity/source exports; it remains the owner of document collection and storage. |

All four CodeGraph indexes are reachable and report healthy indexes: local project 39 files/1,256 nodes; StockQA 92/1,584; StockWiki 262/4,490; company-wiki 550/10,710. Some recently added, untracked StockQA and StockWiki quick-scan files are not present in their CodeGraph indexes, so their known paths were read directly; this is index lag, not a claim that the files are absent. No index initialization or external write was needed in this pass.

## Current interfaces and ownership

### Quick-scan question and answer path

- The local scoring catalog validates as **48 modules / 222 questions**. The published package is `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f`, release `modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9`. The independent fact-library validator returns `ok=true` and `network_used=false`.
- `JSONConfigManager.load_questions()` remains the legacy text-list interface. The separate `load_question_items()` interface returns stable-ID question objects and rejects repeated IDs; this is the adapter used by quick-scan exports.
- The StockQA answer path now propagates nullable score/status and checks question identity and conflicting structured score metadata. The old implementation that replaced scores with 5 is not current behavior.
- StockQA contains a search-aware HTTP adapter, provider response parsing, ordered search routing, provider health state and a durable SQLite work store. The historical `ProviderCascade` helper still holds its own state in memory; it must not be confused with the durable quick-scan health/work stores or their completeness.
- The final-snapshot MiniMax check returned HTTP 200/completed but did not establish a completed web-search chain. Its `search_status` remains unverified and the result is rejected for scoring acceptance. Therefore earlier live-search success against an older snapshot does not make current Q02 fully verified. Q02 remains partial; Q04/Q08 still have the persistent retry/recovery work recorded in the task plan.
- StockQA's README still describes search and LLM integration as placeholders, which is stale relative to the current uncommitted implementation. The attempted `main_with_llm.py --help` probe did not reach the CLI parser: importing the app tried to create `logs/stock_qa_20260926.log` in the external worktree and the read-only boundary denied it. No file was created or changed. This attempt is recorded as an environment/write-boundary finding, not test evidence; further external execution is deferred to an explicitly isolated owner test.

### Result storage and listed-security identity

- `StockWiki/stockwiki/quick_scan_store.py` is present in the dirty worktree (SQLite schema v1). It owns a separate quick-scan identity/universe store with entity, security, segment, universe and membership tables, plus idempotent migration, transaction, add/list operations and market/security constraints. This base does not yet persist scored observations, fact observations, scan history or the full query/UI projections; those remain later owner work. It does not migrate the formal StockWiki YAML workspace or collect company documents.
- StockWiki is the owner of accepted research meaning and durable investment research. The quick-scan database may own its lightweight screening identities and observations under the approved contract; it must not become a second formal research ledger.
- `company-wiki` exposes versioned per-market security-master snapshots through `SecurityMasterStore`, `SecurityIdentityResolver` and the `company-wiki-identify` CLI. An explicit `--refresh` can fetch and write official snapshots; it was not used. Quick-scan identity lookup must use an already available read-only snapshot and must not copy source documents, web text, or financial filings.
- No UI/runtime wiring or 2,000-company production coverage is evidenced by this baseline. The cross-project storage/UI tasks and G4–G6 live acceptance remain open.

## Historical versus current behavior

The preserved 2026-09-22 report records a then-current `AnswerGenerator` fixed-5 defect and a 5-or-8 observational assertion. That report is historical evidence only. Q01/S02 subsequently repaired the pass-through path. The current focused offline integration test invokes the actual StockQA CLI path with an in-memory HTTP session and asserts score **8** through parser, generator and import normalization; current unknown responses remain `unknown` / `null` rather than defaulting to 5. The test is not a real web search. It runs in a unique temporary directory, restores process state, checks that no StockQA bytecode changed and cleans up its outputs.

The original baseline remains preserved at:

- `docs/implementation/baselines/baseline-report-2026-09-22.md`
- `docs/implementation/baselines/receipt-P00.json` (legacy format; not current completion evidence)
- P01's immutable context manifest `docs/implementation/baselines/P00-context-manifest.json`

The legacy receipt remains at its original path so the manifest stays valid. Current P00 completion evidence is issued separately at the validator's canonical dependency path `docs/implementation/contracts/receipt-P00.json`.

## Checks performed

| Check | Command / selector | Result | Evidence |
|---|---|---|---|
| Local scoring catalog and release | `python -B -X utf8 scripts/question_sets.py validate` | 48 modules, 222 questions, published package/release identified | `validation-P00-scoring-bank-r1.log` |
| Local fact prompt library | `python -B -X utf8 scripts/standard_answers.py validate-library` | `ok=true`, network unused | `validation-P00-fact-bank-r1.log` |
| Current strict score pass-through | `test_question_sets.QuestionSetTests.test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline` | 1 passed; local stub only, not a search test | `validation-P00-strict-score-r1.log` |
| Plan package regression after the BASE-01 erratum | `python -B -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -v` | 79 passed, 0 skipped | `validation-P00-plan-tests-r1.log` |
| Current plan structure | `python -B -X utf8 scripts/implementation_plan.py validate` | 103 tasks / 327 cases / G6; `planning_valid=true` | `validation-P00-plan-validation-r1.log` |
| P01 verifier regression for unrelated-owner plan change | Read-only public verifier rerun after the P00 case/task correction | P01 remains `eligible_to_close=true`; P00 historical context remains hash-locked | P01 receipt, sidecar and context manifest |
| Current local offline repository regression | `python -X utf8 -m unittest discover -s tests -v` | 379 passed, 0 skipped (final frozen P01 snapshot) | `validation-P01-final-full-suite-r6.log` |

No product tests were run inside StockQA, StockWiki or company-wiki. Their worktrees contain substantial unrelated changes, and their documented test runners may write coverage/cache/report artifacts; this P00 owner has read-only authority there. Existing task-specific results are cited only at their recorded scope and are not presented as new full-suite results for the current dirty external snapshots.

## Representative current source hashes

These hashes identify the specific source snapshot read during this baseline; paths are relative to each repository. The uncommitted worktree may continue to change, so later implementation tasks must re-check their own owner files.

| Repository / path | SHA-256 |
|---|---|
| `invest-quick-scan` — `main_questions.json` | `1a21260b972784e94870006e4f47c74c4ad5804ce21269f10fabd2e2ffb7fc9b` |
| `invest-quick-scan` — `questions/catalog.json` | `252dab9e3f71868a71147ecb7dac64cc187d7d56002b28b266a74f406facaf10` |
| `invest-quick-scan` — `scripts/question_sets.py` | `134e2e72e3d83d11f42daed64de2570972686f3a1ae7614aab1f86ca27c389ee` |
| `invest-quick-scan` — `scripts/standard_answers.py` | `aa6ab1b54e54deff6810c02ca30646edb0913533200e55fd580285f08c5a9d5d` |
| `invest-quick-scan` — `scripts/task_receipts.py` | `1054cd195a4abcaace923628978630d71f0830591d58d294e214abdd0ad2c318` |
| `StockQAbyLLM` — `src/config/json_config_manager.py` | `6653e92b8e46c2ffcb0dfeb55540e4dd8655c74dd1ad38d8651fee7df497bb75` |
| `StockQAbyLLM` — `src/providers/llm_client.py` | `9977b097b1eb8870c0da7fd8f61e6d7318a63c050ff6e506c1d8b9724decbd3b` |
| `StockQAbyLLM` — `src/providers/llm_provider.py` | `ad7452aec809c6655a1124b614d2a6abf95047918348182a90db8291d4d0c377` |
| `StockQAbyLLM` — `src/services/answer_generator.py` | `b59840da063d00d7bcaab4ba960b88797f6466a4ead868ba0a7110e4d8fd44f4` |
| `StockQAbyLLM` — `src/utils/llm_integration.py` | `3e7bac54444adf59b7cf4043ab5c150e1af2bdfc3730b289c42751a2f88c01b9` |
| `StockQAbyLLM` — `src/utils/quick_scan_provider_health.py` | `7727fae30c07d08accb3412a2245966e293b58f3f35f071f85f43fed2a95ecf9` |
| `StockQAbyLLM` — `src/utils/quick_scan_work_store.py` | `c21ea1a3b1f0c1f352578bdc4f865be4ccc150a037aa667cf534f11c276acaa2` |
| `StockWiki` — `stockwiki/quick_scan_store.py` | `f0d3f4241b8f251a6996970a6af7eadd49463991ebd3aa88163950cdc8866c0e` |
| `StockWiki` — `tests/test_quick_scan_store.py` | `274c709126626c6c0cfa9ade43c0f71b6913a94b90d168203779131c4bc393b5` |
| `StockWiki` — `stockwiki/crosslink.py` | `483ec094cdba928c0afd40ccc11ff9b7b601e368e025ba8a9f887694391b07eb` |
| `company-wiki` — `src/company_wiki/source_catalog/security_identity.py` | `656cb235ceebbc6788342e80e74200d324d95e182481ca924aec9333c8f30eac` |
| `company-wiki` — `src/company_wiki/source_catalog/identity_cli.py` | `989cf4181f7c8b2084663058fcd84a526c5d03a577cc668983a49dd87d1572a2` |

## BASE-02 constraints and remaining work

- External repositories and CodeGraph are available. The StockWiki quick-scan files are newer untracked files missing from the current graph index; direct read-only inspection was used for those exact known paths.
- The only external execution attempt (`main_with_llm.py --help`) was blocked by logger file creation before reaching the CLI. This pass did not create or delete external files. No external repository tests were run or described as passed.
- No API keys, credentials, company documents, source PDFs, or full web-search bodies were read or copied into this report.
- Next dependency order remains: close current P00 v2 receipt; regenerate current v2 receipts for C01–C07; then run the G0 contract/release audit. Q02 remains partial until the latest source snapshot proves a completed real web search; Q04/Q08 and StockWiki observation/UI integration remain open.
