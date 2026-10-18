# Delivery equivalence and evidence timing addendum

The exact eight delivered paths in StockQA commit `4d77ffb4e73232ef93b082900a74a731bdb256ba` are mechanically equivalent to reviewed CAS `02726d6c…`. This addendum preserves historical `final.json` SHA `1b69e5b5…` unchanged.

All four product ASTs are identical after removing only the new private `_claim_pending_in_transaction -> Optional[Lease]` return annotation. That annotation fixes ordinary mypy's Any-return complaint; its body and the existing singleton transition are unchanged. The remaining delivery differences are Black whitespace/CRLF and isort order in tests. Eight working-file hashes, commit blob IDs/SHA256s, exact changed paths, full normalized AST comparisons and in-memory compilation are recorded in `delivery-addendum.json`.

Ordinary source-path tests passed48 with1 explicitly gated heavy test skipped (8.70s). The third normal commit attempt passed all applicable hooks, including Black, isort, mypy and secrets detection; the first two failed hook logs remain. The original607s public path was not unnecessarily repeated.

Evidence timing correction: `executed-test-source-before-format.json` was captured after c01 completed and immediately before Black, not before c01 launched. During c01 the author also added a pytest collection-only environment skip decorator to the historical continuation test and added its explicit opt-in field to SAFE_ENV. The AST equivalence record therefore establishes final Black versus immediate pre-Black test semantics, not a complete prelaunch byte lock of the c01 harness. Earlier `final.json`/`final.md` wording implying c01 executed those explicitly recorded full test bytes is superseded by this clarification. The four actual product bytes remained frozen; original owner/SDK/OS-exit86/zero-POST recovery observations and the independently read-only-verified database remain the engineering evidence.

`open_findings=[]` for this delivery scope. Overall speedup, actual financial accuracy and price/billing qualification remain ungranted; the original real sample remains failed/not_assessed.
