"""Audit verified identities against the archived per-company evidence."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path("C:/Users/郑曾波/Projects/invest-quick-scan")
WS = ROOT/"runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan"
EVIDENCE = ROOT/"docs/implementation/evidence/verified-identity-2026-10-18"
OUT = ROOT/"runs/existing-list-onboarding-2026-10-18/verified-evidence-audit.json"
PRE_EXISTING = {"Alphabet Inc.", "宁德时代新能源科技股份有限公司"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def norm(value):
    text = unicodedata.normalize("NFKC", str(value or ""))
    return "".join(text.split()).upper()


def load(path):
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            value = json.loads(line)
            rows[value["ticker"]] = value
    return rows


cninfo = load(EVIDENCE/"cninfo-profiles.jsonl")
sec = load(EVIDENCE/"sec-profiles.jsonl")
sec_bodies = {path.stem: path.read_bytes() for path in (EVIDENCE/"sec-submissions").glob("*.json")}

with closing(sqlite3.connect((WS/"scan.sqlite").resolve().as_uri()+"?mode=ro", uri=True)) as con:
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    rows = [dict(r) for r in con.execute(
        """SELECT e.entity_id, e.canonical_name, e.identity_state, e.identity_revision, e.verified_issuer_receipt_id,
                  s.ticker, (SELECT source_record_id FROM quick_scan_source_binding b WHERE b.entity_id=e.entity_id LIMIT 1) AS source_record_id,
                  (SELECT source_canonical_name FROM quick_scan_source_binding b WHERE b.entity_id=e.entity_id LIMIT 1) AS short_name
           FROM quick_scan_entity e JOIN quick_scan_security s USING(entity_id) WHERE e.identity_state='verified'"""
    )]
with closing(sqlite3.connect((WS/"identity_receipts.sqlite").resolve().as_uri()+"?mode=ro", uri=True)) as con:
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    receipts = {}
    for r in con.execute("SELECT receipt_id, kind, entity_id, identity_revision, receipt_json FROM identity_receipt"):
        value = dict(r)
        try:
            body = json.loads(value.get("receipt_json") or "{}")
        except ValueError:
            body = {}
        value["evidence_ref"] = body.get("evidence_ref")
        value["decision_ref"] = body.get("decision_ref")
        receipts[value["receipt_id"]] = value
entities = {}
for row in rows:
    entities.setdefault(row["entity_id"], row)

results = []
for row in entities.values():
    ticker = row["ticker"]
    name = row["canonical_name"]
    ivr = row["verified_issuer_receipt_id"] or ""
    entry = {"ticker": ticker, "entity_id": row["entity_id"], "name": name, "ivr": ivr, "checks": []}
    if name in PRE_EXISTING:
        receipt = receipts.get(ivr) or {}
        entry["status"] = "pre_existing_source"
        entry["checks"].append({"name": "archived_here", "ok": False,
                                "detail": "verified before this archive; earlier owner approval/IVR"})
        entry["evidence_ref"] = receipt.get("evidence_ref")
        entry["receipt_kind"] = receipt.get("kind")
        results.append(entry)
        continue
    if ticker == "000002":
        expected = "IVR_" + hashlib.sha256(("verified:" + row["entity_id"] + ":2:" + name).encode()).hexdigest()[:32]
        entry["checks"].append({"name": "ivr_recompute", "ok": expected == ivr})
        payload = ROOT/"runs/existing-list-onboarding-2026-10-18/payloads-verified-pilot/CN-A_000002.verified.json"
        if payload.is_file():
            value = json.loads(payload.read_text(encoding="utf-8"))
            url = value["issuer_receipt"]["evidence_ref"]
            query = parse_qs(urlparse(url).query)
            entry["checks"].append({"name": "evidence_url", "ok": url.startswith("https://disc.static.szse.cn/"), "detail": url})
            entry["checks"].append({"name": "url_stock_code", "ok": query.get("stockCode") is None or query.get("stockCode") == ["000002"], "detail": str(query)})
        entry["status"] = "passed" if all(c["ok"] for c in entry["checks"]) else "failed"
        results.append(entry)
        continue
    if ticker in cninfo:
        evidence = cninfo[ticker]
        body = evidence["response"]
        sha = hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()
        entry["checks"].append({"name": "evidence_sha", "ok": sha == evidence["sha256"]})
        entry["checks"].append({"name": "legal_name", "ok": body.get("公司名称") == name, "detail": body.get("公司名称")})
        entry["checks"].append({"name": "code_match", "ok": body.get("A股代码") == ticker, "detail": body.get("A股代码")})
        entry["checks"].append({"name": "org_match", "ok": evidence.get("org_id") == row.get("source_record_id"),
                                "detail": evidence.get("org_id") + " vs " + str(row.get("source_record_id"))})
        entry["checks"].append({"name": "name_gate", "ok": evidence.get("name_gate") in {"equal", "contains"},
                                "detail": evidence.get("name_gate") + ": " + str(evidence.get("official_short")) + " vs " + str(row.get("short_name"))})
        expected = "IVR_" + hashlib.sha256(("cninfo:" + row["entity_id"] + ":" + name).encode()).hexdigest()[:32]
        entry["checks"].append({"name": "ivr_recompute", "ok": expected == ivr})
    elif ticker in sec:
        evidence = sec[ticker]
        body = sec_bodies.get(ticker)
        entry["checks"].append({"name": "evidence_sha", "ok": body is not None and hashlib.sha256(body).hexdigest() == evidence["sha256"]})
        value = json.loads(body) if body else {}
        entry["checks"].append({"name": "legal_name", "ok": value.get("name") == name, "detail": value.get("name")})
        entry["checks"].append({"name": "ticker_listed", "ok": ticker in (value.get("tickers") or [])})
        expected = "IVR_" + hashlib.sha256(("sec:" + row["entity_id"] + ":" + name).encode()).hexdigest()[:32]
        entry["checks"].append({"name": "ivr_recompute", "ok": expected == ivr})
    else:
        entry["status"] = "failed"
        entry["checks"].append({"name": "evidence_present", "ok": False, "detail": "no archived evidence"})
        results.append(entry)
        continue
    entry["status"] = "passed" if all(c["ok"] for c in entry["checks"]) else "failed"
    results.append(entry)

raw_diff = sum(1 for row in cninfo.values() if str(row.get("official_short")) != str(row.get("short_name")))
summary = {
    "protocol": "iqs.verified-evidence-audit/1.0.0",
    "verified_entities": len(results),
    "passed": sum(1 for r in results if r["status"] == "passed"),
    "failed": sum(1 for r in results if r["status"] == "failed"),
    "pre_existing_source": sum(1 for r in results if r["status"] == "pre_existing_source"),
    "cninfo_rows": len(cninfo),
    "cninfo_official_short_coverage": sum(1 for row in cninfo.values() if row.get("official_short")),
    "cninfo_raw_short_diff": raw_diff,
    "failures": [r for r in results if r["status"] == "failed"],
    "note": "identity audit only; not financial accuracy or scoring eligibility",
}
OUT.write_text(json.dumps({**summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: summary[k] for k in ("verified_entities", "passed", "failed", "pre_existing_source", "cninfo_rows", "cninfo_official_short_coverage", "cninfo_raw_short_diff")}, ensure_ascii=False))
for r in summary["failures"][:8]:
    print("FAIL", r["ticker"], r["name"], [c for c in r["checks"] if not c["ok"]])
