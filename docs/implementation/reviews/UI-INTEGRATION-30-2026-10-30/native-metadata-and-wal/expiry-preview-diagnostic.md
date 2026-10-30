# Real expired preview: bounded read-only diagnosis

The exact original request currently passes the original native preview service. Its earlier generic CLI failure is not evidence of a malformed request or permanent admission denial.

## Actual evidence

- Original failure: 2026-10-30 11:22:02–11:22:39 UTC, exit 2, `refresh_owner_preview_rejected`; stderr empty. No original exception type/stage survived.
- Current pure `scripts.refresh_contract.validate_request` passes the exact original refresh_request/1.1.0 with source_query/2.6.0. Owner policy and quote both use 1.1.0. Original captured result was coverage_gap with no missing subject refs.
- Independent original QA read inspection passes at 11:33:35–11:33:56 UTC: IQS22 original work is delivered generation 2, budget available, reservation_created=false.
- Independent direct original `RefreshPreviewService.preview` passes at 11:34:50–11:35:37 UTC. Its IQS22 plan is **manual_refresh_required**, existing work delivered, generation=null, reuse_observation_id=null. This is a native planning result, not confirmation, reservation or paid dispatch approval.
- Original preview directory metadata: 59 JSON files, 1,515,387 bytes, no foreign/lock entries; below 512 record / 64 MiB retention limits at this later inspection. This does not establish its past concurrent state.

## Scope and conclusion

The isolated diagnostic uses real original stores read-only, with SQLite connects guarded to URI mode=ro and PRAGMA query_only. Keys were removed, network denied and offline contract temporary files redirected into the reviewer's owned runtime. The native service was invoked directly; the CLI's later `records.save` was deliberately not called. No original source/DB modification, confirmation, admission, model/API call, or server launch occurred. The now-empty owned runtime was strictly resolved beneath ui-review, checked free of files/reparse entries, and deleted.

The current service success rules out a deterministic current request/route/query/QA-inspection/planner failure. It does **not** establish the cause of the earlier transient failure, nor verify actual original CLI preview publication. In `quick_scan_refresh_owner_cli.py`, generic ValueError/KeyError/ObservationImportError branches suppress the original stage/reason; plain failures in `inspect` are generic as well. The failure could have occurred before/within preview or at final records.save. There is insufficient historical evidence to choose one. Do not assert historical WAL/busy/drift/retention as proven.

## Smallest next step

Keep the valid request and original admission rules. Add bounded private stage diagnostics around the native `service.preview` and `records.save` calls; map only known safe error codes, never serialize raw payloads, answers, config or keys. The controller can then refresh the native capture and retry the public planning-only CLI, which may publish its ordinary immutable preview but must not auto-confirm or dispatch. If the native result remains manual_refresh_required, handle it through the existing explicit native work-decision/research workflow, not an invented generation or a bypass.

This diagnosis is independent of the subject DTO projection repair. JSON companion records exact source/evidence SHA256 and scope. Reproduction artifacts: `expiry-preview-qa-inspect.py/.json` and `expiry-preview-service-diagnostic.py/.json`; these are diagnostic harnesses, not production entry points.
