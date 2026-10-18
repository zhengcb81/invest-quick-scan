"""Offline deployment proof v2 verification tests."""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "runs/shared-engine-production-2026-10-18/batch-carrier-controller-candidate"
SPEC = importlib.util.spec_from_file_location("deployment_proof_v2", ROOT / "scripts/deployment_proof_v2.py")
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)


def write(path, value, raw=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        path.write_bytes(raw)
    else:
        path.write_text(json.dumps(value) if not isinstance(value, str) else value, encoding="utf-8")
    return path


def proof(tmp_path, **overrides):
    scope_file = write(tmp_path / "scope.py", "print('x')\n")
    scope = [{"path": str(scope_file), "sha256": hashlib.sha256(scope_file.read_bytes()).hexdigest()}]
    review = {
        "protocol": "iqs.independent_review/1.0.0",
        "status": "passed",
        "open_findings": [],
        "scope_sha256": v2.canonical_sha256(scope),
        "reviewer": {"agent_id": "reviewer-1", "author_agent_ids": ["author-1"]},
    }
    review_file = write(tmp_path / "review.json", review)
    value = {
        "protocol": "iqs.deployment_proof/2.0.0",
        "created_at": "2026-10-18T12:00:00Z",
        "scope": scope,
        "review": {"path": str(review_file), "sha256": hashlib.sha256(review_file.read_bytes()).hexdigest()},
    }
    value.update(overrides)
    return value, review


def test_valid_v2_proof(tmp_path):
    value, _ = proof(tmp_path)
    result = v2.verify(value, allowed_roots=[tmp_path])
    assert result["files"][0]["sha256"]


def test_changed_scope_file_rejected(tmp_path):
    value, _ = proof(tmp_path)
    Path(value["scope"][0]["path"]).write_text("print('changed')\n", encoding="utf-8")
    try:
        v2.verify(value, allowed_roots=[tmp_path])
    except ValueError as error:
        assert "scope_changed" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_reviewer_must_differ_from_authors(tmp_path):
    value, review = proof(tmp_path)
    review["reviewer"]["author_agent_ids"].append("reviewer-1")
    review_file = Path(value["review"]["path"])
    review_file.write_text(json.dumps(review), encoding="utf-8")
    value["review"]["sha256"] = hashlib.sha256(review_file.read_bytes()).hexdigest()
    try:
        v2.verify(value, allowed_roots=[tmp_path])
    except ValueError as error:
        assert "review_not_passed" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_open_findings_rejected(tmp_path):
    value, review = proof(tmp_path)
    review["open_findings"] = ["x"]
    review_file = Path(value["review"]["path"])
    review_file.write_text(json.dumps(review), encoding="utf-8")
    value["review"]["sha256"] = hashlib.sha256(review_file.read_bytes()).hexdigest()
    try:
        v2.verify(value, allowed_roots=[tmp_path])
    except ValueError as error:
        assert "review_not_passed" in str(error)
    else:
        raise AssertionError("expected rejection")


def test_controller_delivery_routes_v2(tmp_path):
    import sys
    sys.path.insert(0, str(DIR))
    import controller_delivery

    scope_file = v2.ROOT / "scripts/search_receipt.py"
    scope = [{"path": str(scope_file), "sha256": hashlib.sha256(scope_file.read_bytes()).hexdigest()}]
    review = {
        "protocol": "iqs.independent_review/1.0.0",
        "status": "passed",
        "open_findings": [],
        "scope_sha256": v2.canonical_sha256(scope),
        "reviewer": {"agent_id": "reviewer-1", "author_agent_ids": ["author-1"]},
    }
    review_file = write(tmp_path / "review.json", review)
    value = {
        "protocol": "iqs.deployment_proof/2.0.0",
        "created_at": "2026-10-18T12:00:00Z",
        "scope": scope,
        "review": {"path": str(review_file), "sha256": hashlib.sha256(review_file.read_bytes()).hexdigest()},
    }
    proof_file = write(tmp_path / "proof.json", value)
    result = controller_delivery.verify_deployment({
        "path": str(proof_file),
        "sha256": hashlib.sha256(proof_file.read_bytes()).hexdigest(),
    })
    assert result["files"][0]["sha256"] == scope[0]["sha256"]
