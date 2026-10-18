"""Render read-only company profile pages from stored observations."""
from __future__ import annotations

import argparse
import html
import json
import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_WS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/c16b/native-owner-alphabet-01/owner-workspace")


def _open(path, uri=False):
    if uri:
        con = sqlite3.connect(path.resolve().as_uri()+"?mode=ro", uri=True)
    else:
        con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    return con


def owner_routed(workspace, entity_id):
    policy_path = workspace/"config/quick_scan_refresh.json"
    if not policy_path.is_file():
        return False
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return any(route.get("scope") == "entity" and route.get("scope_id") == entity_id for route in policy.get("routes", []))


def load(workspace, entity_id):
    data = workspace/"data/quick_scan"
    with closing(_open(data/"scan.sqlite", True)) as con:
        entity = dict(con.execute("SELECT entity_id, canonical_name, identity_state, identity_revision FROM quick_scan_entity WHERE entity_id=?", (entity_id,)).fetchone())
        listings = [dict(r) for r in con.execute("SELECT market, ticker, listing_status FROM quick_scan_security WHERE entity_id=?", (entity_id,))]
    observations = []
    if (data/"scan_observations.sqlite").is_file():
        with closing(_open(data/"scan_observations.sqlite", True)) as con:
            for row in con.execute("SELECT observation_id, question_id, observed_at, information_cutoff, payload_json FROM quick_scan_observation WHERE entity_id=? ORDER BY question_id", (entity_id,)):
                value = dict(row)
                value["payload"] = json.loads(value.pop("payload_json"))
                observations.append(value)
    return entity, listings, observations


def load_reviews(entity_id):
    root = Path("C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/financial-verdicts")
    found = {}
    for path in root.glob("*.json") if root.is_dir() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if value.get("entity_id") == entity_id:
            found[path.stem] = value
    return found


def _review_banner(reviews):
    if not reviews:
        return ""
    parts = []
    for key, value in reviews.items():
        caveats = ", ".join(c["id"] for c in value.get("caveats") or []) or "none"
        parts.append(f"<b>{html.escape(key)}</b>：{html.escape(str(value.get('status')))} · 事实 {value.get('facts',{}).get('supported')}/{value.get('facts',{}).get('total')} · 评分 gold {value.get('score_gold',{}).get('subjective')}/{value.get('score_gold',{}).get('full_construct')} · 保留 caveat：{html.escape(caveats)}")
    return '<div class="banner review">金融复核：' + "<br>".join(parts) + '<br><span class="muted">' + html.escape(next(iter(reviews.values())).get("boundary") or "") + "</span></div>"


def _caveat(question_id, reviews):
    notes = []
    for value in reviews.values():
        for caveat in value.get("caveats") or []:
            if caveat.get("question_id") == question_id:
                notes.append(f"{caveat.get('id')}: {caveat.get('handling')}")
    return ('<p class="caveat">' + html.escape("；".join(notes)) + "</p>") if notes else ""


def _card(obs, reviews=None):
    answer = obs["payload"].get("answer") or {}
    status = str(answer.get("status"))
    badge = "ok" if status in ("scored", "answered") else "warn"
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{} ~ {}</td><td>{}</td></tr>".format(
            html.escape(str(m.get("metric_id"))), html.escape(str(m.get("value"))),
            html.escape(str(m.get("unit")) + (" " + str(m.get("currency")) if m.get("currency") else "")),
            html.escape(str(m.get("period_start") or "-")), html.escape(str(m.get("period_end") or "-")),
            html.escape(", ".join(m.get("evidence_ids") or [])),
        )
        for m in (answer.get("metrics") or [])
    )
    evidence = "".join(
        '<li><a href="{}" target="_blank" rel="noreferrer">{}</a> <span class="muted">{} · {}</span></li>'.format(
            html.escape(str(e.get("url"))), html.escape(str(e.get("title") or e.get("id"))),
            html.escape(str(e.get("published_at") or "")), html.escape(str(e.get("id") or "")),
        )
        for e in (answer.get("evidence") or [])
    )
    execution = obs["payload"].get("execution") or {}
    search = (
        " · search-backed"
        if execution.get("search_status") == "executed" and execution.get("search_receipt_id")
        else ""
    )
    missing = answer.get("missing_fields") or []
    return f"""
<section class="card">
  <div class="head"><h2>{html.escape(str(obs['question_id']))}</h2><span class="badge {badge}">{html.escape(status)}</span></div>
  <p>{html.escape(str(answer.get('summary') or ''))}</p>
  <div class="meta">score: {html.escape(str(answer.get('score')))} · as_of: {html.escape(str(answer.get('information_as_of')))} · cutoff: {html.escape(str(obs.get('information_cutoff')))}{search}</div>
  <h3>metrics</h3><table><thead><tr><th>metric</th><th>value</th><th>unit</th><th>period</th><th>evidence</th></tr></thead><tbody>{rows or '<tr><td colspan="5" class="muted">none</td></tr>'}</tbody></table>
  <h3>evidence</h3><ul>{evidence or '<li class="muted">none</li>'}</ul>
  <h3>missing fields</h3><p class="muted">{html.escape(', '.join(map(str, missing)) or 'none')}</p>
  {_caveat(obs['question_id'], reviews or {})}
</section>"""


