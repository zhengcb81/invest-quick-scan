"""Build an owner-review pack from pipeline cross-check results.

Route B of PIPELINE-AUDIT-17: compositions stay hand-written, the applicability
snapshot acts as validator, and the owner adjudicates each disagreement. This
tool turns cross-check output into a self-contained review page the owner opens
locally (file://, zero dependencies, zero network), clicks a decision per row,
and exports a decisions file that scripts/pipeline_review_apply.py ingests.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import applic_pipeline_check as apc  # noqa: E402

PACK_SCHEMA = "pipeline-review-pack/1.0.0"

CATEGORY_LABELS = {
    "snapshot_applicable_not_composed": "快照适用，组装未选",
    "composed_but_not_applicable": "组装已选，快照不适用/不可判",
    "composed_module_missing_in_snapshot": "模块 ID 未对齐",
}

DECISIONS = ("adopt_snapshot", "keep_composition", "known_deviation")
DECISION_LABELS = {
    "adopt_snapshot": "采纳快照（改组装）",
    "keep_composition": "保留组装（人工优先）",
    "known_deviation": "记录为已知偏差",
}


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_applicable(snapshot_doc: dict, entity_id: str) -> list[str]:
    return sorted(
        str(cell.get("module_id"))
        for cell in snapshot_doc.get("cells") or []
        if cell.get("entity_id") == entity_id and cell.get("state") == "applicable"
    )


def build_pack(manifest_paths: list[Path], snapshot_path: Path, out_dir: Path) -> dict:
    snapshot_doc = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    companies: list[dict] = []
    rows: list[dict] = []
    index = 0
    for manifest_path in manifest_paths:
        code, result = apc.compare(manifest_path, snapshot_path)
        if code == 3 or result.get("status") == "data_error":
            raise SystemExit(f"manifest failed cross-check: {manifest_path} ({result.get('error')})")
        identity = result["manifest_identity"]
        entity_id = identity["entity_id"]
        section_rows = []
        for disagreement in result["disagreements"] + result["unaligned"]:
            index += 1
            section_rows.append(
                {
                    "row_id": f"R{index:03d}",
                    "module_id": disagreement["module_id"],
                    "category": disagreement["category"],
                    "category_label": CATEGORY_LABELS.get(
                        disagreement["category"], disagreement["category"]
                    ),
                    "snapshot_state": disagreement.get("snapshot_state"),
                    "basis_kind": disagreement.get("basis_kind"),
                    "reason": disagreement.get("reason")
                    or "组装选择了快照没有该模块轴的 ID（ID 级不匹配，非判定分歧）",
                }
            )
        companies.append(
            {
                "company": identity.get("company") or entity_id,
                "entity_id": entity_id,
                "as_of": identity.get("as_of"),
                "manifest_path": str(manifest_path),
                "manifest_sha256": result["manifest_sha256"],
                "composed_modules": _composed_modules(manifest_path),
                "snapshot_applicable": _snapshot_applicable(snapshot_doc, entity_id),
                "profile_fields": identity.get("profile_fields") or {},
                "summary": result["summary"],
                "rows": section_rows,
            }
        )
        rows.extend(section_rows)
    pack = {
        "schema": PACK_SCHEMA,
        "pack_id": f"review-{out_dir.name}",
        "created_at_utc": _utcnow(),
        "snapshot": {
            "path": str(snapshot_path),
            "sha256": _sha256_file(snapshot_path),
            "snapshot_id": snapshot_doc.get("snapshot_id"),
            "inputs": snapshot_doc.get("inputs") or {},
        },
        "decision_options": [
            {"value": value, "label": DECISION_LABELS[value]} for value in DECISIONS
        ],
        "companies": companies,
        "row_count": len(rows),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pack.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    html = _render_html(pack, out_dir)
    (out_dir / "review.html").write_text(html, encoding="utf-8")
    return pack


def _composed_modules(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    return list(manifest.get("modules") or [])


_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>管线差异复核 __PACK_ID__</title>
<style>
  :root { --green:#1f9d55; --amber:#b8860b; --gray:#9aa0a6; --blue:#2563eb; --red:#c0392b; --ink:#1a1a1a; --bg:#f6f7f9; }
  * { box-sizing:border-box; }
  body { font-family:"Segoe UI","Microsoft YaHei",sans-serif; margin:0; background:var(--bg); color:var(--ink); }
  header { background:#fff; border-bottom:1px solid #e2e4e8; padding:20px 28px; }
  h1 { font-size:20px; margin:0 0 6px; }
  .meta { font-size:13px; color:#555; }
  .meta code { background:#eef0f3; padding:1px 6px; border-radius:3px; }
  .steps { margin-top:10px; font-size:13px; color:#333; line-height:1.7; }
  main { max-width:1100px; margin:0 auto; padding:24px 28px 80px; }
  section.company { background:#fff; border:1px solid #e2e4e8; border-radius:8px; margin-bottom:22px; }
  .co-head { padding:14px 20px; border-bottom:1px solid #eef0f3; display:flex; flex-wrap:wrap; gap:10px 24px; align-items:baseline; }
  .co-head h2 { font-size:17px; margin:0; }
  .co-stats { font-size:12.5px; color:#555; }
  .co-stats b { color:var(--ink); }
  table { width:100%; border-collapse:collapse; font-size:13.5px; }
  th { text-align:left; font-size:12px; color:#777; font-weight:600; padding:10px 14px; border-bottom:1px solid #eef0f3; }
  td { padding:12px 14px; border-bottom:1px solid #f2f3f5; vertical-align:top; }
  tr:last-child td { border-bottom:none; }
  .chip { display:inline-block; padding:2px 9px; border-radius:10px; font-size:12px; color:#fff; }
  .chip.snapshot_applicable_not_composed { background:var(--blue); }
  .chip.composed_but_not_applicable { background:var(--red); }
  .chip.composed_module_missing_in_snapshot { background:var(--gray); }
  .state { font-weight:600; }
  .state.applicable { color:var(--green); }
  .state.unknown { color:var(--amber); }
  .state.not_applicable { color:#888; text-decoration:line-through; }
  details.reason { margin-top:6px; }
  details.reason summary { cursor:pointer; color:var(--blue); font-size:12.5px; }
  details.reason div { margin-top:6px; padding:8px 10px; background:#f8f9fa; border-left:3px solid var(--gray); font-size:12.5px; color:#444; white-space:pre-wrap; }
  .decision { display:flex; flex-direction:column; gap:6px; }
  .decision label { display:flex; gap:6px; align-items:center; font-size:13px; cursor:pointer; }
  .decision input[type=radio] { accent-color:var(--blue); }
  .decision label.opt-adopt_snapshot input { accent-color:var(--blue); }
  .decision label.opt-keep_composition input { accent-color:var(--green); }
  .decision label.opt-known_deviation input { accent-color:var(--amber); }
  textarea.reason-input { width:100%; min-height:44px; font:inherit; font-size:12.5px; padding:6px 8px; border:1px solid #d8dade; border-radius:4px; resize:vertical; }
  textarea.reason-input.missing { border-color:var(--red); }
  .row-missing { outline:2px solid var(--red); outline-offset:-2px; }
  .modules { font-size:12.5px; color:#555; padding:10px 20px; background:#fafbfc; border-bottom:1px solid #eef0f3; }
  .modules code { background:#eef0f3; padding:1px 5px; border-radius:3px; margin:1px; display:inline-block; }
  footer { position:fixed; bottom:0; left:0; right:0; background:#fff; border-top:1px solid #e2e4e8; padding:12px 28px; display:flex; gap:14px; align-items:center; flex-wrap:wrap; }
  footer .count { font-size:13px; color:#555; }
  button { font:inherit; font-size:14px; padding:8px 18px; border:none; border-radius:6px; cursor:pointer; }
  button.primary { background:var(--blue); color:#fff; }
  button.ghost { background:#eef0f3; color:var(--ink); }
  #status { font-size:13px; color:var(--green); }
  #status.err { color:var(--red); }
</style>
</head>
<body>
<header>
  <h1>管线差异复核 <span style="color:var(--gray)">__PACK_ID__</span></h1>
  <div class="meta">快照 <code>__SNAPSHOT_ID__</code>（sha256 <code>__SNAPSHOT_SHA8__</code>）× 组装 manifest —— 每条差异请给一项裁定与一句理由</div>
  <div class="steps">① 逐行选择裁定并填理由 → ② 点「导出 decisions.json」（保存到 <code>__DECISIONS_PATH__</code>）→ ③ 告诉 agent 跑 <code>__APPLY_CMD__</code></div>
</header>
<main id="main"></main>
<footer>
  <span class="count" id="count"></span>
  <button class="primary" id="export">导出 decisions.json</button>
  <button class="ghost" id="copy">复制 JSON 到剪贴板</button>
  <span id="status"></span>
</footer>
<script>
const PACK = __PACK_JSON__;
const DECISIONS = PACK.decision_options;
const state = {};  // row_id -> {decision, reason}
function chip(category) {
  return `<span class="chip ${category}">${categoryLabel(category)}</span>`;
}
function categoryLabel(c) {
  return ({'snapshot_applicable_not_composed':'快照适用，组装未选','composed_but_not_applicable':'组装已选，快照不适用','composed_module_missing_in_snapshot':'模块 ID 未对齐'})[c] || c;
}
function stateSpan(s) {
  if (!s) return '<span style="color:#999">—（无轴）</span>';
  return `<span class="state ${s}">${s}</span>`;
}
function render() {
  const main = document.getElementById('main');
  main.innerHTML = PACK.companies.map(co => `
    <section class="company">
      <div class="co-head">
        <h2>${co.company}</h2>
        <span class="co-stats">组装 <b>${co.composed_modules.length}</b> 模块 · 快照适用 <b>${co.snapshot_applicable.length}</b> 模块 · 一致 <b>${co.summary.agree||0}</b> · 差异 <b>${co.rows.length}</b></span>
        <span class="co-stats">as_of ${co.as_of || '—'}</span>
      </div>
      <div class="modules"><b>组装：</b>${co.composed_modules.map(m=>`<code>${m}</code>`).join('')}<br><b>快照适用：</b>${co.snapshot_applicable.map(m=>`<code>${m}</code>`).join('')}</div>
      <table>
        <tr><th style="width:16%">模块</th><th style="width:20%">差异</th><th style="width:24%">快照判定与依据</th><th style="width:40%">你的裁定（必填理由）</th></tr>
        ${co.rows.map(r => `
          <tr data-row="${r.row_id}">
            <td><b>${r.module_id}</b><div style="font-size:11px;color:#999">${r.row_id}</div></td>
            <td>${chip(r.category)}</td>
            <td>${stateSpan(r.snapshot_state)}${r.basis_kind?`<div style="font-size:12px;color:#777">${r.basis_kind}</div>`:''}
              <details class="reason"><summary>依据原文</summary><div>${(r.reason||'').replace(/</g,'<')}</div></details></td>
            <td><div class="decision" data-decision="${r.row_id}">
              ${DECISIONS.map(d=>`<label class="opt-${d.value}"><input type="radio" name="d-${r.row_id}" value="${d.value}"> ${d.label}</label>`).join('')}
              <textarea class="reason-input" data-reason="${r.row_id}" placeholder="一句理由（必填，原样入台账）"></textarea>
            </div></td>
          </tr>`).join('')}
      </table>
    </section>`).join('');
  bind();
}
function bind() {
  document.querySelectorAll('input[type=radio]').forEach(el => el.addEventListener('change', () => {
    const id = el.name.slice(2);
    state[id] = state[id] || {};
    state[id].decision = el.value;
    updateCount();
  }));
  document.querySelectorAll('textarea.reason-input').forEach(el => el.addEventListener('input', () => {
    const id = el.dataset.reason;
    state[id] = state[id] || {};
    state[id].reason = el.value;
    el.classList.remove('missing');
  }));
  document.getElementById('export').addEventListener('click', exportDecisions);
  document.getElementById('copy').addEventListener('click', copyDecisions);
  updateCount();
}
function missing() {
  const miss = [];
  for (const co of PACK.companies) for (const r of co.rows) {
    const s = state[r.row_id];
    if (!s || !s.decision) miss.push({id:r.row_id, why:'未选裁定'});
    else if (!s.reason || !s.reason.trim()) miss.push({id:r.row_id, why:'未填理由'});
  }
  return miss;
}
function updateCount() {
  const total = PACK.row_count, done = Object.values(state).filter(s=>s.decision&&s.reason&&s.reason.trim()).length;
  document.getElementById('count').textContent = `已完整裁定 ${done}/${total}`;
}
function setStatus(msg, err) { const el=document.getElementById('status'); el.textContent=msg; el.className=err?'err':''; }
function decisionsJSON() {
  const ds = [];
  for (const co of PACK.companies) for (const r of co.rows) {
    const s = state[r.row_id] || {};
    ds.push({row_id:r.row_id, module_id:r.module_id, entity_id:co.entity_id, category:r.category, decision:s.decision||null, reason:(s.reason||'').trim()});
  }
  return {schema:'pipeline-review-decisions/1.0.0', pack_id:PACK.pack_id, exported_at:new Date().toISOString(), decisions:ds};
}
function exportDecisions() {
  const miss = missing();
  if (miss.length) {
    setStatus(`还有 ${miss.length} 行未完成（先选裁定、再填理由）`, true);
    document.querySelectorAll('tr[data-row]').forEach(tr=>tr.classList.remove('row-missing'));
    miss.forEach(m => document.querySelector(`tr[data-row="${m.id}"]`).classList.add('row-missing'));
    document.querySelector(`tr[data-row="${miss[0].id}"]`).scrollIntoView({behavior:'smooth', block:'center'});
    return;
  }
  const blob = new Blob([JSON.stringify(decisionsJSON(), null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'decisions.json';
  a.click();
  setStatus('已导出 decisions.json —— 请保存到上方给出的目录，然后通知 agent');
}
function copyDecisions() {
  navigator.clipboard.writeText(JSON.stringify(decisionsJSON(), null, 2))
    .then(()=>setStatus('JSON 已复制到剪贴板'))
    .catch(()=>setStatus('复制失败，请用导出按钮', true));
}
render();
</script>
</body>
</html>
"""


def _render_html(pack: dict, out_dir: Path) -> str:
    html = _HTML
    replacements = {
        "__PACK_ID__": pack["pack_id"],
        "__SNAPSHOT_ID__": str(pack["snapshot"]["snapshot_id"]),
        "__SNAPSHOT_SHA8__": pack["snapshot"]["sha256"][:8],
        "__DECISIONS_PATH__": str((out_dir / "decisions.json").resolve()),
        "__APPLY_CMD__": (
            f"python -B -X utf8 scripts\\pipeline_review_apply.py --pack {out_dir.resolve()}"
        ),
        "__PACK_JSON__": json.dumps(pack, ensure_ascii=False),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    return html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, action="append", type=Path,
                        help="composed manifest（可重复传入多家公司）")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    pack = build_pack(args.manifest, args.snapshot, args.out)
    summary = {
        "pack_id": pack["pack_id"],
        "pack_path": str(args.out / "pack.json"),
        "review_html": str(args.out / "review.html"),
        "companies": len(pack["companies"]),
        "row_count": pack["row_count"],
    }
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
