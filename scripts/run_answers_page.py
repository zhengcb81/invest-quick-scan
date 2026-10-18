"""Render a read-only page for real run answers.

Offline only; the page is a review artifact, not a score, financial conclusion,
or observation import.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{run_id} answers</title>
<style>
body{{font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:2rem;max-width:1100px;color:#1f2937}}
.banner{{background:#fef3c7;border:1px solid #f59e0b;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem}}
.card{{border:1px solid #e5e7eb;border-radius:.6rem;padding:1rem;margin:1rem 0}}
.muted{{color:#6b7280}} code{{background:#f3f4f6;padding:.1rem .3rem;border-radius:.25rem}}
li{{margin:.2rem 0}}
</style></head><body>
<h1>{run_id}</h1>
<div class="banner">真实运行答案（只读）。不是金融准确率结论；未导入 StockWiki observation。</div>
<p class="muted">回答状态统计：{statuses} · 槽位 {slot_count} · 运行 {mode}</p>
{cards}
</body></html>
"""


def render(export_dir, observation_path=None):
    export = Path(export_dir)
    run = json.loads((export / "research-run.json").read_text(encoding="utf-8"))
    observation = {}
    if observation_path and Path(observation_path).is_file():
        observation = json.loads(Path(observation_path).read_text(encoding="utf-8"))
    runtime = observation.get("runtime_summary") or {}
    cards = []
    statuses = {}
    for slot in run.get("slots", []):
        answer = slot.get("answer") or {}
        status = answer.get("status") or slot.get("execution_status")
        statuses[status] = statuses.get(status, 0) + 1
        evidence = "".join(
            "<li><a href='{url}'>{title}</a> <code>{id}</code></li>".format(
                url=html.escape(str(row.get("url"))),
                title=html.escape(str(row.get("title"))),
                id=html.escape(str(row.get("id"))),
            )
            for row in (answer.get("evidence") or [])
        )
        cards.append(
            "<div class='card'><h2>{qid} · {status}</h2>"
            "<p class='muted'>score={score} · confidence={conf} · basis={basis}</p>"
            "<p>{summary}</p>"
            "<h3>证据</h3><ul>{evidence}</ul></div>".format(
                qid=html.escape(str(slot.get("question_id"))),
                status=html.escape(str(status)),
                score=html.escape(str(answer.get("score"))),
                conf=html.escape(str(answer.get("confidence"))),
                basis=html.escape(str(answer.get("basis"))),
                summary=html.escape(str(answer.get("summary"))),
                evidence=evidence or "<li class='muted'>无</li>",
            )
        )
    return PAGE.format(
        run_id=html.escape(str(run.get("run_id"))),
        statuses=html.escape(json.dumps(statuses, ensure_ascii=False)),
        slot_count=len(run.get("slots", [])),
        mode=html.escape(str(run.get("mode", run.get("strategy_id")))),
        cards="\n".join(cards),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    page = render(args.export, args.observation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    print(json.dumps({"protocol": "iqs.run_answers_page/1.0.0", "output": str(args.output.resolve())},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
