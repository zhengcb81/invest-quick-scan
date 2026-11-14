"""AC-01 harness: dump deterministic outputs from one checkout for byte comparison.

Run with the checkout's own scripts on sys.path; prints one JSON object of
sha256 digests. Comparing two checkouts' output must show zero difference when
the question bank is not expanded (BASIC-BANK-EXPANSION-21 AC-01).
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc  # noqa: E402
import question_sets as qs  # noqa: E402
import routing as routing  # noqa: E402
import scoring_rubrics as sr  # noqa: E402


def sha(value):
    return hashlib.sha256(mc.canonical_bytes(value)).hexdigest()


def compose_digests():
    out = {}
    base = qs.read_json(ROOT / "examples/profile.json")
    profiles = {
        "example": base,
        "bank_type": {**base, "company_type": "bank", "industry_modules": []},
        "cyclical": {**base, "cycle_sensitive": True,
                     "cycle_position": "OFFLINE FIXTURE: trough"},
    }
    with tempfile.TemporaryDirectory(prefix="ac01-") as temp:
        for name, profile in profiles.items():
            for mode in ("quick", "full"):
                target = Path(temp) / f"{name}-{mode}"
                qs.compose(profile, mode, target)
                manifest = qs.read_json(target / "manifest.json")
                questions = qs.read_json(target / "questions.json")
                out[f"{name}-{mode}-manifest"] = sha(manifest)
                out[f"{name}-{mode}-questions"] = sha(questions)
                out[f"{name}-{mode}-method_id"] = manifest["method_id"]
                out[f"{name}-{mode}-count"] = manifest["question_count"]
    return out


def library_digest():
    return qs.validate_library()


def route_digests():
    out = {}
    package, modules, release, _ = __import__("module_registry").load_current(root=ROOT)
    if hasattr(routing, "minimum_question_count"):
        out["minimum_questions_empty"] = routing.minimum_question_count(modules, [])
        out["minimum_questions_risk"] = routing.minimum_question_count(
            modules, ["RECOVERY_01", "RECOVERY_02"])
    else:
        # Pre-expansion code path: the same numbers, computed the old way.
        out["minimum_questions_empty"] = len(modules["common"]["questions"])
        out["minimum_questions_risk"] = len(modules["common"]["questions"]) + 2
    return out


def rubric_digests():
    _, modules = qs.load_library()
    body = {
        "schema_version": "1.0.0", "version": "1.0.0",
        "method_id": "core-constructs-v1-operating", "owner": "iqs",
        "cohort": "operating", "valid_from_utc": "2026-09-30T00:00:00Z",
        "valid_until_utc": None, "calibration_sample_refs": [],
        "minimum_check_level": "execution_verified",
        "dimension_min_coverage": 0.7, "quality_min_coverage": 0.8,
        "quality_weights": dict(qs.QUALITY_WEIGHTS), "supersedes": None,
        "core_basket": [{"construct_id": q["construct_id"], "question_id": q["id"],
                         "question_definition_sha256": mc.digest(q),
                         "dimension": q["dimension"], "scope": q["scope"],
                         "rubric_version": q["rubric_version"]}
                        for q in modules["common"]["questions"]],
        "critical_extensions": [],
    }
    sealed = sr.seal_rubric(body)
    return {"rubric_release_id": sealed["rubric_release_id"],
            "core_basket_sha256": sha(sealed["core_basket"]),
            "expected_core": 24 if len(sealed["core_basket"]) == 24 else len(sealed["core_basket"])}


def summarize_digest():
    dims = list(qs.DIMENSIONS)
    rows = [{"id": f"IQS_{i:02}", "construct_id": f"IQS_{i:02}", "comparison_role": "core",
             "dimension": dims[(i - 1) // 3], "aggregation": "scored",
             "status": "scored", "score": 4 + i % 7, "critical": False}
            for i in range(1, 25)]
    return {"summary_sha256": sha(qs.summarize(rows, "core-constructs-v1"))}


print(json.dumps({
    "library": library_digest(),
    "compose": compose_digests(),
    "route": route_digests(),
    "rubric": rubric_digests(),
    "summarize": summarize_digest(),
}, ensure_ascii=False, sort_keys=True))
