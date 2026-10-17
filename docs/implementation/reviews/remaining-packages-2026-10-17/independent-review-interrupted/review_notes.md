# Independent final package review

Reviewer: /root/remaining_package_final_review (not an implementer or repair author).

Scope initially QUERY-ENTITY-07 db3d3f10e4763a8b6be9b04c3c6dad5328bfdbdb,
SOURCE-TIME-07 f7b28d6561bd03e37325f2e8b97615f6b29810ba,
RESUME-CHAOS-06 ab8388fc156e4fe342c8ca3e34ba6dbb6267c5ab.
REVIEW-CAL-06 and RETRIEVAL-AUDIT-07 final revisions are pending delivery.

Read-only source inspection. No source tests executed, no keys read, no model or
search calls. CodeGraph lookup for RESUME returned not initialized; review uses
the exact known files supplied in the task and their literal references.

## Independent findings

1. QE-FINAL-01 (P2): `_read_lock_bytes` omitted ancestor-link checking even
   though normal input reads rejected it. A real Windows junction with the
   valid known lock/hash returned success. Root added the existing common
   path guard; independent repeat is ordinary 0 / junction 3, no traceback.
   `query-probes.json` and `query-green.json` retain actual invocations/results.
   Both junctions were removed with checked link-only `rmdir`.
2. ST-FINAL-01 (P2): ST07-REAL-012 universally claims all frozen H-share code
   records agree on 03750; one excerpt expressly says 0750.HK. The current
   partial label conflicts with this package's published evidence definitions:
   a direct counterexample refutes consistency; it is not merely uncovered
   evidence. Preserve both records and their unresolved actual identity, change
   only candidate label/rationale and derived reports/generator, with regression.
   Root accepted the issue and is preparing that correction.
   Same semantic review also identifies REAL007: neither bound excerpt carries
   the million-unit header, yet the claim says 13,910 million USD and the
   rationale says units match. Currency and FY metadata cannot supply scale;
   author-written `supports` is not independent evidence for its own unit.
   Keep exact excerpts and downgrade to partial / named missing unit unless a
   genuinely bound frozen header is supplied. This matches the project search
   handbook's existing missing-unit rule.
3. RC-FINAL-01 (P2): signed/self-hashed RESUME reports with negative
   `observed.store_counts.attempts_total` and negative `by_status` counts pass
   `summarize` and change its substantive refusal total; by_status=array raises
   AttributeError. The binder validates only three other top-level counters.
   `resume-summary-probes.json` shows baseline 28 cases / 20 synthetic HTTP
   and malformed result; root preparing typed count validation.
   `resume-casebook-probes.json` further proves declared case_count=999 or a
   case input_versions.codec=9.9.9 / all-zero input-lock is marked valid while
   actual verified context remains unchanged. Bind per-case declarations to the
   frozen version contract and actual case count; these are metadata validity
   failures, not evidence that consumer-byte hashing was bypassed.

## Substantive read coverage so far

Read all 35 SOURCE original claim/rationale/status/excerpts and publication
metadata, the definitions and current structural validator/coverage logic.
The repaired strict-before (SYN009) and carrier-role (SYN013) distinctions are
sound. Labels remain authored candidate judgments, not externally certified
financial gold; original excerpts/identity declarations are preserved.

Read QUERY strict JSON / canonical normalization / authority, listing and alias
validity / planner / lock derivation / all-input and output guards. The planner
keeps unresolved relationships and user order, explicitly lacks date filtering,
does not merge same-name/ticker entities or claim actual search quality.

Read RESUME CLI, bootstrap, manifest, worker guards and lifecycle, run API,
summary binding/classification and added regressions. Consumer verification is
now before frozen code import on the main and `-I` worker paths; per-worker
owned writes, network restrictions and owned-PID timeout reaping are wired into
actual invocation. The four original unsupported precise SDK windows remain
honestly listed; 28 synthetic cases and 20 mocked calls do not imply real API,
production reliability or financial qualification.

No final pass asserted until these findings are closed, two remaining packages
are delivered, and actual final payload commits / documentation hashes bound.

## Candidate closure evidence

QUERY final followup supplied by coordinator:
dd1f5f1fc26b1296fad98fd843cff0587fc6c700. Real-junction GREEN retained.
SOURCE final followup: e8a31c22aa9e6d19978172e1bf639b3b03a63e20.
Independent JSON re-hashing and full two-case reread verifies 59 excerpts and
provenance unchanged, 35 claims unchanged, only REAL007/REAL012 judgments and
authored explanations corrected; coverage 7/5/14/9 and all qualifications false.
RESUME followup: f76bb65e089cfb1d64af6606704dea1c390e0327. 13 independent
GREEN cases plus 3 further root-field GREEN checks reject malformed state as
typed errors while preserving the original legitimate 28-case/20-mock summary.
The root's latest 85-case full execution preceded its final tiny root-field
patch; 12 affected tests reran afterward. Do not claim 85 ran on final bytes.

## RETRIEVAL review in progress

Read candidate assignment generation, binding/context and label filtering,
annotation derivation/coverage/conflicts, private-map and A/B comparison,
schemas/JSON/path handling, CLI and new 13 tests. Independently read all 28
synthetic cases (20 substantive baselines, 8 paired variants / 8 complete pair
groups) and their authored expectations; no actual accuracy is claimed.

Independent RED (`retrieval-probes.json`) finds two P2 issues sent directly to
the repair author: complete zero-source A/B annotations incorrectly become a
pending checkpoint, and finite-JSON failure handling misses exponent overflow
and very long integer ValueError. Repairs pending.

Two more substantive RETRIEVAL issues were confirmed in the same whole-package
review (not separate review gates): `retrieval-url-red.json` demonstrates whole
URL lowercasing merges distinct case-sensitive paths, corrupting duplicate
counts; both duplicate counting and same-origin guards need the same safe key.
The rd09 calibration incorrectly treats a different numerical answer to an open
information need as contradicted. The author confirms the rubric does not allow
assuming primary=truth. The coordinator requires preserving legacy raw fixture
compatibility while actually excluding the known disputed entries from new
post-hoc calibration denominators with structured private errata, not merely a
guide disclaimer. Generic public instructions must not leak case IDs/expected
answers; A/B agreement remains separate from correctness. Repairs pending.
