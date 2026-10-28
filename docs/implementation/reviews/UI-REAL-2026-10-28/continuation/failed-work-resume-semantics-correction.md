# Correction: original failed work stops the pack scheduler on resume

Checked against production StockQA commit 09b51ba and the real original CATL run-a341be1cf7464e5ea0b8efce757884de/result-2.json (0 new model HTTP).

The earlier failed-work-resume-semantics.md correctly described immutable original registration and inability to claim failed work, but its conclusion that the full runner automatically skips failed work and continues pending questions was incomplete. QAEngine._process_question_packs sets stopped_reason=work_claim_refused for every before_question refusal, so pending questions after an existing failed item remain undispatched. Actual IQS04 refusal: resume_original_work_delivery_or_reconciliation_required. The root lifecycle is right not to dispatch the failed item; the scheduling branch needs a separately verified read-only terminal-state skip before it may continue other authorized pending items.

Do not repeat the old task on 09b51ba expecting it to progress past existing failed work. Root has requested a small optional native terminal assertion for this entry path, preserving failed work/error/null score and the ordinary owner/budget/send guards. Unknown, foreign, superseded or unproven work must still stop. This is distinct from 09b51ba's already-tested in-flight pack member finalization path. No old fields or scores should be synthesized.

The original report remains separately retained as historical evidence. This correction does not claim the new source is already reviewed, committed, deployed or live-accepted.
