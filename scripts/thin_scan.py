"""Thin draft scan: ask a question set for one company with web search.

Draft only: no owner admission, no receipts, no observation import. Every scored
answer must cite URLs that came back from the actual search call; otherwise the
answer is recorded as insufficient_evidence. Providers are tried in the order
declared in docs/implementation/thin-scan-providers.json (cost/quality ranking),
with no budget-approval gate.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import question_bank  # noqa: E402
import model_config  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/models.json"
USD_MICROS = 1_000_000


def post_json(url: str, key: str, body: dict, timeout: float) -> tuple[int, dict]:
    """POST JSON and never raise on transport failure.

    Returns (status, payload). A timeout or connection error yields status 0 with
    an error marker so one bad request degrades that question instead of aborting
    a multi-question run. Before this, a single read timeout escaped urllib and
    killed a 38-question scan 158 seconds in, discarding every collected answer.
    """
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
    except TimeoutError:
        return 0, {"error": "timeout"}
    except urllib.error.URLError as error:
        reason = getattr(error, "reason", error)
        if isinstance(reason, TimeoutError):
            return 0, {"error": "timeout"}
        return 0, {"error": "transport", "detail": str(reason)[:200]}
    except (OSError, ValueError) as error:
        return 0, {"error": "transport", "detail": str(error)[:200]}


def search_with_status(provider: dict, query: str, count: int) -> tuple[list[dict], str | None]:
    """Search once and distinguish an empty result from a failed call.

    Returns (results, error). error is None only when the provider answered and
    genuinely had nothing. Missing credentials, non-200 responses and malformed
    payloads are reported instead of being flattened into an empty list, so a
    credential outage cannot masquerade as "no usable sources".
    """
    key = os.environ.get(provider["key_env"], "")
    if not key:
        return [], "search_missing_credentials:" + provider["key_env"]
    status, payload = post_json(provider["endpoint"], key, {"query": query, "count": count, "need_content": False}, 30)
    if status == 0:
        marker = (payload or {}).get("error") if isinstance(payload, dict) else None
        return [], "search_timeout" if marker == "timeout" else "search_transport_error"
    if status != 200:
        return [], f"search_http_{status}"
    if not isinstance(payload, dict):
        return [], "search_bad_payload"
    results = payload.get("results")
    if not isinstance(results, list):
        return [], "search_bad_payload"
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
    return out, None


def _record_search_outcome(record: dict, results: list[dict], error: str | None) -> None:
    """Account for one search attempt on the question record."""
    record["searches"] = record.get("searches", 0) + 1
    if error:
        record.setdefault("problems", []).append(error)


def search(provider: dict, query: str, count: int) -> list[dict]:
    """Backwards-compatible list-shaped entrypoint."""
    return search_with_status(provider, query, count)[0]


def build_prompt(question: dict, company: str, sources: list[dict], as_of: str, bank_mode: bool):
    source_text = "\n".join(
        f"[{i+1}] {s['title']}\nURL: {s['url']}\n日期: {s['date']}\n摘要: {s['summary'][:300]}"
        for i, s in enumerate(sources)
    ) or "（本次没有检索到可用来源）"
    if bank_mode and question.get("prompt"):
        base = question["prompt"]
        expected = question.get("prompt_sha256")
        actual = hashlib.sha256(base.encode("utf-8")).hexdigest()
        if expected and actual != expected:
            raise ValueError("manifest prompt hash mismatch for " + str(question.get("id")))
        prompt = (base + "\n\n本次真实检索结果（只可引用这些 URL）：\n" + source_text
                  + "\n\n只输出上述外层 JSON，description 内的 evidence 只填上面出现过的 URL。")
        return prompt, "manifest_full", True
    qtext = question.get("question") or ""
    extra = ""
    if question.get("evidence"):
        extra += "证据关注：" + "；".join(str(x) for x in question["evidence"]) + "\n"
    if question.get("anchors"):
        extra += "评分锚点：" + "；".join(f"{k}={v}" for k, v in question["anchors"].items()) + "\n"
    prompt = (
        "你是严谨的公司研究员。只根据下面给出的检索结果回答，不要使用记忆补充事实。\n"
        "如果证据不足，必须返回 insufficient_evidence，不要猜分数。\n\n"
        f"公司：{company}\n问题：{qtext}\n{extra}信息截止：{as_of}\n\n"
        f"检索结果：\n{source_text}\n\n"
        "只输出一个 JSON 对象，不要 markdown，不要解释。格式：\n"
        '{"status":"scored" 或 "insufficient_evidence","score":1-10 的整数或 null,'
        '"summary":"不超过120字的结论","evidence":["只填上面出现过的 URL"]}\n'
        "规则：status=scored 时 score 必须是 1-10 的整数且 evidence 至少 1 条；"
        "status=insufficient_evidence 时 score 为 null。"
    )
    return prompt, "brief", False


def normalize_bank_answer(raw: dict) -> dict:
    inner = raw
    description = raw.get("description")
    if isinstance(description, str):
        try:
            parsed = json.loads(description)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            inner = parsed
    evidence = inner.get("evidence")
    urls = []
    for entry in evidence or []:
        if isinstance(entry, dict) and isinstance(entry.get("url"), str):
            urls.append(entry["url"])
        elif isinstance(entry, str):
            urls.append(entry)
    status = inner.get("status") or ("scored" if isinstance(inner.get("score"), int) else "insufficient_evidence")
    score = inner.get("score") if status == "scored" else None
    return {
        "status": status,
        "score": score,
        "summary": inner.get("rationale") or raw.get("summary") or "",
        "evidence": urls,
        "counterevidence": inner.get("counterevidence"),
    }


def ask_model(provider: dict, prompt: str, max_tokens: int = 1200) -> dict:
    key = os.environ.get(provider["key_env"], "")
    body = {"model": provider["model"], "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": max_tokens}
    status, payload = post_json(provider["endpoint"], key, body, 90)
    if status == 0:
        marker = (payload or {}).get("error") if isinstance(payload, dict) else None
        return {"error": "model_timeout" if marker == "timeout" else "model_transport_error"}
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
    identity = meta.get("bank")
    summary = meta.get("summary") or {}
    if identity:
        bank_line = ("题库：" + str(identity.get("package_id"))[:20] + "… · "
                     + str(len(identity.get("modules") or [])) + " 模块 · "
                     + str(summary.get("core_scored")) + "/" + str(summary.get("core_total")) + " 核心题有分 · "
                     + str(summary.get("context_scored")) + "/" + str(summary.get("context_total")) + " 扩展题有分"
                     + " · 均值为草稿口径（非正式聚合）")
    else:
        bank_line = "题库：未绑定（仅 24 题通用清单，结果不可版本化重放）"
    page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>__COMPANY__ 薄草稿</title>
<style>body{font:14px/1.6 system-ui,"Microsoft YaHei";max-width:1100px;margin:32px auto;padding:0 16px;color:#1f2328}
table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
.q{color:#6b7280;font-size:12px}.warn{background:#fffbeb;border:1px solid #fde68a;padding:10px 12px;border-radius:8px}</style>
<h1>__COMPANY__ · 24 题薄草稿</h1>
<p class="warn"><b>草稿，非正式入账</b>：没有 owner 凭证、没有预算预留、没有观察入库。分数只用于先看方向，不能当正式结论或投资建议。</p>
<p>生成 __WHEN__ · 搜索 __SEARCHES__ 次 · 模型调用 __CALLS__ 次 · 搜索成本约 $__COST__</p>
<p>__BANK_LINE__</p>
<table><tr><th>问题</th><th>状态</th><th>分</th><th>结论</th><th>来源</th></tr>__ROWS__</table>
</body></html>"""
    page = (page.replace("__COMPANY__", html.escape(company))
                .replace("__WHEN__", html.escape(meta["when"]))
                .replace("__SEARCHES__", str(meta["searches"]))
                .replace("__CALLS__", str(meta["calls"]))
                .replace("__COST__", f"{meta['cost_micros']/USD_MICROS:.4f}")
                .replace("__BANK_LINE__", html.escape(bank_line))
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
    parser.add_argument("--as-of")
    parser.add_argument("--bank-manifest", type=Path,
                        help="composed manifest.json from scripts/question_sets.py compose")
    args = parser.parse_args()
    search_provider = model_config.search()[0]
    models = model_config.models()
    bank = None
    if args.bank_manifest:
        bank = question_bank.load_manifest(args.bank_manifest)
        questions = bank["questions"][: args.limit]
        as_of = args.as_of or bank["identity"].get("as_of") or "2026-10-18"
    else:
        catalog = json.loads(args.questions.read_text(encoding="utf-8-sig"))
        questions = catalog["questions"][: args.limit]
        for q in questions:
            q["core"] = True
        as_of = args.as_of or "2026-10-18"
    args.out.mkdir(parents=True, exist_ok=True)
    spent = 0
    searches = calls = 0
    answers = []
    log = []
    for q in questions:
        record = {"question_id": q["id"], "question": q["question"], "status": "insufficient_evidence",
                  "score": None, "summary": "", "evidence": [], "searches": 0, "problems": [],
                  "module_id": q.get("module_id"), "construct_id": q.get("construct_id"),
                  "core": bool(q.get("core", True)),
                  "prompt_sha256": q.get("prompt_sha256"),
                  "semantic_sha256": q.get("semantic_sha256"),
                  "definition_sha256": q.get("definition_sha256")}
        sources = []
        if args.dry_run:
            record["summary"] = "dry-run：未调用搜索或模型。"
        else:
            for attempt in range(max(1, args.max_searches_per_question)):
                query = (args.company + " " + q["question"] + (" 2025 2026" if attempt else ""))[:220]
                found, search_error = search_with_status(search_provider, query, 5)
                _record_search_outcome(record, found, search_error)
                searches += 1
                spent += int(search_provider.get("cost_micros", 0))
                if found:
                    sources.extend(found)
                    break
            seen = set()
            sources = [s for s in sources if not (s["url"] in seen or seen.add(s["url"]))]
            if not sources:
                if any(str(problem).startswith("search_") for problem in record["problems"]):
                    record["summary"] = "检索调用失败（见 problems），未进入模型；不伪造结论。"
                else:
                    record["summary"] = "检索无可用来源，标为证据不足。"
            else:
                prompt, prompt_mode, prompt_verified = build_prompt(
                    q, args.company, sources, as_of, bank is not None)
                record["prompt_mode"] = prompt_mode
                record["prompt_verified"] = prompt_verified
                record["dispatch_prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                raw = None
                for provider in models:
                    for attempt in range(2):
                        candidate = ask_model(provider, prompt, 2400 if bank else 1200)
                        if bank is not None:
                            candidate = normalize_bank_answer(candidate)
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
    summary = question_bank.summarize(answers)
    identity = bank["identity"] if bank else None
    meta = {"when": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "searches": searches, "calls": calls, "cost_micros": spent,
            "bank": identity, "summary": summary}
    (args.out / "answers.json").write_text(json.dumps(
        {"company": args.company, "draft": True, "verified": False, "as_of": as_of,
         "importable": bank is not None,
         "provenance": "versioned_bank" if bank is not None else "unversioned_flat_list",
         "bank": identity, "summary": summary, "meta": meta, "answers": answers},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "run-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    render(args.company, answers, meta, args.out / "index.html")
    scored = sum(1 for a in answers if a["status"] == "scored")
    print(json.dumps({"company": args.company, "questions": len(answers), "scored": scored,
                      "core": summary, "bank": None if identity is None else identity["package_id"],
                      "searches": searches, "calls": calls,
                      "search_cost_usd": round(spent / USD_MICROS, 4), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
