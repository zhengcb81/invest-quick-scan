# Independent acceptance review: ANSWER-CODEC-03 and SESSION-PACK-04

Review date: 2026-10-16. Baseline: the coordinator's frozen source copies, read
against each implementation card and integration contract. Fixes apply only to
the coordinator candidate copies. Original source and worker handoff documents
remain historical; no external repository commit or production write was made.

## Confirmed findings and disposition

| ID | Priority | Minimal reproducer on frozen source | Repair in candidate |
|---|---|---|---|
| S1 | P1 | Start a 900-second task; snapshot; recover after 899 seconds; new SDK receives 900 seconds. A wait between packs likewise gives 899 seconds rather than at most 1. | Remaining wall uses original UTC deadline and process monotonic time; idle/downtime are charged. |
| S2 | P1 | Supply a matching trusted hash for a syntactically malformed checkpoint: remove sdk_steps_used, set input_tokens_used=-500, add an unknown top-level field, or extend deadline to the next day. Each is accepted. | Closed schema and nonnegative accounting validation, per-segment consistency, exact start+wall UTC deadline; trusted hash check remains first. |
| S3 | P1 | Capture checkpoint from inside injected SDK.step, before its outcome returns. It has sdk_steps_used=1 but usage_complete=true, no uncertain marker, no inspection pack; recovery accepts it as clean. | In-flight pack is explicitly uncertain in public state/checkpoint; recovery refuses it and continuation is blocked during the step. |
| S4 | P2 | Mutate original tools[0].function.name after pack 1; pack 2 receives the changed tool although registered tools_sha256 is unchanged. | Copy tools at construction and again at the factory boundary; copy nested caller context. |
| S5 | P2 | A sole/final unknown_usage step yields public blocked=true but replay incomplete=false; a plan projects following packs with full token allowance. | Unknown final usage gives incomplete replay; unknown/undetermined plan consumption blocks following SDK projections. |
| S6 | P2 | Known step uses 10 input/5 output; restore its checkpoint; segment usage becomes 0/0 although company totals remain 10/5. | Restore per-segment usage and preserve it across two restarts. |
| C1 | P2 | Set a metric value=null and evidence_ids=[FOREIGN-SOURCE] in the valid compact fixture. expand accepts the foreign reference. | Every supplied metric reference is confined to the current answer's source_claims, including null-valued metrics. |
| C2 | P2 | Use a syntactically trusted board with official_url=https:///no-host. expand emits it; frozen native valid_url rejects the missing hostname. | Match native HTTP(S)+hostname syntax validation before copying metadata. |

S2 is a malformed-input validation counterexample, not a claim that an attacker can
forge an already pinned trusted expected hash. C2 likewise binds the intentionally
synthetic board in the test; the separate original-context/wrong-board refusal is
already covered by the package suite. No production identity certification follows.

## Executable evidence

Run from the project root:

    python runs/six-tools-acceptance-2026-10-16-01/reviews/codec-session-scratch/run_acceptance.py
    python runs/six-tools-acceptance-2026-10-16-01/reviews/codec-session-scratch/run_candidate_suites.py

Independent regressions: frozen source SESSION 11 failed / CODEC 2 failed;
candidate SESSION 11 passed / CODEC 2 passed. Candidate package suites:
SESSION 81 passed / CODEC 63 passed, zero failures and skips. The new regressions
are also copied into each candidate tests/test_acceptance_regressions.py.
The second runner sets PYTHONUTF8=1 so subprocess CLI logs are decoded consistently
on Windows, and routes temporary CWD/logs/SQLite under this review's scratch root.
Both runners suppress bytecode writes and disable unrelated pytest plugin loading.

Records: codec-session-scratch/runs.json, suite-runs.json, and the corresponding
source-*, candidate-*, suite-* stdout/stderr raw files. These are independent
coordinator observations, not replacements for the worker's historical tests.json.

## Verified scope

Read-only CodeGraph context for both original labs; frozen source inspection;
pure codec context binding, canonical/raw hash separation, lossless domain,
metric/item evidence linkage; injected SDK resource kwargs, pending tool IDs,
recovery counters/deadline; frozen SDK fake-HTTP integration; original native
answer validation and real T0 round trips; T1 missing-slot replay remains missing.
No model/search requests were sent. Runtime keys and private provider histories
were not loaded. New package metadata and integration docs identify 1.0.1 while
compatible public carriers stay 1.0.0. No installation was performed.

## Not verified / retained boundaries

No live provider retry, cache hit, latency, token/cost improvement, financial answer
quality, production owner, durable native-budget recovery or external source
identity was certified. The controller must authenticate original receipt ownership,
load/verify referenced public result bodies, and durably bind the trusted checkpoint
hash. This review is not a production or financial qualification gate. Main-agent
cross-package integration and final CAS writeback remain separate acceptance work.
