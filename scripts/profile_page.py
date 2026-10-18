"""Render a read-only company profile page from stored observations."""
from __future__ import annotations

import argparse
import html
import json
import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_WS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/c16b/native-owner-alphabet-01/owner-workspace")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    data = args.workspace/"data/quick_scan"
    with closing(sqlite3.connect((data/"scan.sqlite").resolve().as_uri()+"?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        entity = dict(con.execute("SELECT entity_id, canonical_name, identity_state, identity_revision FROM quick_scan_entity WHERE entity_id=?", (args.entity_id,)).fetchone())
        listings = [dict(r) for r in con.execute("SELECT market, ticker, listing_status FROM quick_scan_security WHERE entity_id=?", (args.entity_id,))]
    observations = []
    with closing(sqlite3.connect((data/"scan_observations.sqlite").resolve().as_uri()+"?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        for row in con.execute("SELECT observation_id, question_id, observed_at, information_cutoff, payload_json FROM quick_scan_observation WHERE entity_id=? ORDER BY question_id", (args.entity_id,)):
            value = dict(row)
            value["payload"] = json.loads(value.pop("payload_json"))
            observations.append(value)
    cards = []
    for obs in observations:
        answer = obs["payload"].get("answer") or {}
        status = answer.get("status")
        badge = "ok" if status in ("scored", "answered") else "warn"
        metrics = answer.get("metrics") or []
        metric_rows = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{} ~ {}</td><td>{}</td></tr>".format(
                html.escape(str(m.get("metric_id"))),
                html.escape(str(m.get("value"))),
                html.escape(str(m.get("unit")) + (" " + str(m.get("currency")) if m.get("currency") else "")),
                html.escape(str(m.get("period_start") or "-")),
                html.escape(str(m.get("period_end") or "-")),
                html.escape(", ".join(m.get("evidence_ids") or [])),
            )
            for m in metrics
        )
        evidence = answer.get("evidence") or []
        evidence_items = "".join(
            '<li><a href="{}" target="_blank" rel="noreferrer">{}</a> <span class="muted">{} · {}</span></li>'.format(
                html.escape(str(e.get("url"))), html.escape(str(e.get("title") or e.get("id"))),
                html.escape(str(e.get("published_at") or "")), html.escape(str(e.get("id") or "")),
            )
            for e in evidence
        )
        missing = answer.get("missing_fields") or []
        cards.append(f"""
<section class="card">
  <div class="head"><h2>{html.escape(str(obs['question_id']))}</h2><span class="badge {badge}">{html.escape(str(status))}</span></div>
  <p>{html.escape(str(answer.get('summary') or ''))}</p>
  <div class="meta">score: {html.escape(str(answer.get('score')))} · as_of: {html.escape(str(answer.get('information_as_of')))} · cutoff: {html.escape(str(obs.get('information_cutoff')))}</div>
  <h3>metrics</h3><table><thead><tr><th>metric</th><th>value</th><th>unit</th><th>period</th><th>evidence</th></tr></thead><tbody>{metric_rows or '<tr><td colspan="5" class="muted">none</td></tr>'}</tbody></table>
  <h3>evidence</h3><ul>{evidence_items or '<li class="muted">none</li>'}</ul>
  <h3>missing fields</h3><p class="muted">{html.escape(', '.join(map(str, missing)) or 'none')}</p>
</section>""")
    page = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>{html.escape(entity['canonical_name'])} quick-scan profile</title>
<style>
body{{margin:0;background:#f7f8fa;color:#1f2328;font:14px/1.55 "Segoe UI","Microsoft YaHei",sans-serif}}
main{{max-width:980px;margin:0 auto;padding:28px}}
h1{{font-size:22px;margin:0 0 6px}} h2{{font-size:16px;margin:0}} h3{{font-size:13px;margin:16px 0 6px;color:#6b7280}}
.sub{{color:#6b7280;margin-bottom:18px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:14px}}
.head{{display:flex;align-items:center;gap:10px;justify-content:space-between}}
.badge{{padding:2px 10px;border-radius:999px;font-size:12px;border:1px solid}} .ok{{color:#0f766e;border-color:#99f6e4;background:#f0fdfa}} .warn{{color:#b45309;border-color:#fde68a;background:#fffbeb}}
.meta{{color:#6b7280;font-size:12px;margin:6px 0}}
table{{width:100%;border-collapse:collapse;margin:6px 0}} th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #eef0f2;vertical-align:top}} th{{color:#6b7280;font-size:12px}}
.muted{{color:#6b7280}} .banner{{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 12px;margin-bottom:16px;font-size:13px}}
</style></head><body><main>
<h1>{html.escape(entity['canonical_name'])}</h1>
<div class="sub">entity {html.escape(entity['entity_id'])} · {html.escape(entity['identity_state'])} rev{html.escape(str(entity['identity_revision']))} · listings {html.escape(', '.join(f"{l['market']}:{l['ticker']}" for l in listings))} · observations {len(observations)}</div>
<div class="banner">只读研究型画像：全部为 insufficient_evidence / score=null；不构成评分、投资建议或财务准确性结论。</div>
{''.join(cards) or '<div class="card muted">暂无观察</div>'}
</main></body></html>"""
    args.output.write_text(page, encoding="utf-8")
    print(json.dumps({"entity": entity["canonical_name"], "observations": len(observations), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
