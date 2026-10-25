"""Build a cross-company thin-scan comparison page and copy artifacts."""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

NAMES = {
    "thin-scan-catl-2026-10-18": "宁德时代",
    "thin-scan-000026-2026-10-18": "飞亚达",
    "thin-scan-alphabet-2026-10-18": "Alphabet",
    "thin-scan-vanke-2026-10-18": "万科",
    "thin-scan-wanhua-2026-10-18": "万华化学",
    "thin-scan-pingan-2026-10-18": "中国平安",
    "thin-scan-amec-2026-10-18": "中微公司",
    "thin-scan-microsoft-2026-10-18": "微软",
    "thin-scan-moutai-2026-10-18": "贵州茅台",
    "thin-scan-wuxi-2026-10-18": "药明康德",
    "thin-scan-gree-2026-10-18": "格力电器",
    "thin-scan-yili-2026-10-18": "伊利股份",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    companies = []
    for directory in sorted(args.runs.glob("thin-scan-*-2026-10-18")):
        answers_path = directory / "answers.json"
        if not answers_path.is_file() or "-retest-" in directory.name:
            continue
        document = json.loads(answers_path.read_text(encoding="utf-8"))
        slug = directory.name
        companies.append({"slug": slug, "name": NAMES.get(slug, document.get("company") or slug),
                          "doc": document})
        target = args.out / slug
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(answers_path, target / "answers.json")
        if (directory / "index.html").is_file():
            shutil.copyfile(directory / "index.html", target / "index.html")
    from thin_scan import default_basic_questions
    import question_sets
    basic = default_basic_questions()
    _, modules = question_sets.load_library()
    aggregate_ids = {q['id'] for q in basic if q.get('aggregation') != 'diagnostic'}
    dimension_of = {q['id']: q['dimension'] for module in modules.values() for q in module['questions']}

    def core_answer(answer):
        if answer.get('comparison_role') == 'diagnostic' or answer.get('aggregation') == 'diagnostic':
            return False
        return answer.get('core', answer['question_id'] in aggregate_ids)
    dimension_order = []
    for q in basic:
        if q["dimension"] not in dimension_order:
            dimension_order.append(q["dimension"])
    questions = {}
    for company in companies:
        for answer in company["doc"]["answers"]:
            questions.setdefault(answer["question_id"], answer["question"])
    header = "".join(f"<th>{html.escape(c['name'])}</th>" for c in companies)
    rows = []
    for qid in sorted(questions):
        cells = []
        for company in companies:
            answer = next((a for a in company["doc"]["answers"] if a["question_id"] == qid), None)
            if answer is None:
                cells.append("<td>-</td>")
            elif answer["status"] == "scored":
                cells.append(f"<td class='s'>{answer['score']}</td>")
            else:
                cells.append("<td class='i'>不足</td>")
        rows.append(f"<tr><td>{html.escape(qid)}<br><span class='q'>{html.escape(questions[qid])}</span></td>{''.join(cells)}</tr>")
    summary = []
    for company in companies:
        answers = company["doc"]["answers"]
        scored = [a for a in answers if a["status"] == "scored"]
        aggregate_scored = [a for a in scored if core_answer(a)]
        average = sum(a["score"] for a in aggregate_scored) / len(aggregate_scored) if aggregate_scored else None
        cost = company["doc"]["meta"]["cost_micros"] / 1_000_000
        summary.append(
            "<tr><td>{}</td><td>{}/{}</td><td>{}</td><td>{}</td><td><a href='{}/index.html'>页面</a></td></tr>".format(
                html.escape(company["name"]), len(scored), len(answers),
                "—" if average is None else f"{average:.1f}",
                "$" + f"{cost:.4f}", company["slug"]))
    dimension_rows = []
    for dimension in dimension_order:
        cells = []
        for company in companies:
            values = [a["score"] for a in company["doc"]["answers"]
                      if a["status"] == "scored" and core_answer(a)
                      and dimension_of.get(a["question_id"]) == dimension]
            cells.append("-" if not values else f"{sum(values)/len(values):.1f}")
        dimension_rows.append(f"<tr><td>{html.escape(dimension)}</td>{''.join('<td>'+c+'</td>' for c in cells)}</tr>")
    dimension_table = ("<table><tr><th>维度</th>" + "".join(f"<th>{html.escape(c['name'])}</th>" for c in companies)
                       + "</tr>" + "".join(dimension_rows) + "</table>")
    page = """<!doctype html><html lang="zh"><meta charset="utf-8"><title>薄草稿对比</title>
<style>body{font:14px/1.6 system-ui,"Microsoft YaHei";max-width:1100px;margin:32px auto;padding:0 16px}
table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:6px 8px;text-align:left;vertical-align:top}
.q{color:#6b7280;font-size:12px}.s{color:#0f766e;font-weight:600}.i{color:#b45309}.warn{background:#fffbeb;border:1px solid #fde68a;padding:10px 12px;border-radius:8px}</style>
<h1>薄草稿对比</h1>
<p class="warn">草稿，非正式入账；分数只用于先看方向，不构成投资建议。</p>
<h2>公司汇总</h2><table><tr><th>公司</th><th>已评分</th><th>核心题草稿均分</th><th>搜索成本</th><th>详情</th></tr>__SUMMARY__</table>
<h2>核心维度均分（不含专题与诊断题）</h2>__DIMENSIONS__
<h2>逐题</h2><table><tr><th>问题</th>__HEADER__</tr>__ROWS__</table>
</body></html>"""
    page = (page.replace("__SUMMARY__", "".join(summary))
                .replace("__HEADER__", header)
                .replace("__ROWS__", "".join(rows))
                .replace("__DIMENSIONS__", dimension_table))
    (args.out / "compare.html").write_text(page, encoding="utf-8")
    print(json.dumps({"companies": [c["name"] for c in companies], "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
