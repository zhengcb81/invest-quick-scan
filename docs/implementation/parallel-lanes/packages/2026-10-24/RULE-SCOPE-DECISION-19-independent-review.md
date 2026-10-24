# RULE-SCOPE-DECISION-19 — Independent Review

- Reviewer: independent reviewer (not the author, not the main controller)
- Date: 2026-10-24
- Design input: `docs/implementation/parallel-lanes/packages/2026-10-24/RULE-SCOPE-DECISION-19.md` (tracked; 9006 bytes; sha256 `bdbe2f7b…`)
- Implementation report under review: `RULE-SCOPE-DECISION-19-report.md`
- Method: read-only recomputation from disk in the four repos; targeted test runs; G6 CLI; a throwaway `publish()` probe in a temp root. No repository file was modified except this review file.
- All numbers below are from this reviewer's runs, not copied from the implementation report.

## 1. Gate table (G1–G6)

| Gate | Requirement | Verdict | Evidence |
|---|---|---|---|
| G1 | Card is the design input and is checked by the controller | **PASS** | Card exists and is tracked (added in `220fcbc`; latest docs touch `2f1e8e6`); the report cites it; §1/§2 card blockquote text is byte-identical to the landed catalog text (measured below). |
| G2 | No new ruling items; stop and ask the owner if new semantic questions appear | **PARTIAL** | No new semantic ruling on the two owner statements, but two items that require an owner decision were found/left open: the `publish()` contract blocker (report F1) and the v2-route default-diagnostics gap (report F8). Neither is closed. |
| G3 | TDD | **PASS (evidence-based)** | The two new tests and the four flipped test methods are present in `644ae58`; `tests/test_module_contract.py:182-186` still asserts the publish/upgrade rule; targeted main tests are green (129 passed, 185 subtests, exit 0). The red phase itself is only documented in handoff logs and was not independently re-run. |
| G4 | Independent review | **PASS** | This document. |
| G5 | Owner signoff | **OPEN** | No owner-signoff artifact was found in the main repo or in the three lab repos, and the implementation report does not claim G5. Owner action required. |
| G6 | Three-repo handoff + controller CLI `--verify-references` exit 0 | **PASS** | Final handoffs: UI exit 0, BANK exit 0, APPLIC exit 0 (ran from the main repo). All 13/38/34 declared artifact hashes match disk. See §5. |

## 2. Acceptance criteria (AC-01–AC-05)

