"""Ask an LLM to judge module applicability, then compare with the snapshot and
the owner's adjudication ledger.

Purpose (2026-10-24): the first owner review found the hand-coded applicability
snapshot right on 9 of 10 disputed rows and wrong only on the industry axis
(CATL "battery manufacturing is obviously manufacturing", Alphabet "software").
That is a semantic judgment, not an arithmetic one — this probe measures whether
a language model reproduces the human call where the rule engine could not.

Read-only: loads the snapshot, the catalog module rules and the review ledger,
writes only its own probe outputs. Model calls go through an injected callable
so tests run offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

PROBE_SCHEMA = "applic-llm-probe/1.0.0"
APPLIES = ("yes", "no", "unsure")

PROMPT = """你是资深的权益研究分类员。请依据你对该公司的既有认知{context_line}，
判断下列每一个"问题模块"是否适用于该公司。

公司：{company}（{ticker}，{market}）

模块清单（模块id｜模块轴｜中文名｜适用条件）：
{rules}

输出严格的 JSON（不要 markdown 代码块、不要解释文字），格式：
{{"modules": {{"<模块id>": {{"applies": "yes|no|unsure", "reason": "不超过30字"}}}}}}

要求：
1. 必须覆盖上面列出的全部 {count} 个模块 id，不得增删或改名。
2. applies 只能是 yes / no / unsure 三个值之一。
3. unsure 用于你确实无法判断的模块；不要为了凑答案而猜。
4. reason 用一句中文说明依据（不超过 30 字）。"""


def load_catalog(catalog_path: Path) -> list[dict]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    modules = []
    for module in catalog.get("modules") or []:
        mid = module.get("id")
        if not isinstance(mid, str):
            continue
        modules.append(
            {
                "id": mid,
                "kind": str(module.get("kind") or ""),
                "title": str(module.get("name") or module.get("title") or ""),
                "applies_when": str(module.get("applies_when") or ""),
            }
        )
    return sorted(modules, key=lambda m: m["id"])


def build_prompt(company: dict, modules: list[dict], context: str | None) -> str:
    rules = "\n".join(
        f"- {m['id']}｜{m['kind']}｜{m['title']}｜{m['applies_when']}" for m in modules
    )
    context_line = "，以及下面给出的业务描述" if context else ""
    body = PROMPT.format(
        company=company["name"],
        ticker=company.get("ticker") or "—",
        market=company.get("market") or "—",
        rules=rules,
        count=len(modules),
        context_line=context_line,
    )
    if context:
        body = body.replace(
            f"公司：{company['name']}（{company.get('ticker') or '—'}，{company.get('market') or '—'}）",
            f"公司：{company['name']}（{company.get('ticker') or '—'}，{company.get('market') or '—'}）\n"
            f"业务描述：{context}",
        )
    return body


def snapshot_state_map(snapshot_doc: dict, entity_id: str) -> dict[str, str]:
    """Map snapshot four states onto the probe's yes/no/unsure vocabulary.

    applicable -> yes; not_applicable -> no; unknown / not_evaluated -> unsure
    (both mean "the rules could not affirm applicability").
    """
    mapping = {"applicable": "yes", "not_applicable": "no",
               "unknown": "unsure", "not_evaluated": "unsure"}
    result = {}
    for cell in snapshot_doc.get("cells") or []:
        if cell.get("entity_id") != entity_id:
            continue
        result[str(cell.get("module_id"))] = mapping.get(str(cell.get("state")), "unsure")
    return result


def ledger_implied(ledger_path: Path | None) -> dict[tuple[str, str], dict]:
    """Owner verdicts implied by the review ledger, keyed by (entity_id, module_id).

    adopt_snapshot          -> the module applies as the snapshot said (yes)
    keep_composition        -> the module applies even though the snapshot doubted it (yes)
    known_deviation         -> no applicability claim; excluded from comparison
    """
    if ledger_path is None or not ledger_path.is_file():
        return {}
    result = {}
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("decision") == "known_deviation":
            continue
        result[(record["entity_id"], record["module_id"])] = {
            "decision": record["decision"],
            "implied_applies": "yes",
            "owner_reason": record.get("owner_reason_verbatim"),
        }
    return result


def parse_answer(raw: dict, modules: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """Extract {module_id: {applies, reason}} and list missing/invalid ids."""
    modules_block = raw.get("modules") if isinstance(raw, dict) else None
    if not isinstance(modules_block, dict):
        return {}, [m["id"] for m in modules]
    parsed = {}
    missing = []
    for module in modules:
        entry = modules_block.get(module["id"])
        if not isinstance(entry, dict):
            missing.append(module["id"])
            continue
        applies = str(entry.get("applies") or "").strip().lower()
        if applies not in APPLIES:
            missing.append(module["id"])
            continue
        parsed[module["id"]] = {
            "applies": applies,
            "reason": str(entry.get("reason") or "")[:120],
        }
    return parsed, missing


def compare(company: dict, snapshot_map: dict[str, str], llm: dict[str, dict],
            owner: dict[tuple[str, str], dict]) -> dict:
    rows = []
    for module_id in sorted(snapshot_map):
        snap = snapshot_map[module_id]
        llm_row = llm.get(module_id) or {}
        llm_applies = llm_row.get("applies")
        owner_row = owner.get((company["entity_id"], module_id))
        row = {
            "module_id": module_id,
            "snapshot": snap,
            "llm": llm_applies,
            "llm_reason": llm_row.get("reason"),
            "llm_agrees_snapshot": llm_applies == snap if llm_applies else None,
        }
        if owner_row:
            row["owner_decision"] = owner_row["decision"]
            row["owner_implied_applies"] = owner_row["implied_applies"]
            row["owner_reason"] = owner_row["owner_reason"]
            row["llm_agrees_owner"] = llm_applies == owner_row["implied_applies"] if llm_applies else None
            row["snapshot_agrees_owner"] = snap == owner_row["implied_applies"]
        rows.append(row)
    adjudicated = [r for r in rows if "owner_decision" in r]
    return {
        "company": company["name"],
        "entity_id": company["entity_id"],
        "rows": rows,
        "stats": {
            "cells": len(rows),
            "llm_agree_snapshot": sum(1 for r in rows if r["llm_agrees_snapshot"]),
            "llm_disagree_snapshot": sum(1 for r in rows if r["llm_agrees_snapshot"] is False),
            "llm_unsure": sum(1 for r in rows if r["llm"] == "unsure"),
            "adjudicated_rows": len(adjudicated),
            "llm_agree_owner": sum(1 for r in adjudicated if r.get("llm_agrees_owner")),
            "snapshot_agree_owner": sum(1 for r in adjudicated if r.get("snapshot_agrees_owner")),
        },
        "adjudicated": adjudicated,
    }


def run_probe(*, companies: list[dict], snapshot_path: Path, catalog_path: Path,
              ledger_path: Path | None, out_dir: Path, model_call,
              provider: dict, context: str | None = None,
              tag: str = "A", chunk: int = 0) -> dict:
    catalog_modules = load_catalog(catalog_path)
    snapshot_doc = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    owner = ledger_implied(ledger_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    for company in companies:
        chunks = [catalog_modules]
        if chunk and chunk > 0:
            chunks = [catalog_modules[i:i + chunk] for i in range(0, len(catalog_modules), chunk)]
        parsed: dict[str, dict] = {}
        missing: list[str] = []
        errors: list[str] = []
        prompt_shas: list[str] = []
        for index, modules_slice in enumerate(chunks):
            prompt = build_prompt(company, modules_slice, context)
            prompt_shas.append(hashlib.sha256(prompt.encode("utf-8")).hexdigest())
            answer = model_call(provider, prompt, max_tokens=12000)
            (out_dir / f"prompt-{tag}-{company['entity_id']}-{index}.txt").write_text(
                prompt, encoding="utf-8")
            if isinstance(answer, dict) and answer.get("error"):
                errors.append(str(answer["error"]))
                continue
            usage = (answer or {}).get("_usage") or {}
            for key in total_usage:
                value = usage.get(key)
                if isinstance(value, int):
                    total_usage[key] += value
            parsed_slice, missing_slice = parse_answer(answer, modules_slice)
            parsed.update(parsed_slice)
            missing.extend(missing_slice)
            (out_dir / f"answer-{tag}-{company['entity_id']}-{index}.json").write_text(
                json.dumps({"_raw": answer, "_missing": missing_slice},
                           ensure_ascii=False, indent=1), encoding="utf-8")
        if errors:
            reports.append({"company": company["name"], "error": ";".join(errors),
                            "prompt_sha256": prompt_shas[0] if prompt_shas else None})
            continue
        snapshot_map = snapshot_state_map(snapshot_doc, company["entity_id"])
        report = compare(company, snapshot_map, parsed, owner)
        report["prompt_sha256"] = prompt_shas[0] if len(prompt_shas) == 1 else prompt_shas
        report["missing_modules"] = missing
        reports.append(report)
    return {
        "schema": PROBE_SCHEMA,
        "snapshot": {"path": str(snapshot_path),
                     "sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest()},
        "catalog": {"path": str(catalog_path),
                    "sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest()},
        "ledger": str(ledger_path) if ledger_path else None,
        "model": provider.get("model"),
        "context_supplied": bool(context),
        "usage": total_usage,
        "companies": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--catalog", default=str(ROOT / "questions" / "catalog.json"), type=Path)
    parser.add_argument("--ledger", default=str(ROOT / "docs" / "implementation" /
                                                "pipeline-review" / "review-pack-01.jsonl"),
                        type=Path)
    parser.add_argument("--company", required=True, action="append",
                        help="name|ticker|market|entity_id")
    parser.add_argument("--context", default=None,
                        help="可选：附给模型的业务描述（同一文本用于所有公司时会失真，建议仅单公司使用）")
    parser.add_argument("--model", default="deepseek", help="model_config route 别名")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tag", default="A")
    parser.add_argument("--chunk", type=int, default=0,
                        help="每轮询问的模块数（0=一次问全部；输出过长时用 24 分批）")
    args = parser.parse_args(argv)

    import model_config
    import thin_scan

    route = model_config.routes()[args.model]
    companies = []
    for spec in args.company:
        parts = spec.split("|")
        while len(parts) < 4:
            parts.append("")
        companies.append({"name": parts[0], "ticker": parts[1],
                          "market": parts[2], "entity_id": parts[3]})
    report = run_probe(
        companies=companies,
        snapshot_path=args.snapshot,
        catalog_path=args.catalog,
        ledger_path=args.ledger,
        out_dir=args.out,
        model_call=thin_scan.ask_model,
        provider=route,
        context=args.context,
        tag=args.tag,
        chunk=args.chunk,
    )
    (args.out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "model": report["model"],
        "context_supplied": report["context_supplied"],
        "usage": report["usage"],
        "companies": [
            {"company": c.get("company"), "error": c.get("error"),
             **({"stats": c["stats"]} if "stats" in c else {})}
            for c in report["companies"]
        ],
    }
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if all(not c.get("error") for c in report["companies"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
