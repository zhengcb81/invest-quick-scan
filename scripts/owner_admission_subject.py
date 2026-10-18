"""Build (and optionally import) the owner admission subject for a verified company."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import uuid
from contextlib import closing
from pathlib import Path

ROOT = Path("C:/Users/郑曾波/Projects/invest-quick-scan")
STOCKWIKI = Path("C:/Users/郑曾波/Projects/StockWiki")
DEFAULT_OUT = ROOT/"runs/existing-list-onboarding-2026-10-18/subjects"
AT = "2026-10-18T10:00:00Z"
ENV = {
    "SYSTEMROOT": "C:\\Windows", "PATH": "C:\\Windows\\System32;C:\\Miniconda",
    "PATHEXT": ".COM;.EXE;.BAT;.CMD", "COMSPEC": "C:\\Windows\\System32\\cmd.exe",
    "PYTHONPATH": str(STOCKWIKI), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
}


def uuid4_from(text):
    return str(uuid.UUID(bytes=hashlib.sha256(text.encode()).digest()[:16], version=4))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--scope-as-of", default="2025-12-31T00:00:00Z")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    scan = args.workspace/"data/quick_scan/scan.sqlite"
    with closing(sqlite3.connect(scan.resolve().as_uri()+"?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        row = dict(con.execute(
            "SELECT e.entity_id, e.canonical_name, e.identity_state, e.verified_issuer_receipt_id, s.ticker, s.security_id, "
            "(SELECT source_record_id FROM quick_scan_source_binding b WHERE b.entity_id=e.entity_id LIMIT 1) AS source_record_id "
            "FROM quick_scan_entity e JOIN quick_scan_security s USING(entity_id) WHERE s.ticker=?",
            (args.ticker,),
        ).fetchone())
    if row["identity_state"] != "verified":
        raise SystemExit("entity is not verified: " + args.ticker)
    sys.path.insert(0, str(STOCKWIKI))
    from stockwiki.quick_scan_analysis import perimeter_sha256, validate_subject
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore

    org_id = row.get("source_record_id") or ""
    evidence_url = "https://www.cninfo.com.cn/new/disclosure/stock?stockCode=" + args.ticker
    if org_id:
        evidence_url += "&orgId=" + org_id
    asj = "ASJ_" + uuid4_from("iqs:entity:" + row["entity_id"])
    subject = {
        "analysis_subject_schema_version": "1.0.0",
        "analysis_subject_id": asj,
        "analysis_subject_revision": 1,
        "display_name": row["canonical_name"] + " FY2025 reporting group (subsidiaries not enumerated)",
        "primary_issuer_id": row["entity_id"],
        "anchor_listing_id": None,
        "scope_kind": "consolidated_reporting_group",
        "scope_as_of": args.scope_as_of,
        "perimeter_coverage": "not_enumerated",
        "memberships": [{"entity_id": row["entity_id"], "role": "primary_issuer", "valid_from": None, "valid_to": None, "evidence_ref": evidence_url}],
    }
    sha = perimeter_sha256(subject)
    receipt = {
        "analysis_subject_id": asj, "analysis_subject_revision": 1,
        "decision_ref": "owner-2026-10-18-controller-" + args.ticker + "-fy2025-perimeter-not-enumerated",
        "evidence_ref": evidence_url, "perimeter_sha256": sha, "primary_issuer_id": row["entity_id"],
        "receipt_id": "PRC_" + hashlib.sha256(("iqs:receipt:" + asj).encode()).hexdigest()[:32],
        "recorded_at": AT, "status": "verified",
    }
    payload = {"analysis_subject": subject, "perimeter_receipt": receipt}
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out/(args.ticker + ".json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    validate_subject(subject, identity_store=QuickScanStore(WorkspacePaths.from_root(args.workspace)))
    result = {"ticker": args.ticker, "analysis_subject_id": asj, "perimeter_sha256": sha, "payload": str(path), "applied": False}
    if args.apply:
        done = subprocess.run([sys.executable, "-B", "-m", "stockwiki.cli", "--root", str(args.workspace),
                               "analysis-subject-import", "--file", str(path), "--at", AT],
                              env=ENV, cwd=str(STOCKWIKI), capture_output=True)
        result["applied"] = done.returncode == 0
        result["import_stdout"] = done.stdout.decode("utf8")[:600]
        if done.returncode != 0:
            raise SystemExit("subject import failed: " + done.stderr.decode("utf8")[:400])
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
