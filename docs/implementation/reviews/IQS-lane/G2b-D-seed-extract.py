"""G2b D transitional seeding: extract listing/delisting dates from filing prose.

Read-only extraction (decision "D two-step" step 1 — transitional seeding):
scans company-wiki evidence_spans with STRICT include patterns for genuine
listing/delisting statements, and three negative gates: legal-entity noise
(上市規則/上市實體/上市機制), fiscal/report noise (截至X止年度/年度報告/關鍵審計...),
and windows with no listing verb at all. Output rows are UNREVIEWED
transitional seeds with full provenance (document_id, span_id, excerpt,
document title/date) plus an explicit entity-attribution flag: the window
must itself name the document's entity, otherwise entity_names stays empty
and the row is marked document_level_unverified — no silent mis-attribution.

These seeds do NOT close category D. Category D closes only on the
owner-supplied exchange-official register (HKEX/cninfo/SEC) with
source_sha256; seeds may later be cross-checked against it, never replace it.

Run: python G2b-D-seed-extract.py > G2b-D-transitional-seeding.json (stdout JSON)
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter

CATALOG = (
    "file:C:/Users/郑曾波/Projects/company-wiki/.source_catalog/catalog.sqlite3?mode=ro"
)

DATE = r"([0-9]{4})[-/年.]([0-9]{1,2})[-/月.]([0-9]{1,2})日?"

INCLUDE = [
    (
        "listed",
        re.compile(
            DATE
            + r"(?:起)?[^。；\n]{0,25}?(?:聯交所|联交所|聯合交易所|联合交易所|交易所|主板|納斯達克|纳斯达克|紐約證券交易所|纽约证券交易所)"
            + r"[^。；\n]{0,15}?上市(?!規則|則|實體|機|證券|公司|日期|紀|後|后)"
        ),
    ),
    (
        "listed",
        re.compile(
            r"(?:上市日期(?:為|为|系)?|於上市日期?|于上市日期?)\s*[:：]?\s*" + DATE
        ),
    ),
    (
        "listed",
        re.compile(
            DATE + r"[^。；\n]{0,12}?上市(?!規則|實體|機制|證券|公司|日期|後|后)"
        ),
    ),
    (
        "delisted",
        re.compile(
            r"(?:摘牌日期?|終止上市日期?|终止上市日期?|退市日期?|停止買賣|停止买卖)\s*[:：]?\s*"
            + DATE
        ),
    ),
    (
        "delisted",
        re.compile(
            DATE
            + r"[^。；\n]{0,30}?(?:摘牌|終止上市|终止上市|停止買賣|停止买卖)(?:日期)?"
        ),
    ),
    (
        "delisted",
        re.compile(r"(?:摘牌|終止上市|终止上市)[^。；\n]{0,20}?\s*[:：]?\s*" + DATE),
    ),
]
EXCLUDE = re.compile(
    r"上市規則|上市實體|上市機制|上市證券|非上市|擬上市|拟上市|"
    r"上市公司|上市日期後|上市日期后|未上市|上市事宜|上市地位|上市文件|上市活動|上市活动|招股"
)
SENT_NOISE = re.compile(
    r"截至.{0,20}止年度|年度報告|年度报告|關鍵審計|关键审计|綜合財務|合并财务|"
    r"物業及設備|物业及设备|銀行貸款|银行贷款|董事會報告|董事会报告|核數師|核数师|"
    r"審核合併|公允價值|公允价值|無形資產|无形资产"
)
LISTING_VERB = re.compile(r"上市|摘牌|終止上市|终止上市|停止買賣|停止买卖")
WINDOW = 200


def _norm_date(groups) -> str | None:
    if len(groups) >= 3 and groups[0].isdigit() and len(groups[0]) == 4:
        month, day = int(groups[1]), int(groups[2])
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{groups[0]}-{month:02d}-{day:02d}"
    return None


def main() -> int:
    con = sqlite3.connect(CATALOG, uri=True)
    con.row_factory = sqlite3.Row
    spans = con.execute(
        "SELECT span_id, document_id, raw_text FROM evidence_spans "
        "WHERE raw_text LIKE '%上市%' OR raw_text LIKE '%摘牌%' "
        "OR raw_text LIKE '%终止上市%' OR raw_text LIKE '%終止上市%'"
    ).fetchall()

    doc_entities: dict[str, list[str]] = {}
    for row in con.execute(
        "SELECT de.document_id, e.name FROM document_entities de "
        "JOIN entities e ON e.entity_id = de.entity_id"
    ):
        doc_entities.setdefault(row["document_id"], []).append(row["name"])
    doc_meta: dict[str, dict] = {}
    for row in con.execute("SELECT document_id, title, published_date FROM documents"):
        doc_meta[row["document_id"]] = {
            "document_title": row["title"],
            "published_date": row["published_date"],
        }

    rows: list[dict] = []
    seen: set[tuple] = set()
    excluded_counter: Counter = Counter()
    for span in spans:
        text = span["raw_text"] or ""
        for kind, pattern in INCLUDE:
            for match in pattern.finditer(text):
                date = _norm_date(match.groups())
                if date is None:
                    continue
                window = text[max(0, match.start() - WINDOW) : match.end() + WINDOW]
                excluded = EXCLUDE.search(window)
                if excluded is not None:
                    excluded_counter[excluded.group(0)] += 1
                    break
                if SENT_NOISE.search(window):
                    excluded_counter["fiscal_or_report_noise"] += 1
                    break
                if not LISTING_VERB.search(window):
                    excluded_counter["no_listing_verb_in_window"] += 1
                    break
                excerpt = " ".join(window.split())
                key = (kind, date, span["span_id"])
                if key in seen:
                    continue
                seen.add(key)
                doc = doc_meta.get(span["document_id"], {})
                names = sorted(set(doc_entities.get(span["document_id"], [])))
                sentence_confirmed = any(n and n in window for n in names)
                rows.append(
                    {
                        "event_type": kind,
                        "effective_from": date,
                        "document_id": span["document_id"],
                        "span_id": span["span_id"],
                        "entity_names": names if sentence_confirmed else [],
                        "entity_attribution": (
                            "sentence_confirmed"
                            if sentence_confirmed
                            else "document_level_unverified"
                        ),
                        "document_title": doc.get("document_title"),
                        "published_date": doc.get("published_date"),
                        "excerpt": excerpt[:220],
                        "source": "company-wiki.evidence_spans",
                        "confidence": "transitional_pattern_unreviewed",
                        "review_status": "unreviewed",
                        "closes_category_D": False,
                    }
                )
                break  # one row per span per kind

    con.close()
    listed = [r for r in rows if r["event_type"] == "listed"]
    delisted = [r for r in rows if r["event_type"] == "delisted"]
    companies = sorted({n for r in rows for n in r["entity_names"]})
    payload = {
        "schema": "g2b_d_transitional_seed/1",
        "purpose": (
            "transitional seeding only; category D closes ONLY on the "
            "owner-supplied exchange-official register"
        ),
        "stats": {
            "spans_scanned": len(spans),
            "listed_rows": len(listed),
            "delisted_rows": len(delisted),
            "distinct_documents": len({r["document_id"] for r in rows}),
            "distinct_entity_names_sentence_confirmed": len(companies),
            "attribution": dict(Counter(r["entity_attribution"] for r in rows)),
            "exclude_window_hits": dict(excluded_counter),
        },
        "entity_names_sample": companies[:40],
        "rows": rows,
        "closes_category_D": False,
        "next_step": (
            "owner supplies HKEX/cninfo/SEC official register (effective date + "
            "source_sha256); these seeds may be cross-checked against it but never replace it"
        ),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
