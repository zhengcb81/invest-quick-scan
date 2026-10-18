"""Render a read-only facts pack review page.

Offline only. The page is a review artifact, never an authorization or a score.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import facts_pack_check

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{title} — facts pack</title>
<style>
body{{font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:2rem;color:#1f2937}}
.banner{{background:#fef3c7;border:1px solid #f59e0b;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{border:1px solid #e5e7eb;padding:.5rem;vertical-align:top;text-align:left}}
th{{background:#f9fafb}}
code{{background:#f3f4f6;padding:.1rem .3rem;border-radius:.25rem}}
.status-valid{{color:#047857;font-weight:600}}
.status-rejected{{color:#b91c1c;font-weight:600}}
</style></head><body>
<h1>{title} — facts pack review</h1>
<div class="banner">DRAFT / 只读：这是事实题清单，不是评分、不是运行授权。分类与运行仍需 owner 确认。</div>
<p>目录：<code>{directory}</code></p>
<p>校验：<span class="status-{status}">{status}</span>；题目数：{count}；模式：{mode}；模板：{template}</p>
<table><thead><tr><th>#</th><th>ID</th><th>Field</th><th>Priority</th><th>Prompt</th><th>Relations</th><th>Max items</th></tr></thead><tbody>
{rows}
</tbody></table>
<h2>source_sha256</h2><ul>{sources}</ul>
</body></html>
"""


def render(pack_dir):
    pack = Path(pack_dir)
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    checked = facts_pack_check.check(pack)
    rows = []
    for index, question in enumerate(manifest.get("questions", []), 1):
        rows.append(
            "<tr><td>{}</td><td><code>{}</code></td><td><code>{}</code></td><td>{}</td>"
            "<td>{}</td><td>{}</td><td>{}</td></tr>".format(
                index,
                html.escape(str(question.get("id"))),
                html.escape(str(question.get("field_id"))),
                question.get("priority"),
                html.escape(str(question.get("prompt"))),
                html.escape(", ".join(question.get("relations") or [])),
                question.get("max_items"),
            )
        )
    sources = "".join(
        "<li><code>{}</code> {}</li>".format(html.escape(rel), html.escape(str(sha)))
        for rel, sha in (manifest.get("source_sha256") or {}).items()
    )
    return PAGE.format(
        title=html.escape(str((manifest.get("profile") or {}).get("company") or pack.name)),
        directory=html.escape(str(pack.resolve())),
        status=checked["status"],
        count=checked["question_count"],
        mode=html.escape(str(checked["mode"])),
        template=html.escape(str(checked["template_version"])),
        rows="\n".join(rows),
        sources=sources,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    page = render(args.pack)
    args.output.write_text(page, encoding="utf-8")
    print(json.dumps({"protocol": "iqs.facts_pack_page/1.0.0", "output": str(args.output.resolve()),
                      "status": "rendered"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
