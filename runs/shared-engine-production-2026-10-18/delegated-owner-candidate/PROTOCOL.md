# Delegated owner contract 1.0

This is a first-party local owner capability, not a way to assert that an agent is a human. The authority boundary remains the original OS owner account and StockWiki control namespace. Hashes bind content; they do not authenticate an agent. The current user authorization is not treated as an already-installed application grant.

## Versions and compatibility

| Path | Existing behavior | Additive delegated behavior |
|---|---|---|
| Confirmation ID | rc1_ + 64 lowercase hex | rc2_ + 64 lowercase hex |
| Immutable confirmation | stockwiki.refresh_confirmation_record/1.0.0 | stockwiki.refresh_confirmation_record/2.0.0 |
| Confirmation method | native_owner_terminal | native_owner_delegated_agent |
| Native inspection | stockwiki.refresh_approval_inspection/1.1.0 | stockwiki.refresh_approval_inspection/1.2.0 |
| Request/owner policy | Existing 1.0–1.3 | Unchanged; no silent request dialect upgrade |

Original TTY confirmer, rc1 record class/key/hash/bytes, current OS principal implementation and work-decision confirmer remain unchanged. Existing clients reject unknown rc2. Upgrading either repository alone fails closed; both native producer and original consumer must support the new protocol. Inspection has the original exact top-level WIRE_FIELDS; the versioned delegated record carries its own grant. No consumer confirmed/authorized flag, supplied actor, injectable confirmer or --yes option is added.

## Fixed installation input

The only install input is `<workspace>/config/quick_scan_delegation_install.json`. The CLI does not accept an arbitrary install path. Exact required keys: protocol (`stockwiki.refresh_delegation_install/1.0.0`), workspace_root, preview_id, preview_record_sha256, agent, authorization_reference, expires_at. Unknown keys and duplicate JSON keys are rejected. The current real OS principal must equal both the original preview-service principal and original policy owner.

Installation independently rechecks the original persisted ready preview, exact native record hash, live original owner permissions and input-file stability. It derives the complete binding from the native record and policy, not caller supplied work specifications. The grant's expiry is explicit UTC Z, no more than 24 hours after its native creation; it covers the original preview confirmation window. There is no implicit permission cache or TTL extension.

Agent metadata is `{profile_id, profile_sha256, harness_ref}` as recorded in the owner install file. `agent_assurance=local_owner_namespace` and `authorization_basis=recorded_user_authorization`. These are not proof of a particular harness binary or remote identity. authorization_reference is a bounded opaque source reference, never executed or dereferenced. Strong independent agent authentication would require a separately authenticated deployment identity; it is not claimed here.

## Immutable grant and single action

`stockwiki.refresh_delegation/1.0.0` records native owner principal, canonical workspace root, agent metadata/assurance/source, created_at/expires_at and full binding. Its ID is:

`dg1_ + SHA256(canonical({owner_principal,workspace_root,consumer_id,preview_id}))`.

Its separate `record_sha256` hashes the complete record excluding that hash, including its stable ID and original creation timestamp. The ID intentionally remains stable for the same exact native preview. Reinstalling the identical action preserves its first timestamp. Changing expiry/profile/source or any binding cannot install a replacement under that preview; a revoked grant cannot be reinstalled. Grant paths cannot alias another ID.

The binding contains: preview ID/native record hash, request/scope/owner-state/policy hashes, fixed consumer, original StockWiki store ID, full SubjectRefs, fields, original question items/generations, module anchors, provider/model, cohort, complete frozen original quote, exact original QA deployment/policy/route references and raw original budget-policy file hash. There is no independent budget counter. Positive cost/request quote limits are required; this initial implementation is for bounded dispatch actions, not a zero-cost metadata-only approval.

Grant records reuse original immutable publication in `runs/state/quick_scan_refresh/delegations/`. Revocations are immutable records in `delegation-revocations/`. No queue, result database or cost ledger is introduced. All grant/config/record reads reject symlink/junction/hardlink redirection and unstable/oversized files. Original native namespace retention limits remain fail-closed.

The confirmation ID is:

`rc2_ + SHA256(canonical({owner_principal,consumer_id,grant_id}))`.

The first idempotency-key hash is frozen in the complete confirmation. The same key reuses the first native receipt/time; a different key cannot create a second action for the grant. Concurrent publishers retain original immutable lock behavior: one record, consistent replay or bounded busy/conflict refusal. Callers may retry the same confirmation read/action key; this never authorizes an HTTP resend.

## Current permissions, expiry and accounting

Both fresh registration and current_permissions inspection load the actual installed grant and irrevocable revocation record, check real native principal/current original owner policy, exact namespace/scope/model/quote/deployment/budget-policy hash and grant validity. Current permission reads retain the original frozen quote; a later volatile quote cannot expand it. An expired preview cannot create a new confirmation/registration, but an already registered action may continue only under the original current_permissions rules and a still-valid non-revoked grant.

StockQA uses its original fixed native CLI transport, strict duplicate-free parse, original schema validation and an independent delegated binding validator. Its original admission journal/read_registered/prepare_execution accept rc2 only through that native consent path. Exact original receipt hashes remain in the same action record. Existing ApprovedRefreshSession.check is still the callback at each original native send boundary; no permission memoization or automatic TTL is added. Revocation does not undo a send already admitted/in flight, and cannot discard its actual charge or received outcome.

A delegation does not grant original work-control, comparison retry, unknown isolation, accounting reconciliation or quota cancellation. Work-decision rc1 references in the separate WorkDecisionAuthority/known-outcome journal/refresh comparison schema remain unchanged and reject rc2. Old unknown/unpriced reservations remain original liabilities. In particular the actual S1 database is still schema20 with unpriced outcomes; this candidate does not migrate it, clear it, exclude it, or make it dispatchable. Owner-approved independent continuation requires the separate original-ledger capability, cumulative limits and explicit checks; a grant alone is insufficient.

## Real compatibility defect repaired

A declared v18 read-only budget view previously unconditionally queried quota tables introduced later. The added getter branch validates the complete historical v18 schema, preserves original reserved/spent/request/in-flight/unreconciled totals and reports absent legacy quota capability as zero quota-accounted attempts. It does not set unknown cash to zero. Historical isolation requests are explicitly unsupported. Current schema missing quota tables and a falsely relabelled v18 header still fail schema validation. No reserve path, DDL, production DB or continuation behavior changes.

Historical v15/v18 fixture construction now uses the original disposable-only remove_c06_additions helper and current SCHEMA_VERSION expectations. It removes all later DDL before lowering a disposable test DB header; it never disguises a complete current DB as an old schema and never runs on a real owner workspace.
