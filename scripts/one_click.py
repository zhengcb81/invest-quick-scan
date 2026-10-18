"""One-click local dashboard: roster + every company profile page."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/郑曾波/Projects/invest-quick-scan")
SCRIPTS = ROOT/"scripts"
DEFAULT_WS = ROOT/"runs/c16b/native-owner-alphabet-01/owner-workspace"
DEFAULT_LINKS = ROOT/"runs/existing-list-onboarding-2026-10-18/candidate-links.json"


def run(args):
    done = subprocess.run([sys.executable, "-B", "-X", "utf8", *map(str, args)], cwd=str(ROOT), capture_output=True)
    if done.returncode != 0:
        raise SystemExit("step failed: " + " ".join(map(str, args)) + "\n" + done.stderr.decode("utf8", "replace")[:600])
    return done.stdout.decode("utf8", "replace").strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--out", type=Path, default=ROOT/"runs/existing-list-onboarding-2026-10-18/dashboard")
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    profiles = args.out/"profiles"
    run([SCRIPTS/"profile_page.py", "--workspace", args.workspace, "--all", "--include-empty", "--output-dir", profiles])
    run([SCRIPTS/"roster_status.py", "--workspace", args.workspace, "--profiles-dir", profiles,
         "--profiles-prefix", "profiles", "--links", args.links,
         "--html", args.out/"roster.html", "--json", args.out/"roster-status.json"])
    status = json.loads((args.out/"roster-status.json").read_text(encoding="utf-8"))
    gaps_dir = args.out/"coverage-gaps"
    run([SCRIPTS/"coverage_gaps.py", "--roster", args.out/"roster-status.json",
         "--json", gaps_dir/"gaps.json", "--html", gaps_dir/"index.html",
         "--subjects", args.workspace/"data/quick_scan/analysis_subjects.sqlite"])
    gaps = json.loads((gaps_dir/"gaps.json").read_text(encoding="utf-8"))
    gaps_card = ('<div class="card"><a href="coverage-gaps/index.html">覆盖缺口：verified 但缺 owner 路由（'
                 + str(gaps.get("waiting_owner_admission", 0)) + ' 家 · subject ready ' + str(gaps.get("subject_ready", 0)) + ' · '
                 + json.dumps(gaps.get("by_market", {}), ensure_ascii=False) + '）</a><br><span class="muted">'
                 + '只读清单；准入仍需 owner/route 工作</span></div>')
    fin_dir = args.out/"financial-check"
    fin_dir.mkdir(parents=True, exist_ok=True)
    run([SCRIPTS/"financial_mechanical_check.py", "--workspace", args.workspace,
         "--json", fin_dir/"check.json", "--html", fin_dir/"check.html"])
    fin = json.loads((fin_dir/"check.json").read_text(encoding="utf-8"))
    prov_dir = args.out/"provenance-check"
    prov_dir.mkdir(parents=True, exist_ok=True)
    run([SCRIPTS/"observation_provenance_check.py", "--json", prov_dir/"check.json", "--html", prov_dir/"check.html"])
    prov = json.loads((prov_dir/"check.json").read_text(encoding="utf-8"))
    prov_card = ('<div class="card"><a href="provenance-check/check.html">Search 引用溯源（'
                 + str(prov.get("observations", 0)) + ' 条观察 · pass ' + str(prov.get("pass", 0))
                 + ' · fail ' + str(prov.get("fail", 0)) + ' · research_only ' + str(prov.get("research_only", 0))
                 + '）</a><br><span class="muted">搜索型观察的引用 URL 必须在授权它的 retreival receipt 中</span></div>')
    answer_pages = sorted(ROOT.glob("docs/implementation/reviews/**/answers.html"))
    scored_pages = sorted(ROOT.glob("docs/implementation/reviews/search-scored-*/index.html"))
    scored_card = ""
    if scored_pages:
        import os
        links = "".join(
            '<li><a href="' + os.path.relpath(page, args.out).replace("\\", "/") + '">'
            + page.parent.name + "</a></li>"
            for page in scored_pages
        )
        scored_card = ('<div class="card"><b>Search-backed 评分审阅（未入库，' + str(len(scored_pages))
                       + '）</b><ul>' + links + '</ul><span class="muted">离线校验通过但未进入 owner 观察库</span></div>')
    answers_card = ""
    if answer_pages:
        import os
        links = "".join(
            '<li><a href="' + os.path.relpath(page, args.out).replace("\\", "/") + '">'
            + page.parent.name + '</a></li>'
            for page in answer_pages
        )
        answers_card = ('<div class="card"><b>Search-backed 答案页（' + str(len(answer_pages)) + '）</b>'
                        + '<ul>' + links + '</ul></div>')
    fin_card = ('<div class="card"><a href="financial-check/check.html">金融机械检查（'
                + str(fin.get("observations", 0)) + ' 条观察 · pass ' + str(fin.get("mechanical_pass", 0))
                + ' / fail ' + str(fin.get("mechanical_fail", 0)) + '）</a><br><span class="muted">'
                + '只做结构/单位/期间/引用一致性；不是金融准确性或投资结论</span></div>')
    verdicts_dir = ROOT/"docs/implementation/reviews/financial-verdicts"
    reviewed = len(list(verdicts_dir.glob("*.json"))) if verdicts_dir.is_dir() else 0
    sys.path.insert(0, str(SCRIPTS))
    import facts_registry
    packs = facts_registry.discover(ROOT/"docs/implementation/reviews")
    facts_index = ROOT/"docs/implementation/reviews/facts-packs-index.html"
    facts_card = ""
    if packs:
        import os
        href = os.path.relpath(facts_index, args.out).replace("\\", "/")
        valid = sum(1 for item in packs if facts_registry.facts_pack_check.check(item["pack"])["status"] == "valid")
        facts_card = ('<div class="card"><a href="' + href + '">Facts packs（' + str(len(packs)) + ' 个 draft，' + str(valid) + ' 个 valid）</a></div>')
    landing = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>invest-quick-scan dashboard</title>
<style>body{{font:15px/1.6 "Segoe UI","Microsoft YaHei",sans-serif;max-width:820px;margin:40px auto;color:#1f2328}}
h1{{font-size:22px;margin:0 0 6px}}.muted{{color:#6b7280}}.card{{border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:12px 0}}
a{{color:#1d4ed8;text-decoration:none}}a:hover{{text-decoration:underline}}</style></head><body>
<h1>invest-quick-scan</h1>
<div class="muted">现有公司列表的本地只读看板 · 生成于 {status.get('protocol','')}</div>
<div class="card"><b>{status['entities']}</b> 家公司 · <b>{status['verified']}</b> verified · <b>{status['provisional']}</b> provisional<br>
<span class="muted">可跑画像 {status['by_next_action'].get('ready_for_profile',0)} · 已有观察 {status['by_next_action'].get('has_observations',0)} · search-backed {status.get('search_backed_entities',0)} 家/{status.get('search_backed_observations',0)} 条 · 需要 owner 准入 {status['by_next_action'].get('needs_owner_admission',0)} · 需要 verified {status['by_next_action'].get('needs_verified_identity',0)} · 金融复核 {reviewed} 家</span></div>
<div class="card"><a href="roster.html">打开 Roster（可搜索/筛选/点公司名进画像）</a></div>
<div class="card"><a href="profiles/index.html">打开公司画像索引（{len(list(profiles.glob('ENT_*.html')))} 页）</a></div>
{facts_card}
    {fin_card}
    {gaps_card}
    {prov_card}
    {answers_card}
    {scored_card}
<div class="card muted">只读页面；不构成评分、投资建议或财务准确性结论。</div>
</body></html>"""
    (args.out/"index.html").write_text(landing, encoding="utf-8")
    print(json.dumps({"out": str(args.out), "entities": status["entities"], "verified": status["verified"], "profiles": len(list(profiles.glob('ENT_*.html')))}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
