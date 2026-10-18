# Original owner batch preparation: minimum useful scope

Status: four-file default-off candidate implemented and source frozen; independent whole-node review and b02 original public E2E pending. No original source, owner namespace, environment credentials or
production DB touched. Current real experiment source pins must not be hot changed.
The root owns PWF/source application timing. This candidate is independent.

## Measured root cause

The prior accepted p06 software E2E has 112 direct cold StockWiki subprocesses:
38 refresh-owner calls (~271.5s), 62 route calls (~23.3s), 12 subject-dispatch calls
(~57.6s). The 12 before_question calls take 91.57s. Earliest original lease→POST is
319.96s, safe native output327.65s, recovery432.22s, original lease600s. These are
scripted-wire timings, not actual model-network or financial accuracy claims.

`OwnerResearchServices.generation_scope` loops `lifecycle.before_question`.
Each calls `_owner_work`→`ApprovedRefreshSession.check`, which starts the original
native confirmation/current-permission CLI and then native route validation.
All twelve work items were already registered by the same original immutable
action. Rechecking the full same action before each claim spends most of the
oldest lease on repeated process initialization, before any model POST.

Further repetition is separate: `_begin_question_pack_send` calls the subject
registrar once per member. Each ApprovedSession registrar checks the full action,
then native registrar checks the route both before/after a fixed subject CLI.
The subject CLI also calls pure IQS request/profile/receipt validators via fixed
subprocesses. Merely wrapping the twelve registrations in a shell/list loop would
save few starts and would still pay these inner validators; it is not a useful
performance claim by itself.

## Recommended first increment: owner-bound claim of an exact existing batch

Add an explicit opt-in original owner-batch preparation mode, default off. No
change to singleton callers or the existing default partial-claim behavior.
Only transport-managed original ApprovedRefreshSession + the exact selected
original task/intention question list is eligible. No references/reused results,
nonpending/uncertain work, missing generations, mixed subject/perimeter, mixed
routes or duplicated IDs may be promoted into this batch.

1. Original OwnerResearchServices validates its task/envelope and resolves the
   ordered exact question set through the original approved action/session.
2. A new explicit original lifecycle/session batch method performs one fresh
   `ApprovedRefreshSession.check()` for this one indivisible claim action. It
   validates all per-question prompt/fingerprint, scope, identity, generation,
   original admitted work IDs and native owner bindings. It does not expose a
   caller-provided skip_check flag, monkeypatch `.check`, or install a permission
   cache/ContextVar proof that transport could reuse.
3. The original WorkStore gains a bounded atomic claim primitive for existing
   exact admitted work only (1..30). One original SQLite BEGIN IMMEDIATE verifies
   every work's expected frozen identity/generation/binding and pending state,
   then applies the existing claim transition/event once per work with distinct
   lease tokens, original epochs and the same original clock/lease duration.
   Any mismatch rolls back all claims/run attachments. It creates no new work,
   does not recover expired work, does not reset unknown state, extend leases,
   reserve budget, create attempts or send HTTP. A public primitive alone confers
   no owner/network authority, just like the original singleton store.claim.
4. Return ordinary existing handle dictionaries to the unchanged original
   `dispatch_question_pack_context`, transport, SDK and Runner. Those continue
   fresh current owner/policy/revocation checks and the original atomic budget
   reservation immediately before every POST. Same-generation/cell uniqueness,
   original unknown cost/inflight/request accounting and cached receipt lookup
   remain unchanged.

Small source scope: StockQA WorkStore + lifecycle + ApprovedRefreshSession/
OwnerResearchServices adapter (four existing files; helper factoring only as
needed). No StockWiki/IQS wire/schema/ledger migration, no daemon, HTTP client,
new ledger, second Runner/scheduler or long-lived authority process.

