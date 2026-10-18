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
    thin_rows = []
    thin_dir = ROOT / "docs/implementation/reviews/thin-scan-2026-10-18"
    if thin_dir.is_dir():
        for directory in sorted(thin_dir.iterdir()):
            answers = directory / "answers.json"
            if not answers.is_file():
                continue
            doc = json.loads(answers.read_text(encoding="utf-8"))
            scored = [a for a in doc.get("answers", []) if a.get("status") == "scored"]
            if scored:
                avg = sum(a["score"] for a in scored) / len(scored)
                thin_rows.append((doc.get("company") or directory.name, len(scored), avg))
    thin_rows.sort(key=lambda row: -row[2])
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
        "## 薄草稿扫描（24 题）",
        "",
    ]
    if thin_rows:
        lines.append(f"- {len(thin_rows)} 家；有分题数 {sum(r[1] for r in thin_rows)}/{24 * len(thin_rows)}")
        lines.append("- 平均分（仅有分数的题）：" + "、".join(f"{n} {a:.1f}({c})" for n, c, a in thin_rows[:6]))
        lines.append("- 完整对比：docs/implementation/reviews/thin-scan-2026-10-18/compare.html")
    else:
        lines.append("- 尚无薄草稿结果")
    lines += [
        "",
        "## 外部包验收",
        "",
        "- " + "、".join(acceptance) if acceptance else "- 无",
        "",
        "## 历史阻塞（计划 v2 下已暂停）",
        "",
    ]
    blockers = []
    if not Path(r"C:/Users/郑曾波/Projects/iqs-delivery-audit-lab/docs/handoff/DELIVERY-AUDIT-11/handoff.json").is_file():
        blockers.append("DELIVERY-AUDIT-11：尚无正式 handoff.json，保持隔离")
    if not Path(r"C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab/docs/handoff/EVIDENCE-TIMELINE-11-evidence-pack.json").is_file():
        blockers.append("EVIDENCE-TIMELINE-11：evidence-pack 占位未出现，出现后需复跑 baseline/evaluate")
    blockers.append("已交付题重跑：需要 owner retry decision（owd1）与原始派发凭证，历史 attempt 不可用")
    blockers.append("第二家公司（飞亚达 000026）：subject 就绪，但缺 route decision/manifest，route-refresh 报 route_current_unavailable")
    lines.extend("- " + b for b in blockers)
    lines.append("- 计划 v2 以薄草稿为主线，上述 owner 前置件不再阻塞扫描；EVIDENCE evidence-pack 出现后仍建议复跑一次。")
    lines += [
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
