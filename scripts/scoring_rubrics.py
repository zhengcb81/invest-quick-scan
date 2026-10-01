"""V02 pure rubric publication, aggregation and aligned comparison.

Inputs are projections of caller-validated immutable observations. This module
checks their consistency; it neither authenticates an owner nor grants a check
level. It has no provider, database, mutable registry or active-release pointer.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from module_contract import canonical_bytes, digest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/quick_scan/scoring-rubric.schema.json").read_text(encoding="utf-8"))
DIMENSIONS = ("business", "moat", "execution", "financial", "governance", "resilience", "growth", "valuation")
QUALITY_DIMENSIONS = DIMENSIONS[:6]
CORE_DIMENSIONS = {f"IQS_{i:02}": DIMENSIONS[(i - 1) // 3] for i in range(1, 25)}
CRITICAL_CONSTRUCTS = frozenset({"IQS_12", "IQS_13", "IQS_16"})
CHECK_LEVELS = ("unverified_model_output", "execution_verified", "screening_audited", "formal_research_accepted")
SIGNATURE_FIELDS = ("schema_version", "cohort", "minimum_check_level", "dimension_min_coverage",
                    "quality_min_coverage", "quality_weights", "core_basket", "critical_extensions")
AXIS_FIELDS = ("question_definition_sha256", "question_semantic_sha256", "scope", "scope_basis",
               "period_start", "period_end", "period_basis", "provider", "model", "model_config_sha256")
MAX_INPUT_BYTES = 1024 * 1024


def _validate(value, name):
    schema = dict(SCHEMA, **{"$ref": "#/$defs/" + name})
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    except ValidationError as exc:
        raise ValueError("invalid " + name.lower()) from exc


def _utc(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("invalid UTC time") from exc
    if result.tzinfo is None or result.utcoffset() != timezone.utc.utcoffset(result):
        raise ValueError("explicit UTC time is required")
    return result


def _signature(rubric):
    return {key: rubric[key] for key in SIGNATURE_FIELDS}


def validate_rubric(rubric):
    """Validate immutable identity and the fixed 24-construct denominator."""
    _validate(rubric, "Release")
    body = {key: value for key, value in rubric.items() if key != "rubric_release_id"}
    if rubric["rubric_release_id"] != "rubrel_" + digest(body):
        raise ValueError("rubric content hash mismatch")
    basket = rubric["core_basket"]
    if [q["construct_id"] for q in basket] != sorted(CORE_DIMENSIONS):
        raise ValueError("exactly one sorted entry per core construct is required")
    if any(q["dimension"] != CORE_DIMENSIONS[q["construct_id"]] for q in basket):
        raise ValueError("frozen core dimension cannot change")
    if any(type(w) is not int for w in rubric["quality_weights"].values()):
        raise ValueError("quality weights must be strict integers")
    if sum(rubric["quality_weights"].values()) != 100:
        raise ValueError("quality weights must sum to 100")
    extensions = rubric["critical_extensions"]
    if any(q["construct_id"] is not None or q["dimension"] not in QUALITY_DIMENSIONS for q in extensions):
        raise ValueError("critical extensions must be quality questions outside the core")
    ids = [q["question_id"] for q in basket + extensions]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question or critical replacement")
    if [q["question_id"] for q in extensions] != sorted(q["question_id"] for q in extensions):
        raise ValueError("critical extension order is not canonical")
    start, end = _utc(rubric["valid_from_utc"]), rubric["valid_until_utc"]
    if end is not None and _utc(end) <= start:
        raise ValueError("rubric validity interval is empty or inverted")
    if rubric["supersedes"] == rubric["rubric_release_id"]:
        raise ValueError("rubric cannot supersede itself")


def seal_rubric(body):
    """Create a deterministic candidate; this never activates a release."""
    rubric = copy.deepcopy(body)
    rubric.pop("rubric_release_id", None)
    rubric["core_basket"] = sorted(rubric.get("core_basket", []), key=lambda q: q.get("construct_id") or "")
    rubric["critical_extensions"] = sorted(rubric.get("critical_extensions", []), key=lambda q: q.get("question_id", ""))
    rubric["calibration_sample_refs"] = sorted(rubric.get("calibration_sample_refs", []))
    rubric["rubric_release_id"] = "rubrel_" + digest(rubric)
    validate_rubric(rubric)
    return rubric


def validate_upgrade(old, new):
    """Changed economic meaning requires a new method, never a silent rewrite."""
    validate_rubric(old)
    validate_rubric(new)
    if new["supersedes"] != old["rubric_release_id"]:
        raise ValueError("upgrade must explicitly reference the old release")
    if new["method_id"] == old["method_id"]:
        if _signature(old) != _signature(new):
            raise ValueError("changed aggregation or basket requires a new method_id")
        if tuple(map(int, new["version"].split("."))) <= tuple(map(int, old["version"].split("."))):
            raise ValueError("same-method version must increase")


def _read_bound_json(path, expected_sha256):
    with Path(path).open("rb") as handle:
        data = handle.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("input size or pinned byte hash mismatch")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON value")))


def load_rubric(path, *, expected_sha256, expected_release_id):
    """Read exact pinned bytes, including expired historical releases."""
    rubric = _read_bound_json(path, expected_sha256)
    validate_rubric(rubric)
    if rubric["rubric_release_id"] != expected_release_id:
        raise ValueError("pinned rubric release mismatch")
    return rubric


def _validate_snapshot(snapshot, rubric, expected_hash, at):
    _validate(snapshot, "Snapshot")
    if digest(snapshot) != expected_hash:
        raise ValueError("source snapshot hash mismatch")
    if snapshot["cohort"] != rubric["cohort"]:
        raise ValueError("source cohort does not match rubric")
    if snapshot["information_as_of"] > at.date().isoformat():
        raise ValueError("information cutoff is after computation time")
    rows = snapshot["records"]
    for field in ("id", "observation_id", "construct_id"):
        values = [r[field] for r in rows if r[field] is not None]
        if len(values) != len(set(values)):
            raise ValueError("duplicate source question, observation or construct")
    scope_ids = {}
    for row in rows:
        if row["score"] is not None and type(row["score"]) is not int:
            raise ValueError("scores must be strict integers")
        if row["scope"] == "entity" and row["scope_id"] != snapshot["entity_id"]:
            raise ValueError("row issuer does not match snapshot")
        scope_ids.setdefault(row["scope"], set()).add((row["scope_id"], row["scope_basis"]))
        if row["aggregation_role"] == "diagnostic_only" and row["critical"]:
            raise ValueError("diagnostic-only row cannot be a critical quality gate")
        if (row["period_start"] is not None and row["period_end"] is not None
                and (row["period_start"] > row["period_end"] or row["period_end"] > snapshot["information_as_of"])):
            raise ValueError("invalid or future observation period")
    if any(len(ids) > 1 for ids in scope_ids.values()):
        raise ValueError("mixed scopes cannot be aggregated into one company score")


def _grade_usable(row, rubric):
    return (CHECK_LEVELS.index(row["check_level"]) >= CHECK_LEVELS.index(rubric["minimum_check_level"])
            and row["check_level_receipt_id"] is not None and row["confidence"] != "low")


def _effective(row, question, rubric):
    if row is None:
        return None, False, "missing_question"
    role = "quality_core" if question["dimension"] in QUALITY_DIMENSIONS else question["dimension"] + "_core"
    for field, expected in (("construct_id", question["construct_id"]), ("dimension", question["dimension"]),
                            ("question_definition_sha256", question["question_definition_sha256"]),
                            ("scope", question["scope"]), ("aggregation_role", role)):
        if row[field] != expected:
            return None, False, field + "_mismatch"
    if row["freshness"] != "fresh":
        return None, False, "source_not_fresh"
    if not _grade_usable(row, rubric):
        return None, False, "check_level_or_confidence_unusable"
    audited_na = (row["status"] == "not_applicable" and row["is_audited_na"]
                  and CHECK_LEVELS.index(row["check_level"]) >= CHECK_LEVELS.index("screening_audited"))
    if audited_na:
        return None, True, "audited_not_applicable"
    if row["status"] != "scored" or row["score"] is None:
        return None, False, "status_not_scored"
    if any(row[k] is None for k in ("provider", "model", "model_config_sha256", "period_start", "period_end", "period_basis")):
        return None, False, "missing_comparison_axis"
    return row["score"], False, None


def aggregate(rubric, snapshot, *, expected_snapshot_sha256, at):
    """Derive a new immutable view; invalid raw status never supplies a score."""
    validate_rubric(rubric)
    instant = _utc(at)
    if instant < _utc(rubric["valid_from_utc"]) or (rubric["valid_until_utc"] is not None
            and instant >= _utc(rubric["valid_until_utc"])):
        raise ValueError("rubric not valid for this derivation time")
    _validate_snapshot(snapshot, rubric, expected_snapshot_sha256, instant)
    rows = {r["id"]: r for r in snapshot["records"]}
    evaluated, reasons, critical = [], [], {}
    for question in rubric["core_basket"] + rubric["critical_extensions"]:
        row = rows.get(question["question_id"])
        score, excluded, reason = _effective(row, question, rubric)
        item = dict(question, effective_score=score, excluded=excluded)
        if row is not None:
            item.update({field: row[field] for field in AXIS_FIELDS + ("scope_id",)})
        evaluated.append(item)
        if reason is not None:
            reasons.append({"id": question["question_id"], "code": reason})
        is_critical = (question["construct_id"] in CRITICAL_CONSTRUCTS
                       or question in rubric["critical_extensions"]
                       or (row is not None and row["critical"]))
        if is_critical and (score is None or score <= 3):
            critical[question["question_id"]] = "unresolved" if score is None else "material_concern"
    # A caller's validated extra quality-risk row can add a gate, never remove one.
    for row in snapshot["records"]:
        if row["critical"] and row["id"] not in {q["question_id"] for q in rubric["core_basket"] + rubric["critical_extensions"]}:
            usable = (row["status"] == "scored" and row["freshness"] == "fresh"
                      and _grade_usable(row, rubric)
                      and row["aggregation_role"] == "quality_core"
                      and row["dimension"] in QUALITY_DIMENSIONS
                      and all(row[k] is not None for k in
                              ("provider", "model", "model_config_sha256", "period_start", "period_end", "period_basis")))
            score = row["score"] if usable else None
            if score is None or score <= 3:
                critical[row["id"]] = "unresolved" if score is None else "material_concern"
    dimensions = {}
    core = evaluated[:24]
    for dimension in DIMENSIONS:
        applicable = [r for r in core if r["dimension"] == dimension and not r["excluded"]]
        valid = [r["effective_score"] for r in applicable if r["effective_score"] is not None]
        coverage = len(valid) / len(applicable) if applicable else 0
        dimensions[dimension] = {"applicable": len(applicable), "valid": len(valid), "coverage": round(coverage, 4),
                                 "score": round(sum(valid) / len(valid), 2) if valid and coverage >= rubric["dimension_min_coverage"] else None}
    total = sum(dimensions[d]["applicable"] for d in QUALITY_DIMENSIONS)
    valid_count = sum(dimensions[d]["valid"] for d in QUALITY_DIMENSIONS)
    coverage = valid_count / total if total else 0
    quality = None
    if not critical and coverage >= rubric["quality_min_coverage"] and all(dimensions[d]["score"] is not None for d in QUALITY_DIMENSIONS):
        quality = round(sum(dimensions[d]["score"] * rubric["quality_weights"][d] for d in QUALITY_DIMENSIONS) / 100, 2)
    result = {"schema_version": "1.0.0", "entity_id": snapshot["entity_id"], "cohort": snapshot["cohort"],
              "information_as_of": snapshot["information_as_of"], "computed_at": instant.isoformat().replace("+00:00", "Z"),
              "rubric_release_id": rubric["rubric_release_id"], "rubric_version": rubric["version"], "method_id": rubric["method_id"],
              "source_snapshot_sha256": expected_snapshot_sha256,
              "source_observations": sorted([{"id": r["observation_id"], "sha256": r["observation_sha256"]} for r in snapshot["records"]], key=lambda r: r["id"]),
              "dimensions": dimensions, "quality_score": quality, "quality_coverage": round(coverage, 4),
              "growth_score": dimensions["growth"]["score"], "valuation_score": dimensions["valuation"]["score"],
              "denominator": {"expected_core": 24, "quality_applicable": total, "quality_valid": valid_count},
              "critical_issues": [{"id": qid, "kind": critical[qid]} for qid in sorted(critical)],
              "unavailable_reasons": reasons, "comparison_inputs": core, "new_llm_calls": 0}
    result["derived_id"] = "derived_" + digest(result)
    return result


def compare(left_rubric, left_snapshot, right_rubric, right_snapshot, *,
            left_sha256, right_sha256, at, axis="time"):
    """Return a numerical delta only for an aligned, sufficiently covered basket."""
    if axis not in {"time", "company", "model"}:
        raise ValueError("unknown comparison axis")
    left = aggregate(left_rubric, left_snapshot, expected_snapshot_sha256=left_sha256, at=at)
    right = aggregate(right_rubric, right_snapshot, expected_snapshot_sha256=right_sha256, at=at)
    reasons = []
    if left_rubric["method_id"] != right_rubric["method_id"] or _signature(left_rubric) != _signature(right_rubric):
        reasons.append({"code": "rubric_or_method_mismatch"})
    if axis != "company" and left["entity_id"] != right["entity_id"]:
        reasons.append({"code": "issuer_mismatch"})
    if axis != "time" and left["information_as_of"] != right["information_as_of"]:
        reasons.append({"code": "information_cutoff_mismatch"})
    if axis == "time" and left["information_as_of"] > right["information_as_of"]:
        reasons.append({"code": "timeline_order_invalid"})
    for before, after in zip(left["comparison_inputs"], right["comparison_inputs"]):
        for field in AXIS_FIELDS + (() if axis == "company" else ("scope_id",)):
            if before.get(field) != after.get(field) or before.get(field) is None:
                reasons.append({"question_id": before["question_id"], "code": field + "_mismatch"})
        if before["question_id"] != after["question_id"]:
            reasons.append({"question_id": before["question_id"], "code": "question_id_mismatch"})
        if (before["effective_score"] is None) != (after["effective_score"] is None) or before["excluded"] != after["excluded"]:
            reasons.append({"question_id": before["question_id"], "code": "answered_basket_mismatch"})
    if left["quality_score"] is None or right["quality_score"] is None:
        reasons.append({"code": "quality_score_unavailable"})
    return {"status": "incomparable" if reasons else "comparable", "axis": axis, "reasons": reasons,
            "left": left, "right": right,
            "quality_delta": None if reasons else round(right["quality_score"] - left["quality_score"], 2)}


def rule_input(derived, *, expected_method_id, expected_release_id):
    """Expose a bound quality value to the existing rule AST, not a new rule engine."""
    body = {key: value for key, value in derived.items() if key != "derived_id"}
    if derived.get("derived_id") != "derived_" + digest(body):
        raise ValueError("derived content hash mismatch")
    reasons = []
    if derived["method_id"] != expected_method_id or derived["rubric_release_id"] != expected_release_id:
        reasons.append("rule_method_or_release_mismatch")
    if derived["quality_score"] is None or derived["critical_issues"]:
        reasons.append("quality_score_unavailable")
    return {"status": "unavailable" if reasons else "usable", "score": None if reasons else derived["quality_score"], "reasons": reasons}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only V02 rubric aggregation; no calls or database writes.")
    parser.add_argument("action", choices=("aggregate",))
    parser.add_argument("--rubric", required=True)
    parser.add_argument("--rubric-sha256", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--at", required=True)
    args = parser.parse_args(argv)
    try:
        rubric = load_rubric(args.rubric, expected_sha256=args.rubric_sha256, expected_release_id=args.release_id)
        snapshot = _read_bound_json(args.snapshot, args.snapshot_sha256)
        result = aggregate(rubric, snapshot, expected_snapshot_sha256=digest(snapshot), at=args.at)
    except (ValueError, TypeError, KeyError, OSError):
        print('{"status":"invalid","error_code":"scoring_rubric_input_invalid"}')
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
