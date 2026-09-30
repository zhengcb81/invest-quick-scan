# S01/C06 reviewed-fix validation — 2026-09-27

This log records the review-driven legacy replacement-map hardening in S01 and
the exchange `extensions` wire-shape correction in C06. It does not claim a
production LLM call, external-store integration, or release acceptance.

## Changes under test

- S01 now verifies a legacy replacement map against the exact current catalog,
  profile, deterministic route, selected modules, question IDs, and canonical
  `replaces` metadata before using it for recovery-watch mapping. A missing or
  retired catalog version remains readable, but its recovery mapping is flagged
  `replacement_mapping_unverified` and cannot drive a positive recovery status.
- The frozen no-version legacy-read test explicitly removes `template_version`,
  so compatibility continues to assert the actual historical input shape and
  the normalized output still reports `template_version: unknown`.
- C06 now states that `extensions` is the empty JSON array `[]`, matching the
  schema, reference builder, and exchange fixture. The contract test asserts the
  documented wire shape and fixture value.

## Isolated test evidence

Environment: repository-local test inputs; unique directory under system TEMP
for pytest/TEMP/TMP output; `PYTHONDONTWRITEBYTECODE=1`; pytest base_url and cache
plugins disabled; warnings treated as errors; no API keys, network, or document
downloads used.

Full affected batch command:

```text
python -B -X utf8 -m pytest -p no:base_url -p no:cacheprovider --basetemp <isolated-temp>/pytest -W error tests/test_question_sets.py tests/test_exchange_and_query_contract.py tests/test_g0_regressions.py -q
```

The first batch produced **86 passed, 1 failed, 175 subtests passed**. The sole
failure was the no-version legacy-read test retaining a `template_version` that
the test helper had just been updated to supply; the production code correctly
preserved that field. The fixture was corrected to remove the field only for
that historical test. The exact two affected S01 selectors were then rerun:

```text
tests/test_question_sets.py::QuestionSetTests::test_s01_legacy_manifest_remains_readable_without_new_mapping
tests/test_question_sets.py::QuestionSetTests::test_s01_legacy_recovery_watch_flags_unverified_replacement_mapping
```

Result: **2 passed, 4 subtests passed**. This includes the coordinated rewrite
attack, one-sided drift, missing question metadata, unavailable historical
catalog, and unchanged legacy normalized output. The C06 package/docs regression
passed in the affected batch and in the initial focused run (alongside the S01
attack test).
The only post-batch test-file edit was the one-case legacy fixture correction;
all other selectors and implementation code were unchanged. The random TEMP
roots were removed; a follow-up glob found no leftover full-batch root.

Afterward, all current S01/C06 receipt-bound selectors were run together in a
fresh isolated batch: **10 passed, 6 subtests passed, zero skips**, including
MATRIX-07, SC-08/10/11, C06 contract cases 01/02/03, and both legacy recovery
regressions. Cleanup was verified. The exact command/output is recorded in
`validation-S01-C06-current-followup-2026-09-27.log`.

## Review snapshot hashes

S01:

- `scripts/question_sets.py`: `602480AC453150CE5C4C8529E2C081250405AC915FD9F47CD1AFB4099D36FA47`
- `tests/test_question_sets.py`: `A90616A15B770EF1E936D1C87AF5ED8857891FACD33A9CAE18DEE21C052CA2DC`
- `questions/catalog.json`: `252DAB9E3F71868A71147ECB7DAC64CC187D7D56002B28B266A74F406FACAF10`

C06:

- `docs/implementation/contracts/exchange-and-query.md`: `BF02331088B8F3EF2F283CE6E5B68286558432D2FE29F8CEE2A1065416B70E96`
- `tests/test_exchange_and_query_contract.py`: `052F07906D80527C083D40F3F090801D4666F6660A72D77B8668FED439DEEB04`
- `schemas/quick_scan/exchange.schema.json`: `EFDF0E3427D1BBB73892E9573FBF3B1F0389218E3F5A0C8DFF4CA0CD63764122`
- `schemas/quick_scan/query.schema.json`: `E7FC264B43D85E4CDD5C82A71B9FEDB579DD0FC1196F3C5FDE661F14FA1756F8`
- `scripts/exchange_contract.py`: `BE08F84055DBB72AD5205EA31BD9AC17106B523F4CC5AE17A315171A570592F7`
- `tests/test_g0_regressions.py`: `69291A1EFEC99D14A3381AA20D5E454F10EF8E310F1063505F06C2B2721A3B64`

## Other checks and limitations

- `python -B -X utf8 scripts/implementation_plan.py validate`: passed
  (`planning_valid=true`, 103 tasks, 328 cases, G6).
- `git diff --check` for the four edited implementation/test/contract files:
  passed.
- Ruff and Black checks are not clean on the full affected files: Ruff reports
  existing unused/import-order/semicolon diagnostics outside the added logic;
  Black reports pre-existing formatting differences in those files. No broad
  reformat or unrelated cleanup was applied.
- Independent current-snapshot follow-up review is pending. The earlier
  `needs_revision` reports refer to the pre-fix snapshot and are not approval of
  this version.
