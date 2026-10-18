# Independent publication review — changes requested

Reviewer: `/root/cards_review18`; author: `/root/new_packages18`. Scope: seven draft files in `2026-10-18-mainline-support`, all 63 frozen input entries and relevant earlier package boundaries. No source scripts, network, API or external writes.

Actual checks: all 63 Git blob OID/bytes/raw SHA values match d788a10; all 12 relative links exist; all 3 assigned new Lab roots are absent. Three real release module sets are identical (48 each); all module artifact references are in the catalog.

## Findings

### MS10-R1-F01 (high) — Release-level router/policy changes are invisible and required policy files are missing
Target: `RELEASE-DIFF-10.md`, input/API/output + input-catalog RELEASE-DIFF-10.

All three frozen real releases have exactly the same 48 module entries. modrel_18c... uses schema1/router1; modrel_e123... uses schema2/router2.0/policy0c834...; modrel_8f5... uses schema2/router2.1/policyeef827.... Public payload defines module/question/format changes but no release metadata changes. The two routing_policy_ref files are absent from the assigned catalog.

An implementation can meet the written payload contract while returning all modules/questions unchanged for both real version2 releases, omitting the only actual semantic version difference; it cannot inspect the referenced policies under its valid lock.

Fix: Add explicit versioned release-level field changes for schema/catalog/renderer/router, retirement lists and routing policy reference/hash. Include the two exact policy blobs (and any needed schema) in the assigned lock, or explicitly define locked unresolved policy handling without claiming no policy change. Require actual three-release regression to surface these changes. Preserve candidate/no routing authority boundary.

### MS10-R1-F02 (high) — Snapshot can silently omit or duplicate original answer items
Target: `RELATION-DELTA-10.md`, snapshot item_refs / counts.

item_refs is only described as pointers to answer.items elements. There is no explicit requirement to cover every original element exactly once, no rejection rule for two different item_ids pointing to the same original element, and no rule tying before_total/after_total to answer.items length.

A conforming harness may drop a customer from item_refs or duplicate its pointer and still satisfy its own reported count conservation, hiding unobserved relationships or inflating candidates.

Fix: Make item_refs an exact one-to-one cover of original answer.items (or define an explicit selection scope/denominator contract; the simplest is full cover). Reject missing/duplicate pointers, item IDs/hash mismatch and answer.question_id versus question_ref mismatch; derive totals from validated original arrays. Require omitted-item and duplicate-pointer CLI counterexamples plus normal permutation case.

### MS10-R1-F03 (medium) — unresolved identity confidence is not a matching exclusion
Target: `RELATION-DELTA-10.md`, identity_scope / exact matching key.

identity_scope permits confidence=explicit|unresolved; matching rules only send entity_id=null to unresolved. Thus a non-null caller ID with confidence=unresolved satisfies the written matching key and can be paired.

The tool advertises exact explicit identity matching yet can generate matched relationship-change candidates from explicitly unresolved identity.

Fix: Require explicit confidence and a non-null consistent ID for pairing; any unresolved confidence must produce unresolved with a fixed reason regardless of ID presence. Document when business_unit_ref is sufficiently explicit. Add same ID/unresolved and explicit positive counterpart cases.

### MS10-R1-F04 (medium) — Requested cutoff and competing status outcomes are undefined
Target: `RELATION-DELTA-10.md`, request as_of_date / payload status.

as_of_date is required by the request but the card assigns no validation or eligibility semantics to it. status has cutoff_not_ordered, scope_mismatch and method_changed but no definition of method_changed or precedence when several failures hold.

Two independent weaker harnesses can produce different valid outcomes for future snapshot cutoffs or simultaneous scope/question/time changes; consumers cannot rely on a stable versioned interface.

Fix: Define request cutoff relationship to both information_as_of fields (keep observed_at retrospective collection semantics explicit), define method_changed from listed fields, and set deterministic rejection/status precedence with full item conservation and reason codes. Add future information cutoff, equal/reversed dates, definition change and multiple-failure fixtures.

## Positive review results

- Three unique new write roots are absent and independent. All source inputs are explicit committed Git blobs; no missing dispatch lock because all tasks are strictly offline.
- Expected fixtures/catalog segregated from business inputs; public diagnostics prohibit expected lookup.
- Independent real reviewer identity, two unseen counterexamples, normal non-overblocking case, full review/fix/re-review and final payload binding are required.
- Meaningful unit/integration/CLI E2E, minimal process environment, no network, self-created temp ownership/finally cleanup are specified.
- Compared nearby CONTEXT-PACK-06, ANSWER-CODEC-03, CHAIN-VERIFY-04 and SW-READY-01 responsibilities: no conflicting write root or identical task scope; summary diagnostics intentionally do not regenerate production summaries or semantic entailment.

Verdict: `changes_requested`. The author must fix all four findings and request the same reviewer closure. No published status set by this reviewer.
