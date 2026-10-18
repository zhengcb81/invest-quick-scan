"""Deployment proof v2: reviewed scope instead of a frozen reviewer identity.

Offline verification only. A v2 proof pins the reviewed source bytes and the
independent review document; it grants nothing by itself.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROTOCOL = "iqs.deployment_proof/2.0.0"
ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOTS = (
    ROOT / "scripts",
    ROOT / "schemas",
    ROOT.parent / "StockQAbyLLM" / "src",
    ROOT.parent / "StockWiki" / "stockwiki",
    ROOT / "runs/shared-engine-production-2026-10-18/batch-carrier-controller-candidate",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _under_allowed(path, allowed_roots=None):
    resolved = Path(path).resolve()
    roots = ALLOWED_ROOTS if allowed_roots is None else tuple(Path(root) for root in allowed_roots)
    return any(resolved == root.resolve() or root.resolve() in resolved.parents for root in roots)


def verify(proof, *, proof_path=None, allowed_roots=None):
    if not isinstance(proof, dict) or proof.get("protocol") != PROTOCOL:
        raise ValueError("deployment_proof_v2_required")
    scope = proof.get("scope")
    if not isinstance(scope, list) or not scope:
        raise ValueError("deployment_proof_v2_scope_required")
    review_ref = proof.get("review")
    if not isinstance(review_ref, dict) or not {"path", "sha256"} <= set(review_ref):
        raise ValueError("deployment_proof_v2_review_required")
    review_path = Path(review_ref["path"])
    if not review_path.is_file() or sha256(review_path) != review_ref["sha256"]:
        raise ValueError("deployment_proof_v2_review_changed")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    reviewer = review.get("reviewer") if isinstance(review, dict) else None
    if (
        review.get("status") != "passed"
        or review.get("open_findings") != []
        or not isinstance(reviewer, dict)
        or not isinstance(reviewer.get("agent_id"), str)
        or not reviewer["agent_id"]
        or not isinstance(reviewer.get("author_agent_ids"), list)
        or not reviewer["author_agent_ids"]
        or reviewer["agent_id"] in reviewer["author_agent_ids"]
    ):
        raise ValueError("deployment_proof_v2_review_not_passed")
    if review.get("scope_sha256") != canonical_sha256(scope):
        raise ValueError("deployment_proof_v2_scope_not_reviewed")
    files = []
    for row in scope:
        path = Path(row["path"]).resolve()
        if not path.is_file() or not _under_allowed(path, allowed_roots):
            raise ValueError("deployment_proof_v2_scope_path_unavailable")
        if sha256(path) != row["sha256"]:
            raise ValueError("deployment_proof_v2_scope_changed")
        files.append({"path": str(path), "sha256": row["sha256"], "bytes": path.stat().st_size})
    return {
        "proof_ref": {"path": str(proof_path or ""), "sha256": sha256(proof_path) if proof_path else ""},
        "files": files,
        "public_context": review.get("public_context"),
        "review_protocol": review.get("protocol"),
        "reviewer": reviewer["agent_id"],
    }
