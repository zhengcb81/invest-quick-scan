# P00 current interface and behavior baseline

**As of:** 2026-09-29 (read-only repository snapshot)  
**Task:** P00 / BASE-01 and BASE-02  
**Owner:** `invest-quick-scan`  
**Scope:** Local quick-scan contracts and read-only inspection of StockQAbyLLM, StockWiki, and company-wiki. This is an interface and offline-regression baseline, not a live-search, company-quality, or production-coverage acceptance.

## Result and boundaries

The current P00 rerun confirms the immutable 2026-09-22 baseline artifacts still match P01's context manifest. The current local question bank validates at 48 modules and 222 scored questions; the fact-question library validates without network access. A local integration test runs the actual StockQA CLI path against an in-memory HTTP fixture and verifies exact score pass-through at 8/10. A separate parser check confirms an explicit `unknown` response retains a null score. These are offline contract checks, not proof that a live provider completed web search.

All external repositories were read-only. I did not run their test suites, refresh a company-wiki security master, download company material, submit an API request, or alter an external file. No real company was used: the CLI fixture represents a fictional industrial-equipment issuer. The original 2026-09-22 report and legacy P00 receipt remain unchanged and hash-locked.

## Repository and index snapshots

`HEAD` does not identify uncommitted source, so representative file hashes are recorded in `validation-P00-BASE02-T01-2026-09-29.log`. Git status was collected with `--no-optional-locks`; for the three external worktrees, `safe.directory` was supplied only to that invocation. No Git configuration was changed. Dirty changes predate or are unrelated to this baseline and are not attributed to P00.

| Repository | HEAD | Tracked changed | Untracked entries | CodeGraph |
|---|---|---:|---:|---|
| `invest-quick-scan` | `25b8d14316c06390450e5a1d8883583bfd039d0d` | 47 | 444 | healthy; 53 files, 1,660 nodes, 3,540 edges |
| `StockQAbyLLM` | `3c685dda28f67a00bd653ad257a121d3b8edebb8` | 28 | 27 | healthy; 111 files, 2,322 nodes, 5,817 edges |
| `StockWiki` | `f5b8526c78ef0bc7df27885da043ce5a2534fffb` | 1 | 3 | healthy; 262 files, 4,490 nodes, 6,922 edges |
| `company-wiki` | `25aa51b104a90ace5ca05191ed3190f9d35b813a` | 50 | 3 | healthy; 627 files, 13,033 nodes, 24,954 edges |

StockQAbyLLM has no root `AGENTS.md`. StockWiki's root instructions require real-workspace acceptance and `bash scripts/check_all.sh` before commit; company-wiki's instructions make it the upstream source/document system and prohibit writing StockWiki research state. Those full external checks were not appropriate for this read-only P00 pass. The current StockWiki quick-scan store and test files are untracked and absent from CodeGraph; after checking the index, I read only their already-known paths directly.

## Current component boundaries

### Questions, scoring, and model execution

- The current scoring catalog is 48 modules / 222 questions. Its validator identifies package `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f` and release `modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9`.
- The fact-question library passes `validate-library` with `network_used=false`. The command does not emit a question count, so this report does not infer one.
- `LLMResponseParser` accepts `scored` only with a strict integer from 1 to 10; a non-scored status such as `unknown` requires `score=null`. `AnswerGenerator` carries the parsed score/status through and rejects conflicting question IDs or duplicated outer/inner score claims.
- StockQAbyLLM's quick-scan runner (`LLMRunner._run_single_company`) constructs `OrderedSearchProviderCascade` from the configured, ordered routes and passes it into the QA engine. That quick-scan cascade is distinct from the legacy stateful `ProviderCascade` class in the same module: the latter tracks a global current-provider index, and CodeGraph found no callers for it. The quick-scan cascade is per-question; only explicit classified provider failures permit a later route, while a valid low score, `unknown`, or insufficient-evidence response ends that question's dispatch. Do not infer quick-scan fallback semantics from the legacy helper.
- A selected quick-scan provider calls `LLMClient.send_search_request`, which chooses an allowlisted Responses `web_search` route, checks successful completion, parses protocol search evidence, and records an execution receipt. The older generic `src/services/search_service.py` still documents itself as a simulated placeholder and must not be mistaken for live search.
- The executed CLI test uses an in-memory session whose fixture returns a completed search-call shape; it proves local contract wiring only. No search endpoint was contacted. Q02's live-search acceptance remains separate and unproven by this baseline.

