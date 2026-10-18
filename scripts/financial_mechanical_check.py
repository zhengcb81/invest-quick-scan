"""Deterministic mechanical checks for financial answers.

This is NOT a financial review and grants no accuracy verdict. It only checks
structure, score/status consistency, metric units/periods/cutoff, evidence URLs
and bindings, and reports what a human review still has to judge.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

DEFAULT_WS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/c16b/native-owner-alphabet-01/owner-workspace")
URL_RE = re.compile(r"^https://[^\s]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BASES = {"current", "trailing", "normalized", "stress", "forward", "not_applicable"}


def parse_date(value):
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def check_answer(observation):
    findings = []
    answer = observation.get("answer") or {}
    cutoff = observation.get("information_cutoff")
    cutoff_date = parse_date(cutoff)

    def fail(code, detail):
        findings.append({"code": code, "detail": detail})

    if answer.get("question_id") != observation.get("question_id"):
        fail("question_mismatch", "answer.question_id != observation.question_id")
    status = answer.get("status")
    score = answer.get("score")
    if status == "scored":
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 10:
            fail("score_invalid", "scored answer needs an integer score 1..10")
    elif score is not None:
        fail("score_on_unscored", "non-scored answer must keep score null")
    if answer.get("response_kind") == "fact" and (score is not None or answer.get("items")):
        fail("fact_contract", "fact answer must not use score or items")
    as_of = parse_date(answer.get("information_as_of"))
    if as_of is not None and cutoff_date is not None and as_of > cutoff_date:
        fail("information_after_cutoff", "information_as_of exceeds cutoff")
    period_start = parse_date(answer.get("period_start"))
    period_end = parse_date(answer.get("period_end"))
    if period_start and period_end and period_start > period_end:
        fail("reversed_period", "period_start > period_end")
    if period_end and cutoff_date and period_end > cutoff_date:
        fail("period_after_cutoff", "period_end exceeds cutoff")

    evidence = answer.get("evidence") or []
    evidence_ids = []
    for item in evidence:
        eid = item.get("id")
        if not isinstance(eid, str) or not eid:
            fail("evidence_id_missing", "evidence without id")
            continue
        evidence_ids.append(eid)
        if not URL_RE.fullmatch(str(item.get("url") or "")):
            fail("evidence_url_invalid", eid)
        published = parse_date(item.get("published_at"))
        if item.get("published_at") and published is None:
            fail("evidence_date_invalid", eid)
        if published and cutoff_date and published > cutoff_date:
            fail("evidence_after_cutoff", eid)
        if not str(item.get("title") or "").strip():
            fail("evidence_title_missing", eid)
    if len(evidence_ids) != len(set(evidence_ids)):
        fail("evidence_duplicate", "duplicate evidence id")
    known = set(evidence_ids)

    metrics = answer.get("metrics") or []
    metric_ids = []
    for metric in metrics:
        mid = metric.get("metric_id")
        if not isinstance(mid, str) or not mid:
            fail("metric_id_missing", "metric without id")
            continue
        metric_ids.append(mid)
        if metric.get("basis") not in BASES:
            fail("metric_basis_invalid", mid)
        value = metric.get("value")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            fail("metric_value_invalid", mid)
        if metric.get("unit") == "currency" and not (metric.get("currency") or "").strip():
            fail("metric_currency_missing", mid)
        if metric.get("unit") == "ratio" and metric.get("currency") is not None:
            fail("metric_ratio_currency", mid)
        m_start = parse_date(metric.get("period_start"))
        m_end = parse_date(metric.get("period_end"))
        if m_start and m_end and m_start > m_end:
            fail("metric_reversed_period", mid)
        if m_end and cutoff_date and m_end > cutoff_date:
            fail("metric_period_after_cutoff", mid)
        refs = metric.get("evidence_ids") or []
        if not refs:
            fail("metric_evidence_missing", mid)
        elif not set(refs) <= known:
            fail("metric_evidence_unknown", mid)
        if not str(metric.get("definition") or "").strip():
            fail("metric_definition_missing", mid)
    if len(metric_ids) != len(set(metric_ids)):
        fail("metric_duplicate", "duplicate metric id inside one answer")
    return {
        "observation_id": observation.get("observation_id"),
        "question_id": observation.get("question_id"),
        "entity_id": observation.get("entity_id"),
        "status": status,
        "score": score,
        "metrics": len(metrics),
        "evidence": len(evidence),
        "missing_fields": len(answer.get("missing_fields") or []),
        "findings": findings,
        "mechanical_pass": not findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--html", type=Path, default=None)
    args = parser.parse_args(argv)
    database = args.workspace/"data/quick_scan/scan_observations.sqlite"
    if not database.is_file():
        raise SystemExit("observations store missing: " + str(database))
    results = []
    with closing(sqlite3.connect(database.resolve().as_uri()+"?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        for row in connection.execute("SELECT observation_id, payload_json FROM quick_scan_observation ORDER BY observation_id"):
            results.append(check_answer(json.loads(row["payload_json"])))
    summary = {
        "protocol": "iqs.financial-mechanical-check/1.0.0",
        "workspace": str(args.workspace),
        "observations": len(results),
        "mechanical_pass": sum(1 for r in results if r["mechanical_pass"]),
        "mechanical_fail": sum(1 for r in results if not r["mechanical_pass"]),
        "declared_limits": [
            "not a financial review; no accuracy, rating or investment conclusion",
            "does not judge source adequacy, missing disclosure or counter-evidence quality",
            "human review still owns sufficiency and any score",
        ],
        "results": results,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(payload, encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("observations", "mechanical_pass", "mechanical_fail")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
