"""One-page project status from verified artifacts (read-only)."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "runs/existing-list-onboarding-2026-10-18/dashboard"
WS = ROOT / "runs/c16b/native-owner-alphabet-01/owner-workspace"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    roster = json.loads((DASH / "roster-status.json").read_text(encoding="utf-8-sig"))
    gaps = json.loads((DASH / "coverage-gaps/gaps.json").read_text(encoding="utf-8-sig"))
    fin = json.loads((DASH / "financial-check/check.json").read_text(encoding="utf-8-sig"))
    prov = json.loads((DASH / "provenance-check/check.json").read_text(encoding="utf-8-sig"))
    db = sqlite3.connect((WS / "data/quick_scan/scan_observations.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    observations = [(row[0], row[1]) for row in db.execute("SELECT question_id, import_sequence FROM quick_scan_observation ORDER BY import_sequence")]
    acceptance = sorted(p.stem for p in (ROOT / "docs/implementation/parallel-lanes/acceptance-2026-10-18").glob("*.md"))
    lines = [
        f"# 项目状态快照（{date.today().isoformat()}）",
        "",
        "由 scripts/status_report.py 从已落盘工件生成；不构成评分或投资结论。",
        "",
        "## 公司与覆盖",
        "",
        f"- 公司：{roster['entities']} 家（verified {roster['verified']}）",
        f"- 已有观察：{roster['by_next_action'].get('has_observations', 0)} 家 · search-backed {roster.get('search_backed_entities', 0)} 家 / {roster.get('search_backed_observations', 0)} 条",
        f"- 需 owner 准入：{gaps['waiting_owner_admission']} 家（subject ready {gaps.get('subject_ready', 0)}）{json.dumps(gaps['by_market'], ensure_ascii=False)}",
        "",
        "## 观察库",
        "",
        f"- 共 {len(observations)} 条：" + "、".join(f"{q}(#{seq})" for q, seq in observations),
        "",
        "## 检查",
        "",
        f"- 金融机械检查：{fin['observations']} 条 · pass {fin['mechanical_pass']} / fail {fin['mechanical_fail']}",
        f"- 引用溯源：{prov['observations']} 条 · pass {prov['pass']} / fail {prov['fail']} / research_only {prov['research_only']}",
        "",
        "## 外部包验收",
        "",
        "- " + "、".join(acceptance) if acceptance else "- 无",
        "",
        "## 关键入口",
        "",
        "- 看板：runs/existing-list-onboarding-2026-10-18/dashboard/index.html",
        "- 覆盖缺口：runs/existing-list-onboarding-2026-10-18/dashboard/coverage-gaps/index.html",
        "- scored 审阅：docs/implementation/reviews/search-scored-catl-iqs20-2026-10-18/index.html",
        "",
    ]
    text = "\n".join(lines)
    out = args.output or (ROOT / f"docs/implementation/status-{date.today().isoformat()}.md")
    out.write_text(text, encoding="utf-8")
    print(text[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
