"""Thin draft scan: ask a question set for one company with web search.

Draft only: no owner admission, no receipts, no observation import. Every scored
answer must cite URLs that came back from the actual search call; otherwise the
answer is recorded as insufficient_evidence. Providers are tried in the order
declared in docs/implementation/thin-scan-providers.json (cost/quality ranking),
with no budget-approval gate.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ROOT / "docs/implementation/thin-scan-providers.json"
USD_MICROS = 1_000_000


def post_json(url: str, key: str, body: dict, timeout: float) -> tuple[int, dict]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            payload = {"error": raw.decode("utf-8", "replace")[:500]}
        return error.code, payload


def search(provider: dict, query: str, count: int) -> list[dict]:
    key = os.environ.get(provider["key_env"], "")
    status, payload = post_json(provider["endpoint"], key, {"query": query, "count": count, "need_content": False}, 30)
    if status != 200 or not isinstance(payload, dict):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    out = []
    for item in results:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not (isinstance(url, str) and url.startswith("https://")):
            continue
        out.append({
            "url": url,
            "title": item.get("title") or "",
            "summary": item.get("summary") or item.get("snippet") or "",
            "date": item.get("date") or "",
            "site": item.get("site_name") or "",
        })
    return out


def ask_model(provider: dict, company: str, question: str, sources: list[dict]) -> dict:
    key = os.environ.get(provider["key_env"], "")
    source_text = "\n".join(
        f"[{i+1}] {s['title']}\nURL: {s['url']}\n日期: {s['date']}\n摘要: {s['summary'][:300]}"
        for i, s in enumerate(sources)
    ) or "（本次没有检索到可用来源）"
    prompt = (
        "你是严谨的公司研究员。只根据下面给出的检索结果回答，不要使用记忆补充事实。\n"
        "如果证据不足，必须返回 insufficient_evidence，不要猜分数。\n\n"
        f"公司：{company}\n问题：{question}\n信息截止：2026-10-18\n\n"
        f"检索结果：\n{source_text}\n\n"
        "只输出一个 JSON 对象，不要 markdown，不要解释。格式：\n"
        '{"status":"scored" 或 "insufficient_evidence","score":1-10 的整数或 null,'
        '"summary":"不超过120字的结论","evidence":["只填上面出现过的 URL"]}\n'
        "规则：status=scored 时 score 必须是 1-10 的整数且 evidence 至少 1 条；"
        "status=insufficient_evidence 时 score 为 null。"
    )
    body = {"model": provider["model"], "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": 1200}
    status, payload = post_json(provider["endpoint"], key, body, 90)
    if status != 200 or not isinstance(payload, dict):
        return {"error": f"model_http_{status}"}
    choices = payload.get("choices") or []
    if not choices:
        return {"error": "model_no_choice"}
    text = ((choices[0].get("message") or {}).get("content")) or ""
    try:
        answer, _ = json.JSONDecoder().raw_decode(text.strip())
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {"error": "model_not_json"}
        try:
            answer = json.loads(text[start:end + 1])
        except ValueError:
            return {"error": "model_not_json"}
    usage = payload.get("usage") or {}
    answer["_usage"] = {"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")}
    return answer


def clean_answer(raw: dict, sources: list[dict]) -> tuple[dict, list[str]]:
    problems = []
    allowed = {s["url"]: s for s in sources}
    status = raw.get("status")
    score = raw.get("score")
    summary = raw.get("summary") if isinstance(raw.get("summary"), str) else ""
    evidence_urls = [u for u in (raw.get("evidence") or []) if isinstance(u, str)]
    unknown = [u for u in evidence_urls if u not in allowed]
    if unknown:
        problems.append("dropped_unknown_urls:" + ",".join(unknown[:3]))
    evidence_urls = [u for u in evidence_urls if u in allowed]
    if status == "scored":
        if type(score) is not int or not 1 <= score <= 10:
            status, score, problems = "insufficient_evidence", None, problems + ["score_invalid"]
        elif not evidence_urls:
            status, score = "insufficient_evidence", None
            problems.append("no_evidence_urls")
    elif status != "insufficient_evidence":
        status, score = "insufficient_evidence", None
        problems.append("status_invalid")
    if status != "scored":
        score = None
        if not summary:
            summary = "本次检索未提供可核验的结构性证据。"
    evidence = [{"url": u, "title": allowed[u]["title"], "date": allowed[u]["date"]} for u in evidence_urls]
    return {"status": status, "score": score, "summary": summary[:300], "evidence": evidence}, problems


def render(company: str, answers: list[dict], meta: dict, out: Path) -> None:
    rows = []
    for a in answers:
        ev = "<br>".join(f'<a href="{html.escape(e["url"])}">{html.escape(e["title"] or e["url"])}</a>' for e in a["evidence"])
        rows.append(
            "<tr><td>{}<br><span class='q'>{}</span></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(a["question_id"]), html.escape(a["question"]),
                html.escape("已评分" if a["status"] == "scored" else "证据不足"),
                html.escape(str(a["score"])) if a["score"] is not None else "-",
                html.escape(a["summary"]), ev or "-",
            )
        )
    page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>__COMPANY__ 薄草稿</title>
<style>body{font:14px/1.6 system-ui,"Microsoft YaHei";max-width:1100px;margin:32px auto;padding:0 16px;color:#1f2328}
table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
.q{color:#6b7280;font-size:12px}.warn{background:#fffbeb;border:1px solid #fde68a;padding:10px 12px;border-radius:8px}</style>
<h1>__COMPANY__ · 24 题薄草稿</h1>
<p class="warn"><b>草稿，非正式入账</b>：没有 owner 凭证、没有预算预留、没有观察入库。分数只用于先看方向，不能当正式结论或投资建议。</p>
<p>生成 __WHEN__ · 搜索 __SEARCHES__ 次 · 模型调用 __CALLS__ 次 · 搜索成本约 $__COST__</p>
<table><tr><th>问题</th><th>状态</th><th>分</th><th>结论</th><th>来源</th></tr>__ROWS__</table>
</body></html>"""
    page = (page.replace("__COMPANY__", html.escape(company))
                .replace("__WHEN__", html.escape(meta["when"]))
                .replace("__SEARCHES__", str(meta["searches"]))
                .replace("__CALLS__", str(meta["calls"]))
                .replace("__COST__", f"{meta['cost_micros']/USD_MICROS:.4f}")
                .replace("__ROWS__", "".join(rows)))
    out.write_text(page, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", required=True)
    parser.add_argument("--questions", type=Path, default=ROOT / "docs/implementation/questions-24.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-searches-per-question", type=int, default=1)
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    providers = json.loads(PROVIDERS.read_text(encoding="utf-8-sig"))
    search_provider = providers["search"][0]
    models = providers["model"]
    catalog = json.loads(args.questions.read_text(encoding="utf-8-sig"))
    questions = catalog["questions"][: args.limit]
    args.out.mkdir(parents=True, exist_ok=True)
    spent = 0
    searches = calls = 0
    answers = []
    log = []
    for q in questions:
        record = {"question_id": q["id"], "question": q["question"], "status": "insufficient_evidence",
                  "score": None, "summary": "", "evidence": [], "searches": 0, "problems": []}
        sources = []
        if args.dry_run:
            record["summary"] = "dry-run：未调用搜索或模型。"
        else:
            for attempt in range(max(1, args.max_searches_per_question)):
                query = args.company + " " + q["question"] + (" 2025 2026" if attempt else "")
                found = search(search_provider, query, 5)
                searches += 1
                spent += int(search_provider.get("cost_micros", 0))
                record["searches"] += 1
                if found:
                    sources.extend(found)
                    break
            seen = set()
            sources = [s for s in sources if not (s["url"] in seen or seen.add(s["url"]))]
            if not sources:
                record["summary"] = "检索无可用来源，标为证据不足。"
            else:
                raw = None
                for provider in models:
                    for attempt in range(2):
                        candidate = ask_model(provider, args.company, q["question"], sources)
                        if attempt == 0 and candidate.get("error") == "model_not_json":
                            continue
                        raw = candidate
                        break
                    if raw is not None and "error" not in raw:
                        break
                if raw is None or "error" in raw:
                    record["problems"].append((raw or {}).get("error", "model_failed"))
                    record["summary"] = "模型调用失败，保留证据不足。"
                else:
                    calls += 1
                    cleaned, problems = clean_answer(raw, sources)
                    record.update(cleaned)
                    record["problems"].extend(problems)
                    record["usage"] = raw.get("_usage")
                    if not record["summary"]:
                        record["summary"] = "（模型未给出结论）"
        answers.append(record)
        log.append({"question_id": q["id"], "searches": record["searches"], "status": record["status"],
                    "problems": record["problems"]})
    meta = {"when": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "searches": searches, "calls": calls, "cost_micros": spent}
    (args.out / "answers.json").write_text(json.dumps(
        {"company": args.company, "draft": True, "verified": False, "as_of": "2026-10-18",
         "meta": meta, "answers": answers}, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "run-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    render(args.company, answers, meta, args.out / "index.html")
    scored = sum(1 for a in answers if a["status"] == "scored")
    print(json.dumps({"company": args.company, "questions": len(answers), "scored": scored,
                      "searches": searches, "calls": calls,
                      "search_cost_usd": round(spent / USD_MICROS, 4), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
