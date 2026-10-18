"""Read-only roster status for the existing company list.

Shows every onboarded entity with its identity state, listing and observation
count, and the next action an operator must take. Never writes.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

DEFAULT_WS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/c16b/native-owner-alphabet-01/owner-workspace")
DEFAULT_LINKS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/existing-list-onboarding-2026-10-18/candidate-links.json")


def connect(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def render_html(summary):
    data = json.dumps(summary, ensure_ascii=False).replace("</", "<\\/")
    template = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>invest-quick-scan roster</title>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1f2328;--muted:#6b7280;--line:#e5e7eb;--ok:#0f766e;--warn:#b45309;--info:#1d4ed8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--muted);margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card b{display:block;font-size:24px}.card span{color:var(--muted);font-size:12px}
.toolbar{display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap}
input,select{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:220px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{position:sticky;top:0;background:#f3f4f6;font-size:12px;color:var(--muted)}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid}
.ok{color:var(--ok);border-color:#99f6e4;background:#f0fdfa}
.warn{color:var(--warn);border-color:#fde68a;background:#fffbeb}
.info{color:var(--info);border-color:#bfdbfe;background:#eff6ff}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px;color:var(--muted)}
footer{color:var(--muted);font-size:12px;margin-top:14px}
</style>
</head>
<body><main>
<h1>invest-quick-scan · 现有公司列表 Roster</h1>
<div class="sub" id="generated"></div>
<div class="cards" id="cards"></div>
<div class="toolbar">
  <input id="q" placeholder="搜索公司名 / ticker / entity id">
  <select id="state"><option value="">全部状态</option><option value="verified">verified</option><option value="provisional">provisional</option></select>
  <select id="action"><option value="">全部下一步</option><option value="needs_verified_identity">需要 verified</option><option value="needs_owner_admission">需要 owner 准入</option><option value="ready_for_profile">可跑画像</option><option value="has_observations">已有观察</option></select>
</div>
<table><thead><tr><th>公司</th><th>身份</th><th>上市地</th><th>观察</th><th>下一步</th><th>entity id</th></tr></thead><tbody id="rows"></tbody></table>
<div id="candidates"></div>
<footer>只读快照；不判断答案质量，不授予评分资格。</footer>
</main>
<script>
const data = __DATA__;
document.getElementById('generated').textContent = 'source: ' + data.workspace + ' · generated: ' + new Date().toISOString();
const cards = [
  ['实体', data.entities], ['verified', data.verified], ['provisional', data.provisional],
  ['CN / US / HK', (data.by_market.CN||0)+' / '+(data.by_market.US||0)+' / '+(data.by_market.HK||0)]
];
if (data.candidates) cards.push(['候选 linked / total', (data.candidates.linked||0)+' / '+(data.candidates.total||0)]);
document.getElementById('cards').innerHTML = cards.map(([k,v]) => '<div class="card"><b>'+v+'</b><span>'+k+'</span></div>').join('');
const badge = (a) => {
  if (a === 'has_observations') return '<span class="badge ok">已有观察</span>';
  if (a === 'ready_for_profile') return '<span class="badge info">可跑画像</span>';
  if (a === 'needs_owner_admission') return '<span class="badge warn">需要 owner 准入</span>';
  return '<span class="badge warn">需要 verified</span>';
};
const render = () => {
  const q = document.getElementById('q').value.toLowerCase();
  const st = document.getElementById('state').value;
  const ac = document.getElementById('action').value;
  const rows = data.rows.filter(r =>
    (!q || r.name.toLowerCase().includes(q) || r.entity_id.toLowerCase().includes(q) || r.listings.some(l => (l.ticker||'').toLowerCase().includes(q)))
    && (!st || r.identity_state === st) && (!ac || r.next_action === ac));
  document.getElementById('rows').innerHTML = rows.map(r =>
    '<tr><td>'+r.name+'</td><td>'+r.identity_state+'</td><td>'+r.listings.map(l => l.market+':'+l.ticker).join(', ')+'</td><td>'+r.observations+'</td><td>'+badge(r.next_action)+'</td><td class="mono">'+r.entity_id+'</td></tr>'
  ).join('');
};
['q','state','action'].forEach(id => document.getElementById(id).addEventListener('input', render));
render();
if (data.candidates && (data.candidates.unresolved_rows||[]).length) {
  const rows = data.candidates.unresolved_rows.map(r =>
    '<tr><td class="mono">'+r.listing_key+'</td><td>'+r.reason+'</td></tr>').join('');
  document.getElementById('candidates').innerHTML =
    '<h3 style="font-size:15px;margin:18px 0 8px">未解决候选（'+data.candidates.unresolved+'）</h3>'+
    '<table><thead><tr><th>listing_key</th><th>原因</th></tr></thead><tbody>'+rows+'</tbody></table>';
}
</script>
</body></html>"""
    return template.replace("__DATA__", data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--html", type=Path, default=None)
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    args = parser.parse_args(argv)
    scan = args.workspace/"data/quick_scan/scan.sqlite"
    observations = args.workspace/"data/quick_scan/scan_observations.sqlite"
    with closing(connect(scan)) as connection:
        entities = [dict(row) for row in connection.execute(
            "SELECT entity_id, canonical_name, identity_state, identity_revision FROM quick_scan_entity ORDER BY canonical_name"
        )]
        securities = [dict(row) for row in connection.execute(
            "SELECT security_id, entity_id, market, ticker, listing_status FROM quick_scan_security"
        )]
        bindings = [dict(row) for row in connection.execute(
            "SELECT binding_ref, entity_id, source_namespace FROM quick_scan_source_binding"
        )]
    by_entity = {}
    for row in securities:
        by_entity.setdefault(row["entity_id"], []).append(row)
    binding_count = Counter(row["entity_id"] for row in bindings)
    policy_path = args.workspace/"config/quick_scan_refresh.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.is_file() else {}
    routed = {route.get("scope_id") for route in policy.get("routes", []) if route.get("scope") == "entity"}
    observed = Counter()
    if observations.is_file():
        with closing(connect(observations)) as connection:
            for row in connection.execute("SELECT entity_id FROM quick_scan_observation"):
                observed[row["entity_id"]] += 1
    rows = []
    for entity in entities:
        listings = by_entity.get(entity["entity_id"], [])
        verified = entity["identity_state"] == "verified"
        if not verified:
            action = "needs_verified_identity"
        elif observed.get(entity["entity_id"], 0):
            action = "has_observations"
        elif entity["entity_id"] in routed:
            action = "ready_for_profile"
        else:
            action = "needs_owner_admission"
        rows.append({
            "entity_id": entity["entity_id"],
            "name": entity["canonical_name"],
            "identity_state": entity["identity_state"],
            "identity_revision": entity["identity_revision"],
            "listings": [{"market": l["market"], "ticker": l["ticker"], "status": l["listing_status"]} for l in listings],
            "bindings": binding_count.get(entity["entity_id"], 0),
            "observations": observed.get(entity["entity_id"], 0),
            "next_action": action,
        })
    candidates = None
    if args.links.is_file():
        try:
            report = json.loads(args.links.read_text(encoding="utf-8"))
            candidates = {
                "total": report.get("candidate_count"),
                "linked": report.get("linked"),
                "unresolved": report.get("unresolved"),
                "unresolved_rows": report.get("unresolved_rows", []),
            }
        except (OSError, ValueError):
            candidates = None
    summary = {
        "protocol": "iqs.roster-status/1.0.0",
        "workspace": str(args.workspace),
        "entities": len(rows),
        "verified": sum(1 for r in rows if r["identity_state"] == "verified"),
        "provisional": sum(1 for r in rows if r["identity_state"] == "provisional"),
        "by_market": dict(Counter(l["market"] for r in rows for l in r["listings"])),
        "by_next_action": dict(Counter(r["next_action"] for r in rows)),
        "candidates": candidates,
        "rows": rows,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(payload, encoding="utf-8")
    if args.html:
        args.html.write_text(render_html(summary), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("entities", "verified", "provisional", "by_market", "by_next_action")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
