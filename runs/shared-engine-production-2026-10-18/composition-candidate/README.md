# Shared Company Engine composition candidate

This candidate composes the existing Company Lab `Runner`, Runtime Lab
`RuntimeBridgePort`, and StockQA `OwnerResearchServices`. It contains no model
HTTP implementation, no second work/budget database, and no alternative
question scheduling loop. Do not install or advertise this candidate as an
unrestricted production launch command.

## Callable interface

`execute_shared_engine(task, services, session_config, output, *, session_dir,
transport_origin="stockqa_live")` requires an already constructed original
`OwnerResearchServices` bound to the same original `LoadedTask` and an admitted
StockQA action. Task binding metadata does not substitute for native approval.
Each execution/restart requires a fresh service observer instance over the same
original approved SQLite/session. Prior observations are refused rather than
cleared; native work, held costs and existing safe responses remain intact.

`resume_shared_engine(task, services, session_config, checkpoint_path, output,
*, session_dir, transport_origin="stockqa_live")` verifies the original
checkpoint, entire original event history, and exact registered task. It uses
native receipt/intent inspection before permitting further execution. Missing
or unresolved native response proof causes refusal, never blind resend.

`inspect_native_recovery(services, *, attempt_ref=None, intent=None)` is a
read-only native inspection helper. Exactly one original recovery key is
required. A missing intent proof remains a pause.

The CLI exposes only `capabilities` and `report --input DIR --output NEW_DIR`.
It does not dynamically import user-specified factories or construct owner
authority from arbitrary configuration. The public execution API needs the
original caller's admitted lifecycle; production CLI setup remains a separate
mainline integration obligation.

## Deliberately narrow capability

- Current registered twelve original questions and cutoff `2026-10-13` only;
  the shared strategy validation enforces exact question bodies and projection.
- Existing `fixed3`, `free_agent`, `evidence_agent` scheduling is reused.
- Native one-shot packs currently require the original MiMo capability and
  original owner generation controls. Native multi-turn pack execution is
  refused; original multi-turn registration currently supports singleton work.
- A strategy requesting a repair of previously responded work may be refused
  by the original native service. This does not authorize another send.
- Reports are research artifacts. This composition does not create an official
  search-backed answer checkpoint, financial accuracy approval, or owner grant.
- `stockqa_live` is the caller's observed transport classification, not an owner
  attestation. Scripted tests must pass `scripted_wire`; source/evidence origin
  is derived independently from the original evidence board.

## Durable recovery boundary

The original event journal is validated and atomically persisted on every event.
Before each model dispatch a thin forwarding port saves the original pending
checkpoint and an immutable full history snapshot. A returned original receipt
is saved to that pending checkpoint before it reaches the Runner. This handles
ordinary SDK exceptions and real process death without relying on synthetic
crash exceptions. The pending history is immutable because the active event
journal continues growing after dispatch.

Each next model intent consults the original native SQLite intent lookup. A
saved original response is replayed with no model HTTP; an unresolved existing
intent pauses; only the original service's proof of no prior intent permits its
normal dispatch path. This depends on the original native task/intent binding,
not on an IQS cache index or a new ledger.

On recovery of a historical checkpoint already containing `receipt_model`, the
original exact receipt projection is retained after comparing native physical
identity, actual/planned model, output, tool calls, usage and finish status.
Native getter timestamps and absent private session handles must not cause a
duplicate physical request to be invented. Conflicting native output or usage
is refused. The strict Company metrics deduplication is unchanged.

Atomic record replacement retries only bounded Windows sharing violations on
the same completed rename. It never retries a model request. Failures retain
the directory for inspection. The code does not remove another run's files,
renew native leases, release unknown reservations, restore hidden reasoning, or
claim that an expired native action can resume.

## Test scope

`tests/test_shared_company_engine.py` executes all three original Runner
strategies, original exports, validated reports, pending checkpoint recovery,
warm intent cache replay, unknown fencing and output safety in disposable paths.
Synthetic transport/native observations are explicitly labelled. Native owner
software positives belong to the original owner-service test suite; these tests
are not a real-company, financial accuracy, or production-admission positive.

Tests intentionally retain failed-run evidence under this candidate directory;
do not stage or publish those full temporary trees. No source repository,
production database, stock universe, API key or paid endpoint is modified.

## Native task 3.0 and original-owner acceptance extension

`scripts/shared_company_task.py:create_native_task` is a separate additive
carrier factory. It requires an original `QuickScanWorkLifecycle` with the
original `ApprovedRefreshSession` and native `OwnerRefreshSession` over the
same store. It copies twelve authorized full question contracts from the
original frozen manifest/subject context, binds the exact module versions and
five original input-byte hashes, and derives the identity document from the
approved original identity DTO. It does not use the legacy synthetic target
loader or make a name/ticker join.

The raw protocol is `iqs.company-agent-task/3.0.0`. Its `owner_binding` uses
`iqs.native-company-owner-binding/1.0.0` and contains the original subject,
authority file reference, exact native scope, and original-input digest.
This descriptive binding is restored only for the known task-3 protocol by the
coordinator's Company overlay; the original current native owner check remains
the permission boundary. No permission expiry is invented from a caller flag.

The initial carrier deliberately supports only the original full-pack
`free_agent` strategy, twelve native questions, cutoff `2026-10-13`, and zero
search queries. This avoids assigning a different native question to a legacy
factual domain merely because its scheduling alias occupies that position.
Run and experiment identifiers are bounded at the original export's 80 chars.

`tests/test_shared_company_engine_native_e2e.py` exercises the original public
route/authority/query/preview/confirmation/admission software over synthetic
temporary identity data. A scripted MiMo response runs through the original
SDK, native pack/receipt/visible-output transaction and shared Runner. The cold
child exits immediately after original native response persistence, before
the bridge can return its receipt. A new process must recover the original
pending checkpoint through the original native intent lookup with zero new
POSTs and produce the validated native summary. This extension is not a paid
model accuracy experiment and does not create an official search checkpoint.

The owned fixture's optional dict parameter sets the historical subject scope
and producer information date before their original public import/export; it
does not rewrite a generated authority. The isolated test budget covers the
original conservative twelve-field quote before a one-request pack reduces
actual HTTP. A quote blocked by the original budget is never confirmed.

All native test processes use an explicit environment allowlist and inherited
socket-denial guard. No API key is inherited by the pytest worker or vendor
child. Failure output is bounded. Existing default fixture parameters remain
unchanged. The test uses the original 600-second work lease and never renews
it to conceal slow original owner checks. The exact-source native test passed
on 2026-10-18: one test in 435.21 seconds. The cold process made one scripted
vendor POST and exited with code 86 after original native output persistence.
The fresh process recovered all twelve slots with zero new POSTs and one
original physical attempt. `native-e2e-final.xml`, `native-task-cas.json`, and
`native-e2e-evidence.json` bind the final source and thin evidence. The long
wall time includes original per-question owner/current checks; it is not a
model-speed benchmark. Independent whole-node review remains a separate
coordinator decision. No paid model, real-company accuracy, human consent,
or official search-backed checkpoint is claimed by this software fixture.