| ID | Verdict | Measured result and justification |
|---|---|---|
| AC-01 | **PASS (with caveat)** | CATL `ENT_99ebb735-f072-41e4-8545-823bc012614f`, module `industrial`: state `unknown`, basis.kind `negative_evidence_not_verified`, source `auto` (not applicable). Alphabet `ENT_97bf6a65-a9e6-43f0-8409-c5695e2f6e1e`: same `unknown`. The corrected CATL manifest has modules `['common','operating','auto','mature','dupont','porter']` — `industrial` absent. Caveat: the demo is a hand-authored profile; no code-level applicability filter prevents a future profile/route from listing `industrial`, and the historical `thin-bank-catl-full-2026-10-22` run remains frozen with it (report F5). The AC's "corrected assembly" is satisfied for the delivered demo. |
| AC-02 | **PARTIAL** | Entity cells: CATL and Alphabet `dupont`/`porter` are `applicable`, basis.kind `common_always_applicable`, source `contract`, rule_ref `pred:dupont@pred_6b258097d0b8` / `pred:porter@pred_6b258097d0b8`. `select_questions` on a minimal operating/auto/mature profile returns `['common','operating','auto','mature','dupont','porter']` with 7+5 diagnostic questions and 24 core; explicit exclusion with rationale removes both; missing rationale raises. **But** `select_questions_for_route(['common','operating','auto','mature'])` returns no `dupont`/`porter`; `published_selection` uses that path for v2 route decisions. Default-in therefore holds for profile-driven compose only. The corrected demo includes both through the profile path. If AC-02 means all assembly paths, it is not fully met (documented boundary F8). |
| AC-03 | **PASS** | New snapshot `applicsnap_26f494e5e4faf19828c78e7ef10bcdbd563ff303f4f78b8006af8e97b94ee488`: 10272 cells; distribution `{applicable:1846, not_applicable:0, not_evaluated:0, unknown:8426}` (identical to old `applicsnap_d296…`); per-cell state changes = **0**; basis.kind changes = **428**, exactly `Counter({(dupont, owner_ruled_always_applicable → common_always_applicable): 214, (porter, …): 214})`; all 428 are `applicable` + `source=contract`; 642 cells total have `common_always_applicable` (214 common + 428 dupont/porter); 9844 non-changed cells differ only in `basis.rule_ref`; all 10272 `rule_ref`s moved to the new `pred_6b258097d0b8` prefix (report disclosed this). Card §4.B.2's "428 → 856" arithmetic is wrong; the implementation's F2 correction is the correct reading. |
| AC-04 | **PASS** | 9/9 byte-identical: industrial/dupont/porter `applies_when` in main catalog `3.2.1`, main module files, bank catalog `4.2.1`, bank module files, and applic `provenance.mapped_from`; industrial `name` = `工业装备与专用设备` in main catalog and bank catalog. SHA-256 of each text is identical across sources (industrial `2d293718…`, dupont `2c693e5d…`, porter `7d1735bd…`). Card blockquote text also matches each catalog field exactly. Bank catalog `content_sha256` matches each module file's raw bytes. |
| AC-05 | **PASS (scope noted)** | UI unittest: 122 tests run, 116 passed, 6 skipped, exit 0. Applic unittest at current HEAD: 323 passed, exit 0 (the handoff's 298 was the point-in-time count before the later LLM-JUDGE-20 commits; see finding R-08). Bank unittest: 52 passed, exit 0; `tools/validate_bank.py --releases` OK (`modules=62 questions=257 releases=OK`). Main targeted tests: 129 passed / 185 subtests / exit 0. Parity command vs UI `41be324ce898d94b4a55a342f7f55be797024996`: `state_consistent=true`, mismatch 0, `ui_repo_writes=0`, all four basis pairs are identity mappings (`common_always_applicable -> common_always_applicable`: 642; `negative_evidence_not_verified -> …`: 8409; `predicate_true -> …`: 1204; `attribute_unresolved -> …`: 17), `known_gaps[0]=closed`, `identity_verified=true`. UI `APPLICABILITY_BASES` covers all 4 basis kinds found in `demo/ui-export.json` (`no unknown value`). The main full 1038-test suite was not re-run (per the brief it takes ~45 min); the targeted 129 are the measured main-repo scope. |

## 3. Independent evidence

### 3.1 AC-04 text identity (all values recomputed)

| Field | Main catalog | Main module | Bank catalog | Bank module | Applic `mapped_from` | Card |
|---|---|---|---|---|---|---|
| industrial `applies_when` | same | same | same | same | same | same |
| dupont `applies_when` | same | same | same | same | same | same |
| porter `applies_when` | same | same | same | same | same | same |
| industrial `name` | `工业装备与专用设备` | same | same | same | n/a | text present |

- Main catalog version `3.2.1`; bank catalog version `4.2.1`; main module versions `3.0.1` for all three; bank module versions `industrial 3.1.0`, `dupont 4.2.0`, `porter 4.2.0`.
- Applic predicate table: `catalog_ref.catalog_version=3.2.1`, `catalog_ref.sha256=3e145130ffa1a6f9f19126c28a3cd521b72ef3eeefd8de368810e040e14f91d1`; current `questions/catalog.json` raw sha256 is exactly that; `predicate_version=pred_6b258097d0b88f12d8f08be8afba176e28391e14854023fd3e9076ae78e81511`; recomputed content hash equals that value.
- Predicate diff old→new is exactly 3 rules (`industrial`, `dupont`, `porter`); `industrial` predicate still `{"all":[{"field":"industry","op":"in","values":["industrial"]}]}`, decision `mapped`; `dupont`/`porter` decisions were already `contract_always` — only their `provenance.mapped_from` changed, plus the evaluator's basis mapping.

### 3.2 AC-03 snapshot recomputation

- File sha256 `2457dd1c8a4197fd7f7c99d9d6e0607ef48d0524180edf3eb192e24c4d4a0d68`; ID content-addressing verified: popping `snapshot_id` and re-hashing canonical bytes reproduces `applicsnap_26f494e5e4faf19828c78e7ef10bcdbd563ff303f4f78b8006af8e97b94ee488`.
- Old `applicsnap_d296…` file sha256 `edef5f9e…`; untouched in `e8fbfbf` (`git diff` empty); index old two entries preserved as an exact prefix and the new entry appended.
- Cell keys `(entity_id, module_id)`; 214 entities × 48 modules = 10272; no duplicate keys; key sets identical old/new.
- New basis kind population: `negative_evidence_not_verified 8409`, `predicate_true 1204`, `common_always_applicable 642`, `attribute_unresolved 17`.
- `demo/ui-export.json` cells match the snapshot on `(entity_id, module_id, state, basis.kind, rule_ref)` for all 10272 cells; `generated_from.snapshot_id` is the new ID.

### 3.3 AC-01/AC-02 entity cells and corrected composition

- CATL `industrial`: `state=unknown`, `basis.kind=negative_evidence_not_verified`, `source=auto`, reason `谓词判假但反证仅为 assumed：industry=[auto] 不满足 all(in[industry:industrial])`.
- Alphabet `industrial`: `unknown`, same basis kind, reason with `industry=[internet]`.
- CATL/Alphabet `dupont`/`porter`: `applicable`, `common_always_applicable`, `source=contract`, reason `…模块对所有公司恒适用（题库契约规定；所有者 2026-10-24 裁定纳入必做契约，不再依赖单次裁定记录）`.
- Corrected CATL manifest: 40 questions; modules `['common','operating','auto','mature','dupont','porter']`; 22 common + 7 dupont + 5 porter + 2 operating + 2 auto + 2 mature; `industrial` absent.
- Manifest provenance caveat: `module_package_id=pkg_24f07923…`, `module_release_id=modrel_18c097b2…`; dupont/porter locks are `3.0.0`, not the new `3.0.1` source. The manifest's porter prompts still contain `本题是按需追加的诊断题` (5/5) and no prompt contains `对所有公司适用` (0/12). This demo proves selection/default-in, not the new text end-to-end (see finding R-03).

### 3.4 AC-05 tests, parity, enum

- UI: `python -B -X utf8 -m unittest discover -s tests` → `Ran 122 tests`, `OK (skipped=6)`.
- Applic: same command → `Ran 323 tests`, `OK` (current HEAD `4c698da`; handoff commit `e8fbfbf` is ancestor, later `run_eval.py` changes are from LLM-JUDGE-20).
- Bank: same command → `Ran 52 tests`, `OK`; `python tools/validate_bank.py --releases` → `OK modules=62 questions=257 releases=OK`.
- Main targeted: `pytest tests/test_question_sets.py tests/test_module_registry.py tests/test_module_contract.py tests/test_applic_llm_probe.py -q --tb=line` → `129 passed, 185 subtests passed`, exit 0.
- Parity output (exact command in the brief) is `status=ok`, `state_consistent=true`, `state_mismatch_count=0`, `ui_repo_writes=0`, `ui_commit=ui_commit_expected=41be324…`, `known_gaps[0].closed_or_transitional=closed`, `identity_verified=true`.
- UI enum has 13 values, including `common_always_applicable` and the historical `owner_ruled_always_applicable`; all observed export kinds are covered. `adapters/applicability_resolver.py` blob is `6193da10599172e06e07ee5acb0e11fe039e48fd` at `40d7927^`, `40d7927`, `41be324`, and `HEAD` — byte-identical, as claimed.

## 4. Independent findings (including gaps/risks)

### R-01 (High, genuine open item) — real publish is still blocked by `validate_upgrade`

I copied the real `questions/` + `schemas/` tree to a temp root (outside all repos), then ran `module_registry.publish()` with the frozen `3.0.0` archive and the current `3.0.1` source. Result:

`ValueError: module applicability scope change requires successor IDs for all questions`

Individually, `module_contract.validate_upgrade(old 3.0.0 artifact, new source)` raises the same error for **industrial**, **dupont**, and **porter** (all have identical question ID sets; only `applies_when` changed). `publish()` fails before writing any new artifact. This is a genuine open release item: catalog `3.2.1` / module `3.0.1` text is not publishable under the current contract. The report discloses it as F1 and does not claim otherwise.

No test claims the opposite: `tests/test_module_contract.py:182-186` explicitly asserts the "successor IDs" rule, and the publish tests use fresh temp roots/history rather than the real 3.0.0 archive (`test_module_registry.py`, `test_c06_release_publish.py`), so the full suite can be green while the real publish remains blocked. Owner decision required (successor IDs / contract revision / accept release freeze).

### R-02 (Medium, AC-02 scope) — default-in does not cover the v2 route path

`select_questions` (profile-driven) adds `dupont`/`porter` by default, verified. `select_questions_for_route` — used by `published_selection` when a v2 route decision is supplied — does not add them; measured selected modules `['common','operating','auto','mature']` without diagnostics. Frozen routing policy still classifies both as `user_diagnostic`. The report documents this as F8. Literal AC-02 "组装默认包含" is therefore partial, not universal. Note: `progress.md:1` states "AC-01..05 全满足"; that blanket claim is not supported for AC-02 as written.

### R-03 (Medium) — corrected demo uses the frozen 3.0.0 package, not the new 3.0.1 text

The corrected CATL manifest is a valid demonstration that `industrial` was excluded and `dupont`/`porter` were selected, but it was composed from `pkg_24f07923…` with module locks `3.0.0`. Its 5 porter prompts still say `本题是按需追加的诊断题`; no prompt contains `对所有公司适用`. This is a direct consequence of R-01 (new text cannot be published). The demo lives under gitignored `runs/` (0 tracked files), so it is not reproducible from git alone; the package it uses is tracked, but the current pointer is dirty (R-07).

### R-04 (Medium) — UI's bundled catalog data is stale and contradicts the report's wording

`iqs-question-bank-ui-lab/src/generated/bank.json` still has `catalog.version = 3.2.0`, industrial name `工业制造、自动化与专业设备`, old industrial `applies_when`, and old dupont/porter `applies_when`. The UI reads this file at runtime (`src/app/store.js:42`, `src/app/ui/bank_overview.js` displays `bank.catalog.version`), so it will display the old catalog text until rebuilt. The report says "UI lab 不内嵌 catalog 文本" (F7); that wording is inaccurate — the generated data file embeds it. `scripts/build_data.py --check` only counted cells and passed; it does not detect the version/text drift. This is not one of the three AC-04 sources, but it is a product-level residual.

### R-05 (Medium) — bank 4.2.1 has an internal semantic/text contradiction and a version-policy override

Bank `catalog.json` entries for `dupont`/`porter` still carry `activation: "user_diagnostic…按需激活"` while their new `applies_when` says all companies must do them. The bank's `docs/version-policy.md` §3 says an `applies_when` change is **major** and requires retiring all old question IDs with successors; the bank instead kept module versions `4.2.0` for dupont/porter and catalog `4.2.1`, and `validate_bank` remains green because the machine check does not enforce that policy sentence. The report discloses this as a "裁定覆盖政策行文" tension; it still needs explicit owner signoff (G5) and, strictly, a version-policy exception.

### R-06 (Low, card errata) — card arithmetic and terminology

- Card §4.B.2 says applicable should rise from 428 to 856; measured applicable is 1846 both before and after, with 0 state changes. The report's F2 correction is right; the card text is wrong.
- AC-03 says the 428 cells' "basis 全部为 `contract_always`"; actual `basis.kind` is `common_always_applicable`, while `contract_always` is the predicate `decision` (it was already `contract_always` before this change). The implementation matches the intent and the task's expected `Counter`, but the wording should be corrected in the card/report.
- Card §2's "谓词由 owner_ruled… 改为 contract_always" is imprecise: old and new predicate decisions are both `contract_always`; the change is in `run_eval`'s basis mapping and `provenance.mapped_from`.

### R-07 (Low/Medium) — main worktree is dirty; active pointer is not HEAD

Main repo `git status --porcelain` has 1592 entries. The package's tracked paths (`questions/`, `scripts/question_*.py`, targeted tests, package docs) show no diffs, but `questions/releases/current.json` is modified to `pkg_24f07923…` while HEAD contains `pkg_b5a41d8c…`; `644ae58` did not touch it, so this predates the package commit (report F4), but I cannot prove it predates the review. The corrected demo uses the dirty pointer's package. Owner should reconcile/clean this before the next publish or release evidence.

### R-08 (Low) — stale test count in report/handoff

The report and applic handoff say 298 tests. At current HEAD (`4c698da`, later LLM-JUDGE-20 lane) I measured 323 tests, all green. The 298 figure is consistent with the handoff-time tree, not the current tree; the relevant `e8fbfbf` artifacts are ancestors and the snapshot is frozen, so AC-03 is unaffected. Report should label this as a point-in-time number.

### R-09 (Low) — G6 CLI validates shape/declared scope only

`parallel_handoff_cli.py` reports `validation_scope: handoff_shape_and_declared_scope_only`; it cannot authenticate claims. I compensated by recomputing all declared artifact hashes (0 mismatches) and checking commit ancestry, but the report's phrase "G6 主控 CLI" should not be read as full claim authentication.

## 5. Handoff integrity

### 5.1 Four CLI results

The package contains exactly three RULE-SCOPE-19 handoffs (UI, BANK, APPLIC). The fourth CLI result referenced by the brief is the documented BANK pre-fix failure; I did not rerun that historical failure, but I reran the final three.

| # | Handoff | CLI result | Notes |
|---|---|---|---|
| 1 | `iqs-question-bank-ui-lab/docs/handoff/RULE-SCOPE-19-UI/handoff.json` | **exit 0** (`status=valid`) | Ran from main repo with `--package-id RULE-SCOPE-19-UI --catalog docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json --verify-references`. |
| 2 | `iqs-question-bank-lab/docs/handoff/RULE-SCOPE-19-BANK/handoff.json`, pre-fix | **exit 2** (reported, not rerun) | Report §6.2: `temporary_root_not_cleaned`; fixed by `7af4119`/`96bbb4f`. |
| 3 | same BANK handoff, final | **exit 0** (`status=valid`) | Independent run; artifacts 38/38 match. |
| 4 | `iqs-applic-lab/docs/handoff/RULE-SCOPE-19-APPLIC/handoff.json` | **exit 0** (`status=valid`) | Independent run; artifacts 34/34 match. |

### 5.2 Artifact and commit checks

- Declared artifact hashes: UI 13/13 match raw bytes; BANK 38/38; APPLIC 34/34; 0 mismatches. This includes the new snapshot's sha256/bytes, predicates, `demo/ui-export.json`, and all handoff logs.
- Commits: UI result `40d7927`, handoff `41be324` (= current HEAD); BANK result `a1965fb`, handoff chain ends at `96bbb4f` (= current HEAD); APPLIC result `e8fbfbf`, handoff `2382aea` (ancestor), current HEAD `4c698da` (later LLM-JUDGE-20 commits).
- The handoffs' `changed_paths`/declared scope match the commit contents I inspected; the CLI's `--verify-references` exit 0 plus hash recomputation is the strongest offline check available.

### 5.3 Worktree cleanliness observed

- `iqs-applic-lab`: 0 dirty porcelain lines.
- `iqs-question-bank-ui-lab`: 0 dirty porcelain lines.
- `iqs-question-bank-lab`: 0 dirty porcelain lines.
- `invest-quick-scan`: 1592 dirty lines overall (pre-existing/other-lane artifacts), including `questions/releases/current.json` and many untracked `docs/implementation/intake/...` files. The RULE-SCOPE-19 tracked package paths are clean; before this review the only untracked file in the package directory was the pre-existing `RULE-SCOPE-DECISION-19-review.md` (not mine). After this review, `RULE-SCOPE-DECISION-19-independent-review.md` is also untracked. The corrected run directory is ignored by `runs/` and untracked.

## 6. Open items requiring the owner

1. **Real publish contract (R-01).** Choose one: successor question IDs, revise `module_contract.validate_upgrade`, or accept the release freeze. Until then, the new 3.0.1 texts exist only in authoring source, not in a runnable/published module package.
2. **Route-driven default diagnostics (R-02/F8).** Decide whether v2 route composition must also include `dupont`/`porter`; if yes, produce a new routing-policy artifact and router version.
3. **G5 owner signoff.** No signoff artifact exists.
4. **Bank version-policy exception (R-05).** `applies_when` changed while module versions stayed `4.2.0` and old question IDs were not retired/replaced; the bank's own policy calls for major + successor IDs. Also fix the `activation: 按需激活` mirror text.
5. **UI generated data rebuild (R-04).** Rebuild `src/generated/bank.json` so the UI displays catalog `3.2.1` and the new industrial/dupont/porter text; `build_data.py --check` alone does not catch this.
6. **Main worktree/pointer hygiene (R-07).** Confirm/clean `questions/releases/current.json` (`pkg_24f…` vs HEAD `pkg_b5a…`) before the next release action.
7. **Card errata (R-06).** Correct §4.B.2's 856 arithmetic and AC-03/§2's `contract_always` vs `basis.kind=common_always_applicable` terminology so the next reviewer does not re-litigate a card error.
8. **Demo reproducibility (R-03).** If the corrected CATL assembly is intended as auditable evidence, move it out of the gitignored `runs/` area or record its generating command/inputs; note that its prompts are still 3.0.0.

## 7. Commands and exit codes (selected)

- `python -B -X utf8 -m unittest discover -s tests` (UI) → 122 tests, OK, 6 skipped, exit 0.
- `python -B -X utf8 -m unittest discover -s tests` (applic) → 323 tests, OK, exit 0.
- `python -B -X utf8 -m unittest discover -s tests` (bank) → 52 tests, OK, exit 0.
- `python -B -X utf8 tools/validate_bank.py --releases` (bank) → `OK modules=62 questions=257 releases=OK`, exit 0.
- `python -B -X utf8 -m pytest tests/test_question_sets.py tests/test_module_registry.py tests/test_module_contract.py tests/test_applic_llm_probe.py -q --tb=line` (main) → 129 passed, 185 subtests, exit 0.
- `python -B -X utf8 scripts/parity_check.py --root . --ui-repo C:\Users\郑曾波\Projects\iqs-question-bank-ui-lab --ui-commit 41be324ce898d94b4a55a342f7f55be797024996 --snapshot data\snapshots\applicsnap_26f494e5e4faf19828c78e7ef10bcdbd563ff303f4f78b8006af8e97b94ee488.json` (applic) → `status=ok`, `state_consistent=true`, exit 0.
- `python -B -X utf8 scripts/parallel_handoff_cli.py --input <handoff> --package-id <RULE-SCOPE-19-UI|BANK|APPLIC> --catalog docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json --verify-references` (main) → exit 0 for each final handoff.
- Temp-root publish probe: `module_registry.publish()` → `ValueError: module applicability scope change requires successor IDs for all questions`; no repo was written. The temp root was outside all repos and was cleaned up.

## 8. Bottom line

Phases A/C, B, D, and E are substantially implemented and independently reproduced: the text is byte-identical in the three required sources, the 10272-cell snapshot has exactly the claimed 428 basis changes and zero state changes, parity vs UI `41be324` is clean, the four repos' relevant tests are green, and the three final G6 handoffs are exit 0 with matching artifact hashes.

The package is **not fully closed**: the real `publish()` path is blocked by its own upgrade contract (genuine open item, disclosed), AC-02's "default-in" does not cover v2-route assembly, and G5 owner signoff is absent. These are owner-level decisions, not silent test failures.