Expected opportunity, not a benchmark promise: remove eleven repeated full
owner checks from one exact 12-work claim action (~70–85s in the prior trace),
and stop consuming the earliest lease while later claims wait on CLI startup.
The unrelated subject-registration path remains as-is. This alone may give the
real 200s model more lease headroom; only a measured new E2E can establish it.

## Why not immediately batch subject registration too

It needs a genuine fixed JSON batch operation in both original StockWiki and IQS
validators, the original per-member native receipt semantics and all-or-none
registration/CAS/replay checks, not a bypass or cached expected dispatch. This is
larger than the four-file claim increment. Keep it a follow-up only if measurements
show claim batching is insufficient; don't assert a >200s win without measuring.
An in-process foreign-Python import or a long-lived daemon would violate current
original fixed-CLI isolation; neither is proposed here.

## Concentrated TDD and one whole-node E2E

* Primitive: any duplicate/missing/nonpending/expired/superseded generation or
  fingerprint/owner-binding drift rejects before mutation; injected failure on
  the final member rolls back earlier leases/events; concurrent overlapping
  batches admit at most one; all leases use original seconds/epochs and no send,
  budget, request count or unknown row changes occur.
* Original session: a real ApprovedRefreshSession is required for opt-in; caller
  dictionaries/callbacks cannot claim authority; unknown or reference questions,
  mixed perimeters, stale action/policy/anchor and revoked native confirmation
  cause zero claims/POST. Explicit singleton/default behavior remains unchanged.
* Original transport: revocation after successful batch claim still refuses the
  actual SDK POST via the unchanged fresh original owner guard; budget cap and
  failed/missing member registrar still refuse, preserving old rows and cells.
* One isolated actual public owner/SDK/Company Runner software E2E, no paid API,
  same original full12 MiMo/free-agent pack and original native intent/receipt
  crash/restart/0POST recovery. Measure exact source SHA, claim→POST→safe-output→
  recovery wall and direct CLI counts, unchanged original600 lease, no permission
  caching; don't use reduced synthetic helper checks as a production positive.
* True different-agent whole-node review, all findings fixed before root CAS
  apply. No tiny helper review gates. Use minimum credential-free environment,
  socket deny, owned SQLite/write audit and explicit cleanup/retention evidence.

## Timing / coexistence

This root design reads source only. Pure candidate TDD may proceed in its owned
folder, but no heavy public E2E while the current real sample is running. Root
chooses when to run it and when to apply after exact-source independent review.
If atomic scope validation requires substantially duplicating original admission
logic, stop and report that complexity rather than invent a parallel owner model.

## Implementation ledger

* Root approved exactly four original QA files, opt-in `owner_batch_claim=False`
  by default. No SW/IQS production changes or schema migration.
* RED: absent API cases failed before implementation. Native atomic transaction
  and pure adapter seams reached 32 passing cases; spies are explicitly synthetic
  and do not establish native owner authority. Five original singleton/crash/
  unknown/old-lease/cross-process race regressions passed in owned source overlay.
* Native `read_record` validates the immutable original full action/work/binding
  inside the same BEGIN IMMEDIATE. The approved adapter additionally matches each
  entry/specification to the original action by work ID and question ID; caller
  relabelling cannot claim another native row.
* b01 failed in the original test fixture install-delegation call after its 80s
  helper timeout, before batch claims, leases or SDK calls. Preserve b01.xml.
  Only the owned fixture install/confirm timeout becomes180s for b02; actual
  production behavior, permissions and lease600 remain unchanged.
* b02 uses final four-file source SHA, actual public software owner/delegation/
  quote/SDK/Runner with scripted vendor wire and synthetic identity/facts. It
  tests one true native12 atomic batch, native safe-output process death and
  fresh0POST recovery. It is not a paid-model/financial-accuracy experiment.
* The root separately owns the real HTTP200/error-body/usage-null diagnosis.
  Candidate budget/receipt behavior is deliberately unchanged; existing unknown
  records/actualNULL are not cleared or relabelled by this optimization.
