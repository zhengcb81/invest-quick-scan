# S06/MOD-18 independent implementation review

Date: 2026-09-27

Decision: `approved-for-local-snapshot` for the MOD-18 dependency-closure scope; no actionable P0–P2 findings within that scope.

## Reviewed scope

Read-only review of the S06 dependency-closure implementation, route status and schema, routing contract text, and MOD-18 regression tests. The review checked recursive dependency completion, deterministic ordering, missing/rejected/uncertain/cyclic dependencies, undirected conflicts, coexistence of unselected alternatives, and fail-closed behavior before composition writes a payload.

## Findings

- Dependencies are traversed recursively and deduplicated; output order is deterministic by dependency topology and stable kind/module keys.
- Missing, unselected, rejected, uncertain, malformed, and cyclic dependency conditions become route issues. Route snapshot validation recomputes them and requires `needs_review` with an empty eligible-module list.
- Conflicts are treated as undirected and checked only among selected modules, so mutually exclusive alternatives may remain in the catalog until both are selected.
- The execution validator and public composition path reject `needs_review` before writing question output. The schema permits the review state and an empty eligible list; the routing reference describes the same behavior.
- No P0, P1, or P2 issue found.

## Reviewed source snapshot

| Path | SHA-256 |
|---|---|
| `scripts/routing.py` | `f0535edbf5c92b9101c7af144d90c005550c7469677206c57ba71d47418e1912` |
| `schemas/quick_scan/route-decision.schema.json` | `d52c831cc2426a1dec2a31ad27b6a12161eeeda34d95d62c238d3bc9e51ea734` |
| `references/routing.md` | `12bddd9cbcb896d5f3c268fdc0488055008d6dfef18a5f3c8381ab632108784a` |
| `tests/test_s06_dependency_closure.py` | `e101d0dda3a1fe7b4cafa1536b5abe21ed8c4a6127841616ff97500c2b0446bf` |

## Limits

This review covers local implementation only. It did not run tests or verify production StockQA search, StockWiki identity/refresh, or cross-project dispatch behavior.

## Scope clarification

This MOD-18 review covered dependency closure, route-state recomputation, conflict handling, and fail-closed composition. It was not a full review of ROUTE_02 response semantics. A later full-S06 snapshot review identified a separate P2 outside the MOD-18 checks: the native overall classification `score` is validated by `parse_route_response` but discarded when only the inner candidate envelope is returned (`scripts/routing.py:266-310`); it is neither retained in the route snapshot nor reconciled with per-module confidence. That finding does not change the MOD-18 result above. The broader review supplies the counterexample and full-snapshot hashes.
