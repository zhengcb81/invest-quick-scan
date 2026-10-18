# Native operation handoff (after source review and installation)

These commands are the proposed public workflow. No actual workspace grant has been installed by this lane, and no real database or original S1 status was changed.

1. Use the existing original StockWiki query capture and `stockwiki.quick_scan_refresh_owner_cli --request ...` to obtain a fresh bounded native preview. The original owner policy must itself authorize every actual company/field/model; an IQS_01 policy does not become a 12-question policy through delegation.
2. Read its exact persisted native preview record metadata through the original RefreshRecordStore/native control namespace. Populate the fixed owner `config/quick_scan_delegation_install.json` from that record and the already authorized operator context. Supply a real profile/source reference, accurate local harness provenance metadata and explicit UTC expiry. Do not copy a toy fixture, use consumer JSON as a grant, or mark the process as a TTY human.
3. With the existing trusted root/code/release arguments, run `python -m stockwiki.quick_scan_refresh_owner_cli ... --install-delegation`. It reads only that fixed config, checks native OS owner/current original preview and publishes the exact grant. The response contains dg1 ID and digest, zero API requests and no dispatch.
4. Run the same native module with `--confirm-delegated PREVIEW_ID --delegation-id GRANT_ID --idempotency-key STABLE_KEY`. Capture the rc2 receipt. Reuse the same key after a transient publication-busy failure; never create a fresh model request to recover an uncertain send.
5. Give only rc2 confirmation ID to the original StockQA refresh admission CLI/config. The original executor authenticates native inspection/1.2, registers the action in the original SQLite journal, and enforces original route/budget/work/subject guards. Shared Company engine wiring continues through the previously delivered first-party services; this grant changes no question answers or financial qualifications.
6. Revoke through the same native owner module `--revoke-delegation GRANT_ID`. All later original current-permission/pre-POST checks reject it. Historical charges, unknown outcomes and immutable records remain. There is no grant re-enable/delete operation.

The install JSON must have exactly this shape (placeholders deliberately are not runnable grants):

```json
{
  "protocol": "stockwiki.refresh_delegation_install/1.0.0",
  "workspace_root": "REPLACE_WITH_CANONICAL_NATIVE_OWNER_ROOT",
  "preview_id": "REPLACE_WITH_ACTUAL_NATIVE_RV1_ID",
  "preview_record_sha256": "REPLACE_WITH_EXACT_NATIVE_RECORD_SHA256",
  "agent": {
    "profile_id": "REPLACE_WITH_ACCURATE_OPERATOR_PROFILE",
    "profile_sha256": "REPLACE_WITH_ACCURATELY_RECORDED_PROFILE_SHA256",
    "harness_ref": "REPLACE_WITH_ACCURATE_LOCAL_HARNESS_REFERENCE"
  },
  "authorization_reference": "REPLACE_WITH_RECORDED_USER_AUTHORIZATION_REFERENCE",
  "expires_at": "REPLACE_WITH_EXPLICIT_UTC_Z_DEADLINE"
}
```

No API key belongs in this file. Its profile digest is recorded provenance, not independent authentication of an agent. CLI arguments cannot select an alternative install file. Stronger agent authentication and standalone continuing grant budgets are outside this initial single-action contract.

Before any real model experiment, retain the original ledger and resolve/explicitly handle its old unreconciled constraint through the separate native continuation capability; never create a clean ledger to hide it. This node's green engineering tests do not declare that real S1 is ready or that financial answers are accurate.