def build(entity, listings, observations, reviews=None, routed=False):
    if entity["identity_state"] != "verified":
        action = "需要 verified 身份"
    elif observations:
        action = "已有观察"
    elif routed:
        action = "可跑画像（owner 已路由）"
    else:
        action = "需要 owner 准入"
    return f"""<!doctype html>
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
.review{{background:#eff6ff;border-color:#bfdbfe}} .caveat{{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:8px 10px;font-size:12px;color:#991b1b}}
</style></head><body><main>
<h1>{html.escape(entity['canonical_name'])}</h1>
<div class="sub">entity {html.escape(entity['entity_id'])} · {html.escape(entity['identity_state'])} rev{html.escape(str(entity['identity_revision']))} · listings {html.escape(', '.join(f"{l['market']}:{l['ticker']}" for l in listings))} · observations {len(observations)} <a href="index.html">← all profiles</a></div>
<div class="banner">只读研究型画像：全部为 insufficient_evidence / score=null；不构成评分、投资建议或财务准确性结论。</div>
<div class="card"><b>状态</b>：{html.escape(entity['identity_state'])} · owner 路由：{"有" if routed else "无"} · 观察：{len(observations)} · 下一步：<b>{html.escape(action)}</b></div>
{_review_banner(reviews or {})}
{''.join(_card(o, reviews) for o in observations) or '<div class="card muted">暂无观察</div>'}
</main></body></html>"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--entity-id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--include-empty", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    if args.all:
        if not args.output_dir:
            parser.error("--all requires --output-dir")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        data = args.workspace/"data/quick_scan"
        if args.include_empty:
            with closing(_open(data/"scan.sqlite", True)) as con:
                ids = [r[0] for r in con.execute("SELECT entity_id FROM quick_scan_entity ORDER BY canonical_name")]
        else:
            with closing(_open(data/"scan_observations.sqlite", True)) as con:
                ids = [r[0] for r in con.execute("SELECT DISTINCT entity_id FROM quick_scan_observation ORDER BY entity_id")]
        rows = []
        for entity_id in ids:
            entity, listings, observations = load(args.workspace, entity_id)
            (args.output_dir/(entity_id + ".html")).write_text(build(entity, listings, observations, load_reviews(entity_id), owner_routed(args.workspace, entity_id)), encoding="utf-8")
            rows.append((entity["canonical_name"], entity["identity_state"], len(observations), entity_id + ".html"))
        index = "<!doctype html><html lang=\"zh\"><meta charset=\"utf-8\"><title>company profiles</title><body style=\"font:14px/1.5 'Segoe UI','Microsoft YaHei',sans-serif;max-width:900px;margin:28px auto\"><h1>公司画像</h1><p>只读研究型页面；不构成评分或投资建议。</p><table border=\"0\" cellspacing=\"0\" cellpadding=\"6\"><tr><th align=\"left\">公司</th><th align=\"left\">身份</th><th align=\"left\">观察</th></tr>" + "".join(f'<tr><td><a href="{html.escape(f)}">{html.escape(name)}</a></td><td>{html.escape(state)}</td><td>{n}</td></tr>' for name, state, n, f in rows) + "</table></body></html>"
        (args.output_dir/"index.html").write_text(index, encoding="utf-8")
        print(json.dumps({"profiles": len(rows), "output_dir": str(args.output_dir)}, ensure_ascii=False))
        return 0
    if not args.entity_id or not args.output:
        parser.error("single mode requires --entity-id and --output")
    entity, listings, observations = load(args.workspace, args.entity_id)
    args.output.write_text(build(entity, listings, observations, load_reviews(args.entity_id), owner_routed(args.workspace, args.entity_id)), encoding="utf-8")
    print(json.dumps({"entity": entity["canonical_name"], "observations": len(observations), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
