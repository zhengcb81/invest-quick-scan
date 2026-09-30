# `contract_validation.py` trusted-field ownership audit

Status: local contract audit only. No StockWiki or StockQA implementation was written, and the synthetic test helpers below do not constitute producer evidence.

## Finding

No candidate field in `observation_identity_is_current` is proven to be a duplicate that can safely be removed. The fields form separate joins across identity-at-dispatch, current identity, durable work, one completed attempt, a search event, a StockWiki import acknowledgement, content validation, and the independently stored observation key. Several values repeat across those records by design so a mismatch is detectable. The local validator checks those equalities; it does not fetch the owner records or authenticate their provenance.

| Input / proof | Owner and distinct fact | Current binding in IQS | Removal decision / gap |
|---|---|---|---|
| `trusted_dispatch_identity_context` | StockWiki identity state and security/segment/source-binding projection used when work was authorized | `validate_work_item_v2` checks entity, state, revision, binding version, eligibility, scope and exact binding refs against the work snapshot | Keep. `_owner_context_v2` validates shape only; no producer-issued record reference or provenance hash is checked here. |
| `trusted_current_identity_context` | StockWiki's current entity/security/segment identity projection | Current score gate compares the observation's entity, security/segment scope, state, identity revision, binding version and refs to this projection | Keep. This is a different point-in-time owner view from dispatch; local code cannot prove the caller fetched it from StockWiki. |
| `persisted_work_item` | StockQA durable logical work, generation, response status, run/scan IDs and observation reference/hash | The gate requires delivered status and checks the envelope against the stored work snapshot | Keep. The embedded `observation_hash` binds the payload that StockQA accepted; the owner-store read itself is outside this repository. |
| `persisted_attempt` | StockQA's terminal attempt row, including status, work item, provider/model, request, timestamps and prompt hash | The attempt is matched field-by-field to `observation.execution`; a completed attempt for the same work is mandatory | Keep. Work-level attempt summaries are not the terminal attempt row and do not assert its completed state. |
| `trusted_search_receipt` | StockQA/provider-search execution record | Receipt ID, work ID, attempt ID, request ID and executed status must match the same attempt in the observation | Keep. It proves a distinct search event; its actual owner lookup and provenance hash are not available locally. |
| `trusted_ingest_receipt` | StockWiki transaction acknowledgement | Accepted ACK, StockWiki consumer, work ID, observation ID and accepted observation hash must all match | Keep. This records import/ACK, not answer correctness or search execution. No StockWiki producer golden is available to test its owner lookup. |
| `trusted_content_receipt` | StockWiki package/answer-content validation | Issuer, validated status, validation scope, schema version, observation ID/hash, module package and question ID are checked | Keep. It is separate from transaction ACK. Local tests can reject a wrong issuer/hash but cannot authenticate the record's origin. |
| `expected_observation_id` | Independent persisted observation key supplied by the storage owner | Must equal the envelope ID, which is recomputed from the canonical immutable body hash | Keep. Without an independently obtained key, a self-consistent forged envelope could validate itself. |
| Observation identity/source fields | Immutable historical snapshot claimed by the observation | Included in the observation hash and compared against dispatch work and current owner projection | Keep. Their repetition preserves history and enables current-vs-dispatch comparison; the observation's claim is never accepted alone. |

## Existing negative coverage retained

`tests/test_identity_bound_work_observation.py` covers wrong entity, security binding, identity revision, source-binding version/ref, invalid answer state/score, missing receipts, mismatched work/attempt/observation IDs, search event, import hash and content issuer/scope/schema/package/question. `tests/test_g0_regressions.py` preserves wrong-issuer and self-awarded check-level rejection; `tests/test_freshness_and_jobs_contract.py` preserves expired and inconsistent reporting-period rejection. The 2026-09-29 combined focused run passed 35 tests and 62 subtests after adding a matrix that mutates each persisted proof's issuer/state/hash/join fields.

## Hold for producer contract

The word `trusted` describes the caller's responsibility, not cryptographic verification performed by IQS. The local fixture `current_proofs()` constructs owner-shaped dictionaries in memory. To close the provenance gap, the owning systems must publish a versioned DTO/record contract with stable owner record IDs and source/revision/hash semantics, and the integration test must read that DTO through each owner's public interface. Do not remove or synthesize those fields before StockWiki and StockQA owners supply that evidence. This is separate from the local deployment request change; no cross-repository write or fake positive producer golden was made.
