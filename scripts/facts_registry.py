"""Render a registry page for generated facts packs.

Offline only. Lists draft and validated packs with their review pages; it never
registers a pack or implies an owner admission.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import facts_pack_check

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Facts packs</title>
<style>
body{{font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:2rem;color:#1f2937}}
.banner{{background:#eff6ff;border:1px solid #3b82f6;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{border:1px solid #e5e7eb;padding:.5rem;text-align:left;vertical-align:top}}
th{{background:#f9fafb}}
code{{background:#f3f4f6;padding:.1rem .3rem;border-radius:.25rem}}
</style></head><body>
<h1>Facts packs</h1>
<div class="banner">只读索引：列出已生成的 facts pack；DRAFT 表示分类或口径尚未获 owner 确认，不代表可运行。</div>
<table><thead><tr><th>Company</th><th>Mode</th><th>Questions</th><th>Check</th><th>Profile</th><th>Review</th></tr></thead><tbody>
{rows}
</tbody></table>
<p>生成：python scripts/facts_registry.py --root docs/implementation/reviews --output docs/implementation/reviews/facts-packs-index.html</p>
</body></html>
"""


def discover(root):
    root = Path(root)
    packs = []
    for manifest in sorted(root.glob("**/facts-pack-*/manifest.json")):
        pack = manifest.parent
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        packs.append(
            dict(
                pack=pack,
                company=str((data.get("profile") or {}).get("company") or pack.parent.name),
                mode=data.get("mode"),
                count=len(data.get("questions") or []),
                review=pack.parent / "facts-pack-review.html",
                profile=pack.parent / "profile.draft.json",
            )
        )
    return packs


def render(root, base_dir=None):
    import os

    base = Path(base_dir or ".").resolve()
    rows = []
    for item in discover(root):
        checked = facts_pack_check.check(item["pack"])
        review = item["review"]
        if review.is_file() and review.parent == item["pack"].parent:
            link = os.path.relpath(review, base).replace("\\", "/")
            review_cell = '<a href="{}">review</a>'.format(html.escape(link))
        else:
            review_cell = "-"
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(item["company"]),
                html.escape(str(item["mode"])),
                item["count"],
                html.escape(checked["status"]),
                "DRAFT" if item["profile"].is_file() else "-",
                review_cell,
            )
        )
    return PAGE.format(rows="\n".join(rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("docs/implementation/reviews"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    args.output.write_text(render(args.root, base_dir=args.output.parent), encoding="utf-8")
    print(json.dumps({"protocol": "iqs.facts_registry/1.0.0", "packs": len(discover(args.root)),
                      "output": str(args.output.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
