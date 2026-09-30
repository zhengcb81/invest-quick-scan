# StockWiki W02/W03 first-segment validation — 2026-09-27

## Scope and result

This validation covers only the user-authorized eight StockWiki paths: `stockwiki/quick_scan_store.py`, `stockwiki/quick_scan_identity.py`, `stockwiki/quick_scan_universe.py`, `stockwiki/cli_parsers/quick_scan.py`, `stockwiki/cli_registry.py`, `tests/test_quick_scan_store.py`, `tests/test_quick_scan_identity.py`, and `tests/test_quick_scan_universe.py`. No W05, UI, company-wiki, or other StockWiki files were written.

The first W02/W03 segment is implemented and independently reviewed. The security-master importer records source candidates only; it does not merge securities into authoritative entities. Universe operations are versioned and append-only, reconciliation only adds missing members, soft capacity does not evict members, and restore-plus-pin commits atomically. Source URLs are stored as HTTPS origins only; paths, user information, queries, and fragments are removed. Candidate records whose URL required path removal receive the manual-review reason.

## Verification

- Isolated target suite with the real CN/HK/US security-master snapshots copied into a temporary directory: **59 passed, 1 skipped**. The skip is the optional classification-YAML test with no configured input. The snapshots were read-only; temporary databases, copies, and pytest files were removed automatically.
- After the final review fixes, URL-redaction and v1 migration success/rollback/concurrency regressions: **4 passed, 45 deselected**.
- `ruff check --no-cache` passed for all eight paths. `ruff format --check --no-cache` passed for the five new formatted source/test files. The existing large store test file was intentionally not reformatted wholesale. Scoped `git diff --check` passed; Git emitted only the existing LF/CRLF notice for `cli_registry.py`.
- The independent reviewer verified every hash below, closed both P2 findings (path credentials and non-frozen migration fixture), reran the four URL/migration regressions, and reported no remaining P0–P2 findings. The reviewer made no edits and used no network/API.
- No LLM/API call or company-document download was made. The company-wiki security master was read only.

## Final reviewed SHA-256

| File | SHA-256 |
|---|---|
| `stockwiki/quick_scan_store.py` | `54AC91D09CD7916876F311CBF61E488708751A1D3A71146913338FD95D8EA867` |
| `stockwiki/quick_scan_identity.py` | `C6985E03E193CDF6886C79B147A39787CCFD2A4F4063A1B518AB4E85621FF462` |
| `stockwiki/quick_scan_universe.py` | `10CC271B9C41A5AEC938F10DC6EF7FE40935AA4E5531B002E5773E648B58B165` |
| `stockwiki/cli_parsers/quick_scan.py` | `ACCD8B464A79D7B557FD099C80E976ED10A68C95D46DEF6A9CEBF9CFDEA255A5` |
| `stockwiki/cli_registry.py` | `74DA02DE903EB169C4E9D14C3EECB0A0C4AA534303C64DEBDC0473F80048ACA6` |
| `tests/test_quick_scan_store.py` | `A1566E21F8DEF67FEA098F76CF8156055E727070770C96002D4BC02B842B9A8B` |
| `tests/test_quick_scan_identity.py` | `EFB0297B9BECFCD6BFDBC83A2ECB282BBB35037DDF48C126933BC3ED44662BF9` |
| `tests/test_quick_scan_universe.py` | `D5FEA7721DE5F01197D0B280FB7282C61456155F975F6F3A7D8C81DE662F2BB2` |

## Remaining boundary

This result does not claim the 2,000-company universe is populated or scanned. W02 still needs an approved identity binding/promotion workflow and a transaction-owned authoritative projection. W03 still needs that projection connected to StockQA work items. W05 observation import/ACK, StockWiki UI, full scanning, and production-database migration remain open and outside this authorization.
