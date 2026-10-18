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
<span class="muted">可跑画像 {status['by_next_action'].get('ready_for_profile',0)} · 已有观察 {status['by_next_action'].get('has_observations',0)} · 需要 owner 准入 {status['by_next_action'].get('needs_owner_admission',0)} · 需要 verified {status['by_next_action'].get('needs_verified_identity',0)} · 金融复核 {reviewed} 家</span></div>
<div class="card"><a href="roster.html">打开 Roster（可搜索/筛选/点公司名进画像）</a></div>
<div class="card"><a href="profiles/index.html">打开公司画像索引（{len(list(profiles.glob('ENT_*.html')))} 页）</a></div>
{facts_card}
<div class="card muted">只读页面；不构成评分、投资建议或财务准确性结论。</div>
</body></html>"""
    (args.out/"index.html").write_text(landing, encoding="utf-8")
    print(json.dumps({"out": str(args.out), "entities": status["entities"], "verified": status["verified"], "profiles": len(list(profiles.glob('ENT_*.html')))}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
