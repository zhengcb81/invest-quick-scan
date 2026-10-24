"""Run the applicability probe across several model routes and compare.

Benchmark question (2026-10-24): on the twelve rows the owner adjudicated, which
of the configured models reproduces the human call — and the snapshot's — and
where do they diverge? Reads the owner decisions export as ground truth, runs
scripts/applic_llm_probe.run_probe per (model, company), then writes a
side-by-side table.

Offline-friendly: model calls are injected; `--dry-run` builds the table from
existing report.json files without calling any model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import applic_llm_probe as probe  # noqa: E402

COMPARE_SCHEMA = "applic-llm-compare/1.0.0"


def owner_implied_from_decisions(decisions_path: Path) -> dict[tuple[str, str], dict]:
    """Owner applicability implied by the review-page export (incl. blank reasons)."""
    doc = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    result = {}
    for item in doc.get("decisions") or []:
        if item.get("decision") == "known_deviation":
            continue
        result[(item["entity_id"], item["module_id"])] = {
            "decision": item["decision"],
            "implied_applies": "yes",
            "owner_reason": item.get("reason") or "",
            "row_id": item.get("row_id"),
        }
    return result


def _cell_value(report: dict, entity_id: str, module_id: str) -> dict | None:
    for company in report.get("companies") or []:
        if company.get("entity_id") != entity_id:
            continue
        for row in company.get("rows") or []:
            if row["module_id"] == module_id:
                return row
    return None


def build_comparison(*, reports: dict[str, dict], owner: dict[tuple[str, str], dict],
                     snapshot_doc: dict) -> dict:
    rows = []
    for (entity_id, module_id), owner_row in sorted(owner.items()):
        snap = probe.snapshot_state_map(snapshot_doc, entity_id).get(module_id)
        entry = {
            "entity_id": entity_id,
            "module_id": module_id,
            "row_id": owner_row.get("row_id"),
            "owner_decision": owner_row["decision"],
            "owner_implied": owner_row["implied_applies"],
            "snapshot": snap,
            "owner_reason": owner_row.get("owner_reason") or "(未填)",
            "models": {},
        }
        for model_id, report in reports.items():
            cell = _cell_value(report, entity_id, module_id)
            if cell is None:
                entry["models"][model_id] = {"applies": None, "error": "missing"}
                continue
            entry["models"][model_id] = {
                "applies": cell.get("llm"),
                "reason": cell.get("llm_reason"),
                "agrees_owner": cell.get("llm") == owner_row["implied_applies"],
            }
        rows.append(entry)

    per_model = {}
    for model_id, report in reports.items():
        matches = sum(1 for row in rows if row["models"][model_id].get("agrees_owner"))
        errors = [row["row_id"] for row in rows
                  if row["models"][model_id].get("error")]
        company_stats = {
            c.get("company"): c.get("stats") for c in report.get("companies") or []
        }
        per_model[model_id] = {
            "model": report.get("model"),
            "usage": report.get("usage"),
            "owner_rows_matched": matches,
            "owner_rows_total": len(rows),
            "errors": errors,
            "company_stats": company_stats,
        }
    snapshot_matches = sum(1 for row in rows if row["snapshot"] == row["owner_implied"])
    return {
        "schema": COMPARE_SCHEMA,
        "rows": rows,
        "per_model": per_model,
        "snapshot_matched": snapshot_matches,
        "snapshot_total": len(rows),
    }


def render_markdown(comparison: dict, model_order: list[str]) -> str:
    rows = comparison["rows"]
    header = "| 公司 | 模块 | 你的裁定 | 快照 | " + " | ".join(model_order) + " |"
    sep = "|" + "---|" * (4 + len(model_order))
    lines = [header, sep]
    company_short = {}
    for row in rows:
        company = "宁德时代" if row["entity_id"].startswith("ENT_99ebb") else "Alphabet"
        company_short[row["entity_id"]] = company
        marks = []
        for model_id in model_order:
            cell = row["models"][model_id]
            if cell.get("error"):
                marks.append("✗")
            else:
                value = cell.get("applies")
                marks.append({("yes"): "✓", "no": "✗否", "unsure": "?"}.get(value, str(value)))
        lines.append(
            f"| {company} | {row['module_id']} | {row['owner_decision']} | {row['snapshot']} | "
            + " | ".join(marks) + " |"
        )
    lines.append("")
    lines.append("图例：✓ = 与你的裁定一致（适用）；✗否 = 判为不适用；? = 不确定；✗ = 调用失败/缺失")
    lines.append("")
    lines.append("| 模型 | 与你一致 | 调用失败行 | prompt tokens | completion tokens |")
    lines.append("|---|---|---|---|---|")
    for model_id in model_order:
        info = comparison["per_model"][model_id]
        usage = info.get("usage") or {}
        lines.append(
            f"| {model_id}（{info.get('model')}） | {info['owner_rows_matched']}/{info['owner_rows_total']} "
            f"| {', '.join(info['errors']) or '—'} | {usage.get('prompt_tokens')} | {usage.get('completion_tokens')} |"
        )
    lines.append("")
    lines.append(f"快照本身与你一致的行数：{comparison['snapshot_matched']}/{comparison['snapshot_total']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--catalog", default=str(ROOT / "questions" / "catalog.json"), type=Path)
    parser.add_argument("--decisions", required=True, type=Path,
                        help="复核页导出的 decisions.json（含全部裁定行）")
    parser.add_argument("--company", required=True, action="append",
                        help="name|ticker|market|entity_id")
    parser.add_argument("--model", required=True, action="append",
                        help="model_config route 别名，可重复")
    parser.add_argument("--chunk", type=int, default=24)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true",
                        help="不调用模型，读取既有 report.json 生成对照")
    args = parser.parse_args(argv)

    companies = []
    for spec in args.company:
        parts = spec.split("|")
        while len(parts) < 4:
            parts.append("")
        companies.append({"name": parts[0], "ticker": parts[1],
                          "market": parts[2], "entity_id": parts[3]})

    snapshot_doc = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    owner = owner_implied_from_decisions(args.decisions)
    args.out.mkdir(parents=True, exist_ok=True)
    reports: dict[str, dict] = {}

    if args.dry_run:
        for model_id in args.model:
            path = args.out / f"report-{model_id}.json"
            if path.is_file():
                reports[model_id] = json.loads(path.read_text(encoding="utf-8"))
    else:
        import model_config
        import thin_scan
        routes = model_config.routes()
        for model_id in args.model:
            route = routes[model_id]
            report = probe.run_probe(
                companies=companies, snapshot_path=args.snapshot,
                catalog_path=args.catalog, ledger_path=None,
                out_dir=args.out / model_id, model_call=thin_scan.ask_model,
                provider=route, tag=model_id, chunk=args.chunk,
            )
            (args.out / f"report-{model_id}.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            reports[model_id] = report

    comparison = build_comparison(reports=reports, owner=owner, snapshot_doc=snapshot_doc)
    (args.out / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = render_markdown(comparison, args.model)
    (args.out / "comparison.md").write_text(markdown, encoding="utf-8")
    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