### Identity, persistence, and cross-project roles

- StockWiki's `QuickScanStore` schema v1 owns a separate lightweight SQLite area for quick-scan issuer/security/source-binding identity, segments, universes, memberships, and membership history. It does not yet provide the complete scored-observation timeline, model comparison projections, or finished quick-scan UI. This database is not a copy of company documents or the formal StockWiki research ledger.
- company-wiki owns upstream source discovery, immutable raw documents, extraction/evidence locations, and read-only versioned security-master exports. `SecurityIdentityResolver` resolves candidates with market/exchange context. No `--refresh` or other write-capable command was run.
- Cross-project exchange must use explicit versioned IDs/exports; this baseline did not copy sources, PDFs, snippets, or mutable databases between repositories.

## Historical behavior versus current checks

The preserved 2026-09-22 baseline described an earlier `AnswerGenerator` fallback that could turn missing scores into 5, and a historical test that accepted 5 or 8. That is historical evidence, not current behavior. The current local integration selector asserts score 8 exactly through parser, provider fixture, CLI, and normalization. The explicit parser probe asserts `status="unknown"` and `score is None`. No default score is manufactured by either current check.

P01's immutable context manifest still matches both original inputs:

| Preserved artifact | SHA-256 | Result |
|---|---|---|
| `docs/implementation/baselines/baseline-report-2026-09-22.md` | `029363860a08213910e37fcb6d335e97c6b911684c02d4df953a1e41fc0f3c0c` | match |
| `docs/implementation/baselines/receipt-P00.json` (legacy) | `0d7cccbab76842ac7bd45e94e23242da88ff18a0c34b0910a310842ce0ee5983` | match |

The legacy receipt remains historical only. Current P00 v2 evidence is kept at `docs/implementation/contracts/receipt-P00.json` with its own detached validation sidecar.

## Checks performed

| Check | Result | Evidence |
|---|---|---|
| P01 context manifest vs preserved report and legacy receipt | Both hashes match; no write/network | `validation-P00-BASE01-T01-2026-09-29.log` |
| Current StockQA CLI integration, exact scored value | 1 test passed; all fixture-scored questions normalize to 8 | `validation-P00-BASE01-T02-2026-09-29.log` |
| Current parser unknown/null behavior | Explicit structured response remains `unknown` / `null` | same isolated log |
| Question catalog validation | 48 modules / 222 questions; package and release IDs recorded | `validation-P00-scoring-bank-2026-09-29.log` |
| Fact question library validation | `ok=true`, `network_used=false` | `validation-P00-fact-bank-2026-09-29.log` |
| Repository, source-hash, and CodeGraph snapshot | Read-only snapshot recorded; no external test suite run | `validation-P00-BASE02-T01-2026-09-29.log` |
| Implementation plan validation | valid; 108 tasks / 365 acceptance cases / G6 | `validation-P00-BASE02-T02-2026-09-29.log` |

The isolated CLI check directs temporary output to a dedicated temporary root, checks that the StockQA worktree status and representative source hashes are unchanged, and removes the entire temporary root (including the logger's temporary `logs` directory). The test's own fixture verifies no StockQA bytecode changed. No skipped tests were counted as passes. There were zero live network requests and zero API fees.

## Remaining limits and dependency order

This baseline does not establish live web-search execution, answer correctness on real issuers, production storage of observations, UI completeness, or the 2,000-company universe. Those remain later implementation and acceptance work. External repositories were deliberately not tested because this task has read-only authority there and StockWiki's own gate requires a full real-workspace suite before commit; neither condition is replaced by a claimed pass here.

P01 has a current v2 receipt, an eligible detached sidecar, and a separate approved post-seal evidence review. After P00 is independently reviewed and sealed, the next receipt sequence is to refresh C01–C07 against the current task/case contracts, then pass G0 before any W01 work that depends on those gates.
