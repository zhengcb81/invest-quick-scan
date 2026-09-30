# Q01/Q03 r1 independent follow-up — 2026-09-24

**Decision: needs revision; do not mark the current Q01/Q03 snapshot verified.** The four original CLI counterexamples are fixed, but an existing supported consumer path regressed and duplicate-key rejection remains bypassable in legacy regex extraction mode. Q02/live status is not reassessed by this follow-up.

## Reviewed snapshot and scope

Owner HEAD remains `3c685dda28f67a00bd653ad257a121d3b8edebb8`. This is the working tree after separately authorized Q04 r4, not a clean checkout. All five hashes supplied for this review match the files read:

| File | SHA-256 |
|---|---|
| `src/providers/llm_response_parser.py` | `b0fa5b79604b0263d969d1827f4bdb507250527bc3a7d365b42cb87cf35699ff` |
| `tests/unit/test_llm_response_parser.py` | `005973486eb73060ee24b7c3d2a8656005adb293d708799cebb5e0eadddca07f` |
| `tests/integration/test_quick_scan_cli.py` | `939d91efcdfdd54a574c6001364b20d71d02c9e9ff37fd8f13833f8b9c337ad2` |
| `src/runners/llm_runner.py` | `579cde5a1fb21604e0a2bdca5667c880e45e78864602e2bd664f23a2dbedd2a4` |
| `src/services/answer_generator.py` | `b59840da063d00d7bcaab4ba960b88797f6466a4ead868ba0a7110e4d8fd44f4` |

Existing Q04 changes in configuration, provider policy, integration and runner files were retained and were not attributed to this remediation. The implementer's 272-pass suite and supplied red/green log hashes were treated as submitted evidence, not substituted for independent execution.

The unchanged r0 isolation runner was reused. Every execution used a new TEMP root, bytecode suppression, redirected logs/cache/XML, stripped provider credentials and audit guards against external writes/network calls. Only the existing narrowly scoped Python standard-library Windows asyncio self-pipe exception was allowed. No StockQA file was edited and no live API was called.

All three runs recorded **2,594 external filesystem entries and unchanged pre/post Git status**, with no added/removed/modified entry. The pre-existing unreadable `.pytest_cache` and device-like `nul` snapshot limitations from r0 still apply. No Q04 or user change was reset. TEMP-generated artifacts remain inventoried; raw captured logs and all review artifacts are in this directory.

## Independently executed results

| Run | Result | Meaning |
|---|---|---|
| `r1-selected` | **151 passed**, exit 0, no skips | Existing six owner test files plus the unchanged 13-case r0 independent CLI probes. Includes original 4 negative CLI cases, native 8/null, strict value boundaries, sync/async search paths, and current CLI Q04 regressions present in the selected file. |
| `r1-consumer` | **1 failed**, exit 1 | Previously passing S02 actual-CLI-to-consumer test fails early when the legitimate agreeing structured description is rejected. |
| `r1-followup` | **9 passed / 2 failed**, exit 1, no skips | Original four fixed cases each checked in strict mode and actual surrounding-text/Markdown regex mode; valid non-answer JSON prose accepted; two new counterexamples below fail. |

Exact command lines, cwd, exit codes and artifact hashes are in the corresponding `*-execution.json`; test selectors and complete failures are in stdout/JUnit. No test expectation was relaxed. The certifi HTTP-client suite was not rerun because neither that environment nor that source was changed by r1; its r0 limitation is not used to explain either current failure.

## Original finding dispositions

- **F01 fixed for its original trigger:** serialized inner insufficient-evidence/null with outer transport 5 is now unscored through the native public CLI. It is rejected, not converted into a native success.
- **F02 fixed for its original triggers:** inner/outer score conflict and wrong nested question ID are now unscored through the native public CLI.
- **F03 fixed for the original flat duplicate-key fixture, but still open for the regex extraction path described below.** Both direct and ordinary Markdown-wrapped flat duplicate fixtures reject correctly. The object-pairs hook is active, but does not make all rejected complete responses terminal.

## Open finding F04 — legitimate current IQS reply format is rejected

Severity: blocking integration regression. Tasks: Q01/Q03; dependent S02 path affected.

The new `_contains_unselected_nested_answer` check at `src/providers/llm_response_parser.py:188` rejects every complete description object having an ID, status and score, including an internally consistent, evidence-bearing 8-point response used by the current IQS legacy/screening protocol. No legacy protocol selector or coordinated consumer migration accompanies the change.

Two independent executions establish the impact:

1. The exact existing `tests/test_question_sets.py::QuestionSetTests::test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline` that passed in r0 now fails at line 727, because `parser().parse_response(json.dumps(raw))` returns `None` and cannot be unpacked. This occurs before the later CLI assertions; it is not attributed to the CLI without further evidence.
2. `test_r1_followup.py::test_valid_existing_structured_description_remains_compatible_through_cli` separately drives the real CLI with a valid outer native identity, `status=scored`, `score=8`, and an agreeing inner IQS_05/status/scored/8 description carrying evidence and the expected research fields. Only HTTP transport is stubbed. The actual CLI result is `unknown` with a null score, so its unchanged expected-8 assertion fails.

The test does not require accepting conflicting or unselected malformed payloads. It detects that the valid documented production/consumer shape was removed without a replacement path. A local negative-test-only pass cannot establish end-to-end compatibility.

Expected remediation: retain a clearly selected, validated legacy/screening adapter, **or** perform an explicit versioned migration of the request exporter, StockQA public entry, structured result and actual consumer together. Then rerun the unchanged legacy compatibility obligation or document an authorized replacement contract with equivalent identity/evidence/8/null checks. Do not change this existing positive test to expect rejection merely to match r1.

## F03 follow-up — regex promotes metadata after duplicate-key rejection

Severity: important acceptance failure; repeated/conflicting ID rejection incomplete in the shared parser's supported legacy mode. Location: `parse_structured_response` line 119 and `_try_extract_json_with_regex` lines 150–165.

Minimal valid-JSON input:

```json
{"question_id":"IQS_06","question_id":"IQS_05","score":8,"description":"ambiguous outer","metadata":{"question_id":"IQS_05","score":9,"description":"not the answer"}}
```

Call:

```python
LLMResponseParser().parse_structured_response(content, expected_question_id="IQS_05")
```

Expected: no adopted answer from an ambiguous response. Observed: the direct parser logs duplicate JSON keys, then regex extraction finds the nested `metadata` object and returns score **9**, description `not the answer`. The direct parse's semantic rejection is represented by the same `None` used for non-JSON surrounding text, so fallback continues and chooses a different object.

Reproduction: `test_r1_followup.py::test_r1_regex_must_not_promote_nested_object_from_duplicate_key_response`; unchanged expected `None` fails in `r1-followup-stdout.log`.

This does not claim a bypass of the public quick-scan CLI's `strict_json_only=True` path. It does demonstrate that the required shared-parser direct/regex duplicate-key protection is incomplete. Make an ambiguous complete JSON response terminal and ensure extraction considers the intended whole answer object, not arbitrary nested metadata. Preserve legitimate non-JSON wrapper compatibility without retrying semantic failures through a weaker parser.

## Handoff

Current native false-positive examples are closed, but the current snapshot remains `needs_revision` because the positive consumer path and regex ambiguity test fail. Retain all r0 and r1 evidence. A follow-up should rerun the selected suite, unchanged r0 CLI probes, the direct/regex probes, and the S02 positive consumer path against the new exact snapshot. This review does not re-approve Q04, authorize external edits, or provide live-search approval.
